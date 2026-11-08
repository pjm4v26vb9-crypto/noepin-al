import unittest
from dataclasses import replace
from noepin_al_080_adversarial_contrarian_verifier import *
def base(): return default_request(),default_plan(),default_risk_model(),default_constraints(),default_environment()
def neg(t,z):
    for k in ('plan_mutated','permission_granted','counterexample_executed','environment_written','action_executed','plan_committed','world_truth_proven','safety_proven','action_success'): t.assertFalse(getattr(z,k),k)
class T(unittest.TestCase):
    def test_001_no_counterexample_allow(self): q,p,r,c,e=base(); z=evaluate(q,p,r,c,e); self.assertEqual(z.decision,Decision.ALLOW); self.assertEqual(z.coverage,1.0); neg(self,z)
    def test_002_critical_counterexample_deny(self): q,p,r,c,e=base(); a=replace(p.actions[0],effect_tags=('EXTERNAL_WRITE',)); pp=replace(p,actions=(a,p.actions[1]),plan_fingerprint=plan_fingerprint((a,p.actions[1]))); self.assertEqual(evaluate(q,pp,r,c,e).decision,Decision.DENY)
    def test_003_high_counterexample_hold(self): q,p,r,c,e=base(); a=replace(p.actions[0],effect_tags=('EXTERNAL_SEND',)); pp=replace(p,actions=(a,p.actions[1]),plan_fingerprint=plan_fingerprint((a,p.actions[1]))); self.assertEqual(evaluate(q,pp,r,c,e).decision,Decision.HOLD)
    def test_004_minor_counterexample_allow(self): q,p,r,c,e=base(); a=replace(p.actions[0],effect_tags=('UNBOUNDED_SCAN',)); pp=replace(p,actions=(a,p.actions[1]),plan_fingerprint=plan_fingerprint((a,p.actions[1]))); z=evaluate(q,pp,r,c,e); self.assertEqual(z.decision,Decision.ALLOW); self.assertGreater(z.risk_addition,0)
    def test_005_coverage_hold(self): q,p,r,c,e=base(); c=(replace(c[0],observed=False),c[1],c[2]); self.assertEqual(evaluate(q,p,r,c,e).decision,Decision.HOLD)
    def test_006_env_unobserved_hold(self): q,p,r,c,e=base(); e=(replace(e[0],observed=False),e[1]); self.assertEqual(evaluate(q,p,r,c,e).decision,Decision.HOLD)
    def test_007_false_counterexample_env_mismatch_no_deny(self): q,p,r,c,e=base(); a=replace(p.actions[0],effect_tags=('EXTERNAL_WRITE',),assumptions=(('network','ON'),)); a2=replace(p.actions[1],assumptions=(('network','ON'),)); pp=replace(p,actions=(a,a2),plan_fingerprint=plan_fingerprint((a,a2))); e=(replace(e[0],value='ON'),e[1]); self.assertNotEqual(evaluate(q,pp,r,c,e).decision,Decision.DENY)
    def test_008_assumption_contradiction(self): q,p,r,c,e=base(); a=replace(p.actions[0],assumptions=(('network','ON'),)); pp=replace(p,actions=(a,p.actions[1]),plan_fingerprint=plan_fingerprint((a,p.actions[1]))); self.assertEqual(evaluate(q,pp,r,c,e).decision,Decision.DENY)
    def test_009_plan_fingerprint_hold(self): q,p,r,c,e=base(); self.assertEqual(evaluate(q,replace(p,plan_fingerprint='BAD'),r,c,e).decision,Decision.HOLD)
    def test_010_plan_id_hold(self): q,p,r,c,e=base(); self.assertEqual(evaluate(replace(q,plan_id='BAD'),p,r,c,e).decision,Decision.HOLD)
    def test_011_constraint_unknown_hold(self): q,p,r,c,e=base(); self.assertEqual(evaluate(replace(q,constraint_ids=('NOPE',)),p,r,c,e).decision,Decision.HOLD)
    def test_012_no_constraints_hold(self): q,p,r,c,e=base(); self.assertEqual(evaluate(replace(q,constraint_ids=()),p,r,c,e).decision,Decision.HOLD)
    def test_013_duplicate_request_constraint_hold(self): q,p,r,c,e=base(); self.assertEqual(evaluate(replace(q,constraint_ids=('C-LOCAL','C-LOCAL')),p,r,c,e).decision,Decision.HOLD)
    def test_014_duplicate_constraint_hold(self): q,p,r,c,e=base(); cc=(c[0],c[0],c[2]); self.assertEqual(evaluate(q,p,r,cc,e).decision,Decision.HOLD)
    def test_015_duplicate_env_hold(self): q,p,r,c,e=base(); ee=(e[0],e[0]); self.assertEqual(evaluate(q,p,r,c,ee).decision,Decision.HOLD)
    def test_016_binding_hold(self): q,p,r,c,e=base(); self.assertEqual(evaluate(replace(q,binding='BAD'),p,r,c,e).decision,Decision.HOLD)
    def test_017_plan_binding_hold(self): q,p,r,c,e=base(); self.assertEqual(evaluate(q,replace(p,binding='BAD'),r,c,e).decision,Decision.HOLD)
    def test_018_constraint_binding_hold(self): q,p,r,c,e=base(); cc=(replace(c[0],binding='BAD'),c[1],c[2]); self.assertEqual(evaluate(q,p,r,cc,e).decision,Decision.HOLD)
    def test_019_env_binding_hold(self): q,p,r,c,e=base(); ee=(replace(e[0],binding='BAD'),e[1]); self.assertEqual(evaluate(q,p,r,c,ee).decision,Decision.HOLD)
    def test_020_revoked_hold(self): q,p,r,c,e=base(); self.assertEqual(evaluate(q,p,replace(r,revoked=True),c,e).decision,Decision.HOLD)
    def test_021_invalid_risk_hold(self): q,p,r,c,e=base(); self.assertEqual(evaluate(q,p,replace(r,min_coverage=1.5),c,e).decision,Decision.HOLD)
    def test_022_prepared_same(self): q,p,r,c,e=base(); st=prepare_state(r,c,e,binding=r.binding); v=validate_prepared_integrity(st); self.assertTrue(v); self.assertEqual(evaluate(q,p,r,c,e),evaluate_prepared(q,p,st,current_risk_fingerprint=st.risk_model_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=v))
    def test_023_prepared_unvalidated_hold(self): q,p,r,c,e=base(); st=prepare_state(r,c,e,binding=r.binding); self.assertEqual(evaluate_prepared(q,p,st,current_risk_fingerprint=st.risk_model_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=False).decision,Decision.HOLD)
    def test_024_prepared_risk_mismatch(self): q,p,r,c,e=base(); st=prepare_state(r,c,e,binding=r.binding); self.assertEqual(evaluate_prepared(q,p,st,current_risk_fingerprint='BAD',current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True).decision,Decision.HOLD)
    def test_025_prepared_registry_mismatch(self): q,p,r,c,e=base(); st=prepare_state(r,c,e,binding=r.binding); self.assertEqual(evaluate_prepared(q,p,st,current_risk_fingerprint=st.risk_model_fingerprint,current_registry_fingerprint='BAD',prepared_integrity_validated=True).decision,Decision.HOLD)
    def test_026_tamper_invalid(self): q,p,r,c,e=base(); st=prepare_state(r,c,e,binding=r.binding); self.assertFalse(validate_prepared_integrity(replace(st,registry_fingerprint='BAD')))
    def test_027_delta_roundtrip(self): q,p,r,c,e=base(); a=prepare_state(r,c,e,binding=r.binding); b=prepare_state(r,(replace(c[0],observed=False),c[1],c[2]),e,binding=r.binding); self.assertEqual(apply_delta(a,make_delta(a,b)).registry_fingerprint,b.registry_fingerprint)
    def test_028_delta_base_mismatch(self): q,p,r,c,e=base(); a=prepare_state(r,c,e,binding=r.binding); b=prepare_state(r,(replace(c[0],observed=False),c[1],c[2]),e,binding=r.binding); d=replace(make_delta(a,b),base_fingerprint='BAD'); self.assertRaises(ValueError,apply_delta,a,d)
    def test_029_missing_sync(self): q,p,r,c,e=base(); st=prepare_state(r,c,e,binding=r.binding); kc=dict(st.constraint_fingerprints); ke=dict(st.environment_fingerprints); kc.pop('C-LOCAL'); plan=missing_only_sync_plan(st,kc,ke); self.assertIn('C-LOCAL',plan.missing_or_changed_constraints); self.assertFalse(plan.full_resend_required)
    def test_030_invalid_typed_hold(self): q,p,r,c,e=base(); self.assertEqual(evaluate({},p,r,c,e).decision,Decision.HOLD)
    def test_031_plan_immutable(self): q,p,r,c,e=base(); z=evaluate(q,p,r,c,e); self.assertFalse(z.plan_mutated)
    def test_032_no_safety_proof(self): q,p,r,c,e=base(); neg(self,evaluate(q,p,r,c,e))
    def test_033_coverage_subset(self): q,p,r,c,e=base(); qq=replace(q,constraint_ids=('C-BOUNDARY',)); self.assertEqual(evaluate(qq,p,r,c,e).coverage,1.0)
    def test_034_env_mismatch_failure_condition(self): q,p,r,c,e=base(); ee=(replace(e[0],value='ON'),e[1]); z=evaluate(q,p,r,c,ee); self.assertTrue(any('ENV_MISMATCH' in x for x in z.failure_conditions))
    def test_035_critical_counterexample_recorded(self): q,p,r,c,e=base(); a=replace(p.actions[0],effect_tags=('DELETE',)); pp=replace(p,actions=(a,p.actions[1]),plan_fingerprint=plan_fingerprint((a,p.actions[1]))); z=evaluate(q,pp,r,c,e); self.assertTrue(any(x.severity==Severity.CRITICAL for x in z.counterexamples))
    def test_036_medium_risk_addition(self): q,p,r,c,e=base(); a=replace(p.actions[0],effect_tags=('UNBOUNDED_SCAN',)); pp=replace(p,actions=(a,p.actions[1]),plan_fingerprint=plan_fingerprint((a,p.actions[1]))); self.assertGreater(evaluate(q,pp,r,c,e).risk_addition,0)
    def test_037_counterexample_not_executed(self): q,p,r,c,e=base(); a=replace(p.actions[0],effect_tags=('DELETE',)); pp=replace(p,actions=(a,p.actions[1]),plan_fingerprint=plan_fingerprint((a,p.actions[1]))); neg(self,evaluate(q,pp,r,c,e))
    def test_038_empty_plan_allowed_if_valid(self): q,p,r,c,e=base(); pp=replace(p,actions=(),plan_fingerprint=plan_fingerprint(())); self.assertEqual(evaluate(q,pp,r,c,e).decision,Decision.ALLOW)
    def test_039_risk_no_critical_deny_high_hold(self): q,p,r,c,e=base(); rr=replace(r,critical_denies=False); a=replace(p.actions[0],effect_tags=('EXTERNAL_WRITE',)); pp=replace(p,actions=(a,p.actions[1]),plan_fingerprint=plan_fingerprint((a,p.actions[1]))); self.assertIn(evaluate(q,pp,rr,c,e).decision,(Decision.ALLOW,Decision.HOLD))
    def test_040_authority_negatives(self): q,p,r,c,e=base(); neg(self,evaluate(q,p,r,c,e))
def _gen(i):
    def f(self):
        q,p,r,c,e=base(); m=i%12
        if m==0: want=Decision.ALLOW
        elif m==1:
            a=replace(p.actions[0],effect_tags=('EXTERNAL_WRITE',)); p=replace(p,actions=(a,p.actions[1]),plan_fingerprint=plan_fingerprint((a,p.actions[1]))); want=Decision.DENY
        elif m==2:
            a=replace(p.actions[0],effect_tags=('EXTERNAL_SEND',)); p=replace(p,actions=(a,p.actions[1]),plan_fingerprint=plan_fingerprint((a,p.actions[1]))); want=Decision.HOLD
        elif m==3: c=(replace(c[0],observed=False),c[1],c[2]); want=Decision.HOLD
        elif m==4: q=replace(q,binding=f'BAD-{i}'); want=Decision.HOLD
        elif m==5: p=replace(p,plan_fingerprint='BAD'); want=Decision.HOLD
        elif m==6: q=replace(q,constraint_ids=('NOPE',)); want=Decision.HOLD
        elif m==7: e=(replace(e[0],observed=False),e[1]); want=Decision.HOLD
        elif m==8:
            a=replace(p.actions[0],effect_tags=('UNBOUNDED_SCAN',)); p=replace(p,actions=(a,p.actions[1]),plan_fingerprint=plan_fingerprint((a,p.actions[1]))); want=Decision.ALLOW
        elif m==9: r=replace(r,revoked=True); want=Decision.HOLD
        elif m==10: q=replace(q,constraint_ids=()); want=Decision.HOLD
        else: want=Decision.ALLOW
        z=evaluate(q,p,r,c,e); self.assertEqual(z.decision,want); neg(self,z)
    return f
for i in range(120): setattr(T,f'test_regression_{i:03d}',_gen(i))
if __name__=='__main__': unittest.main(verbosity=2)
