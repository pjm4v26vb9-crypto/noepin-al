import unittest
from dataclasses import replace
from noepin_al_092_bayesian_uncertainty_fusion import *

class T(unittest.TestCase):
    def base(self): return default_request(),default_hypotheses(),default_evidence(),default_sources(),default_policy()
    def neg(self,z):
        self.assertFalse(z.permission_granted); self.assertFalse(z.action_executed); self.assertFalse(z.plan_committed); self.assertFalse(z.atomic_publish_executed); self.assertFalse(z.external_write_performed); self.assertFalse(z.world_truth_proven); self.assertFalse(z.authority_promoted); self.assertFalse(z.safety_proven); self.assertFalse(z.action_success)
    def test_001_default_allow(self): self.assertEqual(default_evaluation().decision,Decision.ALLOW)
    def test_002_default_next_gate(self): self.assertTrue(default_evaluation().next_gate_candidate)
    def test_003_authority_negative(self): self.neg(default_evaluation())
    def test_004_conflicting_hold(self): r,h,e,s,p=self.base(); e=(replace(e[0],likelihoods=(('H-SAFE',.55),('H-UNSAFE',.45))),replace(e[1],likelihoods=(('H-SAFE',.45),('H-UNSAFE',.55))),replace(e[2],likelihoods=(('H-SAFE',.5),('H-UNSAFE',.5))),replace(e[3],likelihoods=(('H-SAFE',.5),('H-UNSAFE',.5)))); self.assertEqual(evaluate(r,h,e,s,p).decision,Decision.HOLD)
    def test_005_low_reliability_lowers_confidence(self): r,h,e,s,p=self.base(); z1=evaluate(r,h,e,s,p); s2=tuple(replace(x,reliability=.1) for x in s); z2=evaluate(r,h,e,s2,p); self.assertLess(z2.decision_confidence,z1.decision_confidence)
    def test_006_biased_prior_updates(self): r,h,e,s,p=self.base(); h=(replace(h[0],prior=.1),replace(h[1],prior=.9)); z=evaluate(r,h,e,s,p); self.assertGreater(z.target_posterior,.5)
    def test_007_unknown_high_risk_hold(self): r,h,e,s,p=self.base(); r=replace(r,risk=RiskLevel.HIGH); e=(replace(e[0],model_known=False),)+e[1:]; self.assertEqual(evaluate(r,h,e,s,p).decision,Decision.HOLD)
    def test_008_unknown_reduces_confidence(self): r,h,e,s,p=self.base(); z1=evaluate(r,h,e,s,p); z2=evaluate(r,h,tuple(replace(x,model_known=False) for x in e),s,p); self.assertLess(z2.decision_confidence,z1.decision_confidence)
    def test_009_dependency_discount(self): r,h,e,s,p=self.base(); z1=evaluate(r,h,e,s,p); dep=tuple(replace(x,dependency_group='SAME') for x in e); z2=evaluate(r,h,dep,s,p); self.assertGreater(z2.dependency_penalty,z1.dependency_penalty)
    def test_010_policy_revoked(self): r,h,e,s,p=self.base(); self.assertEqual(evaluate(r,h,e,s,replace(p,revoked=True)).decision,Decision.HOLD)
    def test_011_source_unobserved(self): r,h,e,s,p=self.base(); s=(replace(s[0],observed=False),s[1]); self.assertEqual(evaluate(r,h,e,s,p).decision,Decision.HOLD)
    def test_012_evidence_unobserved(self): r,h,e,s,p=self.base(); e=(replace(e[0],observed=False),)+e[1:]; self.assertEqual(evaluate(r,h,e,s,p).decision,Decision.HOLD)
    def test_013_source_missing(self): r,h,e,s,p=self.base(); self.assertEqual(evaluate(r,h,e,s[:1],p).decision,Decision.HOLD)
    def test_014_target_missing(self): r,h,e,s,p=self.base(); r=replace(r,target_hypothesis_id='X'); self.assertEqual(evaluate(r,h,e,s,p).decision,Decision.HOLD)
    def test_015_invalid_prior(self): r,h,e,s,p=self.base(); h=(replace(h[0],prior=0),h[1]); self.assertEqual(evaluate(r,h,e,s,p).decision,Decision.HOLD)
    def test_016_invalid_likelihood(self): r,h,e,s,p=self.base(); e=(replace(e[0],likelihoods=(('H-SAFE',1.2),('H-UNSAFE',.1))),)+e[1:]; self.assertEqual(evaluate(r,h,e,s,p).decision,Decision.HOLD)
    def test_017_binding_mismatch(self): r,h,e,s,p=self.base(); self.assertEqual(evaluate(replace(r,binding='X'),h,e,s,p).decision,Decision.HOLD)
    def test_018_state_mismatch(self): r,h,e,s,p=self.base(); self.assertEqual(evaluate(replace(r,state_epoch='X'),h,e,s,p).decision,Decision.HOLD)
    def test_019_duplicate_evidence(self): r,h,e,s,p=self.base(); self.assertEqual(evaluate(r,h,e+(e[0],),s,p).decision,Decision.HOLD)
    def test_020_duplicate_source(self): r,h,e,s,p=self.base(); self.assertEqual(evaluate(r,h,e,s+(s[0],),p).decision,Decision.HOLD)
    def test_021_duplicate_hypothesis(self): r,h,e,s,p=self.base(); self.assertEqual(evaluate(r,h+(h[0],),e,s,p).decision,Decision.HOLD)
    def test_022_no_evidence(self): r,h,e,s,p=self.base(); self.assertEqual(evaluate(r,h,(),s,p).decision,Decision.HOLD)
    def test_023_source_version_mismatch(self): r,h,e,s,p=self.base(); e=(replace(e[0],source_version='V2'),)+e[1:]; self.assertEqual(evaluate(r,h,e,s,p).decision,Decision.HOLD)
    def test_024_high_risk_wide_hold(self): r,h,e,s,p=self.base(); r=replace(r,risk=RiskLevel.HIGH); e=tuple(replace(x,likelihoods=(('H-SAFE',.55),('H-UNSAFE',.45))) for x in e); self.assertEqual(evaluate(r,h,e,s,p).decision,Decision.HOLD)
    def test_025_critical_wide_hold(self): r,h,e,s,p=self.base(); r=replace(r,risk=RiskLevel.CRITICAL); e=tuple(replace(x,likelihoods=(('H-SAFE',.55),('H-UNSAFE',.45))) for x in e); self.assertEqual(evaluate(r,h,e,s,p).decision,Decision.HOLD)
    def test_026_refutation_deny(self): r,h,e,s,p=self.base(); e=tuple(replace(x,likelihoods=(('H-SAFE',.02),('H-UNSAFE',.98))) for x in e); z=evaluate(r,h,e,s,p); self.assertEqual(z.decision,Decision.DENY); self.assertTrue(z.refutation_candidate)
    def test_027_bounds(self): z=default_evaluation(); self.assertGreaterEqual(z.credible_interval[0],0); self.assertLessEqual(z.credible_interval[1],1)
    def test_028_posterior_sums_one(self): self.assertAlmostEqual(sum(v for _,v in default_evaluation().posterior),1.0,places=12)
    def test_029_prepared_valid(self): r,h,e,s,p=self.base(); st=prepare_state(r,h,e,s,p,binding=p.binding,state_epoch=p.state_epoch); self.assertTrue(validate_prepared_integrity(st)); self.assertEqual(evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_calibration_fingerprint=st.calibration_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True),default_evaluation())
    def test_030_prepared_context_changed(self): r,h,e,s,p=self.base(); st=prepare_state(r,h,e,s,p,binding=p.binding,state_epoch=p.state_epoch); self.assertEqual(evaluate_prepared(st,current_context_fingerprint='BAD',current_dependency_fingerprint=st.dependency_fingerprint,current_calibration_fingerprint=st.calibration_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True).decision,Decision.HOLD)
    def test_031_prepared_unvalidated(self): r,h,e,s,p=self.base(); st=prepare_state(r,h,e,s,p,binding=p.binding,state_epoch=p.state_epoch); self.assertEqual(evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_calibration_fingerprint=st.calibration_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=False).decision,Decision.HOLD)
    def test_032_delta_roundtrip(self): r,h,e,s,p=self.base(); a=prepare_state(r,h,e,s,p,binding=p.binding,state_epoch=p.state_epoch); e2=(replace(e[0],likelihoods=(('H-SAFE',.7),('H-UNSAFE',.3))),)+e[1:]; b=prepare_state(r,h,e2,s,p,binding=p.binding,state_epoch=p.state_epoch); self.assertEqual(apply_delta(a,make_delta(a,b)),b)
    def test_033_missing_only(self): r,h,e,s,p=self.base(); st=prepare_state(r,h,e,s,p,binding=p.binding,state_epoch=p.state_epoch); known=dict(st.record_fingerprints); known.pop('EVID:E-A'); plan=missing_only_sync_plan(st,known); self.assertEqual(plan.missing_or_changed_record_ids,('EVID:E-A',)); self.assertFalse(plan.full_resend_required)
    def test_034_deterministic(self): r,h,e,s,p=self.base(); self.assertEqual(evaluate(r,h,e,s,p),evaluate(r,tuple(reversed(h)),tuple(reversed(e)),tuple(reversed(s)),p))
    def test_035_source_fingerprint_changes_registry(self): r,h,e,s,p=self.base(); a=prepare_state(r,h,e,s,p,binding=p.binding,state_epoch=p.state_epoch); s2=(replace(s[0],source_fingerprint='NEW'),s[1]); b=prepare_state(r,h,e,s2,p,binding=p.binding,state_epoch=p.state_epoch); self.assertNotEqual(a.registry_fingerprint,b.registry_fingerprint)
    def test_036_evidence_fingerprint_changes_registry(self): r,h,e,s,p=self.base(); a=prepare_state(r,h,e,s,p,binding=p.binding,state_epoch=p.state_epoch); e2=(replace(e[0],evidence_fingerprint='NEW'),)+e[1:]; b=prepare_state(r,h,e2,s,p,binding=p.binding,state_epoch=p.state_epoch); self.assertNotEqual(a.registry_fingerprint,b.registry_fingerprint)
    def test_037_calibration_changes_fingerprint(self): r,h,e,s,p=self.base(); a=prepare_state(r,h,e,s,p,binding=p.binding,state_epoch=p.state_epoch); b=prepare_state(r,h,e,s,replace(p,allow_threshold=.7),binding=p.binding,state_epoch=p.state_epoch); self.assertNotEqual(a.calibration_fingerprint,b.calibration_fingerprint)
    def test_038_posterior_not_truth(self): z=default_evaluation(); self.assertFalse(z.world_truth_proven); self.assertFalse(z.authority_promoted)
    def test_039_low_reliability_not_zeroed(self): r,h,e,s,p=self.base(); s=tuple(replace(x,reliability=0.0) for x in s); z=evaluate(r,h,e,s,p); self.assertGreater(z.effective_evidence_weight,0)
    def test_040_confidence_in_range(self): z=default_evaluation(); self.assertTrue(0<=z.decision_confidence<=1)

def _gen(k):
    def f(self):
        r,h,e,s,p=self.base(); mode=k%12
        if mode==0: want=Decision.ALLOW
        elif mode==1: e=tuple(replace(x,likelihoods=(('H-SAFE',.02),('H-UNSAFE',.98))) for x in e); want=Decision.DENY
        elif mode==2: r=replace(r,risk=RiskLevel.HIGH); want=Decision.ALLOW
        elif mode==3: e=(replace(e[0],model_known=False),)+e[1:]; r=replace(r,risk=RiskLevel.HIGH); want=Decision.HOLD
        elif mode==4: p=replace(p,revoked=True); want=Decision.HOLD
        elif mode==5: e=(replace(e[0],observed=False),)+e[1:]; want=Decision.HOLD
        elif mode==6: s=(replace(s[0],observed=False),s[1]); want=Decision.HOLD
        elif mode==7: r=replace(r,observed=False); want=Decision.HOLD
        elif mode==8: e=tuple(replace(x,dependency_group='SAME') for x in e); want=Decision.ALLOW
        elif mode==9: h=(replace(h[0],prior=.05),replace(h[1],prior=.95)); want=Decision.ALLOW
        elif mode==10: e=tuple(replace(x,likelihoods=(('H-SAFE',.55),('H-UNSAFE',.45))) for x in e); want=Decision.HOLD
        else: e=(replace(e[0],source_version='BAD'),)+e[1:]; want=Decision.HOLD
        z=evaluate(r,h,e,s,p); self.assertEqual(z.decision,want); self.neg(z)
    return f
for k in range(120): setattr(T,f'test_regression_{k:03d}',_gen(k))
if __name__=='__main__': unittest.main(verbosity=2)
