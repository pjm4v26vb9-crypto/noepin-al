"""NOEPIN AL 041 — AI Behavior Anomaly Detection.

Creator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん

AI-assisted implementation / analysis / documentation support using ChatGPT.
License / Rights: NOT SPECIFIED.

This module is a pure pre-execution/control-plane evaluator. It compares supplied
behavior events with an authoritative, versioned baseline. It does not execute
alerts, stop agents, grant permissions, persist memory, contact external systems,
or prove compromise/safety/truth.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from enum import Enum
from hashlib import sha256
import json
from typing import Any, FrozenSet, Iterable, Mapping, Optional, Tuple

CREATOR = "NOEPIN / のえぴん"
PROJECT_OWNER = CREATOR
ORIGINAL_CONCEPT = CREATOR
ARCHITECTURE_DIRECTION = CREATOR
AI_SUPPORT = "AI-assisted implementation / analysis / documentation support using ChatGPT"
LICENSE_RIGHTS = "NOT SPECIFIED"
TECHNOLOGY_NUMBER = 41
TECHNOLOGY_NAME = "AI行動異常検知"
SCHEMA_VERSION = "NOEPIN_AL_041_V2"
# The existing System Origin GUID remains authoritative in the immutable V1/provenance chain.
# Successor V2 does not invent or replace a GUID when the baseline attachment byte identity is unverified.
ORIGIN_GUID_POLICY = "PRESERVE_EXISTING_SYSTEM_ORIGIN_GUID_BY_PROVENANCE_REFERENCE"


class ControlDecision(str, Enum):
    ALLOW = "ALLOW"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"
    HOLD = "HOLD"
    DENY = "DENY"


class DetectionLevel(str, Enum):
    NORMAL = "NORMAL"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    INDETERMINATE = "INDETERMINATE"


class RecommendedControl(str, Enum):
    CONTINUE = "CONTINUE"
    ALERT_AND_REVIEW = "ALERT_AND_REVIEW"
    HOLD_CANDIDATE = "HOLD_CANDIDATE"
    STOP_CANDIDATE = "STOP_CANDIDATE"


@dataclass(frozen=True)
class BehaviorBaseline:
    baseline_id: str
    version: str
    authority_epoch: int
    issued_at: int
    expires_at: int
    allowed_tools: FrozenSet[str]
    allowed_operations: FrozenSet[str]
    allowed_tool_operation_pairs: FrozenSet[str]
    allowed_resource_classes: FrozenSet[str]
    allowed_hours_utc: FrozenSet[int]
    max_events_per_minute: float
    max_tool_calls_per_minute: float
    expected_capabilities: FrozenSet[str] = field(default_factory=frozenset)
    alert_threshold: float = 0.35
    hold_threshold: float = 0.70
    deny_threshold: float = 0.90
    revoked: bool = False

    def validate(self, now: int) -> None:
        if not self.baseline_id or not self.version:
            raise ValueError("baseline identity/version required")
        if self.authority_epoch < 1:
            raise ValueError("authority_epoch must be >= 1")
        if self.issued_at < 0 or self.expires_at <= self.issued_at:
            raise ValueError("invalid baseline lifetime")
        if self.revoked:
            raise ValueError("baseline revoked")
        if now < self.issued_at:
            raise ValueError("baseline not yet valid")
        if now >= self.expires_at:
            raise ValueError("baseline expired")
        for group in (
            self.allowed_tools, self.allowed_operations, self.allowed_tool_operation_pairs,
            self.allowed_resource_classes, self.expected_capabilities,
        ):
            if any(not isinstance(x, str) or not x.strip() for x in group):
                raise ValueError("invalid baseline token")
        if any(not isinstance(h, int) or h < 0 or h > 23 for h in self.allowed_hours_utc):
            raise ValueError("allowed_hours_utc must be 0..23")
        if self.max_events_per_minute <= 0 or self.max_tool_calls_per_minute < 0:
            raise ValueError("invalid rate limits")
        if not (0.0 <= self.alert_threshold < self.hold_threshold < self.deny_threshold <= 1.0):
            raise ValueError("invalid anomaly thresholds")


@dataclass(frozen=True)
class BehaviorEvent:
    event_id: str
    actor_id: str
    observed_at: int
    tool_name: str
    operation: str
    resource_class: str
    events_per_minute: float
    tool_calls_per_minute: float
    capabilities: FrozenSet[str]
    expected_baseline_id: str
    expected_baseline_version: str
    expected_authority_epoch: int
    evidence_id: str
    evidence_verified: bool

    def validate(self) -> None:
        if not self.event_id or not self.actor_id or not self.evidence_id:
            raise ValueError("event identity/evidence required")
        if self.observed_at < 0:
            raise ValueError("observed_at must be non-negative")
        if not self.tool_name or not self.operation or not self.resource_class:
            raise ValueError("tool/operation/resource required")
        if self.events_per_minute < 0 or self.tool_calls_per_minute < 0:
            raise ValueError("rates must be non-negative")
        if self.expected_authority_epoch < 1:
            raise ValueError("expected_authority_epoch must be >=1")
        if any(not isinstance(x, str) or not x.strip() for x in self.capabilities):
            raise ValueError("invalid capability")


@dataclass(frozen=True)
class AnomalyFinding:
    decision: ControlDecision
    level: DetectionLevel
    anomaly_score: float
    reasons: Tuple[str, ...]
    recommended_control: RecommendedControl
    baseline_id: str
    baseline_version: str
    authority_epoch: int
    event_id: str
    baseline_fingerprint: str
    event_fingerprint: str
    alert_candidate: bool
    stop_recommended: bool
    compromise_proven: bool = False
    system_safe_proven: bool = False
    permission_granted: bool = False
    alert_executed: bool = False
    stop_executed: bool = False
    action_success: bool = False
    truth_established: bool = False


@dataclass(frozen=True)
class PreparedBaseline:
    baseline: BehaviorBaseline
    baseline_fingerprint: str
    tool_operation_pairs: FrozenSet[str]


@dataclass(frozen=True)
class BaselineDelta:
    base_fingerprint: str
    target_fingerprint: str
    target_baseline_id: str
    target_version: str
    target_authority_epoch: int
    target_issued_at: int
    target_expires_at: int
    target_max_events_per_minute: float
    target_max_tool_calls_per_minute: float
    target_alert_threshold: float
    target_hold_threshold: float
    target_deny_threshold: float
    target_revoked: bool
    add_tools: Tuple[str, ...]
    remove_tools: Tuple[str, ...]
    add_operations: Tuple[str, ...]
    remove_operations: Tuple[str, ...]
    add_pairs: Tuple[str, ...]
    remove_pairs: Tuple[str, ...]
    add_resources: Tuple[str, ...]
    remove_resources: Tuple[str, ...]
    add_hours: Tuple[int, ...]
    remove_hours: Tuple[int, ...]
    add_capabilities: Tuple[str, ...]
    remove_capabilities: Tuple[str, ...]


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(k): _jsonable(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (set, frozenset)):
        vals = [_jsonable(v) for v in value]
        vals.sort(key=lambda x: json.dumps(x, sort_keys=True, ensure_ascii=False))
        return vals
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if hasattr(value, "__dataclass_fields__"):
        return {k: _jsonable(v) for k, v in asdict(value).items()}
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(_jsonable(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _pair(tool_name: str, operation: str) -> str:
    return f"{tool_name}|{operation}"


def prepare_baseline(baseline: BehaviorBaseline, *, now: int) -> PreparedBaseline:
    baseline.validate(now)
    return PreparedBaseline(
        baseline=baseline,
        baseline_fingerprint=fingerprint(baseline),
        tool_operation_pairs=frozenset(baseline.allowed_tool_operation_pairs),
    )


def _indeterminate(event: BehaviorEvent, baseline: BehaviorBaseline, reasons: Iterable[str]) -> AnomalyFinding:
    return AnomalyFinding(
        decision=ControlDecision.HOLD,
        level=DetectionLevel.INDETERMINATE,
        anomaly_score=0.0,
        reasons=tuple(reasons),
        recommended_control=RecommendedControl.HOLD_CANDIDATE,
        baseline_id=baseline.baseline_id,
        baseline_version=baseline.version,
        authority_epoch=baseline.authority_epoch,
        event_id=event.event_id,
        baseline_fingerprint=fingerprint(baseline),
        event_fingerprint=fingerprint(event),
        alert_candidate=True,
        stop_recommended=False,
    )


def _rate_penalty(observed: float, maximum: float) -> float:
    if observed <= maximum:
        return 0.0
    if maximum <= 0:
        return 0.25
    ratio = observed / maximum
    return min(0.25, 0.10 + 0.05 * min(3.0, max(0.0, ratio - 1.0)))


def evaluate_prepared(event: BehaviorEvent, prepared: PreparedBaseline, *, now: int) -> AnomalyFinding:
    baseline = prepared.baseline
    try:
        baseline.validate(now)
    except ValueError as exc:
        # Invalid authority state is fail-closed, not proof of anomalous behavior.
        dummy = event if isinstance(event, BehaviorEvent) else BehaviorEvent(
            "INVALID", "UNKNOWN", max(0, now), "UNKNOWN", "UNKNOWN", "UNKNOWN", 0, 0,
            frozenset(), baseline.baseline_id, baseline.version, max(1, baseline.authority_epoch),
            "INVALID", False,
        )
        return _indeterminate(dummy, baseline, (f"BASELINE_INVALID:{str(exc)}",))
    try:
        event.validate()
    except (ValueError, AttributeError) as exc:
        dummy = event if isinstance(event, BehaviorEvent) else BehaviorEvent(
            "INVALID", "UNKNOWN", max(0, now), "UNKNOWN", "UNKNOWN", "UNKNOWN", 0, 0,
            frozenset(), baseline.baseline_id, baseline.version, baseline.authority_epoch,
            "INVALID", False,
        )
        return _indeterminate(dummy, baseline, (f"EVENT_INVALID:{str(exc)}",))

    binding_reasons = []
    if event.expected_baseline_id != baseline.baseline_id:
        binding_reasons.append("BASELINE_ID_MISMATCH")
    if event.expected_baseline_version != baseline.version:
        binding_reasons.append("BASELINE_VERSION_MISMATCH")
    if event.expected_authority_epoch != baseline.authority_epoch:
        binding_reasons.append("AUTHORITY_EPOCH_MISMATCH")
    if event.observed_at > now:
        binding_reasons.append("EVENT_FROM_FUTURE")
    if not event.evidence_verified:
        binding_reasons.append("EVIDENCE_UNVERIFIED")
    if binding_reasons:
        return _indeterminate(event, baseline, binding_reasons)

    score = 0.0
    reasons: list[str] = []
    if event.tool_name not in baseline.allowed_tools:
        score += 0.45
        reasons.append("TOOL_OUTSIDE_BASELINE")
    if event.operation not in baseline.allowed_operations:
        score += 0.35
        reasons.append("OPERATION_OUTSIDE_BASELINE")
    if _pair(event.tool_name, event.operation) not in prepared.tool_operation_pairs:
        score += 0.25
        reasons.append("TOOL_OPERATION_PAIR_OUTSIDE_BASELINE")
    if event.resource_class not in baseline.allowed_resource_classes:
        score += 0.15
        reasons.append("RESOURCE_CLASS_OUTSIDE_BASELINE")
    hour = (event.observed_at // 3600) % 24
    if baseline.allowed_hours_utc and hour not in baseline.allowed_hours_utc:
        score += 0.10
        reasons.append("TIME_WINDOW_OUTSIDE_BASELINE")
    event_penalty = _rate_penalty(event.events_per_minute, baseline.max_events_per_minute)
    if event_penalty:
        score += event_penalty
        reasons.append("EVENT_RATE_ABOVE_BASELINE")
    tool_penalty = _rate_penalty(event.tool_calls_per_minute, baseline.max_tool_calls_per_minute)
    if tool_penalty:
        score += tool_penalty
        reasons.append("TOOL_RATE_ABOVE_BASELINE")
    unexpected_caps = sorted(event.capabilities - baseline.expected_capabilities)
    if unexpected_caps:
        score += min(0.35, 0.20 + 0.05 * min(3, len(unexpected_caps)))
        reasons.extend(f"CAPABILITY_OUTSIDE_BASELINE:{x}" for x in unexpected_caps)

    score = round(min(1.0, score), 6)
    if score >= baseline.deny_threshold:
        decision = ControlDecision.DENY
        level = DetectionLevel.CRITICAL
        control = RecommendedControl.STOP_CANDIDATE
        stop_recommended = True
    elif score >= baseline.hold_threshold:
        decision = ControlDecision.HOLD
        level = DetectionLevel.HIGH
        control = RecommendedControl.HOLD_CANDIDATE
        stop_recommended = False
    elif score >= baseline.alert_threshold:
        decision = ControlDecision.HUMAN_APPROVAL
        level = DetectionLevel.MEDIUM
        control = RecommendedControl.ALERT_AND_REVIEW
        stop_recommended = False
    else:
        decision = ControlDecision.ALLOW
        level = DetectionLevel.NORMAL
        control = RecommendedControl.CONTINUE
        stop_recommended = False
        if not reasons:
            reasons.append("BASELINE_MATCH")

    return AnomalyFinding(
        decision=decision,
        level=level,
        anomaly_score=score,
        reasons=tuple(reasons),
        recommended_control=control,
        baseline_id=baseline.baseline_id,
        baseline_version=baseline.version,
        authority_epoch=baseline.authority_epoch,
        event_id=event.event_id,
        baseline_fingerprint=prepared.baseline_fingerprint,
        event_fingerprint=fingerprint(event),
        alert_candidate=decision is not ControlDecision.ALLOW,
        stop_recommended=stop_recommended,
    )


def evaluate(event: BehaviorEvent, baseline: BehaviorBaseline, *, now: int) -> AnomalyFinding:
    """Full-materialization reference path."""
    try:
        prepared = prepare_baseline(baseline, now=now)
    except ValueError as exc:
        # Preserve fail-closed semantics without letting invalid authority data crash callers.
        return _indeterminate(event, baseline, (f"BASELINE_INVALID:{str(exc)}",))
    return evaluate_prepared(event, prepared, now=now)


def make_baseline_delta(base: BehaviorBaseline, target: BehaviorBaseline) -> BaselineDelta:
    def diff(a: Iterable[Any], b: Iterable[Any]):
        sa, sb = set(a), set(b)
        return tuple(sorted(sb - sa)), tuple(sorted(sa - sb))

    add_tools, rem_tools = diff(base.allowed_tools, target.allowed_tools)
    add_ops, rem_ops = diff(base.allowed_operations, target.allowed_operations)
    add_pairs, rem_pairs = diff(base.allowed_tool_operation_pairs, target.allowed_tool_operation_pairs)
    add_res, rem_res = diff(base.allowed_resource_classes, target.allowed_resource_classes)
    add_hours, rem_hours = diff(base.allowed_hours_utc, target.allowed_hours_utc)
    add_caps, rem_caps = diff(base.expected_capabilities, target.expected_capabilities)
    return BaselineDelta(
        base_fingerprint=fingerprint(base), target_fingerprint=fingerprint(target),
        target_baseline_id=target.baseline_id, target_version=target.version,
        target_authority_epoch=target.authority_epoch, target_issued_at=target.issued_at,
        target_expires_at=target.expires_at,
        target_max_events_per_minute=target.max_events_per_minute,
        target_max_tool_calls_per_minute=target.max_tool_calls_per_minute,
        target_alert_threshold=target.alert_threshold, target_hold_threshold=target.hold_threshold,
        target_deny_threshold=target.deny_threshold, target_revoked=target.revoked,
        add_tools=add_tools, remove_tools=rem_tools,
        add_operations=add_ops, remove_operations=rem_ops,
        add_pairs=add_pairs, remove_pairs=rem_pairs,
        add_resources=add_res, remove_resources=rem_res,
        add_hours=add_hours, remove_hours=rem_hours,
        add_capabilities=add_caps, remove_capabilities=rem_caps,
    )


def apply_baseline_delta(base: BehaviorBaseline, delta: BaselineDelta) -> BehaviorBaseline:
    if fingerprint(base) != delta.base_fingerprint:
        raise ValueError("base fingerprint mismatch")

    def apply(values: Iterable[Any], adds: Iterable[Any], removes: Iterable[Any]) -> frozenset:
        out = set(values)
        out.difference_update(removes)
        out.update(adds)
        return frozenset(out)

    target = BehaviorBaseline(
        baseline_id=delta.target_baseline_id,
        version=delta.target_version,
        authority_epoch=delta.target_authority_epoch,
        issued_at=delta.target_issued_at,
        expires_at=delta.target_expires_at,
        revoked=delta.target_revoked,
        allowed_tools=apply(base.allowed_tools, delta.add_tools, delta.remove_tools),
        allowed_operations=apply(base.allowed_operations, delta.add_operations, delta.remove_operations),
        allowed_tool_operation_pairs=apply(base.allowed_tool_operation_pairs, delta.add_pairs, delta.remove_pairs),
        allowed_resource_classes=apply(base.allowed_resource_classes, delta.add_resources, delta.remove_resources),
        allowed_hours_utc=apply(base.allowed_hours_utc, delta.add_hours, delta.remove_hours),
        max_events_per_minute=delta.target_max_events_per_minute,
        max_tool_calls_per_minute=delta.target_max_tool_calls_per_minute,
        expected_capabilities=apply(base.expected_capabilities, delta.add_capabilities, delta.remove_capabilities),
        alert_threshold=delta.target_alert_threshold,
        hold_threshold=delta.target_hold_threshold,
        deny_threshold=delta.target_deny_threshold,
    )
    if fingerprint(target) != delta.target_fingerprint:
        raise ValueError("target fingerprint mismatch")
    return target


def findings_digest(findings: Iterable[AnomalyFinding]) -> str:
    return fingerprint(tuple(findings))


def default_baseline(now: int = 1_800_000_000) -> BehaviorBaseline:
    return BehaviorBaseline(
        baseline_id="NOEPIN-AL-041-DEFAULT",
        version="1",
        authority_epoch=1,
        issued_at=now - 3600,
        expires_at=now + 86400,
        allowed_tools=frozenset({"NONE", "LOCAL_ANALYZER", "LOCAL_TEST"}),
        allowed_operations=frozenset({"OBSERVE", "ANALYZE", "VERIFY"}),
        allowed_tool_operation_pairs=frozenset({
            "NONE|OBSERVE", "LOCAL_ANALYZER|ANALYZE", "LOCAL_TEST|VERIFY"
        }),
        allowed_resource_classes=frozenset({"INTERNAL_METADATA", "TEST_ARTIFACT"}),
        allowed_hours_utc=frozenset(range(24)),
        max_events_per_minute=120.0,
        max_tool_calls_per_minute=60.0,
        expected_capabilities=frozenset({"READ_METADATA", "LOCAL_EVAL"}),
    )
