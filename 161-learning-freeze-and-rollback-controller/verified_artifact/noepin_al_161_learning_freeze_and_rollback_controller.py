\
"""NOEPIN AL 161 — Learning Freeze and Rollback Controller — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-161
DCSR: DIRECT INTEGRATION / 直接統合.

Pure control-decision evaluator for learning freeze / rollback containment. It version-binds learning
update evidence, consumes safety signals, selects a last-known-safe target candidate, and emits only
Run/Freeze/Rollback/Resume-review candidates. It never executes a kill switch, learning update,
rollback, resume, deployment, routing, policy/model/trust mutation, permission grant, approval,
external action, or Action Success. Shadow/Canary state never becomes Production Authority.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json

class Decision(str,Enum): ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class ControlVerdict(str,Enum):
    RUN_CANDIDATE='RUN_CANDIDATE'; FREEZE_CANDIDATE='FREEZE_CANDIDATE'; FREEZE_ROLLBACK_CANDIDATE='FREEZE_ROLLBACK_CANDIDATE'; FREEZE_MAINTAIN_CANDIDATE='FREEZE_MAINTAIN_CANDIDATE'; RESUME_REVIEW_CANDIDATE='RESUME_REVIEW_CANDIDATE'; INVALID='INVALID'
class EngineState(str,Enum):
    LEARNING_RUN_CANDIDATE='LEARNING_RUN_CANDIDATE'; CRITICAL_FREEZE_ROLLBACK_CANDIDATE='CRITICAL_FREEZE_ROLLBACK_CANDIDATE'; ATTACK_FREEZE_CANDIDATE='ATTACK_FREEZE_CANDIDATE'; UNKNOWN_FREEZE_MAINTAIN_CANDIDATE='UNKNOWN_FREEZE_MAINTAIN_CANDIDATE'; ROLLBACK_TARGET_UNAVAILABLE_CANDIDATE='ROLLBACK_TARGET_UNAVAILABLE_CANDIDATE'; RESUME_REVIEW_REQUIRED_CANDIDATE='RESUME_REVIEW_REQUIRED_CANDIDATE'; INVALID='INVALID'
class NextAction(str,Enum):
    CONTINUE_LEARNING_CANDIDATE='CONTINUE_LEARNING_CANDIDATE'; FREEZE_AND_ROLLBACK_CANDIDATE='FREEZE_AND_ROLLBACK_CANDIDATE'; FREEZE_LEARNING_CANDIDATE='FREEZE_LEARNING_CANDIDATE'; MAINTAIN_FREEZE_CANDIDATE='MAINTAIN_FREEZE_CANDIDATE'; REQUIRE_ROLLBACK_TARGET_REVIEW_CANDIDATE='REQUIRE_ROLLBACK_TARGET_REVIEW_CANDIDATE'; REQUIRE_INDEPENDENT_REVIEW_CANDIDATE='REQUIRE_INDEPENDENT_REVIEW_CANDIDATE'; REVIEW_CONFIGURATION_CANDIDATE='REVIEW_CONFIGURATION_CANDIDATE'
class Escalation(str,Enum):
    NONE='NONE'; CRITICAL_REGRESSION='CRITICAL_REGRESSION'; ACTIVE_ATTACK='ACTIVE_ATTACK'; UNKNOWN_CAUSE='UNKNOWN_CAUSE'; ROLLBACK_TARGET_UNAVAILABLE='ROLLBACK_TARGET_UNAVAILABLE'; INDEPENDENT_REVIEW_REQUIRED='INDEPENDENT_REVIEW_REQUIRED'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'

@dataclass(frozen=True)
class LearningUpdate:
    update_id:str; version_id:str; update_type:str; verified:bool; committed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class SafetySignal:
    signal_id:str; critical_regression:bool; drift_detected:bool; attack_active:bool; cause_known:bool; safe_state_confirmed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class VersionRecord:
    version_id:str; verified_safe:bool; fingerprint:str; rollback_compatible:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class RollbackPoint:
    point_id:str; target_version:str; target_fingerprint:str; target_available:bool; integrity_verified:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class ResumeEvidence:
    independent_review_passed:bool; safety_reverified:bool; attack_cleared:bool; cause_resolved:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class FreezeRollbackRequest:
    request_id:str; update:LearningUpdate; safety:SafetySignal; version_history:tuple[VersionRecord,...]; rollback_point:RollbackPoint; resume:ResumeEvidence; binding:str; state_epoch:str
@dataclass(frozen=True)
class IncidentRecord:
    incident_type:str; signal_id:str; update_version:str; target_version:str; note:str
@dataclass(frozen=True)
class FreezeRollbackResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState; verdict:ControlVerdict; request_id:str; target_version:str|None; target_fingerprint:str|None; learning_freeze_candidate:bool; rollback_candidate:bool; resume_review_candidate:bool; incident_record:IncidentRecord; fallback_known_safe_candidate:bool; reasons:tuple[str,...]; next_gate_candidate:bool
    learning_update_executed:bool=False; learning_update_committed:bool=False; freeze_executed:bool=False; kill_switch_executed:bool=False; rollback_executed:bool=False; resume_executed:bool=False; target_version_restored:bool=False; model_updated:bool=False; policy_modified:bool=False; threshold_modified:bool=False; trust_modified:bool=False; hard_constraint_modified:bool=False; guardrail_modified:bool=False; deployment_executed:bool=False; routing_mutated:bool=False; incident_record_mutated:bool=False; reviewer_invoked:bool=False; tool_invoked:bool=False; file_write_executed:bool=False; network_send_executed:bool=False; dcsr_reconstruction_created_fact:bool=False; sender_authority_inherited:bool=False; sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False; permission_granted:bool=False; approval_executed:bool=False; authority_granted:bool=False; stop_executed:bool=False; action_executed:bool=False; plan_committed:bool=False; publish_executed:bool=False; external_write_performed:bool=False; world_truth_proven:bool=False; domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedFreezeRollbackState:
    request:FreezeRollbackRequest; result:FreezeRollbackResult; update_fingerprint:str; safety_fingerprint:str; history_fingerprint:str; rollback_fingerprint:str; resume_fingerprint:str; request_context_fingerprint:str; result_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class FreezeRollbackDelta:
    update_changed:bool; safety_changed:bool; history_changed:bool; rollback_changed:bool; resume_changed:bool; request_context_changed:bool; from_manifest_fingerprint:str; to_manifest_fingerprint:str
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
    update=LearningUpdate('UPD-161-A','model-v8','MODEL',True,False,b,e)
    history=(
        VersionRecord('model-v6',True,sha256(b'model-v6').hexdigest(),True,b,e),
        VersionRecord('model-v7',True,sha256(b'model-v7').hexdigest(),True,b,e),
        VersionRecord('model-v8',False,sha256(b'model-v8').hexdigest(),True,b,e),
    )
    rb=RollbackPoint('RB-161-A','model-v7',sha256(b'model-v7').hexdigest(),True,True,b,e)
    safety=SafetySignal('SIG-161-A',False,False,False,True,True,b,e)
    resume=ResumeEvidence(False,False,True,True,b,e)
    return FreezeRollbackRequest('FR-161-A',update,safety,history,rb,resume,b,e)

def _incident(kind,q,target,note): return IncidentRecord(kind,q.safety.signal_id,q.update.version_id,target or '',note)
def _invalid(reason):
    inc=IncidentRecord('INVALID','','','',reason)
    return FreezeRollbackResult(Decision.HOLD,NextAction.REVIEW_CONFIGURATION_CANDIDATE,Escalation.INVALID_CONFIGURATION,EngineState.INVALID,ControlVerdict.INVALID,'',None,None,True,False,False,inc,False,(reason,'CANDIDATE_ONLY_NO_FREEZE_ROLLBACK_RESUME_UPDATE_POLICY_MODEL_TRUST_OR_EXTERNAL_ACTION_EXECUTION'),False)

def _validate(q):
    if not q.request_id or not q.binding or not q.state_epoch: return 'EMPTY_REQUEST_CONTEXT'
    parts=((q.update,'LEARNING_UPDATE'),(q.safety,'SAFETY_SIGNAL'),(q.rollback_point,'ROLLBACK_POINT'),(q.resume,'RESUME_EVIDENCE'))
    for x,n in parts:
        if x.binding!=q.binding or x.state_epoch!=q.state_epoch: return n+'_BINDING_MISMATCH'
    if not q.version_history: return 'EMPTY_VERSION_HISTORY'
    for v in q.version_history:
        if v.binding!=q.binding or v.state_epoch!=q.state_epoch: return 'VERSION_HISTORY_BINDING_MISMATCH'
        if not v.version_id or len(v.fingerprint)!=64: return 'INVALID_VERSION_RECORD'
    if not q.update.update_id or not q.update.version_id or not q.update.update_type: return 'INVALID_UPDATE'
    if q.update.committed: return 'PRECOMMITTED_UPDATE_NOT_ACCEPTED'
    if not q.safety.signal_id: return 'INVALID_SAFETY_SIGNAL'
    if not q.rollback_point.point_id or not q.rollback_point.target_version or len(q.rollback_point.target_fingerprint)!=64: return 'INVALID_ROLLBACK_POINT'
    return None

def _target_status(q):
    matches=[v for v in q.version_history if v.version_id==q.rollback_point.target_version]
    if len(matches)!=1: return False,None
    v=matches[0]
    ok=(v.verified_safe and v.rollback_compatible and q.rollback_point.target_available and q.rollback_point.integrity_verified and v.fingerprint==q.rollback_point.target_fingerprint)
    return ok,v

def evaluate(q):
    bad=_validate(q)
    if bad: return _invalid(bad)
    target_ok,target=_target_status(q)
    target_version=q.rollback_point.target_version if target_ok else None
    target_fp=q.rollback_point.target_fingerprint if target_ok else None
    common=('SAFETY_SIGNAL_IS_EVIDENCE_NOT_TRUTH','KNOWN_SAFE_VERSION_IS_TARGET_CANDIDATE_NOT_ROLLBACK_EXECUTION','FREEZE_CANDIDATE_IS_NOT_KILL_SWITCH_EXECUTION','RESUME_REQUIRES_INDEPENDENT_REVIEW_CANDIDATE','SHADOW_CANARY_STATE_HAS_NO_PRODUCTION_AUTHORITY','DCSR_RECONSTRUCTION_DOES_NOT_CREATE_TRUTH_PERMISSION_SAFETY_PROOF_AUTHORITY_ACTION_OR_SUCCESS')
    # Critical regression has highest containment precedence.
    if q.safety.critical_regression:
        if not target_ok:
            inc=_incident('CRITICAL_REGRESSION',q,None,'critical regression; rollback target unavailable or unverifiable')
            return FreezeRollbackResult(Decision.DENY,NextAction.REQUIRE_ROLLBACK_TARGET_REVIEW_CANDIDATE,Escalation.ROLLBACK_TARGET_UNAVAILABLE,EngineState.ROLLBACK_TARGET_UNAVAILABLE_CANDIDATE,ControlVerdict.FREEZE_MAINTAIN_CANDIDATE,q.request_id,None,None,True,False,False,inc,False,('CRITICAL_REGRESSION_FREEZE_REQUIRED','ROLLBACK_TARGET_NOT_VERIFIED')+common,True)
        inc=_incident('CRITICAL_REGRESSION',q,target_version,'freeze and rollback candidate to last-known-safe version')
        return FreezeRollbackResult(Decision.HOLD,NextAction.FREEZE_AND_ROLLBACK_CANDIDATE,Escalation.CRITICAL_REGRESSION,EngineState.CRITICAL_FREEZE_ROLLBACK_CANDIDATE,ControlVerdict.FREEZE_ROLLBACK_CANDIDATE,q.request_id,target_version,target_fp,True,True,False,inc,True,('CRITICAL_REGRESSION_FREEZE_AND_ROLLBACK_CANDIDATE','LAST_KNOWN_SAFE_TARGET_SELECTED')+common,True)
    # Active attack freezes learning; rollback target is available as fallback candidate only.
    if q.safety.attack_active:
        inc=_incident('ACTIVE_ATTACK',q,target_version,'freeze learning while attack remains active')
        return FreezeRollbackResult(Decision.HOLD,NextAction.FREEZE_LEARNING_CANDIDATE,Escalation.ACTIVE_ATTACK,EngineState.ATTACK_FREEZE_CANDIDATE,ControlVerdict.FREEZE_CANDIDATE,q.request_id,target_version,target_fp,True,False,False,inc,target_ok,('ACTIVE_ATTACK_FREEZE_CANDIDATE',)+common,True)
    # Unknown cause or unconfirmed safe state remains frozen fail-closed.
    if (not q.safety.cause_known) or (not q.safety.safe_state_confirmed) or q.safety.drift_detected:
        esc=Escalation.UNKNOWN_CAUSE
        inc=_incident('UNCONFIRMED_SAFETY',q,target_version,'maintain freeze until cause and safe state are independently resolved')
        return FreezeRollbackResult(Decision.HOLD,NextAction.MAINTAIN_FREEZE_CANDIDATE,esc,EngineState.UNKNOWN_FREEZE_MAINTAIN_CANDIDATE,ControlVerdict.FREEZE_MAINTAIN_CANDIDATE,q.request_id,target_version,target_fp,True,False,False,inc,target_ok,('SAFETY_NOT_CONFIRMED_MAINTAIN_FREEZE_CANDIDATE',)+common,True)
    # If a previous incident is resolved, resume is still gated by independent review evidence.
    if q.resume.independent_review_passed or q.resume.safety_reverified:
        if q.resume.independent_review_passed and q.resume.safety_reverified and q.resume.attack_cleared and q.resume.cause_resolved:
            inc=_incident('RESUME_REVIEW',q,target_version,'independent review evidence supports resume candidate only')
            return FreezeRollbackResult(Decision.ALLOW,NextAction.REQUIRE_INDEPENDENT_REVIEW_CANDIDATE,Escalation.INDEPENDENT_REVIEW_REQUIRED,EngineState.RESUME_REVIEW_REQUIRED_CANDIDATE,ControlVerdict.RESUME_REVIEW_CANDIDATE,q.request_id,target_version,target_fp,False,False,True,inc,target_ok,('RESUME_REVIEW_PASSED_CANDIDATE_ONLY','NO_AUTOMATIC_RESUME')+common,True)
        inc=_incident('RESUME_REVIEW',q,target_version,'resume evidence incomplete')
        return FreezeRollbackResult(Decision.HOLD,NextAction.REQUIRE_INDEPENDENT_REVIEW_CANDIDATE,Escalation.INDEPENDENT_REVIEW_REQUIRED,EngineState.RESUME_REVIEW_REQUIRED_CANDIDATE,ControlVerdict.RESUME_REVIEW_CANDIDATE,q.request_id,target_version,target_fp,True,False,True,inc,target_ok,('RESUME_EVIDENCE_INCOMPLETE_MAINTAIN_FREEZE',)+common,True)
    # Normal learning: verified update may continue as candidate, not execution/commit.
    if not q.update.verified:
        inc=_incident('UNVERIFIED_UPDATE',q,target_version,'unverified learning update held')
        return FreezeRollbackResult(Decision.HOLD,NextAction.MAINTAIN_FREEZE_CANDIDATE,Escalation.UNKNOWN_CAUSE,EngineState.UNKNOWN_FREEZE_MAINTAIN_CANDIDATE,ControlVerdict.FREEZE_MAINTAIN_CANDIDATE,q.request_id,target_version,target_fp,True,False,False,inc,target_ok,('UNVERIFIED_UPDATE_HELD',)+common,True)
    inc=_incident('NORMAL',q,target_version,'verified update may continue as non-executing candidate')
    return FreezeRollbackResult(Decision.ALLOW,NextAction.CONTINUE_LEARNING_CANDIDATE,Escalation.NONE,EngineState.LEARNING_RUN_CANDIDATE,ControlVerdict.RUN_CANDIDATE,q.request_id,target_version,target_fp,False,False,False,inc,target_ok,('VERIFIED_UPDATE_RUN_CANDIDATE','NO_LEARNING_UPDATE_COMMIT')+common,True)

def default_evaluation(): return evaluate(default_request())

def prepare_state(q,binding,state_epoch):
    if binding!=q.binding or state_epoch!=q.state_epoch: raise ValueError('PREPARE_BINDING_MISMATCH')
    r=evaluate(q)
    vals=(_fp(q.update),_fp(q.safety),_fp(q.version_history),_fp(q.rollback_point),_fp(q.resume),_fp((q.request_id,q.binding,q.state_epoch)),_fp(r))
    integ=_fp(vals+(binding,state_epoch))
    return PreparedFreezeRollbackState(q,r,*vals,integ,binding,state_epoch)

def evaluate_prepared(st,*,integrity_validated,current_update_fingerprint,current_safety_fingerprint,current_history_fingerprint,current_rollback_fingerprint,current_resume_fingerprint,current_request_context_fingerprint,current_result_fingerprint):
    cur=(current_update_fingerprint,current_safety_fingerprint,current_history_fingerprint,current_rollback_fingerprint,current_resume_fingerprint,current_request_context_fingerprint,current_result_fingerprint)
    exp=(st.update_fingerprint,st.safety_fingerprint,st.history_fingerprint,st.rollback_fingerprint,st.resume_fingerprint,st.request_context_fingerprint,st.result_fingerprint)
    if not integrity_validated or cur!=exp or _fp(exp+(st.binding,st.state_epoch))!=st.integrity_fingerprint: return _invalid('PREPARED_STATE_INTEGRITY_FAILURE')
    return st.result

def make_delta(a,b):
    return FreezeRollbackDelta(a.update_fingerprint!=b.update_fingerprint,a.safety_fingerprint!=b.safety_fingerprint,a.history_fingerprint!=b.history_fingerprint,a.rollback_fingerprint!=b.rollback_fingerprint,a.resume_fingerprint!=b.resume_fingerprint,a.request_context_fingerprint!=b.request_context_fingerprint,a.integrity_fingerprint,b.integrity_fingerprint)

def plan_missing_only(a,b):
    d=make_delta(a,b); names=[]
    if d.update_changed:names.append('LEARNING_UPDATE')
    if d.safety_changed:names.append('SAFETY_SIGNAL')
    if d.history_changed:names.append('VERSION_HISTORY')
    if d.rollback_changed:names.append('ROLLBACK_POINT')
    if d.resume_changed:names.append('RESUME_EVIDENCE')
    if d.request_context_changed:names.append('REQUEST_CONTEXT')
    return MissingOnlyPlan(tuple(names),len(_canon({'from':d.from_manifest_fingerprint,'to':d.to_manifest_fingerprint,'missing':names})),False)
