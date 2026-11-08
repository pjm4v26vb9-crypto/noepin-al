import dataclasses, unittest
import noepin_al_097_conflict_mass_aggregator as m

class TestAL097(unittest.TestCase):
    def test_001_default_allow(self):
        r=m.default_evaluation(); self.assertEqual(r.decision,m.Decision.ALLOW); self.assertTrue(r.next_gate_candidate); self.assertLess(r.conflict_mass,r.conflict_threshold)
    def test_002_complete_conflict_hold(self):
        p=m.default_policy(); b=(dataclasses.replace(m.default_beliefs()[0],support_mass=.95,opposition_mass=.0,uncertainty_mass=.05), dataclasses.replace(m.default_beliefs()[1],support_mass=.0,opposition_mass=.95,uncertainty_mass=.05))
        r=m.evaluate(m.default_query(),b,(),p); self.assertEqual(r.decision,m.Decision.HOLD); self.assertEqual(r.decision_hint,m.DecisionHint.HOLD_CONFLICT)
    def test_003_weak_conflict_allow(self):
        p=m.default_policy(); b=(dataclasses.replace(m.default_beliefs()[0],support_mass=.78,opposition_mass=.10,uncertainty_mass=.12),dataclasses.replace(m.default_beliefs()[1],support_mass=.72,opposition_mass=.12,uncertainty_mass=.16)); r=m.evaluate(m.default_query(),b,(),p); self.assertEqual(r.decision,m.Decision.ALLOW)
    def test_004_low_reliability_discount(self):
        p=m.default_policy(); b=(dataclasses.replace(m.default_beliefs()[0],source_reliability=.05),dataclasses.replace(m.default_beliefs()[1],source_reliability=.05)); r=m.evaluate(m.default_query(),b,(),p); self.assertEqual(r.decision,m.Decision.HOLD)
    def test_005_critical_threshold_lower(self):
        p=m.default_policy(); q=dataclasses.replace(m.default_query(),risk=m.RiskLevel.CRITICAL); b=(dataclasses.replace(m.default_beliefs()[0],support_mass=.70,opposition_mass=.20,uncertainty_mass=.10),dataclasses.replace(m.default_beliefs()[1],support_mass=.70,opposition_mass=.20,uncertainty_mass=.10)); r=m.evaluate(q,b,(),p); self.assertEqual(r.decision,m.Decision.HOLD)
    def test_006_opposition_deny_candidate(self):
        p=m.default_policy(); b=tuple(dataclasses.replace(x,support_mass=.05,opposition_mass=.85,uncertainty_mass=.10) for x in m.default_beliefs()); r=m.evaluate(m.default_query(),b,(),p); self.assertEqual(r.decision,m.Decision.DENY); self.assertEqual(r.decision_hint,m.DecisionHint.DENY_CANDIDATE)
    def test_007_both_weak(self):
        p=m.default_policy(); b=tuple(dataclasses.replace(x,support_mass=.10,opposition_mass=.10,uncertainty_mass=.80) for x in m.default_beliefs()); r=m.evaluate(m.default_query(),b,(),p); self.assertEqual(r.decision,m.Decision.HOLD)
    def test_008_explicit_relation_conflict(self):
        p=m.default_policy(); b=(dataclasses.replace(m.default_beliefs()[0],support_mass=.90,opposition_mass=.02,uncertainty_mass=.08),dataclasses.replace(m.default_beliefs()[1],support_mass=.02,opposition_mass=.90,uncertainty_mass=.08)); rel=(m.ConflictRelation('R1','E1','E2',1.0,1.0,True,p.binding,p.state_epoch),); r=m.evaluate(m.default_query(),b,rel,p); self.assertEqual(r.decision,m.Decision.HOLD); self.assertGreater(r.conflict_mass,.5)
    def test_009_invalid_mass(self):
        p=m.default_policy(); b=(dataclasses.replace(m.default_beliefs()[0],support_mass=.9),m.default_beliefs()[1]); self.assertEqual(m.evaluate(m.default_query(),b,(),p).decision,m.Decision.HOLD)
    def test_010_duplicate(self):
        p=m.default_policy(); b=(m.default_beliefs()[0],m.default_beliefs()[0]); self.assertEqual(m.evaluate(m.default_query(),b,(),p).decision,m.Decision.HOLD)
    def test_011_scope(self):
        q=dataclasses.replace(m.default_query(),binding='X'); self.assertEqual(m.evaluate(q,m.default_beliefs(),(),m.default_policy()).decision,m.Decision.HOLD)
    def test_012_revoked(self):
        p=dataclasses.replace(m.default_policy(),revoked=True); self.assertEqual(m.evaluate(m.default_query(),m.default_beliefs(),(),p).decision,m.Decision.HOLD)
    def test_013_prepared(self):
        p=m.default_policy(); st=m.prepare_state(m.default_query(),m.default_beliefs(),(),p,binding=p.binding,state_epoch=p.state_epoch); self.assertTrue(m.validate_prepared_integrity(st)); r=m.evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_calibration_fingerprint=st.calibration_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True); self.assertEqual(r,st.precomputed_result)
    def test_014_prepared_unvalidated(self):
        p=m.default_policy(); st=m.prepare_state(m.default_query(),m.default_beliefs(),(),p,binding=p.binding,state_epoch=p.state_epoch); r=m.evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_calibration_fingerprint=st.calibration_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=False); self.assertEqual(r.decision,m.Decision.HOLD)
    def test_015_delta(self):
        p=m.default_policy(); base=m.prepare_state(m.default_query(),m.default_beliefs(),(),p,binding=p.binding,state_epoch=p.state_epoch); b=list(m.default_beliefs()); b[0]=dataclasses.replace(b[0],source_version='V2',source_fingerprint='SFP-X'); target=m.prepare_state(m.default_query(),tuple(b),(),p,binding=p.binding,state_epoch=p.state_epoch); self.assertEqual(m.apply_delta(base,m.make_delta(base,target)),target)
    def test_016_missing_sync(self):
        p=m.default_policy(); st=m.prepare_state(m.default_query(),m.default_beliefs(),(),p,binding=p.binding,state_epoch=p.state_epoch); plan=m.missing_only_sync_plan(st,{}); self.assertEqual(len(plan.missing_or_changed_record_ids),2)
    def test_017_no_authority_promotion(self):
        r=m.default_evaluation(); self.assertFalse(any((r.cache_promoted_to_truth,r.cache_promoted_to_authority,r.permission_granted,r.action_executed,r.plan_committed,r.atomic_publish_executed,r.external_write_performed,r.world_truth_proven,r.safety_proven,r.action_success)))
    def test_018_threshold_monotonic(self):
        p=m.default_policy(); self.assertGreaterEqual(p.conflict_threshold_low,p.conflict_threshold_medium); self.assertGreaterEqual(p.conflict_threshold_medium,p.conflict_threshold_high); self.assertGreaterEqual(p.conflict_threshold_high,p.conflict_threshold_critical)
    def test_019_independence_discount(self):
        p=m.default_policy(); high=m.evaluate(m.default_query(),m.default_beliefs(),(),p); lowb=tuple(dataclasses.replace(x,independence_score=.2) for x in m.default_beliefs()); low=m.evaluate(m.default_query(),lowb,(),p); self.assertLess(low.effective_evidence_count,high.effective_evidence_count)
    def test_020_relation_scope_invalid(self):
        p=m.default_policy(); r=(m.ConflictRelation('R1','E1','E2',1,1,True,'X',p.state_epoch),); self.assertEqual(m.evaluate(m.default_query(),m.default_beliefs(),r,p).decision,m.Decision.HOLD)

def _make(i):
    def t(self):
        p=m.default_policy(); risk=list(m.RiskLevel)[i%4]
        a=(i%70)/100; o=((i*7)%40)/100; u=max(0.0,1-a-o)
        if a+o>1: o=max(0,1-a); u=0
        b1=dataclasses.replace(m.default_beliefs()[0],support_mass=a,opposition_mass=o,uncertainty_mass=1-a-o,source_reliability=.35+(i%60)/100,independence_score=.4+(i%50)/100,source_version=f'V{i}',source_fingerprint=f'S{i}')
        b2=dataclasses.replace(m.default_beliefs()[1],support_mass=min(.95,max(.0,a-.05)),opposition_mass=min(.95,max(.0,o+.03)),uncertainty_mass=0.0,source_reliability=.4+((i*3)%55)/100,independence_score=.45+((i*5)%50)/100,source_version=f'W{i}',source_fingerprint=f'T{i}')
        rem=1-b2.support_mass-b2.opposition_mass
        if rem<0:
            b2=dataclasses.replace(b2,opposition_mass=max(0,1-b2.support_mass),uncertainty_mass=0.0)
        else: b2=dataclasses.replace(b2,uncertainty_mass=rem)
        q=dataclasses.replace(m.default_query(),risk=risk); r=m.evaluate(q,(b1,b2),(),p)
        self.assertTrue(0<=r.support<=1 and 0<=r.opposition<=1 and 0<=r.conflict_mass<=1); self.assertFalse(r.permission_granted); self.assertFalse(r.action_success)
    return t
for i in range(21,161): setattr(TestAL097,f'test_{i:03d}_generated',_make(i))
if __name__=='__main__': unittest.main(verbosity=2)
