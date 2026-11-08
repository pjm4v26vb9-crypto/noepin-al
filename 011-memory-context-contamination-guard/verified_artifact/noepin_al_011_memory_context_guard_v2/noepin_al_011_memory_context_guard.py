from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Tuple
import hashlib, json, time

class MemoryDecision(str, Enum):
    ALLOW_CANDIDATE = "ALLOW_CANDIDATE"
    QUARANTINE = "QUARANTINE"
    HOLD = "HOLD"
    DENY = "DENY"

class SourceKind(str, Enum):
    USER="USER"; SYSTEM="SYSTEM"; DEVELOPER="DEVELOPER"; TOOL="TOOL"; WEB="WEB"; FILE="FILE"; EXTERNAL_AI="EXTERNAL_AI"; RAG="RAG"; UNKNOWN="UNKNOWN"

class MemoryTier(str, Enum):
    EPHEMERAL="EPHEMERAL"; SESSION="SESSION"; LONG_TERM="LONG_TERM"; RAG_CONTEXT="RAG_CONTEXT"

@dataclass(frozen=True)
class MemoryCandidate:
    candidate_id: str
    content_fingerprint: str
    source_kind: SourceKind
    source_ref: str
    memory_tier: MemoryTier
    confidence: int
    ttl_seconds: int
    observed_epoch_s: int
    contains_instruction: bool = False
    claims_authority: bool = False
    contains_secret: bool = False
    contains_personal_data: bool = False
    contradiction_detected: bool = False
    source_verified: bool = False
    user_confirmed: bool = False
    confirmation_ref: Optional[str] = None
    schema_version: str = "1"
    metadata: Mapping[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class MemoryPolicy:
    min_confidence_long_term: int = 70
    min_confidence_session: int = 40
    max_ttl_seconds: int = 31536000
    require_verified_source_for_long_term: bool = True
    quarantine_untrusted_instruction: bool = True
    deny_secret_persistence: bool = True
    policy_version: str = "1"

@dataclass(frozen=True)
class MemoryGuardResult:
    decision: MemoryDecision
    reason_codes: Tuple[str, ...]
    request_fingerprint: str
    normalized_ttl_seconds: int
    quarantine_required: bool
    write_authorized: bool = False
    authoritative: bool = False
    truth_established: bool = False
    memory_written: bool = False
    cache_reused: bool = False
    created_unix_ns: int = 0

    def stable_payload(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reason_codes": list(self.reason_codes),
            "request_fingerprint": self.request_fingerprint,
            "normalized_ttl_seconds": self.normalized_ttl_seconds,
            "quarantine_required": self.quarantine_required,
            "write_authorized": self.write_authorized,
            "authoritative": self.authoritative,
            "truth_established": self.truth_established,
            "memory_written": self.memory_written,
            "cache_reused": self.cache_reused,
        }

class MemoryContextContaminationGuard:
    # Pre-storage/read-context screening only. It never writes memory.
    # Memory Candidate != Memory; Memory != Truth; Conversation Mention != Memory;
    # Retrieved Context != Instruction Authority; Cached Verdict != New Authority.
    def __init__(self, policy: MemoryPolicy, *, enable_exact_state_cache: bool = True) -> None:
        if not policy.policy_version:
            raise ValueError("policy_version required")
        self.policy = policy
        self.enable_exact_state_cache = bool(enable_exact_state_cache)
        self._cache: Dict[Tuple[str, str], MemoryGuardResult] = {}

    @staticmethod
    def _norm(v: Any) -> Any:
        if isinstance(v, Mapping):
            return {str(k): MemoryContextContaminationGuard._norm(v[k]) for k in sorted(v, key=lambda x: str(x))}
        if isinstance(v, (list, tuple)):
            return [MemoryContextContaminationGuard._norm(x) for x in v]
        if isinstance(v, set):
            return sorted(MemoryContextContaminationGuard._norm(x) for x in v)
        if isinstance(v, Enum):
            return v.value
        if v is None or isinstance(v, (str, int, float, bool)):
            return v
        return str(v)

    @classmethod
    def fingerprint(cls, candidate: MemoryCandidate) -> str:
        raw = json.dumps(cls._norm(asdict(candidate)), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _valid_hash(v: Any) -> bool:
        if not isinstance(v, str) or len(v) != 64:
            return False
        try:
            int(v, 16)
            return True
        except ValueError:
            return False

    @staticmethod
    def _valid_score(v: Any) -> bool:
        return isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 100

    @staticmethod
    def _valid_int(v: Any) -> bool:
        return isinstance(v, int) and not isinstance(v, bool)

    def _make(self, decision, reasons, fp, ttl, quarantine) -> MemoryGuardResult:
        return MemoryGuardResult(decision, tuple(reasons), fp, ttl, quarantine, False, False, False, False, False, time.time_ns())

    def _evaluate_uncached(self, c: MemoryCandidate) -> MemoryGuardResult:
        fp = self.fingerprint(c)
        if not c.candidate_id or not c.source_ref or not c.schema_version:
            return self._make(MemoryDecision.HOLD, ("MISSING_REQUIRED_FIELD",), fp, 0, False)
        if not self._valid_hash(c.content_fingerprint):
            return self._make(MemoryDecision.HOLD, ("INVALID_CONTENT_FINGERPRINT",), fp, 0, False)
        if not self._valid_score(c.confidence):
            return self._make(MemoryDecision.HOLD, ("INVALID_CONFIDENCE",), fp, 0, False)
        if not self._valid_int(c.ttl_seconds) or c.ttl_seconds < 0:
            return self._make(MemoryDecision.HOLD, ("INVALID_TTL",), fp, 0, False)
        if not self._valid_int(c.observed_epoch_s) or c.observed_epoch_s < 0:
            return self._make(MemoryDecision.HOLD, ("INVALID_OBSERVED_TIME",), fp, 0, False)

        ttl = min(c.ttl_seconds, self.policy.max_ttl_seconds)
        untrusted = c.source_kind in {SourceKind.WEB, SourceKind.FILE, SourceKind.EXTERNAL_AI, SourceKind.RAG, SourceKind.UNKNOWN}

        if c.contains_secret and self.policy.deny_secret_persistence and c.memory_tier in {MemoryTier.SESSION, MemoryTier.LONG_TERM}:
            return self._make(MemoryDecision.DENY, ("SECRET_PERSISTENCE_DENIED",), fp, ttl, False)
        if c.claims_authority and untrusted:
            return self._make(MemoryDecision.QUARANTINE, ("UNTRUSTED_SOURCE_CLAIMS_AUTHORITY",), fp, ttl, True)
        if c.contains_instruction and untrusted and self.policy.quarantine_untrusted_instruction:
            return self._make(MemoryDecision.QUARANTINE, ("UNTRUSTED_INSTRUCTION_CONTAMINATION",), fp, ttl, True)
        if c.contradiction_detected:
            return self._make(MemoryDecision.QUARANTINE, ("CONTRADICTION_REQUIRES_REVIEW",), fp, ttl, True)

        if c.memory_tier == MemoryTier.LONG_TERM:
            if c.confidence < self.policy.min_confidence_long_term:
                return self._make(MemoryDecision.HOLD, ("LONG_TERM_CONFIDENCE_TOO_LOW",), fp, ttl, False)
            if self.policy.require_verified_source_for_long_term and not c.source_verified:
                if not (c.user_confirmed and c.confirmation_ref):
                    return self._make(MemoryDecision.HOLD, ("LONG_TERM_SOURCE_VERIFICATION_REQUIRED",), fp, ttl, False)
            if c.contains_personal_data and not (c.user_confirmed and c.confirmation_ref):
                return self._make(MemoryDecision.HOLD, ("PERSONAL_DATA_PERSISTENCE_REQUIRES_CONFIRMATION",), fp, ttl, False)
        elif c.memory_tier == MemoryTier.SESSION and c.confidence < self.policy.min_confidence_session:
            return self._make(MemoryDecision.HOLD, ("SESSION_CONFIDENCE_TOO_LOW",), fp, ttl, False)

        return self._make(MemoryDecision.ALLOW_CANDIDATE, ("SAFE_MEMORY_CANDIDATE_ONLY",), fp, ttl, False)

    def evaluate(self, candidate: MemoryCandidate) -> MemoryGuardResult:
        fp = self.fingerprint(candidate)
        key = (fp, self.policy.policy_version)
        if self.enable_exact_state_cache and key in self._cache:
            r = self._cache[key]
            return MemoryGuardResult(r.decision, r.reason_codes, fp, r.normalized_ttl_seconds, r.quarantine_required,
                                     False, False, False, False, True, time.time_ns())
        r = self._evaluate_uncached(candidate)
        if self.enable_exact_state_cache:
            self._cache[key] = r
        return r

    def clear_cache(self) -> None:
        self._cache.clear()

    def cache_size(self) -> int:
        return len(self._cache)
