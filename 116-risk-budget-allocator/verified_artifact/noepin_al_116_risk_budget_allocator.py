"""NOEPIN AL 116 — Risk Budget Allocator — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Deterministic, fail-safe risk-budget ledger and constrained allocator. Total Risk Budget is
immutable input evidence; subtasks receive bounded candidate allocations according to priority,
risk estimate, critical-step caps, unknown-risk conservative caps, prior consumption and limited
redistribution. The allocator does not grant permission, create additional risk budget, execute a
stop/action, prove safety, or promote estimates to World Truth.

Canonical identity: NOEPIN-AL-116
DCSR level: AUXILIARY INTEGRATION / 補助統合.
Provenance note: exact registered Origin GUID was not freshly reverified and is intentionally not
guessed. Pre-existing Notion V1 attachment byte identity was not freshly reverified.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str, Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class NextAction(str, Enum):
    BUDGET_ALLOCATION_CANDIDATE='BUDGET_ALLOCATION_CANDIDATE'
    CONSERVATIVE_ALLOCATION_CANDIDATE='CONSERVATIVE_ALLOCATION_CANDIDATE'
    HOLD_OVERRUN_CANDIDATE='HOLD_OVERRUN_CANDIDATE'
    HOLD_INSUFFICIENT_BUDGET_CANDIDATE='HOLD_INSUFFICIENT_BUDGET_CANDIDATE'
    POLICY_REVIEW_CANDIDATE='POLICY_REVIEW_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; TOTAL_OVERRUN='TOTAL_OVERRUN'; UNKNOWN_RISK='UNKNOWN_RISK'; CRITICAL_CAP='CRITICAL_CAP'; INSUFFICIENT_BUDGET='INSUFFICIENT_BUDGET'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'

@dataclass(frozen=True)
class Subtask:
    subtask_id: str
    priority: float
    risk_estimate: float|None
    critical: bool
    consumed_risk: float
    previous_budget: float
    completed: bool
    evidence_version: str
    evidence_fingerprint: str
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class RiskBudgetPolicy:
    critical_step_cap_fraction: float
    unknown_step_cap_fraction: float
    unknown_risk_floor: float
    per_step_max_fraction: float
    min_active_step_fraction: float
    redistribution_cap_fraction: float
    reserve_fraction: float
    allow_redistribution: bool

@dataclass(frozen=True)
class AllocationRequest:
    request_id: str
    total_risk_budget: float
    subtasks: tuple[Subtask,...]
    policy: RiskBudgetPolicy
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class StepAllocation:
    subtask_id: str
    budget_candidate: float
    consumed_risk: float
    remaining_step_budget: float
    risk_estimate: float|None
    critical: bool
    unknown_risk: bool
    cap_applied: bool

@dataclass(frozen=True)
class AllocationResult:
    decision: Decision
    next_action: NextAction
    escalation: Escalation
    reasons: tuple[str,...]
    total_risk_budget: float
    consumed_total: float
    allocatable_remaining: float
    reserve_budget: float
    allocated_total: float
    remaining_budget: float
    redistribution_pool: float
    allocations: tuple[StepAllocation,...]
    overrun_alert: bool
    unknown_risk_count: int
    critical_count: int
    next_gate_candidate: bool
    allocation_promoted_to_permission: bool=False
    additional_budget_granted: bool=False
    permission_granted: bool=False
    approval_executed: bool=False
    authority_granted: bool=False
    stop_executed: bool=False
    action_executed: bool=False
    plan_committed: bool=False
    publish_executed: bool=False
    external_write_performed: bool=False
    world_truth_proven: bool=False
    domain_authority_promoted: bool=False
    safety_proven: bool=False
    action_success: bool=False

@dataclass(frozen=True)
class PreparedRiskBudgetState:
    request: AllocationRequest
    result: AllocationResult
    context_fingerprint: str
    subtask_fingerprint: str
    policy_fingerprint: str
    registry_fingerprint: str
    allocation_fingerprint: str
    integrity_fingerprint: str
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class BudgetDelta:
    changed_subtasks: tuple[Subtask,...]
    removed_subtask_ids: tuple[str,...]
    from_registry_fingerprint: str
    to_registry_fingerprint: str

@dataclass(frozen=True)
class MissingOnlyPlan:
    missing_or_changed_record_ids: tuple[str,...]
    metadata_bytes_required: int
    full_resend_required: bool


def _obj(v):
    if isinstance(v, Enum): return v.value
    if is_dataclass(v): return {f.name:_obj(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v, dict): return {str(k):_obj(v[k]) for k in sorted(v,key=str)}
    if isinstance(v, (tuple,list)): return [_obj(x) for x in v]
    return v

def _canon(v)->bytes:
    return json.dumps(_obj(v),ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')
def _fp(v)->str: return sha256(_canon(v)).hexdigest()
def _finite(x): return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(float(x))
def _round(x): return round(max(0.0,float(x)),12)

def default_policy():
    return RiskBudgetPolicy(0.28,0.10,0.35,0.35,0.015,0.15,0.10,True)

def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    ss=(
        Subtask('RESEARCH',1.0,0.20,False,0.010,0.0,False,'V1','FP-RESEARCH',b,e),
        Subtask('VERIFY',1.5,0.12,True,0.005,0.0,False,'V1','FP-VERIFY',b,e),
        Subtask('BUILD',1.2,0.25,False,0.015,0.0,False,'V1','FP-BUILD',b,e),
        Subtask('PUBLISH-CHECK',1.4,None,True,0.000,0.0,False,'V1','FP-PUBLISH',b,e),
    )
    return AllocationRequest('DEFAULT-116',1.0,ss,default_policy(),b,e)

def _hold(req, reason, esc=Escalation.INVALID_CONFIGURATION, nxt=NextAction.POLICY_REVIEW_CANDIDATE, consumed=0.0):
    total=float(req.total_risk_budget) if _finite(req.total_risk_budget) else 0.0
    return AllocationResult(Decision.HOLD,nxt,esc,(reason,),total,_round(consumed),0.0,0.0,0.0,_round(max(0,total-consumed)),0.0,(),esc==Escalation.TOTAL_OVERRUN,0,0,False)

def evaluate(req: AllocationRequest)->AllocationResult:
    p=req.policy
    if not isinstance(req.request_id,str) or not req.request_id or not isinstance(req.binding,str) or not req.binding or not isinstance(req.state_epoch,str) or not req.state_epoch:
        return _hold(req,'INVALID_REQUEST_IDENTITY')
    if not _finite(req.total_risk_budget) or float(req.total_risk_budget)<=0: return _hold(req,'TOTAL_BUDGET_INVALID')
    pf=(p.critical_step_cap_fraction,p.unknown_step_cap_fraction,p.unknown_risk_floor,p.per_step_max_fraction,p.min_active_step_fraction,p.redistribution_cap_fraction,p.reserve_fraction)
    if not all(_finite(x) for x in pf): return _hold(req,'POLICY_NONFINITE')
    if not (0<p.critical_step_cap_fraction<=1 and 0<p.unknown_step_cap_fraction<=1 and 0<=p.unknown_risk_floor<=1 and 0<p.per_step_max_fraction<=1 and 0<=p.min_active_step_fraction<=1 and 0<=p.redistribution_cap_fraction<=1 and 0<=p.reserve_fraction<1):
        return _hold(req,'POLICY_RANGE_INVALID')
    if not req.subtasks: return _hold(req,'NO_SUBTASKS')
    ordered=tuple(sorted(req.subtasks,key=lambda s:s.subtask_id))
    if len({s.subtask_id for s in ordered})!=len(ordered): return _hold(req,'DUPLICATE_SUBTASK_ID')
    for s in ordered:
        if not s.subtask_id or s.binding!=req.binding or s.state_epoch!=req.state_epoch: return _hold(req,'SUBTASK_BINDING_MISMATCH')
        if not _finite(s.priority) or s.priority<=0 or not _finite(s.consumed_risk) or s.consumed_risk<0 or not _finite(s.previous_budget) or s.previous_budget<0: return _hold(req,'SUBTASK_NUMERIC_INVALID')
        if s.risk_estimate is not None and (not _finite(s.risk_estimate) or not 0<=float(s.risk_estimate)<=1): return _hold(req,'RISK_ESTIMATE_INVALID')
    total=float(req.total_risk_budget); consumed=sum(float(s.consumed_risk) for s in ordered)
    if consumed>total+1e-12:
        r=_hold(req,'TOTAL_RISK_BUDGET_OVERRUN',Escalation.TOTAL_OVERRUN,NextAction.HOLD_OVERRUN_CANDIDATE,consumed)
        return replace(r,overrun_alert=True)
    remaining=max(0.0,total-consumed)
    active=tuple(s for s in ordered if not s.completed)
    if not active:
        return AllocationResult(Decision.ALLOW,NextAction.BUDGET_ALLOCATION_CANDIDATE,Escalation.NONE,('ALL_SUBTASKS_COMPLETE_LEDGER_ONLY',),total,_round(consumed),_round(remaining),0.0,0.0,_round(remaining),0.0,(),False,0,sum(1 for s in ordered if s.critical),True)
    reserve=total*float(p.reserve_fraction)
    distributable=max(0.0,remaining-reserve)
    # Bounded redistribution: only unused prior budget from completed work can be recognized,
    # and at most policy fraction of Total Risk Budget may be reintroduced in this allocation cycle.
    unused_completed=sum(max(0.0,float(s.previous_budget)-float(s.consumed_risk)) for s in ordered if s.completed)
    redistribution=min(unused_completed,total*float(p.redistribution_cap_fraction)) if p.allow_redistribution else 0.0
    base_pool=min(remaining,max(0.0,distributable+redistribution))
    unknown_count=sum(1 for s in active if s.risk_estimate is None)
    crit_count=sum(1 for s in active if s.critical)
    weights=[]
    for s in active:
        risk=float(s.risk_estimate) if s.risk_estimate is not None else float(p.unknown_risk_floor)
        # Critical work gets priority weight, but never bypasses its hard critical cap.
        w=float(s.priority)*(0.25+0.75*risk)*(1.20 if s.critical else 1.0)
        weights.append((s,w))
    wsum=sum(w for _,w in weights)
    if wsum<=0 or base_pool<=0:
        return AllocationResult(Decision.HOLD,NextAction.HOLD_INSUFFICIENT_BUDGET_CANDIDATE,Escalation.INSUFFICIENT_BUDGET,('NO_ALLOCATABLE_BUDGET',),total,_round(consumed),_round(remaining),_round(reserve),0.0,_round(remaining),_round(redistribution),(),False,unknown_count,crit_count,False)
    min_active=total*float(p.min_active_step_fraction)
    caps={}
    raw={}
    for s,w in weights:
        cap=total*float(p.per_step_max_fraction)
        if s.critical: cap=min(cap,total*float(p.critical_step_cap_fraction))
        if s.risk_estimate is None: cap=min(cap,total*float(p.unknown_step_cap_fraction))
        caps[s.subtask_id]=cap
        raw[s.subtask_id]=min(cap,max(min_active,base_pool*w/wsum))
    raw_sum=sum(raw.values())
    if raw_sum>base_pool+1e-12:
        # Deterministic proportional shrink preserving caps; if min floors make pool impossible,
        # no task is silently overfunded.
        scale=base_pool/raw_sum
        raw={k:v*scale for k,v in raw.items()}
    allocs=[]
    for s,_ in weights:
        budget=_round(raw[s.subtask_id])
        allocs.append(StepAllocation(s.subtask_id,budget,_round(s.consumed_risk),_round(max(0.0,budget-float(s.consumed_risk))),s.risk_estimate,s.critical,s.risk_estimate is None,budget>=caps[s.subtask_id]-1e-9))
    allocated=sum(a.budget_candidate for a in allocs)
    rem=max(0.0,remaining-allocated)
    reasons=['TOTAL_BUDGET_IMMUTABLE','POLICY_BOUNDED_ALLOCATION','ALLOCATION_CANDIDATE_ONLY']
    esc=Escalation.NONE; nxt=NextAction.BUDGET_ALLOCATION_CANDIDATE
    if unknown_count:
        reasons.append('UNKNOWN_RISK_CONSERVATIVE_CAP'); esc=Escalation.UNKNOWN_RISK; nxt=NextAction.CONSERVATIVE_ALLOCATION_CANDIDATE
    if any(a.critical and a.cap_applied for a in allocs): reasons.append('CRITICAL_STEP_CAP_APPLIED')
    return AllocationResult(Decision.ALLOW,nxt,esc,tuple(reasons),total,_round(consumed),_round(remaining),_round(reserve),_round(allocated),_round(rem),_round(redistribution),tuple(allocs),False,unknown_count,crit_count,True)

def default_evaluation(): return evaluate(default_request())

def prepare_state(req:AllocationRequest,*,binding:str,state_epoch:str)->PreparedRiskBudgetState:
    if binding!=req.binding or state_epoch!=req.state_epoch: raise ValueError('binding/state_epoch mismatch')
    result=evaluate(req)
    ordered=tuple(sorted(req.subtasks,key=lambda s:s.subtask_id))
    context=_fp((req.request_id,req.total_risk_budget,binding,state_epoch))
    sf=_fp(ordered); pf=_fp(req.policy); rf=_fp(tuple((s.subtask_id,s.evidence_version,s.evidence_fingerprint,s.binding,s.state_epoch) for s in ordered)); af=_fp(result)
    integ=_fp((context,sf,pf,rf,af,binding,state_epoch))
    return PreparedRiskBudgetState(req,result,context,sf,pf,rf,af,integ,binding,state_epoch)

def validate_prepared_integrity(st:PreparedRiskBudgetState)->bool:
    return st.integrity_fingerprint==_fp((st.context_fingerprint,st.subtask_fingerprint,st.policy_fingerprint,st.registry_fingerprint,st.allocation_fingerprint,st.binding,st.state_epoch))

def evaluate_prepared(st:PreparedRiskBudgetState,*,integrity_validated:bool,current_context_fingerprint:str,current_subtask_fingerprint:str,current_policy_fingerprint:str,current_registry_fingerprint:str,current_allocation_fingerprint:str)->AllocationResult:
    if not integrity_validated or not validate_prepared_integrity(st): return _hold(st.request,'PREPARED_INTEGRITY_NOT_VALIDATED')
    current=(current_context_fingerprint,current_subtask_fingerprint,current_policy_fingerprint,current_registry_fingerprint,current_allocation_fingerprint)
    saved=(st.context_fingerprint,st.subtask_fingerprint,st.policy_fingerprint,st.registry_fingerprint,st.allocation_fingerprint)
    if current!=saved: return _hold(st.request,'PREPARED_FINGERPRINT_MISMATCH')
    return st.result

def make_delta(old:PreparedRiskBudgetState,new:PreparedRiskBudgetState)->BudgetDelta:
    om={s.subtask_id:s for s in old.request.subtasks}; nm={s.subtask_id:s for s in new.request.subtasks}
    changed=tuple(nm[k] for k in sorted(nm) if k not in om or _fp(nm[k])!=_fp(om[k])); removed=tuple(k for k in sorted(om) if k not in nm)
    return BudgetDelta(changed,removed,old.registry_fingerprint,new.registry_fingerprint)

def plan_missing_only(old:PreparedRiskBudgetState,new:PreparedRiskBudgetState)->MissingOnlyPlan:
    d=make_delta(old,new); ids=tuple([f'SUBTASK:{s.subtask_id}' for s in d.changed_subtasks]+[f'REMOVED:{x}' for x in d.removed_subtask_ids]); meta=len(_canon({'from':d.from_registry_fingerprint,'to':d.to_registry_fingerprint,'ids':ids})); return MissingOnlyPlan(ids,meta,False)
