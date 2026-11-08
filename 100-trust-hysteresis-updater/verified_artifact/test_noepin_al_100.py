import dataclasses, unittest
import noepin_al_100_trust_hysteresis_updater as m

class TestAL100(unittest.TestCase):
    def test_001_default(self):
        r=m.default_evaluation(); self.assertEqual(r.decision,m.Decision.ALLOW); self.assertEqual(r.trust_tier,m.TrustTier.STANDARD); self.assertAlmostEqual(r.updated_trust,.74); self.assertEqual(r.success_streak,3); self.assertTrue(r.next_gate_candidate)
    def test_002_critical_failure_fast_drop(self):
        p=m.default_policy(); q=m.default_query(); e=dataclasses.replace(m.default_events()[0],outcome=m.EventOutcome.FAILURE,severity=m.Severity.CRITICAL)
        r=m.evaluate(q,(e,),p); self.assertEqual(r.decision,m.Decision.HOLD); self.assertLessEqual(r.updated_trust,p.critical_trust_cap); self.assertTrue(r.serious_incident_active); self.assertTrue(r.isolation_candidate)
    def test_003_high_failure_cap(self):
        p=m.default_policy(); q=m.default_query(); e=dataclasses.replace(m.default_events()[0],outcome=m.EventOutcome.FAILURE,severity=m.Severity.HIGH)
        r=m.evaluate(q,(e,),p); self.assertLessEqual(r.updated_trust,p.high_trust_cap); self.assertTrue(r.serious_incident_active)
    def test_004_one_success_after_incident_not_restore(self):
        p=m.default_policy(); q=dataclasses.replace(m.default_query(),current_trust=.20,current_tier=m.TrustTier.RESTRICTED,current_success_streak=0,serious_incident_active=True)
        e=m.default_events()[0]; r=m.evaluate(q,(e,),p); self.assertEqual(r.decision,m.Decision.HOLD); self.assertTrue(r.serious_incident_active); self.assertFalse(r.recovery_ready_candidate); self.assertLessEqual(r.trust_tier,m.TrustTier.LIMITED)
    def test_005_consecutive_success_recovery_ready(self):
        p=m.default_policy(); q=dataclasses.replace(m.default_query(),current_trust=.22,current_tier=m.TrustTier.RESTRICTED,current_success_streak=4,serious_incident_active=True)
        r=m.evaluate(q,m.default_events(),p); self.assertTrue(r.recovery_ready_candidate); self.assertTrue(r.serious_incident_active); self.assertEqual(r.decision,m.Decision.HOLD)
    def test_006_verified_recovery_can_clear_incident(self):
        p=m.default_policy(); q=dataclasses.replace(m.default_query(),current_trust=.44,current_tier=m.TrustTier.LIMITED,current_success_streak=4,serious_incident_active=True,recovery_verified=True)
        r=m.evaluate(q,m.default_events(),p); self.assertFalse(r.serious_incident_active); self.assertEqual(r.recovery_requirement,m.RecoveryRequirement.NONE); self.assertEqual(r.decision,m.Decision.ALLOW)
    def test_007_unknown_event_small_change_hold(self):
        p=m.default_policy(); q=m.default_query(); e=dataclasses.replace(m.default_events()[0],outcome=m.EventOutcome.UNKNOWN,evidence_strength=.2)
        r=m.evaluate(q,(e,),p); self.assertEqual(r.decision,m.Decision.HOLD); self.assertLessEqual(abs(r.updated_trust-q.current_trust),p.uncertain_event_change_cap+1e-12)
    def test_008_correction_partial_only(self):
        p=m.default_policy(); q=m.default_query(); e=dataclasses.replace(m.default_events()[0],outcome=m.EventOutcome.CORRECTION,severity=m.Severity.HIGH)
        r=m.evaluate(q,(e,),p); self.assertLessEqual(r.updated_trust-q.current_trust,p.correction_gain_cap+1e-12)
    def test_009_inactivity_does_not_repair_low_trust(self):
        p=m.default_policy(); q=dataclasses.replace(m.default_query(),current_trust=.20,current_tier=m.TrustTier.RESTRICTED,serious_incident_active=True)
        r=m.evaluate(q,(),p); self.assertLessEqual(r.updated_trust,.20); self.assertTrue(r.serious_incident_active)
    def test_010_hysteresis_prevents_high_flap(self):
        p=m.default_policy(); q=dataclasses.replace(m.default_query(),current_trust=.80,current_tier=m.TrustTier.HIGH,current_success_streak=0)
        e=dataclasses.replace(m.default_events()[0],outcome=m.EventOutcome.CORRECTION,evidence_strength=0)
        r=m.evaluate(q,(e,),p); self.assertEqual(r.trust_tier,m.TrustTier.HIGH)
    def test_011_shadow_no_production_authority(self):
        q=dataclasses.replace(m.default_query(),lane=m.DeploymentLane.SHADOW); r=m.evaluate(q,m.default_events(),m.default_policy()); self.assertFalse(r.production_authority_granted); self.assertEqual(r.lane,m.DeploymentLane.SHADOW)
    def test_012_canary_no_production_authority(self):
        q=dataclasses.replace(m.default_query(),lane=m.DeploymentLane.CANARY); r=m.evaluate(q,m.default_events(),m.default_policy()); self.assertFalse(r.production_authority_granted)
    def test_013_revoked(self):
        p=dataclasses.replace(m.default_policy(),revoked=True); self.assertEqual(m.evaluate(m.default_query(),m.default_events(),p).decision,m.Decision.HOLD)
    def test_014_scope_mismatch(self):
        q=dataclasses.replace(m.default_query(),binding='X'); self.assertEqual(m.evaluate(q,m.default_events(),m.default_policy()).decision,m.Decision.HOLD)
    def test_015_duplicate_ids(self):
        p=m.default_policy(); e=m.default_events()[0]; self.assertEqual(m.evaluate(m.default_query(),(e,e),p).decision,m.Decision.HOLD)
    def test_016_prepared_reuse(self):
        p=m.default_policy(); q=m.default_query(); es=m.default_events(); st=m.prepare_state(q,es,p,binding=p.binding,state_epoch=p.state_epoch); ok=m.validate_prepared_integrity(st); r=m.evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=ok); self.assertEqual(r,m.evaluate(q,es,p))
    def test_017_prepared_integrity_required(self):
        p=m.default_policy(); st=m.prepare_state(m.default_query(),m.default_events(),p,binding=p.binding,state_epoch=p.state_epoch); r=m.evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=False); self.assertEqual(r.decision,m.Decision.HOLD)
    def test_018_delta_roundtrip(self):
        p=m.default_policy(); q=m.default_query(); base=m.prepare_state(q,m.default_events(),p,binding=p.binding,state_epoch=p.state_epoch); es=list(m.default_events()); es[0]=dataclasses.replace(es[0],model_version='MODEL-V2',source_fingerprint='CHANGED'); target=m.prepare_state(q,tuple(es),p,binding=p.binding,state_epoch=p.state_epoch); self.assertEqual(m.apply_delta(base,m.make_delta(base,target)),target)
    def test_019_sync_plan(self):
        p=m.default_policy(); st=m.prepare_state(m.default_query(),m.default_events(),p,binding=p.binding,state_epoch=p.state_epoch); sp=m.missing_only_sync_plan(st,{}); self.assertEqual(len(sp.missing_or_changed_event_ids),1); self.assertFalse(sp.full_resend_required)
    def test_020_authority_flags_false(self):
        r=m.default_evaluation(); self.assertFalse(r.trust_applied); self.assertFalse(r.trust_tier_applied); self.assertFalse(r.recovery_executed); self.assertFalse(r.isolation_executed); self.assertFalse(r.permission_granted); self.assertFalse(r.action_executed); self.assertFalse(r.world_truth_proven); self.assertFalse(r.safety_proven); self.assertFalse(r.action_success)
    def test_021_long_inactivity_decays_high_trust(self):
        p=m.default_policy(); q=dataclasses.replace(m.default_query(),current_trust=.95,current_tier=m.TrustTier.HIGH,last_event_time=0.0,reference_time=100.0); r=m.evaluate(q,(),p); self.assertLess(r.updated_trust,.95); self.assertGreaterEqual(r.updated_trust,p.neutral_trust)

def _make(i):
    def t(self):
        p=m.default_policy(); q=m.default_query(); outcome=list(m.EventOutcome)[i%4]; sev=list(m.Severity)[i%5]
        e=dataclasses.replace(m.default_events()[0],event_id=f'G{i}',outcome=outcome,severity=sev,evidence_strength=(i%11)/10,sequence_index=i)
        r=m.evaluate(q,(e,),p)
        self.assertGreaterEqual(r.updated_trust,0); self.assertLessEqual(r.updated_trust,1)
        self.assertFalse(r.trust_applied); self.assertFalse(r.trust_tier_applied); self.assertFalse(r.production_authority_granted); self.assertFalse(r.permission_granted); self.assertFalse(r.action_executed); self.assertFalse(r.world_truth_proven); self.assertFalse(r.safety_proven); self.assertFalse(r.action_success)
    return t
for i in range(22,161): setattr(TestAL100,f'test_{i:03d}_generated',_make(i))
if __name__=='__main__': unittest.main(verbosity=2)
