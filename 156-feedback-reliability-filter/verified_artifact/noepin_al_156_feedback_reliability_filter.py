"""NOEPIN AL 156 — Feedback Reliability Filter — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-156
DCSR: DIRECT INTEGRATION / 直接統合.

Pure evaluation core. Feedback evidence is weighted by source validity/reliability, independent outcome
corroboration, delay, conflict and interest. Self feedback is capped. Feedback proposing safety-policy
weakening requires strong independent evidence; insufficient evidence is not admitted to learning.
Invalid sources are rejected. Shadow/Canary safety regression can only emit a known-safe fallback
candidate. No learning update, policy/guardrail mutation, deployment, rollback, file/network write,
tool invocation, or external action is executed here. Accepted Weight != Learning Update; Feedback
Evidence != Truth; Source Reliability != Source Authority; Outcome Evidence != Action Success Proof;
Shadow/Canary State != Production Authority; DCSR reconstruction cannot create Truth, Domain
Authority, Permission, Safety Proof, Approval, Action, or Action Success.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json

class Decision(str, Enum):
    ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class EngineState(str, Enum):
    ACCEPTED_FEEDBACK_CANDIDATE='ACCEPTED_FEEDBACK_CANDIDATE'
    WEIGHT_LIMITED_CANDIDATE='WEIGHT_LIMITED_CANDIDATE'
    POLICY_WEAKENING_HOLD_CANDIDATE='POLICY_WEAKENING_HOLD_CANDIDATE'
    REJECTED_FEEDBACK_CANDIDATE='REJECTED_FEEDBACK_CANDIDATE'
    SAFETY_REGRESSION_FALLBACK_CANDIDATE='SAFETY_REGRESSION_FALLBACK_CANDIDATE'
    INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_LEARNING_CANDIDATE='CONTINUE_LEARNING_CANDIDATE'
    LIMIT_WEIGHT_CANDIDATE='LIMIT_WEIGHT_CANDIDATE'
    REQUIRE_EVIDENCE_CANDIDATE='REQUIRE_EVIDENCE_CANDIDATE'
    REJECT_FEEDBACK_CANDIDATE='REJECT_FEEDBACK_CANDIDATE'
    FALLBACK_KNOWN_SAFE_CANDIDATE='FALLBACK_KNOWN_SAFE_CANDIDATE'
    REVIEW_FEEDBACK_CANDIDATE='REVIEW_FEEDBACK_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; SELF_FEEDBACK_ONLY='SELF_FEEDBACK_ONLY'; INSUFFICIENT_POLICY_EVIDENCE='INSUFFICIENT_POLICY_EVIDENCE'; UNTRUSTED_SOURCE='UNTRUSTED_SOURCE'; CONFLICT_HIGH='CONFLICT_HIGH'; DELAY_HIGH='DELAY_HIGH'; SAFETY_REGRESSION='SAFETY_REGRESSION'; LOW_RELIABILITY='LOW_RELIABILITY'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'

@dataclass(frozen=True)
class Feedback:
    feedback_id:str; source_id:str; score:float; self_feedback:bool; proposes_policy_weakening:bool; rationale:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class SourceProfile:
    source_id:str; source_kind:str; identity_verified:bool; source_valid:bool; historical_reliability:float; conflict_of_interest:float; independent_from_target:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class OutcomeEvidence:
    evidence_id:str; independent_observed:bool; supports_feedback:bool; evidence_strength:float; corroboration_ids:tuple[str,...]; binding:str; state_epoch:str
@dataclass(frozen=True)
class FeedbackContext:
    delay_seconds:float; max_delay_seconds:float; conflict_score:float; minimum_accept_weight:float; required_policy_evidence:float; binding:str; state_epoch:str
@dataclass(frozen=True)
class ShadowCanaryState:
    state_id:str; stable_version:str; canary_version:str; shadow_version:str; safety_regression:bool; known_safe_version:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class FeedbackRequest:
    request_id:str; feedback:Feedback; source:SourceProfile; evidence:OutcomeEvidence; context:FeedbackContext; shadow:ShadowCanaryState; model_policy_version:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class FeedbackResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState; feedback_id:str; accepted_weight:float; rejected_feedback:bool; evidence_match:bool; fallback_known_safe_candidate:bool; fallback_version_candidate:str; reasons:tuple[str,...]; next_gate_candidate:bool
    learning_update_committed:bool=False; feedback_written_to_training:bool=False; online_learning_committed:bool=False; model_updated:bool=False; risk_model_mutated:bool=False; policy_modified:bool=False; hard_constraint_modified:bool=False; guardrail_modified:bool=False; source_authority_granted:bool=False; source_reliability_promoted_to_truth:bool=False; outcome_evidence_promoted_to_action_success:bool=False; canary_deployed:bool=False; shadow_promoted_to_production:bool=False; fallback_executed:bool=False; rollback_executed:bool=False; tool_invoked:bool=False; file_write_executed:bool=False; network_send_executed:bool=False; dcsr_reconstruction_created_fact:bool=False; sender_authority_inherited:bool=False; sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False; permission_granted:bool=False; approval_executed:bool=False; authority_granted:bool=False; stop_executed:bool=False; action_executed:bool=False; plan_committed:bool=False; publish_executed:bool=False; external_write_performed:bool=False; world_truth_proven:bool=False; domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedFeedbackState:
    request:FeedbackRequest; result:FeedbackResult; feedback_fingerprint:str; source_fingerprint:str; evidence_fingerprint:str; context_fingerprint:str; shadow_fingerprint:str; request_context_fingerprint:str; result_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class FeedbackDelta:
    feedback_changed:bool; source_changed:bool; evidence_changed:bool; context_changed:bool; shadow_changed:bool; request_context_changed:bool; from_manifest_fingerprint:str; to_manifest_fingerprint:str
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
def _clamp(v,lo=0.0,hi=1.0): return max(lo,min(hi,v))

def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    f=Feedback('FB-156-A','SRC-TRUSTED-USER',0.8,False,False,'observed safe successful outcome',b,e)
    s=SourceProfile('SRC-TRUSTED-USER','TRUSTED_USER',True,True,0.76,0.05,True,b,e)
    ev=OutcomeEvidence('EV-156-A',True,True,0.90,('OBS-A','OBS-B'),b,e)
    cx=FeedbackContext(30.0,3600.0,0.05,0.40,0.85,b,e)
    sh=ShadowCanaryState('SC-156-A','stable-v1','canary-v2','shadow-v2',False,'stable-v1',b,e)
    return FeedbackRequest('REQ-156-A',f,s,ev,cx,sh,'policy-v1',b,e)

def _invalid(reason):
    return FeedbackResult(Decision.HOLD,NextAction.REVIEW_FEEDBACK_CANDIDATE,Escalation.INVALID_CONFIGURATION,EngineState.INVALID,'',0.0,True,False,False,'',(reason,'NO_LEARNING_OR_POLICY_MUTATION','NO_EXTERNAL_ACTION_EXECUTION'),False)

def _validate(q):
    if not q.request_id or not q.model_policy_version or not q.binding or not q.state_epoch: return 'EMPTY_REQUEST_CONTEXT'
    for x,n in ((q.feedback,'FEEDBACK'),(q.source,'SOURCE'),(q.evidence,'EVIDENCE'),(q.context,'CONTEXT'),(q.shadow,'SHADOW')):
        if x.binding!=q.binding or x.state_epoch!=q.state_epoch: return n+'_BINDING_MISMATCH'
    if not q.feedback.feedback_id or not q.feedback.source_id or q.feedback.source_id!=q.source.source_id: return 'INVALID_FEEDBACK_SOURCE_BINDING'
    if not (-1.0 <= q.feedback.score <= 1.0): return 'INVALID_FEEDBACK_SCORE'
    if not (0.0 <= q.source.historical_reliability <= 1.0) or not (0.0 <= q.source.conflict_of_interest <= 1.0): return 'INVALID_SOURCE_PROFILE'
    if not (0.0 <= q.evidence.evidence_strength <= 1.0): return 'INVALID_EVIDENCE_STRENGTH'
    c=q.context
    if c.delay_seconds<0 or c.max_delay_seconds<=0 or not (0<=c.conflict_score<=1) or not (0<c.minimum_accept_weight<=1) or not (0<c.required_policy_evidence<=1): return 'INVALID_CONTEXT'
    if not q.shadow.known_safe_version: return 'MISSING_KNOWN_SAFE_VERSION'
    return None

def evaluate(q):
    err=_validate(q)
    if err: return _invalid(err)
    f,s,e,c,sh=q.feedback,q.source,q.evidence,q.context,q.shadow
    base_reasons=['FEEDBACK_EVIDENCE_IS_NOT_TRUTH','SOURCE_RELIABILITY_IS_NOT_SOURCE_AUTHORITY','OUTCOME_EVIDENCE_IS_NOT_ACTION_SUCCESS_PROOF','ACCEPTED_WEIGHT_IS_NOT_LEARNING_UPDATE','SHADOW_CANARY_HAVE_NO_PRODUCTION_AUTHORITY','NO_LEARNING_POLICY_DEPLOYMENT_OR_EXTERNAL_EXECUTION']
    if sh.safety_regression:
        return FeedbackResult(Decision.DENY,NextAction.FALLBACK_KNOWN_SAFE_CANDIDATE,Escalation.SAFETY_REGRESSION,EngineState.SAFETY_REGRESSION_FALLBACK_CANDIDATE,f.feedback_id,0.0,True,e.independent_observed and e.supports_feedback,True,sh.known_safe_version,tuple(base_reasons+['SAFETY_REGRESSION_FALLBACK_CANDIDATE_ONLY']),False)
    if (not s.source_valid) or (not s.identity_verified):
        return FeedbackResult(Decision.DENY,NextAction.REJECT_FEEDBACK_CANDIDATE,Escalation.UNTRUSTED_SOURCE,EngineState.REJECTED_FEEDBACK_CANDIDATE,f.feedback_id,0.0,True,False,False,'',tuple(base_reasons+['INVALID_OR_UNVERIFIED_SOURCE_REJECTED']),False)
    match=e.independent_observed and e.supports_feedback
    contradiction=e.independent_observed and not e.supports_feedback
    if f.proposes_policy_weakening and (not e.independent_observed or not e.supports_feedback or e.evidence_strength<c.required_policy_evidence):
        return FeedbackResult(Decision.HOLD,NextAction.REQUIRE_EVIDENCE_CANDIDATE,Escalation.INSUFFICIENT_POLICY_EVIDENCE,EngineState.POLICY_WEAKENING_HOLD_CANDIDATE,f.feedback_id,0.0,True,match,False,'',tuple(base_reasons+['POLICY_WEAKENING_REQUIRES_STRONG_INDEPENDENT_EVIDENCE','INSUFFICIENT_EVIDENCE_NOT_ADMITTED_TO_LEARNING']),False)
    w=s.historical_reliability
    if match: w += 0.20*e.evidence_strength
    if contradiction: w *= max(0.05,1.0-0.85*e.evidence_strength)
    w *= max(0.0,1.0-0.50*s.conflict_of_interest)
    w *= max(0.0,1.0-0.60*c.conflict_score)
    delay_ratio=min(1.0,c.delay_seconds/c.max_delay_seconds)
    w *= (1.0-0.45*delay_ratio)
    esc=Escalation.NONE; action=NextAction.CONTINUE_LEARNING_CANDIDATE; state=EngineState.ACCEPTED_FEEDBACK_CANDIDATE; dec=Decision.ALLOW
    rs=list(base_reasons)
    if f.self_feedback and not e.independent_observed:
        w=min(w,0.25); esc=Escalation.SELF_FEEDBACK_ONLY; action=NextAction.LIMIT_WEIGHT_CANDIDATE; state=EngineState.WEIGHT_LIMITED_CANDIDATE; dec=Decision.HOLD; rs.append('SELF_FEEDBACK_WEIGHT_CAPPED')
    elif c.delay_seconds>c.max_delay_seconds:
        w*=0.5; esc=Escalation.DELAY_HIGH; action=NextAction.LIMIT_WEIGHT_CANDIDATE; state=EngineState.WEIGHT_LIMITED_CANDIDATE; dec=Decision.HOLD; rs.append('DELAY_REDUCES_WEIGHT')
    elif contradiction or c.conflict_score>=0.70:
        w*=0.5; esc=Escalation.CONFLICT_HIGH; action=NextAction.LIMIT_WEIGHT_CANDIDATE; state=EngineState.WEIGHT_LIMITED_CANDIDATE; dec=Decision.HOLD; rs.append('CONFLICT_REDUCES_WEIGHT')
    w=round(_clamp(w),6)
    if dec==Decision.ALLOW and w<c.minimum_accept_weight:
        dec=Decision.HOLD; esc=Escalation.LOW_RELIABILITY; action=NextAction.LIMIT_WEIGHT_CANDIDATE; state=EngineState.WEIGHT_LIMITED_CANDIDATE; rs.append('WEIGHT_BELOW_ACCEPTANCE_THRESHOLD')
    if match: rs.append('INDEPENDENT_OUTCOME_MATCH_WEIGHT_INCREASE')
    if f.proposes_policy_weakening: rs.append('POLICY_WEAKENING_EVIDENCE_THRESHOLD_SATISFIED_CANDIDATE_ONLY')
    return FeedbackResult(dec,action,esc,state,f.feedback_id,w,False,match,False,'',tuple(rs),dec==Decision.ALLOW)

def default_evaluation(): return evaluate(default_request())

def prepare_state(q,binding,state_epoch):
    if binding!=q.binding or state_epoch!=q.state_epoch: raise ValueError('PREPARE_BINDING_MISMATCH')
    r=evaluate(q)
    ff=_fp(q.feedback); sf=_fp(q.source); ef=_fp(q.evidence); cf=_fp(q.context); shf=_fp(q.shadow); rcf=_fp((q.request_id,q.model_policy_version,q.binding,q.state_epoch)); rf=_fp(r)
    integ=_fp((ff,sf,ef,cf,shf,rcf,rf,binding,state_epoch))
    return PreparedFeedbackState(q,r,ff,sf,ef,cf,shf,rcf,rf,integ,binding,state_epoch)

def evaluate_prepared(s,*,integrity_validated,current_feedback_fingerprint,current_source_fingerprint,current_evidence_fingerprint,current_context_fingerprint,current_shadow_fingerprint,current_request_context_fingerprint,current_result_fingerprint):
    if not integrity_validated: return _invalid('PREPARED_INTEGRITY_NOT_VALIDATED')
    vals=(current_feedback_fingerprint,current_source_fingerprint,current_evidence_fingerprint,current_context_fingerprint,current_shadow_fingerprint,current_request_context_fingerprint,current_result_fingerprint)
    exp=(s.feedback_fingerprint,s.source_fingerprint,s.evidence_fingerprint,s.context_fingerprint,s.shadow_fingerprint,s.request_context_fingerprint,s.result_fingerprint)
    if vals!=exp: return _invalid('PREPARED_FINGERPRINT_MISMATCH')
    if _fp((s.feedback_fingerprint,s.source_fingerprint,s.evidence_fingerprint,s.context_fingerprint,s.shadow_fingerprint,s.request_context_fingerprint,s.result_fingerprint,s.binding,s.state_epoch))!=s.integrity_fingerprint: return _invalid('PREPARED_INTEGRITY_MISMATCH')
    return s.result

def make_delta(a,b):
    return FeedbackDelta(a.feedback_fingerprint!=b.feedback_fingerprint,a.source_fingerprint!=b.source_fingerprint,a.evidence_fingerprint!=b.evidence_fingerprint,a.context_fingerprint!=b.context_fingerprint,a.shadow_fingerprint!=b.shadow_fingerprint,a.request_context_fingerprint!=b.request_context_fingerprint,_fp((a.feedback_fingerprint,a.source_fingerprint,a.evidence_fingerprint,a.context_fingerprint,a.shadow_fingerprint,a.request_context_fingerprint)),_fp((b.feedback_fingerprint,b.source_fingerprint,b.evidence_fingerprint,b.context_fingerprint,b.shadow_fingerprint,b.request_context_fingerprint)))
def plan_missing_only(a,b):
    ids=[]
    if a.feedback_fingerprint!=b.feedback_fingerprint: ids.append('FEEDBACK')
    if a.source_fingerprint!=b.source_fingerprint: ids.append('SOURCE_PROFILE')
    if a.evidence_fingerprint!=b.evidence_fingerprint: ids.append('OUTCOME_EVIDENCE')
    if a.context_fingerprint!=b.context_fingerprint: ids.append('FEEDBACK_CONTEXT')
    if a.shadow_fingerprint!=b.shadow_fingerprint: ids.append('SHADOW_CANARY_STATE')
    if a.request_context_fingerprint!=b.request_context_fingerprint: ids.append('REQUEST_CONTEXT')
    return MissingOnlyPlan(tuple(ids),len(_canon(ids))+64,False)
