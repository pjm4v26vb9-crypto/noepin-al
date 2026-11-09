"""NOEPIN AL 103 — Constrained Beam Planner — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Pure planning candidate evidence. This module performs deterministic beam search,
filters hard-constraint violations before ranking at every depth, ranks surviving
candidates by utility minus risk, uses reversibility as a deterministic safety
preference on score ties, and returns HOLD rather than reviving unsafe candidates
when the beam is exhausted or the depth limit is reached before the goal.

A Top Plan is only a plan candidate. It is never Permission Grant, Action
Execution, Commit/Publish, Production Authority, Safety Proof, or Action Success.

Canonical identity: NOEPIN-AL-103
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
class RiskClass(IntEnum):
    LOW=0; MEDIUM=1; HIGH=2; CRITICAL=3
class NextAction(str, Enum):
    TOP_PLAN_CANDIDATE='TOP_PLAN_CANDIDATE'; HUMAN_REVIEW_CANDIDATE='HUMAN_REVIEW_CANDIDATE'; REPLAN_CANDIDATE='REPLAN_CANDIDATE'; CONSTRAINT_REPAIR_CANDIDATE='CONSTRAINT_REPAIR_CANDIDATE'; HOLD_UNRESOLVED='HOLD_UNRESOLVED'

@dataclass(frozen=True)
class BeamRequest:
    request_id:str; start_state:str; goal_state:str; risk:RiskClass; beam_width:int; max_depth:int
    max_total_risk:float; min_final_utility:float; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class BeamAction:
    action_id:str; from_state:str; to_state:str; utility_delta:float; risk_cost:float; reversibility:float
    hard_constraint_passed:bool; constraint_reason:str; action_version:str; action_fingerprint:str
    observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class BeamPolicy:
    risk_penalty:float; low_risk_cap:float; medium_risk_cap:float; high_risk_cap:float; critical_risk_cap:float
    approval_risk_threshold:float; max_generated_candidates:int; require_hard_constraints:bool
    binding:str; state_epoch:str; revoked:bool=False
@dataclass(frozen=True)
class PlanCandidate:
    action_ids:tuple[str,...]; state_trace:tuple[str,...]; total_utility:float; total_risk:float
    rank_score:float; min_reversibility:float
@dataclass(frozen=True)
class BeamPlanResult:
    decision:Decision; next_action:NextAction; reasons:tuple[str,...]; top_plans:tuple[PlanCandidate,...]
    pruned_reasons:tuple[tuple[str,int],...]; explored_depth:int; generated_candidates:int; beam_exhausted:bool
    depth_limit_reached:bool; next_gate_candidate:bool; plan_promoted_to_permission:bool=False
    permission_granted:bool=False; action_executed:bool=False; plan_committed:bool=False
    atomic_publish_executed:bool=False; external_write_performed:bool=False; world_truth_proven:bool=False
    domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedBeamState:
    request:BeamRequest; actions:tuple[BeamAction,...]; policy:BeamPolicy; action_fingerprints:tuple[tuple[str,str],...]
    context_fingerprint:str; dependency_fingerprint:str; policy_fingerprint:str; registry_fingerprint:str
    frontier_fingerprint:str; rank_fingerprint:str; precomputed_result:BeamPlanResult; binding:str; state_epoch:str
@dataclass(frozen=True)
class BeamStateDelta:
    base_fingerprint:str; target_fingerprint:str; changed_actions:tuple[BeamAction,...]; removed_action_ids:tuple[str,...]
    target_request:BeamRequest|None; target_policy:BeamPolicy|None; binding:str; state_epoch:str
@dataclass(frozen=True)
class BeamSyncPlan:
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
def _round(x): return round(float(x),12)

def _validate(q, actions, p):
    if p.revoked: return 'POLICY_REVOKED'
    if not q.observed or not q.request_id or not q.start_state or not q.goal_state: return 'REQUEST_INVALID'
    if q.binding!=p.binding or q.state_epoch!=p.state_epoch: return 'REQUEST_SCOPE_MISMATCH'
    if q.beam_width<=0 or q.max_depth<=0: return 'BEAM_OR_DEPTH_INVALID'
    if p.max_generated_candidates<=0: return 'GENERATION_BUDGET_INVALID'
    vals=(q.max_total_risk,q.min_final_utility,p.risk_penalty,p.low_risk_cap,p.medium_risk_cap,p.high_risk_cap,p.critical_risk_cap,p.approval_risk_threshold)
    if any(not math.isfinite(v) for v in vals): return 'NUMERIC_VALUE_INVALID'
    if q.max_total_risk<0 or p.risk_penalty<0 or p.approval_risk_threshold<0: return 'NUMERIC_VALUE_INVALID'
    if not (p.low_risk_cap>=p.medium_risk_cap>=p.high_risk_cap>=p.critical_risk_cap>=0): return 'POLICY_RISK_CAP_NONMONOTONIC'
    ids=[a.action_id for a in actions]
    if len(ids)!=len(set(ids)): return 'DUPLICATE_ACTION_ID'
    for a in actions:
        if not a.observed or not a.action_id or not a.from_state or not a.to_state or not a.action_version or not a.action_fingerprint: return 'ACTION_INVALID'
        if a.binding!=p.binding or a.state_epoch!=p.state_epoch: return 'ACTION_SCOPE_MISMATCH'
        if any(not math.isfinite(v) for v in (a.utility_delta,a.risk_cost,a.reversibility)): return 'ACTION_NUMERIC_INVALID'
        if a.risk_cost<0 or not (0<=a.reversibility<=1): return 'ACTION_NUMERIC_INVALID'
        if p.require_hard_constraints and not a.hard_constraint_passed and not a.constraint_reason: return 'CONSTRAINT_EVIDENCE_INVALID'
    return None

def _hold(reason, *, action=NextAction.HOLD_UNRESOLVED, pruned=(), depth=0, generated=0, exhausted=False, depth_limit=False):
    return BeamPlanResult(Decision.HOLD,action,(reason,),(),tuple(sorted(pruned)),depth,generated,exhausted,depth_limit,False)

def _rank(c:PlanCandidate):
    # Higher score first. If score ties, lower risk then higher reversibility; lexical action IDs stabilize replay.
    return (-c.rank_score,c.total_risk,-c.min_reversibility,c.action_ids,c.state_trace)

def evaluate(q:BeamRequest, actions:tuple[BeamAction,...], p:BeamPolicy)->BeamPlanResult:
    actions=tuple(actions); err=_validate(q,actions,p)
    if err: return _hold(err)
    if q.start_state==q.goal_state:
        c=PlanCandidate((),(q.start_state,),0.0,0.0,0.0,1.0)
        return BeamPlanResult(Decision.ALLOW,NextAction.TOP_PLAN_CANDIDATE,('GOAL_ALREADY_SATISFIED','PLAN_CANDIDATE_ONLY'),(c,),(),0,0,False,False,True)
    outgoing={}
    for a in actions: outgoing.setdefault(a.from_state,[]).append(a)
    for k in outgoing: outgoing[k].sort(key=lambda x:(x.action_id,x.to_state))
    cap=min(q.max_total_risk,_risk_cap(q.risk,p))
    beam=(PlanCandidate((),(q.start_state,),0.0,0.0,0.0,1.0),)
    pruned={}; generated=0
    for depth in range(1,q.max_depth+1):
        expanded=[]; completed=[]
        for c in beam:
            state=c.state_trace[-1]
            for a in outgoing.get(state,()):
                generated+=1
                if generated>p.max_generated_candidates:
                    return _hold('GENERATION_BUDGET_EXCEEDED',action=NextAction.REPLAN_CANDIDATE,pruned=tuple(pruned.items()),depth=depth-1,generated=generated-1)
                if p.require_hard_constraints and not a.hard_constraint_passed:
                    pruned['HARD_CONSTRAINT_VIOLATION']=pruned.get('HARD_CONSTRAINT_VIOLATION',0)+1; continue
                nr=_round(c.total_risk+a.risk_cost)
                if nr>cap+1e-12:
                    pruned['RISK_BUDGET_EXCEEDED']=pruned.get('RISK_BUDGET_EXCEEDED',0)+1; continue
                nu=_round(c.total_utility+a.utility_delta)
                rev=min(c.min_reversibility,a.reversibility)
                score=_round(nu-p.risk_penalty*nr)
                nc=PlanCandidate(c.action_ids+(a.action_id,),c.state_trace+(a.to_state,),nu,nr,score,_round(rev))
                if a.to_state==q.goal_state: completed.append(nc)
                else: expanded.append(nc)
        if completed:
            completed.sort(key=_rank)
            top=tuple(completed[:q.beam_width])
            best=top[0]
            if best.total_utility<q.min_final_utility:
                return _hold('GOAL_CANDIDATES_BELOW_MIN_UTILITY',action=NextAction.REPLAN_CANDIDATE,pruned=tuple(pruned.items()),depth=depth,generated=generated)
            reasons=['SAFE_BEAM_GOAL_FOUND','HARD_CONSTRAINTS_PRESERVED','PLAN_CANDIDATE_ONLY']
            if pruned: reasons.append('CANDIDATES_PRUNED')
            if q.risk in (RiskClass.HIGH,RiskClass.CRITICAL) and best.total_risk>=p.approval_risk_threshold:
                return BeamPlanResult(Decision.HUMAN_APPROVAL,NextAction.HUMAN_REVIEW_CANDIDATE,tuple(reasons+['RISK_REQUIRES_HUMAN_REVIEW_CANDIDATE']),top,tuple(sorted(pruned.items())),depth,generated,False,False,False)
            return BeamPlanResult(Decision.ALLOW,NextAction.TOP_PLAN_CANDIDATE,tuple(reasons),top,tuple(sorted(pruned.items())),depth,generated,False,False,True)
        if not expanded:
            action=NextAction.CONSTRAINT_REPAIR_CANDIDATE if pruned.get('HARD_CONSTRAINT_VIOLATION',0) else NextAction.REPLAN_CANDIDATE
            return _hold('BEAM_EXHAUSTED_NO_SAFE_CANDIDATE',action=action,pruned=tuple(pruned.items()),depth=depth,generated=generated,exhausted=True)
        expanded.sort(key=_rank)
        beam=tuple(expanded[:q.beam_width])
    return _hold('MAX_DEPTH_REACHED_GOAL_INCOMPLETE',action=NextAction.REPLAN_CANDIDATE,pruned=tuple(pruned.items()),depth=q.max_depth,generated=generated,depth_limit=True)

def default_policy():
    return BeamPolicy(.60,10.0,8.0,5.0,2.0,1.0,10000,True,'BEAM-BIND','STATE-EPOCH-1')
def default_request():
    p=default_policy(); return BeamRequest('REQ-103','S0','GOAL',RiskClass.LOW,2,4,10.0,1.0,True,p.binding,p.state_epoch)
def default_actions():
    p=default_policy(); b=p.binding; e=p.state_epoch
    return (
        BeamAction('A-SAFE-1','S0','S1',2.0,.20,.95,True,'PASS','A1','FP-A1',True,b,e),
        BeamAction('A-SAFE-2','S1','GOAL',2.0,.20,.95,True,'PASS','A1','FP-A2',True,b,e),
        BeamAction('A-ALT-1','S0','S2',1.8,.10,1.00,True,'PASS','A1','FP-B1',True,b,e),
        BeamAction('A-ALT-2','S2','GOAL',1.8,.10,1.00,True,'PASS','A1','FP-B2',True,b,e),
        BeamAction('A-DANGER','S0','GOAL',10.0,9.0,.10,False,'HARD_CONSTRAINT_VIOLATION','A1','FP-X',True,b,e),
    )
def default_evaluation(): return evaluate(default_request(),default_actions(),default_policy())

def _action_fps(actions): return tuple((f'ACTION:{a.action_id}',_fp(a)) for a in sorted(actions,key=lambda x:x.action_id))
def _context_fp(q): return _fp(q)
def _dependency_fp(actions): return _fp(_action_fps(actions))
def _policy_fp(p): return _fp(p)
def _registry_fp(q,actions,p): return _fp((q,_action_fps(actions),p))
def _frontier_fp(q,actions,p):
    safe=tuple((a.action_id,a.from_state,a.to_state,a.utility_delta,a.risk_cost,a.reversibility) for a in sorted(actions,key=lambda x:x.action_id) if a.hard_constraint_passed)
    return _fp((q.start_state,q.goal_state,q.beam_width,q.max_depth,safe,p.risk_penalty))
def _rank_fp(p): return _fp(('UTILITY_MINUS_RISK',p.risk_penalty,'TIE_LOW_RISK_HIGH_REVERSIBILITY'))
def prepare_state(q,actions,p,*,binding:str,state_epoch:str):
    actions=tuple(actions); fps=_action_fps(actions)
    return PreparedBeamState(q,actions,p,fps,_context_fp(q),_dependency_fp(actions),_policy_fp(p),_registry_fp(q,actions,p),_frontier_fp(q,actions,p),_rank_fp(p),evaluate(q,actions,p),binding,state_epoch)
def validate_prepared_integrity(st):
    return (st.binding==st.policy.binding==st.request.binding and st.state_epoch==st.policy.state_epoch==st.request.state_epoch and
            st.action_fingerprints==_action_fps(st.actions) and st.context_fingerprint==_context_fp(st.request) and
            st.dependency_fingerprint==_dependency_fp(st.actions) and st.policy_fingerprint==_policy_fp(st.policy) and
            st.registry_fingerprint==_registry_fp(st.request,st.actions,st.policy) and st.frontier_fingerprint==_frontier_fp(st.request,st.actions,st.policy) and
            st.rank_fingerprint==_rank_fp(st.policy) and st.precomputed_result==evaluate(st.request,st.actions,st.policy))
def evaluate_prepared(st,*,integrity_validated:bool,current_context_fingerprint:str,current_dependency_fingerprint:str,current_policy_fingerprint:str,current_registry_fingerprint:str,current_frontier_fingerprint:str,current_rank_fingerprint:str):
    if not integrity_validated: return _hold('PREPARED_INTEGRITY_NOT_VALIDATED')
    if (st.context_fingerprint!=current_context_fingerprint or st.dependency_fingerprint!=current_dependency_fingerprint or
        st.policy_fingerprint!=current_policy_fingerprint or st.registry_fingerprint!=current_registry_fingerprint or
        st.frontier_fingerprint!=current_frontier_fingerprint or st.rank_fingerprint!=current_rank_fingerprint):
        return _hold('PREPARED_FINGERPRINT_MISMATCH_REEVALUATION_REQUIRED',action=NextAction.REPLAN_CANDIDATE)
    return st.precomputed_result
def make_delta(base:PreparedBeamState,target:PreparedBeamState):
    bm=dict(base.action_fingerprints); tm=dict(target.action_fingerprints); tby={a.action_id:a for a in target.actions}
    changed=tuple(tby[k[7:]] for k,v in tm.items() if bm.get(k)!=v)
    removed=tuple(k[7:] for k in bm if k not in tm)
    return BeamStateDelta(base.registry_fingerprint,target.registry_fingerprint,changed,removed,target.request if base.context_fingerprint!=target.context_fingerprint else None,target.policy if base.policy_fingerprint!=target.policy_fingerprint else None,target.binding,target.state_epoch)
def plan_missing_only(local:PreparedBeamState,target:PreparedBeamState):
    lm=dict(local.action_fingerprints); tm=dict(target.action_fingerprints); ids=tuple(k[7:] for k,v in tm.items() if lm.get(k)!=v)
    return BeamSyncPlan(ids,len(_canon(ids)),False)
