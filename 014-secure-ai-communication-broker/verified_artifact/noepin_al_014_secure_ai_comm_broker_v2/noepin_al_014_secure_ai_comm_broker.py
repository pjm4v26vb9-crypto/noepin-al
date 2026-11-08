from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Tuple
import hashlib
import hmac
import json
import time


class BrokerDecision(str, Enum):
    ALLOW_PREPARE = "ALLOW_PREPARE"
    HUMAN_CONFIRM = "HUMAN_CONFIRM"
    HOLD = "HOLD"
    DENY = "DENY"


@dataclass(frozen=True)
class AgentRoute:
    agent_id: str
    key_id: str
    allowed_destinations: Tuple[str, ...]
    allowed_purposes: Tuple[str, ...]
    disabled: bool = False
    route_version: int = 1


@dataclass(frozen=True)
class SecureEnvelope:
    message_id: str
    sender_id: str
    recipient_id: str
    purpose: str
    payload_sha256: str
    issued_at_epoch_s: int
    expires_at_epoch_s: int
    nonce: str
    key_id: str
    signature_hex: str
    tls_authenticated: bool
    mtls_authenticated: bool
    sender_certificate_ref: Optional[str] = None
    shared_state_fingerprint: Optional[str] = None
    delta_fingerprint: Optional[str] = None
    claims_authority: bool = False
    requests_external_action: bool = False
    risk_score: int = 0
    human_approved: bool = False
    approval_ref: Optional[str] = None
    schema_version: str = "1"
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CommunicationRequest:
    request_id: str
    envelope: SecureEnvelope
    observed_epoch_s: int
    nonce_already_seen: bool = False
    expected_sender_route_version: Optional[int] = None
    schema_version: str = "1"
    context: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BrokerPolicy:
    require_tls: bool = True
    require_mtls: bool = True
    require_sender_certificate: bool = True
    max_clock_skew_seconds: int = 300
    max_message_lifetime_seconds: int = 3600
    max_risk_without_confirmation: int = 35
    high_risk_purposes: Tuple[str, ...] = ("execute", "publish", "purchase", "external_send", "privilege_change")
    policy_version: str = "1"


@dataclass(frozen=True)
class BrokerResult:
    decision: BrokerDecision
    reason_codes: Tuple[str, ...]
    request_fingerprint: str
    sender_authenticated: bool
    signature_verified: bool
    purpose_authorized: bool
    replay_check_passed: bool
    authoritative: bool = False
    message_sent: bool = False
    message_delivered: bool = False
    recipient_heard: bool = False
    action_executed: bool = False
    action_succeeded: bool = False
    cache_reused: bool = False
    created_unix_ns: int = 0

    def stable_payload(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reason_codes": list(self.reason_codes),
            "request_fingerprint": self.request_fingerprint,
            "sender_authenticated": self.sender_authenticated,
            "signature_verified": self.signature_verified,
            "purpose_authorized": self.purpose_authorized,
            "replay_check_passed": self.replay_check_passed,
            "authoritative": self.authoritative,
            "message_sent": self.message_sent,
            "message_delivered": self.message_delivered,
            "recipient_heard": self.recipient_heard,
            "action_executed": self.action_executed,
            "action_succeeded": self.action_succeeded,
            "cache_reused": self.cache_reused,
        }


class SecureAICommunicationBroker:
    """
    NOEPIN AL 014 — Secure AI-to-AI Communication Broker.

    Verifies a prepared AI-to-AI message envelope. It does not open sockets, transmit
    the message, mark delivery/hearing, or execute a requested downstream action.

    Invariants:
      Authenticated channel != Message authority
      Signature verified != Purpose authorization
      Sender identity != Downstream action authority
      Message accepted != Delivered
      Delivered != Heard
      Message request != Action success
      Fingerprint match != Authority match
      Cached verification != New authority
      DCSR reconstructed state != Trusted instruction
    """

    def __init__(
        self,
        policy: BrokerPolicy,
        routes: Mapping[str, AgentRoute],
        hmac_keys: Mapping[str, bytes],
        *,
        enable_exact_state_cache: bool = True,
    ) -> None:
        if not policy.policy_version:
            raise ValueError("policy_version required")
        self.policy = policy
        self.routes = dict(routes)
        self._hmac_keys = dict(hmac_keys)
        self.enable_exact_state_cache = bool(enable_exact_state_cache)
        self._cache: Dict[Tuple[str, str], BrokerResult] = {}

    @staticmethod
    def _normalize(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {str(k): SecureAICommunicationBroker._normalize(value[k]) for k in sorted(value, key=lambda x: str(x))}
        if isinstance(value, (list, tuple)):
            return [SecureAICommunicationBroker._normalize(x) for x in value]
        if isinstance(value, set):
            return sorted(SecureAICommunicationBroker._normalize(x) for x in value)
        if isinstance(value, Enum):
            return value.value
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        return str(value)

    @staticmethod
    def _valid_hash(value: Optional[str], allow_none: bool = False) -> bool:
        if value is None:
            return allow_none
        if not isinstance(value, str) or len(value) != 64:
            return False
        try:
            int(value, 16)
            return True
        except ValueError:
            return False

    @staticmethod
    def _valid_int(value: Any) -> bool:
        return isinstance(value, int) and not isinstance(value, bool)

    @staticmethod
    def _valid_score(value: Any) -> bool:
        return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 100

    @classmethod
    def signing_payload(cls, envelope: SecureEnvelope) -> bytes:
        payload = {
            "message_id": envelope.message_id,
            "sender_id": envelope.sender_id,
            "recipient_id": envelope.recipient_id,
            "purpose": envelope.purpose,
            "payload_sha256": envelope.payload_sha256,
            "issued_at_epoch_s": envelope.issued_at_epoch_s,
            "expires_at_epoch_s": envelope.expires_at_epoch_s,
            "nonce": envelope.nonce,
            "key_id": envelope.key_id,
            "sender_certificate_ref": envelope.sender_certificate_ref,
            "shared_state_fingerprint": envelope.shared_state_fingerprint,
            "delta_fingerprint": envelope.delta_fingerprint,
            "claims_authority": envelope.claims_authority,
            "requests_external_action": envelope.requests_external_action,
            "risk_score": envelope.risk_score,
            "schema_version": envelope.schema_version,
            "metadata": cls._normalize(envelope.metadata),
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

    @classmethod
    def sign_envelope(cls, envelope: SecureEnvelope, key: bytes) -> str:
        return hmac.new(key, cls.signing_payload(envelope), hashlib.sha256).hexdigest()

    @classmethod
    def request_fingerprint(cls, request: CommunicationRequest) -> str:
        # The HMAC secret itself is intentionally not part of the fingerprint.
        raw = json.dumps(cls._normalize(asdict(request)), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def _make(
        self,
        decision: BrokerDecision,
        reasons: Tuple[str, ...],
        fp: str,
        sender_authenticated: bool,
        signature_verified: bool,
        purpose_authorized: bool,
        replay_check_passed: bool,
    ) -> BrokerResult:
        return BrokerResult(
            decision=decision,
            reason_codes=tuple(reasons),
            request_fingerprint=fp,
            sender_authenticated=sender_authenticated,
            signature_verified=signature_verified,
            purpose_authorized=purpose_authorized,
            replay_check_passed=replay_check_passed,
            authoritative=False,
            message_sent=False,
            message_delivered=False,
            recipient_heard=False,
            action_executed=False,
            action_succeeded=False,
            cache_reused=False,
            created_unix_ns=time.time_ns(),
        )

    def _evaluate_uncached(self, request: CommunicationRequest) -> BrokerResult:
        fp = self.request_fingerprint(request)
        e = request.envelope

        if not request.request_id or not request.schema_version:
            return self._make(BrokerDecision.HOLD, ("MISSING_REQUEST_OR_SCHEMA",), fp, False, False, False, False)

        if not all([e.message_id, e.sender_id, e.recipient_id, e.purpose, e.nonce, e.key_id, e.schema_version]):
            return self._make(BrokerDecision.HOLD, ("MISSING_ENVELOPE_FIELD",), fp, False, False, False, False)

        if e.sender_id == e.recipient_id:
            return self._make(BrokerDecision.HOLD, ("SENDER_RECIPIENT_COLLISION",), fp, False, False, False, False)

        if not self._valid_hash(e.payload_sha256):
            return self._make(BrokerDecision.HOLD, ("INVALID_PAYLOAD_HASH",), fp, False, False, False, False)

        if not self._valid_hash(e.shared_state_fingerprint, allow_none=True):
            return self._make(BrokerDecision.HOLD, ("INVALID_SHARED_STATE_FINGERPRINT",), fp, False, False, False, False)

        if not self._valid_hash(e.delta_fingerprint, allow_none=True):
            return self._make(BrokerDecision.HOLD, ("INVALID_DELTA_FINGERPRINT",), fp, False, False, False, False)

        if not self._valid_int(request.observed_epoch_s) or request.observed_epoch_s < 0:
            return self._make(BrokerDecision.HOLD, ("INVALID_OBSERVED_TIME",), fp, False, False, False, False)

        if not self._valid_int(e.issued_at_epoch_s) or not self._valid_int(e.expires_at_epoch_s):
            return self._make(BrokerDecision.HOLD, ("INVALID_ENVELOPE_TIME",), fp, False, False, False, False)

        if e.expires_at_epoch_s <= e.issued_at_epoch_s:
            return self._make(BrokerDecision.DENY, ("INVALID_MESSAGE_LIFETIME",), fp, False, False, False, False)

        if e.expires_at_epoch_s - e.issued_at_epoch_s > self.policy.max_message_lifetime_seconds:
            return self._make(BrokerDecision.DENY, ("MESSAGE_LIFETIME_EXCEEDS_POLICY",), fp, False, False, False, False)

        if request.observed_epoch_s >= e.expires_at_epoch_s:
            return self._make(BrokerDecision.DENY, ("MESSAGE_EXPIRED",), fp, False, False, False, False)

        if e.issued_at_epoch_s - request.observed_epoch_s > self.policy.max_clock_skew_seconds:
            return self._make(BrokerDecision.HOLD, ("MESSAGE_ISSUED_TOO_FAR_IN_FUTURE",), fp, False, False, False, False)

        if not self._valid_score(e.risk_score):
            return self._make(BrokerDecision.HOLD, ("INVALID_RISK_SCORE",), fp, False, False, False, False)

        if request.nonce_already_seen:
            return self._make(BrokerDecision.DENY, ("REPLAY_NONCE_ALREADY_SEEN",), fp, False, False, False, False)

        route = self.routes.get(e.sender_id)
        if route is None:
            return self._make(BrokerDecision.DENY, ("UNKNOWN_SENDER",), fp, False, False, False, True)

        if route.disabled:
            return self._make(BrokerDecision.DENY, ("SENDER_DISABLED",), fp, False, False, False, True)

        if route.agent_id != e.sender_id or not route.key_id:
            return self._make(BrokerDecision.DENY, ("INVALID_SENDER_ROUTE",), fp, False, False, False, True)

        if request.expected_sender_route_version is not None and request.expected_sender_route_version != route.route_version:
            return self._make(BrokerDecision.HOLD, ("SENDER_ROUTE_VERSION_MISMATCH",), fp, False, False, False, True)

        if self.policy.require_tls and not e.tls_authenticated:
            return self._make(BrokerDecision.DENY, ("TLS_AUTHENTICATION_REQUIRED",), fp, False, False, False, True)

        if self.policy.require_mtls and not e.mtls_authenticated:
            return self._make(BrokerDecision.DENY, ("MTLS_AUTHENTICATION_REQUIRED",), fp, False, False, False, True)

        if self.policy.require_sender_certificate and not e.sender_certificate_ref:
            return self._make(BrokerDecision.HOLD, ("SENDER_CERTIFICATE_REFERENCE_REQUIRED",), fp, False, False, False, True)

        sender_authenticated = True

        if e.key_id != route.key_id:
            return self._make(BrokerDecision.DENY, ("KEY_ID_ROUTE_MISMATCH",), fp, sender_authenticated, False, False, True)

        key = self._hmac_keys.get(e.key_id)
        if key is None:
            return self._make(BrokerDecision.HOLD, ("HMAC_KEY_UNAVAILABLE",), fp, sender_authenticated, False, False, True)

        if not isinstance(e.signature_hex, str) or len(e.signature_hex) != 64:
            return self._make(BrokerDecision.DENY, ("INVALID_SIGNATURE_FORMAT",), fp, sender_authenticated, False, False, True)

        expected_signature = self.sign_envelope(e, key)
        signature_verified = hmac.compare_digest(expected_signature, e.signature_hex)
        if not signature_verified:
            return self._make(BrokerDecision.DENY, ("SIGNATURE_VERIFICATION_FAILED",), fp, sender_authenticated, False, False, True)

        if e.recipient_id not in set(route.allowed_destinations):
            return self._make(BrokerDecision.DENY, ("RECIPIENT_NOT_AUTHORIZED",), fp, sender_authenticated, True, False, True)

        if e.purpose not in set(route.allowed_purposes):
            return self._make(BrokerDecision.DENY, ("PURPOSE_NOT_AUTHORIZED",), fp, sender_authenticated, True, False, True)

        purpose_authorized = True

        if e.claims_authority:
            return self._make(
                BrokerDecision.HOLD,
                ("MESSAGE_CANNOT_SELF_GRANT_AUTHORITY",),
                fp, sender_authenticated, True, purpose_authorized, True
            )

        needs_human = (
            e.requests_external_action
            or e.risk_score > self.policy.max_risk_without_confirmation
            or e.purpose in set(self.policy.high_risk_purposes)
        )
        if needs_human and not (e.human_approved and e.approval_ref):
            return self._make(
                BrokerDecision.HUMAN_CONFIRM,
                ("HIGH_RISK_MESSAGE_REQUIRES_HUMAN_CONFIRMATION",),
                fp, sender_authenticated, True, purpose_authorized, True
            )

        return self._make(
            BrokerDecision.ALLOW_PREPARE,
            ("SECURE_ENVELOPE_VALID_PREPARE_ONLY",),
            fp, sender_authenticated, True, purpose_authorized, True
        )

    def evaluate(self, request: CommunicationRequest) -> BrokerResult:
        fp = self.request_fingerprint(request)
        key = (fp, self.policy.policy_version)

        if self.enable_exact_state_cache and key in self._cache:
            r = self._cache[key]
            return BrokerResult(
                decision=r.decision,
                reason_codes=r.reason_codes,
                request_fingerprint=fp,
                sender_authenticated=r.sender_authenticated,
                signature_verified=r.signature_verified,
                purpose_authorized=r.purpose_authorized,
                replay_check_passed=r.replay_check_passed,
                authoritative=False,
                message_sent=False,
                message_delivered=False,
                recipient_heard=False,
                action_executed=False,
                action_succeeded=False,
                cache_reused=True,
                created_unix_ns=time.time_ns(),
            )

        result = self._evaluate_uncached(request)
        if self.enable_exact_state_cache:
            self._cache[key] = result
        return result

    def clear_cache(self) -> None:
        self._cache.clear()

    def cache_size(self) -> int:
        return len(self._cache)
