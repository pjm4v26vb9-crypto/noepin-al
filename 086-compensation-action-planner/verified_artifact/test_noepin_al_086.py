import unittest
from dataclasses import replace
from noepin_al_086_compensation_action_planner import *

class T(unittest.TestCase):
    def base(self):
        return (default_request(),default_intent(),default_permit(),default_actions(),default_effects(),default_compensations(),default_policy())
    def neg(self,z):
        self.assertFalse(z.request_promoted_to_success); self.assertFalse(z.intent_promoted_to_action); self.assertFalse(z.permission_granted)
        self.assertFalse(z.forward_action_executed); self.assertFalse(z.compensation_executed); self.assertFalse(z.plan_committed)
        self.assertFalse(z.atomic_publish_executed); self.assertFalse(z.external_write_performed); self.assertFalse(z.receipt_promoted_to_truth)
        self.assertFalse(z.world_truth_proven); self.assertFalse(z.safety_proven); self.assertFalse(z.action_success)
    def test_001_default_allow(self):
        z=default_evaluation(); self.assertEqual(z.decision,Decision.ALLOW); self.assertTrue(z.next_gate_candidate); self.neg(z)
    def test_002_reverse_order(self):
        z=default_evaluation(); self.assertEqual(tuple(x.action_id for x in z.compensation_plan),('A2','A1'))
    def test_003_full_coverage(self): self.assertEqual(default_evaluation().coverage,1.0)
    def test_004_partial_coverage_acceptable(self):
        r,i,p,a,e,c,pol=self.base(); c=(c[0],replace(c[1],coverage=.8)); z=evaluate(r,i,p,a,e,c,pol); self.assertEqual(z.decision,Decision.ALLOW); self.assertTrue(z.residual_risk>0)
    def test_005_partial_coverage_insufficient(self):
        r,i,p,a,e,c,pol=self.base(); c=(c[0],replace(c[1],coverage=.2)); self.assertEqual(evaluate(r,i,p,a,e,c,pol).decision,Decision.HOLD)
    def test_006_critical_uncompensable_human(self):
        r,i,p,a,e,c,pol=self.base(); e=(e[0],replace(e[1],severity=Risk.CRITICAL)); c=(c[0],replace(c[1],status=CompensationStatus.FAILED)); z=evaluate(r,i,p,a,e,c,pol); self.assertEqual(z.decision,Decision.HUMAN_APPROVAL); self.assertEqual(z.approval_state,ApprovalState.REQUIRED); self.neg(z)
    def test_007_high_risk_compensation_hold(self):
        r,i,p,a,e,c,pol=self.base(); c=(c[0],replace(c[1],risk=Risk.HIGH)); self.assertEqual(evaluate(r,i,p,a,e,c,pol).decision,Decision.HOLD)
    def test_008_compensation_failed(self):
        r,i,p,a,e,c,pol=self.base(); c=(c[0],replace(c[1],status=CompensationStatus.FAILED)); self.assertEqual(evaluate(r,i,p,a,e,c,pol).decision,Decision.HOLD)
    def test_009_compensation_unobserved(self):
        r,i,p,a,e,c,pol=self.base(); c=(c[0],replace(c[1],observed=False)); self.assertEqual(evaluate(r,i,p,a,e,c,pol).decision,Decision.HOLD)
    def test_010_request_unobserved(self):
        r,i,p,a,e,c,pol=self.base(); self.assertEqual(evaluate(replace(r,observed=False),i,p,a,e,c,pol).decision,Decision.HOLD)
    def test_011_intent_unobserved(self):
        r,i,p,a,e,c,pol=self.base(); self.assertEqual(evaluate(r,replace(i,observed=False),p,a,e,c,pol).decision,Decision.HOLD)
    def test_012_permit_unobserved(self):
        r,i,p,a,e,c,pol=self.base(); self.assertEqual(evaluate(r,i,replace(p,observed=False),a,e,c,pol).decision,Decision.HOLD)
    def test_013_permit_not_allowed(self):
        r,i,p,a,e,c,pol=self.base(); self.assertEqual(evaluate(r,i,replace(p,allow_candidate=False),a,e,c,pol).decision,Decision.HOLD)
    def test_014_empty_actions(self):
        r,i,p,a,e,c,pol=self.base(); self.assertEqual(evaluate(r,i,p,(),e,c,pol).decision,Decision.HOLD)
    def test_015_empty_effects(self):
        r,i,p,a,e,c,pol=self.base(); self.assertEqual(evaluate(r,i,p,a,(),(),pol).decision,Decision.HOLD)
    def test_016_action_unobserved(self):
        r,i,p,a,e,c,pol=self.base(); a=(replace(a[0],observed=False),a[1]); self.assertEqual(evaluate(r,i,p,a,e,c,pol).decision,Decision.HOLD)
    def test_017_effect_unobserved(self):
        r,i,p,a,e,c,pol=self.base(); e=(replace(e[0],observed=False),e[1]); self.assertEqual(evaluate(r,i,p,a,e,c,pol).decision,Decision.HOLD)
    def test_018_action_risk_unknown(self):
        r,i,p,a,e,c,pol=self.base(); a=(replace(a[0],risk=Risk.UNKNOWN),a[1]); self.assertEqual(evaluate(r,i,p,a,e,c,pol).decision,Decision.HOLD)
    def test_019_effect_severity_unknown(self):
        r,i,p,a,e,c,pol=self.base(); e=(replace(e[0],severity=Risk.UNKNOWN),e[1]); self.assertEqual(evaluate(r,i,p,a,e,c,pol).decision,Decision.HOLD)
    def test_020_policy_revoked(self):
        r,i,p,a,e,c,pol=self.base(); self.assertEqual(evaluate(r,i,p,a,e,c,replace(pol,revoked=True)).decision,Decision.HOLD)
    def test_021_binding_mismatch(self):
        r,i,p,a,e,c,pol=self.base(); self.assertEqual(evaluate(replace(r,binding='X'),i,p,a,e,c,pol).decision,Decision.HOLD)
    def test_022_epoch_mismatch(self):
        r,i,p,a,e,c,pol=self.base(); self.assertEqual(evaluate(r,replace(i,state_epoch='OLD'),p,a,e,c,pol).decision,Decision.HOLD)
    def test_023_plan_id_mismatch(self):
        r,i,p,a,e,c,pol=self.base(); self.assertEqual(evaluate(r,i,replace(p,plan_id='X'),a,e,c,pol).decision,Decision.HOLD)
    def test_024_duplicate_action_id(self):
        r,i,p,a,e,c,pol=self.base(); a=(a[0],replace(a[1],action_id=a[0].action_id)); self.assertEqual(evaluate(r,i,p,a,e,c,pol).decision,Decision.HOLD)
    def test_025_duplicate_action_order(self):
        r,i,p,a,e,c,pol=self.base(); a=(a[0],replace(a[1],order=0)); self.assertEqual(evaluate(r,i,p,a,e,c,pol).decision,Decision.HOLD)
    def test_026_noncontiguous_order(self):
        r,i,p,a,e,c,pol=self.base(); a=(a[0],replace(a[1],order=2)); self.assertEqual(evaluate(r,i,p,a,e,c,pol).decision,Decision.HOLD)
    def test_027_duplicate_effect_id(self):
        r,i,p,a,e,c,pol=self.base(); e=(e[0],replace(e[1],effect_id=e[0].effect_id)); self.assertEqual(evaluate(r,i,p,a,e,c,pol).decision,Decision.HOLD)
    def test_028_duplicate_compensation_id(self):
        r,i,p,a,e,c,pol=self.base(); c=(c[0],replace(c[1],compensation_id=c[0].compensation_id)); self.assertEqual(evaluate(r,i,p,a,e,c,pol).decision,Decision.HOLD)
    def test_029_unknown_effect_action(self):
        r,i,p,a,e,c,pol=self.base(); e=(replace(e[0],action_id='NOPE'),e[1]); self.assertEqual(evaluate(r,i,p,a,e,c,pol).decision,Decision.HOLD)
    def test_030_unknown_comp_effect(self):
        r,i,p,a,e,c,pol=self.base(); c=(replace(c[0],effect_id='NOPE'),c[1]); self.assertEqual(evaluate(r,i,p,a,e,c,pol).decision,Decision.HOLD)
    def test_031_invalid_coverage(self):
        r,i,p,a,e,c,pol=self.base(); c=(replace(c[0],coverage=1.1),c[1]); self.assertEqual(evaluate(r,i,p,a,e,c,pol).decision,Decision.HOLD)
    def test_032_invalid_effect_weight(self):
        r,i,p,a,e,c,pol=self.base(); e=(replace(e[0],weight=0),e[1]); self.assertEqual(evaluate(r,i,p,a,e,c,pol).decision,Decision.HOLD)
    def test_033_prepared_semantic(self):
        x=self.base(); st=prepare_state(*x,binding=x[-1].binding,state_epoch=x[-1].state_epoch); self.assertTrue(validate_prepared_integrity(st)); z=evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True); self.assertEqual(z,evaluate(*x))
    def test_034_prepared_stale(self):
        x=self.base(); st=prepare_state(*x,binding=x[-1].binding,state_epoch=x[-1].state_epoch); self.assertEqual(evaluate_prepared(st,current_context_fingerprint='X',current_dependency_fingerprint=st.dependency_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True).decision,Decision.HOLD)
    def test_035_prepared_integrity_required(self):
        x=self.base(); st=prepare_state(*x,binding=x[-1].binding,state_epoch=x[-1].state_epoch); self.assertEqual(evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=False).decision,Decision.HOLD)
    def test_036_delta_reconstruction(self):
        x=self.base(); s1=prepare_state(*x,binding=x[-1].binding,state_epoch=x[-1].state_epoch); c=list(x[5]); c[0]=replace(c[0],coverage=.9); x2=x[:5]+(tuple(c),)+x[6:]; s2=prepare_state(*x2,binding=x2[-1].binding,state_epoch=x2[-1].state_epoch); self.assertEqual(apply_delta(s1,make_delta(s1,s2)),s2)
    def test_037_missing_only(self):
        x=self.base(); N=20; a=tuple(ForwardAction(f'A{n}',n,Risk.MEDIUM,True,'COMP-BIND','STATE-EPOCH-1') for n in range(N)); e=tuple(EffectRecord(f'E{n}',f'A{n}',Risk.MEDIUM,1,True,'COMP-BIND','STATE-EPOCH-1') for n in range(N)); c=tuple(CompensationCandidate(f'C{n}',f'E{n}',1,Risk.LOW,CompensationStatus.READY,True,'COMP-BIND','STATE-EPOCH-1') for n in range(N)); xx=x[:3]+(a,e,c)+x[6:]; st=prepare_state(*xx,binding=xx[-1].binding,state_epoch=xx[-1].state_epoch); ka=dict(st.action_fingerprints); ke=dict(st.effect_fingerprints); kc=dict(st.compensation_fingerprints); [ke.pop(f'E{n}') for n in range(5)]; plan=missing_only_sync_plan(st,ka,ke,kc); self.assertEqual(len(plan.missing_or_changed_effect_ids),5); self.assertFalse(plan.full_resend_required)
    def test_038_delta_smaller(self):
        x=self.base(); N=100; a=tuple(ForwardAction(f'A{n}',n,Risk.MEDIUM,True,'COMP-BIND','STATE-EPOCH-1') for n in range(N)); e=tuple(EffectRecord(f'E{n}',f'A{n}',Risk.MEDIUM,1,True,'COMP-BIND','STATE-EPOCH-1') for n in range(N)); c=tuple(CompensationCandidate(f'C{n}',f'E{n}',1,Risk.LOW,CompensationStatus.READY,True,'COMP-BIND','STATE-EPOCH-1') for n in range(N)); xx=x[:3]+(a,e,c)+x[6:]; s1=prepare_state(*xx,binding=xx[-1].binding,state_epoch=xx[-1].state_epoch); cc=list(c); cc[0]=replace(cc[0],coverage=.9); xx2=x[:3]+(a,e,tuple(cc))+x[6:]; s2=prepare_state(*xx2,binding=xx2[-1].binding,state_epoch=xx2[-1].state_epoch); self.assertLess(delta_bytes(make_delta(s1,s2)),full_registry_bytes(s2))
    def test_039_authority_flags_false(self): self.neg(default_evaluation())
    def test_040_plan_not_execution(self):
        z=default_evaluation(); self.assertTrue(z.plan_attached_candidate); self.assertFalse(z.forward_action_executed); self.assertFalse(z.compensation_executed); self.assertFalse(z.plan_committed)

def _gen(k):
    def f(self):
        r,i,p,a,e,c,pol=self.base(); mode=k%12
        if mode==0: want=Decision.ALLOW
        elif mode==1: p=replace(p,allow_candidate=False); want=Decision.HOLD
        elif mode==2: e=(e[0],replace(e[1],observed=False)); want=Decision.HOLD
        elif mode==3: c=(c[0],replace(c[1],status=CompensationStatus.FAILED)); want=Decision.HOLD
        elif mode==4: c=(c[0],replace(c[1],risk=Risk.HIGH)); want=Decision.HOLD
        elif mode==5: c=(c[0],replace(c[1],coverage=.8)); want=Decision.ALLOW
        elif mode==6: c=(c[0],replace(c[1],coverage=.2)); want=Decision.HOLD
        elif mode==7: a=(replace(a[0],risk=Risk.UNKNOWN),a[1]); want=Decision.HOLD
        elif mode==8: e=(e[0],replace(e[1],severity=Risk.CRITICAL)); c=(c[0],replace(c[1],status=CompensationStatus.FAILED)); want=Decision.HUMAN_APPROVAL
        elif mode==9: pol=replace(pol,revoked=True); want=Decision.HOLD
        elif mode==10: r=replace(r,observed=False); want=Decision.HOLD
        else: i=replace(i,observed=False); want=Decision.HOLD
        z=evaluate(r,i,p,a,e,c,pol); self.assertEqual(z.decision,want); self.neg(z)
    return f
for k in range(120): setattr(T,f'test_regression_{k:03d}',_gen(k))

if __name__=='__main__': unittest.main(verbosity=2)
