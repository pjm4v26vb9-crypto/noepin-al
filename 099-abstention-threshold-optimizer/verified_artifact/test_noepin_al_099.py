import dataclasses, unittest
import noepin_al_099_abstention_threshold_optimizer as m

class TestAL099(unittest.TestCase):
    def test_001_default_allow(self):
        r=m.default_evaluation(); self.assertEqual(r.decision,m.Decision.ALLOW); self.assertTrue(r.next_gate_candidate); self.assertGreaterEqual(r.abstention_threshold,m.default_policy().minimum_threshold_low)
    def test_002_boundaries_false(self):
        r=m.default_evaluation(); self.assertFalse(any((r.threshold_applied,r.policy_mutated,r.cache_promoted_to_truth,r.cache_promoted_to_authority,r.permission_granted,r.action_executed,r.plan_committed,r.atomic_publish_executed,r.external_write_performed,r.world_truth_proven,r.safety_proven,r.action_success)))
    def test_003_false_allow_cost_raises_or_equal(self):
        p=m.default_policy(); q=m.default_query(); r1=m.evaluate(dataclasses.replace(q,false_allow_cost=1.0),m.default_records(),p); r2=m.evaluate(dataclasses.replace(q,false_allow_cost=20.0),m.default_records(),p); self.assertGreaterEqual(r2.abstention_threshold,r1.abstention_threshold)
    def test_004_false_hold_cost_lowers_or_equal(self):
        p=m.default_policy(); q=m.default_query(); r1=m.evaluate(dataclasses.replace(q,false_hold_cost=1.0),m.default_records(),p); r2=m.evaluate(dataclasses.replace(q,false_hold_cost=20.0),m.default_records(),p); self.assertLessEqual(r2.abstention_threshold,r1.abstention_threshold)
    def test_005_critical_floor(self):
        p=m.default_policy(); q=dataclasses.replace(m.default_query(),risk=m.RiskLevel.CRITICAL); r=m.evaluate(q,m.default_records(),p); self.assertGreaterEqual(r.abstention_threshold,p.minimum_threshold_critical)
    def test_006_sparse_high_hold(self):
        p=m.default_policy(); q=dataclasses.replace(m.default_query(),risk=m.RiskLevel.HIGH); r=m.evaluate(q,m.default_records()[:8],p); self.assertEqual(r.decision,m.Decision.HOLD); self.assertTrue(r.sparse_data); self.assertGreaterEqual(r.abstention_threshold,p.conservative_threshold_high)
    def test_007_sparse_low_conservative_candidate(self):
        p=m.default_policy(); r=m.evaluate(m.default_query(),m.default_records()[:8],p); self.assertEqual(r.decision,m.Decision.ALLOW); self.assertEqual(r.threshold_source,m.ThresholdSource.CONSERVATIVE); self.assertGreaterEqual(r.abstention_threshold,p.conservative_threshold_low)
    def test_008_degradation_high_hold(self):
        p=m.default_policy(); q=dataclasses.replace(m.default_query(),risk=m.RiskLevel.HIGH); xs=[]
        for i in range(50):
            success=True if i<40 else False
            xs.append(m.CalibrationRecord(f'D{i}','TASK-A',.9,success,i,'V1',f'S{i}',True,p.binding,p.state_epoch))
        r=m.evaluate(q,tuple(xs),p); self.assertTrue(r.degradation_detected); self.assertEqual(r.decision,m.Decision.HOLD); self.assertEqual(r.threshold_source,m.ThresholdSource.DEGRADED_RAISED)
    def test_009_policy_ceiling(self):
        p=dataclasses.replace(m.default_policy(),maximum_threshold=.92,conservative_threshold_critical=.92); q=dataclasses.replace(m.default_query(),risk=m.RiskLevel.CRITICAL); r=m.evaluate(q,m.default_records(),p); self.assertLessEqual(r.abstention_threshold,.92)
    def test_010_revoked(self):
        p=dataclasses.replace(m.default_policy(),revoked=True); self.assertEqual(m.evaluate(m.default_query(),m.default_records(),p).decision,m.Decision.HOLD)
    def test_011_scope_mismatch(self):
        q=dataclasses.replace(m.default_query(),binding='X'); self.assertEqual(m.evaluate(q,m.default_records(),m.default_policy()).decision,m.Decision.HOLD)
    def test_012_duplicate_ids(self):
        p=m.default_policy(); xs=list(m.default_records()); xs[1]=dataclasses.replace(xs[1],record_id=xs[0].record_id); self.assertEqual(m.evaluate(m.default_query(),tuple(xs),p).decision,m.Decision.HOLD)
    def test_013_invalid_confidence(self):
        p=m.default_policy(); xs=list(m.default_records()); xs[0]=dataclasses.replace(xs[0],predicted_confidence=2.0); self.assertEqual(m.evaluate(m.default_query(),tuple(xs),p).decision,m.Decision.HOLD)
    def test_014_prepared_reuse(self):
        p=m.default_policy(); q=m.default_query(); xs=m.default_records(); st=m.prepare_state(q,xs,p,binding=p.binding,state_epoch=p.state_epoch); ok=m.validate_prepared_integrity(st); r=m.evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_constraint_fingerprint=st.constraint_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=ok); self.assertEqual(r,m.evaluate(q,xs,p))
    def test_015_prepared_integrity_required(self):
        p=m.default_policy(); st=m.prepare_state(m.default_query(),m.default_records(),p,binding=p.binding,state_epoch=p.state_epoch); r=m.evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_constraint_fingerprint=st.constraint_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=False); self.assertEqual(r.decision,m.Decision.HOLD)
    def test_016_prepared_constraint_mismatch(self):
        p=m.default_policy(); st=m.prepare_state(m.default_query(),m.default_records(),p,binding=p.binding,state_epoch=p.state_epoch); r=m.evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_constraint_fingerprint='X',current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True); self.assertEqual(r.decision,m.Decision.HOLD)
    def test_017_delta_roundtrip(self):
        p=m.default_policy(); q=m.default_query(); base=m.prepare_state(q,m.default_records(),p,binding=p.binding,state_epoch=p.state_epoch); xs=list(m.default_records()); xs[0]=dataclasses.replace(xs[0],predicted_confidence=.77,source_version='V2'); target=m.prepare_state(q,tuple(xs),p,binding=p.binding,state_epoch=p.state_epoch); self.assertEqual(m.apply_delta(base,m.make_delta(base,target)),target)
    def test_018_sync_plan(self):
        p=m.default_policy(); st=m.prepare_state(m.default_query(),m.default_records(),p,binding=p.binding,state_epoch=p.state_epoch); known=dict(st.record_fingerprints); known.pop(next(iter(known))); sp=m.missing_only_sync_plan(st,known); self.assertEqual(len(sp.missing_or_changed_record_ids),1); self.assertFalse(sp.full_resend_required)
    def test_019_class_thresholds(self):
        r=m.default_evaluation(); d=dict(r.class_specific_thresholds); self.assertIn('TASK-A',d); self.assertIn('TASK-B',d)
    def test_020_expected_loss_nonnegative(self):
        r=m.default_evaluation(); self.assertGreaterEqual(r.expected_loss,0); self.assertGreaterEqual(r.false_allow_count,0); self.assertGreaterEqual(r.false_hold_count,0)

def _make(i):
    def t(self):
        p=m.default_policy(); risk=list(m.RiskLevel)[i%4]
        q=dataclasses.replace(m.default_query(),risk=risk,false_allow_cost=1.0+(i%13),false_hold_cost=1.0+((i*3)%11))
        r=m.evaluate(q,m.default_records(),p)
        self.assertGreaterEqual(r.abstention_threshold,m._floor(risk,p)); self.assertLessEqual(r.abstention_threshold,p.maximum_threshold)
        self.assertGreaterEqual(r.expected_loss,0); self.assertFalse(r.threshold_applied); self.assertFalse(r.policy_mutated); self.assertFalse(r.permission_granted); self.assertFalse(r.action_executed); self.assertFalse(r.world_truth_proven); self.assertFalse(r.safety_proven); self.assertFalse(r.action_success)
    return t
for i in range(21,161): setattr(TestAL099,f'test_{i:03d}_generated',_make(i))
if __name__=='__main__': unittest.main(verbosity=2)
