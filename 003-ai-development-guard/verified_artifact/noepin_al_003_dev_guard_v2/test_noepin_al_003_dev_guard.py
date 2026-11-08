import hashlib
import json
import random
import unittest

from noepin_al_003_dev_guard import (
    DevelopmentGuard, DevelopmentPolicy, DevelopmentRequest,
    GuardDecision, Operation
)

H0 = "0" * 64
H1 = "1" * 64
H2 = "2" * 64

def policy():
    return DevelopmentPolicy(
        allowed_roots=("project", "sandbox", "tests"),
        protected_prefixes=("project/.git", "project/baseline", "project/production"),
        executable_roots=("tests", "sandbox/tools"),
        require_successor_for_modify=True,
        require_rollback_for_destructive=True,
        require_human_for_delete=True,
        require_human_for_overwrite=True,
        max_diff_bytes_without_confirmation=1024,
        policy_version="v2",
    )

def req(**kw):
    base = dict(
        operation=Operation.READ, target_path="project/src/a.py", actor_id="ai-1",
        target_exists=True, overwrite_existing=False, successor_path=None,
        rollback_ref=None, source_sha256=None, proposed_sha256=None,
        diff_sha256=None, diff_bytes=0, human_approved=False,
        approval_ref=None, external_side_effect=False, requested_execution=False,
        context={}, schema_version="1",
    )
    base.update(kw)
    return DevelopmentRequest(**base)

class GuardTests(unittest.TestCase):
    def setUp(self):
        self.g = DevelopmentGuard(policy())

    def assertD(self, r, d, reason=None):
        out = self.g.evaluate(r)
        self.assertEqual(out.decision, d)
        self.assertFalse(out.action_executed)
        self.assertFalse(out.commit_performed)
        self.assertFalse(out.authoritative)
        if reason:
            self.assertIn(reason, out.reason_codes)

    def test_read_allowed(self): self.assertD(req(), GuardDecision.ALLOW_PREPARE)
    def test_backslash_normalized(self): self.assertEqual(self.g.evaluate(req(target_path=r"project\src\a.py")).canonical_target, "project/src/a.py")
    def test_dot_normalized(self): self.assertEqual(self.g.evaluate(req(target_path="project/./src/a.py")).canonical_target, "project/src/a.py")
    def test_parent_traversal_denied(self): self.assertD(req(target_path="project/src/../../x"), GuardDecision.DENY)
    def test_absolute_denied(self): self.assertD(req(target_path="/etc/passwd"), GuardDecision.DENY)
    def test_windows_drive_denied(self): self.assertD(req(target_path="C:\\temp\\a"), GuardDecision.DENY)
    def test_empty_denied(self): self.assertD(req(target_path=""), GuardDecision.DENY)
    def test_outside_root_denied(self): self.assertD(req(target_path="other/a"), GuardDecision.DENY)
    def test_protected_git_denied(self): self.assertD(req(target_path="project/.git/config"), GuardDecision.DENY)
    def test_protected_baseline_denied(self): self.assertD(req(target_path="project/baseline/a"), GuardDecision.DENY)
    def test_protected_production_denied(self): self.assertD(req(target_path="project/production/a"), GuardDecision.DENY)
    def test_missing_actor_hold(self): self.assertD(req(actor_id=""), GuardDecision.HOLD)
    def test_missing_schema_hold(self): self.assertD(req(schema_version=""), GuardDecision.HOLD)
    def test_bad_diff_type_hold(self): self.assertD(req(diff_bytes=-1), GuardDecision.HOLD)

    def test_create_allowed(self):
        self.assertD(req(operation=Operation.CREATE,target_path="sandbox/new.py",target_exists=False,proposed_sha256=H1), GuardDecision.ALLOW_PREPARE)
    def test_create_missing_hash_hold(self):
        self.assertD(req(operation=Operation.CREATE,target_path="sandbox/new.py",target_exists=False), GuardDecision.HOLD)
    def test_create_overwrite_needs_human(self):
        self.assertD(req(operation=Operation.CREATE,target_path="sandbox/a",target_exists=True,overwrite_existing=True,proposed_sha256=H1), GuardDecision.HUMAN_CONFIRM)
    def test_create_overwrite_with_approval(self):
        self.assertD(req(operation=Operation.CREATE,target_path="sandbox/a",target_exists=True,overwrite_existing=True,proposed_sha256=H1,human_approved=True,approval_ref="A1"), GuardDecision.ALLOW_PREPARE)
    def test_create_external_side_effect_confirm(self):
        self.assertD(req(operation=Operation.CREATE,target_path="sandbox/a",proposed_sha256=H1,external_side_effect=True), GuardDecision.HUMAN_CONFIRM)

    def test_modify_requires_existing(self):
        self.assertD(req(operation=Operation.MODIFY,target_exists=False,source_sha256=H0,proposed_sha256=H1,diff_sha256=H2,successor_path="project/src/a.v2.py"), GuardDecision.HOLD)
    def test_modify_requires_hashes(self):
        self.assertD(req(operation=Operation.MODIFY,target_exists=True,successor_path="project/src/a.v2.py"), GuardDecision.HOLD)
    def test_modify_no_effect_hold(self):
        self.assertD(req(operation=Operation.MODIFY,target_exists=True,source_sha256=H1,proposed_sha256=H1,diff_sha256=H2,successor_path="project/src/a.v2.py"), GuardDecision.HOLD)
    def test_modify_requires_successor(self):
        self.assertD(req(operation=Operation.MODIFY,target_exists=True,source_sha256=H0,proposed_sha256=H1,diff_sha256=H2), GuardDecision.HOLD)
    def test_modify_in_place_forbidden(self):
        self.assertD(req(operation=Operation.MODIFY,target_exists=True,source_sha256=H0,proposed_sha256=H1,diff_sha256=H2,successor_path="project/src/a.py"), GuardDecision.DENY)
    def test_modify_successor_outside_denied(self):
        self.assertD(req(operation=Operation.MODIFY,target_exists=True,source_sha256=H0,proposed_sha256=H1,diff_sha256=H2,successor_path="other/a.py"), GuardDecision.DENY)
    def test_modify_successor_protected_denied(self):
        self.assertD(req(operation=Operation.MODIFY,target_exists=True,source_sha256=H0,proposed_sha256=H1,diff_sha256=H2,successor_path="project/production/a.v2.py"), GuardDecision.DENY)
    def test_modify_allowed(self):
        self.assertD(req(operation=Operation.MODIFY,target_exists=True,source_sha256=H0,proposed_sha256=H1,diff_sha256=H2,successor_path="project/src/a.v2.py",diff_bytes=500), GuardDecision.ALLOW_PREPARE)
    def test_modify_large_diff_confirm(self):
        self.assertD(req(operation=Operation.MODIFY,target_exists=True,source_sha256=H0,proposed_sha256=H1,diff_sha256=H2,successor_path="project/src/a.v2.py",diff_bytes=2048), GuardDecision.HUMAN_CONFIRM)
    def test_modify_large_diff_approved(self):
        self.assertD(req(operation=Operation.MODIFY,target_exists=True,source_sha256=H0,proposed_sha256=H1,diff_sha256=H2,successor_path="project/src/a.v2.py",diff_bytes=2048,human_approved=True,approval_ref="A2"), GuardDecision.ALLOW_PREPARE)
    def test_modify_overwrite_confirm(self):
        self.assertD(req(operation=Operation.MODIFY,target_exists=True,overwrite_existing=True,source_sha256=H0,proposed_sha256=H1,diff_sha256=H2,successor_path="project/src/a.v2.py"), GuardDecision.HUMAN_CONFIRM)
    def test_modify_overwrite_approved(self):
        self.assertD(req(operation=Operation.MODIFY,target_exists=True,overwrite_existing=True,source_sha256=H0,proposed_sha256=H1,diff_sha256=H2,successor_path="project/src/a.v2.py",human_approved=True,approval_ref="A3"), GuardDecision.ALLOW_PREPARE)

    def test_delete_requires_rollback(self):
        self.assertD(req(operation=Operation.DELETE), GuardDecision.HOLD)
    def test_delete_requires_human(self):
        self.assertD(req(operation=Operation.DELETE,rollback_ref="snap:1"), GuardDecision.HUMAN_CONFIRM)
    def test_delete_approved_still_not_executed(self):
        out=self.g.evaluate(req(operation=Operation.DELETE,rollback_ref="snap:1",human_approved=True,approval_ref="A4"))
        self.assertEqual(out.decision,GuardDecision.ALLOW_PREPARE); self.assertFalse(out.action_executed); self.assertFalse(out.commit_performed)

    def test_rename_requires_destination(self):
        self.assertD(req(operation=Operation.RENAME,rollback_ref="snap:1"), GuardDecision.HOLD)
    def test_rename_same_hold(self):
        self.assertD(req(operation=Operation.RENAME,successor_path="project/src/a.py",rollback_ref="snap:1"), GuardDecision.HOLD)
    def test_rename_outside_denied(self):
        self.assertD(req(operation=Operation.RENAME,successor_path="other/a.py",rollback_ref="snap:1"), GuardDecision.DENY)
    def test_rename_protected_denied(self):
        self.assertD(req(operation=Operation.RENAME,successor_path="project/baseline/a.py",rollback_ref="snap:1"), GuardDecision.DENY)
    def test_rename_requires_rollback(self):
        self.assertD(req(operation=Operation.RENAME,successor_path="project/src/b.py"), GuardDecision.HOLD)
    def test_rename_requires_human(self):
        self.assertD(req(operation=Operation.RENAME,successor_path="project/src/b.py",rollback_ref="snap:1"), GuardDecision.HUMAN_CONFIRM)
    def test_rename_approved(self):
        self.assertD(req(operation=Operation.RENAME,successor_path="project/src/b.py",rollback_ref="snap:1",human_approved=True,approval_ref="A5"), GuardDecision.ALLOW_PREPARE)

    def test_execute_outside_root_denied(self):
        self.assertD(req(operation=Operation.EXECUTE,target_path="project/src/a.py",requested_execution=True,human_approved=True,approval_ref="A6"), GuardDecision.DENY)
    def test_execute_intent_explicit(self):
        self.assertD(req(operation=Operation.EXECUTE,target_path="tests/test.py",requested_execution=False), GuardDecision.HOLD)
    def test_execute_requires_human(self):
        self.assertD(req(operation=Operation.EXECUTE,target_path="tests/test.py",requested_execution=True), GuardDecision.HUMAN_CONFIRM)
    def test_execute_approved_prepared_only(self):
        out=self.g.evaluate(req(operation=Operation.EXECUTE,target_path="tests/test.py",requested_execution=True,human_approved=True,approval_ref="A6"))
        self.assertEqual(out.decision,GuardDecision.ALLOW_PREPARE); self.assertFalse(out.action_executed)

    def test_bad_source_hash_hold(self):
        self.assertD(req(operation=Operation.MODIFY,source_sha256="bad",proposed_sha256=H1,diff_sha256=H2,successor_path="project/src/a.v2.py"), GuardDecision.HOLD)
    def test_bad_proposed_hash_hold(self):
        self.assertD(req(operation=Operation.CREATE,target_path="sandbox/a",proposed_sha256="bad"), GuardDecision.HOLD)
    def test_bad_diff_hash_hold(self):
        self.assertD(req(operation=Operation.MODIFY,source_sha256=H0,proposed_sha256=H1,diff_sha256="bad",successor_path="project/src/a.v2.py"), GuardDecision.HOLD)

    def test_cache_reuses_exact(self):
        r=req(); a=self.g.evaluate(r); b=self.g.evaluate(r); self.assertFalse(a.cache_reused); self.assertTrue(b.cache_reused)
    def test_cache_diff_approval_state(self):
        a=self.g.evaluate(req(operation=Operation.DELETE,rollback_ref="s"))
        b=self.g.evaluate(req(operation=Operation.DELETE,rollback_ref="s",human_approved=True,approval_ref="A"))
        self.assertNotEqual(a.request_fingerprint,b.request_fingerprint)
    def test_cache_diff_successor(self):
        a=self.g.evaluate(req(operation=Operation.MODIFY,source_sha256=H0,proposed_sha256=H1,diff_sha256=H2,successor_path="project/src/a.v2.py"))
        b=self.g.evaluate(req(operation=Operation.MODIFY,source_sha256=H0,proposed_sha256=H1,diff_sha256=H2,successor_path="project/src/a.v3.py"))
        self.assertNotEqual(a.request_fingerprint,b.request_fingerprint)
    def test_cache_never_authoritative(self):
        self.g.evaluate(req()); b=self.g.evaluate(req()); self.assertFalse(b.authoritative)
    def test_cache_never_commits(self):
        self.g.evaluate(req()); b=self.g.evaluate(req()); self.assertFalse(b.commit_performed)
    def test_clear_cache(self):
        self.g.evaluate(req()); self.assertGreater(self.g.cache_size(),0); self.g.clear_cache(); self.assertEqual(self.g.cache_size(),0)
    def test_deterministic_fingerprint_context_order(self):
        a=req(context={"b":2,"a":1}); b=req(context={"a":1,"b":2}); self.assertEqual(self.g.fingerprint_request(a),self.g.fingerprint_request(b))

    def test_many_allowed_read_paths(self):
        for i in range(10):
            self.assertD(req(target_path=f"project/src/f{i}.py"), GuardDecision.ALLOW_PREPARE)

    def test_many_traversals_denied(self):
        for p in ["../x","project/../x","project/src/../../../x",r"..\x",r"project\..\x"]:
            self.assertD(req(target_path=p), GuardDecision.DENY)

    def test_read_cannot_smuggle_execution(self):
        self.assertD(req(operation=Operation.READ,requested_execution=True), GuardDecision.DENY)

    def test_external_modify_confirm(self):
        self.assertD(req(operation=Operation.MODIFY,source_sha256=H0,proposed_sha256=H1,diff_sha256=H2,successor_path="project/src/a.v2.py",external_side_effect=True), GuardDecision.HUMAN_CONFIRM)

    def test_successor_canonical(self):
        o=self.g.evaluate(req(operation=Operation.MODIFY,source_sha256=H0,proposed_sha256=H1,diff_sha256=H2,successor_path="project/./src/b.py"))
        self.assertEqual(o.canonical_successor,"project/src/b.py")

    def test_result_stable_payload_excludes_time(self):
        o=self.g.evaluate(req()); self.assertNotIn("created_unix_ns",o.stable_payload())

def replay_fingerprint():
    g=DevelopmentGuard(policy())
    corpus=[]
    ops=[Operation.READ,Operation.CREATE,Operation.MODIFY,Operation.DELETE,Operation.RENAME,Operation.EXECUTE]
    for i in range(1000):
        op=ops[i%len(ops)]
        if op==Operation.READ:
            r=req(target_path=f"project/src/r{i%17}.py")
        elif op==Operation.CREATE:
            r=req(operation=op,target_path=f"sandbox/n{i%19}.txt",target_exists=False,proposed_sha256=H1)
        elif op==Operation.MODIFY:
            r=req(operation=op,target_path=f"project/src/m{i%13}.py",target_exists=True,source_sha256=H0,proposed_sha256=H1,diff_sha256=H2,successor_path=f"project/src/m{i%13}.v2.py",diff_bytes=i%900)
        elif op==Operation.DELETE:
            r=req(operation=op,target_path=f"project/tmp/d{i%11}.txt",rollback_ref="snap",human_approved=(i%2==0),approval_ref="A" if i%2==0 else None)
        elif op==Operation.RENAME:
            r=req(operation=op,target_path=f"project/tmp/r{i%7}.txt",successor_path=f"project/tmp/r{i%7}.v2.txt",rollback_ref="snap",human_approved=True,approval_ref="A")
        else:
            r=req(operation=op,target_path=f"tests/t{i%5}.py",requested_execution=True,human_approved=(i%3==0),approval_ref="A" if i%3==0 else None)
        o=g.evaluate(r)
        corpus.append(o.stable_payload())
    raw=json.dumps(corpus,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

if __name__ == "__main__":
    unittest.main()
