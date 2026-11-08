from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Tuple
import hashlib, json, time

class ResourceDecision(str, Enum):
    ALLOW_PREPARE = "ALLOW_PREPARE"
    THROTTLE = "THROTTLE"
    HUMAN_CONFIRM = "HUMAN_CONFIRM"
    STOP_PREPARE = "STOP_PREPARE"
    HOLD = "HOLD"
    DENY = "DENY"

@dataclass(frozen=True)
class ResourceRequest:
    request_id: str
    workload_id: str
    agent_id: str
    operation: str
    budget_version: int
    authority_version: int
    observed_epoch_ms: int

    max_cost_usd: float
    used_cost_usd: float
    projected_incremental_cost_usd: float

    max_tokens: int
    used_tokens: int
    projected_incremental_tokens: int

    max_elapsed_ms: int
    elapsed_ms: int
    projected_incremental_ms: int

    max_api_calls: int
    api_calls_used: int
    projected_incremental_calls: int

    max_iterations: int
    iterations_used: int
    projected_incremental_iterations: int

    max_cpu_seconds: float
    cpu_seconds_used: float
    projected_incremental_cpu_seconds: float

    max_gpu_seconds: float
    gpu_seconds_used: float
    projected_incremental_gpu_seconds: float

    deadline_epoch_ms: Optional[int]
    rate_limit_per_window: int
    calls_in_window: int
    window_end_epoch_ms: Optional[int]

    hard_stop_requested: bool = False
    provider_rate_limited: bool = False
    high_cost_operation: bool = False
    human_approved: bool = False
    approval_ref: Optional[str] = None
    schema_version: str = "1"
    context: Mapping[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class ResourceResult:
    decision: ResourceDecision
    reason_codes: Tuple[str, ...]
    request_fingerprint: str
    projected_cost_usd: float
    projected_tokens: int
    projected_elapsed_ms: int
    projected_api_calls: int
    projected_iterations: int
    projected_cpu_seconds: float
    projected_gpu_seconds: float
    near_limit: bool
    stop_plan_created: bool
    throttle_plan_created: bool
    process_stopped: bool = False
    api_calls_stopped: bool = False
    billing_stopped: bool = False
    resources_released: bool = False
    action_executed: bool = False
    action_succeeded: bool = False
    state_committed: bool = False
    authoritative: bool = False
    cache_reused: bool = False
    created_unix_ns: int = 0

    def stable_payload(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reason_codes": list(self.reason_codes),
            "request_fingerprint": self.request_fingerprint,
            "projected_cost_usd": self.projected_cost_usd,
            "projected_tokens": self.projected_tokens,
            "projected_elapsed_ms": self.projected_elapsed_ms,
            "projected_api_calls": self.projected_api_calls,
            "projected_iterations": self.projected_iterations,
            "projected_cpu_seconds": self.projected_cpu_seconds,
            "projected_gpu_seconds": self.projected_gpu_seconds,
            "near_limit": self.near_limit,
            "stop_plan_created": self.stop_plan_created,
            "throttle_plan_created": self.throttle_plan_created,
            "process_stopped": False,
            "api_calls_stopped": False,
            "billing_stopped": False,
            "resources_released": False,
            "action_executed": False,
            "action_succeeded": False,
            "state_committed": False,
            "authoritative": False,
            "cache_reused": self.cache_reused,
        }

class ResourceCostGuard:
    """
    NOEPIN AL 023 — Resource / Cost Limit Guard.

    The guard evaluates budget, quota, rate, deadline and stop conditions.
    It never terminates a process, cancels provider billing, blocks a network call,
    releases CPU/GPU resources, or commits runtime state.

    Invariants:
      Remaining Budget != Execution Authority
      Limit Exceeded != Job Actually Stopped
      STOP_PREPARE != Process Stopped
      Cost Estimate != Actual Charge
      Rate Limit Observation != Provider Enforcement
      Deadline Reached != Cancellation Success
      Cache Hit != Current Usage
    """

    def __init__(
        self,
        *,
        policy_version: str = "1",
        enable_exact_state_cache: bool = True,
        near_limit_ratio: float = 0.85,
        high_cost_requires_human: bool = True,
    ):
        if not policy_version:
            raise ValueError("policy_version required")
        if not (0.0 < float(near_limit_ratio) < 1.0):
            raise ValueError("near_limit_ratio must be between 0 and 1")
        self.policy_version = str(policy_version)
        self.enable_exact_state_cache = bool(enable_exact_state_cache)
        self.near_limit_ratio = float(near_limit_ratio)
        self.high_cost_requires_human = bool(high_cost_requires_human)
        self._cache: Dict[Tuple[str, str], ResourceResult] = {}

    @staticmethod
    def _norm(v: Any) -> Any:
        if isinstance(v, Mapping):
            return {str(k): ResourceCostGuard._norm(v[k]) for k in sorted(v, key=lambda x: str(x))}
        if isinstance(v, (tuple, list)):
            return [ResourceCostGuard._norm(x) for x in v]
        if isinstance(v, set):
            return sorted(ResourceCostGuard._norm(x) for x in v)
        if isinstance(v, Enum):
            return v.value
        if v is None or isinstance(v, (str, int, float, bool)):
            return v
        return str(v)

    @classmethod
    def fingerprint(cls, req: ResourceRequest) -> str:
        raw = json.dumps(cls._norm(asdict(req)), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _valid_int(v: Any) -> bool:
        return isinstance(v, int) and not isinstance(v, bool)

    @staticmethod
    def _valid_num(v: Any) -> bool:
        return isinstance(v, (int, float)) and not isinstance(v, bool)

    @staticmethod
    def _project(r: ResourceRequest):
        return (
            r.used_cost_usd + r.projected_incremental_cost_usd,
            r.used_tokens + r.projected_incremental_tokens,
            r.elapsed_ms + r.projected_incremental_ms,
            r.api_calls_used + r.projected_incremental_calls,
            r.iterations_used + r.projected_incremental_iterations,
            r.cpu_seconds_used + r.projected_incremental_cpu_seconds,
            r.gpu_seconds_used + r.projected_incremental_gpu_seconds,
        )

    def _make(self, decision: ResourceDecision, reasons, fp: str, r: ResourceRequest,
              *, near=False, stop=False, throttle=False) -> ResourceResult:
        pc, pt, pe, pac, pi, pcpu, pgpu = self._project(r)
        return ResourceResult(
            decision=decision,
            reason_codes=tuple(reasons),
            request_fingerprint=fp,
            projected_cost_usd=round(float(pc), 10),
            projected_tokens=int(pt),
            projected_elapsed_ms=int(pe),
            projected_api_calls=int(pac),
            projected_iterations=int(pi),
            projected_cpu_seconds=round(float(pcpu), 10),
            projected_gpu_seconds=round(float(pgpu), 10),
            near_limit=bool(near),
            stop_plan_created=bool(stop),
            throttle_plan_created=bool(throttle),
            process_stopped=False,
            api_calls_stopped=False,
            billing_stopped=False,
            resources_released=False,
            action_executed=False,
            action_succeeded=False,
            state_committed=False,
            authoritative=False,
            cache_reused=False,
            created_unix_ns=time.time_ns(),
        )

    def _validate(self, r: ResourceRequest):
        required = [r.request_id, r.workload_id, r.agent_id, r.operation, r.schema_version]
        if any(not x for x in required):
            return "REQUIRED_FIELD_MISSING"
        for v, name in (
            (r.budget_version, "BUDGET_VERSION"),
            (r.authority_version, "AUTHORITY_VERSION"),
            (r.observed_epoch_ms, "OBSERVED_TIME"),
            (r.max_tokens, "MAX_TOKENS"), (r.used_tokens, "USED_TOKENS"),
            (r.projected_incremental_tokens, "PROJECTED_TOKENS"),
            (r.max_elapsed_ms, "MAX_ELAPSED_MS"), (r.elapsed_ms, "ELAPSED_MS"),
            (r.projected_incremental_ms, "PROJECTED_MS"),
            (r.max_api_calls, "MAX_API_CALLS"), (r.api_calls_used, "API_CALLS_USED"),
            (r.projected_incremental_calls, "PROJECTED_CALLS"),
            (r.max_iterations, "MAX_ITERATIONS"), (r.iterations_used, "ITERATIONS_USED"),
            (r.projected_incremental_iterations, "PROJECTED_ITERATIONS"),
            (r.rate_limit_per_window, "RATE_LIMIT"), (r.calls_in_window, "CALLS_IN_WINDOW"),
        ):
            if not self._valid_int(v) or v < 0:
                return f"{name}_INVALID"
        if r.budget_version < 1 or r.authority_version < 1:
            return "VERSION_INVALID"
        for v, name in (
            (r.max_cost_usd, "MAX_COST"), (r.used_cost_usd, "USED_COST"),
            (r.projected_incremental_cost_usd, "PROJECTED_COST"),
            (r.max_cpu_seconds, "MAX_CPU"), (r.cpu_seconds_used, "USED_CPU"),
            (r.projected_incremental_cpu_seconds, "PROJECTED_CPU"),
            (r.max_gpu_seconds, "MAX_GPU"), (r.gpu_seconds_used, "USED_GPU"),
            (r.projected_incremental_gpu_seconds, "PROJECTED_GPU"),
        ):
            if not self._valid_num(v) or float(v) < 0:
                return f"{name}_INVALID"
        for v, name in ((r.deadline_epoch_ms, "DEADLINE"), (r.window_end_epoch_ms, "WINDOW_END")):
            if v is not None and (not self._valid_int(v) or v < 0):
                return f"{name}_INVALID"
        return None

    @staticmethod
    def _ratio(value: float, limit: float) -> float:
        if limit <= 0:
            return 1.0 if value > 0 else 0.0
        return value / limit

    def _evaluate_uncached(self, r: ResourceRequest) -> ResourceResult:
        fp = self.fingerprint(r)
        err = self._validate(r)
        if err:
            return self._make(ResourceDecision.HOLD, (err,), fp, r)

        if r.hard_stop_requested:
            return self._make(ResourceDecision.STOP_PREPARE, ("HARD_STOP_REQUESTED",), fp, r, stop=True)

        if r.deadline_epoch_ms is not None and r.observed_epoch_ms >= r.deadline_epoch_ms:
            return self._make(ResourceDecision.STOP_PREPARE, ("DEADLINE_REACHED",), fp, r, stop=True)

        projected = self._project(r)
        limits = (
            (projected[0], r.max_cost_usd, "COST_LIMIT_EXCEEDED"),
            (projected[1], r.max_tokens, "TOKEN_LIMIT_EXCEEDED"),
            (projected[2], r.max_elapsed_ms, "TIME_LIMIT_EXCEEDED"),
            (projected[3], r.max_api_calls, "API_CALL_LIMIT_EXCEEDED"),
            (projected[4], r.max_iterations, "ITERATION_LIMIT_EXCEEDED"),
            (projected[5], r.max_cpu_seconds, "CPU_LIMIT_EXCEEDED"),
            (projected[6], r.max_gpu_seconds, "GPU_LIMIT_EXCEEDED"),
        )
        exceeded = [code for value, limit, code in limits if value > limit]
        if exceeded:
            return self._make(ResourceDecision.STOP_PREPARE, tuple(exceeded), fp, r, stop=True)

        if r.provider_rate_limited:
            return self._make(ResourceDecision.THROTTLE, ("PROVIDER_RATE_LIMIT_OBSERVED",), fp, r, throttle=True)

        if r.rate_limit_per_window > 0 and r.calls_in_window + r.projected_incremental_calls > r.rate_limit_per_window:
            return self._make(ResourceDecision.THROTTLE, ("LOCAL_RATE_LIMIT_EXCEEDED",), fp, r, throttle=True)

        ratios = [self._ratio(float(value), float(limit)) for value, limit, _ in limits]
        near = any(x >= self.near_limit_ratio for x in ratios)

        if self.high_cost_requires_human and r.high_cost_operation:
            if not (r.human_approved and r.approval_ref):
                return self._make(ResourceDecision.HUMAN_CONFIRM, ("HIGH_COST_OPERATION_CONFIRM_REQUIRED",), fp, r, near=near)
            return self._make(ResourceDecision.ALLOW_PREPARE, ("APPROVAL_EVIDENCE_PRESENT_BUDGET_STILL_ENFORCED",), fp, r, near=near)

        if near:
            return self._make(ResourceDecision.ALLOW_PREPARE, ("WITHIN_LIMITS_NEAR_THRESHOLD",), fp, r, near=True)
        return self._make(ResourceDecision.ALLOW_PREPARE, ("WITHIN_LIMITS",), fp, r)

    def evaluate(self, r: ResourceRequest) -> ResourceResult:
        fp = self.fingerprint(r)
        key = (fp, self.policy_version)
        if self.enable_exact_state_cache and key in self._cache:
            x = self._cache[key]
            return ResourceResult(
                decision=x.decision,
                reason_codes=x.reason_codes,
                request_fingerprint=fp,
                projected_cost_usd=x.projected_cost_usd,
                projected_tokens=x.projected_tokens,
                projected_elapsed_ms=x.projected_elapsed_ms,
                projected_api_calls=x.projected_api_calls,
                projected_iterations=x.projected_iterations,
                projected_cpu_seconds=x.projected_cpu_seconds,
                projected_gpu_seconds=x.projected_gpu_seconds,
                near_limit=x.near_limit,
                stop_plan_created=x.stop_plan_created,
                throttle_plan_created=x.throttle_plan_created,
                process_stopped=False,
                api_calls_stopped=False,
                billing_stopped=False,
                resources_released=False,
                action_executed=False,
                action_succeeded=False,
                state_committed=False,
                authoritative=False,
                cache_reused=True,
                created_unix_ns=time.time_ns(),
            )
        out = self._evaluate_uncached(r)
        if self.enable_exact_state_cache:
            self._cache[key] = out
        return out

    def clear_cache(self) -> None:
        self._cache.clear()

    def cache_size(self) -> int:
        return len(self._cache)
