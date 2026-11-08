import unittest
from dataclasses import replace
from noepin_al_089_idempotency_guard import *

class T(unittest.TestCase):
    def base(self): return default_request(),default_histories(),default_policy()
    def neg(self,z):
        self.assertFalse(z.request_promoted_to_success); self.assertFalse(z.history_store_mutated); self.assertFalse(z.key_registered)
        self.assertFalse(z.permission_granted); self.assertFalse(z.action_executed); self.assertFalse(z.plan_committed)
        self.assertFalse(z.atomic_publish_executed); self.assertFalse(z.external_write_performed); self.assertFalse(z.receipt_promoted_to_truth)
        self.assertFalse(z.world_truth_proven); self.assertFalse(z.safety_proven); self.assertFalse(z.action_success)
    def mk(self,record_id='H',key='KEY-NEW',intent='INTENT-NEW',action='ACTION-FP-SEND',status=ExecutionStatus.SUCCESS,result='R',observed=True):
        return ExecutionHistoryRecord(record_id,key,intent,action,status,result,observed,'IDEM-BIND','STATE-EPOCH-1')
    def test_001_default_allow(self): z=default_evaluation(); self.assertEqual(z.decision,Decision.ALLOW); self.assertEqual(z.idempotency_state,IdempotencyState.NEW); self.neg(z)
    def test_002_default_registration_candidate(self): self.assertTrue(default_evaluation().history_registration_candidate)
    def test_003_same_key_success_denied(self): r,h,p=self.base(); z=evaluate(r,h+(self.mk(),),p); self.assertEqual(z.decision,Decision.DENY); self.assertEqual(z.idempotency_state,IdempotencyState.REPLAY); self.assertTrue(z.result_reuse_candidate); self.neg(z)
    def test_004_same_key_success_no_result(self): r,h,p=self.base(); z=evaluate(r,h+(self.mk(result=''),),p); self.assertEqual(z.decision,Decision.DENY); self.assertFalse(z.result_reuse_candidate); self.neg(z)
    def test_005_same_key_inflight_hold(self): r,h,p=self.base(); z=evaluate(r,h+(self.mk(status=ExecutionStatus.IN_FLIGHT,result=''),),p); self.assertEqual(z.decision,Decision.HOLD); self.neg(z)
    def test_006_same_key_unknown_hold(self): r,h,p=self.base(); z=evaluate(r,h+(self.mk(status=ExecutionStatus.UNKNOWN,result=''),),p); self.assertEqual(z.decision,Decision.HOLD); self.neg(z)
    def test_007_same_key_failed_retry(self): r,h,p=self.base(); z=evaluate(r,h+(self.mk(status=ExecutionStatus.FAILED,result=''),),p); self.assertEqual(z.decision,Decision.ALLOW); self.assertEqual(z.safe_retry_method,SafeRetryMethod.SAME_KEY_RETRY); self.neg(z)
    def test_008_failed_retry_disabled(self): r,h,p=self.base(); p=replace(p,allow_retry_after_failed_same_key=False); z=evaluate(r,h+(self.mk(status=ExecutionStatus.FAILED,result=''),),p); self.assertEqual(z.decision,Decision.HOLD); self.neg(z)
    def test_009_key_conflict(self): r,h,p=self.base(); z=evaluate(r,h+(self.mk(intent='OTHER'),),p); self.assertEqual(z.decision,Decision.DENY); self.assertEqual(z.idempotency_state,IdempotencyState.KEY_CONFLICT); self.neg(z)
    def test_010_same_intent_other_key_hold(self): r,h,p=self.base(); z=evaluate(r,h+(self.mk(key='OTHER-KEY'),),p); self.assertEqual(z.decision,Decision.HOLD); self.assertEqual(z.idempotency_state,IdempotencyState.DUPLICATE); self.neg(z)
    def test_011_read_retry_no_store(self): r,h,p=self.base(); r=replace(r,side_effecting=False,history_store_available=False,history_complete=False,idempotency_key=''); z=evaluate(r,h,p); self.assertEqual(z.decision,Decision.ALLOW); self.assertEqual(z.safe_retry_method,SafeRetryMethod.READ_RETRY); self.neg(z)
    def test_012_store_unavailable_hold(self): r,h,p=self.base(); z=evaluate(replace(r,history_store_available=False),h,p); self.assertEqual(z.decision,Decision.HOLD); self.neg(z)
    def test_013_history_incomplete_hold(self): r,h,p=self.base(); z=evaluate(replace(r,history_complete=False),h,p); self.assertEqual(z.decision,Decision.HOLD); self.neg(z)
    def test_014_missing_key_hold(self): r,h,p=self.base(); z=evaluate(replace(r,idempotency_key=''),h,p); self.assertEqual(z.decision,Decision.HOLD); self.assertTrue(z.generated_key_candidate.startswith('IDEM-')); self.neg(z)
    def test_015_unobserved_request(self): r,h,p=self.base(); self.assertEqual(evaluate(replace(r,observed=False),h,p).decision,Decision.HOLD)
    def test_016_unobserved_same_key_history(self): r,h,p=self.base(); z=evaluate(r,h+(self.mk(observed=False),),p); self.assertEqual(z.decision,Decision.HOLD); self.neg(z)
    def test_017_revoked_policy(self): r,h,p=self.base(); self.assertEqual(evaluate(r,h,replace(p,revoked=True)).decision,Decision.HOLD)
    def test_018_scope_mismatch_request(self): r,h,p=self.base(); self.assertEqual(evaluate(replace(r,binding='X'),h,p).decision,Decision.HOLD)
    def test_019_scope_mismatch_history(self): r,h,p=self.base(); hh=replace(h[0],binding='X'); self.assertEqual(evaluate(r,(hh,h[1]),p).decision,Decision.HOLD)
    def test_020_duplicate_record_id(self): r,h,p=self.base(); self.assertEqual(evaluate(r,(h[0],h[0]),p).decision,Decision.HOLD)
    def test_021_empty_request_identity(self): r,h,p=self.base(); self.assertEqual(evaluate(replace(r,intent_fingerprint=''),h,p).decision,Decision.HOLD)
    def test_022_incomplete_history_identity(self): r,h,p=self.base(); self.assertEqual(evaluate(r,(replace(h[0],idempotency_key=''),h[1]),p).decision,Decision.HOLD)
    def test_023_generated_key_deterministic(self): r,h,p=self.base(); r=replace(r,idempotency_key=''); self.assertEqual(evaluate(r,h,p).generated_key_candidate,evaluate(r,h,p).generated_key_candidate)
    def test_024_other_failed_same_intent_not_duplicate(self): r,h,p=self.base(); x=self.mk(key='OTHER',status=ExecutionStatus.FAILED,result=''); self.assertEqual(evaluate(r,h+(x,),p).decision,Decision.ALLOW)
    def test_025_sort_deterministic_eval(self): r,h,p=self.base(); self.assertEqual(evaluate(r,h,p),evaluate(r,tuple(reversed(h)),p))
    def test_026_prepare_valid(self): r,h,p=self.base(); st=prepare_state(r,h,p,binding=p.binding,state_epoch=p.state_epoch); self.assertTrue(validate_prepared_integrity(st))
    def test_027_prepare_sorted(self): r,h,p=self.base(); s1=prepare_state(r,h,p,binding=p.binding,state_epoch=p.state_epoch); s2=prepare_state(r,tuple(reversed(h)),p,binding=p.binding,state_epoch=p.state_epoch); self.assertEqual(s1,s2)
    def test_028_prepared_eval(self): r,h,p=self.base(); st=prepare_state(r,h,p,binding=p.binding,state_epoch=p.state_epoch); z=evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True); self.assertEqual(z,evaluate(r,h,p))
    def test_029_prepared_integrity_required(self): r,h,p=self.base(); st=prepare_state(r,h,p,binding=p.binding,state_epoch=p.state_epoch); z=evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=False); self.assertEqual(z.decision,Decision.HOLD)
    def test_030_prepared_stale_history(self): r,h,p=self.base(); st=prepare_state(r,h,p,binding=p.binding,state_epoch=p.state_epoch); z=evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint='X',current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True); self.assertEqual(z.decision,Decision.HOLD)
    def test_031_delta_reconstruction(self): r,h,p=self.base(); s1=prepare_state(r,h,p,binding=p.binding,state_epoch=p.state_epoch); h2=(replace(h[0],result_fingerprint='R2'),h[1]); s2=prepare_state(r,h2,p,binding=p.binding,state_epoch=p.state_epoch); self.assertEqual(apply_delta(s1,make_delta(s1,s2)),s2)
    def test_032_delta_base_mismatch(self): r,h,p=self.base(); s1=prepare_state(r,h,p,binding=p.binding,state_epoch=p.state_epoch); s2=prepare_state(r,h+(self.mk(record_id='X',key='X',intent='X',action='X'),),p,binding=p.binding,state_epoch=p.state_epoch); d=make_delta(s1,s2); bad=replace(d,base_fingerprint='X'); self.assertRaises(ValueError,apply_delta,s1,bad)
    def test_033_missing_only(self): r,_,p=self.base(); hs=tuple(self.mk(record_id=f'H{n}',key=f'K{n}',intent=f'I{n}',action=f'A{n}',status=ExecutionStatus.FAILED,result='') for n in range(20)); st=prepare_state(r,hs,p,binding=p.binding,state_epoch=p.state_epoch); known=dict(st.history_fingerprints); [known.pop(f'H{n}') for n in range(5)]; plan=missing_only_sync_plan(st,known); self.assertEqual(len(plan.missing_or_changed_record_ids),5); self.assertFalse(plan.full_resend_required)
    def test_034_delta_smaller(self): r,_,p=self.base(); hs=tuple(self.mk(record_id=f'H{n}',key=f'K{n}',intent=f'I{n}',action=f'A{n}',status=ExecutionStatus.FAILED,result='') for n in range(100)); s1=prepare_state(r,hs,p,binding=p.binding,state_epoch=p.state_epoch); h2=list(hs); h2[0]=replace(h2[0],result_fingerprint='X'); s2=prepare_state(r,tuple(h2),p,binding=p.binding,state_epoch=p.state_epoch); self.assertLess(delta_bytes(make_delta(s1,s2)),full_registry_bytes(s2))
    def test_035_history_change_changes_fp(self): r,h,p=self.base(); s1=prepare_state(r,h,p,binding=p.binding,state_epoch=p.state_epoch); s2=prepare_state(r,(replace(h[0],status=ExecutionStatus.UNKNOWN),h[1]),p,binding=p.binding,state_epoch=p.state_epoch); self.assertNotEqual(s1.dependency_fingerprint,s2.dependency_fingerprint)
    def test_036_policy_change_changes_fp(self): r,h,p=self.base(); s1=prepare_state(r,h,p,binding=p.binding,state_epoch=p.state_epoch); p2=replace(p,allow_retry_after_failed_same_key=False); s2=prepare_state(r,h,p2,binding=p2.binding,state_epoch=p2.state_epoch); self.assertNotEqual(s1.policy_fingerprint,s2.policy_fingerprint)
    def test_037_result_reuse_not_success(self): r,h,p=self.base(); z=evaluate(r,h+(self.mk(),),p); self.assertTrue(z.result_reuse_candidate); self.assertFalse(z.action_success); self.assertFalse(z.receipt_promoted_to_truth)
    def test_038_new_candidate_not_execution(self): z=default_evaluation(); self.assertTrue(z.next_gate_candidate); self.assertFalse(z.action_executed); self.assertFalse(z.history_store_mutated)
    def test_039_read_retry_not_execution(self): r,h,p=self.base(); z=evaluate(replace(r,side_effecting=False,idempotency_key=''),h,p); self.assertTrue(z.retry_candidate); self.assertFalse(z.action_executed)
    def test_040_authority_flags_false(self): self.neg(default_evaluation())

def _gen(k):
    def f(self):
        r,h,p=self.base(); mode=k%12
        if mode==0: want=Decision.ALLOW
        elif mode==1: h=h+(self.mk(record_id=f'S{k}'),); want=Decision.DENY
        elif mode==2: h=h+(self.mk(record_id=f'D{k}',key=f'OTHER{k}'),); want=Decision.HOLD
        elif mode==3: r=replace(r,side_effecting=False,history_store_available=False,history_complete=False,idempotency_key=''); want=Decision.ALLOW
        elif mode==4: r=replace(r,history_store_available=False); want=Decision.HOLD
        elif mode==5: r=replace(r,history_complete=False); want=Decision.HOLD
        elif mode==6: r=replace(r,idempotency_key=''); want=Decision.HOLD
        elif mode==7: h=h+(self.mk(record_id=f'F{k}',status=ExecutionStatus.FAILED,result=''),); want=Decision.ALLOW
        elif mode==8: h=h+(self.mk(record_id=f'I{k}',status=ExecutionStatus.IN_FLIGHT,result=''),); want=Decision.HOLD
        elif mode==9: p=replace(p,revoked=True); want=Decision.HOLD
        elif mode==10: r=replace(r,observed=False); want=Decision.HOLD
        else: h=h+(self.mk(record_id=f'C{k}',intent='OTHER'),); want=Decision.DENY
        z=evaluate(r,h,p); self.assertEqual(z.decision,want); self.neg(z)
    return f
for k in range(120): setattr(T,f'test_regression_{k:03d}',_gen(k))

if __name__=='__main__': unittest.main(verbosity=2)
