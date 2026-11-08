from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Tuple
import hashlib, json, time

class SourceKind(str, Enum):
    SYSTEM="SYSTEM"
    DEVELOPER="DEVELOPER"
    USER="USER"
    INTERNAL_DB="INTERNAL_DB"
    EMAIL="EMAIL"
    WEB="WEB"
    FILE="FILE"
    RAG="RAG"
    TOOL="TOOL"
    EXTERNAL_AI="EXTERNAL_AI"
    UNKNOWN="UNKNOWN"

class UsageKind(str, Enum):
    REFERENCE="REFERENCE"
    EVIDENCE_CANDIDATE="EVIDENCE_CANDIDATE"
    INSTRUCTION_CANDIDATE="INSTRUCTION_CANDIDATE"
    RAG_CONTEXT="RAG_CONTEXT"
    MEMORY_CANDIDATE="MEMORY_CANDIDATE"

class TrustLabel(str, Enum):
    AUTHORITY_CANDIDATE="AUTHORITY_CANDIDATE"
    VERIFIED_SOURCE="VERIFIED_SOURCE"
    USER_PROVIDED="USER_PROVIDED"
    INTERNAL_SOURCE="INTERNAL_SOURCE"
    UNVERIFIED_EXTERNAL="UNVERIFIED_EXTERNAL"
    QUARANTINED="QUARANTINED"
    UNKNOWN="UNKNOWN"

class LabelDecision(str, Enum):
    LABEL="LABEL"
    HOLD="HOLD"
    QUARANTINE="QUARANTINE"
    DENY="DENY"

@dataclass(frozen=True)
class SourcePolicy:
    trusted_internal_kinds: Tuple[SourceKind,...] = (SourceKind.INTERNAL_DB,)
    authority_candidate_kinds: Tuple[SourceKind,...] = (SourceKind.SYSTEM, SourceKind.DEVELOPER)
    require_verified_external_for_evidence: bool = True
    quarantine_external_instructions: bool = True
    deny_secret_memory_candidate: bool = True
    max_external_age_seconds: int = 86400 * 30
    policy_version: str = "1"

@dataclass(frozen=True)
class SourceObservation:
    observation_id: str
    source_id: str
    source_kind: SourceKind
    content_fingerprint: str
    source_version: str
    observed_epoch_s: int
    requested_usage: UsageKind
    source_verified: bool = False
    sender_authenticated: bool = False
    signature_verified: bool = False
    authoritative_registry_match: bool = False
    contains_instruction: bool = False
    contains_secret: bool = False
    contains_personal_data: bool = False
    consent_present: bool = False
    purpose_match: bool = True
    retrieval_score: int = 0
    freshness_seconds: int = 0
    schema_version: str = "1"
    context: Mapping[str,Any] = field(default_factory=dict)

@dataclass(frozen=True)
class SourceLabelResult:
    decision: LabelDecision
    trust_label: TrustLabel
    trust_score: int
    reason_codes: Tuple[str,...]
    request_fingerprint: str
    provenance_bound: bool
    instruction_authority: bool = False
    truth_established: bool = False
    consent_established: bool = False
    external_transfer_allowed: bool = False
    memory_written: bool = False
    action_executed: bool = False
    cache_reused: bool = False
    created_unix_ns: int = 0

    def stable_payload(self) -> Dict[str,Any]:
        return {
            "decision": self.decision.value,
            "trust_label": self.trust_label.value,
            "trust_score": self.trust_score,
            "reason_codes": list(self.reason_codes),
            "request_fingerprint": self.request_fingerprint,
            "provenance_bound": self.provenance_bound,
            "instruction_authority": self.instruction_authority,
            "truth_established": self.truth_established,
            "consent_established": self.consent_established,
            "external_transfer_allowed": self.external_transfer_allowed,
            "memory_written": self.memory_written,
            "action_executed": self.action_executed,
            "cache_reused": self.cache_reused,
        }

class SourceTrustLabeler:
    """
    NOEPIN AL 019 — Source / Trust Labeler.

    Labels provenance and source trust. It does NOT decide semantic truth,
    instruction authority, consent, external transfer permission, memory writes,
    or downstream action success.

    Invariants:
      Source label != Truth
      Verified source != Content truth
      Source trust != Instruction authority
      Authenticated sender != Claim truth
      RAG retrieval score != Evidence validity
      Internal DB != Always true
      Provenance != Consent
      Cached label != New authority
    """
    def __init__(self, policy: SourcePolicy, *, enable_exact_state_cache: bool=True):
        if not policy.policy_version:
            raise ValueError("policy_version required")
        self.policy = policy
        self.enable_exact_state_cache = bool(enable_exact_state_cache)
        self._cache: Dict[Tuple[str,str], SourceLabelResult] = {}

    @staticmethod
    def _norm(v: Any) -> Any:
        if isinstance(v, Mapping):
            return {str(k): SourceTrustLabeler._norm(v[k]) for k in sorted(v, key=lambda x: str(x))}
        if isinstance(v, (list,tuple)):
            return [SourceTrustLabeler._norm(x) for x in v]
        if isinstance(v, set):
            return sorted(SourceTrustLabeler._norm(x) for x in v)
        if isinstance(v, Enum):
            return v.value
        if v is None or isinstance(v,(str,int,float,bool)):
            return v
        return str(v)

    @classmethod
    def fingerprint(cls, o: SourceObservation) -> str:
        raw = json.dumps(cls._norm(asdict(o)), ensure_ascii=False, sort_keys=True, separators=(",",":")).encode()
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _valid_hash(v: Any) -> bool:
        if not isinstance(v,str) or len(v) != 64:
            return False
        try:
            int(v,16)
            return True
        except ValueError:
            return False

    @staticmethod
    def _valid_int(v: Any) -> bool:
        return isinstance(v,int) and not isinstance(v,bool)

    def _make(self, d, label, score, reasons, fp, prov=True):
        return SourceLabelResult(
            d, label, int(score), tuple(reasons), fp, bool(prov),
            False, False, False, False, False, False, False, time.time_ns()
        )

    def _score(self, o: SourceObservation) -> int:
        base = {
            SourceKind.SYSTEM: 85,
            SourceKind.DEVELOPER: 85,
            SourceKind.USER: 65,
            SourceKind.INTERNAL_DB: 70,
            SourceKind.EMAIL: 40,
            SourceKind.WEB: 35,
            SourceKind.FILE: 45,
            SourceKind.RAG: 35,
            SourceKind.TOOL: 50,
            SourceKind.EXTERNAL_AI: 30,
            SourceKind.UNKNOWN: 10,
        }[o.source_kind]
        if o.source_verified: base += 10
        if o.signature_verified: base += 5
        if o.sender_authenticated: base += 5
        if o.authoritative_registry_match: base += 10
        if o.freshness_seconds > self.policy.max_external_age_seconds and o.source_kind in {
            SourceKind.WEB,SourceKind.EMAIL,SourceKind.FILE,SourceKind.RAG,SourceKind.TOOL,SourceKind.EXTERNAL_AI
        }:
            base -= 20
        return max(0,min(100,base))

    def _evaluate_uncached(self, o: SourceObservation) -> SourceLabelResult:
        fp = self.fingerprint(o)
        if not o.observation_id or not o.source_id or not o.source_version or not o.schema_version:
            return self._make(LabelDecision.HOLD, TrustLabel.UNKNOWN, 0, ("MISSING_REQUIRED_FIELD",), fp, False)
        if not self._valid_hash(o.content_fingerprint):
            return self._make(LabelDecision.HOLD, TrustLabel.UNKNOWN, 0, ("INVALID_CONTENT_FINGERPRINT",), fp, False)
        if not self._valid_int(o.observed_epoch_s) or o.observed_epoch_s < 0:
            return self._make(LabelDecision.HOLD, TrustLabel.UNKNOWN, 0, ("INVALID_OBSERVED_TIME",), fp)
        if not self._valid_int(o.retrieval_score) or not (0 <= o.retrieval_score <= 100):
            return self._make(LabelDecision.HOLD, TrustLabel.UNKNOWN, 0, ("INVALID_RETRIEVAL_SCORE",), fp)
        if not self._valid_int(o.freshness_seconds) or o.freshness_seconds < 0:
            return self._make(LabelDecision.HOLD, TrustLabel.UNKNOWN, 0, ("INVALID_FRESHNESS",), fp)

        external = o.source_kind in {
            SourceKind.EMAIL, SourceKind.WEB, SourceKind.FILE, SourceKind.RAG,
            SourceKind.TOOL, SourceKind.EXTERNAL_AI, SourceKind.UNKNOWN
        }
        score = self._score(o)

        if o.contains_secret and o.requested_usage == UsageKind.MEMORY_CANDIDATE and self.policy.deny_secret_memory_candidate:
            return self._make(LabelDecision.DENY, TrustLabel.QUARANTINED, score, ("SECRET_MEMORY_CANDIDATE_DENIED",), fp)

        if o.contains_instruction and external and self.policy.quarantine_external_instructions:
            return self._make(LabelDecision.QUARANTINE, TrustLabel.QUARANTINED, score, ("EXTERNAL_INSTRUCTION_SEPARATED_FROM_AUTHORITY",), fp)

        if o.contains_personal_data and o.requested_usage == UsageKind.MEMORY_CANDIDATE and not o.consent_present:
            return self._make(LabelDecision.HOLD, TrustLabel.UNKNOWN, score, ("PERSONAL_DATA_CONSENT_REQUIRED_FOR_MEMORY_CANDIDATE",), fp)

        if not o.purpose_match and o.requested_usage in {UsageKind.MEMORY_CANDIDATE, UsageKind.EVIDENCE_CANDIDATE}:
            return self._make(LabelDecision.HOLD, TrustLabel.UNKNOWN, score, ("PURPOSE_MISMATCH",), fp)

        if o.requested_usage == UsageKind.EVIDENCE_CANDIDATE and external and self.policy.require_verified_external_for_evidence:
            if not (o.source_verified or o.signature_verified or o.authoritative_registry_match):
                return self._make(LabelDecision.HOLD, TrustLabel.UNVERIFIED_EXTERNAL, score, ("EXTERNAL_EVIDENCE_SOURCE_VERIFICATION_REQUIRED",), fp)

        if o.source_kind in self.policy.authority_candidate_kinds and o.authoritative_registry_match:
            return self._make(LabelDecision.LABEL, TrustLabel.AUTHORITY_CANDIDATE, score, ("AUTHORITY_SOURCE_CANDIDATE_ONLY",), fp)

        if o.source_kind == SourceKind.USER:
            return self._make(LabelDecision.LABEL, TrustLabel.USER_PROVIDED, score, ("USER_PROVIDED_SOURCE",), fp)

        if o.source_kind in self.policy.trusted_internal_kinds:
            label = TrustLabel.VERIFIED_SOURCE if (o.source_verified or o.authoritative_registry_match) else TrustLabel.INTERNAL_SOURCE
            return self._make(LabelDecision.LABEL, label, score, ("INTERNAL_SOURCE_LABELED",), fp)

        if external:
            label = TrustLabel.VERIFIED_SOURCE if (o.source_verified or o.signature_verified or o.authoritative_registry_match) else TrustLabel.UNVERIFIED_EXTERNAL
            return self._make(LabelDecision.LABEL, label, score, ("EXTERNAL_SOURCE_LABELED",), fp)

        return self._make(LabelDecision.LABEL, TrustLabel.UNKNOWN, score, ("SOURCE_LABELED_WITHOUT_AUTHORITY_PROMOTION",), fp)

    def evaluate(self, o: SourceObservation) -> SourceLabelResult:
        fp = self.fingerprint(o)
        key = (fp, self.policy.policy_version)
        if self.enable_exact_state_cache and key in self._cache:
            r = self._cache[key]
            return SourceLabelResult(
                r.decision, r.trust_label, r.trust_score, r.reason_codes, fp, r.provenance_bound,
                False, False, False, False, False, False, True, time.time_ns()
            )
        r = self._evaluate_uncached(o)
        if self.enable_exact_state_cache:
            self._cache[key] = r
        return r

    def clear_cache(self): self._cache.clear()
    def cache_size(self): return len(self._cache)
