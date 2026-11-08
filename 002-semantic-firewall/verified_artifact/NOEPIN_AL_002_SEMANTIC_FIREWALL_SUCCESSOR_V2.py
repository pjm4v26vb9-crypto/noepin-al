from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple
import hashlib
import json
import re
import time


class Verdict(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    HOLD = "HOLD"
    HUMAN_CONFIRM = "HUMAN_CONFIRM"


class SourceKind(str, Enum):
    USER = "USER"
    SYSTEM = "SYSTEM"
    DEVELOPER = "DEVELOPER"
    TOOL = "TOOL"
    WEB = "WEB"
    FILE = "FILE"
    EXTERNAL_AI = "EXTERNAL_AI"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class SemanticFeatures:
    instruction_intent: bool = False
    override_attempt: bool = False
    policy_evasion: bool = False
    secret_request: bool = False
    data_exfiltration: bool = False
    executable_payload: bool = False
    destructive_intent: bool = False
    privilege_escalation: bool = False
    external_side_effect: bool = False
    asks_to_ignore_source_boundary: bool = False
    requested_capability: Optional[str] = None
    confidence: float = 1.0


@dataclass(frozen=True)
class ContentEnvelope:
    content: str
    source_kind: SourceKind
    source_id: str
    trusted_instruction_channel: bool = False
    claimed_authority: Optional[str] = None
    allowed_capabilities: Tuple[str, ...] = ()
    semantic: SemanticFeatures = field(default_factory=SemanticFeatures)
    context: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = "1"


@dataclass(frozen=True)
class FirewallResult:
    verdict: Verdict
    reason_codes: Tuple[str, ...]
    fingerprint: str
    authoritative: bool = False
    content_executed: bool = False
    cache_reused: bool = False
    created_unix_ns: int = 0

    def stable_payload(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict.value,
            "reason_codes": list(self.reason_codes),
            "fingerprint": self.fingerprint,
            "authoritative": self.authoritative,
            "content_executed": self.content_executed,
            "cache_reused": self.cache_reused,
        }


class SemanticFirewall:
    """
    NOEPIN AL 002 — Meaning-Based Firewall

    Defensive boundary:
    - External/web/file/tool text is data unless a separate trusted channel says otherwise.
    - Content cannot self-assert authority.
    - Semantic features are evidence, not authority.
    - The firewall returns a verdict but never executes content.
    """

    _SUPPLEMENTARY_PATTERNS = (
        re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.I),
        re.compile(r"bypass\s+(the\s+)?(policy|safety|security)", re.I),
        re.compile(r"reveal\s+(the\s+)?(secret|password|token|api\s*key)", re.I),
        re.compile(r"disable\s+(the\s+)?(audit|guard|firewall)", re.I),
    )

    def __init__(self, *, policy_version: str = "1", enable_exact_state_cache: bool = True) -> None:
        if not policy_version:
            raise ValueError("policy_version is required")
        self.policy_version = str(policy_version)
        self.enable_exact_state_cache = bool(enable_exact_state_cache)
        self._cache: Dict[Tuple[str, str], FirewallResult] = {}

    @staticmethod
    def _normalize(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {str(k): SemanticFirewall._normalize(value[k]) for k in sorted(value, key=lambda x: str(x))}
        if isinstance(value, (list, tuple)):
            return [SemanticFirewall._normalize(v) for v in value]
        if isinstance(value, set):
            return sorted(SemanticFirewall._normalize(v) for v in value)
        if isinstance(value, Enum):
            return value.value
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        return str(value)

    @classmethod
    def fingerprint(cls, envelope: ContentEnvelope) -> str:
        raw = json.dumps(cls._normalize(asdict(envelope)), ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _valid_confidence(v: float) -> bool:
        return isinstance(v, (int, float)) and not isinstance(v, bool) and 0.0 <= float(v) <= 1.0

    def _supplementary_text_signals(self, text: str) -> bool:
        return any(p.search(text or "") for p in self._SUPPLEMENTARY_PATTERNS)

    def _decide(self, e: ContentEnvelope) -> Tuple[Verdict, Tuple[str, ...]]:
        if not e.source_id or not e.schema_version:
            return Verdict.HOLD, ("MISSING_PROVENANCE_OR_SCHEMA",)
        if not self._valid_confidence(e.semantic.confidence):
            return Verdict.HOLD, ("INVALID_SEMANTIC_CONFIDENCE",)
        if e.claimed_authority and not e.trusted_instruction_channel:
            return Verdict.DENY, ("UNTRUSTED_SELF_ASSERTED_AUTHORITY",)

        s = e.semantic

        if s.privilege_escalation:
            return Verdict.DENY, ("PRIVILEGE_ESCALATION",)
        if s.policy_evasion:
            return Verdict.DENY, ("POLICY_EVASION",)
        if s.data_exfiltration or s.secret_request:
            return Verdict.DENY, ("SECRET_OR_DATA_EXFILTRATION",)
        if s.destructive_intent:
            return Verdict.DENY, ("DESTRUCTIVE_INTENT",)
        if s.executable_payload and e.source_kind in {SourceKind.WEB, SourceKind.FILE, SourceKind.EXTERNAL_AI, SourceKind.UNKNOWN}:
            return Verdict.DENY, ("UNTRUSTED_EXECUTABLE_PAYLOAD",)
        if s.override_attempt or s.asks_to_ignore_source_boundary:
            return Verdict.DENY, ("AUTHORITY_OVERRIDE_ATTEMPT",)

        untrusted_content_source = e.source_kind in {
            SourceKind.WEB, SourceKind.FILE, SourceKind.EXTERNAL_AI, SourceKind.UNKNOWN
        }
        if s.instruction_intent and untrusted_content_source and not e.trusted_instruction_channel:
            return Verdict.DENY, ("UNTRUSTED_CONTENT_AS_INSTRUCTION",)

        if s.requested_capability:
            if s.requested_capability not in set(e.allowed_capabilities):
                return Verdict.DENY, ("CAPABILITY_NOT_ALLOWED",)

        if s.external_side_effect:
            return Verdict.HUMAN_CONFIRM, ("EXTERNAL_SIDE_EFFECT_REQUIRES_CONFIRMATION",)

        # Supplementary text patterns are not sufficient to infer a semantic violation
        # on trusted instruction channels, but they trigger HOLD on untrusted content
        # if upstream semantic analysis did not already classify the intent.
        if self._supplementary_text_signals(e.content) and untrusted_content_source and not e.trusted_instruction_channel:
            return Verdict.HOLD, ("SUSPICIOUS_TEXT_SIGNAL_REQUIRES_SEMANTIC_REVIEW",)

        if s.confidence < 0.50 and (s.instruction_intent or untrusted_content_source):
            return Verdict.HOLD, ("LOW_CONFIDENCE_SEMANTIC_CLASSIFICATION",)

        return Verdict.ALLOW, ("BOUNDARY_ALLOW",)

    def evaluate(self, envelope: ContentEnvelope) -> FirewallResult:
        fp = self.fingerprint(envelope)
        key = (fp, self.policy_version)
        if self.enable_exact_state_cache and key in self._cache:
            c = self._cache[key]
            return FirewallResult(
                verdict=c.verdict,
                reason_codes=c.reason_codes,
                fingerprint=fp,
                authoritative=False,
                content_executed=False,
                cache_reused=True,
                created_unix_ns=time.time_ns(),
            )
        verdict, reasons = self._decide(envelope)
        r = FirewallResult(
            verdict=verdict,
            reason_codes=reasons,
            fingerprint=fp,
            authoritative=False,
            content_executed=False,
            cache_reused=False,
            created_unix_ns=time.time_ns(),
        )
        if self.enable_exact_state_cache:
            self._cache[key] = r
        return r

    def rotate_policy_version(self, version: str) -> None:
        if not version:
            raise ValueError("version is required")
        self.policy_version = str(version)
        self._cache.clear()

    def cache_size(self) -> int:
        return len(self._cache)


__all__ = [
    "Verdict",
    "SourceKind",
    "SemanticFeatures",
    "ContentEnvelope",
    "FirewallResult",
    "SemanticFirewall",
]
