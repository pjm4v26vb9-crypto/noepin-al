import unittest, dataclasses
import noepin_al_095_confidence_to_authority_mapper as m

class TestAL095(unittest.TestCase):
    def test_001_default(self):
        r=m.default_evaluation(); self.assertEqual(r.decision,m.Decision.ALLOW); self.assertEqual(r.authority_tier_candidate,m.AuthorityTier.AUTONOMOUS); self.assertTrue(r.next_gate_candidate); self.assertFalse(r.authority_granted)
    def test_002_critical_human(self):
        q=dataclasses.replace(m.default_request(),action_risk=m.RiskLevel.CRITICAL,adjusted_confidence=1.0); r=m.evaluate(q,m.default_capabilities(),m.default_policy()); self.assertEqual(r.decision,m.Decision.HUMAN_APPROVAL); self.assertLessEqual(r.authority_tier_candidate,m.AuthorityTier.READ_ONLY)
    def test_003_high_human(self):
        q=dataclasses.replace(m.default_request(),action_risk=m.RiskLevel.HIGH); r=m.evaluate(q,m.default_capabilities(),m.default_policy()); self.assertEqual(r.decision,m.Decision.HUMAN_APPROVAL); self.assertEqual(r.authority_tier_candidate,m.AuthorityTier.ASSISTED)
    def test_004_low_conf_hold(self):
        q=dataclasses.replace(m.default_request(),adjusted_confidence=.40); r=m.evaluate(q,m.default_capabilities(),m.default_policy()); self.assertEqual(r.decision,m.Decision.HOLD); self.assertEqual(r.authority_tier_candidate,m.AuthorityTier.READ_ONLY)
    def test_005_too_low(self):
        q=dataclasses.replace(m.default_request(),adjusted_confidence=.1); r=m.evaluate(q,m.default_capabilities(),m.default_policy()); self.assertEqual(r.authority_tier_candidate,m.AuthorityTier.NONE)
    def test_006_policy_cap(self):
        p=dataclasses.replace(m.default_policy(),global_max=m.AuthorityTier.LIMITED_WRITE); r=m.evaluate(m.default_request(),m.default_capabilities(),p); self.assertEqual(r.authority_tier_candidate,m.AuthorityTier.LIMITED_WRITE)
    def test_007_uncalibrated(self):
        q=dataclasses.replace(m.default_request(),confidence_calibrated=False); self.assertEqual(m.evaluate(q,m.default_capabilities(),m.default_policy()).decision,m.Decision.HOLD)
    def test_008_duplicate_cap(self):
        c=m.default_capabilities()[0]; self.assertEqual(m.evaluate(m.default_request(),(c,c),m.default_policy()).decision,m.Decision.HOLD)
    def test_009_monotonic_confidence(self):
        p=m.default_policy(); caps=m.default_capabilities(); tiers=[]
        for x in (.35,.55,.70,.88,.99): tiers.append(m.evaluate(dataclasses.replace(m.default_request(),adjusted_confidence=x),caps,p).authority_tier_candidate)
        self.assertEqual(tiers,sorted(tiers))
    def test_010_risk_never_increases_tier(self):
        p=m.default_policy(); caps=m.default_capabilities(); tiers=[m.evaluate(dataclasses.replace(m.default_request(),action_risk=r),caps,p).authority_tier_candidate for r in m.RiskLevel]; self.assertEqual(tiers,sorted(tiers,reverse=True))
    def test_011_prepared(self):
        p=m.default_policy(); st=m.prepare_state(m.default_request(),m.default_capabilities(),p,binding=p.binding,state_epoch=p.state_epoch); self.assertTrue(m.validate_prepared_integrity(st)); r=m.evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_constraint_fingerprint=st.constraint_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True); self.assertEqual(r,st.precomputed_result)
    def test_012_prepared_unvalidated(self):
        p=m.default_policy(); st=m.prepare_state(m.default_request(),m.default_capabilities(),p,binding=p.binding,state_epoch=p.state_epoch); r=m.evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_constraint_fingerprint=st.constraint_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=False); self.assertEqual(r.decision,m.Decision.HOLD)
    def test_013_delta(self):
        p=m.default_policy(); base=m.prepare_state(m.default_request(),m.default_capabilities(),p,binding=p.binding,state_epoch=p.state_epoch); caps=list(m.default_capabilities()); caps[0]=dataclasses.replace(caps[0],maximum_risk=m.RiskLevel.HIGH); target=m.prepare_state(m.default_request(),tuple(caps),p,binding=p.binding,state_epoch=p.state_epoch); d=m.make_delta(base,target); self.assertEqual(m.apply_delta(base,d),target)
    def test_014_missing_sync(self):
        p=m.default_policy(); st=m.prepare_state(m.default_request(),m.default_capabilities(),p,binding=p.binding,state_epoch=p.state_epoch); known=dict(st.record_fingerprints[:-1]); s=m.missing_only_sync_plan(st,known); self.assertEqual(len(s.missing_or_changed_record_ids),1)
    def test_015_no_actual_authority(self):
        r=m.default_evaluation(); self.assertFalse(any((r.authority_granted,r.permission_granted,r.approval_executed,r.capability_mutated,r.action_executed,r.plan_committed,r.atomic_publish_executed,r.external_write_performed,r.world_truth_proven,r.safety_proven,r.action_success)))
    def test_016_scope_mismatch(self):
        q=dataclasses.replace(m.default_request(),binding='X'); self.assertEqual(m.evaluate(q,m.default_capabilities(),m.default_policy()).decision,m.Decision.HOLD)
    def test_017_revoked(self):
        p=dataclasses.replace(m.default_policy(),revoked=True); self.assertEqual(m.evaluate(m.default_request(),m.default_capabilities(),p).decision,m.Decision.HOLD)
    def test_018_threshold_order(self):
        p=dataclasses.replace(m.default_policy(),readonly_threshold=.8,assisted_threshold=.5); self.assertEqual(m.evaluate(m.default_request(),m.default_capabilities(),p).decision,m.Decision.HOLD)
    def test_019_capability_filter(self):
        q=dataclasses.replace(m.default_request(),action_risk=m.RiskLevel.MEDIUM); r=m.evaluate(q,m.default_capabilities(),m.default_policy()); self.assertNotIn('AUTOMATE_LOW_RISK',r.allowed_capability_candidates)
    def test_020_dcsr_aux_only(self):
        r=m.default_evaluation(); self.assertIn(r.decision,(m.Decision.ALLOW,m.Decision.HOLD,m.Decision.HUMAN_APPROVAL)); self.assertFalse(r.permission_granted)

def _make(idx):
    def t(self):
        p=m.default_policy(); caps=m.default_capabilities(); conf=((idx*37)%101)/100
        q=dataclasses.replace(m.default_request(),adjusted_confidence=conf,action_risk=list(m.RiskLevel)[idx%4])
        r=m.evaluate(q,caps,p)
        self.assertGreaterEqual(r.authority_tier_candidate,m.AuthorityTier.NONE)
        self.assertLessEqual(r.authority_tier_candidate,p.global_max)
        self.assertFalse(r.permission_granted); self.assertFalse(r.action_executed); self.assertFalse(r.action_success)
    return t
for i in range(21,161): setattr(TestAL095,f'test_{i:03d}_generated',_make(i))
if __name__=='__main__': unittest.main(verbosity=2)
