import unittest
from dataclasses import replace
from noepin_al_088_decision_freshness_window_verifier import *

class T(unittest.TestCase):
    def base(self): return default_request(),default_dependencies(),default_policy()
    def neg(self,z):
        self.assertFalse(z.cache_promoted_to_truth); self.assertFalse(z.cache_promoted_to_authority)
        self.assertFalse(z.permission_granted); self.assertFalse(z.action_executed); self.assertFalse(z.plan_committed)
        self.assertFalse(z.atomic_publish_executed); self.assertFalse(z.external_write_performed)
        self.assertFalse(z.world_truth_proven); self.assertFalse(z.safety_proven); self.assertFalse(z.action_success)
    def test_001_default_allow(self): z=default_evaluation(); self.assertEqual(z.decision,Decision.ALLOW); self.assertEqual(z.freshness_state,FreshnessState.FRESH); self.assertTrue(z.next_gate_candidate); self.neg(z)
    def test_002_critical_expired_hold(self): r,d,p=self.base(); d=(replace(d[0],criticality=Criticality.CRITICAL,last_observed_at=900),d[1]); z=evaluate(r,d,p); self.assertEqual(z.decision,Decision.HOLD); self.assertEqual(z.reevaluation_flag,ReevaluationFlag.REEVALUATE_DECISION)
    def test_003_low_minor_expired_refresh(self): r,d,p=self.base(); r=replace(r,risk=RiskLevel.LOW,decision_time=1005); d=(replace(d[0],criticality=Criticality.LOW,last_observed_at=600,volatility_score=0.1),replace(d[1],last_observed_at=1009,criticality=Criticality.LOW,volatility_score=0.0)); z=evaluate(r,d,p); self.assertEqual(z.decision,Decision.HOLD); self.assertEqual(z.reevaluation_flag,ReevaluationFlag.REFRESH_FIELDS); self.assertIn('FIELD-A',z.refresh_required_fields)
    def test_004_high_volatility_shortens(self): r,d,p=self.base(); z1=evaluate(r,d,p); d2=(replace(d[0],volatility_score=1.0,criticality=Criticality.LOW,last_observed_at=1009),replace(d[1],criticality=Criticality.LOW,last_observed_at=1009,volatility_score=0.0)); z2=evaluate(r,d2,p); self.assertLess(z2.freshness_window_seconds,z1.freshness_window_seconds)
    def test_005_unknown_high_short_window(self): r,d,p=self.base(); r=replace(r,risk=RiskLevel.HIGH,now=1004,decision_time=1000); d=(replace(d[0],volatility_score=None,last_observed_at=1003,criticality=Criticality.LOW),replace(d[1],last_observed_at=1003,criticality=Criticality.LOW)); z=evaluate(r,d,p); self.assertEqual(z.decision,Decision.ALLOW); self.assertLessEqual(z.freshness_window_seconds,5.0); self.assertIn('FIELD-A',z.unknown_volatility_fields)
    def test_006_unknown_high_expired(self): r,d,p=self.base(); r=replace(r,risk=RiskLevel.HIGH,now=1011,decision_time=1008); d=(replace(d[0],volatility_score=None,last_observed_at=1005,criticality=Criticality.LOW),replace(d[1],last_observed_at=1010,criticality=Criticality.LOW)); self.assertEqual(evaluate(r,d,p).decision,Decision.HOLD)
    def test_007_unknown_low_window(self): r,d,p=self.base(); r=replace(r,risk=RiskLevel.LOW,now=1005,decision_time=1000); d=(replace(d[0],volatility_score=None,last_observed_at=1004,criticality=Criticality.LOW),replace(d[1],last_observed_at=1004,criticality=Criticality.LOW)); z=evaluate(r,d,p); self.assertEqual(z.decision,Decision.ALLOW); self.assertLessEqual(z.freshness_window_seconds,30.0)
    def test_008_future_dependency_hold(self): r,d,p=self.base(); d=(replace(d[0],last_observed_at=1013),d[1]); self.assertEqual(evaluate(r,d,p).decision,Decision.HOLD)
    def test_009_future_within_skew_allowed(self): r,d,p=self.base(); d=(replace(d[0],last_observed_at=1011),d[1]); self.assertEqual(evaluate(r,d,p).decision,Decision.ALLOW)
    def test_010_future_decision_hold(self): r,d,p=self.base(); r=replace(r,decision_time=1013); self.assertEqual(evaluate(r,d,p).decision,Decision.HOLD)
    def test_011_future_decision_within_skew(self): r,d,p=self.base(); r=replace(r,decision_time=1011); self.assertEqual(evaluate(r,d,p).decision,Decision.ALLOW)
    def test_012_revoked_policy(self): r,d,p=self.base(); self.assertEqual(evaluate(r,d,replace(p,revoked=True)).decision,Decision.HOLD)
    def test_013_request_binding(self): r,d,p=self.base(); self.assertEqual(evaluate(replace(r,binding='X'),d,p).decision,Decision.HOLD)
    def test_014_dependency_binding(self): r,d,p=self.base(); d=(replace(d[0],binding='X'),d[1]); self.assertEqual(evaluate(r,d,p).decision,Decision.HOLD)
    def test_015_duplicate_field(self): r,d,p=self.base(); self.assertEqual(evaluate(r,(d[0],replace(d[1],field_id=d[0].field_id)),p).decision,Decision.HOLD)
    def test_016_invalid_vol_low(self): r,d,p=self.base(); d=(replace(d[0],volatility_score=-0.1),d[1]); self.assertEqual(evaluate(r,d,p).decision,Decision.HOLD)
    def test_017_invalid_vol_high(self): r,d,p=self.base(); d=(replace(d[0],volatility_score=1.1),d[1]); self.assertEqual(evaluate(r,d,p).decision,Decision.HOLD)
    def test_018_no_deps(self): r,d,p=self.base(); self.assertEqual(evaluate(r,(),p).decision,Decision.HOLD)
    def test_019_request_unobserved(self): r,d,p=self.base(); self.assertEqual(evaluate(replace(r,observed=False),d,p).decision,Decision.HOLD)
    def test_020_dep_unobserved(self): r,d,p=self.base(); d=(replace(d[0],observed=False),d[1]); z=evaluate(r,d,p); self.assertEqual(z.freshness_state,FreshnessState.UNKNOWN)
    def test_021_empty_source(self): r,d,p=self.base(); d=(replace(d[0],source_id=''),d[1]); self.assertEqual(evaluate(r,d,p).decision,Decision.HOLD)
    def test_022_empty_version(self): r,d,p=self.base(); d=(replace(d[0],source_version=''),d[1]); self.assertEqual(evaluate(r,d,p).decision,Decision.HOLD)
    def test_023_empty_evidence_fp(self): r,d,p=self.base(); d=(replace(d[0],evidence_fingerprint=''),d[1]); self.assertEqual(evaluate(r,d,p).decision,Decision.HOLD)
    def test_024_decision_expired(self): r,d,p=self.base(); r=replace(r,now=1150); d=(replace(d[0],last_observed_at=1149,criticality=Criticality.LOW,volatility_score=0.0),replace(d[1],last_observed_at=1149,criticality=Criticality.LOW,volatility_score=0.0)); self.assertEqual(evaluate(r,d,p).reevaluation_flag,ReevaluationFlag.REEVALUATE_DECISION)
    def test_025_exact_boundary_fresh(self): r,d,p=self.base(); r=replace(r,risk=RiskLevel.HIGH,now=1015,decision_time=1014); d=(replace(d[0],last_observed_at=1010,volatility_score=None,criticality=Criticality.LOW),replace(d[1],last_observed_at=1015,criticality=Criticality.LOW,volatility_score=0.0)); self.assertEqual(evaluate(r,d,p).decision,Decision.ALLOW)
    def test_026_beyond_boundary_hold(self): r,d,p=self.base(); r=replace(r,risk=RiskLevel.HIGH,now=1015.1,decision_time=1014); d=(replace(d[0],last_observed_at=1010,volatility_score=None,criticality=Criticality.LOW),replace(d[1],last_observed_at=1015,criticality=Criticality.LOW,volatility_score=0.0)); self.assertEqual(evaluate(r,d,p).decision,Decision.HOLD)
    def test_027_high_risk_shorter_than_low(self): r,d,p=self.base(); low=evaluate(replace(r,risk=RiskLevel.LOW,decision_time=1009),d,p); high=evaluate(replace(r,risk=RiskLevel.HIGH,decision_time=1009),d,p); self.assertLess(high.freshness_window_seconds,low.freshness_window_seconds)
    def test_028_critical_risk_shortest(self): r,d,p=self.base(); r=replace(r,risk=RiskLevel.CRITICAL,now=1001,decision_time=1000); d=tuple(replace(x,last_observed_at=1001,criticality=Criticality.LOW,volatility_score=0.0) for x in d); self.assertLessEqual(evaluate(r,d,p).freshness_window_seconds,p.critical_window_seconds)
    def test_029_prepared_semantic(self): x=self.base(); st=prepare_state(*x,binding=x[-1].binding,state_epoch=x[-1].state_epoch); self.assertTrue(validate_prepared_integrity(st)); self.assertEqual(evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_calibration_fingerprint=st.calibration_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True),evaluate(*x))
    def test_030_prepared_stale_context(self): x=self.base(); st=prepare_state(*x,binding=x[-1].binding,state_epoch=x[-1].state_epoch); self.assertEqual(evaluate_prepared(st,current_context_fingerprint='X',current_dependency_fingerprint=st.dependency_fingerprint,current_calibration_fingerprint=st.calibration_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True).decision,Decision.HOLD)
    def test_031_prepared_stale_evidence(self): x=self.base(); st=prepare_state(*x,binding=x[-1].binding,state_epoch=x[-1].state_epoch); self.assertEqual(evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint='X',current_calibration_fingerprint=st.calibration_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True).decision,Decision.HOLD)
    def test_032_prepared_integrity_required(self): x=self.base(); st=prepare_state(*x,binding=x[-1].binding,state_epoch=x[-1].state_epoch); self.assertEqual(evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_calibration_fingerprint=st.calibration_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=False).decision,Decision.HOLD)
    def test_033_delta_reconstruction(self): x=self.base(); s1=prepare_state(*x,binding=x[-1].binding,state_epoch=x[-1].state_epoch); d=list(x[1]); d[0]=replace(d[0],source_version='V2',evidence_fingerprint='EVID-A2'); x2=(x[0],tuple(d),x[2]); s2=prepare_state(*x2,binding=x2[-1].binding,state_epoch=x2[-1].state_epoch); self.assertEqual(apply_delta(s1,make_delta(s1,s2)),s2)
    def test_034_missing_only(self): r,_,p=self.base(); deps=tuple(DependencyFreshness(f'F{n}',1009,0.1,Criticality.LOW,'S',f'V{n}',f'E{n}',True,p.binding,p.state_epoch) for n in range(20)); st=prepare_state(r,deps,p,binding=p.binding,state_epoch=p.state_epoch); k=dict(st.dependency_fingerprints); [k.pop(f'F{n}') for n in range(5)]; plan=missing_only_sync_plan(st,k); self.assertEqual(len(plan.missing_or_changed_field_ids),5); self.assertFalse(plan.full_resend_required)
    def test_035_delta_smaller(self): r,_,p=self.base(); deps=tuple(DependencyFreshness(f'F{n}',1009,0.1,Criticality.LOW,'S',f'V{n}',f'E{n}',True,p.binding,p.state_epoch) for n in range(100)); s1=prepare_state(r,deps,p,binding=p.binding,state_epoch=p.state_epoch); d=list(deps); d[0]=replace(d[0],source_version='VX'); s2=prepare_state(r,tuple(d),p,binding=p.binding,state_epoch=p.state_epoch); self.assertLess(delta_bytes(make_delta(s1,s2)),full_registry_bytes(s2))
    def test_036_sort_deterministic(self): r,d,p=self.base(); s1=prepare_state(r,d,p,binding=p.binding,state_epoch=p.state_epoch); s2=prepare_state(r,tuple(reversed(d)),p,binding=p.binding,state_epoch=p.state_epoch); self.assertEqual(s1,s2)
    def test_037_evidence_change_changes_fp(self): r,d,p=self.base(); s1=prepare_state(r,d,p,binding=p.binding,state_epoch=p.state_epoch); d2=(replace(d[0],evidence_fingerprint='NEW'),d[1]); s2=prepare_state(r,d2,p,binding=p.binding,state_epoch=p.state_epoch); self.assertNotEqual(s1.dependency_fingerprint,s2.dependency_fingerprint)
    def test_038_unknown_list(self): r,d,p=self.base(); d=(replace(d[0],volatility_score=None),d[1]); self.assertIn('FIELD-A',evaluate(r,d,p).unknown_volatility_fields)
    def test_039_authority_flags_false(self): self.neg(default_evaluation())
    def test_040_cache_candidate_only(self): z=default_evaluation(); self.assertTrue(z.cache_reuse_candidate); self.assertFalse(z.cache_promoted_to_truth); self.assertFalse(z.cache_promoted_to_authority)

def _gen(k):
    def f(self):
        r,d,p=self.base(); mode=k%12
        if mode==0: want=Decision.ALLOW
        elif mode==1: d=(replace(d[0],last_observed_at=900,criticality=Criticality.CRITICAL),d[1]); want=Decision.HOLD
        elif mode==2: r=replace(r,risk=RiskLevel.HIGH,now=1011,decision_time=1008); d=(replace(d[0],volatility_score=None,last_observed_at=1005,criticality=Criticality.LOW),replace(d[1],last_observed_at=1010,criticality=Criticality.LOW)); want=Decision.HOLD
        elif mode==3: d=(replace(d[0],observed=False),d[1]); want=Decision.HOLD
        elif mode==4: d=(replace(d[0],source_version=''),d[1]); want=Decision.HOLD
        elif mode==5: r=replace(r,now=1004,decision_time=1003); d=tuple(replace(x,last_observed_at=1004,volatility_score=1.0,criticality=Criticality.LOW) for x in d); want=Decision.ALLOW
        elif mode==6: r=replace(r,now=1150); d=tuple(replace(x,last_observed_at=1149,volatility_score=0.0,criticality=Criticality.LOW) for x in d); want=Decision.HOLD
        elif mode==7: p=replace(p,revoked=True); want=Decision.HOLD
        elif mode==8: d=(replace(d[0],last_observed_at=1013),d[1]); want=Decision.HOLD
        elif mode==9: r=replace(r,risk=RiskLevel.LOW,decision_time=1009); d=(replace(d[0],last_observed_at=600,criticality=Criticality.LOW),replace(d[1],last_observed_at=1009,criticality=Criticality.LOW,volatility_score=0.0)); want=Decision.HOLD
        elif mode==10: r=replace(r,risk=RiskLevel.HIGH,now=1004,decision_time=1003); d=tuple(replace(x,last_observed_at=1004,criticality=Criticality.LOW,volatility_score=0.0) for x in d); want=Decision.ALLOW
        else: r=replace(r,observed=False); want=Decision.HOLD
        z=evaluate(r,d,p); self.assertEqual(z.decision,want); self.neg(z)
    return f
for k in range(120): setattr(T,f'test_regression_{k:03d}',_gen(k))

if __name__=='__main__': unittest.main(verbosity=2)
