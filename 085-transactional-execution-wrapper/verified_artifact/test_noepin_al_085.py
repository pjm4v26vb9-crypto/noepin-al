import unittest
from dataclasses import replace
from noepin_al_085_transactional_execution_wrapper import *
class T(unittest.TestCase):
    def base(self): return default_request(),default_intent(),default_permit(),default_plan(),default_before(),default_after(),default_steps(),default_verify(),default_rollback(),default_policy()
    def neg(self,z):
        self.assertFalse(z.request_promoted_to_success); self.assertFalse(z.intent_promoted_to_action); self.assertFalse(z.permission_granted); self.assertFalse(z.action_executed); self.assertFalse(z.commit_executed); self.assertFalse(z.rollback_executed); self.assertFalse(z.external_write_performed); self.assertFalse(z.receipt_promoted_to_truth); self.assertFalse(z.world_truth_proven); self.assertFalse(z.safety_proven); self.assertFalse(z.action_success)
    def test_001_default_allow_candidate(self):
        z=default_evaluation(); self.assertEqual(z.decision,Decision.ALLOW); self.assertTrue(z.commit_candidate); self.assertTrue(z.next_gate_candidate); self.neg(z)
    def test_002_all_success_state(self): self.assertEqual(default_evaluation().transaction_state,TransactionState.COMMIT_CANDIDATE)
    def test_003_middle_failure(self):
        r,i,p,pl,b,a,s,v,rb,pol=self.base(); s=(s[0],replace(s[1],status=StepStatus.FAILED)); z=evaluate(r,i,p,pl,b,a,s,v,rb,pol); self.assertEqual(z.decision,Decision.HOLD); self.assertTrue(z.rollback_candidate); self.assertEqual(z.failed_action_id,'A2'); self.neg(z)
    def test_004_verify_mismatch(self):
        r,i,p,pl,b,a,s,v,rb,pol=self.base(); v=replace(v,status=VerifyStatus.MISMATCH); z=evaluate(r,i,p,pl,b,a,s,v,rb,pol); self.assertEqual(z.transaction_state,TransactionState.ROLLBACK_REQUIRED); self.assertTrue(z.rollback_candidate)
    def test_005_rollback_failure_incident(self):
        r,i,p,pl,b,a,s,v,rb,pol=self.base(); s=(s[0],replace(s[1],status=StepStatus.FAILED)); rb=replace(rb,observed=True,status=RollbackStatus.FAILED); z=evaluate(r,i,p,pl,b,a,s,v,rb,pol); self.assertEqual(z.transaction_state,TransactionState.INCIDENT_HOLD); self.assertTrue(z.incident_candidate); self.neg(z)
    def test_006_timeout(self):
        r,i,p,pl,b,a,s,v,rb,pol=self.base(); s=(replace(s[0],status=StepStatus.TIMEOUT),s[1]); z=evaluate(r,i,p,pl,b,a,s,v,rb,pol); self.assertEqual(z.decision,Decision.HOLD); self.assertTrue(z.rollback_candidate)
    def test_007_verify_timeout(self):
        r,i,p,pl,b,a,s,v,rb,pol=self.base(); z=evaluate(r,i,p,pl,b,a,s,replace(v,status=VerifyStatus.TIMEOUT),rb,pol); self.assertEqual(z.decision,Decision.HOLD)
    def test_008_verify_exception(self):
        r,i,p,pl,b,a,s,v,rb,pol=self.base(); z=evaluate(r,i,p,pl,b,a,s,replace(v,status=VerifyStatus.EXCEPTION),rb,pol); self.assertEqual(z.decision,Decision.HOLD)
    def test_009_step_exception(self):
        r,i,p,pl,b,a,s,v,rb,pol=self.base(); z=evaluate(r,i,p,pl,b,a,(replace(s[0],status=StepStatus.EXCEPTION),s[1]),v,rb,pol); self.assertEqual(z.decision,Decision.HOLD)
    def test_010_request_unobserved(self):
        r,i,p,pl,b,a,s,v,rb,pol=self.base(); self.assertEqual(evaluate(replace(r,observed=False),i,p,pl,b,a,s,v,rb,pol).decision,Decision.HOLD)
    def test_011_intent_unobserved(self):
        r,i,p,pl,b,a,s,v,rb,pol=self.base(); self.assertEqual(evaluate(r,replace(i,observed=False),p,pl,b,a,s,v,rb,pol).decision,Decision.HOLD)
    def test_012_permit_unobserved(self):
        r,i,p,pl,b,a,s,v,rb,pol=self.base(); self.assertEqual(evaluate(r,i,replace(p,observed=False),pl,b,a,s,v,rb,pol).decision,Decision.HOLD)
    def test_013_permit_not_allowed(self):
        r,i,p,pl,b,a,s,v,rb,pol=self.base(); self.assertEqual(evaluate(r,i,replace(p,allow_candidate=False),pl,b,a,s,v,rb,pol).decision,Decision.HOLD)
    def test_014_before_unobserved(self):
        r,i,p,pl,b,a,s,v,rb,pol=self.base(); self.assertEqual(evaluate(r,i,p,pl,replace(b,observed=False),a,s,v,rb,pol).decision,Decision.HOLD)
    def test_015_after_unobserved(self):
        r,i,p,pl,b,a,s,v,rb,pol=self.base(); z=evaluate(r,i,p,pl,b,replace(a,observed=False),s,v,rb,pol); self.assertTrue(z.rollback_candidate)
    def test_016_verify_unobserved(self):
        r,i,p,pl,b,a,s,v,rb,pol=self.base(); z=evaluate(r,i,p,pl,b,a,s,replace(v,observed=False),rb,pol); self.assertTrue(z.rollback_candidate)
    def test_017_verify_fingerprint_mismatch(self):
        r,i,p,pl,b,a,s,v,rb,pol=self.base(); z=evaluate(r,i,p,pl,b,a,s,replace(v,final_state_fingerprint='X'),rb,pol); self.assertEqual(z.decision,Decision.HOLD)
    def test_018_after_snapshot_mismatch(self):
        r,i,p,pl,b,a,s,v,rb,pol=self.base(); z=evaluate(r,i,p,pl,b,replace(a,state_fingerprint='X'),s,v,rb,pol); self.assertEqual(z.decision,Decision.HOLD)
    def test_019_rollback_success_evidence(self):
        r,i,p,pl,b,a,s,v,rb,pol=self.base(); s=(s[0],replace(s[1],status=StepStatus.FAILED)); rb=replace(rb,observed=True,status=RollbackStatus.SUCCEEDED,restored_state_fingerprint=b.state_fingerprint,snapshot_state_fingerprint=b.state_fingerprint); z=evaluate(r,i,p,pl,b,a,s,v,rb,pol); self.assertEqual(z.transaction_state,TransactionState.ROLLBACK_VERIFIED); self.assertTrue(z.rollback_verified); self.assertFalse(z.rollback_executed)
    def test_020_bad_rollback_restore_incident(self):
        r,i,p,pl,b,a,s,v,rb,pol=self.base(); s=(s[0],replace(s[1],status=StepStatus.FAILED)); rb=replace(rb,observed=True,status=RollbackStatus.SUCCEEDED,restored_state_fingerprint='WRONG'); z=evaluate(r,i,p,pl,b,a,s,v,rb,pol); self.assertEqual(z.transaction_state,TransactionState.INCIDENT_HOLD)
    def test_021_empty_plan(self):
        r,i,p,pl,b,a,s,v,rb,pol=self.base(); self.assertEqual(evaluate(r,i,p,replace(pl,actions=()),b,a,(),v,rb,pol).decision,Decision.HOLD)
    def test_022_duplicate_action_id(self):
        r,i,p,pl,b,a,s,v,rb,pol=self.base(); pl=replace(pl,actions=(ActionSpec('A1',0),ActionSpec('A1',1))); self.assertEqual(evaluate(r,i,p,pl,b,a,s,v,rb,pol).decision,Decision.HOLD)
    def test_023_duplicate_order(self):
        r,i,p,pl,b,a,s,v,rb,pol=self.base(); pl=replace(pl,actions=(ActionSpec('A1',0),ActionSpec('A2',0))); self.assertEqual(evaluate(r,i,p,pl,b,a,s,v,rb,pol).decision,Decision.HOLD)
    def test_024_noncontiguous_order(self):
        r,i,p,pl,b,a,s,v,rb,pol=self.base(); pl=replace(pl,actions=(ActionSpec('A1',0),ActionSpec('A2',2))); self.assertEqual(evaluate(r,i,p,pl,b,a,s,v,rb,pol).decision,Decision.HOLD)
    def test_025_missing_step(self):
        r,i,p,pl,b,a,s,v,rb,pol=self.base(); z=evaluate(r,i,p,pl,b,a,(s[0],),v,rb,pol); self.assertTrue(z.rollback_candidate)
    def test_026_unobserved_step(self):
        r,i,p,pl,b,a,s,v,rb,pol=self.base(); z=evaluate(r,i,p,pl,b,a,(replace(s[0],observed=False),s[1]),v,rb,pol); self.assertTrue(z.rollback_candidate)
    def test_027_missing_before_fp(self):
        r,i,p,pl,b,a,s,v,rb,pol=self.base(); z=evaluate(r,i,p,pl,b,a,(replace(s[0],before_fingerprint=''),s[1]),v,rb,pol); self.assertTrue(z.rollback_candidate)
    def test_028_missing_after_fp(self):
        r,i,p,pl,b,a,s,v,rb,pol=self.base(); z=evaluate(r,i,p,pl,b,a,(replace(s[0],after_fingerprint=''),s[1]),v,rb,pol); self.assertTrue(z.rollback_candidate)
    def test_029_binding_mismatch(self):
        r,i,p,pl,b,a,s,v,rb,pol=self.base(); self.assertEqual(evaluate(replace(r,binding='X'),i,p,pl,b,a,s,v,rb,pol).decision,Decision.HOLD)
    def test_030_epoch_mismatch(self):
        r,i,p,pl,b,a,s,v,rb,pol=self.base(); self.assertEqual(evaluate(r,replace(i,state_epoch='OLD'),p,pl,b,a,s,v,rb,pol).decision,Decision.HOLD)
    def test_031_transaction_id_mismatch(self):
        r,i,p,pl,b,a,s,v,rb,pol=self.base(); self.assertEqual(evaluate(r,i,replace(p,transaction_id='TX-X'),pl,b,a,s,v,rb,pol).decision,Decision.HOLD)
    def test_032_policy_revoked(self):
        r,i,p,pl,b,a,s,v,rb,pol=self.base(); self.assertEqual(evaluate(r,i,p,pl,b,a,s,v,rb,replace(pol,revoked=True)).decision,Decision.HOLD)
    def test_033_prepared_semantic(self):
        x=self.base(); st=prepare_state(*x,binding=x[-1].binding,state_epoch=x[-1].state_epoch); self.assertTrue(validate_prepared_integrity(st)); z=evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True); self.assertEqual(z,evaluate(*x))
    def test_034_prepared_stale(self):
        x=self.base(); st=prepare_state(*x,binding=x[-1].binding,state_epoch=x[-1].state_epoch); self.assertEqual(evaluate_prepared(st,current_context_fingerprint='X',current_dependency_fingerprint=st.dependency_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True).decision,Decision.HOLD)
    def test_035_prepared_integrity_required(self):
        x=self.base(); st=prepare_state(*x,binding=x[-1].binding,state_epoch=x[-1].state_epoch); self.assertEqual(evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=False).decision,Decision.HOLD)
    def test_036_delta_reconstruction(self):
        x=self.base(); s1=prepare_state(*x,binding=x[-1].binding,state_epoch=x[-1].state_epoch); steps=list(x[6]); steps[0]=replace(steps[0],after_fingerprint='M2'); x2=x[:6]+(tuple(steps),)+x[7:]; s2=prepare_state(*x2,binding=x2[-1].binding,state_epoch=x2[-1].state_epoch); self.assertEqual(apply_delta(s1,make_delta(s1,s2)),s2)
    def test_037_missing_only(self):
        x=self.base(); many=tuple(StepEvidence(f'S{n}','TX-1',f'A{n}',True,StepStatus.APPLIED,f'B{n}',f'A{n}','TX-BIND','STATE-EPOCH-1') for n in range(20)); pl=replace(x[3],actions=tuple(ActionSpec(f'A{n}',n) for n in range(20))); xx=x[:3]+(pl,)+x[4:6]+(many,)+x[7:]; st=prepare_state(*xx,binding=xx[-1].binding,state_epoch=xx[-1].state_epoch); k=dict(st.step_fingerprints); [k.pop(f'S{n}') for n in range(5)]; plan=missing_only_sync_plan(st,k); self.assertEqual(len(plan.missing_or_changed_step_ids),5); self.assertFalse(plan.full_resend_required)
    def test_038_delta_smaller(self):
        x=self.base(); many=tuple(StepEvidence(f'S{n}','TX-1',f'A{n}',True,StepStatus.APPLIED,f'B{n}',f'A{n}','TX-BIND','STATE-EPOCH-1') for n in range(100)); pl=replace(x[3],actions=tuple(ActionSpec(f'A{n}',n) for n in range(100))); xx=x[:3]+(pl,)+x[4:6]+(many,)+x[7:]; s1=prepare_state(*xx,binding=xx[-1].binding,state_epoch=xx[-1].state_epoch); m=list(many); m[0]=replace(m[0],after_fingerprint='CHANGED'); xx2=xx[:6]+(tuple(m),)+xx[7:]; s2=prepare_state(*xx2,binding=xx2[-1].binding,state_epoch=xx2[-1].state_epoch); self.assertLess(delta_bytes(make_delta(s1,s2)),full_registry_bytes(s2))
    def test_039_authority_flags_false(self): self.neg(default_evaluation())
    def test_040_commit_not_executed(self):
        z=default_evaluation(); self.assertEqual(z.commit_result,'CANDIDATE_ONLY'); self.assertFalse(z.commit_executed)

def _gen(k):
    def f(self):
        r,i,p,pl,b,a,s,v,rb,pol=self.base(); mode=k%12
        if mode==0: want=Decision.ALLOW
        elif mode==1: s=(s[0],replace(s[1],status=StepStatus.FAILED)); want=Decision.HOLD
        elif mode==2: v=replace(v,status=VerifyStatus.MISMATCH); want=Decision.HOLD
        elif mode==3: v=replace(v,status=VerifyStatus.TIMEOUT); want=Decision.HOLD
        elif mode==4: s=(replace(s[0],status=StepStatus.EXCEPTION),s[1]); want=Decision.HOLD
        elif mode==5: p=replace(p,observed=False); want=Decision.HOLD
        elif mode==6: p=replace(p,allow_candidate=False); want=Decision.HOLD
        elif mode==7: a=replace(a,observed=False); want=Decision.HOLD
        elif mode==8: v=replace(v,final_state_fingerprint='BAD'); want=Decision.HOLD
        elif mode==9: pol=replace(pol,revoked=True); want=Decision.HOLD
        elif mode==10: s=(s[0],replace(s[1],observed=False)); want=Decision.HOLD
        else: r=replace(r,observed=False); want=Decision.HOLD
        z=evaluate(r,i,p,pl,b,a,s,v,rb,pol); self.assertEqual(z.decision,want); self.neg(z)
    return f
for k in range(120): setattr(T,f'test_regression_{k:03d}',_gen(k))
if __name__=='__main__': unittest.main(verbosity=2)
