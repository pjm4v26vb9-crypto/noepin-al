import unittest
from dataclasses import replace
from noepin_al_074_sequential_risk_composer import *
NOW=1_800_000_000

def base():
    return default_policy(),default_actions(NOW),default_rules(),default_request()

def add_action(actions, action): return tuple(actions)+(action,)

def with_seq(req,*ids): return replace(req,sequence=tuple(ids))

class T(unittest.TestCase):
    def test_001_low_risk_allow(self):
        p,a,r,q=base(); z=evaluate(q,p,a,r); self.assertEqual(z.decision,Decision.ALLOW); self.assertTrue(z.next_gate_candidate)
    def test_002_budget_exceed_hold(self):
        p,a,r,q=base(); q=with_seq(q,'A-READ','A-ANALYZE','A-WRITE','A-SEND'); self.assertEqual(evaluate(q,p,a,r).decision,Decision.HOLD)
    def test_003_hard_pair_deny(self):
        p,a,r,q=base(); a=add_action(a,ActionRisk('A-DELETE','DELETE',1000,NOW-5,(),True,'RISK-BIND','STATE-EPOCH-1')); q=with_seq(q,'A-DELETE','A-SEND'); self.assertEqual(evaluate(q,p,a,r).decision,Decision.DENY)
    def test_004_unknown_pair_uplift(self):
        p,a,r,q=base(); a=add_action(a,ActionRisk('A-X','UNKNOWNX',1000,NOW-5,(),True,'RISK-BIND','STATE-EPOCH-1')); q=with_seq(q,'A-READ','A-X'); z=evaluate(q,p,a,r); self.assertGreaterEqual(z.unknown_interaction_risk,p.unknown_interaction_risk)
    def test_005_time_decay(self):
        p,a,r,q=base(); old=ActionRisk('A-OLD','READ',5000,NOW-1000,(),True,'RISK-BIND','STATE-EPOCH-1'); a=add_action(a,old); q=replace(q,sequence=('A-OLD','A-ANALYZE'),time_window_seconds=2000); z=evaluate(q,p,a,r); self.assertLess(z.contributions[0].effective_base_risk,5000)
    def test_006_outside_window_zero(self):
        p,a,r,q=base(); old=ActionRisk('A-OLD','READ',5000,NOW-1000,(),True,'RISK-BIND','STATE-EPOCH-1'); a=add_action(a,old); q=replace(q,sequence=('A-OLD','A-ANALYZE'),time_window_seconds=100); z=evaluate(q,p,a,r); self.assertEqual(z.contributions[0].effective_base_risk,0)
    def test_007_unobserved_hold(self):
        p,a,r,q=base(); a=tuple(replace(x,observed=False) if x.action_id=='A-READ' else x for x in a); self.assertEqual(evaluate(q,p,a,r).decision,Decision.HOLD)
    def test_008_unknown_action_hold(self):
        p,a,r,q=base(); q=with_seq(q,'MISSING'); self.assertEqual(evaluate(q,p,a,r).decision,Decision.HOLD)
    def test_009_duplicate_sequence_hold(self):
        p,a,r,q=base(); q=replace(q,sequence=('A-READ','A-READ')); self.assertEqual(evaluate(q,p,a,r).decision,Decision.HOLD)
    def test_010_dependency_order_hold(self):
        p,a,r,q=base(); q=with_seq(q,'A-ANALYZE','A-READ'); self.assertEqual(evaluate(q,p,a,r).decision,Decision.HOLD)
    def test_011_policy_revoked_hold(self):
        p,a,r,q=base(); p=replace(p,revoked=True); self.assertEqual(evaluate(q,p,a,r).decision,Decision.HOLD)
    def test_012_binding_hold(self):
        p,a,r,q=base(); q=replace(q,binding='X'); self.assertEqual(evaluate(q,p,a,r).decision,Decision.HOLD)
    def test_013_epoch_hold(self):
        p,a,r,q=base(); q=replace(q,state_epoch='X'); self.assertEqual(evaluate(q,p,a,r).decision,Decision.HOLD)
    def test_014_sequence_length_hold(self):
        p,a,r,q=base(); p=replace(p,max_sequence_length=1); self.assertEqual(evaluate(q,p,a,r).decision,Decision.HOLD)
    def test_015_single_action_hard_deny(self):
        p,a,r,q=base(); x=ActionRisk('A-HUGE','READ',p.deny_threshold+1,NOW,(),True,'RISK-BIND','STATE-EPOCH-1'); a=add_action(a,x); q=with_seq(q,'A-HUGE'); self.assertEqual(evaluate(q,p,a,r).decision,Decision.DENY)
    def test_016_no_authority_promotion(self):
        p,a,r,q=base(); z=evaluate(q,p,a,r); self.assertFalse(z.permission_granted); self.assertFalse(z.tool_executed); self.assertFalse(z.action_success); self.assertFalse(z.safety_proven)
    def test_017_prepare_valid(self):
        p,a,r,q=base(); st=prepare_state(p,a,r,binding=p.binding); self.assertTrue(validate_prepared_integrity(st))
    def test_018_prepared_semantic_match(self):
        p,a,r,q=base(); st=prepare_state(p,a,r,binding=p.binding); z1=evaluate(q,p,a,r); z2=evaluate_prepared(q,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True); self.assertEqual((z1.decision,z1.reasons,z1.cumulative_risk),(z2.decision,z2.reasons,z2.cumulative_risk))
    def test_019_prepared_integrity_required(self):
        p,a,r,q=base(); st=prepare_state(p,a,r,binding=p.binding); self.assertEqual(evaluate_prepared(q,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=False).decision,Decision.HOLD)
    def test_020_policy_fp_mismatch_hold(self):
        p,a,r,q=base(); st=prepare_state(p,a,r,binding=p.binding); self.assertEqual(evaluate_prepared(q,st,current_policy_fingerprint='x',current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True).decision,Decision.HOLD)
    def test_021_registry_fp_mismatch_hold(self):
        p,a,r,q=base(); st=prepare_state(p,a,r,binding=p.binding); self.assertEqual(evaluate_prepared(q,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint='x',prepared_integrity_validated=True).decision,Decision.HOLD)
    def test_022_tampered_action_integrity_false(self):
        p,a,r,q=base(); st=prepare_state(p,a,r,binding=p.binding); bad=replace(st,actions=(replace(st.actions[0],base_risk=9999),)+st.actions[1:]); self.assertFalse(validate_prepared_integrity(bad))
    def test_023_tampered_rule_integrity_false(self):
        p,a,r,q=base(); st=prepare_state(p,a,r,binding=p.binding); bad=replace(st,rules=(replace(st.rules[0],risk_delta=777),)+st.rules[1:]); self.assertFalse(validate_prepared_integrity(bad))
    def test_024_delta_roundtrip(self):
        p,a,r,q=base(); s1=prepare_state(p,a,r,binding=p.binding); a2=tuple(replace(x,base_risk=x.base_risk+1) if x.action_id=='A-READ' else x for x in a); s2=prepare_state(p,a2,r,binding=p.binding); d=make_delta(s1,s2); self.assertEqual(apply_delta(s1,d).registry_fingerprint,s2.registry_fingerprint)
    def test_025_missing_sync(self):
        p,a,r,q=base(); st=prepare_state(p,a,r,binding=p.binding); ra=dict(st.action_fingerprints); rr=dict(st.rule_fingerprints); ra.pop('A-READ'); plan=missing_only_sync_plan(st,ra,rr); self.assertIn('A-READ',plan.missing_or_changed_actions); self.assertFalse(plan.full_resend_required)
    def test_026_rule_binding_invalid_input(self):
        p,a,r,q=base(); r=(replace(r[0],binding='X'),)+r[1:]; self.assertEqual(evaluate(q,p,a,r).decision,Decision.HOLD)
    def test_027_action_binding_hold(self):
        p,a,r,q=base(); a=tuple(replace(x,binding='X') if x.action_id=='A-READ' else x for x in a); self.assertEqual(evaluate(q,p,a,r).decision,Decision.HOLD)
    def test_028_future_time_hold(self):
        p,a,r,q=base(); a=tuple(replace(x,occurred_at=NOW+100) if x.action_id=='A-READ' else x for x in a); self.assertEqual(evaluate(q,p,a,r).decision,Decision.HOLD)
    def test_029_unknown_dependency_hold(self):
        p,a,r,q=base(); a=tuple(replace(x,dependencies=('MISSING',)) if x.action_id=='A-ANALYZE' else x for x in a); self.assertEqual(evaluate(q,p,a,r).decision,Decision.HOLD)
    def test_030_known_synergy_added(self):
        p,a,r,q=base(); q=with_seq(q,'A-ANALYZE','A-WRITE'); z=evaluate(q,p,a,r); self.assertGreater(z.synergy_risk,0)
    def test_031_deny_threshold(self):
        p,a,r,q=base(); p=replace(p,risk_budget=5000,deny_threshold=6000); q=with_seq(q,'A-WRITE','A-SEND'); self.assertEqual(evaluate(q,p,a,r).decision,Decision.DENY)
    def test_032_budget_hold_not_permission(self):
        p,a,r,q=base(); p=replace(p,risk_budget=7000); q=with_seq(q,'A-WRITE','A-SEND'); z=evaluate(q,p,a,r); self.assertIn(z.decision,(Decision.HOLD,Decision.DENY)); self.assertFalse(z.permission_granted)
    def test_033_prepare_rejects_bad_binding(self):
        p,a,r,q=base();
        with self.assertRaises(ValueError): prepare_state(p,a,r,binding='X')
    def test_034_delta_rejects_bad_base(self):
        p,a,r,q=base(); s=prepare_state(p,a,r,binding=p.binding); bad=replace(s,registry_fingerprint='x')
        with self.assertRaises(ValueError): make_delta(bad,s)
    def test_035_unknown_upper_bound_can_stop(self):
        p,a,r,q=base(); x=ActionRisk('A-X','X',4500,NOW-1,(),True,'RISK-BIND','STATE-EPOCH-1'); y=ActionRisk('A-Y','Y',4500,NOW,(),True,'RISK-BIND','STATE-EPOCH-1'); a=add_action(add_action(a,x),y); q=with_seq(q,'A-X','A-Y'); z=evaluate(q,p,a,r); self.assertEqual(z.decision,Decision.HOLD); self.assertGreater(z.unknown_interaction_risk,0)
    def test_036_empty_sequence_hold(self):
        p,a,r,q=base(); q=replace(q,sequence=()); self.assertEqual(evaluate(q,p,a,r).decision,Decision.HOLD)
    def test_037_invalid_time_window_hold(self):
        p,a,r,q=base(); q=replace(q,time_window_seconds=0); self.assertEqual(evaluate(q,p,a,r).decision,Decision.HOLD)
    def test_038_duplicate_action_registry_hold(self):
        p,a,r,q=base(); a=a+(a[0],); self.assertEqual(evaluate(q,p,a,r).decision,Decision.HOLD)
    def test_039_duplicate_rule_registry_hold(self):
        p,a,r,q=base(); r=r+(r[0],); self.assertEqual(evaluate(q,p,a,r).decision,Decision.HOLD)
    def test_040_stop_point_first_exceed(self):
        p,a,r,q=base(); q=with_seq(q,'A-READ','A-ANALYZE','A-WRITE','A-SEND'); z=evaluate(q,p,a,r); self.assertIsNotNone(z.stop_point); self.assertEqual(z.stop_action_id,q.sequence[z.stop_point])

def _gen(i):
    def f(self):
        p,a,r,q=base(); m=i%8
        if m==0:
            q=with_seq(q,'A-READ','A-ANALYZE'); want=Decision.ALLOW
        elif m==1:
            q=with_seq(q,'A-READ','A-ANALYZE','A-WRITE','A-SEND'); want=Decision.HOLD
        elif m==2:
            x=ActionRisk(f'X{i}','X',1000,NOW-1,(),True,'RISK-BIND','STATE-EPOCH-1'); a=add_action(a,x); q=with_seq(q,'A-READ',f'X{i}'); want=Decision.ALLOW
        elif m==3:
            a=tuple(replace(x,observed=False) if x.action_id=='A-READ' else x for x in a); want=Decision.HOLD
        elif m==4:
            q=replace(q,binding=f'BAD{i}'); want=Decision.HOLD
        elif m==5:
            p=replace(p,risk_budget=2500); q=with_seq(q,'A-READ','A-ANALYZE'); want=Decision.HOLD
        elif m==6:
            x=ActionRisk(f'D{i}','DELETE',1000,NOW-1,(),True,'RISK-BIND','STATE-EPOCH-1'); a=add_action(a,x); q=with_seq(q,f'D{i}','A-SEND'); want=Decision.DENY
        else:
            q=with_seq(q,'A-ANALYZE','A-WRITE'); want=Decision.ALLOW
        z=evaluate(q,p,a,r); self.assertEqual(z.decision,want)
        self.assertFalse(z.risk_budget_spent); self.assertFalse(z.permission_granted); self.assertFalse(z.human_approval_executed); self.assertFalse(z.tool_executed); self.assertFalse(z.transaction_committed); self.assertFalse(z.external_write_performed); self.assertFalse(z.world_truth_proven); self.assertFalse(z.safety_proven); self.assertFalse(z.action_success)
    return f
for i in range(120): setattr(T,f'test_regression_{i:03d}',_gen(i))

if __name__=='__main__': unittest.main()
