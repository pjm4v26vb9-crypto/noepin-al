import unittest
from dataclasses import replace
from noepin_al_091_two_phase_action_commit import *
class T(unittest.TestCase):
    def base(self): return default_request(),default_actions(),default_participants(),default_prepares(),default_approvals(),default_outcomes(),default_policy()
    def neg(self,z):
        for k in ('permission_granted','approval_executed','prepare_request_executed','resource_lock_mutated','commit_executed','abort_executed','action_executed','compensation_executed','plan_committed','atomic_publish_executed','external_write_performed','world_truth_proven','safety_proven','action_success'): self.assertFalse(getattr(z,k))
    def test_001_default_commit_candidate(self): z=default_evaluation(); self.assertEqual(z.decision,Decision.ALLOW); self.assertEqual(z.transaction_state,TransactionState.COMMIT_CANDIDATE); self.assertTrue(z.commit_candidate); self.neg(z)
    def test_002_all_prepared(self): z=default_evaluation(); self.assertEqual(z.prepared_participant_ids,('P-A','P-B'))
    def test_003_next_gate(self): self.assertTrue(default_evaluation().next_gate_candidate)
    def test_004_no_authority_flags(self): self.neg(default_evaluation())
    def test_005_reject_abort(self): r,a,p,pr,ap,o,pol=self.base(); pr=(replace(pr[0],status=PrepareStatus.REJECTED),pr[1]); z=evaluate(r,a,p,pr,ap,o,pol); self.assertEqual(z.decision,Decision.DENY); self.assertTrue(z.abort_candidate); self.neg(z)
    def test_006_timeout_abort_hold(self): r,a,p,pr,ap,o,pol=self.base(); pr=(replace(pr[0],status=PrepareStatus.TIMEOUT),pr[1]); z=evaluate(r,a,p,pr,ap,o,pol); self.assertEqual(z.decision,Decision.HOLD); self.assertTrue(z.abort_candidate)
    def test_007_unknown_abort_hold(self): r,a,p,pr,ap,o,pol=self.base(); pr=(replace(pr[0],status=PrepareStatus.UNKNOWN),pr[1]); z=evaluate(r,a,p,pr,ap,o,pol); self.assertEqual(z.decision,Decision.HOLD); self.assertTrue(z.abort_candidate)
    def test_008_missing_prepare(self): r,a,p,pr,ap,o,pol=self.base(); z=evaluate(r,a,p,pr[:-1],ap,o,pol); self.assertEqual(z.decision,Decision.HOLD)
    def test_009_precondition_fail(self): r,a,p,pr,ap,o,pol=self.base(); pr=(replace(pr[0],preconditions_ok=False),pr[1]); z=evaluate(r,a,p,pr,ap,o,pol); self.assertEqual(z.decision,Decision.DENY); self.assertTrue(z.abort_candidate)
    def test_010_permission_evidence_fail(self): r,a,p,pr,ap,o,pol=self.base(); pr=(replace(pr[0],permission_evidence_valid=False),pr[1]); z=evaluate(r,a,p,pr,ap,o,pol); self.assertEqual(z.decision,Decision.DENY)
    def test_011_resource_not_ready(self): r,a,p,pr,ap,o,pol=self.base(); pr=(replace(pr[0],resource_ready_evidence=False),pr[1]); z=evaluate(r,a,p,pr,ap,o,pol); self.assertEqual(z.decision,Decision.DENY); self.assertIn('RESOURCE_NOT_READY',z.reasons)
    def test_012_approval_missing(self): r,a,p,pr,ap,o,pol=self.base(); z=evaluate(r,a,p,pr,(),o,pol); self.assertEqual(z.decision,Decision.HUMAN_APPROVAL); self.assertTrue(z.human_approval_candidate)
    def test_013_approval_binding_mismatch(self): r,a,p,pr,ap,o,pol=self.base(); ap=(replace(ap[0],approval_binding_digest='BAD'),); z=evaluate(r,a,p,pr,ap,o,pol); self.assertEqual(z.decision,Decision.HOLD); self.assertTrue(z.abort_candidate)
    def test_014_approval_rejected(self): r,a,p,pr,ap,o,pol=self.base(); ap=(replace(ap[0],approved=False),); z=evaluate(r,a,p,pr,ap,o,pol); self.assertEqual(z.decision,Decision.HUMAN_APPROVAL)
    def test_015_policy_revoked(self): r,a,p,pr,ap,o,pol=self.base(); z=evaluate(r,a,p,pr,ap,o,replace(pol,revoked=True)); self.assertEqual(z.decision,Decision.HOLD)
    def test_016_duplicate_participant(self): r,a,p,pr,ap,o,pol=self.base(); z=evaluate(r,a,p+(p[0],),pr,ap,o,pol); self.assertEqual(z.decision,Decision.HOLD)
    def test_017_duplicate_prepare(self): r,a,p,pr,ap,o,pol=self.base(); z=evaluate(r,a,p,pr+(pr[0],),ap,o,pol); self.assertEqual(z.decision,Decision.HOLD)
    def test_018_unknown_action_participant(self): r,a,p,pr,ap,o,pol=self.base(); a=(replace(a[0],participant_ids=('X',)),a[1]); z=evaluate(r,a,p,pr,ap,o,pol); self.assertEqual(z.decision,Decision.HOLD)
    def test_019_unobserved_participant(self): r,a,p,pr,ap,o,pol=self.base(); p=(replace(p[0],observed=False),p[1]); z=evaluate(r,a,p,pr,ap,o,pol); self.assertEqual(z.decision,Decision.HOLD)
    def test_020_unobserved_prepare(self): r,a,p,pr,ap,o,pol=self.base(); pr=(replace(pr[0],observed=False),pr[1]); z=evaluate(r,a,p,pr,ap,o,pol); self.assertEqual(z.decision,Decision.HOLD)
    def test_021_tx_mismatch(self): r,a,p,pr,ap,o,pol=self.base(); pr=(replace(pr[0],tx_id='OTHER'),pr[1]); z=evaluate(r,a,p,pr,ap,o,pol); self.assertEqual(z.decision,Decision.HOLD)
    def test_022_scope_mismatch(self): r,a,p,pr,ap,o,pol=self.base(); z=evaluate(replace(r,binding='X'),a,p,pr,ap,o,pol); self.assertEqual(z.decision,Decision.HOLD)
    def test_023_commit_failure_incident(self): r,a,p,pr,ap,o,pol=self.base(); o=(CommitOutcomeEvidence('P-A',r.tx_id,CommitObservationStatus.FAILED,True,pol.binding,pol.state_epoch),); z=evaluate(r,a,p,pr,ap,o,pol); self.assertEqual(z.transaction_state,TransactionState.INCIDENT_HOLD); self.assertTrue(z.incident_candidate); self.assertTrue(z.compensation_candidate); self.neg(z)
    def test_024_commit_unknown_incident(self): r,a,p,pr,ap,o,pol=self.base(); o=(CommitOutcomeEvidence('P-A',r.tx_id,CommitObservationStatus.UNKNOWN,True,pol.binding,pol.state_epoch),); z=evaluate(r,a,p,pr,ap,o,pol); self.assertTrue(z.incident_candidate)
    def test_025_commit_success_not_action_success(self): r,a,p,pr,ap,o,pol=self.base(); o=(CommitOutcomeEvidence('P-A',r.tx_id,CommitObservationStatus.SUCCESS,True,pol.binding,pol.state_epoch),); z=evaluate(r,a,p,pr,ap,o,pol); self.assertFalse(z.action_success); self.assertFalse(z.commit_executed)
    def test_026_restart_valid(self): r,a,p,pr,ap,o,pol=self.base(); tmp=prepare_state(r,a,p,pr,ap,o,pol,binding=pol.binding,state_epoch=pol.state_epoch); r=replace(r,coordinator_restarted=True,recovered_prepare_fingerprint=tmp.prepare_set_fingerprint); z=evaluate(r,a,p,pr,ap,o,pol); self.assertTrue(z.coordinator_recovery_validated); self.assertTrue(z.commit_candidate)
    def test_027_restart_mismatch(self): r,a,p,pr,ap,o,pol=self.base(); r=replace(r,coordinator_restarted=True,recovered_prepare_fingerprint='BAD'); z=evaluate(r,a,p,pr,ap,o,pol); self.assertEqual(z.decision,Decision.HOLD); self.assertTrue(z.abort_candidate)
    def test_028_empty_participants(self): r,a,p,pr,ap,o,pol=self.base(); z=evaluate(r,a,(),(),ap,o,pol); self.assertEqual(z.decision,Decision.HOLD)
    def test_029_duplicate_approval(self): r,a,p,pr,ap,o,pol=self.base(); z=evaluate(r,a,p,pr,ap+(ap[0],),o,pol); self.assertEqual(z.decision,Decision.HOLD)
    def test_030_insufficient_approval_count(self): r,a,p,pr,ap,o,pol=self.base(); z=evaluate(r,a,p,pr,ap,o,replace(pol,required_approvals=2)); self.assertEqual(z.decision,Decision.HUMAN_APPROVAL)
    def test_031_two_approvals(self): r,a,p,pr,ap,o,pol=self.base(); ap=ap+(ApprovalEvidence('APP-2',r.tx_id,True,r.approval_binding_digest,True,pol.binding,pol.state_epoch),); z=evaluate(r,a,p,pr,ap,o,replace(pol,required_approvals=2)); self.assertEqual(z.decision,Decision.ALLOW)
    def test_032_unobserved_approval_excluded(self): r,a,p,pr,ap,o,pol=self.base(); ap=(replace(ap[0],observed=False),); z=evaluate(r,a,p,pr,ap,o,pol); self.assertEqual(z.decision,Decision.HUMAN_APPROVAL)
    def test_033_unknown_commit_participant(self): r,a,p,pr,ap,o,pol=self.base(); o=(CommitOutcomeEvidence('X',r.tx_id,CommitObservationStatus.FAILED,True,pol.binding,pol.state_epoch),); z=evaluate(r,a,p,pr,ap,o,pol); self.assertEqual(z.decision,Decision.HOLD)
    def test_034_commit_outcome_tx_mismatch(self): r,a,p,pr,ap,o,pol=self.base(); o=(CommitOutcomeEvidence('P-A','BAD',CommitObservationStatus.FAILED,True,pol.binding,pol.state_epoch),); z=evaluate(r,a,p,pr,ap,o,pol); self.assertEqual(z.decision,Decision.HOLD)
    def test_035_prepared_valid(self): r,a,p,pr,ap,o,pol=self.base(); x=prepare_state(r,a,p,pr,ap,o,pol,binding=pol.binding,state_epoch=pol.state_epoch); self.assertTrue(validate_prepared_integrity(x)); self.assertEqual(evaluate_prepared(x,current_context_fingerprint=x.context_fingerprint,current_dependency_fingerprint=x.dependency_fingerprint,current_policy_fingerprint=x.policy_fingerprint,current_registry_fingerprint=x.registry_fingerprint,prepared_integrity_validated=True),default_evaluation())
    def test_036_prepared_changed_hold(self): r,a,p,pr,ap,o,pol=self.base(); x=prepare_state(r,a,p,pr,ap,o,pol,binding=pol.binding,state_epoch=pol.state_epoch); z=evaluate_prepared(x,current_context_fingerprint='BAD',current_dependency_fingerprint=x.dependency_fingerprint,current_policy_fingerprint=x.policy_fingerprint,current_registry_fingerprint=x.registry_fingerprint,prepared_integrity_validated=True); self.assertEqual(z.decision,Decision.HOLD)
    def test_037_prepared_unvalidated_hold(self): r,a,p,pr,ap,o,pol=self.base(); x=prepare_state(r,a,p,pr,ap,o,pol,binding=pol.binding,state_epoch=pol.state_epoch); z=evaluate_prepared(x,current_context_fingerprint=x.context_fingerprint,current_dependency_fingerprint=x.dependency_fingerprint,current_policy_fingerprint=x.policy_fingerprint,current_registry_fingerprint=x.registry_fingerprint,prepared_integrity_validated=False); self.assertEqual(z.decision,Decision.HOLD)
    def test_038_delta_roundtrip(self): r,a,p,pr,ap,o,pol=self.base(); x=prepare_state(r,a,p,pr,ap,o,pol,binding=pol.binding,state_epoch=pol.state_epoch); pr2=(replace(pr[0],status=PrepareStatus.REJECTED),pr[1]); y=prepare_state(r,a,p,pr2,ap,o,pol,binding=pol.binding,state_epoch=pol.state_epoch); self.assertEqual(apply_delta(x,make_delta(x,y)),y)
    def test_039_missing_only(self): r,a,p,pr,ap,o,pol=self.base(); x=prepare_state(r,a,p,pr,ap,o,pol,binding=pol.binding,state_epoch=pol.state_epoch); known=dict(x.record_fingerprints); known.pop('PREPARE:P-A'); plan=missing_only_sync_plan(x,known); self.assertEqual(plan.missing_or_changed_record_ids,('PREPARE:P-A',)); self.assertFalse(plan.full_resend_required)
    def test_040_deterministic(self): r,a,p,pr,ap,o,pol=self.base(); z1=evaluate(r,a,p,pr,ap,o,pol); z2=evaluate(r,tuple(reversed(a)),tuple(reversed(p)),tuple(reversed(pr)),tuple(reversed(ap)),o,pol); self.assertEqual(z1,z2)

def _gen(k):
    def f(self):
        r,a,p,pr,ap,o,pol=self.base(); mode=k%12
        if mode==0: want=Decision.ALLOW
        elif mode==1: pr=(replace(pr[0],status=PrepareStatus.REJECTED),pr[1]); want=Decision.DENY
        elif mode==2: pr=(replace(pr[0],status=PrepareStatus.TIMEOUT),pr[1]); want=Decision.HOLD
        elif mode==3: pr=(replace(pr[0],status=PrepareStatus.UNKNOWN),pr[1]); want=Decision.HOLD
        elif mode==4: ap=(); want=Decision.HUMAN_APPROVAL
        elif mode==5: pol=replace(pol,revoked=True); want=Decision.HOLD
        elif mode==6: pr=(replace(pr[0],resource_ready_evidence=False),pr[1]); want=Decision.DENY
        elif mode==7: r=replace(r,observed=False); want=Decision.HOLD
        elif mode==8: o=(CommitOutcomeEvidence('P-A',r.tx_id,CommitObservationStatus.FAILED,True,pol.binding,pol.state_epoch),); want=Decision.HOLD
        elif mode==9: pol=replace(pol,allow_commit_candidate=False); want=Decision.HOLD
        elif mode==10: ap=(replace(ap[0],approved=False),); want=Decision.HUMAN_APPROVAL
        else: pr=(replace(pr[0],preconditions_ok=False),pr[1]); want=Decision.DENY
        z=evaluate(r,a,p,pr,ap,o,pol); self.assertEqual(z.decision,want); self.neg(z)
    return f
for k in range(120): setattr(T,f'test_regression_{k:03d}',_gen(k))
if __name__=='__main__': unittest.main(verbosity=2)
