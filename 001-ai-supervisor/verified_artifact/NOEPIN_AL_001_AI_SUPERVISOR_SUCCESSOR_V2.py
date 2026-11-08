from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple
import hashlib
import json
import time


class Decision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    HOLD = "HOLD"
    HUMAN_CONFIRM = "HUMAN_CONFIRM"


class GatewayDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    HOLD = "HOLD"
    HUMAN_CONFIRM = "HUMAN_CONFIRM"


@dataclass(frozen=True)
class RolePolicy:
    role: str
    allowed_actions: frozenset[str] = frozenset()
    denied_actions: frozenset[str] = frozenset()
    allowed_resources: frozenset[str] = frozenset({"*"})
    max_risk: int = 50
    human_confirm_actions: frozenset[str] = frozenset()
    human_confirm_risk: int = 30


@dataclass(frozen=True)
class SupervisionRequest:
    agent_id: str
    role: str
    action: str
    resource: str
    risk: int
    context: Mapping[str, Any] = field(default_factory=dict)
    irreversible: bool = False
    external_side_effect: bool = False
    requested_effect: Optional[str] = None
    authority_refs: Mapping[str, str] = field(default_factory=dict)
    schema_version: str = "1"


@dataclass(frozen=True)
class DecisionRecord:
    decision: Decision
    reason_codes: Tuple[str, ...]
    request_fingerprint: str
    policy_version: str
    gateway_decision: GatewayDecision
    authoritative: bool = False
    action_executed: bool = False
    cache_reused: bool = False
    created_unix_ns: int = 0

    def stable_payload(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reason_codes": list(self.reason_codes),
            "request_fingerprint": self.request_fingerprint,
            "policy_version": self.policy_version,
            "gateway_decision": self.gateway_decision.value,
            "authoritative": self.authoritative,
            "action_executed": self.action_executed,
            "cache_reused": self.cache_reused,
        }


@dataclass(frozen=True)
class AuditEvent:
    sequence: int
    request_fingerprint: str
    decision: str
    reason_codes: Tuple[str, ...]
    previous_hash: str
    event_hash: str


class AISupervisor:
    """
    NOEPIN AL 001 — AI Supervisor

    Scope:
      * Supervises requests and returns ALLOW / DENY / HOLD / HUMAN_CONFIRM.
      * Never performs the requested action.
      * Never converts a supervisor decision into Action Success.
      * Treats DCSR/cache as state infrastructure only. Cache hits are validated
        against exact request fingerprint + policy version + gateway decision.
    """

    def __init__(
        self,
        role_policies: Mapping[str, RolePolicy],
        *,
        policy_version: str = "1",
        registered_agents: Optional[Mapping[str, str]] = None,
        enable_exact_state_cache: bool = True,
    ) -> None:
        if not policy_version:
            raise ValueError("policy_version is required")
        self._policies = dict(role_policies)
        self._policy_version = str(policy_version)
        self._registered_agents = dict(registered_agents or {})
        self._enable_cache = bool(enable_exact_state_cache)
        self._cache: Dict[Tuple[str, str, str], DecisionRecord] = {}
        self._audit: List[AuditEvent] = []

    @property
    def policy_version(self) -> str:
        return self._policy_version

    @staticmethod
    def _normalize(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {str(k): AISupervisor._normalize(value[k]) for k in sorted(value, key=lambda x: str(x))}
        if isinstance(value, (list, tuple)):
            return [AISupervisor._normalize(v) for v in value]
        if isinstance(value, set):
            return sorted(AISupervisor._normalize(v) for v in value)
        if isinstance(value, Enum):
            return value.value
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        return str(value)

    @classmethod
    def fingerprint_request(cls, request: SupervisionRequest) -> str:
        payload = cls._normalize(asdict(request))
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _resource_allowed(resource: str, allowed: Iterable[str]) -> bool:
        allowed_set = set(allowed)
        if "*" in allowed_set:
            return True
        return resource in allowed_set

    def _validate_request(self, r: SupervisionRequest) -> Tuple[bool, Tuple[str, ...]]:
        reasons: List[str] = []
        if not r.agent_id or not r.role or not r.action or not r.resource:
            reasons.append("MISSING_REQUIRED_FIELD")
        if not isinstance(r.risk, int) or isinstance(r.risk, bool) or r.risk < 0 or r.risk > 100:
            reasons.append("INVALID_RISK")
        if not r.schema_version:
            reasons.append("MISSING_SCHEMA_VERSION")
        return (len(reasons) == 0, tuple(reasons))

    def _decide_uncached(
        self,
        r: SupervisionRequest,
        gateway_decision: GatewayDecision,
    ) -> Tuple[Decision, Tuple[str, ...]]:
        valid, validation_reasons = self._validate_request(r)
        if not valid:
            return Decision.HOLD, validation_reasons

        if gateway_decision == GatewayDecision.DENY:
            return Decision.DENY, ("SECURITY_GATEWAY_DENY",)
        if gateway_decision == GatewayDecision.HOLD:
            return Decision.HOLD, ("SECURITY_GATEWAY_HOLD",)
        if gateway_decision == GatewayDecision.HUMAN_CONFIRM:
            return Decision.HUMAN_CONFIRM, ("SECURITY_GATEWAY_HUMAN_CONFIRM",)

        expected_role = self._registered_agents.get(r.agent_id)
        if self._registered_agents and expected_role is None:
            return Decision.HOLD, ("UNKNOWN_AGENT",)
        if expected_role is not None and expected_role != r.role:
            return Decision.DENY, ("AGENT_ROLE_MISMATCH",)

        policy = self._policies.get(r.role)
        if policy is None:
            return Decision.HOLD, ("UNKNOWN_ROLE",)

        if r.action in policy.denied_actions:
            return Decision.DENY, ("EXPLICIT_ACTION_DENY",)

        if r.action not in policy.allowed_actions:
            return Decision.DENY, ("ACTION_NOT_ALLOWED",)

        if not self._resource_allowed(r.resource, policy.allowed_resources):
            return Decision.DENY, ("RESOURCE_NOT_ALLOWED",)

        if r.risk > policy.max_risk:
            return Decision.DENY, ("RISK_EXCEEDS_ROLE_MAXIMUM",)

        if r.irreversible:
            return Decision.HUMAN_CONFIRM, ("IRREVERSIBLE_REQUIRES_HUMAN_CONFIRM",)

        if r.external_side_effect:
            return Decision.HUMAN_CONFIRM, ("EXTERNAL_SIDE_EFFECT_REQUIRES_HUMAN_CONFIRM",)

        if r.action in policy.human_confirm_actions:
            return Decision.HUMAN_CONFIRM, ("ACTION_REQUIRES_HUMAN_CONFIRM",)

        if r.risk >= policy.human_confirm_risk:
            return Decision.HUMAN_CONFIRM, ("RISK_REQUIRES_HUMAN_CONFIRM",)

        return Decision.ALLOW, ("POLICY_ALLOW",)

    def supervise(
        self,
        request: SupervisionRequest,
        *,
        gateway_decision: GatewayDecision = GatewayDecision.ALLOW,
    ) -> DecisionRecord:
        fp = self.fingerprint_request(request)
        cache_key = (fp, self._policy_version, gateway_decision.value)

        if self._enable_cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                record = DecisionRecord(
                    decision=cached.decision,
                    reason_codes=cached.reason_codes,
                    request_fingerprint=fp,
                    policy_version=self._policy_version,
                    gateway_decision=gateway_decision,
                    authoritative=False,
                    action_executed=False,
                    cache_reused=True,
                    created_unix_ns=time.time_ns(),
                )
                self._append_audit(record)
                return record

        decision, reasons = self._decide_uncached(request, gateway_decision)
        record = DecisionRecord(
            decision=decision,
            reason_codes=tuple(reasons),
            request_fingerprint=fp,
            policy_version=self._policy_version,
            gateway_decision=gateway_decision,
            authoritative=False,
            action_executed=False,
            cache_reused=False,
            created_unix_ns=time.time_ns(),
        )
        if self._enable_cache:
            self._cache[cache_key] = record
        self._append_audit(record)
        return record

    def _append_audit(self, record: DecisionRecord) -> None:
        previous_hash = self._audit[-1].event_hash if self._audit else "0" * 64
        seq = len(self._audit) + 1
        payload = {
            "sequence": seq,
            "request_fingerprint": record.request_fingerprint,
            "decision": record.decision.value,
            "reason_codes": list(record.reason_codes),
            "previous_hash": previous_hash,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        event_hash = hashlib.sha256(raw).hexdigest()
        self._audit.append(
            AuditEvent(
                sequence=seq,
                request_fingerprint=record.request_fingerprint,
                decision=record.decision.value,
                reason_codes=record.reason_codes,
                previous_hash=previous_hash,
                event_hash=event_hash,
            )
        )

    def verify_audit_chain(self) -> bool:
        previous = "0" * 64
        for expected_seq, event in enumerate(self._audit, start=1):
            if event.sequence != expected_seq or event.previous_hash != previous:
                return False
            payload = {
                "sequence": event.sequence,
                "request_fingerprint": event.request_fingerprint,
                "decision": event.decision,
                "reason_codes": list(event.reason_codes),
                "previous_hash": event.previous_hash,
            }
            raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
            if hashlib.sha256(raw).hexdigest() != event.event_hash:
                return False
            previous = event.event_hash
        return True

    def audit_events(self) -> Tuple[AuditEvent, ...]:
        return tuple(self._audit)

    def cache_size(self) -> int:
        return len(self._cache)

    def clear_cache(self) -> None:
        self._cache.clear()

    def rotate_policy_version(self, version: str) -> None:
        if not version:
            raise ValueError("version is required")
        self._policy_version = str(version)
        self.clear_cache()


def default_policies() -> Dict[str, RolePolicy]:
    return {
        "observer": RolePolicy(
            role="observer",
            allowed_actions=frozenset({"read", "inspect", "summarize"}),
            denied_actions=frozenset({"write", "delete", "execute"}),
            allowed_resources=frozenset({"public", "project_read"}),
            max_risk=20,
            human_confirm_risk=15,
        ),
        "developer": RolePolicy(
            role="developer",
            allowed_actions=frozenset({"read", "inspect", "summarize", "propose_patch", "run_test"}),
            denied_actions=frozenset({"delete_production", "publish_public"}),
            allowed_resources=frozenset({"public", "project_read", "sandbox", "test_runtime"}),
            max_risk=60,
            human_confirm_actions=frozenset({"propose_patch"}),
            human_confirm_risk=40,
        ),
        "operator": RolePolicy(
            role="operator",
            allowed_actions=frozenset({"read", "inspect", "run_test", "deploy_candidate", "rollback_candidate"}),
            denied_actions=frozenset({"disable_audit", "bypass_policy"}),
            allowed_resources=frozenset({"public", "project_read", "sandbox", "test_runtime", "candidate_runtime"}),
            max_risk=70,
            human_confirm_actions=frozenset({"deploy_candidate", "rollback_candidate"}),
            human_confirm_risk=35,
        ),
    }


__all__ = [
    "Decision",
    "GatewayDecision",
    "RolePolicy",
    "SupervisionRequest",
    "DecisionRecord",
    "AuditEvent",
    "AISupervisor",
    "default_policies",
]
