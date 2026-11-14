"""NOEPIN AL 177 — Execution Receipt Artifact — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-177
DCSR: DIRECT INTEGRATION / 直接統合.

Deterministic, side-effect-free safety artifact for validating an execution receipt
issued by an execution authority after an action attempt. It binds Request / Permit /
Action / Target / time / status / changes / postconditions / rollback reference /
Intent+Policy fingerprints / Result Digest. This module does not execute the action,
issue the permit, create a success receipt from partial state, or promote a receipt
status to independently verified World Truth / Permission / Action Success.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import json, math, re

class ReceiptStatus(str, Enum):
    SUCCEEDED='SUCCEEDED'; FAILED='FAILED'; PARTIAL='PARTIAL'; ROLLED_BACK='ROLLED_BACK'
class BindingDecision(str, Enum): MATCH='MATCH'; HOLD='HOLD'; DENY='DENY'
class EngineState(str, Enum):
    EXECUTION_RECEIPT_BOUND_CANDIDATE='EXECUTION_RECEIPT_BOUND_CANDIDATE'
    RECEIPT_REACQUISITION_CANDIDATE='RECEIPT_REACQUISITION_CANDIDATE'
    INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_POST_EXECUTION_AUDIT_CANDIDATE='CONTINUE_POST_EXECUTION_AUDIT_CANDIDATE'
    REACQUIRE_EXECUTION_RECEIPT_CANDIDATE='REACQUIRE_EXECUTION_RECEIPT_CANDIDATE'
    RETAIN_NO_ACTION_CANDIDATE='RETAIN_NO_ACTION_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'; RECEIPT_FINGERPRINT_MISMATCH='RECEIPT_FINGERPRINT_MISMATCH'; BINDING_MISMATCH='BINDING_MISMATCH'

HEX64=re.compile(r'^[0-9a-f]{64}$'); _WS=re.compile(r'\s+')
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
def _seed_fp(label:str)->str: return sha256(label.encode()).hexdigest()
def _norm(v:str)->str: return _WS.sub(' ',str(v).strip())
def _parse_aware(s:str)->datetime:
    try: d=datetime.fromisoformat(str(s))
    except Exception as e: raise ValueError('invalid ISO datetime') from e
    if d.tzinfo is None or d.utcoffset() is None: raise ValueError('timezone-aware datetime required')
    return d.astimezone(timezone.utc)
def _valid_hex64(v:str)->bool: return bool(HEX64.fullmatch(str(v)))
def _norm_tuple(xs): return tuple(_norm(x) for x in xs if _norm(x))

@dataclass(frozen=True)
class ExecutionReceipt:
    schema:str; receipt_id:str; request_id:str; permit_id:str; action:str; target:str
    started_at:str; finished_at:str; status:ReceiptStatus
    changes:tuple[str,...]; postconditions:tuple[str,...]; rollback_reference:str|None
    intent_fingerprint:str; policy_fingerprint:str; result_digest:str; issuer_authority_id:str
    fingerprint:str

@dataclass(frozen=True)
class ReceiptBindingRequest:
    verification_id:str; receipt:ExecutionReceipt; expected_request_id:str; expected_permit_id:str
    expected_action:str; expected_target:str; binding:str; state_epoch:str

@dataclass(frozen=True)
class ReceiptBindingResult:
    binding_decision:BindingDecision; next_action:NextAction; escalation:Escalation; engine_state:EngineState
    verification_id:str; receipt_fingerprint_valid:bool; request_match:bool; permit_match:bool
    action_match:bool; target_match:bool; time_order_valid:bool; status_rules_valid:bool
    receipt_status:ReceiptStatus|None; change_count:int; postcondition_count:int; rollback_reference_present:bool
    next_gate_candidate:bool; receipt_fingerprint:str; reasons:tuple[str,...]
    receipt_status_promoted_to_world_truth:bool=False; receipt_status_promoted_to_action_success:bool=False
    result_digest_promoted_to_truth:bool=False; postcondition_promoted_to_truth:bool=False
    permission_granted:bool=False; policy_decision_executed:bool=False; approval_executed:bool=False
    human_approval_executed:bool=False; permit_issued:bool=False; tool_invoked:bool=False
    action_executed_by_artifact:bool=False; action_success_promoted:bool=False; rollback_executed:bool=False
    stop_executed:bool=False; file_write_executed:bool=False; network_send_executed:bool=False
    external_write_performed:bool=False; authoritative_state_created:bool=False; cached_state_promoted:bool=False
    reconstructed_state_promoted:bool=False; partial_state_promoted_to_success:bool=False
    dcsr_generated_success_receipt:bool=False; dcsr_changed_receipt_status:bool=False
    dcsr_reconstruction_created_fact:bool=False; sender_authority_inherited:bool=False
    sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False; authority_granted:bool=False
    world_truth_proven:bool=False; domain_authority_promoted:bool=False; safety_proven:bool=False

@dataclass(frozen=True)
class PreparedReceiptState:
    request:ReceiptBindingRequest; result:ReceiptBindingResult; receipt_fingerprint:str
    query_fingerprint:str; result_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str

@dataclass(frozen=True)
class ReceiptChange:
    receipt_changed:bool; query_changed:bool; receipt_id_changed:bool; from_fingerprint:str; to_fingerprint:str

@dataclass(frozen=True)
class MissingOnlyPlan:
    missing_or_changed_record_ids:tuple[str,...]; metadata_bytes_required:int; full_resend_required:bool


def _payload(schema,receipt_id,request_id,permit_id,action,target,started_at,finished_at,status,changes,postconditions,rollback_reference,intent_fingerprint,policy_fingerprint,result_digest,issuer_authority_id):
    return {'schema':schema,'receipt_id':receipt_id,'request_id':request_id,'permit_id':permit_id,'action':action,'target':target,
            'started_at':started_at,'finished_at':finished_at,'status':status,'changes':changes,'postconditions':postconditions,
            'rollback_reference':rollback_reference,'intent_fingerprint':intent_fingerprint,'policy_fingerprint':policy_fingerprint,
            'result_digest':result_digest,'issuer_authority_id':issuer_authority_id}

def build_receipt(*,receipt_id,request_id,permit_id,action,target,started_at,finished_at,status,changes=(),postconditions=(),rollback_reference=None,intent_fingerprint,policy_fingerprint,result_digest,issuer_authority_id):
    rid=_norm(receipt_id); req=_norm(request_id); pid=_norm(permit_id); act=_norm(action); tgt=_norm(target); issuer=_norm(issuer_authority_id)
    if not all((rid,req,pid,act,tgt,issuer)): raise ValueError('Receipt/Request/Permit/Action/Target/Issuer IDs are required')
    try: st=ReceiptStatus(status)
    except Exception as e: raise ValueError('Unknown Receipt Status') from e
    start=_parse_aware(started_at); finish=_parse_aware(finished_at)
    if finish < start: raise ValueError('Finished time must not precede Started time')
    if not _valid_hex64(intent_fingerprint) or not _valid_hex64(policy_fingerprint) or not _valid_hex64(result_digest):
        raise ValueError('Intent/Policy/Result digests must be lowercase SHA-256 hex')
    ch=_norm_tuple(changes); pc=_norm_tuple(postconditions); rb=_norm(rollback_reference) if rollback_reference is not None else None
    if st==ReceiptStatus.SUCCEEDED and not pc: raise ValueError('SUCCEEDED receipt requires Postcondition evidence')
    if st in (ReceiptStatus.PARTIAL,ReceiptStatus.ROLLED_BACK) and not rb: raise ValueError('PARTIAL/ROLLED_BACK receipt requires Rollback reference')
    schema='NOEPIN_AL_EXECUTION_RECEIPT_V1'; start_s=start.isoformat(); finish_s=finish.isoformat()
    p=_payload(schema,rid,req,pid,act,tgt,start_s,finish_s,st,ch,pc,rb,intent_fingerprint,policy_fingerprint,result_digest,issuer)
    return ExecutionReceipt(schema,rid,req,pid,act,tgt,start_s,finish_s,st,ch,pc,rb,intent_fingerprint,policy_fingerprint,result_digest,issuer,_fp(p))

def _receipt_fp_valid(r:ExecutionReceipt)->bool:
    try:
        if r.schema!='NOEPIN_AL_EXECUTION_RECEIPT_V1': return False
        rebuilt=build_receipt(receipt_id=r.receipt_id,request_id=r.request_id,permit_id=r.permit_id,action=r.action,target=r.target,started_at=r.started_at,finished_at=r.finished_at,status=r.status,changes=r.changes,postconditions=r.postconditions,rollback_reference=r.rollback_reference,intent_fingerprint=r.intent_fingerprint,policy_fingerprint=r.policy_fingerprint,result_digest=r.result_digest,issuer_authority_id=r.issuer_authority_id)
        return rebuilt==r
    except Exception: return False

def _query_payload(q:ReceiptBindingRequest):
    return {'verification_id':q.verification_id,'expected_request_id':q.expected_request_id,'expected_permit_id':q.expected_permit_id,'expected_action':q.expected_action,'expected_target':q.expected_target,'binding':q.binding,'state_epoch':q.state_epoch}

def evaluate(q:ReceiptBindingRequest)->ReceiptBindingResult:
    vid=_norm(q.verification_id)
    if not vid:
        return ReceiptBindingResult(BindingDecision.HOLD,NextAction.RETAIN_NO_ACTION_CANDIDATE,Escalation.INVALID_CONFIGURATION,EngineState.INVALID,'',False,False,False,False,False,False,False,None,0,0,False,False,q.receipt.fingerprint,('verification_id required',))
    if not _receipt_fp_valid(q.receipt):
        return ReceiptBindingResult(BindingDecision.DENY,NextAction.RETAIN_NO_ACTION_CANDIDATE,Escalation.RECEIPT_FINGERPRINT_MISMATCH,EngineState.INVALID,vid,False,False,False,False,False,False,False,None,len(q.receipt.changes),len(q.receipt.postconditions),bool(q.receipt.rollback_reference),False,q.receipt.fingerprint,('Execution Receipt fingerprint or structure mismatch',))
    rm=q.receipt.request_id==_norm(q.expected_request_id); pm=q.receipt.permit_id==_norm(q.expected_permit_id); am=q.receipt.action==_norm(q.expected_action); tm=q.receipt.target==_norm(q.expected_target)
    start=_parse_aware(q.receipt.started_at); finish=_parse_aware(q.receipt.finished_at); tov=finish>=start
    srv=(q.receipt.status!=ReceiptStatus.SUCCEEDED or bool(q.receipt.postconditions)) and (q.receipt.status not in (ReceiptStatus.PARTIAL,ReceiptStatus.ROLLED_BACK) or bool(q.receipt.rollback_reference))
    if not all((rm,pm,am,tm)):
        return ReceiptBindingResult(BindingDecision.HOLD,NextAction.REACQUIRE_EXECUTION_RECEIPT_CANDIDATE,Escalation.BINDING_MISMATCH,EngineState.RECEIPT_REACQUISITION_CANDIDATE,vid,True,rm,pm,am,tm,tov,srv,q.receipt.status,len(q.receipt.changes),len(q.receipt.postconditions),bool(q.receipt.rollback_reference),False,q.receipt.fingerprint,('Request/Permit/Action/Target binding mismatch',))
    return ReceiptBindingResult(BindingDecision.MATCH,NextAction.CONTINUE_POST_EXECUTION_AUDIT_CANDIDATE,Escalation.NONE,EngineState.EXECUTION_RECEIPT_BOUND_CANDIDATE,vid,True,True,True,True,True,tov,srv,q.receipt.status,len(q.receipt.changes),len(q.receipt.postconditions),bool(q.receipt.rollback_reference),True,q.receipt.fingerprint,('Execution Receipt is structurally valid and bound as a post-execution evidence candidate only',))

def prepare_state(q,binding,state_epoch):
    r=evaluate(q); qfp=_fp(_query_payload(q)); rfp=_fp(r)
    base={'receipt_fingerprint':q.receipt.fingerprint,'query_fingerprint':qfp,'result_fingerprint':rfp,'binding':binding,'state_epoch':state_epoch}
    return PreparedReceiptState(q,r,q.receipt.fingerprint,qfp,rfp,_fp(base),binding,state_epoch)

def _prepared_integrity_ok(st):
    base={'receipt_fingerprint':st.receipt_fingerprint,'query_fingerprint':st.query_fingerprint,'result_fingerprint':st.result_fingerprint,'binding':st.binding,'state_epoch':st.state_epoch}
    return st.integrity_fingerprint==_fp(base)

def evaluate_prepared(st:PreparedReceiptState,*,integrity_validated,current_receipt_fingerprint,current_query_fingerprint,current_result_fingerprint):
    if not integrity_validated or not _prepared_integrity_ok(st) or current_receipt_fingerprint!=st.receipt_fingerprint or current_query_fingerprint!=st.query_fingerprint or current_result_fingerprint!=st.result_fingerprint:
        return ReceiptBindingResult(BindingDecision.HOLD,NextAction.RETAIN_NO_ACTION_CANDIDATE,Escalation.INVALID_CONFIGURATION,EngineState.INVALID,st.request.verification_id,False,False,False,False,False,False,False,None,0,0,False,False,st.request.receipt.fingerprint,('Prepared state integrity/current fingerprints not validated',))
    return st.result

def make_delta(old:PreparedReceiptState,new:PreparedReceiptState)->ReceiptChange:
    return ReceiptChange(old.receipt_fingerprint!=new.receipt_fingerprint,old.query_fingerprint!=new.query_fingerprint,old.request.receipt.receipt_id!=new.request.receipt.receipt_id,old.integrity_fingerprint,new.integrity_fingerprint)

def plan_missing_only(old:PreparedReceiptState,new:PreparedReceiptState)->MissingOnlyPlan:
    d=make_delta(old,new); rec=[]
    if d.receipt_changed:
        rec.append(('RECEIPT:' if d.receipt_id_changed else 'CHANGE_SEGMENT:')+new.request.receipt.receipt_id)
    if d.query_changed: rec.append('BINDING_QUERY')
    records=tuple(rec); metadata=len(_canon({'records':records,'from':d.from_fingerprint,'to':d.to_fingerprint}))
    return MissingOnlyPlan(records,metadata,False)

def default_receipt():
    return build_receipt(receipt_id='RCPT-177-A',request_id='REQ-177-A',permit_id='PERMIT-177-A',action='update_verified_artifact',target='artifact:NOEPIN-AL-177',started_at='2026-11-13T16:30:00+00:00',finished_at='2026-11-13T16:30:02+00:00',status=ReceiptStatus.SUCCEEDED,changes=('artifact content recorded','postcondition evidence captured'),postconditions=('target fingerprint matches expected result digest','no unauthorized external write observed'),rollback_reference=None,intent_fingerprint=_seed_fp('INTENT-177-A'),policy_fingerprint=_seed_fp('POLICY-177-A'),result_digest=_seed_fp('RESULT-177-A'),issuer_authority_id='EXEC-AUTH-177-A')
def default_request():
    r=default_receipt(); return ReceiptBindingRequest('ER-177-A',r,r.request_id,r.permit_id,r.action,r.target,'DEFAULT-BINDING','EPOCH-1')
def default_evaluation(): return evaluate(default_request())

if __name__=='__main__': print(json.dumps(_obj(default_evaluation()),ensure_ascii=False,sort_keys=True,indent=2))
