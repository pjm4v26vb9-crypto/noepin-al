\
"""NOEPIN AL 160 — Shadow-Mode Comparison Engine — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-160
DCSR: DIRECT INTEGRATION / 直接統合.

Pure shadow comparison evaluator. Stable and Shadow receive the same canonical request evidence,
but Shadow cannot issue execution Permit or acquire Production Authority. Decision/Reason deltas are
compared against observed Outcome evidence. Critical permissiveness deltas produce Manual Review
Candidate; bounded safe improvement produces Canary Candidate; secret requests fail closed without
content export. No deployment, routing, permit issuance, promotion, rollback, policy/model mutation,
file/network write, tool invocation, approval, external action, or Action Success is executed here.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json

class Decision(str,Enum): ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class ShadowVerdict(str,Enum):
    MATCH_CANDIDATE='MATCH_CANDIDATE'; CANARY_CANDIDATE='CANARY_CANDIDATE'; MANUAL_REVIEW_CANDIDATE='MANUAL_REVIEW_CANDIDATE'; CONTAINMENT_CANDIDATE='CONTAINMENT_CANDIDATE'; INVALID='INVALID'
class EngineState(str,Enum):
    MATCHED_SHADOW_CANDIDATE='MATCHED_SHADOW_CANDIDATE'; IMPROVEMENT_CANARY_CANDIDATE='IMPROVEMENT_CANARY_CANDIDATE'; CRITICAL_REVIEW_CANDIDATE='CRITICAL_REVIEW_CANDIDATE'; SECRET_CONTAINMENT_CANDIDATE='SECRET_CONTAINMENT_CANDIDATE'; PERMIT_VIOLATION_CANDIDATE='PERMIT_VIOLATION_CANDIDATE'; INVALID='INVALID'
class NextAction(str,Enum):
    CONTINUE_SHADOW_EVALUATION_CANDIDATE='CONTINUE_SHADOW_EVALUATION_CANDIDATE'; CONTINUE_CANARY_CANDIDATE='CONTINUE_CANARY_CANDIDATE'; REQUIRE_MANUAL_REVIEW_CANDIDATE='REQUIRE_MANUAL_REVIEW_CANDIDATE'; CONTAIN_SECRET_CANDIDATE='CONTAIN_SECRET_CANDIDATE'; REJECT_SHADOW_PERMIT_CANDIDATE='REJECT_SHADOW_PERMIT_CANDIDATE'; REVIEW_CONFIGURATION_CANDIDATE='REVIEW_CONFIGURATION_CANDIDATE'
class Escalation(str,Enum):
    NONE='NONE'; CRITICAL_DECISION_DIFF='CRITICAL_DECISION_DIFF'; UNSAFE_SHADOW_DIFF='UNSAFE_SHADOW_DIFF'; SECRET_REQUEST='SECRET_REQUEST'; SHADOW_PERMIT_VIOLATION='SHADOW_PERMIT_VIOLATION'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'

@dataclass(frozen=True)
class LiveRequest:
    request_id:str; task_class:str; sensitive:bool; canonical_input_hash:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class DecisionRecord:
    decision_id:str; decision:Decision; reason_code:str; risk_score:float; permit_requested:bool; permit_issued:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class Outcome:
    outcome_id:str; observed:bool; safe:bool; utility_score:float; binding:str; state_epoch:str
@dataclass(frozen=True)
class ShadowPolicy:
    prohibit_shadow_permit:bool; prohibit_secret_export:bool; canary_gain_threshold:float; critical_risk_delta:float; binding:str; state_epoch:str
@dataclass(frozen=True)
class ShadowComparisonRequest:
    comparison_id:str; live_request:LiveRequest; stable:DecisionRecord; shadow:DecisionRecord; outcome:Outcome; policy:ShadowPolicy; binding:str; state_epoch:str
@dataclass(frozen=True)
class DecisionDiff:
    stable_decision:str; shadow_decision:str; decision_changed:bool; reason_changed:bool; risk_delta:float
@dataclass(frozen=True)
class ShadowComparisonResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState; verdict:ShadowVerdict; comparison_id:str; decision_diff:DecisionDiff; potential_gain:float; potential_risk:float; candidate_case:bool; canary_candidate:bool; reviewer_required:bool; secret_containment_candidate:bool; permit_rejected:bool; fallback_stable_candidate:bool; reasons:tuple[str,...]; next_gate_candidate:bool
    shadow_permit_issued:bool=False; deployment_executed:bool=False; promotion_executed:bool=False; rollback_executed:bool=False; routing_mutated:bool=False; stable_decision_mutated:bool=False; shadow_decision_mutated:bool=False; policy_modified:bool=False; hard_constraint_modified:bool=False; guardrail_modified:bool=False; model_updated:bool=False; secret_exported:bool=False; reviewer_invoked:bool=False; tool_invoked:bool=False; file_write_executed:bool=False; network_send_executed:bool=False; dcsr_reconstruction_created_fact:bool=False; sender_authority_inherited:bool=False; sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False; permission_granted:bool=False; approval_executed:bool=False; authority_granted:bool=False; stop_executed:bool=False; action_executed:bool=False; plan_committed:bool=False; publish_executed:bool=False; external_write_performed:bool=False; world_truth_proven:bool=False; domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedShadowState:
    request:ShadowComparisonRequest; result:ShadowComparisonResult; live_request_fingerprint:str; stable_fingerprint:str; shadow_fingerprint:str; outcome_fingerprint:str; policy_fingerprint:str; request_context_fingerprint:str; result_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class ShadowDelta:
    live_request_changed:bool; stable_changed:bool; shadow_changed:bool; outcome_changed:bool; policy_changed:bool; request_context_changed:bool; from_manifest_fingerprint:str; to_manifest_fingerprint:str
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
    live=LiveRequest('LIVE-160-A','GENERAL',False,sha256(b'canonical-input-160').hexdigest(),b,e)
    stable=DecisionRecord('STABLE-160-A',Decision.HOLD,'NEEDS_MORE_EVIDENCE',0.42,False,False,b,e)
    shadow=DecisionRecord('SHADOW-160-A',Decision.ALLOW,'SUFFICIENT_EVIDENCE',0.38,False,False,b,e)
    outcome=Outcome('OUT-160-A',True,True,0.91,b,e)
    policy=ShadowPolicy(True,True,0.05,0.25,b,e)
    return ShadowComparisonRequest('CMP-160-A',live,stable,shadow,outcome,policy,b,e)

def _empty_diff(): return DecisionDiff('','',False,False,0.0)
def _invalid(reason):
    return ShadowComparisonResult(Decision.HOLD,NextAction.REVIEW_CONFIGURATION_CANDIDATE,Escalation.INVALID_CONFIGURATION,EngineState.INVALID,ShadowVerdict.INVALID,'',_empty_diff(),0.0,0.0,False,False,False,False,False,True,(reason,'NO_PERMIT_DEPLOYMENT_PROMOTION_ROLLBACK_ROUTING_POLICY_MODEL_OR_EXTERNAL_ACTION_EXECUTION'),False)

def _validate(q):
    if not q.comparison_id or not q.binding or not q.state_epoch: return 'EMPTY_REQUEST_CONTEXT'
    for x,n in ((q.live_request,'LIVE_REQUEST'),(q.stable,'STABLE_DECISION'),(q.shadow,'SHADOW_DECISION'),(q.outcome,'OUTCOME'),(q.policy,'SHADOW_POLICY')):
        if x.binding!=q.binding or x.state_epoch!=q.state_epoch: return n+'_BINDING_MISMATCH'
    if not q.live_request.request_id or not q.live_request.canonical_input_hash: return 'INVALID_LIVE_REQUEST'
    for d,n in ((q.stable,'STABLE'),(q.shadow,'SHADOW')):
        if not d.decision_id or not d.reason_code: return 'INVALID_'+n+'_DECISION'
        if not (0.0 <= d.risk_score <= 1.0): return 'INVALID_'+n+'_RISK_SCORE'
    if not (0.0 <= q.outcome.utility_score <= 1.0): return 'INVALID_OUTCOME_UTILITY'
    if not (0.0 <= q.policy.canary_gain_threshold <= 1.0): return 'INVALID_CANARY_GAIN_THRESHOLD'
    if not (0.0 <= q.policy.critical_risk_delta <= 1.0): return 'INVALID_CRITICAL_RISK_DELTA'
    return None

def evaluate(q):
    bad=_validate(q)
    if bad: return _invalid(bad)
    diff=DecisionDiff(q.stable.decision.value,q.shadow.decision.value,q.stable.decision!=q.shadow.decision,q.stable.reason_code!=q.shadow.reason_code,q.shadow.risk_score-q.stable.risk_score)
    common=('SHADOW_EVIDENCE_IS_NOT_TRUTH','SHADOW_HAS_NO_PRODUCTION_AUTHORITY','SHADOW_PERMIT_CANNOT_BE_ISSUED','CANDIDATE_DOES_NOT_EXECUTE_DEPLOYMENT_PROMOTION_ROLLBACK_OR_ROUTING','DCSR_RECONSTRUCTION_DOES_NOT_CREATE_TRUTH_PERMISSION_SAFETY_PROOF_AUTHORITY_ACTION_OR_SUCCESS')
    if q.policy.prohibit_shadow_permit and (q.shadow.permit_requested or q.shadow.permit_issued):
        return ShadowComparisonResult(Decision.DENY,NextAction.REJECT_SHADOW_PERMIT_CANDIDATE,Escalation.SHADOW_PERMIT_VIOLATION,EngineState.PERMIT_VIOLATION_CANDIDATE,ShadowVerdict.CONTAINMENT_CANDIDATE,q.comparison_id,diff,0.0,max(0.0,diff.risk_delta),True,False,True,False,True,True,('SHADOW_PERMIT_REQUEST_OR_ISSUE_REJECTED',)+common,True)
    if q.live_request.sensitive and q.policy.prohibit_secret_export:
        return ShadowComparisonResult(Decision.HOLD,NextAction.CONTAIN_SECRET_CANDIDATE,Escalation.SECRET_REQUEST,EngineState.SECRET_CONTAINMENT_CANDIDATE,ShadowVerdict.CONTAINMENT_CANDIDATE,q.comparison_id,diff,0.0,0.0,True,False,True,True,False,True,('SENSITIVE_REQUEST_COMPARISON_CONTAINED','NO_SECRET_EXPORT'),*common,True)
    rank={Decision.ALLOW:0,Decision.HOLD:1,Decision.DENY:2}
    permissiveness=rank[q.stable.decision]-rank[q.shadow.decision]
    potential_risk=max(0.0,permissiveness/2.0,max(0.0,-diff.risk_delta))
    potential_gain=max(0.0,q.outcome.utility_score-q.shadow.risk_score) if q.outcome.observed and q.outcome.safe else 0.0
    if q.stable.decision==Decision.DENY and q.shadow.decision==Decision.ALLOW:
        return ShadowComparisonResult(Decision.HOLD,NextAction.REQUIRE_MANUAL_REVIEW_CANDIDATE,Escalation.CRITICAL_DECISION_DIFF,EngineState.CRITICAL_REVIEW_CANDIDATE,ShadowVerdict.MANUAL_REVIEW_CANDIDATE,q.comparison_id,diff,0.0,max(potential_risk,1.0),True,False,True,False,False,True,('CRITICAL_DENY_TO_ALLOW_DIFF_REQUIRES_MANUAL_REVIEW',)+common,True)
    if permissiveness>0 and (not q.outcome.observed or not q.outcome.safe):
        return ShadowComparisonResult(Decision.HOLD,NextAction.REQUIRE_MANUAL_REVIEW_CANDIDATE,Escalation.UNSAFE_SHADOW_DIFF,EngineState.CRITICAL_REVIEW_CANDIDATE,ShadowVerdict.MANUAL_REVIEW_CANDIDATE,q.comparison_id,diff,0.0,potential_risk,True,False,True,False,False,True,('PERMISSIVE_SHADOW_DIFF_NOT_SUPPORTED_BY_SAFE_OUTCOME',)+common,True)
    if permissiveness>0 and q.outcome.observed and q.outcome.safe and potential_gain>=q.policy.canary_gain_threshold and abs(diff.risk_delta)<=q.policy.critical_risk_delta:
        return ShadowComparisonResult(Decision.ALLOW,NextAction.CONTINUE_CANARY_CANDIDATE,Escalation.NONE,EngineState.IMPROVEMENT_CANARY_CANDIDATE,ShadowVerdict.CANARY_CANDIDATE,q.comparison_id,diff,potential_gain,potential_risk,True,True,False,False,False,False,('SAFE_OUTCOME_SUPPORTS_BOUNDED_SHADOW_IMPROVEMENT','CANARY_CANDIDATE_ONLY')+common,True)
    if not diff.decision_changed and not diff.reason_changed:
        return ShadowComparisonResult(Decision.ALLOW,NextAction.CONTINUE_SHADOW_EVALUATION_CANDIDATE,Escalation.NONE,EngineState.MATCHED_SHADOW_CANDIDATE,ShadowVerdict.MATCH_CANDIDATE,q.comparison_id,diff,0.0,0.0,False,False,False,False,False,False,('STABLE_AND_SHADOW_DECISIONS_MATCH',)+common,True)
    return ShadowComparisonResult(Decision.HOLD,NextAction.REQUIRE_MANUAL_REVIEW_CANDIDATE,Escalation.NONE,EngineState.CRITICAL_REVIEW_CANDIDATE,ShadowVerdict.MANUAL_REVIEW_CANDIDATE,q.comparison_id,diff,potential_gain,potential_risk,True,False,True,False,False,True,('NONCRITICAL_DECISION_OR_REASON_DIFF_REQUIRES_REVIEW',)+common,True)

def default_evaluation(): return evaluate(default_request())

def prepare_state(q,binding,state_epoch):
    if binding!=q.binding or state_epoch!=q.state_epoch: raise ValueError('PREPARED_BINDING_MISMATCH')
    r=evaluate(q)
    pieces=(_fp(q.live_request),_fp(q.stable),_fp(q.shadow),_fp(q.outcome),_fp(q.policy),_fp((q.comparison_id,q.binding,q.state_epoch)),_fp(r))
    integ=_fp(pieces+(binding,state_epoch))
    return PreparedShadowState(q,r,*pieces,integ,binding,state_epoch)

def evaluate_prepared(st,*,integrity_validated,current_live_request_fingerprint,current_stable_fingerprint,current_shadow_fingerprint,current_outcome_fingerprint,current_policy_fingerprint,current_request_context_fingerprint,current_result_fingerprint):
    if not integrity_validated: return _invalid('PREPARED_INTEGRITY_NOT_VALIDATED')
    cur=(current_live_request_fingerprint,current_stable_fingerprint,current_shadow_fingerprint,current_outcome_fingerprint,current_policy_fingerprint,current_request_context_fingerprint,current_result_fingerprint)
    exp=(st.live_request_fingerprint,st.stable_fingerprint,st.shadow_fingerprint,st.outcome_fingerprint,st.policy_fingerprint,st.request_context_fingerprint,st.result_fingerprint)
    if cur!=exp or _fp(exp+(st.binding,st.state_epoch))!=st.integrity_fingerprint: return _invalid('PREPARED_FINGERPRINT_MISMATCH')
    return st.result

def make_delta(a,b):
    fa=_fp((a.live_request_fingerprint,a.stable_fingerprint,a.shadow_fingerprint,a.outcome_fingerprint,a.policy_fingerprint,a.request_context_fingerprint))
    fb=_fp((b.live_request_fingerprint,b.stable_fingerprint,b.shadow_fingerprint,b.outcome_fingerprint,b.policy_fingerprint,b.request_context_fingerprint))
    return ShadowDelta(a.live_request_fingerprint!=b.live_request_fingerprint,a.stable_fingerprint!=b.stable_fingerprint,a.shadow_fingerprint!=b.shadow_fingerprint,a.outcome_fingerprint!=b.outcome_fingerprint,a.policy_fingerprint!=b.policy_fingerprint,a.request_context_fingerprint!=b.request_context_fingerprint,fa,fb)

def plan_missing_only(a,b):
    d=make_delta(a,b); ids=[]
    for flag,name in ((d.live_request_changed,'LIVE_REQUEST'),(d.stable_changed,'STABLE_DECISION'),(d.shadow_changed,'SHADOW_DECISION'),(d.outcome_changed,'OUTCOME'),(d.policy_changed,'SHADOW_POLICY'),(d.request_context_changed,'REQUEST_CONTEXT')):
        if flag: ids.append(name)
    meta=len(_canon({'missing':ids,'from':d.from_manifest_fingerprint,'to':d.to_manifest_fingerprint}))
    return MissingOnlyPlan(tuple(ids),meta,False)
