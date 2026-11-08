from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Tuple
import hashlib
import json
import time


class SimulationDecision(str, Enum):
    SAFE_TO_PREPARE = "SAFE_TO_PREPARE"
    HOLD = "HOLD"
    HUMAN_CONFIRM = "HUMAN_CONFIRM"
    REJECT = "REJECT"


class ActionKind(str, Enum):
    READ = "READ"
    WRITE = "WRITE"
    DELETE = "DELETE"
    MOVE = "MOVE"
    CONFIG_CHANGE = "CONFIG_CHANGE"
    EXTERNAL_SEND = "EXTERNAL_SEND"
    EXECUTE = "EXECUTE"


@dataclass(frozen=True)
class SimulationPolicy:
    max_impact_without_confirmation: int = 40
    max_impact_allowed: int = 85
    require_snapshot_for_destructive: bool = True
    require_rollback_for_destructive: bool = True
    require_human_for_external_send: bool = True
    require_human_for_execute: bool = True
    policy_version: str = "1"


@dataclass(frozen=True)
class ActionPlan:
    action: ActionKind
    target: str
    actor_id: str
    estimated_impact: int
    reversible: bool
    rollback_ref: Optional[str] = None
    snapshot_ref: Optional[str] = None
    external_side_effect: bool = False
    writes_world_state: bool = False
    deletes_data: bool = False
    affects_production: bool = False
    approval_present: bool = False
    approval_ref: Optional[str] = None
    dependencies_ready: bool = True
    schema_version: str = "1"
    context: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ImpactReport:
    decision: SimulationDecision
    reason_codes: Tuple[str, ...]
    request_fingerprint: str
    impact_score: int
    reversibility_score: int
    requires_snapshot: bool
    requires_rollback: bool
    requires_human_confirmation: bool
    simulation_only: bool = True
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
            "impact_score": self.impact_score,
            "reversibility_score": self.reversibility_score,
            "requires_snapshot": self.requires_snapshot,
            "requires_rollback": self.requires_rollback,
            "requires_human_confirmation": self.requires_human_confirmation,
            "simulation_only": self.simulation_only,
            "authoritative": self.authoritative,
            "action_executed": self.action_executed,
            "action_succeeded": self.action_succeeded,
            "state_committed": self.state_committed,
            "cache_reused": self.cache_reused,
        }


class PreExecutionSimulator:
    """
    NOEPIN AL 004 — Pre-Execution Simulator.

    Dry-run evaluator only. It never performs the proposed action.

    Invariants:
      Simulation PASS != Action Success
      Impact estimate != Truth
      Snapshot reference != Snapshot existence unless externally verified
      Rollback reference != Rollback success
      Human approval evidence != Action execution
      Cached simulation != New Authority
    """

    def __init__(self, policy: SimulationPolicy, *, enable_exact_state_cache: bool = True) -> None:
        if not policy.policy_version:
            raise ValueError("policy_version required")
        self.policy = policy
        self.enable_exact_state_cache = bool(enable_exact_state_cache)
        self._cache: Dict[Tuple[str, str], ImpactReport] = {}

    @staticmethod
    def _normalize(v: Any) -> Any:
        if isinstance(v, Mapping):
            return {str(k): PreExecutionSimulator._normalize(v[k]) for k in sorted(v, key=lambda x: str(x))}
        if isinstance(v, (list, tuple)):
            return [PreExecutionSimulator._normalize(x) for x in v]
        if isinstance(v, set):
            return sorted(PreExecutionSimulator._normalize(x) for x in v)
        if isinstance(v, Enum):
            return v.value
        if v is None or isinstance(v, (str, int, float, bool)):
            return v
        return str(v)

    @classmethod
    def fingerprint(cls, plan: ActionPlan) -> str:
        raw = json.dumps(cls._normalize(asdict(plan)), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _valid_score(v: int) -> bool:
        return isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 100

    @staticmethod
    def _reversibility_score(plan: ActionPlan) -> int:
        score = 100
        if not plan.reversible:
            score -= 60
        if plan.deletes_data:
            score -= 25
        if plan.affects_production:
            score -= 15
        if plan.external_side_effect:
            score -= 20
        if plan.rollback_ref:
            score += 10
        if plan.snapshot_ref:
            score += 10
        return max(0, min(100, score))

    def _evaluate_uncached(self, plan: ActionPlan) -> ImpactReport:
        fp = self.fingerprint(plan)
        if not plan.actor_id or not plan.target or not plan.schema_version:
            return self._make(SimulationDecision.HOLD, ("MISSING_REQUIRED_FIELD",), fp, plan, 0, False, False, False)

        if not self._valid_score(plan.estimated_impact):
            return self._make(SimulationDecision.HOLD, ("INVALID_IMPACT_SCORE",), fp, plan, 0, False, False, False)

        if not plan.dependencies_ready:
            return self._make(SimulationDecision.HOLD, ("DEPENDENCY_NOT_READY",), fp, plan, plan.estimated_impact, False, False, False)

        destructive = plan.action in {ActionKind.DELETE, ActionKind.MOVE, ActionKind.CONFIG_CHANGE, ActionKind.EXECUTE} or plan.deletes_data or plan.writes_world_state
        req_snapshot = destructive and self.policy.require_snapshot_for_destructive
        req_rollback = destructive and self.policy.require_rollback_for_destructive

        if plan.estimated_impact > self.policy.max_impact_allowed:
            return self._make(SimulationDecision.REJECT, ("IMPACT_EXCEEDS_MAXIMUM",), fp, plan, plan.estimated_impact, req_snapshot, req_rollback, False)

        if req_snapshot and not plan.snapshot_ref:
            return self._make(SimulationDecision.HOLD, ("SNAPSHOT_REQUIRED",), fp, plan, plan.estimated_impact, req_snapshot, req_rollback, False)

        if req_rollback and not plan.rollback_ref:
            return self._make(SimulationDecision.HOLD, ("ROLLBACK_REF_REQUIRED",), fp, plan, plan.estimated_impact, req_snapshot, req_rollback, False)

        needs_human = False
        reasons = []

        if plan.estimated_impact > self.policy.max_impact_without_confirmation:
            needs_human = True
            reasons.append("IMPACT_REQUIRES_HUMAN_CONFIRMATION")
        if plan.action == ActionKind.DELETE or plan.deletes_data:
            needs_human = True
            reasons.append("DELETE_REQUIRES_HUMAN_CONFIRMATION")
        if plan.external_side_effect:
            needs_human = True
            reasons.append("EXTERNAL_SIDE_EFFECT_REQUIRES_HUMAN_CONFIRMATION")
        if plan.action == ActionKind.EXTERNAL_SEND and self.policy.require_human_for_external_send:
            needs_human = True
            reasons.append("EXTERNAL_SEND_REQUIRES_HUMAN_CONFIRMATION")
        if plan.action == ActionKind.EXECUTE and self.policy.require_human_for_execute:
            needs_human = True
            reasons.append("EXECUTE_REQUIRES_HUMAN_CONFIRMATION")
        if not plan.reversible:
            needs_human = True
            reasons.append("IRREVERSIBLE_ACTION_REQUIRES_HUMAN_CONFIRMATION")
        if plan.affects_production:
            needs_human = True
            reasons.append("PRODUCTION_IMPACT_REQUIRES_HUMAN_CONFIRMATION")

        if needs_human and not (plan.approval_present and plan.approval_ref):
            return self._make(SimulationDecision.HUMAN_CONFIRM, tuple(reasons), fp, plan, plan.estimated_impact, req_snapshot, req_rollback, True)

        final_reasons = tuple(reasons) if reasons else ("DRY_RUN_ACCEPTABLE",)
        return self._make(SimulationDecision.SAFE_TO_PREPARE, final_reasons, fp, plan, plan.estimated_impact, req_snapshot, req_rollback, needs_human)

    def _make(self, decision, reasons, fp, plan, impact, req_snapshot, req_rollback, req_human):
        return ImpactReport(
            decision=decision,
            reason_codes=tuple(reasons),
            request_fingerprint=fp,
            impact_score=impact,
            reversibility_score=self._reversibility_score(plan),
            requires_snapshot=req_snapshot,
            requires_rollback=req_rollback,
            requires_human_confirmation=req_human,
            simulation_only=True,
            authoritative=False,
            action_executed=False,
            action_succeeded=False,
            state_committed=False,
            cache_reused=False,
            created_unix_ns=time.time_ns(),
        )

    def simulate(self, plan: ActionPlan) -> ImpactReport:
        fp = self.fingerprint(plan)
        key = (fp, self.policy.policy_version)
        if self.enable_exact_state_cache and key in self._cache:
            c = self._cache[key]
            return ImpactReport(
                decision=c.decision,
                reason_codes=c.reason_codes,
                request_fingerprint=fp,
                impact_score=c.impact_score,
                reversibility_score=c.reversibility_score,
                requires_snapshot=c.requires_snapshot,
                requires_rollback=c.requires_rollback,
                requires_human_confirmation=c.requires_human_confirmation,
                simulation_only=True,
                authoritative=False,
                action_executed=False,
                action_succeeded=False,
                state_committed=False,
                cache_reused=True,
                created_unix_ns=time.time_ns(),
            )
        r = self._evaluate_uncached(plan)
        if self.enable_exact_state_cache:
            self._cache[key] = r
        return r

    def clear_cache(self) -> None:
        self._cache.clear()

    def cache_size(self) -> int:
        return len(self._cache)
