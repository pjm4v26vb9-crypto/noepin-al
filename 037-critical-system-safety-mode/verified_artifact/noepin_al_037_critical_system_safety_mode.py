"""NOEPIN AL 037 — Critical System Safety Mode / 重要システム安全モード.

Creator / Project Owner / Original Concept / Architecture Direction:
    NOEPIN / のえぴん
Implementation / analysis / documentation support:
    AI-assisted using ChatGPT
License / Rights:
    NOT SPECIFIED

This module is a PRE-EXECUTION CONTROL PLANE. It evaluates requests and returns
ALLOW / HUMAN_APPROVAL / HOLD / DENY. It never executes operations, grants
permissions, persists state, or treats DCSR cache/materialization as authority.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict, replace
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Dict, FrozenSet, Iterable, Mapping, Optional, Sequence, Tuple

TECHNOLOGY_NUMBER = 37
TECHNOLOGY_NAME = "重要システム安全モード"
ARTIFACT_VERSION = "2.0.0"
CREATOR = "NOEPIN / のえぴん"
LICENSE_STATUS = "NOT SPECIFIED"


class Decision(str, Enum):
    ALLOW = "ALLOW"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"
    HOLD = "HOLD"
    DENY = "DENY"


class Mode(str, Enum):
    SAFE_PROFILE = "SAFE_PROFILE"
    OFFLINE = "OFFLINE"
    MANUAL_OVERRIDE = "MANUAL_OVERRIDE"


class SafetyModeError(ValueError):
    """Base error for malformed or mismatched safety-mode inputs."""


class FingerprintMismatch(SafetyModeError):
    """Raised when a DCSR delta is applied to the wrong base state."""


def _stable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, frozenset):
        return sorted(_stable(v) for v in value)
    if isinstance(value, set):
        return sorted(_stable(v) for v in value)
    if isinstance(value, tuple):
        return [_stable(v) for v in value]
    if isinstance(value, list):
        return [_stable(v) for v in value]
    if isinstance(value, Mapping):
        return {str(k): _stable(value[k]) for k in sorted(value, key=lambda x: str(x))}
    if hasattr(value, "__dataclass_fields__"):
        return _stable(asdict(value))
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(_stable(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SafetyRequest:
    request_id: str
    actor: str
    operation: str
    resource: str
    risk_level: int = 0
    impact_scope: int = 0
    requested_capabilities: FrozenSet[str] = field(default_factory=frozenset)
    metadata: Mapping[str, str] = field(default_factory=dict)
    network_required: bool = False
    offline_mode: bool = False
    manual_override_requested: bool = False
    expected_policy_version: Optional[str] = None


@dataclass(frozen=True)
class ApprovalEvidence:
    approval_id: str = ""
    actor: str = ""
    operation: str = ""
    resource: str = ""
    verified_by_external_authority: bool = False
    issued_at: int = 0
    expires_at: int = 0
    revoked: bool = False

    def valid_for(self, req: SafetyRequest, now: int) -> bool:
        return (
            self.verified_by_external_authority
            and not self.revoked
            and bool(self.approval_id)
            and self.actor == req.actor
            and self.operation == req.operation
            and self.resource == req.resource
            and self.issued_at <= now < self.expires_at
        )


@dataclass(frozen=True)
class OverrideEvidence:
    override_id: str = ""
    actor: str = ""
    allowed_operations: FrozenSet[str] = field(default_factory=frozenset)
    allowed_resources: FrozenSet[str] = field(default_factory=frozenset)
    verified_by_external_authority: bool = False
    issued_at: int = 0
    expires_at: int = 0
    revoked: bool = False

    def valid_for(self, req: SafetyRequest, now: int) -> bool:
        return (
            self.verified_by_external_authority
            and not self.revoked
            and bool(self.override_id)
            and self.actor == req.actor
            and req.operation in self.allowed_operations
            and req.resource in self.allowed_resources
            and self.issued_at <= now < self.expires_at
        )


@dataclass(frozen=True)
class AuthorityContext:
    active_actor: bool
    actor_revoked: bool
    permission_grants: FrozenSet[str]
    authority_epoch: str
    approval: ApprovalEvidence = field(default_factory=ApprovalEvidence)
    override: OverrideEvidence = field(default_factory=OverrideEvidence)

    def has_permission(self, req: SafetyRequest) -> bool:
        exact = f"{req.operation}@{req.resource}"
        op_wildcard = f"{req.operation}@*"
        return exact in self.permission_grants or op_wildcard in self.permission_grants


@dataclass(frozen=True)
class SafeProfile:
    profile_id: str
    policy_version: str
    issued_at: int
    expires_at: int
    revoked: bool
    allowed_operations: FrozenSet[str]
    denied_operations: FrozenSet[str]
    human_approval_operations: FrozenSet[str]
    offline_allowed_operations: FrozenSet[str]
    allowed_capabilities: FrozenSet[str]
    required_metadata: FrozenSet[str]
    max_risk_allow: int = 1
    max_impact_allow: int = 1
    max_risk_human_approval: int = 4
    max_impact_human_approval: int = 4
    require_offline_for_critical: bool = False

    def validate(self) -> Tuple[str, ...]:
        errors = []
        if not self.profile_id:
            errors.append("PROFILE_ID_MISSING")
        if not self.policy_version:
            errors.append("POLICY_VERSION_MISSING")
        if self.expires_at <= self.issued_at:
            errors.append("PROFILE_TIME_RANGE_INVALID")
        if not 0 <= self.max_risk_allow <= 5:
            errors.append("MAX_RISK_ALLOW_INVALID")
        if not 0 <= self.max_impact_allow <= 5:
            errors.append("MAX_IMPACT_ALLOW_INVALID")
        if not 0 <= self.max_risk_human_approval <= 5:
            errors.append("MAX_RISK_HUMAN_INVALID")
        if not 0 <= self.max_impact_human_approval <= 5:
            errors.append("MAX_IMPACT_HUMAN_INVALID")
        if self.allowed_operations & self.denied_operations:
            errors.append("ALLOW_DENY_OVERLAP")
        return tuple(errors)


@dataclass(frozen=True)
class SafetyDecision:
    decision: Decision
    reasons: Tuple[str, ...]
    modes: Tuple[Mode, ...]
    request_fingerprint: str
    policy_fingerprint: str
    authority_fingerprint: str
    result_fingerprint: str
    dcsr_cache_hit: bool
    provisional: bool = False
    action_executed: bool = False
    permission_granted: bool = False
    action_success: bool = False

    def canonical_record(self) -> Dict[str, Any]:
        return _stable(asdict(self))


@dataclass(frozen=True)
class PolicyDelta:
    base_fingerprint: str
    target_fingerprint: str
    scalar_changes: Mapping[str, Any]
    added_operations: FrozenSet[str]
    removed_operations: FrozenSet[str]
    added_denied_operations: FrozenSet[str]
    removed_denied_operations: FrozenSet[str]


def safe_profile_from_mapping(raw: Mapping[str, Any]) -> SafeProfile:
    """Normalize an untrusted mapping into a validated SafeProfile.

    Parsing does not grant authority. Invalid policy data raises SafetyModeError so
    the caller can fail closed.
    """
    try:
        p = SafeProfile(
            profile_id=str(raw["profile_id"]),
            policy_version=str(raw["policy_version"]),
            issued_at=int(raw["issued_at"]),
            expires_at=int(raw["expires_at"]),
            revoked=bool(raw.get("revoked", False)),
            allowed_operations=frozenset(map(str, raw.get("allowed_operations", ()))),
            denied_operations=frozenset(map(str, raw.get("denied_operations", ()))),
            human_approval_operations=frozenset(map(str, raw.get("human_approval_operations", ()))),
            offline_allowed_operations=frozenset(map(str, raw.get("offline_allowed_operations", ()))),
            allowed_capabilities=frozenset(map(str, raw.get("allowed_capabilities", ()))),
            required_metadata=frozenset(map(str, raw.get("required_metadata", ()))),
            max_risk_allow=int(raw.get("max_risk_allow", 1)),
            max_impact_allow=int(raw.get("max_impact_allow", 1)),
            max_risk_human_approval=int(raw.get("max_risk_human_approval", 4)),
            max_impact_human_approval=int(raw.get("max_impact_human_approval", 4)),
            require_offline_for_critical=bool(raw.get("require_offline_for_critical", False)),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise SafetyModeError("POLICY_PARSE_ERROR") from exc
    errors = p.validate()
    if errors:
        raise SafetyModeError(";".join(errors))
    return p


def _request_validation_reasons(req: SafetyRequest) -> Tuple[str, ...]:
    reasons = []
    if not req.request_id:
        reasons.append("REQUEST_ID_MISSING")
    if not req.actor:
        reasons.append("ACTOR_MISSING")
    if not req.operation:
        reasons.append("OPERATION_MISSING")
    if not req.resource:
        reasons.append("RESOURCE_MISSING")
    if not isinstance(req.risk_level, int) or not 0 <= req.risk_level <= 5:
        reasons.append("RISK_LEVEL_INVALID")
    if not isinstance(req.impact_scope, int) or not 0 <= req.impact_scope <= 5:
        reasons.append("IMPACT_SCOPE_INVALID")
    return tuple(reasons)


def _authority_public_state(auth: AuthorityContext) -> Dict[str, Any]:
    """State used for authority fingerprinting; contains no secrets."""
    return {
        "active_actor": auth.active_actor,
        "actor_revoked": auth.actor_revoked,
        "permission_grants": sorted(auth.permission_grants),
        "authority_epoch": auth.authority_epoch,
        "approval": asdict(auth.approval),
        "override": _stable(asdict(auth.override)),
    }


def _build_decision(
    decision: Decision,
    reasons: Sequence[str],
    modes: Sequence[Mode],
    req: SafetyRequest,
    profile: SafeProfile,
    auth: AuthorityContext,
    cache_hit: bool,
) -> SafetyDecision:
    req_fp = fingerprint(req)
    policy_fp = fingerprint(profile)
    auth_fp = fingerprint(_authority_public_state(auth))
    core = {
        "decision": decision.value,
        "reasons": list(reasons),
        "modes": [m.value for m in modes],
        "request_fingerprint": req_fp,
        "policy_fingerprint": policy_fp,
        "authority_fingerprint": auth_fp,
        "provisional": False,
        "action_executed": False,
        "permission_granted": False,
        "action_success": False,
    }
    return SafetyDecision(
        decision=decision,
        reasons=tuple(reasons),
        modes=tuple(modes),
        request_fingerprint=req_fp,
        policy_fingerprint=policy_fp,
        authority_fingerprint=auth_fp,
        result_fingerprint=fingerprint(core),
        dcsr_cache_hit=cache_hit,
    )


def evaluate(
    req: SafetyRequest,
    profile: SafeProfile,
    auth: AuthorityContext,
    *,
    now: int,
    cache_hit: bool = False,
) -> SafetyDecision:
    """Evaluate a critical-system request without performing any side effect."""
    modes = [Mode.SAFE_PROFILE]
    if req.offline_mode:
        modes.append(Mode.OFFLINE)
    if req.manual_override_requested:
        modes.append(Mode.MANUAL_OVERRIDE)

    invalid = _request_validation_reasons(req)
    if invalid:
        return _build_decision(Decision.DENY, invalid, modes, req, profile, auth, cache_hit)

    p_errors = profile.validate()
    if p_errors:
        return _build_decision(Decision.DENY, ("PROFILE_INVALID",) + p_errors, modes, req, profile, auth, cache_hit)
    if profile.revoked:
        return _build_decision(Decision.DENY, ("PROFILE_REVOKED",), modes, req, profile, auth, cache_hit)
    if not profile.issued_at <= now < profile.expires_at:
        return _build_decision(Decision.DENY, ("PROFILE_EXPIRED_OR_NOT_YET_VALID",), modes, req, profile, auth, cache_hit)
    if req.expected_policy_version and req.expected_policy_version != profile.policy_version:
        return _build_decision(Decision.DENY, ("POLICY_VERSION_MISMATCH",), modes, req, profile, auth, cache_hit)

    if not auth.active_actor or auth.actor_revoked:
        return _build_decision(Decision.DENY, ("ACTOR_NOT_ACTIVE",), modes, req, profile, auth, cache_hit)
    if not auth.authority_epoch:
        return _build_decision(Decision.DENY, ("AUTHORITY_EPOCH_MISSING",), modes, req, profile, auth, cache_hit)

    missing_meta = tuple(sorted(k for k in profile.required_metadata if not str(req.metadata.get(k, "")).strip()))
    if missing_meta:
        return _build_decision(Decision.HOLD, ("REQUIRED_METADATA_MISSING",) + missing_meta, modes, req, profile, auth, cache_hit)

    if req.operation in profile.denied_operations:
        return _build_decision(Decision.DENY, ("OPERATION_EXPLICITLY_DENIED",), modes, req, profile, auth, cache_hit)

    if req.operation not in profile.allowed_operations and req.operation not in profile.human_approval_operations:
        return _build_decision(Decision.DENY, ("OPERATION_NOT_IN_SAFE_PROFILE",), modes, req, profile, auth, cache_hit)

    unknown_caps = tuple(sorted(req.requested_capabilities - profile.allowed_capabilities))
    if unknown_caps:
        return _build_decision(Decision.DENY, ("CAPABILITY_NOT_ALLOWED",) + unknown_caps, modes, req, profile, auth, cache_hit)

    if not auth.has_permission(req):
        return _build_decision(Decision.DENY, ("EXTERNAL_PERMISSION_MISSING",), modes, req, profile, auth, cache_hit)

    if req.offline_mode and req.network_required:
        return _build_decision(Decision.DENY, ("NETWORK_REQUIRED_IN_OFFLINE_MODE",), modes, req, profile, auth, cache_hit)
    if req.offline_mode and req.operation not in profile.offline_allowed_operations:
        return _build_decision(Decision.DENY, ("OPERATION_NOT_ALLOWED_OFFLINE",), modes, req, profile, auth, cache_hit)
    if profile.require_offline_for_critical and (req.risk_level >= 3 or req.impact_scope >= 3) and not req.offline_mode:
        return _build_decision(Decision.HOLD, ("CRITICAL_OPERATION_REQUIRES_OFFLINE_MODE",), modes, req, profile, auth, cache_hit)

    if req.risk_level > profile.max_risk_human_approval or req.impact_scope > profile.max_impact_human_approval:
        return _build_decision(Decision.DENY, ("RISK_OR_IMPACT_EXCEEDS_HUMAN_APPROVAL_CEILING",), modes, req, profile, auth, cache_hit)

    needs_human = (
        req.operation in profile.human_approval_operations
        or req.risk_level > profile.max_risk_allow
        or req.impact_scope > profile.max_impact_allow
        or req.manual_override_requested
    )
    if needs_human:
        approval_ok = auth.approval.valid_for(req, now)
        override_ok = req.manual_override_requested and auth.override.valid_for(req, now)
        if approval_ok or override_ok:
            reason = "EXTERNAL_APPROVAL_VALID" if approval_ok else "SCOPED_MANUAL_OVERRIDE_VALID"
            return _build_decision(Decision.ALLOW, (reason, "PRE_EXECUTION_ONLY"), modes, req, profile, auth, cache_hit)
        return _build_decision(Decision.HUMAN_APPROVAL, ("EXTERNAL_HUMAN_APPROVAL_REQUIRED",), modes, req, profile, auth, cache_hit)

    return _build_decision(Decision.ALLOW, ("SAFE_PROFILE_MATCH", "PRE_EXECUTION_ONLY"), modes, req, profile, auth, cache_hit)


@dataclass
class PreparedSafetyEvaluator:
    """DCSR-limited prepared-state evaluator.

    The cache reuses exact evaluation results only while policy, authority, request,
    and validity interval still match. It cannot create permissions or approvals.
    """
    profile: SafeProfile
    _cache: Dict[str, Tuple[int, SafetyDecision]] = field(default_factory=dict)
    _profile_fp: str = field(init=False)

    def __post_init__(self) -> None:
        self._profile_fp = fingerprint(self.profile)

    def _key(self, req: SafetyRequest, auth: AuthorityContext) -> str:
        return fingerprint({
            "request": req,
            "policy_fingerprint": self._profile_fp,
            "authority": _authority_public_state(auth),
        })

    def _valid_until(self, auth: AuthorityContext, now: int) -> int:
        # The cached result may change at any future validity boundary.
        candidates = [self.profile.expires_at]
        for boundary in (
            auth.approval.issued_at, auth.approval.expires_at,
            auth.override.issued_at, auth.override.expires_at,
        ):
            if boundary > now:
                candidates.append(boundary)
        return min(candidates)

    def evaluate(self, req: SafetyRequest, auth: AuthorityContext, *, now: int) -> SafetyDecision:
        key = self._key(req, auth)
        item = self._cache.get(key)
        if item is not None:
            valid_until, prior = item
            if now < valid_until and self.profile.issued_at <= now:
                return replace(prior, dcsr_cache_hit=True)
            self._cache.pop(key, None)
        result = evaluate(req, self.profile, auth, now=now, cache_hit=False)
        self._cache[key] = (self._valid_until(auth, now), result)
        return result

    def invalidate_all(self) -> None:
        self._cache.clear()

    @property
    def cache_entries(self) -> int:
        return len(self._cache)


def evaluate_unprepared(raw_policy: Mapping[str, Any], req: SafetyRequest, auth: AuthorityContext, *, now: int) -> SafetyDecision:
    """Reference path that reparses/validates the full policy for each evaluation."""
    return evaluate(req, safe_profile_from_mapping(raw_policy), auth, now=now, cache_hit=False)


def compute_policy_delta(base: SafeProfile, target: SafeProfile) -> PolicyDelta:
    scalar_names = (
        "profile_id", "policy_version", "issued_at", "expires_at", "revoked",
        "human_approval_operations", "offline_allowed_operations", "allowed_capabilities",
        "required_metadata", "max_risk_allow", "max_impact_allow",
        "max_risk_human_approval", "max_impact_human_approval", "require_offline_for_critical",
    )
    scalar_changes: Dict[str, Any] = {}
    for name in scalar_names:
        a = getattr(base, name)
        b = getattr(target, name)
        if a != b:
            scalar_changes[name] = _stable(b)
    return PolicyDelta(
        base_fingerprint=fingerprint(base),
        target_fingerprint=fingerprint(target),
        scalar_changes=scalar_changes,
        added_operations=target.allowed_operations - base.allowed_operations,
        removed_operations=base.allowed_operations - target.allowed_operations,
        added_denied_operations=target.denied_operations - base.denied_operations,
        removed_denied_operations=base.denied_operations - target.denied_operations,
    )


def apply_policy_delta(base: SafeProfile, delta: PolicyDelta) -> SafeProfile:
    if fingerprint(base) != delta.base_fingerprint:
        raise FingerprintMismatch("BASE_FINGERPRINT_MISMATCH")
    data = asdict(base)
    for key, value in delta.scalar_changes.items():
        if key in {
            "human_approval_operations", "offline_allowed_operations", "allowed_capabilities", "required_metadata"
        }:
            data[key] = frozenset(value)
        else:
            data[key] = value
    data["allowed_operations"] = (base.allowed_operations | delta.added_operations) - delta.removed_operations
    data["denied_operations"] = (base.denied_operations | delta.added_denied_operations) - delta.removed_denied_operations
    rebuilt = SafeProfile(**data)
    if fingerprint(rebuilt) != delta.target_fingerprint:
        raise FingerprintMismatch("TARGET_FINGERPRINT_MISMATCH")
    return rebuilt


def audit_record(decision: SafetyDecision) -> Dict[str, Any]:
    """Return an audit-ready immutable-data record. No persistence is performed."""
    return decision.canonical_record()


def default_profile(now: int = 1_700_000_000) -> SafeProfile:
    return SafeProfile(
        profile_id="critical-system-default",
        policy_version="2026.11",
        issued_at=now - 1000,
        expires_at=now + 86_400,
        revoked=False,
        allowed_operations=frozenset({"read_status", "inspect_metrics", "simulate_change"}),
        denied_operations=frozenset({"disable_safety", "erase_audit", "grant_permission", "execute_shell"}),
        human_approval_operations=frozenset({"apply_config", "restart_service"}),
        offline_allowed_operations=frozenset({"read_status", "inspect_metrics", "simulate_change", "apply_config"}),
        allowed_capabilities=frozenset({"read", "simulate", "prepare_config"}),
        required_metadata=frozenset({"ticket", "purpose"}),
        max_risk_allow=1,
        max_impact_allow=1,
        max_risk_human_approval=4,
        max_impact_human_approval=4,
        require_offline_for_critical=True,
    )


def default_authority() -> AuthorityContext:
    return AuthorityContext(
        active_actor=True,
        actor_revoked=False,
        permission_grants=frozenset({
            "read_status@plant:A", "inspect_metrics@plant:A", "simulate_change@plant:A",
            "apply_config@plant:A", "restart_service@plant:A",
        }),
        authority_epoch="epoch-001",
    )


__all__ = [
    "Decision", "Mode", "SafetyModeError", "FingerprintMismatch", "SafetyRequest",
    "ApprovalEvidence", "OverrideEvidence", "AuthorityContext", "SafeProfile", "SafetyDecision",
    "PolicyDelta", "PreparedSafetyEvaluator", "canonical_json", "fingerprint",
    "safe_profile_from_mapping", "evaluate", "evaluate_unprepared", "compute_policy_delta",
    "apply_policy_delta", "audit_record", "default_profile", "default_authority",
]
