"""NOEPIN AL 182 — Failure-State Propagation Protocol — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-182
DCSR: DIRECT INTEGRATION / 直接統合.

Pure, deterministic, side-effect-free protocol for monotonically propagating failure
states across layers. Severity is fixed as OK < HOLD < HUMAN_APPROVAL < DENY < ABORT.
A lower-severity incoming state never weakens the current state. An explicit proposed
severity downgrade requires current Recovery Authorization evidence; that evidence is
validated only as an input to this protocol and is not promoted to Truth, Permission,
Permit issuance, Tool invocation, Action execution, Action success, or Recovery
execution. DCSR may transport state records but cannot downgrade severity, invent or
substitute Recovery Authorization, or promote cached/reconstructed state to current
authoritative state.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
from hashlib import sha256
import json, re

class Decision(str, Enum):
    ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class FailureState(str, Enum):
    OK='OK'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'; DENY='DENY'; ABORT='ABORT'
class EngineState(str, Enum):
    FAILURE_STATE_PROPAGATED_CANDIDATE='FAILURE_STATE_PROPAGATED_CANDIDATE'
    FAILURE_STATE_RETAINED_CANDIDATE='FAILURE_STATE_RETAINED_CANDIDATE'
    RECOVERY_DOWNGRADE_ACCEPTED_CANDIDATE='RECOVERY_DOWNGRADE_ACCEPTED_CANDIDATE'
    RECOVERY_AUTHORIZATION_REQUIRED_CANDIDATE='RECOVERY_AUTHORIZATION_REQUIRED_CANDIDATE'
    INVALID='INVALID'
class NextAction(str, Enum):
    PROPAGATE_FAILURE_STATE_CANDIDATE='PROPAGATE_FAILURE_STATE_CANDIDATE'
    RETAIN_HIGHER_FAILURE_STATE_CANDIDATE='RETAIN_HIGHER_FAILURE_STATE_CANDIDATE'
    CONTINUE_RECOVERY_REVALIDATION_CANDIDATE='CONTINUE_RECOVERY_REVALIDATION_CANDIDATE'
    REQUEST_RECOVERY_AUTHORIZATION_CANDIDATE='REQUEST_RECOVERY_AUTHORIZATION_CANDIDATE'
    RETAIN_NO_ACTION_CANDIDATE='RETAIN_NO_ACTION_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; INVALID_STATE='INVALID_STATE'; DOWNGRADE_WITHOUT_RECOVERY_AUTHORIZATION='DOWNGRADE_WITHOUT_RECOVERY_AUTHORIZATION'
    RECOVERY_BINDING_MISMATCH='RECOVERY_BINDING_MISMATCH'; PREPARED_STATE_STALE='PREPARED_STATE_STALE'

SEVERITY={FailureState.OK:0, FailureState.HOLD:1, FailureState.HUMAN_APPROVAL:2, FailureState.DENY:3, FailureState.ABORT:4}
_WS=re.compile(r'\s+')

def _obj(v):
    if isinstance(v,Enum): return v.value
    if is_dataclass(v): return {f.name:_obj(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v,dict): return {str(k):_obj(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(tuple,list)): return [_obj(x) for x in v]
    return v

def _canon(v): return json.dumps(_obj(v),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def _fp(v): return sha256(_canon(v)).hexdigest()
def _norm(s): return _WS.sub(' ',str(s).strip())

def _state(v):
    if isinstance(v,FailureState): return v
    try: return FailureState(_norm(v).upper())
    except Exception as e: raise ValueError('unknown Failure State') from e

@dataclass(frozen=True)
class RecoveryAuthorization:
    authorization_id:str; from_state:FailureState; to_state:FailureState; binding:str; state_epoch:str; final_verified:bool

@dataclass(frozen=True)
class PropagationRequest:
    propagation_id:str; current_state:FailureState; incoming_state:FailureState; proposed_state:FailureState|None
    recovery_authorization:RecoveryAuthorization|None; binding:str; state_epoch:str

@dataclass(frozen=True)
class PropagationResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState
    propagation_id:str; current_state:FailureState; incoming_state:FailureState; proposed_state:FailureState|None
    effective_state:FailureState; severity_before:int; severity_incoming:int; severity_effective:int
    escalated:bool; lower_incoming_ignored:bool; downgrade_requested:bool; recovery_authorization_valid:bool
    downgrade_accepted:bool; next_gate_candidate:bool; propagation_fingerprint:str; reasons:tuple[str,...]
    recovery_authorization_promoted_to_truth:bool=False; recovery_authorization_promoted_to_permission:bool=False
    recovery_executed:bool=False; state_downgrade_executed:bool=False; permission_granted:bool=False
    permit_issued:bool=False; approval_executed:bool=False; human_approval_executed:bool=False
    tool_invoked:bool=False; action_executed:bool=False; action_success:bool=False; stop_executed:bool=False
    file_write_executed:bool=False; network_send_executed:bool=False; external_write_performed:bool=False
    authoritative_state_created:bool=False; cached_state_promoted:bool=False; reconstructed_state_promoted:bool=False
    partial_state_promoted:bool=False; dcsr_downgraded_failure_state:bool=False
    dcsr_invented_recovery_authorization:bool=False; dcsr_substituted_recovery_authorization:bool=False
    dcsr_reconstruction_created_fact:bool=False; sender_authority_inherited:bool=False
    sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False; authority_granted:bool=False
    world_truth_proven:bool=False; domain_authority_promoted:bool=False; safety_proven:bool=False

@dataclass(frozen=True)
class PreparedPropagationState:
    request:PropagationRequest; result:PropagationResult; request_fingerprint:str; result_fingerprint:str
    integrity_fingerprint:str; binding:str; state_epoch:str

@dataclass(frozen=True)
class StateChangeSegment:
    record_id:str; from_state:FailureState; to_state:FailureState; state_fingerprint:str

@dataclass(frozen=True)
class MissingOnlyPlan:
    missing_or_changed_record_ids:tuple[str,...]; metadata_bytes_required:int; full_resend_required:bool


def build_recovery_authorization(authorization_id,from_state,to_state,binding,state_epoch,final_verified=True):
    aid=_norm(authorization_id); b=_norm(binding); e=_norm(state_epoch); f=_state(from_state); t=_state(to_state)
    if not aid or not b or not e: raise ValueError('Recovery Authorization ID/binding/state epoch required')
    if SEVERITY[t] >= SEVERITY[f]: raise ValueError('Recovery Authorization must bind a strict severity downgrade')
    return RecoveryAuthorization(aid,f,t,b,e,bool(final_verified))

def make_request(current_state,incoming_state,proposed_state=None,recovery_authorization=None,
                 propagation_id='FSP-182-A',binding='DEFAULT-BINDING',state_epoch='EPOCH-1'):
    pid=_norm(propagation_id); b=_norm(binding); e=_norm(state_epoch)
    if not pid or not b or not e: raise ValueError('Propagation ID/binding/state epoch required')
    c=_state(current_state); i=_state(incoming_state); p=None if proposed_state is None else _state(proposed_state)
    if recovery_authorization is not None and not isinstance(recovery_authorization,RecoveryAuthorization):
        raise ValueError('invalid Recovery Authorization')
    return PropagationRequest(pid,c,i,p,recovery_authorization,b,e)

def _recovery_valid(q,base_state):
    a=q.recovery_authorization
    return bool(a and a.final_verified and a.from_state==base_state and a.to_state==q.proposed_state and a.binding==q.binding and a.state_epoch==q.state_epoch)

def evaluate(q:PropagationRequest):
    try:
        c=_state(q.current_state); i=_state(q.incoming_state); p=None if q.proposed_state is None else _state(q.proposed_state)
    except Exception:
        # Construction normally prevents this, but fail closed for forged instances.
        return _invalid_result(q)
    base=i if SEVERITY[i] > SEVERITY[c] else c
    escalated=SEVERITY[i] > SEVERITY[c]
    lower=SEVERITY[i] < SEVERITY[c]
    downgrade=bool(p is not None and SEVERITY[p] < SEVERITY[base])
    if p is not None and SEVERITY[p] > SEVERITY[base]:
        # Proposed higher failure state is a monotonic escalation and needs no Recovery Authorization.
        base=p; escalated=True; lower=False; downgrade=False
    if downgrade:
        valid=_recovery_valid(q,base)
        if not valid:
            reasons=('severity downgrade requires current Recovery Authorization',)
            return _result(q,Decision.DENY,NextAction.REQUEST_RECOVERY_AUTHORIZATION_CANDIDATE,
                           Escalation.DOWNGRADE_WITHOUT_RECOVERY_AUTHORIZATION,EngineState.RECOVERY_AUTHORIZATION_REQUIRED_CANDIDATE,
                           base,escalated,lower,True,False,False,False,reasons)
        reasons=('explicit Recovery Authorization verified for proposed downgrade candidate',)
        return _result(q,Decision.ALLOW,NextAction.CONTINUE_RECOVERY_REVALIDATION_CANDIDATE,
                       Escalation.NONE,EngineState.RECOVERY_DOWNGRADE_ACCEPTED_CANDIDATE,
                       p,escalated,lower,True,True,True,True,reasons)
    if p is not None and SEVERITY[p] < SEVERITY[c] and SEVERITY[base] >= SEVERITY[c]:
        # Defensive path; strict downgrade is handled above.
        return _result(q,Decision.DENY,NextAction.REQUEST_RECOVERY_AUTHORIZATION_CANDIDATE,
                       Escalation.DOWNGRADE_WITHOUT_RECOVERY_AUTHORIZATION,EngineState.RECOVERY_AUTHORIZATION_REQUIRED_CANDIDATE,
                       base,escalated,lower,True,False,False,False,('downgrade rejected',))
    if escalated:
        return _result(q,Decision.ALLOW,NextAction.PROPAGATE_FAILURE_STATE_CANDIDATE,Escalation.NONE,
                       EngineState.FAILURE_STATE_PROPAGATED_CANDIDATE,base,True,lower,False,False,False,True,
                       ('higher severity propagated',))
    return _result(q,Decision.ALLOW,NextAction.RETAIN_HIGHER_FAILURE_STATE_CANDIDATE,Escalation.NONE,
                   EngineState.FAILURE_STATE_RETAINED_CANDIDATE,base,False,lower,False,False,False,True,
                   (('lower incoming ignored',) if lower else ('equal severity retained',)))

def _result(q,decision,next_action,escalation,engine,effective,escalated,lower,downgrade,auth_valid,downgrade_accepted,next_gate,reasons):
    c=_state(q.current_state); i=_state(q.incoming_state); p=None if q.proposed_state is None else _state(q.proposed_state)
    fp=_fp({'propagation_id':q.propagation_id,'current_state':c,'incoming_state':i,'proposed_state':p,
            'effective_state':effective,'binding':q.binding,'state_epoch':q.state_epoch,
            'recovery_authorization_id':None if q.recovery_authorization is None else q.recovery_authorization.authorization_id})
    return PropagationResult(decision,next_action,escalation,engine,q.propagation_id,c,i,p,effective,
                             SEVERITY[c],SEVERITY[i],SEVERITY[effective],escalated,lower,downgrade,
                             auth_valid,downgrade_accepted,next_gate,fp,tuple(reasons))

def _invalid_result(q):
    # Forge-safe fallback values do not authorize anything.
    try: c=_state(q.current_state)
    except Exception: c=FailureState.ABORT
    try: i=_state(q.incoming_state)
    except Exception: i=FailureState.ABORT
    return PropagationResult(Decision.DENY,NextAction.RETAIN_NO_ACTION_CANDIDATE,Escalation.INVALID_STATE,EngineState.INVALID,
        getattr(q,'propagation_id','INVALID'),c,i,None,c,SEVERITY[c],SEVERITY[i],SEVERITY[c],False,False,False,False,False,False,
        _fp({'invalid':True}),('unknown/invalid state rejected',))

def prepare_state(q,binding,state_epoch):
    if _norm(binding)!=q.binding or _norm(state_epoch)!=q.state_epoch: raise ValueError('binding/state epoch mismatch')
    r=evaluate(q); rf=_fp(q); sf=_fp(r); integrity=_fp({'request':rf,'result':sf,'binding':q.binding,'state_epoch':q.state_epoch})
    return PreparedPropagationState(q,r,rf,sf,integrity,q.binding,q.state_epoch)

def evaluate_prepared(st:PreparedPropagationState,*,integrity_validated,current_request_fingerprint,current_result_fingerprint,
                      current_binding,current_state_epoch,current_current_state,current_incoming_state,current_proposed_state,
                      current_recovery_authorization):
    expected=_fp({'request':st.request_fingerprint,'result':st.result_fingerprint,'binding':st.binding,'state_epoch':st.state_epoch})
    if (not integrity_validated or st.integrity_fingerprint!=expected or current_request_fingerprint!=st.request_fingerprint or
        current_result_fingerprint!=st.result_fingerprint or _norm(current_binding)!=st.binding or _norm(current_state_epoch)!=st.state_epoch):
        q=make_request(current_current_state,current_incoming_state,current_proposed_state,current_recovery_authorization,
                       st.request.propagation_id,_norm(current_binding),_norm(current_state_epoch))
        base=evaluate(q)
        return replace(base,decision=Decision.HOLD,next_action=NextAction.RETAIN_NO_ACTION_CANDIDATE,
                       escalation=Escalation.PREPARED_STATE_STALE,engine_state=EngineState.INVALID,next_gate_candidate=False,
                       reasons=('prepared state integrity/current fingerprint mismatch',))
    # Current Authority-side state and Recovery Authorization are always reconstructed and re-evaluated; no cache authority reuse.
    q=make_request(current_current_state,current_incoming_state,current_proposed_state,current_recovery_authorization,
                   st.request.propagation_id,st.binding,st.state_epoch)
    return evaluate(q)

def make_delta(from_state,to_state):
    f=_state(from_state); t=_state(to_state)
    return StateChangeSegment('FAILURE_STATE',f,t,_fp({'from':f,'to':t}))

def plan_missing_only(from_state,to_state):
    f=_state(from_state); t=_state(to_state)
    ids=() if f==t else ('FAILURE_STATE',)
    return MissingOnlyPlan(ids,0 if not ids else len(_canon({'record_id':'FAILURE_STATE','from':f,'to':t})),False)

def default_request(): return make_request(FailureState.HOLD,FailureState.DENY)
def default_evaluation(): return evaluate(default_request())
