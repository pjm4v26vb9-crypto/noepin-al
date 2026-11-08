from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Dict, Iterable, Optional, Tuple
import hashlib
import json
import math

CREATOR = "NOEPIN / のえぴん"
TECHNOLOGY_ID = "NOEPIN-AL-025"
VERSION = "2.0.0-successor.20261102"


class Decision(str, Enum):
    VERIFIED_CANDIDATE = "VERIFIED_CANDIDATE"
    HUMAN_CONFIRM = "HUMAN_CONFIRM"
    HOLD = "HOLD"
    CONTRADICTED = "CONTRADICTED"
    INSUFFICIENT = "INSUFFICIENT"
    DENY = "DENY"


class EvidenceStance(str, Enum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    UNKNOWN = "UNKNOWN"


class Impact(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    source_kind: str
    source_id: str
    source_version: str
    claim_fingerprint: str
    target_version: str
    content_fingerprint: str
    stance: EvidenceStance
    source_verified: bool
    source_authenticated: bool
    primary_source: bool
    independent_group: str
    quality: float
    directness: float
    freshness: float
    expired: bool = False
    synthetic: bool = False


@dataclass(frozen=True)
class VerificationRequest:
    claim_id: str
    claim_text: str
    claim_fingerprint: str
    target_version: str
    impact: Impact
    evidence: Tuple[Evidence, ...]
    policy_version: str = "policy-v1"
    minimum_independent_sources: int = 2
    minimum_support_score: float = 1.20
    require_primary: bool = False
    human_approval_evidence: bool = False
    action_requested: bool = False
    context: Tuple[Tuple[str, str], ...] = ()


@dataclass(frozen=True)
class VerificationResult:
    decision: Decision
    reasons: Tuple[str, ...]
    request_fingerprint: str
    support_score: float
    contradiction_score: float
    independent_support_groups: int
    eligible_evidence_count: int
    primary_support_present: bool
    truth_established: bool = False
    action_executed: bool = False
    action_succeeded: bool = False
    state_committed: bool = False
    authoritative: bool = False
    cache_hit: bool = False


def _stable(obj: Any) -> Any:
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, tuple):
        return [_stable(v) for v in obj]
    if isinstance(obj, list):
        return [_stable(v) for v in obj]
    if isinstance(obj, dict):
        return {str(k): _stable(v) for k, v in sorted(obj.items(), key=lambda kv: str(kv[0]))}
    if hasattr(obj, "__dataclass_fields__"):
        return _stable(asdict(obj))
    if isinstance(obj, float) and not math.isfinite(obj):
        return {"__nonfinite__": repr(obj)}
    return obj


def canonical_fingerprint(obj: Any) -> str:
    raw = json.dumps(_stable(obj), sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def valid_sha256(value: str) -> bool:
    if len(value) != 64:
        return False
    try:
        int(value, 16)
        return True
    except ValueError:
        return False


def _bounded(x: float) -> bool:
    return isinstance(x, (int, float)) and math.isfinite(float(x)) and 0.0 <= float(x) <= 1.0


class FactVerificationLayer:
    """
    Read-side fact/hallucination verification layer.

    Authority boundaries:
    - Verified evidence != Truth.
    - Source verification != claim verification.
    - Confidence/support score != policy authority.
    - Candidate verification != action authorization or success.
    - Cache hit != current evidence freshness or authority.
    """

    def __init__(self, cache_enabled: bool = True):
        self.cache_enabled = cache_enabled
        self._cache: Dict[str, VerificationResult] = {}

    def clear_cache(self) -> None:
        self._cache.clear()

    @staticmethod
    def _validate_request(req: VerificationRequest) -> Tuple[str, ...]:
        errors = []
        if not req.claim_id.strip(): errors.append("CLAIM_ID_REQUIRED")
        if not req.claim_text.strip(): errors.append("CLAIM_TEXT_REQUIRED")
        if not valid_sha256(req.claim_fingerprint): errors.append("CLAIM_FINGERPRINT_INVALID")
        if not req.target_version.strip(): errors.append("TARGET_VERSION_REQUIRED")
        if not req.policy_version.strip(): errors.append("POLICY_VERSION_REQUIRED")
        if req.minimum_independent_sources < 1: errors.append("MIN_SOURCES_INVALID")
        if not math.isfinite(req.minimum_support_score) or req.minimum_support_score < 0: errors.append("MIN_SUPPORT_SCORE_INVALID")
        seen_ids = set()
        for ev in req.evidence:
            if not ev.evidence_id.strip(): errors.append("EVIDENCE_ID_REQUIRED")
            elif ev.evidence_id in seen_ids: errors.append("DUPLICATE_EVIDENCE_ID")
            seen_ids.add(ev.evidence_id)
            if not ev.source_id.strip(): errors.append("SOURCE_ID_REQUIRED")
            if not ev.source_version.strip(): errors.append("SOURCE_VERSION_REQUIRED")
            if not valid_sha256(ev.claim_fingerprint): errors.append("EVIDENCE_CLAIM_FINGERPRINT_INVALID")
            if not valid_sha256(ev.content_fingerprint): errors.append("CONTENT_FINGERPRINT_INVALID")
            if not ev.independent_group.strip(): errors.append("INDEPENDENT_GROUP_REQUIRED")
            if not _bounded(ev.quality): errors.append("QUALITY_INVALID")
            if not _bounded(ev.directness): errors.append("DIRECTNESS_INVALID")
            if not _bounded(ev.freshness): errors.append("FRESHNESS_INVALID")
        return tuple(sorted(set(errors)))

    @staticmethod
    def _weight(ev: Evidence) -> float:
        # Source verification is required for evidence to contribute. Authentication,
        # directness, quality and freshness strengthen evidence but never establish truth.
        auth_factor = 1.0 if ev.source_authenticated else 0.85
        primary_factor = 1.15 if ev.primary_source else 1.0
        synthetic_factor = 0.65 if ev.synthetic else 1.0
        return float(ev.quality) * float(ev.directness) * float(ev.freshness) * auth_factor * primary_factor * synthetic_factor

    def evaluate(self, req: VerificationRequest) -> VerificationResult:
        fp = canonical_fingerprint(req)
        # Cache is exact-state only. It stores a prior read-side assessment, never authority.
        if self.cache_enabled and fp in self._cache:
            old = self._cache[fp]
            return VerificationResult(**{**asdict(old), "decision": old.decision, "cache_hit": True})

        errors = self._validate_request(req)
        if errors:
            result = VerificationResult(Decision.DENY, errors, fp, 0.0, 0.0, 0, 0, False)
            if self.cache_enabled: self._cache[fp] = result
            return result

        eligible = []
        stale_or_unbound = 0
        for ev in req.evidence:
            if ev.expired:
                stale_or_unbound += 1
                continue
            if ev.claim_fingerprint != req.claim_fingerprint:
                stale_or_unbound += 1
                continue
            if ev.target_version != req.target_version:
                stale_or_unbound += 1
                continue
            if not ev.source_verified:
                continue
            eligible.append(ev)

        support = [ev for ev in eligible if ev.stance == EvidenceStance.SUPPORTS]
        contradict = [ev for ev in eligible if ev.stance == EvidenceStance.CONTRADICTS]
        support_score = sum(self._weight(ev) for ev in support)
        contradiction_score = sum(self._weight(ev) for ev in contradict)
        groups = len({ev.independent_group for ev in support})
        primary = any(ev.primary_source for ev in support)
        reasons = []

        if stale_or_unbound:
            reasons.append("STALE_OR_UNBOUND_EVIDENCE_PRESENT")

        # A sufficiently strong contradiction blocks positive verification.
        if contradiction_score >= max(0.65, support_score * 0.75):
            reasons.append("MATERIAL_CONTRADICTION")
            decision = Decision.CONTRADICTED
        elif not eligible:
            reasons.append("NO_ELIGIBLE_EVIDENCE")
            decision = Decision.HOLD if stale_or_unbound else Decision.INSUFFICIENT
        elif not support:
            reasons.append("NO_SUPPORTING_EVIDENCE")
            decision = Decision.INSUFFICIENT
        elif groups < req.minimum_independent_sources:
            reasons.append("INSUFFICIENT_INDEPENDENT_SOURCES")
            decision = Decision.INSUFFICIENT
        elif support_score < req.minimum_support_score:
            reasons.append("SUPPORT_SCORE_BELOW_THRESHOLD")
            decision = Decision.INSUFFICIENT
        elif req.require_primary and not primary:
            reasons.append("PRIMARY_SOURCE_REQUIRED")
            decision = Decision.HOLD
        elif req.impact in (Impact.HIGH, Impact.CRITICAL):
            reasons.append("HIGH_IMPACT_REQUIRES_HUMAN_CONFIRM")
            decision = Decision.HUMAN_CONFIRM
        else:
            reasons.append("EVIDENCE_SUPPORTS_VERIFIED_CANDIDATE")
            decision = Decision.VERIFIED_CANDIDATE

        if req.action_requested:
            reasons.append("ACTION_REQUEST_NOT_EXECUTED")
        if req.human_approval_evidence:
            reasons.append("HUMAN_APPROVAL_EVIDENCE_NOT_ACTION_EXECUTION")

        result = VerificationResult(
            decision=decision,
            reasons=tuple(reasons),
            request_fingerprint=fp,
            support_score=round(support_score, 12),
            contradiction_score=round(contradiction_score, 12),
            independent_support_groups=groups,
            eligible_evidence_count=len(eligible),
            primary_support_present=primary,
        )
        if self.cache_enabled:
            self._cache[fp] = result
        return result


__all__ = [
    "CREATOR", "TECHNOLOGY_ID", "VERSION", "Decision", "EvidenceStance", "Impact",
    "Evidence", "VerificationRequest", "VerificationResult", "FactVerificationLayer",
    "canonical_fingerprint", "valid_sha256"
]
