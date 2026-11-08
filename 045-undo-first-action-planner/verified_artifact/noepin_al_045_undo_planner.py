"""NOEPIN AL 045 — Undo-First Action Planner.

Pure control-plane planner. It ranks candidate actions that can achieve the same
objective and prefers reversible options such as trash-over-delete and draft-over-send.
It never executes, commits, transmits, deletes, publishes, deploys, or grants permission.

Creator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support using ChatGPT
License / Rights: NOT SPECIFIED
"""
from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Any, FrozenSet, Iterable, Mapping, Optional, Sequence, Tuple


class ControlDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    HOLD = "HOLD"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"


@dataclass(frozen=True)
class PlannerPolicy:
    policy_id: str
    version: str
    authority_epoch: int
    issued_at: int
    expires_at: int
    min_reversibility_for_direct_allow: int
    max_risk_for_direct_allow: int
    require_human_for_irreversible: bool
    preferred_substitutions: Mapping[str, Tuple[str, ...]]
    allowed_side_effect_scopes: FrozenSet[str]
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
        if not 0 <= self.min_reversibility_for_direct_allow <= 100:
            raise ValueError("invalid reversibility threshold")
        if not 0 <= self.max_risk_for_direct_allow <= 100:
            raise ValueError("invalid risk threshold")
        if not self.allowed_side_effect_scopes:
            raise ValueError("allowed_side_effect_scopes required")
        for op, prefs in self.preferred_substitutions.items():
            if not op or not isinstance(prefs, tuple) or any(not x for x in prefs):
                raise ValueError("invalid preferred substitution")


@dataclass(frozen=True)
class ActionCandidate:
    action_id: str
    objective: str
    operation: str
    reversibility_score: int
    risk_score: int
    undo_mode: str
    side_effect_scope: str
    requires_network: bool = False
    destructive: bool = False
    evidence_binding: str = ""

    def validate(self) -> None:
        if not self.action_id or not self.objective or not self.operation:
            raise ValueError("action identity/objective/operation required")
        if not 0 <= self.reversibility_score <= 100:
            raise ValueError("invalid reversibility_score")
        if not 0 <= self.risk_score <= 100:
            raise ValueError("invalid risk_score")
        if not self.undo_mode or not self.side_effect_scope or not self.evidence_binding:
            raise ValueError("action binding required")


@dataclass(frozen=True)
class PlanRequest:
    request_id: str
    objective: str
    requested_operation: str
    evidence_binding: str
    expected_policy_id: str
    expected_policy_version: str
    expected_authority_epoch: int
    require_exact_operation: bool = False
    human_approval_evidence: bool = False

    def validate(self) -> None:
        if not self.request_id or not self.objective or not self.requested_operation or not self.evidence_binding:
            raise ValueError("request identity/objective/operation/binding required")
        if not self.expected_policy_id or not self.expected_policy_version or self.expected_authority_epoch < 1:
            raise ValueError("expected policy binding required")


@dataclass(frozen=True)
class PreparedActionCatalog:
    catalog_fingerprint: str
    policy_fingerprint: str
    candidates: Tuple[ActionCandidate, ...]
    item_fingerprints: Mapping[str, str]
    objective_index: Mapping[str, Tuple[str, ...]]


@dataclass(frozen=True)
class ActionCatalogDelta:
    base_fingerprint: str
    target_fingerprint: str
    changed: Tuple[ActionCandidate, ...]
    removed_ids: Tuple[str, ...]
    added: Tuple[ActionCandidate, ...]


@dataclass(frozen=True)
class CatalogTransferPlan:
    missing_or_changed_ids: Tuple[str, ...]
    metadata_bytes_required: int
    full_metadata_bytes: int
    full_resend_required: bool
    action_execution_authorized: bool = False
    permission_granted: bool = False


@dataclass(frozen=True)
class PlanAssessment:
    decision: ControlDecision
    reasons: Tuple[str, ...]
    request_id: str
    recommended_action_id: Optional[str]
    recommended_operation: Optional[str]
    ordered_action_ids: Tuple[str, ...]
    catalog_fingerprint: str
    policy_fingerprint: str
    request_fingerprint: str
    reversibility_score: Optional[int]
    risk_score: Optional[int]
    permission_granted: bool = False
    action_executed: bool = False
    commit_performed: bool = False
    state_mutated: bool = False
    action_success: bool = False
    undo_success: bool = False
    safety_proven: bool = False


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


def _normalize_candidates(candidates: Iterable[ActionCandidate]) -> Tuple[ActionCandidate, ...]:
    ordered = tuple(sorted(candidates, key=lambda x: x.action_id))
    ids = [c.action_id for c in ordered]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate action_id")
    for c in ordered:
        c.validate()
    return ordered


def catalog_fingerprint(candidates: Iterable[ActionCandidate]) -> str:
    return fingerprint(_normalize_candidates(candidates))


def prepare_catalog(policy: PlannerPolicy, candidates: Iterable[ActionCandidate], *, now: int) -> PreparedActionCatalog:
    policy.validate(now)
    if policy.revoked:
        raise ValueError("policy revoked")
    normalized = _normalize_candidates(candidates)
    item_fps = {c.action_id: fingerprint(c) for c in normalized}
    idx: dict[str, list[str]] = {}
    for c in normalized:
        idx.setdefault(c.objective, []).append(c.action_id)
    return PreparedActionCatalog(
        catalog_fingerprint=fingerprint(normalized),
        policy_fingerprint=fingerprint(policy),
        candidates=normalized,
        item_fingerprints=item_fps,
        objective_index={k: tuple(sorted(v)) for k, v in sorted(idx.items())},
    )


def _hold(request: PlanRequest, policy_fp: str, catalog_fp: str, reasons: Iterable[str]) -> PlanAssessment:
    return PlanAssessment(
        decision=ControlDecision.HOLD,
        reasons=tuple(sorted(set(reasons))),
        request_id=request.request_id,
        recommended_action_id=None,
        recommended_operation=None,
        ordered_action_ids=(),
        catalog_fingerprint=catalog_fp,
        policy_fingerprint=policy_fp,
        request_fingerprint=fingerprint(request),
        reversibility_score=None,
        risk_score=None,
    )


def _rank_candidates(request: PlanRequest, policy: PlannerPolicy, candidates: Sequence[ActionCandidate]) -> Tuple[ActionCandidate, ...]:
    preferred = policy.preferred_substitutions.get(request.requested_operation, ())
    pref_rank = {op: i for i, op in enumerate(preferred)}

    def key(c: ActionCandidate) -> tuple:
        if request.require_exact_operation:
            tier = 0 if c.operation == request.requested_operation else 1000
        elif c.operation in pref_rank:
            tier = pref_rank[c.operation]
        elif c.operation == request.requested_operation:
            tier = len(preferred) + 1
        else:
            tier = len(preferred) + 2
        return (tier, -c.reversibility_score, c.risk_score, c.action_id)

    return tuple(sorted(candidates, key=key))


def evaluate_prepared(request: PlanRequest, policy: PlannerPolicy, prepared: PreparedActionCatalog, *, now: int) -> PlanAssessment:
    policy_fp = fingerprint(policy)
    try:
        request.validate()
        policy.validate(now)
    except (ValueError, TypeError) as exc:
        return _hold(request, policy_fp, prepared.catalog_fingerprint, (f"INVALID_REQUEST_OR_POLICY:{exc}",))

    if policy.revoked:
        return _hold(request, policy_fp, prepared.catalog_fingerprint, ("POLICY_REVOKED",))
    if policy_fp != prepared.policy_fingerprint:
        return _hold(request, policy_fp, prepared.catalog_fingerprint, ("PREPARED_POLICY_FINGERPRINT_MISMATCH",))
    if request.expected_policy_id != policy.policy_id:
        return _hold(request, policy_fp, prepared.catalog_fingerprint, ("POLICY_ID_MISMATCH",))
    if request.expected_policy_version != policy.version:
        return _hold(request, policy_fp, prepared.catalog_fingerprint, ("POLICY_VERSION_MISMATCH",))
    if request.expected_authority_epoch != policy.authority_epoch:
        return _hold(request, policy_fp, prepared.catalog_fingerprint, ("AUTHORITY_EPOCH_MISMATCH",))

    by_id = {c.action_id: c for c in prepared.candidates}
    ids = prepared.objective_index.get(request.objective, ())
    objective_candidates = tuple(by_id[i] for i in ids)
    if not objective_candidates:
        return _hold(request, policy_fp, prepared.catalog_fingerprint, ("NO_OBJECTIVE_CANDIDATE",))

    objective_candidates = tuple(c for c in objective_candidates if c.side_effect_scope in policy.allowed_side_effect_scopes)
    if not objective_candidates:
        return _hold(request, policy_fp, prepared.catalog_fingerprint, ("SIDE_EFFECT_SCOPE_NOT_ALLOWED",))

    if request.require_exact_operation:
        objective_candidates = tuple(c for c in objective_candidates if c.operation == request.requested_operation)
        if not objective_candidates:
            return _hold(request, policy_fp, prepared.catalog_fingerprint, ("EXACT_OPERATION_UNAVAILABLE",))

    ranked = _rank_candidates(request, policy, objective_candidates)
    chosen = ranked[0]
    reasons: list[str] = []
    preferred = policy.preferred_substitutions.get(request.requested_operation, ())
    if chosen.operation != request.requested_operation:
        if chosen.operation in preferred:
            reasons.append("REVERSIBLE_ALTERNATIVE_SELECTED")
        else:
            reasons.append("SAME_OBJECTIVE_ALTERNATIVE_SELECTED")
    else:
        reasons.append("REQUESTED_OPERATION_SELECTED")

    if chosen.risk_score > policy.max_risk_for_direct_allow:
        return PlanAssessment(
            ControlDecision.HOLD, tuple(sorted(set(reasons + ["RISK_ABOVE_POLICY_LIMIT"]))), request.request_id,
            chosen.action_id, chosen.operation, tuple(c.action_id for c in ranked), prepared.catalog_fingerprint,
            policy_fp, fingerprint(request), chosen.reversibility_score, chosen.risk_score
        )

    irreversible = chosen.reversibility_score < policy.min_reversibility_for_direct_allow or chosen.undo_mode == "NONE"
    if irreversible and policy.require_human_for_irreversible and not request.human_approval_evidence:
        decision = ControlDecision.HUMAN_APPROVAL
        reasons.append("IRREVERSIBLE_REQUIRES_HUMAN_APPROVAL")
    else:
        decision = ControlDecision.ALLOW
        reasons.append("UNDO_FIRST_PLAN_CANDIDATE")
        if irreversible and request.human_approval_evidence:
            reasons.append("HUMAN_APPROVAL_EVIDENCE_PRESENT")

    return PlanAssessment(
        decision=decision,
        reasons=tuple(sorted(set(reasons))),
        request_id=request.request_id,
        recommended_action_id=chosen.action_id,
        recommended_operation=chosen.operation,
        ordered_action_ids=tuple(c.action_id for c in ranked),
        catalog_fingerprint=prepared.catalog_fingerprint,
        policy_fingerprint=policy_fp,
        request_fingerprint=fingerprint(request),
        reversibility_score=chosen.reversibility_score,
        risk_score=chosen.risk_score,
    )


def evaluate(request: PlanRequest, policy: PlannerPolicy, candidates: Iterable[ActionCandidate], *, now: int) -> PlanAssessment:
    try:
        prepared = prepare_catalog(policy, candidates, now=now)
    except (ValueError, TypeError) as exc:
        return _hold(request, fingerprint(policy), "", (f"INVALID_CATALOG_OR_POLICY:{exc}",))
    return evaluate_prepared(request, policy, prepared, now=now)


def build_catalog_delta(base: Iterable[ActionCandidate], target: Iterable[ActionCandidate]) -> ActionCatalogDelta:
    b = _normalize_candidates(base)
    t = _normalize_candidates(target)
    bm = {x.action_id: x for x in b}
    tm = {x.action_id: x for x in t}
    changed = tuple(tm[k] for k in sorted(set(bm) & set(tm)) if fingerprint(bm[k]) != fingerprint(tm[k]))
    removed = tuple(sorted(set(bm) - set(tm)))
    added = tuple(tm[k] for k in sorted(set(tm) - set(bm)))
    return ActionCatalogDelta(fingerprint(b), fingerprint(t), changed, removed, added)


def apply_catalog_delta(base: Iterable[ActionCandidate], delta: ActionCatalogDelta) -> Tuple[ActionCandidate, ...]:
    normalized = _normalize_candidates(base)
    if fingerprint(normalized) != delta.base_fingerprint:
        raise ValueError("base fingerprint mismatch")
    m = {x.action_id: x for x in normalized}
    for rid in delta.removed_ids:
        if rid not in m:
            raise ValueError("removed id missing from base")
        del m[rid]
    for c in delta.changed:
        if c.action_id not in m:
            raise ValueError("changed id missing from base")
        c.validate(); m[c.action_id] = c
    for c in delta.added:
        if c.action_id in m:
            raise ValueError("added id already exists")
        c.validate(); m[c.action_id] = c
    out = _normalize_candidates(m.values())
    if fingerprint(out) != delta.target_fingerprint:
        raise ValueError("target fingerprint mismatch")
    return out


def plan_catalog_sync(prepared: PreparedActionCatalog, remote_known_item_fingerprints: Mapping[str, str]) -> CatalogTransferPlan:
    missing = tuple(sorted(k for k, fp in prepared.item_fingerprints.items() if remote_known_item_fingerprints.get(k) != fp))
    by_id = {c.action_id: c for c in prepared.candidates}
    metadata_bytes = sum(len(canonical_json(by_id[i]).encode("utf-8")) for i in missing)
    full_bytes = len(canonical_json(prepared.candidates).encode("utf-8"))
    return CatalogTransferPlan(
        missing_or_changed_ids=missing,
        metadata_bytes_required=metadata_bytes,
        full_metadata_bytes=full_bytes,
        full_resend_required=metadata_bytes >= full_bytes,
    )


def assessment_digest(values: Iterable[PlanAssessment]) -> str:
    return fingerprint(tuple(values))


def default_policy(now: int = 1_800_000_000) -> PlannerPolicy:
    return PlannerPolicy(
        policy_id="UNDO-FIRST-V2",
        version="2",
        authority_epoch=1,
        issued_at=now - 100,
        expires_at=now + 100_000,
        min_reversibility_for_direct_allow=50,
        max_risk_for_direct_allow=70,
        require_human_for_irreversible=True,
        preferred_substitutions={
            "delete": ("trash", "archive"),
            "send": ("draft",),
            "publish": ("preview", "stage"),
            "overwrite": ("versioned_write", "copy"),
            "deploy": ("dry_run", "staging"),
        },
        allowed_side_effect_scopes=frozenset({"local", "workspace", "external_candidate"}),
    )


def default_candidates() -> Tuple[ActionCandidate, ...]:
    return (
        ActionCandidate("A-DELETE", "remove_file", "delete", 0, 65, "NONE", "local", False, True, "E-A-DELETE"),
        ActionCandidate("A-TRASH", "remove_file", "trash", 90, 20, "RESTORE_FROM_TRASH", "local", False, False, "E-A-TRASH"),
        ActionCandidate("A-ARCHIVE", "remove_file", "archive", 95, 10, "UNARCHIVE", "local", False, False, "E-A-ARCHIVE"),
        ActionCandidate("A-SEND", "communicate", "send", 5, 70, "NONE", "external_candidate", True, False, "E-A-SEND"),
        ActionCandidate("A-DRAFT", "communicate", "draft", 100, 10, "DISCARD_DRAFT", "local", False, False, "E-A-DRAFT"),
        ActionCandidate("A-PUBLISH", "release", "publish", 10, 75, "NONE", "external_candidate", True, False, "E-A-PUBLISH"),
        ActionCandidate("A-PREVIEW", "release", "preview", 100, 5, "DISCARD_PREVIEW", "local", False, False, "E-A-PREVIEW"),
        ActionCandidate("A-STAGE", "release", "stage", 90, 15, "UNSTAGE", "workspace", False, False, "E-A-STAGE"),
        ActionCandidate("A-OVERWRITE", "update_file", "overwrite", 10, 60, "NONE", "local", False, True, "E-A-OVERWRITE"),
        ActionCandidate("A-VERSION", "update_file", "versioned_write", 95, 15, "ROLLBACK_VERSION", "local", False, False, "E-A-VERSION"),
        ActionCandidate("A-COPY", "update_file", "copy", 100, 10, "REMOVE_COPY", "local", False, False, "E-A-COPY"),
        ActionCandidate("A-DEPLOY", "deploy_change", "deploy", 5, 80, "NONE", "external_candidate", True, False, "E-A-DEPLOY"),
        ActionCandidate("A-DRYRUN", "deploy_change", "dry_run", 100, 5, "DISCARD_RESULT", "local", False, False, "E-A-DRYRUN"),
        ActionCandidate("A-STAGING", "deploy_change", "staging", 85, 25, "ROLLBACK_STAGING", "workspace", False, False, "E-A-STAGING"),
    )


def default_request(now: int = 1_800_000_000, *, objective: str = "communicate", requested_operation: str = "send") -> PlanRequest:
    p = default_policy(now)
    return PlanRequest(
        request_id="REQ-UNDO-DEFAULT",
        objective=objective,
        requested_operation=requested_operation,
        evidence_binding="E-REQ-UNDO",
        expected_policy_id=p.policy_id,
        expected_policy_version=p.version,
        expected_authority_epoch=p.authority_epoch,
    )
