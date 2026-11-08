"""NOEPIN AL 075 — Latent Goal Inference Guard — Sequential Successor V2.

Creator / Originator / Project Owner: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

This module is a deterministic control-evidence evaluator. It does not infer private
mental states. It ranks typed goal candidates from supplied action/effect evidence
and preserves ambiguity instead of converting a candidate into truth.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Iterable, Mapping, Sequence


class Decision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    HOLD = "HOLD"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"


@dataclass(frozen=True)
class GoalSpec:
    goal_id: str
    desired_effects: tuple[str, ...]
    forbidden_effects: tuple[str, ...]
    high_impact: bool
    binding: str
    state_epoch: str


@dataclass(frozen=True)
class EffectSpec:
    effect_id: str
    semantic_tags: tuple[str, ...]
    observed: bool
    impact: int
    binding: str
    state_epoch: str


@dataclass(frozen=True)
class ActionSpec:
    action_id: str
    effect_ids: tuple[str, ...]
    observed: bool
    binding: str
    state_epoch: str


@dataclass(frozen=True)
class GoalChangeEvidence:
    evidence_id: str
    target_goal_id: str
    independent: bool
    valid: bool
    revoked: bool
    binding: str
    state_epoch: str


@dataclass(frozen=True)
class LatentGoalPolicy:
    binding: str
    state_epoch: str
    max_sequence_length: int = 128
    allow_distance: int = 2500
    hold_distance: int = 5500
    ambiguity_margin: int = 700
    min_candidate_score: int = 1800
    high_impact_ambiguity_score: int = 2500
    revoked: bool = False


@dataclass(frozen=True)
class LatentGoalRequest:
    request_id: str
    surface_request: str
    action_sequence: tuple[str, ...]
    user_goal_id: str
    binding: str
    state_epoch: str
    goal_change_requested: bool = False
    requested_goal_id: str | None = None
    approval_evidence_id: str | None = None


@dataclass(frozen=True)
class GoalCandidate:
    goal_id: str
    score: int
    distance: int
    desired_overlap: tuple[str, ...]
    forbidden_overlap: tuple[str, ...]
    supporting_effects: tuple[str, ...]
    conflicting_effects: tuple[str, ...]


@dataclass(frozen=True)
class LatentGoalResult:
    decision: Decision
    reasons: tuple[str, ...]
    candidates: tuple[GoalCandidate, ...]
    top_goal_id: str | None
    goal_distance: int | None
    ambiguity: bool
    deviation_detected: bool
    recheck_required: bool
    next_gate_candidate: bool
    human_approval_candidate: bool
    # authority negatives
    permission_granted: bool = False
    goal_changed: bool = False
    human_approval_executed: bool = False
    tool_executed: bool = False
    transaction_committed: bool = False
    external_write_performed: bool = False
    world_truth_proven: bool = False
    safety_proven: bool = False
    action_success: bool = False


@dataclass(frozen=True)
class PreparedGoalState:
    policy: LatentGoalPolicy
    goals: tuple[GoalSpec, ...]
    effects: tuple[EffectSpec, ...]
    actions: tuple[ActionSpec, ...]
    approvals: tuple[GoalChangeEvidence, ...]
    goal_fingerprints: tuple[tuple[str, str], ...]
    effect_fingerprints: tuple[tuple[str, str], ...]
    action_fingerprints: tuple[tuple[str, str], ...]
    approval_fingerprints: tuple[tuple[str, str], ...]
    policy_fingerprint: str
    registry_fingerprint: str
    goal_index: tuple[tuple[str, GoalSpec], ...]
    effect_index: tuple[tuple[str, EffectSpec], ...]
    action_index: tuple[tuple[str, ActionSpec], ...]
    approval_index: tuple[tuple[str, GoalChangeEvidence], ...]
    binding: str
    state_epoch: str


@dataclass(frozen=True)
class GoalRegistryDelta:
    base_fingerprint: str
    target_fingerprint: str
    changed_goals: tuple[GoalSpec, ...]
    removed_goal_ids: tuple[str, ...]
    changed_effects: tuple[EffectSpec, ...]
    removed_effect_ids: tuple[str, ...]
    changed_actions: tuple[ActionSpec, ...]
    removed_action_ids: tuple[str, ...]
    changed_approvals: tuple[GoalChangeEvidence, ...]
    removed_approval_ids: tuple[str, ...]
    target_policy: LatentGoalPolicy
    binding: str
    state_epoch: str


@dataclass(frozen=True)
class GoalSyncPlan:
    missing_or_changed_goals: tuple[str, ...]
    missing_or_changed_effects: tuple[str, ...]
    missing_or_changed_actions: tuple[str, ...]
    missing_or_changed_approvals: tuple[str, ...]
    metadata_bytes_required: int
    full_resend_required: bool


def _canon(v) -> bytes:
    def cv(x):
        if isinstance(x, Enum): return x.value
        if hasattr(x, "__dataclass_fields__"):
            return {k: cv(getattr(x, k)) for k in x.__dataclass_fields__}
        if isinstance(x, tuple): return [cv(i) for i in x]
        if isinstance(x, list): return [cv(i) for i in x]
        if isinstance(x, dict): return {str(k): cv(x[k]) for k in sorted(x)}
        return x
    return json.dumps(cv(v), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _fp(v) -> str:
    return sha256(_canon(v)).hexdigest()


def _unique_ids(items: Sequence, attr: str) -> bool:
    ids = [getattr(x, attr) for x in items]
    return len(ids) == len(set(ids))


def _normalize_tags(xs: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(set(str(x).strip().upper() for x in xs if str(x).strip())))


def _registry_fingerprint(policy, goals, effects, actions, approvals) -> str:
    return _fp({
        "policy": _fp(policy),
        "goals": sorted((g.goal_id, _fp(g)) for g in goals),
        "effects": sorted((e.effect_id, _fp(e)) for e in effects),
        "actions": sorted((a.action_id, _fp(a)) for a in actions),
        "approvals": sorted((a.evidence_id, _fp(a)) for a in approvals),
    })


def default_policy() -> LatentGoalPolicy:
    return LatentGoalPolicy(binding="GOAL-BIND", state_epoch="STATE-EPOCH-1")


def default_goals() -> tuple[GoalSpec, ...]:
    b, e = "GOAL-BIND", "STATE-EPOCH-1"
    return (
        GoalSpec("G-LOCAL-ANALYSIS", ("READ", "ANALYZE", "SUMMARIZE"), ("EXTERNAL_SEND", "DELETE", "ESCALATE_AUTH"), False, b, e),
        GoalSpec("G-EXTERNAL-SHARE", ("READ", "ANALYZE", "EXTERNAL_SEND"), ("DELETE",), True, b, e),
        GoalSpec("G-DELETE-DATA", ("DELETE",), ("PRESERVE",), True, b, e),
        GoalSpec("G-PRIVILEGE-EXPANSION", ("ESCALATE_AUTH",), ("LEAST_PRIVILEGE",), True, b, e),
        GoalSpec("G-PRESERVE", ("READ", "PRESERVE"), ("DELETE",), False, b, e),
    )


def default_effects() -> tuple[EffectSpec, ...]:
    b, e = "GOAL-BIND", "STATE-EPOCH-1"
    return (
        EffectSpec("E-READ", ("READ",), True, 1, b, e),
        EffectSpec("E-ANALYZE", ("ANALYZE",), True, 1, b, e),
        EffectSpec("E-SUMMARY", ("SUMMARIZE",), True, 1, b, e),
        EffectSpec("E-SEND", ("EXTERNAL_SEND",), True, 5, b, e),
        EffectSpec("E-DELETE", ("DELETE",), True, 5, b, e),
        EffectSpec("E-ESCALATE", ("ESCALATE_AUTH",), True, 5, b, e),
        EffectSpec("E-PRESERVE", ("PRESERVE",), True, 2, b, e),
    )


def default_actions() -> tuple[ActionSpec, ...]:
    b, e = "GOAL-BIND", "STATE-EPOCH-1"
    return (
        ActionSpec("A-READ", ("E-READ",), True, b, e),
        ActionSpec("A-ANALYZE", ("E-ANALYZE",), True, b, e),
        ActionSpec("A-SUMMARY", ("E-SUMMARY",), True, b, e),
        ActionSpec("A-SEND", ("E-SEND",), True, b, e),
        ActionSpec("A-DELETE", ("E-DELETE",), True, b, e),
        ActionSpec("A-ESCALATE", ("E-ESCALATE",), True, b, e),
        ActionSpec("A-PRESERVE", ("E-PRESERVE",), True, b, e),
    )


def default_approvals() -> tuple[GoalChangeEvidence, ...]:
    return (
        GoalChangeEvidence("APR-GOAL-CHANGE", "G-EXTERNAL-SHARE", True, True, False, "GOAL-BIND", "STATE-EPOCH-1"),
    )


def default_request() -> LatentGoalRequest:
    return LatentGoalRequest("REQ-75", "analyze locally and summarize", ("A-READ", "A-ANALYZE", "A-SUMMARY"), "G-LOCAL-ANALYSIS", "GOAL-BIND", "STATE-EPOCH-1")


def _validate_registry(policy, goals, effects, actions, approvals) -> tuple[bool, tuple[str, ...]]:
    reasons=[]
    if policy.revoked: reasons.append("POLICY_REVOKED")
    if not policy.binding or not policy.state_epoch: reasons.append("POLICY_IDENTITY_MISSING")
    if policy.max_sequence_length <= 0: reasons.append("INVALID_POLICY_LIMIT")
    if not (0 <= policy.allow_distance <= policy.hold_distance <= 10000): reasons.append("INVALID_DISTANCE_POLICY")
    if not _unique_ids(goals,"goal_id"): reasons.append("DUPLICATE_GOAL")
    if not _unique_ids(effects,"effect_id"): reasons.append("DUPLICATE_EFFECT")
    if not _unique_ids(actions,"action_id"): reasons.append("DUPLICATE_ACTION")
    if not _unique_ids(approvals,"evidence_id"): reasons.append("DUPLICATE_APPROVAL")
    for x in list(goals)+list(effects)+list(actions)+list(approvals):
        if getattr(x,"binding") != policy.binding or getattr(x,"state_epoch") != policy.state_epoch:
            reasons.append("REGISTRY_BINDING_MISMATCH"); break
    eids={x.effect_id for x in effects}
    for a in actions:
        if not a.effect_ids or any(e not in eids for e in a.effect_ids):
            reasons.append("ACTION_EFFECT_REFERENCE_INVALID"); break
    for g in goals:
        if not g.desired_effects: reasons.append("GOAL_DESIRED_EFFECTS_EMPTY"); break
    return (not reasons, tuple(sorted(set(reasons))))


def _candidate(goal: GoalSpec, observed_tags: set[str], observed_effect_ids: tuple[str,...]) -> GoalCandidate:
    desired=set(_normalize_tags(goal.desired_effects)); forbidden=set(_normalize_tags(goal.forbidden_effects))
    pos=sorted(observed_tags & desired); neg=sorted(observed_tags & forbidden)
    missing=desired-observed_tags
    denom=max(1,len(desired))
    coverage=int(round(10000*len(pos)/denom))
    conflict_penalty=min(10000, len(neg)*4500)
    score=max(0, coverage-conflict_penalty)
    # distance: missing desired + conflicts; 0 is close to goal
    distance=min(10000, int(round(10000*len(missing)/denom)) + len(neg)*3000)
    return GoalCandidate(goal.goal_id,score,distance,tuple(pos),tuple(neg),observed_effect_ids,tuple(neg))


def _eval_core(req, policy, goals, effects, actions, approvals, *, indexes=None, registry_already_validated: bool=False) -> LatentGoalResult:
    def result(dec,reasons,cands=(),top=None,dist=None,amb=False,dev=False,recheck=False,nextg=False,human=False):
        return LatentGoalResult(dec,tuple(reasons),tuple(cands),top,dist,amb,dev,recheck,nextg,human)
    try:
        if not isinstance(req,LatentGoalRequest): return result(Decision.HOLD,("INVALID_TYPED_INPUT",),recheck=True)
        if req.binding != policy.binding or req.state_epoch != policy.state_epoch: return result(Decision.HOLD,("REQUEST_BINDING_MISMATCH",),recheck=True)
        if not registry_already_validated:
            ok,rr=_validate_registry(policy,goals,effects,actions,approvals)
            if not ok: return result(Decision.HOLD,rr,recheck=True)
        if not req.surface_request.strip(): return result(Decision.HOLD,("SURFACE_REQUEST_EMPTY",),recheck=True)
        if not req.action_sequence: return result(Decision.HOLD,("ACTION_SEQUENCE_EMPTY",),recheck=True)
        if len(req.action_sequence)>policy.max_sequence_length: return result(Decision.HOLD,("SEQUENCE_LIMIT_EXCEEDED",),recheck=True)
        if len(set(req.action_sequence))!=len(req.action_sequence): return result(Decision.HOLD,("DUPLICATE_ACTION_IN_SEQUENCE",),recheck=True)
        if indexes is None:
            gi={g.goal_id:g for g in goals}; ei={e.effect_id:e for e in effects}; ai={a.action_id:a for a in actions}; ap={x.evidence_id:x for x in approvals}
        else: gi,ei,ai,ap=indexes
        if req.user_goal_id not in gi: return result(Decision.HOLD,("USER_GOAL_UNKNOWN",),recheck=True)
        observed_effect_ids=[]; observed_tags=set(); max_impact=0
        for aid in req.action_sequence:
            a=ai.get(aid)
            if a is None: return result(Decision.HOLD,("ACTION_UNKNOWN",aid),recheck=True)
            if not a.observed: return result(Decision.HOLD,("ACTION_UNOBSERVED",aid),recheck=True)
            for eid in a.effect_ids:
                eff=ei.get(eid)
                if eff is None: return result(Decision.HOLD,("EFFECT_UNKNOWN",eid),recheck=True)
                if not eff.observed: return result(Decision.HOLD,("EFFECT_UNOBSERVED",eid),recheck=True)
                observed_effect_ids.append(eid); observed_tags.update(_normalize_tags(eff.semantic_tags)); max_impact=max(max_impact,eff.impact)
        observed_effect_ids=tuple(sorted(set(observed_effect_ids)))
        user=gi[req.user_goal_id]
        user_forbidden=set(_normalize_tags(user.forbidden_effects))
        forbidden_overlap=tuple(sorted(observed_tags & user_forbidden))
        cands=tuple(sorted((_candidate(g,observed_tags,observed_effect_ids) for g in goals),key=lambda c:(-c.score,c.distance,c.goal_id)))
        viable=tuple(c for c in cands if c.score>=policy.min_candidate_score)
        top=viable[0] if viable else None
        if forbidden_overlap:
            return result(Decision.DENY,("USER_GOAL_FORBIDDEN_EFFECT",)+forbidden_overlap,cands,top.goal_id if top else None,top.distance if top else None,False,True,True)
        if top is None:
            return result(Decision.HOLD,("NO_SUFFICIENT_LATENT_GOAL_CANDIDATE",),cands,recheck=True)
        ambiguous=False
        if len(viable)>1:
            second=viable[1]
            meaning_diff = top.goal_id != second.goal_id and (gi[top.goal_id].high_impact or gi[second.goal_id].high_impact or max_impact>=4)
            ambiguous = meaning_diff and abs(top.score-second.score)<=policy.ambiguity_margin
        if ambiguous:
            return result(Decision.HOLD,("MATERIAL_LATENT_GOAL_AMBIGUITY",),cands,top.goal_id,top.distance,True,True,True)
        if top.goal_id != user.goal_id:
            # A highly supported different goal is deviation, but change can only be routed to HUMAN_APPROVAL candidate.
            if req.goal_change_requested and req.requested_goal_id==top.goal_id:
                ev=ap.get(req.approval_evidence_id or "")
                if ev and ev.target_goal_id==top.goal_id and ev.independent and ev.valid and not ev.revoked and ev.binding==policy.binding and ev.state_epoch==policy.state_epoch:
                    return result(Decision.HUMAN_APPROVAL,("GOAL_CHANGE_REQUIRES_HUMAN_APPROVAL_EXECUTION",),cands,top.goal_id,top.distance,False,True,True,False,True)
            # If the observed effect pattern is far from user goal, hold rather than claim motive.
            user_cand=next(c for c in cands if c.goal_id==user.goal_id)
            if user_cand.distance>=policy.hold_distance or top.score>user_cand.score+policy.ambiguity_margin:
                return result(Decision.HOLD,("LATENT_GOAL_DEVIATION",),cands,top.goal_id,user_cand.distance,False,True,True)
        user_cand=next(c for c in cands if c.goal_id==user.goal_id)
        if user_cand.distance>policy.allow_distance:
            return result(Decision.HOLD,("USER_GOAL_DISTANCE_HIGH",),cands,top.goal_id,user_cand.distance,False,True,True)
        return result(Decision.ALLOW,("GOAL_ALIGNED_WITH_SUPPLIED_EFFECT_MODEL",),cands,top.goal_id,user_cand.distance,False,False,False,True)
    except Exception:
        return result(Decision.HOLD,("INVALID_TYPED_INPUT",),recheck=True)


def evaluate(req: LatentGoalRequest, policy: LatentGoalPolicy, goals: Sequence[GoalSpec], effects: Sequence[EffectSpec], actions: Sequence[ActionSpec], approvals: Sequence[GoalChangeEvidence]=()) -> LatentGoalResult:
    return _eval_core(req,policy,tuple(goals),tuple(effects),tuple(actions),tuple(approvals))


def prepare_state(policy, goals, effects, actions, approvals=(), *, binding: str) -> PreparedGoalState:
    goals, effects, actions, approvals = tuple(goals),tuple(effects),tuple(actions),tuple(approvals)
    ok,reasons=_validate_registry(policy,goals,effects,actions,approvals)
    if not ok or binding!=policy.binding: raise ValueError("invalid registry: "+",".join(reasons))
    gf=tuple(sorted((x.goal_id,_fp(x)) for x in goals)); ef=tuple(sorted((x.effect_id,_fp(x)) for x in effects)); af=tuple(sorted((x.action_id,_fp(x)) for x in actions)); pf=tuple(sorted((x.evidence_id,_fp(x)) for x in approvals))
    reg=_registry_fingerprint(policy,goals,effects,actions,approvals)
    return PreparedGoalState(policy,goals,effects,actions,approvals,gf,ef,af,pf,_fp(policy),reg,tuple(sorted((x.goal_id,x) for x in goals)),tuple(sorted((x.effect_id,x) for x in effects)),tuple(sorted((x.action_id,x) for x in actions)),tuple(sorted((x.evidence_id,x) for x in approvals)),binding,policy.state_epoch)


def validate_prepared_integrity(st: PreparedGoalState) -> bool:
    try:
        if st.binding!=st.policy.binding or st.state_epoch!=st.policy.state_epoch: return False
        if _fp(st.policy)!=st.policy_fingerprint: return False
        if tuple(sorted((x.goal_id,_fp(x)) for x in st.goals))!=st.goal_fingerprints: return False
        if tuple(sorted((x.effect_id,_fp(x)) for x in st.effects))!=st.effect_fingerprints: return False
        if tuple(sorted((x.action_id,_fp(x)) for x in st.actions))!=st.action_fingerprints: return False
        if tuple(sorted((x.evidence_id,_fp(x)) for x in st.approvals))!=st.approval_fingerprints: return False
        if tuple(sorted((x.goal_id,x) for x in st.goals))!=st.goal_index: return False
        if tuple(sorted((x.effect_id,x) for x in st.effects))!=st.effect_index: return False
        if tuple(sorted((x.action_id,x) for x in st.actions))!=st.action_index: return False
        if tuple(sorted((x.evidence_id,x) for x in st.approvals))!=st.approval_index: return False
        return _registry_fingerprint(st.policy,st.goals,st.effects,st.actions,st.approvals)==st.registry_fingerprint
    except Exception: return False


def evaluate_prepared(req: LatentGoalRequest, st: PreparedGoalState, *, current_policy_fingerprint: str, current_registry_fingerprint: str, prepared_integrity_validated: bool) -> LatentGoalResult:
    if not prepared_integrity_validated:
        return LatentGoalResult(Decision.HOLD,("PREPARED_INTEGRITY_NOT_VALIDATED",),(),None,None,False,False,True,False,False)
    if current_policy_fingerprint!=st.policy_fingerprint:
        return LatentGoalResult(Decision.HOLD,("POLICY_FINGERPRINT_CHANGED",),(),None,None,False,False,True,False,False)
    if current_registry_fingerprint!=st.registry_fingerprint:
        return LatentGoalResult(Decision.HOLD,("REGISTRY_FINGERPRINT_CHANGED",),(),None,None,False,False,True,False,False)
    indexes=(dict(st.goal_index),dict(st.effect_index),dict(st.action_index),dict(st.approval_index))
    return _eval_core(req,st.policy,st.goals,st.effects,st.actions,st.approvals,indexes=indexes,registry_already_validated=True)


def make_delta(base: PreparedGoalState, target: PreparedGoalState) -> GoalRegistryDelta:
    if not validate_prepared_integrity(base) or not validate_prepared_integrity(target): raise ValueError("invalid prepared state")
    if base.binding!=target.binding or base.state_epoch!=target.state_epoch: raise ValueError("identity mismatch")
    def changes(base_items,target_items,key):
        b={key(x):_fp(x) for x in base_items}; t={key(x):x for x in target_items}
        changed=tuple(t[k] for k in sorted(t) if b.get(k)!=_fp(t[k])); removed=tuple(sorted(set(b)-set(t))); return changed,removed
    cg,rg=changes(base.goals,target.goals,lambda x:x.goal_id); ce,re=changes(base.effects,target.effects,lambda x:x.effect_id); ca,ra=changes(base.actions,target.actions,lambda x:x.action_id); cp,rp=changes(base.approvals,target.approvals,lambda x:x.evidence_id)
    return GoalRegistryDelta(base.registry_fingerprint,target.registry_fingerprint,cg,rg,ce,re,ca,ra,cp,rp,target.policy,target.binding,target.state_epoch)


def apply_delta(base: PreparedGoalState, delta: GoalRegistryDelta) -> PreparedGoalState:
    if not validate_prepared_integrity(base) or base.registry_fingerprint!=delta.base_fingerprint: raise ValueError("base mismatch")
    def patch(items,changed,removed,key):
        d={key(x):x for x in items}
        for k in removed: d.pop(k,None)
        for x in changed: d[key(x)]=x
        return tuple(d[k] for k in sorted(d))
    st=prepare_state(delta.target_policy,patch(base.goals,delta.changed_goals,delta.removed_goal_ids,lambda x:x.goal_id),patch(base.effects,delta.changed_effects,delta.removed_effect_ids,lambda x:x.effect_id),patch(base.actions,delta.changed_actions,delta.removed_action_ids,lambda x:x.action_id),patch(base.approvals,delta.changed_approvals,delta.removed_approval_ids,lambda x:x.evidence_id),binding=delta.binding)
    if st.registry_fingerprint!=delta.target_fingerprint: raise ValueError("target fingerprint mismatch")
    return st


def missing_only_sync_plan(st: PreparedGoalState, remote_goal_fps: Mapping[str,str], remote_effect_fps: Mapping[str,str], remote_action_fps: Mapping[str,str], remote_approval_fps: Mapping[str,str]) -> GoalSyncPlan:
    if not validate_prepared_integrity(st): return GoalSyncPlan((),(),(),(),0,True)
    def miss(local_pairs,remote): return tuple(k for k,v in local_pairs if remote.get(k)!=v)
    mg=miss(st.goal_fingerprints,remote_goal_fps); me=miss(st.effect_fingerprints,remote_effect_fps); ma=miss(st.action_fingerprints,remote_action_fps); mp=miss(st.approval_fingerprints,remote_approval_fps)
    meta=len(_canon({"g":mg,"e":me,"a":ma,"p":mp,"base":st.registry_fingerprint}))
    return GoalSyncPlan(mg,me,ma,mp,meta,False)


def full_registry_bytes(st: PreparedGoalState) -> int:
    return len(_canon({"policy":st.policy,"goals":st.goals,"effects":st.effects,"actions":st.actions,"approvals":st.approvals}))


def delta_bytes(delta: GoalRegistryDelta) -> int:
    return len(_canon(delta))
