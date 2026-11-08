from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, Iterable, Optional, Tuple

CREATOR = "NOEPIN / のえぴん"
VERSION = "2.0.0-successor.20261102"


class VoteDecision(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    HOLD = "HOLD"
    ABSTAIN = "ABSTAIN"


class QuorumDecision(str, Enum):
    QUORUM_APPROVE_CANDIDATE = "QUORUM_APPROVE_CANDIDATE"
    QUORUM_REJECT_CANDIDATE = "QUORUM_REJECT_CANDIDATE"
    HUMAN_CONFIRM = "HUMAN_CONFIRM"
    HOLD = "HOLD"
    DENY = "DENY"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class QuorumPolicy:
    policy_version: str = "quorum-policy-v2"
    authority_version: str = "authority-v1"
    required_quorum: int = 2
    min_independent_groups: int = 2
    min_distinct_model_families: int = 2
    min_distinct_contexts: int = 2
    min_confidence: float = 0.60
    critical_requires_human_confirmation: bool = True
    reject_on_any_verified_reject_for_critical: bool = False
    detect_correlated_context: bool = True
    detect_correlated_evidence: bool = True


@dataclass(frozen=True)
class Vote:
    voter_id: str
    identity_version: str
    model_family: str
    independence_group: str
    context_fingerprint: str
    evidence_fingerprint: str
    decision: VoteDecision
    confidence: float
    verified_identity: bool = True
    ballot_version: str = "v1"
    rationale_fingerprint: str = ""


@dataclass(frozen=True)
class QuorumRequest:
    request_id: str
    action_fingerprint: str
    target_ref: str
    target_version: str
    risk_level: RiskLevel
    votes: Tuple[Vote, ...]
    expected_policy_version: str = "quorum-policy-v2"
    expected_authority_version: str = "authority-v1"
    context: str = ""


@dataclass(frozen=True)
class QuorumResult:
    decision: QuorumDecision
    reasons: Tuple[str, ...]
    counted_vote_ids: Tuple[str, ...]
    approve_count: int
    reject_count: int
    hold_count: int
    abstain_count: int
    independent_group_count: int
    distinct_model_family_count: int
    distinct_context_count: int
    distinct_evidence_count: int
    correlated_context_detected: bool
    correlated_evidence_detected: bool
    request_fingerprint: Optional[str]
    authoritative: bool = False
    truth_established: bool = False
    permission_granted: bool = False
    action_executed: bool = False
    action_succeeded: bool = False
    state_committed: bool = False


def _canonical_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _fingerprint(value) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _valid_fp(value: str) -> bool:
    return bool(value) and len(value) >= 8 and all(c.isalnum() or c in "-_" for c in value)


class QuorumControl:
    """Pure quorum evaluator. It never grants permission or executes an action."""

    def __init__(self, policy: QuorumPolicy = QuorumPolicy()):
        self.policy = policy
        self._cache: Dict[str, QuorumResult] = {}

    def clear_cache(self) -> None:
        self._cache.clear()

    def _deny(self, reason: str) -> QuorumResult:
        return QuorumResult(QuorumDecision.DENY, (reason,), tuple(), 0, 0, 0, 0, 0, 0, 0, 0, False, False, None)

    def _hold(self, reason: str) -> QuorumResult:
        return QuorumResult(QuorumDecision.HOLD, (reason,), tuple(), 0, 0, 0, 0, 0, 0, 0, 0, False, False, None)

    def _validate(self, request: QuorumRequest) -> Optional[QuorumResult]:
        if not request.request_id or not request.action_fingerprint or not request.target_ref:
            return self._deny("missing request/action/target identity")
        if not request.target_version:
            return self._hold("missing target_version")
        if request.expected_policy_version != self.policy.policy_version:
            return self._hold("policy_version mismatch")
        if request.expected_authority_version != self.policy.authority_version:
            return self._hold("authority_version mismatch")
        if self.policy.required_quorum < 1 or self.policy.min_independent_groups < 1:
            return self._deny("invalid quorum policy")
        if self.policy.min_confidence < 0 or self.policy.min_confidence > 1:
            return self._deny("invalid confidence policy")
        if len(request.votes) < self.policy.required_quorum:
            return self._hold("insufficient ballots for quorum")
        seen = set()
        for vote in request.votes:
            if not vote.voter_id or not vote.identity_version or not vote.model_family or not vote.independence_group:
                return self._hold("incomplete voter identity metadata")
            if vote.voter_id in seen:
                return self._hold("duplicate voter_id")
            seen.add(vote.voter_id)
            if not _valid_fp(vote.context_fingerprint) or not _valid_fp(vote.evidence_fingerprint):
                return self._hold("missing or invalid context/evidence fingerprint")
            if not isinstance(vote.confidence, (int, float)) or not math.isfinite(float(vote.confidence)):
                return self._deny("non-finite confidence")
            if vote.confidence < 0 or vote.confidence > 1:
                return self._deny("confidence out of range")
        return None

    def _request_key(self, request: QuorumRequest) -> str:
        material = {
            "policy": asdict(self.policy),
            "request": {
                "request_id": request.request_id,
                "action_fingerprint": request.action_fingerprint,
                "target_ref": request.target_ref,
                "target_version": request.target_version,
                "risk_level": request.risk_level.value,
                "expected_policy_version": request.expected_policy_version,
                "expected_authority_version": request.expected_authority_version,
                "context": request.context,
                "votes": [
                    {
                        **asdict(v),
                        "decision": v.decision.value,
                    }
                    for v in sorted(request.votes, key=lambda x: x.voter_id)
                ],
            },
        }
        return _fingerprint(material)

    def evaluate(self, request: QuorumRequest, *, use_cache: bool = True) -> QuorumResult:
        invalid = self._validate(request)
        if invalid is not None:
            return invalid

        key = self._request_key(request)
        if use_cache and key in self._cache:
            return self._cache[key]

        verified_votes = tuple(v for v in request.votes if v.verified_identity)
        if len(verified_votes) < self.policy.required_quorum:
            result = self._hold("insufficient verified voter identities")
            return result

        eligible = tuple(v for v in verified_votes if v.confidence >= self.policy.min_confidence or v.decision in (VoteDecision.HOLD, VoteDecision.ABSTAIN))
        decisive = tuple(v for v in eligible if v.decision in (VoteDecision.APPROVE, VoteDecision.REJECT))
        approve = tuple(v for v in decisive if v.decision == VoteDecision.APPROVE)
        reject = tuple(v for v in decisive if v.decision == VoteDecision.REJECT)
        holds = tuple(v for v in eligible if v.decision == VoteDecision.HOLD)
        abstains = tuple(v for v in eligible if v.decision == VoteDecision.ABSTAIN)

        independent_groups = {v.independence_group for v in decisive}
        model_families = {v.model_family for v in decisive}
        contexts = {v.context_fingerprint for v in decisive}
        evidences = {v.evidence_fingerprint for v in decisive}
        correlated_context = len(decisive) > 1 and len(contexts) < len(decisive)
        correlated_evidence = len(decisive) > 1 and len(evidences) < len(decisive)

        reasons = []
        final = QuorumDecision.HOLD

        if not decisive:
            reasons.append("no decisive verified ballots")
        elif len(independent_groups) < self.policy.min_independent_groups:
            reasons.append("independence quorum not satisfied")
        elif len(model_families) < self.policy.min_distinct_model_families:
            reasons.append("model-family diversity requirement not satisfied")
        elif len(contexts) < self.policy.min_distinct_contexts:
            reasons.append("independent-context requirement not satisfied")
        elif self.policy.detect_correlated_context and correlated_context:
            final = QuorumDecision.HUMAN_CONFIRM
            reasons.append("correlated context detected")
        elif self.policy.detect_correlated_evidence and correlated_evidence:
            final = QuorumDecision.HUMAN_CONFIRM
            reasons.append("correlated evidence detected")
        elif len(reject) >= self.policy.required_quorum:
            final = QuorumDecision.QUORUM_REJECT_CANDIDATE
            reasons.append("independent reject quorum candidate reached")
        elif len(approve) >= self.policy.required_quorum:
            if request.risk_level == RiskLevel.CRITICAL and self.policy.critical_requires_human_confirmation:
                final = QuorumDecision.HUMAN_CONFIRM
                reasons.append("critical-risk approval quorum requires human confirmation")
            else:
                final = QuorumDecision.QUORUM_APPROVE_CANDIDATE
                reasons.append("independent approval quorum candidate reached")
        elif request.risk_level == RiskLevel.CRITICAL and self.policy.reject_on_any_verified_reject_for_critical and reject:
            final = QuorumDecision.QUORUM_REJECT_CANDIDATE
            reasons.append("critical-risk policy treats verified reject as reject candidate")
        else:
            reasons.append("decisive quorum not reached")

        if holds:
            reasons.append(f"{len(holds)} hold ballot(s) present")
        if abstains:
            reasons.append(f"{len(abstains)} abstain ballot(s) present")
        if len(verified_votes) != len(request.votes):
            reasons.append("unverified voter identities excluded")

        result = QuorumResult(
            decision=final,
            reasons=tuple(reasons),
            counted_vote_ids=tuple(sorted(v.voter_id for v in eligible)),
            approve_count=len(approve),
            reject_count=len(reject),
            hold_count=len(holds),
            abstain_count=len(abstains),
            independent_group_count=len(independent_groups),
            distinct_model_family_count=len(model_families),
            distinct_context_count=len(contexts),
            distinct_evidence_count=len(evidences),
            correlated_context_detected=correlated_context,
            correlated_evidence_detected=correlated_evidence,
            request_fingerprint=key,
        )
        if use_cache:
            self._cache[key] = result
        return result


__all__ = [
    "CREATOR", "VERSION", "VoteDecision", "QuorumDecision", "RiskLevel",
    "QuorumPolicy", "Vote", "QuorumRequest", "QuorumResult", "QuorumControl"
]
