"""NOEPIN AL 108 — Cost-Risk Pareto Planner — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Pure deterministic multi-objective planning evidence. Candidate plans are filtered by
hard constraints/policy/risk caps, then compared by Pareto dominance without collapsing
cost, time, risk, success probability and reversibility into an arbitrary scalar. When
multiple non-dominated candidates remain and policy preferences do not determine a
unique choice, the result is HUMAN_APPROVAL candidate evidence rather than invented
weights. Returned plan evidence never grants permission, executes actions, commits,
publishes, proves safety/world truth, or establishes action success.

Canonical identity: NOEPIN-AL-108
DCSR level: AUXILIARY INTEGRATION / 補助統合.
Provenance note: exact registered Origin GUID was not freshly reverified in this
completion session and is intentionally not guessed or regenerated.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, IntEnum
from hashlib import sha256
import json, math

class Decision(str, Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class RiskClass(IntEnum): LOW=0; MEDIUM=1; HIGH=2; CRITICAL=3
class Objective(str, Enum):
    COST='COST'; TIME='TIME'; RISK='RISK'; SUCCESS='SUCCESS'; REVERSIBILITY='REVERSIBILITY'
class NextAction(str, Enum):
    SELECTED_PLAN_CANDIDATE='SELECTED_PLAN_CANDIDATE'
    HUMAN_REVIEW_CANDIDATE='HUMAN_REVIEW_CANDIDATE'
    HOLD_NO_SAFE_PLAN='HOLD_NO_SAFE_PLAN'

@dataclass(frozen=True)
class CandidatePlan:
    plan_id:str; total_cost:float; total_time:float; total_risk:float; success_probability:float; reversibility:float
    hard_constraint_passed:bool; policy_allowed:bool; observed:bool; plan_version:str; plan_fingerprint:str
    binding:str; state_epoch:str

@dataclass(frozen=True)
class ParetoRequest:
    request_id:str; risk_class:RiskClass; max_total_cost:float; max_total_time:float; max_total_risk:float
    min_success_probability:float; min_reversibility:float; observed:bool; binding:str; state_epoch:str

@dataclass(frozen=True)
class PreferencePolicy:
    priority_order:tuple[Objective,...]; low_risk_cap:float; medium_risk_cap:float; high_risk_cap:float; critical_risk_cap:float
    major_tradeoff_risk_delta:float; major_tradeoff_cost_ratio:float; major_tradeoff_time_ratio:float
    require_hard_constraints:bool; require_policy_allowed:bool; binding:str; state_epoch:str; revoked:bool=False

@dataclass(frozen=True)
class PlanScore:
    plan_id:str; total_cost:float; total_time:float; total_risk:float; success_probability:float; reversibility:float
    tradeoffs:tuple[str,...]

@dataclass(frozen=True)
class ParetoResult:
    decision:Decision; next_action:NextAction; reasons:tuple[str,...]; pareto_frontier:tuple[PlanScore,...]
    dominated_plans:tuple[str,...]; rejected_plans:tuple[tuple[str,str],...]; selected_plan:str|None
    major_tradeoff:bool; preference_resolved:bool; next_gate_candidate:bool
    plan_promoted_to_permission:bool=False; permission_granted:bool=False; authority_granted:bool=False
    action_executed:bool=False; plan_committed:bool=False; atomic_publish_executed:bool=False
    external_write_performed:bool=False; world_truth_proven:bool=False; domain_authority_promoted:bool=False
    safety_proven:bool=False; action_success:bool=False

@dataclass(frozen=True)
class PreparedParetoState:
    request:ParetoRequest; plans:tuple[CandidatePlan,...]; policy:PreferencePolicy
    record_fingerprints:tuple[tuple[str,str],...]; context_fingerprint:str; dependency_fingerprint:str
    policy_fingerprint:str; registry_fingerprint:str; frontier_fingerprint:str; selection_fingerprint:str
    precomputed_result:ParetoResult; binding:str; state_epoch:str

@dataclass(frozen=True)
class ParetoStateDelta:
    base_fingerprint:str; target_fingerprint:str; changed_plans:tuple[CandidatePlan,...]; removed_record_ids:tuple[str,...]
    target_request:ParetoRequest|None; target_policy:PreferencePolicy|None; binding:str; state_epoch:str

@dataclass(frozen=True)
class ParetoSyncPlan:
    missing_or_changed_record_ids:tuple[str,...]; metadata_bytes_required:int; full_resend_required:bool

def _cv(x):
    if isinstance(x,Enum): return x.name if isinstance(x,IntEnum) else x.value
    if hasattr(x,'__dataclass_fields__'): return {k:_cv(getattr(x,k)) for k in x.__dataclass_fields__}
    if isinstance(x,tuple): return [_cv(v) for v in x]
    if isinstance(x,list): return [_cv(v) for v in x]
    if isinstance(x,dict): return {str(k):_cv(x[k]) for k in sorted(x)}
    return x

def _canon(x)->bytes: return json.dumps(_cv(x),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def _fp(x)->str: return sha256(_canon(x)).hexdigest()
def _risk_cap(r,p): return {RiskClass.LOW:p.low_risk_cap,RiskClass.MEDIUM:p.medium_risk_cap,RiskClass.HIGH:p.high_risk_cap,RiskClass.CRITICAL:p.critical_risk_cap}[r]

def _hold(reason,rejected=()):
    return ParetoResult(Decision.HOLD,NextAction.HOLD_NO_SAFE_PLAN,(reason,),(),(),tuple(sorted(rejected)),None,False,False,False)

def _validate(q,plans,p):
    if p.revoked: return 'POLICY_REVOKED'
    if not q.observed or not q.request_id: return 'REQUEST_INVALID'
    if q.binding!=p.binding or q.state_epoch!=p.state_epoch: return 'SCOPE_MISMATCH'
    nums=(q.max_total_cost,q.max_total_time,q.max_total_risk,q.min_success_probability,q.min_reversibility,
          p.low_risk_cap,p.medium_risk_cap,p.high_risk_cap,p.critical_risk_cap,p.major_tradeoff_risk_delta,
          p.major_tradeoff_cost_ratio,p.major_tradeoff_time_ratio)
    if any(not math.isfinite(v) for v in nums): return 'NUMERIC_INVALID'
    if min(q.max_total_cost,q.max_total_time,q.max_total_risk)<0: return 'REQUEST_LIMIT_INVALID'
    if not (0<=q.min_success_probability<=1 and 0<=q.min_reversibility<=1): return 'REQUEST_PROBABILITY_INVALID'
    if not (p.low_risk_cap>=p.medium_risk_cap>=p.high_risk_cap>=p.critical_risk_cap>=0): return 'POLICY_RISK_CAP_NONMONOTONIC'
    if p.major_tradeoff_risk_delta<0 or p.major_tradeoff_cost_ratio<1 or p.major_tradeoff_time_ratio<1: return 'TRADEOFF_POLICY_INVALID'
    if len(p.priority_order)!=len(set(p.priority_order)): return 'DUPLICATE_POLICY_PRIORITY'
    ids=[x.plan_id for x in plans]
    if len(ids)!=len(set(ids)): return 'DUPLICATE_PLAN_ID'
    for x in plans:
        if not x.observed or not x.plan_id or not x.plan_version or not x.plan_fingerprint: return 'PLAN_INVALID'
        if x.binding!=p.binding or x.state_epoch!=p.state_epoch: return 'PLAN_SCOPE_MISMATCH'
        vals=(x.total_cost,x.total_time,x.total_risk,x.success_probability,x.reversibility)
        if any(not math.isfinite(v) for v in vals) or min(x.total_cost,x.total_time,x.total_risk)<0: return 'PLAN_NUMERIC_INVALID'
        if not (0<=x.success_probability<=1 and 0<=x.reversibility<=1): return 'PLAN_PROBABILITY_INVALID'
    return None

def _dominates(a:CandidatePlan,b:CandidatePlan)->bool:
    weak=(a.total_cost<=b.total_cost and a.total_time<=b.total_time and a.total_risk<=b.total_risk and
          a.success_probability>=b.success_probability and a.reversibility>=b.reversibility)
    strict=(a.total_cost<b.total_cost or a.total_time<b.total_time or a.total_risk<b.total_risk or
            a.success_probability>b.success_probability or a.reversibility>b.reversibility)
    return weak and strict

def _objective_key(x:CandidatePlan,obj:Objective):
    if obj==Objective.COST: return x.total_cost
    if obj==Objective.TIME: return x.total_time
    if obj==Objective.RISK: return x.total_risk
    if obj==Objective.SUCCESS: return -x.success_probability
    if obj==Objective.REVERSIBILITY: return -x.reversibility
    raise ValueError(obj)

def _tradeoffs(x,frontier):
    best_cost=min(p.total_cost for p in frontier); best_time=min(p.total_time for p in frontier); best_risk=min(p.total_risk for p in frontier)
    best_success=max(p.success_probability for p in frontier); best_rev=max(p.reversibility for p in frontier)
    out=[]
    if x.total_cost>best_cost: out.append('HIGHER_COST')
    if x.total_time>best_time: out.append('LONGER_TIME')
    if x.total_risk>best_risk: out.append('HIGHER_RISK')
    if x.success_probability<best_success: out.append('LOWER_SUCCESS')
    if x.reversibility<best_rev: out.append('LOWER_REVERSIBILITY')
    if not out: out.append('PARETO_REFERENCE')
    return tuple(out)

def _major_tradeoff(frontier,p):
    if len(frontier)<2: return False
    risks=[x.total_risk for x in frontier]; costs=[x.total_cost for x in frontier]; times=[x.total_time for x in frontier]
    risk_major=max(risks)-min(risks)>=p.major_tradeoff_risk_delta
    cmin=min(costs); tmin=min(times)
    cost_major=(max(costs)/cmin>=p.major_tradeoff_cost_ratio) if cmin>0 else max(costs)>0
    time_major=(max(times)/tmin>=p.major_tradeoff_time_ratio) if tmin>0 else max(times)>0
    return risk_major or cost_major or time_major

def evaluate(q:ParetoRequest, plans:tuple[CandidatePlan,...], p:PreferencePolicy)->ParetoResult:
    plans=tuple(plans); err=_validate(q,plans,p)
    if err: return _hold(err)
    cap=min(q.max_total_risk,_risk_cap(q.risk_class,p)); eligible=[]; rejected=[]
    for x in sorted(plans,key=lambda z:z.plan_id):
        reason=None
        if p.require_hard_constraints and not x.hard_constraint_passed: reason='HARD_CONSTRAINT'
        elif p.require_policy_allowed and not x.policy_allowed: reason='POLICY_DENIED'
        elif x.total_cost>q.max_total_cost: reason='COST_LIMIT'
        elif x.total_time>q.max_total_time: reason='TIME_LIMIT'
        elif x.total_risk>cap: reason='RISK_LIMIT'
        elif x.success_probability<q.min_success_probability: reason='SUCCESS_FLOOR'
        elif x.reversibility<q.min_reversibility: reason='REVERSIBILITY_FLOOR'
        if reason: rejected.append((x.plan_id,reason))
        else: eligible.append(x)
    if not eligible: return _hold('NO_SAFE_CANDIDATE',rejected)
    frontier=[]; dominated=[]
    for x in eligible:
        if any(_dominates(y,x) for y in eligible if y.plan_id!=x.plan_id): dominated.append(x.plan_id)
        else: frontier.append(x)
    frontier.sort(key=lambda x:(x.total_risk,x.total_cost,x.total_time,-x.success_probability,-x.reversibility,x.plan_id))
    scores=tuple(PlanScore(x.plan_id,x.total_cost,x.total_time,x.total_risk,x.success_probability,x.reversibility,_tradeoffs(x,frontier)) for x in frontier)
    major=_major_tradeoff(frontier,p)
    # Unique frontier candidate is unambiguous even without a preference order.
    if len(frontier)==1:
        selected=frontier[0].plan_id
        return ParetoResult(Decision.ALLOW,NextAction.SELECTED_PLAN_CANDIDATE,('UNIQUE_PARETO_PLAN',),scores,tuple(sorted(dominated)),tuple(sorted(rejected)),selected,False,True,True)
    if not p.priority_order:
        return ParetoResult(Decision.HUMAN_APPROVAL,NextAction.HUMAN_REVIEW_CANDIDATE,('POLICY_PRIORITY_UNRESOLVED',),scores,tuple(sorted(dominated)),tuple(sorted(rejected)),None,major,False,False)
    ordered=sorted(frontier,key=lambda x:tuple(_objective_key(x,o) for o in p.priority_order)+(x.plan_id,))
    first=ordered[0]
    # If explicit priority dimensions still tie exactly, do not invent a hidden tiebreak beyond plan identity.
    first_key=tuple(_objective_key(first,o) for o in p.priority_order)
    tied=[x for x in ordered if tuple(_objective_key(x,o) for o in p.priority_order)==first_key]
    if len(tied)>1:
        return ParetoResult(Decision.HUMAN_APPROVAL,NextAction.HUMAN_REVIEW_CANDIDATE,('POLICY_TIE_UNRESOLVED',),scores,tuple(sorted(dominated)),tuple(sorted(rejected)),None,major,False,False)
    # Major tradeoff is acceptable when policy explicitly resolves it; the evidence still remains a candidate only.
    return ParetoResult(Decision.ALLOW,NextAction.SELECTED_PLAN_CANDIDATE,('POLICY_RESOLVED_PARETO_SELECTION',),scores,tuple(sorted(dominated)),tuple(sorted(rejected)),first.plan_id,major,True,True)

def default_policy():
    return PreferencePolicy((Objective.RISK,Objective.REVERSIBILITY,Objective.COST,Objective.TIME,Objective.SUCCESS),4.0,3.0,2.0,1.0,.5,1.5,1.5,True,True,'PARETO-BIND','STATE-EPOCH-1')
def default_request():
    p=default_policy(); return ParetoRequest('REQ-108',RiskClass.LOW,20.0,20.0,4.0,.70,.50,True,p.binding,p.state_epoch)
def default_plans():
    p=default_policy(); b=p.binding; e=p.state_epoch
    return (
        CandidatePlan('PLAN-SAFE',8.0,8.0,.4,.93,.95,True,True,True,'V1','FP-SAFE',b,e),
        CandidatePlan('PLAN-FAST',9.0,4.0,.9,.96,.75,True,True,True,'V1','FP-FAST',b,e),
        CandidatePlan('PLAN-CHEAP',4.0,10.0,.8,.90,.80,True,True,True,'V1','FP-CHEAP',b,e),
        CandidatePlan('PLAN-DOMINATED',10.0,11.0,1.2,.80,.60,True,True,True,'V1','FP-DOM',b,e),
        CandidatePlan('PLAN-UNSAFE',1.0,1.0,.1,.99,1.0,False,False,True,'V1','FP-UNSAFE',b,e),
    )
def default_evaluation(): return evaluate(default_request(),default_plans(),default_policy())

def _record_fps(plans): return tuple((f'PLAN:{x.plan_id}',_fp(x)) for x in sorted(plans,key=lambda y:y.plan_id))
def _context_fp(q): return _fp(q)
def _dependency_fp(plans): return _fp(tuple((x.plan_id,x.plan_version,x.plan_fingerprint) for x in sorted(plans,key=lambda y:y.plan_id)))
def _policy_fp(p): return _fp(p)
def _registry_fp(q,plans,p): return _fp((q,_record_fps(plans),p))
def _frontier_fp(q,plans): return _fp((q.risk_class,q.max_total_cost,q.max_total_time,q.max_total_risk,q.min_success_probability,q.min_reversibility,tuple((x.plan_id,x.total_cost,x.total_time,x.total_risk,x.success_probability,x.reversibility,x.hard_constraint_passed,x.policy_allowed) for x in sorted(plans,key=lambda y:y.plan_id))))
def _selection_fp(p): return _fp((p.priority_order,p.major_tradeoff_risk_delta,p.major_tradeoff_cost_ratio,p.major_tradeoff_time_ratio))

def prepare_state(q,plans,p,*,binding,state_epoch):
    plans=tuple(plans); fps=_record_fps(plans)
    return PreparedParetoState(q,plans,p,fps,_context_fp(q),_dependency_fp(plans),_policy_fp(p),_registry_fp(q,plans,p),_frontier_fp(q,plans),_selection_fp(p),evaluate(q,plans,p),binding,state_epoch)
def validate_prepared_integrity(st):
    return (st.binding==st.request.binding==st.policy.binding and st.state_epoch==st.request.state_epoch==st.policy.state_epoch and
            st.record_fingerprints==_record_fps(st.plans) and st.context_fingerprint==_context_fp(st.request) and
            st.dependency_fingerprint==_dependency_fp(st.plans) and st.policy_fingerprint==_policy_fp(st.policy) and
            st.registry_fingerprint==_registry_fp(st.request,st.plans,st.policy) and st.frontier_fingerprint==_frontier_fp(st.request,st.plans) and
            st.selection_fingerprint==_selection_fp(st.policy) and st.precomputed_result==evaluate(st.request,st.plans,st.policy))
def evaluate_prepared(st,*,integrity_validated,current_context_fingerprint,current_dependency_fingerprint,current_policy_fingerprint,current_registry_fingerprint,current_frontier_fingerprint,current_selection_fingerprint):
    if not integrity_validated: return _hold('PREPARED_INTEGRITY_NOT_VALIDATED')
    if (st.context_fingerprint!=current_context_fingerprint or st.dependency_fingerprint!=current_dependency_fingerprint or
        st.policy_fingerprint!=current_policy_fingerprint or st.registry_fingerprint!=current_registry_fingerprint or
        st.frontier_fingerprint!=current_frontier_fingerprint or st.selection_fingerprint!=current_selection_fingerprint):
        return _hold('PREPARED_FINGERPRINT_MISMATCH_REEVALUATION_REQUIRED')
    return st.precomputed_result

def make_delta(base,target):
    bm=dict(base.record_fingerprints); tm=dict(target.record_fingerprints); pm={f'PLAN:{x.plan_id}':x for x in target.plans}
    changed=tuple(pm[k] for k,v in tm.items() if bm.get(k)!=v); removed=tuple(k for k in bm if k not in tm)
    return ParetoStateDelta(base.registry_fingerprint,target.registry_fingerprint,changed,removed,target.request if base.request!=target.request else None,target.policy if base.policy!=target.policy else None,target.binding,target.state_epoch)
def plan_missing_only(local,target):
    lm=dict(local.record_fingerprints); tm=dict(target.record_fingerprints); ids=tuple(k for k,v in tm.items() if lm.get(k)!=v)
    return ParetoSyncPlan(ids,len(_canon(ids)),False)
