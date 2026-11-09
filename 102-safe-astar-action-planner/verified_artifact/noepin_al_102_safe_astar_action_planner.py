"""NOEPIN AL 102 — Safe A* Action Planner — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Pure planning candidate evidence. This module performs A* search only across actions
whose hard-constraint evidence passed, combines execution cost with risk-weighted
cost, prefers lower risk on equal cost, and returns HOLD rather than a dangerous
route when no safe path exists or budgets are exceeded. A Safe Plan is only a plan
candidate: it is never Permission Grant, Action Execution, Commit/Publish,
Production Authority, Safety Proof, or Action Success.

Canonical identity: NOEPIN-AL-102
DCSR level: AUXILIARY INTEGRATION / 補助統合.
Provenance note: exact registered Origin GUID was not freshly reverified in this
completion session and is intentionally not guessed or regenerated.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, IntEnum
from hashlib import sha256
import heapq, json, math

class Decision(str,Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class RiskClass(IntEnum):
    LOW=0; MEDIUM=1; HIGH=2; CRITICAL=3
class NextAction(str,Enum):
    SAFE_PLAN_CANDIDATE='SAFE_PLAN_CANDIDATE'; REPLAN_CANDIDATE='REPLAN_CANDIDATE'; CONSTRAINT_REPAIR_CANDIDATE='CONSTRAINT_REPAIR_CANDIDATE'; HOLD_UNRESOLVED='HOLD_UNRESOLVED'

@dataclass(frozen=True)
class PlanningRequest:
    request_id:str; start_state:str; goal_state:str; risk:RiskClass; max_total_cost:float; max_total_risk:float
    observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class ActionEdge:
    action_id:str; from_state:str; to_state:str; execution_cost:float; risk_cost:float
    hard_constraint_passed:bool; constraint_reason:str; action_version:str; action_fingerprint:str
    observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class PlannerPolicy:
    risk_weight:float; max_expansions:int; low_risk_cap:float; medium_risk_cap:float; high_risk_cap:float; critical_risk_cap:float
    require_hard_constraints:bool; binding:str; state_epoch:str; revoked:bool=False
@dataclass(frozen=True)
class SafePlanResult:
    decision:Decision; next_action:NextAction; reasons:tuple[str,...]; safe_plan:tuple[str,...]
    state_trace:tuple[str,...]; total_cost:float; execution_cost:float; total_risk:float; risk_trace:tuple[float,...]
    expanded_nodes:int; hard_constraint_exclusions:int; budget_exceeded:bool; next_gate_candidate:bool
    safe_plan_promoted_to_permission:bool=False; permission_granted:bool=False; action_executed:bool=False
    plan_committed:bool=False; atomic_publish_executed:bool=False; external_write_performed:bool=False
    world_truth_proven:bool=False; domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedPlannerState:
    request:PlanningRequest; actions:tuple[ActionEdge,...]; policy:PlannerPolicy
    action_fingerprints:tuple[tuple[str,str],...]; context_fingerprint:str; dependency_fingerprint:str
    policy_fingerprint:str; registry_fingerprint:str; frontier_fingerprint:str; heuristic_fingerprint:str
    precomputed_result:SafePlanResult; binding:str; state_epoch:str
@dataclass(frozen=True)
class PlannerStateDelta:
    base_fingerprint:str; target_fingerprint:str; changed_actions:tuple[ActionEdge,...]; removed_action_ids:tuple[str,...]
    target_request:PlanningRequest|None; target_policy:PlannerPolicy|None; binding:str; state_epoch:str
@dataclass(frozen=True)
class PlannerSyncPlan:
    missing_or_changed_action_ids:tuple[str,...]; metadata_bytes_required:int; full_resend_required:bool

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

def _validate(req,actions,p):
    if p.revoked: return 'POLICY_REVOKED'
    if not req.observed or not req.request_id or not req.start_state or not req.goal_state: return 'REQUEST_INVALID'
    if req.binding!=p.binding or req.state_epoch!=p.state_epoch: return 'REQUEST_SCOPE_MISMATCH'
    vals=(req.max_total_cost,req.max_total_risk,p.risk_weight,p.low_risk_cap,p.medium_risk_cap,p.high_risk_cap,p.critical_risk_cap)
    if any(not math.isfinite(v) or v<0 for v in vals): return 'NUMERIC_VALUE_INVALID'
    if p.max_expansions<=0: return 'POLICY_EXPANSION_BUDGET_INVALID'
    if not (p.low_risk_cap>=p.medium_risk_cap>=p.high_risk_cap>=p.critical_risk_cap>=0): return 'POLICY_RISK_CAP_NONMONOTONIC'
    ids=[a.action_id for a in actions]
    if len(ids)!=len(set(ids)): return 'DUPLICATE_ACTION_ID'
    for a in actions:
        if not a.observed or not a.action_id or not a.from_state or not a.to_state or not a.action_version or not a.action_fingerprint: return 'ACTION_INVALID'
        if a.binding!=p.binding or a.state_epoch!=p.state_epoch: return 'ACTION_SCOPE_MISMATCH'
        if not math.isfinite(a.execution_cost) or not math.isfinite(a.risk_cost) or a.execution_cost<0 or a.risk_cost<0: return 'ACTION_COST_INVALID'
        if p.require_hard_constraints and not a.hard_constraint_passed and not a.constraint_reason: return 'CONSTRAINT_EVIDENCE_INVALID'
    return None

def _hold(reason,*,action=NextAction.HOLD_UNRESOLVED,expanded=0,excluded=0,budget=False):
    return SafePlanResult(Decision.HOLD,action,(reason,),(),(),0.0,0.0,0.0,(),expanded,excluded,budget,False)

def evaluate(req:PlanningRequest,actions:tuple[ActionEdge,...],p:PlannerPolicy)->SafePlanResult:
    actions=tuple(actions); err=_validate(req,actions,p)
    if err: return _hold(err)
    if req.start_state==req.goal_state:
        return SafePlanResult(Decision.ALLOW,NextAction.SAFE_PLAN_CANDIDATE,('GOAL_ALREADY_SATISFIED','SAFE_PLAN_CANDIDATE_ONLY'),(),(req.start_state,),0.0,0.0,0.0,(),0,0,False,True)
    outgoing={}; excluded=0
    for a in actions:
        if p.require_hard_constraints and not a.hard_constraint_passed:
            excluded+=1; continue
        outgoing.setdefault(a.from_state,[]).append(a)
    for k in outgoing: outgoing[k].sort(key=lambda a:(a.action_id,a.to_state))
    risk_cap=min(req.max_total_risk,_risk_cap(req.risk,p))
    # A* with h=0 fallback: zero is admissible for all nonnegative edge costs.
    # Queue ordering includes cumulative risk after f/g so equal-cost routes prefer lower risk.
    pq=[(0.0,0.0,0.0,0,req.start_state,(),(req.start_state,),())]
    best={(req.start_state,0.0):(0.0,0.0)}
    expanded=0; saw_cost_budget=False; saw_risk_budget=False
    while pq:
        f,g,risk,steps,state,plan,states,risks=heapq.heappop(pq)
        expanded+=1
        if expanded>p.max_expansions:
            return _hold('SEARCH_EXPANSION_BUDGET_EXCEEDED',action=NextAction.REPLAN_CANDIDATE,expanded=expanded-1,excluded=excluded,budget=True)
        if state==req.goal_state:
            exec_cost=sum(next(a.execution_cost for a in actions if a.action_id==aid) for aid in plan)
            reasons=['SAFE_PATH_FOUND','HARD_CONSTRAINTS_PRESERVED','SAFE_PLAN_CANDIDATE_ONLY']
            if excluded: reasons.append('UNSAFE_ACTIONS_EXCLUDED')
            return SafePlanResult(Decision.ALLOW,NextAction.SAFE_PLAN_CANDIDATE,tuple(reasons),plan,states,round(g,12),round(exec_cost,12),round(risk,12),tuple(round(x,12) for x in risks),expanded,excluded,False,True)
        for a in outgoing.get(state,()):
            nrisk=risk+a.risk_cost
            ng=g+a.execution_cost+p.risk_weight*a.risk_cost
            if nrisk>risk_cap+1e-12:
                saw_risk_budget=True; continue
            if ng>req.max_total_cost+1e-12:
                saw_cost_budget=True; continue
            # h=0 admissible; deterministic queue order gives stable replay.
            key=(a.to_state,round(nrisk,12))
            old=best.get(key)
            cand=(ng,nrisk)
            if old is not None and old<=cand: continue
            best[key]=cand
            heapq.heappush(pq,(ng,ng,nrisk,steps+1,a.to_state,plan+(a.action_id,),states+(a.to_state,),risks+(a.risk_cost,)))
    if saw_cost_budget or saw_risk_budget:
        return _hold('SAFE_PATH_BUDGET_EXCEEDED',action=NextAction.REPLAN_CANDIDATE,expanded=expanded,excluded=excluded,budget=True)
    if excluded:
        return _hold('NO_SAFE_PATH_CONSTRAINTS_EXCLUDE_ALL_ROUTES',action=NextAction.CONSTRAINT_REPAIR_CANDIDATE,expanded=expanded,excluded=excluded)
    return _hold('NO_SAFE_PATH',action=NextAction.REPLAN_CANDIDATE,expanded=expanded,excluded=excluded)

def default_policy():
    return PlannerPolicy(.50,1000,10.0,8.0,5.0,2.0,True,'SAFE-ASTAR-BIND','STATE-EPOCH-1')
def default_request():
    p=default_policy(); return PlanningRequest('REQ-102','S0','GOAL',RiskClass.LOW,20.0,10.0,True,p.binding,p.state_epoch)
def default_actions():
    p=default_policy(); b=p.binding; e=p.state_epoch
    return (
      ActionEdge('A-SAFE-1','S0','S1',2.0,.2,True,'PASS','A1','FP-A1',True,b,e),
      ActionEdge('A-SAFE-2','S1','GOAL',2.0,.2,True,'PASS','A1','FP-A2',True,b,e),
      ActionEdge('A-DANGER','S0','GOAL',.5,9.0,False,'HARD_CONSTRAINT_VIOLATION','A1','FP-AD',True,b,e),
    )
def default_evaluation(): return evaluate(default_request(),default_actions(),default_policy())

def _action_fps(actions): return tuple((f'ACTION:{a.action_id}',_fp(a)) for a in sorted(actions,key=lambda x:x.action_id))
def _context_fp(req): return _fp(req)
def _dependency_fp(actions): return _fp(_action_fps(actions))
def _policy_fp(p): return _fp(p)
def _registry_fp(req,actions,p): return _fp((req,_action_fps(actions),p))
def _frontier_fp(req,actions,p):
    # Derived search-subproblem identity only; not authoritative state.
    safe=tuple((a.action_id,a.from_state,a.to_state,a.execution_cost,a.risk_cost) for a in sorted(actions,key=lambda x:x.action_id) if a.hard_constraint_passed)
    return _fp((req.start_state,req.goal_state,safe,p.risk_weight,p.max_expansions))
def _heuristic_fp(req,actions): return _fp(('ZERO_ADMISSIBLE_HEURISTIC',req.goal_state,tuple(sorted({a.to_state for a in actions}|{a.from_state for a in actions}))))
def prepare_state(req,actions,p,*,binding:str,state_epoch:str):
    actions=tuple(actions); fps=_action_fps(actions)
    return PreparedPlannerState(req,actions,p,fps,_context_fp(req),_dependency_fp(actions),_policy_fp(p),_registry_fp(req,actions,p),_frontier_fp(req,actions,p),_heuristic_fp(req,actions),evaluate(req,actions,p),binding,state_epoch)
def validate_prepared_integrity(st):
    return (st.binding==st.policy.binding==st.request.binding and st.state_epoch==st.policy.state_epoch==st.request.state_epoch and
            st.action_fingerprints==_action_fps(st.actions) and st.context_fingerprint==_context_fp(st.request) and
            st.dependency_fingerprint==_dependency_fp(st.actions) and st.policy_fingerprint==_policy_fp(st.policy) and
            st.registry_fingerprint==_registry_fp(st.request,st.actions,st.policy) and st.frontier_fingerprint==_frontier_fp(st.request,st.actions,st.policy) and
            st.heuristic_fingerprint==_heuristic_fp(st.request,st.actions) and st.precomputed_result==evaluate(st.request,st.actions,st.policy))
def evaluate_prepared(st,*,integrity_validated:bool,current_context_fingerprint:str,current_dependency_fingerprint:str,current_policy_fingerprint:str,current_registry_fingerprint:str,current_frontier_fingerprint:str,current_heuristic_fingerprint:str):
    if not integrity_validated:
        return _hold('PREPARED_INTEGRITY_NOT_VALIDATED')
    if (st.context_fingerprint!=current_context_fingerprint or st.dependency_fingerprint!=current_dependency_fingerprint or
        st.policy_fingerprint!=current_policy_fingerprint or st.registry_fingerprint!=current_registry_fingerprint or
        st.frontier_fingerprint!=current_frontier_fingerprint or st.heuristic_fingerprint!=current_heuristic_fingerprint):
        return _hold('PREPARED_FINGERPRINT_MISMATCH_REEVALUATION_REQUIRED',action=NextAction.REPLAN_CANDIDATE)
    return st.precomputed_result

def make_delta(base:PreparedPlannerState,target:PreparedPlannerState):
    bm=dict(base.action_fingerprints); tm=dict(target.action_fingerprints); tby={a.action_id:a for a in target.actions}
    changed=tuple(tby[k[7:]] for k,v in tm.items() if bm.get(k)!=v)
    removed=tuple(k[7:] for k in bm if k not in tm)
    return PlannerStateDelta(base.registry_fingerprint,target.registry_fingerprint,changed,removed,target.request if base.context_fingerprint!=target.context_fingerprint else None,target.policy if base.policy_fingerprint!=target.policy_fingerprint else None,target.binding,target.state_epoch)
def plan_missing_only(local:PreparedPlannerState,target:PreparedPlannerState):
    lm=dict(local.action_fingerprints); tm=dict(target.action_fingerprints); ids=tuple(k[7:] for k,v in tm.items() if lm.get(k)!=v)
    return PlannerSyncPlan(ids,len(_canon(ids)),False)
