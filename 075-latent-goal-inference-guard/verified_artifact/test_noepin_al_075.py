import unittest
from dataclasses import replace
from noepin_al_075_latent_goal_inference_guard import *

def base(): return default_policy(),default_goals(),default_effects(),default_actions(),default_approvals(),default_request()
class T(unittest.TestCase):
    def test_001_goal_match(self):
        p,g,e,a,ap,q=base(); z=evaluate(q,p,g,e,a,ap); self.assertEqual(z.decision,Decision.ALLOW); self.assertTrue(z.next_gate_candidate)
    def test_002_hidden_external_send_deny(self):
        p,g,e,a,ap,q=base(); q=replace(q,action_sequence=('A-READ','A-ANALYZE','A-SEND')); z=evaluate(q,p,g,e,a,ap); self.assertEqual(z.decision,Decision.DENY)
    def test_003_delete_against_goal_deny(self):
        p,g,e,a,ap,q=base(); q=replace(q,action_sequence=('A-READ','A-DELETE')); self.assertEqual(evaluate(q,p,g,e,a,ap).decision,Decision.DENY)
    def test_004_privilege_against_goal_deny(self):
        p,g,e,a,ap,q=base(); q=replace(q,action_sequence=('A-READ','A-ESCALATE')); self.assertEqual(evaluate(q,p,g,e,a,ap).decision,Decision.DENY)
    def test_005_ambiguous_high_impact_hold(self):
        p,g,e,a,ap,q=base(); extra=GoalSpec('G-EXTERNAL-SHARE-ALT',('READ','ANALYZE','EXTERNAL_SEND'),('DELETE',),True,p.binding,p.state_epoch); g=g+(extra,); q=replace(q,user_goal_id='G-EXTERNAL-SHARE',action_sequence=('A-READ','A-ANALYZE','A-SEND')); self.assertEqual(evaluate(q,p,g,e,a,ap).decision,Decision.HOLD)
    def test_006_unobserved_action_hold(self):
        p,g,e,a,ap,q=base(); a=tuple(replace(x,observed=False) if x.action_id=='A-READ' else x for x in a); self.assertEqual(evaluate(q,p,g,e,a,ap).decision,Decision.HOLD)
    def test_007_unobserved_effect_hold(self):
        p,g,e,a,ap,q=base(); e=tuple(replace(x,observed=False) if x.effect_id=='E-READ' else x for x in e); self.assertEqual(evaluate(q,p,g,e,a,ap).decision,Decision.HOLD)
    def test_008_unknown_action_hold(self):
        p,g,e,a,ap,q=base(); q=replace(q,action_sequence=('MISSING',)); self.assertEqual(evaluate(q,p,g,e,a,ap).decision,Decision.HOLD)
    def test_009_empty_sequence_hold(self):
        p,g,e,a,ap,q=base(); q=replace(q,action_sequence=()); self.assertEqual(evaluate(q,p,g,e,a,ap).decision,Decision.HOLD)
    def test_010_empty_surface_hold(self):
        p,g,e,a,ap,q=base(); q=replace(q,surface_request=''); self.assertEqual(evaluate(q,p,g,e,a,ap).decision,Decision.HOLD)
    def test_011_goal_change_human_approval_candidate(self):
        p,g,e,a,ap,q=base(); q=replace(q,user_goal_id='G-PRESERVE',action_sequence=('A-READ','A-ANALYZE','A-SEND'),goal_change_requested=True,requested_goal_id='G-EXTERNAL-SHARE',approval_evidence_id='APR-GOAL-CHANGE'); z=evaluate(q,p,g,e,a,ap); self.assertEqual(z.decision,Decision.HUMAN_APPROVAL); self.assertTrue(z.human_approval_candidate); self.assertFalse(z.human_approval_executed)
    def test_012_bad_approval_not_human_approval(self):
        p,g,e,a,ap,q=base(); ap=(replace(ap[0],valid=False),); q=replace(q,user_goal_id='G-PRESERVE',action_sequence=('A-READ','A-ANALYZE','A-SEND'),goal_change_requested=True,requested_goal_id='G-EXTERNAL-SHARE',approval_evidence_id='APR-GOAL-CHANGE'); self.assertEqual(evaluate(q,p,g,e,a,ap).decision,Decision.HOLD)
    def test_013_unknown_user_goal_hold(self):
        p,g,e,a,ap,q=base(); q=replace(q,user_goal_id='MISSING'); self.assertEqual(evaluate(q,p,g,e,a,ap).decision,Decision.HOLD)
    def test_014_duplicate_sequence_hold(self):
        p,g,e,a,ap,q=base(); q=replace(q,action_sequence=('A-READ','A-READ')); self.assertEqual(evaluate(q,p,g,e,a,ap).decision,Decision.HOLD)
    def test_015_request_binding_hold(self):
        p,g,e,a,ap,q=base(); q=replace(q,binding='BAD'); self.assertEqual(evaluate(q,p,g,e,a,ap).decision,Decision.HOLD)
    def test_016_request_epoch_hold(self):
        p,g,e,a,ap,q=base(); q=replace(q,state_epoch='BAD'); self.assertEqual(evaluate(q,p,g,e,a,ap).decision,Decision.HOLD)
    def test_017_policy_revoked_hold(self):
        p,g,e,a,ap,q=base(); p=replace(p,revoked=True); self.assertEqual(evaluate(q,p,g,e,a,ap).decision,Decision.HOLD)
    def test_018_duplicate_goal_hold(self):
        p,g,e,a,ap,q=base(); g=g+(g[0],); self.assertEqual(evaluate(q,p,g,e,a,ap).decision,Decision.HOLD)
    def test_019_duplicate_effect_hold(self):
        p,g,e,a,ap,q=base(); e=e+(e[0],); self.assertEqual(evaluate(q,p,g,e,a,ap).decision,Decision.HOLD)
    def test_020_duplicate_action_hold(self):
        p,g,e,a,ap,q=base(); a=a+(a[0],); self.assertEqual(evaluate(q,p,g,e,a,ap).decision,Decision.HOLD)
    def test_021_prepare_valid(self):
        p,g,e,a,ap,q=base(); st=prepare_state(p,g,e,a,ap,binding=p.binding); self.assertTrue(validate_prepared_integrity(st))
    def test_022_prepared_match(self):
        p,g,e,a,ap,q=base(); st=prepare_state(p,g,e,a,ap,binding=p.binding); z1=evaluate(q,p,g,e,a,ap); z2=evaluate_prepared(q,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True); self.assertEqual((z1.decision,z1.reasons,z1.top_goal_id),(z2.decision,z2.reasons,z2.top_goal_id))
    def test_023_prepared_integrity_required(self):
        p,g,e,a,ap,q=base(); st=prepare_state(p,g,e,a,ap,binding=p.binding); self.assertEqual(evaluate_prepared(q,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=False).decision,Decision.HOLD)
    def test_024_policy_fp_mismatch_hold(self):
        p,g,e,a,ap,q=base(); st=prepare_state(p,g,e,a,ap,binding=p.binding); self.assertEqual(evaluate_prepared(q,st,current_policy_fingerprint='x',current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True).decision,Decision.HOLD)
    def test_025_registry_fp_mismatch_hold(self):
        p,g,e,a,ap,q=base(); st=prepare_state(p,g,e,a,ap,binding=p.binding); self.assertEqual(evaluate_prepared(q,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint='x',prepared_integrity_validated=True).decision,Decision.HOLD)
    def test_026_tampered_goal_false(self):
        p,g,e,a,ap,q=base(); st=prepare_state(p,g,e,a,ap,binding=p.binding); bad=replace(st,goals=(replace(st.goals[0],desired_effects=('DELETE',)),)+st.goals[1:]); self.assertFalse(validate_prepared_integrity(bad))
    def test_027_tampered_effect_false(self):
        p,g,e,a,ap,q=base(); st=prepare_state(p,g,e,a,ap,binding=p.binding); bad=replace(st,effects=(replace(st.effects[0],impact=99),)+st.effects[1:]); self.assertFalse(validate_prepared_integrity(bad))
    def test_028_tampered_action_false(self):
        p,g,e,a,ap,q=base(); st=prepare_state(p,g,e,a,ap,binding=p.binding); bad=replace(st,actions=(replace(st.actions[0],effect_ids=('E-DELETE',)),)+st.actions[1:]); self.assertFalse(validate_prepared_integrity(bad))
    def test_029_delta_roundtrip(self):
        p,g,e,a,ap,q=base(); s1=prepare_state(p,g,e,a,ap,binding=p.binding); g2=tuple(replace(x,high_impact=True) if x.goal_id=='G-PRESERVE' else x for x in g); s2=prepare_state(p,g2,e,a,ap,binding=p.binding); d=make_delta(s1,s2); self.assertEqual(apply_delta(s1,d).registry_fingerprint,s2.registry_fingerprint)
    def test_030_missing_sync(self):
        p,g,e,a,ap,q=base(); st=prepare_state(p,g,e,a,ap,binding=p.binding); rg=dict(st.goal_fingerprints); re=dict(st.effect_fingerprints); ra=dict(st.action_fingerprints); rp=dict(st.approval_fingerprints); ra.pop('A-READ'); plan=missing_only_sync_plan(st,rg,re,ra,rp); self.assertIn('A-READ',plan.missing_or_changed_actions); self.assertFalse(plan.full_resend_required)
    def test_031_bad_action_effect_ref_hold(self):
        p,g,e,a,ap,q=base(); a=tuple(replace(x,effect_ids=('MISSING',)) if x.action_id=='A-READ' else x for x in a); self.assertEqual(evaluate(q,p,g,e,a,ap).decision,Decision.HOLD)
    def test_032_registry_binding_hold(self):
        p,g,e,a,ap,q=base(); e=tuple(replace(x,binding='BAD') if x.effect_id=='E-READ' else x for x in e); self.assertEqual(evaluate(q,p,g,e,a,ap).decision,Decision.HOLD)
    def test_033_no_authority_promotion(self):
        p,g,e,a,ap,q=base(); z=evaluate(q,p,g,e,a,ap); self.assertFalse(z.permission_granted); self.assertFalse(z.goal_changed); self.assertFalse(z.human_approval_executed); self.assertFalse(z.tool_executed); self.assertFalse(z.transaction_committed); self.assertFalse(z.external_write_performed); self.assertFalse(z.world_truth_proven); self.assertFalse(z.safety_proven); self.assertFalse(z.action_success)
    def test_034_sequence_limit_hold(self):
        p,g,e,a,ap,q=base(); p=replace(p,max_sequence_length=2); self.assertEqual(evaluate(q,p,g,e,a,ap).decision,Decision.HOLD)
    def test_035_goal_distance_hold(self):
        p,g,e,a,ap,q=base(); q=replace(q,action_sequence=('A-READ',)); self.assertEqual(evaluate(q,p,g,e,a,ap).decision,Decision.HOLD)
    def test_036_preserve_goal_allow(self):
        p,g,e,a,ap,q=base(); q=replace(q,user_goal_id='G-PRESERVE',action_sequence=('A-READ','A-PRESERVE')); self.assertEqual(evaluate(q,p,g,e,a,ap).decision,Decision.ALLOW)
    def test_037_send_goal_allow(self):
        p,g,e,a,ap,q=base(); q=replace(q,user_goal_id='G-EXTERNAL-SHARE',action_sequence=('A-READ','A-ANALYZE','A-SEND')); self.assertEqual(evaluate(q,p,g,e,a,ap).decision,Decision.ALLOW)
    def test_038_delete_goal_allow(self):
        p,g,e,a,ap,q=base(); q=replace(q,user_goal_id='G-DELETE-DATA',action_sequence=('A-DELETE',)); self.assertEqual(evaluate(q,p,g,e,a,ap).decision,Decision.ALLOW)
    def test_039_privilege_goal_allow(self):
        p,g,e,a,ap,q=base(); q=replace(q,user_goal_id='G-PRIVILEGE-EXPANSION',action_sequence=('A-ESCALATE',)); self.assertEqual(evaluate(q,p,g,e,a,ap).decision,Decision.ALLOW)
    def test_040_prepare_rejects_bad_binding(self):
        p,g,e,a,ap,q=base();
        with self.assertRaises(ValueError): prepare_state(p,g,e,a,ap,binding='BAD')

def _gen(i):
    def f(self):
        p,g,e,a,ap,q=base(); m=i%8
        if m==0: want=Decision.ALLOW
        elif m==1: q=replace(q,action_sequence=('A-READ','A-ANALYZE','A-SEND')); want=Decision.DENY
        elif m==2: q=replace(q,action_sequence=('A-READ',)); want=Decision.HOLD
        elif m==3: q=replace(q,user_goal_id='G-PRESERVE',action_sequence=('A-READ','A-PRESERVE')); want=Decision.ALLOW
        elif m==4: a=tuple(replace(x,observed=False) if x.action_id=='A-READ' else x for x in a); want=Decision.HOLD
        elif m==5: q=replace(q,binding=f'BAD{i}'); want=Decision.HOLD
        elif m==6: q=replace(q,user_goal_id='G-EXTERNAL-SHARE',action_sequence=('A-READ','A-ANALYZE','A-SEND')); want=Decision.ALLOW
        else: q=replace(q,action_sequence=('A-READ','A-DELETE')); want=Decision.DENY
        z=evaluate(q,p,g,e,a,ap); self.assertEqual(z.decision,want); self.assertFalse(z.permission_granted); self.assertFalse(z.goal_changed); self.assertFalse(z.human_approval_executed); self.assertFalse(z.tool_executed); self.assertFalse(z.transaction_committed); self.assertFalse(z.external_write_performed); self.assertFalse(z.world_truth_proven); self.assertFalse(z.safety_proven); self.assertFalse(z.action_success)
    return f
for i in range(120): setattr(T,f'test_regression_{i:03d}',_gen(i))
if __name__=='__main__': unittest.main()
