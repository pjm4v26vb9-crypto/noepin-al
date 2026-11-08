import dataclasses, unittest
import noepin_al_098_epistemic_aleatoric_splitter as m

class TestAL098(unittest.TestCase):
    def test_001_default_allow(self):
        r=m.default_evaluation(); self.assertEqual(r.decision,m.Decision.ALLOW); self.assertEqual(r.separation_status,m.SeparationStatus.SEPARATED); self.assertTrue(r.next_gate_candidate)
    def test_002_default_boundaries_false(self):
        r=m.default_evaluation(); self.assertFalse(any((r.cache_promoted_to_truth,r.cache_promoted_to_authority,r.permission_granted,r.research_executed,r.action_executed,r.plan_committed,r.atomic_publish_executed,r.external_write_performed,r.world_truth_proven,r.intrinsic_randomness_proven,r.resolvability_proven,r.safety_proven,r.action_success)))
    def test_003_high_epistemic_holds(self):
        p=m.default_policy(); xs=list(m.default_predictions()); vals=(.1,.5,.9); xs=[dataclasses.replace(x,predicted_value=vals[i],observation_noise_variance=.0001) for i,x in enumerate(xs)]; r=m.evaluate(m.default_query(),tuple(xs),p); self.assertEqual(r.decision,m.Decision.HOLD); self.assertTrue(r.research_candidate); self.assertIn('EPISTEMIC_HIGH',r.reasons)
    def test_004_high_aleatoric_critical_human(self):
        p=m.default_policy(); q=dataclasses.replace(m.default_query(),risk=m.RiskLevel.CRITICAL); xs=tuple(dataclasses.replace(x,observation_noise_variance=.05) for x in m.default_predictions()); r=m.evaluate(q,xs,p); self.assertEqual(r.decision,m.Decision.HUMAN_APPROVAL); self.assertTrue(r.human_approval_candidate)
    def test_005_both_high_epistemic_precedence(self):
        p=m.default_policy(); q=dataclasses.replace(m.default_query(),risk=m.RiskLevel.CRITICAL); xs=list(m.default_predictions()); vals=(.1,.5,.9); xs=tuple(dataclasses.replace(x,predicted_value=vals[i],observation_noise_variance=.05) for i,x in enumerate(xs)); r=m.evaluate(q,xs,p); self.assertEqual(r.decision,m.Decision.HOLD); self.assertTrue(r.research_candidate); self.assertTrue(r.human_approval_candidate)
    def test_006_inseparable_missing_noise(self):
        p=m.default_policy(); xs=list(m.default_predictions()); xs[0]=dataclasses.replace(xs[0],observation_noise_variance=None); r=m.evaluate(m.default_query(),tuple(xs),p); self.assertEqual(r.decision,m.Decision.HOLD); self.assertEqual(r.separation_status,m.SeparationStatus.INSEPARABLE); self.assertFalse(r.research_candidate)
    def test_007_inseparable_single_model(self):
        p=m.default_policy(); xs=tuple(dataclasses.replace(x,model_id='ONE') for x in m.default_predictions()); r=m.evaluate(m.default_query(),xs,p); self.assertEqual(r.separation_status,m.SeparationStatus.INSEPARABLE)
    def test_008_inseparable_too_few_predictions(self):
        p=m.default_policy(); r=m.evaluate(m.default_query(),m.default_predictions()[:2],p); self.assertEqual(r.decision,m.Decision.HOLD)
    def test_009_policy_revoked(self):
        p=dataclasses.replace(m.default_policy(),revoked=True); self.assertEqual(m.evaluate(m.default_query(),m.default_predictions(),p).decision,m.Decision.HOLD)
    def test_010_scope_mismatch(self):
        q=dataclasses.replace(m.default_query(),binding='X'); self.assertEqual(m.evaluate(q,m.default_predictions(),m.default_policy()).decision,m.Decision.HOLD)
    def test_011_duplicate_ids(self):
        p=m.default_policy(); xs=list(m.default_predictions()); xs[1]=dataclasses.replace(xs[1],prediction_id=xs[0].prediction_id); self.assertEqual(m.evaluate(m.default_query(),tuple(xs),p).decision,m.Decision.HOLD)
    def test_012_negative_noise_invalid(self):
        p=m.default_policy(); xs=list(m.default_predictions()); xs[0]=dataclasses.replace(xs[0],observation_noise_variance=-1); self.assertEqual(m.evaluate(m.default_query(),tuple(xs),p).decision,m.Decision.HOLD)
    def test_013_prepared_reuse(self):
        p=m.default_policy(); q=m.default_query(); xs=m.default_predictions(); st=m.prepare_state(q,xs,p,binding=p.binding,state_epoch=p.state_epoch); ok=m.validate_prepared_integrity(st); r=m.evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_calibration_fingerprint=st.calibration_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=ok); self.assertEqual(r,m.evaluate(q,xs,p))
    def test_014_prepared_integrity_required(self):
        p=m.default_policy(); st=m.prepare_state(m.default_query(),m.default_predictions(),p,binding=p.binding,state_epoch=p.state_epoch); r=m.evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_calibration_fingerprint=st.calibration_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=False); self.assertEqual(r.decision,m.Decision.HOLD)
    def test_015_prepared_dependency_mismatch(self):
        p=m.default_policy(); st=m.prepare_state(m.default_query(),m.default_predictions(),p,binding=p.binding,state_epoch=p.state_epoch); r=m.evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint='X',current_calibration_fingerprint=st.calibration_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True); self.assertEqual(r.decision,m.Decision.HOLD)
    def test_016_delta_roundtrip(self):
        p=m.default_policy(); q=m.default_query(); base=m.prepare_state(q,m.default_predictions(),p,binding=p.binding,state_epoch=p.state_epoch); xs=list(m.default_predictions()); xs[0]=dataclasses.replace(xs[0],predicted_value=.55,source_version='V2'); target=m.prepare_state(q,tuple(xs),p,binding=p.binding,state_epoch=p.state_epoch); self.assertEqual(m.apply_delta(base,m.make_delta(base,target)),target)
    def test_017_sync_plan(self):
        p=m.default_policy(); st=m.prepare_state(m.default_query(),m.default_predictions(),p,binding=p.binding,state_epoch=p.state_epoch); known=dict(st.record_fingerprints); known.pop(next(iter(known))); sp=m.missing_only_sync_plan(st,known); self.assertEqual(len(sp.missing_or_changed_record_ids),1); self.assertFalse(sp.full_resend_required)
    def test_018_threshold_monotonic(self):
        p=m.default_policy(); self.assertGreaterEqual(p.epistemic_threshold_low,p.epistemic_threshold_medium); self.assertGreaterEqual(p.epistemic_threshold_medium,p.epistemic_threshold_high); self.assertGreaterEqual(p.epistemic_threshold_high,p.epistemic_threshold_critical); self.assertGreaterEqual(p.aleatoric_threshold_low,p.aleatoric_threshold_medium); self.assertGreaterEqual(p.aleatoric_threshold_medium,p.aleatoric_threshold_high); self.assertGreaterEqual(p.aleatoric_threshold_high,p.aleatoric_threshold_critical)
    def test_019_total_variance_sum(self):
        r=m.default_evaluation(); self.assertAlmostEqual(r.total_variance,r.epistemic_variance+r.aleatoric_variance,12); self.assertAlmostEqual(r.epistemic_fraction+r.aleatoric_fraction,1.0,12)
    def test_020_high_aleatoric_lowrisk_hold(self):
        p=m.default_policy(); xs=tuple(dataclasses.replace(x,observation_noise_variance=.05) for x in m.default_predictions()); r=m.evaluate(m.default_query(),xs,p); self.assertEqual(r.decision,m.Decision.HOLD); self.assertEqual(r.next_action,m.NextAction.RISK_AWARE_DECISION_CANDIDATE)

def _make(i):
    def t(self):
        p=m.default_policy(); risk=list(m.RiskLevel)[i%4]; q=dataclasses.replace(m.default_query(),risk=risk)
        center=((i%20)-10)/100
        spread=(i%7)/100
        noise=((i*3)%9)/1000
        xs=[]
        for j,x in enumerate(m.default_predictions()):
            v=.5+center+(j-1)*spread
            nv=noise + (j%2)*.0002
            xs.append(dataclasses.replace(x,prediction_id=f'P{j}-{i}',run_id=f'R{i}-{j}',predicted_value=v,observation_noise_variance=nv,source_version=f'V{i}',source_fingerprint=f'S{i}-{j}',evidence_fingerprint=f'E{i}-{j}'))
        r=m.evaluate(q,tuple(xs),p)
        self.assertTrue(0<=r.epistemic_score<=1 and 0<=r.aleatoric_score<=1)
        self.assertAlmostEqual(r.total_variance,r.epistemic_variance+r.aleatoric_variance,10)
        self.assertFalse(r.permission_granted); self.assertFalse(r.action_executed); self.assertFalse(r.world_truth_proven); self.assertFalse(r.intrinsic_randomness_proven); self.assertFalse(r.resolvability_proven); self.assertFalse(r.action_success)
    return t
for i in range(21,161): setattr(TestAL098,f'test_{i:03d}_generated',_make(i))
if __name__=='__main__': unittest.main(verbosity=2)
