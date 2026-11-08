"""NOEPIN AL 047 — Risk Budget / Safety Budget Manager.

Pure control-plane evaluator that tracks caller-supplied risk/impact observations
against a versioned budget policy. It returns an execution-control candidate only.
It never grants permission, executes or stops an action, commits state, or treats a
risk score / remaining budget as truth or authority.

Creator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support using ChatGPT
License / Rights: NOT SPECIFIED
"""
from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Any, FrozenSet, Iterable, Mapping, Tuple


class ControlDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    HOLD = "HOLD"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"


@dataclass(frozen=True)
class RiskBudgetPolicy:
    policy_id: str
    version: str
    authority_epoch: int
    issued_at: int
    expires_at: int
    max_total_risk_units: int
    warning_risk_units: int
    max_total_impact_units: int
    warning_impact_units: int
    max_single_risk_units: int
    max_action_count: int
    high_risk_threshold: int
    max_consecutive_high_risk: int
    allowed_operations: FrozenSet[str]
    allowed_scopes: FrozenSet[str]
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
        if self.max_total_risk_units <= 0 or self.max_total_impact_units <= 0:
            raise ValueError("budgets must be positive")
        if not 0 <= self.warning_risk_units < self.max_total_risk_units:
            raise ValueError("invalid risk warning threshold")
        if not 0 <= self.warning_impact_units < self.max_total_impact_units:
            raise ValueError("invalid impact warning threshold")
        if not 0 <= self.max_single_risk_units <= self.max_total_risk_units:
            raise ValueError("invalid single risk limit")
        if self.max_action_count < 1 or self.max_consecutive_high_risk < 1:
            raise ValueError("invalid count limits")
        if not 0 <= self.high_risk_threshold <= self.max_single_risk_units:
            raise ValueError("invalid high-risk threshold")
        if not self.allowed_operations or not self.allowed_scopes:
            raise ValueError("allowed operations/scopes required")


@dataclass(frozen=True)
class RiskLedgerEntry:
    entry_id: str
    task_id: str
    operation: str
    scope: str
    risk_units: int
    impact_units: int
    occurred_at: int
    expires_at: int
    revoked: bool
    policy_id: str
    policy_version: str
    authority_epoch: int
    evidence_binding: str

    def validate(self) -> None:
        if not self.entry_id or not self.task_id or not self.operation or not self.scope:
            raise ValueError("entry/task/operation/scope required")
        if not 0 <= self.risk_units <= 1000 or not 0 <= self.impact_units <= 1000:
            raise ValueError("invalid ledger risk/impact")
        if self.occurred_at < 0 or self.expires_at <= self.occurred_at:
            raise ValueError("invalid entry lifetime")
        if not self.policy_id or not self.policy_version or self.authority_epoch < 1:
            raise ValueError("entry policy binding required")
        if not self.evidence_binding:
            raise ValueError("entry evidence binding required")


@dataclass(frozen=True)
class RiskBudgetRequest:
    request_id: str
    task_id: str
    candidate_id: str
    operation: str
    scope: str
    candidate_risk_units: int
    candidate_impact_units: int
    evidence_binding: str
    expected_policy_id: str
    expected_policy_version: str
    expected_authority_epoch: int

    def validate(self) -> None:
        if not self.request_id or not self.task_id or not self.candidate_id:
            raise ValueError("request/task/candidate required")
        if not self.operation or not self.scope or not self.evidence_binding:
            raise ValueError("operation/scope/binding required")
        if not 0 <= self.candidate_risk_units <= 1000 or not 0 <= self.candidate_impact_units <= 1000:
            raise ValueError("invalid candidate risk/impact")
        if not self.expected_policy_id or not self.expected_policy_version or self.expected_authority_epoch < 1:
            raise ValueError("expected policy binding required")


@dataclass(frozen=True)
class PreparedBudgetRegistry:
    registry_fingerprint: str
    policy_fingerprint: str
    entries: Tuple[RiskLedgerEntry, ...]
    item_fingerprints: Mapping[str, str]
    task_index: Mapping[str, Tuple[str, ...]]


@dataclass(frozen=True)
class BudgetRegistryDelta:
    base_fingerprint: str
    target_fingerprint: str
    changed: Tuple[RiskLedgerEntry, ...]
    removed_ids: Tuple[str, ...]
    added: Tuple[RiskLedgerEntry, ...]


@dataclass(frozen=True)
class RegistrySyncPlan:
    missing_or_changed_ids: Tuple[str, ...]
    metadata_bytes_required: int
    full_metadata_bytes: int
    full_resend_required: bool
    permission_granted: bool = False
    action_execution_authorized: bool = False
    stop_execution_authorized: bool = False


@dataclass(frozen=True)
class BudgetAssessment:
    decision: ControlDecision
    reasons: Tuple[str, ...]
    request_id: str
    task_id: str
    active_entry_ids: Tuple[str, ...]
    ignored_entry_ids: Tuple[str, ...]
    used_risk_units: int
    projected_risk_units: int
    remaining_risk_units: int
    used_impact_units: int
    projected_impact_units: int
    remaining_impact_units: int
    active_action_count: int
    projected_action_count: int
    consecutive_high_risk_count: int
    budget_warning_candidate: bool
    budget_exhausted_candidate: bool
    stop_candidate: bool
    registry_fingerprint: str
    policy_fingerprint: str
    request_fingerprint: str
    permission_granted: bool = False
    action_executed: bool = False
    stop_executed: bool = False
    commit_performed: bool = False
    action_success: bool = False
    risk_truth_proven: bool = False


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


def _normalize_entries(entries: Iterable[RiskLedgerEntry]) -> Tuple[RiskLedgerEntry, ...]:
    ordered = tuple(sorted(entries, key=lambda x: x.entry_id))
    ids = [e.entry_id for e in ordered]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate entry_id")
    for e in ordered:
        e.validate()
    return ordered


def registry_fingerprint(entries: Iterable[RiskLedgerEntry]) -> str:
    return fingerprint(_normalize_entries(entries))


def prepare_registry(policy: RiskBudgetPolicy, entries: Iterable[RiskLedgerEntry], *, now: int) -> PreparedBudgetRegistry:
    policy.validate(now)
    if policy.revoked:
        raise ValueError("policy revoked")
    normalized = _normalize_entries(entries)
    item_fps = {e.entry_id: fingerprint(e) for e in normalized}
    idx: dict[str, list[str]] = {}
    for e in normalized:
        idx.setdefault(e.task_id, []).append(e.entry_id)
    return PreparedBudgetRegistry(
        registry_fingerprint=fingerprint(normalized),
        policy_fingerprint=fingerprint(policy),
        entries=normalized,
        item_fingerprints=item_fps,
        task_index={k: tuple(sorted(v)) for k, v in sorted(idx.items())},
    )


def _empty_assessment(request: RiskBudgetRequest, policy: RiskBudgetPolicy, registry_fp: str,
                      decision: ControlDecision, reasons: Iterable[str]) -> BudgetAssessment:
    return BudgetAssessment(
        decision=decision,
        reasons=tuple(sorted(set(reasons))),
        request_id=request.request_id,
        task_id=request.task_id,
        active_entry_ids=(),
        ignored_entry_ids=(),
        used_risk_units=0,
        projected_risk_units=request.candidate_risk_units,
        remaining_risk_units=max(0, policy.max_total_risk_units-request.candidate_risk_units),
        used_impact_units=0,
        projected_impact_units=request.candidate_impact_units,
        remaining_impact_units=max(0, policy.max_total_impact_units-request.candidate_impact_units),
        active_action_count=0,
        projected_action_count=1,
        consecutive_high_risk_count=0,
        budget_warning_candidate=False,
        budget_exhausted_candidate=False,
        stop_candidate=False,
        registry_fingerprint=registry_fp,
        policy_fingerprint=fingerprint(policy),
        request_fingerprint=fingerprint(request),
    )


def evaluate_prepared(request: RiskBudgetRequest, policy: RiskBudgetPolicy, prepared: PreparedBudgetRegistry, *, now: int) -> BudgetAssessment:
    try:
        request.validate()
        policy.validate(now)
    except (ValueError, TypeError) as exc:
        return _empty_assessment(request, policy, prepared.registry_fingerprint, ControlDecision.HOLD, (f"INVALID_REQUEST_OR_POLICY:{exc}",))

    if policy.revoked:
        return _empty_assessment(request, policy, prepared.registry_fingerprint, ControlDecision.HOLD, ("POLICY_REVOKED",))
    if prepared.policy_fingerprint != fingerprint(policy):
        return _empty_assessment(request, policy, prepared.registry_fingerprint, ControlDecision.HOLD, ("PREPARED_POLICY_FINGERPRINT_MISMATCH",))
    if request.expected_policy_id != policy.policy_id:
        return _empty_assessment(request, policy, prepared.registry_fingerprint, ControlDecision.HOLD, ("POLICY_ID_MISMATCH",))
    if request.expected_policy_version != policy.version:
        return _empty_assessment(request, policy, prepared.registry_fingerprint, ControlDecision.HOLD, ("POLICY_VERSION_MISMATCH",))
    if request.expected_authority_epoch != policy.authority_epoch:
        return _empty_assessment(request, policy, prepared.registry_fingerprint, ControlDecision.HOLD, ("AUTHORITY_EPOCH_MISMATCH",))
    if request.operation not in policy.allowed_operations:
        return _empty_assessment(request, policy, prepared.registry_fingerprint, ControlDecision.DENY, ("OPERATION_NOT_ALLOWED",))
    if request.scope not in policy.allowed_scopes:
        return _empty_assessment(request, policy, prepared.registry_fingerprint, ControlDecision.DENY, ("SCOPE_NOT_ALLOWED",))

    by_id = {e.entry_id: e for e in prepared.entries}
    active: list[RiskLedgerEntry] = []
    ignored: list[str] = []
    for eid in prepared.task_index.get(request.task_id, ()):
        e = by_id[eid]
        valid = (
            not e.revoked
            and e.occurred_at <= now < e.expires_at
            and e.policy_id == policy.policy_id
            and e.policy_version == policy.version
            and e.authority_epoch == policy.authority_epoch
            and e.evidence_binding == request.evidence_binding
        )
        if valid:
            active.append(e)
        else:
            ignored.append(e.entry_id)

    active.sort(key=lambda e: (e.occurred_at, e.entry_id))
    used_risk = sum(e.risk_units for e in active)
    used_impact = sum(e.impact_units for e in active)
    projected_risk = used_risk + request.candidate_risk_units
    projected_impact = used_impact + request.candidate_impact_units
    projected_count = len(active) + 1

    consecutive = 0
    for e in reversed(active):
        if e.risk_units >= policy.high_risk_threshold:
            consecutive += 1
        else:
            break
    projected_consecutive = consecutive + (1 if request.candidate_risk_units >= policy.high_risk_threshold else 0)

    reasons: list[str] = []
    exhausted = False
    if request.candidate_risk_units > policy.max_single_risk_units:
        exhausted = True; reasons.append("SINGLE_ACTION_RISK_LIMIT_EXCEEDED")
    if projected_risk > policy.max_total_risk_units:
        exhausted = True; reasons.append("TOTAL_RISK_BUDGET_EXCEEDED")
    if projected_impact > policy.max_total_impact_units:
        exhausted = True; reasons.append("TOTAL_IMPACT_BUDGET_EXCEEDED")
    if projected_count > policy.max_action_count:
        exhausted = True; reasons.append("ACTION_COUNT_BUDGET_EXCEEDED")
    if projected_consecutive > policy.max_consecutive_high_risk:
        exhausted = True; reasons.append("CONSECUTIVE_HIGH_RISK_LIMIT_EXCEEDED")

    warning = (
        projected_risk >= policy.warning_risk_units
        or projected_impact >= policy.warning_impact_units
        or projected_count >= max(1, policy.max_action_count - 1)
        or projected_consecutive >= policy.max_consecutive_high_risk
    )

    if exhausted:
        decision = ControlDecision.DENY
        reasons.append("BUDGET_EXHAUSTED_CANDIDATE")
    elif warning:
        decision = ControlDecision.HUMAN_APPROVAL
        reasons.append("BUDGET_WARNING_CANDIDATE")
    else:
        decision = ControlDecision.ALLOW
        reasons.append("WITHIN_BUDGET_CANDIDATE")

    return BudgetAssessment(
        decision=decision,
        reasons=tuple(sorted(set(reasons))),
        request_id=request.request_id,
        task_id=request.task_id,
        active_entry_ids=tuple(e.entry_id for e in active),
        ignored_entry_ids=tuple(sorted(ignored)),
        used_risk_units=used_risk,
        projected_risk_units=projected_risk,
        remaining_risk_units=max(0, policy.max_total_risk_units-projected_risk),
        used_impact_units=used_impact,
        projected_impact_units=projected_impact,
        remaining_impact_units=max(0, policy.max_total_impact_units-projected_impact),
        active_action_count=len(active),
        projected_action_count=projected_count,
        consecutive_high_risk_count=projected_consecutive,
        budget_warning_candidate=warning and not exhausted,
        budget_exhausted_candidate=exhausted,
        stop_candidate=exhausted,
        registry_fingerprint=prepared.registry_fingerprint,
        policy_fingerprint=fingerprint(policy),
        request_fingerprint=fingerprint(request),
    )


def evaluate(request: RiskBudgetRequest, policy: RiskBudgetPolicy, entries: Iterable[RiskLedgerEntry], *, now: int) -> BudgetAssessment:
    try:
        prepared = prepare_registry(policy, entries, now=now)
    except (ValueError, TypeError) as exc:
        # Preserve a deterministic failure surface without claiming execution authority.
        try:
            reg_fp = registry_fingerprint(entries)
        except Exception:
            reg_fp = fingerprint(("INVALID_REGISTRY",))
        return _empty_assessment(request, policy, reg_fp, ControlDecision.HOLD, (f"INVALID_REGISTRY:{exc}",))
    return evaluate_prepared(request, policy, prepared, now=now)


def build_registry_delta(base: Iterable[RiskLedgerEntry], target: Iterable[RiskLedgerEntry]) -> BudgetRegistryDelta:
    b = {e.entry_id: e for e in _normalize_entries(base)}
    t = {e.entry_id: e for e in _normalize_entries(target)}
    changed = tuple(t[k] for k in sorted(b.keys() & t.keys()) if fingerprint(b[k]) != fingerprint(t[k]))
    removed = tuple(sorted(b.keys() - t.keys()))
    added = tuple(t[k] for k in sorted(t.keys() - b.keys()))
    return BudgetRegistryDelta(
        base_fingerprint=fingerprint(tuple(b[k] for k in sorted(b))),
        target_fingerprint=fingerprint(tuple(t[k] for k in sorted(t))),
        changed=changed,
        removed_ids=removed,
        added=added,
    )


def apply_registry_delta(base: Iterable[RiskLedgerEntry], delta: BudgetRegistryDelta) -> Tuple[RiskLedgerEntry, ...]:
    normalized = _normalize_entries(base)
    if fingerprint(normalized) != delta.base_fingerprint:
        raise ValueError("base fingerprint mismatch")
    data = {e.entry_id: e for e in normalized}
    for eid in delta.removed_ids:
        data.pop(eid, None)
    for e in delta.changed:
        if e.entry_id not in data:
            raise ValueError("changed id missing from base")
        data[e.entry_id] = e
    for e in delta.added:
        if e.entry_id in data:
            raise ValueError("added id already exists")
        data[e.entry_id] = e
    out = tuple(data[k] for k in sorted(data))
    if fingerprint(out) != delta.target_fingerprint:
        raise ValueError("target fingerprint mismatch")
    return out


def plan_registry_sync(prepared: PreparedBudgetRegistry, remote_fingerprints: Mapping[str, str]) -> RegistrySyncPlan:
    missing = tuple(sorted(k for k, fp in prepared.item_fingerprints.items() if remote_fingerprints.get(k) != fp))
    by_id = {e.entry_id: e for e in prepared.entries}
    metadata_bytes = len(canonical_json(tuple(by_id[k] for k in missing)).encode("utf-8"))
    full_bytes = len(canonical_json(prepared.entries).encode("utf-8"))
    return RegistrySyncPlan(
        missing_or_changed_ids=missing,
        metadata_bytes_required=metadata_bytes,
        full_metadata_bytes=full_bytes,
        full_resend_required=(metadata_bytes >= full_bytes if full_bytes else False),
    )


def registry_from_dict(policy: RiskBudgetPolicy, payload: Iterable[Mapping[str, Any]], *, now: int) -> PreparedBudgetRegistry:
    entries = tuple(RiskLedgerEntry(
        entry_id=str(x["entry_id"]), task_id=str(x["task_id"]), operation=str(x["operation"]), scope=str(x["scope"]),
        risk_units=int(x["risk_units"]), impact_units=int(x["impact_units"]), occurred_at=int(x["occurred_at"]),
        expires_at=int(x["expires_at"]), revoked=bool(x["revoked"]), policy_id=str(x["policy_id"]),
        policy_version=str(x["policy_version"]), authority_epoch=int(x["authority_epoch"]), evidence_binding=str(x["evidence_binding"])
    ) for x in payload)
    return prepare_registry(policy, entries, now=now)


def assessment_digest(results: Iterable[BudgetAssessment]) -> str:
    return fingerprint(tuple(results))


def default_policy(now: int) -> RiskBudgetPolicy:
    return RiskBudgetPolicy(
        policy_id="RISK-BUDGET-047", version="1", authority_epoch=1,
        issued_at=now-1000, expires_at=now+100000,
        max_total_risk_units=1000, warning_risk_units=800,
        max_total_impact_units=1200, warning_impact_units=950,
        max_single_risk_units=300, max_action_count=20,
        high_risk_threshold=200, max_consecutive_high_risk=2,
        allowed_operations=frozenset({"DRAFT","TRASH","PREVIEW","VERSIONED_WRITE","DRY_RUN","LOCAL_TEST","PUBLISH_CANDIDATE","DELETE_CANDIDATE"}),
        allowed_scopes=frozenset({"workspace","artifact","external_candidate","critical_system_candidate"}),
        revoked=False,
    )


def default_request(now: int) -> RiskBudgetRequest:
    p = default_policy(now)
    return RiskBudgetRequest(
        request_id="REQ-047", task_id="TASK-047", candidate_id="CANDIDATE-047",
        operation="LOCAL_TEST", scope="artifact", candidate_risk_units=80, candidate_impact_units=70,
        evidence_binding="BIND-047", expected_policy_id=p.policy_id, expected_policy_version=p.version,
        expected_authority_epoch=p.authority_epoch,
    )


def default_entries(now: int) -> Tuple[RiskLedgerEntry, ...]:
    p = default_policy(now)
    return (
        RiskLedgerEntry("R1","TASK-047","LOCAL_TEST","artifact",100,80,now-300,now+10000,False,p.policy_id,p.version,p.authority_epoch,"BIND-047"),
        RiskLedgerEntry("R2","TASK-047","DRAFT","workspace",120,100,now-200,now+10000,False,p.policy_id,p.version,p.authority_epoch,"BIND-047"),
        RiskLedgerEntry("R3","TASK-047","PREVIEW","external_candidate",90,120,now-100,now+10000,False,p.policy_id,p.version,p.authority_epoch,"BIND-047"),
    )
