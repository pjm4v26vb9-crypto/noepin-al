import unittest
from dataclasses import replace
from noepin_al_069_dependency_order_verifier import *

NOW=1_800_000_000

def common():
    return dict(binding="DOV-BIND",verified=True,revoked=False,policy_id="DOV-POLICY",policy_version="1",authority_epoch="DOV-EPOCH")

def base(seq=None):
    return default_policy(NOW), default_actions(), default_observations(), default_forbidden_orders(), default_request(NOW,seq)

class T(unittest.TestCase):
    def test_001_normal_order_allow(self):
        p,a,o,f,r=base(); z=evaluate(r,p,a,o,f,now=NOW); self.assertEqual(z.decision,Decision.ALLOW); self.assertTrue(z.next_gate_candidate); self.assertEqual(z.legal_order,r.action_sequence)
    def test_002_missing_prerequisite_action_hold(self):
        p,a,o,f,r=base(("A-APPLY","A-VERIFY","A-CLEANUP")); z=evaluate(r,p,a,o,f,now=NOW); self.assertEqual(z.decision,Decision.HOLD); self.assertTrue(any(x.startswith("MISSING_ACTION:A-SNAPSHOT") for x in z.unmet_dependencies))
    def test_003_reversed_dependency_hold_with_reorder(self):
        p,a,o,f,r=base(("A-APPLY","A-SNAPSHOT","A-VERIFY","A-CLEANUP")); z=evaluate(r,p,a,o,f,now=NOW); self.assertEqual(z.decision,Decision.HOLD); self.assertTrue(z.reorder_required); self.assertEqual(z.legal_order,("A-SNAPSHOT","A-APPLY","A-VERIFY","A-CLEANUP"))
    def test_004_forbidden_order_deny(self):
        p,a,o,f,r=base(("A-SNAPSHOT","A-APPLY","A-CLEANUP","A-VERIFY")); z=evaluate(r,p,a,o,f,now=NOW); self.assertEqual(z.decision,Decision.DENY); self.assertIn("A-CLEANUP>A-VERIFY",z.forbidden_violations)
    def test_005_cycle_hold(self):
        p,a,o,f,r=base(); a=tuple(replace(x,preconditions=x.preconditions+(Predicate("cleanup_done","true"),)) if x.action_id=="A-SNAPSHOT" else x for x in a); z=evaluate(r,p,a,o,f,now=NOW); self.assertEqual(z.decision,Decision.HOLD); self.assertIn("CYCLIC_DEPENDENCY",z.reasons)
    def test_006_unknown_observation_hold(self):
        p,a,o,f,r=base(); o=tuple(replace(x,known=False) if x.predicate.name=="workspace_ready" else x for x in o); z=evaluate(r,p,a,o,f,now=NOW); self.assertEqual(z.decision,Decision.HOLD); self.assertIn("UNOBSERVABLE_PRECONDITION",z.reasons)
    def test_007_unsatisfied_no_producer_hold(self):
        p,a,o,f,r=base(); a=tuple(replace(x,preconditions=x.preconditions+(Predicate("manual_lock","true"),)) if x.action_id=="A-SNAPSHOT" else x for x in a); o=o+(StateObservation(Predicate("manual_lock","true"),False,**common()),); z=evaluate(r,p,a,o,f,now=NOW); self.assertEqual(z.decision,Decision.HOLD); self.assertIn("UNOBSERVABLE_PRECONDITION",z.reasons)
    def test_008_duplicate_plan_action_hold(self):
        p,a,o,f,r=base(("A-SNAPSHOT","A-APPLY","A-APPLY","A-VERIFY")); self.assertEqual(evaluate(r,p,a,o,f,now=NOW).decision,Decision.HOLD)
    def test_009_unknown_action_hold(self):
        p,a,o,f,r=base(("A-SNAPSHOT","NOPE")); z=evaluate(r,p,a,o,f,now=NOW); self.assertEqual(z.decision,Decision.HOLD); self.assertIn("NOPE",z.violating_actions)
    def test_010_policy_mismatch_hold(self):
        p,a,o,f,r=base(); r=replace(r,expected_policy_version="X"); self.assertEqual(evaluate(r,p,a,o,f,now=NOW).decision,Decision.HOLD)
    def test_011_binding_mismatch_hold(self):
        p,a,o,f,r=base(); r=replace(r,binding="X"); self.assertEqual(evaluate(r,p,a,o,f,now=NOW).decision,Decision.HOLD)
    def test_012_stale_request_hold(self):
        p,a,o,f,r=base(); r=replace(r,created_at=NOW-9999); self.assertEqual(evaluate(r,p,a,o,f,now=NOW).decision,Decision.HOLD)
    def test_013_invalid_policy_hold(self):
        p,a,o,f,r=base(); p=replace(p,revoked=True); self.assertEqual(evaluate(r,p,a,o,f,now=NOW).decision,Decision.HOLD)
    def test_014_duplicate_action_id_invalid(self):
        p,a,o,f,r=base(); self.assertEqual(evaluate(r,p,a+(a[0],),o,f,now=NOW).decision,Decision.HOLD)
    def test_015_multiple_producer_invalid(self):
        p,a,o,f,r=base(); extra=replace(a[0],action_id="A-SNAPSHOT-2"); self.assertEqual(evaluate(r,p,a+(extra,),o,f,now=NOW).decision,Decision.HOLD)
    def test_016_prepared_allow(self):
        p,a,o,f,r=base(); st=prepare_state(p,a,o,f,binding=r.binding,now=NOW); self.assertTrue(validate_prepared_integrity(st)); z=evaluate_prepared(r,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True,now=NOW); self.assertEqual(z.decision,Decision.ALLOW)
    def test_017_prepared_integrity_required(self):
        p,a,o,f,r=base(); st=prepare_state(p,a,o,f,binding=r.binding,now=NOW); z=evaluate_prepared(r,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=False,now=NOW); self.assertEqual(z.decision,Decision.HOLD)
    def test_018_prepared_tamper_detected(self):
        p,a,o,f,r=base(); st=prepare_state(p,a,o,f,binding=r.binding,now=NOW); tam=replace(st,actions=(replace(st.actions[0],postconditions=(Predicate("tampered","true"),)),)+st.actions[1:]); self.assertFalse(validate_prepared_integrity(tam))
    def test_019_registry_fp_mismatch_hold(self):
        p,a,o,f,r=base(); st=prepare_state(p,a,o,f,binding=r.binding,now=NOW); z=evaluate_prepared(r,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint="bad",prepared_integrity_validated=True,now=NOW); self.assertEqual(z.decision,Decision.HOLD)
    def test_020_delta_reconstruct(self):
        p,a,o,f,r=base(); s1=prepare_state(p,a,o,f,binding=r.binding,now=NOW); a2=tuple(replace(x,postconditions=x.postconditions+(Predicate("audit_marker","true"),)) if x.action_id=="A-CLEANUP" else x for x in a); s2=prepare_state(p,a2,o,f,binding=r.binding,now=NOW); d=make_delta(s1,s2); s3=apply_delta(s1,d,now=NOW); self.assertEqual(s2.registry_fingerprint,s3.registry_fingerprint)
    def test_021_delta_base_mismatch(self):
        p,a,o,f,r=base(); st=prepare_state(p,a,o,f,binding=r.binding,now=NOW); d=replace(make_delta(st,st),base_fingerprint="bad")
        with self.assertRaises(ValueError): apply_delta(st,d,now=NOW)
    def test_022_missing_only_sync(self):
        p,a,o,f,r=base(); st=prepare_state(p,a,o,f,binding=r.binding,now=NOW); remote={"actions":dict(st.action_fingerprints),"observations":dict(st.observation_fingerprints),"forbidden_orders":dict(st.forbidden_fingerprints)}; remote["actions"].pop("A-CLEANUP"); q=missing_only_sync_plan(st,remote); self.assertEqual(q.missing_or_changed_action_ids,("A-CLEANUP",)); self.assertFalse(q.full_resend_required)
    def test_023_authority_false(self):
        p,a,o,f,r=base(); z=evaluate(r,p,a,o,f,now=NOW); self.assertFalse(any((z.permission_granted,z.plan_rewritten,z.state_written,z.action_executed,z.deployment_executed,z.approval_executed,z.world_truth_proven,z.safety_proven,z.action_success)))
    def test_024_independent_actions_stable(self):
        p,a,o,f,r=base(); c=common(); a=a+(ActionSpec("A-NOTE",(Predicate("workspace_ready","true"),),(Predicate("note_ready","true"),),**c),); r=replace(r,action_sequence=("A-NOTE",)+r.action_sequence); z=evaluate(r,p,a,o,f,now=NOW); self.assertEqual(z.decision,Decision.ALLOW); self.assertEqual(z.legal_order,r.action_sequence)
    def test_025_satisfied_current_state_allows_producer_omission(self):
        p,a,o,f,r=base(("A-APPLY","A-VERIFY","A-CLEANUP")); o=tuple(replace(x,known=True) if x.predicate.name=="snapshot_exists" else x for x in o); z=evaluate(r,p,a,o,f,now=NOW); self.assertEqual(z.decision,Decision.ALLOW)

def _gen(i):
    def f(self):
        p,a,o,fo,r=base(); m=i%5
        if m==0:
            z=evaluate(r,p,a,o,fo,now=NOW); self.assertEqual(z.decision,Decision.ALLOW)
        elif m==1:
            rr=replace(r,action_sequence=("A-APPLY","A-VERIFY","A-CLEANUP")); z=evaluate(rr,p,a,o,fo,now=NOW); self.assertEqual(z.decision,Decision.HOLD)
        elif m==2:
            rr=replace(r,action_sequence=("A-APPLY","A-SNAPSHOT","A-VERIFY","A-CLEANUP")); z=evaluate(rr,p,a,o,fo,now=NOW); self.assertEqual(z.decision,Decision.HOLD); self.assertTrue(z.reorder_required)
        elif m==3:
            rr=replace(r,action_sequence=("A-SNAPSHOT","A-APPLY","A-CLEANUP","A-VERIFY")); z=evaluate(rr,p,a,o,fo,now=NOW); self.assertEqual(z.decision,Decision.DENY)
        else:
            oo=tuple(replace(x,known=False) if x.predicate.name=="workspace_ready" else x for x in o); z=evaluate(r,p,a,oo,fo,now=NOW); self.assertEqual(z.decision,Decision.HOLD)
        self.assertFalse(z.permission_granted); self.assertFalse(z.action_executed); self.assertFalse(z.action_success)
    return f
for i in range(135): setattr(T,f"test_regression_{i:03d}",_gen(i))

if __name__=='__main__': unittest.main()
