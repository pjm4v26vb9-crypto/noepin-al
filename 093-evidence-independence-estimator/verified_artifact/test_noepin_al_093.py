import unittest
from dataclasses import replace
from noepin_al_093_evidence_independence_estimator import *

class T(unittest.TestCase):
    def base(self): return default_request(),default_evidence(),default_edges(),default_policy()
    def neg(self,z):
        self.assertFalse(z.permission_granted); self.assertFalse(z.action_executed); self.assertFalse(z.plan_committed); self.assertFalse(z.atomic_publish_executed); self.assertFalse(z.external_write_performed); self.assertFalse(z.world_truth_proven); self.assertFalse(z.authority_promoted); self.assertFalse(z.safety_proven); self.assertFalse(z.action_success)
    def test_001_default_allow(self): self.assertEqual(default_evaluation().decision,Decision.ALLOW)
    def test_002_default_effective_four(self): self.assertAlmostEqual(default_evaluation().effective_evidence_count,4.0,places=12)
    def test_003_default_clusters(self): self.assertEqual(default_evaluation().clusters,(('E-A',),('E-B',),('E-C',),('E-D',)))
    def test_004_authority_negative(self): self.neg(default_evaluation())
    def test_005_same_source_dependent(self): r,e,g,p=self.base(); e=tuple(replace(x,source_id='SAME') for x in e); z=evaluate(r,e,g,p); self.assertEqual(z.decision,Decision.HOLD); self.assertLess(z.effective_evidence_count,1.2)
    def test_006_same_model_discount(self): r,e,g,p=self.base(); z1=evaluate(r,e,g,p); z2=evaluate(r,tuple(replace(x,model_id='M') for x in e),g,p); self.assertLess(z2.effective_evidence_count,z1.effective_evidence_count)
    def test_007_same_url_discount(self): r,e,g,p=self.base(); z=evaluate(r,tuple(replace(x,url_id='U') for x in e),g,p); self.assertLess(z.effective_evidence_count,2)
    def test_008_same_document_discount(self): r,e,g,p=self.base(); z=evaluate(r,tuple(replace(x,document_id='D') for x in e),g,p); self.assertLess(z.effective_evidence_count,2)
    def test_009_same_content_strong(self): r,e,g,p=self.base(); z=evaluate(r,tuple(replace(x,content_fingerprint='C') for x in e),g,p); self.assertGreater(z.strong_dependence_pairs,0)
    def test_010_direct_citation(self): r,e,g,p=self.base(); e=(e[0],replace(e[1],parent_evidence_ids=('E-A',)),e[2],e[3]); z=evaluate(r,e,g,p); pair=[x for x in z.independence_matrix if x[:2]==('E-A','E-B')][0]; self.assertLess(pair[2],.3)
    def test_011_edge_citation(self): r,e,g,p=self.base(); g=(LineageEdge('E-A','E-B',Relation.CITES,True,p.binding,p.state_epoch),); z=evaluate(r,e,g,p); pair=[x for x in z.independence_matrix if x[:2]==('E-A','E-B')][0]; self.assertLess(pair[2],.3)
    def test_012_citation_chain(self): r,e,g,p=self.base(); g=(LineageEdge('E-A','E-B',Relation.CITES,True,p.binding,p.state_epoch),LineageEdge('E-B','E-C',Relation.CITES,True,p.binding,p.state_epoch)); z=evaluate(r,e,g,p); pair=[x for x in z.independence_matrix if x[:2]==('E-A','E-C')][0]; self.assertLess(pair[2],.3)
    def test_013_shared_ancestor(self): r,e,g,p=self.base(); g=(LineageEdge('E-A','E-B',Relation.CITES,True,p.binding,p.state_epoch),LineageEdge('E-A','E-C',Relation.CITES,True,p.binding,p.state_epoch)); z=evaluate(r,e,g,p); pair=[x for x in z.independence_matrix if x[:2]==('E-B','E-C')][0]; self.assertLess(pair[2],.4)
    def test_014_unknown_lineage_not_full_independent(self): r,e,g,p=self.base(); e=(replace(e[0],lineage_known=False),)+e[1:]; z=evaluate(r,e,g,p); self.assertGreater(z.unknown_lineage_count,0); self.assertLess(z.mean_independence,1)
    def test_015_unknown_high_risk_hold(self): r,e,g,p=self.base(); r=replace(r,risk=RiskLevel.HIGH); e=(replace(e[0],lineage_known=False),)+e[1:]; self.assertEqual(evaluate(r,e,g,p).decision,Decision.HOLD)
    def test_016_one_evidence_insufficient(self): r,e,g,p=self.base(); self.assertEqual(evaluate(r,e[:1],g,p).decision,Decision.HOLD)
    def test_017_two_independent_low_allow(self): r,e,g,p=self.base(); self.assertEqual(evaluate(r,e[:2],g,p).decision,Decision.ALLOW)
    def test_018_critical_four_allow(self): r,e,g,p=self.base(); r=replace(r,risk=RiskLevel.CRITICAL); self.assertEqual(evaluate(r,e,g,p).decision,Decision.ALLOW)
    def test_019_policy_revoked(self): r,e,g,p=self.base(); self.assertEqual(evaluate(r,e,g,replace(p,revoked=True)).decision,Decision.HOLD)
    def test_020_request_unobserved(self): r,e,g,p=self.base(); self.assertEqual(evaluate(replace(r,observed=False),e,g,p).decision,Decision.HOLD)
    def test_021_binding_mismatch(self): r,e,g,p=self.base(); self.assertEqual(evaluate(replace(r,binding='X'),e,g,p).decision,Decision.HOLD)
    def test_022_duplicate_evidence(self): r,e,g,p=self.base(); self.assertEqual(evaluate(r,e+(e[0],),g,p).decision,Decision.HOLD)
    def test_023_evidence_unobserved(self): r,e,g,p=self.base(); e=(replace(e[0],observed=False),)+e[1:]; self.assertEqual(evaluate(r,e,g,p).decision,Decision.HOLD)
    def test_024_parent_missing(self): r,e,g,p=self.base(); e=(replace(e[0],parent_evidence_ids=('NOPE',)),)+e[1:]; self.assertEqual(evaluate(r,e,g,p).decision,Decision.HOLD)
    def test_025_edge_missing_endpoint(self): r,e,g,p=self.base(); g=(LineageEdge('NOPE','E-B',Relation.CITES,True,p.binding,p.state_epoch),); self.assertEqual(evaluate(r,e,g,p).decision,Decision.HOLD)
    def test_026_edge_unobserved(self): r,e,g,p=self.base(); g=(LineageEdge('E-A','E-B',Relation.CITES,False,p.binding,p.state_epoch),); self.assertEqual(evaluate(r,e,g,p).decision,Decision.HOLD)
    def test_027_matrix_size(self): self.assertEqual(len(default_evaluation().independence_matrix),6)
    def test_028_mean_bounds(self): z=default_evaluation(); self.assertTrue(0<=z.mean_independence<=1); self.assertTrue(0<=z.mean_dependence<=1)
    def test_029_prepared_valid(self): r,e,g,p=self.base(); st=prepare_state(r,e,g,p,binding=p.binding,state_epoch=p.state_epoch); self.assertTrue(validate_prepared_integrity(st)); self.assertEqual(evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_calibration_fingerprint=st.calibration_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True),default_evaluation())
    def test_030_prepared_context_changed(self): r,e,g,p=self.base(); st=prepare_state(r,e,g,p,binding=p.binding,state_epoch=p.state_epoch); self.assertEqual(evaluate_prepared(st,current_context_fingerprint='BAD',current_dependency_fingerprint=st.dependency_fingerprint,current_calibration_fingerprint=st.calibration_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True).decision,Decision.HOLD)
    def test_031_prepared_unvalidated(self): r,e,g,p=self.base(); st=prepare_state(r,e,g,p,binding=p.binding,state_epoch=p.state_epoch); self.assertEqual(evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_calibration_fingerprint=st.calibration_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=False).decision,Decision.HOLD)
    def test_032_delta_roundtrip(self): r,e,g,p=self.base(); a=prepare_state(r,e,g,p,binding=p.binding,state_epoch=p.state_epoch); e2=(replace(e[0],source_id='NEW'),)+e[1:]; b=prepare_state(r,e2,g,p,binding=p.binding,state_epoch=p.state_epoch); self.assertEqual(apply_delta(a,make_delta(a,b)),b)
    def test_033_missing_only(self): r,e,g,p=self.base(); st=prepare_state(r,e,g,p,binding=p.binding,state_epoch=p.state_epoch); known=dict(st.record_fingerprints); known.pop('EVID:E-A'); plan=missing_only_sync_plan(st,known); self.assertEqual(plan.missing_or_changed_record_ids,('EVID:E-A',)); self.assertFalse(plan.full_resend_required)
    def test_034_deterministic(self): r,e,g,p=self.base(); self.assertEqual(evaluate(r,e,g,p),evaluate(r,tuple(reversed(e)),tuple(reversed(g)),p))
    def test_035_evidence_fingerprint_changes_registry(self): r,e,g,p=self.base(); a=prepare_state(r,e,g,p,binding=p.binding,state_epoch=p.state_epoch); b=prepare_state(r,(replace(e[0],evidence_fingerprint='NEW'),)+e[1:],g,p,binding=p.binding,state_epoch=p.state_epoch); self.assertNotEqual(a.registry_fingerprint,b.registry_fingerprint)
    def test_036_lineage_changes_registry(self): r,e,g,p=self.base(); a=prepare_state(r,e,g,p,binding=p.binding,state_epoch=p.state_epoch); g2=(LineageEdge('E-A','E-B',Relation.CITES,True,p.binding,p.state_epoch),); b=prepare_state(r,e,g2,p,binding=p.binding,state_epoch=p.state_epoch); self.assertNotEqual(a.registry_fingerprint,b.registry_fingerprint)
    def test_037_calibration_changes_fingerprint(self): r,e,g,p=self.base(); a=prepare_state(r,e,g,p,binding=p.binding,state_epoch=p.state_epoch); b=prepare_state(r,e,g,replace(p,same_model_dependence=.7),binding=p.binding,state_epoch=p.state_epoch); self.assertNotEqual(a.calibration_fingerprint,b.calibration_fingerprint)
    def test_038_cache_not_truth(self): z=default_evaluation(); self.assertFalse(z.world_truth_proven); self.assertFalse(z.authority_promoted)
    def test_039_unknown_low_conservative(self): r,e,g,p=self.base(); z1=evaluate(r,e,g,p); z2=evaluate(r,tuple(replace(x,lineage_known=False) for x in e),g,p); self.assertLess(z2.effective_evidence_count,z1.effective_evidence_count)
    def test_040_clusters_merge_strong(self): r,e,g,p=self.base(); e=(e[0],replace(e[1],source_id=e[0].source_id),e[2],e[3]); z=evaluate(r,e,g,p); self.assertTrue(any(set(c)=={'E-A','E-B'} for c in z.clusters))

def _gen(k):
    def f(self):
        r,e,g,p=self.base(); mode=k%12
        if mode==0: want=Decision.ALLOW
        elif mode==1: e=tuple(replace(x,source_id='SAME') for x in e); want=Decision.HOLD
        elif mode==2: e=tuple(replace(x,model_id='SAME') for x in e); want=Decision.HOLD
        elif mode==3: e=(replace(e[0],lineage_known=False),)+e[1:]; r=replace(r,risk=RiskLevel.HIGH); want=Decision.HOLD
        elif mode==4: p=replace(p,revoked=True); want=Decision.HOLD
        elif mode==5: e=(replace(e[0],observed=False),)+e[1:]; want=Decision.HOLD
        elif mode==6: r=replace(r,observed=False); want=Decision.HOLD
        elif mode==7: e=e[:1]; want=Decision.HOLD
        elif mode==8: e=e[:2]; want=Decision.ALLOW
        elif mode==9: r=replace(r,risk=RiskLevel.CRITICAL); want=Decision.ALLOW
        elif mode==10: g=(LineageEdge('E-A','E-B',Relation.CITES,True,p.binding,p.state_epoch),LineageEdge('E-A','E-C',Relation.CITES,True,p.binding,p.state_epoch),LineageEdge('E-A','E-D',Relation.CITES,True,p.binding,p.state_epoch)); want=Decision.HOLD
        else: e=tuple(replace(x,url_id='U') for x in e); want=Decision.HOLD
        z=evaluate(r,e,g,p); self.assertEqual(z.decision,want); self.neg(z)
    return f
for k in range(120): setattr(T,f'test_regression_{k:03d}',_gen(k))
if __name__=='__main__': unittest.main(verbosity=2)
