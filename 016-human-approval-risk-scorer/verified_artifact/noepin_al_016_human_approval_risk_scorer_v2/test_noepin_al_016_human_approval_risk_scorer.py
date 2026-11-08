import hashlib, json, unittest
from noepin_al_016_human_approval_risk_scorer import *

H0="0"*64

def policy():
    return RiskPolicy(
        human_threshold=40, deny_threshold=90,
        amount_human_threshold=10000, amount_deny_threshold=1000000,
        large_scope_threshold=100, max_uncertainty_without_hold=60,
        policy_version="v2"
    )

def req(**kw):
    d=dict(
        request_id="r1", actor_id="a1", operation=OperationKind.READ,
        target_id="resource:1", target_version="v1",
        evidence_fingerprint=H0, evidence_version=1,
        amount=0, items_affected=1, destructive=False, public_effect=False,
        privilege_change=False, external_side_effect=False, irreversible=False,
        production=False, sensitive_data=False, critical_resource=False,
        uncertainty=0, reversibility=100, human_approved=False,
        approval_ref=None, schema_version="1", context={}
    )
    d.update(kw); return RiskRequest(**d)

class T(unittest.TestCase):
    def setUp(self): self.s=HumanApprovalRiskScorer(policy())
    def check(self,r,d):
        o=self.s.evaluate(r); self.assertEqual(o.decision,d)
        self.assertFalse(o.authoritative); self.assertFalse(o.approval_granted)
        self.assertFalse(o.action_executed); self.assertFalse(o.action_succeeded); self.assertFalse(o.state_committed)
        return o

    def test_read_low(self): self.check(req(),RiskDecision.LOW_RISK_CANDIDATE)
    def test_missing_request(self): self.check(req(request_id=""),RiskDecision.HOLD)
    def test_missing_actor(self): self.check(req(actor_id=""),RiskDecision.HOLD)
    def test_missing_target(self): self.check(req(target_id=""),RiskDecision.HOLD)
    def test_missing_target_version(self): self.check(req(target_version=""),RiskDecision.HOLD)
    def test_missing_schema(self): self.check(req(schema_version=""),RiskDecision.HOLD)
    def test_bad_hash(self): self.check(req(evidence_fingerprint="bad"),RiskDecision.HOLD)
    def test_bad_evidence_version(self): self.check(req(evidence_version=0),RiskDecision.HOLD)
    def test_bool_evidence_version(self): self.check(req(evidence_version=True),RiskDecision.HOLD)
    def test_bad_amount(self): self.check(req(amount=-1),RiskDecision.HOLD)
    def test_bool_amount(self): self.check(req(amount=True),RiskDecision.HOLD)
    def test_bad_items(self): self.check(req(items_affected=0),RiskDecision.HOLD)
    def test_bad_uncertainty(self): self.check(req(uncertainty=-1),RiskDecision.HOLD)
    def test_uncertainty_over_100(self): self.check(req(uncertainty=101),RiskDecision.HOLD)
    def test_bad_reversibility(self): self.check(req(reversibility=-1),RiskDecision.HOLD)
    def test_reversibility_over_100(self): self.check(req(reversibility=101),RiskDecision.HOLD)
    def test_uncertainty_over_policy_hold(self): self.check(req(uncertainty=61),RiskDecision.HOLD)
    def test_uncertainty_boundary(self):
        o=self.check(req(uncertainty=60),RiskDecision.LOW_RISK_CANDIDATE); self.assertLess(o.risk_score,40)

    def test_write_low(self): self.check(req(operation=OperationKind.WRITE),RiskDecision.LOW_RISK_CANDIDATE)
    def test_delete_human(self): self.check(req(operation=OperationKind.DELETE),RiskDecision.HUMAN_CONFIRM)
    def test_publish_human(self): self.check(req(operation=OperationKind.PUBLISH),RiskDecision.HUMAN_CONFIRM)
    def test_privilege_op_human(self): self.check(req(operation=OperationKind.PRIVILEGE_CHANGE),RiskDecision.HUMAN_CONFIRM)
    def test_purchase_human(self): self.check(req(operation=OperationKind.PURCHASE),RiskDecision.HUMAN_CONFIRM)
    def test_external_send_human(self): self.check(req(operation=OperationKind.EXTERNAL_SEND),RiskDecision.HUMAN_CONFIRM)
    def test_execute_human(self): self.check(req(operation=OperationKind.EXECUTE),RiskDecision.HUMAN_CONFIRM)
    def test_config_change_low(self): self.check(req(operation=OperationKind.CONFIG_CHANGE),RiskDecision.LOW_RISK_CANDIDATE)

    def test_destructive_human(self): self.check(req(destructive=True),RiskDecision.HUMAN_CONFIRM)
    def test_public_human(self): self.check(req(public_effect=True),RiskDecision.HUMAN_CONFIRM)
    def test_privilege_flag_human(self): self.check(req(privilege_change=True),RiskDecision.HUMAN_CONFIRM)
    def test_external_flag_human(self): self.check(req(external_side_effect=True),RiskDecision.HUMAN_CONFIRM)
    def test_irreversible_human(self): self.check(req(irreversible=True),RiskDecision.HUMAN_CONFIRM)
    def test_production_human(self): self.check(req(production=True),RiskDecision.HUMAN_CONFIRM)
    def test_sensitive_human(self): self.check(req(sensitive_data=True),RiskDecision.HUMAN_CONFIRM)
    def test_critical_human(self): self.check(req(critical_resource=True),RiskDecision.HUMAN_CONFIRM)

    def test_amount_small_low(self): self.check(req(amount=1),RiskDecision.LOW_RISK_CANDIDATE)
    def test_amount_threshold_low_score_but_human_by_score(self):
        # 25 alone stays below threshold, so monetary threshold is evidence but not hard-human unless aggregate crosses.
        self.check(req(amount=10000),RiskDecision.LOW_RISK_CANDIDATE)
    def test_amount_high_plus_write_human(self): self.check(req(amount=10000,operation=OperationKind.WRITE),RiskDecision.LOW_RISK_CANDIDATE)
    def test_amount_very_high_deny(self): self.check(req(amount=1000000,operation=OperationKind.PRIVILEGE_CHANGE),RiskDecision.DENY)

    def test_large_scope(self): self.check(req(items_affected=100,operation=OperationKind.WRITE),RiskDecision.LOW_RISK_CANDIDATE)
    def test_many_scope_plus_public_human(self): self.check(req(items_affected=100,public_effect=True),RiskDecision.HUMAN_CONFIRM)
    def test_low_reversibility(self): self.check(req(reversibility=0,operation=OperationKind.WRITE),RiskDecision.LOW_RISK_CANDIDATE)
    def test_low_reversibility_plus_destructive_human(self): self.check(req(reversibility=0,destructive=True),RiskDecision.HUMAN_CONFIRM)

    def test_approval_evidence_not_grant(self):
        o=self.check(req(destructive=True,human_approved=True,approval_ref="H"),RiskDecision.HUMAN_CONFIRM)
        self.assertFalse(o.approval_granted); self.assertFalse(o.action_executed)
    def test_approval_bool_without_ref(self): self.check(req(destructive=True,human_approved=True),RiskDecision.HUMAN_CONFIRM)
    def test_approval_ref_without_bool(self): self.check(req(destructive=True,approval_ref="H"),RiskDecision.HUMAN_CONFIRM)

    def test_extreme_combo_deny(self):
        self.check(req(operation=OperationKind.DELETE,destructive=True,public_effect=True,production=True,critical_resource=True),RiskDecision.DENY)
    def test_extreme_approval_still_deny(self):
        self.check(req(operation=OperationKind.DELETE,destructive=True,public_effect=True,production=True,critical_resource=True,human_approved=True,approval_ref="H"),RiskDecision.DENY)

    def test_cache_exact(self):
        r=req(); a=self.s.evaluate(r); b=self.s.evaluate(r); self.assertFalse(a.cache_reused); self.assertTrue(b.cache_reused)
    def test_cache_no_authority(self):
        r=req(); self.s.evaluate(r); self.assertFalse(self.s.evaluate(r).authoritative)
    def test_cache_no_approval(self):
        r=req(); self.s.evaluate(r); self.assertFalse(self.s.evaluate(r).approval_granted)
    def test_evidence_version_changes_fingerprint(self):
        self.assertNotEqual(self.s.fingerprint(req()),self.s.fingerprint(req(evidence_version=2)))
    def test_target_version_changes_fingerprint(self):
        self.assertNotEqual(self.s.fingerprint(req()),self.s.fingerprint(req(target_version="v2")))
    def test_evidence_hash_changes_fingerprint(self):
        self.assertNotEqual(self.s.fingerprint(req()),self.s.fingerprint(req(evidence_fingerprint="1"*64)))
    def test_approval_changes_fingerprint(self):
        self.assertNotEqual(self.s.fingerprint(req()),self.s.fingerprint(req(human_approved=True,approval_ref="H")))
    def test_context_order(self):
        self.assertEqual(self.s.fingerprint(req(context={"b":2,"a":1})),self.s.fingerprint(req(context={"a":1,"b":2})))
    def test_clear_cache(self):
        self.s.evaluate(req()); self.assertGreater(self.s.cache_size(),0); self.s.clear_cache(); self.assertEqual(self.s.cache_size(),0)
    def test_stable_no_time(self): self.assertNotIn("created_unix_ns",self.s.evaluate(req()).stable_payload())
    def test_low_risk_not_authorization(self):
        o=self.check(req(),RiskDecision.LOW_RISK_CANDIDATE); self.assertFalse(o.authoritative); self.assertFalse(o.action_succeeded)

def replay_fingerprint():
    s=HumanApprovalRiskScorer(policy()); out=[]
    ops=list(OperationKind)
    for i in range(1000):
        r=RiskRequest(
            request_id=f"r{i}", actor_id=f"a{i%7}", operation=ops[i%len(ops)],
            target_id=f"t{i%19}", target_version=f"v{1+i%3}",
            evidence_fingerprint=f"{i:x}".rjust(64,"0"), evidence_version=1+(i%4),
            amount=(i%5)*5000, items_affected=1+(i%150),
            destructive=(i%11==0), public_effect=(i%13==0),
            privilege_change=(i%17==0), external_side_effect=(i%19==0),
            irreversible=(i%23==0), production=(i%7==0),
            sensitive_data=(i%29==0), critical_resource=(i%31==0),
            uncertainty=i%61, reversibility=100-(i%101),
            human_approved=(i%6==0), approval_ref="H" if i%6==0 else None,
        )
        out.append(s.evaluate(r).stable_payload())
    raw=json.dumps(out,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

if __name__=="__main__":
    unittest.main()
