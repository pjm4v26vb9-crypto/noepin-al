"""NOEPIN AL 140 — Knowledge Refresh Scheduler — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-140
DCSR: LIMITED INTEGRATION / 限定適用.

Schedules refresh candidates for stale or volatile Knowledge without executing external
retrieval. Freshness != Truth. Refresh Candidate != Retrieval Execution. Queue Priority
!= Permission Grant. HOLD Candidate != Stop Execution. DCSR reconstruction does not
create new Knowledge, known Fact, Domain Authority, Permission, Approval, Action,
or Action Success.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str, Enum):
    ALLOW='ALLOW'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'; DENY='DENY'
class SchedulerState(str, Enum):
    CURRENT_CANDIDATE='CURRENT_CANDIDATE'; REFRESH_DUE_CANDIDATE='REFRESH_DUE_CANDIDATE'
    CRITICAL_REFRESH_REQUIRED_CANDIDATE='CRITICAL_REFRESH_REQUIRED_CANDIDATE'
    CRITICAL_STALE_HOLD_CANDIDATE='CRITICAL_STALE_HOLD_CANDIDATE'
    EMPTY='EMPTY'; INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_CANDIDATE='CONTINUE_CANDIDATE'; REFRESH_QUEUE_CANDIDATE='REFRESH_QUEUE_CANDIDATE'
    REFRESH_REQUIRED_BEFORE_USE_CANDIDATE='REFRESH_REQUIRED_BEFORE_USE_CANDIDATE'
    HOLD_STALE_DEPENDENT_ACTION_CANDIDATE='HOLD_STALE_DEPENDENT_ACTION_CANDIDATE'
    NO_KNOWLEDGE_CANDIDATE='NO_KNOWLEDGE_CANDIDATE'; REVIEW_CANDIDATE='REVIEW_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; REFRESH_DUE='REFRESH_DUE'; CRITICAL_EXPIRED='CRITICAL_EXPIRED'
    REFRESH_FAILED_CRITICAL='REFRESH_FAILED_CRITICAL'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'
class RefreshStatus(str, Enum):
    NOT_ATTEMPTED='NOT_ATTEMPTED'; SUCCEEDED='SUCCEEDED'; FAILED='FAILED'; UNAVAILABLE='UNAVAILABLE'

@dataclass(frozen=True)
class KnowledgeItem:
    knowledge_id:str; source_id:str; purpose:str; provenance_ids:tuple[str,...]
    importance:float; volatility:float; usage_rate:float; refresh_cost:float
    age_seconds:float; ttl_seconds:float; critical:bool; refresh_status:RefreshStatus
    binding:str; state_epoch:str

@dataclass(frozen=True)
class RefreshPolicy:
    volatility_weight:float=.30; importance_weight:float=.25; usage_weight:float=.20
    freshness_weight:float=.30; refresh_cost_penalty:float=.10
    low_importance_cost_extension:float=1.50; max_interval_multiplier:float=3.0

@dataclass(frozen=True)
class SchedulerRequest:
    request_id:str; items:tuple[KnowledgeItem,...]; policy:RefreshPolicy; binding:str; state_epoch:str

@dataclass(frozen=True)
class RefreshEvidence:
    knowledge_id:str; effective_age_seconds:float; freshness_ratio:float; computed_interval_seconds:float
    priority:float; next_refresh_in_seconds:float; due:bool; expired:bool; stale_explicit:bool
    critical:bool; refresh_status:RefreshStatus; reasons:tuple[str,...]

@dataclass(frozen=True)
class RefreshQueueEntry:
    knowledge_id:str; priority:float; next_refresh_in_seconds:float; critical:bool
    expired:bool; stale_explicit:bool; refresh_candidate:bool=True

@dataclass(frozen=True)
class SchedulerResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; scheduler_state:SchedulerState
    refresh_queue:tuple[RefreshQueueEntry,...]; evidence:tuple[RefreshEvidence,...]
    next_refresh_time_seconds:float|None; stale_knowledge_ids:tuple[str,...]; reasons:tuple[str,...]
    next_gate_candidate:bool
    freshness_promoted_to_truth:bool=False; knowledge_promoted_to_world_truth:bool=False
    refresh_candidate_executed:bool=False; external_retrieval_executed:bool=False
    timestamp_mutated:bool=False; knowledge_write_performed:bool=False; knowledge_delete_performed:bool=False
    source_promoted_to_authority:bool=False; dcsr_reconstruction_created_knowledge:bool=False
    sender_authority_inherited:bool=False; sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False
    permission_granted:bool=False; approval_executed:bool=False; authority_granted:bool=False
    stop_executed:bool=False; action_executed:bool=False; plan_committed:bool=False
    publish_executed:bool=False; external_write_performed:bool=False; world_truth_proven:bool=False
    domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False

@dataclass(frozen=True)
class PreparedSchedulerState:
    request:SchedulerRequest; result:SchedulerResult; context_fingerprint:str; items_fingerprint:str
    policy_fingerprint:str; outcome_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str

@dataclass(frozen=True)
class RefreshDelta:
    changed_items:tuple[KnowledgeItem,...]; removed_knowledge_ids:tuple[str,...]; policy_changed:bool
    from_manifest_fingerprint:str; to_manifest_fingerprint:str

@dataclass(frozen=True)
class MissingOnlyPlan:
    missing_or_changed_record_ids:tuple[str,...]; metadata_bytes_required:int; full_resend_required:bool


def _obj(v):
    if isinstance(v,Enum): return v.value
    if is_dataclass(v): return {f.name:_obj(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v,dict): return {str(k):_obj(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(tuple,list)): return [_obj(x) for x in v]
    return v

def _canon(v): return json.dumps(_obj(v),ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def _fp(v): return sha256(_canon(v)).hexdigest()
def _finite(x): return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(float(x))
def _clamp(x): return 0.0 if x<0 else (1.0 if x>1 else float(x))
def _manifest_fp(req): return _fp((req.items,req.policy,req.binding,req.state_epoch))

def default_policy(): return RefreshPolicy()
def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    item=KnowledgeItem('KN-140-A','SRC-CANONICAL','PROJECT-A',('TRACE-140-A',),.85,.20,.55,.20,120.0,3600.0,False,RefreshStatus.NOT_ATTEMPTED,b,e)
    return SchedulerRequest('REQ-140',(item,),default_policy(),b,e)

def _invalid(reason):
    return SchedulerResult(Decision.HOLD,NextAction.REVIEW_CANDIDATE,Escalation.INVALID_CONFIGURATION,SchedulerState.INVALID,(),(),None,(),(reason,'NO_EXTERNAL_RETRIEVAL','NO_KNOWLEDGE_WRITE'),False)

def _validate(req):
    p=req.policy
    nums=(p.volatility_weight,p.importance_weight,p.usage_weight,p.freshness_weight,p.refresh_cost_penalty,p.low_importance_cost_extension,p.max_interval_multiplier)
    if not all(_finite(x) for x in nums): return 'NONFINITE_POLICY'
    if any(x<0 for x in nums) or p.max_interval_multiplier<1: return 'INVALID_POLICY_RANGE'
    ids=set()
    for x in req.items:
        if x.knowledge_id in ids: return 'DUPLICATE_KNOWLEDGE_ID'
        ids.add(x.knowledge_id)
        if not x.knowledge_id or not x.source_id: return 'EMPTY_KNOWLEDGE_KEY'
        if x.binding!=req.binding or x.state_epoch!=req.state_epoch: return 'KNOWLEDGE_STATE_BINDING_MISMATCH'
        vals=(x.importance,x.volatility,x.usage_rate,x.refresh_cost)
        if not all(_finite(v) and 0<=v<=1 for v in vals): return 'KNOWLEDGE_SCORE_RANGE_OR_NONFINITE'
        if not _finite(x.age_seconds) or x.age_seconds<0: return 'AGE_RANGE_OR_NONFINITE'
        if not _finite(x.ttl_seconds) or x.ttl_seconds<=0: return 'TTL_RANGE_OR_NONFINITE'
        if len(set(x.provenance_ids))!=len(x.provenance_ids): return 'DUPLICATE_PROVENANCE_ID'
    return None

def _interval(x,p):
    pressure=1.0 + 1.75*x.volatility + .75*x.usage_rate + .50*x.importance
    base=x.ttl_seconds/pressure
    extension=1.0 + p.low_importance_cost_extension*x.refresh_cost*(1.0-x.importance)
    interval=base*extension
    if x.critical: interval=min(interval,x.ttl_seconds)
    return max(1.0,min(interval,x.ttl_seconds*p.max_interval_multiplier))

def _evidence(x,p):
    effective_age=0.0 if x.refresh_status==RefreshStatus.SUCCEEDED else x.age_seconds
    interval=_interval(x,p)
    freshness_ratio=effective_age/x.ttl_seconds
    expired=effective_age>=x.ttl_seconds
    due=effective_age>=interval
    stale_explicit=x.refresh_status in (RefreshStatus.FAILED,RefreshStatus.UNAVAILABLE) and (due or expired)
    freshness_risk=_clamp(effective_age/max(interval,1.0))
    priority=(p.freshness_weight*freshness_risk + p.volatility_weight*x.volatility + p.importance_weight*x.importance + p.usage_weight*x.usage_rate - p.refresh_cost_penalty*x.refresh_cost)
    if expired: priority+=.20
    if x.critical: priority+=.15
    if stale_explicit: priority+=.10
    priority=_clamp(priority)
    next_in=max(0.0,interval-effective_age)
    reasons=[]
    if x.refresh_status==RefreshStatus.SUCCEEDED: reasons.append('REFRESH_SUCCESS_TIMESTAMP_RESET_CANDIDATE')
    if expired: reasons.append('TTL_EXPIRED')
    elif due: reasons.append('REFRESH_INTERVAL_DUE')
    if x.volatility>=.70: reasons.append('HIGH_VOLATILITY')
    if x.importance<=.25 and x.refresh_cost>=.75: reasons.append('LOW_IMPORTANCE_HIGH_COST_INTERVAL_EXTENSION')
    if stale_explicit: reasons.append('REFRESH_FAILURE_STALE_EXPLICIT')
    if x.critical: reasons.append('CRITICAL_KNOWLEDGE')
    if not reasons: reasons.append('CURRENT_WITHIN_REFRESH_INTERVAL')
    return RefreshEvidence(x.knowledge_id,effective_age,freshness_ratio,interval,priority,next_in,due,expired,stale_explicit,x.critical,x.refresh_status,tuple(reasons))

def evaluate(req):
    err=_validate(req)
    if err: return _invalid(err)
    if not req.items:
        return SchedulerResult(Decision.ALLOW,NextAction.NO_KNOWLEDGE_CANDIDATE,Escalation.NONE,SchedulerState.EMPTY,(),(),None,(),('NO_KNOWLEDGE_ITEMS','NO_EXTERNAL_RETRIEVAL'),True)
    ev=tuple(_evidence(x,req.policy) for x in sorted(req.items,key=lambda z:z.knowledge_id))
    by_id={x.knowledge_id:x for x in req.items}
    queue_ev=[e for e in ev if e.due or e.expired or e.stale_explicit]
    queue_ev.sort(key=lambda e:(0 if (e.critical and e.expired) else 1, -e.priority, e.next_refresh_in_seconds, e.knowledge_id))
    queue=tuple(RefreshQueueEntry(e.knowledge_id,e.priority,e.next_refresh_in_seconds,e.critical,e.expired,e.stale_explicit) for e in queue_ev)
    stale=tuple(sorted(e.knowledge_id for e in ev if e.stale_explicit))
    critical_failed=tuple(e for e in queue_ev if e.critical and e.expired and e.refresh_status in (RefreshStatus.FAILED,RefreshStatus.UNAVAILABLE))
    critical_expired=tuple(e for e in queue_ev if e.critical and e.expired)
    next_time=min((e.next_refresh_in_seconds for e in ev),default=None)
    if critical_failed:
        return SchedulerResult(Decision.HOLD,NextAction.HOLD_STALE_DEPENDENT_ACTION_CANDIDATE,Escalation.REFRESH_FAILED_CRITICAL,SchedulerState.CRITICAL_STALE_HOLD_CANDIDATE,queue,ev,next_time,stale,('CRITICAL_KNOWLEDGE_EXPIRED_AND_REFRESH_UNAVAILABLE','STALE_EXPLICIT','DEPENDENT_ACTION_HOLD_CANDIDATE_ONLY','NO_EXTERNAL_RETRIEVAL','NO_STOP_EXECUTION'),False)
    if critical_expired:
        return SchedulerResult(Decision.HOLD,NextAction.REFRESH_REQUIRED_BEFORE_USE_CANDIDATE,Escalation.CRITICAL_EXPIRED,SchedulerState.CRITICAL_REFRESH_REQUIRED_CANDIDATE,queue,ev,next_time,stale,('CRITICAL_KNOWLEDGE_EXPIRED','REFRESH_FIRST_CANDIDATE','NO_EXTERNAL_RETRIEVAL','NO_STOP_EXECUTION'),False)
    if queue:
        return SchedulerResult(Decision.ALLOW,NextAction.REFRESH_QUEUE_CANDIDATE,Escalation.REFRESH_DUE,SchedulerState.REFRESH_DUE_CANDIDATE,queue,ev,next_time,stale,('REFRESH_QUEUE_CANDIDATE_ONLY','STALE_MARKED_WHEN_REFRESH_FAILED','NO_EXTERNAL_RETRIEVAL'),True)
    return SchedulerResult(Decision.ALLOW,NextAction.CONTINUE_CANDIDATE,Escalation.NONE,SchedulerState.CURRENT_CANDIDATE,(),ev,next_time,(),('KNOWLEDGE_WITHIN_REFRESH_INTERVAL','NO_EXTERNAL_RETRIEVAL'),True)

def default_evaluation(): return evaluate(default_request())

def _fps(req,res): return (_fp((req.request_id,req.binding,req.state_epoch)),_fp(req.items),_fp(req.policy),_fp(res))
def prepare_state(req,binding,state_epoch):
    if binding!=req.binding or state_epoch!=req.state_epoch: raise ValueError('PREPARED_BINDING_MISMATCH')
    res=evaluate(req); c,i,p,o=_fps(req,res); integ=_fp((c,i,p,o,binding,state_epoch))
    return PreparedSchedulerState(req,res,c,i,p,o,integ,binding,state_epoch)
def validate_prepared_integrity(st): return st.integrity_fingerprint==_fp((st.context_fingerprint,st.items_fingerprint,st.policy_fingerprint,st.outcome_fingerprint,st.binding,st.state_epoch))
def evaluate_prepared(st,*,integrity_validated,current_context_fingerprint,current_items_fingerprint,current_policy_fingerprint,current_outcome_fingerprint):
    if not integrity_validated or not validate_prepared_integrity(st): return _invalid('PREPARED_INTEGRITY_NOT_VALIDATED')
    if (current_context_fingerprint,current_items_fingerprint,current_policy_fingerprint,current_outcome_fingerprint)!=(st.context_fingerprint,st.items_fingerprint,st.policy_fingerprint,st.outcome_fingerprint): return _invalid('PREPARED_FINGERPRINT_MISMATCH')
    return st.result

def make_delta(old,new):
    a={x.knowledge_id:x for x in old.request.items}; b={x.knowledge_id:x for x in new.request.items}
    changed=tuple(b[k] for k in sorted(b) if k not in a or a[k]!=b[k]); removed=tuple(sorted(set(a)-set(b)))
    return RefreshDelta(changed,removed,old.policy_fingerprint!=new.policy_fingerprint,_manifest_fp(old.request),_manifest_fp(new.request))
def plan_missing_only(old,new):
    d=make_delta(old,new); ids=[f'KNOWLEDGE:{x.knowledge_id}' for x in d.changed_items]+[f'KNOWLEDGE:{x}' for x in d.removed_knowledge_ids]
    if d.policy_changed: ids.append('REFRESH_POLICY')
    meta=len(_canon((tuple(ids),d.from_manifest_fingerprint,d.to_manifest_fingerprint)))
    return MissingOnlyPlan(tuple(ids),meta,False)
