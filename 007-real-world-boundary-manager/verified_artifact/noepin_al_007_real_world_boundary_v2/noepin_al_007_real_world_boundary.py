from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Tuple
import hashlib
import json
import time


class BoundaryDecision(str, Enum):
    ALLOW_PREPARE = "ALLOW_PREPARE"
    HUMAN_CONFIRM = "HUMAN_CONFIRM"
    HOLD = "HOLD"
    DENY = "DENY"


class AdapterKind(str, Enum):
    PC = "PC"
    UNITY = "UNITY"
    SMART_HOME = "SMART_HOME"
    ROBOT = "ROBOT"
    EXTERNAL_SERVICE = "EXTERNAL_SERVICE"


@dataclass(frozen=True)
class CapabilityToken:
    token_id: str
    subject_id: str
    resource_id: str
    capabilities: Tuple[str, ...]
    expires_at_epoch_s: int
    issuer_ref: str
    revoked: bool = False


@dataclass(frozen=True)
class BoundaryPolicy:
    allowed_adapters: Tuple[AdapterKind, ...]
    high_risk_capabilities: Tuple[str, ...] = (
        "physical_motion", "unlock", "power_cycle", "delete", "purchase", "send_external"
    )
    require_human_for_physical: bool = True
    require_interlock_for_physical: bool = True
    max_risk_without_confirmation: int = 35
    policy_version: str = "1"


@dataclass(frozen=True)
class BoundaryRequest:
    request_id: str
    actor_id: str
    adapter_kind: AdapterKind
    resource_id: str
    capability: str
    risk_score: int
    observed_epoch_s: int
    token: Optional[CapabilityToken] = None
    interlock_ready: bool = False
    emergency_stop_active: bool = False
    device_online: bool = True
    target_state_known: bool = True
    human_approved: bool = False
    approval_ref: Optional[str] = None
    external_side_effect: bool = False
    physical_effect: bool = False
    schema_version: str = "1"
    context: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BoundaryResult:
    decision: BoundaryDecision
    reason_codes: Tuple[str, ...]
    request_fingerprint: str
    token_validated: bool
    interlock_validated: bool
    emergency_stop_observed: bool
    authoritative: bool = False
    action_executed: bool = False
    action_succeeded: bool = False
    state_committed: bool = False
    cache_reused: bool = False
    created_unix_ns: int = 0

    def stable_payload(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reason_codes": list(self.reason_codes),
            "request_fingerprint": self.request_fingerprint,
            "token_validated": self.token_validated,
            "interlock_validated": self.interlock_validated,
            "emergency_stop_observed": self.emergency_stop_observed,
            "authoritative": self.authoritative,
            "action_executed": self.action_executed,
            "action_succeeded": self.action_succeeded,
            "state_committed": self.state_committed,
            "cache_reused": self.cache_reused,
        }


class RealWorldBoundaryManager:
    """
    NOEPIN AL 007 — Real-World Boundary Manager.

    Final pre-action boundary check only. It NEVER controls a device or service itself.

    Invariants:
      Capability token != Action Success
      Human approval evidence != Action execution
      Prepared boundary decision != committed world change
      Cached result != New Authority
      Partial/provisional state != safe physical state
      Emergency Stop overrides cache and prior allow decisions
    """

    def __init__(self, policy: BoundaryPolicy, *, enable_exact_state_cache: bool = True) -> None:
        if not policy.allowed_adapters:
            raise ValueError("at least one adapter is required")
        if not policy.policy_version:
            raise ValueError("policy_version required")
        self.policy = policy
        self.enable_exact_state_cache = bool(enable_exact_state_cache)
        self._cache: Dict[Tuple[str, str], BoundaryResult] = {}

    @staticmethod
    def _normalize(v: Any) -> Any:
        if isinstance(v, Mapping):
            return {str(k): RealWorldBoundaryManager._normalize(v[k]) for k in sorted(v, key=lambda x: str(x))}
        if isinstance(v, (list, tuple)):
            return [RealWorldBoundaryManager._normalize(x) for x in v]
        if isinstance(v, set):
            return sorted(RealWorldBoundaryManager._normalize(x) for x in v)
        if isinstance(v, Enum):
            return v.value
        if v is None or isinstance(v, (str, int, float, bool)):
            return v
        return str(v)

    @classmethod
    def fingerprint(cls, req: BoundaryRequest) -> str:
        raw = json.dumps(cls._normalize(asdict(req)), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _valid_score(v: int) -> bool:
        return isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 100

    def _validate_token(self, req: BoundaryRequest) -> Tuple[bool, str]:
        token = req.token
        if token is None:
            return False, "CAPABILITY_TOKEN_REQUIRED"
        if not token.token_id or not token.subject_id or not token.resource_id or not token.issuer_ref:
            return False, "MALFORMED_CAPABILITY_TOKEN"
        if token.revoked:
            return False, "CAPABILITY_TOKEN_REVOKED"
        if token.subject_id != req.actor_id:
            return False, "CAPABILITY_TOKEN_SUBJECT_MISMATCH"
        if token.resource_id != req.resource_id:
            return False, "CAPABILITY_TOKEN_RESOURCE_MISMATCH"
        if req.capability not in set(token.capabilities):
            return False, "CAPABILITY_NOT_GRANTED"
        if not isinstance(req.observed_epoch_s, int) or isinstance(req.observed_epoch_s, bool) or req.observed_epoch_s < 0:
            return False, "INVALID_OBSERVED_TIME"
        if not isinstance(token.expires_at_epoch_s, int) or isinstance(token.expires_at_epoch_s, bool):
            return False, "INVALID_TOKEN_EXPIRY"
        if req.observed_epoch_s >= token.expires_at_epoch_s:
            return False, "CAPABILITY_TOKEN_EXPIRED"
        return True, "CAPABILITY_TOKEN_VALID"

    def _make(self, decision, reasons, fp, token_validated, interlock_validated, emergency) -> BoundaryResult:
        return BoundaryResult(
            decision=decision,
            reason_codes=tuple(reasons),
            request_fingerprint=fp,
            token_validated=bool(token_validated),
            interlock_validated=bool(interlock_validated),
            emergency_stop_observed=bool(emergency),
            authoritative=False,
            action_executed=False,
            action_succeeded=False,
            state_committed=False,
            cache_reused=False,
            created_unix_ns=time.time_ns(),
        )

    def _evaluate_uncached(self, req: BoundaryRequest) -> BoundaryResult:
        fp = self.fingerprint(req)

        if not req.request_id or not req.actor_id or not req.resource_id or not req.capability or not req.schema_version:
            return self._make(BoundaryDecision.HOLD, ("MISSING_REQUIRED_FIELD",), fp, False, False, req.emergency_stop_active)

        if req.emergency_stop_active:
            return self._make(BoundaryDecision.DENY, ("EMERGENCY_STOP_ACTIVE",), fp, False, False, True)

        if req.adapter_kind not in set(self.policy.allowed_adapters):
            return self._make(BoundaryDecision.DENY, ("ADAPTER_NOT_ALLOWED",), fp, False, False, False)

        if not self._valid_score(req.risk_score):
            return self._make(BoundaryDecision.HOLD, ("INVALID_RISK_SCORE",), fp, False, False, False)

        if not req.device_online:
            return self._make(BoundaryDecision.HOLD, ("TARGET_OFFLINE_OR_UNREACHABLE",), fp, False, False, False)

        if not req.target_state_known:
            return self._make(BoundaryDecision.HOLD, ("TARGET_STATE_UNKNOWN",), fp, False, False, False)

        token_ok, token_reason = self._validate_token(req)
        if not token_ok:
            return self._make(BoundaryDecision.DENY if token_reason not in {"INVALID_OBSERVED_TIME","INVALID_TOKEN_EXPIRY"} else BoundaryDecision.HOLD,
                              (token_reason,), fp, False, False, False)

        physical = bool(req.physical_effect or req.adapter_kind in {AdapterKind.SMART_HOME, AdapterKind.ROBOT})
        if physical and self.policy.require_interlock_for_physical and not req.interlock_ready:
            return self._make(BoundaryDecision.HOLD, ("PHYSICAL_SAFETY_INTERLOCK_NOT_READY",), fp, True, False, False)

        interlock_ok = (not physical) or req.interlock_ready

        needs_human = False
        reasons = []
        if physical and self.policy.require_human_for_physical:
            needs_human = True
            reasons.append("PHYSICAL_EFFECT_REQUIRES_HUMAN_CONFIRMATION")
        if req.capability in set(self.policy.high_risk_capabilities):
            needs_human = True
            reasons.append("HIGH_RISK_CAPABILITY_REQUIRES_HUMAN_CONFIRMATION")
        if req.risk_score > self.policy.max_risk_without_confirmation:
            needs_human = True
            reasons.append("RISK_REQUIRES_HUMAN_CONFIRMATION")
        if req.external_side_effect:
            needs_human = True
            reasons.append("EXTERNAL_SIDE_EFFECT_REQUIRES_HUMAN_CONFIRMATION")

        if needs_human and not (req.human_approved and req.approval_ref):
            return self._make(BoundaryDecision.HUMAN_CONFIRM, tuple(reasons), fp, True, interlock_ok, False)

        return self._make(
            BoundaryDecision.ALLOW_PREPARE,
            tuple(reasons) if reasons else ("BOUNDARY_CHECK_PASS_PREPARE_ONLY",),
            fp, True, interlock_ok, False
        )

    def evaluate(self, req: BoundaryRequest) -> BoundaryResult:
        # Emergency stop MUST bypass cache and override any prior permit.
        if req.emergency_stop_active:
            return self._evaluate_uncached(req)

        fp = self.fingerprint(req)
        key = (fp, self.policy.policy_version)
        if self.enable_exact_state_cache and key in self._cache:
            c = self._cache[key]
            return BoundaryResult(
                decision=c.decision,
                reason_codes=c.reason_codes,
                request_fingerprint=fp,
                token_validated=c.token_validated,
                interlock_validated=c.interlock_validated,
                emergency_stop_observed=False,
                authoritative=False,
                action_executed=False,
                action_succeeded=False,
                state_committed=False,
                cache_reused=True,
                created_unix_ns=time.time_ns(),
            )

        result = self._evaluate_uncached(req)
        if self.enable_exact_state_cache:
            self._cache[key] = result
        return result

    def clear_cache(self) -> None:
        self._cache.clear()

    def cache_size(self) -> int:
        return len(self._cache)
