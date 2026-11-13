"""NOEPIN AL 144 — Declassification Gate — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-144
DCSR: AUXILIARY INTEGRATION / 補助統合.

Evaluates a requested classification downgrade against sanitizer proof, residual sensitivity,
and approver authority evidence. This core never mutates classification, releases data, sends data,
executes approval, replaces authentication/encryption/Policy/DLP, or treats DCSR reconstruction as
Truth/Authority/Permission/Safety Proof. Declassification Decision != Classification Mutation.
Approver Evidence != Approval Execution. Sanitization Proof != universal Safety Proof.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json

class Decision(str, Enum):
    ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class EngineState(str, Enum):
    DECLASSIFICATION_ALLOWED_CANDIDATE='DECLASSIFICATION_ALLOWED_CANDIDATE'
    DECLASSIFICATION_BLOCKED_CANDIDATE='DECLASSIFICATION_BLOCKED_CANDIDATE'
    REVIEW_CANDIDATE='REVIEW_CANDIDATE'; INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_DECLASSIFICATION_CANDIDATE='CONTINUE_DECLASSIFICATION_CANDIDATE'
    BLOCK_DOWNGRADE_CANDIDATE='BLOCK_DOWNGRADE_CANDIDATE'
    REVIEW_CANDIDATE='REVIEW_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; PROOF_MISSING='PROOF_MISSING'; PROOF_INVALID='PROOF_INVALID'
    RESIDUAL_SENSITIVITY='RESIDUAL_SENSITIVITY'; AUTHORITY_INVALID='AUTHORITY_INVALID'
    CLASSIFICATION_INVALID='CLASSIFICATION_INVALID'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'
class Classification(str, Enum):
    PUBLIC='PUBLIC'; INTERNAL='INTERNAL'; CONFIDENTIAL='CONFIDENTIAL'; RESTRICTED='RESTRICTED'; SECRET='SECRET'

RANK={Classification.PUBLIC:0,Classification.INTERNAL:1,Classification.CONFIDENTIAL:2,Classification.RESTRICTED:3,Classification.SECRET:4}

@dataclass(frozen=True)
class SanitizationProof:
    proof_id:str; verified:bool; sanitizer_id:str; max_residual_sensitivity:float
    target_classification:Classification; provenance_ids:tuple[str,...]; binding:str; state_epoch:str

@dataclass(frozen=True)
class ApproverEvidence:
    approver_id:str; authority_verified:bool; permitted_from:tuple[Classification,...]
    permitted_to:tuple[Classification,...]; approval_binding:str; binding:str; state_epoch:str

@dataclass(frozen=True)
class DeclassificationRequest:
    request_id:str; data_id:str; current_classification:Classification; requested_classification:Classification
    residual_sensitivity:float; sanitization_proof:SanitizationProof|None; approver:ApproverEvidence|None
    binding:str; state_epoch:str; provenance_ids:tuple[str,...]=()

@dataclass(frozen=True)
class DeclassificationResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState
    current_classification:Classification; requested_classification:Classification
    residual_sensitivity:float; proof_verified:bool; approver_verified:bool; reasons:tuple[str,...]
    audit_proof:tuple[str,...]; next_gate_candidate:bool
    classification_mutated:bool=False; data_released:bool=False; external_send_executed:bool=False
    approval_executed:bool=False; approver_evidence_promoted_to_authority:bool=False
    sanitization_proof_promoted_to_universal_safety:bool=False; residual_score_promoted_to_truth:bool=False
    declassification_decision_promoted_to_permission:bool=False; tool_invoked:bool=False
    policy_modified:bool=False; dlp_replaced:bool=False; authentication_replaced:bool=False
    encryption_replaced:bool=False; dcsr_reconstruction_created_fact:bool=False
    sender_authority_inherited:bool=False; sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False
    permission_granted:bool=False; authority_granted:bool=False; stop_executed:bool=False
    action_executed:bool=False; plan_committed:bool=False; publish_executed:bool=False
    external_write_performed:bool=False; world_truth_proven:bool=False; domain_authority_promoted:bool=False
    safety_proven:bool=False; action_success:bool=False

@dataclass(frozen=True)
class PreparedDeclassificationState:
    request:DeclassificationRequest; result:DeclassificationResult; request_fingerprint:str
    proof_fingerprint:str; approver_fingerprint:str; outcome_fingerprint:str; integrity_fingerprint:str
    binding:str; state_epoch:str

@dataclass(frozen=True)
class DeclassificationDelta:
    request_changed:bool; proof_changed:bool; approver_changed:bool
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
    p=SanitizationProof('PROOF-144',True,'SAN-144',0.10,Classification.INTERNAL,('SRC-144-A',),b,e)
    a=ApproverEvidence('APPROVER-144',True,(Classification.CONFIDENTIAL,Classification.RESTRICTED,Classification.SECRET),(Classification.PUBLIC,Classification.INTERNAL,Classification.CONFIDENTIAL),'APPROVAL-BIND-144',b,e)
    return DeclassificationRequest('REQ-144','DATA-144-A',Classification.CONFIDENTIAL,Classification.INTERNAL,0.08,p,a,b,e,('SRC-144-A',))

def _invalid(req,reason):
    return DeclassificationResult(Decision.HOLD,NextAction.REVIEW_CANDIDATE,Escalation.INVALID_CONFIGURATION,EngineState.INVALID,
        req.current_classification,req.requested_classification,req.residual_sensitivity,False,False,
        (reason,'NO_CLASSIFICATION_MUTATION','NO_DATA_RELEASE'),(),False)

def _validate(req):
    if not req.request_id or not req.data_id or not req.binding or not req.state_epoch: return 'EMPTY_REQUEST_CONTEXT'
    if not (0.0 <= req.residual_sensitivity <= 1.0): return 'INVALID_RESIDUAL_SENSITIVITY'
    if len(set(req.provenance_ids))!=len(req.provenance_ids) or any(not x for x in req.provenance_ids): return 'INVALID_PROVENANCE'
    p=req.sanitization_proof
    if p is not None:
        if not p.proof_id or not p.sanitizer_id or p.binding!=req.binding or p.state_epoch!=req.state_epoch: return 'PROOF_BINDING_MISMATCH'
        if not (0.0 <= p.max_residual_sensitivity <= 1.0): return 'INVALID_PROOF_THRESHOLD'
        if len(set(p.provenance_ids))!=len(p.provenance_ids) or any(not x for x in p.provenance_ids): return 'INVALID_PROOF_PROVENANCE'
    a=req.approver
    if a is not None:
        if not a.approver_id or not a.approval_binding or a.binding!=req.binding or a.state_epoch!=req.state_epoch: return 'APPROVER_BINDING_MISMATCH'
        if len(set(a.permitted_from))!=len(a.permitted_from) or len(set(a.permitted_to))!=len(a.permitted_to): return 'DUPLICATE_APPROVER_SCOPE'
    return None

def evaluate(req):
    err=_validate(req)
    if err: return _invalid(req,err)
    cur=req.current_classification; target=req.requested_classification
    if RANK[target] >= RANK[cur]:
        return DeclassificationResult(Decision.HOLD,NextAction.REVIEW_CANDIDATE,Escalation.CLASSIFICATION_INVALID,EngineState.REVIEW_CANDIDATE,
            cur,target,req.residual_sensitivity,False,False,('REQUEST_IS_NOT_A_DOWNGRADE','NO_CLASSIFICATION_MUTATION'),(),False)
    p=req.sanitization_proof
    if p is None:
        return DeclassificationResult(Decision.DENY,NextAction.BLOCK_DOWNGRADE_CANDIDATE,Escalation.PROOF_MISSING,EngineState.DECLASSIFICATION_BLOCKED_CANDIDATE,
            cur,target,req.residual_sensitivity,False,False,('SANITIZATION_PROOF_REQUIRED','NO_CLASSIFICATION_MUTATION'),(),True)
    if not p.verified or RANK[p.target_classification] > RANK[target]:
        return DeclassificationResult(Decision.DENY,NextAction.BLOCK_DOWNGRADE_CANDIDATE,Escalation.PROOF_INVALID,EngineState.DECLASSIFICATION_BLOCKED_CANDIDATE,
            cur,target,req.residual_sensitivity,False,False,('SANITIZATION_PROOF_NOT_VERIFIED_FOR_REQUESTED_TARGET','NO_CLASSIFICATION_MUTATION'),(p.proof_id,),True)
    threshold=min(p.max_residual_sensitivity,0.20 if target==Classification.INTERNAL else 0.05 if target==Classification.PUBLIC else 0.35)
    if req.residual_sensitivity>threshold:
        return DeclassificationResult(Decision.HOLD,NextAction.REVIEW_CANDIDATE,Escalation.RESIDUAL_SENSITIVITY,EngineState.REVIEW_CANDIDATE,
            cur,target,req.residual_sensitivity,True,False,('RESIDUAL_SENSITIVITY_TOO_HIGH','PROOF_DOES_NOT_ERASE_RESIDUAL_RISK','NO_CLASSIFICATION_MUTATION'),(p.proof_id,),True)
    a=req.approver
    if a is None or not a.authority_verified or cur not in a.permitted_from or target not in a.permitted_to:
        return DeclassificationResult(Decision.DENY,NextAction.BLOCK_DOWNGRADE_CANDIDATE,Escalation.AUTHORITY_INVALID,EngineState.DECLASSIFICATION_BLOCKED_CANDIDATE,
            cur,target,req.residual_sensitivity,True,False,('APPROVER_AUTHORITY_NOT_VERIFIED_FOR_TRANSITION','APPROVER_EVIDENCE_IS_NOT_APPROVAL_EXECUTION','NO_CLASSIFICATION_MUTATION'),(p.proof_id,),True)
    audit=(p.proof_id,a.approval_binding,*p.provenance_ids,*req.provenance_ids)
    return DeclassificationResult(Decision.ALLOW,NextAction.CONTINUE_DECLASSIFICATION_CANDIDATE,Escalation.NONE,EngineState.DECLASSIFICATION_ALLOWED_CANDIDATE,
        cur,target,req.residual_sensitivity,True,True,
        ('SANITIZATION_PROOF_VERIFIED','RESIDUAL_SENSITIVITY_WITHIN_BOUND','APPROVER_AUTHORITY_EVIDENCE_VERIFIED','ALLOW_IS_CANDIDATE_NOT_CLASSIFICATION_MUTATION','NO_DATA_RELEASE'),
        tuple(dict.fromkeys(audit)),True)

def _request_fp(req):
    return _fp((req.request_id,req.data_id,req.current_classification,req.requested_classification,req.residual_sensitivity,req.binding,req.state_epoch,req.provenance_ids))
def _proof_fp(req): return _fp(req.sanitization_proof)
def _approver_fp(req): return _fp(req.approver)

def prepare_state(req,binding,state_epoch):
    if binding!=req.binding or state_epoch!=req.state_epoch: return None
    r=evaluate(req); rf=_request_fp(req); pf=_proof_fp(req); af=_approver_fp(req); of=_fp(r)
    integ=_fp((rf,pf,af,of,binding,state_epoch))
    return PreparedDeclassificationState(req,r,rf,pf,af,of,integ,binding,state_epoch)

def evaluate_prepared(st,*,integrity_validated,current_request_fingerprint,current_proof_fingerprint,current_approver_fingerprint,current_outcome_fingerprint):
    if st is None or not integrity_validated: return _invalid(default_request(),'PREPARED_STATE_NOT_VALIDATED')
    if _fp((st.request_fingerprint,st.proof_fingerprint,st.approver_fingerprint,st.outcome_fingerprint,st.binding,st.state_epoch))!=st.integrity_fingerprint:
        return _invalid(st.request,'PREPARED_STATE_INTEGRITY_MISMATCH')
    if current_request_fingerprint!=st.request_fingerprint or current_proof_fingerprint!=st.proof_fingerprint or current_approver_fingerprint!=st.approver_fingerprint or current_outcome_fingerprint!=st.outcome_fingerprint:
        return _invalid(st.request,'PREPARED_STATE_FINGERPRINT_MISMATCH')
    return st.result

def _manifest_fp(st): return _fp((st.request_fingerprint,st.proof_fingerprint,st.approver_fingerprint,st.outcome_fingerprint,st.binding,st.state_epoch))
def make_delta(old,new):
    return DeclassificationDelta(old.request_fingerprint!=new.request_fingerprint,old.proof_fingerprint!=new.proof_fingerprint,old.approver_fingerprint!=new.approver_fingerprint,_manifest_fp(old),_manifest_fp(new))
def plan_missing_only(old,new):
    ids=[]
    if old.request_fingerprint!=new.request_fingerprint: ids.append('REQUEST_CONTEXT')
    if old.proof_fingerprint!=new.proof_fingerprint: ids.append('SANITIZATION_PROOF')
    if old.approver_fingerprint!=new.approver_fingerprint: ids.append('APPROVER_EVIDENCE')
    meta=len(_canon(tuple(ids)))+96
    return MissingOnlyPlan(tuple(ids),meta,False)

def default_evaluation(): return evaluate(default_request())

if __name__=='__main__':
    print(json.dumps(_obj(default_evaluation()),ensure_ascii=False,sort_keys=True))
