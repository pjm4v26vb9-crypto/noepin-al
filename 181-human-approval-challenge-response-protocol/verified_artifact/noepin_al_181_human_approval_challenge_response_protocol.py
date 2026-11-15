"""NOEPIN AL 181 — Human Approval Challenge-Response Protocol — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-181
DCSR: DIRECT INTEGRATION / 直接統合.

Pure, deterministic, side-effect-free protocol for binding a human approval response to
an exact Action digest, Risk digest, Scope summary, Nonce, Challenge fingerprint, and
expiry window. It verifies approval evidence; it does not grant Permission, issue a
Permit, invoke a Tool, execute an Action, establish Action Success, or substitute DCSR
for the human approver. Nonces and approval responses are never authorized for cache-hit
reuse. Prepared-state evaluation still rechecks the current Action/Risk digests, Nonce,
Challenge fingerprint, and expiry against current Authority-side inputs.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass, replace
from datetime import datetime, timezone, timedelta
from enum import Enum
from hashlib import sha256
import json, re

class Decision(str, Enum):
    ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class HumanDecision(str, Enum):
    APPROVE='APPROVE'; REJECT='REJECT'
class EngineState(str, Enum):
    HUMAN_APPROVAL_RESPONSE_VERIFIED_CANDIDATE='HUMAN_APPROVAL_RESPONSE_VERIFIED_CANDIDATE'
    HUMAN_REJECTION_VERIFIED_CANDIDATE='HUMAN_REJECTION_VERIFIED_CANDIDATE'
    RECHALLENGE_REQUIRED_CANDIDATE='RECHALLENGE_REQUIRED_CANDIDATE'
    INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_PERMIT_HANDSHAKE_CANDIDATE='CONTINUE_PERMIT_HANDSHAKE_CANDIDATE'
    RETAIN_HUMAN_REJECTION_CANDIDATE='RETAIN_HUMAN_REJECTION_CANDIDATE'
    ISSUE_NEW_CHALLENGE_CANDIDATE='ISSUE_NEW_CHALLENGE_CANDIDATE'
    RETAIN_NO_ACTION_CANDIDATE='RETAIN_NO_ACTION_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'; WRONG_NONCE='WRONG_NONCE'
    WRONG_CHALLENGE_FINGERPRINT='WRONG_CHALLENGE_FINGERPRINT'; EXPIRED='EXPIRED'
    NOT_YET_VALID='NOT_YET_VALID'; ACTION_DIGEST_MISMATCH='ACTION_DIGEST_MISMATCH'
    RISK_DIGEST_MISMATCH='RISK_DIGEST_MISMATCH'; UNKNOWN_DECISION='UNKNOWN_DECISION'
    PREPARED_STATE_STALE='PREPARED_STATE_STALE'

_HEX64=re.compile(r'^[0-9a-f]{64}$')
_WS=re.compile(r'\s+')

def _obj(v):
    if isinstance(v,Enum): return v.value
    if is_dataclass(v): return {f.name:_obj(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v,datetime): return v.astimezone(timezone.utc).isoformat()
    if isinstance(v,dict): return {str(k):_obj(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(tuple,list)): return [_obj(x) for x in v]
    return v

def _canon(v): return json.dumps(_obj(v),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def _fp(v): return sha256(_canon(v)).hexdigest()
def _norm(s): return _WS.sub(' ',str(s).strip())
def _digest(s):
    x=_norm(s).lower()
    if not _HEX64.fullmatch(x): raise ValueError('SHA-256 digest must be 64 lowercase hex chars')
    return x

def _aware(dt):
    if not isinstance(dt,datetime) or dt.tzinfo is None or dt.utcoffset() is None: raise ValueError('timezone-aware datetime required')
    return dt.astimezone(timezone.utc)

@dataclass(frozen=True)
class ApprovalChallenge:
    schema:str; request_id:str; action_digest:str; risk_digest:str; scope_summary:str
    nonce:str; issued_at:datetime; expires_at:datetime; challenge_fingerprint:str

@dataclass(frozen=True)
class HumanResponse:
    decision:str; challenge_fingerprint:str; nonce:str; responded_at:datetime; responder_ref:str

@dataclass(frozen=True)
class VerificationRequest:
    verification_id:str; challenge:ApprovalChallenge; response:HumanResponse
    current_action_digest:str; current_risk_digest:str; current_nonce:str
    current_time:datetime; binding:str; state_epoch:str

@dataclass(frozen=True)
class VerificationResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState
    verification_id:str; challenge_fingerprint_valid:bool; nonce_match:bool
    action_digest_match:bool; risk_digest_match:bool; within_validity_window:bool
    human_decision:HumanDecision|None; approval_response_verified:bool; rejection_response_verified:bool
    next_gate_candidate:bool; challenge_fingerprint:str; reasons:tuple[str,...]
    human_approval_evidence_verified:bool=False; human_rejection_evidence_verified:bool=False
    human_approval_executed:bool=False; approval_executed:bool=False; permission_granted:bool=False
    permit_issued:bool=False; tool_invoked:bool=False; action_executed:bool=False; action_success:bool=False
    stop_executed:bool=False; file_write_executed:bool=False; network_send_executed:bool=False
    external_write_performed:bool=False; authoritative_state_created:bool=False
    cached_nonce_reused:bool=False; cached_approval_response_reused:bool=False
    dcsr_substituted_human_approval:bool=False; dcsr_created_approval_response:bool=False
    dcsr_changed_action_digest:bool=False; dcsr_changed_risk_digest:bool=False
    cached_state_promoted:bool=False; reconstructed_state_promoted:bool=False; partial_state_promoted:bool=False
    sender_authority_inherited:bool=False; sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False
    authority_granted:bool=False; world_truth_proven:bool=False; domain_authority_promoted:bool=False; safety_proven:bool=False

@dataclass(frozen=True)
class PreparedVerificationState:
    request:VerificationRequest; result:VerificationResult; challenge_state_fingerprint:str
    response_fingerprint:str; query_fingerprint:str; result_fingerprint:str; integrity_fingerprint:str
    binding:str; state_epoch:str

@dataclass(frozen=True)
class ApprovalChange:
    response_record_added:bool; from_fingerprint:str; to_fingerprint:str

@dataclass(frozen=True)
class MissingOnlyPlan:
    missing_or_changed_record_ids:tuple[str,...]; metadata_bytes_required:int; full_resend_required:bool


def _challenge_payload(schema,request_id,action_digest,risk_digest,scope_summary,nonce,issued_at,expires_at):
    return {'schema':schema,'request_id':request_id,'action_digest':action_digest,'risk_digest':risk_digest,
            'scope_summary':scope_summary,'nonce':nonce,'issued_at':issued_at,'expires_at':expires_at}

def build_challenge(request_id,action_digest,risk_digest,scope_summary,nonce,issued_at,expires_at):
    rid=_norm(request_id); scope=_norm(scope_summary); n=_norm(nonce)
    if not rid: raise ValueError('Request ID required')
    if not scope: raise ValueError('Scope Summary required')
    if not n: raise ValueError('Nonce required')
    ad=_digest(action_digest); rd=_digest(risk_digest); ia=_aware(issued_at); ea=_aware(expires_at)
    if ea<=ia: raise ValueError('Expiry must be after issue time')
    schema='NOEPIN_AL_HUMAN_APPROVAL_CHALLENGE_V1'
    p=_challenge_payload(schema,rid,ad,rd,scope,n,ia,ea)
    return ApprovalChallenge(schema,rid,ad,rd,scope,n,ia,ea,_fp(p))

def challenge_valid(c):
    try:
        if c.schema!='NOEPIN_AL_HUMAN_APPROVAL_CHALLENGE_V1': return False
        if not _norm(c.request_id) or not _norm(c.scope_summary) or not _norm(c.nonce): return False
        ad=_digest(c.action_digest); rd=_digest(c.risk_digest); ia=_aware(c.issued_at); ea=_aware(c.expires_at)
        if ea<=ia: return False
        return c.challenge_fingerprint==_fp(_challenge_payload(c.schema,c.request_id,ad,rd,c.scope_summary,c.nonce,ia,ea))
    except Exception: return False

def build_response(decision,challenge_fingerprint,nonce,responded_at,responder_ref):
    d=_norm(decision).upper(); fp=_norm(challenge_fingerprint).lower(); n=_norm(nonce); rr=_norm(responder_ref); t=_aware(responded_at)
    if d not in {HumanDecision.APPROVE.value,HumanDecision.REJECT.value}: raise ValueError('Decision must be APPROVE or REJECT')
    if not _HEX64.fullmatch(fp): raise ValueError('Challenge fingerprint invalid')
    if not n: raise ValueError('Nonce required')
    if not rr: raise ValueError('Responder reference required')
    return HumanResponse(d,fp,n,t,rr)

def make_verification_request(challenge,response,current_action_digest,current_risk_digest,current_nonce,current_time,
                              verification_id='HACR-181-A',binding='DEFAULT-BINDING',state_epoch='EPOCH-1'):
    vid=_norm(verification_id); b=_norm(binding); e=_norm(state_epoch); n=_norm(current_nonce); t=_aware(current_time)
    if not vid or not b or not e or not n: raise ValueError('Verification ID/binding/state epoch/current nonce required')
    return VerificationRequest(vid,challenge,response,_digest(current_action_digest),_digest(current_risk_digest),n,t,b,e)

def _base(q,decision,next_action,escalation,engine_state,*,fp_valid=False,nonce=False,ad=False,rd=False,window=False,human=None,approve=False,reject=False,next_gate=False,reasons=()):
    return VerificationResult(decision,next_action,escalation,engine_state,q.verification_id,fp_valid,nonce,ad,rd,window,human,
                              approve,reject,next_gate,q.challenge.challenge_fingerprint,tuple(reasons),
                              human_approval_evidence_verified=approve,human_rejection_evidence_verified=reject)

def evaluate_response(q):
    c=q.challenge; r=q.response
    if not challenge_valid(c):
        return _base(q,Decision.DENY,NextAction.RETAIN_NO_ACTION_CANDIDATE,Escalation.INVALID_CONFIGURATION,EngineState.INVALID,reasons=('Challenge structure/fingerprint invalid',))
    fp_ok=(r.challenge_fingerprint==c.challenge_fingerprint)
    nonce_ok=(r.nonce==c.nonce==q.current_nonce)
    ad_ok=(q.current_action_digest==c.action_digest)
    rd_ok=(q.current_risk_digest==c.risk_digest)
    ct=_aware(q.current_time); rt=_aware(r.responded_at)
    if ct<c.issued_at or rt<c.issued_at:
        return _base(q,Decision.HOLD,NextAction.ISSUE_NEW_CHALLENGE_CANDIDATE,Escalation.NOT_YET_VALID,EngineState.RECHALLENGE_REQUIRED_CANDIDATE,fp_valid=fp_ok,nonce=nonce_ok,ad=ad_ok,rd=rd_ok,reasons=('Challenge/response time precedes issue time',))
    if ct>c.expires_at or rt>c.expires_at:
        return _base(q,Decision.HOLD,NextAction.ISSUE_NEW_CHALLENGE_CANDIDATE,Escalation.EXPIRED,EngineState.RECHALLENGE_REQUIRED_CANDIDATE,fp_valid=fp_ok,nonce=nonce_ok,ad=ad_ok,rd=rd_ok,reasons=('Challenge expired',))
    window=True
    if not ad_ok:
        return _base(q,Decision.HOLD,NextAction.ISSUE_NEW_CHALLENGE_CANDIDATE,Escalation.ACTION_DIGEST_MISMATCH,EngineState.RECHALLENGE_REQUIRED_CANDIDATE,fp_valid=fp_ok,nonce=nonce_ok,ad=False,rd=rd_ok,window=window,reasons=('Current Action digest differs from challenged Action',))
    if not rd_ok:
        return _base(q,Decision.HOLD,NextAction.ISSUE_NEW_CHALLENGE_CANDIDATE,Escalation.RISK_DIGEST_MISMATCH,EngineState.RECHALLENGE_REQUIRED_CANDIDATE,fp_valid=fp_ok,nonce=nonce_ok,ad=ad_ok,rd=False,window=window,reasons=('Current Risk digest differs from challenged Risk',))
    if not fp_ok:
        return _base(q,Decision.HOLD,NextAction.ISSUE_NEW_CHALLENGE_CANDIDATE,Escalation.WRONG_CHALLENGE_FINGERPRINT,EngineState.RECHALLENGE_REQUIRED_CANDIDATE,fp_valid=False,nonce=nonce_ok,ad=ad_ok,rd=rd_ok,window=window,reasons=('Response challenge fingerprint mismatch',))
    if not nonce_ok:
        return _base(q,Decision.HOLD,NextAction.ISSUE_NEW_CHALLENGE_CANDIDATE,Escalation.WRONG_NONCE,EngineState.RECHALLENGE_REQUIRED_CANDIDATE,fp_valid=True,nonce=False,ad=ad_ok,rd=rd_ok,window=window,reasons=('Response/current nonce mismatch',))
    try: hd=HumanDecision(r.decision)
    except Exception:
        return _base(q,Decision.DENY,NextAction.RETAIN_NO_ACTION_CANDIDATE,Escalation.UNKNOWN_DECISION,EngineState.INVALID,fp_valid=True,nonce=True,ad=True,rd=True,window=True,reasons=('Unknown human response decision',))
    if hd is HumanDecision.REJECT:
        return _base(q,Decision.DENY,NextAction.RETAIN_HUMAN_REJECTION_CANDIDATE,Escalation.NONE,EngineState.HUMAN_REJECTION_VERIFIED_CANDIDATE,fp_valid=True,nonce=True,ad=True,rd=True,window=True,human=hd,reject=True,reasons=('Human REJECT response is bound to the current challenge',))
    return _base(q,Decision.ALLOW,NextAction.CONTINUE_PERMIT_HANDSHAKE_CANDIDATE,Escalation.NONE,EngineState.HUMAN_APPROVAL_RESPONSE_VERIFIED_CANDIDATE,fp_valid=True,nonce=True,ad=True,rd=True,window=True,human=hd,approve=True,next_gate=True,reasons=('Human APPROVE response is bound to current Action/Risk/Scope/Nonce/Expiry challenge',))

def _query_payload(q):
    return {'verification_id':q.verification_id,'current_action_digest':q.current_action_digest,'current_risk_digest':q.current_risk_digest,
            'current_nonce':q.current_nonce,'current_time':q.current_time,'binding':q.binding,'state_epoch':q.state_epoch,
            'challenge_fingerprint':q.challenge.challenge_fingerprint,'response':q.response}

def prepare_state(q,binding,state_epoch):
    r=evaluate_response(q)
    cs=_fp(q.challenge); rf=_fp(q.response); qf=_fp(_query_payload(q)); rr=_fp(r)
    integ=_fp({'challenge_state_fingerprint':cs,'response_fingerprint':rf,'query_fingerprint':qf,'result_fingerprint':rr,'binding':binding,'state_epoch':state_epoch})
    return PreparedVerificationState(q,r,cs,rf,qf,rr,integ,_norm(binding),_norm(state_epoch))

def evaluate_prepared(st,*,integrity_validated,current_challenge_state_fingerprint,current_response_fingerprint,current_query_fingerprint,current_result_fingerprint,
                      current_action_digest,current_risk_digest,current_nonce,current_time):
    q=st.request
    checks=(integrity_validated, current_challenge_state_fingerprint==st.challenge_state_fingerprint,
            current_response_fingerprint==st.response_fingerprint, current_query_fingerprint==st.query_fingerprint,
            current_result_fingerprint==st.result_fingerprint, _digest(current_action_digest)==q.challenge.action_digest,
            _digest(current_risk_digest)==q.challenge.risk_digest, _norm(current_nonce)==q.challenge.nonce)
    if not all(checks):
        return _base(q,Decision.HOLD,NextAction.ISSUE_NEW_CHALLENGE_CANDIDATE,Escalation.PREPARED_STATE_STALE,EngineState.RECHALLENGE_REQUIRED_CANDIDATE,reasons=('Prepared state cannot reuse nonce/approval response; current Authority-side inputs must match and still be revalidated',))
    q2=replace(q,current_action_digest=_digest(current_action_digest),current_risk_digest=_digest(current_risk_digest),current_nonce=_norm(current_nonce),current_time=_aware(current_time))
    return evaluate_response(q2)

def make_delta(old_response,new_response):
    of=_fp(old_response) if old_response is not None else _fp({'response':None})
    nf=_fp(new_response) if new_response is not None else _fp({'response':None})
    return ApprovalChange(old_response!=new_response,of,nf)

def plan_missing_only(old_response,new_response):
    changed=old_response!=new_response
    ids=('APPROVAL_RESPONSE',) if changed else ()
    meta=len(_canon({'missing_or_changed_record_ids':ids,'full_resend_required':False}))
    return MissingOnlyPlan(ids,meta,False)

def default_times():
    ia=datetime(2026,11,14,0,0,0,tzinfo=timezone.utc); return ia,ia+timedelta(minutes=15),ia+timedelta(minutes=5)

def default_challenge():
    ia,ea,_=default_times()
    return build_challenge('REQ-181-A','a'*64,'b'*64,'Publish verified NOEPIN AL artifact metadata only','NONCE-181-A',ia,ea)

def default_response(decision='APPROVE'):
    c=default_challenge(); _,_,rt=default_times(); return build_response(decision,c.challenge_fingerprint,c.nonce,rt,'HUMAN-APPROVER-181-A')

def default_verification_request(decision='APPROVE'):
    c=default_challenge(); _,_,ct=default_times(); r=default_response(decision)
    return make_verification_request(c,r,c.action_digest,c.risk_digest,c.nonce,ct)

def default_evaluation(): return evaluate_response(default_verification_request())
