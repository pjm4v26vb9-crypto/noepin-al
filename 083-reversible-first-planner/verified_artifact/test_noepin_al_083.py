import unittest
from dataclasses import replace
from noepin_al_083_reversible_first_planner import *

class T(unittest.TestCase):
    def base(self): return default_goal(),default_actions(),default_approvals(),default_policy()
    def neg(self,z):
        self.assertFalse(z.permission_granted); self.assertFalse(z.approval_executed); self.assertFalse(z.action_executed); self.assertFalse(z.rollback_executed); self.assertFalse(z.plan_committed); self.assertFalse(z.external_write_performed); self.assertFalse(z.world_truth_proven); self.assertFalse(z.safety_proven); self.assertFalse(z.action_success)
    def test_001_delete_vs_quarantine(self):
        g,a,e,p=self.base(); z=evaluate(g,a,e,p); self.assertEqual(z.decision,Decision.ALLOW); self.assertEqual(z.chosen_action_id,'QUARANTINE'); self.neg(z)
    def test_002_send_vs_draft(self):
        g,_,e,p=self.base(); b,ep=p.binding,p.state_epoch; a=(CandidateAction('SEND',g.goal_id,1,0,1,Risk.HIGH,None,True,True,None,b,ep),CandidateAction('DRAFT',g.goal_id,1,.95,1,Risk.LOW,'DELETE_DRAFT',False,True,None,b,ep)); z=evaluate(g,a,e,p); self.assertEqual(z.chosen_action_id,'DRAFT')
    def test_003_equal_reversibility_cost_tie(self):
        g,_,e,p=self.base(); b,ep=p.binding,p.state_epoch; a=(CandidateAction('A',g.goal_id,1,.9,5,Risk.LOW,'RA',False,True,None,b,ep),CandidateAction('B',g.goal_id,1,.9,2,Risk.LOW,'RB',False,True,None,b,ep)); self.assertEqual(evaluate(g,a,e,p).chosen_action_id,'B')
    def test_004_irreversible_only_no_approval(self):
        g,_,e,p=self.base(); b,ep=p.binding,p.state_epoch; a=(CandidateAction('DELETE',g.goal_id,1,0,1,Risk.MEDIUM,None,True,True,None,b,ep),); z=evaluate(g,a,e,p); self.assertEqual(z.decision,Decision.HUMAN_APPROVAL); self.assertTrue(z.human_approval_candidate); self.neg(z)
    def test_005_irreversible_with_bound_approval(self):
        g,_,_,p=self.base(); b,ep=p.binding,p.state_epoch; a=(CandidateAction('DELETE',g.goal_id,1,0,1,Risk.MEDIUM,None,True,True,'AP1',b,ep),); ev=(ApprovalEvidence('AP1','DELETE',True,True,b,ep),); z=evaluate(g,a,ev,p); self.assertEqual(z.decision,Decision.ALLOW); self.assertEqual(z.chosen_action_id,'DELETE'); self.neg(z)
    def test_006_high_risk_no_rollback(self):
        g,_,e,p=self.base(); b,ep=p.binding,p.state_epoch; a=(CandidateAction('RISKY',g.goal_id,1,.9,1,Risk.HIGH,None,False,True,None,b,ep),); z=evaluate(g,a,e,p); self.assertEqual(z.decision,Decision.HOLD); self.neg(z)
    def test_007_high_risk_unknown_reversibility(self):
        g,_,e,p=self.base(); b,ep=p.binding,p.state_epoch; a=(CandidateAction('RISKY',g.goal_id,1,None,1,Risk.HIGH,'RB',False,True,None,b,ep),); self.assertEqual(evaluate(g,a,e,p).decision,Decision.HOLD)
    def test_008_safe_alt_avoids_unknown(self):
        g,_,e,p=self.base(); b,ep=p.binding,p.state_epoch; a=(CandidateAction('UNK',g.goal_id,1,None,1,Risk.HIGH,'RB',False,True,None,b,ep),CandidateAction('SAFE',g.goal_id,.95,.8,2,Risk.LOW,'RS',False,True,None,b,ep)); self.assertEqual(evaluate(g,a,e,p).chosen_action_id,'SAFE')
    def test_009_goal_below_min(self):
        g,_,e,p=self.base(); b,ep=p.binding,p.state_epoch; a=(CandidateAction('A',g.goal_id,.5,.9,1,Risk.LOW,'R',False,True,None,b,ep),); self.assertEqual(evaluate(g,a,e,p).decision,Decision.HOLD)
    def test_010_no_actions(self):
        g,_,e,p=self.base(); self.assertEqual(evaluate(g,(),e,p).decision,Decision.HOLD)
    def test_011_revoked_policy(self):
        g,a,e,p=self.base(); self.assertEqual(evaluate(g,a,e,replace(p,revoked=True)).decision,Decision.HOLD)
    def test_012_binding_mismatch(self):
        g,a,e,p=self.base(); self.assertEqual(evaluate(replace(g,binding='X'),a,e,p).decision,Decision.HOLD)
    def test_013_epoch_mismatch(self):
        g,a,e,p=self.base(); aa=(replace(a[0],state_epoch='OLD'),)+a[1:]; self.assertEqual(evaluate(g,aa,e,p).decision,Decision.HOLD)
    def test_014_duplicate_ids(self):
        g,a,e,p=self.base(); self.assertEqual(evaluate(g,(a[1],a[1]),e,p).decision,Decision.HOLD)
    def test_015_invalid_reversibility(self):
        g,a,e,p=self.base(); aa=(replace(a[1],reversibility_score=1.2),); self.assertEqual(evaluate(g,aa,e,p).decision,Decision.HOLD)
    def test_016_invalid_cost(self):
        g,a,e,p=self.base(); aa=(replace(a[1],cost=-1),); self.assertEqual(evaluate(g,aa,e,p).decision,Decision.HOLD)
    def test_017_wrong_action_approval(self):
        g,_,_,p=self.base(); b,ep=p.binding,p.state_epoch; a=(CandidateAction('DELETE',g.goal_id,1,0,1,Risk.MEDIUM,None,True,True,'AP',b,ep),); ev=(ApprovalEvidence('AP','OTHER',True,True,b,ep),); self.assertEqual(evaluate(g,a,ev,p).decision,Decision.HUMAN_APPROVAL)
    def test_018_unobserved_approval(self):
        g,_,_,p=self.base(); b,ep=p.binding,p.state_epoch; a=(CandidateAction('DELETE',g.goal_id,1,0,1,Risk.MEDIUM,None,True,True,'AP',b,ep),); ev=(ApprovalEvidence('AP','DELETE',False,True,b,ep),); self.assertEqual(evaluate(g,a,ev,p).decision,Decision.HUMAN_APPROVAL)
    def test_019_unauthorized_approval(self):
        g,_,_,p=self.base(); b,ep=p.binding,p.state_epoch; a=(CandidateAction('DELETE',g.goal_id,1,0,1,Risk.MEDIUM,None,True,True,'AP',b,ep),); ev=(ApprovalEvidence('AP','DELETE',True,False,b,ep),); self.assertEqual(evaluate(g,a,ev,p).decision,Decision.HUMAN_APPROVAL)
    def test_020_rollback_option(self):
        g,a,e,p=self.base(); z=evaluate(g,a,e,p); self.assertEqual(z.rollback_option,'RESTORE')
    def test_021_safe_chosen(self):
        g,a,e,p=self.base(); self.assertNotEqual(evaluate(g,a,e,p).chosen_action_id,'DELETE')
    def test_022_ordered_plan_deterministic(self):
        g,a,e,p=self.base(); z=evaluate(g,a,e,p); self.assertEqual(tuple(x.action_id for x in z.ordered_plan),('QUARANTINE','ARCHIVE','DELETE'))
    def test_023_authority_flags_false(self):
        g,a,e,p=self.base(); self.neg(evaluate(g,a,e,p))
    def test_024_prepared_semantic(self):
        g,a,e,p=self.base(); st=prepare_state(p,g,a,e,binding=p.binding,state_epoch=p.state_epoch); self.assertTrue(validate_prepared_integrity(st)); z=evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True); self.assertEqual(z,evaluate(g,a,e,p))
    def test_025_prepared_stale(self):
        g,a,e,p=self.base(); st=prepare_state(p,g,a,e,binding=p.binding,state_epoch=p.state_epoch); z=evaluate_prepared(st,current_context_fingerprint='bad',current_dependency_fingerprint=st.dependency_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True); self.assertEqual(z.decision,Decision.HOLD)
    def test_026_prepared_integrity_required(self):
        g,a,e,p=self.base(); st=prepare_state(p,g,a,e,binding=p.binding,state_epoch=p.state_epoch); z=evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=False); self.assertEqual(z.decision,Decision.HOLD)
    def test_027_delta_reconstruction(self):
        g,a,e,p=self.base(); s1=prepare_state(p,g,a,e,binding=p.binding,state_epoch=p.state_epoch); a2=tuple(replace(x,cost=x.cost+.1) if x.action_id=='ARCHIVE' else x for x in a); s2=prepare_state(p,g,a2,e,binding=p.binding,state_epoch=p.state_epoch); d=make_delta(s1,s2); self.assertEqual(apply_delta(s1,d),s2)
    def test_028_missing_only(self):
        g,a,e,p=self.base(); many=tuple(CandidateAction(f'A{i}',g.goal_id,1,.9,float(i),Risk.LOW,f'R{i}',False,True,None,p.binding,p.state_epoch) for i in range(20)); st=prepare_state(p,g,many,e,binding=p.binding,state_epoch=p.state_epoch); known=dict(st.action_fingerprints); [known.pop(f'A{i}') for i in range(10)]; plan=missing_only_sync_plan(st,known,{}); self.assertEqual(len(plan.missing_or_changed_action_ids),10); self.assertFalse(plan.full_resend_required)
    def test_029_delta_smaller(self):
        g,a,e,p=self.base(); many=tuple(CandidateAction(f'A{i}',g.goal_id,1,.9,float(i),Risk.LOW,f'R{i}',False,True,None,p.binding,p.state_epoch) for i in range(100)); s1=prepare_state(p,g,many,e,binding=p.binding,state_epoch=p.state_epoch); many2=list(many); many2[0]=replace(many2[0],cost=999); s2=prepare_state(p,g,tuple(many2),e,binding=p.binding,state_epoch=p.state_epoch); self.assertLess(delta_bytes(make_delta(s1,s2)),full_registry_bytes(s2))
    def test_030_deterministic(self):
        g,a,e,p=self.base(); self.assertEqual(evaluate(g,a,e,p),evaluate(g,tuple(reversed(a)),e,p))
    def test_031_low_risk_unknown_only_hold(self):
        g,_,e,p=self.base(); b,ep=p.binding,p.state_epoch; a=(CandidateAction('U',g.goal_id,1,None,1,Risk.LOW,'R',False,True,None,b,ep),); self.assertEqual(evaluate(g,a,e,p).decision,Decision.HOLD)
    def test_032_low_reversibility_approval(self):
        g,_,e,p=self.base(); b,ep=p.binding,p.state_epoch; a=(CandidateAction('L',g.goal_id,1,.2,1,Risk.LOW,'R',False,True,None,b,ep),); self.assertEqual(evaluate(g,a,e,p).decision,Decision.HUMAN_APPROVAL)
    def test_033_high_risk_with_rollback(self):
        g,_,e,p=self.base(); b,ep=p.binding,p.state_epoch; a=(CandidateAction('H',g.goal_id,1,.9,1,Risk.HIGH,'R',False,True,None,b,ep),); z=evaluate(g,a,e,p); self.assertEqual(z.decision,Decision.ALLOW); self.neg(z)
    def test_034_critical_only_hold(self):
        g,_,e,p=self.base(); b,ep=p.binding,p.state_epoch; a=(CandidateAction('C',g.goal_id,1,.95,1,Risk.CRITICAL,'R',False,True,None,b,ep),); self.assertEqual(evaluate(g,a,e,p).decision,Decision.HOLD)
    def test_035_approval_not_execution(self):
        g,_,_,p=self.base(); b,ep=p.binding,p.state_epoch; a=(CandidateAction('X',g.goal_id,1,0,1,Risk.LOW,None,True,True,'AP',b,ep),); ev=(ApprovalEvidence('AP','X',True,True,b,ep),); z=evaluate(g,a,ev,p); self.assertFalse(z.approval_executed); self.assertFalse(z.permission_granted)
    def test_036_choice_not_execution(self):
        g,a,e,p=self.base(); z=evaluate(g,a,e,p); self.assertIsNotNone(z.chosen_action_id); self.assertFalse(z.action_executed)
    def test_037_prepare_binding_reject(self):
        g,a,e,p=self.base();
        with self.assertRaises(ValueError): prepare_state(p,g,a,e,binding='X',state_epoch=p.state_epoch)
    def test_038_wrong_delta_base(self):
        g,a,e,p=self.base(); s=prepare_state(p,g,a,e,binding=p.binding,state_epoch=p.state_epoch); d=make_delta(s,s); d=replace(d,base_fingerprint='bad');
        with self.assertRaises(ValueError): apply_delta(s,d)
    def test_039_approval_epoch_mismatch_input_hold(self):
        g,_,_,p=self.base(); b,ep=p.binding,p.state_epoch; a=(CandidateAction('X',g.goal_id,1,0,1,Risk.LOW,None,True,True,'AP',b,ep),); ev=(ApprovalEvidence('AP','X',True,True,b,'OLD'),); self.assertEqual(evaluate(g,a,ev,p).decision,Decision.HOLD)
    def test_040_other_goal_ignored(self):
        g,_,e,p=self.base(); b,ep=p.binding,p.state_epoch; a=(CandidateAction('OTHER','G2',1,.99,0,Risk.LOW,'R',False,True,None,b,ep),); self.assertEqual(evaluate(g,a,e,p).decision,Decision.HOLD)

def _gen(k):
    def f(self):
        g,a,e,p=self.base(); b,ep=p.binding,p.state_epoch; m=k%12
        if m==0: aa=(CandidateAction(f'S{k}',g.goal_id,1,.90,2,Risk.LOW,'R',False,True,None,b,ep),CandidateAction(f'D{k}',g.goal_id,1,0,1,Risk.HIGH,None,True,True,None,b,ep)); want=Decision.ALLOW
        elif m==1: aa=(CandidateAction(f'I{k}',g.goal_id,1,0,1,Risk.MEDIUM,None,True,True,None,b,ep),); want=Decision.HUMAN_APPROVAL
        elif m==2: aa=(CandidateAction(f'H{k}',g.goal_id,1,None,1,Risk.HIGH,'R',False,True,None,b,ep),); want=Decision.HOLD
        elif m==3: aa=(CandidateAction(f'N{k}',g.goal_id,.5,.9,1,Risk.LOW,'R',False,True,None,b,ep),); want=Decision.HOLD
        elif m==4: aa=(CandidateAction(f'R{k}',g.goal_id,1,.95,3,Risk.MEDIUM,'RB',False,True,None,b,ep),); want=Decision.ALLOW
        elif m==5: aa=(CandidateAction(f'C{k}',g.goal_id,1,.95,1,Risk.CRITICAL,'RB',False,True,None,b,ep),); want=Decision.HOLD
        elif m==6: aa=(CandidateAction(f'L{k}',g.goal_id,1,.2,1,Risk.LOW,'RB',False,True,None,b,ep),); want=Decision.HUMAN_APPROVAL
        elif m==7:
            aid=f'A{k}'; aa=(CandidateAction(aid,g.goal_id,1,.2,1,Risk.LOW,'RB',False,True,f'EV{k}',b,ep),); e=(ApprovalEvidence(f'EV{k}',aid,True,True,b,ep),); want=Decision.ALLOW
        elif m==8: aa=(CandidateAction(f'X{k}',g.goal_id,1,.95,1,Risk.HIGH,None,False,True,None,b,ep),); want=Decision.HOLD
        elif m==9: aa=(CandidateAction(f'F{k}',g.goal_id,1,.95,1,Risk.LOW,'RB',False,False,None,b,ep),); want=Decision.HOLD
        elif m==10: aa=(CandidateAction(f'A{k}',g.goal_id,1,.90,2,Risk.MEDIUM,'R',False,True,None,b,ep),CandidateAction(f'B{k}',g.goal_id,1,.95,5,Risk.MEDIUM,'R2',False,True,None,b,ep)); want=Decision.ALLOW
        else: aa=(CandidateAction(f'A{k}',g.goal_id,.9,.9,1,Risk.LOW,'R',False,True,None,b,ep),); want=Decision.ALLOW
        z=evaluate(g,aa,e,p); self.assertEqual(z.decision,want); self.neg(z)
    return f
for k in range(120): setattr(T,f'test_regression_{k:03d}',_gen(k))
if __name__=='__main__': unittest.main(verbosity=2)
