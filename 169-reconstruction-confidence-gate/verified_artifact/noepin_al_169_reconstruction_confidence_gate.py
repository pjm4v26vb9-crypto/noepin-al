"""NOEPIN AL 169 — Reconstruction Confidence Gate — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-169
DCSR: DIRECT INTEGRATION / 直接統合.

Deterministic, side-effect-free final-validation evaluator for reconstructed-state candidates.
It combines expected fingerprint integrity, residual coverage, maximum reconstruction error,
Critical-element error, and expected-evidence completeness into an ALLOW/HOLD/DENY candidate.
Hash mismatch is DENY. Critical error, insufficient residual coverage, or missing Critical expected
evidence is HOLD. ALLOW is only a candidate to continue validation; it does not publish, promote,
write, grant authority, execute fallback, or prove truth/safety/action success.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str, Enum): ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class EngineState(str, Enum):
    RECONSTRUCTION_CONFIDENCE_CANDIDATE='RECONSTRUCTION_CONFIDENCE_CANDIDATE'
    FULL_ORIGINAL_RETENTION_CANDIDATE='FULL_ORIGINAL_RETENTION_CANDIDATE'
    INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_FINAL_VALIDATION_CANDIDATE='CONTINUE_FINAL_VALIDATION_CANDIDATE'
    RETAIN_FULL_ORIGINAL_CANDIDATE='RETAIN_FULL_ORIGINAL_CANDIDATE'
    REVIEW_INPUT_CANDIDATE='REVIEW_INPUT_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'; HASH_MISMATCH='HASH_MISMATCH'
    CRITICAL_ERROR_EXCEEDED='CRITICAL_ERROR_EXCEEDED'; COVERAGE_INSUFFICIENT='COVERAGE_INSUFFICIENT'
    EXPECTED_CRITICAL_EVIDENCE_MISSING='EXPECTED_CRITICAL_EVIDENCE_MISSING'; MAX_ERROR_EXCEEDED='MAX_ERROR_EXCEEDED'
    LENGTH_MISMATCH='LENGTH_MISMATCH'; INVALID_VALUE='INVALID_VALUE'

@dataclass(frozen=True)
class ReconstructionConfidenceRequest:
    request_id:str
    reconstructed_values:tuple[float,...]
    expected_values:tuple[float,...]
    expected_fingerprint:str
    residual_applied:int
    residual_expected:int
    minimum_residual_coverage:float
    maximum_error_threshold:float
    critical_error_threshold:float
    critical_indices:tuple[int,...]
    expected_critical_indices:tuple[int,...]
    require_expected_critical_evidence:bool
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class ReconstructionConfidenceResult:
    decision:Decision
    next_action:NextAction
    escalation:Escalation
    engine_state:EngineState
    request_id:str
    observed_fingerprint:str
    expected_fingerprint:str
    fingerprint_match:bool
    residual_coverage:float
    residual_coverage_sufficient:bool
    maximum_error:float
    maximum_error_within_threshold:bool
    critical_maximum_error:float
    critical_error_within_threshold:bool
    critical_expected_evidence_complete:bool
    confidence:float
    confidence_components:tuple[tuple[str,float],...]
    next_gate_candidate:bool
    reasons:tuple[str,...]
    reconstructed_values_mutated:bool=False
    authoritative_state_created:bool=False
    cached_state_promoted:bool=False
    reconstructed_state_promoted:bool=False
    partial_state_promoted:bool=False
    publish_executed:bool=False
    final_validation_committed:bool=False
    fallback_executed:bool=False
    original_deleted:bool=False
    tool_invoked:bool=False
    file_write_executed:bool=False
    network_send_executed:bool=False
    dcsr_reconstruction_created_fact:bool=False
    sender_authority_inherited:bool=False
    sender_intent_inherited:bool=False
    sender_agreement_inherited:bool=False
    permission_granted:bool=False
    approval_executed:bool=False
    authority_granted:bool=False
    stop_executed:bool=False
    action_executed:bool=False
    plan_committed:bool=False
    external_write_performed:bool=False
    world_truth_proven:bool=False
    domain_authority_promoted:bool=False
    safety_proven:bool=False
    action_success:bool=False

@dataclass(frozen=True)
class PreparedReconstructionConfidenceState:
    request:ReconstructionConfidenceRequest
    result:ReconstructionConfidenceResult
    reconstruction_fingerprint:str
    evidence_fingerprint:str
    config_fingerprint:str
    result_fingerprint:str
    integrity_fingerprint:str
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class ReconstructionConfidenceChange:
    reconstruction_changed:bool
    evidence_changed:bool
    config_changed:bool
    from_fingerprint:str
    to_fingerprint:str

@dataclass(frozen=True)
class MissingOnlyPlan:
    missing_or_changed_record_ids:tuple[str,...]
    metadata_bytes_required:int
    full_resend_required:bool


def _obj(v):
    if isinstance(v,Enum): return v.value
    if is_dataclass(v): return {f.name:_obj(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v,dict): return {str(k):_obj(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(tuple,list)): return [_obj(x) for x in v]
    if isinstance(v,float):
        if not math.isfinite(v): raise ValueError('non-finite float')
        return v
    return v

def _canon(v): return json.dumps(_obj(v),ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def _fp(v): return sha256(_canon(v)).hexdigest()
def _valid_number(v): return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(float(v))
def fingerprint_values(values): return _fp(tuple(float(x) for x in values))

def _invalid(q,reason,esc,decision=Decision.HOLD):
    return ReconstructionConfidenceResult(decision,NextAction.REVIEW_INPUT_CANDIDATE,esc,EngineState.INVALID,getattr(q,'request_id',''),'0'*64,getattr(q,'expected_fingerprint',''),False,0.0,False,0.0,False,0.0,False,False,0.0,(),False,(reason,'NO_AUTHORITATIVE_STATE_PROMOTION','FULL_ORIGINAL_RETENTION_REMAINS_CANDIDATE','DCSR_STATE_IS_NOT_AUTHORITATIVE_STATE'))

def _validate(q):
    if not q.request_id or not q.binding or not q.state_epoch: return ('EMPTY_REQUEST_CONTEXT',Escalation.INVALID_CONFIGURATION)
    if not q.reconstructed_values or not q.expected_values: return ('EMPTY_RECONSTRUCTION_OR_EXPECTED',Escalation.INVALID_CONFIGURATION)
    if len(q.reconstructed_values)!=len(q.expected_values): return ('LENGTH_MISMATCH',Escalation.LENGTH_MISMATCH)
    if any(not _valid_number(x) for x in q.reconstructed_values+q.expected_values): return ('INVALID_VALUE',Escalation.INVALID_VALUE)
    if len(q.expected_fingerprint)!=64 or any(c not in '0123456789abcdef' for c in q.expected_fingerprint.lower()): return ('INVALID_EXPECTED_FINGERPRINT',Escalation.INVALID_CONFIGURATION)
    if not isinstance(q.residual_applied,int) or isinstance(q.residual_applied,bool) or q.residual_applied<0: return ('INVALID_RESIDUAL_APPLIED',Escalation.INVALID_CONFIGURATION)
    if not isinstance(q.residual_expected,int) or isinstance(q.residual_expected,bool) or q.residual_expected<0: return ('INVALID_RESIDUAL_EXPECTED',Escalation.INVALID_CONFIGURATION)
    if q.residual_applied>q.residual_expected: return ('RESIDUAL_APPLIED_EXCEEDS_EXPECTED',Escalation.INVALID_CONFIGURATION)
    if not _valid_number(q.minimum_residual_coverage) or not 0.0<=float(q.minimum_residual_coverage)<=1.0: return ('INVALID_MINIMUM_COVERAGE',Escalation.INVALID_CONFIGURATION)
    if not _valid_number(q.maximum_error_threshold) or float(q.maximum_error_threshold)<0: return ('INVALID_MAX_ERROR_THRESHOLD',Escalation.INVALID_CONFIGURATION)
    if not _valid_number(q.critical_error_threshold) or float(q.critical_error_threshold)<0: return ('INVALID_CRITICAL_ERROR_THRESHOLD',Escalation.INVALID_CONFIGURATION)
    if len(set(q.critical_indices))!=len(q.critical_indices): return ('DUPLICATE_CRITICAL_INDEX',Escalation.INVALID_CONFIGURATION)
    if any((not isinstance(i,int) or isinstance(i,bool) or i<0 or i>=len(q.reconstructed_values)) for i in q.critical_indices): return ('INVALID_CRITICAL_INDEX',Escalation.INVALID_CONFIGURATION)
    if len(set(q.expected_critical_indices))!=len(q.expected_critical_indices): return ('DUPLICATE_EXPECTED_CRITICAL_INDEX',Escalation.INVALID_CONFIGURATION)
    if any((not isinstance(i,int) or isinstance(i,bool) or i<0 or i>=len(q.expected_values)) for i in q.expected_critical_indices): return ('INVALID_EXPECTED_CRITICAL_INDEX',Escalation.INVALID_CONFIGURATION)
    return None

def evaluate(q):
    bad=_validate(q)
    if bad:
        deny={Escalation.LENGTH_MISMATCH,Escalation.INVALID_VALUE}
        return _invalid(q,bad[0],bad[1],Decision.DENY if bad[1] in deny else Decision.HOLD)
    obs_fp=fingerprint_values(q.reconstructed_values)
    hash_match=(obs_fp==q.expected_fingerprint)
    errs=tuple(abs(float(a)-float(b)) for a,b in zip(q.reconstructed_values,q.expected_values))
    max_err=max(errs) if errs else 0.0
    crit_err=max((errs[i] for i in q.critical_indices),default=0.0)
    coverage=1.0 if q.residual_expected==0 else q.residual_applied/q.residual_expected
    coverage_ok=coverage>=float(q.minimum_residual_coverage)
    max_ok=max_err<=float(q.maximum_error_threshold)
    crit_ok=crit_err<=float(q.critical_error_threshold)
    critical_evidence_complete=(not q.require_expected_critical_evidence) or set(q.critical_indices).issubset(set(q.expected_critical_indices))
    # Confidence is an audit score only; it does not override hard gates.
    coverage_score=min(1.0,max(0.0,coverage))
    max_score=1.0 if q.maximum_error_threshold==0 and max_err==0 else (0.0 if q.maximum_error_threshold==0 else max(0.0,1.0-max_err/max(float(q.maximum_error_threshold),1e-12)))
    crit_score=1.0 if q.critical_error_threshold==0 and crit_err==0 else (0.0 if q.critical_error_threshold==0 else max(0.0,1.0-crit_err/max(float(q.critical_error_threshold),1e-12)))
    hash_score=1.0 if hash_match else 0.0
    evidence_score=1.0 if critical_evidence_complete else 0.0
    confidence=round((0.35*hash_score+0.2*coverage_score+0.15*max_score+0.2*crit_score+0.1*evidence_score),12)
    comps=(('hash',hash_score),('coverage',round(coverage_score,12)),('max_error',round(max_score,12)),('critical_error',round(crit_score,12)),('critical_evidence',evidence_score))
    if not hash_match:
        return ReconstructionConfidenceResult(Decision.DENY,NextAction.RETAIN_FULL_ORIGINAL_CANDIDATE,Escalation.HASH_MISMATCH,EngineState.FULL_ORIGINAL_RETENTION_CANDIDATE,q.request_id,obs_fp,q.expected_fingerprint,False,coverage,coverage_ok,max_err,max_ok,crit_err,crit_ok,critical_evidence_complete,confidence,comps,False,('EXPECTED_FINGERPRINT_MISMATCH','RECONSTRUCTED_STATE_NOT_AUTHORIZED','FULL_ORIGINAL_RETENTION_CANDIDATE','NO_PERMISSION_WRITE_DEPLOYMENT_OR_ACTION_EXECUTION'))
    if not critical_evidence_complete:
        return ReconstructionConfidenceResult(Decision.HOLD,NextAction.RETAIN_FULL_ORIGINAL_CANDIDATE,Escalation.EXPECTED_CRITICAL_EVIDENCE_MISSING,EngineState.FULL_ORIGINAL_RETENTION_CANDIDATE,q.request_id,obs_fp,q.expected_fingerprint,True,coverage,coverage_ok,max_err,max_ok,crit_err,crit_ok,False,confidence,comps,False,('EXPECTED_CRITICAL_EVIDENCE_MISSING','CRITICAL_RECONSTRUCTION_NOT_ALLOWED_TO_CONTINUE','FULL_ORIGINAL_RETENTION_CANDIDATE','NO_AUTHORITATIVE_STATE_PROMOTION'))
    if not crit_ok:
        return ReconstructionConfidenceResult(Decision.HOLD,NextAction.RETAIN_FULL_ORIGINAL_CANDIDATE,Escalation.CRITICAL_ERROR_EXCEEDED,EngineState.FULL_ORIGINAL_RETENTION_CANDIDATE,q.request_id,obs_fp,q.expected_fingerprint,True,coverage,coverage_ok,max_err,max_ok,crit_err,False,True,confidence,comps,False,('CRITICAL_ERROR_THRESHOLD_EXCEEDED','FULL_ORIGINAL_RETENTION_CANDIDATE','CONFIDENCE_DOES_NOT_OVERRIDE_HARD_GATES','NO_AUTHORITATIVE_STATE_PROMOTION'))
    if not coverage_ok:
        return ReconstructionConfidenceResult(Decision.HOLD,NextAction.RETAIN_FULL_ORIGINAL_CANDIDATE,Escalation.COVERAGE_INSUFFICIENT,EngineState.FULL_ORIGINAL_RETENTION_CANDIDATE,q.request_id,obs_fp,q.expected_fingerprint,True,coverage,False,max_err,max_ok,crit_err,True,True,confidence,comps,False,('RESIDUAL_COVERAGE_BELOW_THRESHOLD','FULL_ORIGINAL_RETENTION_CANDIDATE','CONFIDENCE_DOES_NOT_OVERRIDE_HARD_GATES','NO_AUTHORITATIVE_STATE_PROMOTION'))
    if not max_ok:
        return ReconstructionConfidenceResult(Decision.HOLD,NextAction.RETAIN_FULL_ORIGINAL_CANDIDATE,Escalation.MAX_ERROR_EXCEEDED,EngineState.FULL_ORIGINAL_RETENTION_CANDIDATE,q.request_id,obs_fp,q.expected_fingerprint,True,coverage,True,max_err,False,crit_err,True,True,confidence,comps,False,('MAXIMUM_ERROR_THRESHOLD_EXCEEDED','FULL_ORIGINAL_RETENTION_CANDIDATE','CONFIDENCE_DOES_NOT_OVERRIDE_HARD_GATES','NO_AUTHORITATIVE_STATE_PROMOTION'))
    return ReconstructionConfidenceResult(Decision.ALLOW,NextAction.CONTINUE_FINAL_VALIDATION_CANDIDATE,Escalation.NONE,EngineState.RECONSTRUCTION_CONFIDENCE_CANDIDATE,q.request_id,obs_fp,q.expected_fingerprint,True,coverage,True,max_err,True,crit_err,True,True,confidence,comps,True,('EXPECTED_FINGERPRINT_MATCHED','RESIDUAL_COVERAGE_SUFFICIENT','MAXIMUM_ERROR_WITHIN_THRESHOLD','CRITICAL_ERROR_WITHIN_THRESHOLD','EXPECTED_CRITICAL_EVIDENCE_COMPLETE','CONFIDENCE_IS_AUDIT_SCORE_NOT_AUTHORITY','NO_AUTHORITATIVE_STATE_PROMOTION_OR_PUBLICATION','NO_PERMISSION_WRITE_DEPLOYMENT_OR_ACTION_EXECUTION'))

def default_request():
    vals=tuple(round(((i*19)%257)/256.0,6) for i in range(512))
    return ReconstructionConfidenceRequest('RCG-169-A',vals,vals,fingerprint_values(vals),96,100,0.95,0.002,0.001,(0,7,31,127,255,511),(0,7,31,127,255,511),True,'DEFAULT-BINDING','EPOCH-1')
def default_evaluation(): return evaluate(default_request())

def _reconstruction_fp(q): return _fp(q.reconstructed_values)
def _evidence_fp(q): return _fp((q.expected_values,q.expected_fingerprint,q.residual_applied,q.residual_expected,q.critical_indices,q.expected_critical_indices))
def _config_fp(q): return _fp((q.minimum_residual_coverage,q.maximum_error_threshold,q.critical_error_threshold,q.require_expected_critical_evidence,q.binding,q.state_epoch))
def prepare_state(q,binding,state_epoch):
    if q.binding!=binding or q.state_epoch!=state_epoch:
        r=_invalid(q,'PREPARED_BINDING_MISMATCH',Escalation.INVALID_CONFIGURATION)
        return PreparedReconstructionConfidenceState(q,r,'0'*64,'0'*64,'0'*64,'0'*64,'0'*64,binding,state_epoch)
    r=evaluate(q); af=_reconstruction_fp(q); ef=_evidence_fp(q); cf=_config_fp(q); rf=_fp(r); integ=_fp((af,ef,cf,rf,binding,state_epoch))
    return PreparedReconstructionConfidenceState(q,r,af,ef,cf,rf,integ,binding,state_epoch)
def evaluate_prepared(st,*,integrity_validated,current_reconstruction_fingerprint,current_evidence_fingerprint,current_config_fingerprint,current_result_fingerprint):
    q=st.request
    if not integrity_validated: return _invalid(q,'PREPARED_INTEGRITY_NOT_VALIDATED',Escalation.INVALID_CONFIGURATION)
    if current_reconstruction_fingerprint!=st.reconstruction_fingerprint: return _invalid(q,'PREPARED_RECONSTRUCTION_FINGERPRINT_MISMATCH',Escalation.INVALID_CONFIGURATION)
    if current_evidence_fingerprint!=st.evidence_fingerprint: return _invalid(q,'PREPARED_EVIDENCE_FINGERPRINT_MISMATCH',Escalation.INVALID_CONFIGURATION)
    if current_config_fingerprint!=st.config_fingerprint: return _invalid(q,'PREPARED_CONFIG_FINGERPRINT_MISMATCH',Escalation.INVALID_CONFIGURATION)
    if current_result_fingerprint!=st.result_fingerprint: return _invalid(q,'PREPARED_RESULT_FINGERPRINT_MISMATCH',Escalation.INVALID_CONFIGURATION)
    if _fp((st.reconstruction_fingerprint,st.evidence_fingerprint,st.config_fingerprint,st.result_fingerprint,st.binding,st.state_epoch))!=st.integrity_fingerprint: return _invalid(q,'PREPARED_INTEGRITY_FINGERPRINT_MISMATCH',Escalation.INVALID_CONFIGURATION)
    return st.result

def make_delta(a,b):
    return ReconstructionConfidenceChange(a.reconstruction_fingerprint!=b.reconstruction_fingerprint,a.evidence_fingerprint!=b.evidence_fingerprint,a.config_fingerprint!=b.config_fingerprint,_fp((a.reconstruction_fingerprint,a.evidence_fingerprint,a.config_fingerprint)),_fp((b.reconstruction_fingerprint,b.evidence_fingerprint,b.config_fingerprint)))
def plan_missing_only(a,b):
    d=make_delta(a,b); ids=[]
    if d.reconstruction_changed: ids.append('RECONSTRUCTION_RESULT')
    if d.evidence_changed: ids.append('EXPECTED_EVIDENCE')
    if d.config_changed: ids.append('CONFIDENCE_GATE_CONFIG')
    return MissingOnlyPlan(tuple(ids),96+len(ids)*17,False)
