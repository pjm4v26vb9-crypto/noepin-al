from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Iterable, Mapping, Optional, Tuple
import hashlib
import json
import math
import time


VERSION = "2.0.0-successor.20261102"
CREATOR = "NOEPIN / のえぴん"


class Effect(str, Enum):
    DENY = "DENY"
    ALLOW = "ALLOW"
    HOLD = "HOLD"
    HUMAN_CONFIRM = "HUMAN_CONFIRM"


class Decision(str, Enum):
    DENY = "DENY"
    ALLOW_CANDIDATE = "ALLOW_CANDIDATE"
    HOLD = "HOLD"
    HUMAN_CONFIRM = "HUMAN_CONFIRM"


@dataclass(frozen=True)
class PolicyRule:
    rule_id: str
    effect: Effect
    priority: int = 0
    actions: Tuple[str, ...] = ()
    resources: Tuple[str, ...] = ()
    roles: Tuple[str, ...] = ()
    purposes: Tuple[str, ...] = ()
    environments: Tuple[str, ...] = ()
    scopes: Tuple[str, ...] = ()
    required_flags: Tuple[str, ...] = ()
    forbidden_flags: Tuple[str, ...] = ()
    require_human_approval: bool = False
    enabled: bool = True

    def validate(self) -> None:
        if not self.rule_id or not self.rule_id.strip():
            raise ValueError("rule_id required")
        if isinstance(self.priority, bool) or not isinstance(self.priority, int):
            raise ValueError("priority must be int")
        if self.priority < -1_000_000 or self.priority > 1_000_000:
            raise ValueError("priority out of range")
        for group in (
            self.actions, self.resources, self.roles, self.purposes,
            self.environments, self.scopes, self.required_flags,
            self.forbidden_flags,
        ):
            if len(group) != len(set(group)):
                raise ValueError("duplicate condition")
            for item in group:
                if not isinstance(item, str) or not item.strip():
                    raise ValueError("conditions must be non-empty strings")
        if set(self.required_flags) & set(self.forbidden_flags):
            raise ValueError("same flag cannot be both required and forbidden")


@dataclass(frozen=True)
class PolicySet:
    policy_id: str
    policy_version: str
    authority_version: str
    rules: Tuple[PolicyRule, ...]
    active: bool = True
    expires_at_epoch: Optional[float] = None
    default_effect: Effect = Effect.DENY

    def validate(self) -> None:
        if not self.policy_id.strip() or not self.policy_version.strip() or not self.authority_version.strip():
            raise ValueError("policy identity/version required")
        if self.default_effect != Effect.DENY:
            raise ValueError("deny-by-default is mandatory")
        ids = set()
        for rule in self.rules:
            rule.validate()
            if rule.rule_id in ids:
                raise ValueError("duplicate rule_id")
            ids.add(rule.rule_id)
        if self.expires_at_epoch is not None:
            if not isinstance(self.expires_at_epoch, (int, float)) or isinstance(self.expires_at_epoch, bool):
                raise ValueError("expires_at_epoch must be numeric")
            if not math.isfinite(float(self.expires_at_epoch)):
                raise ValueError("expires_at_epoch must be finite")


@dataclass(frozen=True)
class PolicyRequest:
    request_id: str
    subject_id: str
    action: str
    resource: str
    role: str
    purpose: str
    environment: str
    scopes: Tuple[str, ...] = ()
    risk_flags: Tuple[str, ...] = ()
    human_approval_evidence: bool = False
    expected_policy_version: Optional[str] = None
    expected_authority_version: Optional[str] = None
    observed_at_epoch: float = 0.0
    context: Mapping[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        for name in ("request_id", "subject_id", "action", "resource", "role", "purpose", "environment"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} required")
        for group in (self.scopes, self.risk_flags):
            if len(group) != len(set(group)):
                raise ValueError("duplicate request values")
            if any(not isinstance(x, str) or not x.strip() for x in group):
                raise ValueError("request values must be non-empty strings")
        if not isinstance(self.observed_at_epoch, (int, float)) or isinstance(self.observed_at_epoch, bool):
            raise ValueError("observed_at_epoch must be numeric")
        if not math.isfinite(float(self.observed_at_epoch)):
            raise ValueError("observed_at_epoch must be finite")
        if len(self.context) > 64:
            raise ValueError("context too large")
        for k, v in self.context.items():
            if not isinstance(k, str) or not isinstance(v, str):
                raise ValueError("context must be string-string")


@dataclass(frozen=True)
class PolicyResult:
    decision: Decision
    reasons: Tuple[str, ...]
    matched_rule_ids: Tuple[str, ...]
    request_fingerprint: str
    policy_fingerprint: str
    result_fingerprint: str
    authoritative: bool = False
    truth_established: bool = False
    permission_granted: bool = False
    action_executed: bool = False
    action_succeeded: bool = False
    state_committed: bool = False
    cache_hit: bool = False


def _canonical(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha(obj) -> str:
    return hashlib.sha256(_canonical(obj).encode("utf-8")).hexdigest()


def _tuple_match(allowed: Tuple[str, ...], value: str) -> bool:
    return not allowed or value in allowed


def _scopes_match(required: Tuple[str, ...], actual: Tuple[str, ...]) -> bool:
    return not required or set(required).issubset(actual)


def _rule_matches(rule: PolicyRule, req: PolicyRequest) -> bool:
    if not rule.enabled:
        return False
    if not _tuple_match(rule.actions, req.action):
        return False
    if not _tuple_match(rule.resources, req.resource):
        return False
    if not _tuple_match(rule.roles, req.role):
        return False
    if not _tuple_match(rule.purposes, req.purpose):
        return False
    if not _tuple_match(rule.environments, req.environment):
        return False
    if not _scopes_match(rule.scopes, req.scopes):
        return False
    flags = set(req.risk_flags)
    if not set(rule.required_flags).issubset(flags):
        return False
    if set(rule.forbidden_flags) & flags:
        return False
    return True


class PolicyEngine:
    """Pure decision engine. It cannot execute actions or mutate external state."""

    def __init__(self, policy: PolicySet, *, enable_cache: bool = True):
        policy.validate()
        self._policy = policy
        self._enable_cache = bool(enable_cache)
        self._cache: dict[str, PolicyResult] = {}
        self._refresh_policy_materialized_state()

    @property
    def policy(self) -> PolicySet:
        return self._policy

    def replace_policy(self, policy: PolicySet) -> None:
        policy.validate()
        self._policy = policy
        self._cache.clear()
        self._refresh_policy_materialized_state()

    def _refresh_policy_materialized_state(self) -> None:
        self._policy_state_cache = self._build_policy_state()
        self._policy_fingerprint_cache = _sha(self._policy_state_cache)

    def _build_policy_state(self) -> dict:
        return {
            "policy_id": self._policy.policy_id,
            "policy_version": self._policy.policy_version,
            "authority_version": self._policy.authority_version,
            "active": self._policy.active,
            "expires_at_epoch": self._policy.expires_at_epoch,
            "default_effect": self._policy.default_effect.value,
            "rules": [
                {
                    **asdict(r),
                    "effect": r.effect.value,
                }
                for r in self._policy.rules
            ],
        }

    def _request_state(self, req: PolicyRequest) -> dict:
        return {
            "request_id": req.request_id,
            "subject_id": req.subject_id,
            "action": req.action,
            "resource": req.resource,
            "role": req.role,
            "purpose": req.purpose,
            "environment": req.environment,
            "scopes": list(req.scopes),
            "risk_flags": list(req.risk_flags),
            "human_approval_evidence": req.human_approval_evidence,
            "expected_policy_version": req.expected_policy_version,
            "expected_authority_version": req.expected_authority_version,
            "observed_at_epoch": req.observed_at_epoch,
            "context": dict(req.context),
        }

    def evaluate(self, req: PolicyRequest) -> PolicyResult:
        req.validate()
        self._policy.validate()
        request_state = self._request_state(req)
        policy_state = self._policy_state_cache
        request_fp = _sha(request_state)
        policy_fp = self._policy_fingerprint_cache
        cache_key = _sha({"request": request_state, "policy_fingerprint": policy_fp})
        if self._enable_cache and cache_key in self._cache:
            prior = self._cache[cache_key]
            return PolicyResult(**{**asdict(prior), "decision": prior.decision, "cache_hit": True})

        reasons: list[str] = []
        matched: list[PolicyRule] = []

        if not self._policy.active:
            decision = Decision.DENY
            reasons.append("POLICY_INACTIVE")
        elif self._policy.expires_at_epoch is not None and req.observed_at_epoch >= self._policy.expires_at_epoch:
            decision = Decision.DENY
            reasons.append("POLICY_EXPIRED")
        elif req.expected_policy_version and req.expected_policy_version != self._policy.policy_version:
            decision = Decision.HOLD
            reasons.append("POLICY_VERSION_MISMATCH")
        elif req.expected_authority_version and req.expected_authority_version != self._policy.authority_version:
            decision = Decision.HOLD
            reasons.append("AUTHORITY_VERSION_MISMATCH")
        else:
            matched = [r for r in self._policy.rules if _rule_matches(r, req)]
            if not matched:
                decision = Decision.DENY
                reasons.append("DENY_BY_DEFAULT")
            else:
                highest = max(r.priority for r in matched)
                top = [r for r in matched if r.priority == highest]
                effects = {r.effect for r in top}
                # deny wins at same priority; then hold; then human confirm; only then allow candidate
                if Effect.DENY in effects:
                    decision = Decision.DENY
                    reasons.append("EXPLICIT_DENY")
                elif Effect.HOLD in effects:
                    decision = Decision.HOLD
                    reasons.append("POLICY_HOLD")
                elif Effect.HUMAN_CONFIRM in effects or any(r.require_human_approval for r in top):
                    if req.human_approval_evidence:
                        decision = Decision.ALLOW_CANDIDATE
                        reasons.append("HUMAN_APPROVAL_EVIDENCE_PRESENT")
                    else:
                        decision = Decision.HUMAN_CONFIRM
                        reasons.append("HUMAN_CONFIRM_REQUIRED")
                elif Effect.ALLOW in effects:
                    decision = Decision.ALLOW_CANDIDATE
                    reasons.append("EXPLICIT_ALLOW_CANDIDATE")
                else:
                    decision = Decision.DENY
                    reasons.append("DENY_BY_DEFAULT")

        matched_ids = tuple(r.rule_id for r in sorted(matched, key=lambda x: (-x.priority, x.rule_id)))
        result_core = {
            "decision": decision.value,
            "reasons": reasons,
            "matched_rule_ids": matched_ids,
            "request_fingerprint": request_fp,
            "policy_fingerprint": policy_fp,
        }
        result = PolicyResult(
            decision=decision,
            reasons=tuple(reasons),
            matched_rule_ids=matched_ids,
            request_fingerprint=request_fp,
            policy_fingerprint=policy_fp,
            result_fingerprint=_sha(result_core),
        )
        if self._enable_cache:
            self._cache[cache_key] = result
        return result


def sample_policy(extra_rules: int = 0) -> PolicySet:
    rules = [
        PolicyRule("deny-prod-delete", Effect.DENY, priority=100, actions=("delete",), environments=("production",)),
        PolicyRule("deny-secret-export", Effect.DENY, priority=100, actions=("export",), required_flags=("secret",)),
        PolicyRule("hold-admin-mismatch", Effect.HOLD, priority=90, roles=("admin",), required_flags=("authority_uncertain",)),
        PolicyRule("human-prod-write", Effect.HUMAN_CONFIRM, priority=80, actions=("write",), environments=("production",), require_human_approval=True),
        PolicyRule("allow-stage-read", Effect.ALLOW, priority=50, actions=("read",), environments=("staging",), purposes=("diagnostics",)),
        PolicyRule("allow-prod-read", Effect.ALLOW, priority=50, actions=("read",), environments=("production",), roles=("observer",), purposes=("diagnostics",)),
        PolicyRule("allow-stage-write", Effect.ALLOW, priority=40, actions=("write",), environments=("staging",), roles=("operator",), purposes=("maintenance",), scopes=("resource:write",)),
    ]
    for i in range(extra_rules):
        rules.append(PolicyRule(f"noise-{i:04d}", Effect.ALLOW, priority=1, actions=(f"noop-{i}",), environments=("sandbox",)))
    return PolicySet("noepin-al-026", "policy-v2", "auth-v7", tuple(rules), active=True, expires_at_epoch=4_102_444_800.0)


def sample_request(**overrides) -> PolicyRequest:
    base = dict(
        request_id="req-001",
        subject_id="agent-a",
        action="read",
        resource="db:orders",
        role="observer",
        purpose="diagnostics",
        environment="production",
        scopes=("resource:read",),
        risk_flags=(),
        human_approval_evidence=False,
        expected_policy_version="policy-v2",
        expected_authority_version="auth-v7",
        observed_at_epoch=1_800_000_000.0,
        context={"tenant": "alpha"},
    )
    base.update(overrides)
    return PolicyRequest(**base)
