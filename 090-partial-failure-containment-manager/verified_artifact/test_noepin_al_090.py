import unittest
from dataclasses import replace
from noepin_al_090_partial_failure_containment_manager import *
class T(unittest.TestCase):
    def base(self): return default_request(),default_steps(),default_states(),default_compensations(),default_policy()
    def neg(self,z):
        self.assertFalse(z.permission_granted); self.assertFalse(z.action_executed); self.assertFalse(z.branch_execution_started); self.assertFalse(z.isolation_executed); self.assertFalse(z.compensation_executed); self.assertFalse(z.resource_lock_mutated); self.assertFalse(z.plan_committed); self.assertFalse(z.atomic_publish_executed); self.assertFalse(z.external_write_performed); self.assertFalse(z.world_truth_proven); self.assertFalse(z.safety_proven); self.assertFalse(z.action_success)
    def test_001_default_allow(self): z=default_evaluation(); self.assertEqual(z.decision,Decision.ALLOW); self.assertEqual(z.containment_state,ContainmentState.SAFE_CONTINUE); self.neg(z)
    def test_002_containment_a_b(self): z=default_evaluation(); self.assertEqual(z.containment_set,('A','B'))
    def test_003_continue_c(self): z=default_evaluation(); self.assertEqual(z.continue_step_ids,('C',)); self.assertTrue(z.continue_candidate)
    def test_004_recovery_plan(self): z=default_evaluation(); self.assertEqual(z.recovery_plan,(('A','COMP-A'),)); self.assertTrue(z.recovery_candidate)
    def test_005_blast_unknown_full_stop(self): r,s,st,c,p=self.base(); z=evaluate(replace(r,blast_radius_known=False),s,st,c,p); self.assertEqual(z.decision,Decision.HOLD); self.assertTrue(z.full_stop_candidate); self.assertEqual(set(z.stopped_step_ids),{x.step_id for x in s}); self.neg(z)
    def test_006_resource_map_unknown_full_stop(self): r,s,st,c,p=self.base(); z=evaluate(replace(r,resource_map_complete=False),s,st,c,p); self.assertTrue(z.full_stop_candidate); self.neg(z)
    def test_007_critical_shared_resource(self): r,s,st,c,p=self.base(); s=(replace(s[0],resources=('GLOBAL-LEDGER',)),replace(s[1],resources=('GLOBAL-LEDGER',)),s[2],s[3]); z=evaluate(r,s,st,c,p); self.assertTrue(z.full_stop_candidate); self.assertIn('CRITICAL_SHARED_RESOURCE_AFFECTED',z.reasons)
    def test_008_no_failure(self): r,s,st,c,p=self.base(); st=tuple(replace(x,state=StepState.SUCCESS,failure_code='') if x.step_id=='A' else x for x in st); z=evaluate(r,s,st,c,p); self.assertEqual(z.containment_state,ContainmentState.NO_FAILURE); self.assertEqual(z.decision,Decision.ALLOW)
    def test_009_unknown_state(self): r,s,st,c,p=self.base(); st=tuple(replace(x,state=StepState.UNKNOWN) if x.step_id=='A' else x for x in st); z=evaluate(r,s,st,c,p); self.assertTrue(z.full_stop_candidate); self.assertTrue(z.incident_candidate)
    def test_010_missing_state(self): r,s,st,c,p=self.base(); z=evaluate(r,s,st[:-1],c,p); self.assertEqual(z.decision,Decision.HOLD)
    def test_011_duplicate_step(self): r,s,st,c,p=self.base(); z=evaluate(r,s+(s[0],),st,c,p); self.assertEqual(z.decision,Decision.HOLD)
    def test_012_duplicate_state(self): r,s,st,c,p=self.base(); z=evaluate(r,s,st+(st[0],),c,p); self.assertEqual(z.decision,Decision.HOLD)
    def test_013_missing_dependency(self): r,s,st,c,p=self.base(); s=(replace(s[0],dependencies=('X',)),)+s[1:]; z=evaluate(r,s,st,c,p); self.assertEqual(z.decision,Decision.HOLD)
    def test_014_cycle(self): r,s,st,c,p=self.base(); s=(replace(s[0],dependencies=('B',)),s[1],s[2],s[3]); z=evaluate(r,s,st,c,p); self.assertEqual(z.decision,Decision.HOLD); self.assertIn('EXECUTION_GRAPH_CYCLE',z.reasons)
    def test_015_policy_revoked(self): r,s,st,c,p=self.base(); z=evaluate(r,s,st,c,replace(p,revoked=True)); self.assertEqual(z.decision,Decision.HOLD)
    def test_016_scope_mismatch(self): r,s,st,c,p=self.base(); z=evaluate(replace(r,binding='X'),s,st,c,p); self.assertEqual(z.decision,Decision.HOLD)
    def test_017_request_unobserved(self): r,s,st,c,p=self.base(); z=evaluate(replace(r,observed=False),s,st,c,p); self.assertEqual(z.decision,Decision.HOLD)
    def test_018_step_unobserved(self): r,s,st,c,p=self.base(); s=(replace(s[0],observed=False),)+s[1:]; z=evaluate(r,s,st,c,p); self.assertEqual(z.decision,Decision.HOLD)
    def test_019_state_unobserved(self): r,s,st,c,p=self.base(); st=(replace(st[0],observed=False),)+st[1:]; z=evaluate(r,s,st,c,p); self.assertEqual(z.decision,Decision.HOLD)
    def test_020_comp_coverage_invalid(self): r,s,st,c,p=self.base(); c=(replace(c[0],coverage=1.1),); z=evaluate(r,s,st,c,p); self.assertEqual(z.decision,Decision.HOLD)
    def test_021_high_risk_comp_excluded(self): r,s,st,c,p=self.base(); c=(replace(c[0],risk=RiskLevel.HIGH),); z=evaluate(r,s,st,c,p); self.assertFalse(z.recovery_candidate); self.assertEqual(z.decision,Decision.ALLOW)
    def test_022_low_coverage_comp_excluded(self): r,s,st,c,p=self.base(); c=(replace(c[0],coverage=.5),); z=evaluate(r,s,st,c,p); self.assertFalse(z.recovery_candidate)
    def test_023_best_comp(self): r,s,st,c,p=self.base(); c=c+(CompensationRecord('A','COMP-Z',.9,RiskLevel.LOW,True,True,p.binding,p.state_epoch),); z=evaluate(r,s,st,c,p); self.assertEqual(z.recovery_plan,(('A','COMP-A'),))
    def test_024_unobserved_comp_excluded(self): r,s,st,c,p=self.base(); c=(replace(c[0],observed=False),); z=evaluate(r,s,st,c,p); self.assertFalse(z.recovery_candidate)
    def test_025_unavailable_comp_excluded(self): r,s,st,c,p=self.base(); c=(replace(c[0],available=False),); z=evaluate(r,s,st,c,p); self.assertFalse(z.recovery_candidate)
    def test_026_resource_propagation(self): z=default_evaluation(); self.assertIn('B',z.containment_set)
    def test_027_downstream_chain(self): r,s,st,c,p=self.base(); s=s+(ExecutionStep('E',('B',),('E-R',),RiskLevel.LOW,True,p.binding,p.state_epoch),); st=st+(StepStateRecord('E',StepState.PENDING,'',True,p.binding,p.state_epoch),); z=evaluate(r,s,st,c,p); self.assertIn('E',z.containment_set)
    def test_028_multiple_failures(self): r,s,st,c,p=self.base(); st=tuple(replace(x,state=StepState.FAILED,failure_code='ERR') if x.step_id in ('A','C') else x for x in st); z=evaluate(r,s,st,c,p); self.assertEqual(z.failed_step_ids,('A','C'))
    def test_029_no_safe_branch_with_recovery(self): r,s,st,c,p=self.base(); s=s[:2]; st=st[:2]; z=evaluate(r,s,st,c,p); self.assertEqual(z.containment_state,ContainmentState.RECOVERY_REQUIRED); self.assertTrue(z.full_stop_candidate); self.assertTrue(z.recovery_candidate)
    def test_030_no_safe_branch_no_recovery(self): r,s,st,c,p=self.base(); s=s[:2]; st=st[:2]; z=evaluate(r,s,st,(),p); self.assertEqual(z.containment_state,ContainmentState.FULL_STOP); self.assertTrue(z.incident_candidate)
    def test_031_allow_not_execution(self): z=default_evaluation(); self.assertTrue(z.next_gate_candidate); self.neg(z)
    def test_032_recovery_not_execution(self): z=default_evaluation(); self.assertTrue(z.recovery_candidate); self.assertFalse(z.compensation_executed)
    def test_033_full_stop_not_stop_execution(self): r,s,st,c,p=self.base(); z=evaluate(replace(r,blast_radius_known=False),s,st,c,p); self.assertTrue(z.full_stop_candidate); self.assertFalse(z.isolation_executed); self.neg(z)
    def test_034_prepared_valid(self): r,s,st,c,p=self.base(); x=prepare_state(r,s,st,c,p,binding=p.binding,state_epoch=p.state_epoch); self.assertTrue(validate_prepared_integrity(x)); self.assertEqual(evaluate_prepared(x,current_context_fingerprint=x.context_fingerprint,current_dependency_fingerprint=x.dependency_fingerprint,current_policy_fingerprint=x.policy_fingerprint,current_registry_fingerprint=x.registry_fingerprint,prepared_integrity_validated=True),default_evaluation())
    def test_035_prepared_changed_hold(self): r,s,st,c,p=self.base(); x=prepare_state(r,s,st,c,p,binding=p.binding,state_epoch=p.state_epoch); z=evaluate_prepared(x,current_context_fingerprint='X',current_dependency_fingerprint=x.dependency_fingerprint,current_policy_fingerprint=x.policy_fingerprint,current_registry_fingerprint=x.registry_fingerprint,prepared_integrity_validated=True); self.assertEqual(z.decision,Decision.HOLD)
    def test_036_prepared_unvalidated_hold(self): r,s,st,c,p=self.base(); x=prepare_state(r,s,st,c,p,binding=p.binding,state_epoch=p.state_epoch); z=evaluate_prepared(x,current_context_fingerprint=x.context_fingerprint,current_dependency_fingerprint=x.dependency_fingerprint,current_policy_fingerprint=x.policy_fingerprint,current_registry_fingerprint=x.registry_fingerprint,prepared_integrity_validated=False); self.assertEqual(z.decision,Decision.HOLD)
    def test_037_delta_roundtrip(self): r,s,st,c,p=self.base(); x=prepare_state(r,s,st,c,p,binding=p.binding,state_epoch=p.state_epoch); st2=tuple(replace(v,state=StepState.SUCCESS,failure_code='') if v.step_id=='A' else v for v in st); y=prepare_state(r,s,st2,c,p,binding=p.binding,state_epoch=p.state_epoch); self.assertEqual(apply_delta(x,make_delta(x,y)),y)
    def test_038_missing_only(self): r,s,st,c,p=self.base(); x=prepare_state(r,s,st,c,p,binding=p.binding,state_epoch=p.state_epoch); known=dict(x.record_fingerprints); known.pop('STATE:A'); plan=missing_only_sync_plan(x,known); self.assertEqual(plan.missing_or_changed_record_ids,('STATE:A',)); self.assertFalse(plan.full_resend_required)
    def test_039_deterministic(self): r,s,st,c,p=self.base(); z1=evaluate(r,s,st,c,p); z2=evaluate(r,tuple(reversed(s)),tuple(reversed(st)),tuple(reversed(c)),p); self.assertEqual(z1,z2)
    def test_040_authority_flags_false(self): self.neg(default_evaluation())

def _gen(k):
    def f(self):
        r,s,st,c,p=self.base(); mode=k%12
        if mode==0: want=Decision.ALLOW
        elif mode==1: r=replace(r,blast_radius_known=False); want=Decision.HOLD
        elif mode==2: r=replace(r,resource_map_complete=False); want=Decision.HOLD
        elif mode==3: st=tuple(replace(x,state=StepState.UNKNOWN) if x.step_id=='A' else x for x in st); want=Decision.HOLD
        elif mode==4: c=(replace(c[0],coverage=.2),); want=Decision.ALLOW
        elif mode==5: p=replace(p,revoked=True); want=Decision.HOLD
        elif mode==6: st=tuple(replace(x,state=StepState.SUCCESS,failure_code='') if x.step_id=='A' else x for x in st); want=Decision.ALLOW
        elif mode==7: s=(replace(s[0],resources=('GLOBAL-LEDGER',)),replace(s[1],resources=('GLOBAL-LEDGER',)),s[2],s[3]); want=Decision.HOLD
        elif mode==8: st=tuple(replace(x,state=StepState.FAILED,failure_code='ERR') if x.step_id in ('A','C') else x for x in st); want=Decision.HOLD
        elif mode==9: r=replace(r,observed=False); want=Decision.HOLD
        elif mode==10: c=(replace(c[0],risk=RiskLevel.HIGH),); want=Decision.ALLOW
        else: s=s[:2]; st=st[:2]; want=Decision.HOLD
        z=evaluate(r,s,st,c,p); self.assertEqual(z.decision,want); self.neg(z)
    return f
for k in range(120): setattr(T,f'test_regression_{k:03d}',_gen(k))
if __name__=='__main__': unittest.main(verbosity=2)
