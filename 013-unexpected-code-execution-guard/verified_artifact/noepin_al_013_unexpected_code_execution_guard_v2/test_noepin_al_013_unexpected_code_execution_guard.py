import hashlib, json, unittest
from noepin_al_013_unexpected_code_execution_guard import *

H0="0"*64
H1="1"*64

def policy():
    return ExecutionPolicy(
        allowed_action_types=("FILE","PROCESS","NETWORK","TRANSFORM"),
        allowed_operations=("read","write","spawn","http_get","transform"),
        allowed_capabilities=("fs.read","fs.write","process.spawn","net.http"),
        policy_version="v2"
    )

def action(**kw):
    d=dict(action_type="FILE",operation="read",target="project/a.txt",args_fingerprint=H0,code_sha256=None,
           requested_capabilities=("fs.read",),sandbox_required=True,sandbox_id="sb1",origin=OriginKind.GENERATED,
           raw_shell_requested=False,dynamic_eval_requested=False,process_spawn_requested=False,network_requested=False,
           filesystem_write_requested=False,protected_target=False,external_side_effect=False,risk_score=5,
           schema_version="1",metadata={})
    d.update(kw); return TypedAction(**d)

def req(**kw):
    d=dict(request_id="r1",actor_id="ai",action=action(),human_approved=False,approval_ref=None,
           capability_authorized=True,authorization_ref="cap1",observed_policy_version="v2",schema_version="1",context={})
    d.update(kw); return ExecutionRequest(**d)

class T(unittest.TestCase):
    def setUp(self): self.g=UnexpectedCodeExecutionGuard(policy())
    def check(self,r,d):
        o=self.g.evaluate(r); self.assertEqual(o.decision,d)
        self.assertFalse(o.authoritative); self.assertFalse(o.code_executed)
        self.assertFalse(o.action_succeeded); self.assertFalse(o.state_committed); return o

    def test_allow(self): self.check(req(),ExecutionDecision.ALLOW_PREPARE)
    def test_missing_request(self): self.check(req(request_id=""),ExecutionDecision.HOLD)
    def test_missing_actor(self): self.check(req(actor_id=""),ExecutionDecision.HOLD)
    def test_missing_schema(self): self.check(req(schema_version=""),ExecutionDecision.HOLD)
    def test_policy_mismatch(self): self.check(req(observed_policy_version="old"),ExecutionDecision.HOLD)
    def test_missing_action_type(self): self.check(req(action=action(action_type="")),ExecutionDecision.HOLD)
    def test_missing_operation(self): self.check(req(action=action(operation="")),ExecutionDecision.HOLD)
    def test_missing_target(self): self.check(req(action=action(target="")),ExecutionDecision.HOLD)
    def test_bad_args_hash(self): self.check(req(action=action(args_fingerprint="bad")),ExecutionDecision.HOLD)
    def test_bad_code_hash(self): self.check(req(action=action(code_sha256="bad")),ExecutionDecision.HOLD)
    def test_bad_risk(self): self.check(req(action=action(risk_score=101)),ExecutionDecision.HOLD)
    def test_bool_risk(self): self.check(req(action=action(risk_score=True)),ExecutionDecision.HOLD)

    def test_action_type_not_allowlisted(self): self.check(req(action=action(action_type="SHELL")),ExecutionDecision.DENY)
    def test_forbidden_operation(self): self.check(req(action=action(operation="eval")),ExecutionDecision.DENY)
    def test_operation_not_allowlisted(self): self.check(req(action=action(operation="chmod")),ExecutionDecision.DENY)
    def test_protected_target(self): self.check(req(action=action(protected_target=True)),ExecutionDecision.DENY)
    def test_raw_shell_denied(self): self.check(req(action=action(raw_shell_requested=True)),ExecutionDecision.DENY)
    def test_dynamic_eval_denied(self): self.check(req(action=action(dynamic_eval_requested=True)),ExecutionDecision.DENY)

    def test_capability_not_allowlisted(self):
        self.check(req(action=action(requested_capabilities=("root",))),ExecutionDecision.DENY)
    def test_capability_authorization_required(self):
        self.check(req(capability_authorized=False,authorization_ref=None),ExecutionDecision.HOLD)
    def test_capability_bool_only_not_enough(self):
        self.check(req(capability_authorized=True,authorization_ref=None),ExecutionDecision.HOLD)
    def test_no_capability_no_auth_needed(self):
        self.check(req(action=action(requested_capabilities=()),capability_authorized=False,authorization_ref=None),ExecutionDecision.ALLOW_PREPARE)

    def test_generated_requires_sandbox(self):
        self.check(req(action=action(sandbox_id=None)),ExecutionDecision.HOLD)
    def test_generated_sandbox_flag_required(self):
        self.check(req(action=action(sandbox_required=False)),ExecutionDecision.HOLD)
    def test_user_origin_no_sandbox_required(self):
        self.check(req(action=action(origin=OriginKind.USER,sandbox_required=False,sandbox_id=None)),ExecutionDecision.ALLOW_PREPARE)
    def test_web_origin_requires_sandbox(self):
        self.check(req(action=action(origin=OriginKind.WEB,sandbox_id=None)),ExecutionDecision.HOLD)
    def test_external_ai_requires_sandbox(self):
        self.check(req(action=action(origin=OriginKind.EXTERNAL_AI,sandbox_id=None)),ExecutionDecision.HOLD)

    def test_process_spawn_confirm(self):
        a=action(action_type="PROCESS",operation="spawn",requested_capabilities=("process.spawn",),process_spawn_requested=True)
        self.check(req(action=a),ExecutionDecision.HUMAN_CONFIRM)
    def test_process_spawn_approved(self):
        a=action(action_type="PROCESS",operation="spawn",requested_capabilities=("process.spawn",),process_spawn_requested=True)
        self.check(req(action=a,human_approved=True,approval_ref="H"),ExecutionDecision.ALLOW_PREPARE)
    def test_network_confirm(self):
        a=action(action_type="NETWORK",operation="http_get",requested_capabilities=("net.http",),network_requested=True)
        self.check(req(action=a),ExecutionDecision.HUMAN_CONFIRM)
    def test_network_approved(self):
        a=action(action_type="NETWORK",operation="http_get",requested_capabilities=("net.http",),network_requested=True)
        self.check(req(action=a,human_approved=True,approval_ref="H"),ExecutionDecision.ALLOW_PREPARE)
    def test_write_confirm(self):
        a=action(operation="write",requested_capabilities=("fs.write",),filesystem_write_requested=True)
        self.check(req(action=a),ExecutionDecision.HUMAN_CONFIRM)
    def test_write_approved(self):
        a=action(operation="write",requested_capabilities=("fs.write",),filesystem_write_requested=True)
        self.check(req(action=a,human_approved=True,approval_ref="H"),ExecutionDecision.ALLOW_PREPARE)
    def test_external_side_effect_confirm(self):
        self.check(req(action=action(external_side_effect=True)),ExecutionDecision.HUMAN_CONFIRM)
    def test_risk_boundary_35_allow(self): self.check(req(action=action(risk_score=35)),ExecutionDecision.ALLOW_PREPARE)
    def test_risk_36_confirm(self): self.check(req(action=action(risk_score=36)),ExecutionDecision.HUMAN_CONFIRM)
    def test_approval_bool_only(self): self.check(req(action=action(risk_score=36),human_approved=True),ExecutionDecision.HUMAN_CONFIRM)

    def test_cache_exact(self):
        r=req(); a=self.g.evaluate(r); b=self.g.evaluate(r); self.assertFalse(a.cache_reused); self.assertTrue(b.cache_reused)
    def test_cache_never_execute(self):
        r=req(); self.g.evaluate(r); self.assertFalse(self.g.evaluate(r).code_executed)
    def test_cache_never_success(self):
        r=req(); self.g.evaluate(r); self.assertFalse(self.g.evaluate(r).action_succeeded)
    def test_cache_cap_auth_diff(self):
        self.assertNotEqual(self.g.fingerprint(req()),self.g.fingerprint(req(capability_authorized=False)))
    def test_cache_sandbox_diff(self):
        self.assertNotEqual(self.g.fingerprint(req()),self.g.fingerprint(req(action=action(sandbox_id="sb2"))))
    def test_cache_risk_diff(self):
        self.assertNotEqual(self.g.fingerprint(req()),self.g.fingerprint(req(action=action(risk_score=36))))
    def test_context_order(self):
        self.assertEqual(self.g.fingerprint(req(context={"b":2,"a":1})),self.g.fingerprint(req(context={"a":1,"b":2})))
    def test_clear_cache(self):
        self.g.evaluate(req()); self.assertGreater(self.g.cache_size(),0); self.g.clear_cache(); self.assertEqual(self.g.cache_size(),0)
    def test_stable_no_time(self): self.assertNotIn("created_unix_ns",self.g.evaluate(req()).stable_payload())
    def test_allow_prepare_not_execution(self):
        o=self.check(req(),ExecutionDecision.ALLOW_PREPARE); self.assertTrue(o.typed_action_valid); self.assertFalse(o.code_executed)

    def test_code_hash_is_evidence_only(self):
        o=self.check(req(action=action(code_sha256=H1)),ExecutionDecision.ALLOW_PREPARE)
        self.assertFalse(o.authoritative)
    def test_sandbox_selection_not_execution(self):
        o=self.check(req(),ExecutionDecision.ALLOW_PREPARE); self.assertTrue(o.sandbox_validated); self.assertFalse(o.state_committed)
    def test_many_valid_reads(self):
        for i in range(10):
            self.check(req(request_id=f"r{i}",action=action(target=f"project/{i}.txt",args_fingerprint=f"{i:x}".rjust(64,"0"))),ExecutionDecision.ALLOW_PREPARE)

def replay_fingerprint():
    g=UnexpectedCodeExecutionGuard(policy()); out=[]
    origins=list(OriginKind)
    for i in range(1000):
        mode=i%4
        if mode==0:
            a=action(origin=origins[i%len(origins)],risk_score=i%36)
        elif mode==1:
            a=action(action_type="PROCESS",operation="spawn",requested_capabilities=("process.spawn",),process_spawn_requested=True,risk_score=i%50)
        elif mode==2:
            a=action(action_type="NETWORK",operation="http_get",requested_capabilities=("net.http",),network_requested=True,risk_score=i%50)
        else:
            a=action(operation="write",requested_capabilities=("fs.write",),filesystem_write_requested=True,risk_score=i%50)
        r=ExecutionRequest(request_id=f"r{i}",actor_id="ai",action=a,
            human_approved=(i%5==0),approval_ref="H" if i%5==0 else None,
            capability_authorized=True,authorization_ref="CAP",observed_policy_version="v2")
        out.append(g.evaluate(r).stable_payload())
    raw=json.dumps(out,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

if __name__=="__main__": unittest.main()
