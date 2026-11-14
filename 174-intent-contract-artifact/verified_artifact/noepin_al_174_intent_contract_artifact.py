"""NOEPIN AL 174 — Intent Contract Artifact — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-174
DCSR: DIRECT INTEGRATION / 直接統合.

Deterministic, side-effect-free typed safety artifact for binding a user goal, allowed/denied
actions, target scope, consent identifier, and timezone-aware creation/expiry times into one
canonical Intent Contract fingerprint. It validates construction and evaluates Action/Target/Time
against the contract. DENY/HOLD/ALLOW are contract-match decisions only: this artifact does not
grant permission, execute consent, call tools, perform actions, write state, or promote any cache
or reconstructed state to authoritative state.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import json, math, re

class Decision(str, Enum): ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class EngineState(str, Enum):
    INTENT_CONTRACT_MATCH_CANDIDATE='INTENT_CONTRACT_MATCH_CANDIDATE'
    CONTRACT_BLOCK_CANDIDATE='CONTRACT_BLOCK_CANDIDATE'
    INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_POLICY_PERMIT_EVALUATION_CANDIDATE='CONTINUE_POLICY_PERMIT_EVALUATION_CANDIDATE'
    RETAIN_NO_ACTION_CANDIDATE='RETAIN_NO_ACTION_CANDIDATE'
    REVIEW_CONTRACT_CANDIDATE='REVIEW_CONTRACT_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'
    INVALID_CONFIGURATION='INVALID_CONFIGURATION'
    CONTRACT_FINGERPRINT_MISMATCH='CONTRACT_FINGERPRINT_MISMATCH'
    ACTION_EXPLICITLY_DENIED='ACTION_EXPLICITLY_DENIED'
    ACTION_NOT_ALLOWED='ACTION_NOT_ALLOWED'
    TARGET_OUT_OF_SCOPE='TARGET_OUT_OF_SCOPE'
    CONTRACT_EXPIRED='CONTRACT_EXPIRED'
    CONTRACT_NOT_YET_ACTIVE='CONTRACT_NOT_YET_ACTIVE'

@dataclass(frozen=True)
class IntentContract:
    schema:str
    user_goal:str
    allowed_actions:tuple[str,...]
    denied_actions:tuple[str,...]
    scope_targets:tuple[str,...]
    consent_id:str
    created_time:str
    expiry_time:str
    fingerprint:str

@dataclass(frozen=True)
class IntentCheckRequest:
    request_id:str
    action:str
    target:str
    at_time:str
    contract:IntentContract
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class IntentCheckResult:
    decision:Decision
    next_action:NextAction
    escalation:Escalation
    engine_state:EngineState
    request_id:str
    contract_fingerprint_valid:bool
    action_allowed:bool
    action_explicitly_denied:bool
    target_in_scope:bool
    time_active:bool
    consent_id_present:bool
    normalized_action:str
    normalized_target:str
    contract_fingerprint:str
    next_gate_candidate:bool
    reasons:tuple[str,...]
    source_contract_mutated:bool=False
    consent_executed:bool=False
    policy_decision_executed:bool=False
    permit_issued:bool=False
    permission_granted:bool=False
    tool_invoked:bool=False
    action_executed:bool=False
    action_success:bool=False
    file_write_executed:bool=False
    network_send_executed:bool=False
    external_write_performed:bool=False
    authoritative_state_created:bool=False
    cached_state_promoted:bool=False
    reconstructed_state_promoted:bool=False
    partial_state_promoted:bool=False
    dcsr_reconstruction_created_fact:bool=False
    sender_authority_inherited:bool=False
    sender_intent_inherited:bool=False
    sender_agreement_inherited:bool=False
    approval_executed:bool=False
    authority_granted:bool=False
    stop_executed:bool=False
    world_truth_proven:bool=False
    domain_authority_promoted:bool=False
    safety_proven:bool=False

@dataclass(frozen=True)
class PreparedIntentState:
    request:IntentCheckRequest
    result:IntentCheckResult
    contract_fingerprint:str
    query_fingerprint:str
    result_fingerprint:str
    integrity_fingerprint:str
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class IntentChange:
    contract_changed:bool
    query_changed:bool
    from_fingerprint:str
    to_fingerprint:str

@dataclass(frozen=True)
class MissingOnlyPlan:
    missing_or_changed_record_ids:tuple[str,...]
    metadata_bytes_required:int
    full_resend_required:bool

_WS=re.compile(r'\s+')

def _obj(v):
    if isinstance(v,Enum): return v.value
    if is_dataclass(v): return {f.name:_obj(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v,dict): return {str(k):_obj(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(tuple,list)): return [_obj(x) for x in v]
    if isinstance(v,datetime): return v.isoformat()
    if isinstance(v,float):
        if not math.isfinite(v): raise ValueError('non-finite float')
        return v
    return v

def _canon(v): return json.dumps(_obj(v),ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def _fp(v): return sha256(_canon(v)).hexdigest()
def _norm_text(v:str)->str: return _WS.sub(' ',v.strip())
def _norm_action(v:str)->str: return _norm_text(v).casefold()
def _norm_target(v:str)->str: return _norm_text(v)

def _parse_aware(s:str)->datetime:
    try: d=datetime.fromisoformat(s)
    except Exception as e: raise ValueError('invalid ISO datetime') from e
    if d.tzinfo is None or d.utcoffset() is None: raise ValueError('timezone-aware datetime required')
    return d.astimezone(timezone.utc)

def _contract_payload(schema,user_goal,allowed_actions,denied_actions,scope_targets,consent_id,created_time,expiry_time):
    return {'schema':schema,'user_goal':user_goal,'allowed_actions':allowed_actions,'denied_actions':denied_actions,'scope_targets':scope_targets,'consent_id':consent_id,'created_time':created_time,'expiry_time':expiry_time}

def build_contract(*,user_goal,allowed_actions,denied_actions,scope_targets,consent_id,created_time,expiry_time):
    goal=_norm_text(str(user_goal)); consent=_norm_text(str(consent_id))
    if not goal or not consent: raise ValueError('user_goal and consent_id are required')
    allowed=tuple(sorted(set(_norm_action(str(x)) for x in allowed_actions if _norm_text(str(x)))))
    denied=tuple(sorted(set(_norm_action(str(x)) for x in denied_actions if _norm_text(str(x)))))
    scope=tuple(sorted(set(_norm_target(str(x)) for x in scope_targets if _norm_text(str(x)))))
    if not allowed: raise ValueError('allowed_actions must not be empty')
    if not scope: raise ValueError('scope_targets must not be empty')
    if set(allowed)&set(denied): raise ValueError('allowed/denied action conflict')
    c=_parse_aware(str(created_time)); e=_parse_aware(str(expiry_time))
    if e<=c: raise ValueError('expiry_time must be after created_time')
    ci=c.isoformat(); ei=e.isoformat(); schema='NOEPIN_AL_INTENT_CONTRACT_V1'
    payload=_contract_payload(schema,goal,allowed,denied,scope,consent,ci,ei)
    return IntentContract(schema,goal,allowed,denied,scope,consent,ci,ei,_fp(payload))

def _contract_fp_valid(c:IntentContract)->bool:
    try:
        payload=_contract_payload(c.schema,c.user_goal,c.allowed_actions,c.denied_actions,c.scope_targets,c.consent_id,c.created_time,c.expiry_time)
        return c.fingerprint==_fp(payload)
    except Exception:
        return False

def _invalid(q,reason,esc=Escalation.INVALID_CONFIGURATION):
    c=getattr(q,'contract',None)
    return IntentCheckResult(Decision.HOLD,NextAction.REVIEW_CONTRACT_CANDIDATE,esc,EngineState.INVALID,getattr(q,'request_id',''),False,False,False,False,False,bool(getattr(c,'consent_id','')),_norm_action(getattr(q,'action','')) if getattr(q,'action',None) is not None else '',_norm_target(getattr(q,'target','')) if getattr(q,'target',None) is not None else '',getattr(c,'fingerprint',''),False,(reason,'NO_PERMISSION_GRANT','NO_ACTION_EXECUTION','DCSR_CACHE_IS_NOT_AUTHORITY'))

def _validate_request(q):
    if not q.request_id or not q.binding or not q.state_epoch: return 'EMPTY_REQUEST_CONTEXT'
    if not isinstance(q.contract,IntentContract): return 'INVALID_CONTRACT_TYPE'
    if not q.action or not q.target or not q.at_time: return 'EMPTY_ACTION_TARGET_OR_TIME'
    try: _parse_aware(q.at_time)
    except ValueError: return 'REQUEST_TIME_NOT_TIMEZONE_AWARE_OR_INVALID'
    return None

def evaluate(q:IntentCheckRequest)->IntentCheckResult:
    bad=_validate_request(q)
    if bad: return _invalid(q,bad)
    c=q.contract; action=_norm_action(q.action); target=_norm_target(q.target)
    fp_ok=_contract_fp_valid(c)
    if not fp_ok:
        return IntentCheckResult(Decision.DENY,NextAction.RETAIN_NO_ACTION_CANDIDATE,Escalation.CONTRACT_FINGERPRINT_MISMATCH,EngineState.CONTRACT_BLOCK_CANDIDATE,q.request_id,False,False,False,False,False,bool(c.consent_id),action,target,c.fingerprint,False,('CONTRACT_FINGERPRINT_MISMATCH','NO_PERMISSION_GRANT','NO_ACTION_EXECUTION'))
    now=_parse_aware(q.at_time); created=_parse_aware(c.created_time); expiry=_parse_aware(c.expiry_time)
    if now<created:
        return IntentCheckResult(Decision.HOLD,NextAction.RETAIN_NO_ACTION_CANDIDATE,Escalation.CONTRACT_NOT_YET_ACTIVE,EngineState.CONTRACT_BLOCK_CANDIDATE,q.request_id,True,action in c.allowed_actions,action in c.denied_actions,target in c.scope_targets,False,True,action,target,c.fingerprint,False,('CONTRACT_NOT_YET_ACTIVE','NO_PERMISSION_GRANT','NO_ACTION_EXECUTION'))
    if now>expiry:
        return IntentCheckResult(Decision.HOLD,NextAction.RETAIN_NO_ACTION_CANDIDATE,Escalation.CONTRACT_EXPIRED,EngineState.CONTRACT_BLOCK_CANDIDATE,q.request_id,True,action in c.allowed_actions,action in c.denied_actions,target in c.scope_targets,False,True,action,target,c.fingerprint,False,('CONTRACT_EXPIRED','CACHE_REUSE_FOR_EXPIRED_CONTRACT_FORBIDDEN','NO_PERMISSION_GRANT','NO_ACTION_EXECUTION'))
    if action in c.denied_actions:
        return IntentCheckResult(Decision.DENY,NextAction.RETAIN_NO_ACTION_CANDIDATE,Escalation.ACTION_EXPLICITLY_DENIED,EngineState.CONTRACT_BLOCK_CANDIDATE,q.request_id,True,False,True,target in c.scope_targets,True,True,action,target,c.fingerprint,False,('ACTION_EXPLICITLY_DENIED','DENIED_ACTION_OVERRIDES','NO_PERMISSION_GRANT','NO_ACTION_EXECUTION'))
    if target not in c.scope_targets:
        return IntentCheckResult(Decision.DENY,NextAction.RETAIN_NO_ACTION_CANDIDATE,Escalation.TARGET_OUT_OF_SCOPE,EngineState.CONTRACT_BLOCK_CANDIDATE,q.request_id,True,action in c.allowed_actions,False,False,True,True,action,target,c.fingerprint,False,('TARGET_OUT_OF_SCOPE','NO_PERMISSION_GRANT','NO_ACTION_EXECUTION'))
    if action not in c.allowed_actions:
        return IntentCheckResult(Decision.HOLD,NextAction.REVIEW_CONTRACT_CANDIDATE,Escalation.ACTION_NOT_ALLOWED,EngineState.CONTRACT_BLOCK_CANDIDATE,q.request_id,True,False,False,True,True,True,action,target,c.fingerprint,False,('ACTION_NOT_IN_ALLOWED_SET','UNKNOWN_ACTION_NOT_AUTO_ALLOWED','NO_PERMISSION_GRANT','NO_ACTION_EXECUTION'))
    return IntentCheckResult(Decision.ALLOW,NextAction.CONTINUE_POLICY_PERMIT_EVALUATION_CANDIDATE,Escalation.NONE,EngineState.INTENT_CONTRACT_MATCH_CANDIDATE,q.request_id,True,True,False,True,True,True,action,target,c.fingerprint,True,('CONTRACT_ACTION_TARGET_TIME_MATCH','ALLOW_IS_CONTRACT_MATCH_ONLY','NO_PERMISSION_GRANT','NO_ACTION_EXECUTION','DCSR_STATE_IS_NOT_AUTHORITATIVE_STATE'))

def _contract_state_fp(q): return _fp(q.contract)
def _query_fp(q): return _fp((q.request_id,_norm_action(q.action),_norm_target(q.target),q.at_time,q.binding,q.state_epoch))
def _integrity_fp(req,res,cf,qf,rf,binding,epoch): return _fp((req,res,cf,qf,rf,binding,epoch))

def prepare_state(q,binding,state_epoch):
    if binding!=q.binding or state_epoch!=q.state_epoch: raise ValueError('binding/state_epoch mismatch')
    r=evaluate(q); cf=_contract_state_fp(q); qf=_query_fp(q); rf=_fp(r)
    return PreparedIntentState(q,r,cf,qf,rf,_integrity_fp(q,r,cf,qf,rf,binding,state_epoch),binding,state_epoch)

def evaluate_prepared(st,*,integrity_validated,current_contract_fingerprint,current_query_fingerprint,current_result_fingerprint,current_time):
    # Expiry must be rechecked for every prepared/cached reuse. Cached equality cannot extend consent lifetime.
    valid=bool(integrity_validated and st.integrity_fingerprint==_integrity_fp(st.request,st.result,st.contract_fingerprint,st.query_fingerprint,st.result_fingerprint,st.binding,st.state_epoch) and current_contract_fingerprint==st.contract_fingerprint and current_query_fingerprint==st.query_fingerprint and current_result_fingerprint==st.result_fingerprint)
    if not valid: return _invalid(st.request,'PREPARED_STATE_INTEGRITY_OR_FINGERPRINT_MISMATCH')
    q=IntentCheckRequest(st.request.request_id,st.request.action,st.request.target,current_time,st.request.contract,st.request.binding,st.request.state_epoch)
    return evaluate(q)

def make_delta(a,b):
    return IntentChange(a.contract_fingerprint!=b.contract_fingerprint,a.query_fingerprint!=b.query_fingerprint,a.integrity_fingerprint,b.integrity_fingerprint)

def plan_missing_only(a,b):
    d=make_delta(a,b); ids=[]
    if d.contract_changed: ids.append('INTENT_CONTRACT')
    if d.query_changed: ids.append('AUTHORIZATION_QUERY')
    return MissingOnlyPlan(tuple(ids),len(_canon(tuple(ids)))+96,False)

def default_contract():
    return build_contract(
        user_goal='Analyze and prepare optimization candidates for the designated asset bundle without modifying originals.',
        allowed_actions=('read','analyze','prepare optimization candidate'),
        denied_actions=('delete','publish','execute external action'),
        scope_targets=('asset:bundle-A','asset:profile-A'),
        consent_id='CONSENT-174-A',
        created_time='2026-11-13T09:00:00+00:00',
        expiry_time='2026-11-13T12:00:00+00:00')

def default_request():
    return IntentCheckRequest('IC-174-A','analyze','asset:bundle-A','2026-11-13T10:00:00+00:00',default_contract(),'DEFAULT-BINDING','EPOCH-1')
def default_evaluation(): return evaluate(default_request())

if __name__=='__main__': print(json.dumps(_obj(default_evaluation()),ensure_ascii=False,sort_keys=True,indent=2))
