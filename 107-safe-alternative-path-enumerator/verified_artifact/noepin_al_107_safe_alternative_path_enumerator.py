"""NOEPIN AL 107 — Safe Alternative Path Enumerator — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Pure deterministic enumeration of multiple safe path candidates. Unsafe nodes/edges,
hard-constraint failures and policy-budget violations are removed before ranking.
If no safe path exists the module returns HOLD; it never resurrects an unsafe path
as a fallback. Returned paths are candidate evidence only and never grant permission,
execute actions, commit/publish, prove safety/world truth, or establish action success.

Canonical identity: NOEPIN-AL-107
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
class RiskClass(IntEnum): LOW=0; MEDIUM=1; HIGH=2; CRITICAL=3
class NextAction(str,Enum):
    SAFE_PATHS_CANDIDATE='SAFE_PATHS_CANDIDATE'; HUMAN_REVIEW_CANDIDATE='HUMAN_REVIEW_CANDIDATE';
    HOLD_NO_SAFE_PATH='HOLD_NO_SAFE_PATH'; REPLAN_CANDIDATE='REPLAN_CANDIDATE'

@dataclass(frozen=True)
class GraphEdge:
    edge_id:str; source:str; target:str; cost:float; time_cost:float; risk:float; reversibility:float
    hard_constraint_passed:bool; policy_allowed:bool; edge_version:str; edge_fingerprint:str
    observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class PathRequest:
    request_id:str; start_node:str; goal_node:str; k:int; risk_class:RiskClass; max_hops:int
    max_total_cost:float; max_total_time:float; max_total_risk:float; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class PathPolicy:
    low_risk_cap:float; medium_risk_cap:float; high_risk_cap:float; critical_risk_cap:float
    human_review_risk:float; max_k:int; max_expansions:int; require_hard_constraints:bool
    require_policy_allowed:bool; binding:str; state_epoch:str; revoked:bool=False
@dataclass(frozen=True)
class SafePath:
    path_id:str; nodes:tuple[str,...]; edge_ids:tuple[str,...]; total_cost:float; total_time:float
    total_risk:float; reversibility:float; tradeoffs:tuple[str,...]
@dataclass(frozen=True)
class PathResult:
    decision:Decision; next_action:NextAction; reasons:tuple[str,...]; safe_paths:tuple[SafePath,...]
    pruned_reasons:tuple[tuple[str,str],...]; explored_states:int; requested_k:int; returned_k:int
    next_gate_candidate:bool; replan_candidate:bool
    paths_promoted_to_permission:bool=False; permission_granted:bool=False; authority_granted:bool=False
    action_executed:bool=False; plan_committed:bool=False; atomic_publish_executed:bool=False
    external_write_performed:bool=False; world_truth_proven:bool=False; domain_authority_promoted:bool=False
    safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedPathState:
    request:PathRequest; edges:tuple[GraphEdge,...]; forbidden_nodes:tuple[str,...]; policy:PathPolicy
    record_fingerprints:tuple[tuple[str,str],...]; context_fingerprint:str; dependency_fingerprint:str
    policy_fingerprint:str; registry_fingerprint:str; frontier_fingerprint:str; pareto_fingerprint:str
    precomputed_result:PathResult; binding:str; state_epoch:str
@dataclass(frozen=True)
class PathStateDelta:
    base_fingerprint:str; target_fingerprint:str; changed_edges:tuple[GraphEdge,...]; removed_record_ids:tuple[str,...]
    target_request:PathRequest|None; target_forbidden_nodes:tuple[str,...]|None; target_policy:PathPolicy|None
    binding:str; state_epoch:str
@dataclass(frozen=True)
class PathSyncPlan:
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
def _hold(q,reason,*,pruned=(),explored=0,replan=False):
    return PathResult(Decision.HOLD,NextAction.REPLAN_CANDIDATE if replan else NextAction.HOLD_NO_SAFE_PATH,(reason,),(),tuple(sorted(pruned)),explored,q.k,0,False,replan)

def _validate(q,edges,forbidden,p):
    if p.revoked: return 'POLICY_REVOKED'
    if not q.observed or not q.request_id or not q.start_node or not q.goal_node: return 'REQUEST_INVALID'
    if q.binding!=p.binding or q.state_epoch!=p.state_epoch: return 'SCOPE_MISMATCH'
    if q.k<1 or q.k>p.max_k or q.max_hops<1: return 'REQUEST_LIMIT_INVALID'
    nums=(q.max_total_cost,q.max_total_time,q.max_total_risk,p.low_risk_cap,p.medium_risk_cap,p.high_risk_cap,p.critical_risk_cap,p.human_review_risk)
    if any(not math.isfinite(v) or v<0 for v in nums): return 'NUMERIC_INVALID'
    if p.max_k<1 or p.max_expansions<1: return 'POLICY_LIMIT_INVALID'
    if not (p.low_risk_cap>=p.medium_risk_cap>=p.high_risk_cap>=p.critical_risk_cap>=0): return 'POLICY_RISK_CAP_NONMONOTONIC'
    ids=[e.edge_id for e in edges]
    if len(ids)!=len(set(ids)): return 'DUPLICATE_EDGE_ID'
    for e in edges:
        if not e.observed or not e.edge_id or not e.source or not e.target or not e.edge_version or not e.edge_fingerprint: return 'EDGE_INVALID'
        if e.binding!=p.binding or e.state_epoch!=p.state_epoch: return 'EDGE_SCOPE_MISMATCH'
        vals=(e.cost,e.time_cost,e.risk,e.reversibility)
        if any(not math.isfinite(v) for v in vals) or e.cost<0 or e.time_cost<0 or e.risk<0 or not (0<=e.reversibility<=1): return 'EDGE_NUMERIC_INVALID'
    if len(forbidden)!=len(set(forbidden)): return 'DUPLICATE_FORBIDDEN_NODE'
    return None

def _dominates(a:SafePath,b:SafePath)->bool:
    weak=(a.total_cost<=b.total_cost and a.total_time<=b.total_time and a.total_risk<=b.total_risk and a.reversibility>=b.reversibility)
    strict=(a.total_cost<b.total_cost or a.total_time<b.total_time or a.total_risk<b.total_risk or a.reversibility>b.reversibility)
    return weak and strict

def _tradeoffs(path:SafePath, best_cost:float, best_risk:float, best_time:float, best_rev:float)->tuple[str,...]:
    out=[]
    if path.total_cost>best_cost: out.append('HIGHER_COST')
    if path.total_risk>best_risk: out.append('HIGHER_RISK')
    if path.total_time>best_time: out.append('LONGER_TIME')
    if path.reversibility<best_rev: out.append('LOWER_REVERSIBILITY')
    if not out: out.append('PARETO_REFERENCE')
    return tuple(out)

def evaluate(q:PathRequest, edges:tuple[GraphEdge,...], forbidden_nodes:tuple[str,...], p:PathPolicy)->PathResult:
    edges=tuple(edges); forbidden_nodes=tuple(sorted(forbidden_nodes)); err=_validate(q,edges,forbidden_nodes,p)
    if err: return _hold(q,err)
    forbidden=set(forbidden_nodes)
    if q.start_node in forbidden or q.goal_node in forbidden: return _hold(q,'START_OR_GOAL_FORBIDDEN')
    risk_cap=min(q.max_total_risk,_risk_cap(q.risk_class,p))
    adj={}
    pruned=[]
    for e in sorted(edges,key=lambda x:x.edge_id):
        reason=None
        if e.source in forbidden or e.target in forbidden: reason='FORBIDDEN_NODE'
        elif p.require_hard_constraints and not e.hard_constraint_passed: reason='HARD_CONSTRAINT'
        elif p.require_policy_allowed and not e.policy_allowed: reason='POLICY_DENIED'
        elif e.risk>risk_cap: reason='EDGE_RISK_CAP_EXCEEDED'
        if reason: pruned.append((e.edge_id,reason)); continue
        adj.setdefault(e.source,[]).append(e)
    # Uniform-cost style enumeration of simple safe paths. Reversibility is a tie-breaker only.
    heap=[(0.0,0.0,0.0,-1.0,(q.start_node,),(),1.0)]
    found=[]; explored=0
    while heap and explored<p.max_expansions and len(found)<max(q.k*8,q.k+4):
        cost,risk,tim,neg_rev,nodes,eids,rev=heapq.heappop(heap); explored+=1
        node=nodes[-1]
        if node==q.goal_node:
            pid='PATH-' + sha256(('|'.join(eids)).encode()).hexdigest()[:12]
            found.append(SafePath(pid,nodes,eids,cost,tim,risk,rev,()))
            continue
        if len(eids)>=q.max_hops: continue
        for e in adj.get(node,()):
            if e.target in nodes: continue
            nc=cost+e.cost; nr=risk+e.risk; nt=tim+e.time_cost; nrev=min(rev,e.reversibility)
            if nc>q.max_total_cost or nr>risk_cap or nt>q.max_total_time: continue
            heapq.heappush(heap,(nc,nr,nt,-nrev,nodes+(e.target,),eids+(e.edge_id,),nrev))
    if not found:
        reason='SEARCH_BUDGET_EXHAUSTED_NO_SAFE_PATH' if heap and explored>=p.max_expansions else 'NO_SAFE_PATH'
        return _hold(q,reason,pruned=pruned,explored=explored,replan=True)
    # De-duplicate exact edge sequences and form a Pareto frontier.
    uniq={x.edge_ids:x for x in found}; cand=list(uniq.values())
    pareto=[]
    for x in cand:
        if not any(_dominates(y,x) for y in cand if y.edge_ids!=x.edge_ids): pareto.append(x)
    if not pareto: pareto=cand
    pareto.sort(key=lambda x:(x.total_cost,x.total_risk,x.total_time,-x.reversibility,x.edge_ids))
    best_cost=min(x.total_cost for x in pareto); best_risk=min(x.total_risk for x in pareto); best_time=min(x.total_time for x in pareto); best_rev=max(x.reversibility for x in pareto)
    out=[]
    for x in pareto[:q.k]: out.append(SafePath(x.path_id,x.nodes,x.edge_ids,x.total_cost,x.total_time,x.total_risk,x.reversibility,_tradeoffs(x,best_cost,best_risk,best_time,best_rev)))
    decision=Decision.ALLOW; action=NextAction.SAFE_PATHS_CANDIDATE
    if q.risk_class>=RiskClass.HIGH and out and out[0].total_risk>=p.human_review_risk:
        decision=Decision.HUMAN_APPROVAL; action=NextAction.HUMAN_REVIEW_CANDIDATE
    return PathResult(decision,action,('SAFE_PATHS_ENUMERATED',),tuple(out),tuple(sorted(pruned)),explored,q.k,len(out),decision==Decision.ALLOW,False)

def default_policy(): return PathPolicy(4.0,3.0,2.0,1.0,1.0,8,25000,True,True,'PATH-BIND','STATE-EPOCH-1')
def default_request():
    p=default_policy(); return PathRequest('REQ-107','START','GOAL',3,RiskClass.LOW,6,12.0,12.0,4.0,True,p.binding,p.state_epoch)
def default_edges():
    p=default_policy(); b=p.binding; e=p.state_epoch
    return (
        GraphEdge('E-SA','START','A',1.0,1.0,.2,.95,True,True,'V1','FP-SA',True,b,e),
        GraphEdge('E-AG','A','GOAL',1.0,1.0,.2,.95,True,True,'V1','FP-AG',True,b,e),
        GraphEdge('E-SB','START','B',1.0,1.1,.1,.90,True,True,'V1','FP-SB',True,b,e),
        GraphEdge('E-BG','B','GOAL',1.2,1.0,.1,.90,True,True,'V1','FP-BG',True,b,e),
        GraphEdge('E-SC','START','C',.8,.9,.25,.98,True,True,'V1','FP-SC',True,b,e),
        GraphEdge('E-CG','C','GOAL',1.5,1.0,.25,.98,True,True,'V1','FP-CG',True,b,e),
        GraphEdge('E-DIRECT-UNSAFE','START','GOAL',.1,.1,8.0,.1,False,False,'V1','FP-DU',True,b,e),
    )
def default_forbidden_nodes(): return ('FORBIDDEN',)
def default_evaluation(): return evaluate(default_request(),default_edges(),default_forbidden_nodes(),default_policy())

def _record_fps(edges): return tuple((f'EDGE:{x.edge_id}',_fp(x)) for x in sorted(edges,key=lambda y:y.edge_id))
def _context_fp(q,forbidden): return _fp((q,tuple(sorted(forbidden))))
def _dependency_fp(edges): return _fp(tuple((e.edge_id,e.source,e.target) for e in sorted(edges,key=lambda x:x.edge_id)))
def _policy_fp(p): return _fp(p)
def _registry_fp(q,edges,forbidden,p): return _fp((q,_record_fps(edges),tuple(sorted(forbidden)),p))
def _frontier_fp(q,edges,forbidden): return _fp((q.start_node,q.goal_node,q.k,q.max_hops,tuple(sorted(forbidden)),tuple((e.edge_id,e.source,e.target,e.cost,e.risk,e.hard_constraint_passed,e.policy_allowed) for e in sorted(edges,key=lambda x:x.edge_id))))
def _pareto_fp(q,p): return _fp((q.k,q.risk_class,q.max_total_cost,q.max_total_time,q.max_total_risk,p.human_review_risk))
def prepare_state(q,edges,forbidden,p,*,binding,state_epoch):
    edges=tuple(edges); forbidden=tuple(forbidden); fps=_record_fps(edges)
    return PreparedPathState(q,edges,forbidden,p,fps,_context_fp(q,forbidden),_dependency_fp(edges),_policy_fp(p),_registry_fp(q,edges,forbidden,p),_frontier_fp(q,edges,forbidden),_pareto_fp(q,p),evaluate(q,edges,forbidden,p),binding,state_epoch)
def validate_prepared_integrity(st):
    return (st.binding==st.request.binding==st.policy.binding and st.state_epoch==st.request.state_epoch==st.policy.state_epoch and st.record_fingerprints==_record_fps(st.edges) and st.context_fingerprint==_context_fp(st.request,st.forbidden_nodes) and st.dependency_fingerprint==_dependency_fp(st.edges) and st.policy_fingerprint==_policy_fp(st.policy) and st.registry_fingerprint==_registry_fp(st.request,st.edges,st.forbidden_nodes,st.policy) and st.frontier_fingerprint==_frontier_fp(st.request,st.edges,st.forbidden_nodes) and st.pareto_fingerprint==_pareto_fp(st.request,st.policy) and st.precomputed_result==evaluate(st.request,st.edges,st.forbidden_nodes,st.policy))
def evaluate_prepared(st,*,integrity_validated,current_context_fingerprint,current_dependency_fingerprint,current_policy_fingerprint,current_registry_fingerprint,current_frontier_fingerprint,current_pareto_fingerprint):
    if not integrity_validated: return _hold(st.request,'PREPARED_INTEGRITY_NOT_VALIDATED')
    if (st.context_fingerprint!=current_context_fingerprint or st.dependency_fingerprint!=current_dependency_fingerprint or st.policy_fingerprint!=current_policy_fingerprint or st.registry_fingerprint!=current_registry_fingerprint or st.frontier_fingerprint!=current_frontier_fingerprint or st.pareto_fingerprint!=current_pareto_fingerprint):
        return _hold(st.request,'PREPARED_FINGERPRINT_MISMATCH_REEVALUATION_REQUIRED',replan=True)
    return st.precomputed_result
def make_delta(base,target):
    bm=dict(base.record_fingerprints); tm=dict(target.record_fingerprints); em={f'EDGE:{x.edge_id}':x for x in target.edges}
    changed=tuple(em[k] for k,v in tm.items() if bm.get(k)!=v); removed=tuple(k for k in bm if k not in tm)
    return PathStateDelta(base.registry_fingerprint,target.registry_fingerprint,changed,removed,target.request if base.request!=target.request else None,target.forbidden_nodes if base.forbidden_nodes!=target.forbidden_nodes else None,target.policy if base.policy!=target.policy else None,target.binding,target.state_epoch)
def plan_missing_only(local,target):
    lm=dict(local.record_fingerprints); tm=dict(target.record_fingerprints); ids=tuple(k for k,v in tm.items() if lm.get(k)!=v)
    return PathSyncPlan(ids,len(_canon(ids)),False)
