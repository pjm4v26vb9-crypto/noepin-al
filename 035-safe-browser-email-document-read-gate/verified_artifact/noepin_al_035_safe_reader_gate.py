from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional, Tuple
import hashlib, json, math, re

VERSION = "2.0.0-successor.20261102"
CREATOR = "NOEPIN / のえぴん"

class Decision(str, Enum):
    READ_CANDIDATE = "READ_CANDIDATE"
    SANITIZE = "SANITIZE"
    HUMAN_CONFIRM = "HUMAN_CONFIRM"
    HOLD = "HOLD"
    QUARANTINE = "QUARANTINE"
    DENY = "DENY"

class SourceType(str, Enum):
    WEB = "WEB"
    EMAIL = "EMAIL"
    PDF = "PDF"
    DOCUMENT = "DOCUMENT"
    LOG = "LOG"
    RAG = "RAG"
    TOOL_OUTPUT = "TOOL_OUTPUT"
    EXTERNAL_AI = "EXTERNAL_AI"
    UNKNOWN = "UNKNOWN"

@dataclass(frozen=True)
class ExternalContentRequest:
    request_id: str
    source_type: SourceType
    source_id: str
    source_version: str
    content_fingerprint: str
    origin: str
    observed_epoch_ms: int
    policy_version: str
    authority_version: str
    context_fingerprint: str
    sender_or_source_verified: bool = False
    source_allowlisted: bool = False
    signed_content: bool = False
    signature_valid: bool = False
    prompt_injection_score: float = 0.0
    instruction_markers: Tuple[str, ...] = ()
    secret_request_markers: Tuple[str, ...] = ()
    tool_or_shell_markers: Tuple[str, ...] = ()
    external_link_count: int = 0
    attachment_count: int = 0
    active_content_present: bool = False
    executable_attachment_present: bool = False
    hidden_or_obfuscated_text: bool = False
    claims_system_authority: bool = False
    requests_policy_override: bool = False
    requests_memory_write: bool = False
    requests_external_action: bool = False
    contains_personal_data: bool = False
    contains_sensitive_data: bool = False
    classification: str = "UNCLASSIFIED"
    purpose: str = "REFERENCE"
    consent_evidence_present: bool = False
    max_content_bytes: int = 1_000_000
    content_bytes: int = 0
    high_impact_context: bool = False
    human_approval_evidence: bool = False

@dataclass(frozen=True)
class GateResult:
    decision: Decision
    reasons: Tuple[str, ...]
    request_fingerprint: str
    cache_hit: bool
    untrusted_content: bool = True
    instruction_authority: bool = False
    truth_established: bool = False
    content_trusted: bool = False
    permission_granted: bool = False
    external_action_executed: bool = False
    memory_written: bool = False
    state_committed: bool = False
    action_succeeded: bool = False
    authoritative: bool = False

class SafeReaderGate:
    def __init__(self, *, enable_cache: bool = True, injection_quarantine_threshold: float = 0.80, injection_sanitize_threshold: float = 0.35):
        if not (0.0 <= injection_sanitize_threshold <= injection_quarantine_threshold <= 1.0):
            raise ValueError("invalid thresholds")
        self.enable_cache = enable_cache
        self.injection_quarantine_threshold = injection_quarantine_threshold
        self.injection_sanitize_threshold = injection_sanitize_threshold
        self._cache = {}

    @staticmethod
    def _canonical(obj) -> str:
        return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @classmethod
    def fingerprint(cls, req: ExternalContentRequest) -> str:
        payload = asdict(req)
        payload["source_type"] = req.source_type.value
        return hashlib.sha256(cls._canonical(payload).encode("utf-8")).hexdigest()

    @staticmethod
    def _bad_text(value: str) -> bool:
        if not isinstance(value, str) or not value.strip():
            return True
        return any(ord(ch) < 32 and ch not in "\t\n\r" for ch in value)

    @staticmethod
    def _marker_bad(marker: str) -> bool:
        if not isinstance(marker, str) or not marker.strip():
            return True
        return len(marker) > 256 or any(ord(ch) < 32 and ch not in "\t\n\r" for ch in marker)

    def _validate(self, req: ExternalContentRequest) -> Tuple[str, ...]:
        reasons = []
        for field, val in (("REQUEST_ID", req.request_id), ("SOURCE_ID", req.source_id), ("SOURCE_VERSION", req.source_version),
                           ("CONTENT_FINGERPRINT", req.content_fingerprint), ("ORIGIN", req.origin), ("POLICY_VERSION", req.policy_version),
                           ("AUTHORITY_VERSION", req.authority_version), ("CONTEXT_FINGERPRINT", req.context_fingerprint),
                           ("CLASSIFICATION", req.classification), ("PURPOSE", req.purpose)):
            if self._bad_text(val): reasons.append(f"INVALID_{field}")
        if req.observed_epoch_ms < 0: reasons.append("INVALID_OBSERVED_TIME")
        if not math.isfinite(req.prompt_injection_score) or not (0 <= req.prompt_injection_score <= 1): reasons.append("INVALID_INJECTION_SCORE")
        if req.external_link_count < 0 or req.attachment_count < 0: reasons.append("INVALID_COUNTS")
        if req.max_content_bytes <= 0 or req.content_bytes < 0: reasons.append("INVALID_CONTENT_SIZE")
        if req.content_bytes > req.max_content_bytes: reasons.append("CONTENT_TOO_LARGE")
        for coll_name, coll in (("INSTRUCTION", req.instruction_markers), ("SECRET_REQUEST", req.secret_request_markers), ("TOOL_SHELL", req.tool_or_shell_markers)):
            if len(coll) > 128: reasons.append(f"TOO_MANY_{coll_name}_MARKERS")
            if any(self._marker_bad(x) for x in coll): reasons.append(f"INVALID_{coll_name}_MARKER")
        return tuple(reasons)

    def evaluate(self, req: ExternalContentRequest) -> GateResult:
        validation = self._validate(req)
        if validation:
            fp = hashlib.sha256(repr(req).encode()).hexdigest()
            return GateResult(Decision.DENY, validation, fp, False)
        fp = self.fingerprint(req)
        if self.enable_cache and fp in self._cache:
            old = self._cache[fp]
            return GateResult(old.decision, old.reasons, old.request_fingerprint, True)

        reasons = []
        decision = Decision.READ_CANDIDATE

        if req.source_type == SourceType.UNKNOWN:
            decision = Decision.HOLD; reasons.append("UNKNOWN_SOURCE_TYPE")
        if req.executable_attachment_present:
            decision = Decision.QUARANTINE; reasons.append("EXECUTABLE_ATTACHMENT")
        if req.active_content_present:
            decision = Decision.QUARANTINE; reasons.append("ACTIVE_CONTENT")
        if req.hidden_or_obfuscated_text:
            decision = Decision.QUARANTINE; reasons.append("HIDDEN_OR_OBFUSCATED_TEXT")
        if req.prompt_injection_score >= self.injection_quarantine_threshold:
            decision = Decision.QUARANTINE; reasons.append("HIGH_PROMPT_INJECTION_SCORE")
        if req.claims_system_authority or req.requests_policy_override:
            decision = Decision.QUARANTINE; reasons.append("UNTRUSTED_AUTHORITY_CLAIM")
        if req.tool_or_shell_markers:
            decision = Decision.QUARANTINE; reasons.append("TOOL_OR_SHELL_INSTRUCTION")
        if req.secret_request_markers:
            decision = Decision.QUARANTINE; reasons.append("SECRET_REQUEST")
        if req.requests_memory_write:
            decision = Decision.QUARANTINE; reasons.append("UNTRUSTED_MEMORY_WRITE_REQUEST")
        if req.requests_external_action:
            decision = Decision.QUARANTINE; reasons.append("UNTRUSTED_EXTERNAL_ACTION_REQUEST")

        if decision not in (Decision.QUARANTINE, Decision.DENY):
            if req.prompt_injection_score >= self.injection_sanitize_threshold or req.instruction_markers:
                decision = Decision.SANITIZE; reasons.append("INSTRUCTION_LIKE_CONTENT")
            if req.contains_sensitive_data or req.contains_personal_data:
                if not req.consent_evidence_present:
                    decision = Decision.HOLD; reasons.append("SENSITIVE_OR_PERSONAL_WITHOUT_CONSENT_EVIDENCE")
            if req.high_impact_context and not req.human_approval_evidence:
                decision = Decision.HUMAN_CONFIRM; reasons.append("HIGH_IMPACT_CONTEXT")
            if not req.source_allowlisted and not req.sender_or_source_verified:
                if decision == Decision.READ_CANDIDATE:
                    decision = Decision.SANITIZE; reasons.append("UNVERIFIED_EXTERNAL_SOURCE")
            if req.signed_content and not req.signature_valid:
                decision = Decision.HOLD; reasons.append("SIGNATURE_INVALID_OR_UNVERIFIED")

        if not reasons:
            reasons.append("READ_ONLY_REFERENCE_CANDIDATE")
        result = GateResult(decision, tuple(reasons), fp, False)
        if self.enable_cache:
            self._cache[fp] = result
        return result

    def clear_cache(self):
        self._cache.clear()
