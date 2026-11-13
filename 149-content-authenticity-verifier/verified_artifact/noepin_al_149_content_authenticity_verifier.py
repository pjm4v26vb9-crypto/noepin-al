"""NOEPIN AL 149 — Content Authenticity Verifier — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-149
DCSR: AUXILIARY INTEGRATION / 補助統合.

Verifies content digest, signature-verification evidence, publisher identity, provenance chain and acquisition path.
Outputs are Authenticity State / Mismatch / Trust Adjustment candidates only. Authenticity Candidate != Truth.
Signature Evidence != Publisher Authority. Trust Adjustment Candidate != Trust Mutation. Quarantine Candidate != Quarantine Execution.
ALLOW Candidate != Policy/Tool Activation or Permission. HOLD/DENY Candidate != Stop Execution.
This core performs no network fetch, external signature-service call, content publication, policy activation, tool activation,
permission grant, trust-store mutation, quarantine action, or external write. DCSR reconstruction cannot create Truth,
Authority, Permission, Safety Proof, Approval, Action, or Action Success.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json

class Decision(str, Enum):
    ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class AuthenticityState(str, Enum):
    AUTHENTIC_CANDIDATE='AUTHENTIC_CANDIDATE'
    QUARANTINE_CANDIDATE='QUARANTINE_CANDIDATE'
    REVIEW_CANDIDATE='REVIEW_CANDIDATE'
    INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_USE_CANDIDATE='CONTINUE_USE_CANDIDATE'
    QUARANTINE_CONTENT_CANDIDATE='QUARANTINE_CONTENT_CANDIDATE'
    REVIEW_AUTHENTICITY_CANDIDATE='REVIEW_AUTHENTICITY_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; HASH_MISMATCH='HASH_MISMATCH'; HASH_MISSING='HASH_MISSING'
    SIGNATURE_INVALID='SIGNATURE_INVALID'; SIGNATURE_MISSING='SIGNATURE_MISSING'; SIGNATURE_STALE='SIGNATURE_STALE'
    PUBLISHER_MISMATCH='PUBLISHER_MISMATCH'; PROVENANCE_INVALID='PROVENANCE_INVALID'
    ACQUISITION_PATH_MISMATCH='ACQUISITION_PATH_MISMATCH'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'
class ContentClass(str, Enum):
    GENERAL='GENERAL'; POLICY='POLICY'; TOOL_DEFINITION='TOOL_DEFINITION'; RESEARCH='RESEARCH'; CONFIG='CONFIG'

@dataclass(frozen=True)
class ContentArtifact:
    content_id:str; content:str; content_class:ContentClass; critical:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class SignatureEvidence:
    signature_id:str; present:bool; verified:bool; signer_publisher:str; signed_content_sha256:str
    stale:bool; verification_method:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class ProvenanceMetadata:
    publisher_id:str; chain_ids:tuple[str,...]; chain_verified:bool; acquisition_path:str
    registered_acquisition_paths:tuple[str,...]; binding:str; state_epoch:str
@dataclass(frozen=True)
class PublisherExpectation:
    expected_publisher_id:str; expected_content_sha256:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class AuthenticityRequest:
    request_id:str; content:ContentArtifact; signature:SignatureEvidence; provenance:ProvenanceMetadata
    expected:PublisherExpectation; binding:str; state_epoch:str
@dataclass(frozen=True)
class AuthenticityResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; authenticity_state:AuthenticityState
    content_id:str; observed_content_sha256:str; mismatch:tuple[str,...]; trust_adjustment_candidate:int
    reasons:tuple[str,...]; trace:tuple[str,...]; next_gate_candidate:bool
    authenticity_promoted_to_truth:bool=False; signature_evidence_promoted_to_publisher_authority:bool=False
    trust_adjustment_applied:bool=False; quarantine_executed:bool=False; content_used:bool=False
    policy_applied:bool=False; tool_definition_activated:bool=False; content_published:bool=False
    external_send_executed:bool=False; external_verification_service_called:bool=False; tool_invoked:bool=False
    policy_modified:bool=False; trust_store_modified:bool=False; dlp_replaced:bool=False
    authentication_replaced:bool=False; encryption_replaced:bool=False; dcsr_reconstruction_created_fact:bool=False
    sender_authority_inherited:bool=False; sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False
    permission_granted:bool=False; approval_executed:bool=False; authority_granted:bool=False
    stop_executed:bool=False; action_executed:bool=False; plan_committed:bool=False; external_write_performed:bool=False
    world_truth_proven:bool=False; domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedAuthenticityState:
    request:AuthenticityRequest; result:AuthenticityResult; content_fingerprint:str; signature_fingerprint:str
    provenance_fingerprint:str; expectation_fingerprint:str; outcome_fingerprint:str; integrity_fingerprint:str
    binding:str; state_epoch:str
@dataclass(frozen=True)
class AuthenticityDelta:
    content_changed:bool; signature_changed:bool; provenance_changed:bool; expectation_changed:bool
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
def _content_sha(content:str): return sha256(content.encode('utf-8')).hexdigest()

def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'; content='NOEPIN AL 149 canonical policy content'
    digest=_content_sha(content)
    c=ContentArtifact('CONTENT-149-A',content,ContentClass.POLICY,True,b,e)
    s=SignatureEvidence('SIG-149-A',True,True,'NOEPIN',digest,False,'OFFLINE_VERIFIED_SIGNATURE_EVIDENCE',b,e)
    p=ProvenanceMetadata('NOEPIN',('SRC-149-A','DIST-149-A'),True,'notion://canonical/149',('notion://canonical/149',),b,e)
    x=PublisherExpectation('NOEPIN',digest,b,e)
    return AuthenticityRequest('REQ-149',c,s,p,x,b,e)

def _invalid(req,reason):
    observed=_content_sha(getattr(req.content,'content',''))
    return AuthenticityResult(Decision.HOLD,NextAction.REVIEW_AUTHENTICITY_CANDIDATE,Escalation.INVALID_CONFIGURATION,
        AuthenticityState.INVALID,getattr(req.content,'content_id',''),observed,(reason,),0,
        (reason,'NO_CONTENT_USE_EXECUTION','NO_AUTHORITY_PROMOTION'),(),False)

def _validate(req):
    if not req.request_id or not req.binding or not req.state_epoch: return 'EMPTY_REQUEST_CONTEXT'
    c=req.content; s=req.signature; p=req.provenance; x=req.expected
    if c.binding!=req.binding or c.state_epoch!=req.state_epoch: return 'CONTENT_BINDING_MISMATCH'
    if s.binding!=req.binding or s.state_epoch!=req.state_epoch: return 'SIGNATURE_BINDING_MISMATCH'
    if p.binding!=req.binding or p.state_epoch!=req.state_epoch: return 'PROVENANCE_BINDING_MISMATCH'
    if x.binding!=req.binding or x.state_epoch!=req.state_epoch: return 'EXPECTATION_BINDING_MISMATCH'
    if not c.content_id: return 'EMPTY_CONTENT_ID'
    if s.present and (not s.signature_id or not s.verification_method): return 'INVALID_SIGNATURE_EVIDENCE'
    if len(set(p.chain_ids))!=len(p.chain_ids) or any(not z for z in p.chain_ids): return 'INVALID_PROVENANCE_CHAIN'
    if len(set(p.registered_acquisition_paths))!=len(p.registered_acquisition_paths): return 'DUPLICATE_ACQUISITION_PATH'
    if not x.expected_publisher_id: return 'EMPTY_EXPECTED_PUBLISHER'
    return None

def evaluate(req):
    bad=_validate(req)
    if bad: return _invalid(req,bad)
    c,s,p,x=req.content,req.signature,req.provenance,req.expected
    observed=_content_sha(c.content)
    mismatch=[]; trace=[f'CONTENT:{c.content_id}',f'CLASS:{c.content_class.value}',f'CRITICAL:{c.critical}',f'PUBLISHER:{p.publisher_id}']
    if x.expected_content_sha256 and observed!=x.expected_content_sha256: mismatch.append('EXPECTED_HASH_MISMATCH')
    if s.present and s.signed_content_sha256 and observed!=s.signed_content_sha256: mismatch.append('SIGNED_HASH_MISMATCH')
    if not x.expected_content_sha256: mismatch.append('EXPECTED_HASH_MISSING')
    if p.publisher_id!=x.expected_publisher_id: mismatch.append('PROVENANCE_PUBLISHER_MISMATCH')
    if s.present and s.signer_publisher!=x.expected_publisher_id: mismatch.append('SIGNER_PUBLISHER_MISMATCH')
    if not p.chain_verified: mismatch.append('PROVENANCE_CHAIN_UNVERIFIED')
    if p.registered_acquisition_paths and p.acquisition_path not in p.registered_acquisition_paths: mismatch.append('ACQUISITION_PATH_MISMATCH')

    # Strong integrity/publisher failures are quarantine candidates. No quarantine execution occurs here.
    if 'EXPECTED_HASH_MISMATCH' in mismatch or 'SIGNED_HASH_MISMATCH' in mismatch:
        return AuthenticityResult(Decision.DENY,NextAction.QUARANTINE_CONTENT_CANDIDATE,Escalation.HASH_MISMATCH,
            AuthenticityState.QUARANTINE_CANDIDATE,c.content_id,observed,tuple(mismatch),-3,
            ('CONTENT_HASH_MISMATCH','QUARANTINE_IS_CANDIDATE_ONLY','NO_CONTENT_USE_EXECUTION'),tuple(trace),True)
    if 'PROVENANCE_PUBLISHER_MISMATCH' in mismatch or 'SIGNER_PUBLISHER_MISMATCH' in mismatch:
        return AuthenticityResult(Decision.DENY,NextAction.QUARANTINE_CONTENT_CANDIDATE,Escalation.PUBLISHER_MISMATCH,
            AuthenticityState.QUARANTINE_CANDIDATE,c.content_id,observed,tuple(mismatch),-3,
            ('PUBLISHER_IDENTITY_MISMATCH','NO_PUBLISHER_AUTHORITY_PROMOTION'),tuple(trace),True)
    if s.present and not s.verified:
        return AuthenticityResult(Decision.DENY,NextAction.QUARANTINE_CONTENT_CANDIDATE,Escalation.SIGNATURE_INVALID,
            AuthenticityState.QUARANTINE_CANDIDATE,c.content_id,observed,tuple(mismatch),-3,
            ('SIGNATURE_VERIFICATION_EVIDENCE_INVALID','NO_POLICY_OR_TOOL_ACTIVATION'),tuple(trace),True)
    if s.present and s.stale:
        return AuthenticityResult(Decision.HOLD,NextAction.REVIEW_AUTHENTICITY_CANDIDATE,Escalation.SIGNATURE_STALE,
            AuthenticityState.REVIEW_CANDIDATE,c.content_id,observed,tuple(mismatch),-1,
            ('SIGNATURE_EVIDENCE_STALE','REVERIFY_BEFORE_USE_CANDIDATE'),tuple(trace),True)
    if not p.chain_verified:
        return AuthenticityResult(Decision.DENY if c.critical else Decision.HOLD,
            NextAction.QUARANTINE_CONTENT_CANDIDATE if c.critical else NextAction.REVIEW_AUTHENTICITY_CANDIDATE,
            Escalation.PROVENANCE_INVALID,AuthenticityState.QUARANTINE_CANDIDATE if c.critical else AuthenticityState.REVIEW_CANDIDATE,
            c.content_id,observed,tuple(mismatch),-2,('PROVENANCE_CHAIN_NOT_VERIFIED','NO_TRUST_MUTATION'),tuple(trace),True)
    if 'ACQUISITION_PATH_MISMATCH' in mismatch:
        return AuthenticityResult(Decision.DENY if c.critical else Decision.HOLD,
            NextAction.QUARANTINE_CONTENT_CANDIDATE if c.critical else NextAction.REVIEW_AUTHENTICITY_CANDIDATE,
            Escalation.ACQUISITION_PATH_MISMATCH,AuthenticityState.QUARANTINE_CANDIDATE if c.critical else AuthenticityState.REVIEW_CANDIDATE,
            c.content_id,observed,tuple(mismatch),-2,('ACQUISITION_PATH_NOT_REGISTERED','NO_CONTENT_USE_EXECUTION'),tuple(trace),True)
    if not s.present:
        return AuthenticityResult(Decision.HOLD,NextAction.REVIEW_AUTHENTICITY_CANDIDATE,Escalation.SIGNATURE_MISSING,
            AuthenticityState.REVIEW_CANDIDATE,c.content_id,observed,tuple(mismatch),-1 if c.critical else 0,
            (('CRITICAL_SIGNATURE_MISSING' if c.critical else 'SIGNATURE_MISSING_REVIEW'),
             'HOLD_IS_CANDIDATE_NOT_STOP_EXECUTION','NO_CONTENT_USE_EXECUTION'),tuple(trace),True)
    if not x.expected_content_sha256:
        return AuthenticityResult(Decision.HOLD,NextAction.REVIEW_AUTHENTICITY_CANDIDATE,Escalation.HASH_MISSING,
            AuthenticityState.REVIEW_CANDIDATE,c.content_id,observed,tuple(mismatch),0,
            ('EXPECTED_HASH_MISSING','REVIEW_BEFORE_USE_CANDIDATE'),tuple(trace),True)
    return AuthenticityResult(Decision.ALLOW,NextAction.CONTINUE_USE_CANDIDATE,Escalation.NONE,
        AuthenticityState.AUTHENTIC_CANDIDATE,c.content_id,observed,tuple(mismatch),2,
        ('HASH_MATCH','SIGNATURE_EVIDENCE_VERIFIED','PUBLISHER_MATCH','PROVENANCE_CHAIN_VERIFIED','ACQUISITION_PATH_MATCH',
         'AUTHENTICITY_IS_CANDIDATE_NOT_TRUTH','TRUST_ADJUSTMENT_IS_CANDIDATE_ONLY','NO_CONTENT_USE_EXECUTION'),tuple(trace),True)

def default_evaluation(): return evaluate(default_request())

def prepare_state(req,binding,state_epoch):
    if binding!=req.binding or state_epoch!=req.state_epoch: raise ValueError('PREPARE_BINDING_MISMATCH')
    result=evaluate(req); cf=_fp(req.content); sf=_fp(req.signature); pf=_fp(req.provenance); ef=_fp(req.expected); of=_fp(result)
    integ=_fp((cf,sf,pf,ef,of,binding,state_epoch))
    return PreparedAuthenticityState(req,result,cf,sf,pf,ef,of,integ,binding,state_epoch)

def evaluate_prepared(state,*,integrity_validated,current_content_fingerprint,current_signature_fingerprint,
                      current_provenance_fingerprint,current_expectation_fingerprint,current_outcome_fingerprint):
    expected=_fp((state.content_fingerprint,state.signature_fingerprint,state.provenance_fingerprint,
                  state.expectation_fingerprint,state.outcome_fingerprint,state.binding,state.state_epoch))
    if (not integrity_validated or expected!=state.integrity_fingerprint or current_content_fingerprint!=state.content_fingerprint
        or current_signature_fingerprint!=state.signature_fingerprint or current_provenance_fingerprint!=state.provenance_fingerprint
        or current_expectation_fingerprint!=state.expectation_fingerprint or current_outcome_fingerprint!=state.outcome_fingerprint):
        return _invalid(state.request,'PREPARED_STATE_INTEGRITY_MISMATCH')
    return state.result

def make_delta(old,new):
    return AuthenticityDelta(old.content_fingerprint!=new.content_fingerprint,old.signature_fingerprint!=new.signature_fingerprint,
        old.provenance_fingerprint!=new.provenance_fingerprint,old.expectation_fingerprint!=new.expectation_fingerprint,
        old.integrity_fingerprint,new.integrity_fingerprint)

def plan_missing_only(old,new):
    ids=[]
    if old.content_fingerprint!=new.content_fingerprint: ids.append('CONTENT')
    if old.signature_fingerprint!=new.signature_fingerprint: ids.append('SIGNATURE_EVIDENCE')
    if old.provenance_fingerprint!=new.provenance_fingerprint: ids.append('PROVENANCE_METADATA')
    if old.expectation_fingerprint!=new.expectation_fingerprint: ids.append('PUBLISHER_EXPECTATION')
    return MissingOnlyPlan(tuple(ids),len(_canon(tuple(ids)))+64,False)
