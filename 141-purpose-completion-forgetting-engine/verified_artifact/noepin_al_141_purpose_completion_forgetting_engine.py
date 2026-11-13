"""NOEPIN AL 141 — Purpose-Completion Forgetting Engine — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-141
DCSR: LIMITED INTEGRATION / 限定適用.

Produces retention/deletion/archive/anonymization candidates after a purpose completes,
without performing destructive mutation. Memory != Truth. Delete Candidate != Delete
Execution. Retain Candidate != World Truth. Legal Hold Evidence != external enforcement.
HOLD/Review Candidate != Stop Execution. DCSR reconstruction does not create Memory,
known Fact, Domain Authority, Permission, Approval, Action, or Action Success.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str, Enum):
    ALLOW='ALLOW'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'; DENY='DENY'
class EngineState(str, Enum):
    PLAN_READY_CANDIDATE='PLAN_READY_CANDIDATE'; REVIEW_REQUIRED_CANDIDATE='REVIEW_REQUIRED_CANDIDATE'
    EMPTY='EMPTY'; INVALID='INVALID'
class NextAction(str, Enum):
    APPLY_RETENTION_PLAN_CANDIDATE='APPLY_RETENTION_PLAN_CANDIDATE'; REVIEW_RETENTION_CANDIDATE='REVIEW_RETENTION_CANDIDATE'
    NO_MEMORY_CANDIDATE='NO_MEMORY_CANDIDATE'; REVIEW_CANDIDATE='REVIEW_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; POLICY_OR_PROVENANCE_UNCLEAR='POLICY_OR_PROVENANCE_UNCLEAR'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'
class PlanAction(str, Enum):
    DELETE_CANDIDATE='DELETE_CANDIDATE'; ARCHIVE_CANDIDATE='ARCHIVE_CANDIDATE'; RETAIN_CANDIDATE='RETAIN_CANDIDATE'
    ANONYMIZE_CANDIDATE='ANONYMIZE_CANDIDATE'; REVIEW_CANDIDATE='REVIEW_CANDIDATE'; NO_CHANGE_CANDIDATE='NO_CHANGE_CANDIDATE'
class MemoryKind(str, Enum):
    GENERAL='GENERAL'; CREDENTIAL='CREDENTIAL'; PERSONAL='PERSONAL'; PROVENANCE='PROVENANCE'; AUDIT='AUDIT'
class RetentionClass(str, Enum):
    DELETE_AFTER_PURPOSE='DELETE_AFTER_PURPOSE'; ARCHIVE_AFTER_PURPOSE='ARCHIVE_AFTER_PURPOSE'
    RETAIN_REQUIRED='RETAIN_REQUIRED'; ANONYMIZE_AFTER_PURPOSE='ANONYMIZE_AFTER_PURPOSE'; UNKNOWN='UNKNOWN'

@dataclass(frozen=True)
class MemoryRecord:
    memory_id:str; purpose_ids:tuple[str,...]; memory_kind:MemoryKind; retention_class:RetentionClass
    provenance_ids:tuple[str,...]; legal_hold:bool; audit_required:bool; provenance_required:bool
    retention_reason:str; binding:str; state_epoch:str

@dataclass(frozen=True)
class RetentionPolicy:
    credential_delete_candidate:bool=True
    legal_hold_retain:bool=True
    audit_retain:bool=True
    provenance_retain:bool=True
    unknown_requires_review:bool=True
    personal_anonymize_candidate:bool=True

@dataclass(frozen=True)
class ForgetRequest:
    request_id:str; completed_purpose_ids:tuple[str,...]; memories:tuple[MemoryRecord,...]
    policy:RetentionPolicy; binding:str; state_epoch:str

@dataclass(frozen=True)
class PlanEntry:
    memory_id:str; action:PlanAction; affected_completed_purposes:tuple[str,...]
    remaining_purposes:tuple[str,...]; reasons:tuple[str,...]
    destructive_execution_performed:bool=False

@dataclass(frozen=True)
class ProofEntry:
    memory_id:str; action:PlanAction; legal_hold_observed:bool; audit_required_observed:bool
    provenance_required_observed:bool; retention_class:RetentionClass; reasons:tuple[str,...]

@dataclass(frozen=True)
class ForgetResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState
    plan:tuple[PlanEntry,...]; proof_log:tuple[ProofEntry,...]; review_memory_ids:tuple[str,...]
    delete_candidate_ids:tuple[str,...]; archive_candidate_ids:tuple[str,...]; retain_candidate_ids:tuple[str,...]
    anonymize_candidate_ids:tuple[str,...]; reasons:tuple[str,...]; next_gate_candidate:bool
    memory_promoted_to_truth:bool=False; mention_promoted_to_memory:bool=False
    delete_executed:bool=False; archive_executed:bool=False; anonymize_executed:bool=False; credential_revoked:bool=False
    memory_write_performed:bool=False; memory_delete_performed:bool=False; retention_policy_modified:bool=False
    legal_hold_enforced_externally:bool=False; proof_log_written_externally:bool=False
    dcsr_reconstruction_created_memory:bool=False; sender_authority_inherited:bool=False; sender_intent_inherited:bool=False
    sender_agreement_inherited:bool=False; permission_granted:bool=False; approval_executed:bool=False
    authority_granted:bool=False; stop_executed:bool=False; action_executed:bool=False; plan_committed:bool=False
    publish_executed:bool=False; external_write_performed:bool=False; world_truth_proven:bool=False
    domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False

@dataclass(frozen=True)
class PreparedForgetState:
    request:ForgetRequest; result:ForgetResult; context_fingerprint:str; memories_fingerprint:str
    policy_fingerprint:str; outcome_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str

@dataclass(frozen=True)
class ForgetDelta:
    changed_memories:tuple[MemoryRecord,...]; removed_memory_ids:tuple[str,...]; completed_purposes_changed:bool
    policy_changed:bool; from_manifest_fingerprint:str; to_manifest_fingerprint:str

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
def _manifest_fp(req): return _fp((req.completed_purpose_ids,req.memories,req.policy,req.binding,req.state_epoch))

def default_policy(): return RetentionPolicy()
def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    m=MemoryRecord('MEM-141-A',('PURPOSE-A',),MemoryKind.GENERAL,RetentionClass.DELETE_AFTER_PURPOSE,('TRACE-141-A',),False,False,False,'',b,e)
    return ForgetRequest('REQ-141',('PURPOSE-A',),(m,),default_policy(),b,e)

def _invalid(reason):
    return ForgetResult(Decision.HOLD,NextAction.REVIEW_CANDIDATE,Escalation.INVALID_CONFIGURATION,EngineState.INVALID,(),(),(),(),(),(),(),(reason,'NO_DESTRUCTIVE_EXECUTION','NO_MEMORY_WRITE'),False)

def _validate(req):
    if not req.request_id or not req.binding or not req.state_epoch: return 'EMPTY_REQUEST_CONTEXT'
    if len(set(req.completed_purpose_ids))!=len(req.completed_purpose_ids): return 'DUPLICATE_COMPLETED_PURPOSE_ID'
    if any(not x for x in req.completed_purpose_ids): return 'EMPTY_COMPLETED_PURPOSE_ID'
    ids=set()
    for x in req.memories:
        if not x.memory_id: return 'EMPTY_MEMORY_ID'
        if x.memory_id in ids: return 'DUPLICATE_MEMORY_ID'
        ids.add(x.memory_id)
        if x.binding!=req.binding or x.state_epoch!=req.state_epoch: return 'MEMORY_STATE_BINDING_MISMATCH'
        if len(set(x.purpose_ids))!=len(x.purpose_ids): return 'DUPLICATE_PURPOSE_LINK'
        if len(set(x.provenance_ids))!=len(x.provenance_ids): return 'DUPLICATE_PROVENANCE_ID'
        if any(not p for p in x.purpose_ids): return 'EMPTY_PURPOSE_LINK'
        if any(not p for p in x.provenance_ids): return 'EMPTY_PROVENANCE_ID'
    return None

def _plan_one(x,completed,policy):
    affected=tuple(sorted(set(x.purpose_ids)&completed)); remaining=tuple(sorted(set(x.purpose_ids)-completed)); reasons=[]
    if not affected:
        return PlanEntry(x.memory_id,PlanAction.NO_CHANGE_CANDIDATE,(),remaining,('NO_COMPLETED_PURPOSE_DEPENDENCY',)), ProofEntry(x.memory_id,PlanAction.NO_CHANGE_CANDIDATE,x.legal_hold,x.audit_required,x.provenance_required,x.retention_class,('NO_COMPLETED_PURPOSE_DEPENDENCY',))
    if remaining:
        reasons=('OTHER_ACTIVE_PURPOSE_DEPENDENCY_REMAINS','NO_DESTRUCTIVE_EXECUTION')
        return PlanEntry(x.memory_id,PlanAction.RETAIN_CANDIDATE,affected,remaining,reasons), ProofEntry(x.memory_id,PlanAction.RETAIN_CANDIDATE,x.legal_hold,x.audit_required,x.provenance_required,x.retention_class,reasons)
    if x.legal_hold and policy.legal_hold_retain:
        reasons=('LEGAL_HOLD_RETAIN_CANDIDATE','LEGAL_HOLD_EVIDENCE_NOT_EXTERNAL_ENFORCEMENT')
        return PlanEntry(x.memory_id,PlanAction.RETAIN_CANDIDATE,affected,(),reasons), ProofEntry(x.memory_id,PlanAction.RETAIN_CANDIDATE,True,x.audit_required,x.provenance_required,x.retention_class,reasons)
    if x.audit_required and policy.audit_retain:
        reasons=('AUDIT_RETENTION_REQUIRED','NO_DESTRUCTIVE_EXECUTION')
        return PlanEntry(x.memory_id,PlanAction.RETAIN_CANDIDATE,affected,(),reasons), ProofEntry(x.memory_id,PlanAction.RETAIN_CANDIDATE,x.legal_hold,True,x.provenance_required,x.retention_class,reasons)
    if x.provenance_required and policy.provenance_retain:
        reasons=('PROVENANCE_RETENTION_REQUIRED','NO_DESTRUCTIVE_EXECUTION')
        return PlanEntry(x.memory_id,PlanAction.RETAIN_CANDIDATE,affected,(),reasons), ProofEntry(x.memory_id,PlanAction.RETAIN_CANDIDATE,x.legal_hold,x.audit_required,True,x.retention_class,reasons)
    if x.retention_class==RetentionClass.RETAIN_REQUIRED:
        reasons=('RETENTION_POLICY_RETAIN_REQUIRED','NO_DESTRUCTIVE_EXECUTION')
        return PlanEntry(x.memory_id,PlanAction.RETAIN_CANDIDATE,affected,(),reasons), ProofEntry(x.memory_id,PlanAction.RETAIN_CANDIDATE,x.legal_hold,x.audit_required,x.provenance_required,x.retention_class,reasons)
    if x.retention_class==RetentionClass.UNKNOWN and policy.unknown_requires_review:
        reasons=('RETENTION_POLICY_UNKNOWN','REVIEW_REQUIRED','NO_DESTRUCTIVE_EXECUTION')
        return PlanEntry(x.memory_id,PlanAction.REVIEW_CANDIDATE,affected,(),reasons), ProofEntry(x.memory_id,PlanAction.REVIEW_CANDIDATE,x.legal_hold,x.audit_required,x.provenance_required,x.retention_class,reasons)
    if x.memory_kind==MemoryKind.CREDENTIAL and policy.credential_delete_candidate:
        reasons=('CREDENTIAL_PURPOSE_COMPLETED','REVOCATION_OR_DELETE_CANDIDATE_ONLY','NO_CREDENTIAL_REVOCATION_EXECUTED')
        return PlanEntry(x.memory_id,PlanAction.DELETE_CANDIDATE,affected,(),reasons), ProofEntry(x.memory_id,PlanAction.DELETE_CANDIDATE,x.legal_hold,x.audit_required,x.provenance_required,x.retention_class,reasons)
    if x.retention_class==RetentionClass.ARCHIVE_AFTER_PURPOSE:
        reasons=('PURPOSE_COMPLETED','ARCHIVE_POLICY_MATCH','ARCHIVE_CANDIDATE_ONLY')
        return PlanEntry(x.memory_id,PlanAction.ARCHIVE_CANDIDATE,affected,(),reasons), ProofEntry(x.memory_id,PlanAction.ARCHIVE_CANDIDATE,x.legal_hold,x.audit_required,x.provenance_required,x.retention_class,reasons)
    if x.retention_class==RetentionClass.ANONYMIZE_AFTER_PURPOSE and policy.personal_anonymize_candidate:
        reasons=('PURPOSE_COMPLETED','ANONYMIZE_POLICY_MATCH','ANONYMIZE_CANDIDATE_ONLY')
        return PlanEntry(x.memory_id,PlanAction.ANONYMIZE_CANDIDATE,affected,(),reasons), ProofEntry(x.memory_id,PlanAction.ANONYMIZE_CANDIDATE,x.legal_hold,x.audit_required,x.provenance_required,x.retention_class,reasons)
    if x.retention_class==RetentionClass.DELETE_AFTER_PURPOSE:
        reasons=('PURPOSE_COMPLETED','NO_RETENTION_GROUND','DELETE_CANDIDATE_ONLY')
        return PlanEntry(x.memory_id,PlanAction.DELETE_CANDIDATE,affected,(),reasons), ProofEntry(x.memory_id,PlanAction.DELETE_CANDIDATE,x.legal_hold,x.audit_required,x.provenance_required,x.retention_class,reasons)
    reasons=('UNRESOLVED_RETENTION_RULE','REVIEW_REQUIRED','NO_DESTRUCTIVE_EXECUTION')
    return PlanEntry(x.memory_id,PlanAction.REVIEW_CANDIDATE,affected,(),reasons), ProofEntry(x.memory_id,PlanAction.REVIEW_CANDIDATE,x.legal_hold,x.audit_required,x.provenance_required,x.retention_class,reasons)

def evaluate(req):
    err=_validate(req)
    if err: return _invalid(err)
    if not req.memories:
        return ForgetResult(Decision.ALLOW,NextAction.NO_MEMORY_CANDIDATE,Escalation.NONE,EngineState.EMPTY,(),(),(),(),(),(),(),('NO_MEMORY_RECORDS','NO_DESTRUCTIVE_EXECUTION'),True)
    completed=set(req.completed_purpose_ids)
    pairs=tuple(_plan_one(x,completed,req.policy) for x in req.memories)
    plan=tuple(p[0] for p in pairs); proof=tuple(p[1] for p in pairs)
    review=tuple(sorted(p.memory_id for p in plan if p.action==PlanAction.REVIEW_CANDIDATE))
    deletes=tuple(sorted(p.memory_id for p in plan if p.action==PlanAction.DELETE_CANDIDATE))
    archives=tuple(sorted(p.memory_id for p in plan if p.action==PlanAction.ARCHIVE_CANDIDATE))
    retains=tuple(sorted(p.memory_id for p in plan if p.action==PlanAction.RETAIN_CANDIDATE))
    anonymize=tuple(sorted(p.memory_id for p in plan if p.action==PlanAction.ANONYMIZE_CANDIDATE))
    if review:
        return ForgetResult(Decision.HOLD,NextAction.REVIEW_RETENTION_CANDIDATE,Escalation.POLICY_OR_PROVENANCE_UNCLEAR,EngineState.REVIEW_REQUIRED_CANDIDATE,plan,proof,review,deletes,archives,retains,anonymize,('REVIEW_REQUIRED_BEFORE_DESTRUCTIVE_CANDIDATE','NO_DESTRUCTIVE_EXECUTION','NO_STOP_EXECUTION'),False)
    return ForgetResult(Decision.ALLOW,NextAction.APPLY_RETENTION_PLAN_CANDIDATE,Escalation.NONE,EngineState.PLAN_READY_CANDIDATE,plan,proof,(),deletes,archives,retains,anonymize,('RETENTION_PLAN_CANDIDATE_ONLY','NO_DESTRUCTIVE_EXECUTION','NO_EXTERNAL_WRITE'),True)

def default_evaluation(): return evaluate(default_request())

def _fps(req,res): return (_fp((req.request_id,req.binding,req.state_epoch,req.completed_purpose_ids)),_fp(req.memories),_fp(req.policy),_fp(res))
def prepare_state(req,binding,state_epoch):
    if binding!=req.binding or state_epoch!=req.state_epoch: raise ValueError('PREPARED_BINDING_MISMATCH')
    res=evaluate(req); c,m,p,o=_fps(req,res); integ=_fp((c,m,p,o,binding,state_epoch))
    return PreparedForgetState(req,res,c,m,p,o,integ,binding,state_epoch)
def validate_prepared_integrity(st): return st.integrity_fingerprint==_fp((st.context_fingerprint,st.memories_fingerprint,st.policy_fingerprint,st.outcome_fingerprint,st.binding,st.state_epoch))
def evaluate_prepared(st,*,integrity_validated,current_context_fingerprint,current_memories_fingerprint,current_policy_fingerprint,current_outcome_fingerprint):
    if not integrity_validated or not validate_prepared_integrity(st): return _invalid('PREPARED_INTEGRITY_NOT_VALIDATED')
    if (current_context_fingerprint,current_memories_fingerprint,current_policy_fingerprint,current_outcome_fingerprint)!=(st.context_fingerprint,st.memories_fingerprint,st.policy_fingerprint,st.outcome_fingerprint): return _invalid('PREPARED_FINGERPRINT_MISMATCH')
    return st.result

def make_delta(old,new):
    a={x.memory_id:x for x in old.request.memories}; b={x.memory_id:x for x in new.request.memories}
    changed=tuple(b[k] for k in sorted(b) if k not in a or a[k]!=b[k]); removed=tuple(sorted(set(a)-set(b)))
    return ForgetDelta(changed,removed,old.request.completed_purpose_ids!=new.request.completed_purpose_ids,old.policy_fingerprint!=new.policy_fingerprint,_manifest_fp(old.request),_manifest_fp(new.request))
def plan_missing_only(old,new):
    d=make_delta(old,new); ids=[f'MEMORY:{x.memory_id}' for x in d.changed_memories]+[f'MEMORY:{x}' for x in d.removed_memory_ids]
    if d.completed_purposes_changed: ids.append('COMPLETED_PURPOSE_SET')
    if d.policy_changed: ids.append('RETENTION_POLICY')
    meta=len(_canon((tuple(ids),d.from_manifest_fingerprint,d.to_manifest_fingerprint)))
    return MissingOnlyPlan(tuple(ids),meta,False)
