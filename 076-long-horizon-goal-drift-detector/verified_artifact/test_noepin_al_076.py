import unittest
from dataclasses import replace
from noepin_al_076_long_horizon_goal_drift_detector import *

START=1_800_000_000
def base(): return default_policy(),default_goals(),default_steps(START),default_plans(),default_checkpoints(),default_request(START)

def assert_neg(t,z):
    t.assertFalse(z.permission_granted); t.assertFalse(z.goal_baseline_mutated); t.assertFalse(z.human_approval_executed); t.assertFalse(z.tool_executed); t.assertFalse(z.transaction_committed); t.assertFalse(z.external_write_performed); t.assertFalse(z.world_truth_proven); t.assertFalse(z.safety_proven); t.assertFalse(z.action_success)

class T(unittest.TestCase):
    def test_001_stable_long_task_allow(self):
        p,g,s,pl,c,q=base(); z=evaluate(q,p,g,s,pl,c); self.assertEqual(z.decision,Decision.ALLOW); self.assertTrue(z.next_gate_candidate); assert_neg(self,z)
    def test_002_gradual_drift_hold(self):
        p,g,s,pl,c,q=base(); extra=tuple(StepRecord(f'S-U{i}',START+100+i,(f'UNRELATED{i}',),True,p.binding,p.state_epoch) for i in range(8)); s=s+extra; q=replace(q,step_history=tuple(x.step_id for x in extra),evaluation_time=START+200); z=evaluate(q,p,g,s,pl,c); self.assertEqual(z.decision,Decision.HOLD); self.assertIn('CUMULATIVE_GOAL_DRIFT_THRESHOLD_EXCEEDED',z.reasons)
    def test_003_acute_reverse_deny(self):
        p,g,s,pl,c,q=base(); q=replace(q,step_history=('S-READ','S-SEND')); z=evaluate(q,p,g,s,pl,c); self.assertEqual(z.decision,Decision.DENY); self.assertIn('ACUTE_REVERSE_GOAL_DRIFT',z.reasons)
    def test_004_legitimate_committed_goal_change_allow(self):
        p,g,s,pl,c,q=base(); q=replace(q,step_history=('S-READ','S-ANALYZE','S-SUMMARY','S-SEND'),current_plan_id='P-SEND',checkpoint_id='CP-EXTERNAL-COMMITTED'); z=evaluate(q,p,g,s,pl,c); self.assertEqual(z.decision,Decision.ALLOW); self.assertEqual(z.effective_goal_id,'G-EXTERNAL-SHARE'); self.assertTrue(z.baseline_update_candidate); assert_neg(self,z)
    def test_005_goal_missing_hold(self):
        p,g,s,pl,c,q=base(); q=replace(q,original_goal_id='MISSING'); self.assertEqual(evaluate(q,p,g,s,pl,c).decision,Decision.HOLD)
    def test_006_step_unobserved_hold(self):
        p,g,s,pl,c,q=base(); s=tuple(replace(x,observed=False) if x.step_id=='S-READ' else x for x in s); self.assertEqual(evaluate(q,p,g,s,pl,c).decision,Decision.HOLD)
    def test_007_step_unknown_hold(self):
        p,g,s,pl,c,q=base(); q=replace(q,step_history=('MISSING',)); self.assertEqual(evaluate(q,p,g,s,pl,c).decision,Decision.HOLD)
    def test_008_future_step_hold(self):
        p,g,s,pl,c,q=base(); s=tuple(replace(x,timestamp=START+1000) if x.step_id=='S-READ' else x for x in s); self.assertEqual(evaluate(q,p,g,s,pl,c).decision,Decision.HOLD)
    def test_009_time_order_hold(self):
        p,g,s,pl,c,q=base(); q=replace(q,step_history=('S-SUMMARY','S-READ')); self.assertEqual(evaluate(q,p,g,s,pl,c).decision,Decision.HOLD)
    def test_010_duplicate_history_hold(self):
        p,g,s,pl,c,q=base(); q=replace(q,step_history=('S-READ','S-READ')); self.assertEqual(evaluate(q,p,g,s,pl,c).decision,Decision.HOLD)
    def test_011_history_empty_hold(self):
        p,g,s,pl,c,q=base(); q=replace(q,step_history=()); self.assertEqual(evaluate(q,p,g,s,pl,c).decision,Decision.HOLD)
    def test_012_history_limit_hold(self):
        p,g,s,pl,c,q=base(); p=replace(p,max_steps=2); self.assertEqual(evaluate(q,p,g,s,pl,c).decision,Decision.HOLD)
    def test_013_current_plan_unknown_hold(self):
        p,g,s,pl,c,q=base(); q=replace(q,current_plan_id='MISSING'); self.assertEqual(evaluate(q,p,g,s,pl,c).decision,Decision.HOLD)
    def test_014_current_plan_unobserved_hold(self):
        p,g,s,pl,c,q=base(); pl=tuple(replace(x,observed=False) if x.plan_id=='P-STABLE' else x for x in pl); self.assertEqual(evaluate(q,p,g,s,pl,c).decision,Decision.HOLD)
    def test_015_current_plan_reverse_deny(self):
        p,g,s,pl,c,q=base(); q=replace(q,current_plan_id='P-SEND'); self.assertEqual(evaluate(q,p,g,s,pl,c).decision,Decision.DENY)
    def test_016_current_plan_high_drift_hold(self):
        p,g,s,pl,c,q=base(); pl=pl+(PlanRecord('P-HIGH',('FORMAT','RENAME','ARCHIVE'),True,p.binding,p.state_epoch),); q=replace(q,current_plan_id='P-HIGH'); z=evaluate(q,p,g,s,pl,c); self.assertEqual(z.decision,Decision.HOLD); self.assertIn('CURRENT_PLAN_DRIFT_HIGH',z.reasons)
    def test_017_checkpoint_unknown_hold(self):
        p,g,s,pl,c,q=base(); q=replace(q,checkpoint_id='MISSING'); self.assertEqual(evaluate(q,p,g,s,pl,c).decision,Decision.HOLD)
    def test_018_checkpoint_unobserved_hold(self):
        p,g,s,pl,c,q=base(); c=tuple(replace(x,observed=False) if x.checkpoint_id=='CP-STABLE' else x for x in c); q=replace(q,checkpoint_id='CP-STABLE'); self.assertEqual(evaluate(q,p,g,s,pl,c).decision,Decision.HOLD)
    def test_019_checkpoint_revoked_hold(self):
        p,g,s,pl,c,q=base(); c=tuple(replace(x,revoked=True) if x.checkpoint_id=='CP-STABLE' else x for x in c); q=replace(q,checkpoint_id='CP-STABLE'); self.assertEqual(evaluate(q,p,g,s,pl,c).decision,Decision.HOLD)
    def test_020_checkpoint_nonindependent_goal_change_hold(self):
        p,g,s,pl,c,q=base(); c=tuple(replace(x,independent_authority=False) if x.checkpoint_id=='CP-EXTERNAL-COMMITTED' else x for x in c); q=replace(q,checkpoint_id='CP-EXTERNAL-COMMITTED'); self.assertEqual(evaluate(q,p,g,s,pl,c).decision,Decision.HOLD)
    def test_021_uncommitted_changed_checkpoint_hold(self):
        p,g,s,pl,c,q=base(); cp=CheckpointRecord('CP-BAD','G-EXTERNAL-SHARE','S-SUMMARY',True,False,True,True,False,p.binding,p.state_epoch); q=replace(q,checkpoint_id='CP-BAD'); self.assertEqual(evaluate(q,p,g,s,pl,c+(cp,)).decision,Decision.HOLD)
    def test_022_registry_binding_hold(self):
        p,g,s,pl,c,q=base(); s=tuple(replace(x,binding='BAD') if x.step_id=='S-READ' else x for x in s); self.assertEqual(evaluate(q,p,g,s,pl,c).decision,Decision.HOLD)
    def test_023_request_binding_hold(self):
        p,g,s,pl,c,q=base(); q=replace(q,binding='BAD'); self.assertEqual(evaluate(q,p,g,s,pl,c).decision,Decision.HOLD)
    def test_024_policy_revoked_hold(self):
        p,g,s,pl,c,q=base(); p=replace(p,revoked=True); self.assertEqual(evaluate(q,p,g,s,pl,c).decision,Decision.HOLD)
    def test_025_invalid_policy_threshold_hold(self):
        p,g,s,pl,c,q=base(); p=replace(p,warning_drift=-1); self.assertEqual(evaluate(q,p,g,s,pl,c).decision,Decision.HOLD)
    def test_026_prepare_and_integrity(self):
        p,g,s,pl,c,q=base(); st=prepare_state(p,g,s,pl,c,binding=p.binding); self.assertTrue(validate_prepared_integrity(st))
    def test_027_prepared_semantics(self):
        p,g,s,pl,c,q=base(); st=prepare_state(p,g,s,pl,c,binding=p.binding); z1=evaluate(q,p,g,s,pl,c); z2=evaluate_prepared(q,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True); self.assertEqual((z1.decision,z1.reasons,z1.drift_curve),(z2.decision,z2.reasons,z2.drift_curve))
    def test_028_prepared_unvalidated_hold(self):
        p,g,s,pl,c,q=base(); st=prepare_state(p,g,s,pl,c,binding=p.binding); self.assertEqual(evaluate_prepared(q,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=False).decision,Decision.HOLD)
    def test_029_prepared_policy_changed_hold(self):
        p,g,s,pl,c,q=base(); st=prepare_state(p,g,s,pl,c,binding=p.binding); self.assertEqual(evaluate_prepared(q,st,current_policy_fingerprint='BAD',current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True).decision,Decision.HOLD)
    def test_030_prepared_registry_changed_hold(self):
        p,g,s,pl,c,q=base(); st=prepare_state(p,g,s,pl,c,binding=p.binding); self.assertEqual(evaluate_prepared(q,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint='BAD',prepared_integrity_validated=True).decision,Decision.HOLD)
    def test_031_tampered_prepared_integrity_false(self):
        p,g,s,pl,c,q=base(); st=prepare_state(p,g,s,pl,c,binding=p.binding); st=replace(st,registry_fingerprint='BAD'); self.assertFalse(validate_prepared_integrity(st))
    def test_032_delta_roundtrip(self):
        p,g,s,pl,c,q=base(); a=prepare_state(p,g,s,pl,c,binding=p.binding); s2=tuple(replace(x,effect_tags=('READ','ANALYZE')) if x.step_id=='S-READ' else x for x in s); b=prepare_state(p,g,s2,pl,c,binding=p.binding); d=make_delta(a,b); self.assertEqual(apply_delta(a,d).registry_fingerprint,b.registry_fingerprint)
    def test_033_missing_only_sync(self):
        p,g,s,pl,c,q=base(); st=prepare_state(p,g,s,pl,c,binding=p.binding); rg=dict(st.goal_fingerprints); rs=dict(st.step_fingerprints); rp=dict(st.plan_fingerprints); rc=dict(st.checkpoint_fingerprints); rs.pop('S-READ'); plan=missing_only_sync_plan(st,rg,rs,rp,rc); self.assertIn('S-READ',plan.missing_or_changed_steps); self.assertFalse(plan.full_resend_required)
    def test_034_authority_negatives(self):
        p,g,s,pl,c,q=base(); assert_neg(self,evaluate(q,p,g,s,pl,c))
    def test_035_temporary_warning_allow(self):
        p,g,s,pl,c,q=base(); q=replace(q,step_history=('S-READ','S-SUMMARY','S-UNRELATED-1')); z=evaluate(q,p,g,s,pl,c); self.assertEqual(z.decision,Decision.ALLOW); self.assertTrue(z.warning)
    def test_036_external_checkpoint_does_not_mutate(self):
        p,g,s,pl,c,q=base(); q=replace(q,step_history=('S-READ','S-ANALYZE','S-SUMMARY','S-SEND'),current_plan_id='P-SEND',checkpoint_id='CP-EXTERNAL-COMMITTED'); z=evaluate(q,p,g,s,pl,c); self.assertTrue(z.baseline_update_candidate); self.assertFalse(z.goal_baseline_mutated); self.assertFalse(z.human_approval_executed)
    def test_037_checkpoint_goal_unknown_registry_hold(self):
        p,g,s,pl,c,q=base(); c=c+(CheckpointRecord('CP-X','MISSING',None,True,True,True,True,False,p.binding,p.state_epoch),); self.assertEqual(evaluate(q,p,g,s,pl,c).decision,Decision.HOLD)
    def test_038_duplicate_step_registry_hold(self):
        p,g,s,pl,c,q=base(); self.assertEqual(evaluate(q,p,g,s+(s[0],),pl,c).decision,Decision.HOLD)
    def test_039_invalid_typed_input_hold(self):
        p,g,s,pl,c,q=base(); self.assertEqual(evaluate({'x':1},p,g,s,pl,c).decision,Decision.HOLD)
    def test_040_prepare_bad_binding_raises(self):
        p,g,s,pl,c,q=base();
        with self.assertRaises(ValueError): prepare_state(p,g,s,pl,c,binding='BAD')

def _gen(i):
    def f(self):
        p,g,s,pl,c,q=base(); m=i%10
        if m==0: want=Decision.ALLOW
        elif m==1: q=replace(q,step_history=('S-READ','S-SEND')); want=Decision.DENY
        elif m==2: q=replace(q,current_plan_id='P-SEND'); want=Decision.DENY
        elif m==3: q=replace(q,binding=f'BAD{i}'); want=Decision.HOLD
        elif m==4: s=tuple(replace(x,observed=False) if x.step_id=='S-READ' else x for x in s); want=Decision.HOLD
        elif m==5: q=replace(q,step_history=('S-READ','S-SUMMARY','S-UNRELATED-1')); want=Decision.ALLOW
        elif m==6: q=replace(q,step_history=('S-READ','S-ANALYZE','S-SUMMARY','S-SEND'),current_plan_id='P-SEND',checkpoint_id='CP-EXTERNAL-COMMITTED'); want=Decision.ALLOW
        elif m==7: q=replace(q,checkpoint_id='MISSING'); want=Decision.HOLD
        elif m==8: q=replace(q,original_goal_id='MISSING'); want=Decision.HOLD
        else: q=replace(q,step_history=('S-SUMMARY','S-READ')); want=Decision.HOLD
        z=evaluate(q,p,g,s,pl,c); self.assertEqual(z.decision,want); assert_neg(self,z)
    return f
for i in range(120): setattr(T,f'test_regression_{i:03d}',_gen(i))
if __name__=='__main__': unittest.main()
