"""NOEPIN AL 081 — Postcondition Auditor — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Deterministic, fail-safe postcondition auditor. Success is derived from independently
supplied observed state and before/after diff evidence, never from an AI/action
self-report. The module does not execute rollback, publish state, grant permission,
write to an environment, or promote an execution receipt to truth.

Canonical identity: NOEPIN-AL-081
Provenance note: exact registered Origin GUID was not freshly reverified in this
completion session and is intentionally not guessed or regenerated.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Sequence


class Decision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    HOLD = "HOLD"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PredicateOperator(str, Enum):
    EQ = "EQ"
    NE = "NE"
    EXISTS = "EXISTS"
    ABSENT = "ABSENT"


class SuccessState(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ExpectedPostcondition:
    condition_id: str
    path: str
    operator: PredicateOperator
    expected_value: str | None
    required: bool
    severity: Severity
    binding: str
    state_epoch: str


@dataclass(frozen=True)
class StateFact:
    path: str
    value: str | None
    exists: bool
    observed: bool
    source_id: str
    binding: str
    state_epoch: str


@dataclass(frozen=True)
class DiffEffect:
    effect_id: str
    path: str
    before_value: str | None
    after_value: str | None
    observed: bool
    expected_change: bool
    severity: Severity
    binding: str
    state_epoch: str


@dataclass(frozen=True)
class AuditRequest:
    request_id: str
    intent_id: str
    permit_id: str
    condition_ids: tuple[str, ...]
    allowed_effect_paths: tuple[str, ...]
    diff_complete: bool
    binding: str
    state_epoch: str


@dataclass(frozen=True)
class IntentEvidence:
    intent_id: str
    declared_scope_paths: tuple[str, ...]
    observed: bool
    binding: str
    state_epoch: str


@dataclass(frozen=True)
class PermitEvidence:
    permit_id: str
    allowed_paths: tuple[str, ...]
    valid: bool
    revocation_checked: bool
    observed: bool
    binding: str
    state_epoch: str


@dataclass(frozen=True)
class ExecutionReceipt:
    request_id: str
    claimed_success: bool
    observed: bool
    binding: str
    state_epoch: str


@dataclass(frozen=True)
class AuditPolicy:
    binding: str
    state_epoch: str
    critical_unexpected_denies: bool = True
    required_unmet_denies: bool = True
    unexpected_effects_fail_success: bool = True
    revoked: bool = False


@dataclass(frozen=True)
class AuditResult:
    decision: Decision
    success_state: SuccessState
    reasons: tuple[str, ...]
    unmet_conditions: tuple[str, ...]
    unexpected_effects: tuple[str, ...]
    observed_required: int
    required_total: int
    coverage: float
    next_gate_candidate: bool
    rollback_candidate: bool
    atomic_publish_candidate: bool
    permission_granted: bool = False
    rollback_executed: bool = False
    state_committed: bool = False
    external_write_performed: bool = False
    action_executed: bool = False
    receipt_promoted_to_truth: bool = False
    world_truth_proven: bool = False
    safety_proven: bool = False
    action_success: bool = False


@dataclass(frozen=True)
class PreparedPostconditionState:
    policy: AuditPolicy
    request: AuditRequest
    intent: IntentEvidence
    permit: PermitEvidence
    receipt: ExecutionReceipt
    conditions: tuple[ExpectedPostcondition, ...]
    observed_state: tuple[StateFact, ...]
    diff: tuple[DiffEffect, ...]
    condition_fingerprints: tuple[tuple[str, str], ...]
    state_fingerprints: tuple[tuple[str, str], ...]
    effect_fingerprints: tuple[tuple[str, str], ...]
    policy_fingerprint: str
    request_fingerprint: str
    intent_fingerprint: str
    permit_fingerprint: str
    receipt_fingerprint: str
    registry_fingerprint: str
    condition_index: tuple[tuple[str, ExpectedPostcondition], ...]
    state_index: tuple[tuple[str, StateFact], ...]
    binding: str
    state_epoch: str


@dataclass(frozen=True)
class PostconditionStateDelta:
    base_fingerprint: str
    target_fingerprint: str
    changed_conditions: tuple[ExpectedPostcondition, ...]
    removed_condition_ids: tuple[str, ...]
    changed_state: tuple[StateFact, ...]
    removed_state_paths: tuple[str, ...]
    changed_effects: tuple[DiffEffect, ...]
    removed_effect_ids: tuple[str, ...]
    target_policy: AuditPolicy
    target_request: AuditRequest
    target_intent: IntentEvidence
    target_permit: PermitEvidence
    target_receipt: ExecutionReceipt
    binding: str
    state_epoch: str


@dataclass(frozen=True)
class PostconditionSyncPlan:
    missing_or_changed_conditions: tuple[str, ...]
    missing_or_changed_state_paths: tuple[str, ...]
    missing_or_changed_effect_ids: tuple[str, ...]
    metadata_bytes_required: int
    full_resend_required: bool


def _canon(value) -> bytes:
    def cv(x):
        if isinstance(x, Enum):
            return x.value
        if hasattr(x, "__dataclass_fields__"):
            return {k: cv(getattr(x, k)) for k in x.__dataclass_fields__}
        if isinstance(x, tuple):
            return [cv(i) for i in x]
        if isinstance(x, list):
            return [cv(i) for i in x]
        if isinstance(x, dict):
            return {str(k): cv(x[k]) for k in sorted(x)}
        if isinstance(x, float):
            return round(x, 12)
        return x

    return json.dumps(cv(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def _fp(value) -> str:
    return sha256(_canon(value)).hexdigest()


def _idx(items, key: str):
    return tuple(sorted(((getattr(x, key), x) for x in items), key=lambda z: z[0]))


def _lookup(index, key):
    lo, hi = 0, len(index)
    while lo < hi:
        mid = (lo + hi) // 2
        if index[mid][0] < key:
            lo = mid + 1
        else:
            hi = mid
    return index[lo][1] if lo < len(index) and index[lo][0] == key else None


def _unique(items, attr: str) -> bool:
    vals = [getattr(x, attr) for x in items]
    return len(vals) == len(set(vals))


def _registry_fp(policy, request, intent, permit, receipt, conditions, observed_state, diff) -> str:
    return _fp(
        {
            "policy": _fp(policy),
            "request": _fp(request),
            "intent": _fp(intent),
            "permit": _fp(permit),
            "receipt": _fp(receipt),
            "conditions": sorted((x.condition_id, _fp(x)) for x in conditions),
            "state": sorted((x.path, _fp(x)) for x in observed_state),
            "diff": sorted((x.effect_id, _fp(x)) for x in diff),
        }
    )


def default_policy() -> AuditPolicy:
    return AuditPolicy("POST-BIND", "STATE-EPOCH-1")


def default_request() -> AuditRequest:
    return AuditRequest(
        "REQ-081-1",
        "INTENT-081-1",
        "PERMIT-081-1",
        ("C-ARTIFACT", "C-HASH", "C-STATUS"),
        ("artifact.json", "artifact.sha256", "status"),
        True,
        "POST-BIND",
        "STATE-EPOCH-1",
    )


def default_intent() -> IntentEvidence:
    return IntentEvidence(
        "INTENT-081-1",
        ("artifact.json", "artifact.sha256", "status"),
        True,
        "POST-BIND",
        "STATE-EPOCH-1",
    )


def default_permit() -> PermitEvidence:
    return PermitEvidence(
        "PERMIT-081-1",
        ("artifact.json", "artifact.sha256", "status"),
        True,
        True,
        True,
        "POST-BIND",
        "STATE-EPOCH-1",
    )


def default_receipt() -> ExecutionReceipt:
    return ExecutionReceipt("REQ-081-1", True, True, "POST-BIND", "STATE-EPOCH-1")


def default_conditions() -> tuple[ExpectedPostcondition, ...]:
    b, e = "POST-BIND", "STATE-EPOCH-1"
    return (
        ExpectedPostcondition("C-ARTIFACT", "artifact.json", PredicateOperator.EXISTS, None, True, Severity.HIGH, b, e),
        ExpectedPostcondition("C-HASH", "artifact.sha256", PredicateOperator.EQ, "abc123", True, Severity.HIGH, b, e),
        ExpectedPostcondition("C-STATUS", "status", PredicateOperator.EQ, "VERIFIED", True, Severity.MEDIUM, b, e),
    )


def default_observed_state() -> tuple[StateFact, ...]:
    b, e = "POST-BIND", "STATE-EPOCH-1"
    return (
        StateFact("artifact.json", "present", True, True, "READ-ADAPTER-1", b, e),
        StateFact("artifact.sha256", "abc123", True, True, "READ-ADAPTER-1", b, e),
        StateFact("status", "VERIFIED", True, True, "READ-ADAPTER-1", b, e),
    )


def default_diff() -> tuple[DiffEffect, ...]:
    b, e = "POST-BIND", "STATE-EPOCH-1"
    return (
        DiffEffect("D-ARTIFACT", "artifact.json", None, "present", True, True, Severity.LOW, b, e),
        DiffEffect("D-HASH", "artifact.sha256", None, "abc123", True, True, Severity.LOW, b, e),
        DiffEffect("D-STATUS", "status", "PENDING", "VERIFIED", True, True, Severity.LOW, b, e),
    )


def _hold(reason: str, required_total: int = 0, observed_required: int = 0, unmet=(), unexpected=(), rollback=False) -> AuditResult:
    coverage = 0.0 if required_total == 0 else observed_required / required_total
    return AuditResult(
        Decision.HOLD,
        SuccessState.UNKNOWN,
        (reason,),
        tuple(unmet),
        tuple(unexpected),
        observed_required,
        required_total,
        round(coverage, 12),
        False,
        rollback,
        False,
    )


def _condition_met(condition: ExpectedPostcondition, fact: StateFact) -> bool:
    op = condition.operator
    if op == PredicateOperator.EXISTS:
        return fact.exists
    if op == PredicateOperator.ABSENT:
        return not fact.exists
    if not fact.exists:
        return False
    if op == PredicateOperator.EQ:
        return fact.value == condition.expected_value
    if op == PredicateOperator.NE:
        return fact.value != condition.expected_value
    return False


def _binding_ok(obj, policy: AuditPolicy) -> bool:
    return getattr(obj, "binding", None) == policy.binding and getattr(obj, "state_epoch", None) == policy.state_epoch


def _evaluate(
    request: AuditRequest,
    intent: IntentEvidence,
    permit: PermitEvidence,
    receipt: ExecutionReceipt,
    policy: AuditPolicy,
    conditions: Sequence[ExpectedPostcondition],
    observed_state: Sequence[StateFact],
    diff: Sequence[DiffEffect],
    *,
    condition_index=None,
    state_index=None,
) -> AuditResult:
    if not all(
        isinstance(x, t)
        for x, t in (
            (request, AuditRequest),
            (intent, IntentEvidence),
            (permit, PermitEvidence),
            (receipt, ExecutionReceipt),
            (policy, AuditPolicy),
        )
    ):
        return _hold("INVALID_TYPED_INPUT")
    if policy.revoked:
        return _hold("AUDIT_POLICY_REVOKED")
    for obj, label in (
        (request, "REQUEST"),
        (intent, "INTENT"),
        (permit, "PERMIT"),
        (receipt, "RECEIPT"),
    ):
        if not _binding_ok(obj, policy):
            return _hold(f"{label}_BINDING_OR_EPOCH_MISMATCH")
    if request.intent_id != intent.intent_id:
        return _hold("INTENT_ID_MISMATCH")
    if request.permit_id != permit.permit_id:
        return _hold("PERMIT_ID_MISMATCH")
    if request.request_id != receipt.request_id:
        return _hold("RECEIPT_REQUEST_ID_MISMATCH")
    if not intent.observed:
        return _hold("INTENT_CONTEXT_UNOBSERVED")
    if not permit.observed or not permit.revocation_checked or not permit.valid:
        return _hold("PERMIT_EVIDENCE_NOT_CURRENT_OR_VALID")
    allowed = set(request.allowed_effect_paths)
    if len(request.allowed_effect_paths) != len(allowed):
        return _hold("DUPLICATE_ALLOWED_EFFECT_PATH")
    if not allowed.issubset(set(permit.allowed_paths)):
        return _hold("REQUEST_SCOPE_EXCEEDS_PERMIT_EVIDENCE")
    if not allowed.issubset(set(intent.declared_scope_paths)):
        return _hold("REQUEST_SCOPE_EXCEEDS_DECLARED_INTENT")
    if not request.diff_complete:
        return _hold("BEFORE_AFTER_DIFF_INCOMPLETE")
    if not _unique(conditions, "condition_id"):
        return _hold("DUPLICATE_CONDITION_ID")
    if not _unique(observed_state, "path"):
        return _hold("DUPLICATE_STATE_PATH")
    if not _unique(diff, "effect_id"):
        return _hold("DUPLICATE_EFFECT_ID")
    if len(request.condition_ids) != len(set(request.condition_ids)):
        return _hold("DUPLICATE_REQUEST_CONDITION")
    if not request.condition_ids:
        return _hold("NO_POSTCONDITIONS_REQUESTED")

    ci = condition_index if condition_index is not None else _idx(conditions, "condition_id")
    si = state_index if state_index is not None else _idx(observed_state, "path")
    selected = []
    for cid in request.condition_ids:
        c = _lookup(ci, cid)
        if c is None:
            return _hold("CONDITION_UNKNOWN")
        if not _binding_ok(c, policy):
            return _hold("CONDITION_BINDING_OR_EPOCH_MISMATCH")
        selected.append(c)

    required_total = sum(1 for c in selected if c.required)
    if required_total == 0:
        return _hold("NO_REQUIRED_POSTCONDITIONS")

    observed_required = 0
    unmet = []
    unknown_required = []
    for c in selected:
        fact = _lookup(si, c.path)
        if fact is None or not fact.observed:
            if c.required:
                unknown_required.append(c.condition_id)
            continue
        if not _binding_ok(fact, policy):
            return _hold("STATE_BINDING_OR_EPOCH_MISMATCH", required_total, observed_required)
        if c.required:
            observed_required += 1
        if not _condition_met(c, fact) and c.required:
            unmet.append(c.condition_id)

    unexpected = []
    critical_unexpected = []
    unobserved_effects = []
    for effect in diff:
        if not _binding_ok(effect, policy):
            return _hold("DIFF_BINDING_OR_EPOCH_MISMATCH", required_total, observed_required, unmet, unexpected)
        if not effect.observed:
            unobserved_effects.append(effect.effect_id)
            continue
        expected = effect.expected_change and effect.path in allowed
        if not expected:
            unexpected.append(effect.effect_id)
            if effect.severity == Severity.CRITICAL:
                critical_unexpected.append(effect.effect_id)

    unexpected = sorted(set(unexpected))
    unmet = sorted(set(unmet))
    unknown_required = sorted(set(unknown_required))
    coverage = round(observed_required / required_total, 12)

    if unknown_required:
        return _hold(
            "REQUIRED_POSTCONDITION_UNOBSERVED",
            required_total,
            observed_required,
            unmet,
            unexpected,
            rollback=bool(critical_unexpected),
        )
    if unobserved_effects:
        return _hold(
            "DIFF_EFFECT_UNOBSERVED",
            required_total,
            observed_required,
            unmet,
            unexpected,
            rollback=bool(critical_unexpected),
        )
    if unmet and policy.required_unmet_denies:
        reasons = ["REQUIRED_POSTCONDITION_UNMET"]
        if receipt.observed and receipt.claimed_success:
            reasons.append("SUCCESS_RECEIPT_CONTRADICTED_BY_OBSERVATION")
        return AuditResult(
            Decision.DENY,
            SuccessState.FAILURE,
            tuple(reasons),
            tuple(unmet),
            tuple(unexpected),
            observed_required,
            required_total,
            coverage,
            False,
            bool(critical_unexpected),
            False,
        )
    if critical_unexpected and policy.critical_unexpected_denies:
        return AuditResult(
            Decision.DENY,
            SuccessState.FAILURE,
            ("CRITICAL_UNEXPECTED_EFFECT",),
            tuple(unmet),
            tuple(unexpected),
            observed_required,
            required_total,
            coverage,
            False,
            True,
            False,
        )
    if unexpected and policy.unexpected_effects_fail_success:
        return AuditResult(
            Decision.HOLD,
            SuccessState.UNKNOWN,
            ("UNEXPECTED_EFFECT_REQUIRES_REVIEW",),
            tuple(unmet),
            tuple(unexpected),
            observed_required,
            required_total,
            coverage,
            False,
            False,
            False,
        )

    reasons = ["ALL_REQUIRED_POSTCONDITIONS_OBSERVED_AND_MET", "NO_UNEXPECTED_EFFECTS_OBSERVED"]
    if receipt.observed and not receipt.claimed_success:
        reasons.append("RECEIPT_FAILURE_CLAIM_NOT_PROMOTED_OVER_OBSERVED_STATE")
    elif not receipt.observed:
        reasons.append("RECEIPT_UNOBSERVED_NOT_USED_AS_SUCCESS_AUTHORITY")
    return AuditResult(
        Decision.ALLOW,
        SuccessState.SUCCESS,
        tuple(reasons),
        (),
        (),
        observed_required,
        required_total,
        coverage,
        True,
        False,
        True,
    )


def evaluate(
    request: AuditRequest,
    intent: IntentEvidence,
    permit: PermitEvidence,
    receipt: ExecutionReceipt,
    policy: AuditPolicy,
    conditions: Sequence[ExpectedPostcondition],
    observed_state: Sequence[StateFact],
    diff: Sequence[DiffEffect],
) -> AuditResult:
    return _evaluate(request, intent, permit, receipt, policy, conditions, observed_state, diff)


def prepare_state(
    policy: AuditPolicy,
    request: AuditRequest,
    intent: IntentEvidence,
    permit: PermitEvidence,
    receipt: ExecutionReceipt,
    conditions: Sequence[ExpectedPostcondition],
    observed_state: Sequence[StateFact],
    diff: Sequence[DiffEffect],
    *,
    binding: str,
) -> PreparedPostconditionState:
    c = tuple(sorted(conditions, key=lambda x: x.condition_id))
    s = tuple(sorted(observed_state, key=lambda x: x.path))
    d = tuple(sorted(diff, key=lambda x: x.effect_id))
    return PreparedPostconditionState(
        policy,
        request,
        intent,
        permit,
        receipt,
        c,
        s,
        d,
        tuple((x.condition_id, _fp(x)) for x in c),
        tuple((x.path, _fp(x)) for x in s),
        tuple((x.effect_id, _fp(x)) for x in d),
        _fp(policy),
        _fp(request),
        _fp(intent),
        _fp(permit),
        _fp(receipt),
        _registry_fp(policy, request, intent, permit, receipt, c, s, d),
        _idx(c, "condition_id"),
        _idx(s, "path"),
        binding,
        policy.state_epoch,
    )


def validate_prepared_integrity(state: PreparedPostconditionState) -> bool:
    if not isinstance(state, PreparedPostconditionState):
        return False
    if state.binding != state.policy.binding or state.state_epoch != state.policy.state_epoch:
        return False
    if state.policy_fingerprint != _fp(state.policy):
        return False
    if state.request_fingerprint != _fp(state.request) or state.intent_fingerprint != _fp(state.intent):
        return False
    if state.permit_fingerprint != _fp(state.permit) or state.receipt_fingerprint != _fp(state.receipt):
        return False
    if state.condition_fingerprints != tuple((x.condition_id, _fp(x)) for x in state.conditions):
        return False
    if state.state_fingerprints != tuple((x.path, _fp(x)) for x in state.observed_state):
        return False
    if state.effect_fingerprints != tuple((x.effect_id, _fp(x)) for x in state.diff):
        return False
    if state.condition_index != _idx(state.conditions, "condition_id"):
        return False
    if state.state_index != _idx(state.observed_state, "path"):
        return False
    return state.registry_fingerprint == _registry_fp(
        state.policy,
        state.request,
        state.intent,
        state.permit,
        state.receipt,
        state.conditions,
        state.observed_state,
        state.diff,
    )


def evaluate_prepared(
    state: PreparedPostconditionState,
    *,
    current_policy_fingerprint: str,
    current_request_fingerprint: str,
    current_registry_fingerprint: str,
    prepared_integrity_validated: bool,
) -> AuditResult:
    if not isinstance(state, PreparedPostconditionState):
        return _hold("INVALID_PREPARED_STATE")
    required_total = sum(1 for x in state.conditions if x.required and x.condition_id in set(state.request.condition_ids))
    if not prepared_integrity_validated:
        return _hold("PREPARED_STATE_INTEGRITY_NOT_VALIDATED", required_total)
    if current_policy_fingerprint != state.policy_fingerprint:
        return _hold("PREPARED_POLICY_STALE", required_total)
    if current_request_fingerprint != state.request_fingerprint:
        return _hold("PREPARED_REQUEST_STALE", required_total)
    if current_registry_fingerprint != state.registry_fingerprint:
        return _hold("PREPARED_REGISTRY_STALE", required_total)
    return _evaluate(
        state.request,
        state.intent,
        state.permit,
        state.receipt,
        state.policy,
        state.conditions,
        state.observed_state,
        state.diff,
        condition_index=state.condition_index,
        state_index=state.state_index,
    )


def make_delta(base: PreparedPostconditionState, target: PreparedPostconditionState) -> PostconditionStateDelta:
    if base.binding != target.binding or base.state_epoch != target.state_epoch:
        raise ValueError("binding/state epoch mismatch")
    bc, tc = dict(base.condition_fingerprints), dict(target.condition_fingerprints)
    bs, ts = dict(base.state_fingerprints), dict(target.state_fingerprints)
    be, te = dict(base.effect_fingerprints), dict(target.effect_fingerprints)
    changed_c = tuple(x for x in target.conditions if bc.get(x.condition_id) != tc[x.condition_id])
    changed_s = tuple(x for x in target.observed_state if bs.get(x.path) != ts[x.path])
    changed_e = tuple(x for x in target.diff if be.get(x.effect_id) != te[x.effect_id])
    return PostconditionStateDelta(
        base.registry_fingerprint,
        target.registry_fingerprint,
        changed_c,
        tuple(sorted(set(bc) - set(tc))),
        changed_s,
        tuple(sorted(set(bs) - set(ts))),
        changed_e,
        tuple(sorted(set(be) - set(te))),
        target.policy,
        target.request,
        target.intent,
        target.permit,
        target.receipt,
        target.binding,
        target.state_epoch,
    )


def apply_delta(base: PreparedPostconditionState, delta: PostconditionStateDelta) -> PreparedPostconditionState:
    if base.registry_fingerprint != delta.base_fingerprint:
        raise ValueError("delta base fingerprint mismatch")
    if base.binding != delta.binding or base.state_epoch != delta.state_epoch:
        raise ValueError("delta binding/state epoch mismatch")
    c = {x.condition_id: x for x in base.conditions}
    s = {x.path: x for x in base.observed_state}
    e = {x.effect_id: x for x in base.diff}
    for k in delta.removed_condition_ids:
        c.pop(k, None)
    for k in delta.removed_state_paths:
        s.pop(k, None)
    for k in delta.removed_effect_ids:
        e.pop(k, None)
    for x in delta.changed_conditions:
        c[x.condition_id] = x
    for x in delta.changed_state:
        s[x.path] = x
    for x in delta.changed_effects:
        e[x.effect_id] = x
    out = prepare_state(
        delta.target_policy,
        delta.target_request,
        delta.target_intent,
        delta.target_permit,
        delta.target_receipt,
        tuple(c.values()),
        tuple(s.values()),
        tuple(e.values()),
        binding=delta.binding,
    )
    if out.registry_fingerprint != delta.target_fingerprint:
        raise ValueError("delta target fingerprint mismatch")
    return out


def missing_only_sync_plan(
    target: PreparedPostconditionState,
    known_conditions: dict[str, str],
    known_state: dict[str, str],
    known_effects: dict[str, str],
) -> PostconditionSyncPlan:
    mc = tuple(k for k, fp in target.condition_fingerprints if known_conditions.get(k) != fp)
    ms = tuple(k for k, fp in target.state_fingerprints if known_state.get(k) != fp)
    me = tuple(k for k, fp in target.effect_fingerprints if known_effects.get(k) != fp)
    ci = {x.condition_id: x for x in target.conditions}
    si = {x.path: x for x in target.observed_state}
    ei = {x.effect_id: x for x in target.diff}
    nbytes = sum(len(_canon(ci[k])) for k in mc) + sum(len(_canon(si[k])) for k in ms) + sum(len(_canon(ei[k])) for k in me)
    return PostconditionSyncPlan(mc, ms, me, nbytes, False)


def full_registry_bytes(state: PreparedPostconditionState) -> int:
    return len(
        _canon(
            {
                "policy": state.policy,
                "request": state.request,
                "intent": state.intent,
                "permit": state.permit,
                "receipt": state.receipt,
                "conditions": state.conditions,
                "state": state.observed_state,
                "diff": state.diff,
            }
        )
    )


def delta_bytes(delta: PostconditionStateDelta) -> int:
    return len(_canon(delta))
