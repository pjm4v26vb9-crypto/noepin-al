import unittest
from dataclasses import replace
from noepin_al_067_assumption_verification_graph import *

NOW=1_800_000_000

def base():
    return default_policy(NOW), default_assumptions(), default_edges(), default_evidence(NOW), default_observations(NOW), default_actions(), default_request(NOW)

class T(unittest.TestCase):
    def test_001_all_verified(self):
        p,a,e,v,o,x,r=base(); z=evaluate(r,p,a,e,v,o,x,now=NOW); self.assertEqual(z.decision,Decision.ALLOW); self.assertTrue(z.next_gate_candidate)
    def test_002_high_unverified_hold(self):
        p,a,e,v,o,x,r=base(); v=tuple(q for q in v if q.assumption_id!="ASM-SCHEMA-COMPAT"); z=evaluate(r,p,a,e,v,o,x,now=NOW); self.assertEqual(z.decision,Decision.HOLD)
    def test_003_contradicted_deny(self):
        p,a,e,v,o,x,r=base(); v=v+(replace(v[1],evidence_id="E-SCHEMA-NO",state=EvidenceState.CONTRADICTED),); self.assertEqual(evaluate(r,p,a,e,v,o,x,now=NOW).decision,Decision.DENY)
    def test_004_low_unverified_risk(self):
        p,a,e,v,o,x,r=base(); r=replace(r,selected_action_ids=("ACT-READ-LOG",)); z=evaluate(r,p,a,e,v,o,x,now=NOW); self.assertEqual(z.decision,Decision.ALLOW); self.assertGreater(z.low_unverified_risk,0)
    def test_005_medium_unverified_hold(self):
        p,a,e,v,o,x,r=base(); v=tuple(q for q in v if q.assumption_id!="ASM-BACKUP-READY"); self.assertEqual(evaluate(r,p,a,e,v,o,x,now=NOW).decision,Decision.HOLD)
    def test_006_cycle_hold(self):
        p,a,e,v,o,x,r=base(); e=e+(AssumptionEdge("ASM-CONFIG-EXISTS","ASM-SCHEMA-COMPAT"),); z=evaluate(r,p,a,e,v,o,x,now=NOW); self.assertEqual(z.decision,Decision.HOLD); self.assertIn("ASSUMPTION_CYCLE",z.reasons[0])
    def test_007_unknown_action(self):
        p,a,e,v,o,x,r=base(); r=replace(r,selected_action_ids=("NOPE",)); self.assertEqual(evaluate(r,p,a,e,v,o,x,now=NOW).decision,Decision.HOLD)
    def test_008_policy_mismatch(self):
        p,a,e,v,o,x,r=base(); r=replace(r,expected_policy_version="X"); self.assertEqual(evaluate(r,p,a,e,v,o,x,now=NOW).decision,Decision.HOLD)
    def test_009_binding_mismatch(self):
        p,a,e,v,o,x,r=base(); r=replace(r,binding="X"); self.assertEqual(evaluate(r,p,a,e,v,o,x,now=NOW).decision,Decision.HOLD)
    def test_010_stale_request(self):
        p,a,e,v,o,x,r=base(); r=replace(r,created_at=NOW-9999); self.assertEqual(evaluate(r,p,a,e,v,o,x,now=NOW).decision,Decision.HOLD)
    def test_011_expired_evidence_is_unverified(self):
        p,a,e,v,o,x,r=base(); v=tuple(replace(q,expires_at=NOW-1) if q.assumption_id=="ASM-SCHEMA-COMPAT" else q for q in v); self.assertEqual(evaluate(r,p,a,e,v,o,x,now=NOW).decision,Decision.HOLD)
    def test_012_low_confidence_not_verified(self):
        p,a,e,v,o,x,r=base(); v=tuple(replace(q,confidence=.1) if q.assumption_id=="ASM-SCHEMA-COMPAT" else q for q in v); self.assertEqual(evaluate(r,p,a,e,v,o,x,now=NOW).decision,Decision.HOLD)
    def test_013_contradiction_beats_verified(self):
        p,a,e,v,o,x,r=base(); v=v+(replace(v[1],evidence_id="E-CONTRA",state=EvidenceState.CONTRADICTED),); self.assertIn("ASM-SCHEMA-COMPAT",evaluate(r,p,a,e,v,o,x,now=NOW).contradicted_assumption_ids)
    def test_014_observation_can_verify(self):
        p,a,e,v,o,x,r=base(); v=tuple(q for q in v if q.assumption_id!="ASM-SCHEMA-COMPAT"); c=dict(binding="AVG-BIND",verified=True,revoked=False,policy_id="AVG-POLICY",policy_version="1",authority_epoch="AVG-EPOCH"); o=o+(ObservationRecord("O-SCHEMA","ASM-SCHEMA-COMPAT",EvidenceState.VERIFIED,NOW-1,NOW+100,**c),); self.assertEqual(evaluate(r,p,a,e,v,o,x,now=NOW).decision,Decision.ALLOW)
    def test_015_prepared(self):
        p,a,e,v,o,x,r=base(); s=prepare_state(p,a,e,v,o,x,binding=r.binding,now=NOW); self.assertTrue(validate_prepared_integrity(s)); z=evaluate_prepared(r,s,current_policy_fingerprint=s.policy_fingerprint,current_registry_fingerprint=s.registry_fingerprint,prepared_integrity_validated=True,now=NOW); self.assertEqual(z.decision,Decision.ALLOW)
    def test_016_prepared_integrity_required(self):
        p,a,e,v,o,x,r=base(); s=prepare_state(p,a,e,v,o,x,binding=r.binding,now=NOW); self.assertEqual(evaluate_prepared(r,s,current_policy_fingerprint=s.policy_fingerprint,current_registry_fingerprint=s.registry_fingerprint,prepared_integrity_validated=False,now=NOW).decision,Decision.HOLD)
    def test_017_registry_mismatch(self):
        p,a,e,v,o,x,r=base(); s=prepare_state(p,a,e,v,o,x,binding=r.binding,now=NOW); self.assertEqual(evaluate_prepared(r,s,current_policy_fingerprint=s.policy_fingerprint,current_registry_fingerprint="bad",prepared_integrity_validated=True,now=NOW).decision,Decision.HOLD)
    def test_018_delta_reconstruct(self):
        p,a,e,v,o,x,r=base(); s1=prepare_state(p,a,e,v,o,x,binding=r.binding,now=NOW); v2=tuple(replace(q,confidence=.91) if q.evidence_id=="E-SCHEMA" else q for q in v); s2=prepare_state(p,a,e,v2,o,x,binding=r.binding,now=NOW); d=make_delta(s1,s2); s3=apply_delta(s1,d,now=NOW); self.assertEqual(s2.registry_fingerprint,s3.registry_fingerprint)
    def test_019_delta_base_mismatch(self):
        p,a,e,v,o,x,r=base(); s=prepare_state(p,a,e,v,o,x,binding=r.binding,now=NOW); d=make_delta(s,s); bad=replace(d,base_fingerprint="bad");
        with self.assertRaises(ValueError): apply_delta(s,bad,now=NOW)
    def test_020_missing_only(self):
        p,a,e,v,o,x,r=base(); s=prepare_state(p,a,e,v,o,x,binding=r.binding,now=NOW); remote={"assumptions":dict(s.assumption_fingerprints),"edges":dict(s.edge_fingerprints),"evidence":dict(s.evidence_fingerprints),"observations":dict(s.observation_fingerprints),"actions":{}}; plan=missing_only_sync_plan(s,remote); self.assertEqual(len(plan.missing_or_changed_action_ids),len(x)); self.assertFalse(plan.full_resend_required)
    def test_021_authority_false(self):
        p,a,e,v,o,x,r=base(); z=evaluate(r,p,a,e,v,o,x,now=NOW); self.assertFalse(any((z.permission_granted,z.environment_changed,z.evidence_written,z.action_executed,z.approval_executed,z.assumption_truth_proven,z.world_truth_proven,z.safety_proven,z.action_success)))
    def test_022_duplicate_assumption_invalid(self):
        p,a,e,v,o,x,r=base(); a=a+(a[0],); self.assertEqual(evaluate(r,p,a,e,v,o,x,now=NOW).decision,Decision.HOLD)
    def test_023_unknown_edge_invalid(self):
        p,a,e,v,o,x,r=base(); e=e+(AssumptionEdge("ASM-SCHEMA-COMPAT","NOPE"),); self.assertEqual(evaluate(r,p,a,e,v,o,x,now=NOW).decision,Decision.HOLD)
    def test_024_risk_budget(self):
        p,a,e,v,o,x,r=base(); a=a+(AssumptionSpec("L2",Impact.LOW,"AVG-BIND",True,False,"AVG-POLICY","1","AVG-EPOCH"),AssumptionSpec("L3",Impact.LOW,"AVG-BIND",True,False,"AVG-POLICY","1","AVG-EPOCH"),AssumptionSpec("L4",Impact.LOW,"AVG-BIND",True,False,"AVG-POLICY","1","AVG-EPOCH"),AssumptionSpec("L5",Impact.LOW,"AVG-BIND",True,False,"AVG-POLICY","1","AVG-EPOCH")); x=x+(ActionSpec("ACT-MANY",("ASM-LOG-LABEL","L2","L3","L4","L5"),"AVG-BIND",True,False,"AVG-POLICY","1","AVG-EPOCH"),); r=replace(r,selected_action_ids=("ACT-MANY",)); self.assertEqual(evaluate(r,p,a,e,v,o,x,now=NOW).decision,Decision.HOLD)
    def test_025_prepared_record_tamper_detected(self):
        p,a,e,v,o,x,r=base(); s=prepare_state(p,a,e,v,o,x,binding=r.binding,now=NOW); tampered=replace(s,evidence=(replace(s.evidence[0],confidence=.01),)+s.evidence[1:]); self.assertFalse(validate_prepared_integrity(tampered))

def _gen(i):
    def f(self):
        p,a,e,v,o,x,r=base()
        mode=i%4
        if mode==0: z=evaluate(r,p,a,e,v,o,x,now=NOW); self.assertEqual(z.decision,Decision.ALLOW)
        elif mode==1:
            vv=tuple(q for q in v if q.assumption_id!="ASM-SCHEMA-COMPAT"); z=evaluate(r,p,a,e,vv,o,x,now=NOW); self.assertEqual(z.decision,Decision.HOLD)
        elif mode==2:
            vv=v+(replace(v[0],evidence_id=f"C{i}",state=EvidenceState.CONTRADICTED),); z=evaluate(r,p,a,e,vv,o,x,now=NOW); self.assertEqual(z.decision,Decision.DENY)
        else:
            rr=replace(r,selected_action_ids=("ACT-READ-LOG",)); z=evaluate(rr,p,a,e,v,o,x,now=NOW); self.assertEqual(z.decision,Decision.ALLOW)
        self.assertFalse(z.permission_granted); self.assertFalse(z.action_executed); self.assertFalse(z.action_success)
    return f
for i in range(135): setattr(T,f"test_regression_{i:03d}",_gen(i))

if __name__=='__main__': unittest.main()
