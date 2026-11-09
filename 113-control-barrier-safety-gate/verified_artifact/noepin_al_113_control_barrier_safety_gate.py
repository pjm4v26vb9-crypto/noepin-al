"""NOEPIN AL 113 — Control-Barrier Safety Gate — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Pure deterministic discrete control-barrier evidence. A candidate action is projected by a
supplied typed dynamics approximation, hard safety barriers are evaluated before any
preference/repair ranking, and an unsafe candidate is denied. If a supplied alternative
can remain inside the invariant set with adequate margin, it is returned only as a
Corrected Action Candidate. No action is executed and no permission/authority is granted.
Unknown state, safety function, stale bindings, invalid dynamics, or model uncertainty
fail safe to HOLD.

Canonical identity: NOEPIN-AL-113
DCSR level: AUXILIARY INTEGRATION / 補助統合.
Provenance note: exact registered Origin GUID was not freshly reverified in this
completion session and is intentionally not guessed or regenerated.
Pre-existing Notion V1 attachment byte identity was not freshly reverified.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str, Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class NextAction(str, Enum):
    SAFE_ACTION_CANDIDATE='SAFE_ACTION_CANDIDATE'
    CORRECTED_ACTION_CANDIDATE='CORRECTED_ACTION_CANDIDATE'
    AUTHORITY_REDUCTION_CANDIDATE='AUTHORITY_REDUCTION_CANDIDATE'
    HOLD_REPLAN_CANDIDATE='HOLD_REPLAN_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; BARRIER_VIOLATION='BARRIER_VIOLATION'; LOW_BARRIER_MARGIN='LOW_BARRIER_MARGIN'; UNKNOWN_STATE='UNKNOWN_STATE'; MODEL_UNCERTAINTY='MODEL_UNCERTAINTY'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'

@dataclass(frozen=True)
class SafetyBarrier:
    barrier_id: str
    field: str
    minimum: float
    maximum: float
    minimum_margin: float
    barrier_version: str
    barrier_fingerprint: str
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class ActionDynamics:
    action_id: str
    deltas: tuple[tuple[str,float],...]
    model_uncertainty: float
    correction_cost: float
    dynamics_version: str
    dynamics_fingerprint: str
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class BarrierRequest:
    request_id: str
    current_state: tuple[tuple[str,float],...]
    candidate_action_id: str
    actions: tuple[ActionDynamics,...]
    barriers: tuple[SafetyBarrier,...]
    max_model_uncertainty: float
    allow_correction_search: bool
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class BarrierEvaluation:
    action_id: str
    predicted_state: tuple[tuple[str,float],...]
    current_barrier_margin: float
    predicted_barrier_margin: float
    barrier_rate: float
    violating_barrier_ids: tuple[str,...]
    low_margin_barrier_ids: tuple[str,...]
    model_uncertainty: float
    correction_cost: float

@dataclass(frozen=True)
class BarrierResult:
    decision: Decision
    next_action: NextAction
    escalation: Escalation
    reasons: tuple[str,...]
    candidate_action_id: str|None
    corrected_action_candidate: str|None
    predicted_state: tuple[tuple[str,float],...]
    barrier_margin: float|None
    barrier_rate: float|None
    safe_set_preserved: bool
    correction_available: bool
    authority_reduced: bool
    next_gate_candidate: bool
    candidate_promoted_to_permission: bool=False
    corrected_action_promoted_to_permission: bool=False
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
class PreparedBarrierState:
    request: BarrierRequest
    action_fingerprints: tuple[tuple[str,str],...]
    barrier_fingerprints: tuple[tuple[str,str],...]
    context_fingerprint: str
    dynamics_fingerprint: str
    safety_fingerprint: str
    policy_fingerprint: str
    registry_fingerprint: str
    evaluation_fingerprint: str
    precomputed_result: BarrierResult
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class BarrierStateDelta:
    base_registry_fingerprint: str
    target_registry_fingerprint: str
    changed_actions: tuple[ActionDynamics,...]
    changed_barriers: tuple[SafetyBarrier,...]
    removed_record_ids: tuple[str,...]
    current_state_replacement: tuple[tuple[str,float],...]|None
    candidate_action_replacement: str|None
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class BarrierSyncPlan:
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
def _hold(reason, escalation=Escalation.INVALID_CONFIGURATION):
    return BarrierResult(Decision.HOLD,NextAction.HOLD_REPLAN_CANDIDATE,escalation,(reason,),None,None,(),None,None,False,False,False,False)

def _validate(req:BarrierRequest):
    if not isinstance(req,BarrierRequest): return 'TYPE_INVALID',Escalation.INVALID_CONFIGURATION
    if not req.request_id or not req.binding or not req.state_epoch: return 'REQUEST_INVALID',Escalation.INVALID_CONFIGURATION
    if not isinstance(req.allow_correction_search,bool): return 'CORRECTION_POLICY_INVALID',Escalation.INVALID_CONFIGURATION
    if not _finite(req.max_model_uncertainty) or req.max_model_uncertainty<0: return 'MODEL_UNCERTAINTY_BOUND_INVALID',Escalation.INVALID_CONFIGURATION
    if not req.candidate_action_id or not req.actions: return 'ACTIONS_MISSING',Escalation.INVALID_CONFIGURATION
    if not req.barriers: return 'SAFETY_FUNCTION_MISSING',Escalation.UNKNOWN_STATE
    state=dict(req.current_state)
    if len(state)!=len(req.current_state) or not state or any(not k or not _finite(v) for k,v in req.current_state): return 'CURRENT_STATE_UNKNOWN',Escalation.UNKNOWN_STATE
    aids=[a.action_id for a in req.actions]
    if len(aids)!=len(set(aids)): return 'DUPLICATE_ACTION_ID',Escalation.INVALID_CONFIGURATION
    if req.candidate_action_id not in set(aids): return 'CANDIDATE_ACTION_UNKNOWN',Escalation.UNKNOWN_STATE
    bids=[b.barrier_id for b in req.barriers]
    if len(bids)!=len(set(bids)): return 'DUPLICATE_BARRIER_ID',Escalation.INVALID_CONFIGURATION
    for a in req.actions:
        if not isinstance(a,ActionDynamics) or not a.action_id or a.binding!=req.binding or a.state_epoch!=req.state_epoch: return 'ACTION_DYNAMICS_INVALID',Escalation.INVALID_CONFIGURATION
        if not _finite(a.model_uncertainty) or a.model_uncertainty<0 or not _finite(a.correction_cost) or a.correction_cost<0: return 'ACTION_DYNAMICS_COST_INVALID',Escalation.INVALID_CONFIGURATION
        d=dict(a.deltas)
        if len(d)!=len(a.deltas) or not d or any(k not in state or not _finite(v) for k,v in a.deltas): return 'ACTION_DELTA_INVALID',Escalation.INVALID_CONFIGURATION
    for b in req.barriers:
        if not isinstance(b,SafetyBarrier) or not b.barrier_id or not b.field or b.binding!=req.binding or b.state_epoch!=req.state_epoch: return 'BARRIER_INVALID',Escalation.INVALID_CONFIGURATION
        if b.field not in state: return 'BARRIER_STATE_FIELD_UNKNOWN',Escalation.UNKNOWN_STATE
        if not _finite(b.minimum) or not _finite(b.maximum) or b.minimum>b.maximum: return 'BARRIER_BOUNDS_INVALID',Escalation.INVALID_CONFIGURATION
        if not _finite(b.minimum_margin) or b.minimum_margin<0: return 'BARRIER_MARGIN_INVALID',Escalation.INVALID_CONFIGURATION
    return None,None

def _barrier_metrics(state:dict[str,float], barriers:tuple[SafetyBarrier,...]):
    margins=[]; violating=[]; low=[]
    for b in barriers:
        v=float(state[b.field]); m=min(v-float(b.minimum),float(b.maximum)-v); margins.append(m)
        if m<0: violating.append(b.barrier_id)
        elif m<float(b.minimum_margin): low.append(b.barrier_id)
    return min(margins),tuple(sorted(violating)),tuple(sorted(low))

def _evaluate_action(req:BarrierRequest, action:ActionDynamics):
    state={k:float(v) for k,v in req.current_state}
    current_margin,_,_= _barrier_metrics(state,req.barriers)
    for k,d in action.deltas: state[k]=state[k]+float(d)
    predicted_margin,violating,low=_barrier_metrics(state,req.barriers)
    return BarrierEvaluation(action.action_id,tuple(sorted(state.items())),current_margin,predicted_margin,predicted_margin-current_margin,violating,low,float(action.model_uncertainty),float(action.correction_cost))

def evaluate(req:BarrierRequest)->BarrierResult:
    err,esc=_validate(req)
    if err: return _hold(err,esc)
    actions={a.action_id:a for a in req.actions}; candidate=actions[req.candidate_action_id]
    ev=_evaluate_action(req,candidate)
    if ev.model_uncertainty>float(req.max_model_uncertainty):
        return BarrierResult(Decision.HOLD,NextAction.HOLD_REPLAN_CANDIDATE,Escalation.MODEL_UNCERTAINTY,('MODEL_UNCERTAINTY_HIGH',),candidate.action_id,None,ev.predicted_state,ev.predicted_barrier_margin,ev.barrier_rate,False,False,True,False)
    if ev.violating_barrier_ids:
        corrected=None
        if req.allow_correction_search:
            alts=[]
            for a in req.actions:
                if a.action_id==candidate.action_id or a.model_uncertainty>float(req.max_model_uncertainty): continue
                ae=_evaluate_action(req,a)
                if not ae.violating_barrier_ids and not ae.low_margin_barrier_ids:
                    alts.append((ae.correction_cost,-ae.predicted_barrier_margin,a.action_id,ae))
            if alts: corrected=sorted(alts,key=lambda x:(x[0],x[1],x[2]))[0][3]
        return BarrierResult(Decision.DENY,NextAction.CORRECTED_ACTION_CANDIDATE if corrected else NextAction.HOLD_REPLAN_CANDIDATE,Escalation.BARRIER_VIOLATION,('BARRIER_LT_ZERO',)+tuple('VIOLATION:'+x for x in ev.violating_barrier_ids),candidate.action_id,corrected.action_id if corrected else None,ev.predicted_state,ev.predicted_barrier_margin,ev.barrier_rate,False,corrected is not None,True,corrected is not None)
    if ev.low_margin_barrier_ids:
        return BarrierResult(Decision.HOLD,NextAction.AUTHORITY_REDUCTION_CANDIDATE,Escalation.LOW_BARRIER_MARGIN,('BARRIER_MARGIN_LOW',)+tuple('LOW_MARGIN:'+x for x in ev.low_margin_barrier_ids),candidate.action_id,None,ev.predicted_state,ev.predicted_barrier_margin,ev.barrier_rate,True,False,True,True)
    return BarrierResult(Decision.ALLOW,NextAction.SAFE_ACTION_CANDIDATE,Escalation.NONE,('SAFE_SET_PRESERVED','MARGIN_SUFFICIENT'),candidate.action_id,None,ev.predicted_state,ev.predicted_barrier_margin,ev.barrier_rate,True,False,False,True)

def _fingerprints(req:BarrierRequest):
    af=tuple(sorted((a.action_id,a.dynamics_fingerprint) for a in req.actions)); bf=tuple(sorted((b.barrier_id,b.barrier_fingerprint) for b in req.barriers))
    context=_fp((req.request_id,tuple(sorted(req.current_state)),req.candidate_action_id,req.binding,req.state_epoch))
    dynamics=_fp(af); safety=_fp(bf); policy=_fp((req.max_model_uncertainty,req.allow_correction_search)); registry=_fp((af,bf)); return af,bf,context,dynamics,safety,policy,registry

def prepare_state(req:BarrierRequest,*,binding:str,state_epoch:str)->PreparedBarrierState:
    if binding!=req.binding or state_epoch!=req.state_epoch: raise ValueError('PREPARE_BINDING_EPOCH_MISMATCH')
    err,_=_validate(req)
    if err: raise ValueError(err)
    af,bf,ctx,dyn,saf,pol,reg=_fingerprints(req); result=evaluate(req); ef=_fp(result)
    return PreparedBarrierState(req,af,bf,ctx,dyn,saf,pol,reg,ef,result,binding,state_epoch)

def validate_prepared_integrity(st:PreparedBarrierState)->bool:
    try:
        if not isinstance(st,PreparedBarrierState): return False
        if st.binding!=st.request.binding or st.state_epoch!=st.request.state_epoch: return False
        af,bf,ctx,dyn,saf,pol,reg=_fingerprints(st.request)
        return (af,bf,ctx,dyn,saf,pol,reg,_fp(st.precomputed_result))==(st.action_fingerprints,st.barrier_fingerprints,st.context_fingerprint,st.dynamics_fingerprint,st.safety_fingerprint,st.policy_fingerprint,st.registry_fingerprint,st.evaluation_fingerprint)
    except Exception: return False

def evaluate_prepared(st:PreparedBarrierState,*,integrity_validated:bool,current_context_fingerprint:str,current_dynamics_fingerprint:str,current_safety_fingerprint:str,current_policy_fingerprint:str,current_registry_fingerprint:str,current_evaluation_fingerprint:str)->BarrierResult:
    if not integrity_validated: return _hold('PREPARED_INTEGRITY_NOT_VALIDATED')
    expected=(st.context_fingerprint,st.dynamics_fingerprint,st.safety_fingerprint,st.policy_fingerprint,st.registry_fingerprint,st.evaluation_fingerprint)
    current=(current_context_fingerprint,current_dynamics_fingerprint,current_safety_fingerprint,current_policy_fingerprint,current_registry_fingerprint,current_evaluation_fingerprint)
    if current!=expected: return _hold('PREPARED_FINGERPRINT_MISMATCH')
    return st.precomputed_result

def make_delta(base:PreparedBarrierState,target:PreparedBarrierState)->BarrierStateDelta:
    ba={a.action_id:a for a in base.request.actions}; ta={a.action_id:a for a in target.request.actions}; bb={b.barrier_id:b for b in base.request.barriers}; tb={b.barrier_id:b for b in target.request.barriers}
    ca=tuple(ta[k] for k in sorted(ta) if k not in ba or _fp(ta[k])!=_fp(ba[k])); cb=tuple(tb[k] for k in sorted(tb) if k not in bb or _fp(tb[k])!=_fp(bb[k]))
    removed=tuple(sorted([f'ACTION:{k}' for k in ba if k not in ta]+[f'BARRIER:{k}' for k in bb if k not in tb]))
    cs=None if tuple(sorted(base.request.current_state))==tuple(sorted(target.request.current_state)) else target.request.current_state
    cand=None if base.request.candidate_action_id==target.request.candidate_action_id else target.request.candidate_action_id
    return BarrierStateDelta(base.registry_fingerprint,target.registry_fingerprint,ca,cb,removed,cs,cand,target.binding,target.state_epoch)

def plan_missing_only(base:PreparedBarrierState,target:PreparedBarrierState)->BarrierSyncPlan:
    d=make_delta(base,target); ids=[f'ACTION:{a.action_id}' for a in d.changed_actions]+[f'BARRIER:{b.barrier_id}' for b in d.changed_barriers]+list(d.removed_record_ids)
    if d.current_state_replacement is not None: ids.append('CURRENT_STATE')
    if d.candidate_action_replacement is not None: ids.append('CANDIDATE_ACTION')
    metadata=len(_canon((d.base_registry_fingerprint,d.target_registry_fingerprint,d.binding,d.state_epoch)))
    return BarrierSyncPlan(tuple(sorted(ids)),metadata,False)

def default_request()->BarrierRequest:
    b='NOEPIN-AL-113-DEFAULT'; e='EPOCH-1'
    barriers=(SafetyBarrier('RESOURCE_BOUND','resource',0.0,100.0,10.0,'V1','FP-B-RESOURCE',b,e),SafetyBarrier('PRIVILEGE_BOUND','privilege',0.0,10.0,1.0,'V1','FP-B-PRIV',b,e))
    actions=(ActionDynamics('SAFE_STEP',(('resource',-5.0),('privilege',0.0)),0.02,0.0,'V1','FP-A-SAFE',b,e),ActionDynamics('RISKY_STEP',(('resource',-50.0),('privilege',9.0)),0.02,5.0,'V1','FP-A-RISKY',b,e),ActionDynamics('CONSERVATIVE_STEP',(('resource',-1.0),('privilege',0.0)),0.01,1.0,'V1','FP-A-CONS',b,e))
    return BarrierRequest('REQ-113-DEFAULT',(('privilege',2.0),('resource',70.0)),'SAFE_STEP',actions,barriers,0.2,True,b,e)

def default_evaluation(): return evaluate(default_request())

__all__=['Decision','NextAction','Escalation','SafetyBarrier','ActionDynamics','BarrierRequest','BarrierEvaluation','BarrierResult','PreparedBarrierState','BarrierStateDelta','BarrierSyncPlan','evaluate','prepare_state','validate_prepared_integrity','evaluate_prepared','make_delta','plan_missing_only','default_request','default_evaluation','_canon','_fp']
