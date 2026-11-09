"""NOEPIN AL 129 — Conflict-Resolution Equilibrium Selector — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-129
DCSR: DIRECT INTEGRATION / 直接統合.

Stable/Pareto/Nash-like outputs are arbitration candidates only. They do not prove world truth,
safety, permission, authority, approval, execution, or action success. Material unresolved trade-offs
remain explicit and can route to HUMAN_APPROVAL/HOLD rather than being forced into one winner.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str, Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class EquilibriumState(str, Enum):
    STABLE='STABLE'; MULTIPLE_TRADEOFFS='MULTIPLE_TRADEOFFS'; NO_SAFE_CANDIDATE='NO_SAFE_CANDIDATE'; SHARED_GOAL_UNKNOWN='SHARED_GOAL_UNKNOWN'; INVALID='INVALID'
class NextAction(str, Enum):
    STABLE_CANDIDATE_CANDIDATE='STABLE_CANDIDATE_CANDIDATE'; HUMAN_TRADEOFF_REVIEW_CANDIDATE='HUMAN_TRADEOFF_REVIEW_CANDIDATE'; HOLD_CONFLICT_REVIEW_CANDIDATE='HOLD_CONFLICT_REVIEW_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; MATERIAL_TRADEOFF='MATERIAL_TRADEOFF'; NO_SAFE_CANDIDATE='NO_SAFE_CANDIDATE'; SHARED_GOAL_UNKNOWN='SHARED_GOAL_UNKNOWN'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'

@dataclass(frozen=True)
class AgentUtility:
    agent_id:str
    utility:float

@dataclass(frozen=True)
class Proposal:
    proposal_id:str
    proposer_agent_id:str
    utilities:tuple[AgentUtility,...]
    risk:float
    shared_goal_alignment:float
    hard_constraints_met:bool
    available:bool
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class SharedGoal:
    goal_id:str
    known:bool
    minimum_utility:float
    max_acceptable_risk:float
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class EquilibriumPolicy:
    risk_weight:float=.35
    goal_weight:float=.35
    nash_weight:float=.30
    dissent_utility_threshold:float=.42
    material_tradeoff_gap:float=.035
    monopoly_spread_threshold:float=.55
    require_all_agent_utilities:bool=True
    allow_human_escalation:bool=True

@dataclass(frozen=True)
class EquilibriumRequest:
    request_id:str
    proposals:tuple[Proposal,...]
    shared_goal:SharedGoal
    policy:EquilibriumPolicy
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class CandidateEvaluation:
    proposal_id:str
    proposer_agent_id:str
    normalized_utility_mean:float
    minimum_utility:float
    nash_like_score:float
    stability_score:float
    risk:float
    shared_goal_alignment:float
    dissent_agents:tuple[str,...]
    pareto_dominated:bool
    monopoly_flag:bool

@dataclass(frozen=True)
class EquilibriumResult:
    decision:Decision
    next_action:NextAction
    escalation:Escalation
    equilibrium_state:EquilibriumState
    reasons:tuple[str,...]
    stable_candidate:str|None
    reserve_candidates:tuple[str,...]
    tradeoffs:tuple[str,...]
    dissent:tuple[str,...]
    evaluations:tuple[CandidateEvaluation,...]
    next_gate_candidate:bool
    stable_candidate_promoted_to_permission:bool=False
    equilibrium_promoted_to_truth:bool=False
    tradeoff_promoted_to_truth:bool=False
    human_approval_promoted_to_execution:bool=False
    sender_authority_inherited:bool=False
    sender_intent_inherited:bool=False
    sender_agreement_inherited:bool=False
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
class PreparedEquilibriumState:
    request:EquilibriumRequest
    result:EquilibriumResult
    context_fingerprint:str
    proposal_fingerprint:str
    policy_fingerprint:str
    outcome_fingerprint:str
    integrity_fingerprint:str
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class EquilibriumDelta:
    changed_proposals:tuple[Proposal,...]
    removed_proposal_ids:tuple[str,...]
    shared_goal_changed:bool
    from_manifest_fingerprint:str
    to_manifest_fingerprint:str

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

def _canon(v): return json.dumps(_obj(v),ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def _fp(v): return sha256(_canon(v)).hexdigest()
def _finite(x): return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(float(x))
def _manifest_fp(req): return _fp((req.proposals,req.shared_goal,req.binding,req.state_epoch))

def default_policy(): return EquilibriumPolicy()

def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    props=(
        Proposal('P-BALANCED','AGENT-A',(AgentUtility('AGENT-A',.82),AgentUtility('AGENT-B',.78),AgentUtility('AGENT-C',.80)),.14,.94,True,True,b,e),
        Proposal('P-A-FAVOR','AGENT-A',(AgentUtility('AGENT-A',.96),AgentUtility('AGENT-B',.46),AgentUtility('AGENT-C',.50)),.12,.82,True,True,b,e),
        Proposal('P-B-FAVOR','AGENT-B',(AgentUtility('AGENT-A',.48),AgentUtility('AGENT-B',.95),AgentUtility('AGENT-C',.52)),.13,.81,True,True,b,e),
    )
    return EquilibriumRequest('DEFAULT-129',props,SharedGoal('GOAL-1',True,.40,.35,b,e),default_policy(),b,e)

def _invalid(reason):
    return EquilibriumResult(Decision.HOLD,NextAction.HOLD_CONFLICT_REVIEW_CANDIDATE,Escalation.INVALID_CONFIGURATION,EquilibriumState.INVALID,(reason,'NO_PERMISSION_OR_EXECUTION_PROMOTION'),None,(),(),(),(),False)

def _proposal_map(p:Proposal): return {u.agent_id:u.utility for u in p.utilities}

def _validate(req:EquilibriumRequest):
    if not req.request_id or not req.binding or not req.state_epoch: return 'INVALID_REQUEST_IDENTITY'
    p=req.policy; g=req.shared_goal
    nums=(p.risk_weight,p.goal_weight,p.nash_weight,p.dissent_utility_threshold,p.material_tradeoff_gap,p.monopoly_spread_threshold,g.minimum_utility,g.max_acceptable_risk)
    if any(not _finite(x) for x in nums): return 'INVALID_NUMERIC'
    if any(not 0<=x<=1 for x in nums): return 'INVALID_RANGE'
    if p.risk_weight+p.goal_weight+p.nash_weight<=0: return 'INVALID_WEIGHTS'
    if g.binding!=req.binding or g.state_epoch!=req.state_epoch or not g.goal_id: return 'SHARED_GOAL_IDENTITY_INVALID'
    ids=[x.proposal_id for x in req.proposals]
    if any(not x for x in ids) or len(ids)!=len(set(ids)): return 'DUPLICATE_OR_EMPTY_PROPOSAL'
    for x in req.proposals:
        if x.binding!=req.binding or x.state_epoch!=req.state_epoch or not x.proposer_agent_id: return 'PROPOSAL_IDENTITY_INVALID'
        if not _finite(x.risk) or not _finite(x.shared_goal_alignment) or not 0<=x.risk<=1 or not 0<=x.shared_goal_alignment<=1: return 'PROPOSAL_NUMERIC_INVALID'
        aids=[u.agent_id for u in x.utilities]
        if not aids or any(not a for a in aids) or len(aids)!=len(set(aids)): return 'UTILITY_AGENT_INVALID'
        if any(not _finite(u.utility) or not 0<=u.utility<=1 for u in x.utilities): return 'UTILITY_INVALID'
    if req.proposals and p.require_all_agent_utilities:
        universe=set(u.agent_id for x in req.proposals for u in x.utilities)
        if any(set(_proposal_map(x))!=universe for x in req.proposals): return 'UTILITY_DOMAIN_MISMATCH'
    return None

def _dominates(a:CandidateEvaluation,b:CandidateEvaluation, amap:dict[str,float],bmap:dict[str,float]):
    keys=sorted(set(amap)|set(bmap))
    return all(amap.get(k,0)>=bmap.get(k,0)-1e-12 for k in keys) and any(amap.get(k,0)>bmap.get(k,0)+1e-12 for k in keys) and a.risk<=b.risk+1e-12 and a.shared_goal_alignment>=b.shared_goal_alignment-1e-12

def evaluate(req:EquilibriumRequest)->EquilibriumResult:
    bad=_validate(req)
    if bad: return _invalid(bad)
    g=req.shared_goal; p=req.policy
    if not g.known:
        return EquilibriumResult(Decision.HOLD,NextAction.HUMAN_TRADEOFF_REVIEW_CANDIDATE if p.allow_human_escalation else NextAction.HOLD_CONFLICT_REVIEW_CANDIDATE,Escalation.SHARED_GOAL_UNKNOWN,EquilibriumState.SHARED_GOAL_UNKNOWN,('SHARED_GOAL_UNKNOWN','DO_NOT_FORCE_EQUILIBRIUM'),None,(),(),(),(),False)
    feasible=[]
    excluded=[]
    all_agents=sorted(set(u.agent_id for x in req.proposals for u in x.utilities))
    wsum=p.risk_weight+p.goal_weight+p.nash_weight
    for x in sorted(req.proposals,key=lambda q:q.proposal_id):
        um=_proposal_map(x); vals=[um[a] for a in all_agents]
        if not x.hard_constraints_met:
            excluded.append(f'{x.proposal_id}:HARD_CONSTRAINT'); continue
        if not x.available:
            excluded.append(f'{x.proposal_id}:UNAVAILABLE'); continue
        if x.risk>g.max_acceptable_risk:
            excluded.append(f'{x.proposal_id}:RISK_LIMIT'); continue
        if min(vals)<g.minimum_utility:
            excluded.append(f'{x.proposal_id}:MINIMUM_UTILITY'); continue
        mean=sum(vals)/len(vals); min_u=min(vals)
        # Nash-like cooperative welfare; tiny floor avoids zero collapse but preserves low-utility penalty.
        nash=math.exp(sum(math.log(max(1e-12,v)) for v in vals)/len(vals))
        risk_component=1-x.risk
        stability=(p.risk_weight*risk_component+p.goal_weight*x.shared_goal_alignment+p.nash_weight*nash)/wsum
        dissent=tuple(a for a in all_agents if um[a]<p.dissent_utility_threshold)
        monopoly=(max(vals)-min(vals))>p.monopoly_spread_threshold
        feasible.append((x,CandidateEvaluation(x.proposal_id,x.proposer_agent_id,mean,min_u,nash,stability,x.risk,x.shared_goal_alignment,dissent,False,monopoly),um))
    if not feasible:
        return EquilibriumResult(Decision.HOLD,NextAction.HOLD_CONFLICT_REVIEW_CANDIDATE,Escalation.NO_SAFE_CANDIDATE,EquilibriumState.NO_SAFE_CANDIDATE,('NO_SAFE_FEASIBLE_PROPOSAL','SAFETY_CONSTRAINTS_NOT_RELAXED')+tuple(excluded),None,(),(),(),(),False)
    # Pareto filter over participant utilities plus lower risk and higher shared-goal alignment.
    evals=[]
    for i,(x,ev,um) in enumerate(feasible):
        dom=False
        for j,(x2,ev2,um2) in enumerate(feasible):
            if i!=j and _dominates(ev2,ev,um2,um): dom=True; break
        evals.append(CandidateEvaluation(ev.proposal_id,ev.proposer_agent_id,ev.normalized_utility_mean,ev.minimum_utility,ev.nash_like_score,ev.stability_score,ev.risk,ev.shared_goal_alignment,ev.dissent_agents,dom,ev.monopoly_flag))
    evals=tuple(sorted(evals,key=lambda z:(z.pareto_dominated,-z.stability_score,z.proposal_id)))
    front=[z for z in evals if not z.pareto_dominated]
    front.sort(key=lambda z:(-z.stability_score,z.proposal_id))
    top=front[0]
    near=[z for z in front if top.stability_score-z.stability_score<=p.material_tradeoff_gap+1e-12]
    tradeoffs=[]
    for z in front:
        tradeoffs.append(f'{z.proposal_id}|score={z.stability_score:.6f}|risk={z.risk:.6f}|goal={z.shared_goal_alignment:.6f}|minU={z.minimum_utility:.6f}|nash={z.nash_like_score:.6f}|dissent={";".join(z.dissent_agents) or "NONE"}|monopoly={str(z.monopoly_flag).upper()}')
    dissent=tuple(sorted(set(a for z in near for a in z.dissent_agents)))
    # Material near-tie, monopoly among the top near-front, or dissent on near-equivalent choices requires human arbitration.
    if len(near)>1 or top.monopoly_flag or dissent:
        return EquilibriumResult(Decision.HUMAN_APPROVAL if p.allow_human_escalation else Decision.HOLD,NextAction.HUMAN_TRADEOFF_REVIEW_CANDIDATE if p.allow_human_escalation else NextAction.HOLD_CONFLICT_REVIEW_CANDIDATE,Escalation.MATERIAL_TRADEOFF,EquilibriumState.MULTIPLE_TRADEOFFS,('MATERIAL_TRADEOFF_REMAINS','NO_AUTOMATIC_WINNER_PROMOTION'),None,tuple(z.proposal_id for z in front),tuple(tradeoffs),dissent,evals,False)
    reserves=tuple(z.proposal_id for z in front[1:])
    return EquilibriumResult(Decision.ALLOW,NextAction.STABLE_CANDIDATE_CANDIDATE,Escalation.NONE,EquilibriumState.STABLE,('STABLE_CANDIDATE_ONLY','HARD_CONSTRAINTS_PRESERVED','NO_PERMISSION_OR_EXECUTION_PROMOTION'),top.proposal_id,reserves,tuple(tradeoffs),(),evals,True)

def default_evaluation(): return evaluate(default_request())

def _fps(req,result): return (_fp((req.request_id,req.shared_goal,req.binding,req.state_epoch)),_fp(req.proposals),_fp(req.policy),_fp(result))
def _integrity_payload(cf,pf,polf,of,b,e): return (cf,pf,polf,of,b,e,'NOEPIN-AL-129-PREPARED-V1')
def prepare_state(req:EquilibriumRequest,*,binding:str,state_epoch:str)->PreparedEquilibriumState:
    r=_invalid('PREPARED_BINDING_OR_EPOCH_MISMATCH') if binding!=req.binding or state_epoch!=req.state_epoch else evaluate(req)
    cf,pf,polf,of=_fps(req,r); integ=_fp(_integrity_payload(cf,pf,polf,of,binding,state_epoch))
    return PreparedEquilibriumState(req,r,cf,pf,polf,of,integ,binding,state_epoch)
def validate_prepared_integrity(st):
    return st.integrity_fingerprint==_fp(_integrity_payload(st.context_fingerprint,st.proposal_fingerprint,st.policy_fingerprint,st.outcome_fingerprint,st.binding,st.state_epoch))
def evaluate_prepared(st:PreparedEquilibriumState,*,integrity_validated:bool,current_context_fingerprint:str,current_proposal_fingerprint:str,current_policy_fingerprint:str,current_outcome_fingerprint:str)->EquilibriumResult:
    ok=(integrity_validated and validate_prepared_integrity(st) and st.binding==st.request.binding and st.state_epoch==st.request.state_epoch and current_context_fingerprint==st.context_fingerprint and current_proposal_fingerprint==st.proposal_fingerprint and current_policy_fingerprint==st.policy_fingerprint and current_outcome_fingerprint==st.outcome_fingerprint)
    return st.result if ok else _invalid('PREPARED_REUSE_REJECTED')
def make_delta(old:PreparedEquilibriumState,new:PreparedEquilibriumState)->EquilibriumDelta:
    op={x.proposal_id:x for x in old.request.proposals}; np={x.proposal_id:x for x in new.request.proposals}
    changed=tuple(np[k] for k in sorted(np) if k not in op or _canon(np[k])!=_canon(op[k])); removed=tuple(sorted(set(op)-set(np)))
    return EquilibriumDelta(changed,removed,_canon(old.request.shared_goal)!=_canon(new.request.shared_goal),_manifest_fp(old.request),_manifest_fp(new.request))
def plan_missing_only(old:PreparedEquilibriumState,new:PreparedEquilibriumState)->MissingOnlyPlan:
    d=make_delta(old,new); ids=[f'PROPOSAL:{x.proposal_id}' for x in d.changed_proposals]+[f'REMOVED_PROPOSAL:{x}' for x in d.removed_proposal_ids]
    if d.shared_goal_changed: ids.append('SHARED_GOAL')
    ids=tuple(sorted(ids)); meta=len(_canon({'from':d.from_manifest_fingerprint,'to':d.to_manifest_fingerprint,'ids':ids}))
    return MissingOnlyPlan(ids,meta,False)
