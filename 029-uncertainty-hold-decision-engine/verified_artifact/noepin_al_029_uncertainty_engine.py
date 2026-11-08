from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Dict, Optional, Tuple

CREATOR = "NOEPIN / のえぴん"
VERSION = "2.0.0-successor.20261102"


class Decision(str, Enum):
    PROCEED_CANDIDATE = "PROCEED_CANDIDATE"
    ASK_USER = "ASK_USER"
    RESEARCH_REQUIRED = "RESEARCH_REQUIRED"
    HUMAN_CONFIRM = "HUMAN_CONFIRM"
    HOLD = "HOLD"
    DENY = "DENY"


class ImpactLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class UncertaintyPolicy:
    policy_version: str = "uncertainty-policy-v2"
    authority_version: str = "authority-v1"
    min_confidence_proceed: float = 0.82
    min_evidence_coverage: float = 0.75
    min_freshness_score: float = 0.70
    max_contradiction_score: float = 0.20
    high_impact_min_confidence: float = 0.92
    high_impact_min_evidence: float = 0.90
    critical_always_human_confirm: bool = True
    irreversible_always_human_confirm: bool = True
    ask_user_on_missing_fields: bool = True
    research_on_stale_or_conflicted: bool = True


@dataclass(frozen=True)
class UncertaintyRequest:
    request_id: str
    target_ref: str
    target_version: str
    evidence_binding_fingerprint: str
    confidence: float
    evidence_coverage: float
    contradiction_score: float
    freshness_score: float
    unknown_count: int
    ambiguity_count: int
    missing_required_fields: Tuple[str, ...] = tuple()
    impact_level: ImpactLevel = ImpactLevel.MEDIUM
    irreversible: bool = False
    user_clarification_available: bool = True
    research_available: bool = True
    human_review_available: bool = True
    expected_policy_version: str = "uncertainty-policy-v2"
    expected_authority_version: str = "authority-v1"
    context_fingerprint: str = "context-v1"


@dataclass(frozen=True)
class UncertaintyResult:
    decision: Decision
    reasons: Tuple[str, ...]
    request_fingerprint: Optional[str]
    uncertainty_score: Optional[float]
    authoritative: bool = False
    truth_established: bool = False
    known_established: bool = False
    research_completed: bool = False
    human_approval_granted: bool = False
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


class UncertaintyHoldEngine:
    """Pure uncertainty/hold evaluator. It never performs research, grants approval, or executes actions."""

    def __init__(self, policy: UncertaintyPolicy = UncertaintyPolicy()):
        self.policy = policy
        self._cache: Dict[str, UncertaintyResult] = {}

    def clear_cache(self) -> None:
        self._cache.clear()

    def _result(self, decision: Decision, reasons: Tuple[str, ...], fp: Optional[str] = None, score: Optional[float] = None) -> UncertaintyResult:
        return UncertaintyResult(decision=decision, reasons=reasons, request_fingerprint=fp, uncertainty_score=score)

    def _validate(self, req: UncertaintyRequest) -> Optional[UncertaintyResult]:
        if not req.request_id or not req.target_ref:
            return self._result(Decision.DENY, ("missing request or target identity",))
        if not req.target_version:
            return self._result(Decision.HOLD, ("missing target_version",))
        if not _valid_fp(req.evidence_binding_fingerprint) or not _valid_fp(req.context_fingerprint):
            return self._result(Decision.HOLD, ("missing or invalid evidence/context binding",))
        if req.expected_policy_version != self.policy.policy_version:
            return self._result(Decision.HOLD, ("policy_version mismatch",))
        if req.expected_authority_version != self.policy.authority_version:
            return self._result(Decision.HOLD, ("authority_version mismatch",))
        for name, value in (
            ("confidence", req.confidence),
            ("evidence_coverage", req.evidence_coverage),
            ("contradiction_score", req.contradiction_score),
            ("freshness_score", req.freshness_score),
        ):
            if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                return self._result(Decision.DENY, (f"non-finite {name}",))
            if value < 0 or value > 1:
                return self._result(Decision.DENY, (f"{name} out of range",))
        if req.unknown_count < 0 or req.ambiguity_count < 0:
            return self._result(Decision.DENY, ("negative uncertainty counter",))
        p = self.policy
        for name, value in (
            ("min_confidence_proceed", p.min_confidence_proceed),
            ("min_evidence_coverage", p.min_evidence_coverage),
            ("min_freshness_score", p.min_freshness_score),
            ("max_contradiction_score", p.max_contradiction_score),
            ("high_impact_min_confidence", p.high_impact_min_confidence),
            ("high_impact_min_evidence", p.high_impact_min_evidence),
        ):
            if not isinstance(value, (int, float)) or not math.isfinite(float(value)) or value < 0 or value > 1:
                return self._result(Decision.DENY, (f"invalid policy threshold: {name}",))
        return None

    def _request_key(self, req: UncertaintyRequest) -> str:
        material = {
            "policy": asdict(self.policy),
            "request": {
                **asdict(req),
                "impact_level": req.impact_level.value,
                "missing_required_fields": sorted(req.missing_required_fields),
            },
        }
        return _fingerprint(material)

    def _uncertainty_score(self, req: UncertaintyRequest) -> float:
        score = (
            (1.0 - req.confidence) * 0.30
            + (1.0 - req.evidence_coverage) * 0.25
            + req.contradiction_score * 0.20
            + (1.0 - req.freshness_score) * 0.15
            + min(req.unknown_count, 5) / 5.0 * 0.06
            + min(req.ambiguity_count, 5) / 5.0 * 0.04
        )
        return round(min(max(score, 0.0), 1.0), 6)

    def evaluate(self, req: UncertaintyRequest, *, use_cache: bool = True) -> UncertaintyResult:
        invalid = self._validate(req)
        if invalid is not None:
            return invalid

        key = self._request_key(req)
        if use_cache and key in self._cache:
            return self._cache[key]

        p = self.policy
        reasons = []
        score = self._uncertainty_score(req)
        final = Decision.PROCEED_CANDIDATE

        missing = tuple(sorted({x.strip() for x in req.missing_required_fields if x and x.strip()}))
        if missing:
            reasons.append("required information missing: " + ",".join(missing))
            if p.ask_user_on_missing_fields and req.user_clarification_available:
                final = Decision.ASK_USER
            elif req.research_available:
                final = Decision.RESEARCH_REQUIRED
            else:
                final = Decision.HOLD
        elif req.contradiction_score > p.max_contradiction_score:
            reasons.append("contradiction threshold exceeded")
            if p.research_on_stale_or_conflicted and req.research_available:
                final = Decision.RESEARCH_REQUIRED
            elif req.human_review_available:
                final = Decision.HUMAN_CONFIRM
            else:
                final = Decision.HOLD
        elif req.freshness_score < p.min_freshness_score:
            reasons.append("evidence freshness below threshold")
            if p.research_on_stale_or_conflicted and req.research_available:
                final = Decision.RESEARCH_REQUIRED
            else:
                final = Decision.HOLD
        elif req.evidence_coverage < p.min_evidence_coverage:
            reasons.append("evidence coverage below threshold")
            if req.research_available:
                final = Decision.RESEARCH_REQUIRED
            elif req.user_clarification_available:
                final = Decision.ASK_USER
            else:
                final = Decision.HOLD
        elif req.confidence < p.min_confidence_proceed:
            reasons.append("confidence below proceed threshold")
            if req.user_clarification_available and (req.ambiguity_count > 0 or req.unknown_count > 0):
                final = Decision.ASK_USER
            elif req.research_available:
                final = Decision.RESEARCH_REQUIRED
            elif req.human_review_available:
                final = Decision.HUMAN_CONFIRM
            else:
                final = Decision.HOLD
        elif req.impact_level == ImpactLevel.CRITICAL and p.critical_always_human_confirm:
            reasons.append("critical impact requires human confirmation")
            final = Decision.HUMAN_CONFIRM if req.human_review_available else Decision.HOLD
        elif req.irreversible and p.irreversible_always_human_confirm:
            reasons.append("irreversible operation requires human confirmation")
            final = Decision.HUMAN_CONFIRM if req.human_review_available else Decision.HOLD
        elif req.impact_level == ImpactLevel.HIGH and (
            req.confidence < p.high_impact_min_confidence or req.evidence_coverage < p.high_impact_min_evidence
        ):
            reasons.append("high-impact evidence/confidence margin insufficient")
            final = Decision.HUMAN_CONFIRM if req.human_review_available else Decision.HOLD
        else:
            reasons.append("uncertainty within candidate threshold")

        if req.unknown_count:
            reasons.append(f"unknown_count={req.unknown_count}")
        if req.ambiguity_count:
            reasons.append(f"ambiguity_count={req.ambiguity_count}")

        result = self._result(final, tuple(reasons), key, score)
        if use_cache:
            self._cache[key] = result
        return result
