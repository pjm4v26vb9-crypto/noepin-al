"""NOEPIN AL 150 — Tainted-Instruction Sink Guard — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-150
DCSR: AUXILIARY INTEGRATION / 補助統合.

Tracks instruction/data taint through transformations and evaluates it immediately before a target sink.
Outputs are Sink Decision / Taint Path / Sanitization Need candidates only.
Taint != Truth. User Authorization Evidence != Permission Grant. Sink Decision != Sink Execution.
Sanitization Need != Sanitization Execution. DENY/HOLD Candidate != Stop Execution.
This core performs no tool invocation, file write, network send, read operation, policy mutation,
authorization mutation, approval, quarantine, stop, or external action. DCSR reconstruction cannot
create Truth, Domain Authority, Permission, Safety Proof, Approval, Action, or Action Success.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json

class Decision(str, Enum):
    ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class EngineState(str, Enum):
    SAFE_SINK_CANDIDATE='SAFE_SINK_CANDIDATE'
    TAINTED_DANGEROUS_SINK_CANDIDATE='TAINTED_DANGEROUS_SINK_CANDIDATE'
    REAUTHORIZED_SINK_CANDIDATE='REAUTHORIZED_SINK_CANDIDATE'
    REVIEW_CANDIDATE='REVIEW_CANDIDATE'
    INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_SINK_CANDIDATE='CONTINUE_SINK_CANDIDATE'
    REJECT_SINK_CANDIDATE='REJECT_SINK_CANDIDATE'
    REQUIRE_REAUTHORIZATION_CANDIDATE='REQUIRE_REAUTHORIZATION_CANDIDATE'
    REVIEW_TAINT_PATH_CANDIDATE='REVIEW_TAINT_PATH_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'
    DANGEROUS_TAINT_TO_SINK='DANGEROUS_TAINT_TO_SINK'
    TAINT_PATH_UNKNOWN='TAINT_PATH_UNKNOWN'
    USER_AUTHORIZATION_REQUIRED='USER_AUTHORIZATION_REQUIRED'
    AUTHORIZATION_BINDING_MISMATCH='AUTHORIZATION_BINDING_MISMATCH'
    DATA_TAINT_AT_MUTATING_SINK='DATA_TAINT_AT_MUTATING_SINK'
    INVALID_CONFIGURATION='INVALID_CONFIGURATION'
class TaintKind(str, Enum):
    NONE='NONE'; TRUSTED_INSTRUCTION='TRUSTED_INSTRUCTION'; UNTRUSTED_INSTRUCTION='UNTRUSTED_INSTRUCTION'; DATA_ONLY='DATA_ONLY'
class SinkClass(str, Enum):
    READ='READ'; TOOL_EXECUTE='TOOL_EXECUTE'; FILE_WRITE='FILE_WRITE'; NETWORK_SEND='NETWORK_SEND'

@dataclass(frozen=True)
class InstructionNode:
    instruction_id:str; intent:str; source_id:str; source_trusted:bool; transformation_chain:tuple[str,...]; binding:str; state_epoch:str
@dataclass(frozen=True)
class TaintLabel:
    label_id:str; kind:TaintKind; source_id:str; inherited_through:tuple[str,...]; confidence:float; binding:str; state_epoch:str
@dataclass(frozen=True)
class TargetSink:
    sink_id:str; sink_class:SinkClass; target_ref:str; mutating:bool; external:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class UserAuthorizationEvidence:
    evidence_id:str; explicit:bool; authorized_sink_classes:tuple[SinkClass,...]; instruction_id:str; sink_id:str; current:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class SinkGuardRequest:
    request_id:str; instruction:InstructionNode; taints:tuple[TaintLabel,...]; sink:TargetSink; authorization:UserAuthorizationEvidence
    taint_path_complete:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class SinkGuardResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState
    instruction_id:str; sink_id:str; taint_path:tuple[str,...]; taint_summary:tuple[str,...]; sanitization_need:tuple[str,...]
    reasons:tuple[str,...]; next_gate_candidate:bool
    taint_promoted_to_truth:bool=False; user_authorization_promoted_to_permission:bool=False
    sink_decision_executed:bool=False; sanitization_executed:bool=False; tool_invoked:bool=False
    file_write_executed:bool=False; network_send_executed:bool=False; read_executed:bool=False
    policy_modified:bool=False; authorization_modified:bool=False; dlp_replaced:bool=False
    authentication_replaced:bool=False; encryption_replaced:bool=False; dcsr_reconstruction_created_fact:bool=False
    sender_authority_inherited:bool=False; sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False
    permission_granted:bool=False; approval_executed:bool=False; authority_granted:bool=False
    stop_executed:bool=False; action_executed:bool=False; plan_committed:bool=False; publish_executed:bool=False
    external_write_performed:bool=False; world_truth_proven:bool=False; domain_authority_promoted:bool=False
    safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedSinkGuardState:
    request:SinkGuardRequest; result:SinkGuardResult; instruction_fingerprint:str; taint_fingerprint:str
    sink_fingerprint:str; authorization_fingerprint:str; path_fingerprint:str; outcome_fingerprint:str
    integrity_fingerprint:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class SinkGuardDelta:
    instruction_changed:bool; taint_changed:bool; sink_changed:bool; authorization_changed:bool; path_changed:bool
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

def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    inst=InstructionNode('INST-150-A','send tool result to external endpoint','WEB-RAG-150',False,('EXTRACT','SUMMARIZE','PLAN'),b,e)
    taint=TaintLabel('TAINT-150-A',TaintKind.UNTRUSTED_INSTRUCTION,'WEB-RAG-150',('EXTRACT','SUMMARIZE','PLAN'),1.0,b,e)
    sink=TargetSink('SINK-150-A',SinkClass.TOOL_EXECUTE,'tool://external-send',True,True,b,e)
    auth=UserAuthorizationEvidence('AUTH-150-NONE',False,(),inst.instruction_id,sink.sink_id,False,b,e)
    return SinkGuardRequest('REQ-150',inst,(taint,),sink,auth,True,b,e)

def _invalid(req,reason):
    return SinkGuardResult(Decision.HOLD,NextAction.REVIEW_TAINT_PATH_CANDIDATE,Escalation.INVALID_CONFIGURATION,
        EngineState.INVALID,getattr(req.instruction,'instruction_id',''),getattr(req.sink,'sink_id',''),(),(),('REVIEW_CONFIGURATION',),
        (reason,'NO_SINK_EXECUTION','NO_AUTHORITY_PROMOTION'),False)

def _validate(req):
    if not req.request_id or not req.binding or not req.state_epoch: return 'EMPTY_REQUEST_CONTEXT'
    i,s,a=req.instruction,req.sink,req.authorization
    if i.binding!=req.binding or i.state_epoch!=req.state_epoch: return 'INSTRUCTION_BINDING_MISMATCH'
    if s.binding!=req.binding or s.state_epoch!=req.state_epoch: return 'SINK_BINDING_MISMATCH'
    if a.binding!=req.binding or a.state_epoch!=req.state_epoch: return 'AUTHORIZATION_BINDING_MISMATCH'
    if not i.instruction_id or not i.source_id or not s.sink_id or not s.target_ref: return 'EMPTY_REQUIRED_ID'
    seen=set()
    for t in req.taints:
        if t.binding!=req.binding or t.state_epoch!=req.state_epoch: return 'TAINT_BINDING_MISMATCH'
        if not t.label_id or t.label_id in seen: return 'INVALID_TAINT_LABEL_ID'
        seen.add(t.label_id)
        if not (0.0 <= t.confidence <= 1.0): return 'INVALID_TAINT_CONFIDENCE'
    if a.explicit:
        if not a.evidence_id or not a.current: return 'INVALID_AUTHORIZATION_EVIDENCE'
        if a.instruction_id!=i.instruction_id or a.sink_id!=s.sink_id: return 'AUTHORIZATION_TARGET_MISMATCH'
    return None

def _dangerous_sink(s): return s.sink_class in (SinkClass.TOOL_EXECUTE,SinkClass.FILE_WRITE,SinkClass.NETWORK_SEND) or s.mutating or s.external

def _authorization_matches(req):
    a=req.authorization
    return bool(a.explicit and a.current and a.instruction_id==req.instruction.instruction_id and a.sink_id==req.sink.sink_id and req.sink.sink_class in a.authorized_sink_classes)

def evaluate(req):
    bad=_validate(req)
    if bad: return _invalid(req,bad)
    i,s=req.instruction,req.sink
    kinds={t.kind for t in req.taints}
    taint_summary=tuple(sorted(f'{t.label_id}:{t.kind.value}:{t.source_id}:{t.confidence:.3f}' for t in req.taints))
    path=[f'SOURCE:{i.source_id}']+[f'TRANSFORM:{x}' for x in i.transformation_chain]+[f'SINK:{s.sink_class.value}:{s.sink_id}']
    reasons=['TAINT_IS_EVIDENCE_NOT_TRUTH','SINK_DECISION_IS_CANDIDATE_NOT_EXECUTION','NO_TOOL_FILE_OR_NETWORK_EXECUTION']
    dangerous=_dangerous_sink(s)
    auth_ok=_authorization_matches(req)

    if not req.taint_path_complete:
        return SinkGuardResult(Decision.HOLD,NextAction.REVIEW_TAINT_PATH_CANDIDATE,Escalation.TAINT_PATH_UNKNOWN,
            EngineState.REVIEW_CANDIDATE,i.instruction_id,s.sink_id,tuple(path),taint_summary,('RESOLVE_TAINT_PATH','REAUTHORIZE_IF_NEEDED'),
            tuple(['TAINT_PATH_INCOMPLETE']+reasons),True)

    if TaintKind.UNTRUSTED_INSTRUCTION in kinds and dangerous:
        if auth_ok:
            return SinkGuardResult(Decision.ALLOW,NextAction.CONTINUE_SINK_CANDIDATE,Escalation.NONE,
                EngineState.REAUTHORIZED_SINK_CANDIDATE,i.instruction_id,s.sink_id,tuple(path),taint_summary,(),
                tuple(['UNTRUSTED_INSTRUCTION_TAINT_PRESERVED','EXPLICIT_USER_REAUTHORIZATION_EVIDENCE_MATCHED','REAUTHORIZATION_TRIGGERS_REEVALUATION_ONLY']+reasons),True)
        return SinkGuardResult(Decision.DENY,NextAction.REJECT_SINK_CANDIDATE,Escalation.DANGEROUS_TAINT_TO_SINK,
            EngineState.TAINTED_DANGEROUS_SINK_CANDIDATE,i.instruction_id,s.sink_id,tuple(path),taint_summary,
            ('REMOVE_UNTRUSTED_INSTRUCTION_INFLUENCE','OBTAIN_EXPLICIT_REAUTHORIZATION_EVIDENCE'),
            tuple(['UNTRUSTED_INSTRUCTION_TAINT_REACHED_DANGEROUS_SINK']+reasons),True)

    if TaintKind.TRUSTED_INSTRUCTION in kinds and dangerous:
        if auth_ok:
            return SinkGuardResult(Decision.ALLOW,NextAction.CONTINUE_SINK_CANDIDATE,Escalation.NONE,
                EngineState.REAUTHORIZED_SINK_CANDIDATE,i.instruction_id,s.sink_id,tuple(path),taint_summary,(),
                tuple(['TRUSTED_INSTRUCTION_SOURCE','EXPLICIT_USER_AUTHORIZATION_EVIDENCE_MATCHED']+reasons),True)
        return SinkGuardResult(Decision.HOLD,NextAction.REQUIRE_REAUTHORIZATION_CANDIDATE,Escalation.USER_AUTHORIZATION_REQUIRED,
            EngineState.REVIEW_CANDIDATE,i.instruction_id,s.sink_id,tuple(path),taint_summary,('OBTAIN_EXPLICIT_USER_AUTHORIZATION_EVIDENCE',),
            tuple(['SOURCE_TRUST_DOES_NOT_GRANT_SINK_AUTHORITY']+reasons),True)

    if TaintKind.DATA_ONLY in kinds and dangerous:
        return SinkGuardResult(Decision.HOLD,NextAction.REVIEW_TAINT_PATH_CANDIDATE,Escalation.DATA_TAINT_AT_MUTATING_SINK,
            EngineState.REVIEW_CANDIDATE,i.instruction_id,s.sink_id,tuple(path),taint_summary,('CONFIRM_DATA_IS_NOT_INTERPRETED_AS_INSTRUCTION',),
            tuple(['DATA_ONLY_TAINT_AT_DANGEROUS_SINK']+reasons),True)

    if s.sink_class==SinkClass.READ and not s.mutating and not s.external:
        return SinkGuardResult(Decision.ALLOW,NextAction.CONTINUE_SINK_CANDIDATE,Escalation.NONE,
            EngineState.SAFE_SINK_CANDIDATE,i.instruction_id,s.sink_id,tuple(path),taint_summary,(),
            tuple(['READ_ONLY_SINK_CANDIDATE']+reasons),True)

    if dangerous and not auth_ok:
        return SinkGuardResult(Decision.HOLD,NextAction.REQUIRE_REAUTHORIZATION_CANDIDATE,Escalation.USER_AUTHORIZATION_REQUIRED,
            EngineState.REVIEW_CANDIDATE,i.instruction_id,s.sink_id,tuple(path),taint_summary,('OBTAIN_EXPLICIT_USER_AUTHORIZATION_EVIDENCE',),
            tuple(['MUTATING_OR_EXTERNAL_SINK_REQUIRES_AUTHORIZATION_EVIDENCE']+reasons),True)

    return SinkGuardResult(Decision.ALLOW,NextAction.CONTINUE_SINK_CANDIDATE,Escalation.NONE,
        EngineState.SAFE_SINK_CANDIDATE,i.instruction_id,s.sink_id,tuple(path),taint_summary,(),tuple(['NO_DANGEROUS_TAINT_PATH_FOUND']+reasons),True)

def default_evaluation(): return evaluate(default_request())

def prepare_state(req,binding,state_epoch):
    if binding!=req.binding or state_epoch!=req.state_epoch: raise ValueError('PREPARE_BINDING_MISMATCH')
    r=evaluate(req)
    if r.engine_state==EngineState.INVALID: raise ValueError('INVALID_REQUEST')
    fi,ft,fs,fa,fp=_fp(req.instruction),_fp(req.taints),_fp(req.sink),_fp(req.authorization),_fp(req.taint_path_complete)
    fo=_fp(r); integ=_fp((fi,ft,fs,fa,fp,fo,binding,state_epoch))
    return PreparedSinkGuardState(req,r,fi,ft,fs,fa,fp,fo,integ,binding,state_epoch)

def evaluate_prepared(st,*,integrity_validated,current_instruction_fingerprint,current_taint_fingerprint,current_sink_fingerprint,current_authorization_fingerprint,current_path_fingerprint,current_outcome_fingerprint):
    exp=_fp((st.instruction_fingerprint,st.taint_fingerprint,st.sink_fingerprint,st.authorization_fingerprint,st.path_fingerprint,st.outcome_fingerprint,st.binding,st.state_epoch))
    valid=(integrity_validated and exp==st.integrity_fingerprint and current_instruction_fingerprint==st.instruction_fingerprint and
           current_taint_fingerprint==st.taint_fingerprint and current_sink_fingerprint==st.sink_fingerprint and
           current_authorization_fingerprint==st.authorization_fingerprint and current_path_fingerprint==st.path_fingerprint and
           current_outcome_fingerprint==st.outcome_fingerprint)
    return st.result if valid else _invalid(st.request,'PREPARED_STATE_INTEGRITY_MISMATCH')

def _manifest_fp(st): return _fp((st.instruction_fingerprint,st.taint_fingerprint,st.sink_fingerprint,st.authorization_fingerprint,st.path_fingerprint))
def make_delta(old,new):
    return SinkGuardDelta(old.instruction_fingerprint!=new.instruction_fingerprint,old.taint_fingerprint!=new.taint_fingerprint,
        old.sink_fingerprint!=new.sink_fingerprint,old.authorization_fingerprint!=new.authorization_fingerprint,
        old.path_fingerprint!=new.path_fingerprint,_manifest_fp(old),_manifest_fp(new))
def plan_missing_only(old,new):
    d=make_delta(old,new); ids=[]
    if d.instruction_changed: ids.append('INSTRUCTION')
    if d.taint_changed: ids.append('TAINT_LABELS')
    if d.sink_changed: ids.append('TARGET_SINK')
    if d.authorization_changed: ids.append('USER_AUTHORIZATION_EVIDENCE')
    if d.path_changed: ids.append('TAINT_PATH_STATE')
    metadata=len(_canon({'missing':ids,'from':d.from_manifest_fingerprint,'to':d.to_manifest_fingerprint}))
    return MissingOnlyPlan(tuple(ids),metadata,False)
