import hashlib, json, unittest
from noepin_al_009_tool_permission_controller import *

def policy():
    return ToolControllerPolicy(
        allowed_servers=("mcp:files","mcp:notion"),
        allowed_tools=("read_file","write_file","search","update_page"),
        high_risk_operations=("delete","publish","purchase","external_send","execute","write_production"),
        max_risk_without_confirmation=35,
        policy_version="v2"
    )

def permit(**kw):
    d=dict(
        permit_id="p1", agent_id="a1", server_id="mcp:files", tool_name="read_file",
        operations=("read",), scopes=("project",), expires_at_epoch_s=2000,
        permit_version=1, issuer_ref="auth", revoked=False
    )
    d.update(kw)
    return ToolPermit(**d)

def req(**kw):
    d=dict(
        request_id="r1", agent_id="a1", server_id="mcp:files", tool_name="read_file",
        operation="read", required_scope="project/file", observed_epoch_s=1000,
        risk_score=5, permit=permit(), expected_permit_version=1,
        oauth_authenticated=False, oidc_authenticated=False, external_side_effect=False,
        human_approved=False, approval_ref=None, schema_version="1", context={}
    )
    d.update(kw)
    return ToolRequest(**d)

class T(unittest.TestCase):
    def setUp(self): self.c=ToolPermissionController(policy())
    def check(self,r,d):
        o=self.c.evaluate(r); self.assertEqual(o.decision,d)
        self.assertFalse(o.authoritative); self.assertFalse(o.tool_called)
        self.assertFalse(o.action_executed); self.assertFalse(o.action_succeeded)
        return o

    def test_allow(self): self.check(req(),ToolDecision.ALLOW_PREPARE)
    def test_missing_request(self): self.check(req(request_id=""),ToolDecision.HOLD)
    def test_missing_agent(self): self.check(req(agent_id=""),ToolDecision.HOLD)
    def test_missing_server(self): self.check(req(server_id=""),ToolDecision.HOLD)
    def test_missing_tool(self): self.check(req(tool_name=""),ToolDecision.HOLD)
    def test_missing_operation(self): self.check(req(operation=""),ToolDecision.HOLD)
    def test_missing_scope(self): self.check(req(required_scope=""),ToolDecision.HOLD)
    def test_missing_schema(self): self.check(req(schema_version=""),ToolDecision.HOLD)
    def test_server_not_allowlisted(self): self.check(req(server_id="mcp:other"),ToolDecision.DENY)
    def test_tool_not_allowlisted(self): self.check(req(tool_name="shell"),ToolDecision.DENY)
    def test_bad_time(self): self.check(req(observed_epoch_s=-1),ToolDecision.HOLD)
    def test_bad_risk(self): self.check(req(risk_score=101),ToolDecision.HOLD)
    def test_bool_risk(self): self.check(req(risk_score=True),ToolDecision.HOLD)

    def test_permit_required(self): self.check(req(permit=None),ToolDecision.DENY)
    def test_malformed_permit(self): self.check(req(permit=permit(permit_id="")),ToolDecision.DENY)
    def test_bad_permit_version(self): self.check(req(permit=permit(permit_version=0)),ToolDecision.HOLD)
    def test_bad_expiry(self): self.check(req(permit=permit(expires_at_epoch_s=True)),ToolDecision.HOLD)
    def test_revoked(self): self.check(req(permit=permit(revoked=True)),ToolDecision.DENY)
    def test_version_mismatch(self): self.check(req(expected_permit_version=2),ToolDecision.HOLD)
    def test_agent_mismatch(self): self.check(req(permit=permit(agent_id="a2")),ToolDecision.DENY)
    def test_server_mismatch(self): self.check(req(permit=permit(server_id="mcp:notion")),ToolDecision.DENY)
    def test_tool_mismatch(self): self.check(req(permit=permit(tool_name="search")),ToolDecision.DENY)
    def test_expired_equal(self): self.check(req(observed_epoch_s=2000),ToolDecision.DENY)
    def test_expired_after(self): self.check(req(observed_epoch_s=2001),ToolDecision.DENY)
    def test_before_expiry(self): self.check(req(observed_epoch_s=1999),ToolDecision.ALLOW_PREPARE)

    def test_operation_denied(self): self.check(req(operation="write"),ToolDecision.DENY)
    def test_operation_wildcard(self): self.check(req(operation="write",permit=permit(operations=("*",))),ToolDecision.ALLOW_PREPARE)
    def test_scope_denied(self): self.check(req(required_scope="other/file"),ToolDecision.DENY)
    def test_scope_wildcard(self): self.check(req(required_scope="other/file",permit=permit(scopes=("*",))),ToolDecision.ALLOW_PREPARE)
    def test_nested_scope(self): self.check(req(required_scope="project/a/b"),ToolDecision.ALLOW_PREPARE)
    def test_similar_prefix_denied(self): self.check(req(required_scope="project2/file"),ToolDecision.DENY)

    def test_oauth_alone_not_authority(self):
        self.check(req(permit=None,oauth_authenticated=True),ToolDecision.DENY)
    def test_oidc_alone_not_authority(self):
        self.check(req(permit=None,oidc_authenticated=True),ToolDecision.DENY)
    def test_auth_does_not_expand_operation(self):
        self.check(req(operation="write",oauth_authenticated=True,oidc_authenticated=True),ToolDecision.DENY)

    def test_high_risk_operation_confirm(self):
        p=permit(operations=("delete",))
        self.check(req(operation="delete",permit=p),ToolDecision.HUMAN_CONFIRM)
    def test_high_risk_approved(self):
        p=permit(operations=("delete",))
        self.check(req(operation="delete",permit=p,human_approved=True,approval_ref="H"),ToolDecision.ALLOW_PREPARE)
    def test_risk_35_allow(self): self.check(req(risk_score=35),ToolDecision.ALLOW_PREPARE)
    def test_risk_36_confirm(self): self.check(req(risk_score=36),ToolDecision.HUMAN_CONFIRM)
    def test_risk_36_approved(self): self.check(req(risk_score=36,human_approved=True,approval_ref="H"),ToolDecision.ALLOW_PREPARE)
    def test_external_side_effect_confirm(self): self.check(req(external_side_effect=True),ToolDecision.HUMAN_CONFIRM)
    def test_external_side_effect_approved(self): self.check(req(external_side_effect=True,human_approved=True,approval_ref="H"),ToolDecision.ALLOW_PREPARE)
    def test_approval_bool_without_ref(self): self.check(req(risk_score=36,human_approved=True),ToolDecision.HUMAN_CONFIRM)

    def test_cache_exact(self):
        r=req(); a=self.c.evaluate(r); b=self.c.evaluate(r)
        self.assertFalse(a.cache_reused); self.assertTrue(b.cache_reused)
    def test_cache_never_tool_call(self):
        r=req(); self.c.evaluate(r); self.assertFalse(self.c.evaluate(r).tool_called)
    def test_cache_never_authority(self):
        r=req(); self.c.evaluate(r); self.assertFalse(self.c.evaluate(r).authoritative)
    def test_revocation_changes_fingerprint(self):
        self.assertNotEqual(self.c.fingerprint(req()),self.c.fingerprint(req(permit=permit(revoked=True))))
    def test_expiry_changes_fingerprint(self):
        self.assertNotEqual(self.c.fingerprint(req()),self.c.fingerprint(req(permit=permit(expires_at_epoch_s=3000))))
    def test_scope_changes_fingerprint(self):
        self.assertNotEqual(self.c.fingerprint(req()),self.c.fingerprint(req(required_scope="project/other")))
    def test_operation_changes_fingerprint(self):
        self.assertNotEqual(self.c.fingerprint(req()),self.c.fingerprint(req(operation="write")))
    def test_context_order(self):
        self.assertEqual(self.c.fingerprint(req(context={"b":2,"a":1})),self.c.fingerprint(req(context={"a":1,"b":2})))
    def test_clear_cache(self):
        self.c.evaluate(req()); self.assertGreater(self.c.cache_size(),0); self.c.clear_cache(); self.assertEqual(self.c.cache_size(),0)
    def test_stable_no_time(self):
        self.assertNotIn("created_unix_ns",self.c.evaluate(req()).stable_payload())
    def test_allow_prepare_not_success(self):
        o=self.check(req(),ToolDecision.ALLOW_PREPARE); self.assertFalse(o.action_succeeded)

    def test_many_valid(self):
        for i in range(10):
            p=permit(permit_id=f"p{i}")
            self.check(req(request_id=f"r{i}",permit=p),ToolDecision.ALLOW_PREPARE)

def replay_fingerprint():
    c=ToolPermissionController(policy()); out=[]
    for i in range(1000):
        tool="read_file" if i%2==0 else "write_file"
        op="read" if tool=="read_file" else "write"
        p=ToolPermit(
            permit_id=f"p{i%19}",agent_id=f"a{i%7}",server_id="mcp:files",tool_name=tool,
            operations=(op,"delete"),scopes=("project",),expires_at_epoch_s=5000,
            permit_version=1+(i%3),issuer_ref="auth",revoked=(i%31==0)
        )
        r=ToolRequest(
            request_id=f"r{i}",agent_id=p.agent_id,server_id="mcp:files",tool_name=tool,
            operation="delete" if i%11==0 else op,required_scope=f"project/f{i%13}",
            observed_epoch_s=1000+(i%100),risk_score=i%50,permit=p,
            expected_permit_version=p.permit_version,oauth_authenticated=(i%2==0),
            oidc_authenticated=(i%3==0),external_side_effect=(i%17==0),
            human_approved=(i%5==0),approval_ref="H" if i%5==0 else None
        )
        out.append(c.evaluate(r).stable_payload())
    raw=json.dumps(out,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

if __name__=="__main__":
    unittest.main()
