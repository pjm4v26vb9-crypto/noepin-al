"""NOEPIN AL 050 — Independent Safety Monitor.

Pure control-plane evaluator implementing Separate Context, Monitor-only Privileges,
and Blocking Verdict candidates. The monitor evaluates worker plan/tool observations from
an independently-bound context without invoking tools, blocking processes, granting
permission, or promoting observations/fingerprints to truth or safety proof.

Creator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support using ChatGPT
License / Rights: NOT SPECIFIED
"""
from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
from hashlib import sha256
import json
from typing import Any, FrozenSet, Iterable, Mapping, Tuple


class ControlDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    HOLD = "HOLD"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"


class PrivilegeMode(str, Enum):
    MONITOR_ONLY = "MONITOR_ONLY"


class SignalSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


_SEVERITY_WEIGHT = {
    SignalSeverity.INFO: 0.00,
    SignalSeverity.LOW: 0.10,
    SignalSeverity.MEDIUM: 0.25,
    SignalSeverity.HIGH: 0.45,
    SignalSeverity.CRITICAL: 0.80,
}


@dataclass(frozen=True)
class MonitorPolicy:
    policy_id: str
    version: str
    authority_epoch: int
    issued_at: int
    expires_at: int
    trusted_monitor_ids: FrozenSet[str]
    trusted_independent_sources: FrozenSet[str]
    allowed_channels: FrozenSet[str]
    prohibited_tool_operations: FrozenSet[str]
    human_review_threshold: float
    block_threshold: float
    max_observation_age_seconds: int
    max_observations: int
    require_independent_evidence: bool = True
    revoked: bool = False

    def validate(self, now: int) -> None:
        if not self.policy_id or not self.version:
            raise ValueError("policy id/version required")
        if self.authority_epoch < 1:
            raise ValueError("authority_epoch must be >=1")
        if self.issued_at < 0 or self.expires_at <= self.issued_at:
            raise ValueError("invalid policy lifetime")
        if not self.issued_at <= now < self.expires_at:
            raise ValueError("policy not current")
        if not self.trusted_monitor_ids or not self.trusted_independent_sources or not self.allowed_channels:
            raise ValueError("trusted monitor/source/channel required")
        if not 0 <= self.human_review_threshold < self.block_threshold <= 1:
            raise ValueError("invalid monitor thresholds")
        if self.max_observation_age_seconds < 1 or self.max_observations < 1:
            raise ValueError("invalid observation limits")


@dataclass(frozen=True)
class MonitorContext:
    monitor_id: str
    privilege_mode: PrivilegeMode
    independent_source_id: str
    channels: FrozenSet[str]
    evidence_binding: str
    evidence_verified: bool
    context_epoch: int

    def validate(self) -> None:
        if not self.monitor_id or not self.independent_source_id or not self.evidence_binding:
            raise ValueError("monitor/source/evidence required")
        if self.privilege_mode is not PrivilegeMode.MONITOR_ONLY:
            raise ValueError("monitor must be monitor-only")
        if not self.channels:
            raise ValueError("monitor channels required")
        if self.context_epoch < 1:
            raise ValueError("context epoch must be >=1")


@dataclass(frozen=True)
class SafetyObservation:
    observation_id: str
    worker_id: str
    task_id: str
    observed_at: int
    channel: str
    signal_code: str
    severity: SignalSeverity
    risk_score: float
    tool_name: str
    operation: str
    plan_fingerprint: str
    evidence_binding: str
    evidence_verified: bool
    source_is_independent: bool
    worker_self_reported: bool = False
    revoked: bool = False

    def validate(self) -> None:
        if not self.observation_id or not self.worker_id or not self.task_id:
            raise ValueError("observation/worker/task required")
        if self.observed_at < 0 or not self.channel or not self.signal_code:
            raise ValueError("time/channel/signal required")
        if not 0 <= self.risk_score <= 1:
            raise ValueError("risk_score out of range")
        if not self.tool_name or not self.operation or not self.plan_fingerprint or not self.evidence_binding:
            raise ValueError("tool/operation/plan/evidence required")


@dataclass(frozen=True)
class MonitorRequest:
    request_id: str
    worker_id: str
    task_id: str
    plan_fingerprint: str
    requested_tool: str
    requested_operation: str
    expected_policy_id: str
    expected_policy_version: str
    expected_authority_epoch: int
    expected_context_epoch: int
    evidence_binding: str

    def validate(self) -> None:
        if not self.request_id or not self.worker_id or not self.task_id or not self.plan_fingerprint:
            raise ValueError("request/worker/task/plan required")
        if not self.requested_tool or not self.requested_operation:
            raise ValueError("tool/operation required")
        if not self.expected_policy_id or not self.expected_policy_version or self.expected_authority_epoch < 1:
            raise ValueError("policy binding required")
        if self.expected_context_epoch < 1 or not self.evidence_binding:
            raise ValueError("context/evidence binding required")


@dataclass(frozen=True)
class PreparedObservationRegistry:
    registry_fingerprint: str
    policy_fingerprint: str
    context_fingerprint: str
    observations: Tuple[SafetyObservation, ...]
    observation_fingerprints: Mapping[str, str]
    task_index: Mapping[str, Tuple[str, ...]]
    worker_index: Mapping[str, Tuple[str, ...]]
    channel_index: Mapping[str, Tuple[str, ...]]


@dataclass(frozen=True)
class ObservationDelta:
    base_fingerprint: str
    target_fingerprint: str
    changed_observations: Tuple[SafetyObservation, ...]
    removed_observation_ids: Tuple[str, ...]
    added_observations: Tuple[SafetyObservation, ...]


@dataclass(frozen=True)
class RegistrySyncPlan:
    missing_or_changed_observation_ids: Tuple[str, ...]
    metadata_bytes_required: int
    full_metadata_bytes: int
    full_resend_required: bool
    permission_granted: bool = False
    block_execution_authorized: bool = False
    tool_execution_authorized: bool = False


@dataclass(frozen=True)
class MonitorVerdict:
    decision: ControlDecision
    reasons: Tuple[str, ...]
    request_id: str
    worker_id: str
    task_id: str
    risk_score: float
    active_observation_ids: Tuple[str, ...]
    independent_observation_ids: Tuple[str, ...]
    self_report_observation_ids: Tuple[str, ...]
    prohibited_operation_observed: bool
    block_candidate: bool
    human_review_candidate: bool
    registry_fingerprint: str
    policy_fingerprint: str
    context_fingerprint: str
    request_fingerprint: str
    permission_granted: bool = False
    block_executed: bool = False
    tool_executed: bool = False
    action_success: bool = False
    observed_signal_truth_proven: bool = False
    system_safe_proven: bool = False


def _canonical(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {f.name: _canonical(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (set, frozenset)):
        vals = [_canonical(v) for v in value]
        return sorted(vals, key=lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    if isinstance(value, (tuple, list)):
        return [_canonical(v) for v in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(_canonical(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _normalize(observations: Iterable[SafetyObservation]) -> Tuple[SafetyObservation, ...]:
    out = tuple(sorted(observations, key=lambda x: x.observation_id))
    ids = [o.observation_id for o in out]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate observation_id")
    for o in out:
        o.validate()
    return out


def registry_fingerprint(observations: Iterable[SafetyObservation]) -> str:
    return fingerprint(_normalize(observations))


def prepare_registry(policy: MonitorPolicy, context: MonitorContext, observations: Iterable[SafetyObservation], *, now: int) -> PreparedObservationRegistry:
    policy.validate(now)
    context.validate()
    if policy.revoked:
        raise ValueError("policy revoked")
    if context.monitor_id not in policy.trusted_monitor_ids:
        raise ValueError("untrusted monitor")
    if context.independent_source_id not in policy.trusted_independent_sources:
        raise ValueError("untrusted independent source")
    if not context.channels <= policy.allowed_channels:
        raise ValueError("context channel outside policy")
    if not context.evidence_verified:
        raise ValueError("context evidence unverified")
    items = _normalize(observations)
    if len(items) > policy.max_observations:
        raise ValueError("observation count exceeds policy")
    fps = {o.observation_id: fingerprint(o) for o in items}
    task: dict[str, list[str]] = {}
    worker: dict[str, list[str]] = {}
    channel: dict[str, list[str]] = {}
    for o in items:
        task.setdefault(o.task_id, []).append(o.observation_id)
        worker.setdefault(o.worker_id, []).append(o.observation_id)
        channel.setdefault(o.channel, []).append(o.observation_id)
    return PreparedObservationRegistry(
        registry_fingerprint=registry_fingerprint(items),
        policy_fingerprint=fingerprint(policy),
        context_fingerprint=fingerprint(context),
        observations=items,
        observation_fingerprints=fps,
        task_index={k: tuple(sorted(v)) for k, v in sorted(task.items())},
        worker_index={k: tuple(sorted(v)) for k, v in sorted(worker.items())},
        channel_index={k: tuple(sorted(v)) for k, v in sorted(channel.items())},
    )


def _fail(request: MonitorRequest, policy: MonitorPolicy, context: MonitorContext, observations: Iterable[SafetyObservation], reason: str) -> MonitorVerdict:
    items = tuple(observations)
    return MonitorVerdict(
        decision=ControlDecision.HOLD,
        reasons=(reason,),
        request_id=request.request_id,
        worker_id=request.worker_id,
        task_id=request.task_id,
        risk_score=0.0,
        active_observation_ids=(),
        independent_observation_ids=(),
        self_report_observation_ids=(),
        prohibited_operation_observed=False,
        block_candidate=False,
        human_review_candidate=False,
        registry_fingerprint=registry_fingerprint(items) if items else fingerprint(()),
        policy_fingerprint=fingerprint(policy),
        context_fingerprint=fingerprint(context),
        request_fingerprint=fingerprint(request),
    )


def _validate_bindings(request: MonitorRequest, policy: MonitorPolicy, context: MonitorContext, *, now: int) -> str | None:
    try:
        request.validate(); policy.validate(now); context.validate()
    except ValueError as exc:
        return f"INVALID_INPUT:{exc}"
    if policy.revoked:
        return "POLICY_REVOKED"
    if request.expected_policy_id != policy.policy_id:
        return "POLICY_ID_MISMATCH"
    if request.expected_policy_version != policy.version:
        return "POLICY_VERSION_MISMATCH"
    if request.expected_authority_epoch != policy.authority_epoch:
        return "AUTHORITY_EPOCH_MISMATCH"
    if request.expected_context_epoch != context.context_epoch:
        return "CONTEXT_EPOCH_MISMATCH"
    if request.evidence_binding != context.evidence_binding:
        return "EVIDENCE_BINDING_MISMATCH"
    if context.monitor_id not in policy.trusted_monitor_ids:
        return "UNTRUSTED_MONITOR"
    if context.independent_source_id not in policy.trusted_independent_sources:
        return "UNTRUSTED_INDEPENDENT_SOURCE"
    if context.privilege_mode is not PrivilegeMode.MONITOR_ONLY:
        return "MONITOR_PRIVILEGE_VIOLATION"
    if not context.channels <= policy.allowed_channels:
        return "CONTEXT_CHANNEL_OUTSIDE_POLICY"
    if not context.evidence_verified:
        return "CONTEXT_EVIDENCE_UNVERIFIED"
    return None


def evaluate_prepared(request: MonitorRequest, policy: MonitorPolicy, context: MonitorContext, prepared: PreparedObservationRegistry, *, now: int) -> MonitorVerdict:
    binding_error = _validate_bindings(request, policy, context, now=now)
    if binding_error:
        return _fail(request, policy, context, prepared.observations, binding_error)
    if prepared.policy_fingerprint != fingerprint(policy):
        return _fail(request, policy, context, prepared.observations, "PREPARED_POLICY_FINGERPRINT_MISMATCH")
    if prepared.context_fingerprint != fingerprint(context):
        return _fail(request, policy, context, prepared.observations, "PREPARED_CONTEXT_FINGERPRINT_MISMATCH")
    if prepared.registry_fingerprint != registry_fingerprint(prepared.observations):
        return _fail(request, policy, context, prepared.observations, "PREPARED_REGISTRY_FINGERPRINT_MISMATCH")

    active: list[SafetyObservation] = []
    reasons: list[str] = []
    for o in prepared.observations:
        if o.revoked or not o.evidence_verified:
            continue
        if o.worker_id != request.worker_id or o.task_id != request.task_id:
            continue
        if o.plan_fingerprint != request.plan_fingerprint:
            continue
        if o.evidence_binding != request.evidence_binding:
            continue
        if o.channel not in context.channels or o.channel not in policy.allowed_channels:
            continue
        age = now - o.observed_at
        if age < 0 or age > policy.max_observation_age_seconds:
            continue
        active.append(o)

    independent = [o for o in active if o.source_is_independent and not o.worker_self_reported]
    self_reports = [o for o in active if o.worker_self_reported]
    if policy.require_independent_evidence and not independent:
        reasons.append("INDEPENDENT_EVIDENCE_REQUIRED")
        return MonitorVerdict(
            decision=ControlDecision.HOLD,
            reasons=tuple(reasons),
            request_id=request.request_id,
            worker_id=request.worker_id,
            task_id=request.task_id,
            risk_score=0.0,
            active_observation_ids=tuple(o.observation_id for o in active),
            independent_observation_ids=(),
            self_report_observation_ids=tuple(o.observation_id for o in self_reports),
            prohibited_operation_observed=False,
            block_candidate=False,
            human_review_candidate=False,
            registry_fingerprint=prepared.registry_fingerprint,
            policy_fingerprint=prepared.policy_fingerprint,
            context_fingerprint=prepared.context_fingerprint,
            request_fingerprint=fingerprint(request),
        )

    score = 0.0
    prohibited = False
    for o in active:
        weight = _SEVERITY_WEIGHT[o.severity]
        if o.source_is_independent and not o.worker_self_reported:
            weight += 0.10
        score = max(score, min(1.0, max(o.risk_score, weight)))
        op_key = f"{o.tool_name}:{o.operation}"
        if op_key in policy.prohibited_tool_operations:
            prohibited = True
            score = max(score, 1.0)
    requested_key = f"{request.requested_tool}:{request.requested_operation}"
    if requested_key in policy.prohibited_tool_operations:
        prohibited = True
        score = 1.0

    if prohibited or score >= policy.block_threshold:
        decision = ControlDecision.DENY; block = True; human = True
        reasons.append("BLOCK_THRESHOLD_REACHED" if not prohibited else "PROHIBITED_TOOL_OPERATION")
    elif score >= policy.human_review_threshold:
        decision = ControlDecision.HUMAN_APPROVAL; block = False; human = True
        reasons.append("HUMAN_REVIEW_THRESHOLD_REACHED")
    else:
        decision = ControlDecision.ALLOW; block = False; human = False
        reasons.append("MONITOR_WITHIN_POLICY")

    return MonitorVerdict(
        decision=decision,
        reasons=tuple(reasons),
        request_id=request.request_id,
        worker_id=request.worker_id,
        task_id=request.task_id,
        risk_score=round(score, 6),
        active_observation_ids=tuple(o.observation_id for o in active),
        independent_observation_ids=tuple(o.observation_id for o in independent),
        self_report_observation_ids=tuple(o.observation_id for o in self_reports),
        prohibited_operation_observed=prohibited,
        block_candidate=block,
        human_review_candidate=human,
        registry_fingerprint=prepared.registry_fingerprint,
        policy_fingerprint=prepared.policy_fingerprint,
        context_fingerprint=prepared.context_fingerprint,
        request_fingerprint=fingerprint(request),
    )


def evaluate(request: MonitorRequest, policy: MonitorPolicy, context: MonitorContext, observations: Iterable[SafetyObservation], *, now: int) -> MonitorVerdict:
    items = tuple(observations)
    binding_error = _validate_bindings(request, policy, context, now=now)
    if binding_error:
        return _fail(request, policy, context, items, binding_error)
    try:
        prepared = prepare_registry(policy, context, items, now=now)
    except ValueError as exc:
        return _fail(request, policy, context, items, f"INVALID_REGISTRY:{exc}")
    return evaluate_prepared(request, policy, context, prepared, now=now)


def make_registry_delta(base: Iterable[SafetyObservation], target: Iterable[SafetyObservation]) -> ObservationDelta:
    b = {o.observation_id: o for o in _normalize(base)}
    t = {o.observation_id: o for o in _normalize(target)}
    changed = tuple(t[k] for k in sorted(b.keys() & t.keys()) if fingerprint(b[k]) != fingerprint(t[k]))
    removed = tuple(sorted(b.keys() - t.keys()))
    added = tuple(t[k] for k in sorted(t.keys() - b.keys()))
    return ObservationDelta(registry_fingerprint(b.values()), registry_fingerprint(t.values()), changed, removed, added)


def apply_registry_delta(base: Iterable[SafetyObservation], delta: ObservationDelta) -> Tuple[SafetyObservation, ...]:
    base_items = _normalize(base)
    if registry_fingerprint(base_items) != delta.base_fingerprint:
        raise ValueError("delta base fingerprint mismatch")
    d = {o.observation_id: o for o in base_items}
    for oid in delta.removed_observation_ids:
        d.pop(oid, None)
    for o in delta.changed_observations:
        if o.observation_id not in d:
            raise ValueError("changed observation missing from base")
        d[o.observation_id] = o
    for o in delta.added_observations:
        if o.observation_id in d:
            raise ValueError("added observation already exists")
        d[o.observation_id] = o
    out = _normalize(d.values())
    if registry_fingerprint(out) != delta.target_fingerprint:
        raise ValueError("delta target fingerprint mismatch")
    return out


def plan_registry_sync(target: Iterable[SafetyObservation], remote_known_fingerprints: Mapping[str, str]) -> RegistrySyncPlan:
    items = _normalize(target)
    missing = tuple(o.observation_id for o in items if remote_known_fingerprints.get(o.observation_id) != fingerprint(o))
    subset = tuple(o for o in items if o.observation_id in set(missing))
    full_bytes = len(canonical_json(items).encode("utf-8"))
    needed_bytes = len(canonical_json(subset).encode("utf-8"))
    return RegistrySyncPlan(missing, needed_bytes, full_bytes, needed_bytes >= full_bytes)


def verdicts_digest(items: Iterable[MonitorVerdict]) -> str:
    return fingerprint(tuple(items))


def default_policy(now: int) -> MonitorPolicy:
    return MonitorPolicy(
        policy_id="NOEPIN-AL-050-MONITOR-POLICY",
        version="1",
        authority_epoch=1,
        issued_at=now-1000,
        expires_at=now+100000,
        trusted_monitor_ids=frozenset({"MONITOR-050"}),
        trusted_independent_sources=frozenset({"OBS-SOURCE-050"}),
        allowed_channels=frozenset({"PLAN","TOOL","NETWORK","RISK"}),
        prohibited_tool_operations=frozenset({"EXTERNAL_SEND:SEND_SECRET","SHELL:EXECUTE_UNVERIFIED"}),
        human_review_threshold=0.55,
        block_threshold=0.80,
        max_observation_age_seconds=3600,
        max_observations=10000,
    )


def default_context() -> MonitorContext:
    return MonitorContext("MONITOR-050", PrivilegeMode.MONITOR_ONLY, "OBS-SOURCE-050", frozenset({"PLAN","TOOL","NETWORK","RISK"}), "MONITOR-EVIDENCE-050", True, 1)


def default_request(now: int) -> MonitorRequest:
    p = default_policy(now); c = default_context()
    return MonitorRequest("REQ-050","WORKER-A","TASK-A","PLAN-A","FILE_READ","READ_LOCAL",p.policy_id,p.version,p.authority_epoch,c.context_epoch,c.evidence_binding)


def default_observations(now: int) -> Tuple[SafetyObservation, ...]:
    c=default_context()
    return (
        SafetyObservation("OBS-050-1","WORKER-A","TASK-A",now-10,"PLAN","PLAN_STABLE",SignalSeverity.LOW,0.10,"FILE_READ","READ_LOCAL","PLAN-A",c.evidence_binding,True,True,False),
        SafetyObservation("OBS-050-2","WORKER-A","TASK-A",now-8,"TOOL","TOOL_CALL_MATCH",SignalSeverity.LOW,0.10,"FILE_READ","READ_LOCAL","PLAN-A",c.evidence_binding,True,False,True),
    )


ORIGIN_GUID_POLICY = "PRESERVE_EXISTING_SYSTEM_ORIGIN_GUID_BY_PROVENANCE_REFERENCE"
LICENSE_RIGHTS = "NOT SPECIFIED"
CREATOR = "NOEPIN / のえぴん"
