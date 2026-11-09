"""NOEPIN AL 110 — Resource-Bounded Planner — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Pure deterministic resource-constrained planning evidence. The planner searches only
eligible action edges, tracks cumulative multi-resource use, prunes hard-budget
violations, preserves explicitly mandatory safety actions, and prefers plans that retain
configured reserve budget. If the goal needs more budget, it returns HOLD or a
HUMAN_APPROVAL candidate; it never grants additional budget, permission, credentials,
execution, publication, external writes, world truth, safety proof, or action success.

Canonical identity: NOEPIN-AL-110
DCSR level: AUXILIARY INTEGRATION / 補助統合.
Provenance note: exact registered Origin GUID was not freshly reverified in this
completion session and is intentionally not guessed or regenerated.
Pre-existing Notion V1 attachment byte identity was not freshly reverified.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum, IntEnum
from hashlib import sha256
import heapq, json, math

class Decision(str, Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class RiskClass(IntEnum): LOW=0; MEDIUM=1; HIGH=2; CRITICAL=3
class Escalation(str, Enum):
    NONE='NONE'; RESOURCE_SHORTFALL_CANDIDATE='RESOURCE_SHORTFALL_CANDIDATE'; REPLAN_CANDIDATE='REPLAN_CANDIDATE'
class NextAction(str, Enum):
    FEASIBLE_PLAN_CANDIDATE='FEASIBLE_PLAN_CANDIDATE'
    ADDITIONAL_BUDGET_REVIEW_CANDIDATE='ADDITIONAL_BUDGET_REVIEW_CANDIDATE'
    HOLD_REPLAN_CANDIDATE='HOLD_REPLAN_CANDIDATE'

@dataclass(frozen=True)
class ResourceLimit:
    resource: str
    hard_limit: float
    reserve_required: float
    unit: str
    weight: float

@dataclass(frozen=True)
class ActionRecord:
    action_id: str
    from_state: str
    to_state: str
    resource_cost: tuple[tuple[str,float],...]
    risk: float
    mandatory_safety: bool
    hard_constraint_passed: bool
    policy_allowed: bool
    action_version: str
    action_fingerprint: str
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class PlanRequest:
    request_id: str
    start_state: str
    goal_state: str
    risk_class: RiskClass
    additional_budget_candidate_allowed: bool
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class PlannerPolicy:
    low_risk_cap: float
    medium_risk_cap: float
    high_risk_cap: float
    critical_risk_cap: float
    max_expansions: int
    require_hard_constraints: bool
    require_policy_allowed: bool
    require_reserve: bool
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class ResourceForecast:
    resource: str
    used: float
    hard_limit: float
    remaining: float
    reserve_required: float
    reserve_margin: float

@dataclass(frozen=True)
class ResourceShortfall:
    resource: str
    required_additional: float
    basis: str

@dataclass(frozen=True)
class PlanResult:
    decision: Decision
    next_action: NextAction
    escalation: Escalation
    reasons: tuple[str,...]
    plan: tuple[str,...]
    total_costs: tuple[tuple[str,float],...]
    resource_forecast: tuple[ResourceForecast,...]
    shortfall: tuple[ResourceShortfall,...]
    expanded_nodes: int
    budget_feasible: bool
    reserve_satisfied: bool
    mandatory_safety_preserved: bool
    next_gate_candidate: bool
    plan_promoted_to_permission: bool=False
    permission_granted: bool=False
    budget_granted: bool=False
    credential_granted: bool=False
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
class PreparedResourceState:
    request: PlanRequest
    actions: tuple[ActionRecord,...]
    limits: tuple[ResourceLimit,...]
    policy: PlannerPolicy
    record_fingerprints: tuple[tuple[str,str],...]
    context_fingerprint: str
    dependency_fingerprint: str
    policy_fingerprint: str
    budget_fingerprint: str
    registry_fingerprint: str
    frontier_fingerprint: str
    precomputed_result: PlanResult
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class ResourceStateDelta:
    base_registry_fingerprint: str
    target_registry_fingerprint: str
    changed_actions: tuple[ActionRecord,...]
    changed_limits: tuple[ResourceLimit,...]
    removed_record_ids: tuple[str,...]
    request_replacement: PlanRequest|None
    policy_replacement: PlannerPolicy|None
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class ResourceSyncPlan:
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

def _risk_cap(q,p):
    return {RiskClass.LOW:p.low_risk_cap,RiskClass.MEDIUM:p.medium_risk_cap,RiskClass.HIGH:p.high_risk_cap,RiskClass.CRITICAL:p.critical_risk_cap}[q.risk_class]

def _cost_map(a): return {k:float(v) for k,v in a.resource_cost}
def _zero(limits): return {r.resource:0.0 for r in limits}
def _cost_tuple(cost,limits): return tuple((r.resource,float(cost.get(r.resource,0.0))) for r in limits)

def _forecast(cost,limits):
    out=[]
    for r in limits:
        used=float(cost.get(r.resource,0.0)); rem=r.hard_limit-used
        out.append(ResourceForecast(r.resource,used,r.hard_limit,rem,r.reserve_required,rem-r.reserve_required))
    return tuple(out)

def _shortfall(cost,limits,basis):
    out=[]
    for r in limits:
        used=float(cost.get(r.resource,0.0))
        need=max(0.0,used + (r.reserve_required if basis=='RESERVE' else 0.0) - r.hard_limit)
        if need>1e-12: out.append(ResourceShortfall(r.resource,need,basis))
    return tuple(out)

def _empty(reason,decision=Decision.HOLD,next_action=NextAction.HOLD_REPLAN_CANDIDATE,escalation=Escalation.REPLAN_CANDIDATE,shortfall=()):
    return PlanResult(decision,next_action,escalation,(reason,),(),(),(),tuple(shortfall),0,False,False,False,False)

def _validate(q,actions,limits,p):
    if not isinstance(q,PlanRequest) or not isinstance(p,PlannerPolicy): return 'TYPE_INVALID'
    if not q.request_id or not q.start_state or not q.goal_state or q.start_state==q.goal_state: return 'REQUEST_INVALID'
    if q.binding!=p.binding or q.state_epoch!=p.state_epoch: return 'REQUEST_POLICY_BINDING_MISMATCH'
    if p.max_expansions<=0 or any(not math.isfinite(x) or x<0 for x in (p.low_risk_cap,p.medium_risk_cap,p.high_risk_cap,p.critical_risk_cap)): return 'POLICY_INVALID'
    if not limits: return 'NO_RESOURCE_LIMITS'
    names=[x.resource for x in limits]
    if len(names)!=len(set(names)) or any(not x.resource or not x.unit for x in limits): return 'RESOURCE_LIMIT_INVALID'
    for x in limits:
        if any(not math.isfinite(v) for v in (x.hard_limit,x.reserve_required,x.weight)) or x.hard_limit<0 or x.reserve_required<0 or x.reserve_required>x.hard_limit or x.weight<=0: return 'RESOURCE_LIMIT_INVALID'
    ids=[x.action_id for x in actions]
    if len(ids)!=len(set(ids)): return 'DUPLICATE_ACTION_ID'
    known=set(names)
    for x in actions:
        if not x.action_id or not x.from_state or not x.to_state or x.from_state==x.to_state: return 'ACTION_INVALID'
        if x.binding!=q.binding or x.state_epoch!=q.state_epoch: return 'ACTION_BINDING_MISMATCH'
        if not math.isfinite(x.risk) or x.risk<0: return 'ACTION_RISK_INVALID'
        cm=_cost_map(x)
        if len(cm)!=len(x.resource_cost) or set(cm)-known: return 'ACTION_RESOURCE_INVALID'
        if any((not math.isfinite(v) or v<0) for v in cm.values()): return 'ACTION_RESOURCE_INVALID'
    return None

def _eligible(actions,q,p):
    cap=_risk_cap(q,p); out=[]
    for a in actions:
        if p.require_hard_constraints and not a.hard_constraint_passed: continue
        if p.require_policy_allowed and not a.policy_allowed: continue
        if a.risk>cap: continue
        out.append(a)
    return tuple(sorted(out,key=lambda x:(x.from_state,x.to_state,x.action_id)))

def _add(cost,a,limits):
    c=dict(cost); ac=_cost_map(a)
    for r in limits: c[r.resource]=c.get(r.resource,0.0)+ac.get(r.resource,0.0)
    return c

def _hard_ok(cost,limits): return all(cost.get(r.resource,0.0)<=r.hard_limit+1e-12 for r in limits)
def _reserve_ok(cost,limits): return all(cost.get(r.resource,0.0)+r.reserve_required<=r.hard_limit+1e-12 for r in limits)
def _score(cost,limits):
    s=0.0
    for r in limits:
        denom=max(r.hard_limit,1e-12); s += r.weight*(cost.get(r.resource,0.0)/denom)
    return s

def _dominates(a,b,limits):
    le=all(a.get(r.resource,0.0)<=b.get(r.resource,0.0)+1e-12 for r in limits)
    lt=any(a.get(r.resource,0.0)<b.get(r.resource,0.0)-1e-12 for r in limits)
    return le and lt

def _search(q,actions,limits,p,hard_budget=True):
    eligible=_eligible(actions,q,p); adj={}
    for a in eligible: adj.setdefault(a.from_state,[]).append(a)
    mandatory={a.action_id for a in actions if a.mandatory_safety}
    start_cost=_zero(limits); heap=[]; serial=0
    heapq.heappush(heap,(_score(start_cost,limits),(),q.start_state,(),start_cost,serial)); serial+=1
    labels={}; goals=[]; expanded=0
    while heap and expanded<p.max_expansions:
        sc,path,state,used_mand,cost,_s=heapq.heappop(heap); expanded+=1
        mand=frozenset(used_mand)
        key=(state,tuple(sorted(mand)))
        vecs=labels.setdefault(key,[])
        if any(_dominates(v,cost,limits) or all(abs(v.get(r.resource,0)-cost.get(r.resource,0))<=1e-12 for r in limits) for v in vecs):
            if vecs: continue
        vecs[:]=[v for v in vecs if not _dominates(cost,v,limits)]; vecs.append(cost)
        if state==q.goal_state and mandatory.issubset(mand):
            goals.append((sc,path,cost,expanded)); continue
        for a in adj.get(state,()):
            if a.action_id in path: continue
            nc=_add(cost,a,limits)
            if hard_budget and not _hard_ok(nc,limits): continue
            nm=tuple(sorted(set(mand)|({a.action_id} if a.mandatory_safety else set())))
            np=path+(a.action_id,)
            heapq.heappush(heap,(_score(nc,limits),np,a.to_state,nm,nc,serial)); serial+=1
    goals.sort(key=lambda x:(not _reserve_ok(x[2],limits),x[0],x[1]))
    return goals,expanded

def evaluate(q:PlanRequest,actions:tuple[ActionRecord,...],limits:tuple[ResourceLimit,...],p:PlannerPolicy)->PlanResult:
    actions=tuple(actions); limits=tuple(sorted(limits,key=lambda x:x.resource)); err=_validate(q,actions,limits,p)
    if err: return _empty(err)
    goals,expanded=_search(q,actions,limits,p,True)
    if goals:
        reserve_goals=[g for g in goals if _reserve_ok(g[2],limits)]
        chosen=(reserve_goals or goals)[0]; _sc,path,cost,_=chosen
        fc=_forecast(cost,limits); mand={a.action_id for a in actions if a.mandatory_safety}; preserved=mand.issubset(set(path))
        if not preserved: return _empty('MANDATORY_SAFETY_NOT_PRESERVED')
        if reserve_goals or not p.require_reserve:
            return PlanResult(Decision.ALLOW,NextAction.FEASIBLE_PLAN_CANDIDATE,Escalation.NONE,('RESOURCE_BUDGET_FEASIBLE','REQUIRED_SAFETY_PRESERVED','RESERVE_BUDGET_SATISFIED' if reserve_goals else 'RESERVE_NOT_REQUIRED'),path,_cost_tuple(cost,limits),fc,(),expanded,True,bool(reserve_goals),True,True)
        sf=_shortfall(cost,limits,'RESERVE')
        if q.additional_budget_candidate_allowed:
            return PlanResult(Decision.HUMAN_APPROVAL,NextAction.ADDITIONAL_BUDGET_REVIEW_CANDIDATE,Escalation.RESOURCE_SHORTFALL_CANDIDATE,('HARD_BUDGET_FEASIBLE','RESERVE_BUDGET_SHORTFALL','ADDITIONAL_BUDGET_REVIEW_ONLY'),path,_cost_tuple(cost,limits),fc,sf,expanded,True,False,True,False)
        return PlanResult(Decision.HOLD,NextAction.HOLD_REPLAN_CANDIDATE,Escalation.REPLAN_CANDIDATE,('RESERVE_BUDGET_SHORTFALL','NO_AUTOMATIC_BUDGET_INCREASE'),path,_cost_tuple(cost,limits),fc,sf,expanded,True,False,True,False)
    # No hard-budget feasible goal. Find an evidence-only unconstrained route to quantify shortfall.
    ub,expanded2=_search(q,actions,limits,p,False)
    if ub:
        _sc,path,cost,_=ub[0]; fc=_forecast(cost,limits); sf=_shortfall(cost,limits,'HARD_LIMIT')
        if q.additional_budget_candidate_allowed:
            return PlanResult(Decision.HUMAN_APPROVAL,NextAction.ADDITIONAL_BUDGET_REVIEW_CANDIDATE,Escalation.RESOURCE_SHORTFALL_CANDIDATE,('HARD_BUDGET_SHORTFALL','ADDITIONAL_BUDGET_REVIEW_ONLY','BUDGET_NOT_GRANTED'),path,_cost_tuple(cost,limits),fc,sf,expanded+expanded2,False,False,True,False)
        return PlanResult(Decision.HOLD,NextAction.HOLD_REPLAN_CANDIDATE,Escalation.REPLAN_CANDIDATE,('HARD_BUDGET_SHORTFALL','NO_AUTOMATIC_BUDGET_INCREASE'),path,_cost_tuple(cost,limits),fc,sf,expanded+expanded2,False,False,True,False)
    return _empty('NO_ELIGIBLE_ROUTE')

def default_limits():
    return (
        ResourceLimit('api_calls',10,2,'calls',1.2), ResourceLimit('cpu_seconds',12,2,'s',1.0),
        ResourceLimit('memory_mb',768,128,'MB',.4), ResourceLimit('money_usd',2.0,.4,'USD',1.5),
        ResourceLimit('tokens',4000,800,'tokens',1.0), ResourceLimit('tool_calls',20,4,'calls',1.2),
    )
def default_policy(): return PlannerPolicy(1.0,2.0,3.0,4.0,10000,True,True,True,'RESOURCE-BIND','STATE-EPOCH-1')
def default_request():
    p=default_policy(); return PlanRequest('REQ-110','START','GOAL',RiskClass.LOW,True,p.binding,p.state_epoch)
def _rc(**kw): return tuple(sorted(((k,float(v)) for k,v in kw.items()),key=lambda x:x[0]))
def default_actions():
    p=default_policy(); b=p.binding; e=p.state_epoch
    return (
        ActionRecord('PREPARE','START','PREPARED',_rc(tokens=300,api_calls=1,cpu_seconds=.5,memory_mb=80,money_usd=.03,tool_calls=1),.2,False,True,True,'V1','FP-PREP',b,e),
        ActionRecord('SAFETY-VERIFY','PREPARED','VERIFIED',_rc(tokens=250,api_calls=1,cpu_seconds=.4,memory_mb=40,money_usd=.02,tool_calls=1),.3,True,True,True,'V1','FP-SAFE',b,e),
        ActionRecord('BUILD','VERIFIED','BUILT',_rc(tokens=900,api_calls=2,cpu_seconds=2.0,memory_mb=160,money_usd=.18,tool_calls=3),.5,False,True,True,'V1','FP-BUILD',b,e),
        ActionRecord('FINAL-CHECK','BUILT','GOAL',_rc(tokens=300,api_calls=1,cpu_seconds=.6,memory_mb=40,money_usd=.03,tool_calls=1),.4,False,True,True,'V1','FP-CHECK',b,e),
        ActionRecord('EXPENSIVE-DIRECT','START','GOAL',_rc(tokens=3500,api_calls=9,cpu_seconds=10,memory_mb=700,money_usd=1.8,tool_calls=18),.8,False,True,True,'V1','FP-DIRECT',b,e),
    )
def default_evaluation(): return evaluate(default_request(),default_actions(),default_limits(),default_policy())

def _record_fps(actions,limits):
    a=tuple((f'ACTION:{x.action_id}',_fp(x)) for x in sorted(actions,key=lambda y:y.action_id))
    r=tuple((f'RESOURCE:{x.resource}',_fp(x)) for x in sorted(limits,key=lambda y:y.resource))
    return a+r

def _context_fp(q): return _fp(q)
def _dependency_fp(actions): return _fp(tuple((x.action_id,x.from_state,x.to_state,x.mandatory_safety,x.action_version,x.action_fingerprint) for x in sorted(actions,key=lambda y:y.action_id)))
def _policy_fp(p): return _fp(p)
def _budget_fp(limits): return _fp(tuple(sorted(limits,key=lambda x:x.resource)))
def _registry_fp(q,actions,limits,p): return _fp((q,_record_fps(actions,limits),p))
def _frontier_fp(q,actions,limits,p): return _fp((q.start_state,q.goal_state,q.risk_class,_dependency_fp(actions),_budget_fp(limits),_risk_cap(q,p)))

def prepare_state(q,actions,limits,p,*,binding,state_epoch):
    actions=tuple(actions); limits=tuple(sorted(limits,key=lambda x:x.resource)); fps=_record_fps(actions,limits)
    return PreparedResourceState(q,actions,limits,p,fps,_context_fp(q),_dependency_fp(actions),_policy_fp(p),_budget_fp(limits),_registry_fp(q,actions,limits,p),_frontier_fp(q,actions,limits,p),evaluate(q,actions,limits,p),binding,state_epoch)
def validate_prepared_integrity(st):
    return (st.binding==st.request.binding==st.policy.binding and st.state_epoch==st.request.state_epoch==st.policy.state_epoch and
            st.record_fingerprints==_record_fps(st.actions,st.limits) and st.context_fingerprint==_context_fp(st.request) and
            st.dependency_fingerprint==_dependency_fp(st.actions) and st.policy_fingerprint==_policy_fp(st.policy) and
            st.budget_fingerprint==_budget_fp(st.limits) and st.registry_fingerprint==_registry_fp(st.request,st.actions,st.limits,st.policy) and
            st.frontier_fingerprint==_frontier_fp(st.request,st.actions,st.limits,st.policy) and st.precomputed_result==evaluate(st.request,st.actions,st.limits,st.policy))
def evaluate_prepared(st,*,integrity_validated,current_context_fingerprint,current_dependency_fingerprint,current_policy_fingerprint,current_budget_fingerprint,current_registry_fingerprint,current_frontier_fingerprint):
    if not integrity_validated: return _empty('PREPARED_INTEGRITY_NOT_VALIDATED')
    if (st.context_fingerprint!=current_context_fingerprint or st.dependency_fingerprint!=current_dependency_fingerprint or st.policy_fingerprint!=current_policy_fingerprint or st.budget_fingerprint!=current_budget_fingerprint or st.registry_fingerprint!=current_registry_fingerprint or st.frontier_fingerprint!=current_frontier_fingerprint):
        return _empty('PREPARED_FINGERPRINT_MISMATCH_REEVALUATION_REQUIRED')
    return st.precomputed_result

def make_delta(base,target):
    bm=dict(base.record_fingerprints); tm=dict(target.record_fingerprints)
    amap={f'ACTION:{x.action_id}':x for x in target.actions}; rmap={f'RESOURCE:{x.resource}':x for x in target.limits}
    changed_actions=tuple(amap[k] for k,v in tm.items() if k.startswith('ACTION:') and bm.get(k)!=v)
    changed_limits=tuple(rmap[k] for k,v in tm.items() if k.startswith('RESOURCE:') and bm.get(k)!=v)
    removed=tuple(sorted(k for k in bm if k not in tm))
    return ResourceStateDelta(base.registry_fingerprint,target.registry_fingerprint,changed_actions,changed_limits,removed,target.request if base.request!=target.request else None,target.policy if base.policy!=target.policy else None,target.binding,target.state_epoch)
def plan_missing_only(local,target):
    lm=dict(local.record_fingerprints); tm=dict(target.record_fingerprints); ids=tuple(sorted(k for k,v in tm.items() if lm.get(k)!=v))
    return ResourceSyncPlan(ids,len(_canon(ids)),False)
