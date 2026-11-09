"""NOEPIN AL 118 — Rollback Checkpoint Optimizer — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-118
DCSR: DIRECT INTEGRATION / 直接統合.

Produces deterministic checkpoint *candidates* from failure probability, step cost, irreversibility,
and snapshot/reconstruction cost. Full snapshots and DCSR Shared-Base+Delta reconstruction are compared.
No checkpoint is executed, no rollback is executed, and no permission/authority is granted.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str,Enum): ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class NextAction(str,Enum):
    CHECKPOINT_PLAN_CANDIDATE='CHECKPOINT_PLAN_CANDIDATE'
    HUMAN_APPROVAL_CHECKPOINT_CANDIDATE='HUMAN_APPROVAL_CHECKPOINT_CANDIDATE'
    HOLD_ROLLBACK_CANDIDATE='HOLD_ROLLBACK_CANDIDATE'
class Escalation(str,Enum):
    NONE='NONE'; CHECKPOINT_UNAVAILABLE_HIGH_RISK='CHECKPOINT_UNAVAILABLE_HIGH_RISK'; UNKNOWN_RISK='UNKNOWN_RISK'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'

@dataclass(frozen=True)
class PlanStep:
    step_id:str
    step_cost:float
    failure_probability:float|None
    snapshot_cost:float
    snapshot_possible:bool
    reversible:bool
    state_full_bytes:int
    shared_base_bytes:int
    delta_bytes:int
    priority:float
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class CheckpointPolicy:
    high_risk_threshold:float
    irreversible_risk_threshold:float
    conservative_unknown_failure_probability:float
    snapshot_weight:float
    recovery_weight:float
    dcsr_byte_cost:float
    max_checkpoint_interval:int

@dataclass(frozen=True)
class RollbackRequest:
    request_id:str
    plan:tuple[PlanStep,...]
    policy:CheckpointPolicy
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class CheckpointCandidate:
    before_step_id:str
    reconstruction_mode:str
    snapshot_or_reconstruction_cost:float
    mandatory:bool
    reason:str

@dataclass(frozen=True)
class RollbackResult:
    decision:Decision
    next_action:NextAction
    escalation:Escalation
    reasons:tuple[str,...]
    checkpoint_locations:tuple[str,...]
    checkpoints:tuple[CheckpointCandidate,...]
    expected_recovery_cost:float
    expected_snapshot_cost:float
    total_expected_cost:float
    high_risk_checkpoint_coverage_complete:bool
    dcsr_direct_reconstruction_used:bool
    next_gate_candidate:bool
    checkpoint_promoted_to_permission:bool=False
    snapshot_executed:bool=False
    rollback_executed:bool=False
    permission_granted:bool=False
    approval_executed:bool=False
    authority_granted:bool=False
    stop_executed:bool=False
    action_executed:bool=False
    plan_committed:bool=False
    publish_executed:bool=False
    external_write_performed:bool=False
    world_truth_proven:bool=False
    domain_authority_promoted:bool=False
    safety_proven:bool=False
    action_success:bool=False

@dataclass(frozen=True)
class PreparedRollbackState:
    request:RollbackRequest
    result:RollbackResult
    context_fingerprint:str
    plan_fingerprint:str
    policy_fingerprint:str
    registry_fingerprint:str
    optimization_fingerprint:str
    integrity_fingerprint:str
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class RollbackDelta:
    changed_steps:tuple[PlanStep,...]
    removed_step_ids:tuple[str,...]
    from_registry_fingerprint:str
    to_registry_fingerprint:str

@dataclass(frozen=True)
class MissingOnlyPlan:
    missing_or_changed_record_ids:tuple[str,...]
    metadata_bytes_required:int
    full_resend_required:bool

def _obj(v):
    if isinstance(v,Enum): return v.value
    if is_dataclass(v): return {f.name:_obj(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v,dict): return {str(k):_obj(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(tuple,list)): return [_obj(x) for x in v]
    return v

def _canon(v)->bytes: return json.dumps(_obj(v),ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def _fp(v)->str: return sha256(_canon(v)).hexdigest()
def _finite(x): return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(float(x))

def default_policy():
    return CheckpointPolicy(.35,.25,.50,1.0,1.0,0.000002,4)

def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    p=(
      PlanStep('S1',2,.05,1,True,True,500000,450000,20000,1,b,e),
      PlanStep('S2',4,.10,1.2,True,True,520000,450000,30000,1,b,e),
      PlanStep('S3',8,.45,1.4,True,False,600000,450000,50000,2,b,e),
      PlanStep('S4',3,.08,1.0,True,True,610000,450000,55000,1,b,e),
      PlanStep('S5',2,.05,1.0,True,True,620000,450000,60000,1,b,e),
    )
    return RollbackRequest('DEFAULT-118',p,default_policy(),b,e)

def _invalid(req,reason):
    return RollbackResult(Decision.HOLD,NextAction.HOLD_ROLLBACK_CANDIDATE,Escalation.INVALID_CONFIGURATION,(reason,),(),(),0,0,0,False,False,False)

def _risk(step:PlanStep,policy:CheckpointPolicy):
    return policy.conservative_unknown_failure_probability if step.failure_probability is None else float(step.failure_probability)

def _checkpoint_cost(step:PlanStep,policy:CheckpointPolicy):
    full=float(step.snapshot_cost)
    dcsr=(float(step.shared_base_bytes)+float(step.delta_bytes))*policy.dcsr_byte_cost
    if dcsr < full: return dcsr,'DCSR_SHARED_BASE_DELTA'
    return full,'FULL_SNAPSHOT'

def evaluate(req:RollbackRequest)->RollbackResult:
    p=req.policy
    if not req.request_id or not req.binding or not req.state_epoch: return _invalid(req,'INVALID_REQUEST_IDENTITY')
    nums=(p.high_risk_threshold,p.irreversible_risk_threshold,p.conservative_unknown_failure_probability,p.snapshot_weight,p.recovery_weight,p.dcsr_byte_cost)
    if not all(_finite(x) for x in nums): return _invalid(req,'POLICY_NONFINITE')
    if not (0<=p.high_risk_threshold<=1 and 0<=p.irreversible_risk_threshold<=1 and 0<=p.conservative_unknown_failure_probability<=1): return _invalid(req,'POLICY_PROBABILITY_RANGE_INVALID')
    if p.snapshot_weight<0 or p.recovery_weight<0 or p.dcsr_byte_cost<0 or not isinstance(p.max_checkpoint_interval,int) or p.max_checkpoint_interval<1: return _invalid(req,'POLICY_COST_OR_INTERVAL_INVALID')
    if not req.plan: return _invalid(req,'EMPTY_PLAN')
    ids=[s.step_id for s in req.plan]
    if len(set(ids))!=len(ids): return _invalid(req,'DUPLICATE_STEP_ID')
    for s in req.plan:
        if not s.step_id or s.binding!=req.binding or s.state_epoch!=req.state_epoch: return _invalid(req,'STEP_BINDING_OR_IDENTITY_INVALID')
        vals=(s.step_cost,s.snapshot_cost,s.priority)
        if not all(_finite(x) and float(x)>=0 for x in vals): return _invalid(req,'STEP_COST_INVALID')
        if s.failure_probability is not None and (not _finite(s.failure_probability) or not 0<=float(s.failure_probability)<=1): return _invalid(req,'FAILURE_PROBABILITY_INVALID')
        if any((not isinstance(x,int) or x<0) for x in (s.state_full_bytes,s.shared_base_bytes,s.delta_bytes)): return _invalid(req,'STATE_SIZE_INVALID')
    mandatory=[]; unknown=False
    for i,s in enumerate(req.plan):
        r=_risk(s,p); unknown |= s.failure_probability is None
        if (not s.reversible and r>=p.irreversible_risk_threshold) or r>=p.high_risk_threshold:
            mandatory.append(i)
            if i>0 and not s.snapshot_possible:
                dec=Decision.HUMAN_APPROVAL if not s.reversible else Decision.HOLD
                return RollbackResult(dec,NextAction.HUMAN_APPROVAL_CHECKPOINT_CANDIDATE if dec==Decision.HUMAN_APPROVAL else NextAction.HOLD_ROLLBACK_CANDIDATE,Escalation.CHECKPOINT_UNAVAILABLE_HIGH_RISK,('HIGH_RISK_CHECKPOINT_UNAVAILABLE','NO_AUTOMATIC_CONTINUE'),(),(),0,0,0,False,False,False)
    n=len(req.plan)
    # Dynamic program: choose checkpoints so each segment's expected rework + checkpoint cost is minimized.
    # Mandatory boundaries cannot be skipped; max interval bounds exposure.
    inf=float('inf'); dp=[inf]*(n+1); prev=[None]*(n+1); dp[0]=0.0
    prefix_cost=[0.0]
    for s in req.plan: prefix_cost.append(prefix_cost[-1]+float(s.step_cost))
    mandatory_set=set(mandatory)
    for end in range(1,n+1):
        boundary_step=req.plan[end] if end<n else None
        if end<n and not boundary_step.snapshot_possible: continue
        cp_cost,mode=_checkpoint_cost(boundary_step,p) if end<n else (0.0,'END')
        for start in range(max(0,end-p.max_checkpoint_interval),end):
            if dp[start]==inf: continue
            # A mandatory checkpoint before step m means segment cannot cross m without starting there.
            if any(start < m < end for m in mandatory_set): continue
            seg_expected=0.0; accumulated=0.0
            for k in range(start,end):
                accumulated += float(req.plan[k].step_cost)
                seg_expected += _risk(req.plan[k],p)*accumulated*float(req.plan[k].priority)
            val=dp[start]+p.recovery_weight*seg_expected+p.snapshot_weight*cp_cost
            if val < dp[end]-1e-12 or (abs(val-dp[end])<=1e-12 and (prev[end] is None or start>prev[end][0])):
                dp[end]=val; prev[end]=(start,mode,cp_cost)
    if dp[n]==inf: return RollbackResult(Decision.HOLD,NextAction.HOLD_ROLLBACK_CANDIDATE,Escalation.CHECKPOINT_UNAVAILABLE_HIGH_RISK,('NO_FEASIBLE_CHECKPOINT_LAYOUT','NO_AUTOMATIC_CONTINUE'),(),(),0,0,0,False,False,False)
    boundaries=[]; cur=n
    while cur>0:
        st,mode,cost=prev[cur];
        if cur<n: boundaries.append((cur,mode,cost))
        cur=st
    boundaries.reverse()
    # Ensure mandatory checkpoints are explicitly included before mandatory steps.
    chosen={b[0]:b for b in boundaries}
    for m in mandatory:
        if m==0: # initial state is the rollback base; no new snapshot required.
            continue
        if m not in chosen:
            step=req.plan[m]
            if not step.snapshot_possible:
                return RollbackResult(Decision.HUMAN_APPROVAL,NextAction.HUMAN_APPROVAL_CHECKPOINT_CANDIDATE,Escalation.CHECKPOINT_UNAVAILABLE_HIGH_RISK,('MANDATORY_CHECKPOINT_UNAVAILABLE',),(),(),0,0,0,False,False,False)
            c,mode=_checkpoint_cost(step,p); chosen[m]=(m,mode,c)
    final_bounds=[chosen[k] for k in sorted(chosen)]
    cps=[]; snap_total=0.0; dcsr=False
    for idx,mode,cost in final_bounds:
        step=req.plan[idx]
        mandatory_flag=idx in mandatory_set
        reason='MANDATORY_HIGH_RISK_OR_IRREVERSIBLE' if mandatory_flag else 'EXPECTED_COST_OPTIMUM'
        cps.append(CheckpointCandidate(step.step_id,mode,cost,mandatory_flag,reason)); snap_total+=cost; dcsr |= mode=='DCSR_SHARED_BASE_DELTA'
    # Expected recovery from selected segments.
    cp_indices=[0]+[x[0] for x in final_bounds]+[n]
    recovery=0.0
    for a,b in zip(cp_indices,cp_indices[1:]):
        acc=0.0
        for k in range(a,b):
            acc+=float(req.plan[k].step_cost); recovery += _risk(req.plan[k],p)*acc*float(req.plan[k].priority)
    coverage=all(m==0 or m in chosen for m in mandatory)
    reasons=['CHECKPOINT_LAYOUT_OPTIMIZED','FULL_AND_DCSR_RECONSTRUCTION_COST_COMPARED','CHECKPOINTS_ARE_CANDIDATES_ONLY']
    esc=Escalation.UNKNOWN_RISK if unknown else Escalation.NONE
    if unknown: reasons.append('UNKNOWN_RISK_CONSERVATIVE_ESTIMATE_USED')
    return RollbackResult(Decision.ALLOW,NextAction.CHECKPOINT_PLAN_CANDIDATE,esc,tuple(reasons),tuple(c.before_step_id for c in cps),tuple(cps),recovery,snap_total,p.recovery_weight*recovery+p.snapshot_weight*snap_total,coverage,dcsr,coverage)

def default_evaluation(): return evaluate(default_request())

def prepare_state(req:RollbackRequest,*,binding:str,state_epoch:str)->PreparedRollbackState:
    if binding!=req.binding or state_epoch!=req.state_epoch: raise ValueError('binding/state_epoch mismatch')
    res=evaluate(req)
    context=_fp((req.request_id,binding,state_epoch))
    planfp=_fp(req.plan); policyfp=_fp(req.policy)
    registry=_fp(tuple((s.step_id,s.failure_probability,s.snapshot_possible,s.reversible,s.state_full_bytes,s.shared_base_bytes,s.delta_bytes,s.binding,s.state_epoch) for s in req.plan))
    opt=_fp(res); integ=_fp((context,planfp,policyfp,registry,opt,binding,state_epoch))
    return PreparedRollbackState(req,res,context,planfp,policyfp,registry,opt,integ,binding,state_epoch)

def validate_prepared_integrity(st): return st.integrity_fingerprint==_fp((st.context_fingerprint,st.plan_fingerprint,st.policy_fingerprint,st.registry_fingerprint,st.optimization_fingerprint,st.binding,st.state_epoch))

def evaluate_prepared(st,*,integrity_validated,current_context_fingerprint,current_plan_fingerprint,current_policy_fingerprint,current_registry_fingerprint,current_optimization_fingerprint):
    if not integrity_validated or not validate_prepared_integrity(st): return _invalid(st.request,'PREPARED_INTEGRITY_NOT_VALIDATED')
    if (current_context_fingerprint,current_plan_fingerprint,current_policy_fingerprint,current_registry_fingerprint,current_optimization_fingerprint)!=(st.context_fingerprint,st.plan_fingerprint,st.policy_fingerprint,st.registry_fingerprint,st.optimization_fingerprint): return _invalid(st.request,'PREPARED_FINGERPRINT_MISMATCH')
    return st.result

def make_delta(old,new):
    om={s.step_id:s for s in old.request.plan}; nm={s.step_id:s for s in new.request.plan}
    changed=tuple(nm[k] for k in sorted(nm) if k not in om or _fp(nm[k])!=_fp(om[k])); removed=tuple(k for k in sorted(om) if k not in nm)
    return RollbackDelta(changed,removed,old.registry_fingerprint,new.registry_fingerprint)

def plan_missing_only(old,new):
    d=make_delta(old,new); ids=tuple([f'STEP:{s.step_id}' for s in d.changed_steps]+[f'REMOVED:{x}' for x in d.removed_step_ids]); meta=len(_canon({'from':d.from_registry_fingerprint,'to':d.to_registry_fingerprint,'ids':ids})); return MissingOnlyPlan(ids,meta,False)
