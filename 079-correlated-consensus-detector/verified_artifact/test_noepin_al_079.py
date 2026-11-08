import unittest
from dataclasses import replace
from noepin_al_079_correlated_consensus_detector import *

def base(): return default_policy(),default_outputs(),default_request()
def neg(t,z):
    for k in ('permission_granted','consensus_executed','sender_authority_inherited','sender_intent_inherited','sender_consent_inherited','authentication_proven','world_truth_proven','external_write_performed','action_executed','safety_proven','action_success'):
        t.assertFalse(getattr(z,k),k)
class T(unittest.TestCase):
    def test_001_independent_allow(self): p,o,q=base(); z=evaluate(q,p,o); self.assertEqual(z.decision,Decision.ALLOW); self.assertAlmostEqual(z.adjusted_consensus,2/3,places=6); neg(self,z)
    def test_002_same_source_discount(self):
        p,o,q=base(); a=o[0]; b=replace(o[1],model_id=a.model_id,prompt_family=a.prompt_family,source_ids=a.source_ids,evidence_ids=a.evidence_ids); z=evaluate(q,p,(a,b,o[2])); self.assertEqual(z.decision,Decision.HOLD); self.assertLess(z.independence_score,1)
    def test_003_same_model_partial_discount(self):
        p,o,q=base(); b=replace(o[1],model_id=o[0].model_id); z=evaluate(q,p,(o[0],b,o[2])); self.assertLess(z.independence_score,1); self.assertIn(z.decision,(Decision.ALLOW,Decision.HOLD))
    def test_004_mixed_cluster(self):
        p,o,q=base(); b=replace(o[1],source_ids=o[0].source_ids,evidence_ids=('EVID-B',)); z=evaluate(q,p,(o[0],b,o[2])); self.assertGreaterEqual(len(z.clusters),2)
    def test_005_lineage_missing_hold(self):
        p,o,q=base(); a=replace(o[0],lineage_observed=False); z=evaluate(q,p,(a,o[1],o[2])); self.assertEqual(z.decision,Decision.HOLD); self.assertIn('OUT-A',z.lineage_unknown_ids)
    def test_006_empty_source_and_evidence_hold(self):
        p,o,q=base(); a=replace(o[0],source_ids=(),evidence_ids=()); self.assertEqual(evaluate(q,p,(a,o[1],o[2])).decision,Decision.HOLD)
    def test_007_unknown_output_hold(self): p,o,q=base(); q=replace(q,output_ids=('OUT-A','NOPE')); self.assertEqual(evaluate(q,p,o).decision,Decision.HOLD)
    def test_008_duplicate_request_hold(self): p,o,q=base(); q=replace(q,output_ids=('OUT-A','OUT-A')); self.assertEqual(evaluate(q,p,o).decision,Decision.HOLD)
    def test_009_duplicate_agent_hold(self): p,o,q=base(); oo=(o[0],replace(o[1],agent_id=o[0].agent_id),o[2]); self.assertEqual(evaluate(q,p,oo).decision,Decision.HOLD)
    def test_010_binding_hold(self): p,o,q=base(); self.assertEqual(evaluate(replace(q,binding='BAD'),p,o).decision,Decision.HOLD)
    def test_011_epoch_hold(self): p,o,q=base(); self.assertEqual(evaluate(replace(q,state_epoch='BAD'),p,o).decision,Decision.HOLD)
    def test_012_output_binding_hold(self): p,o,q=base(); oo=(replace(o[0],binding='BAD'),o[1],o[2]); self.assertEqual(evaluate(q,p,oo).decision,Decision.HOLD)
    def test_013_invalid_weight_hold(self): p,o,q=base(); oo=(replace(o[0],weight=2.0),o[1],o[2]); self.assertEqual(evaluate(q,p,oo).decision,Decision.HOLD)
    def test_014_revoked_hold(self): p,o,q=base(); self.assertEqual(evaluate(q,replace(p,revoked=True),o).decision,Decision.HOLD)
    def test_015_invalid_policy_hold(self): p,o,q=base(); self.assertEqual(evaluate(q,replace(p,threshold=.4),o).decision,Decision.HOLD)
    def test_016_opposition_deny(self):
        p,o,q=base(); oo=(replace(o[0],conclusion='NO'),replace(o[1],conclusion='NO'),o[2]); z=evaluate(q,p,oo); self.assertEqual(z.decision,Decision.DENY)
    def test_017_inconclusive_hold(self):
        p,o,q=base(); p=replace(p,threshold=.75); self.assertEqual(evaluate(q,p,o).decision,Decision.HOLD)
    def test_018_insufficient_effective_hold(self):
        p,o,q=base(); p=replace(p,min_effective_votes=4); self.assertEqual(evaluate(q,p,o).decision,Decision.HOLD)
    def test_019_complete_same_origin_one_vote(self):
        p,o,q=base(); a=o[0]; oo=tuple(replace(x,conclusion='YES',model_id=a.model_id,prompt_family=a.prompt_family,source_ids=a.source_ids,evidence_ids=a.evidence_ids) for x in o); z=evaluate(q,p,oo); self.assertEqual(z.decision,Decision.HOLD); self.assertLessEqual(z.effective_total,1.01)
    def test_020_partial_share_reduces(self):
        p,o,q=base(); b=replace(o[1],source_ids=o[0].source_ids); z=evaluate(q,p,(o[0],b,o[2])); self.assertLess(z.independence_score,1)
    def test_021_edges_reasons(self):
        p,o,q=base(); b=replace(o[1],model_id=o[0].model_id,prompt_family=o[0].prompt_family); z=evaluate(q,p,(o[0],b,o[2])); self.assertTrue(any('SAME_MODEL' in e.reasons for e in z.edges))
    def test_022_cluster_deterministic(self):
        p,o,q=base(); z1=evaluate(q,p,o); z2=evaluate(q,p,tuple(reversed(o))); self.assertEqual(z1.clusters,z2.clusters)
    def test_023_prepared_same(self):
        p,o,q=base(); st=prepare_state(p,o,binding=p.binding); v=validate_prepared_integrity(st); self.assertTrue(v); self.assertEqual(evaluate(q,p,o),evaluate_prepared(q,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=v))
    def test_024_prepared_unvalidated_hold(self): p,o,q=base(); st=prepare_state(p,o,binding=p.binding); self.assertEqual(evaluate_prepared(q,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=False).decision,Decision.HOLD)
    def test_025_prepared_policy_mismatch(self): p,o,q=base(); st=prepare_state(p,o,binding=p.binding); self.assertEqual(evaluate_prepared(q,st,current_policy_fingerprint='BAD',current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True).decision,Decision.HOLD)
    def test_026_prepared_registry_mismatch(self): p,o,q=base(); st=prepare_state(p,o,binding=p.binding); self.assertEqual(evaluate_prepared(q,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint='BAD',prepared_integrity_validated=True).decision,Decision.HOLD)
    def test_027_tamper_invalid(self): p,o,q=base(); st=prepare_state(p,o,binding=p.binding); self.assertFalse(validate_prepared_integrity(replace(st,registry_fingerprint='BAD')))
    def test_028_delta_roundtrip(self):
        p,o,q=base(); a=prepare_state(p,o,binding=p.binding); b=prepare_state(p,(replace(o[0],model_id='MODEL-X'),o[1],o[2]),binding=p.binding); self.assertEqual(apply_delta(a,make_delta(a,b)).registry_fingerprint,b.registry_fingerprint)
    def test_029_delta_base_mismatch(self):
        p,o,q=base(); a=prepare_state(p,o,binding=p.binding); b=prepare_state(p,(replace(o[0],model_id='MODEL-X'),o[1],o[2]),binding=p.binding); d=make_delta(a,b); bad=replace(d,base_fingerprint='BAD'); self.assertRaises(ValueError,apply_delta,a,bad)
    def test_030_missing_sync(self): p,o,q=base(); st=prepare_state(p,o,binding=p.binding); known=dict(st.output_fingerprints); known.pop('OUT-A'); plan=missing_only_sync_plan(st,known); self.assertEqual(plan.missing_or_changed_outputs,('OUT-A',)); self.assertFalse(plan.full_resend_required)
    def test_031_no_outputs_hold(self): p,o,q=base(); q=replace(q,output_ids=()); self.assertEqual(evaluate(q,p,o).decision,Decision.HOLD)
    def test_032_invalid_typed_hold(self): p,o,q=base(); self.assertEqual(evaluate({'x':1},p,o).decision,Decision.HOLD)
    def test_033_raw_votes_not_truth(self): p,o,q=base(); z=evaluate(q,p,o); self.assertFalse(z.world_truth_proven)
    def test_034_no_permission(self): p,o,q=base(); neg(self,evaluate(q,p,o))
    def test_035_source_overlap_graph(self): p,o,q=base(); b=replace(o[1],source_ids=('SRC-A','SRC-X')); a=replace(o[0],source_ids=('SRC-A','SRC-Y')); z=evaluate(q,p,(a,b,o[2])); self.assertTrue(any('SHARED_SOURCE' in e.reasons for e in z.edges))
    def test_036_evidence_overlap_graph(self): p,o,q=base(); b=replace(o[1],evidence_ids=('EVID-A','EVID-X')); a=replace(o[0],evidence_ids=('EVID-A','EVID-Y')); z=evaluate(q,p,(a,b,o[2])); self.assertTrue(any('SHARED_EVIDENCE' in e.reasons for e in z.edges))
    def test_037_agent_order_independent(self): p,o,q=base(); self.assertEqual(evaluate(q,p,o).adjusted_consensus,evaluate(q,p,(o[2],o[0],o[1])).adjusted_consensus)
    def test_038_target_missing_hold_or_deny(self): p,o,q=base(); q=replace(q,target_conclusion='MAYBE'); self.assertIn(evaluate(q,p,o).decision,(Decision.DENY,Decision.HOLD))
    def test_039_single_vote_hold(self): p,o,q=base(); q=replace(q,output_ids=('OUT-A',)); self.assertEqual(evaluate(q,p,o).decision,Decision.HOLD)
    def test_040_authority_negatives(self): p,o,q=base(); neg(self,evaluate(q,p,o))

def _gen(i):
    def f(self):
        p,o,q=base(); m=i%12
        if m==0: want=Decision.ALLOW
        elif m==1: o=(replace(o[0],lineage_observed=False),o[1],o[2]); want=Decision.HOLD
        elif m==2: q=replace(q,output_ids=('OUT-A',)); want=Decision.HOLD
        elif m==3: o=(replace(o[0],conclusion='NO'),replace(o[1],conclusion='NO'),o[2]); want=Decision.DENY
        elif m==4: p=replace(p,threshold=.75); want=Decision.HOLD
        elif m==5: q=replace(q,binding=f'BAD-{i}'); want=Decision.HOLD
        elif m==6: o=(replace(o[0],source_ids=(),evidence_ids=()),o[1],o[2]); want=Decision.HOLD
        elif m==7: q=replace(q,output_ids=('OUT-A','NOPE')); want=Decision.HOLD
        elif m==8: p=replace(p,min_effective_votes=4); want=Decision.HOLD
        elif m==9: a=o[0]; o=(a,replace(o[1],model_id=a.model_id,prompt_family=a.prompt_family,source_ids=a.source_ids,evidence_ids=a.evidence_ids),o[2]); want=Decision.HOLD
        elif m==10: o=(replace(o[0],weight=-1),o[1],o[2]); want=Decision.HOLD
        else: want=Decision.ALLOW
        z=evaluate(q,p,o); self.assertEqual(z.decision,want); neg(self,z)
    return f
for i in range(120): setattr(T,f'test_regression_{i:03d}',_gen(i))
if __name__=='__main__': unittest.main(verbosity=2)
