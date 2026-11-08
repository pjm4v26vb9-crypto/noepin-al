import dataclasses, math, unittest
import noepin_al_096_source_freshness_decay as m

class TestAL096(unittest.TestCase):
    def test_001_default(self):
        r=m.default_evaluation(); self.assertEqual(r.decision,m.Decision.ALLOW); self.assertFalse(r.expired); self.assertTrue(r.next_gate_candidate)
    def test_002_expired_critical(self):
        q=dataclasses.replace(m.default_query(),now=1200.0,risk=m.RiskLevel.CRITICAL); r=m.evaluate(q,m.default_sources(),m.default_policy()); self.assertEqual(r.decision,m.Decision.HOLD); self.assertTrue(r.expired); self.assertEqual(r.refresh_priority,m.RefreshPriority.IMMEDIATE)
    def test_003_unknown_timestamp_high_volatility(self):
        s=dataclasses.replace(m.default_sources()[0],source_timestamp=None,volatility=m.Volatility.HIGH); r=m.evaluate(m.default_query(),(s,),m.default_policy()); self.assertEqual(r.decision,m.Decision.HOLD)
    def test_004_updated_verified_reset(self):
        s=dataclasses.replace(m.default_sources()[0],source_timestamp=None,volatility=m.Volatility.HIGH,updated_verified=True); r=m.evaluate(m.default_query(),(s,),m.default_policy()); self.assertEqual(r.freshness_score,1.0); self.assertEqual(r.decision,m.Decision.ALLOW)
    def test_005_high_volatility_decays_faster(self):
        p=m.default_policy(); q=dataclasses.replace(m.default_query(),now=1010.0); a=dataclasses.replace(m.default_sources()[0],volatility=m.Volatility.LOW); b=dataclasses.replace(a,volatility=m.Volatility.HIGH); self.assertGreater(m.evaluate(q,(a,),p).freshness_score,m.evaluate(q,(b,),p).freshness_score)
    def test_006_low_volatility_decays_slower(self):
        p=m.default_policy(); q=dataclasses.replace(m.default_query(),now=1015.0); s=dataclasses.replace(m.default_sources()[0],source_type=m.SourceType.STATIC_DOCUMENT,volatility=m.Volatility.LOW); self.assertGreater(m.evaluate(q,(s,),p).freshness_score,.99)
    def test_007_future_timestamp(self):
        s=dataclasses.replace(m.default_sources()[0],source_timestamp=1100.0); r=m.evaluate(m.default_query(),(s,),m.default_policy()); self.assertEqual(r.decision,m.Decision.HOLD); self.assertIn('FUTURE',r.reasons[0])
    def test_008_low_risk_stale_warn(self):
        q=dataclasses.replace(m.default_query(),now=1100.0,risk=m.RiskLevel.LOW); r=m.evaluate(q,m.default_sources(),m.default_policy()); self.assertEqual(r.decision,m.Decision.ALLOW); self.assertTrue(r.expired); self.assertTrue(r.refresh_candidate)
    def test_009_medium_stale_hold(self):
        q=dataclasses.replace(m.default_query(),now=1100.0,risk=m.RiskLevel.MEDIUM); r=m.evaluate(q,m.default_sources(),m.default_policy()); self.assertEqual(r.decision,m.Decision.HOLD)
    def test_010_missing_source(self):
        r=m.evaluate(m.default_query(),(),m.default_policy()); self.assertEqual(r.decision,m.Decision.HOLD)
    def test_011_scope_mismatch(self):
        q=dataclasses.replace(m.default_query(),binding='X'); self.assertEqual(m.evaluate(q,m.default_sources(),m.default_policy()).decision,m.Decision.HOLD)
    def test_012_revoked(self):
        p=dataclasses.replace(m.default_policy(),revoked=True); self.assertEqual(m.evaluate(m.default_query(),m.default_sources(),p).decision,m.Decision.HOLD)
    def test_013_prepared(self):
        p=m.default_policy(); st=m.prepare_state(m.default_query(),m.default_sources(),p,binding=p.binding,state_epoch=p.state_epoch); self.assertTrue(m.validate_prepared_integrity(st)); r=m.evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_calibration_fingerprint=st.calibration_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True); self.assertEqual(r,st.precomputed_result)
    def test_014_prepared_unvalidated(self):
        p=m.default_policy(); st=m.prepare_state(m.default_query(),m.default_sources(),p,binding=p.binding,state_epoch=p.state_epoch); r=m.evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_calibration_fingerprint=st.calibration_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=False); self.assertEqual(r.decision,m.Decision.HOLD)
    def test_015_delta(self):
        p=m.default_policy(); base=m.prepare_state(m.default_query(),m.default_sources(),p,binding=p.binding,state_epoch=p.state_epoch); s=dataclasses.replace(m.default_sources()[0],source_version='API-V2',source_fingerprint='SOURCE-FP-2'); target=m.prepare_state(m.default_query(),(s,),p,binding=p.binding,state_epoch=p.state_epoch); self.assertEqual(m.apply_delta(base,m.make_delta(base,target)),target)
    def test_016_missing_sync(self):
        p=m.default_policy(); st=m.prepare_state(m.default_query(),m.default_sources(),p,binding=p.binding,state_epoch=p.state_epoch); plan=m.missing_only_sync_plan(st,{}); self.assertEqual(plan.missing_or_changed_record_ids,('SRC:SRC-1',))
    def test_017_no_authority_promotion(self):
        r=m.default_evaluation(); self.assertFalse(any((r.cache_promoted_to_truth,r.cache_promoted_to_authority,r.permission_granted,r.refresh_executed,r.action_executed,r.plan_committed,r.atomic_publish_executed,r.external_write_performed,r.world_truth_proven,r.safety_proven,r.action_success)))
    def test_018_unknown_low_volatility_conservative(self):
        s=dataclasses.replace(m.default_sources()[0],source_timestamp=None,volatility=m.Volatility.LOW); r=m.evaluate(m.default_query(),(s,),m.default_policy()); self.assertLessEqual(r.freshness_score,.55)
    def test_019_risk_threshold_monotonic(self):
        p=m.default_policy(); self.assertLessEqual(p.threshold_low,p.threshold_medium); self.assertLessEqual(p.threshold_medium,p.threshold_high); self.assertLessEqual(p.threshold_high,p.threshold_critical)
    def test_020_decay_monotonic_age(self):
        p=m.default_policy(); s=m.default_sources(); vals=[m.evaluate(dataclasses.replace(m.default_query(),now=1000+t),s,p).freshness_score for t in (0,5,10,20)]; self.assertEqual(vals,sorted(vals,reverse=True))

def _make(i):
    def t(self):
        p=m.default_policy(); vol=list(m.Volatility)[i%4]; st=list(m.SourceType)[i%5]; risk=list(m.RiskLevel)[i%4]
        ts=None if i%17==0 else 1000.0-(i%7)
        s=dataclasses.replace(m.default_sources()[0],source_type=st,volatility=vol,source_timestamp=ts,updated_verified=(i%29==0),source_version=f'V{i}',source_fingerprint=f'S{i}',claim_fingerprint=f'C{i}')
        q=dataclasses.replace(m.default_query(),now=1000.0+(i%200),risk=risk)
        r=m.evaluate(q,(s,),p)
        self.assertTrue(0.0<=r.freshness_score<=1.0); self.assertFalse(r.permission_granted); self.assertFalse(r.action_executed); self.assertFalse(r.action_success)
    return t
for i in range(21,161): setattr(TestAL096,f'test_{i:03d}_generated',_make(i))
if __name__=='__main__': unittest.main(verbosity=2)
