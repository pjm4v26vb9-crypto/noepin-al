import hashlib, json, unittest
from noepin_al_017_rogue_ai_kill_switch import *

H0="0"*64

def policy(): return KillPolicy(policy_version="v2")
def snap(**kw):
    d=dict(agent_id="a1",authority_version=1,permit_version=1,revoked=False,network_allowed=True,tools_allowed=True,process_allowed=True,safe_state_required=False)
    d.update(kw); return AgentAuthoritySnapshot(**d)
def req(**kw):
    d=dict(request_id="r1",snapshot=snap(),observed_authority_version=1,observed_permit_version=1,
           policy_violation_score=0,anomaly_score=0,evidence_fingerprint=H0,evidence_version=1,schema_version="1",context={})
    d.update(kw); return KillRequest(**d)

class T(unittest.TestCase):
    def setUp(self): self.k=RogueAIKillSwitch(policy())
    def check(self,r,d):
        o=self.k.evaluate(r); self.assertEqual(o.decision,d)
        self.assertFalse(o.authoritative); self.assertFalse(o.permissions_revoked); self.assertFalse(o.network_quarantined)
        self.assertFalse(o.tools_disabled); self.assertFalse(o.process_stopped); self.assertFalse(o.safe_state_reached)
        self.assertFalse(o.action_executed); self.assertFalse(o.action_succeeded); return o
    def test_continue(self): self.check(req(),KillDecision.CONTINUE)
    def test_missing_request(self): self.check(req(request_id=""),KillDecision.HOLD)
    def test_missing_schema(self): self.check(req(schema_version=""),KillDecision.HOLD)
    def test_missing_agent(self): self.check(req(snapshot=snap(agent_id="")),KillDecision.HOLD)
    def test_bad_auth_version(self): self.check(req(snapshot=snap(authority_version=0)),KillDecision.HOLD)
    def test_bad_permit_version(self): self.check(req(snapshot=snap(permit_version=0)),KillDecision.HOLD)
    def test_bad_observed_auth(self): self.check(req(observed_authority_version=0),KillDecision.HOLD)
    def test_bad_observed_permit(self): self.check(req(observed_permit_version=0),KillDecision.HOLD)
    def test_auth_mismatch(self): self.check(req(observed_authority_version=2),KillDecision.HOLD)
    def test_permit_mismatch(self): self.check(req(observed_permit_version=2),KillDecision.HOLD)
    def test_bad_policy_score(self): self.check(req(policy_violation_score=101),KillDecision.HOLD)
    def test_bad_anomaly_score(self): self.check(req(anomaly_score=-1),KillDecision.HOLD)
    def test_bool_score(self): self.check(req(anomaly_score=True),KillDecision.HOLD)
    def test_bad_hash(self): self.check(req(evidence_fingerprint="bad"),KillDecision.HOLD)
    def test_bad_evidence_version(self): self.check(req(evidence_version=0),KillDecision.HOLD)
    def test_emergency(self):
        o=self.check(req(emergency_stop_active=True),KillDecision.CONTAIN_PREPARE); self.assertTrue(o.plan.revoke_permissions)
    def test_revoked_snapshot(self): self.check(req(snapshot=snap(revoked=True)),KillDecision.CONTAIN_PREPARE)
    def test_scope_expansion(self): self.check(req(unauthorized_scope_expansion=True),KillDecision.CONTAIN_PREPARE)
    def test_network_attempt(self): self.check(req(unauthorized_network_attempt=True),KillDecision.CONTAIN_PREPARE)
    def test_tool_attempt(self): self.check(req(unauthorized_tool_attempt=True),KillDecision.CONTAIN_PREPARE)
    def test_process_attempt(self): self.check(req(unauthorized_process_attempt=True),KillDecision.CONTAIN_PREPARE)
    def test_guard_bypass(self): self.check(req(repeated_guard_bypass_attempt=True),KillDecision.CONTAIN_PREPARE)
    def test_hard_policy_threshold(self): self.check(req(policy_violation_score=80),KillDecision.CONTAIN_PREPARE)
    def test_hard_policy_below(self): self.check(req(policy_violation_score=79),KillDecision.HUMAN_CONFIRM)
    def test_anomaly_threshold(self): self.check(req(anomaly_score=70),KillDecision.CONTAIN_PREPARE)
    def test_anomaly_below(self): self.check(req(anomaly_score=69),KillDecision.CONTINUE)
    def test_soft_threshold(self): self.check(req(policy_violation_score=45),KillDecision.HUMAN_CONFIRM)
    def test_soft_below(self): self.check(req(policy_violation_score=44),KillDecision.CONTINUE)
    def test_soft_approved(self): self.check(req(policy_violation_score=45,human_approved=True,approval_ref="H"),KillDecision.CONTAIN_PREPARE)
    def test_soft_bool_only(self): self.check(req(policy_violation_score=45,human_approved=True),KillDecision.HUMAN_CONFIRM)
    def test_soft_ref_only(self): self.check(req(policy_violation_score=45,approval_ref="H"),KillDecision.HUMAN_CONFIRM)
    def test_emergency_ignores_approval(self): self.check(req(emergency_stop_active=True,human_approved=False),KillDecision.CONTAIN_PREPARE)
    def test_plan_all_true_on_contain(self):
        p=self.check(req(unauthorized_tool_attempt=True),KillDecision.CONTAIN_PREPARE).plan
        self.assertTrue(all(asdict(p).values()))
    def test_plan_all_false_on_continue(self):
        p=self.check(req(),KillDecision.CONTINUE).plan
        self.assertFalse(any(asdict(p).values()))
    def test_cache_exact(self):
        r=req(); a=self.k.evaluate(r); b=self.k.evaluate(r); self.assertFalse(a.cache_reused); self.assertTrue(b.cache_reused)
    def test_cache_no_success(self):
        r=req(); self.k.evaluate(r); self.assertFalse(self.k.evaluate(r).action_succeeded)
    def test_cache_no_revocation(self):
        r=req(); self.k.evaluate(r); self.assertFalse(self.k.evaluate(r).permissions_revoked)
    def test_cache_diff_authority_version(self):
        self.assertNotEqual(self.k.fingerprint(req()), self.k.fingerprint(req(snapshot=snap(authority_version=2),observed_authority_version=2)))
    def test_cache_diff_permit_version(self):
        self.assertNotEqual(self.k.fingerprint(req()), self.k.fingerprint(req(snapshot=snap(permit_version=2),observed_permit_version=2)))
    def test_cache_diff_evidence_version(self): self.assertNotEqual(self.k.fingerprint(req()),self.k.fingerprint(req(evidence_version=2)))
    def test_cache_diff_hash(self): self.assertNotEqual(self.k.fingerprint(req()),self.k.fingerprint(req(evidence_fingerprint="1"*64)))
    def test_context_order(self): self.assertEqual(self.k.fingerprint(req(context={"b":2,"a":1})),self.k.fingerprint(req(context={"a":1,"b":2})))
    def test_clear_cache(self): self.k.evaluate(req()); self.assertGreater(self.k.cache_size(),0); self.k.clear_cache(); self.assertEqual(self.k.cache_size(),0)
    def test_stable_no_time(self): self.assertNotIn("created_unix_ns",self.k.evaluate(req()).stable_payload())
    def test_emergency_bypasses_cached_continue(self):
        self.assertEqual(self.k.evaluate(req()).decision,KillDecision.CONTINUE)
        o=self.k.evaluate(req(emergency_stop_active=True)); self.assertEqual(o.decision,KillDecision.CONTAIN_PREPARE); self.assertFalse(o.cache_reused)
    def test_revocation_bypasses_cache(self):
        self.k.evaluate(req()); o=self.k.evaluate(req(snapshot=snap(revoked=True))); self.assertEqual(o.decision,KillDecision.CONTAIN_PREPARE); self.assertFalse(o.cache_reused)
    def test_contain_not_actual_stop(self):
        o=self.check(req(unauthorized_process_attempt=True),KillDecision.CONTAIN_PREPARE); self.assertFalse(o.process_stopped)
    def test_contain_not_safe_state(self):
        o=self.check(req(unauthorized_scope_expansion=True),KillDecision.CONTAIN_PREPARE); self.assertFalse(o.safe_state_reached)
    def test_contain_not_network_closed(self):
        o=self.check(req(unauthorized_network_attempt=True),KillDecision.CONTAIN_PREPARE); self.assertFalse(o.network_quarantined)
    def test_many_continue(self):
        for i in range(10): self.check(req(request_id=f"r{i}",policy_violation_score=i,anomaly_score=i),KillDecision.CONTINUE)

def replay_fingerprint():
    k=RogueAIKillSwitch(policy()); out=[]
    for i in range(1000):
        s=snap(authority_version=1+(i%3),permit_version=1+(i%4),revoked=(i%97==0))
        r=KillRequest(request_id=f"r{i}",snapshot=s,observed_authority_version=s.authority_version,observed_permit_version=s.permit_version,
            policy_violation_score=i%90,anomaly_score=(i*3)%100,unauthorized_scope_expansion=(i%41==0),
            unauthorized_network_attempt=(i%43==0),unauthorized_tool_attempt=(i%47==0),unauthorized_process_attempt=(i%53==0),
            repeated_guard_bypass_attempt=(i%59==0),emergency_stop_active=(i%101==0),human_approved=(i%5==0),approval_ref="H" if i%5==0 else None,
            evidence_fingerprint=f"{i:x}".rjust(64,"0"),evidence_version=1+(i%5),context={"bucket":i%13})
        out.append(k.evaluate(r).stable_payload())
    raw=json.dumps(out,sort_keys=True,separators=(",",":")).encode(); return hashlib.sha256(raw).hexdigest()

if __name__=="__main__": unittest.main()
