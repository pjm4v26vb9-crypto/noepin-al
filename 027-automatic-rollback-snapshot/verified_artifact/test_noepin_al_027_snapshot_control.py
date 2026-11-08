import dataclasses
import math
import unittest

from noepin_al_027_snapshot_control import (
    RollbackRequest,
    SnapshotControl,
    SnapshotDecision,
    SnapshotMode,
    SnapshotPolicy,
    SnapshotRequest,
    fingerprint,
)


class SnapshotControlTests(unittest.TestCase):
    def setUp(self):
        self.policy = SnapshotPolicy(max_delta_ratio=0.50)
        self.c = SnapshotControl(self.policy)
        self.base = {"a": 1, "b": {"x": 2, "y": 3}, "c": "ok", "list": [1,2,3]}
        self.cur = {"a": 1, "b": {"x": 9, "y": 3}, "c": "ok", "list": [1,2,3]}

    def req(self, **kw):
        d = dict(request_id="r1", target_ref="cfg/app", target_version="v2", current_state=self.cur, previous_state=self.base,
                 previous_snapshot_id="snap-base", previous_snapshot_fingerprint=fingerprint(self.base,self.policy), reason="pre_action", context="test")
        d.update(kw)
        return SnapshotRequest(**d)

    def test_01_delta_selected_for_small_change(self):
        p=self.c.prepare_snapshot(self.req()); self.assertEqual(p.mode, SnapshotMode.DELTA)
    def test_02_snapshot_prepare_only(self):
        p=self.c.prepare_snapshot(self.req()); self.assertEqual(p.decision, SnapshotDecision.SNAPSHOT_PREPARE); self.assertFalse(p.snapshot_persisted)
    def test_03_not_authoritative(self): self.assertFalse(self.c.prepare_snapshot(self.req()).authoritative)
    def test_04_not_committed(self): self.assertFalse(self.c.prepare_snapshot(self.req()).state_committed)
    def test_05_not_rollback_executed(self): self.assertFalse(self.c.prepare_snapshot(self.req()).rollback_executed)
    def test_06_not_rollback_succeeded(self): self.assertFalse(self.c.prepare_snapshot(self.req()).rollback_succeeded)
    def test_07_verify_delta(self): self.assertTrue(self.c.verify_snapshot_plan(self.c.prepare_snapshot(self.req()), base_state=self.base))
    def test_08_full_without_previous(self):
        r=self.req(previous_state=None,previous_snapshot_id=None,previous_snapshot_fingerprint=None); p=self.c.prepare_snapshot(r); self.assertEqual(p.mode, SnapshotMode.FULL)
    def test_09_verify_full(self):
        r=self.req(previous_state=None,previous_snapshot_id=None,previous_snapshot_fingerprint=None); p=self.c.prepare_snapshot(r); self.assertTrue(self.c.verify_snapshot_plan(p))
    def test_10_full_contains_state(self):
        r=self.req(previous_state=None,previous_snapshot_id=None,previous_snapshot_fingerprint=None); self.assertEqual(self.c.prepare_snapshot(r).full_state, self.cur)
    def test_11_delta_has_no_full_state(self): self.assertIsNone(self.c.prepare_snapshot(self.req()).full_state)
    def test_12_delta_nonempty(self): self.assertGreater(len(self.c.prepare_snapshot(self.req()).delta),0)
    def test_13_missing_request_denied(self): self.assertEqual(self.c.prepare_snapshot(self.req(request_id="")).decision, SnapshotDecision.DENY)
    def test_14_missing_target_denied(self): self.assertEqual(self.c.prepare_snapshot(self.req(target_ref="")).decision, SnapshotDecision.DENY)
    def test_15_missing_version_hold(self): self.assertEqual(self.c.prepare_snapshot(self.req(target_version="")).decision, SnapshotDecision.HOLD)
    def test_16_base_fp_mismatch_hold(self): self.assertEqual(self.c.prepare_snapshot(self.req(previous_snapshot_fingerprint="bad")).decision, SnapshotDecision.HOLD)
    def test_17_nonfinite_current_denied(self): self.assertEqual(self.c.prepare_snapshot(self.req(current_state={"x":float("nan")})).decision, SnapshotDecision.DENY)
    def test_18_nonfinite_previous_denied(self): self.assertEqual(self.c.prepare_snapshot(self.req(previous_state={"x":float("inf")},previous_snapshot_fingerprint=None)).decision, SnapshotDecision.DENY)
    def test_19_non_string_key_denied(self): self.assertEqual(self.c.prepare_snapshot(self.req(current_state={1:"x"})).decision, SnapshotDecision.DENY)
    def test_20_unsupported_type_denied(self): self.assertEqual(self.c.prepare_snapshot(self.req(current_state={"x":object()})).decision, SnapshotDecision.DENY)
    def test_21_snapshot_id_deterministic(self): self.assertEqual(self.c.prepare_snapshot(self.req()).snapshot_id,self.c.prepare_snapshot(self.req()).snapshot_id)
    def test_22_checkpoint_deterministic(self): self.assertEqual(self.c.prepare_snapshot(self.req()).checkpoint_fingerprint,self.c.prepare_snapshot(self.req()).checkpoint_fingerprint)
    def test_23_state_fp_changes_with_state(self):
        p1=self.c.prepare_snapshot(self.req()); p2=self.c.prepare_snapshot(self.req(request_id="r2",current_state={**self.cur,"z":1})); self.assertNotEqual(p1.state_fingerprint,p2.state_fingerprint)
    def test_24_target_version_changes_id(self):
        self.assertNotEqual(self.c.prepare_snapshot(self.req()).snapshot_id,self.c.prepare_snapshot(self.req(request_id="r2",target_version="v3")).snapshot_id)
    def test_25_target_ref_changes_id(self):
        self.assertNotEqual(self.c.prepare_snapshot(self.req()).snapshot_id,self.c.prepare_snapshot(self.req(request_id="r2",target_ref="other")).snapshot_id)
    def test_26_cache_same_object_value(self): self.assertEqual(self.c.prepare_snapshot(self.req()), self.c.prepare_snapshot(self.req()))
    def test_27_cache_bypass_same_result(self): self.assertEqual(self.c.prepare_snapshot(self.req()), self.c.prepare_snapshot(self.req(),use_cache=False))
    def test_28_cache_clear(self): self.c.prepare_snapshot(self.req()); self.c.clear_cache(); self.assertEqual(self.c._cache,{})
    def test_29_large_change_full(self):
        current={f"k{i}":i+1000 for i in range(100)}; base={f"k{i}":i for i in range(100)}
        p=self.c.prepare_snapshot(SnapshotRequest("r","t","v",current,base,"b",fingerprint(base,self.policy))); self.assertEqual(p.mode,SnapshotMode.FULL)
    def test_30_removed_key_delta_reconstructs(self):
        base={"a":1,"b":2}; cur={"a":1}; p=self.c.prepare_snapshot(SnapshotRequest("r","t","v",cur,base,"b",fingerprint(base,self.policy))); self.assertTrue(self.c.verify_snapshot_plan(p,base_state=base))
    def test_31_added_key_delta_reconstructs(self):
        base={"a":1}; cur={"a":1,"b":2}; p=self.c.prepare_snapshot(SnapshotRequest("r","t","v",cur,base,"b",fingerprint(base,self.policy))); self.assertTrue(self.c.verify_snapshot_plan(p,base_state=base))
    def test_32_nested_delta_reconstructs(self): self.assertTrue(self.c.verify_snapshot_plan(self.c.prepare_snapshot(self.req()),base_state=self.base))
    def test_33_escaped_path_reconstructs(self):
        base={"a/b":{"~x":1}}; cur={"a/b":{"~x":2}}; p=self.c.prepare_snapshot(SnapshotRequest("r","t","v",cur,base,"b",fingerprint(base,self.policy))); self.assertTrue(self.c.verify_snapshot_plan(p,base_state=base))
    def test_34_wrong_base_fails_verify(self): self.assertFalse(self.c.verify_snapshot_plan(self.c.prepare_snapshot(self.req()),base_state={"bad":1}))
    def test_35_tampered_state_fp_fails(self):
        p=self.c.prepare_snapshot(self.req()); q=dataclasses.replace(p,state_fingerprint="0"*64); self.assertFalse(self.c.verify_snapshot_plan(q,base_state=self.base))
    def test_36_tampered_checkpoint_fails(self):
        p=self.c.prepare_snapshot(self.req()); q=dataclasses.replace(p,checkpoint_fingerprint="0"*64); self.assertFalse(self.c.verify_snapshot_plan(q,base_state=self.base))
    def test_37_tampered_delta_fails(self):
        p=self.c.prepare_snapshot(self.req()); q=dataclasses.replace(p,delta=(("set","/b/x",999),)); self.assertFalse(self.c.verify_snapshot_plan(q,base_state=self.base))
    def test_38_full_with_delta_fails(self):
        r=self.req(previous_state=None,previous_snapshot_id=None,previous_snapshot_fingerprint=None); p=self.c.prepare_snapshot(r); q=dataclasses.replace(p,delta=(("set","/x",1),)); self.assertFalse(self.c.verify_snapshot_plan(q))
    def test_39_delta_with_full_state_fails(self):
        p=self.c.prepare_snapshot(self.req()); q=dataclasses.replace(p,full_state=self.cur); self.assertFalse(self.c.verify_snapshot_plan(q,base_state=self.base))
    def test_40_rollback_candidate_prepared(self):
        p=self.c.prepare_snapshot(self.req()); rr=RollbackRequest("rb","cfg/app","v3",{"changed":1},p,self.base,p.snapshot_id); rb=self.c.prepare_rollback(rr); self.assertEqual(rb.decision,SnapshotDecision.ROLLBACK_PREPARE)
    def test_41_rollback_candidate_matches_snapshot(self):
        p=self.c.prepare_snapshot(self.req()); rb=self.c.prepare_rollback(RollbackRequest("rb","cfg/app","v3",{},p,self.base,p.snapshot_id)); self.assertEqual(rb.restored_candidate,self.cur)
    def test_42_rollback_not_executed(self):
        p=self.c.prepare_snapshot(self.req()); rb=self.c.prepare_rollback(RollbackRequest("rb","cfg/app","v3",{},p,self.base,p.snapshot_id)); self.assertFalse(rb.rollback_executed)
    def test_43_rollback_not_succeeded(self):
        p=self.c.prepare_snapshot(self.req()); rb=self.c.prepare_rollback(RollbackRequest("rb","cfg/app","v3",{},p,self.base,p.snapshot_id)); self.assertFalse(rb.rollback_succeeded)
    def test_44_rollback_not_committed(self):
        p=self.c.prepare_snapshot(self.req()); rb=self.c.prepare_rollback(RollbackRequest("rb","cfg/app","v3",{},p,self.base,p.snapshot_id)); self.assertFalse(rb.state_committed)
    def test_45_rollback_not_authoritative(self):
        p=self.c.prepare_snapshot(self.req()); rb=self.c.prepare_rollback(RollbackRequest("rb","cfg/app","v3",{},p,self.base,p.snapshot_id)); self.assertFalse(rb.authoritative)
    def test_46_rollback_wrong_id_hold(self):
        p=self.c.prepare_snapshot(self.req()); rb=self.c.prepare_rollback(RollbackRequest("rb","cfg/app","v3",{},p,self.base,"wrong")); self.assertEqual(rb.decision,SnapshotDecision.HOLD)
    def test_47_rollback_wrong_target_deny(self):
        p=self.c.prepare_snapshot(self.req()); rb=self.c.prepare_rollback(RollbackRequest("rb","other","v3",{},p,self.base,p.snapshot_id)); self.assertEqual(rb.decision,SnapshotDecision.DENY)
    def test_48_rollback_missing_version_hold(self):
        p=self.c.prepare_snapshot(self.req()); rb=self.c.prepare_rollback(RollbackRequest("rb","cfg/app","",{},p,self.base,p.snapshot_id)); self.assertEqual(rb.decision,SnapshotDecision.HOLD)
    def test_49_rollback_bad_base_hold(self):
        p=self.c.prepare_snapshot(self.req()); rb=self.c.prepare_rollback(RollbackRequest("rb","cfg/app","v3",{},p,{"bad":1},p.snapshot_id)); self.assertEqual(rb.decision,SnapshotDecision.HOLD)
    def test_50_full_rollback(self):
        p=self.c.prepare_snapshot(self.req(previous_state=None,previous_snapshot_id=None,previous_snapshot_fingerprint=None)); rb=self.c.prepare_rollback(RollbackRequest("rb","cfg/app","v3",{},p,None,p.snapshot_id)); self.assertEqual(rb.restored_candidate,self.cur)
    def test_51_depth_limit(self):
        c=SnapshotControl(SnapshotPolicy(max_depth=2)); self.assertEqual(c.prepare_snapshot(SnapshotRequest("r","t","v",{"a":{"b":{"c":1}}})).decision,SnapshotDecision.DENY)
    def test_52_node_limit(self):
        c=SnapshotControl(SnapshotPolicy(max_nodes=3)); self.assertEqual(c.prepare_snapshot(SnapshotRequest("r","t","v",{"a":1,"b":2,"c":3})).decision,SnapshotDecision.DENY)
    def test_53_list_change_forces_set_op(self):
        base={"a":[1,2]}; cur={"a":[1,3]}; p=self.c.prepare_snapshot(SnapshotRequest("r","t","v",cur,base,"b",fingerprint(base,self.policy))); self.assertTrue(self.c.verify_snapshot_plan(p,base_state=base))
    def test_54_key_order_same_fp(self): self.assertEqual(fingerprint({"a":1,"b":2},self.policy),fingerprint({"b":2,"a":1},self.policy))
    def test_55_tuple_list_same_canonical_fp(self): self.assertEqual(fingerprint({"a":(1,2)},self.policy),fingerprint({"a":[1,2]},self.policy))
    def test_56_request_reason_changes_cache_key_not_state_fp(self):
        p1=self.c.prepare_snapshot(self.req()); p2=self.c.prepare_snapshot(self.req(request_id="r2",reason="manual")); self.assertEqual(p1.state_fingerprint,p2.state_fingerprint)
    def test_57_context_changes_cache_key_not_snapshot_id(self):
        p1=self.c.prepare_snapshot(self.req()); p2=self.c.prepare_snapshot(self.req(request_id="r2",context="x")); self.assertEqual(p1.snapshot_id,p2.snapshot_id)
    def test_58_previous_snapshot_id_not_authority(self):
        p=self.c.prepare_snapshot(self.req(previous_snapshot_id="fake-but-bound")); self.assertEqual(p.decision,SnapshotDecision.SNAPSHOT_PREPARE); self.assertFalse(p.authoritative)
    def test_59_snapshot_persisted_always_false(self): self.assertFalse(self.c.prepare_snapshot(self.req()).snapshot_persisted)
    def test_60_rollback_fp_equals_snapshot_fp(self):
        p=self.c.prepare_snapshot(self.req()); rb=self.c.prepare_rollback(RollbackRequest("rb","cfg/app","v3",{},p,self.base,p.snapshot_id)); self.assertEqual(rb.restored_fingerprint,p.state_fingerprint)
    def test_61_current_state_not_mutated(self):
        cur=dict(self.cur); _=self.c.prepare_snapshot(self.req(current_state=cur)); self.assertEqual(cur,self.cur)
    def test_62_base_state_not_mutated(self):
        base={"a":1,"b":2}; original=dict(base); _=self.c.prepare_snapshot(SnapshotRequest("r","t","v",{"a":2,"b":2},base,"b",fingerprint(base,self.policy))); self.assertEqual(base,original)
    def test_63_rollback_base_not_mutated(self):
        base=dict(self.base); p=self.c.prepare_snapshot(self.req()); _=self.c.prepare_rollback(RollbackRequest("rb","cfg/app","v3",{},p,base,p.snapshot_id)); self.assertEqual(base,self.base)
    def test_64_no_policy_truth_flag(self): self.assertFalse(hasattr(self.c,"truth_established"))
    def test_65_default_policy_version_bound(self): self.assertIn("snapshot-policy-v2", self.policy.policy_version)
    def test_66_invalid_plan_hold_rollback(self):
        p=dataclasses.replace(self.c.prepare_snapshot(self.req()),decision=SnapshotDecision.HOLD); rb=self.c.prepare_rollback(RollbackRequest("rb","cfg/app","v3",{},p,self.base,p.snapshot_id)); self.assertEqual(rb.decision,SnapshotDecision.HOLD)
    def test_67_checkpoint_changes_on_delta_change(self):
        p1=self.c.prepare_snapshot(self.req()); cur2={**self.cur,"z":1}; p2=self.c.prepare_snapshot(self.req(request_id="r2",current_state=cur2)); self.assertNotEqual(p1.checkpoint_fingerprint,p2.checkpoint_fingerprint)
    def test_68_checkpoint_not_success_flag(self): self.assertFalse(self.c.prepare_snapshot(self.req()).rollback_succeeded)
    def test_69_policy_delta_ratio_zero_forces_full(self):
        c=SnapshotControl(SnapshotPolicy(max_delta_ratio=0.0)); p=c.prepare_snapshot(SnapshotRequest("r","t","v",self.cur,self.base,"b",fingerprint(self.base,c.policy))); self.assertEqual(p.mode,SnapshotMode.FULL)
    def test_70_empty_dict_full(self):
        p=self.c.prepare_snapshot(SnapshotRequest("r","t","v",{})); self.assertEqual(p.mode,SnapshotMode.FULL); self.assertTrue(self.c.verify_snapshot_plan(p))

if __name__ == "__main__":
    unittest.main()
