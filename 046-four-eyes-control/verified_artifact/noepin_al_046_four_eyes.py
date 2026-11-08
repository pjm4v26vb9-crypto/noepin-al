"""NOEPIN AL 046 — Four-Eyes / Dual Approval Control.

Pure control-plane evaluator for high-risk operations. It validates independent,
current, policy-bound approval evidence and returns a control decision candidate.
It never grants permission, executes an action, commits state, sends funds/data,
or treats approval evidence as truth.

Creator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support using ChatGPT
License / Rights: NOT SPECIFIED
"""
from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Any, FrozenSet, Iterable, Mapping, Optional, Tuple


class ControlDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    HOLD = "HOLD"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"


class ActorKind(str, Enum):
    HUMAN = "HUMAN"
    AI = "AI"


@dataclass(frozen=True)
class ApprovalPolicy:
    policy_id: str
    version: str
    authority_epoch: int
    issued_at: int
    expires_at: int
    required_approvals: int
    required_human_approvals: int
    required_distinct_roles: int
    allowed_roles: FrozenSet[str]
    allowed_actions: FrozenSet[str]
    allowed_scopes: FrozenSet[str]
    allow_ai_approver: bool
    initiator_may_approve: bool
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
        if self.required_approvals < 2:
            raise ValueError("four-eyes requires at least two approvals")
        if not 0 <= self.required_human_approvals <= self.required_approvals:
            raise ValueError("invalid required_human_approvals")
        if not 1 <= self.required_distinct_roles <= self.required_approvals:
            raise ValueError("invalid required_distinct_roles")
        if not self.allowed_roles or not self.allowed_actions or not self.allowed_scopes:
            raise ValueError("allowed roles/actions/scopes required")


@dataclass(frozen=True)
class ApprovalEvidence:
    evidence_id: str
    actor_id: str
    actor_kind: ActorKind
    role: str
    action_id: str
    scope: str
    approved: bool
    issued_at: int
    expires_at: int
    revoked: bool
    policy_id: str
    policy_version: str
    authority_epoch: int
    evidence_binding: str

    def validate(self) -> None:
        if not self.evidence_id or not self.actor_id or not self.role:
            raise ValueError("evidence/actor/role required")
        if not self.action_id or not self.scope or not self.evidence_binding:
            raise ValueError("action/scope/binding required")
        if self.issued_at < 0 or self.expires_at <= self.issued_at:
            raise ValueError("invalid evidence lifetime")
        if not self.policy_id or not self.policy_version or self.authority_epoch < 1:
            raise ValueError("policy binding required")


@dataclass(frozen=True)
class FourEyesRequest:
    request_id: str
    action_id: str
    operation: str
    scope: str
    initiator_id: str
    risk_score: int
    evidence_binding: str
    expected_policy_id: str
    expected_policy_version: str
    expected_authority_epoch: int

    def validate(self) -> None:
        if not self.request_id or not self.action_id or not self.operation or not self.scope:
            raise ValueError("request/action/operation/scope required")
        if not self.initiator_id or not self.evidence_binding:
            raise ValueError("initiator/binding required")
        if not 0 <= self.risk_score <= 100:
            raise ValueError("invalid risk_score")
        if not self.expected_policy_id or not self.expected_policy_version or self.expected_authority_epoch < 1:
            raise ValueError("expected policy binding required")


@dataclass(frozen=True)
class PreparedApprovalRegistry:
    registry_fingerprint: str
    policy_fingerprint: str
    evidence: Tuple[ApprovalEvidence, ...]
    item_fingerprints: Mapping[str, str]
    action_index: Mapping[str, Tuple[str, ...]]


@dataclass(frozen=True)
class ApprovalRegistryDelta:
    base_fingerprint: str
    target_fingerprint: str
    changed: Tuple[ApprovalEvidence, ...]
    removed_ids: Tuple[str, ...]
    added: Tuple[ApprovalEvidence, ...]


@dataclass(frozen=True)
class RegistryTransferPlan:
    missing_or_changed_ids: Tuple[str, ...]
    metadata_bytes_required: int
    full_metadata_bytes: int
    full_resend_required: bool
    permission_granted: bool = False
    action_execution_authorized: bool = False


@dataclass(frozen=True)
class ApprovalAssessment:
    decision: ControlDecision
    reasons: Tuple[str, ...]
    request_id: str
    valid_approver_ids: Tuple[str, ...]
    valid_roles: Tuple[str, ...]
    rejected_evidence_ids: Tuple[str, ...]
    required_approvals: int
    required_human_approvals: int
    human_approval_count: int
    distinct_role_count: int
    approval_complete_candidate: bool
    registry_fingerprint: str
    policy_fingerprint: str
    request_fingerprint: str
    permission_granted: bool = False
    action_executed: bool = False
    commit_performed: bool = False
    action_success: bool = False
    approval_truth_proven: bool = False


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


def _normalize_evidence(evidence: Iterable[ApprovalEvidence]) -> Tuple[ApprovalEvidence, ...]:
    ordered = tuple(sorted(evidence, key=lambda x: x.evidence_id))
    ids = [e.evidence_id for e in ordered]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate evidence_id")
    for e in ordered:
        e.validate()
    return ordered


def registry_fingerprint(evidence: Iterable[ApprovalEvidence]) -> str:
    return fingerprint(_normalize_evidence(evidence))


def prepare_registry(policy: ApprovalPolicy, evidence: Iterable[ApprovalEvidence], *, now: int) -> PreparedApprovalRegistry:
    policy.validate(now)
    if policy.revoked:
        raise ValueError("policy revoked")
    normalized = _normalize_evidence(evidence)
    item_fps = {e.evidence_id: fingerprint(e) for e in normalized}
    idx: dict[str, list[str]] = {}
    for e in normalized:
        idx.setdefault(e.action_id, []).append(e.evidence_id)
    return PreparedApprovalRegistry(
        registry_fingerprint=fingerprint(normalized),
        policy_fingerprint=fingerprint(policy),
        evidence=normalized,
        item_fingerprints=item_fps,
        action_index={k: tuple(sorted(v)) for k, v in sorted(idx.items())},
    )


def _assessment(request: FourEyesRequest, policy: ApprovalPolicy, registry_fp: str, decision: ControlDecision,
                reasons: Iterable[str], valid: Iterable[ApprovalEvidence] = (), rejected: Iterable[str] = (),
                approval_complete_candidate: bool = False) -> ApprovalAssessment:
    v = tuple(sorted(valid, key=lambda x: x.actor_id))
    humans = sum(1 for e in v if e.actor_kind is ActorKind.HUMAN)
    roles = tuple(sorted({e.role for e in v}))
    return ApprovalAssessment(
        decision=decision,
        reasons=tuple(sorted(set(reasons))),
        request_id=request.request_id,
        valid_approver_ids=tuple(e.actor_id for e in v),
        valid_roles=roles,
        rejected_evidence_ids=tuple(sorted(set(rejected))),
        required_approvals=policy.required_approvals,
        required_human_approvals=policy.required_human_approvals,
        human_approval_count=humans,
        distinct_role_count=len(roles),
        approval_complete_candidate=approval_complete_candidate,
        registry_fingerprint=registry_fp,
        policy_fingerprint=fingerprint(policy),
        request_fingerprint=fingerprint(request),
    )


def evaluate_prepared(request: FourEyesRequest, policy: ApprovalPolicy, prepared: PreparedApprovalRegistry, *, now: int) -> ApprovalAssessment:
    try:
        request.validate()
        policy.validate(now)
    except (ValueError, TypeError) as exc:
        return _assessment(request, policy, prepared.registry_fingerprint, ControlDecision.HOLD, (f"INVALID_REQUEST_OR_POLICY:{exc}",))

    if policy.revoked:
        return _assessment(request, policy, prepared.registry_fingerprint, ControlDecision.HOLD, ("POLICY_REVOKED",))
    if fingerprint(policy) != prepared.policy_fingerprint:
        return _assessment(request, policy, prepared.registry_fingerprint, ControlDecision.HOLD, ("PREPARED_POLICY_FINGERPRINT_MISMATCH",))
    if request.expected_policy_id != policy.policy_id:
        return _assessment(request, policy, prepared.registry_fingerprint, ControlDecision.HOLD, ("POLICY_ID_MISMATCH",))
    if request.expected_policy_version != policy.version:
        return _assessment(request, policy, prepared.registry_fingerprint, ControlDecision.HOLD, ("POLICY_VERSION_MISMATCH",))
    if request.expected_authority_epoch != policy.authority_epoch:
        return _assessment(request, policy, prepared.registry_fingerprint, ControlDecision.HOLD, ("AUTHORITY_EPOCH_MISMATCH",))
    if request.operation not in policy.allowed_actions:
        return _assessment(request, policy, prepared.registry_fingerprint, ControlDecision.DENY, ("ACTION_NOT_ALLOWED",))
    if request.scope not in policy.allowed_scopes:
        return _assessment(request, policy, prepared.registry_fingerprint, ControlDecision.DENY, ("SCOPE_NOT_ALLOWED",))

    by_id = {e.evidence_id: e for e in prepared.evidence}
    candidate_ids = prepared.action_index.get(request.action_id, ())
    valid_by_actor: dict[str, ApprovalEvidence] = {}
    rejected: list[str] = []
    reasons: list[str] = []

    for eid in candidate_ids:
        e = by_id[eid]
        reject_reason: Optional[str] = None
        if e.policy_id != policy.policy_id or e.policy_version != policy.version or e.authority_epoch != policy.authority_epoch:
            reject_reason = "APPROVAL_POLICY_BINDING_MISMATCH"
        elif e.scope != request.scope or e.evidence_binding != request.evidence_binding:
            reject_reason = "APPROVAL_REQUEST_BINDING_MISMATCH"
        elif e.role not in policy.allowed_roles:
            reject_reason = "APPROVER_ROLE_NOT_ALLOWED"
        elif e.actor_kind is ActorKind.AI and not policy.allow_ai_approver:
            reject_reason = "AI_APPROVER_NOT_ALLOWED"
        elif e.revoked:
            reject_reason = "APPROVAL_REVOKED"
        elif not e.issued_at <= now < e.expires_at:
            reject_reason = "APPROVAL_EXPIRED_OR_NOT_YET_VALID"
        elif not policy.initiator_may_approve and e.actor_id == request.initiator_id:
            reject_reason = "INITIATOR_CANNOT_SELF_APPROVE"

        if reject_reason:
            rejected.append(e.evidence_id)
            reasons.append(reject_reason)
            continue

        # A current, correctly-bound explicit rejection is authoritative for this control decision.
        if not e.approved:
            rejected.append(e.evidence_id)
            return _assessment(
                request, policy, prepared.registry_fingerprint, ControlDecision.DENY,
                tuple(reasons) + ("EXPLICIT_REJECTION",), valid_by_actor.values(), rejected,
            )

        # Multiple evidence objects from the same actor count once.
        if e.actor_id in valid_by_actor:
            rejected.append(e.evidence_id)
            reasons.append("DUPLICATE_ACTOR_APPROVAL_IGNORED")
            continue
        valid_by_actor[e.actor_id] = e

    valid = tuple(valid_by_actor.values())
    human_count = sum(1 for e in valid if e.actor_kind is ActorKind.HUMAN)
    role_count = len({e.role for e in valid})
    complete = (
        len(valid) >= policy.required_approvals
        and human_count >= policy.required_human_approvals
        and role_count >= policy.required_distinct_roles
    )

    if complete:
        reasons.append("FOUR_EYES_REQUIREMENTS_MET_CANDIDATE")
        return _assessment(request, policy, prepared.registry_fingerprint, ControlDecision.ALLOW, reasons, valid, rejected, True)

    if len(valid) < policy.required_approvals:
        reasons.append("MORE_INDEPENDENT_APPROVALS_REQUIRED")
    if human_count < policy.required_human_approvals:
        reasons.append("MORE_HUMAN_APPROVALS_REQUIRED")
    if role_count < policy.required_distinct_roles:
        reasons.append("MORE_DISTINCT_ROLES_REQUIRED")
    return _assessment(request, policy, prepared.registry_fingerprint, ControlDecision.HUMAN_APPROVAL, reasons, valid, rejected, False)


def evaluate(request: FourEyesRequest, policy: ApprovalPolicy, evidence: Iterable[ApprovalEvidence], *, now: int) -> ApprovalAssessment:
    try:
        prepared = prepare_registry(policy, evidence, now=now)
    except (ValueError, TypeError) as exc:
        return _assessment(request, policy, "", ControlDecision.HOLD, (f"INVALID_REGISTRY_OR_POLICY:{exc}",))
    return evaluate_prepared(request, policy, prepared, now=now)


def build_registry_delta(base: Iterable[ApprovalEvidence], target: Iterable[ApprovalEvidence]) -> ApprovalRegistryDelta:
    b = _normalize_evidence(base)
    t = _normalize_evidence(target)
    bm = {x.evidence_id: x for x in b}
    tm = {x.evidence_id: x for x in t}
    changed = tuple(tm[k] for k in sorted(set(bm) & set(tm)) if fingerprint(bm[k]) != fingerprint(tm[k]))
    removed = tuple(sorted(set(bm) - set(tm)))
    added = tuple(tm[k] for k in sorted(set(tm) - set(bm)))
    return ApprovalRegistryDelta(fingerprint(b), fingerprint(t), changed, removed, added)


def apply_registry_delta(base: Iterable[ApprovalEvidence], delta: ApprovalRegistryDelta) -> Tuple[ApprovalEvidence, ...]:
    normalized = _normalize_evidence(base)
    if fingerprint(normalized) != delta.base_fingerprint:
        raise ValueError("base fingerprint mismatch")
    m = {x.evidence_id: x for x in normalized}
    for rid in delta.removed_ids:
        if rid not in m:
            raise ValueError("removed id missing from base")
        del m[rid]
    for e in delta.changed:
        if e.evidence_id not in m:
            raise ValueError("changed id missing from base")
        e.validate(); m[e.evidence_id] = e
    for e in delta.added:
        if e.evidence_id in m:
            raise ValueError("added id already exists")
        e.validate(); m[e.evidence_id] = e
    out = _normalize_evidence(m.values())
    if fingerprint(out) != delta.target_fingerprint:
        raise ValueError("target fingerprint mismatch")
    return out


def plan_registry_sync(prepared: PreparedApprovalRegistry, remote_known_item_fingerprints: Mapping[str, str]) -> RegistryTransferPlan:
    missing = tuple(sorted(k for k, fp in prepared.item_fingerprints.items() if remote_known_item_fingerprints.get(k) != fp))
    by_id = {e.evidence_id: e for e in prepared.evidence}
    metadata_bytes = sum(len(canonical_json(by_id[i]).encode("utf-8")) for i in missing)
    full_bytes = len(canonical_json(prepared.evidence).encode("utf-8"))
    return RegistryTransferPlan(
        missing_or_changed_ids=missing,
        metadata_bytes_required=metadata_bytes,
        full_metadata_bytes=full_bytes,
        full_resend_required=metadata_bytes >= full_bytes,
    )


def evidence_from_dict(d: Mapping[str, Any]) -> ApprovalEvidence:
    return ApprovalEvidence(
        evidence_id=str(d["evidence_id"]), actor_id=str(d["actor_id"]), actor_kind=ActorKind(str(d["actor_kind"])),
        role=str(d["role"]), action_id=str(d["action_id"]), scope=str(d["scope"]), approved=bool(d["approved"]),
        issued_at=int(d["issued_at"]), expires_at=int(d["expires_at"]), revoked=bool(d["revoked"]),
        policy_id=str(d["policy_id"]), policy_version=str(d["policy_version"]), authority_epoch=int(d["authority_epoch"]),
        evidence_binding=str(d["evidence_binding"]),
    )


def registry_from_dict(policy: ApprovalPolicy, payload: Iterable[Mapping[str, Any]], *, now: int) -> PreparedApprovalRegistry:
    return prepare_registry(policy, (evidence_from_dict(x) for x in payload), now=now)


def assessment_digest(values: Iterable[ApprovalAssessment]) -> str:
    return fingerprint(tuple(values))


def default_policy(now: int = 1_800_000_000) -> ApprovalPolicy:
    return ApprovalPolicy(
        policy_id="FOUR-EYES-V2", version="2", authority_epoch=1,
        issued_at=now-100, expires_at=now+100_000,
        required_approvals=2, required_human_approvals=1, required_distinct_roles=2,
        allowed_roles=frozenset({"OWNER", "REVIEWER", "SECURITY", "AI_CONTROL"}),
        allowed_actions=frozenset({"PUBLISH", "DELETE", "TRANSFER", "CRITICAL_CONFIG_CHANGE"}),
        allowed_scopes=frozenset({"workspace", "external_candidate", "critical_system"}),
        allow_ai_approver=True, initiator_may_approve=False,
    )


def default_request(now: int = 1_800_000_000) -> FourEyesRequest:
    p = default_policy(now)
    return FourEyesRequest(
        request_id="REQ-FOUR-EYES-DEFAULT", action_id="ACTION-001", operation="PUBLISH", scope="external_candidate",
        initiator_id="INITIATOR-1", risk_score=90, evidence_binding="BIND-ACTION-001",
        expected_policy_id=p.policy_id, expected_policy_version=p.version, expected_authority_epoch=p.authority_epoch,
    )


def default_evidence(now: int = 1_800_000_000) -> Tuple[ApprovalEvidence, ...]:
    p = default_policy(now); r = default_request(now)
    return (
        ApprovalEvidence("APP-HUMAN-1", "HUMAN-OWNER-1", ActorKind.HUMAN, "OWNER", r.action_id, r.scope, True,
                         now-20, now+1000, False, p.policy_id, p.version, p.authority_epoch, r.evidence_binding),
        ApprovalEvidence("APP-AI-1", "AI-CONTROL-1", ActorKind.AI, "AI_CONTROL", r.action_id, r.scope, True,
                         now-10, now+1000, False, p.policy_id, p.version, p.authority_epoch, r.evidence_binding),
    )
