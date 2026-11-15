"""NOEPIN AL 179 — Decision-to-Execution Handshake Protocol — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-179
DCSR: DIRECT INTEGRATION / 直接統合.

Pure, deterministic, side-effect-free protocol state machine. It fixes the ordered
handshake from Request through Intent, Policy, Evidence/Risk, Decision, Permit,
Execution record, and Receipt verification. Artifact fingerprints are bindings,
not Truth, Permission, Approval execution, Permit issuance, Tool invocation,
Action execution, or Action Success. DCSR may reuse verified fingerprints and
request missing bindings, but partial reconstruction cannot advance a state.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
from hashlib import sha256
import json, re

class Decision(str, Enum):
    ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class HandshakeState(str, Enum):
    REQUESTED='REQUESTED'
    INTENT_BOUND='INTENT_BOUND'
    POLICY_BOUND='POLICY_BOUND'
    EVIDENCE_BOUND='EVIDENCE_BOUND'
    DECISION_BOUND='DECISION_BOUND'
    PERMIT_BOUND='PERMIT_BOUND'
    EXECUTION_RECORDED='EXECUTION_RECORDED'
    RECEIPT_VERIFIED='RECEIPT_VERIFIED'
    HOLD='HOLD'
    ABORTED='ABORTED'
class ArtifactKind(str, Enum):
    INTENT='INTENT'; POLICY='POLICY'; EVIDENCE='EVIDENCE'; RISK='RISK'
    DECISION='DECISION'; PERMIT='PERMIT'; EXECUTION='EXECUTION'; RECEIPT='RECEIPT'
class EngineState(str, Enum):
    HANDSHAKE_TRANSITION_READY_CANDIDATE='HANDSHAKE_TRANSITION_READY_CANDIDATE'
    HANDSHAKE_WAITING_FOR_ARTIFACT_CANDIDATE='HANDSHAKE_WAITING_FOR_ARTIFACT_CANDIDATE'
    HANDSHAKE_HOLD_LOCKED_CANDIDATE='HANDSHAKE_HOLD_LOCKED_CANDIDATE'
    HANDSHAKE_COMPLETED_CANDIDATE='HANDSHAKE_COMPLETED_CANDIDATE'
    HANDSHAKE_ABORTED_CANDIDATE='HANDSHAKE_ABORTED_CANDIDATE'
    INVALID='INVALID'
class NextAction(str, Enum):
    BIND_MISSING_ARTIFACT_CANDIDATE='BIND_MISSING_ARTIFACT_CANDIDATE'
    ADVANCE_HANDSHAKE_CANDIDATE='ADVANCE_HANDSHAKE_CANDIDATE'
    ENTER_HOLD_CANDIDATE='ENTER_HOLD_CANDIDATE'
    ABORT_HANDSHAKE_CANDIDATE='ABORT_HANDSHAKE_CANDIDATE'
    CONTINUE_POST_EXECUTION_AUDIT_CANDIDATE='CONTINUE_POST_EXECUTION_AUDIT_CANDIDATE'
    RETAIN_NO_ACTION_CANDIDATE='RETAIN_NO_ACTION_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'
    INVALID_STATE_TRANSITION='INVALID_STATE_TRANSITION'
    REQUIRED_ARTIFACT_MISSING='REQUIRED_ARTIFACT_MISSING'
    ARTIFACT_NOT_FINAL_VERIFIED='ARTIFACT_NOT_FINAL_VERIFIED'
    HOLD_LOCKED='HOLD_LOCKED'
    SESSION_FINGERPRINT_MISMATCH='SESSION_FINGERPRINT_MISMATCH'

_WS=re.compile(r'\s+')
_SHA=re.compile(r'^[0-9a-f]{64}$')

def _obj(v):
    if isinstance(v,Enum): return v.value
    if is_dataclass(v): return {f.name:_obj(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v,dict): return {str(k):_obj(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(tuple,list)): return [_obj(x) for x in v]
    return v

def _canon(v): return json.dumps(_obj(v),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def _fp(v): return sha256(_canon(v)).hexdigest()
def _norm(s): return _WS.sub(' ',str(s).strip())
def _sha(s):
    x=_norm(s).lower()
    if not _SHA.fullmatch(x): raise ValueError('SHA-256 digest must be lowercase 64-char hex')
    return x

@dataclass(frozen=True)
class ArtifactBinding:
    kind:ArtifactKind; fingerprint:str; final_verified:bool

@dataclass(frozen=True)
class TransitionRecord:
    sequence:int; from_state:HandshakeState; to_state:HandshakeState
    required_artifacts:tuple[ArtifactKind,...]; transition_fingerprint:str

@dataclass(frozen=True)
class HandshakeSession:
    schema:str; request_id:str; current_state:HandshakeState
    bound_artifacts:tuple[ArtifactBinding,...]; history:tuple[TransitionRecord,...]; session_fingerprint:str

@dataclass(frozen=True)
class TransitionRequest:
    verification_id:str; session:HandshakeSession; requested_state:HandshakeState
    binding:str; state_epoch:str

@dataclass(frozen=True)
class TransitionResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState
    verification_id:str; session_fingerprint_valid:bool; transition_allowed:bool
    required_artifacts_present:bool; required_artifacts_final_verified:bool; hold_locked:bool
    transitioned:bool; from_state:HandshakeState; requested_state:HandshakeState; resulting_state:HandshakeState
    missing_artifacts:tuple[str,...]; unverified_artifacts:tuple[str,...]
    bound_artifact_count:int; history_count:int; next_gate_candidate:bool; session_fingerprint:str; reasons:tuple[str,...]
    artifact_binding_promoted_to_truth:bool=False; artifact_final_verified_promoted_to_truth:bool=False
    decision_binding_promoted_to_decision_execution:bool=False; permit_binding_promoted_to_permit_issuance:bool=False
    execution_state_promoted_to_action_execution:bool=False; receipt_binding_promoted_to_action_success:bool=False
    permission_granted:bool=False; policy_decision_executed:bool=False; approval_executed:bool=False
    human_approval_executed:bool=False; permit_issued:bool=False; tool_invoked:bool=False
    action_executed:bool=False; action_success:bool=False; stop_executed:bool=False
    file_write_executed:bool=False; network_send_executed:bool=False; external_write_performed:bool=False
    authoritative_state_created:bool=False; cached_state_promoted:bool=False; reconstructed_state_promoted:bool=False
    partial_reconstruction_advanced:bool=False; dcsr_changed_transition_order:bool=False
    dcsr_created_artifact_binding:bool=False; dcsr_promoted_unverified_artifact:bool=False
    sender_authority_inherited:bool=False; sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False
    authority_granted:bool=False; world_truth_proven:bool=False; domain_authority_promoted:bool=False; safety_proven:bool=False

@dataclass(frozen=True)
class PreparedHandshakeState:
    request:TransitionRequest; result:TransitionResult; session_fingerprint:str
    query_fingerprint:str; result_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str

@dataclass(frozen=True)
class HandshakeChange:
    binding_records_added:tuple[str,...]; transition_records_added:tuple[str,...]
    from_fingerprint:str; to_fingerprint:str

@dataclass(frozen=True)
class MissingOnlyPlan:
    missing_or_changed_record_ids:tuple[str,...]; metadata_bytes_required:int; full_resend_required:bool

_ORDER=(HandshakeState.REQUESTED,HandshakeState.INTENT_BOUND,HandshakeState.POLICY_BOUND,
       HandshakeState.EVIDENCE_BOUND,HandshakeState.DECISION_BOUND,HandshakeState.PERMIT_BOUND,
       HandshakeState.EXECUTION_RECORDED,HandshakeState.RECEIPT_VERIFIED)
_NEXT={_ORDER[i]:_ORDER[i+1] for i in range(len(_ORDER)-1)}
_REQUIREMENTS={
    HandshakeState.INTENT_BOUND:(ArtifactKind.INTENT,),
    HandshakeState.POLICY_BOUND:(ArtifactKind.INTENT,ArtifactKind.POLICY),
    HandshakeState.EVIDENCE_BOUND:(ArtifactKind.INTENT,ArtifactKind.POLICY,ArtifactKind.EVIDENCE,ArtifactKind.RISK),
    HandshakeState.DECISION_BOUND:(ArtifactKind.DECISION,),
    HandshakeState.PERMIT_BOUND:(ArtifactKind.PERMIT,),
    HandshakeState.EXECUTION_RECORDED:(ArtifactKind.EXECUTION,),
    HandshakeState.RECEIPT_VERIFIED:(ArtifactKind.RECEIPT,),
}

def _session_payload(schema,request_id,state,bindings,history):
    return {'schema':schema,'request_id':request_id,'current_state':state,'bound_artifacts':bindings,'history':history}

def _with_fingerprint(schema,request_id,state,bindings,history):
    p=_session_payload(schema,request_id,state,bindings,history)
    return HandshakeSession(schema,request_id,state,bindings,history,_fp(p))

def build_session(request_id):
    rid=_norm(request_id)
    if not rid: raise ValueError('Request ID required')
    return _with_fingerprint('NOEPIN_AL_DECISION_EXECUTION_HANDSHAKE_V1',rid,HandshakeState.REQUESTED,(),())

def _session_valid(s):
    try:
        if s.schema!='NOEPIN_AL_DECISION_EXECUTION_HANDSHAKE_V1' or not _norm(s.request_id): return False
        seen=set()
        for b in s.bound_artifacts:
            if b.kind in seen or not _SHA.fullmatch(b.fingerprint): return False
            seen.add(b.kind)
        for i,h in enumerate(s.history,1):
            if h.sequence!=i or not _SHA.fullmatch(h.transition_fingerprint): return False
            expected=_fp({'sequence':h.sequence,'from_state':h.from_state,'to_state':h.to_state,'required_artifacts':h.required_artifacts})
            if expected!=h.transition_fingerprint: return False
        return _with_fingerprint(s.schema,s.request_id,s.current_state,s.bound_artifacts,s.history).session_fingerprint==s.session_fingerprint
    except Exception: return False

def _binding_map(s): return {b.kind:b for b in s.bound_artifacts}

def bind_artifact(session,kind,fingerprint,*,final_verified):
    if not _session_valid(session): raise ValueError('Invalid session')
    k=kind if isinstance(kind,ArtifactKind) else ArtifactKind(str(kind))
    fp=_sha(fingerprint); bm=_binding_map(session)
    if k in bm:
        old=bm[k]
        if old.fingerprint!=fp: raise ValueError('Conflicting fingerprint for existing Artifact binding')
        if old.final_verified and not final_verified: raise ValueError('Cannot downgrade Final Verified binding')
        if old.final_verified==bool(final_verified): return session
        repl=tuple(ArtifactBinding(x.kind,x.fingerprint,True if x.kind==k else x.final_verified) for x in session.bound_artifacts)
        return _with_fingerprint(session.schema,session.request_id,session.current_state,repl,session.history)
    bindings=tuple(sorted(session.bound_artifacts+(ArtifactBinding(k,fp,bool(final_verified)),),key=lambda x:x.kind.value))
    return _with_fingerprint(session.schema,session.request_id,session.current_state,bindings,session.history)

def _transition_record(seq,frm,to,required):
    p={'sequence':seq,'from_state':frm,'to_state':to,'required_artifacts':required}
    return TransitionRecord(seq,frm,to,required,_fp(p))

def _result(decision,next_action,escalation,engine,req,valid,allowed,present,verified,locked,transitioned,resulting,missing,unverified,reasons,next_gate=False):
    return TransitionResult(decision,next_action,escalation,engine,_norm(req.verification_id),valid,allowed,present,verified,locked,transitioned,
        req.session.current_state,req.requested_state,resulting,tuple(x.value if isinstance(x,ArtifactKind) else str(x) for x in missing),
        tuple(x.value if isinstance(x,ArtifactKind) else str(x) for x in unverified),len(req.session.bound_artifacts),len(req.session.history)+(1 if transitioned else 0),next_gate,req.session.session_fingerprint,tuple(reasons))

def evaluate_transition(req:TransitionRequest):
    s=req.session
    if not _norm(req.verification_id) or not _norm(req.binding) or not _norm(req.state_epoch):
        return _result(Decision.HOLD,NextAction.RETAIN_NO_ACTION_CANDIDATE,Escalation.INVALID_CONFIGURATION,EngineState.INVALID,req,False,False,False,False,False,False,s.current_state,(),(),('Missing verification metadata',))
    if not _session_valid(s):
        return _result(Decision.DENY,NextAction.RETAIN_NO_ACTION_CANDIDATE,Escalation.SESSION_FINGERPRINT_MISMATCH,EngineState.INVALID,req,False,False,False,False,False,False,s.current_state,(),(),('Session fingerprint or structure mismatch',))
    if s.current_state==HandshakeState.HOLD:
        if req.requested_state==HandshakeState.ABORTED:
            return _result(Decision.ALLOW,NextAction.ABORT_HANDSHAKE_CANDIDATE,Escalation.NONE,EngineState.HANDSHAKE_ABORTED_CANDIDATE,req,True,True,True,True,True,True,HandshakeState.ABORTED,(),(),('HOLD may transition only to ABORTED',),True)
        return _result(Decision.DENY,NextAction.ABORT_HANDSHAKE_CANDIDATE,Escalation.HOLD_LOCKED,EngineState.HANDSHAKE_HOLD_LOCKED_CANDIDATE,req,True,False,False,False,True,False,HandshakeState.HOLD,(),(),('HOLD is locked; automatic or unauthorized resume is forbidden',))
    if s.current_state in (HandshakeState.ABORTED,HandshakeState.RECEIPT_VERIFIED):
        return _result(Decision.DENY,NextAction.RETAIN_NO_ACTION_CANDIDATE,Escalation.INVALID_STATE_TRANSITION,EngineState.INVALID,req,True,False,False,False,False,False,s.current_state,(),(),('Terminal state cannot advance',))
    if req.requested_state==HandshakeState.HOLD:
        return _result(Decision.HOLD,NextAction.ENTER_HOLD_CANDIDATE,Escalation.NONE,EngineState.HANDSHAKE_HOLD_LOCKED_CANDIDATE,req,True,True,True,True,False,True,HandshakeState.HOLD,(),(),('Explicit HOLD candidate accepted; no execution is performed',),False)
    if req.requested_state==HandshakeState.ABORTED:
        return _result(Decision.ALLOW,NextAction.ABORT_HANDSHAKE_CANDIDATE,Escalation.NONE,EngineState.HANDSHAKE_ABORTED_CANDIDATE,req,True,True,True,True,False,True,HandshakeState.ABORTED,(),(),('Explicit ABORT candidate accepted; no external action is performed',),True)
    expected=_NEXT.get(s.current_state)
    if req.requested_state!=expected:
        return _result(Decision.DENY,NextAction.RETAIN_NO_ACTION_CANDIDATE,Escalation.INVALID_STATE_TRANSITION,EngineState.INVALID,req,True,False,False,False,False,False,s.current_state,(),(),('State skip or out-of-order transition rejected',))
    required=_REQUIREMENTS[req.requested_state]; bm=_binding_map(s)
    missing=tuple(k for k in required if k not in bm)
    if missing:
        return _result(Decision.HOLD,NextAction.BIND_MISSING_ARTIFACT_CANDIDATE,Escalation.REQUIRED_ARTIFACT_MISSING,EngineState.HANDSHAKE_WAITING_FOR_ARTIFACT_CANDIDATE,req,True,True,False,False,False,False,s.current_state,missing,(),('Required Artifact binding missing',))
    unverified=tuple(k for k in required if not bm[k].final_verified)
    if unverified:
        return _result(Decision.HOLD,NextAction.BIND_MISSING_ARTIFACT_CANDIDATE,Escalation.ARTIFACT_NOT_FINAL_VERIFIED,EngineState.HANDSHAKE_WAITING_FOR_ARTIFACT_CANDIDATE,req,True,True,True,False,False,False,s.current_state,(),unverified,('Required Artifact is not Final Verified',))
    engine=EngineState.HANDSHAKE_COMPLETED_CANDIDATE if req.requested_state==HandshakeState.RECEIPT_VERIFIED else EngineState.HANDSHAKE_TRANSITION_READY_CANDIDATE
    action=NextAction.CONTINUE_POST_EXECUTION_AUDIT_CANDIDATE if req.requested_state==HandshakeState.RECEIPT_VERIFIED else NextAction.ADVANCE_HANDSHAKE_CANDIDATE
    return _result(Decision.ALLOW,action,Escalation.NONE,engine,req,True,True,True,True,False,True,req.requested_state,(),(),('Required Artifact bindings are present and Final Verified; protocol transition candidate is valid',),True)

def apply_transition(req:TransitionRequest):
    r=evaluate_transition(req)
    if not r.transitioned: return req.session,r
    required=_REQUIREMENTS.get(r.resulting_state,())
    rec=_transition_record(len(req.session.history)+1,req.session.current_state,r.resulting_state,required)
    ns=_with_fingerprint(req.session.schema,req.session.request_id,r.resulting_state,req.session.bound_artifacts,req.session.history+(rec,))
    return ns,replace(r,session_fingerprint=ns.session_fingerprint)

def make_transition_request(session,target,verification_id='HS-179-A',binding='DEFAULT-BINDING',state_epoch='EPOCH-1'):
    t=target if isinstance(target,HandshakeState) else HandshakeState(str(target))
    return TransitionRequest(_norm(verification_id),session,t,_norm(binding),_norm(state_epoch))

def run_full_handshake(session=None):
    s=session or default_bound_session()
    results=[]
    for target in _ORDER[1:]:
        s,r=apply_transition(make_transition_request(s,target)); results.append(r)
        if not r.transitioned: break
    return s,tuple(results)

def _query_fp(req): return _fp({'verification_id':req.verification_id,'requested_state':req.requested_state,'binding':req.binding,'state_epoch':req.state_epoch})

def prepare_state(req,binding,state_epoch):
    if req.binding!=binding or req.state_epoch!=state_epoch: raise ValueError('binding/state epoch mismatch')
    r=evaluate_transition(req); sf=req.session.session_fingerprint; qf=_query_fp(req); rf=_fp(r)
    integ=_fp({'session':sf,'query':qf,'result':rf,'binding':binding,'state_epoch':state_epoch})
    return PreparedHandshakeState(req,r,sf,qf,rf,integ,binding,state_epoch)

def evaluate_prepared(st,*,integrity_validated,current_session_fingerprint,current_query_fingerprint,current_result_fingerprint):
    ok=(integrity_validated and current_session_fingerprint==st.session_fingerprint and current_query_fingerprint==st.query_fingerprint and current_result_fingerprint==st.result_fingerprint)
    if not ok:
        req=st.request
        return _result(Decision.HOLD,NextAction.RETAIN_NO_ACTION_CANDIDATE,Escalation.INVALID_CONFIGURATION,EngineState.INVALID,req,False,False,False,False,False,False,req.session.current_state,(),(),('Prepared state integrity/current fingerprints not validated',))
    return evaluate_transition(st.request)

def make_delta(old:HandshakeSession,new:HandshakeSession):
    ob=_binding_map(old); nb=_binding_map(new); added=[]
    for k in sorted(nb,key=lambda x:x.value):
        if k not in ob or ob[k]!=nb[k]: added.append(f'BINDING:{k.value}')
    trans=[]
    prefix=len(old.history)<=len(new.history) and old.history==new.history[:len(old.history)]
    if prefix:
        for h in new.history[len(old.history):]: trans.append(f'TRANSITION:{h.sequence}:{h.to_state.value}')
    elif old.history!=new.history: trans.append('TRANSITION_HISTORY_REACQUIRE')
    return HandshakeChange(tuple(added),tuple(trans),old.session_fingerprint,new.session_fingerprint)

def plan_missing_only(old:HandshakeSession,new:HandshakeSession):
    d=make_delta(old,new); records=d.binding_records_added+d.transition_records_added
    metadata=len(_canon({'records':records,'from':d.from_fingerprint,'to':d.to_fingerprint}))
    return MissingOnlyPlan(records,metadata,False)

def _seed(name): return sha256(name.encode()).hexdigest()
def default_bound_session():
    s=build_session('REQ-179-A')
    for k,name in ((ArtifactKind.INTENT,'INTENT-174-A'),(ArtifactKind.POLICY,'POLICY-179-A'),(ArtifactKind.EVIDENCE,'EVIDENCE-176-A'),(ArtifactKind.RISK,'RISK-178-A'),(ArtifactKind.DECISION,'DECISION-175-A'),(ArtifactKind.PERMIT,'PERMIT-179-A'),(ArtifactKind.EXECUTION,'EXECUTION-179-A'),(ArtifactKind.RECEIPT,'RECEIPT-177-A')):
        s=bind_artifact(s,k,_seed(name),final_verified=True)
    return s

def default_session_before_receipt():
    s=default_bound_session()
    for target in _ORDER[1:-1]: s,_=apply_transition(make_transition_request(s,target))
    return s

def default_request(): return make_transition_request(default_session_before_receipt(),HandshakeState.RECEIPT_VERIFIED)
def default_evaluation(): return evaluate_transition(default_request())
def default_completed_session(): return apply_transition(default_request())[0]

if __name__=='__main__': print(json.dumps(_obj(default_evaluation()),ensure_ascii=False,sort_keys=True,indent=2))
