"""NOEPIN AL 175 — Decision Envelope Artifact — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-175
DCSR: DIRECT INTEGRATION / 直接統合.

Deterministic, side-effect-free safety artifact for binding a Decision to Request ID,
Intent / Policy / Evidence / Risk SHA-256 fingerprints, reasons, and timezone-aware
issued/expiry times. The artifact transports and verifies a pre-existing decision; it
does not create policy truth, grant permission, execute approval, call tools, perform
external writes, or execute actions. DCSR may transport/cache a fingerprinted Envelope
but may not generate or alter ALLOW/DENY/HOLD/HUMAN_APPROVAL.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import json, math, re

class Decision(str, Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class BindingDecision(str, Enum): MATCH='MATCH'; HOLD='HOLD'; DENY='DENY'
class EngineState(str, Enum):
    DECISION_ENVELOPE_BOUND_CANDIDATE='DECISION_ENVELOPE_BOUND_CANDIDATE'
    BINDING_FAILURE_CANDIDATE='BINDING_FAILURE_CANDIDATE'
    INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_PERMIT_HANDSHAKE_CANDIDATE='CONTINUE_PERMIT_HANDSHAKE_CANDIDATE'
    REACQUIRE_DECISION_ENVELOPE_CANDIDATE='REACQUIRE_DECISION_ENVELOPE_CANDIDATE'
    RETAIN_NO_ACTION_CANDIDATE='RETAIN_NO_ACTION_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'
    INVALID_CONFIGURATION='INVALID_CONFIGURATION'
    ENVELOPE_FINGERPRINT_MISMATCH='ENVELOPE_FINGERPRINT_MISMATCH'
    ENVELOPE_EXPIRED='ENVELOPE_EXPIRED'
    ENVELOPE_NOT_YET_ACTIVE='ENVELOPE_NOT_YET_ACTIVE'
    REQUEST_BINDING_MISMATCH='REQUEST_BINDING_MISMATCH'
    INTENT_BINDING_MISMATCH='INTENT_BINDING_MISMATCH'
    POLICY_BINDING_MISMATCH='POLICY_BINDING_MISMATCH'
    EVIDENCE_BINDING_MISMATCH='EVIDENCE_BINDING_MISMATCH'
    RISK_BINDING_MISMATCH='RISK_BINDING_MISMATCH'

HEX64=re.compile(r'^[0-9a-f]{64}$')
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
def _norm(v:str)->str: return _WS.sub(' ',str(v).strip())
def _parse_aware(s:str)->datetime:
    try: d=datetime.fromisoformat(str(s))
    except Exception as e: raise ValueError('invalid ISO datetime') from e
    if d.tzinfo is None or d.utcoffset() is None: raise ValueError('timezone-aware datetime required')
    return d.astimezone(timezone.utc)
def _valid_hex64(v:str)->bool: return bool(HEX64.fullmatch(str(v)))

@dataclass(frozen=True)
class DecisionEnvelope:
    schema:str
    decision:Decision
    request_id:str
    reasons:tuple[str,...]
    intent_fingerprint:str
    policy_fingerprint:str
    evidence_fingerprint:str
    risk_fingerprint:str
    issued_time:str
    expiry_time:str
    fingerprint:str

@dataclass(frozen=True)
class BindingRequest:
    verification_id:str
    envelope:DecisionEnvelope
    current_request_id:str
    current_intent_fingerprint:str
    current_policy_fingerprint:str
    current_evidence_fingerprint:str
    current_risk_fingerprint:str
    at_time:str
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class BindingResult:
    binding_decision:BindingDecision
    next_action:NextAction
    escalation:Escalation
    engine_state:EngineState
    verification_id:str
    envelope_decision:Decision|None
    envelope_fingerprint_valid:bool
    request_match:bool
    intent_match:bool
    policy_match:bool
    evidence_match:bool
    risk_match:bool
    time_active:bool
    reasons_present:bool
    decision_valid:bool
    next_gate_candidate:bool
    envelope_fingerprint:str
    reasons:tuple[str,...]
    decision_generated_by_dcsr:bool=False
    decision_changed_by_dcsr:bool=False
    source_envelope_mutated:bool=False
    permission_granted:bool=False
    policy_decision_executed:bool=False
    approval_executed:bool=False
    human_approval_executed:bool=False
    permit_issued:bool=False
    tool_invoked:bool=False
    action_executed:bool=False
    action_success:bool=False
    stop_executed:bool=False
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
    authority_granted:bool=False
    world_truth_proven:bool=False
    domain_authority_promoted:bool=False
    safety_proven:bool=False

@dataclass(frozen=True)
class PreparedEnvelopeState:
    request:BindingRequest
    result:BindingResult
    envelope_fingerprint:str
    binding_query_fingerprint:str
    result_fingerprint:str
    integrity_fingerprint:str
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class EnvelopeChange:
    envelope_changed:bool
    binding_query_changed:bool
    from_fingerprint:str
    to_fingerprint:str

@dataclass(frozen=True)
class MissingOnlyPlan:
    missing_or_changed_record_ids:tuple[str,...]
    metadata_bytes_required:int
    full_resend_required:bool


def _payload(schema,decision,request_id,reasons,intent_fp,policy_fp,evidence_fp,risk_fp,issued,expiry):
    return {'schema':schema,'decision':decision,'request_id':request_id,'reasons':reasons,'intent_fingerprint':intent_fp,'policy_fingerprint':policy_fp,'evidence_fingerprint':evidence_fp,'risk_fingerprint':risk_fp,'issued_time':issued,'expiry_time':expiry}

def build_envelope(*,decision,request_id,reasons,intent_fingerprint,policy_fingerprint,evidence_fingerprint,risk_fingerprint,issued_time,expiry_time):
    try: dec=decision if isinstance(decision,Decision) else Decision(str(decision))
    except Exception as e: raise ValueError('unknown decision') from e
    rid=_norm(request_id)
    rs=tuple(_norm(x) for x in reasons if _norm(x))
    if not rid: raise ValueError('request_id required')
    if not rs: raise ValueError('at least one reason required')
    fps=(str(intent_fingerprint),str(policy_fingerprint),str(evidence_fingerprint),str(risk_fingerprint))
    if not all(_valid_hex64(x) for x in fps): raise ValueError('all fingerprints must be lowercase SHA-256 hex')
    issued=_parse_aware(issued_time); expiry=_parse_aware(expiry_time)
    if expiry<=issued: raise ValueError('expiry_time must be after issued_time')
    schema='NOEPIN_AL_DECISION_ENVELOPE_V1'; ii=issued.isoformat(); ee=expiry.isoformat()
    p=_payload(schema,dec.value,rid,rs,*fps,ii,ee)
    return DecisionEnvelope(schema,dec,rid,rs,*fps,ii,ee,_fp(p))

def _envelope_fp_valid(e:DecisionEnvelope)->bool:
    try:
        if not isinstance(e.decision,Decision): return False
        if not e.request_id or not e.reasons: return False
        if not all(_valid_hex64(x) for x in (e.intent_fingerprint,e.policy_fingerprint,e.evidence_fingerprint,e.risk_fingerprint)): return False
        issued=_parse_aware(e.issued_time); expiry=_parse_aware(e.expiry_time)
        if expiry<=issued: return False
        p=_payload(e.schema,e.decision.value,e.request_id,e.reasons,e.intent_fingerprint,e.policy_fingerprint,e.evidence_fingerprint,e.risk_fingerprint,e.issued_time,e.expiry_time)
        return e.fingerprint==_fp(p)
    except Exception: return False

def _invalid(q,reason,esc=Escalation.INVALID_CONFIGURATION):
    e=getattr(q,'envelope',None)
    return BindingResult(BindingDecision.HOLD,NextAction.REACQUIRE_DECISION_ENVELOPE_CANDIDATE,esc,EngineState.INVALID,getattr(q,'verification_id',''),getattr(e,'decision',None),False,False,False,False,False,False,False,bool(getattr(e,'reasons',())),isinstance(getattr(e,'decision',None),Decision),False,getattr(e,'fingerprint',''),(reason,'NO_PERMISSION_GRANT','NO_APPROVAL_EXECUTION','NO_ACTION_EXECUTION','DCSR_DECISION_MUTATION_FORBIDDEN'))

def _validate_request(q):
    if not isinstance(q,BindingRequest): return 'INVALID_REQUEST_TYPE'
    if not q.verification_id or not q.binding or not q.state_epoch: return 'EMPTY_VERIFICATION_CONTEXT'
    if not isinstance(q.envelope,DecisionEnvelope): return 'INVALID_ENVELOPE_TYPE'
    if not q.current_request_id or not q.at_time: return 'EMPTY_CURRENT_REQUEST_OR_TIME'
    if not all(_valid_hex64(x) for x in (q.current_intent_fingerprint,q.current_policy_fingerprint,q.current_evidence_fingerprint,q.current_risk_fingerprint)): return 'INVALID_CURRENT_FINGERPRINT'
    try: _parse_aware(q.at_time)
    except ValueError: return 'REQUEST_TIME_NOT_TIMEZONE_AWARE_OR_INVALID'
    return None

def evaluate(q:BindingRequest)->BindingResult:
    bad=_validate_request(q)
    if bad: return _invalid(q,bad)
    e=q.envelope; fp_ok=_envelope_fp_valid(e)
    dec_ok=isinstance(e.decision,Decision); reasons_ok=bool(e.reasons)
    if not fp_ok:
        return BindingResult(BindingDecision.DENY,NextAction.REACQUIRE_DECISION_ENVELOPE_CANDIDATE,Escalation.ENVELOPE_FINGERPRINT_MISMATCH,EngineState.BINDING_FAILURE_CANDIDATE,q.verification_id,e.decision,False,False,False,False,False,False,False,reasons_ok,dec_ok,False,e.fingerprint,('ENVELOPE_FINGERPRINT_OR_STRUCTURE_INVALID','NO_PERMISSION_GRANT','NO_ACTION_EXECUTION'))
    now=_parse_aware(q.at_time); issued=_parse_aware(e.issued_time); expiry=_parse_aware(e.expiry_time)
    req=q.current_request_id==e.request_id; im=q.current_intent_fingerprint==e.intent_fingerprint; pm=q.current_policy_fingerprint==e.policy_fingerprint; ev=q.current_evidence_fingerprint==e.evidence_fingerprint; rm=q.current_risk_fingerprint==e.risk_fingerprint
    if now<issued:
        return BindingResult(BindingDecision.HOLD,NextAction.REACQUIRE_DECISION_ENVELOPE_CANDIDATE,Escalation.ENVELOPE_NOT_YET_ACTIVE,EngineState.BINDING_FAILURE_CANDIDATE,q.verification_id,e.decision,True,req,im,pm,ev,rm,False,True,True,False,e.fingerprint,('ENVELOPE_NOT_YET_ACTIVE','NO_PERMISSION_GRANT','NO_ACTION_EXECUTION'))
    if now>expiry:
        return BindingResult(BindingDecision.HOLD,NextAction.REACQUIRE_DECISION_ENVELOPE_CANDIDATE,Escalation.ENVELOPE_EXPIRED,EngineState.BINDING_FAILURE_CANDIDATE,q.verification_id,e.decision,True,req,im,pm,ev,rm,False,True,True,False,e.fingerprint,('ENVELOPE_EXPIRED','EXPIRED_CACHE_REUSE_FORBIDDEN','NO_PERMISSION_GRANT','NO_ACTION_EXECUTION'))
    mismatches=[(req,Escalation.REQUEST_BINDING_MISMATCH,'REQUEST_BINDING_MISMATCH'),(im,Escalation.INTENT_BINDING_MISMATCH,'INTENT_BINDING_MISMATCH'),(pm,Escalation.POLICY_BINDING_MISMATCH,'POLICY_BINDING_MISMATCH'),(ev,Escalation.EVIDENCE_BINDING_MISMATCH,'EVIDENCE_BINDING_MISMATCH'),(rm,Escalation.RISK_BINDING_MISMATCH,'RISK_BINDING_MISMATCH')]
    for ok,esc,msg in mismatches:
        if not ok:
            return BindingResult(BindingDecision.HOLD,NextAction.REACQUIRE_DECISION_ENVELOPE_CANDIDATE,esc,EngineState.BINDING_FAILURE_CANDIDATE,q.verification_id,e.decision,True,req,im,pm,ev,rm,True,True,True,False,e.fingerprint,(msg,'BINDING_FAILURE_REQUIRES_REACQUIRE','NO_PERMISSION_GRANT','NO_ACTION_EXECUTION'))
    return BindingResult(BindingDecision.MATCH,NextAction.CONTINUE_PERMIT_HANDSHAKE_CANDIDATE,Escalation.NONE,EngineState.DECISION_ENVELOPE_BOUND_CANDIDATE,q.verification_id,e.decision,True,True,True,True,True,True,True,True,True,True,e.fingerprint,('DECISION_ENVELOPE_BINDING_MATCH','ENVELOPE_DECISION_IS_TRANSPORTED_NOT_EXECUTED','NO_PERMISSION_GRANT','NO_APPROVAL_EXECUTION','NO_ACTION_EXECUTION','DCSR_DECISION_MUTATION_FORBIDDEN'))

def _envelope_state_fp(q): return _fp(q.envelope)
def _binding_query_fp(q): return _fp((q.verification_id,q.current_request_id,q.current_intent_fingerprint,q.current_policy_fingerprint,q.current_evidence_fingerprint,q.current_risk_fingerprint,q.at_time,q.binding,q.state_epoch))
def _integrity_fp(req,res,ef,qf,rf,binding,epoch): return _fp((req,res,ef,qf,rf,binding,epoch))

def prepare_state(q,binding,state_epoch):
    if binding!=q.binding or state_epoch!=q.state_epoch: raise ValueError('binding/state_epoch mismatch')
    r=evaluate(q); ef=_envelope_state_fp(q); qf=_binding_query_fp(q); rf=_fp(r)
    return PreparedEnvelopeState(q,r,ef,qf,rf,_integrity_fp(q,r,ef,qf,rf,binding,state_epoch),binding,state_epoch)

def evaluate_prepared(st,*,integrity_validated,current_envelope_fingerprint,current_binding_query_fingerprint,current_result_fingerprint,current_time):
    valid=bool(integrity_validated and st.integrity_fingerprint==_integrity_fp(st.request,st.result,st.envelope_fingerprint,st.binding_query_fingerprint,st.result_fingerprint,st.binding,st.state_epoch) and current_envelope_fingerprint==st.envelope_fingerprint and current_binding_query_fingerprint==st.binding_query_fingerprint and current_result_fingerprint==st.result_fingerprint)
    if not valid: return _invalid(st.request,'PREPARED_STATE_INTEGRITY_OR_FINGERPRINT_MISMATCH')
    # Current time is always rechecked. Cached equality cannot extend Decision validity.
    q=BindingRequest(st.request.verification_id,st.request.envelope,st.request.current_request_id,st.request.current_intent_fingerprint,st.request.current_policy_fingerprint,st.request.current_evidence_fingerprint,st.request.current_risk_fingerprint,current_time,st.request.binding,st.request.state_epoch)
    return evaluate(q)

def make_delta(a,b):
    return EnvelopeChange(a.envelope_fingerprint!=b.envelope_fingerprint,a.binding_query_fingerprint!=b.binding_query_fingerprint,a.integrity_fingerprint,b.integrity_fingerprint)
def plan_missing_only(a,b):
    d=make_delta(a,b); ids=[]
    if d.envelope_changed: ids.append('DECISION_ENVELOPE')
    if d.binding_query_changed: ids.append('BINDING_QUERY')
    return MissingOnlyPlan(tuple(ids),len(_canon(tuple(ids)))+96,False)

def _seed_fp(label): return sha256(label.encode()).hexdigest()
def default_envelope():
    return build_envelope(decision=Decision.ALLOW,request_id='REQ-175-A',reasons=('Policy conditions satisfied for candidate handoff','Risk within evaluated threshold'),intent_fingerprint=_seed_fp('INTENT-175-A'),policy_fingerprint=_seed_fp('POLICY-175-A'),evidence_fingerprint=_seed_fp('EVIDENCE-175-A'),risk_fingerprint=_seed_fp('RISK-175-A'),issued_time='2026-11-13T10:00:00+00:00',expiry_time='2026-11-13T12:00:00+00:00')
def default_request():
    e=default_envelope()
    return BindingRequest('DE-175-A',e,e.request_id,e.intent_fingerprint,e.policy_fingerprint,e.evidence_fingerprint,e.risk_fingerprint,'2026-11-13T11:00:00+00:00','DEFAULT-BINDING','EPOCH-1')
def default_evaluation(): return evaluate(default_request())

if __name__=='__main__': print(json.dumps(_obj(default_evaluation()),ensure_ascii=False,sort_keys=True,indent=2))
