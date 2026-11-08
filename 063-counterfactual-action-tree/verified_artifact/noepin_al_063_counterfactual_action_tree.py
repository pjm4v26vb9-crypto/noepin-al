"""NOEPIN AL 063 — Counterfactual Action Tree — Sequential Successor V2.

Creator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
Implementation / analysis / documentation support: AI-assisted using ChatGPT
License / Rights: NOT SPECIFIED

Pure algorithm/control-plane counterfactual evaluator. It never executes actions, grants
permission, establishes world truth, or claims action success.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, is_dataclass, replace
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence

CREATOR = "NOEPIN / のえぴん"
AI_SUPPORT = "AI-assisted implementation / analysis / documentation support using ChatGPT"
LICENSE_RIGHTS = "NOT SPECIFIED"
CANONICAL_ID = "NOEPIN-AL-063"


class Decision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    HOLD = "HOLD"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"


class BranchKind(str, Enum):
    DO = "DO"
    DO_NOT = "DO_NOT"
    SAFER_ALTERNATIVE = "SAFER_ALTERNATIVE"


@dataclass(frozen=True)
class EffectModel:
    model_id: str
    version: str
    binding: str
    verified: bool
    revoked: bool
    confidence: float
    valid_from: int
    expires_at: int
    policy_id: str
    policy_version: str
    authority_epoch: str


@dataclass(frozen=True)
class ActionCandidate:
    action_id: str
    label: str
    binding: str
    goal_alignment: float
    reversible: bool
    external_side_effect: bool
    sensitive_data: bool
    privilege_elevation: bool
    explicit_authorization: bool
    approval_required: bool
    expected_effect_model_id: str
    expected_effect_model_version: str


@dataclass(frozen=True)
class CounterfactualBranch:
    branch_id: str
    action_id: str
    parent_branch_id: str
    depth: int
    kind: BranchKind
    binding: str
    evaluable: bool
    verified: bool
    revoked: bool
    effect_model_id: str
    effect_model_version: str
    model_confidence: float
    goal_utility: float
    risk: float
    severe_loss: bool
    irreversible_effect: bool
    external_side_effect: bool
    hard_policy_violation: bool
    predicted_state_fingerprint: str
    safer_alternative_for: str = ""


@dataclass(frozen=True)
class ApprovalEvidence:
    approval_id: str
    action_id: str
    role: str
    binding: str
    verified: bool
    revoked: bool
    independent: bool
    decision: str
    valid_from: int
    expires_at: int
    policy_id: str
    policy_version: str
    authority_epoch: str


@dataclass(frozen=True)
class CounterfactualRequest:
    request_id: str
    requested_action_id: str
    current_state_fingerprint: str
    goal_id: str
    goal_binding: str
    graph_binding: str
    expected_policy_id: str
    expected_policy_version: str
    expected_authority_epoch: str
    expected_effect_model_id: str
    expected_effect_model_version: str
    created_at: int
    expires_at: int


@dataclass(frozen=True)
class CounterfactualPolicy:
    policy_id: str
    version: str
    authority_epoch: str
    valid_from: int
    expires_at: int
    revoked: bool
    min_effect_model_confidence: float
    min_branch_confidence: float
    max_risk_allow: float
    severe_loss_deny_threshold: float
    high_risk_approval_threshold: float
    min_goal_utility: float
    safer_alternative_utility_ratio: float
    safer_alternative_risk_delta: float
    max_depth: int
    max_branches: int
    max_request_age_seconds: int
    approval_role: str


@dataclass(frozen=True)
class PreparedTreeState:
    graph_binding: str
    effect_model_fingerprint: str
    policy_fingerprint: str
    registry_fingerprint: str
    action_fingerprints: tuple[tuple[str, str], ...]
    branch_fingerprints: tuple[tuple[str, str], ...]
    branch_index: tuple[tuple[str, tuple[str, ...]], ...]
    branches_by_id: tuple[tuple[str, CounterfactualBranch], ...]
    actions_by_id: tuple[tuple[str, ActionCandidate], ...]
    generated_at: int


@dataclass(frozen=True)
class TreeDelta:
    base_fingerprint: str
    target_fingerprint: str
    scalar_changes: tuple[tuple[str, Any], ...]
    changed_actions: tuple[ActionCandidate, ...]
    removed_action_ids: tuple[str, ...]
    added_actions: tuple[ActionCandidate, ...]
    changed_branches: tuple[CounterfactualBranch, ...]
    removed_branch_ids: tuple[str, ...]
    added_branches: tuple[CounterfactualBranch, ...]


@dataclass(frozen=True)
class TreeSyncPlan:
    registry_fingerprint: str
    missing_or_changed_action_ids: tuple[str, ...]
    missing_or_changed_branch_ids: tuple[str, ...]
    metadata_bytes_required: int
    full_bytes: int
    full_resend_required: bool
    permission_granted: bool = False
    action_execution_authorized: bool = False
    world_truth_authorized: bool = False
    action_success_authorized: bool = False


@dataclass(frozen=True)
class CounterfactualResult:
    decision: Decision
    reasons: tuple[str, ...]
    requested_action_id: str
    recommended_action_candidate: str
    safer_alternative_candidate: str
    evaluated_branch_ids: tuple[str, ...]
    pareto_branch_ids: tuple[str, ...]
    requested_action_max_risk: float
    requested_action_best_utility: float
    effect_model_confidence: float
    approval_required: bool
    next_gate_candidate: bool
    permission_granted: bool = False
    action_executed: bool = False
    action_selected_committed: bool = False
    approval_executed: bool = False
    prediction_truth_proven: bool = False
    world_fact_proven: bool = False
    safety_proven: bool = False
    action_success: bool = False


def _norm(v: Any) -> Any:
    if isinstance(v, Enum):
        return v.value
    if is_dataclass(v):
        return {k: _norm(x) for k, x in asdict(v).items()}
    if isinstance(v, dict):
        return {str(k): _norm(v[k]) for k in sorted(v, key=lambda x: str(x))}
    if isinstance(v, (tuple, list)):
        return [_norm(x) for x in v]
    if isinstance(v, (set, frozenset)):
        return [_norm(x) for x in sorted(v, key=lambda x: str(x))]
    return v


def canonical_json(v: Any) -> str:
    return json.dumps(_norm(v), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def fingerprint(v: Any) -> str:
    return sha256(canonical_json(v).encode("utf-8")).hexdigest()


def _registry_from_fps(
    graph_binding: str,
    policy_fingerprint: str,
    effect_model_fingerprint: str,
    action_fingerprints: Sequence[tuple[str, str]],
    branch_fingerprints: Sequence[tuple[str, str]],
) -> str:
    return fingerprint({
        "graph_binding": graph_binding,
        "policy_fingerprint": policy_fingerprint,
        "effect_model_fingerprint": effect_model_fingerprint,
        "action_fingerprints": tuple(sorted(action_fingerprints)),
        "branch_fingerprints": tuple(sorted(branch_fingerprints)),
    })

def _registry_fingerprint(
    policy: CounterfactualPolicy,
    actions: Sequence[ActionCandidate],
    branches: Sequence[CounterfactualBranch],
    effect_model: EffectModel,
    graph_binding: str,
) -> str:
    af=tuple(sorted((a.action_id,fingerprint(a)) for a in actions))
    bf=tuple(sorted((b.branch_id,fingerprint(b)) for b in branches))
    return _registry_from_fps(graph_binding,fingerprint(policy),fingerprint(effect_model),af,bf)


def _pareto(branches: Sequence[CounterfactualBranch]) -> tuple[str, ...]:
    eligible = [b for b in branches if b.evaluable and b.verified and not b.revoked and not b.hard_policy_violation]
    out: list[str] = []
    for b in eligible:
        dominated = False
        for o in eligible:
            if o.branch_id == b.branch_id:
                continue
            if o.goal_utility >= b.goal_utility and o.risk <= b.risk and (
                o.goal_utility > b.goal_utility or o.risk < b.risk
            ):
                dominated = True
                break
        if not dominated:
            out.append(b.branch_id)
    return tuple(sorted(out))


def prepare_tree(
    policy: CounterfactualPolicy,
    effect_model: EffectModel,
    actions: Sequence[ActionCandidate],
    branches: Sequence[CounterfactualBranch],
    *,
    graph_binding: str,
    now: int,
) -> PreparedTreeState:
    af = tuple(sorted((a.action_id, fingerprint(a)) for a in actions))
    bf = tuple(sorted((b.branch_id, fingerprint(b)) for b in branches))
    idx: dict[str, list[str]] = {a.action_id: [] for a in actions}
    for b in branches:
        idx.setdefault(b.action_id, []).append(b.branch_id)
    for k in idx:
        idx[k].sort()
    return PreparedTreeState(
        graph_binding=graph_binding,
        effect_model_fingerprint=fingerprint(effect_model),
        policy_fingerprint=fingerprint(policy),
        registry_fingerprint=_registry_from_fps(graph_binding, fingerprint(policy), fingerprint(effect_model), af, bf),
        action_fingerprints=af,
        branch_fingerprints=bf,
        branch_index=tuple(sorted((k, tuple(v)) for k, v in idx.items())),
        branches_by_id=tuple(sorted((b.branch_id, b) for b in branches)),
        actions_by_id=tuple(sorted((a.action_id, a) for a in actions)),
        generated_at=now,
    )


def validate_prepared_state(
    prepared: PreparedTreeState,
    policy: CounterfactualPolicy,
    effect_model: EffectModel,
    actions: Sequence[ActionCandidate],
    branches: Sequence[CounterfactualBranch],
    *,
    graph_binding: str,
) -> bool:
    """Explicit integrity verification for a newly received/materialized prepared state.

    Call once when accepting a prepared state. Evaluation itself still re-checks current
    policy/effect-model identity, validity, binding, branch evidence and authority epoch,
    but does not rebuild the entire registry fingerprint on every evaluation.
    """
    return (
        prepared.graph_binding == graph_binding
        and prepared.policy_fingerprint == fingerprint(policy)
        and prepared.effect_model_fingerprint == fingerprint(effect_model)
        and prepared.registry_fingerprint == _registry_fingerprint(policy, actions, branches, effect_model, graph_binding)
        and dict(prepared.action_fingerprints) == {a.action_id: fingerprint(a) for a in actions}
        and dict(prepared.branch_fingerprints) == {b.branch_id: fingerprint(b) for b in branches}
    )


def _hold(req: CounterfactualRequest, model: EffectModel, reason: str, *extra: str) -> CounterfactualResult:
    return CounterfactualResult(
        Decision.HOLD,
        (reason,) + tuple(extra),
        req.requested_action_id,
        "",
        "",
        (),
        (),
        0.0,
        0.0,
        model.confidence,
        False,
        False,
    )


def _deny(
    req: CounterfactualRequest,
    model: EffectModel,
    reason: str,
    evaluated: Sequence[str],
    max_risk: float,
    best_utility: float,
) -> CounterfactualResult:
    return CounterfactualResult(
        Decision.DENY,
        (reason,),
        req.requested_action_id,
        "",
        "",
        tuple(sorted(evaluated)),
        (),
        max_risk,
        best_utility,
        model.confidence,
        False,
        False,
    )


def _approval_valid(
    evidence: ApprovalEvidence | None,
    req: CounterfactualRequest,
    policy: CounterfactualPolicy,
    *,
    now: int,
) -> bool:
    if evidence is None:
        return False
    return (
        evidence.action_id == req.requested_action_id
        and evidence.role == policy.approval_role
        and evidence.binding == req.graph_binding
        and evidence.verified
        and not evidence.revoked
        and evidence.independent
        and evidence.decision == "APPROVE"
        and evidence.valid_from <= now <= evidence.expires_at
        and (evidence.policy_id, evidence.policy_version, evidence.authority_epoch)
        == (policy.policy_id, policy.version, policy.authority_epoch)
    )


def _evaluate(
    req: CounterfactualRequest,
    policy: CounterfactualPolicy,
    effect_model: EffectModel,
    actions: Mapping[str, ActionCandidate],
    branches: Mapping[str, CounterfactualBranch],
    branch_index: Mapping[str, Sequence[str]],
    approval: ApprovalEvidence | None,
    *,
    now: int,
) -> CounterfactualResult:
    if policy.revoked or not (policy.valid_from <= now <= policy.expires_at):
        return _hold(req, effect_model, "POLICY_INACTIVE")
    if (req.expected_policy_id, req.expected_policy_version, req.expected_authority_epoch) != (
        policy.policy_id,
        policy.version,
        policy.authority_epoch,
    ):
        return _hold(req, effect_model, "POLICY_OR_AUTHORITY_MISMATCH")
    if req.created_at > now or req.expires_at < now or now - req.created_at > policy.max_request_age_seconds:
        return _hold(req, effect_model, "REQUEST_STALE_OR_EXPIRED")
    if not req.current_state_fingerprint or not req.goal_id or not req.goal_binding or not req.graph_binding:
        return _hold(req, effect_model, "REQUIRED_CONTEXT_MISSING")
    if effect_model.revoked or not effect_model.verified or not (effect_model.valid_from <= now <= effect_model.expires_at):
        return _hold(req, effect_model, "EFFECT_MODEL_INVALID")
    if (effect_model.policy_id, effect_model.policy_version, effect_model.authority_epoch) != (
        policy.policy_id,
        policy.version,
        policy.authority_epoch,
    ):
        return _hold(req, effect_model, "EFFECT_MODEL_POLICY_OR_AUTHORITY_MISMATCH")
    if (req.expected_effect_model_id, req.expected_effect_model_version) != (
        effect_model.model_id,
        effect_model.version,
    ):
        return _hold(req, effect_model, "EFFECT_MODEL_IDENTITY_MISMATCH")
    if effect_model.binding != req.graph_binding:
        return _hold(req, effect_model, "EFFECT_MODEL_BINDING_MISMATCH")
    if not (0.0 <= effect_model.confidence <= 1.0) or effect_model.confidence < policy.min_effect_model_confidence:
        return _hold(req, effect_model, "EFFECT_MODEL_CONFIDENCE_LOW")
    if len(branches) > policy.max_branches:
        return _hold(req, effect_model, "BRANCH_LIMIT_EXCEEDED")
    if req.requested_action_id not in actions:
        return _hold(req, effect_model, "REQUESTED_ACTION_MISSING")

    action = actions[req.requested_action_id]
    if action.binding != req.graph_binding:
        return _hold(req, effect_model, "ACTION_BINDING_MISMATCH")
    if (action.expected_effect_model_id, action.expected_effect_model_version) != (
        effect_model.model_id,
        effect_model.version,
    ):
        return _hold(req, effect_model, "ACTION_EFFECT_MODEL_MISMATCH")
    if not (0.0 <= action.goal_alignment <= 1.0):
        return _hold(req, effect_model, "ACTION_GOAL_ALIGNMENT_INVALID")
    if not action.explicit_authorization and (
        action.privilege_elevation or action.sensitive_data or action.external_side_effect
    ):
        return _deny(req, effect_model, "ACTION_EXPLICIT_AUTHORIZATION_MISSING", (), 0.0, 0.0)

    ids = tuple(branch_index.get(req.requested_action_id, ()))
    if not ids:
        return _hold(req, effect_model, "REQUESTED_ACTION_BRANCHES_MISSING")

    action_branches: list[CounterfactualBranch] = []
    for bid in ids:
        b = branches.get(bid)
        if b is None:
            return _hold(req, effect_model, "BRANCH_INDEX_INCONSISTENT", bid)
        action_branches.append(b)

    # Require all three canonical counterfactual worlds for a meaningful comparison.
    kinds = {b.kind for b in action_branches}
    if BranchKind.DO not in kinds or BranchKind.DO_NOT not in kinds:
        return _hold(req, effect_model, "COUNTERFACTUAL_CORE_BRANCH_MISSING")
    if any(b.depth < 0 or b.depth > policy.max_depth for b in action_branches):
        return _hold(req, effect_model, "DEPTH_LIMIT_REACHED")

    evaluated: list[str] = []
    for b in action_branches:
        if b.action_id != action.action_id or b.binding != req.graph_binding:
            return _hold(req, effect_model, "BRANCH_BINDING_OR_ACTION_MISMATCH", b.branch_id)
        if not b.verified or b.revoked:
            return _hold(req, effect_model, "BRANCH_EVIDENCE_INVALID", b.branch_id)
        if (b.effect_model_id, b.effect_model_version) != (effect_model.model_id, effect_model.version):
            return _hold(req, effect_model, "BRANCH_EFFECT_MODEL_MISMATCH", b.branch_id)
        if not b.evaluable:
            return _hold(req, effect_model, "MAJOR_BRANCH_UNEVALUABLE", b.branch_id)
        if not (0.0 <= b.model_confidence <= 1.0) or b.model_confidence < policy.min_branch_confidence:
            return _hold(req, effect_model, "BRANCH_CONFIDENCE_LOW", b.branch_id)
        if not (0.0 <= b.goal_utility <= 1.0) or not (0.0 <= b.risk <= 1.0):
            return _hold(req, effect_model, "BRANCH_SCORE_INVALID", b.branch_id)
        if not b.predicted_state_fingerprint:
            return _hold(req, effect_model, "PREDICTED_STATE_FINGERPRINT_MISSING", b.branch_id)
        evaluated.append(b.branch_id)

    do_branches = [b for b in action_branches if b.kind is BranchKind.DO]
    max_risk = max((b.risk for b in do_branches), default=0.0)
    best_utility = max((b.goal_utility for b in do_branches), default=0.0)
    if any(b.hard_policy_violation for b in do_branches):
        return _deny(req, effect_model, "HARD_POLICY_VIOLATION", evaluated, max_risk, best_utility)
    if any(b.severe_loss and b.risk >= policy.severe_loss_deny_threshold for b in do_branches):
        return _deny(req, effect_model, "SEVERE_LOSS_THRESHOLD_EXCEEDED", evaluated, max_risk, best_utility)

    all_action_branches = list(action_branches)
    safer_candidates: list[CounterfactualBranch] = []
    for b in branches.values():
        if b.kind is BranchKind.SAFER_ALTERNATIVE and b.safer_alternative_for == action.action_id:
            alternative_action = actions.get(b.action_id)
            if (
                alternative_action is not None
                and alternative_action.binding == req.graph_binding
                and (alternative_action.expected_effect_model_id, alternative_action.expected_effect_model_version) == (effect_model.model_id, effect_model.version)
                and b.binding == req.graph_binding
                and b.verified
                and not b.revoked
                and b.evaluable
                and 0 <= b.depth <= policy.max_depth
                and not b.hard_policy_violation
                and not (b.severe_loss and b.risk >= policy.severe_loss_deny_threshold)
                and (b.effect_model_id, b.effect_model_version) == (effect_model.model_id, effect_model.version)
                and b.model_confidence >= policy.min_branch_confidence
                and 0.0 <= b.goal_utility <= 1.0
                and 0.0 <= b.risk <= 1.0
                and b.predicted_state_fingerprint
            ):
                safer_candidates.append(b)
                all_action_branches.append(b)

    pareto_ids = _pareto(all_action_branches)
    safer_candidates.sort(key=lambda b: (-b.goal_utility, b.risk, b.branch_id))
    safer = safer_candidates[0] if safer_candidates else None
    requested_best_utility = max((b.goal_utility for b in do_branches), default=0.0)
    requested_best_risk = min((b.risk for b in do_branches), default=1.0)
    if safer is not None:
        required_utility = requested_best_utility * policy.safer_alternative_utility_ratio
        if (
            safer.goal_utility >= required_utility
            and safer.risk + policy.safer_alternative_risk_delta <= requested_best_risk
        ):
            return CounterfactualResult(
                Decision.HOLD,
                ("SAFER_ALTERNATIVE_AVAILABLE",),
                req.requested_action_id,
                "",
                safer.action_id,
                tuple(sorted(evaluated + [safer.branch_id])),
                pareto_ids,
                max_risk,
                best_utility,
                effect_model.confidence,
                False,
                False,
            )

    approval_needed = action.approval_required or max_risk >= policy.high_risk_approval_threshold or (
        not action.reversible and any(b.irreversible_effect for b in do_branches)
    )
    approval_ok = _approval_valid(approval, req, policy, now=now)
    if approval_needed and not approval_ok:
        return CounterfactualResult(
            Decision.HUMAN_APPROVAL,
            ("HUMAN_APPROVAL_REQUIRED",),
            req.requested_action_id,
            "",
            "",
            tuple(sorted(evaluated)),
            pareto_ids,
            max_risk,
            best_utility,
            effect_model.confidence,
            True,
            False,
        )

    if action.goal_alignment < policy.min_goal_utility or best_utility < policy.min_goal_utility:
        return _hold(req, effect_model, "GOAL_UTILITY_INSUFFICIENT")
    if max_risk > policy.max_risk_allow:
        return CounterfactualResult(
            Decision.HOLD,
            ("RISK_ABOVE_ALLOW_THRESHOLD",),
            req.requested_action_id,
            "",
            "",
            tuple(sorted(evaluated)),
            pareto_ids,
            max_risk,
            best_utility,
            effect_model.confidence,
            False,
            False,
        )

    return CounterfactualResult(
        Decision.ALLOW,
        ("COUNTERFACTUAL_PRECHECK_PASS",),
        req.requested_action_id,
        action.action_id,
        "",
        tuple(sorted(evaluated)),
        pareto_ids,
        max_risk,
        best_utility,
        effect_model.confidence,
        approval_needed,
        True,
    )


def evaluate(
    req: CounterfactualRequest,
    policy: CounterfactualPolicy,
    effect_model: EffectModel,
    actions: Sequence[ActionCandidate],
    branches: Sequence[CounterfactualBranch],
    approval: ApprovalEvidence | None = None,
    *,
    now: int,
) -> CounterfactualResult:
    if len({a.action_id for a in actions}) != len(actions):
        return _hold(req, effect_model, "DUPLICATE_ACTION_ID")
    if len({b.branch_id for b in branches}) != len(branches):
        return _hold(req, effect_model, "DUPLICATE_BRANCH_ID")
    amap = {a.action_id: a for a in actions}
    bmap = {b.branch_id: b for b in branches}
    idx: dict[str, list[str]] = {a.action_id: [] for a in actions}
    for b in branches:
        idx.setdefault(b.action_id, []).append(b.branch_id)
    for k in idx:
        idx[k].sort()
    return _evaluate(req, policy, effect_model, amap, bmap, idx, approval, now=now)


def evaluate_prepared(
    req: CounterfactualRequest,
    policy: CounterfactualPolicy,
    effect_model: EffectModel,
    prepared: PreparedTreeState,
    approval: ApprovalEvidence | None = None,
    *,
    now: int,
) -> CounterfactualResult:
    # Current authority/model identity is always rechecked. Prepared state integrity must
    # be verified when the prepared state is received/materialized via validate_prepared_state().
    if prepared.graph_binding != req.graph_binding:
        return _hold(req, effect_model, "PREPARED_GRAPH_BINDING_MISMATCH")
    if prepared.policy_fingerprint != fingerprint(policy):
        return _hold(req, effect_model, "PREPARED_POLICY_MISMATCH")
    if prepared.effect_model_fingerprint != fingerprint(effect_model):
        return _hold(req, effect_model, "PREPARED_EFFECT_MODEL_MISMATCH")
    return _evaluate(
        req,
        policy,
        effect_model,
        dict(prepared.actions_by_id),
        dict(prepared.branches_by_id),
        dict(prepared.branch_index),
        approval,
        now=now,
    )


def make_delta(
    base: PreparedTreeState,
    target: PreparedTreeState,
) -> TreeDelta:
    if base.graph_binding != target.graph_binding:
        raise ValueError("graph_binding mismatch")
    ba = dict(base.actions_by_id)
    ta = dict(target.actions_by_id)
    bb = dict(base.branches_by_id)
    tb = dict(target.branches_by_id)
    baf = dict(base.action_fingerprints)
    taf = dict(target.action_fingerprints)
    bbf = dict(base.branch_fingerprints)
    tbf = dict(target.branch_fingerprints)
    changed_actions = tuple(ta[k] for k in sorted(set(ba) & set(ta)) if baf[k] != taf[k])
    removed_action_ids = tuple(sorted(set(ba) - set(ta)))
    added_actions = tuple(ta[k] for k in sorted(set(ta) - set(ba)))
    changed_branches = tuple(tb[k] for k in sorted(set(bb) & set(tb)) if bbf[k] != tbf[k])
    removed_branch_ids = tuple(sorted(set(bb) - set(tb)))
    added_branches = tuple(tb[k] for k in sorted(set(tb) - set(bb)))
    scalar_changes: list[tuple[str, Any]] = []
    if base.effect_model_fingerprint != target.effect_model_fingerprint:
        scalar_changes.append(("effect_model_fingerprint", target.effect_model_fingerprint))
    if base.policy_fingerprint != target.policy_fingerprint:
        scalar_changes.append(("policy_fingerprint", target.policy_fingerprint))
    return TreeDelta(
        base.registry_fingerprint,
        target.registry_fingerprint,
        tuple(scalar_changes),
        changed_actions,
        removed_action_ids,
        added_actions,
        changed_branches,
        removed_branch_ids,
        added_branches,
    )


def apply_delta(base: PreparedTreeState, delta: TreeDelta, *, generated_at: int) -> PreparedTreeState:
    if base.registry_fingerprint != delta.base_fingerprint:
        raise ValueError("wrong delta base")
    actions = dict(base.actions_by_id)
    branches = dict(base.branches_by_id)
    for k in delta.removed_action_ids:
        actions.pop(k, None)
    for a in delta.changed_actions + delta.added_actions:
        actions[a.action_id] = a
    for k in delta.removed_branch_ids:
        branches.pop(k, None)
    for b in delta.changed_branches + delta.added_branches:
        branches[b.branch_id] = b
    # Reconstruct structural indexes from the changed state without granting authority.
    idx: dict[str, list[str]] = {k: [] for k in actions}
    for b in branches.values():
        idx.setdefault(b.action_id, []).append(b.branch_id)
    for k in idx:
        idx[k].sort()
    af = tuple(sorted((k, fingerprint(v)) for k, v in actions.items()))
    bf = tuple(sorted((k, fingerprint(v)) for k, v in branches.items()))
    policy_fp = base.policy_fingerprint
    model_fp = base.effect_model_fingerprint
    for k, v in delta.scalar_changes:
        if k == "policy_fingerprint":
            policy_fp = str(v)
        elif k == "effect_model_fingerprint":
            model_fp = str(v)
    reconstructed_fp = _registry_from_fps(base.graph_binding, policy_fp, model_fp, af, bf)
    if reconstructed_fp != delta.target_fingerprint:
        raise ValueError("delta target fingerprint mismatch")
    target = PreparedTreeState(
        graph_binding=base.graph_binding,
        effect_model_fingerprint=model_fp,
        policy_fingerprint=policy_fp,
        registry_fingerprint=reconstructed_fp,
        action_fingerprints=af,
        branch_fingerprints=bf,
        branch_index=tuple(sorted((k, tuple(v)) for k, v in idx.items())),
        branches_by_id=tuple(sorted(branches.items())),
        actions_by_id=tuple(sorted(actions.items())),
        generated_at=generated_at,
    )
    return target


def sync_plan(
    prepared: PreparedTreeState,
    known_action_fingerprints: Mapping[str, str],
    known_branch_fingerprints: Mapping[str, str],
) -> TreeSyncPlan:
    af = dict(prepared.action_fingerprints)
    bf = dict(prepared.branch_fingerprints)
    missing_a = tuple(sorted(k for k, v in af.items() if known_action_fingerprints.get(k) != v))
    missing_b = tuple(sorted(k for k, v in bf.items() if known_branch_fingerprints.get(k) != v))
    amap = dict(prepared.actions_by_id)
    bmap = dict(prepared.branches_by_id)
    metadata = canonical_json(
        {
            "actions": [amap[k] for k in missing_a],
            "branches": [bmap[k] for k in missing_b],
        }
    ).encode("utf-8")
    full = canonical_json({"actions": prepared.actions_by_id, "branches": prepared.branches_by_id}).encode("utf-8")
    return TreeSyncPlan(
        prepared.registry_fingerprint,
        missing_a,
        missing_b,
        len(metadata),
        len(full),
        len(metadata) >= len(full),
    )


def default_policy(now: int) -> CounterfactualPolicy:
    return CounterfactualPolicy(
        policy_id="NOEPIN-063-POLICY",
        version="1",
        authority_epoch="E1",
        valid_from=now - 3600,
        expires_at=now + 86400,
        revoked=False,
        min_effect_model_confidence=0.80,
        min_branch_confidence=0.75,
        max_risk_allow=0.35,
        severe_loss_deny_threshold=0.70,
        high_risk_approval_threshold=0.55,
        min_goal_utility=0.60,
        safer_alternative_utility_ratio=0.95,
        safer_alternative_risk_delta=0.10,
        max_depth=4,
        max_branches=10000,
        max_request_age_seconds=3600,
        approval_role="OWNER",
    )


def default_effect_model(now: int) -> EffectModel:
    return EffectModel(
        model_id="EFFECT-063",
        version="1",
        binding="CTX-063",
        verified=True,
        revoked=False,
        confidence=0.95,
        valid_from=now - 3600,
        expires_at=now + 86400,
        policy_id="NOEPIN-063-POLICY",
        policy_version="1",
        authority_epoch="E1",
    )


def default_actions(now: int | None = None) -> tuple[ActionCandidate, ...]:
    return (
        ActionCandidate("ACT-SAFE", "safe local transform", "CTX-063", 0.90, True, False, False, False, True, False, "EFFECT-063", "1"),
        ActionCandidate("ACT-ALT", "safer alternative", "CTX-063", 0.88, True, False, False, False, True, False, "EFFECT-063", "1"),
    )


def default_branches(now: int | None = None) -> tuple[CounterfactualBranch, ...]:
    def b(
        bid: str,
        aid: str,
        kind: BranchKind,
        utility: float,
        risk: float,
        *,
        alt_for: str = "",
        depth: int = 1,
        severe: bool = False,
        irreversible: bool = False,
        external: bool = False,
        violation: bool = False,
        evaluable: bool = True,
        conf: float = 0.95,
    ) -> CounterfactualBranch:
        return CounterfactualBranch(
            bid,
            aid,
            "ROOT",
            depth,
            kind,
            "CTX-063",
            evaluable,
            True,
            False,
            "EFFECT-063",
            "1",
            conf,
            utility,
            risk,
            severe,
            irreversible,
            external,
            violation,
            fingerprint((bid, aid, kind.value, utility, risk)),
            alt_for,
        )
    return (
        b("B-SAFE-DO", "ACT-SAFE", BranchKind.DO, 0.92, 0.20),
        b("B-SAFE-NO", "ACT-SAFE", BranchKind.DO_NOT, 0.20, 0.05),
        b("B-ALT-DO", "ACT-ALT", BranchKind.DO, 0.89, 0.12),
        b("B-ALT-NO", "ACT-ALT", BranchKind.DO_NOT, 0.20, 0.05),
    )


def default_request(now: int) -> CounterfactualRequest:
    return CounterfactualRequest(
        request_id="REQ-063",
        requested_action_id="ACT-SAFE",
        current_state_fingerprint=fingerprint({"state": "current", "v": 1}),
        goal_id="GOAL-063",
        goal_binding="GOAL-BIND-063",
        graph_binding="CTX-063",
        expected_policy_id="NOEPIN-063-POLICY",
        expected_policy_version="1",
        expected_authority_epoch="E1",
        expected_effect_model_id="EFFECT-063",
        expected_effect_model_version="1",
        created_at=now - 10,
        expires_at=now + 600,
    )


def default_approval(now: int) -> ApprovalEvidence:
    return ApprovalEvidence(
        approval_id="APP-063",
        action_id="ACT-SAFE",
        role="OWNER",
        binding="CTX-063",
        verified=True,
        revoked=False,
        independent=True,
        decision="APPROVE",
        valid_from=now - 100,
        expires_at=now + 1000,
        policy_id="NOEPIN-063-POLICY",
        policy_version="1",
        authority_epoch="E1",
    )
