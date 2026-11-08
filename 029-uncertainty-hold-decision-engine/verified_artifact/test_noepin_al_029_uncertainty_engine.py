import dataclasses
import math
import unittest

from noepin_al_029_uncertainty_engine import (
    Decision, ImpactLevel, UncertaintyHoldEngine, UncertaintyPolicy, UncertaintyRequest
)


class TestUncertaintyHoldEngine(unittest.TestCase):
    def setUp(self):
        self.p = UncertaintyPolicy()
        self.e = UncertaintyHoldEngine(self.p)

    def req(self, **kw):
        base = dict(
            request_id="r1", target_ref="target-a", target_version="v1",
            evidence_binding_fingerprint="evidence-abcdef12", context_fingerprint="context-abcdef12",
            confidence=.90, evidence_coverage=.90, contradiction_score=.05, freshness_score=.95,
            unknown_count=0, ambiguity_count=0, missing_required_fields=tuple(),
            impact_level=ImpactLevel.MEDIUM, irreversible=False,
            user_clarification_available=True, research_available=True, human_review_available=True,
            expected_policy_version="uncertainty-policy-v2", expected_authority_version="authority-v1"
        )
        base.update(kw)
        return UncertaintyRequest(**base)

    def test_01_normal_candidate(self): self.assertEqual(self.e.evaluate(self.req()).decision, Decision.PROCEED_CANDIDATE)
    def test_02_missing_field_ask(self): self.assertEqual(self.e.evaluate(self.req(missing_required_fields=("account_id",))).decision, Decision.ASK_USER)
    def test_03_missing_field_research_without_user(self): self.assertEqual(self.e.evaluate(self.req(missing_required_fields=("account_id",),user_clarification_available=False)).decision, Decision.RESEARCH_REQUIRED)
    def test_04_missing_field_hold_no_paths(self): self.assertEqual(self.e.evaluate(self.req(missing_required_fields=("account_id",),user_clarification_available=False,research_available=False)).decision, Decision.HOLD)
    def test_05_conflict_research(self): self.assertEqual(self.e.evaluate(self.req(contradiction_score=.21)).decision, Decision.RESEARCH_REQUIRED)
    def test_06_conflict_human_without_research(self): self.assertEqual(self.e.evaluate(self.req(contradiction_score=.21,research_available=False)).decision, Decision.HUMAN_CONFIRM)
    def test_07_conflict_hold_no_review(self): self.assertEqual(self.e.evaluate(self.req(contradiction_score=.21,research_available=False,human_review_available=False)).decision, Decision.HOLD)
    def test_08_stale_research(self): self.assertEqual(self.e.evaluate(self.req(freshness_score=.69)).decision, Decision.RESEARCH_REQUIRED)
    def test_09_stale_hold(self): self.assertEqual(self.e.evaluate(self.req(freshness_score=.69,research_available=False)).decision, Decision.HOLD)
    def test_10_low_evidence_research(self): self.assertEqual(self.e.evaluate(self.req(evidence_coverage=.74)).decision, Decision.RESEARCH_REQUIRED)
    def test_11_low_evidence_ask_without_research(self): self.assertEqual(self.e.evaluate(self.req(evidence_coverage=.74,research_available=False)).decision, Decision.ASK_USER)
    def test_12_low_evidence_hold_no_paths(self): self.assertEqual(self.e.evaluate(self.req(evidence_coverage=.74,research_available=False,user_clarification_available=False)).decision, Decision.HOLD)
    def test_13_low_confidence_ask_on_unknown(self): self.assertEqual(self.e.evaluate(self.req(confidence=.81,unknown_count=1)).decision, Decision.ASK_USER)
    def test_14_low_confidence_research_no_unknown(self): self.assertEqual(self.e.evaluate(self.req(confidence=.81)).decision, Decision.RESEARCH_REQUIRED)
    def test_15_low_confidence_human_no_research(self): self.assertEqual(self.e.evaluate(self.req(confidence=.81,research_available=False,user_clarification_available=False)).decision, Decision.HUMAN_CONFIRM)
    def test_16_low_confidence_hold_no_paths(self): self.assertEqual(self.e.evaluate(self.req(confidence=.81,research_available=False,user_clarification_available=False,human_review_available=False)).decision, Decision.HOLD)
    def test_17_critical_human(self): self.assertEqual(self.e.evaluate(self.req(impact_level=ImpactLevel.CRITICAL)).decision, Decision.HUMAN_CONFIRM)
    def test_18_critical_hold_no_human(self): self.assertEqual(self.e.evaluate(self.req(impact_level=ImpactLevel.CRITICAL,human_review_available=False)).decision, Decision.HOLD)
    def test_19_irreversible_human(self): self.assertEqual(self.e.evaluate(self.req(irreversible=True)).decision, Decision.HUMAN_CONFIRM)
    def test_20_high_margin_human(self): self.assertEqual(self.e.evaluate(self.req(impact_level=ImpactLevel.HIGH,confidence=.91)).decision, Decision.HUMAN_CONFIRM)
    def test_21_high_strong_candidate(self): self.assertEqual(self.e.evaluate(self.req(impact_level=ImpactLevel.HIGH,confidence=.95,evidence_coverage=.95)).decision, Decision.PROCEED_CANDIDATE)
    def test_22_policy_mismatch_hold(self): self.assertEqual(self.e.evaluate(self.req(expected_policy_version="old")).decision, Decision.HOLD)
    def test_23_authority_mismatch_hold(self): self.assertEqual(self.e.evaluate(self.req(expected_authority_version="old")).decision, Decision.HOLD)
    def test_24_missing_target_version_hold(self): self.assertEqual(self.e.evaluate(self.req(target_version="")).decision, Decision.HOLD)
    def test_25_missing_request_deny(self): self.assertEqual(self.e.evaluate(self.req(request_id="")).decision, Decision.DENY)
    def test_26_missing_target_deny(self): self.assertEqual(self.e.evaluate(self.req(target_ref="")).decision, Decision.DENY)
    def test_27_invalid_evidence_fp_hold(self): self.assertEqual(self.e.evaluate(self.req(evidence_binding_fingerprint="")).decision, Decision.HOLD)
    def test_28_invalid_context_fp_hold(self): self.assertEqual(self.e.evaluate(self.req(context_fingerprint="")).decision, Decision.HOLD)
    def test_29_nan_confidence_deny(self): self.assertEqual(self.e.evaluate(self.req(confidence=float("nan"))).decision, Decision.DENY)
    def test_30_inf_confidence_deny(self): self.assertEqual(self.e.evaluate(self.req(confidence=float("inf"))).decision, Decision.DENY)
    def test_31_confidence_negative_deny(self): self.assertEqual(self.e.evaluate(self.req(confidence=-.1)).decision, Decision.DENY)
    def test_32_confidence_over_deny(self): self.assertEqual(self.e.evaluate(self.req(confidence=1.1)).decision, Decision.DENY)
    def test_33_nan_evidence_deny(self): self.assertEqual(self.e.evaluate(self.req(evidence_coverage=float("nan"))).decision, Decision.DENY)
    def test_34_conflict_over_deny(self): self.assertEqual(self.e.evaluate(self.req(contradiction_score=1.1)).decision, Decision.DENY)
    def test_35_freshness_negative_deny(self): self.assertEqual(self.e.evaluate(self.req(freshness_score=-.1)).decision, Decision.DENY)
    def test_36_negative_unknown_deny(self): self.assertEqual(self.e.evaluate(self.req(unknown_count=-1)).decision, Decision.DENY)
    def test_37_negative_ambiguity_deny(self): self.assertEqual(self.e.evaluate(self.req(ambiguity_count=-1)).decision, Decision.DENY)
    def test_38_invalid_policy_threshold_deny(self):
        e=UncertaintyHoldEngine(dataclasses.replace(self.p,min_confidence_proceed=2.0)); self.assertEqual(e.evaluate(self.req()).decision, Decision.DENY)
    def test_39_not_authoritative(self): self.assertFalse(self.e.evaluate(self.req()).authoritative)
    def test_40_truth_false(self): self.assertFalse(self.e.evaluate(self.req()).truth_established)
    def test_41_known_false(self): self.assertFalse(self.e.evaluate(self.req()).known_established)
    def test_42_research_completed_false(self): self.assertFalse(self.e.evaluate(self.req(freshness_score=.5)).research_completed)
    def test_43_human_approval_false(self): self.assertFalse(self.e.evaluate(self.req(impact_level=ImpactLevel.CRITICAL)).human_approval_granted)
    def test_44_permission_false(self): self.assertFalse(self.e.evaluate(self.req()).permission_granted)
    def test_45_action_executed_false(self): self.assertFalse(self.e.evaluate(self.req()).action_executed)
    def test_46_action_succeeded_false(self): self.assertFalse(self.e.evaluate(self.req()).action_succeeded)
    def test_47_state_committed_false(self): self.assertFalse(self.e.evaluate(self.req()).state_committed)
    def test_48_cache_same(self): self.assertEqual(self.e.evaluate(self.req()), self.e.evaluate(self.req()))
    def test_49_cache_bypass_same(self): self.assertEqual(self.e.evaluate(self.req()), self.e.evaluate(self.req(),use_cache=False))
    def test_50_clear_cache(self): self.e.evaluate(self.req()); self.e.clear_cache(); self.assertEqual(self.e._cache,{})
    def test_51_target_version_changes_fp(self): self.assertNotEqual(self.e.evaluate(self.req()).request_fingerprint,self.e.evaluate(self.req(target_version="v2")).request_fingerprint)
    def test_52_evidence_binding_changes_fp(self): self.assertNotEqual(self.e.evaluate(self.req()).request_fingerprint,self.e.evaluate(self.req(evidence_binding_fingerprint="evidence-xyz98765")).request_fingerprint)
    def test_53_context_changes_fp(self): self.assertNotEqual(self.e.evaluate(self.req()).request_fingerprint,self.e.evaluate(self.req(context_fingerprint="context-xyz98765")).request_fingerprint)
    def test_54_confidence_changes_fp(self): self.assertNotEqual(self.e.evaluate(self.req()).request_fingerprint,self.e.evaluate(self.req(confidence=.91)).request_fingerprint)
    def test_55_evidence_changes_fp(self): self.assertNotEqual(self.e.evaluate(self.req()).request_fingerprint,self.e.evaluate(self.req(evidence_coverage=.91)).request_fingerprint)
    def test_56_conflict_changes_fp(self): self.assertNotEqual(self.e.evaluate(self.req()).request_fingerprint,self.e.evaluate(self.req(contradiction_score=.06)).request_fingerprint)
    def test_57_freshness_changes_fp(self): self.assertNotEqual(self.e.evaluate(self.req()).request_fingerprint,self.e.evaluate(self.req(freshness_score=.96)).request_fingerprint)
    def test_58_unknown_changes_fp(self): self.assertNotEqual(self.e.evaluate(self.req()).request_fingerprint,self.e.evaluate(self.req(unknown_count=1)).request_fingerprint)
    def test_59_ambiguity_changes_fp(self): self.assertNotEqual(self.e.evaluate(self.req()).request_fingerprint,self.e.evaluate(self.req(ambiguity_count=1)).request_fingerprint)
    def test_60_missing_order_same_fp(self):
        a=self.e.evaluate(self.req(missing_required_fields=("b","a"))); b=self.e.evaluate(self.req(missing_required_fields=("a","b"))); self.assertEqual(a.request_fingerprint,b.request_fingerprint)
    def test_61_score_present(self): self.assertIsInstance(self.e.evaluate(self.req()).uncertainty_score,float)
    def test_62_score_in_range(self): self.assertGreaterEqual(self.e.evaluate(self.req()).uncertainty_score,0); self.assertLessEqual(self.e.evaluate(self.req()).uncertainty_score,1)
    def test_63_worse_confidence_higher_score(self): self.assertGreater(self.e.evaluate(self.req(confidence=.83),use_cache=False).uncertainty_score,self.e.evaluate(self.req(confidence=.95),use_cache=False).uncertainty_score)
    def test_64_worse_evidence_higher_score(self): self.assertGreater(self.e.evaluate(self.req(evidence_coverage=.76),use_cache=False).uncertainty_score,self.e.evaluate(self.req(evidence_coverage=.95),use_cache=False).uncertainty_score)
    def test_65_more_conflict_higher_score(self): self.assertGreater(self.e.evaluate(self.req(contradiction_score=.19),use_cache=False).uncertainty_score,self.e.evaluate(self.req(contradiction_score=.01),use_cache=False).uncertainty_score)
    def test_66_more_unknown_higher_score(self): self.assertGreater(self.e.evaluate(self.req(unknown_count=3),use_cache=False).uncertainty_score,self.e.evaluate(self.req(unknown_count=0),use_cache=False).uncertainty_score)
    def test_67_duplicate_missing_fields_normalized(self):
        r=self.e.evaluate(self.req(missing_required_fields=("x","x"," y "))); self.assertIn("required information missing: x,y",r.reasons[0])
    def test_68_missing_empty_ignored(self): self.assertEqual(self.e.evaluate(self.req(missing_required_fields=("", "  "))).decision,Decision.PROCEED_CANDIDATE)
    def test_69_unknown_reason_recorded(self): self.assertIn("unknown_count=2", self.e.evaluate(self.req(unknown_count=2,confidence=.81)).reasons)
    def test_70_ambiguity_reason_recorded(self): self.assertIn("ambiguity_count=2", self.e.evaluate(self.req(ambiguity_count=2,confidence=.81)).reasons)
    def test_71_research_required_not_completed(self): self.assertFalse(self.e.evaluate(self.req(freshness_score=.1)).research_completed)
    def test_72_human_confirm_not_approval(self): self.assertFalse(self.e.evaluate(self.req(impact_level=ImpactLevel.CRITICAL)).human_approval_granted)
    def test_73_candidate_not_success(self): self.assertFalse(self.e.evaluate(self.req()).action_succeeded)
    def test_74_ask_user_not_known(self): self.assertFalse(self.e.evaluate(self.req(missing_required_fields=("x",))).known_established)

if __name__ == "__main__":
    unittest.main()
