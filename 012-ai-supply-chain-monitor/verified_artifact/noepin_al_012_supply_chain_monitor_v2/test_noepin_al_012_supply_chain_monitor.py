import hashlib, json, unittest
from noepin_al_012_supply_chain_monitor import *

H0="0"*64
H1="1"*64
H2="2"*64

def comp(cid="model", **kw):
    d=dict(component_id=cid,kind=ComponentKind.MODEL,version="1.0",artifact_sha256=H0,config_sha256=None,
           signer_ref="signer",signature_verified=True,source_ref="registry",enabled=True,metadata={})
    d.update(kw); return ComponentState(**d)

def manifest(mid="m1", comps=None, **kw):
    d=dict(manifest_id=mid,version=1,authority_version=1,components=tuple(comps or (comp(),)),
           manifest_sha256=None,approved_change_ref=None,revoked=False,schema_version="1")
    d.update(kw)
    m=SupplyManifest(**d)
    return m

def req(**kw):
    b=manifest("base")
    o=manifest("obs")
    d=dict(request_id="r1",baseline=b,observed=o,expected_baseline_version=1,expected_authority_version=1,
           human_approved=False,approval_ref=None,schema_version="1",context={})
    d.update(kw); return SupplyAuditRequest(**d)

class T(unittest.TestCase):
    def setUp(self): self.m=AISupplyChainMonitor(policy_version="v2")
    def check(self,r,d):
        o=self.m.evaluate(r); self.assertEqual(o.decision,d)
        self.assertFalse(o.authoritative); self.assertFalse(o.change_approved)
        self.assertFalse(o.action_executed); self.assertFalse(o.deployment_succeeded)
        return o

    def test_match(self): self.check(req(),SupplyDecision.MATCH)
    def test_missing_request(self): self.check(req(request_id=""),SupplyDecision.HOLD)
    def test_missing_schema(self): self.check(req(schema_version=""),SupplyDecision.HOLD)
    def test_baseline_missing_id(self): self.check(req(baseline=manifest("",)),SupplyDecision.HOLD)
    def test_observed_missing_id(self): self.check(req(observed=manifest("",)),SupplyDecision.HOLD)
    def test_bad_baseline_version(self): self.check(req(baseline=manifest(version=0)),SupplyDecision.HOLD)
    def test_bad_observed_version(self): self.check(req(observed=manifest(version=0)),SupplyDecision.HOLD)
    def test_bad_authority_version(self): self.check(req(baseline=manifest(authority_version=0)),SupplyDecision.HOLD)
    def test_baseline_revoked(self): self.check(req(baseline=manifest(revoked=True)),SupplyDecision.DENY)
    def test_observed_revoked(self): self.check(req(observed=manifest(revoked=True)),SupplyDecision.DENY)
    def test_duplicate_component(self): self.check(req(observed=manifest(comps=(comp("x"),comp("x")))),SupplyDecision.HOLD)
    def test_missing_component_id(self): self.check(req(observed=manifest(comps=(comp(""),))),SupplyDecision.HOLD)
    def test_missing_component_version(self): self.check(req(observed=manifest(comps=(comp(version=""),))),SupplyDecision.HOLD)
    def test_bad_artifact_hash(self): self.check(req(observed=manifest(comps=(comp(artifact_sha256="bad"),))),SupplyDecision.HOLD)
    def test_bad_config_hash(self): self.check(req(observed=manifest(comps=(comp(config_sha256="bad"),))),SupplyDecision.HOLD)
    def test_baseline_version_mismatch(self): self.check(req(expected_baseline_version=2),SupplyDecision.HOLD)
    def test_authority_version_mismatch(self): self.check(req(expected_authority_version=2),SupplyDecision.HOLD)

    def test_manifest_hash_valid(self):
        b=manifest("base"); bh=self.m.canonical_manifest_hash(b); b=SupplyManifest(**{**b.__dict__,"manifest_sha256":bh})
        o=manifest("obs"); oh=self.m.canonical_manifest_hash(o); o=SupplyManifest(**{**o.__dict__,"manifest_sha256":oh})
        self.check(req(baseline=b,observed=o),SupplyDecision.MATCH)
    def test_manifest_hash_invalid(self):
        o=manifest("obs",manifest_sha256=H2); self.check(req(observed=o),SupplyDecision.DENY)
    def test_manifest_hash_malformed(self):
        o=manifest("obs",manifest_sha256="bad"); self.check(req(observed=o),SupplyDecision.HOLD)

    def test_signature_required(self):
        o=manifest("obs",comps=(comp(signer_ref=None,signature_verified=False),))
        self.check(req(observed=o),SupplyDecision.HOLD)
    def test_signature_unverified(self):
        o=manifest("obs",comps=(comp(signature_verified=False),))
        self.check(req(observed=o),SupplyDecision.DENY)
    def test_prompt_signature_not_required(self):
        c=comp(kind=ComponentKind.PROMPT,signer_ref=None,signature_verified=False)
        b=manifest("base",comps=(c,)); o=manifest("obs",comps=(c,))
        self.check(req(baseline=b,observed=o),SupplyDecision.MATCH)

    def test_added(self):
        b=manifest("base",comps=(comp("a"),)); o=manifest("obs",comps=(comp("a"),comp("b")))
        r=self.check(req(baseline=b,observed=o),SupplyDecision.HUMAN_REVIEW); self.assertEqual(r.added_ids,("b",))
    def test_removed(self):
        b=manifest("base",comps=(comp("a"),comp("b"))); o=manifest("obs",comps=(comp("a"),))
        r=self.check(req(baseline=b,observed=o),SupplyDecision.HUMAN_REVIEW); self.assertEqual(r.removed_ids,("b",))
    def test_changed_version(self):
        b=manifest("base",comps=(comp("a"),)); o=manifest("obs",comps=(comp("a",version="2.0"),))
        r=self.check(req(baseline=b,observed=o),SupplyDecision.HUMAN_REVIEW); self.assertEqual(r.changed_ids,("a",))
    def test_changed_hash(self):
        b=manifest("base",comps=(comp("a"),)); o=manifest("obs",comps=(comp("a",artifact_sha256=H1),))
        self.check(req(baseline=b,observed=o),SupplyDecision.HUMAN_REVIEW)
    def test_changed_config(self):
        b=manifest("base",comps=(comp("a",config_sha256=H0),)); o=manifest("obs",comps=(comp("a",config_sha256=H1),))
        self.check(req(baseline=b,observed=o),SupplyDecision.HUMAN_REVIEW)
    def test_changed_enabled(self):
        b=manifest("base",comps=(comp("a"),)); o=manifest("obs",comps=(comp("a",enabled=False),))
        self.check(req(baseline=b,observed=o),SupplyDecision.HUMAN_REVIEW)
    def test_unchanged_ids(self):
        b=manifest("base",comps=(comp("a"),comp("b"))); o=manifest("obs",comps=(comp("a"),comp("b")))
        r=self.check(req(baseline=b,observed=o),SupplyDecision.MATCH); self.assertEqual(r.unchanged_ids,("a","b"))

    def test_human_approval_still_review(self):
        b=manifest("base",comps=(comp("a"),)); o=manifest("obs",comps=(comp("a",version="2"),))
        r=self.check(req(baseline=b,observed=o,human_approved=True,approval_ref="H"),SupplyDecision.HUMAN_REVIEW)
        self.assertFalse(r.change_approved)
    def test_approval_bool_only_no_auto(self):
        b=manifest("base",comps=(comp("a"),)); o=manifest("obs",comps=(comp("a",version="2"),))
        self.check(req(baseline=b,observed=o,human_approved=True),SupplyDecision.HUMAN_REVIEW)

    def test_cache_exact(self):
        r=req(); a=self.m.evaluate(r); b=self.m.evaluate(r); self.assertFalse(a.cache_reused); self.assertTrue(b.cache_reused)
    def test_cache_no_authority(self):
        r=req(); self.m.evaluate(r); self.assertFalse(self.m.evaluate(r).authoritative)
    def test_cache_no_deploy_success(self):
        r=req(); self.m.evaluate(r); self.assertFalse(self.m.evaluate(r).deployment_succeeded)
    def test_cache_diff_hash_changes(self):
        b=manifest("base"); o1=manifest("obs"); o2=manifest("obs",comps=(comp(artifact_sha256=H1),))
        self.assertNotEqual(self.m.fingerprint(req(baseline=b,observed=o1)),self.m.fingerprint(req(baseline=b,observed=o2)))
    def test_cache_diff_signature_changes(self):
        self.assertNotEqual(self.m.fingerprint(req()),self.m.fingerprint(req(observed=manifest("obs",comps=(comp(signature_verified=False),)))))
    def test_context_order(self):
        self.assertEqual(self.m.fingerprint(req(context={"b":2,"a":1})),self.m.fingerprint(req(context={"a":1,"b":2})))
    def test_clear_cache(self):
        self.m.evaluate(req()); self.assertGreater(self.m.cache_size(),0); self.m.clear_cache(); self.assertEqual(self.m.cache_size(),0)
    def test_stable_no_time(self):
        self.assertNotIn("created_unix_ns",self.m.evaluate(req()).stable_payload())

    def test_match_not_deployment_success(self):
        r=self.check(req(),SupplyDecision.MATCH); self.assertFalse(r.deployment_succeeded)
    def test_signature_verified_not_authority(self):
        r=self.check(req(),SupplyDecision.MATCH); self.assertFalse(r.authoritative)
    def test_fingerprint_match_not_authority(self):
        r=self.check(req(),SupplyDecision.MATCH); self.assertTrue(r.manifest_match); self.assertFalse(r.authoritative)

    def test_model_change(self):
        b=manifest("base",comps=(comp("m",kind=ComponentKind.MODEL),)); o=manifest("obs",comps=(comp("m",kind=ComponentKind.MODEL,version="2"),))
        self.check(req(baseline=b,observed=o),SupplyDecision.HUMAN_REVIEW)
    def test_mcp_change(self):
        b=manifest("base",comps=(comp("x",kind=ComponentKind.MCP),)); o=manifest("obs",comps=(comp("x",kind=ComponentKind.MCP,artifact_sha256=H1),))
        self.check(req(baseline=b,observed=o),SupplyDecision.HUMAN_REVIEW)
    def test_plugin_change(self):
        b=manifest("base",comps=(comp("x",kind=ComponentKind.PLUGIN),)); o=manifest("obs",comps=(comp("x",kind=ComponentKind.PLUGIN,version="2"),))
        self.check(req(baseline=b,observed=o),SupplyDecision.HUMAN_REVIEW)
    def test_library_change(self):
        b=manifest("base",comps=(comp("x",kind=ComponentKind.LIBRARY),)); o=manifest("obs",comps=(comp("x",kind=ComponentKind.LIBRARY,version="2"),))
        self.check(req(baseline=b,observed=o),SupplyDecision.HUMAN_REVIEW)
    def test_prompt_change(self):
        a=comp("x",kind=ComponentKind.PROMPT,signer_ref=None,signature_verified=False)
        b=manifest("base",comps=(a,)); o=manifest("obs",comps=(ComponentState(**{**a.__dict__,"artifact_sha256":H1}),))
        self.check(req(baseline=b,observed=o),SupplyDecision.HUMAN_REVIEW)
    def test_data_source_change(self):
        a=comp("x",kind=ComponentKind.DATA_SOURCE,signer_ref=None,signature_verified=False)
        b=manifest("base",comps=(a,)); o=manifest("obs",comps=(ComponentState(**{**a.__dict__,"version":"2"}),))
        self.check(req(baseline=b,observed=o),SupplyDecision.HUMAN_REVIEW)

def replay_fingerprint():
    m=AISupplyChainMonitor(policy_version="v2"); out=[]
    kinds=list(ComponentKind)
    for i in range(1000):
        k=kinds[i%len(kinds)]
        signed=k in {ComponentKind.MODEL,ComponentKind.MCP,ComponentKind.PLUGIN,ComponentKind.LIBRARY}
        basec=comp("x",kind=k,signer_ref="s" if signed else None,signature_verified=signed)
        obsc=ComponentState(**{**basec.__dict__,"version":"2" if i%7==0 else "1.0","artifact_sha256":H1 if i%11==0 else H0})
        b=manifest(f"b{i%13}",comps=(basec,),version=1+(i%3),authority_version=1+(i%2))
        o=manifest(f"o{i%13}",comps=(obsc,),version=1+(i%3),authority_version=1+(i%2))
        r=SupplyAuditRequest(request_id=f"r{i}",baseline=b,observed=o,
            expected_baseline_version=b.version,expected_authority_version=b.authority_version,
            human_approved=(i%5==0),approval_ref="H" if i%5==0 else None)
        out.append(m.evaluate(r).stable_payload())
    raw=json.dumps(out,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

if __name__=="__main__": unittest.main()
