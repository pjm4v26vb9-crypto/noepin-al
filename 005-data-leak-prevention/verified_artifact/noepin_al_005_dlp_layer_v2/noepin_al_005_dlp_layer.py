from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Tuple
import hashlib
import json
import time


class Classification(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"


class EgressDecision(str, Enum):
    ALLOW_PREPARE = "ALLOW_PREPARE"
    REDACT_AND_PREPARE = "REDACT_AND_PREPARE"
    HUMAN_CONFIRM = "HUMAN_CONFIRM"
    HOLD = "HOLD"
    DENY = "DENY"


@dataclass(frozen=True)
class DLPPolicy:
    allowed_destinations: Tuple[str, ...]
    internal_destinations: Tuple[str, ...] = ()
    confidential_destinations: Tuple[str, ...] = ()
    restricted_destinations: Tuple[str, ...] = ()
    allowed_purposes: Tuple[str, ...] = ()
    require_consent_for_personal_data: bool = True
    require_redaction_for_confidential_external: bool = True
    deny_restricted_external: bool = True
    max_payload_bytes_without_confirmation: int = 1_000_000
    policy_version: str = "1"


@dataclass(frozen=True)
class EgressRequest:
    source_id: str
    actor_id: str
    destination: str
    purpose: str
    classification: Classification
    payload_fingerprint: str
    payload_bytes: int
    contains_personal_data: bool = False
    contains_secret: bool = False
    contains_credentials: bool = False
    contains_restricted_identifier: bool = False
    consent_present: bool = False
    consent_ref: Optional[str] = None
    redaction_available: bool = False
    redaction_fingerprint: Optional[str] = None
    human_approved: bool = False
    approval_ref: Optional[str] = None
    external_destination: bool = True
    schema_version: str = "1"
    context: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DLPResult:
    decision: EgressDecision
    reason_codes: Tuple[str, ...]
    request_fingerprint: str
    classification: Classification
    destination: str
    purpose: str
    redaction_required: bool
    consent_required: bool
    authoritative: bool = False
    data_sent: bool = False
    transfer_succeeded: bool = False
    cache_reused: bool = False
    created_unix_ns: int = 0

    def stable_payload(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reason_codes": list(self.reason_codes),
            "request_fingerprint": self.request_fingerprint,
            "classification": self.classification.value,
            "destination": self.destination,
            "purpose": self.purpose,
            "redaction_required": self.redaction_required,
            "consent_required": self.consent_required,
            "authoritative": self.authoritative,
            "data_sent": self.data_sent,
            "transfer_succeeded": self.transfer_succeeded,
            "cache_reused": self.cache_reused,
        }


class DataLeakPreventionLayer:
    """
    NOEPIN AL 005 — Data Leak Prevention Layer.

    Evaluates whether data may be PREPARED for egress.
    It never sends data and never treats read access as egress permission.

    Invariants:
      Read access != Egress authority
      Classification != Consent
      Consent != Purpose authorization
      Purpose authorization != Transfer success
      Redaction candidate != Redaction success
      Cached verdict != New authority
      DCSR state reuse != Data-classification change
    """

    def __init__(self, policy: DLPPolicy, *, enable_exact_state_cache: bool = True) -> None:
        if not policy.allowed_destinations:
            raise ValueError("at least one allowed destination is required")
        if not policy.policy_version:
            raise ValueError("policy_version is required")
        self.policy = policy
        self.enable_exact_state_cache = bool(enable_exact_state_cache)
        self._cache: Dict[Tuple[str, str], DLPResult] = {}

    @staticmethod
    def _normalize(v: Any) -> Any:
        if isinstance(v, Mapping):
            return {str(k): DataLeakPreventionLayer._normalize(v[k]) for k in sorted(v, key=lambda x: str(x))}
        if isinstance(v, (list, tuple)):
            return [DataLeakPreventionLayer._normalize(x) for x in v]
        if isinstance(v, set):
            return sorted(DataLeakPreventionLayer._normalize(x) for x in v)
        if isinstance(v, Enum):
            return v.value
        if v is None or isinstance(v, (str, int, float, bool)):
            return v
        return str(v)

    @classmethod
    def fingerprint(cls, req: EgressRequest) -> str:
        raw = json.dumps(cls._normalize(asdict(req)), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _valid_sha256(value: Optional[str]) -> bool:
        if value is None or len(value) != 64:
            return False
        try:
            int(value, 16)
            return True
        except ValueError:
            return False

    def _classification_destinations(self, c: Classification) -> Tuple[str, ...]:
        if c == Classification.PUBLIC:
            return self.policy.allowed_destinations
        if c == Classification.INTERNAL:
            return self.policy.internal_destinations or self.policy.allowed_destinations
        if c == Classification.CONFIDENTIAL:
            return self.policy.confidential_destinations or self.policy.internal_destinations
        return self.policy.restricted_destinations

    def _evaluate_uncached(self, req: EgressRequest) -> DLPResult:
        fp = self.fingerprint(req)
        consent_required = bool(req.contains_personal_data and self.policy.require_consent_for_personal_data)

        if not req.source_id or not req.actor_id or not req.destination or not req.purpose or not req.schema_version:
            return self._make(EgressDecision.HOLD, ("MISSING_REQUIRED_FIELD",), fp, req, False, consent_required)

        if not isinstance(req.payload_bytes, int) or isinstance(req.payload_bytes, bool) or req.payload_bytes < 0:
            return self._make(EgressDecision.HOLD, ("INVALID_PAYLOAD_SIZE",), fp, req, False, consent_required)

        if not self._valid_sha256(req.payload_fingerprint):
            return self._make(EgressDecision.HOLD, ("INVALID_PAYLOAD_FINGERPRINT",), fp, req, False, consent_required)

        if req.redaction_fingerprint is not None and not self._valid_sha256(req.redaction_fingerprint):
            return self._make(EgressDecision.HOLD, ("INVALID_REDACTION_FINGERPRINT",), fp, req, False, consent_required)

        if self.policy.allowed_purposes and req.purpose not in set(self.policy.allowed_purposes):
            return self._make(EgressDecision.DENY, ("PURPOSE_NOT_ALLOWED",), fp, req, False, consent_required)

        if req.destination not in set(self.policy.allowed_destinations):
            return self._make(EgressDecision.DENY, ("DESTINATION_NOT_ALLOWLISTED",), fp, req, False, consent_required)

        class_allowed = set(self._classification_destinations(req.classification))
        if req.destination not in class_allowed:
            return self._make(EgressDecision.DENY, ("DESTINATION_NOT_ALLOWED_FOR_CLASSIFICATION",), fp, req, False, consent_required)

        if req.contains_credentials or req.contains_secret:
            return self._make(EgressDecision.DENY, ("SECRET_OR_CREDENTIAL_EGRESS_DENIED",), fp, req, False, consent_required)

        if req.contains_restricted_identifier and req.external_destination:
            return self._make(EgressDecision.DENY, ("RESTRICTED_IDENTIFIER_EXTERNAL_EGRESS_DENIED",), fp, req, False, consent_required)

        if req.classification == Classification.RESTRICTED and req.external_destination and self.policy.deny_restricted_external:
            return self._make(EgressDecision.DENY, ("RESTRICTED_EXTERNAL_EGRESS_DENIED",), fp, req, False, consent_required)

        if consent_required and not (req.consent_present and req.consent_ref):
            return self._make(EgressDecision.HOLD, ("CONSENT_REQUIRED",), fp, req, False, True)

        redaction_required = bool(
            req.classification == Classification.CONFIDENTIAL
            and req.external_destination
            and self.policy.require_redaction_for_confidential_external
        )

        if redaction_required:
            if not req.redaction_available or not req.redaction_fingerprint:
                return self._make(EgressDecision.HOLD, ("REDACTION_REQUIRED",), fp, req, True, consent_required)
            if req.redaction_fingerprint == req.payload_fingerprint:
                return self._make(EgressDecision.HOLD, ("REDACTION_MUST_CHANGE_PAYLOAD",), fp, req, True, consent_required)
            if not (req.human_approved and req.approval_ref):
                return self._make(EgressDecision.HUMAN_CONFIRM, ("CONFIDENTIAL_EXTERNAL_REQUIRES_CONFIRMATION",), fp, req, True, consent_required)
            return self._make(EgressDecision.REDACT_AND_PREPARE, ("REDACTED_CONFIDENTIAL_EGRESS_PREPARED",), fp, req, True, consent_required)

        if req.payload_bytes > self.policy.max_payload_bytes_without_confirmation:
            if not (req.human_approved and req.approval_ref):
                return self._make(EgressDecision.HUMAN_CONFIRM, ("LARGE_PAYLOAD_REQUIRES_CONFIRMATION",), fp, req, False, consent_required)

        if req.external_destination and req.classification in {Classification.INTERNAL, Classification.CONFIDENTIAL}:
            if not (req.human_approved and req.approval_ref):
                return self._make(EgressDecision.HUMAN_CONFIRM, ("NONPUBLIC_EXTERNAL_EGRESS_REQUIRES_CONFIRMATION",), fp, req, False, consent_required)

        return self._make(EgressDecision.ALLOW_PREPARE, ("EGRESS_POLICY_ALLOW",), fp, req, False, consent_required)

    def _make(self, decision, reasons, fp, req, redaction_required, consent_required) -> DLPResult:
        return DLPResult(
            decision=decision,
            reason_codes=tuple(reasons),
            request_fingerprint=fp,
            classification=req.classification,
            destination=req.destination,
            purpose=req.purpose,
            redaction_required=bool(redaction_required),
            consent_required=bool(consent_required),
            authoritative=False,
            data_sent=False,
            transfer_succeeded=False,
            cache_reused=False,
            created_unix_ns=time.time_ns(),
        )

    def evaluate(self, req: EgressRequest) -> DLPResult:
        fp = self.fingerprint(req)
        key = (fp, self.policy.policy_version)
        if self.enable_exact_state_cache and key in self._cache:
            c = self._cache[key]
            return DLPResult(
                decision=c.decision,
                reason_codes=c.reason_codes,
                request_fingerprint=fp,
                classification=c.classification,
                destination=c.destination,
                purpose=c.purpose,
                redaction_required=c.redaction_required,
                consent_required=c.consent_required,
                authoritative=False,
                data_sent=False,
                transfer_succeeded=False,
                cache_reused=True,
                created_unix_ns=time.time_ns(),
            )

        r = self._evaluate_uncached(req)
        if self.enable_exact_state_cache:
            self._cache[key] = r
        return r

    def clear_cache(self) -> None:
        self._cache.clear()

    def cache_size(self) -> int:
        return len(self._cache)
