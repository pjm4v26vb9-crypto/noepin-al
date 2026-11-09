"""NOEPIN AL 127 — Delegation Auction Optimizer — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-127
DCSR: DIRECT INTEGRATION / 直接統合.

Winner/Reserve outputs are delegation candidates only. They do not grant permission, role authority,
approval, execution, safety proof, world truth, or action success. Received DCSR state never
automatically inherits sender authority, intent, agreement, permission, or action-success authority.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str, Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class AuctionState(str, Enum):
    ASSIGNABLE='ASSIGNABLE'; NO_FEASIBLE_AGENT='NO_FEASIBLE_AGENT'; INVALID='INVALID'
class NextAction(str, Enum):
    DELEGATION_ASSIGNMENT_CANDIDATE='DELEGATION_ASSIGNMENT_CANDIDATE'; HOLD_NO_SAFE_DELEGATE_CANDIDATE='HOLD_NO_SAFE_DELEGATE_CANDIDATE'; HUMAN_REVIEW_CANDIDATE='HUMAN_REVIEW_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; NO_SAFE_AGENT='NO_SAFE_AGENT'; CAPABILITY_SHORTFALL='CAPABILITY_SHORTFALL'; RISK_EXCEEDED='RISK_EXCEEDED'; AVAILABILITY_SHORTFALL='AVAILABILITY_SHORTFALL'; AUTHORITY_SCOPE_SHORTFALL='AUTHORITY_SCOPE_SHORTFALL'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'

@dataclass(frozen=True)
class DelegationTask:
    task_id:str
    required_capabilities:tuple[str,...]
    required_authority_scopes:tuple[str,...]
    max_risk:float
    min_availability:float
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class AgentBid:
    agent_id:str
    capabilities:tuple[str,...]
    authority_scopes:tuple[str,...]
    cost:float
    risk:float
    trust:float
    availability:float
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class AuctionPolicy:
    cost_weight:float=.25
    risk_weight:float=.35
    trust_weight:float=.30
    availability_weight:float=.10
    min_trust:float=.45
    reserve_required:bool=False
    allow_human_escalation:bool=True

@dataclass(frozen=True)
class AuctionRequest:
    request_id:str
    task:DelegationTask
    bids:tuple[AgentBid,...]
    policy:AuctionPolicy
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class BidEvaluation:
    agent_id:str
    feasible:bool
    utility:float|None
    rejection_reasons:tuple[str,...]
    cost:float
    risk:float
    trust:float
    availability:float

@dataclass(frozen=True)
class AuctionResult:
    decision:Decision
    next_action:NextAction
    escalation:Escalation
    auction_state:AuctionState
    reasons:tuple[str,...]
    winner_candidate:str|None
    reserve_candidate:str|None
    expected_utility:float|None
    feasible_agent_ids:tuple[str,...]
    bid_evaluations:tuple[BidEvaluation,...]
    next_gate_candidate:bool
    winner_promoted_to_permission:bool=False
    assignment_executed:bool=False
    reserve_promoted_to_authority:bool=False
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
class PreparedAuctionState:
    request:AuctionRequest
    result:AuctionResult
    context_fingerprint:str
    bid_fingerprint:str
    policy_fingerprint:str
    outcome_fingerprint:str
    integrity_fingerprint:str
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class AuctionDelta:
    changed_bids:tuple[AgentBid,...]
    removed_agent_ids:tuple[str,...]
    from_manifest_fingerprint:str
    to_manifest_fingerprint:str

@dataclass(frozen=True)
class MissingOnlyPlan:
    missing_or_changed_bid_ids:tuple[str,...]
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
def _manifest_fp(req): return _fp((req.task,req.bids,req.binding,req.state_epoch))

def default_policy(): return AuctionPolicy()

def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    task=DelegationTask('TASK-127',('reasoning','code'),('sandbox',),.35,.70,b,e)
    bids=(
        AgentBid('AGENT-A',('reasoning','code','review'),('sandbox',),.40,.16,.88,.94,b,e),
        AgentBid('AGENT-B',('reasoning','code'),('sandbox',),.26,.30,.73,.90,b,e),
        AgentBid('AGENT-C',('reasoning',),('sandbox',),.10,.10,.95,.98,b,e),
        AgentBid('AGENT-D',('reasoning','code'),('sandbox',),.20,.55,.92,.96,b,e),
    )
    return AuctionRequest('DEFAULT-127',task,bids,default_policy(),b,e)

def _invalid(reason):
    return AuctionResult(Decision.HOLD,NextAction.HOLD_NO_SAFE_DELEGATE_CANDIDATE,Escalation.INVALID_CONFIGURATION,AuctionState.INVALID,(reason,'NO_PERMISSION_GRANT','NO_ASSIGNMENT_EXECUTION'),None,None,None,(),(),False)

def _utility(b:AgentBid,p:AuctionPolicy)->float:
    # Cost/risk are penalties; trust/availability are benefits. Cost is softly normalized to [0,1].
    c=b.cost/(1.0+b.cost)
    return (p.trust_weight*b.trust + p.availability_weight*b.availability - p.risk_weight*b.risk - p.cost_weight*c)

def evaluate(req:AuctionRequest)->AuctionResult:
    if not req.request_id or not req.binding or not req.state_epoch: return _invalid('INVALID_REQUEST_IDENTITY')
    t=req.task; p=req.policy
    if t.binding!=req.binding or t.state_epoch!=req.state_epoch or not t.task_id: return _invalid('TASK_IDENTITY_INVALID')
    nums=(t.max_risk,t.min_availability,p.cost_weight,p.risk_weight,p.trust_weight,p.availability_weight,p.min_trust)
    if any(not _finite(x) for x in nums): return _invalid('INVALID_NUMERIC')
    if not (0<=t.max_risk<=1 and 0<=t.min_availability<=1 and 0<=p.min_trust<=1): return _invalid('INVALID_RANGE')
    if min(p.cost_weight,p.risk_weight,p.trust_weight,p.availability_weight)<0 or (p.cost_weight+p.risk_weight+p.trust_weight+p.availability_weight)<=0: return _invalid('INVALID_WEIGHTS')
    if len(set(t.required_capabilities))!=len(t.required_capabilities) or len(set(t.required_authority_scopes))!=len(t.required_authority_scopes): return _invalid('DUPLICATE_TASK_REQUIREMENT')
    ids=[x.agent_id for x in req.bids]
    if any(not x for x in ids) or len(ids)!=len(set(ids)): return _invalid('DUPLICATE_OR_EMPTY_AGENT')
    evals=[]; feasible=[]; rejection_counts={k:0 for k in ('CAPABILITY','RISK','AVAILABILITY','AUTHORITY','TRUST')}
    required_cap=set(t.required_capabilities); required_auth=set(t.required_authority_scopes)
    for b in sorted(req.bids,key=lambda x:x.agent_id):
        if b.binding!=req.binding or b.state_epoch!=req.state_epoch: return _invalid('BID_IDENTITY_INVALID')
        if any(not _finite(x) for x in (b.cost,b.risk,b.trust,b.availability)) or b.cost<0 or not (0<=b.risk<=1 and 0<=b.trust<=1 and 0<=b.availability<=1): return _invalid('BID_VALUE_INVALID')
        if len(set(b.capabilities))!=len(b.capabilities) or len(set(b.authority_scopes))!=len(b.authority_scopes): return _invalid('DUPLICATE_BID_ATTRIBUTE')
        reasons=[]
        if not required_cap.issubset(set(b.capabilities)): reasons.append('MISSING_REQUIRED_CAPABILITY'); rejection_counts['CAPABILITY']+=1
        if b.risk>t.max_risk: reasons.append('RISK_LIMIT_EXCEEDED'); rejection_counts['RISK']+=1
        if b.availability<t.min_availability: reasons.append('AVAILABILITY_BELOW_MINIMUM'); rejection_counts['AVAILABILITY']+=1
        if not required_auth.issubset(set(b.authority_scopes)): reasons.append('MISSING_REQUIRED_AUTHORITY_SCOPE'); rejection_counts['AUTHORITY']+=1
        if b.trust<p.min_trust: reasons.append('TRUST_BELOW_MINIMUM'); rejection_counts['TRUST']+=1
        ok=not reasons
        u=_utility(b,p) if ok else None
        be=BidEvaluation(b.agent_id,ok,u,tuple(reasons),b.cost,b.risk,b.trust,b.availability)
        evals.append(be)
        if ok: feasible.append((b,u))
    if not feasible:
        if rejection_counts['CAPABILITY'] and rejection_counts['CAPABILITY']>=max(1,len(req.bids)): esc=Escalation.CAPABILITY_SHORTFALL
        elif rejection_counts['RISK'] and rejection_counts['RISK']>=max(1,len(req.bids)): esc=Escalation.RISK_EXCEEDED
        elif rejection_counts['AVAILABILITY'] and rejection_counts['AVAILABILITY']>=max(1,len(req.bids)): esc=Escalation.AVAILABILITY_SHORTFALL
        elif rejection_counts['AUTHORITY'] and rejection_counts['AUTHORITY']>=max(1,len(req.bids)): esc=Escalation.AUTHORITY_SCOPE_SHORTFALL
        else: esc=Escalation.NO_SAFE_AGENT
        nxt=NextAction.HUMAN_REVIEW_CANDIDATE if p.allow_human_escalation else NextAction.HOLD_NO_SAFE_DELEGATE_CANDIDATE
        return AuctionResult(Decision.HOLD,nxt,esc,AuctionState.NO_FEASIBLE_AGENT,('NO_SAFE_FEASIBLE_AGENT','DO_NOT_FALL_BACK_TO_CHEAP_UNSAFE_AGENT'),None,None,None,(),tuple(evals),False)
    # Deterministic ranking: utility first, then trust, lower risk, lower cost, higher availability, stable agent id.
    ranked=sorted(feasible,key=lambda x:(-x[1],-x[0].trust,x[0].risk,x[0].cost,-x[0].availability,x[0].agent_id))
    winner,wu=ranked[0]
    reserve=ranked[1][0].agent_id if len(ranked)>1 else None
    if p.reserve_required and reserve is None:
        return AuctionResult(Decision.HOLD,NextAction.HUMAN_REVIEW_CANDIDATE,Escalation.NO_SAFE_AGENT,AuctionState.NO_FEASIBLE_AGENT,('RESERVE_REQUIRED_BUT_UNAVAILABLE','DO_NOT_RELAX_SAFETY_FILTERS'),None,None,None,tuple(x[0].agent_id for x in ranked),tuple(evals),False)
    return AuctionResult(Decision.ALLOW,NextAction.DELEGATION_ASSIGNMENT_CANDIDATE,Escalation.NONE,AuctionState.ASSIGNABLE,('HARD_SAFETY_FILTERS_PASSED','WINNER_SELECTED_BY_CONSTRAINED_UTILITY','ASSIGNMENT_IS_CANDIDATE_ONLY'),winner.agent_id,reserve,float(wu),tuple(x[0].agent_id for x in ranked),tuple(evals),True)

def default_evaluation(): return evaluate(default_request())

def _fps(req,result): return (_fp((req.request_id,req.task,req.binding,req.state_epoch)),_fp(req.bids),_fp(req.policy),_fp(result))
def _integrity_payload(cf,bf,pf,of,b,e): return (cf,bf,pf,of,b,e,'NOEPIN-AL-127-PREPARED-V1')
def prepare_state(req:AuctionRequest,*,binding:str,state_epoch:str)->PreparedAuctionState:
    r=_invalid('PREPARED_BINDING_OR_EPOCH_MISMATCH') if binding!=req.binding or state_epoch!=req.state_epoch else evaluate(req)
    cf,bf,pf,of=_fps(req,r); integ=_fp(_integrity_payload(cf,bf,pf,of,binding,state_epoch))
    return PreparedAuctionState(req,r,cf,bf,pf,of,integ,binding,state_epoch)
def validate_prepared_integrity(st):
    return st.integrity_fingerprint==_fp(_integrity_payload(st.context_fingerprint,st.bid_fingerprint,st.policy_fingerprint,st.outcome_fingerprint,st.binding,st.state_epoch))
def evaluate_prepared(st:PreparedAuctionState,*,integrity_validated:bool,current_context_fingerprint:str,current_bid_fingerprint:str,current_policy_fingerprint:str,current_outcome_fingerprint:str)->AuctionResult:
    ok=(integrity_validated and validate_prepared_integrity(st) and st.binding==st.request.binding and st.state_epoch==st.request.state_epoch and current_context_fingerprint==st.context_fingerprint and current_bid_fingerprint==st.bid_fingerprint and current_policy_fingerprint==st.policy_fingerprint and current_outcome_fingerprint==st.outcome_fingerprint)
    return st.result if ok else _invalid('PREPARED_REUSE_REJECTED')
def make_delta(old:PreparedAuctionState,new:PreparedAuctionState)->AuctionDelta:
    oo={x.agent_id:x for x in old.request.bids}; nn={x.agent_id:x for x in new.request.bids}
    changed=tuple(nn[k] for k in sorted(nn) if k not in oo or _canon(nn[k])!=_canon(oo[k])); removed=tuple(sorted(set(oo)-set(nn)))
    return AuctionDelta(changed,removed,_manifest_fp(old.request),_manifest_fp(new.request))
def plan_missing_only(old:PreparedAuctionState,new:PreparedAuctionState)->MissingOnlyPlan:
    d=make_delta(old,new); ids=tuple(sorted([f'BID:{x.agent_id}' for x in d.changed_bids]+[f'REMOVED_BID:{x}' for x in d.removed_agent_ids])); meta=len(_canon({'from':d.from_manifest_fingerprint,'to':d.to_manifest_fingerprint,'ids':ids})); return MissingOnlyPlan(ids,meta,False)
