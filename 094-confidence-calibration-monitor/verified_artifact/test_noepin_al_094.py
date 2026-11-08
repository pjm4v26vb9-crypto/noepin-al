import unittest
from dataclasses import replace
from noepin_al_094_confidence_calibration_monitor import *
class T(unittest.TestCase):
    def base(self): return default_request(),default_observations(),default_policy()
    def neg(self,z):
        self.assertFalse(z.permission_granted); self.assertFalse(z.action_executed); self.assertFalse(z.plan_committed); self.assertFalse(z.atomic_publish_executed); self.assertFalse(z.external_write_performed); self.assertFalse(z.world_truth_proven); self.assertFalse(z.authority_promoted); self.assertFalse(z.safety_proven); self.assertFalse(z.action_success)
    def over(self):
        r,o,p=self.base(); r=replace(r,risk=RiskLevel.HIGH,predicted_confidence=.95); o=tuple(replace(x,predicted_confidence=.95,observed_outcome=(i%2==0)) for i,x in enumerate(o)); return r,o,p
    def drift(self):
        r,o,p=self.base(); rows=[]
        for i,x in enumerate(o):
            if i<20: y=True
            elif i<30: y=True
            else: y=(i%4==0)
            rows.append(replace(x,predicted_confidence=.8,observed_outcome=y))
        return r,tuple(rows),p
    def test_001_default_allow(self): self.assertEqual(default_evaluation().decision,Decision.ALLOW)
    def test_002_default_count(self): self.assertEqual(default_evaluation().sample_count,40)
    def test_003_default_ece_zero(self): self.assertAlmostEqual(default_evaluation().calibration_error_ece,0.0,places=12)
    def test_004_default_empirical(self): self.assertAlmostEqual(default_evaluation().empirical_accuracy,.8,places=12)
    def test_005_default_adjusted(self): self.assertAlmostEqual(default_evaluation().adjusted_confidence,.8,places=12)
    def test_006_authority_negative(self): self.neg(default_evaluation())
    def test_007_overconfidence_high_hold(self): r,o,p=self.over(); z=evaluate(r,o,p); self.assertEqual(z.decision,Decision.HOLD); self.assertTrue(z.authority_shrink_candidate)
    def test_008_overconfidence_gap(self): r,o,p=self.over(); self.assertGreater(evaluate(r,o,p).overconfidence_gap,.4)
    def test_009_underconfidence_detected(self): r,o,p=self.base(); o=tuple(replace(x,predicted_confidence=.3,observed_outcome=(i%5!=4)) for i,x in enumerate(o)); z=evaluate(replace(r,predicted_confidence=.3),o,p); self.assertGreater(z.underconfidence_gap,.4)
    def test_010_sparse_high_hold(self): r,o,p=self.base(); z=evaluate(replace(r,risk=RiskLevel.HIGH),o[:5],p); self.assertEqual(z.decision,Decision.HOLD); self.assertTrue(z.sparse_history)
    def test_011_sparse_prior_shrink(self): r,o,p=self.base(); z=evaluate(r,o[:2],p); self.assertLess(abs(z.adjusted_confidence-p.prior_accuracy),abs(r.predicted_confidence-p.prior_accuracy))
    def test_012_no_task_history(self): r,o,p=self.base(); z=evaluate(replace(r,task_class='OTHER'),o,p); self.assertEqual(z.decision,Decision.HOLD); self.assertEqual(z.sample_count,0)
    def test_013_task_filter(self): r,o,p=self.base(); extra=tuple(replace(x,observation_id='X'+x.observation_id,task_class='OTHER') for x in o); self.assertEqual(evaluate(r,o+extra,p).sample_count,40)
    def test_014_drift_hold(self): r,o,p=self.drift(); z=evaluate(r,o,p); self.assertTrue(z.drift_detected); self.assertEqual(z.decision,Decision.HOLD)
    def test_015_drift_warning(self): r,o,p=self.drift(); self.assertTrue(evaluate(r,o,p).warning_candidate)
    def test_016_policy_revoked(self): r,o,p=self.base(); self.assertEqual(evaluate(r,o,replace(p,revoked=True)).decision,Decision.HOLD)
    def test_017_request_unobserved(self): r,o,p=self.base(); self.assertEqual(evaluate(replace(r,observed=False),o,p).decision,Decision.HOLD)
    def test_018_binding_mismatch(self): r,o,p=self.base(); self.assertEqual(evaluate(replace(r,binding='BAD'),o,p).decision,Decision.HOLD)
    def test_019_request_confidence_invalid(self): r,o,p=self.base(); self.assertEqual(evaluate(replace(r,predicted_confidence=1.1),o,p).decision,Decision.HOLD)
    def test_020_duplicate_observation(self): r,o,p=self.base(); self.assertEqual(evaluate(r,o+(o[0],),p).decision,Decision.HOLD)
    def test_021_observation_unobserved(self): r,o,p=self.base(); o=(replace(o[0],observed=False),)+o[1:]; self.assertEqual(evaluate(r,o,p).decision,Decision.HOLD)
    def test_022_observation_scope_mismatch(self): r,o,p=self.base(); o=(replace(o[0],binding='BAD'),)+o[1:]; self.assertEqual(evaluate(r,o,p).decision,Decision.HOLD)
    def test_023_observation_future(self): r,o,p=self.base(); o=(replace(o[0],observed_at=r.now+1),)+o[1:]; self.assertEqual(evaluate(r,o,p).decision,Decision.HOLD)
    def test_024_identity_invalid(self): r,o,p=self.base(); o=(replace(o[0],evidence_fingerprint=''),)+o[1:]; self.assertEqual(evaluate(r,o,p).decision,Decision.HOLD)
    def test_025_curve_nonempty(self): self.assertGreater(len(default_evaluation().calibration_curve),0)
    def test_026_brier_bounds(self): z=default_evaluation(); self.assertTrue(0<=z.brier_score<=1)
    def test_027_interval_bounds(self): z=default_evaluation(); self.assertTrue(0<=z.credible_interval[0]<=z.credible_interval[1]<=1)
    def test_028_deterministic_order(self): r,o,p=self.base(); self.assertEqual(evaluate(r,o,p),evaluate(r,tuple(reversed(o)),p))
    def test_029_prepared_valid(self): r,o,p=self.base(); st=prepare_state(r,o,p,binding=p.binding,state_epoch=p.state_epoch); self.assertTrue(validate_prepared_integrity(st)); self.assertEqual(evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_calibration_fingerprint=st.calibration_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True),default_evaluation())
    def test_030_prepared_unvalidated(self): r,o,p=self.base(); st=prepare_state(r,o,p,binding=p.binding,state_epoch=p.state_epoch); self.assertEqual(evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_calibration_fingerprint=st.calibration_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=False).decision,Decision.HOLD)
    def test_031_prepared_context_change(self): r,o,p=self.base(); st=prepare_state(r,o,p,binding=p.binding,state_epoch=p.state_epoch); self.assertEqual(evaluate_prepared(st,current_context_fingerprint='BAD',current_dependency_fingerprint=st.dependency_fingerprint,current_calibration_fingerprint=st.calibration_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True).decision,Decision.HOLD)
    def test_032_delta_roundtrip(self): r,o,p=self.base(); a=prepare_state(r,o,p,binding=p.binding,state_epoch=p.state_epoch); o2=(replace(o[0],source_version='V2'),)+o[1:]; b=prepare_state(r,o2,p,binding=p.binding,state_epoch=p.state_epoch); self.assertEqual(apply_delta(a,make_delta(a,b)),b)
    def test_033_missing_only(self): r,o,p=self.base(); st=prepare_state(r,o,p,binding=p.binding,state_epoch=p.state_epoch); known=dict(st.record_fingerprints); known.pop('OBS:O000'); plan=missing_only_sync_plan(st,known); self.assertEqual(plan.missing_or_changed_record_ids,('OBS:O000',)); self.assertFalse(plan.full_resend_required)
    def test_034_source_version_changes_registry(self): r,o,p=self.base(); a=prepare_state(r,o,p,binding=p.binding,state_epoch=p.state_epoch); b=prepare_state(r,(replace(o[0],source_version='V2'),)+o[1:],p,binding=p.binding,state_epoch=p.state_epoch); self.assertNotEqual(a.registry_fingerprint,b.registry_fingerprint)
    def test_035_evidence_fp_changes_registry(self): r,o,p=self.base(); a=prepare_state(r,o,p,binding=p.binding,state_epoch=p.state_epoch); b=prepare_state(r,(replace(o[0],evidence_fingerprint='NEW'),)+o[1:],p,binding=p.binding,state_epoch=p.state_epoch); self.assertNotEqual(a.registry_fingerprint,b.registry_fingerprint)
    def test_036_policy_changes_calibration_fp(self): r,o,p=self.base(); a=prepare_state(r,o,p,binding=p.binding,state_epoch=p.state_epoch); b=prepare_state(r,o,replace(p,prior_accuracy=.55),binding=p.binding,state_epoch=p.state_epoch); self.assertNotEqual(a.calibration_fingerprint,b.calibration_fingerprint)
    def test_037_cache_not_truth(self): z=default_evaluation(); self.assertFalse(z.world_truth_proven); self.assertFalse(z.authority_promoted)
    def test_038_high_risk_good_calibration_allow(self): r,o,p=self.base(); r=replace(r,risk=RiskLevel.HIGH); z=evaluate(r,o,p); self.assertEqual(z.decision,Decision.ALLOW)
    def test_039_critical_threshold_hold(self): r,o,p=self.base(); r=replace(r,risk=RiskLevel.CRITICAL,predicted_confidence=.8); self.assertEqual(evaluate(r,o,p).decision,Decision.HOLD)
    def test_040_underconfidence_not_truth(self): r,o,p=self.base(); o=tuple(replace(x,predicted_confidence=.3) for x in o); z=evaluate(replace(r,predicted_confidence=.3),o,p); self.neg(z)

def _gen(k):
    def f(self):
        r,o,p=self.base(); mode=k%12
        if mode==0: want=Decision.ALLOW
        elif mode==1: r,o,p=self.over(); want=Decision.HOLD
        elif mode==2: r,o,p=self.drift(); want=Decision.HOLD
        elif mode==3: o=o[:5]; r=replace(r,risk=RiskLevel.HIGH); want=Decision.HOLD
        elif mode==4: p=replace(p,revoked=True); want=Decision.HOLD
        elif mode==5: r=replace(r,observed=False); want=Decision.HOLD
        elif mode==6: o=(replace(o[0],observed=False),)+o[1:]; want=Decision.HOLD
        elif mode==7: r=replace(r,task_class='NONE'); want=Decision.HOLD
        elif mode==8: r=replace(r,predicted_confidence=.59); want=Decision.HOLD
        elif mode==9: r=replace(r,risk=RiskLevel.HIGH); want=Decision.ALLOW
        elif mode==10: r=replace(r,risk=RiskLevel.CRITICAL); want=Decision.HOLD
        else: o=tuple(replace(x,predicted_confidence=.3) for x in o); r=replace(r,predicted_confidence=.3); want=Decision.ALLOW
        z=evaluate(r,o,p); self.assertEqual(z.decision,want); self.neg(z)
    return f
for k in range(120): setattr(T,f'test_regression_{k:03d}',_gen(k))
if __name__=='__main__': unittest.main(verbosity=2)
