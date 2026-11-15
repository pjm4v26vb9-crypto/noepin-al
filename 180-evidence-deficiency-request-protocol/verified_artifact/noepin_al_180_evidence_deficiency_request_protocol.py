"""NOEPIN AL 180 — Evidence Deficiency Request Protocol — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-180
DCSR: DIRECT INTEGRATION / 直接統合.

Pure, deterministic, side-effect-free protocol for structured evidence reacquisition.
It binds a Parent Decision ID to explicit missing Claims and allowed Source Types,
accepts only requested responses, keeps unresolved Claims pending, and closes only
when every requested Claim has an accepted response. Accepted Evidence is not Truth;
an allowed Source Type is not trust/authority; a closed deficiency request does not
resume a Parent Decision, grant Permission, issue a Permit, execute Approval, call a
Tool, perform an external write, execute an Action, or establish Action Success.
DCSR may reuse accepted response state and request only missing/stale Claim addresses,
but it may not invent Evidence, widen allowed Sources, or close unresolved Claims.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, re

class Decision(str, Enum):
    ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class RequestStatus(str, Enum):
    OPEN='OPEN'; CLOSED='CLOSED'
class EngineState(str, Enum):
    DEFICIENCY_OPEN_CANDIDATE='DEFICIENCY_OPEN_CANDIDATE'
    RESPONSE_ACCEPTED_PENDING_CANDIDATE='RESPONSE_ACCEPTED_PENDING_CANDIDATE'
    EVIDENCE_DEFICIENCY_CLOSED_CANDIDATE='EVIDENCE_DEFICIENCY_CLOSED_CANDIDATE'
    INVALID='INVALID'
class NextAction(str, Enum):
    REQUEST_PENDING_EVIDENCE_CANDIDATE='REQUEST_PENDING_EVIDENCE_CANDIDATE'
    CLOSE_DEFICIENCY_REQUEST_CANDIDATE='CLOSE_DEFICIENCY_REQUEST_CANDIDATE'
    CONTINUE_PARENT_REVALIDATION_CANDIDATE='CONTINUE_PARENT_REVALIDATION_CANDIDATE'
    RETAIN_NO_ACTION_CANDIDATE='RETAIN_NO_ACTION_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'
    REQUEST_FINGERPRINT_MISMATCH='REQUEST_FINGERPRINT_MISMATCH'
    UNREQUESTED_CLAIM='UNREQUESTED_CLAIM'
    CLAIM_ALREADY_RESOLVED='CLAIM_ALREADY_RESOLVED'
    SOURCE_TYPE_NOT_ALLOWED='SOURCE_TYPE_NOT_ALLOWED'
    EVIDENCE_ID_MISSING='EVIDENCE_ID_MISSING'
    CLOSE_WITH_PENDING_CLAIMS='CLOSE_WITH_PENDING_CLAIMS'
    REQUEST_ALREADY_CLOSED='REQUEST_ALREADY_CLOSED'

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
def _claim(s):
    x=_norm(s)
    if not x: raise ValueError('Claim must not be empty')
    return x
def _source(s):
    x=_norm(s).upper().replace(' ','_')
    if not x: raise ValueError('Source Type must not be empty')
    return x

@dataclass(frozen=True)
class EvidenceResponse:
    claim:str; source_type:str; evidence_id:str

@dataclass(frozen=True)
class EvidenceDeficiencyRequest:
    schema:str; request_id:str; parent_decision_id:str
    missing_claims:tuple[str,...]; allowed_source_types:tuple[str,...]
    accepted_responses:tuple[EvidenceResponse,...]; status:RequestStatus
    request_fingerprint:str

@dataclass(frozen=True)
class ResponseRequest:
    verification_id:str; request:EvidenceDeficiencyRequest; response:EvidenceResponse
    request_close:bool; binding:str; state_epoch:str

@dataclass(frozen=True)
class ResponseResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState
    verification_id:str; request_fingerprint_valid:bool; response_accepted:bool; close_requested:bool
    closed:bool; status:RequestStatus; requested_claim:bool; source_allowed:bool; evidence_id_present:bool
    pending_claims:tuple[str,...]; pending_count:int; accepted_count:int; resulting_request_fingerprint:str
    next_gate_candidate:bool; reasons:tuple[str,...]
    evidence_promoted_to_truth:bool=False; accepted_response_promoted_to_truth:bool=False
    allowed_source_promoted_to_trust:bool=False; allowed_source_promoted_to_authority:bool=False
    evidence_id_promoted_to_provenance_validity:bool=False; closed_request_promoted_to_parent_decision_allow:bool=False
    closed_request_promoted_to_hold_release:bool=False; dcsr_invented_evidence:bool=False
    dcsr_widened_allowed_sources:bool=False; dcsr_closed_unresolved_claim:bool=False
    permission_granted:bool=False; policy_decision_executed:bool=False; approval_executed:bool=False
    human_approval_executed:bool=False; permit_issued:bool=False; tool_invoked:bool=False
    action_executed:bool=False; action_success:bool=False; stop_executed:bool=False
    file_write_executed:bool=False; network_send_executed:bool=False; external_write_performed:bool=False
    authoritative_state_created:bool=False; cached_state_promoted:bool=False; reconstructed_state_promoted:bool=False
    partial_state_promoted:bool=False; dcsr_reconstruction_created_fact:bool=False
    sender_authority_inherited:bool=False; sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False
    authority_granted:bool=False; world_truth_proven:bool=False; domain_authority_promoted:bool=False; safety_proven:bool=False

@dataclass(frozen=True)
class PreparedResponseState:
    request:ResponseRequest; result:ResponseResult; deficiency_fingerprint:str
    query_fingerprint:str; result_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str

@dataclass(frozen=True)
class DeficiencyChange:
    accepted_response_records_added:tuple[str,...]; close_state_changed:bool
    from_fingerprint:str; to_fingerprint:str

@dataclass(frozen=True)
class MissingOnlyPlan:
    missing_or_changed_record_ids:tuple[str,...]; metadata_bytes_required:int; full_resend_required:bool


def _response_norm(r:EvidenceResponse)->EvidenceResponse:
    return EvidenceResponse(_claim(r.claim),_source(r.source_type),_norm(r.evidence_id))

def _payload(schema,request_id,parent_decision_id,missing_claims,allowed_source_types,accepted_responses,status):
    return {'schema':schema,'request_id':request_id,'parent_decision_id':parent_decision_id,
            'missing_claims':missing_claims,'allowed_source_types':allowed_source_types,
            'accepted_responses':accepted_responses,'status':status}

def _with_fp(schema,request_id,parent_decision_id,missing_claims,allowed_source_types,accepted_responses,status):
    p=_payload(schema,request_id,parent_decision_id,missing_claims,allowed_source_types,accepted_responses,status)
    return EvidenceDeficiencyRequest(schema,request_id,parent_decision_id,missing_claims,allowed_source_types,accepted_responses,status,_fp(p))

def build_request(request_id,parent_decision_id,missing_claims,allowed_source_types):
    rid=_norm(request_id); pid=_norm(parent_decision_id)
    if not rid: raise ValueError('Request ID required')
    if not pid: raise ValueError('Parent Decision ID required')
    claims=tuple(_claim(x) for x in missing_claims)
    if not claims: raise ValueError('Missing Claims must not be empty')
    if len(set(claims))!=len(claims): raise ValueError('Missing Claims must be unique after normalization')
    sources=tuple(_source(x) for x in allowed_source_types)
    if not sources: raise ValueError('Allowed Source Types must not be empty')
    if len(set(sources))!=len(sources): raise ValueError('Allowed Source Types must be unique after normalization')
    return _with_fp('NOEPIN_AL_EVIDENCE_DEFICIENCY_REQUEST_V1',rid,pid,claims,sources,(),RequestStatus.OPEN)

def _request_valid(r):
    try:
        if r.schema!='NOEPIN_AL_EVIDENCE_DEFICIENCY_REQUEST_V1': return False
        if not _norm(r.request_id) or not _norm(r.parent_decision_id): return False
        claims=tuple(_claim(x) for x in r.missing_claims); sources=tuple(_source(x) for x in r.allowed_source_types)
        if not claims or len(set(claims))!=len(claims) or not sources or len(set(sources))!=len(sources): return False
        seen=set()
        for x in r.accepted_responses:
            y=_response_norm(x)
            if y.claim not in claims or y.claim in seen or y.source_type not in sources or not y.evidence_id: return False
            seen.add(y.claim)
        pending=tuple(x for x in claims if x not in seen)
        if r.status==RequestStatus.CLOSED and pending: return False
        expected=_fp(_payload(r.schema,r.request_id,r.parent_decision_id,r.missing_claims,r.allowed_source_types,r.accepted_responses,r.status))
        return expected==r.request_fingerprint
    except Exception: return False

def pending_claims(r):
    resolved={_claim(x.claim) for x in r.accepted_responses}
    return tuple(x for x in r.missing_claims if x not in resolved)

def _query_payload(q):
    return {'verification_id':_norm(q.verification_id),'response':_response_norm(q.response),'request_close':bool(q.request_close),'binding':_norm(q.binding),'state_epoch':_norm(q.state_epoch)}

def make_response_request(request,response,request_close=False,verification_id='EDR-180-A',binding='DEFAULT-BINDING',state_epoch='EPOCH-1'):
    if not _norm(verification_id): raise ValueError('Verification ID required')
    return ResponseRequest(_norm(verification_id),request,response,bool(request_close),_norm(binding),_norm(state_epoch))

def _result(q,decision,next_action,escalation,engine_state,*,fp_valid,response_accepted=False,closed=False,requested_claim=False,source_allowed=False,evidence_id_present=False,pending=(),accepted_count=0,resulting_fp='',next_gate=False,reasons=()):
    return ResponseResult(decision,next_action,escalation,engine_state,q.verification_id,fp_valid,response_accepted,q.request_close,
        closed,RequestStatus.CLOSED if closed else RequestStatus.OPEN,requested_claim,source_allowed,evidence_id_present,
        tuple(pending),len(tuple(pending)),accepted_count,resulting_fp,next_gate,tuple(reasons))

def evaluate_response(q:ResponseRequest):
    r=q.request; resp=_response_norm(q.response)
    if not _request_valid(r):
        return _result(q,Decision.DENY,NextAction.RETAIN_NO_ACTION_CANDIDATE,Escalation.REQUEST_FINGERPRINT_MISMATCH,EngineState.INVALID,fp_valid=False,pending=pending_claims(r) if r.missing_claims else (),accepted_count=len(r.accepted_responses),resulting_fp=r.request_fingerprint,reasons=('Deficiency Request fingerprint/structure mismatch',))
    pend=pending_claims(r)
    if r.status==RequestStatus.CLOSED:
        return _result(q,Decision.DENY,NextAction.RETAIN_NO_ACTION_CANDIDATE,Escalation.REQUEST_ALREADY_CLOSED,EngineState.INVALID,fp_valid=True,closed=True,pending=(),accepted_count=len(r.accepted_responses),resulting_fp=r.request_fingerprint,reasons=('Closed deficiency request cannot accept additional Evidence response',))
    requested=resp.claim in r.missing_claims
    if not requested:
        return _result(q,Decision.DENY,NextAction.RETAIN_NO_ACTION_CANDIDATE,Escalation.UNREQUESTED_CLAIM,EngineState.INVALID,fp_valid=True,requested_claim=False,source_allowed=resp.source_type in r.allowed_source_types,evidence_id_present=bool(resp.evidence_id),pending=pend,accepted_count=len(r.accepted_responses),resulting_fp=r.request_fingerprint,reasons=('Response Claim was not requested',))
    if resp.claim not in pend:
        return _result(q,Decision.DENY,NextAction.RETAIN_NO_ACTION_CANDIDATE,Escalation.CLAIM_ALREADY_RESOLVED,EngineState.INVALID,fp_valid=True,requested_claim=True,source_allowed=resp.source_type in r.allowed_source_types,evidence_id_present=bool(resp.evidence_id),pending=pend,accepted_count=len(r.accepted_responses),resulting_fp=r.request_fingerprint,reasons=('Claim already has an accepted Evidence response',))
    allowed=resp.source_type in r.allowed_source_types
    if not allowed:
        return _result(q,Decision.DENY,NextAction.RETAIN_NO_ACTION_CANDIDATE,Escalation.SOURCE_TYPE_NOT_ALLOWED,EngineState.INVALID,fp_valid=True,requested_claim=True,source_allowed=False,evidence_id_present=bool(resp.evidence_id),pending=pend,accepted_count=len(r.accepted_responses),resulting_fp=r.request_fingerprint,reasons=('Evidence Source Type is not allowed by this request',))
    present=bool(resp.evidence_id)
    if not present:
        return _result(q,Decision.DENY,NextAction.RETAIN_NO_ACTION_CANDIDATE,Escalation.EVIDENCE_ID_MISSING,EngineState.INVALID,fp_valid=True,requested_claim=True,source_allowed=True,evidence_id_present=False,pending=pend,accepted_count=len(r.accepted_responses),resulting_fp=r.request_fingerprint,reasons=('Evidence ID is required',))
    new_acc=r.accepted_responses+(resp,); new_pending=tuple(x for x in r.missing_claims if x not in {z.claim for z in new_acc})
    if q.request_close and new_pending:
        return _result(q,Decision.DENY,NextAction.REQUEST_PENDING_EVIDENCE_CANDIDATE,Escalation.CLOSE_WITH_PENDING_CLAIMS,EngineState.DEFICIENCY_OPEN_CANDIDATE,fp_valid=True,requested_claim=True,source_allowed=True,evidence_id_present=True,pending=pend,accepted_count=len(r.accepted_responses),resulting_fp=r.request_fingerprint,reasons=('Close rejected because requested Claims remain unresolved',))
    closed=bool(q.request_close and not new_pending); status=RequestStatus.CLOSED if closed else RequestStatus.OPEN
    nr=_with_fp(r.schema,r.request_id,r.parent_decision_id,r.missing_claims,r.allowed_source_types,new_acc,status)
    if closed:
        return _result(q,Decision.ALLOW,NextAction.CONTINUE_PARENT_REVALIDATION_CANDIDATE,Escalation.NONE,EngineState.EVIDENCE_DEFICIENCY_CLOSED_CANDIDATE,fp_valid=True,response_accepted=True,closed=True,requested_claim=True,source_allowed=True,evidence_id_present=True,pending=(),accepted_count=len(new_acc),resulting_fp=nr.request_fingerprint,next_gate=True,reasons=('Final requested Claim has an accepted response; deficiency request close candidate is structurally valid',))
    action=NextAction.CLOSE_DEFICIENCY_REQUEST_CANDIDATE if not new_pending else NextAction.REQUEST_PENDING_EVIDENCE_CANDIDATE
    state=EngineState.RESPONSE_ACCEPTED_PENDING_CANDIDATE if new_pending else EngineState.DEFICIENCY_OPEN_CANDIDATE
    return _result(q,Decision.ALLOW,action,Escalation.NONE,state,fp_valid=True,response_accepted=True,closed=False,requested_claim=True,source_allowed=True,evidence_id_present=True,pending=new_pending,accepted_count=len(new_acc),resulting_fp=nr.request_fingerprint,next_gate=False,reasons=('Requested Evidence response accepted; unresolved Claims remain' if new_pending else 'All requested Claims resolved; explicit close is now eligible',))

def apply_response(q):
    res=evaluate_response(q)
    if not res.response_accepted: return q.request,res
    resp=_response_norm(q.response); r=q.request
    status=RequestStatus.CLOSED if res.closed else RequestStatus.OPEN
    nr=_with_fp(r.schema,r.request_id,r.parent_decision_id,r.missing_claims,r.allowed_source_types,r.accepted_responses+(resp,),status)
    return nr,res

def close_request(r):
    if not _request_valid(r): raise ValueError('Invalid deficiency request')
    if r.status==RequestStatus.CLOSED: return r
    if pending_claims(r): raise ValueError('Cannot close while requested Claims remain unresolved')
    return _with_fp(r.schema,r.request_id,r.parent_decision_id,r.missing_claims,r.allowed_source_types,r.accepted_responses,RequestStatus.CLOSED)

def _invalid_prepared(q,reason='Prepared state integrity/current fingerprint mismatch'):
    r=q.request
    return _result(q,Decision.DENY,NextAction.RETAIN_NO_ACTION_CANDIDATE,Escalation.INVALID_CONFIGURATION,EngineState.INVALID,fp_valid=_request_valid(r),pending=pending_claims(r),accepted_count=len(r.accepted_responses),resulting_fp=r.request_fingerprint,reasons=(reason,))

def prepare_state(q,binding,state_epoch):
    res=evaluate_response(q); qfp=_fp(_query_payload(q)); rfp=_fp(res)
    integrity=_fp({'request_fingerprint':q.request.request_fingerprint,'query_fingerprint':qfp,'result_fingerprint':rfp,'binding':_norm(binding),'state_epoch':_norm(state_epoch)})
    return PreparedResponseState(q,res,q.request.request_fingerprint,qfp,rfp,integrity,_norm(binding),_norm(state_epoch))

def evaluate_prepared(st,*,integrity_validated,current_deficiency_fingerprint,current_query_fingerprint,current_result_fingerprint):
    expected=_fp({'request_fingerprint':st.deficiency_fingerprint,'query_fingerprint':st.query_fingerprint,'result_fingerprint':st.result_fingerprint,'binding':st.binding,'state_epoch':st.state_epoch})
    if not integrity_validated or expected!=st.integrity_fingerprint: return _invalid_prepared(st.request)
    if current_deficiency_fingerprint!=st.deficiency_fingerprint or current_query_fingerprint!=st.query_fingerprint or current_result_fingerprint!=st.result_fingerprint: return _invalid_prepared(st.request)
    # Re-evaluate deterministically; cached result alone never changes protocol authority.
    return evaluate_response(st.request)

def make_delta(old,new):
    oldmap={x.claim:_fp(x) for x in old.accepted_responses}; newmap={x.claim:_fp(x) for x in new.accepted_responses}
    added=tuple(f'CLAIM:{c}' for c in new.missing_claims if oldmap.get(c)!=newmap.get(c) and c in newmap)
    return DeficiencyChange(added,old.status!=new.status,old.request_fingerprint,new.request_fingerprint)

def plan_missing_only(old,new):
    static_same=(old.schema==new.schema and old.request_id==new.request_id and old.parent_decision_id==new.parent_decision_id and old.missing_claims==new.missing_claims and old.allowed_source_types==new.allowed_source_types)
    if not static_same:
        ids=('FULL_REQUEST_METADATA',); return MissingOnlyPlan(ids,len(_canon(ids)),True)
    oldmap={x.claim:_fp(x) for x in old.accepted_responses}; newmap={x.claim:_fp(x) for x in new.accepted_responses}
    ids=[f'CLAIM:{c}' for c in new.missing_claims if oldmap.get(c)!=newmap.get(c) and c in newmap]
    if old.status!=new.status: ids.append('REQUEST_STATUS')
    t=tuple(ids); return MissingOnlyPlan(t,len(_canon(t)),False)

def _seed(s): return sha256(str(s).encode()).hexdigest()

def default_open_request():
    r=build_request('EDR-180-A','DEC-175-A',('identity binding current','resource state current','authorization scope current'),('SIGNED_RECORD','SYSTEM_RECORD','HUMAN_PROVIDED_RECORD'))
    for resp in (EvidenceResponse('identity binding current','SIGNED_RECORD','EVID-180-001'),EvidenceResponse('resource state current','SYSTEM_RECORD','EVID-180-002')):
        r,res=apply_response(make_response_request(r,resp,False))
        if not res.response_accepted: raise RuntimeError('default setup failed')
    return r

def default_response_request():
    return make_response_request(default_open_request(),EvidenceResponse('authorization scope current','HUMAN_PROVIDED_RECORD','EVID-180-003'),True,'EDR-180-A','DEFAULT-BINDING','EPOCH-1')

def default_evaluation(): return evaluate_response(default_response_request())
def default_closed_request():
    r,res=apply_response(default_response_request())
    if not res.closed: raise RuntimeError('default close failed')
    return r
