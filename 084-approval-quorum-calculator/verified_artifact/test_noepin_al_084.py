import unittest
from dataclasses import replace
from noepin_al_084_approval_quorum_calculator import *

class T(unittest.TestCase):
    def base(self): return default_proposal(),default_role_matrix(),default_approvals(),default_policy()
    def neg(self,z):
        self.assertFalse(z.permission_granted); self.assertFalse(z.approval_executed); self.assertFalse(z.action_executed); self.assertFalse(z.plan_committed); self.assertFalse(z.external_write_performed); self.assertFalse(z.world_truth_proven); self.assertFalse(z.safety_proven); self.assertFalse(z.action_success); self.assertFalse(z.sender_authority_inherited); self.assertFalse(z.sender_intent_inherited); self.assertFalse(z.consent_inherited)
    def test_001_one_approval_low_local(self):
        q,m,a,p=self.base(); q=replace(q,risk_level=RiskLevel.LOW,blast_radius=BlastRadius.LOCAL); z=evaluate(q,m,(a[0],),p); self.assertEqual(z.decision,Decision.ALLOW); self.assertEqual(z.required_quorum,1); self.neg(z)
    def test_002_two_approval_default(self):
        q,m,a,p=self.base(); z=evaluate(q,m,a,p); self.assertEqual(z.decision,Decision.ALLOW); self.assertEqual(z.required_quorum,2); self.assertEqual(z.approval_state,ApprovalState.SATISFIED); self.neg(z)
    def test_003_role_missing(self):
        q,m,a,p=self.base(); m=tuple(replace(x,roles=('OPERATOR',)) if x.actor_id=='bob' else x for x in m); z=evaluate(q,m,a,p); self.assertEqual(z.decision,Decision.HOLD); self.assertIn('REVIEWER',z.missing_roles)
    def test_004_same_actor_duplicate_does_not_count(self):
        q,m,a,p=self.base(); a=(a[0],replace(a[0],approval_id='AP-A2')); z=evaluate(q,m,a,p); self.assertEqual(z.decision,Decision.HOLD); self.assertEqual(z.effective_approval_count,1)
    def test_005_conflict_excluded(self):
        q,m,a,p=self.base(); a=(a[0],replace(a[1],conflict_of_interest=True)); z=evaluate(q,m,a,p); self.assertEqual(z.decision,Decision.HOLD)
    def test_006_same_authority_group_not_double_count(self):
        q,m,a,p=self.base(); m=tuple(replace(x,authority_group='OPS') if x.actor_id=='bob' else x for x in m); z=evaluate(q,m,a,p); self.assertEqual(z.decision,Decision.HOLD); self.assertEqual(z.effective_approval_count,1)
    def test_007_unsigned_excluded(self):
        q,m,a,p=self.base(); z=evaluate(q,m,(a[0],replace(a[1],signature_verified=False)),p); self.assertEqual(z.decision,Decision.HOLD)
    def test_008_unobserved_excluded(self):
        q,m,a,p=self.base(); z=evaluate(q,m,(a[0],replace(a[1],observed=False)),p); self.assertEqual(z.decision,Decision.HOLD)
    def test_009_wrong_proposal_excluded(self):
        q,m,a,p=self.base(); z=evaluate(q,m,(a[0],replace(a[1],proposal_id='OTHER')),p); self.assertEqual(z.decision,Decision.HOLD)
    def test_010_missing_matrix_actor_excluded(self):
        q,m,a,p=self.base(); m=tuple(x for x in m if x.actor_id!='bob'); z=evaluate(q,m,a,p); self.assertEqual(z.decision,Decision.HOLD)
    def test_011_ineligible_actor_excluded(self):
        q,m,a,p=self.base(); m=tuple(replace(x,eligible=False) if x.actor_id=='bob' else x for x in m); self.assertEqual(evaluate(q,m,a,p).decision,Decision.HOLD)
    def test_012_default_allow_candidate(self):
        q,m,a,p=self.base(); z=evaluate(q,m,a,p); self.assertTrue(z.next_gate_candidate); self.neg(z)
    def test_013_allow_not_permission(self):
        q,m,a,p=self.base(); z=evaluate(q,m,a,p); self.assertFalse(z.permission_granted); self.assertFalse(z.approval_executed)
    def test_014_distinct_role_assignment(self):
        q,m,a,p=self.base(); z=evaluate(q,m,a,p); self.assertEqual(len({x.actor_id for x in z.role_assignments}),2); self.assertEqual(len({x.authority_group for x in z.role_assignments}),2)
    def test_015_high_org_three_roles(self):
        q,m,a,p=self.base(); q=replace(q,risk_level=RiskLevel.HIGH,blast_radius=BlastRadius.ORGANIZATION); a=a+(ApprovalEvidence('AP-C',q.proposal_id,'carol',True,True,False,p.binding,p.state_epoch),ApprovalEvidence('AP-D',q.proposal_id,'dave',True,True,False,p.binding,p.state_epoch)); z=evaluate(q,m,a,p); self.assertEqual(z.decision,Decision.ALLOW); self.assertEqual(z.required_quorum,3)
    def test_016_critical_global_four_roles(self):
        q,m,a,p=self.base(); q=replace(q,risk_level=RiskLevel.CRITICAL,blast_radius=BlastRadius.GLOBAL); extra=(ApprovalEvidence('AP-C',q.proposal_id,'carol',True,True,False,p.binding,p.state_epoch),ApprovalEvidence('AP-D',q.proposal_id,'dave',True,True,False,p.binding,p.state_epoch),ApprovalEvidence('AP-E',q.proposal_id,'erin',True,True,False,p.binding,p.state_epoch)); z=evaluate(q,m,a+extra,p); self.assertEqual(z.decision,Decision.ALLOW); self.assertEqual(z.required_quorum,4)
    def test_017_count_enough_role_missing(self):
        q,m,a,p=self.base(); q=replace(q,risk_level=RiskLevel.HIGH,blast_radius=BlastRadius.ORGANIZATION); extra=(ApprovalEvidence('AP-C',q.proposal_id,'carol',True,True,False,p.binding,p.state_epoch),); m=tuple(replace(x,roles=('REVIEWER',)) if x.actor_id=='dave' else x for x in m); z=evaluate(q,m,a+extra,p); self.assertEqual(z.decision,Decision.HOLD); self.assertIn('OWNER',z.missing_roles)
    def test_018_matrix_binding_mismatch(self):
        q,m,a,p=self.base(); m=(replace(m[0],binding='X'),)+m[1:]; self.assertEqual(evaluate(q,m,a,p).decision,Decision.HOLD)
    def test_019_approval_epoch_mismatch(self):
        q,m,a,p=self.base(); a=(replace(a[0],state_epoch='OLD'),)+a[1:]; self.assertEqual(evaluate(q,m,a,p).decision,Decision.HOLD)
    def test_020_duplicate_matrix_actor(self):
        q,m,a,p=self.base(); self.assertEqual(evaluate(q,m+(m[0],),a,p).decision,Decision.HOLD)
    def test_021_duplicate_approval_id(self):
        q,m,a,p=self.base(); self.assertEqual(evaluate(q,m,a+(a[0],),p).decision,Decision.HOLD)
    def test_022_revoked_policy(self):
        q,m,a,p=self.base(); self.assertEqual(evaluate(q,m,a,replace(p,revoked=True)).decision,Decision.HOLD)
    def test_023_duplicate_rule_level(self):
        q,m,a,p=self.base(); p=replace(p,rules=p.rules+(p.rules[0],)); self.assertEqual(evaluate(q,m,a,p).decision,Decision.HOLD)
    def test_024_invalid_role_set_vs_quorum(self):
        q,m,a,p=self.base(); bad=QuorumRule(1,1,('OPERATOR','REVIEWER')); p=replace(p,rules=(p.rules[0],bad,p.rules[2],p.rules[3])); self.assertEqual(evaluate(q,m,a,p).decision,Decision.HOLD)
    def test_025_missing_rule(self):
        q,m,a,p=self.base(); p=replace(p,rules=tuple(r for r in p.rules if r.level!=1)); self.assertEqual(evaluate(q,m,a,p).decision,Decision.HOLD)
    def test_026_prepared_semantic(self):
        q,m,a,p=self.base(); st=prepare_state(p,q,m,a,binding=p.binding,state_epoch=p.state_epoch); self.assertTrue(validate_prepared_integrity(st)); z=evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True); self.assertEqual(z,evaluate(q,m,a,p))
    def test_027_prepared_stale(self):
        q,m,a,p=self.base(); st=prepare_state(p,q,m,a,binding=p.binding,state_epoch=p.state_epoch); z=evaluate_prepared(st,current_context_fingerprint='bad',current_dependency_fingerprint=st.dependency_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True); self.assertEqual(z.decision,Decision.HOLD)
    def test_028_prepared_integrity_required(self):
        q,m,a,p=self.base(); st=prepare_state(p,q,m,a,binding=p.binding,state_epoch=p.state_epoch); z=evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=False); self.assertEqual(z.decision,Decision.HOLD)
    def test_029_delta_reconstruction(self):
        q,m,a,p=self.base(); s1=prepare_state(p,q,m,a,binding=p.binding,state_epoch=p.state_epoch); m2=tuple(replace(x,roles=x.roles+('AUDITOR',)) if x.actor_id=='alice' else x for x in m); s2=prepare_state(p,q,m2,a,binding=p.binding,state_epoch=p.state_epoch); self.assertEqual(apply_delta(s1,make_delta(s1,s2)),s2)
    def test_030_missing_only(self):
        q,m,a,p=self.base(); many=tuple(RoleMatrixEntry(f'u{i}',('OPERATOR',),f'g{i}',True,p.binding,p.state_epoch) for i in range(20)); aps=tuple(ApprovalEvidence(f'ap{i}',q.proposal_id,f'u{i}',True,True,False,p.binding,p.state_epoch) for i in range(20)); st=prepare_state(p,q,many,aps,binding=p.binding,state_epoch=p.state_epoch); kr=dict(st.role_fingerprints); ka=dict(st.approval_fingerprints); [kr.pop(f'u{i}') for i in range(5)]; [ka.pop(f'ap{i}') for i in range(5)]; plan=missing_only_sync_plan(st,kr,ka); self.assertEqual(len(plan.missing_or_changed_actor_ids),5); self.assertEqual(len(plan.missing_or_changed_approval_ids),5); self.assertFalse(plan.full_resend_required)
    def test_031_delta_smaller_than_full(self):
        q,m,a,p=self.base(); many=tuple(RoleMatrixEntry(f'u{i}',('OPERATOR',),f'g{i}',True,p.binding,p.state_epoch) for i in range(100)); aps=tuple(ApprovalEvidence(f'ap{i}',q.proposal_id,f'u{i}',True,True,False,p.binding,p.state_epoch) for i in range(100)); s1=prepare_state(p,q,many,aps,binding=p.binding,state_epoch=p.state_epoch); aps2=list(aps); aps2[0]=replace(aps2[0],observed=False); s2=prepare_state(p,q,many,tuple(aps2),binding=p.binding,state_epoch=p.state_epoch); self.assertLess(delta_bytes(make_delta(s1,s2)),full_registry_bytes(s2))
    def test_032_authority_flags_false(self):
        q,m,a,p=self.base(); self.neg(evaluate(q,m,a,p))
    def test_033_conflicted_actor_stays_excluded_even_with_clean_duplicate(self):
        q,m,a,p=self.base(); a=a+(replace(a[1],approval_id='AP-B2',conflict_of_interest=True),); z=evaluate(q,m,a,p); self.assertEqual(z.decision,Decision.HOLD); self.assertNotIn('bob',z.effective_actor_ids)
    def test_034_one_authority_group_cannot_cover_two_required_roles(self):
        q,m,a,p=self.base(); m=tuple(replace(x,roles=('OPERATOR','REVIEWER'),authority_group='SAME') if x.actor_id in ('alice','bob') else x for x in m); z=evaluate(q,m,a,p); self.assertEqual(z.decision,Decision.HOLD)
    def test_035_invalid_extra_approval_does_not_block_valid_quorum(self):
        q,m,a,p=self.base(); extra=ApprovalEvidence('BAD',q.proposal_id,'carol',True,False,False,p.binding,p.state_epoch); self.assertEqual(evaluate(q,m,a+(extra,),p).decision,Decision.ALLOW)
    def test_036_required_roles_deterministic(self):
        q,m,a,p=self.base(); self.assertEqual(evaluate(q,m,a,p).required_roles,('OPERATOR','REVIEWER'))
    def test_037_required_quorum_default(self):
        q,m,a,p=self.base(); self.assertEqual(evaluate(q,m,a,p).required_quorum,2)
    def test_038_satisfied_roles_default(self):
        q,m,a,p=self.base(); self.assertEqual(evaluate(q,m,a,p).satisfied_roles,('OPERATOR','REVIEWER'))
    def test_039_approval_state_satisfied(self):
        q,m,a,p=self.base(); self.assertEqual(evaluate(q,m,a,p).approval_state,ApprovalState.SATISFIED)
    def test_040_approval_state_pending(self):
        q,m,a,p=self.base(); self.assertEqual(evaluate(q,m,(a[0],),p).approval_state,ApprovalState.PENDING)

def _gen(k):
    def f(self):
        q,m,a,p=self.base(); mode=k%12
        if mode==0:
            q=replace(q,risk_level=RiskLevel.LOW,blast_radius=BlastRadius.LOCAL); a=(a[0],); want=Decision.ALLOW
        elif mode==1:
            want=Decision.ALLOW
        elif mode==2:
            a=(a[0],); want=Decision.HOLD
        elif mode==3:
            a=(a[0],replace(a[1],signature_verified=False)); want=Decision.HOLD
        elif mode==4:
            a=(a[0],replace(a[1],conflict_of_interest=True)); want=Decision.HOLD
        elif mode==5:
            m=tuple(replace(x,authority_group='OPS') if x.actor_id=='bob' else x for x in m); want=Decision.HOLD
        elif mode==6:
            q=replace(q,risk_level=RiskLevel.HIGH,blast_radius=BlastRadius.ORGANIZATION); a=a+(ApprovalEvidence(f'C{k}',q.proposal_id,'carol',True,True,False,p.binding,p.state_epoch),ApprovalEvidence(f'D{k}',q.proposal_id,'dave',True,True,False,p.binding,p.state_epoch)); want=Decision.ALLOW
        elif mode==7:
            q=replace(q,risk_level=RiskLevel.CRITICAL,blast_radius=BlastRadius.GLOBAL); a=a+(ApprovalEvidence(f'C{k}',q.proposal_id,'carol',True,True,False,p.binding,p.state_epoch),ApprovalEvidence(f'D{k}',q.proposal_id,'dave',True,True,False,p.binding,p.state_epoch),ApprovalEvidence(f'E{k}',q.proposal_id,'erin',True,True,False,p.binding,p.state_epoch)); want=Decision.ALLOW
        elif mode==8:
            m=tuple(replace(x,eligible=False) if x.actor_id=='bob' else x for x in m); want=Decision.HOLD
        elif mode==9:
            a=(a[0],replace(a[1],proposal_id='OTHER')); want=Decision.HOLD
        elif mode==10:
            p=replace(p,revoked=True); want=Decision.HOLD
        else:
            extra=ApprovalEvidence(f'X{k}',q.proposal_id,'carol',True,False,False,p.binding,p.state_epoch); a=a+(extra,); want=Decision.ALLOW
        z=evaluate(q,m,a,p); self.assertEqual(z.decision,want); self.neg(z)
    return f
for k in range(120): setattr(T,f'test_regression_{k:03d}',_gen(k))
if __name__=='__main__': unittest.main(verbosity=2)
