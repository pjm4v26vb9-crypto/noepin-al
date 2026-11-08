import dataclasses
import math
import unittest
from noepin_al_028_quorum_control import *


class QuorumTests(unittest.TestCase):
    def setUp(self):
        self.policy = QuorumPolicy()
        self.c = QuorumControl(self.policy)

    def vote(self, i=1, decision=VoteDecision.APPROVE, confidence=0.9, family=None, group=None, ctx=None, ev=None, verified=True, identity_version="idv1", ballot_version="v1"):
        return Vote(
            voter_id=f"ai-{i}", identity_version=identity_version,
            model_family=(f"fam-{i}" if family is None else family), independence_group=(f"grp-{i}" if group is None else group),
            context_fingerprint=(f"ctx-{i}-abcdef" if ctx is None else ctx), evidence_fingerprint=(f"ev-{i}-abcdef" if ev is None else ev),
            decision=decision, confidence=confidence, verified_identity=verified,
            ballot_version=ballot_version, rationale_fingerprint=f"rat-{i}-abcdef")

    def req(self, votes=None, **kw):
        d=dict(request_id="r1", action_fingerprint="act-abcdef12", target_ref="tool/x", target_version="v1", risk_level=RiskLevel.HIGH,
               votes=tuple(votes or [self.vote(1), self.vote(2), self.vote(3, VoteDecision.ABSTAIN)]),
               expected_policy_version=self.policy.policy_version, expected_authority_version=self.policy.authority_version, context="ctx")
        d.update(kw); return QuorumRequest(**d)

    def test_01_two_of_three_approve(self): self.assertEqual(self.c.evaluate(self.req()).decision,QuorumDecision.QUORUM_APPROVE_CANDIDATE)
    def test_02_two_reject(self): self.assertEqual(self.c.evaluate(self.req([self.vote(1,VoteDecision.REJECT),self.vote(2,VoteDecision.REJECT),self.vote(3)])).decision,QuorumDecision.QUORUM_REJECT_CANDIDATE)
    def test_03_split_hold(self): self.assertEqual(self.c.evaluate(self.req([self.vote(1),self.vote(2,VoteDecision.REJECT),self.vote(3,VoteDecision.ABSTAIN)])).decision,QuorumDecision.HOLD)
    def test_04_critical_approve_human(self): self.assertEqual(self.c.evaluate(self.req(risk_level=RiskLevel.CRITICAL)).decision,QuorumDecision.HUMAN_CONFIRM)
    def test_05_high_approve_candidate(self): self.assertEqual(self.c.evaluate(self.req(risk_level=RiskLevel.HIGH)).decision,QuorumDecision.QUORUM_APPROVE_CANDIDATE)
    def test_06_medium_approve_candidate(self): self.assertEqual(self.c.evaluate(self.req(risk_level=RiskLevel.MEDIUM)).decision,QuorumDecision.QUORUM_APPROVE_CANDIDATE)
    def test_07_low_approve_candidate(self): self.assertEqual(self.c.evaluate(self.req(risk_level=RiskLevel.LOW)).decision,QuorumDecision.QUORUM_APPROVE_CANDIDATE)
    def test_08_duplicate_voter_hold(self): self.assertEqual(self.c.evaluate(self.req([self.vote(1),self.vote(1),self.vote(3)])).decision,QuorumDecision.HOLD)
    def test_09_missing_target_version_hold(self): self.assertEqual(self.c.evaluate(self.req(target_version="")).decision,QuorumDecision.HOLD)
    def test_10_missing_request_deny(self): self.assertEqual(self.c.evaluate(self.req(request_id="")).decision,QuorumDecision.DENY)
    def test_11_missing_action_deny(self): self.assertEqual(self.c.evaluate(self.req(action_fingerprint="")).decision,QuorumDecision.DENY)
    def test_12_missing_target_deny(self): self.assertEqual(self.c.evaluate(self.req(target_ref="")).decision,QuorumDecision.DENY)
    def test_13_policy_version_hold(self): self.assertEqual(self.c.evaluate(self.req(expected_policy_version="old")).decision,QuorumDecision.HOLD)
    def test_14_authority_version_hold(self): self.assertEqual(self.c.evaluate(self.req(expected_authority_version="old")).decision,QuorumDecision.HOLD)
    def test_15_too_few_ballots_hold(self): self.assertEqual(self.c.evaluate(self.req([self.vote(1)])).decision,QuorumDecision.HOLD)
    def test_16_unverified_excluded(self):
        r=self.c.evaluate(self.req([self.vote(1),self.vote(2,verified=False),self.vote(3)])); self.assertIn("unverified voter identities excluded",r.reasons)
    def test_17_too_few_verified_hold(self): self.assertEqual(self.c.evaluate(self.req([self.vote(1),self.vote(2,verified=False)])).decision,QuorumDecision.HOLD)
    def test_18_same_group_hold(self): self.assertEqual(self.c.evaluate(self.req([self.vote(1,group="g"),self.vote(2,group="g"),self.vote(3,VoteDecision.ABSTAIN)])).decision,QuorumDecision.HOLD)
    def test_19_same_family_hold(self): self.assertEqual(self.c.evaluate(self.req([self.vote(1,family="f"),self.vote(2,family="f"),self.vote(3,VoteDecision.ABSTAIN)])).decision,QuorumDecision.HOLD)
    def test_20_same_context_hold_requirement(self): self.assertEqual(self.c.evaluate(self.req([self.vote(1,ctx="ctx-same-aa"),self.vote(2,ctx="ctx-same-aa"),self.vote(3,VoteDecision.ABSTAIN)])).decision,QuorumDecision.HOLD)
    def test_21_correlated_evidence_human(self): self.assertEqual(self.c.evaluate(self.req([self.vote(1,ev="ev-same-aa"),self.vote(2,ev="ev-same-aa"),self.vote(3,VoteDecision.ABSTAIN)])).decision,QuorumDecision.HUMAN_CONFIRM)
    def test_22_low_confidence_approve_not_counted(self): self.assertEqual(self.c.evaluate(self.req([self.vote(1,confidence=.59),self.vote(2),self.vote(3,VoteDecision.ABSTAIN)])).decision,QuorumDecision.HOLD)
    def test_23_low_confidence_reject_not_counted(self): self.assertEqual(self.c.evaluate(self.req([self.vote(1,VoteDecision.REJECT,.59),self.vote(2,VoteDecision.REJECT),self.vote(3,VoteDecision.ABSTAIN)])).decision,QuorumDecision.HOLD)
    def test_24_hold_count(self): self.assertEqual(self.c.evaluate(self.req([self.vote(1),self.vote(2),self.vote(3,VoteDecision.HOLD)])).hold_count,1)
    def test_25_abstain_count(self): self.assertEqual(self.c.evaluate(self.req()).abstain_count,1)
    def test_26_approve_count(self): self.assertEqual(self.c.evaluate(self.req()).approve_count,2)
    def test_27_reject_count(self): self.assertEqual(self.c.evaluate(self.req([self.vote(1,VoteDecision.REJECT),self.vote(2,VoteDecision.REJECT),self.vote(3)])).reject_count,2)
    def test_28_group_count(self): self.assertEqual(self.c.evaluate(self.req()).independent_group_count,2)
    def test_29_family_count(self): self.assertEqual(self.c.evaluate(self.req()).distinct_model_family_count,2)
    def test_30_context_count(self): self.assertEqual(self.c.evaluate(self.req()).distinct_context_count,2)
    def test_31_evidence_count(self): self.assertEqual(self.c.evaluate(self.req()).distinct_evidence_count,2)
    def test_32_not_authoritative(self): self.assertFalse(self.c.evaluate(self.req()).authoritative)
    def test_33_truth_false(self): self.assertFalse(self.c.evaluate(self.req()).truth_established)
    def test_34_permission_false(self): self.assertFalse(self.c.evaluate(self.req()).permission_granted)
    def test_35_action_executed_false(self): self.assertFalse(self.c.evaluate(self.req()).action_executed)
    def test_36_action_succeeded_false(self): self.assertFalse(self.c.evaluate(self.req()).action_succeeded)
    def test_37_state_committed_false(self): self.assertFalse(self.c.evaluate(self.req()).state_committed)
    def test_38_cache_same_result(self): self.assertEqual(self.c.evaluate(self.req()),self.c.evaluate(self.req()))
    def test_39_cache_bypass_same_result(self): self.assertEqual(self.c.evaluate(self.req()),self.c.evaluate(self.req(),use_cache=False))
    def test_40_clear_cache(self): self.c.evaluate(self.req()); self.c.clear_cache(); self.assertEqual(self.c._cache,{})
    def test_41_vote_order_same_fp(self):
        a=self.c.evaluate(self.req([self.vote(1),self.vote(2),self.vote(3,VoteDecision.ABSTAIN)])); b=self.c.evaluate(self.req([self.vote(3,VoteDecision.ABSTAIN),self.vote(2),self.vote(1)],request_id="r1")); self.assertEqual(a.request_fingerprint,b.request_fingerprint)
    def test_42_action_change_fp(self): self.assertNotEqual(self.c.evaluate(self.req()).request_fingerprint,self.c.evaluate(self.req(action_fingerprint="act-xyz98765")).request_fingerprint)
    def test_43_target_version_change_fp(self): self.assertNotEqual(self.c.evaluate(self.req()).request_fingerprint,self.c.evaluate(self.req(target_version="v2")).request_fingerprint)
    def test_44_identity_version_change_fp(self): self.assertNotEqual(self.c.evaluate(self.req()).request_fingerprint,self.c.evaluate(self.req([self.vote(1,identity_version="idv2"),self.vote(2),self.vote(3,VoteDecision.ABSTAIN)])).request_fingerprint)
    def test_45_ballot_version_change_fp(self): self.assertNotEqual(self.c.evaluate(self.req()).request_fingerprint,self.c.evaluate(self.req([self.vote(1,ballot_version="v2"),self.vote(2),self.vote(3,VoteDecision.ABSTAIN)])).request_fingerprint)
    def test_46_context_change_fp(self): self.assertNotEqual(self.c.evaluate(self.req()).request_fingerprint,self.c.evaluate(self.req(context="other")).request_fingerprint)
    def test_47_confidence_change_fp(self): self.assertNotEqual(self.c.evaluate(self.req()).request_fingerprint,self.c.evaluate(self.req([self.vote(1,confidence=.8),self.vote(2),self.vote(3,VoteDecision.ABSTAIN)])).request_fingerprint)
    def test_48_decision_change_fp(self): self.assertNotEqual(self.c.evaluate(self.req()).request_fingerprint,self.c.evaluate(self.req([self.vote(1,VoteDecision.REJECT),self.vote(2),self.vote(3,VoteDecision.ABSTAIN)])).request_fingerprint)
    def test_49_nan_deny(self): self.assertEqual(self.c.evaluate(self.req([self.vote(1,confidence=float('nan')),self.vote(2),self.vote(3)])).decision,QuorumDecision.DENY)
    def test_50_inf_deny(self): self.assertEqual(self.c.evaluate(self.req([self.vote(1,confidence=float('inf')),self.vote(2),self.vote(3)])).decision,QuorumDecision.DENY)
    def test_51_negative_confidence_deny(self): self.assertEqual(self.c.evaluate(self.req([self.vote(1,confidence=-.1),self.vote(2),self.vote(3)])).decision,QuorumDecision.DENY)
    def test_52_over_confidence_deny(self): self.assertEqual(self.c.evaluate(self.req([self.vote(1,confidence=1.1),self.vote(2),self.vote(3)])).decision,QuorumDecision.DENY)
    def test_53_invalid_context_fp_hold(self): self.assertEqual(self.c.evaluate(self.req([self.vote(1,ctx=""),self.vote(2),self.vote(3)])).decision,QuorumDecision.HOLD)
    def test_54_invalid_evidence_fp_hold(self): self.assertEqual(self.c.evaluate(self.req([self.vote(1,ev=""),self.vote(2),self.vote(3)])).decision,QuorumDecision.HOLD)
    def test_55_missing_family_hold(self): self.assertEqual(self.c.evaluate(self.req([self.vote(1,family=""),self.vote(2),self.vote(3)])).decision,QuorumDecision.HOLD)
    def test_56_missing_group_hold(self): self.assertEqual(self.c.evaluate(self.req([self.vote(1,group=""),self.vote(2),self.vote(3)])).decision,QuorumDecision.HOLD)
    def test_57_missing_identity_version_hold(self): self.assertEqual(self.c.evaluate(self.req([self.vote(1,identity_version=""),self.vote(2),self.vote(3)])).decision,QuorumDecision.HOLD)
    def test_58_all_abstain_hold(self): self.assertEqual(self.c.evaluate(self.req([self.vote(1,VoteDecision.ABSTAIN),self.vote(2,VoteDecision.ABSTAIN),self.vote(3,VoteDecision.ABSTAIN)])).decision,QuorumDecision.HOLD)
    def test_59_all_hold_hold(self): self.assertEqual(self.c.evaluate(self.req([self.vote(1,VoteDecision.HOLD),self.vote(2,VoteDecision.HOLD),self.vote(3,VoteDecision.HOLD)])).decision,QuorumDecision.HOLD)
    def test_60_three_approve_candidate(self): self.assertEqual(self.c.evaluate(self.req([self.vote(1),self.vote(2),self.vote(3)])).approve_count,3)
    def test_61_three_reject_candidate(self): self.assertEqual(self.c.evaluate(self.req([self.vote(1,VoteDecision.REJECT),self.vote(2,VoteDecision.REJECT),self.vote(3,VoteDecision.REJECT)])).reject_count,3)
    def test_62_critical_two_reject_rejects(self): self.assertEqual(self.c.evaluate(self.req([self.vote(1,VoteDecision.REJECT),self.vote(2,VoteDecision.REJECT),self.vote(3)],risk_level=RiskLevel.CRITICAL)).decision,QuorumDecision.QUORUM_REJECT_CANDIDATE)
    def test_63_custom_three_quorum(self):
        c=QuorumControl(dataclasses.replace(self.policy,required_quorum=3,min_independent_groups=3,min_distinct_model_families=3,min_distinct_contexts=3)); self.assertEqual(c.evaluate(self.req([self.vote(1),self.vote(2),self.vote(3)])).decision,QuorumDecision.QUORUM_APPROVE_CANDIDATE)
    def test_64_custom_three_quorum_two_insufficient(self):
        c=QuorumControl(dataclasses.replace(self.policy,required_quorum=3,min_independent_groups=2,min_distinct_model_families=2,min_distinct_contexts=2)); self.assertEqual(c.evaluate(self.req([self.vote(1),self.vote(2)])).decision,QuorumDecision.HOLD)
    def test_65_human_confirm_does_not_grant(self): self.assertFalse(self.c.evaluate(self.req(risk_level=RiskLevel.CRITICAL)).permission_granted)
    def test_66_reject_candidate_not_authority(self): self.assertFalse(self.c.evaluate(self.req([self.vote(1,VoteDecision.REJECT),self.vote(2,VoteDecision.REJECT),self.vote(3)])).authoritative)
    def test_67_approve_candidate_not_success(self): self.assertFalse(self.c.evaluate(self.req()).action_succeeded)
    def test_68_same_evidence_flag(self): self.assertTrue(self.c.evaluate(self.req([self.vote(1,ev="same-ev12"),self.vote(2,ev="same-ev12"),self.vote(3,VoteDecision.ABSTAIN)])).correlated_evidence_detected)
    def test_69_unique_evidence_no_flag(self): self.assertFalse(self.c.evaluate(self.req()).correlated_evidence_detected)
    def test_70_unique_context_no_flag(self): self.assertFalse(self.c.evaluate(self.req()).correlated_context_detected)
    def test_71_invalid_policy_quorum_deny(self):
        c=QuorumControl(dataclasses.replace(self.policy,required_quorum=0)); self.assertEqual(c.evaluate(self.req()).decision,QuorumDecision.DENY)
    def test_72_invalid_policy_confidence_deny(self):
        c=QuorumControl(dataclasses.replace(self.policy,min_confidence=2.0)); self.assertEqual(c.evaluate(self.req()).decision,QuorumDecision.DENY)

if __name__ == "__main__": unittest.main()
