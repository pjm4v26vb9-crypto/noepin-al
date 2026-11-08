"""NOEPIN AL 061 — Logical Execution Interlock — Sequential Successor V3.

Creator / Project Owner / Original Concept / Architecture Direction:
    NOEPIN / のえぴん
Implementation / analysis / documentation support:
    AI-assisted using ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-061
System Origin GUID: eafb14c1-1d19-5376-86c0-de9aedeff5e1

Pure control-plane evaluator. This module NEVER grants permission, issues/consumes
permits, executes actions, commits state, sends data, elevates privilege, or claims
truth/safety/action success. DCSR materialization is metadata reconstruction only.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass, replace
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping, Sequence

CREATOR = "NOEPIN / のえぴん"
AI_SUPPORT = "AI-assisted implementation / analysis / documentation support using ChatGPT"
LICENSE_RIGHTS = "NOT SPECIFIED"
CANONICAL_ID = "NOEPIN-AL-061"
SYSTEM_ORIGIN_GUID = "eafb14c1-1d19-5376-86c0-de9aedeff5e1"


class InterlockDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    HOLD = "HOLD"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"


def _plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {k: _plain(v) for k, v in asdict(value).items()}
    if isinstance(value, Mapping):
        return {str(k): _plain(v) for k, v in sorted(value.items(), key=lambda x: str(x[0]))}
    if isinstance(value, (tuple, list)):
        return [_plain(v) for v in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(_plain(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class InterlockPolicy:
    policy_id: str
    version: str
    authority_epoch: str
    valid_from: int
    expires_at: int
    allowed_actions: tuple[str, ...]
    allowed_target_prefixes: tuple[str, ...]
    allowed_scope_fingerprints: tuple[str, ...]
    allowed_source_trust: tuple[str, ...]
    max_request_age_seconds: int
    min_semantic_confidence: float
    require_counterfactual: bool
    replay_protection: bool
    deny_sensitive_external: bool
    deny_privilege_elevation: bool
    hold_when_safer_alternative: bool
    human_approval_for_irreversible: bool
    human_approval_for_external_side_effect: bool
    approval_role: str
    max_approval_age_seconds: int


@dataclass(frozen=True)
class ExecutionRequest:
    request_id: str
    task_id: str
    action: str
    target: str
    user_goal_fingerprint: str
    scope_fingerprint: str
    parameters_fingerprint: str
    expected_policy_id: str
    expected_policy_version: str
    expected_authority_epoch: str
    evidence_binding: str
    source_trust: str
    auth_verified: bool
    external_side_effect: bool
    irreversible: bool
    sensitive_data: bool
    privilege_elevation: bool
    explicit_authorization: bool
    safer_alternative_available: bool
    counterfactual_available: bool
    semantic_confidence: float
    created_at: int
    expires_at: int


@dataclass(frozen=True)
class ApprovalEvidence:
    approval_id: str
    request_id: str
    role: str
    approved: bool
    verified: bool
    independent: bool
    observed_at: int
    expires_at: int
    evidence_binding: str
    revoked: bool = False


@dataclass(frozen=True)
class PermitReceipt:
    permit_id: str
    request_id: str
    request_fingerprint: str
    consumed: bool
    verified: bool
    observed_at: int
    evidence_binding: str
    revoked: bool = False


@dataclass(frozen=True)
class PreparedInterlockRegistry:
    registry_fingerprint: str
    policy_fingerprint: str
    approvals: tuple[ApprovalEvidence, ...]
    receipts: tuple[PermitReceipt, ...]
    approval_fingerprints: tuple[tuple[str, str], ...]
    receipt_fingerprints: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class InterlockRegistryDelta:
    base_fingerprint: str
    target_fingerprint: str
    changed_approvals: tuple[ApprovalEvidence, ...]
    removed_approval_ids: tuple[str, ...]
    added_approvals: tuple[ApprovalEvidence, ...]
    changed_receipts: tuple[PermitReceipt, ...]
    removed_receipt_ids: tuple[str, ...]
    added_receipts: tuple[PermitReceipt, ...]


@dataclass(frozen=True)
class RegistrySyncPlan:
    target_fingerprint: str
    missing_or_changed_approval_ids: tuple[str, ...]
    missing_or_changed_receipt_ids: tuple[str, ...]
    metadata_bytes_required: int
    full_bytes: int
    full_resend_required: bool
    permission_granted: bool = False
    permit_issued: bool = False
    permit_consumed: bool = False
    action_execution_authorized: bool = False
    commit_authorized: bool = False
    action_success_authorized: bool = False


@dataclass(frozen=True)
class InterlockAssessment:
    decision: InterlockDecision
    reasons: tuple[str, ...]
    request_fingerprint: str
    policy_fingerprint: str
    registry_fingerprint: str
    permit_candidate: bool
    permit_candidate_id: str | None
    permit_validation_candidate: bool
    human_approval_required: bool
    hard_deny_hit: bool
    replay_detected: bool
    safer_alternative_detected: bool
    counterfactual_checked: bool
    permission_granted: bool = False
    permit_issued: bool = False
    permit_consumed: bool = False
    action_executed: bool = False
    commit_performed: bool = False
    external_effect_performed: bool = False
    privilege_elevated: bool = False
    data_sent: bool = False
    world_truth_proven: bool = False
    safety_proven: bool = False
    action_success: bool = False


def policy_fingerprint(policy: InterlockPolicy) -> str:
    return fingerprint(policy)


def request_fingerprint(request: ExecutionRequest) -> str:
    return fingerprint(request)


def registry_fingerprint(approvals: Sequence[ApprovalEvidence], receipts: Sequence[PermitReceipt]) -> str:
    return fingerprint({"approvals": tuple(approvals), "receipts": tuple(receipts)})


def _id_map(items: Sequence[Any], attr: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for item in items:
        key = getattr(item, attr, None)
        if not isinstance(key, str) or not key:
            raise ValueError(f"INVALID_ID:{attr}")
        if key in out:
            raise ValueError(f"DUPLICATE_ID:{key}")
        out[key] = item
    return out


def _valid_policy(policy: InterlockPolicy, now: int) -> str | None:
    if not all(isinstance(x, str) and x for x in (policy.policy_id, policy.version, policy.authority_epoch)):
        return "INVALID_POLICY_IDENTITY"
    if policy.valid_from > now or policy.expires_at <= now or policy.expires_at <= policy.valid_from:
        return "POLICY_NOT_CURRENT"
    if policy.max_request_age_seconds <= 0 or policy.max_approval_age_seconds <= 0:
        return "INVALID_POLICY_WINDOW"
    if not 0.0 <= policy.min_semantic_confidence <= 1.0:
        return "INVALID_CONFIDENCE_POLICY"
    if not policy.allowed_actions or not policy.allowed_target_prefixes or not policy.allowed_scope_fingerprints:
        return "INVALID_POLICY_ALLOWLIST"
    return None


def _valid_request(request: ExecutionRequest, now: int) -> str | None:
    required = (
        request.request_id, request.task_id, request.action, request.target,
        request.user_goal_fingerprint, request.scope_fingerprint, request.parameters_fingerprint,
        request.expected_policy_id, request.expected_policy_version, request.expected_authority_epoch,
        request.evidence_binding, request.source_trust,
    )
    if not all(isinstance(x, str) and x for x in required):
        return "INVALID_REQUEST_FIELDS"
    if not 0.0 <= request.semantic_confidence <= 1.0:
        return "INVALID_SEMANTIC_CONFIDENCE"
    if request.created_at > now or request.expires_at <= now or request.expires_at <= request.created_at:
        return "REQUEST_NOT_CURRENT"
    return None


def _approval_valid(a: ApprovalEvidence, request: ExecutionRequest, policy: InterlockPolicy, now: int) -> bool:
    return (
        a.request_id == request.request_id
        and a.role == policy.approval_role
        and a.approved
        and a.verified
        and a.independent
        and not a.revoked
        and a.evidence_binding == request.evidence_binding
        and a.observed_at <= now < a.expires_at
        and now - a.observed_at <= policy.max_approval_age_seconds
    )


def _permit_candidate_id(request: ExecutionRequest, policy: InterlockPolicy) -> str:
    return "PC-" + sha256((request_fingerprint(request) + policy_fingerprint(policy)).encode("ascii")).hexdigest()[:32]


def prepare_registry(
    policy: InterlockPolicy,
    approvals: Sequence[ApprovalEvidence],
    receipts: Sequence[PermitReceipt],
    *,
    now: int,
) -> PreparedInterlockRegistry:
    p_err = _valid_policy(policy, now)
    if p_err:
        raise ValueError(p_err)
    _id_map(approvals, "approval_id")
    _id_map(receipts, "permit_id")
    a_sorted = tuple(sorted(approvals, key=lambda x: x.approval_id))
    r_sorted = tuple(sorted(receipts, key=lambda x: x.permit_id))
    return PreparedInterlockRegistry(
        registry_fingerprint(a_sorted, r_sorted),
        policy_fingerprint(policy),
        a_sorted,
        r_sorted,
        tuple((x.approval_id, fingerprint(x)) for x in a_sorted),
        tuple((x.permit_id, fingerprint(x)) for x in r_sorted),
    )


def _assessment(
    decision: InterlockDecision,
    reasons: Iterable[str],
    request: ExecutionRequest,
    policy: InterlockPolicy,
    reg_fp: str,
    *,
    permit_candidate: bool = False,
    permit_candidate_id: str | None = None,
    permit_validation_candidate: bool = False,
    human_approval_required: bool = False,
    hard_deny_hit: bool = False,
    replay_detected: bool = False,
    safer_alternative_detected: bool = False,
    counterfactual_checked: bool = False,
) -> InterlockAssessment:
    return InterlockAssessment(
        decision=decision,
        reasons=tuple(reasons),
        request_fingerprint=request_fingerprint(request),
        policy_fingerprint=policy_fingerprint(policy),
        registry_fingerprint=reg_fp,
        permit_candidate=permit_candidate,
        permit_candidate_id=permit_candidate_id,
        permit_validation_candidate=permit_validation_candidate,
        human_approval_required=human_approval_required,
        hard_deny_hit=hard_deny_hit,
        replay_detected=replay_detected,
        safer_alternative_detected=safer_alternative_detected,
        counterfactual_checked=counterfactual_checked,
    )


def evaluate_prepared(
    request: ExecutionRequest,
    policy: InterlockPolicy,
    prepared: PreparedInterlockRegistry,
    *,
    now: int,
) -> InterlockAssessment:
    p_err = _valid_policy(policy, now)
    r_err = _valid_request(request, now)
    reg_now_fp = registry_fingerprint(prepared.approvals, prepared.receipts)
    if p_err:
        return _assessment(InterlockDecision.HOLD, (p_err,), request, policy, reg_now_fp)
    if r_err:
        return _assessment(InterlockDecision.HOLD, (r_err,), request, policy, reg_now_fp)
    if prepared.registry_fingerprint != reg_now_fp:
        return _assessment(InterlockDecision.HOLD, ("PREPARED_REGISTRY_FINGERPRINT_MISMATCH",), request, policy, reg_now_fp)
    if prepared.policy_fingerprint != policy_fingerprint(policy):
        return _assessment(InterlockDecision.HOLD, ("PREPARED_POLICY_FINGERPRINT_MISMATCH",), request, policy, reg_now_fp)
    try:
        _id_map(prepared.approvals, "approval_id"); _id_map(prepared.receipts, "permit_id")
    except ValueError as e:
        return _assessment(InterlockDecision.HOLD, (f"INVALID_REGISTRY:{e}",), request, policy, reg_now_fp)

    if request.expected_policy_id != policy.policy_id:
        return _assessment(InterlockDecision.HOLD, ("POLICY_ID_MISMATCH",), request, policy, reg_now_fp)
    if request.expected_policy_version != policy.version:
        return _assessment(InterlockDecision.HOLD, ("POLICY_VERSION_MISMATCH",), request, policy, reg_now_fp)
    if request.expected_authority_epoch != policy.authority_epoch:
        return _assessment(InterlockDecision.HOLD, ("AUTHORITY_EPOCH_MISMATCH",), request, policy, reg_now_fp)
    if now - request.created_at > policy.max_request_age_seconds:
        return _assessment(InterlockDecision.HOLD, ("REQUEST_STALE",), request, policy, reg_now_fp)
    if not request.auth_verified:
        return _assessment(InterlockDecision.HOLD, ("AUTHENTICATION_UNVERIFIED",), request, policy, reg_now_fp)
    if request.source_trust not in policy.allowed_source_trust:
        return _assessment(InterlockDecision.HOLD, ("SOURCE_TRUST_NOT_ALLOWED",), request, policy, reg_now_fp)
    if request.action not in policy.allowed_actions:
        return _assessment(InterlockDecision.DENY, ("ACTION_NOT_ALLOWED",), request, policy, reg_now_fp, hard_deny_hit=True)
    if not any(request.target.startswith(prefix) for prefix in policy.allowed_target_prefixes):
        return _assessment(InterlockDecision.DENY, ("TARGET_OUT_OF_SCOPE",), request, policy, reg_now_fp, hard_deny_hit=True)
    if request.scope_fingerprint not in policy.allowed_scope_fingerprints:
        return _assessment(InterlockDecision.DENY, ("SCOPE_MISMATCH",), request, policy, reg_now_fp, hard_deny_hit=True)
    if policy.deny_privilege_elevation and request.privilege_elevation:
        return _assessment(InterlockDecision.DENY, ("PRIVILEGE_ELEVATION_HARD_DENY",), request, policy, reg_now_fp, hard_deny_hit=True)
    if policy.deny_sensitive_external and request.sensitive_data and request.external_side_effect:
        return _assessment(InterlockDecision.DENY, ("SENSITIVE_EXTERNAL_TRANSFER_HARD_DENY",), request, policy, reg_now_fp, hard_deny_hit=True)
    if policy.require_counterfactual and not request.counterfactual_available:
        return _assessment(InterlockDecision.HOLD, ("COUNTERFACTUAL_UNAVAILABLE",), request, policy, reg_now_fp)
    if request.semantic_confidence < policy.min_semantic_confidence:
        return _assessment(InterlockDecision.HOLD, ("SEMANTIC_CONFIDENCE_BELOW_THRESHOLD",), request, policy, reg_now_fp, counterfactual_checked=request.counterfactual_available)
    if policy.hold_when_safer_alternative and request.irreversible and request.safer_alternative_available:
        return _assessment(InterlockDecision.HOLD, ("SAFER_ALTERNATIVE_AVAILABLE",), request, policy, reg_now_fp, safer_alternative_detected=True, counterfactual_checked=request.counterfactual_available)

    pcid = _permit_candidate_id(request, policy)
    if policy.replay_protection:
        for receipt in prepared.receipts:
            if receipt.permit_id == pcid or (receipt.request_id == request.request_id and receipt.request_fingerprint == request_fingerprint(request)):
                if receipt.verified and not receipt.revoked and receipt.evidence_binding == request.evidence_binding and receipt.consumed:
                    return _assessment(InterlockDecision.DENY, ("PERMIT_REPLAY_DETECTED",), request, policy, reg_now_fp, hard_deny_hit=True, replay_detected=True, counterfactual_checked=request.counterfactual_available)
                if not receipt.verified or receipt.revoked or receipt.evidence_binding != request.evidence_binding:
                    return _assessment(InterlockDecision.HOLD, ("PERMIT_RECEIPT_INVALID",), request, policy, reg_now_fp, counterfactual_checked=request.counterfactual_available)

    approval_required = (
        (policy.human_approval_for_irreversible and request.irreversible)
        or (policy.human_approval_for_external_side_effect and request.external_side_effect)
    )
    if approval_required:
        valid = [a for a in prepared.approvals if _approval_valid(a, request, policy, now)]
        if not request.explicit_authorization or not valid:
            return _assessment(InterlockDecision.HUMAN_APPROVAL, ("HUMAN_APPROVAL_REQUIRED",), request, policy, reg_now_fp, human_approval_required=True, counterfactual_checked=request.counterfactual_available)

    return _assessment(
        InterlockDecision.ALLOW,
        ("INTERLOCK_ALLOW_CANDIDATE_ONLY",),
        request,
        policy,
        reg_now_fp,
        permit_candidate=True,
        permit_candidate_id=pcid,
        permit_validation_candidate=True,
        counterfactual_checked=request.counterfactual_available,
    )


def evaluate(
    request: ExecutionRequest,
    policy: InterlockPolicy,
    approvals: Sequence[ApprovalEvidence],
    receipts: Sequence[PermitReceipt],
    *,
    now: int,
) -> InterlockAssessment:
    try:
        prepared = prepare_registry(policy, approvals, receipts, now=now)
    except ValueError as e:
        # Preserve deterministic metadata even when registry preparation fails.
        reg_fp = registry_fingerprint(tuple(approvals), tuple(receipts))
        return _assessment(InterlockDecision.HOLD, (f"INVALID_REGISTRY:{e}",), request, policy, reg_fp)
    return evaluate_prepared(request, policy, prepared, now=now)


def make_registry_delta(
    base_approvals: Sequence[ApprovalEvidence],
    base_receipts: Sequence[PermitReceipt],
    target_approvals: Sequence[ApprovalEvidence],
    target_receipts: Sequence[PermitReceipt],
) -> InterlockRegistryDelta:
    ba = _id_map(base_approvals, "approval_id"); br = _id_map(base_receipts, "permit_id")
    ta = _id_map(target_approvals, "approval_id"); tr = _id_map(target_receipts, "permit_id")
    changed_a = tuple(ta[k] for k in sorted(set(ba) & set(ta)) if fingerprint(ba[k]) != fingerprint(ta[k]))
    changed_r = tuple(tr[k] for k in sorted(set(br) & set(tr)) if fingerprint(br[k]) != fingerprint(tr[k]))
    removed_a = tuple(sorted(set(ba) - set(ta))); removed_r = tuple(sorted(set(br) - set(tr)))
    added_a = tuple(ta[k] for k in sorted(set(ta) - set(ba))); added_r = tuple(tr[k] for k in sorted(set(tr) - set(br)))
    return InterlockRegistryDelta(
        registry_fingerprint(base_approvals, base_receipts),
        registry_fingerprint(target_approvals, target_receipts),
        changed_a, removed_a, added_a, changed_r, removed_r, added_r,
    )


def apply_registry_delta(
    base_approvals: Sequence[ApprovalEvidence],
    base_receipts: Sequence[PermitReceipt],
    delta: InterlockRegistryDelta,
) -> tuple[tuple[ApprovalEvidence, ...], tuple[PermitReceipt, ...]]:
    if registry_fingerprint(base_approvals, base_receipts) != delta.base_fingerprint:
        raise ValueError("DELTA_WRONG_BASE")
    a = _id_map(base_approvals, "approval_id"); r = _id_map(base_receipts, "permit_id")
    for key in delta.removed_approval_ids: a.pop(key, None)
    for key in delta.removed_receipt_ids: r.pop(key, None)
    for item in delta.changed_approvals:
        if item.approval_id not in a: raise ValueError("DELTA_CHANGED_APPROVAL_MISSING_BASE")
        a[item.approval_id] = item
    for item in delta.changed_receipts:
        if item.permit_id not in r: raise ValueError("DELTA_CHANGED_RECEIPT_MISSING_BASE")
        r[item.permit_id] = item
    for item in delta.added_approvals:
        if item.approval_id in a: raise ValueError("DELTA_ADDED_APPROVAL_COLLISION")
        a[item.approval_id] = item
    for item in delta.added_receipts:
        if item.permit_id in r: raise ValueError("DELTA_ADDED_RECEIPT_COLLISION")
        r[item.permit_id] = item
    aa = tuple(a[k] for k in sorted(a)); rr = tuple(r[k] for k in sorted(r))
    if registry_fingerprint(aa, rr) != delta.target_fingerprint:
        raise ValueError("DELTA_TARGET_FINGERPRINT_MISMATCH")
    return aa, rr


def plan_registry_sync(
    approvals: Sequence[ApprovalEvidence],
    receipts: Sequence[PermitReceipt],
    remote_approval_fingerprints: Mapping[str, str] | Sequence[tuple[str, str]],
    remote_receipt_fingerprints: Mapping[str, str] | Sequence[tuple[str, str]],
) -> RegistrySyncPlan:
    local_a = {x.approval_id: fingerprint(x) for x in approvals}
    local_r = {x.permit_id: fingerprint(x) for x in receipts}
    remote_a = dict(remote_approval_fingerprints); remote_r = dict(remote_receipt_fingerprints)
    missing_a = tuple(sorted(k for k, v in local_a.items() if remote_a.get(k) != v))
    missing_r = tuple(sorted(k for k, v in local_r.items() if remote_r.get(k) != v))
    amap = _id_map(approvals, "approval_id"); rmap = _id_map(receipts, "permit_id")
    payload = {"approvals": tuple(amap[k] for k in missing_a), "receipts": tuple(rmap[k] for k in missing_r)}
    full_payload = {"approvals": tuple(approvals), "receipts": tuple(receipts)}
    meta = len(canonical_json(payload).encode("utf-8")); full = len(canonical_json(full_payload).encode("utf-8"))
    return RegistrySyncPlan(
        registry_fingerprint(approvals, receipts), missing_a, missing_r, meta, full,
        bool(full and meta / full >= 0.80),
    )


def default_policy(now: int) -> InterlockPolicy:
    return InterlockPolicy(
        policy_id="POL-061", version="3.0.0", authority_epoch="AE-061-A",
        valid_from=now-3600, expires_at=now+86400,
        allowed_actions=("READ", "ANALYZE", "WRITE_CANDIDATE"),
        allowed_target_prefixes=("workspace:/safe/",),
        allowed_scope_fingerprints=("SCOPE-061",),
        allowed_source_trust=("TRUSTED", "INTERNAL"),
        max_request_age_seconds=600, min_semantic_confidence=0.80,
        require_counterfactual=True, replay_protection=True,
        deny_sensitive_external=True, deny_privilege_elevation=True,
        hold_when_safer_alternative=True,
        human_approval_for_irreversible=True,
        human_approval_for_external_side_effect=True,
        approval_role="OWNER", max_approval_age_seconds=600,
    )


def default_request(now: int) -> ExecutionRequest:
    return ExecutionRequest(
        request_id="REQ-061-A", task_id="TASK-061", action="ANALYZE",
        target="workspace:/safe/report", user_goal_fingerprint="GOAL-061",
        scope_fingerprint="SCOPE-061", parameters_fingerprint="PARAM-061",
        expected_policy_id="POL-061", expected_policy_version="3.0.0",
        expected_authority_epoch="AE-061-A", evidence_binding="BIND-061",
        source_trust="TRUSTED", auth_verified=True,
        external_side_effect=False, irreversible=False, sensitive_data=False,
        privilege_elevation=False, explicit_authorization=False,
        safer_alternative_available=False, counterfactual_available=True,
        semantic_confidence=0.95, created_at=now-10, expires_at=now+300,
    )


def default_approvals(now: int) -> tuple[ApprovalEvidence, ...]:
    return ()


def default_receipts(now: int) -> tuple[PermitReceipt, ...]:
    return ()
