"""NOEPIN AL 130 — Reviewer Rotation Scheduler — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-130
DCSR: DIRECT INTEGRATION / 直接統合.

Reviewer assignments and independence scores are scheduling candidates/audit evidence only.
They do not grant permission, authority, approval, execution, safety proof, truth, or action success.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str, Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class RotationState(str, Enum):
    ASSIGNABLE='ASSIGNABLE'; HUMAN_REVIEW_REQUIRED='HUMAN_REVIEW_REQUIRED'; NO_INDEPENDENT_REVIEWER='NO_INDEPENDENT_REVIEWER'; INVALID='INVALID'
class NextAction(str, Enum):
    REVIEWER_ASSIGNMENT_CANDIDATE='REVIEWER_ASSIGNMENT_CANDIDATE'; HUMAN_REVIEW_CANDIDATE='HUMAN_REVIEW_CANDIDATE'; HOLD_REVIEWER_ROTATION_CANDIDATE='HOLD_REVIEWER_ROTATION_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; INDEPENDENCE_SHORTFALL='INDEPENDENCE_SHORTFALL'; NO_ELIGIBLE_REVIEWER='NO_ELIGIBLE_REVIEWER'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'
class TaskRisk(str, Enum):
    LOW='LOW'; MEDIUM='MEDIUM'; HIGH='HIGH'; CRITICAL='CRITICAL'

@dataclass(frozen=True)
class ReviewerAgent:
    agent_id:str
    model_family:str
    provider:str
    trust:float
    available:bool
    review_capable:bool
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class ReviewEvent:
    subject_agent_id:str
    reviewer_agent_id:str
    task_id:str
    sequence:int
    model_family_pair:str
    provider_pair:str

@dataclass(frozen=True)
class ReviewTask:
    task_id:str
    subject_agent_id:str
    subject_model_family:str
    subject_provider:str
    risk:TaskRisk
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class ConflictRules:
    forbidden_pairs:tuple[tuple[str,str],...]=()
    min_reviewer_trust:float=.55
    recent_pair_window:int=4
    max_same_pair_in_window:int=1
    high_correlation_threshold:float=.78
    critical_min_independence:float=.72
    require_different_family_for_critical:bool=True
    require_different_provider_for_critical:bool=True

@dataclass(frozen=True)
class RotationRequest:
    request_id:str
    task:ReviewTask
    agents:tuple[ReviewerAgent,...]
    history:tuple[ReviewEvent,...]
    rules:ConflictRules
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class ReviewerEvaluation:
    reviewer_agent_id:str
    eligible:bool
    independence_score:float
    rotation_penalty:float
    fairness_penalty:float
    same_family:bool
    same_provider:bool
    recent_pair_count:int
    reason_codes:tuple[str,...]

@dataclass(frozen=True)
class RotationResult:
    decision:Decision
    next_action:NextAction
    escalation:Escalation
    rotation_state:RotationState
    reasons:tuple[str,...]
    reviewer_assignment:str|None
    reserve_reviewers:tuple[str,...]
    independence_score:float
    rotation_plan:tuple[str,...]
    evaluations:tuple[ReviewerEvaluation,...]
    next_gate_candidate:bool
    reviewer_assignment_promoted_to_permission:bool=False
    reviewer_assignment_executed:bool=False
    review_executed:bool=False
    independence_promoted_to_safety_proof:bool=False
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
class PreparedRotationState:
    request:RotationRequest
    result:RotationResult
    context_fingerprint:str
    agent_fingerprint:str
    history_fingerprint:str
    policy_fingerprint:str
    outcome_fingerprint:str
    integrity_fingerprint:str
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class RotationDelta:
    changed_agents:tuple[ReviewerAgent,...]
    removed_agent_ids:tuple[str,...]
    appended_history:tuple[ReviewEvent,...]
    task_changed:bool
    rules_changed:bool
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
def _manifest_fp(req): return _fp((req.task,req.agents,req.history,req.rules,req.binding,req.state_epoch))

def default_rules(): return ConflictRules()

def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    task=ReviewTask('TASK-130','AGENT-SUBJECT','FAMILY-A','PROVIDER-X',TaskRisk.CRITICAL,b,e)
    agents=(
        ReviewerAgent('REVIEWER-A','FAMILY-A','PROVIDER-X',.92,True,True,b,e),
        ReviewerAgent('REVIEWER-B','FAMILY-B','PROVIDER-Y',.88,True,True,b,e),
        ReviewerAgent('REVIEWER-C','FAMILY-C','PROVIDER-Z',.84,True,True,b,e),
        ReviewerAgent('AGENT-SUBJECT','FAMILY-A','PROVIDER-X',.95,True,True,b,e),
    )
    hist=(
        ReviewEvent('AGENT-SUBJECT','REVIEWER-C','OLD-1',1,'FAMILY-A|FAMILY-C','PROVIDER-X|PROVIDER-Z'),
        ReviewEvent('OTHER','REVIEWER-B','OLD-2',2,'FAMILY-Q|FAMILY-B','PROVIDER-Q|PROVIDER-Y'),
    )
    return RotationRequest('DEFAULT-130',task,agents,hist,default_rules(),b,e)

def _invalid(reason):
    return RotationResult(Decision.HOLD,NextAction.HOLD_REVIEWER_ROTATION_CANDIDATE,Escalation.INVALID_CONFIGURATION,RotationState.INVALID,(reason,'NO_PERMISSION_APPROVAL_OR_EXECUTION_PROMOTION'),None,(),0.0,(),(),False)

def _validate(req:RotationRequest):
    if not req.request_id or not req.binding or not req.state_epoch: return 'INVALID_REQUEST_IDENTITY'
    t=req.task; r=req.rules
    if not t.task_id or not t.subject_agent_id or not t.subject_model_family or not t.subject_provider: return 'INVALID_TASK_IDENTITY'
    if t.binding!=req.binding or t.state_epoch!=req.state_epoch: return 'TASK_BINDING_MISMATCH'
    nums=(r.min_reviewer_trust,r.high_correlation_threshold,r.critical_min_independence)
    if any(not _finite(x) for x in nums): return 'INVALID_NUMERIC'
    if any(not 0<=x<=1 for x in nums): return 'INVALID_RANGE'
    if not isinstance(r.recent_pair_window,int) or isinstance(r.recent_pair_window,bool) or r.recent_pair_window<0: return 'INVALID_RECENT_WINDOW'
    if not isinstance(r.max_same_pair_in_window,int) or isinstance(r.max_same_pair_in_window,bool) or r.max_same_pair_in_window<0: return 'INVALID_PAIR_LIMIT'
    ids=[a.agent_id for a in req.agents]
    if any(not x for x in ids) or len(ids)!=len(set(ids)): return 'DUPLICATE_OR_EMPTY_AGENT'
    for a in req.agents:
        if a.binding!=req.binding or a.state_epoch!=req.state_epoch or not a.model_family or not a.provider: return 'AGENT_IDENTITY_INVALID'
        if not _finite(a.trust) or not 0<=a.trust<=1: return 'AGENT_TRUST_INVALID'
    for h in req.history:
        if not h.subject_agent_id or not h.reviewer_agent_id or not h.task_id: return 'HISTORY_IDENTITY_INVALID'
        if not isinstance(h.sequence,int) or isinstance(h.sequence,bool) or h.sequence<0: return 'HISTORY_SEQUENCE_INVALID'
    for x,y in r.forbidden_pairs:
        if not x or not y: return 'INVALID_FORBIDDEN_PAIR'
    return None

def _pair_forbidden(subject,reviewer,rules):
    return (subject,reviewer) in rules.forbidden_pairs or (reviewer,subject) in rules.forbidden_pairs

def _correlation(task:ReviewTask,a:ReviewerAgent):
    # Simple auditable correlation proxy: shared family carries more correlation than shared provider.
    corr=0.0
    if a.model_family==task.subject_model_family: corr+=.62
    if a.provider==task.subject_provider: corr+=.28
    return min(1.0,corr)

def evaluate(req:RotationRequest)->RotationResult:
    bad=_validate(req)
    if bad: return _invalid(bad)
    t=req.task; r=req.rules
    recent=sorted(req.history,key=lambda h:h.sequence)[-r.recent_pair_window:] if r.recent_pair_window else []
    total_counts={}
    pair_counts={}
    for h in req.history:
        total_counts[h.reviewer_agent_id]=total_counts.get(h.reviewer_agent_id,0)+1
    for h in recent:
        if h.subject_agent_id==t.subject_agent_id:
            pair_counts[h.reviewer_agent_id]=pair_counts.get(h.reviewer_agent_id,0)+1
    max_reviews=max(total_counts.values(),default=0)
    evals=[]
    candidates=[]
    for a in sorted(req.agents,key=lambda x:x.agent_id):
        reasons=[]; eligible=True
        same_family=a.model_family==t.subject_model_family; same_provider=a.provider==t.subject_provider
        pair_count=pair_counts.get(a.agent_id,0)
        if a.agent_id==t.subject_agent_id:
            eligible=False; reasons.append('SELF_REVIEW_FORBIDDEN')
        if not a.available:
            eligible=False; reasons.append('REVIEWER_UNAVAILABLE')
        if not a.review_capable:
            eligible=False; reasons.append('REVIEW_CAPABILITY_MISSING')
        if a.trust<r.min_reviewer_trust:
            eligible=False; reasons.append('TRUST_BELOW_MINIMUM')
        if _pair_forbidden(t.subject_agent_id,a.agent_id,r):
            eligible=False; reasons.append('CONFLICT_PAIR_FORBIDDEN')
        corr=_correlation(t,a)
        if pair_count>=r.max_same_pair_in_window and r.max_same_pair_in_window>=0 and pair_count>0:
            eligible=False; reasons.append('RECENT_PAIR_LIMIT')
        if corr>=r.high_correlation_threshold and pair_count>0:
            eligible=False; reasons.append('HIGH_CORRELATION_REPEAT')
        if t.risk==TaskRisk.CRITICAL:
            if r.require_different_family_for_critical and same_family:
                eligible=False; reasons.append('CRITICAL_REQUIRES_DIFFERENT_FAMILY')
            if r.require_different_provider_for_critical and same_provider:
                eligible=False; reasons.append('CRITICAL_REQUIRES_DIFFERENT_PROVIDER')
        rotation_penalty=min(1.0,.30*pair_count)
        fairness_penalty=0.0 if max_reviews==0 else .20*(total_counts.get(a.agent_id,0)/max_reviews)
        independence=max(0.0,min(1.0,1.0-corr-rotation_penalty-fairness_penalty+.10*a.trust))
        if t.risk==TaskRisk.CRITICAL and independence<r.critical_min_independence:
            eligible=False; reasons.append('CRITICAL_INDEPENDENCE_BELOW_MINIMUM')
        if eligible:
            reasons.append('ELIGIBLE_REVIEWER_CANDIDATE')
        ev=ReviewerEvaluation(a.agent_id,eligible,independence,rotation_penalty,fairness_penalty,same_family,same_provider,pair_count,tuple(reasons))
        evals.append(ev)
        if eligible: candidates.append((a,ev))
    if not candidates:
        state=RotationState.NO_INDEPENDENT_REVIEWER if t.risk==TaskRisk.CRITICAL else RotationState.HUMAN_REVIEW_REQUIRED
        decision=Decision.HOLD if t.risk==TaskRisk.CRITICAL else Decision.HUMAN_APPROVAL
        esc=Escalation.INDEPENDENCE_SHORTFALL if t.risk==TaskRisk.CRITICAL else Escalation.NO_ELIGIBLE_REVIEWER
        nxt=NextAction.HOLD_REVIEWER_ROTATION_CANDIDATE if t.risk==TaskRisk.CRITICAL else NextAction.HUMAN_REVIEW_CANDIDATE
        return RotationResult(decision,nxt,esc,state,('NO_ELIGIBLE_INDEPENDENT_REVIEWER','DO_NOT_RELAX_INDEPENDENCE_FOR_SPEED_OR_COST'),None,(),0.0,(),tuple(evals),False)
    # Higher independence/trust, lower recent/fairness use; agent_id gives deterministic tie-break.
    ranked=sorted(candidates,key=lambda z:(-z[1].independence_score,-z[0].trust,z[1].recent_pair_count,z[1].fairness_penalty,z[0].agent_id))
    top,tev=ranked[0]
    reserves=tuple(x.agent_id for x,_ in ranked[1:])
    plan=tuple(x.agent_id for x,_ in ranked)
    return RotationResult(Decision.ALLOW,NextAction.REVIEWER_ASSIGNMENT_CANDIDATE,Escalation.NONE,RotationState.ASSIGNABLE,('INDEPENDENT_REVIEWER_CANDIDATE','ROTATION_HISTORY_APPLIED','NO_PERMISSION_APPROVAL_OR_EXECUTION_PROMOTION'),top.agent_id,reserves,tev.independence_score,plan,tuple(evals),True)

def default_evaluation(): return evaluate(default_request())

def _fps(req,result): return (_fp((req.request_id,req.task,req.binding,req.state_epoch)),_fp(req.agents),_fp(req.history),_fp(req.rules),_fp(result))
def _integrity_payload(cf,af,hf,pf,of,b,e): return (cf,af,hf,pf,of,b,e,'NOEPIN-AL-130-PREPARED-V1')
def prepare_state(req:RotationRequest,*,binding:str,state_epoch:str)->PreparedRotationState:
    rr=_invalid('PREPARED_BINDING_OR_EPOCH_MISMATCH') if binding!=req.binding or state_epoch!=req.state_epoch else evaluate(req)
    cf,af,hf,pf,of=_fps(req,rr); integ=_fp(_integrity_payload(cf,af,hf,pf,of,binding,state_epoch))
    return PreparedRotationState(req,rr,cf,af,hf,pf,of,integ,binding,state_epoch)
def validate_prepared_integrity(st):
    if not isinstance(st,PreparedRotationState): return False
    return st.integrity_fingerprint==_fp(_integrity_payload(st.context_fingerprint,st.agent_fingerprint,st.history_fingerprint,st.policy_fingerprint,st.outcome_fingerprint,st.binding,st.state_epoch))
def evaluate_prepared(st:PreparedRotationState,*,integrity_validated:bool,current_context_fingerprint:str,current_agent_fingerprint:str,current_history_fingerprint:str,current_policy_fingerprint:str,current_outcome_fingerprint:str)->RotationResult:
    if not integrity_validated or not validate_prepared_integrity(st): return _invalid('PREPARED_INTEGRITY_NOT_VALIDATED')
    if (current_context_fingerprint,current_agent_fingerprint,current_history_fingerprint,current_policy_fingerprint,current_outcome_fingerprint)!=(st.context_fingerprint,st.agent_fingerprint,st.history_fingerprint,st.policy_fingerprint,st.outcome_fingerprint): return _invalid('PREPARED_FINGERPRINT_MISMATCH')
    return st.result

def make_delta(old:PreparedRotationState,new:PreparedRotationState)->RotationDelta:
    om={a.agent_id:a for a in old.request.agents}; nm={a.agent_id:a for a in new.request.agents}
    changed=tuple(nm[k] for k in sorted(nm) if k not in om or _canon(nm[k])!=_canon(om[k]))
    removed=tuple(k for k in sorted(om) if k not in nm)
    oh=old.request.history; nh=new.request.history
    appended=nh[len(oh):] if len(nh)>=len(oh) and nh[:len(oh)]==oh else nh
    return RotationDelta(changed,removed,tuple(appended),old.request.task!=new.request.task,old.request.rules!=new.request.rules,_manifest_fp(old.request),_manifest_fp(new.request))

def plan_missing_only(old:PreparedRotationState,new:PreparedRotationState)->MissingOnlyPlan:
    d=make_delta(old,new); ids=[]
    ids += [f'AGENT:{a.agent_id}' for a in d.changed_agents]
    ids += [f'AGENT_REMOVED:{x}' for x in d.removed_agent_ids]
    ids += [f'HISTORY:{h.sequence}:{h.subject_agent_id}:{h.reviewer_agent_id}' for h in d.appended_history]
    if d.task_changed: ids.append('TASK')
    if d.rules_changed: ids.append('RULES')
    return MissingOnlyPlan(tuple(ids),len(_canon((d.from_manifest_fingerprint,d.to_manifest_fingerprint,ids))),False)
