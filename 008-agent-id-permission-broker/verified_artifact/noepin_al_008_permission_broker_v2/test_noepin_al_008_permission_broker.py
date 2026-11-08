import hashlib,json,unittest
from noepin_al_008_permission_broker import *

def policy():
    return BrokerPolicy(policy_version="v2")

def ident(**kw):
    d=dict(agent_id="a1",role="developer",identity_version=1,disabled=False,external=False); d.update(kw); return AgentIdentity(**d)

def permit(**kw):
    d=dict(permit_id="p1",agent_id="a1",role="developer",resource_scope=("project",),
           action_scope=("read","write"),expires_at_epoch_s=2000,permit_version=1,issuer_ref="auth",revoked=False,attributes={})
    d.update(kw); return Permit(**d)

def req(**kw):
    d=dict(request_id="r1",identity=ident(),permit=permit(),resource="project/file",action="read",
           observed_epoch_s=1000,risk_score=10,expected_identity_version=1,expected_permit_version=1,
           human_approved=False,approval_ref=None,schema_version="1",context={})
    d.update(kw); return PermissionRequest(**d)

class T(unittest.TestCase):
    def setUp(self): self.b=AgentPermissionBroker(policy())
    def check(self,r,d):
        o=self.b.evaluate(r); self.assertEqual(o.decision,d)
        self.assertFalse(o.authoritative); self.assertFalse(o.action_executed); self.assertFalse(o.action_succeeded); return o
    def test_allow(self): self.check(req(),PermissionDecision.ALLOW_PREPARE)
    def test_missing_request(self): self.check(req(request_id=""),PermissionDecision.HOLD)
    def test_missing_resource(self): self.check(req(resource=""),PermissionDecision.HOLD)
    def test_missing_action(self): self.check(req(action=""),PermissionDecision.HOLD)
    def test_missing_schema(self): self.check(req(schema_version=""),PermissionDecision.HOLD)
    def test_bad_identity_id(self): self.check(req(identity=ident(agent_id="")),PermissionDecision.HOLD)
    def test_bad_identity_role(self): self.check(req(identity=ident(role="")),PermissionDecision.HOLD)
    def test_bad_identity_version(self): self.check(req(identity=ident(identity_version=0)),PermissionDecision.HOLD)
    def test_disabled(self): self.check(req(identity=ident(disabled=True)),PermissionDecision.DENY)
    def test_identity_version_mismatch(self): self.check(req(expected_identity_version=2),PermissionDecision.HOLD)
    def test_bad_time(self): self.check(req(observed_epoch_s=-1),PermissionDecision.HOLD)
    def test_bad_risk(self): self.check(req(risk_score=101),PermissionDecision.HOLD)
    def test_bool_risk(self): self.check(req(risk_score=True),PermissionDecision.HOLD)
    def test_permit_required(self): self.check(req(permit=None),PermissionDecision.DENY)
    def test_malformed_permit(self): self.check(req(permit=permit(permit_id="")),PermissionDecision.DENY)
    def test_invalid_permit_version(self): self.check(req(permit=permit(permit_version=0)),PermissionDecision.HOLD)
    def test_invalid_expiry(self): self.check(req(permit=permit(expires_at_epoch_s=True)),PermissionDecision.HOLD)
    def test_revoked(self): self.check(req(permit=permit(revoked=True)),PermissionDecision.DENY)
    def test_permit_version_mismatch(self): self.check(req(expected_permit_version=2),PermissionDecision.HOLD)
    def test_agent_mismatch(self): self.check(req(permit=permit(agent_id="other")),PermissionDecision.DENY)
    def test_role_mismatch(self): self.check(req(permit=permit(role="viewer")),PermissionDecision.DENY)
    def test_expired_equal(self): self.check(req(observed_epoch_s=2000),PermissionDecision.DENY)
    def test_expired_after(self): self.check(req(observed_epoch_s=2001),PermissionDecision.DENY)
    def test_valid_before(self): self.check(req(observed_epoch_s=1999),PermissionDecision.ALLOW_PREPARE)
    def test_resource_denied(self): self.check(req(resource="other/file"),PermissionDecision.DENY)
    def test_action_denied(self): self.check(req(action="delete"),PermissionDecision.DENY)
    def test_resource_wildcard(self): self.check(req(permit=permit(resource_scope=("*",))),PermissionDecision.ALLOW_PREPARE)
    def test_action_wildcard(self): self.check(req(action="delete",permit=permit(action_scope=("*",))),PermissionDecision.ALLOW_PREPARE)
    def test_nested_resource_scope(self): self.check(req(resource="project/a/b"),PermissionDecision.ALLOW_PREPARE)
    def test_similar_prefix_denied(self): self.check(req(resource="project2/a"),PermissionDecision.DENY)

    def test_external_highrisk_confirm(self):
        i=ident(external=True); p=permit(action_scope=("delete",))
        self.check(req(identity=i,permit=p,action="delete"),PermissionDecision.HUMAN_CONFIRM)
    def test_external_highrisk_approved(self):
        i=ident(external=True); p=permit(action_scope=("delete",))
        self.check(req(identity=i,permit=p,action="delete",human_approved=True,approval_ref="H"),PermissionDecision.ALLOW_PREPARE)
    def test_external_highrisk_bool_only(self):
        i=ident(external=True); p=permit(action_scope=("delete",))
        self.check(req(identity=i,permit=p,action="delete",human_approved=True),PermissionDecision.HUMAN_CONFIRM)
    def test_external_highrisk_ref_only(self):
        i=ident(external=True); p=permit(action_scope=("delete",))
        self.check(req(identity=i,permit=p,action="delete",approval_ref="H"),PermissionDecision.HUMAN_CONFIRM)
    def test_risk_over_50_external_confirm(self):
        self.check(req(identity=ident(external=True),risk_score=51),PermissionDecision.HUMAN_CONFIRM)
    def test_risk_50_external_allow(self):
        self.check(req(identity=ident(external=True),risk_score=50),PermissionDecision.ALLOW_PREPARE)

    def test_cache_exact(self):
        r=req(); a=self.b.evaluate(r); c=self.b.evaluate(r); self.assertFalse(a.cache_reused); self.assertTrue(c.cache_reused)
    def test_cache_never_authority(self):
        r=req(); self.b.evaluate(r); self.assertFalse(self.b.evaluate(r).authoritative)
    def test_cache_never_success(self):
        r=req(); self.b.evaluate(r); self.assertFalse(self.b.evaluate(r).action_succeeded)
    def test_revocation_changes_fingerprint(self):
        self.assertNotEqual(self.b.fingerprint(req()),self.b.fingerprint(req(permit=permit(revoked=True))))
    def test_expiry_changes_fingerprint(self):
        self.assertNotEqual(self.b.fingerprint(req()),self.b.fingerprint(req(permit=permit(expires_at_epoch_s=3000))))
    def test_role_changes_fingerprint(self):
        self.assertNotEqual(self.b.fingerprint(req()),self.b.fingerprint(req(identity=ident(role="viewer"),permit=permit(role="viewer"))))
    def test_permit_version_changes_fingerprint(self):
        self.assertNotEqual(self.b.fingerprint(req()),self.b.fingerprint(req(permit=permit(permit_version=2),expected_permit_version=2)))
    def test_identity_version_changes_fingerprint(self):
        self.assertNotEqual(self.b.fingerprint(req()),self.b.fingerprint(req(identity=ident(identity_version=2),expected_identity_version=2)))
    def test_context_order(self):
        self.assertEqual(self.b.fingerprint(req(context={"b":2,"a":1})),self.b.fingerprint(req(context={"a":1,"b":2})))
    def test_clear_cache(self):
        self.b.evaluate(req()); self.assertGreater(self.b.cache_size(),0); self.b.clear_cache(); self.assertEqual(self.b.cache_size(),0)
    def test_stable_no_time(self): self.assertNotIn("created_unix_ns",self.b.evaluate(req()).stable_payload())
    def test_allow_never_executes(self):
        o=self.check(req(),PermissionDecision.ALLOW_PREPARE); self.assertFalse(o.action_executed)
    def test_id_known_not_enough(self):
        self.check(req(permit=None),PermissionDecision.DENY)
    def test_permit_present_not_enough(self):
        self.check(req(permit=permit(revoked=True)),PermissionDecision.DENY)
    def test_many_valid(self):
        for i in range(10):
            p=permit(permit_id=f"p{i}")
            self.check(req(request_id=f"r{i}",permit=p),PermissionDecision.ALLOW_PREPARE)

def replay_fingerprint():
    b=AgentPermissionBroker(policy()); out=[]
    for i in range(1000):
        ext=i%3==0; iv=1+(i%3); pv=1+(i%4)
        identity=ident(agent_id=f"a{i%11}",identity_version=iv,external=ext)
        p=permit(permit_id=f"p{i%17}",agent_id=identity.agent_id,identity_version=1 if False else 1) if False else Permit(
            permit_id=f"p{i%17}",agent_id=identity.agent_id,role="developer",resource_scope=("project",),
            action_scope=("read","write","delete"),expires_at_epoch_s=5000,permit_version=pv,issuer_ref="auth",revoked=(i%29==0))
        r=PermissionRequest(request_id=f"r{i}",identity=identity,permit=p,resource=f"project/f{i%13}",action="delete" if i%7==0 else "read",
            observed_epoch_s=1000+(i%100),risk_score=i%60,expected_identity_version=iv,expected_permit_version=pv,
            human_approved=(i%5==0),approval_ref="H" if i%5==0 else None)
        out.append(b.evaluate(r).stable_payload())
    raw=json.dumps(out,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

if __name__=="__main__": unittest.main()
