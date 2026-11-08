from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Tuple
import hashlib
import json
import time


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class BreakerDecision(str, Enum):
    ALLOW_PREPARE = "ALLOW_PREPARE"
    TRIP_PREPARE = "TRIP_PREPARE"
    RECOVERY_PROBE = "RECOVERY_PROBE"
    CLOSE_PREPARE = "CLOSE_PREPARE"
    HOLD = "HOLD"
    DENY = "DENY"


@dataclass(frozen=True)
class BreakerSnapshot:
    node_id: str
    state: CircuitState
    generation: int
    opened_at_epoch_s: Optional[int] = None
    last_transition_ref: Optional[str] = None


@dataclass(frozen=True)
class CascadeSignal:
    request_id: str
    snapshot: BreakerSnapshot
    observed_epoch_s: int
    consecutive_failures: int
    failure_count_window: int
    sample_count_window: int
    error_rate_percent: int
    fanout_estimate: int
    dependency_ids: Tuple[str, ...] = ()
    critical_dependency_failure: bool = False
    validated_failure_evidence: bool = False
    upstream_breaker_open: bool = False
    emergency_stop_active: bool = False
    cooldown_elapsed: bool = False
    recovery_successes: int = 0
    recovery_probe_authorized: bool = False
    expected_generation: Optional[int] = None
    human_approved: bool = False
    approval_ref: Optional[str] = None
    schema_version: str = "1"
    context: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BreakerPolicy:
    consecutive_failure_threshold: int = 3
    failure_count_threshold: int = 5
    error_rate_threshold_percent: int = 50
    fanout_trip_threshold: int = 4
    recovery_success_threshold: int = 2
    critical_failure_requires_human: bool = True
    policy_version: str = "1"


@dataclass(frozen=True)
class BreakerResult:
    decision: BreakerDecision
    reason_codes: Tuple[str, ...]
    request_fingerprint: str
    current_state: CircuitState
    proposed_state: CircuitState
    blast_radius_estimate: int
    transition_proposed: bool
    authoritative: bool = False
    dependencies_stopped: bool = False
    recovery_completed: bool = False
    action_executed: bool = False
    state_committed: bool = False
    cache_reused: bool = False
    created_unix_ns: int = 0

    def stable_payload(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reason_codes": list(self.reason_codes),
            "request_fingerprint": self.request_fingerprint,
            "current_state": self.current_state.value,
            "proposed_state": self.proposed_state.value,
            "blast_radius_estimate": self.blast_radius_estimate,
            "transition_proposed": self.transition_proposed,
            "authoritative": self.authoritative,
            "dependencies_stopped": self.dependencies_stopped,
            "recovery_completed": self.recovery_completed,
            "action_executed": self.action_executed,
            "state_committed": self.state_committed,
            "cache_reused": self.cache_reused,
        }


class CascadeCircuitBreaker:
    """
    NOEPIN AL 015 — Cascade Failure Circuit Breaker.

    Pure decision layer. It proposes breaker transitions but never stops, starts,
    isolates, retries, or mutates external systems.

    Invariants:
      Failure report != Confirmed failure
      Breaker OPEN != Dependencies actually stopped
      Recovery probe success != Recovery complete
      Proposed transition != Committed breaker state
      Emergency stop overrides cached allow
      Cached CLOSED result != Current health
      Human approval evidence != Action execution
    """

    def __init__(self, policy: BreakerPolicy, *, enable_exact_state_cache: bool = True) -> None:
        if not policy.policy_version:
            raise ValueError("policy_version required")
        if policy.consecutive_failure_threshold < 1 or policy.failure_count_threshold < 1:
            raise ValueError("failure thresholds must be positive")
        if not (0 <= policy.error_rate_threshold_percent <= 100):
            raise ValueError("error rate threshold invalid")
        if policy.fanout_trip_threshold < 1 or policy.recovery_success_threshold < 1:
            raise ValueError("fanout/recovery thresholds must be positive")
        self.policy = policy
        self.enable_exact_state_cache = bool(enable_exact_state_cache)
        self._cache: Dict[Tuple[str, str], BreakerResult] = {}

    @staticmethod
    def _normalize(v: Any) -> Any:
        if isinstance(v, Mapping):
            return {str(k): CascadeCircuitBreaker._normalize(v[k]) for k in sorted(v, key=lambda x: str(x))}
        if isinstance(v, (list, tuple)):
            return [CascadeCircuitBreaker._normalize(x) for x in v]
        if isinstance(v, set):
            return sorted(CascadeCircuitBreaker._normalize(x) for x in v)
        if isinstance(v, Enum):
            return v.value
        if v is None or isinstance(v, (str, int, float, bool)):
            return v
        return str(v)

    @classmethod
    def fingerprint(cls, signal: CascadeSignal) -> str:
        raw = json.dumps(cls._normalize(asdict(signal)), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _valid_nonnegative_int(v: Any) -> bool:
        return isinstance(v, int) and not isinstance(v, bool) and v >= 0

    @staticmethod
    def _valid_percent(v: Any) -> bool:
        return isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 100

    def _make(self, decision, reasons, fp, current, proposed, blast, transition) -> BreakerResult:
        return BreakerResult(
            decision=decision,
            reason_codes=tuple(reasons),
            request_fingerprint=fp,
            current_state=current,
            proposed_state=proposed,
            blast_radius_estimate=blast,
            transition_proposed=bool(transition),
            authoritative=False,
            dependencies_stopped=False,
            recovery_completed=False,
            action_executed=False,
            state_committed=False,
            cache_reused=False,
            created_unix_ns=time.time_ns(),
        )

    def _validate(self, s: CascadeSignal):
        if not s.request_id or not s.schema_version or not s.snapshot.node_id:
            return "MISSING_REQUIRED_FIELD"
        if not self._valid_nonnegative_int(s.observed_epoch_s):
            return "INVALID_OBSERVED_TIME"
        if not self._valid_nonnegative_int(s.snapshot.generation):
            return "INVALID_SNAPSHOT_GENERATION"
        if s.expected_generation is not None and s.expected_generation != s.snapshot.generation:
            return "SNAPSHOT_GENERATION_MISMATCH"
        for v, name in [
            (s.consecutive_failures, "CONSECUTIVE_FAILURES"),
            (s.failure_count_window, "FAILURE_COUNT_WINDOW"),
            (s.sample_count_window, "SAMPLE_COUNT_WINDOW"),
            (s.fanout_estimate, "FANOUT_ESTIMATE"),
            (s.recovery_successes, "RECOVERY_SUCCESSES"),
        ]:
            if not self._valid_nonnegative_int(v):
                return f"INVALID_{name}"
        if not self._valid_percent(s.error_rate_percent):
            return "INVALID_ERROR_RATE"
        if s.failure_count_window > s.sample_count_window:
            return "FAILURE_COUNT_EXCEEDS_SAMPLE_COUNT"
        if len(s.dependency_ids) != len(set(s.dependency_ids)):
            return "DUPLICATE_DEPENDENCY_ID"
        if any(not x for x in s.dependency_ids):
            return "EMPTY_DEPENDENCY_ID"
        if s.snapshot.state == CircuitState.OPEN:
            if s.snapshot.opened_at_epoch_s is None:
                return "OPEN_STATE_REQUIRES_OPENED_AT"
            if not self._valid_nonnegative_int(s.snapshot.opened_at_epoch_s):
                return "INVALID_OPENED_AT"
            if s.snapshot.opened_at_epoch_s > s.observed_epoch_s:
                return "OPENED_AT_IN_FUTURE"
        return None

    def _trip_reasons(self, s: CascadeSignal):
        reasons = []
        if s.upstream_breaker_open:
            reasons.append("UPSTREAM_BREAKER_OPEN")
        if s.validated_failure_evidence and s.consecutive_failures >= self.policy.consecutive_failure_threshold:
            reasons.append("CONSECUTIVE_FAILURE_THRESHOLD")
        if s.validated_failure_evidence and s.failure_count_window >= self.policy.failure_count_threshold:
            reasons.append("FAILURE_COUNT_THRESHOLD")
        if s.validated_failure_evidence and s.sample_count_window > 0 and s.error_rate_percent >= self.policy.error_rate_threshold_percent:
            reasons.append("ERROR_RATE_THRESHOLD")
        if s.validated_failure_evidence and s.fanout_estimate >= self.policy.fanout_trip_threshold:
            reasons.append("FANOUT_THRESHOLD")
        if s.validated_failure_evidence and s.critical_dependency_failure:
            reasons.append("CRITICAL_DEPENDENCY_FAILURE")
        return tuple(reasons)

    def _evaluate_uncached(self, s: CascadeSignal) -> BreakerResult:
        fp = self.fingerprint(s)
        err = self._validate(s)
        if err:
            return self._make(BreakerDecision.HOLD, (err,), fp, s.snapshot.state, s.snapshot.state, 0, False)

        blast = max(s.fanout_estimate, len(s.dependency_ids))

        # Emergency stop always proposes OPEN and cannot be overridden by approval.
        if s.emergency_stop_active:
            return self._make(
                BreakerDecision.TRIP_PREPARE,
                ("EMERGENCY_STOP_ACTIVE",),
                fp, s.snapshot.state, CircuitState.OPEN, blast, s.snapshot.state != CircuitState.OPEN
            )

        trip_reasons = self._trip_reasons(s)

        if s.snapshot.state == CircuitState.CLOSED:
            # Raw/unvalidated failure counts alone are not enough to trip.
            if not s.validated_failure_evidence and (
                s.consecutive_failures or s.failure_count_window or s.error_rate_percent or s.critical_dependency_failure
            ):
                return self._make(
                    BreakerDecision.HOLD,
                    ("FAILURE_EVIDENCE_NOT_VALIDATED",),
                    fp, CircuitState.CLOSED, CircuitState.CLOSED, blast, False
                )
            if trip_reasons:
                if (
                    "CRITICAL_DEPENDENCY_FAILURE" in trip_reasons
                    and self.policy.critical_failure_requires_human
                    and not (s.human_approved and s.approval_ref)
                ):
                    return self._make(
                        BreakerDecision.TRIP_PREPARE,
                        tuple(trip_reasons) + ("HUMAN_REVIEW_REQUIRED_FOR_CRITICAL_FAILURE",),
                        fp, CircuitState.CLOSED, CircuitState.OPEN, blast, True
                    )
                return self._make(
                    BreakerDecision.TRIP_PREPARE,
                    trip_reasons,
                    fp, CircuitState.CLOSED, CircuitState.OPEN, blast, True
                )
            return self._make(
                BreakerDecision.ALLOW_PREPARE,
                ("HEALTH_WITHIN_THRESHOLDS",),
                fp, CircuitState.CLOSED, CircuitState.CLOSED, blast, False
            )

        if s.snapshot.state == CircuitState.OPEN:
            # OPEN remains OPEN until cooldown and an explicitly authorized probe.
            if not s.cooldown_elapsed:
                return self._make(
                    BreakerDecision.TRIP_PREPARE,
                    ("OPEN_COOLDOWN_NOT_ELAPSED",),
                    fp, CircuitState.OPEN, CircuitState.OPEN, blast, False
                )
            if not s.recovery_probe_authorized:
                return self._make(
                    BreakerDecision.HOLD,
                    ("RECOVERY_PROBE_AUTHORIZATION_REQUIRED",),
                    fp, CircuitState.OPEN, CircuitState.OPEN, blast, False
                )
            return self._make(
                BreakerDecision.RECOVERY_PROBE,
                ("AUTHORIZED_HALF_OPEN_PROBE_CANDIDATE",),
                fp, CircuitState.OPEN, CircuitState.HALF_OPEN, blast, True
            )

        # HALF_OPEN
        if trip_reasons:
            return self._make(
                BreakerDecision.TRIP_PREPARE,
                tuple(trip_reasons) + ("HALF_OPEN_FAILURE_RETRIP",),
                fp, CircuitState.HALF_OPEN, CircuitState.OPEN, blast, True
            )
        if not s.validated_failure_evidence and (s.consecutive_failures or s.failure_count_window or s.error_rate_percent):
            return self._make(
                BreakerDecision.HOLD,
                ("HALF_OPEN_UNVALIDATED_FAILURE_SIGNAL",),
                fp, CircuitState.HALF_OPEN, CircuitState.HALF_OPEN, blast, False
            )
        if s.recovery_successes < self.policy.recovery_success_threshold:
            return self._make(
                BreakerDecision.HOLD,
                ("RECOVERY_SUCCESS_THRESHOLD_NOT_MET",),
                fp, CircuitState.HALF_OPEN, CircuitState.HALF_OPEN, blast, False
            )
        if not (s.human_approved and s.approval_ref):
            return self._make(
                BreakerDecision.CLOSE_PREPARE,
                ("RECOVERY_EVIDENCE_PRESENT_HUMAN_CONFIRMATION_REQUIRED",),
                fp, CircuitState.HALF_OPEN, CircuitState.CLOSED, blast, True
            )
        return self._make(
            BreakerDecision.CLOSE_PREPARE,
            ("RECOVERY_EVIDENCE_AND_APPROVAL_PRESENT",),
            fp, CircuitState.HALF_OPEN, CircuitState.CLOSED, blast, True
        )

    def evaluate(self, signal: CascadeSignal) -> BreakerResult:
        # Emergency stop bypasses cache to guarantee precedence.
        if signal.emergency_stop_active:
            return self._evaluate_uncached(signal)

        fp = self.fingerprint(signal)
        key = (fp, self.policy.policy_version)
        if self.enable_exact_state_cache and key in self._cache:
            r = self._cache[key]
            return BreakerResult(
                decision=r.decision,
                reason_codes=r.reason_codes,
                request_fingerprint=fp,
                current_state=r.current_state,
                proposed_state=r.proposed_state,
                blast_radius_estimate=r.blast_radius_estimate,
                transition_proposed=r.transition_proposed,
                authoritative=False,
                dependencies_stopped=False,
                recovery_completed=False,
                action_executed=False,
                state_committed=False,
                cache_reused=True,
                created_unix_ns=time.time_ns(),
            )
        result = self._evaluate_uncached(signal)
        if self.enable_exact_state_cache:
            self._cache[key] = result
        return result

    def clear_cache(self) -> None:
        self._cache.clear()

    def cache_size(self) -> int:
        return len(self._cache)
