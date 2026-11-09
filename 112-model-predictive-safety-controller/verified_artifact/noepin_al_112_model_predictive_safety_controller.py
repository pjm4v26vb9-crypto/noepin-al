"""NOEPIN AL 112 — Model-Predictive Safety Controller — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Pure deterministic MPC-style receding-horizon control evidence. The controller predicts
short-horizon trajectories from typed effect models, rejects hard-constraint violations
before optimization, then ranks remaining candidates by goal/risk cost. Only the first
action is returned as a next-gate candidate; no action is executed. If no safe trajectory
exists, model uncertainty is too high, or constraint margin is insufficient, the result
fails safe to HOLD / Safe Mode / Authority Reduction candidacy.

Canonical identity: NOEPIN-AL-112
DCSR level: AUXILIARY INTEGRATION / 補助統合.
Provenance note: exact registered Origin GUID was not freshly reverified in this
completion session and is intentionally not guessed or regenerated.
Pre-existing Notion V1 attachment byte identity was not freshly reverified.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str, Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class NextAction(str, Enum):
    SAFE_ACTION_CANDIDATE='SAFE_ACTION_CANDIDATE'
    AUTHORITY_REDUCTION_CANDIDATE='AUTHORITY_REDUCTION_CANDIDATE'
    SAFE_MODE_CANDIDATE='SAFE_MODE_CANDIDATE'
    HOLD_REPLAN_CANDIDATE='HOLD_REPLAN_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; NO_SAFE_TRAJECTORY='NO_SAFE_TRAJECTORY'; LOW_CONSTRAINT_MARGIN='LOW_CONSTRAINT_MARGIN'; MODEL_UNCERTAINTY='MODEL_UNCERTAINTY'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'

@dataclass(frozen=True)
class GoalTarget:
    field: str
    target: float
    weight: float
    target_version: str
    target_fingerprint: str
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class HardConstraint:
    constraint_id: str
    field: str
    minimum: float
    maximum: float
    constraint_version: str
    constraint_fingerprint: str
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class ActionEffectModel:
    action_id: str
    deltas: tuple[tuple[str,float],...]
    risk_cost: float
    model_uncertainty: float
    effect_version: str
    effect_fingerprint: str
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class MPCRequest:
    request_id: str
    current_state: tuple[tuple[str,float],...]
    actions: tuple[ActionEffectModel,...]
    goals: tuple[GoalTarget,...]
    constraints: tuple[HardConstraint,...]
    horizon: int
    max_model_uncertainty: float
    minimum_constraint_margin: float
    risk_weight: float
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class TrajectoryCandidate:
    action_id: str
    predicted_trajectory: tuple[tuple[tuple[str,float],...],...]
    constraint_margin: float
    goal_cost: float
    risk_cost: float
    model_uncertainty: float
    horizon_used: int
    horizon_shortened: bool
    objective_cost: float

@dataclass(frozen=True)
class MPCResult:
    decision: Decision
    next_action: NextAction
    escalation: Escalation
    reasons: tuple[str,...]
    selected_action_candidate: str|None
    predicted_trajectory: tuple[tuple[tuple[str,float],...],...]
    constraint_margin: float|None
    model_uncertainty: float|None
    horizon_used: int
    horizon_shortened: bool
    safe_trajectory_found: bool
    hard_constraints_preserved: bool
    authority_reduced: bool
    next_gate_candidate: bool
    action_promoted_to_permission: bool=False
    permission_granted: bool=False
    approval_executed: bool=False
    authority_granted: bool=False
    action_executed: bool=False
    plan_committed: bool=False
    publish_executed: bool=False
    external_write_performed: bool=False
    world_truth_proven: bool=False
    domain_authority_promoted: bool=False
    safety_proven: bool=False
    action_success: bool=False

@dataclass(frozen=True)
class PreparedMPCState:
    request: MPCRequest
    action_fingerprints: tuple[tuple[str,str],...]
    constraint_fingerprints: tuple[tuple[str,str],...]
    goal_fingerprints: tuple[tuple[str,str],...]
    context_fingerprint: str
    dynamics_fingerprint: str
    constraint_fingerprint: str
    policy_fingerprint: str
    registry_fingerprint: str
    frontier_fingerprint: str
    precomputed_result: MPCResult
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class MPCStateDelta:
    base_registry_fingerprint: str
    target_registry_fingerprint: str
    changed_actions: tuple[ActionEffectModel,...]
    changed_constraints: tuple[HardConstraint,...]
    changed_goals: tuple[GoalTarget,...]
    removed_record_ids: tuple[str,...]
    current_state_replacement: tuple[tuple[str,float],...]|None
    horizon_replacement: int|None
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class MPCSyncPlan:
    missing_or_changed_record_ids: tuple[str,...]
    metadata_bytes_required: int
    full_resend_required: bool


def _j(v):
    if isinstance(v,Enum): return v.value
    if is_dataclass(v): return {f.name:_j(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v,dict): return {str(k):_j(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(tuple,list)): return [_j(x) for x in v]
    if isinstance(v,float):
        if not math.isfinite(v): return str(v)
        return float(format(v,'.15g'))
    return v

def _canon(v): return json.dumps(_j(v),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
def _fp(v): return sha256(_canon(v)).hexdigest()
def _finite(v): return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(float(v))

def _hold(reason, escalation=Escalation.INVALID_CONFIGURATION, next_action=NextAction.HOLD_REPLAN_CANDIDATE):
    return MPCResult(Decision.HOLD,next_action,escalation,(reason,),None,(),None,None,0,False,False,False,False,False)

def _validate(req:MPCRequest):
    if not isinstance(req,MPCRequest): return 'TYPE_INVALID',Escalation.INVALID_CONFIGURATION
    if not req.request_id or not req.binding or not req.state_epoch: return 'REQUEST_INVALID',Escalation.INVALID_CONFIGURATION
    if not isinstance(req.horizon,int) or req.horizon<=0: return 'HORIZON_INVALID',Escalation.INVALID_CONFIGURATION
    if not _finite(req.max_model_uncertainty) or req.max_model_uncertainty<=0: return 'MODEL_UNCERTAINTY_BOUND_INVALID',Escalation.INVALID_CONFIGURATION
    if not _finite(req.minimum_constraint_margin) or req.minimum_constraint_margin<0: return 'CONSTRAINT_MARGIN_INVALID',Escalation.INVALID_CONFIGURATION
    if not _finite(req.risk_weight) or req.risk_weight<0: return 'RISK_WEIGHT_INVALID',Escalation.INVALID_CONFIGURATION
    if not req.actions: return 'ACTIONS_MISSING',Escalation.INVALID_CONFIGURATION
    if not req.goals: return 'GOALS_MISSING',Escalation.INVALID_CONFIGURATION
    if not req.constraints: return 'CONSTRAINTS_MISSING',Escalation.INVALID_CONFIGURATION
    state=dict(req.current_state)
    if len(state)!=len(req.current_state) or not state or any(not k or not _finite(v) for k,v in req.current_state): return 'CURRENT_STATE_INVALID',Escalation.INVALID_CONFIGURATION
    aids=[a.action_id for a in req.actions]
    if len(aids)!=len(set(aids)): return 'DUPLICATE_ACTION_ID',Escalation.INVALID_CONFIGURATION
    cids=[c.constraint_id for c in req.constraints]
    if len(cids)!=len(set(cids)): return 'DUPLICATE_CONSTRAINT_ID',Escalation.INVALID_CONFIGURATION
    gfields=[g.field for g in req.goals]
    if len(gfields)!=len(set(gfields)): return 'DUPLICATE_GOAL_FIELD',Escalation.INVALID_CONFIGURATION
    for a in req.actions:
        if not isinstance(a,ActionEffectModel) or not a.action_id or a.binding!=req.binding or a.state_epoch!=req.state_epoch: return 'ACTION_INVALID',Escalation.INVALID_CONFIGURATION
        if not _finite(a.risk_cost) or a.risk_cost<0 or not _finite(a.model_uncertainty) or a.model_uncertainty<0: return 'ACTION_COST_INVALID',Escalation.INVALID_CONFIGURATION
        d=dict(a.deltas)
        if len(d)!=len(a.deltas) or not d or any(k not in state or not _finite(v) for k,v in a.deltas): return 'ACTION_DELTA_INVALID',Escalation.INVALID_CONFIGURATION
    for g in req.goals:
        if not isinstance(g,GoalTarget) or g.binding!=req.binding or g.state_epoch!=req.state_epoch or g.field not in state or not _finite(g.target) or not _finite(g.weight) or g.weight<=0: return 'GOAL_INVALID',Escalation.INVALID_CONFIGURATION
    for c in req.constraints:
        if not isinstance(c,HardConstraint) or not c.constraint_id or c.binding!=req.binding or c.state_epoch!=req.state_epoch or c.field not in state: return 'CONSTRAINT_INVALID',Escalation.INVALID_CONFIGURATION
        if not _finite(c.minimum) or not _finite(c.maximum) or c.minimum>c.maximum: return 'CONSTRAINT_BOUNDS_INVALID',Escalation.INVALID_CONFIGURATION
    return None,None

def _constraint_margin(state, constraints):
    margin=math.inf
    for c in constraints:
        v=float(state[c.field]); margin=min(margin,v-float(c.minimum),float(c.maximum)-v)
    return margin

def _predict(req:MPCRequest, action:ActionEffectModel):
    # A one-step effect model is rolled forward only within an uncertainty-qualified horizon.
    if action.model_uncertainty>req.max_model_uncertainty: return None,'MODEL_UNCERTAINTY_EXCEEDS_BOUND'
    if action.model_uncertainty==0:
        h=req.horizon
    else:
        h=min(req.horizon,max(1,int(math.floor(req.max_model_uncertainty/action.model_uncertainty))))
    shortened=h<req.horizon
    state={k:float(v) for k,v in req.current_state}; delta=dict(action.deltas); traj=[]; margin=math.inf
    # Current state itself must satisfy hard constraints.
    margin=min(margin,_constraint_margin(state,req.constraints))
    if margin<0: return None,'CURRENT_STATE_HARD_CONSTRAINT_VIOLATION'
    for _ in range(h):
        for k,d in delta.items(): state[k]=state[k]+float(d)
        m=_constraint_margin(state,req.constraints); margin=min(margin,m)
        if m<0: return None,'PREDICTED_HARD_CONSTRAINT_VIOLATION'
        traj.append(tuple(sorted((k,float(format(v,'.15g'))) for k,v in state.items())))
    goal_cost=sum(abs(state[g.field]-float(g.target))*float(g.weight) for g in req.goals)
    objective=goal_cost + req.risk_weight*float(action.risk_cost) + float(action.model_uncertainty)*h
    return TrajectoryCandidate(action.action_id,tuple(traj),float(format(margin,'.15g')),float(format(goal_cost,'.15g')),action.risk_cost,action.model_uncertainty,h,shortened,float(format(objective,'.15g'))),None

def evaluate(req:MPCRequest)->MPCResult:
    err,esc=_validate(req)
    if err: return _hold(err,esc)
    candidates=[]; reject_reasons=[]
    for a in sorted(req.actions,key=lambda x:x.action_id):
        c,r=_predict(req,a)
        if c is not None: candidates.append(c)
        else: reject_reasons.append((a.action_id,r))
    if not candidates:
        only_uncertainty=bool(reject_reasons) and all(r=='MODEL_UNCERTAINTY_EXCEEDS_BOUND' for _,r in reject_reasons)
        if only_uncertainty:
            return _hold('NO_UNCERTAINTY_QUALIFIED_TRAJECTORY',Escalation.MODEL_UNCERTAINTY,NextAction.SAFE_MODE_CANDIDATE)
        return _hold('NO_SAFE_TRAJECTORY',Escalation.NO_SAFE_TRAJECTORY,NextAction.SAFE_MODE_CANDIDATE)
    candidates.sort(key=lambda c:(c.objective_cost,c.risk_cost,-c.constraint_margin,c.action_id))
    best=candidates[0]
    reasons=['SAFE_TRAJECTORY_FOUND','HARD_CONSTRAINTS_PRESERVED','FIRST_ACTION_ONLY_CANDIDATE']
    if best.horizon_shortened: reasons.append('HORIZON_SHORTENED_FOR_MODEL_UNCERTAINTY')
    if best.constraint_margin < req.minimum_constraint_margin:
        reasons.append('CONSTRAINT_MARGIN_BELOW_REQUIRED_THRESHOLD')
        return MPCResult(Decision.HUMAN_APPROVAL,NextAction.AUTHORITY_REDUCTION_CANDIDATE,Escalation.LOW_CONSTRAINT_MARGIN,tuple(reasons),best.action_id,best.predicted_trajectory,best.constraint_margin,best.model_uncertainty,best.horizon_used,best.horizon_shortened,True,True,True,True)
    return MPCResult(Decision.ALLOW,NextAction.SAFE_ACTION_CANDIDATE,Escalation.NONE,tuple(reasons),best.action_id,best.predicted_trajectory,best.constraint_margin,best.model_uncertainty,best.horizon_used,best.horizon_shortened,True,True,False,True)

def default_request():
    b='MPC-BIND'; e='STATE-EPOCH-1'
    state=(('load',40.0),('reserve',80.0),('temperature',50.0))
    goals=(GoalTarget('temperature',56.0,1.0,'V1','FP-G-TEMP',b,e),GoalTarget('load',43.0,1.0,'V1','FP-G-LOAD',b,e))
    constraints=(HardConstraint('C:TEMP','temperature',0.0,100.0,'V1','FP-C-TEMP',b,e),HardConstraint('C:LOAD','load',0.0,100.0,'V1','FP-C-LOAD',b,e),HardConstraint('C:RESERVE','reserve',20.0,100.0,'V1','FP-C-RESERVE',b,e))
    actions=(
        ActionEffectModel('SAFE_ADJUST',(('load',1.0),('reserve',-1.0),('temperature',2.0)),0.2,0.10,'V1','FP-A-SAFE',b,e),
        ActionEffectModel('FAST_ADJUST',(('load',8.0),('reserve',-5.0),('temperature',8.0)),2.0,0.25,'V1','FP-A-FAST',b,e),
        ActionEffectModel('COOL',(('load',0.0),('reserve',-0.5),('temperature',-4.0)),0.4,0.08,'V1','FP-A-COOL',b,e),
    )
    return MPCRequest('REQ-112',state,actions,goals,constraints,3,1.0,10.0,1.0,b,e)

def default_evaluation(): return evaluate(default_request())

def _action_fps(req): return tuple((f'ACTION:{a.action_id}',_fp(a)) for a in sorted(req.actions,key=lambda x:x.action_id))
def _constraint_fps(req): return tuple((f'CONSTRAINT:{c.constraint_id}',_fp(c)) for c in sorted(req.constraints,key=lambda x:x.constraint_id))
def _goal_fps(req): return tuple((f'GOAL:{g.field}',_fp(g)) for g in sorted(req.goals,key=lambda x:x.field))
def _context_fp(req): return _fp((tuple(sorted(req.current_state)),req.horizon,req.binding,req.state_epoch))
def _dynamics_fp(req): return _fp(_action_fps(req))
def _constraint_fp(req): return _fp(_constraint_fps(req))
def _policy_fp(req): return _fp(('HARD_CONSTRAINT_PRECEDENCE','FIRST_ACTION_ONLY','NO_EXECUTION',req.max_model_uncertainty,req.minimum_constraint_margin,req.risk_weight))
def _registry_fp(req): return _fp((_action_fps(req),_constraint_fps(req),_goal_fps(req),tuple(sorted(req.current_state)),req.horizon))
def _frontier_fp(req): return _fp(evaluate(req))

def prepare_state(req,*,binding,state_epoch):
    return PreparedMPCState(req,_action_fps(req),_constraint_fps(req),_goal_fps(req),_context_fp(req),_dynamics_fp(req),_constraint_fp(req),_policy_fp(req),_registry_fp(req),_frontier_fp(req),evaluate(req),binding,state_epoch)
def validate_prepared_integrity(st):
    q=st.request
    return (st.binding==q.binding and st.state_epoch==q.state_epoch and st.action_fingerprints==_action_fps(q) and st.constraint_fingerprints==_constraint_fps(q) and st.goal_fingerprints==_goal_fps(q) and st.context_fingerprint==_context_fp(q) and st.dynamics_fingerprint==_dynamics_fp(q) and st.constraint_fingerprint==_constraint_fp(q) and st.policy_fingerprint==_policy_fp(q) and st.registry_fingerprint==_registry_fp(q) and st.frontier_fingerprint==_frontier_fp(q) and st.precomputed_result==evaluate(q))
def evaluate_prepared(st,*,integrity_validated,current_context_fingerprint,current_dynamics_fingerprint,current_constraint_fingerprint,current_policy_fingerprint,current_registry_fingerprint,current_frontier_fingerprint):
    if not integrity_validated: return _hold('PREPARED_INTEGRITY_NOT_VALIDATED')
    if (st.context_fingerprint!=current_context_fingerprint or st.dynamics_fingerprint!=current_dynamics_fingerprint or st.constraint_fingerprint!=current_constraint_fingerprint or st.policy_fingerprint!=current_policy_fingerprint or st.registry_fingerprint!=current_registry_fingerprint or st.frontier_fingerprint!=current_frontier_fingerprint):
        return _hold('PREPARED_FINGERPRINT_MISMATCH_REEVALUATION_REQUIRED')
    return st.precomputed_result

def make_delta(base,target):
    ba=dict(base.action_fingerprints); ta=dict(target.action_fingerprints); bc=dict(base.constraint_fingerprints); tc=dict(target.constraint_fingerprints); bg=dict(base.goal_fingerprints); tg=dict(target.goal_fingerprints)
    amap={f'ACTION:{a.action_id}':a for a in target.request.actions}; cmap={f'CONSTRAINT:{c.constraint_id}':c for c in target.request.constraints}; gmap={f'GOAL:{g.field}':g for g in target.request.goals}
    ca=tuple(amap[k] for k,v in ta.items() if ba.get(k)!=v); cc=tuple(cmap[k] for k,v in tc.items() if bc.get(k)!=v); cg=tuple(gmap[k] for k,v in tg.items() if bg.get(k)!=v)
    removed=tuple(sorted([k for k in ba if k not in ta]+[k for k in bc if k not in tc]+[k for k in bg if k not in tg]))
    cs=target.request.current_state if tuple(sorted(base.request.current_state))!=tuple(sorted(target.request.current_state)) else None
    hr=target.request.horizon if base.request.horizon!=target.request.horizon else None
    return MPCStateDelta(base.registry_fingerprint,target.registry_fingerprint,ca,cc,cg,removed,cs,hr,target.binding,target.state_epoch)
def plan_missing_only(local,target):
    lm=dict(local.action_fingerprints+local.constraint_fingerprints+local.goal_fingerprints); tm=dict(target.action_fingerprints+target.constraint_fingerprints+target.goal_fingerprints)
    ids=[k for k,v in tm.items() if lm.get(k)!=v]
    if tuple(sorted(local.request.current_state))!=tuple(sorted(target.request.current_state)): ids.append('META:CURRENT_STATE')
    if local.request.horizon!=target.request.horizon: ids.append('META:HORIZON')
    ids=tuple(sorted(ids)); return MPCSyncPlan(ids,len(_canon(ids)),False)
