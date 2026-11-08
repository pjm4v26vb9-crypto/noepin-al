"""NOEPIN AL 076 — Long-Horizon Goal Drift Detector — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Deterministic typed control-evidence evaluator for long-horizon goal drift.
It does not infer private mental states, grant permission, execute approval, mutate goals,
perform actions, or establish world truth. Supplied checkpoints may attest an externally
committed baseline change; this module only evaluates that evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Mapping, Sequence


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
    binding: str
    state_epoch: str


@dataclass(frozen=True)
class StepRecord:
    step_id: str
    timestamp: int
    effect_tags: tuple[str, ...]
    observed: bool
    binding: str
    state_epoch: str


@dataclass(frozen=True)
class PlanRecord:
    plan_id: str
    effect_tags: tuple[str, ...]
    observed: bool
    binding: str
    state_epoch: str


@dataclass(frozen=True)
class CheckpointRecord:
    checkpoint_id: str
    goal_id: str
    through_step_id: str | None
    observed: bool
    externally_committed_goal_change: bool
    independent_authority: bool
    valid: bool
    revoked: bool
    binding: str
    state_epoch: str


@dataclass(frozen=True)
class DriftPolicy:
    binding: str
    state_epoch: str
    max_steps: int = 512
    warning_drift: int = 2500
    cumulative_hold_threshold: int = 9000
    ewma_hold_threshold: int = 4200
    acute_reverse_deny_threshold: int = 6500
    plan_hold_threshold: int = 4500
    ewma_alpha_bp: int = 3000
    revoked: bool = False


@dataclass(frozen=True)
class DriftRequest:
    request_id: str
    original_goal_id: str
    step_history: tuple[str, ...]
    current_plan_id: str
    checkpoint_id: str | None
    binding: str
    state_epoch: str
    evaluation_time: int


@dataclass(frozen=True)
class DriftPoint:
    step_id: str
    drift_score: int
    ewma_score: int
    cumulative_excess: int
    reverse_direction: bool
    warning: bool


@dataclass(frozen=True)
class DriftResult:
    decision: Decision
    reasons: tuple[str, ...]
    drift_curve: tuple[DriftPoint, ...]
    effective_goal_id: str | None
    deviation_step: str | None
    current_plan_drift: int | None
    resync_required: bool
    warning: bool
    next_gate_candidate: bool
    baseline_update_candidate: bool
    # authority negatives
    permission_granted: bool = False
    goal_baseline_mutated: bool = False
    human_approval_executed: bool = False
    tool_executed: bool = False
    transaction_committed: bool = False
    external_write_performed: bool = False
    world_truth_proven: bool = False
    safety_proven: bool = False
    action_success: bool = False


@dataclass(frozen=True)
class PreparedDriftState:
    policy: DriftPolicy
    goals: tuple[GoalSpec, ...]
    steps: tuple[StepRecord, ...]
    plans: tuple[PlanRecord, ...]
    checkpoints: tuple[CheckpointRecord, ...]
    goal_fingerprints: tuple[tuple[str, str], ...]
    step_fingerprints: tuple[tuple[str, str], ...]
    plan_fingerprints: tuple[tuple[str, str], ...]
    checkpoint_fingerprints: tuple[tuple[str, str], ...]
    policy_fingerprint: str
    registry_fingerprint: str
    goal_index: tuple[tuple[str, GoalSpec], ...]
    step_index: tuple[tuple[str, StepRecord], ...]
    plan_index: tuple[tuple[str, PlanRecord], ...]
    checkpoint_index: tuple[tuple[str, CheckpointRecord], ...]
    binding: str
    state_epoch: str


@dataclass(frozen=True)
class DriftRegistryDelta:
    base_fingerprint: str
    target_fingerprint: str
    changed_goals: tuple[GoalSpec, ...]
    removed_goal_ids: tuple[str, ...]
    changed_steps: tuple[StepRecord, ...]
    removed_step_ids: tuple[str, ...]
    changed_plans: tuple[PlanRecord, ...]
    removed_plan_ids: tuple[str, ...]
    changed_checkpoints: tuple[CheckpointRecord, ...]
    removed_checkpoint_ids: tuple[str, ...]
    target_policy: DriftPolicy
    binding: str
    state_epoch: str


@dataclass(frozen=True)
class DriftSyncPlan:
    missing_or_changed_goals: tuple[str, ...]
    missing_or_changed_steps: tuple[str, ...]
    missing_or_changed_plans: tuple[str, ...]
    missing_or_changed_checkpoints: tuple[str, ...]
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


def _norm(xs) -> tuple[str, ...]:
    return tuple(sorted(set(str(x).strip().upper() for x in xs if str(x).strip())))


def _unique_ids(items: Sequence, attr: str) -> bool:
    ids = [getattr(x, attr) for x in items]
    return len(ids) == len(set(ids))


def _registry_fingerprint(policy, goals, steps, plans, checkpoints) -> str:
    return _fp({
        "policy": _fp(policy),
        "goals": sorted((x.goal_id, _fp(x)) for x in goals),
        "steps": sorted((x.step_id, _fp(x)) for x in steps),
        "plans": sorted((x.plan_id, _fp(x)) for x in plans),
        "checkpoints": sorted((x.checkpoint_id, _fp(x)) for x in checkpoints),
    })


def default_policy() -> DriftPolicy:
    return DriftPolicy(binding="DRIFT-BIND", state_epoch="STATE-EPOCH-1")


def default_goals() -> tuple[GoalSpec, ...]:
    b, e = "DRIFT-BIND", "STATE-EPOCH-1"
    return (
        GoalSpec("G-LOCAL-ANALYSIS", ("READ", "ANALYZE", "SUMMARIZE", "PRESERVE"), ("EXTERNAL_SEND", "DELETE", "ESCALATE_AUTH"), b, e),
        GoalSpec("G-EXTERNAL-SHARE", ("READ", "ANALYZE", "EXTERNAL_SEND"), ("DELETE",), b, e),
        GoalSpec("G-PRESERVE", ("READ", "PRESERVE"), ("DELETE",), b, e),
    )


def default_steps(start: int = 1_800_000_000) -> tuple[StepRecord, ...]:
    b, e = "DRIFT-BIND", "STATE-EPOCH-1"
    return (
        StepRecord("S-READ", start, ("READ",), True, b, e),
        StepRecord("S-ANALYZE", start + 10, ("ANALYZE",), True, b, e),
        StepRecord("S-SUMMARY", start + 20, ("SUMMARIZE",), True, b, e),
        StepRecord("S-PRESERVE", start + 30, ("PRESERVE",), True, b, e),
        StepRecord("S-UNRELATED-1", start + 40, ("FORMAT",), True, b, e),
        StepRecord("S-UNRELATED-2", start + 50, ("RENAME",), True, b, e),
        StepRecord("S-UNRELATED-3", start + 60, ("ARCHIVE",), True, b, e),
        StepRecord("S-SEND", start + 70, ("EXTERNAL_SEND",), True, b, e),
        StepRecord("S-DELETE", start + 80, ("DELETE",), True, b, e),
    )


def default_plans() -> tuple[PlanRecord, ...]:
    b, e = "DRIFT-BIND", "STATE-EPOCH-1"
    return (
        PlanRecord("P-STABLE", ("READ", "ANALYZE", "SUMMARIZE"), True, b, e),
        PlanRecord("P-SEND", ("READ", "EXTERNAL_SEND"), True, b, e),
        PlanRecord("P-UNRELATED", ("FORMAT", "RENAME"), True, b, e),
        PlanRecord("P-PRESERVE", ("READ", "PRESERVE"), True, b, e),
    )


def default_checkpoints() -> tuple[CheckpointRecord, ...]:
    b, e = "DRIFT-BIND", "STATE-EPOCH-1"
    return (
        CheckpointRecord("CP-STABLE", "G-LOCAL-ANALYSIS", "S-SUMMARY", True, False, True, True, False, b, e),
        CheckpointRecord("CP-EXTERNAL-COMMITTED", "G-EXTERNAL-SHARE", "S-SUMMARY", True, True, True, True, False, b, e),
    )


def default_request(start: int = 1_800_000_000) -> DriftRequest:
    return DriftRequest("REQ-76", "G-LOCAL-ANALYSIS", ("S-READ", "S-ANALYZE", "S-SUMMARY"), "P-STABLE", None, "DRIFT-BIND", "STATE-EPOCH-1", start + 100)


def _validate_registry(policy, goals, steps, plans, checkpoints) -> tuple[bool, tuple[str, ...]]:
    reasons=[]
    if not isinstance(policy, DriftPolicy): return False, ("INVALID_POLICY_TYPE",)
    if policy.revoked: reasons.append("POLICY_REVOKED")
    if not policy.binding or not policy.state_epoch: reasons.append("POLICY_IDENTITY_MISSING")
    if policy.max_steps <= 0: reasons.append("INVALID_MAX_STEPS")
    vals=(policy.warning_drift,policy.cumulative_hold_threshold,policy.ewma_hold_threshold,policy.acute_reverse_deny_threshold,policy.plan_hold_threshold)
    if any(v < 0 or v > 10000 for v in vals): reasons.append("INVALID_THRESHOLD")
    if not (1 <= policy.ewma_alpha_bp <= 10000): reasons.append("INVALID_EWMA_ALPHA")
    if not _unique_ids(goals,"goal_id"): reasons.append("DUPLICATE_GOAL")
    if not _unique_ids(steps,"step_id"): reasons.append("DUPLICATE_STEP")
    if not _unique_ids(plans,"plan_id"): reasons.append("DUPLICATE_PLAN")
    if not _unique_ids(checkpoints,"checkpoint_id"): reasons.append("DUPLICATE_CHECKPOINT")
    for x in list(goals)+list(steps)+list(plans)+list(checkpoints):
        if getattr(x,"binding",None)!=policy.binding or getattr(x,"state_epoch",None)!=policy.state_epoch:
            reasons.append("REGISTRY_BINDING_MISMATCH"); break
    for g in goals:
        if not g.desired_effects: reasons.append("GOAL_DESIRED_EFFECTS_EMPTY"); break
    goal_ids={g.goal_id for g in goals}
    step_ids={s.step_id for s in steps}
    for cp in checkpoints:
        if cp.goal_id not in goal_ids: reasons.append("CHECKPOINT_GOAL_UNKNOWN"); break
        if cp.through_step_id is not None and cp.through_step_id not in step_ids: reasons.append("CHECKPOINT_STEP_UNKNOWN"); break
    return (not reasons, tuple(sorted(set(reasons))))


def _drift_score(tags: tuple[str,...], goal: GoalSpec) -> tuple[int,bool]:
    obs=set(_norm(tags)); desired=set(_norm(goal.desired_effects)); forbidden=set(_norm(goal.forbidden_effects))
    if not obs: return 10000, False
    conflict=obs & forbidden
    if conflict:
        return min(10000, 6500 + 700*len(conflict)), True
    support=obs & desired
    unrelated=obs - desired - forbidden
    if support:
        # A legitimate step may realize only one part of a long-horizon goal.
        return min(3000, 350*len(unrelated)), False
    return min(6000, 3300 + 400*len(unrelated)), False


def _eval_core(req, policy, goals, steps, plans, checkpoints, *, indexes=None, registry_already_validated=False) -> DriftResult:
    def out(dec,reasons,curve=(),goal=None,step=None,plan=None,resync=False,warn=False,nextg=False,baseline=False):
        return DriftResult(dec,tuple(reasons),tuple(curve),goal,step,plan,resync,warn,nextg,baseline)
    try:
        if not isinstance(req, DriftRequest): return out(Decision.HOLD,("INVALID_TYPED_INPUT",),resync=True)
        if req.binding!=policy.binding or req.state_epoch!=policy.state_epoch: return out(Decision.HOLD,("REQUEST_BINDING_MISMATCH",),resync=True)
        if req.evaluation_time < 0: return out(Decision.HOLD,("INVALID_EVALUATION_TIME",),resync=True)
        if not registry_already_validated:
            ok,rr=_validate_registry(policy,goals,steps,plans,checkpoints)
            if not ok: return out(Decision.HOLD,rr,resync=True)
        if not req.step_history: return out(Decision.HOLD,("STEP_HISTORY_EMPTY",),resync=True)
        if len(req.step_history)>policy.max_steps: return out(Decision.HOLD,("STEP_HISTORY_LIMIT_EXCEEDED",),resync=True)
        if len(set(req.step_history))!=len(req.step_history): return out(Decision.HOLD,("DUPLICATE_STEP_IN_HISTORY",),resync=True)
        if indexes is None:
            gi={x.goal_id:x for x in goals}; si={x.step_id:x for x in steps}; pi={x.plan_id:x for x in plans}; ci={x.checkpoint_id:x for x in checkpoints}
        else: gi,si,pi,ci=indexes
        if req.original_goal_id not in gi: return out(Decision.HOLD,("ORIGINAL_GOAL_UNRECONSTRUCTABLE",),resync=True)
        original_goal=gi[req.original_goal_id]; active_goal=original_goal; post_checkpoint_goal=None; checkpoint_boundary=None; baseline_update_candidate=False
        if req.checkpoint_id:
            cp=ci.get(req.checkpoint_id)
            if cp is None: return out(Decision.HOLD,("CHECKPOINT_UNKNOWN",),resync=True)
            if not cp.observed: return out(Decision.HOLD,("CHECKPOINT_UNOBSERVED",),resync=True)
            if cp.revoked or not cp.valid: return out(Decision.HOLD,("CHECKPOINT_INVALID",),resync=True)
            if cp.externally_committed_goal_change:
                if not cp.independent_authority: return out(Decision.HOLD,("CHECKPOINT_AUTHORITY_NOT_INDEPENDENT",),resync=True)
                post_checkpoint_goal=gi.get(cp.goal_id)
                if post_checkpoint_goal is None: return out(Decision.HOLD,("CHECKPOINT_GOAL_UNRECONSTRUCTABLE",),resync=True)
                if not cp.through_step_id or cp.through_step_id not in req.step_history:
                    return out(Decision.HOLD,("CHECKPOINT_BOUNDARY_NOT_RECONSTRUCTABLE",),resync=True)
                checkpoint_boundary=cp.through_step_id
                baseline_update_candidate=True
            elif cp.goal_id != req.original_goal_id:
                return out(Decision.HOLD,("UNCOMMITTED_GOAL_CHANGE_AT_CHECKPOINT",),resync=True)
        curve=[]; ewma=0; cumulative=0; warning=False; last_ts=None; boundary_passed=False
        for sid in req.step_history:
            s=si.get(sid)
            if s is None: return out(Decision.HOLD,("STEP_UNKNOWN",sid),curve,goal.goal_id,sid,resync=True,warn=warning,baseline=baseline_update_candidate)
            if not s.observed: return out(Decision.HOLD,("STEP_UNOBSERVED",sid),curve,goal.goal_id,sid,resync=True,warn=warning,baseline=baseline_update_candidate)
            if s.timestamp>req.evaluation_time: return out(Decision.HOLD,("STEP_FROM_FUTURE",sid),curve,goal.goal_id,sid,resync=True,warn=warning,baseline=baseline_update_candidate)
            if last_ts is not None and s.timestamp<last_ts: return out(Decision.HOLD,("STEP_TIME_ORDER_INVALID",sid),curve,goal.goal_id,sid,resync=True,warn=warning,baseline=baseline_update_candidate)
            last_ts=s.timestamp
            score,rev=_drift_score(s.effect_tags,active_goal)
            alpha=policy.ewma_alpha_bp
            ewma=(alpha*score + (10000-alpha)*ewma + 5000)//10000
            excess=max(0,score-policy.warning_drift); cumulative=min(100000,cumulative+excess)
            w=score>=policy.warning_drift; warning=warning or w
            curve.append(DriftPoint(sid,score,ewma,cumulative,rev,w))
            if rev and score>=policy.acute_reverse_deny_threshold:
                return out(Decision.DENY,("ACUTE_REVERSE_GOAL_DRIFT",sid),curve,active_goal.goal_id,sid,resync=True,warn=True,baseline=baseline_update_candidate)
            if cumulative>=policy.cumulative_hold_threshold:
                return out(Decision.HOLD,("CUMULATIVE_GOAL_DRIFT_THRESHOLD_EXCEEDED",sid),curve,active_goal.goal_id,sid,resync=True,warn=True,baseline=baseline_update_candidate)
            if ewma>=policy.ewma_hold_threshold:
                return out(Decision.HOLD,("EWMA_GOAL_DRIFT_THRESHOLD_EXCEEDED",sid),curve,active_goal.goal_id,sid,resync=True,warn=True,baseline=baseline_update_candidate)
            if checkpoint_boundary is not None and sid==checkpoint_boundary:
                boundary_passed=True
                active_goal=post_checkpoint_goal
                ewma=0
                cumulative=0
        if checkpoint_boundary is not None and not boundary_passed:
            return out(Decision.HOLD,("CHECKPOINT_BOUNDARY_NOT_REACHED",),curve,active_goal.goal_id,resync=True,warn=warning,baseline=baseline_update_candidate)
        plan=pi.get(req.current_plan_id)
        if plan is None: return out(Decision.HOLD,("CURRENT_PLAN_UNKNOWN",),curve,goal.goal_id,resync=True,warn=warning,baseline=baseline_update_candidate)
        if not plan.observed: return out(Decision.HOLD,("CURRENT_PLAN_UNOBSERVED",),curve,goal.goal_id,resync=True,warn=warning,baseline=baseline_update_candidate)
        pscore,prev=_drift_score(plan.effect_tags,active_goal)
        if prev and pscore>=policy.acute_reverse_deny_threshold:
            return out(Decision.DENY,("CURRENT_PLAN_REVERSES_GOAL",),curve,active_goal.goal_id,req.current_plan_id,pscore,True,True,False,baseline_update_candidate)
        if pscore>=policy.plan_hold_threshold:
            return out(Decision.HOLD,("CURRENT_PLAN_DRIFT_HIGH",),curve,active_goal.goal_id,req.current_plan_id,pscore,True,True,False,baseline_update_candidate)
        reasons=["GOAL_DRIFT_WITHIN_POLICY"]
        if warning: reasons.append("TEMPORARY_DRIFT_WARNING")
        if baseline_update_candidate: reasons.append("EXTERNAL_COMMITTED_CHECKPOINT_BASELINE_EVIDENCE_USED")
        return out(Decision.ALLOW,reasons,curve,active_goal.goal_id,None,pscore,False,warning,True,baseline_update_candidate)
    except Exception:
        return out(Decision.HOLD,("INVALID_TYPED_INPUT",),resync=True)


def evaluate(req: DriftRequest, policy: DriftPolicy, goals: Sequence[GoalSpec], steps: Sequence[StepRecord], plans: Sequence[PlanRecord], checkpoints: Sequence[CheckpointRecord]=()) -> DriftResult:
    return _eval_core(req,policy,tuple(goals),tuple(steps),tuple(plans),tuple(checkpoints))


def prepare_state(policy, goals, steps, plans, checkpoints=(), *, binding: str) -> PreparedDriftState:
    goals,steps,plans,checkpoints=tuple(goals),tuple(steps),tuple(plans),tuple(checkpoints)
    ok,reasons=_validate_registry(policy,goals,steps,plans,checkpoints)
    if not ok or binding!=policy.binding: raise ValueError("invalid registry: "+",".join(reasons))
    gf=tuple(sorted((x.goal_id,_fp(x)) for x in goals)); sf=tuple(sorted((x.step_id,_fp(x)) for x in steps)); pf=tuple(sorted((x.plan_id,_fp(x)) for x in plans)); cf=tuple(sorted((x.checkpoint_id,_fp(x)) for x in checkpoints))
    reg=_registry_fingerprint(policy,goals,steps,plans,checkpoints)
    return PreparedDriftState(policy,goals,steps,plans,checkpoints,gf,sf,pf,cf,_fp(policy),reg,tuple(sorted((x.goal_id,x) for x in goals)),tuple(sorted((x.step_id,x) for x in steps)),tuple(sorted((x.plan_id,x) for x in plans)),tuple(sorted((x.checkpoint_id,x) for x in checkpoints)),binding,policy.state_epoch)


def validate_prepared_integrity(st: PreparedDriftState) -> bool:
    try:
        if st.binding!=st.policy.binding or st.state_epoch!=st.policy.state_epoch: return False
        if _fp(st.policy)!=st.policy_fingerprint: return False
        if tuple(sorted((x.goal_id,_fp(x)) for x in st.goals))!=st.goal_fingerprints: return False
        if tuple(sorted((x.step_id,_fp(x)) for x in st.steps))!=st.step_fingerprints: return False
        if tuple(sorted((x.plan_id,_fp(x)) for x in st.plans))!=st.plan_fingerprints: return False
        if tuple(sorted((x.checkpoint_id,_fp(x)) for x in st.checkpoints))!=st.checkpoint_fingerprints: return False
        if tuple(sorted((x.goal_id,x) for x in st.goals))!=st.goal_index: return False
        if tuple(sorted((x.step_id,x) for x in st.steps))!=st.step_index: return False
        if tuple(sorted((x.plan_id,x) for x in st.plans))!=st.plan_index: return False
        if tuple(sorted((x.checkpoint_id,x) for x in st.checkpoints))!=st.checkpoint_index: return False
        return _registry_fingerprint(st.policy,st.goals,st.steps,st.plans,st.checkpoints)==st.registry_fingerprint
    except Exception: return False


def evaluate_prepared(req: DriftRequest, st: PreparedDriftState, *, current_policy_fingerprint: str, current_registry_fingerprint: str, prepared_integrity_validated: bool) -> DriftResult:
    if not prepared_integrity_validated:
        return DriftResult(Decision.HOLD,("PREPARED_INTEGRITY_NOT_VALIDATED",),(),None,None,None,True,False,False,False)
    if current_policy_fingerprint!=st.policy_fingerprint:
        return DriftResult(Decision.HOLD,("POLICY_FINGERPRINT_CHANGED",),(),None,None,None,True,False,False,False)
    if current_registry_fingerprint!=st.registry_fingerprint:
        return DriftResult(Decision.HOLD,("REGISTRY_FINGERPRINT_CHANGED",),(),None,None,None,True,False,False,False)
    indexes=(dict(st.goal_index),dict(st.step_index),dict(st.plan_index),dict(st.checkpoint_index))
    return _eval_core(req,st.policy,st.goals,st.steps,st.plans,st.checkpoints,indexes=indexes,registry_already_validated=True)


def make_delta(base: PreparedDriftState, target: PreparedDriftState) -> DriftRegistryDelta:
    if not validate_prepared_integrity(base) or not validate_prepared_integrity(target): raise ValueError("invalid prepared state")
    if base.binding!=target.binding or base.state_epoch!=target.state_epoch: raise ValueError("identity mismatch")
    def changes(base_items,target_items,key):
        b={key(x):_fp(x) for x in base_items}; t={key(x):x for x in target_items}
        return tuple(t[k] for k in sorted(t) if b.get(k)!=_fp(t[k])), tuple(sorted(set(b)-set(t)))
    cg,rg=changes(base.goals,target.goals,lambda x:x.goal_id); cs,rs=changes(base.steps,target.steps,lambda x:x.step_id); cp,rp=changes(base.plans,target.plans,lambda x:x.plan_id); cc,rc=changes(base.checkpoints,target.checkpoints,lambda x:x.checkpoint_id)
    return DriftRegistryDelta(base.registry_fingerprint,target.registry_fingerprint,cg,rg,cs,rs,cp,rp,cc,rc,target.policy,target.binding,target.state_epoch)


def apply_delta(base: PreparedDriftState, delta: DriftRegistryDelta) -> PreparedDriftState:
    if not validate_prepared_integrity(base) or base.registry_fingerprint!=delta.base_fingerprint: raise ValueError("base mismatch")
    def patch(items,changed,removed,key):
        d={key(x):x for x in items}
        for k in removed: d.pop(k,None)
        for x in changed: d[key(x)]=x
        return tuple(d[k] for k in sorted(d))
    st=prepare_state(delta.target_policy,patch(base.goals,delta.changed_goals,delta.removed_goal_ids,lambda x:x.goal_id),patch(base.steps,delta.changed_steps,delta.removed_step_ids,lambda x:x.step_id),patch(base.plans,delta.changed_plans,delta.removed_plan_ids,lambda x:x.plan_id),patch(base.checkpoints,delta.changed_checkpoints,delta.removed_checkpoint_ids,lambda x:x.checkpoint_id),binding=delta.binding)
    if st.registry_fingerprint!=delta.target_fingerprint: raise ValueError("target fingerprint mismatch")
    return st


def missing_only_sync_plan(st: PreparedDriftState, remote_goal_fps: Mapping[str,str], remote_step_fps: Mapping[str,str], remote_plan_fps: Mapping[str,str], remote_checkpoint_fps: Mapping[str,str]) -> DriftSyncPlan:
    if not validate_prepared_integrity(st): return DriftSyncPlan((),(),(),(),0,True)
    def miss(local,remote): return tuple(k for k,v in local if remote.get(k)!=v)
    mg=miss(st.goal_fingerprints,remote_goal_fps); ms=miss(st.step_fingerprints,remote_step_fps); mp=miss(st.plan_fingerprints,remote_plan_fps); mc=miss(st.checkpoint_fingerprints,remote_checkpoint_fps)
    meta=len(_canon({"g":mg,"s":ms,"p":mp,"c":mc,"base":st.registry_fingerprint}))
    return DriftSyncPlan(mg,ms,mp,mc,meta,False)


def full_registry_bytes(st: PreparedDriftState) -> int:
    return len(_canon({"policy":st.policy,"goals":st.goals,"steps":st.steps,"plans":st.plans,"checkpoints":st.checkpoints}))


def delta_bytes(delta: DriftRegistryDelta) -> int:
    return len(_canon(delta))
