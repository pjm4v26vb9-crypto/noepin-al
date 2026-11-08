from __future__ import annotations
import ast, dataclasses, unittest
from pathlib import Path
import noepin_al_047_risk_budget as m

NOW=1_800_000_000

def policy(**kw):
    p=m.default_policy(NOW)
    return dataclasses.replace(p,**kw)

def req(**kw):
    r=m.default_request(NOW)
    return dataclasses.replace(r,**kw)

def ent(eid="E1", task="TASK-047", risk=100, impact=80, occurred=None, expires=None, revoked=False,
        operation="LOCAL_TEST", scope="artifact", binding="BIND-047", **kw):
    p=policy()
    e=m.RiskLedgerEntry(eid,task,operation,scope,risk,impact,NOW-100 if occurred is None else occurred,
        NOW+10000 if expires is None else expires,revoked,p.policy_id,p.version,p.authority_epoch,binding)
    return dataclasses.replace(e,**kw)

class RiskBudgetTests(unittest.TestCase):
    def test_default_allow(self):
        out=m.evaluate(req(),policy(),m.default_entries(NOW),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.ALLOW)
        self.assertFalse(out.permission_granted or out.action_executed or out.stop_executed or out.commit_performed or out.action_success or out.risk_truth_proven)

    def test_cumulative_risk_warning(self):
        es=(ent("E1",risk=400),ent("E2",risk=350,occurred=NOW-90))
        out=m.evaluate(req(candidate_risk_units=60),policy(),es,now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.HUMAN_APPROVAL); self.assertTrue(out.budget_warning_candidate)

    def test_total_risk_exceeded_deny(self):
        es=(ent("E1",risk=500),ent("E2",risk=450,occurred=NOW-90))
        out=m.evaluate(req(candidate_risk_units=60),policy(),es,now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.DENY); self.assertTrue(out.stop_candidate and out.budget_exhausted_candidate); self.assertFalse(out.stop_executed)

    def test_total_impact_exceeded(self):
        es=(ent("E1",risk=100,impact=600),ent("E2",risk=100,impact=550,occurred=NOW-90))
        out=m.evaluate(req(candidate_risk_units=20,candidate_impact_units=100),policy(),es,now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.DENY); self.assertIn("TOTAL_IMPACT_BUDGET_EXCEEDED",out.reasons)

    def test_single_risk_limit(self):
        out=m.evaluate(req(candidate_risk_units=301),policy(),(),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.DENY); self.assertIn("SINGLE_ACTION_RISK_LIMIT_EXCEEDED",out.reasons)

    def test_action_count_limit(self):
        es=tuple(ent(f"E{i}",risk=10,impact=10,occurred=NOW-1000+i) for i in range(20))
        out=m.evaluate(req(candidate_risk_units=1,candidate_impact_units=1),policy(),es,now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.DENY); self.assertIn("ACTION_COUNT_BUDGET_EXCEEDED",out.reasons)

    def test_count_warning_at_penultimate(self):
        es=tuple(ent(f"E{i}",risk=10,impact=10,occurred=NOW-1000+i) for i in range(18))
        out=m.evaluate(req(candidate_risk_units=1,candidate_impact_units=1),policy(),es,now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.HUMAN_APPROVAL)

    def test_consecutive_high_risk_limit(self):
        es=(ent("E1",risk=220,occurred=NOW-30),ent("E2",risk=220,occurred=NOW-20))
        out=m.evaluate(req(candidate_risk_units=220),policy(),es,now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.DENY); self.assertIn("CONSECUTIVE_HIGH_RISK_LIMIT_EXCEEDED",out.reasons)

    def test_old_low_resets_consecutive(self):
        es=(ent("E1",risk=220,occurred=NOW-30),ent("E2",risk=20,occurred=NOW-20))
        out=m.evaluate(req(candidate_risk_units=220),policy(),es,now=NOW)
        self.assertNotIn("CONSECUTIVE_HIGH_RISK_LIMIT_EXCEEDED",out.reasons)

    def test_expired_entry_ignored(self):
        e=ent("E1",risk=900,occurred=NOW-1000,expires=NOW-1)
        out=m.evaluate(req(candidate_risk_units=10,candidate_impact_units=10),policy(),(e,),now=NOW)
        self.assertEqual(out.used_risk_units,0); self.assertIn("E1",out.ignored_entry_ids)

    def test_revoked_entry_ignored(self):
        e=ent("E1",risk=900,revoked=True)
        out=m.evaluate(req(candidate_risk_units=10,candidate_impact_units=10),policy(),(e,),now=NOW)
        self.assertEqual(out.used_risk_units,0); self.assertIn("E1",out.ignored_entry_ids)

    def test_other_task_not_counted(self):
        out=m.evaluate(req(),policy(),(ent("E1",task="OTHER",risk=900),),now=NOW)
        self.assertEqual(out.used_risk_units,0)

    def test_binding_mismatch_ignored(self):
        out=m.evaluate(req(),policy(),(ent("E1",risk=900,binding="OTHER"),),now=NOW)
        self.assertEqual(out.used_risk_units,0); self.assertIn("E1",out.ignored_entry_ids)

    def test_entry_policy_version_mismatch_ignored(self):
        out=m.evaluate(req(),policy(),(ent("E1",risk=900,policy_version="OLD"),),now=NOW)
        self.assertEqual(out.used_risk_units,0)

    def test_entry_epoch_mismatch_ignored(self):
        out=m.evaluate(req(),policy(),(ent("E1",risk=900,authority_epoch=2),),now=NOW)
        self.assertEqual(out.used_risk_units,0)

    def test_policy_id_mismatch_holds(self):
        out=m.evaluate(req(expected_policy_id="WRONG"),policy(),(),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.HOLD)

    def test_policy_version_mismatch_holds(self):
        out=m.evaluate(req(expected_policy_version="OLD"),policy(),(),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.HOLD)

    def test_policy_epoch_mismatch_holds(self):
        out=m.evaluate(req(expected_authority_epoch=2),policy(),(),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.HOLD)

    def test_revoked_policy_holds(self):
        out=m.evaluate(req(),policy(revoked=True),(),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.HOLD)

    def test_expired_policy_holds(self):
        p=policy(expires_at=NOW)
        out=m.evaluate(req(),p,(),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.HOLD)

    def test_future_policy_holds(self):
        p=policy(issued_at=NOW+1,expires_at=NOW+100)
        out=m.evaluate(req(),p,(),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.HOLD)

    def test_operation_denied(self):
        out=m.evaluate(req(operation="WIRE_TRANSFER"),policy(),(),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.DENY)

    def test_scope_denied(self):
        out=m.evaluate(req(scope="production_root"),policy(),(),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.DENY)

    def test_invalid_candidate_risk_holds(self):
        out=m.evaluate(req(candidate_risk_units=1001),policy(),(),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.HOLD)

    def test_invalid_candidate_impact_holds(self):
        out=m.evaluate(req(candidate_impact_units=-1),policy(),(),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.HOLD)

    def test_invalid_ledger_holds(self):
        out=m.evaluate(req(),policy(),(ent("E1",risk=1001),),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.HOLD)

    def test_duplicate_entry_id_invalid(self):
        with self.assertRaises(ValueError): m.prepare_registry(policy(),(ent("E1"),ent("E1",risk=20)),now=NOW)

    def test_registry_order_invariant(self):
        es=(ent("E1"),ent("E2",occurred=NOW-50))
        self.assertEqual(m.registry_fingerprint(es),m.registry_fingerprint(reversed(es)))

    def test_prepared_policy_mismatch_holds(self):
        p=policy(); pr=m.prepare_registry(p,(),now=NOW)
        out=m.evaluate_prepared(req(),dataclasses.replace(p,max_total_risk_units=1100),pr,now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.HOLD); self.assertIn("PREPARED_POLICY_FINGERPRINT_MISMATCH",out.reasons)

    def test_delta_roundtrip(self):
        base=tuple(ent(f"E{i}",task=f"T{i%3}",risk=10+i,impact=20+i,occurred=NOW-1000+i) for i in range(20))
        target=list(base); target[5]=dataclasses.replace(target[5],risk_units=99); target=target[1:]; target.append(ent("E20",task="T2",risk=50,impact=60))
        d=m.build_registry_delta(base,target); rebuilt=m.apply_registry_delta(base,d)
        self.assertEqual(m.registry_fingerprint(rebuilt),m.registry_fingerprint(target)); self.assertEqual((len(d.changed),len(d.removed_ids),len(d.added)),(1,1,1))

    def test_delta_wrong_base_rejected(self):
        base=(ent("E1"),); target=(dataclasses.replace(ent("E1"),risk_units=200),)
        d=m.build_registry_delta(base,target)
        with self.assertRaises(ValueError): m.apply_registry_delta((ent("X"),),d)

    def test_sync_only_missing(self):
        p=policy(); es=tuple(ent(f"E{i}",task=f"T{i%2}",occurred=NOW-1000+i) for i in range(20)); pr=m.prepare_registry(p,es,now=NOW)
        known=dict(pr.item_fingerprints)
        for k in sorted(known)[-3:]: known.pop(k)
        plan=m.plan_registry_sync(pr,known)
        self.assertEqual(len(plan.missing_or_changed_ids),3); self.assertFalse(plan.full_resend_required or plan.permission_granted or plan.action_execution_authorized or plan.stop_execution_authorized)

    def test_sync_changed_fp(self):
        p=policy(); es=(ent("E1"),ent("E2")); pr=m.prepare_registry(p,es,now=NOW)
        known=dict(pr.item_fingerprints); known["E2"]="WRONG"
        plan=m.plan_registry_sync(pr,known); self.assertEqual(plan.missing_or_changed_ids,("E2",))

    def test_registry_from_dict_roundtrip(self):
        es=m.default_entries(NOW); payload=[m._canonical(e) for e in es]
        pr=m.registry_from_dict(policy(),payload,now=NOW)
        self.assertEqual(pr.registry_fingerprint,m.registry_fingerprint(es))

    def test_static_safety_no_execution_primitives(self):
        src=Path(m.__file__).read_text(encoding="utf-8"); tree=ast.parse(src)
        banned_imports={"subprocess","socket","requests","urllib","http","shutil"}
        banned_calls={"system","popen","unlink","remove","rmtree","send","sendall","connect","execute","commit","grant","deploy","publish","write_text","write_bytes"}
        for n in ast.walk(tree):
            if isinstance(n,ast.Import): self.assertTrue(all(a.name.split('.')[0] not in banned_imports for a in n.names))
            elif isinstance(n,ast.ImportFrom): self.assertNotIn((n.module or '').split('.')[0],banned_imports)
            elif isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute): self.assertNotIn(n.func.attr,banned_calls)

    def test_policy_validation_warning(self):
        with self.assertRaises(ValueError): policy(warning_risk_units=1000).validate(NOW)

    def test_policy_validation_high_threshold(self):
        with self.assertRaises(ValueError): policy(high_risk_threshold=301).validate(NOW)

    def test_remaining_never_negative(self):
        out=m.evaluate(req(candidate_risk_units=300,candidate_impact_units=500),policy(),(ent("E1",risk=900,impact=900),),now=NOW)
        self.assertGreaterEqual(out.remaining_risk_units,0); self.assertGreaterEqual(out.remaining_impact_units,0)

    def test_budget_remaining_not_permission(self):
        out=m.evaluate(req(candidate_risk_units=1,candidate_impact_units=1),policy(),(),now=NOW)
        self.assertGreater(out.remaining_risk_units,0); self.assertFalse(out.permission_granted)

    def test_stop_candidate_not_stop_executed(self):
        out=m.evaluate(req(candidate_risk_units=301),policy(),(),now=NOW)
        self.assertTrue(out.stop_candidate); self.assertFalse(out.stop_executed)

    def test_digest_deterministic(self):
        a=m.evaluate(req(),policy(),m.default_entries(NOW),now=NOW)
        self.assertEqual(m.assessment_digest((a,)),m.assessment_digest((a,)))


def _generated_case(i):
    def test(self):
        p=policy()
        task=f"TASK-{i%7}"
        r=req(request_id=f"R-{i}",task_id=task,candidate_id=f"C-{i}",candidate_risk_units=(i*17)%301,candidate_impact_units=(i*23)%401,evidence_binding=f"B-{i%5}")
        es=[]
        for j in range(i%6):
            es.append(ent(f"E-{i}-{j}",task=task,risk=(i+j*13)%180,impact=(i+j*19)%160,occurred=NOW-100+j,binding=r.evidence_binding))
        if i%11==0 and es: es[-1]=dataclasses.replace(es[-1],revoked=True)
        if i%13==0 and es: es[-1]=dataclasses.replace(es[-1],expires_at=NOW-1,occurred_at=NOW-100)
        out=m.evaluate(r,p,tuple(es),now=NOW)
        self.assertIn(out.decision,{m.ControlDecision.ALLOW,m.ControlDecision.HUMAN_APPROVAL,m.ControlDecision.DENY})
        self.assertFalse(out.permission_granted or out.action_executed or out.stop_executed or out.commit_performed or out.action_success or out.risk_truth_proven)
        self.assertEqual(out.projected_risk_units,out.used_risk_units+r.candidate_risk_units)
        self.assertEqual(out.projected_impact_units,out.used_impact_units+r.candidate_impact_units)
    return test

_base_count=len([n for n in dir(RiskBudgetTests) if n.startswith("test_")])
for _i in range(160-_base_count):
    setattr(RiskBudgetTests,f"test_generated_{_i:03d}",_generated_case(_i))

if __name__ == "__main__": unittest.main(verbosity=1)
