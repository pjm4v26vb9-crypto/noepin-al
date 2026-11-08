from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Tuple
import hashlib, json, time

class KillDecision(str, Enum):
    CONTINUE = "CONTINUE"
    CONTAIN_PREPARE = "CONTAIN_PREPARE"
    HUMAN_CONFIRM = "HUMAN_CONFIRM"
    HOLD = "HOLD"
    DENY = "DENY"

@dataclass(frozen=True)
class AgentAuthoritySnapshot:
    agent_id: str
    authority_version: int
    permit_version: int
    revoked: bool = False
    network_allowed: bool = True
    tools_allowed: bool = True
    process_allowed: bool = True
    safe_state_required: bool = False

@dataclass(frozen=True)
class KillPolicy:
    hard_violation_threshold: int = 80
    soft_violation_threshold: int = 45
    anomaly_threshold: int = 70
    require_human_for_non_emergency_containment: bool = True
    policy_version: str = "1"

@dataclass(frozen=True)
class KillRequest:
    request_id: str
    snapshot: AgentAuthoritySnapshot
    observed_authority_version: int
    observed_permit_version: int
    policy_violation_score: int
    anomaly_score: int
    unauthorized_scope_expansion: bool = False
    unauthorized_network_attempt: bool = False
    unauthorized_tool_attempt: bool = False
    unauthorized_process_attempt: bool = False
    repeated_guard_bypass_attempt: bool = False
    emergency_stop_active: bool = False
    human_approved: bool = False
    approval_ref: Optional[str] = None
    evidence_fingerprint: Optional[str] = None
    evidence_version: int = 1
    schema_version: str = "1"
    context: Mapping[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class ContainmentPlan:
    revoke_permissions: bool
    quarantine_network: bool
    disable_tools: bool
    stop_process: bool
    enter_safe_state: bool

@dataclass(frozen=True)
class KillResult:
    decision: KillDecision
    reason_codes: Tuple[str, ...]
    request_fingerprint: str
    plan: ContainmentPlan
    authoritative: bool = False
    permissions_revoked: bool = False
    network_quarantined: bool = False
    tools_disabled: bool = False
    process_stopped: bool = False
    safe_state_reached: bool = False
    action_executed: bool = False
    action_succeeded: bool = False
    cache_reused: bool = False
    created_unix_ns: int = 0

    def stable_payload(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reason_codes": list(self.reason_codes),
            "request_fingerprint": self.request_fingerprint,
            "plan": asdict(self.plan),
            "authoritative": self.authoritative,
            "permissions_revoked": self.permissions_revoked,
            "network_quarantined": self.network_quarantined,
            "tools_disabled": self.tools_disabled,
            "process_stopped": self.process_stopped,
            "safe_state_reached": self.safe_state_reached,
            "action_executed": self.action_executed,
            "action_succeeded": self.action_succeeded,
            "cache_reused": self.cache_reused,
        }

class RogueAIKillSwitch:
    """NOEPIN AL 017 — Rogue AI Kill Switch (decision / containment-plan layer only).

    Invariants:
      Kill request != Containment success
      Revocation requested != Permissions revoked
      Network quarantine requested != Connection closed
      Process stop requested != Process stopped
      Safe-state request != Safe state reached
      Emergency stop overrides cached allow
      Cached CONTINUE != Current safety state
    """

    def __init__(self, policy: KillPolicy, *, enable_exact_state_cache: bool = True) -> None:
        if not policy.policy_version:
            raise ValueError("policy_version required")
        self.policy = policy
        self.enable_exact_state_cache = bool(enable_exact_state_cache)
        self._cache: Dict[Tuple[str, str], KillResult] = {}

    @staticmethod
    def _norm(v: Any) -> Any:
        if isinstance(v, Mapping):
            return {str(k): RogueAIKillSwitch._norm(v[k]) for k in sorted(v, key=lambda x: str(x))}
        if isinstance(v, (list, tuple)):
            return [RogueAIKillSwitch._norm(x) for x in v]
        if isinstance(v, set):
            return sorted(RogueAIKillSwitch._norm(x) for x in v)
        if isinstance(v, Enum):
            return v.value
        if v is None or isinstance(v, (str, int, float, bool)):
            return v
        return str(v)

    @classmethod
    def fingerprint(cls, req: KillRequest) -> str:
        raw = json.dumps(cls._norm(asdict(req)), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _valid_int(v: Any) -> bool:
        return isinstance(v, int) and not isinstance(v, bool)

    @staticmethod
    def _valid_score(v: Any) -> bool:
        return isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 100

    @staticmethod
    def _valid_hash(v: Optional[str]) -> bool:
        if v is None:
            return True
        if not isinstance(v, str) or len(v) != 64:
            return False
        try:
            int(v, 16)
            return True
        except ValueError:
            return False

    @staticmethod
    def _plan(contain: bool) -> ContainmentPlan:
        if not contain:
            return ContainmentPlan(False, False, False, False, False)
        return ContainmentPlan(True, True, True, True, True)

    def _make(self, decision, reasons, fp, contain) -> KillResult:
        return KillResult(
            decision=decision,
            reason_codes=tuple(reasons),
            request_fingerprint=fp,
            plan=self._plan(contain),
            authoritative=False,
            permissions_revoked=False,
            network_quarantined=False,
            tools_disabled=False,
            process_stopped=False,
            safe_state_reached=False,
            action_executed=False,
            action_succeeded=False,
            cache_reused=False,
            created_unix_ns=time.time_ns(),
        )

    def _evaluate_uncached(self, req: KillRequest) -> KillResult:
        fp = self.fingerprint(req)
        s = req.snapshot
        if not req.request_id or not req.schema_version or not s.agent_id:
            return self._make(KillDecision.HOLD, ("MISSING_REQUIRED_FIELD",), fp, False)
        if not self._valid_int(s.authority_version) or s.authority_version < 1:
            return self._make(KillDecision.HOLD, ("INVALID_AUTHORITY_VERSION",), fp, False)
        if not self._valid_int(s.permit_version) or s.permit_version < 1:
            return self._make(KillDecision.HOLD, ("INVALID_PERMIT_VERSION",), fp, False)
        if not self._valid_int(req.observed_authority_version) or req.observed_authority_version < 1:
            return self._make(KillDecision.HOLD, ("INVALID_OBSERVED_AUTHORITY_VERSION",), fp, False)
        if not self._valid_int(req.observed_permit_version) or req.observed_permit_version < 1:
            return self._make(KillDecision.HOLD, ("INVALID_OBSERVED_PERMIT_VERSION",), fp, False)
        if req.observed_authority_version != s.authority_version:
            return self._make(KillDecision.HOLD, ("AUTHORITY_VERSION_MISMATCH",), fp, False)
        if req.observed_permit_version != s.permit_version:
            return self._make(KillDecision.HOLD, ("PERMIT_VERSION_MISMATCH",), fp, False)
        if not self._valid_score(req.policy_violation_score) or not self._valid_score(req.anomaly_score):
            return self._make(KillDecision.HOLD, ("INVALID_SCORE",), fp, False)
        if not self._valid_hash(req.evidence_fingerprint):
            return self._make(KillDecision.HOLD, ("INVALID_EVIDENCE_FINGERPRINT",), fp, False)
        if not self._valid_int(req.evidence_version) or req.evidence_version < 1:
            return self._make(KillDecision.HOLD, ("INVALID_EVIDENCE_VERSION",), fp, False)

        # Emergency always takes precedence and is never softened by approval/cache.
        if req.emergency_stop_active:
            return self._make(KillDecision.CONTAIN_PREPARE, ("EMERGENCY_STOP_ACTIVE",), fp, True)

        if s.revoked:
            return self._make(KillDecision.CONTAIN_PREPARE, ("AUTHORITY_ALREADY_REVOKED_CONTAINMENT_REQUIRED",), fp, True)

        hard_signal = any((
            req.unauthorized_scope_expansion,
            req.unauthorized_network_attempt,
            req.unauthorized_tool_attempt,
            req.unauthorized_process_attempt,
            req.repeated_guard_bypass_attempt,
            req.policy_violation_score >= self.policy.hard_violation_threshold,
            req.anomaly_score >= self.policy.anomaly_threshold,
        ))
        if hard_signal:
            return self._make(KillDecision.CONTAIN_PREPARE, ("HARD_ROGUE_SIGNAL",), fp, True)

        soft_signal = req.policy_violation_score >= self.policy.soft_violation_threshold
        if soft_signal:
            if self.policy.require_human_for_non_emergency_containment:
                if not (req.human_approved and req.approval_ref):
                    return self._make(KillDecision.HUMAN_CONFIRM, ("SOFT_ROGUE_SIGNAL_REQUIRES_HUMAN_CONFIRMATION",), fp, True)
            return self._make(KillDecision.CONTAIN_PREPARE, ("SOFT_ROGUE_SIGNAL_CONFIRMED",), fp, True)

        return self._make(KillDecision.CONTINUE, ("NO_CONTAINMENT_TRIGGER",), fp, False)

    def evaluate(self, req: KillRequest) -> KillResult:
        # Emergency stop and revoked snapshot bypass cache, preventing stale CONTINUE reuse.
        if req.emergency_stop_active or req.snapshot.revoked:
            return self._evaluate_uncached(req)
        fp = self.fingerprint(req)
        key = (fp, self.policy.policy_version)
        if self.enable_exact_state_cache and key in self._cache:
            r = self._cache[key]
            return KillResult(
                decision=r.decision,
                reason_codes=r.reason_codes,
                request_fingerprint=fp,
                plan=r.plan,
                authoritative=False,
                permissions_revoked=False,
                network_quarantined=False,
                tools_disabled=False,
                process_stopped=False,
                safe_state_reached=False,
                action_executed=False,
                action_succeeded=False,
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
