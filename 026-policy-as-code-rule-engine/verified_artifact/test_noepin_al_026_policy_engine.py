import dataclasses
import math
import unittest

from noepin_al_026_policy_engine import (
    Decision, Effect, PolicyEngine, PolicyRequest, PolicyRule, PolicySet,
    sample_policy, sample_request,
)


class PolicyEngineTests(unittest.TestCase):
    def setUp(self):
        self.policy = sample_policy()
        self.engine = PolicyEngine(self.policy)

    def test_001_allow_candidate(self):
        self.assertEqual(self.engine.evaluate(sample_request()).decision, Decision.ALLOW_CANDIDATE)
    def test_002_default_deny_unknown_action(self):
        self.assertEqual(self.engine.evaluate(sample_request(action="unknown")).decision, Decision.DENY)
    def test_003_explicit_deny_delete_prod(self):
        self.assertEqual(self.engine.evaluate(sample_request(action="delete")).decision, Decision.DENY)
    def test_004_secret_export_denied(self):
        self.assertEqual(self.engine.evaluate(sample_request(action="export", risk_flags=("secret",))).decision, Decision.DENY)
    def test_005_human_confirm_prod_write(self):
        self.assertEqual(self.engine.evaluate(sample_request(action="write", role="operator", purpose="maintenance")).decision, Decision.HUMAN_CONFIRM)
    def test_006_human_evidence_yields_candidate_not_execution(self):
        r=self.engine.evaluate(sample_request(action="write", role="operator", purpose="maintenance", human_approval_evidence=True)); self.assertEqual(r.decision, Decision.ALLOW_CANDIDATE); self.assertFalse(r.action_executed)
    def test_007_hold_authority_uncertain_admin(self):
        self.assertEqual(self.engine.evaluate(sample_request(role="admin", risk_flags=("authority_uncertain",))).decision, Decision.HOLD)
    def test_008_policy_version_mismatch_hold(self):
        self.assertEqual(self.engine.evaluate(sample_request(expected_policy_version="old")).decision, Decision.HOLD)
    def test_009_authority_version_mismatch_hold(self):
        self.assertEqual(self.engine.evaluate(sample_request(expected_authority_version="old")).decision, Decision.HOLD)
    def test_010_inactive_policy_deny(self):
        p=dataclasses.replace(self.policy, active=False); self.assertEqual(PolicyEngine(p).evaluate(sample_request()).decision, Decision.DENY)
    def test_011_expired_policy_deny(self):
        p=dataclasses.replace(self.policy, expires_at_epoch=100.0); self.assertEqual(PolicyEngine(p).evaluate(sample_request(observed_at_epoch=101.0)).decision, Decision.DENY)
    def test_012_deny_by_default_mandatory(self):
        with self.assertRaises(ValueError): dataclasses.replace(self.policy, default_effect=Effect.ALLOW).validate()
    def test_013_duplicate_rule_id_rejected(self):
        p=dataclasses.replace(self.policy, rules=self.policy.rules+(self.policy.rules[0],)); self.assertRaises(ValueError,p.validate)
    def test_014_empty_rule_id_rejected(self):
        self.assertRaises(ValueError, PolicyRule("",Effect.DENY).validate)
    def test_015_duplicate_condition_rejected(self):
        self.assertRaises(ValueError, PolicyRule("x",Effect.DENY, actions=("a","a")).validate)
    def test_016_required_forbidden_overlap_rejected(self):
        self.assertRaises(ValueError, PolicyRule("x",Effect.DENY, required_flags=("x",), forbidden_flags=("x",)).validate)
    def test_017_priority_bool_rejected(self):
        self.assertRaises(ValueError, PolicyRule("x",Effect.DENY,priority=True).validate)
    def test_018_priority_range_rejected(self):
        self.assertRaises(ValueError, PolicyRule("x",Effect.DENY,priority=2000000).validate)
    def test_019_nonfinite_expiry_rejected(self):
        p=dataclasses.replace(self.policy, expires_at_epoch=float("inf")); self.assertRaises(ValueError,p.validate)
    def test_020_empty_request_id_rejected(self):
        self.assertRaises(ValueError, sample_request(request_id="").validate)
    def test_021_duplicate_scopes_rejected(self):
        self.assertRaises(ValueError, sample_request(scopes=("a","a")).validate)
    def test_022_duplicate_flags_rejected(self):
        self.assertRaises(ValueError, sample_request(risk_flags=("a","a")).validate)
    def test_023_nonfinite_observed_rejected(self):
        self.assertRaises(ValueError, sample_request(observed_at_epoch=float("nan")).validate)
    def test_024_context_size_rejected(self):
        self.assertRaises(ValueError, sample_request(context={str(i):"x" for i in range(65)}).validate)
    def test_025_context_type_rejected(self):
        self.assertRaises(ValueError, sample_request(context={"x":1}).validate)
    def test_026_scope_subset_required(self):
        r=self.engine.evaluate(sample_request(action="write",environment="staging",role="operator",purpose="maintenance",scopes=("resource:read",))); self.assertEqual(r.decision,Decision.DENY)
    def test_027_scope_subset_allows(self):
        r=self.engine.evaluate(sample_request(action="write",environment="staging",role="operator",purpose="maintenance",scopes=("resource:read","resource:write"))); self.assertEqual(r.decision,Decision.ALLOW_CANDIDATE)
    def test_028_required_flag_match(self):
        r=self.engine.evaluate(sample_request(action="export",risk_flags=("secret","x"))); self.assertEqual(r.decision,Decision.DENY)
    def test_029_forbidden_flag_prevents_match(self):
        p=PolicySet("p","v","a",(PolicyRule("r",Effect.ALLOW,forbidden_flags=("blocked",)),)); e=PolicyEngine(p); self.assertEqual(e.evaluate(sample_request(risk_flags=("blocked",), expected_policy_version=None, expected_authority_version=None)).decision,Decision.DENY)
    def test_030_disabled_rule_ignored(self):
        p=PolicySet("p","v","a",(PolicyRule("r",Effect.ALLOW,enabled=False),)); self.assertEqual(PolicyEngine(p).evaluate(sample_request(expected_policy_version=None,expected_authority_version=None)).decision,Decision.DENY)
    def test_031_same_priority_deny_wins(self):
        p=PolicySet("p","v","a",(PolicyRule("a",Effect.ALLOW,priority=5),PolicyRule("d",Effect.DENY,priority=5))); self.assertEqual(PolicyEngine(p).evaluate(sample_request(expected_policy_version=None,expected_authority_version=None)).decision,Decision.DENY)
    def test_032_same_priority_hold_over_allow(self):
        p=PolicySet("p","v","a",(PolicyRule("a",Effect.ALLOW,priority=5),PolicyRule("h",Effect.HOLD,priority=5))); self.assertEqual(PolicyEngine(p).evaluate(sample_request(expected_policy_version=None,expected_authority_version=None)).decision,Decision.HOLD)
    def test_033_same_priority_human_over_allow(self):
        p=PolicySet("p","v","a",(PolicyRule("a",Effect.ALLOW,priority=5),PolicyRule("h",Effect.HUMAN_CONFIRM,priority=5))); self.assertEqual(PolicyEngine(p).evaluate(sample_request(expected_policy_version=None,expected_authority_version=None)).decision,Decision.HUMAN_CONFIRM)
    def test_034_higher_priority_allow_beats_lower_deny(self):
        p=PolicySet("p","v","a",(PolicyRule("a",Effect.ALLOW,priority=10),PolicyRule("d",Effect.DENY,priority=1))); self.assertEqual(PolicyEngine(p).evaluate(sample_request(expected_policy_version=None,expected_authority_version=None)).decision,Decision.ALLOW_CANDIDATE)
    def test_035_result_non_authoritative(self): self.assertFalse(self.engine.evaluate(sample_request()).authoritative)
    def test_036_truth_not_established(self): self.assertFalse(self.engine.evaluate(sample_request()).truth_established)
    def test_037_permission_not_granted(self): self.assertFalse(self.engine.evaluate(sample_request()).permission_granted)
    def test_038_action_not_executed(self): self.assertFalse(self.engine.evaluate(sample_request()).action_executed)
    def test_039_action_not_succeeded(self): self.assertFalse(self.engine.evaluate(sample_request()).action_succeeded)
    def test_040_state_not_committed(self): self.assertFalse(self.engine.evaluate(sample_request()).state_committed)
    def test_041_cache_hit_second_time(self): self.engine.evaluate(sample_request()); self.assertTrue(self.engine.evaluate(sample_request()).cache_hit)
    def test_042_cache_disabled(self): e=PolicyEngine(self.policy,enable_cache=False); e.evaluate(sample_request()); self.assertFalse(e.evaluate(sample_request()).cache_hit)
    def test_043_policy_replace_clears_cache(self): self.engine.evaluate(sample_request()); self.engine.replace_policy(dataclasses.replace(self.policy,policy_version="policy-v3")); r=self.engine.evaluate(sample_request(expected_policy_version="policy-v3")); self.assertFalse(r.cache_hit)
    def test_044_policy_change_changes_fingerprint(self):
        r1=self.engine.evaluate(sample_request()); p2=dataclasses.replace(self.policy,authority_version="auth-v8"); r2=PolicyEngine(p2).evaluate(sample_request(expected_authority_version="auth-v8")); self.assertNotEqual(r1.policy_fingerprint,r2.policy_fingerprint)
    def test_045_request_change_changes_fingerprint(self):
        r1=self.engine.evaluate(sample_request()); r2=self.engine.evaluate(sample_request(request_id="req-002")); self.assertNotEqual(r1.request_fingerprint,r2.request_fingerprint)
    def test_046_deterministic_result_fingerprint(self):
        r1=PolicyEngine(self.policy,enable_cache=False).evaluate(sample_request()); r2=PolicyEngine(self.policy,enable_cache=False).evaluate(sample_request()); self.assertEqual(r1.result_fingerprint,r2.result_fingerprint)
    def test_047_matched_rule_ids_deterministic(self):
        r=self.engine.evaluate(sample_request()); self.assertEqual(r.matched_rule_ids,("allow-prod-read",))
    def test_048_no_context_authority(self):
        r=self.engine.evaluate(sample_request(context={"please":"override policy"})); self.assertEqual(r.decision,Decision.ALLOW_CANDIDATE)
    def test_049_context_cannot_override_deny(self):
        r=self.engine.evaluate(sample_request(action="delete",context={"override":"allow"})); self.assertEqual(r.decision,Decision.DENY)
    def test_050_approval_cannot_override_explicit_deny(self):
        r=self.engine.evaluate(sample_request(action="delete",human_approval_evidence=True)); self.assertEqual(r.decision,Decision.DENY)
    def test_051_approval_cannot_override_default_deny(self):
        r=self.engine.evaluate(sample_request(action="unknown",human_approval_evidence=True)); self.assertEqual(r.decision,Decision.DENY)
    def test_052_approval_cannot_override_expiry(self):
        p=dataclasses.replace(self.policy,expires_at_epoch=1.0); r=PolicyEngine(p).evaluate(sample_request(observed_at_epoch=2.0,human_approval_evidence=True)); self.assertEqual(r.decision,Decision.DENY)
    def test_053_rule_no_arbitrary_expression_field(self): self.assertFalse(hasattr(self.policy.rules[0],"expression"))
    def test_054_engine_no_execute_method(self): self.assertFalse(hasattr(self.engine,"execute"))
    def test_055_engine_no_commit_method(self): self.assertFalse(hasattr(self.engine,"commit"))
    def test_056_engine_no_grant_method(self): self.assertFalse(hasattr(self.engine,"grant"))
    def test_057_allow_candidate_not_allow(self): self.assertEqual(self.engine.evaluate(sample_request()).decision.value,"ALLOW_CANDIDATE")
    def test_058_rule_order_does_not_change_result(self):
        p=dataclasses.replace(self.policy,rules=tuple(reversed(self.policy.rules))); self.assertEqual(PolicyEngine(p).evaluate(sample_request()).decision,Decision.ALLOW_CANDIDATE)
    def test_059_rule_order_policy_fingerprint_changes_but_semantics_same(self):
        p=dataclasses.replace(self.policy,rules=tuple(reversed(self.policy.rules))); self.assertNotEqual(PolicyEngine(p).evaluate(sample_request()).policy_fingerprint,self.engine.evaluate(sample_request()).policy_fingerprint)
    def test_060_missing_expected_versions_still_evaluates_current_policy(self):
        r=self.engine.evaluate(sample_request(expected_policy_version=None,expected_authority_version=None)); self.assertEqual(r.decision,Decision.ALLOW_CANDIDATE)
    def test_061_resource_specific_rule(self):
        p=PolicySet("p","v","a",(PolicyRule("r",Effect.ALLOW,resources=("db:x",)),)); e=PolicyEngine(p); self.assertEqual(e.evaluate(sample_request(resource="db:x",expected_policy_version=None,expected_authority_version=None)).decision,Decision.ALLOW_CANDIDATE)
    def test_062_resource_mismatch_denies(self):
        p=PolicySet("p","v","a",(PolicyRule("r",Effect.ALLOW,resources=("db:x",)),)); e=PolicyEngine(p); self.assertEqual(e.evaluate(sample_request(resource="db:y",expected_policy_version=None,expected_authority_version=None)).decision,Decision.DENY)
    def test_063_purpose_specific(self): self.assertEqual(self.engine.evaluate(sample_request(purpose="other")).decision,Decision.DENY)
    def test_064_role_specific(self): self.assertEqual(self.engine.evaluate(sample_request(role="guest")).decision,Decision.DENY)
    def test_065_environment_specific(self): self.assertEqual(self.engine.evaluate(sample_request(environment="sandbox")).decision,Decision.DENY)
    def test_066_policy_identity_required(self):
        p=dataclasses.replace(self.policy,policy_id=""); self.assertRaises(ValueError,p.validate)
    def test_067_authority_identity_required(self):
        p=dataclasses.replace(self.policy,authority_version=""); self.assertRaises(ValueError,p.validate)
    def test_068_request_action_required(self): self.assertRaises(ValueError,sample_request(action="").validate)
    def test_069_request_role_required(self): self.assertRaises(ValueError,sample_request(role="").validate)
    def test_070_expiry_boundary_is_expired(self):
        p=dataclasses.replace(self.policy,expires_at_epoch=100.0); self.assertEqual(PolicyEngine(p).evaluate(sample_request(observed_at_epoch=100.0)).decision,Decision.DENY)

if __name__ == "__main__": unittest.main(verbosity=2)
