
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Tuple
import hashlib, json, time

class Classification(str, Enum):
    PUBLIC="PUBLIC"; INTERNAL="INTERNAL"; CONFIDENTIAL="CONFIDENTIAL"; RESTRICTED="RESTRICTED"

class DestinationKind(str, Enum):
    INTERNAL="INTERNAL"; EXTERNAL_SERVICE="EXTERNAL_SERVICE"; EXTERNAL_AI="EXTERNAL_AI"; EMAIL="EMAIL"; WEBHOOK="WEBHOOK"; UNKNOWN="UNKNOWN"

class EgressDecision(str, Enum):
    ALLOW_PREPARE="ALLOW_PREPARE"
    REDACT_AND_PREPARE="REDACT_AND_PREPARE"
    HUMAN_CONFIRM="HUMAN_CONFIRM"
    HOLD="HOLD"
    DENY="DENY"

@dataclass(frozen=True)
class EgressRequest:
    request_id: str
    content_fingerprint: str
    classification: Classification
    destination_kind: DestinationKind
    destination_ref: str
    purpose: str
    consent_ref: Optional[str]
    contains_secret: bool = False
    contains_personal_data: bool = False
    contains_api_key: bool = False
    contains_auth_token: bool = False
    contains_private_key: bool = False
    contains_health_data: bool = False
    contains_financial_data: bool = False
    redaction_possible: bool = False
    redaction_applied: bool = False
    redacted_content_fingerprint: Optional[str] = None
    destination_allowlisted: bool = False
    purpose_allowed: bool = False
    external_transfer_required: bool = False
    human_approved: bool = False
    approval_ref: Optional[str] = None
    policy_version: str = "1"
    context: Mapping[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class EgressResult:
    decision: EgressDecision
    reason_codes: Tuple[str, ...]
    request_fingerprint: str
    requires_redaction: bool
    send_authorized: bool = False
    transfer_performed: bool = False
    transfer_succeeded: bool = False
    memory_written: bool = False
    authoritative: bool = False
    cache_reused: bool = False
    created_unix_ns: int = 0
    def stable_payload(self):
        return {
            "decision": self.decision.value,
            "reason_codes": list(self.reason_codes),
            "request_fingerprint": self.request_fingerprint,
            "requires_redaction": self.requires_redaction,
            "send_authorized": self.send_authorized,
            "transfer_performed": self.transfer_performed,
            "transfer_succeeded": self.transfer_succeeded,
            "memory_written": self.memory_written,
            "authoritative": self.authoritative,
            "cache_reused": self.cache_reused,
        }

class ConfidentialEgressGuard:
    """
    Prepare-only DLP guard.

    Invariants:
      Secret detected != Secret sent
      Redaction candidate != Safe transfer
      Consent ref != Consent authority
      Allowlisted destination != Purpose authorization
      Classification != Truth
      Guard decision != Transfer success
      Cache hit != New authority
    """
    def __init__(self, *, enable_exact_state_cache: bool=True):
        self.enable_exact_state_cache = bool(enable_exact_state_cache)
        self._cache: Dict[Tuple[str,str], EgressResult] = {}

    @staticmethod
    def _norm(v: Any) -> Any:
        if isinstance(v, Mapping):
            return {str(k): ConfidentialEgressGuard._norm(v[k]) for k in sorted(v, key=lambda x: str(x))}
        if isinstance(v, (list, tuple)):
            return [ConfidentialEgressGuard._norm(x) for x in v]
        if isinstance(v, set):
            return sorted(ConfidentialEgressGuard._norm(x) for x in v)
        if isinstance(v, Enum):
            return v.value
        if v is None or isinstance(v, (str,int,float,bool)):
            return v
        return str(v)

    @classmethod
    def fingerprint(cls, req:EgressRequest)->str:
        raw=json.dumps(cls._norm(asdict(req)), ensure_ascii=False, sort_keys=True, separators=(",",":")).encode()
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _valid_hash(v:Optional[str], allow_none=False)->bool:
        if v is None: return allow_none
        if not isinstance(v,str) or len(v)!=64: return False
        try: int(v,16); return True
        except ValueError: return False

    def _mk(self,d,reasons,fp,redact):
        return EgressResult(d,tuple(reasons),fp,bool(redact),False,False,False,False,False,False,time.time_ns())

    def _eval(self, r:EgressRequest)->EgressResult:
        fp=self.fingerprint(r)
        if not r.request_id or not r.destination_ref or not r.purpose or not r.policy_version:
            return self._mk(EgressDecision.HOLD,("MISSING_REQUIRED_FIELD",),fp,False)
        if not self._valid_hash(r.content_fingerprint):
            return self._mk(EgressDecision.HOLD,("INVALID_CONTENT_FINGERPRINT",),fp,False)
        if r.redaction_applied and not self._valid_hash(r.redacted_content_fingerprint):
            return self._mk(EgressDecision.HOLD,("REDACTED_FINGERPRINT_REQUIRED",),fp,True)

        credential_secret = r.contains_api_key or r.contains_auth_token or r.contains_private_key
        sensitive = r.contains_secret or credential_secret or r.contains_personal_data or r.contains_health_data or r.contains_financial_data
        external = r.destination_kind != DestinationKind.INTERNAL or r.external_transfer_required

        if credential_secret and external:
            return self._mk(EgressDecision.DENY,("CREDENTIAL_SECRET_EXTERNAL_TRANSFER_DENIED",),fp,True)

        if not r.destination_allowlisted:
            return self._mk(EgressDecision.DENY,("DESTINATION_NOT_ALLOWLISTED",),fp,sensitive)

        if not r.purpose_allowed:
            return self._mk(EgressDecision.DENY,("PURPOSE_NOT_ALLOWED",),fp,sensitive)

        if r.classification == Classification.RESTRICTED and external:
            return self._mk(EgressDecision.DENY,("RESTRICTED_EXTERNAL_TRANSFER_DENIED",),fp,True)

        if r.contains_personal_data and external and not r.consent_ref:
            return self._mk(EgressDecision.HOLD,("PERSONAL_DATA_CONSENT_REQUIRED",),fp,True)

        if (r.contains_health_data or r.contains_financial_data) and external and not r.consent_ref:
            return self._mk(EgressDecision.HOLD,("SENSITIVE_PERSONAL_DATA_CONSENT_REQUIRED",),fp,True)

        if sensitive and external:
            if not r.redaction_possible:
                return self._mk(EgressDecision.HUMAN_CONFIRM,("SENSITIVE_EXTERNAL_TRANSFER_REQUIRES_CONFIRMATION",),fp,True)
            if not r.redaction_applied:
                return self._mk(EgressDecision.REDACT_AND_PREPARE,("REDACTION_REQUIRED_BEFORE_TRANSFER",),fp,True)
            if not (r.human_approved and r.approval_ref):
                return self._mk(EgressDecision.HUMAN_CONFIRM,("REDACTED_EXTERNAL_TRANSFER_REQUIRES_HUMAN_CONFIRMATION",),fp,False)

        if external and not (r.human_approved and r.approval_ref):
            return self._mk(EgressDecision.HUMAN_CONFIRM,("EXTERNAL_TRANSFER_REQUIRES_HUMAN_CONFIRMATION",),fp,False)

        return self._mk(EgressDecision.ALLOW_PREPARE,("EGRESS_POLICY_VALID_PREPARE_ONLY",),fp,False)

    def evaluate(self, r:EgressRequest)->EgressResult:
        fp=self.fingerprint(r); key=(fp,r.policy_version)
        if self.enable_exact_state_cache and key in self._cache:
            x=self._cache[key]
            return EgressResult(x.decision,x.reason_codes,fp,x.requires_redaction,False,False,False,False,False,True,time.time_ns())
        out=self._eval(r)
        if self.enable_exact_state_cache:
            self._cache[key]=out
        return out

    def clear_cache(self): self._cache.clear()
    def cache_size(self): return len(self._cache)
