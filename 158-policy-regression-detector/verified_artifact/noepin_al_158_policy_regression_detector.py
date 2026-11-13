"""NOEPIN AL 158 — Policy Regression Detector — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-158
DCSR: DIRECT INTEGRATION / 直接統合.

Pure differential evaluation core for old/new policy, rule, or model decision records.
It identifies DENY->ALLOW critical safety regressions, HOLD->ALLOW review regressions,
ALLOW->DENY usability regressions, decision/reason changes, expected-decision mismatches,
and missing regression-corpus evidence. Critical safety regression emits only a release-block
candidate and known-safe fallback candidate; no release, block, rollback, deployment, policy
mutation, model update, reviewer invocation, tool call, file/network write, or external action
is executed here. Regression Evidence != Truth; Release Gate != Release/Block Execution;
Expected Decision != Permission; Fallback Candidate != Rollback Execution; Shadow/Canary State
!= Production Authority; DCSR reconstruction cannot create Truth, Domain Authority, Permission,
Safety Proof, Approval, Action, or Action Success.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json

class Decision(str, Enum):
    ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class ReleaseGate(str, Enum):
    PASS_CANDIDATE='PASS_CANDIDATE'
    PASS_WITH_USABILITY_REVIEW_CANDIDATE='PASS_WITH_USABILITY_REVIEW_CANDIDATE'
    REVIEW_REQUIRED_CANDIDATE='REVIEW_REQUIRED_CANDIDATE'
    BLOCK_CANDIDATE='BLOCK_CANDIDATE'
class EngineState(str, Enum):
    REGRESSION_FREE_CANDIDATE='REGRESSION_FREE_CANDIDATE'
    USABILITY_REGRESSION_RECORDED_CANDIDATE='USABILITY_REGRESSION_RECORDED_CANDIDATE'
    SAFETY_REVIEW_REQUIRED_CANDIDATE='SAFETY_REVIEW_REQUIRED_CANDIDATE'
    CRITICAL_REGRESSION_BLOCK_CANDIDATE='CRITICAL_REGRESSION_BLOCK_CANDIDATE'
    CORPUS_INCOMPLETE_CANDIDATE='CORPUS_INCOMPLETE_CANDIDATE'
    SAFETY_REGRESSION_FALLBACK_CANDIDATE='SAFETY_REGRESSION_FALLBACK_CANDIDATE'
    INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_RELEASE_FLOW_CANDIDATE='CONTINUE_RELEASE_FLOW_CANDIDATE'
    REVIEW_USABILITY_REGRESSION_CANDIDATE='REVIEW_USABILITY_REGRESSION_CANDIDATE'
    REQUIRE_SAFETY_REVIEW_CANDIDATE='REQUIRE_SAFETY_REVIEW_CANDIDATE'
    BLOCK_RELEASE_CANDIDATE='BLOCK_RELEASE_CANDIDATE'
    COMPLETE_CORPUS_CANDIDATE='COMPLETE_CORPUS_CANDIDATE'
    FALLBACK_KNOWN_SAFE_CANDIDATE='FALLBACK_KNOWN_SAFE_CANDIDATE'
    REVIEW_CONFIGURATION_CANDIDATE='REVIEW_CONFIGURATION_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'
    USABILITY_REGRESSION='USABILITY_REGRESSION'
    HOLD_TO_ALLOW_REVIEW='HOLD_TO_ALLOW_REVIEW'
    REASON_CHANGE_REVIEW='REASON_CHANGE_REVIEW'
    EXPECTED_DECISION_MISMATCH='EXPECTED_DECISION_MISMATCH'
    CRITICAL_SAFETY_REGRESSION='CRITICAL_SAFETY_REGRESSION'
    CORPUS_INCOMPLETE='CORPUS_INCOMPLETE'
    SAFETY_REGRESSION='SAFETY_REGRESSION'
    INVALID_CONFIGURATION='INVALID_CONFIGURATION'
class DiffClass(str, Enum):
    NONE='NONE'
    CRITICAL_SAFETY='CRITICAL_SAFETY'
    SAFETY_REVIEW='SAFETY_REVIEW'
    USABILITY='USABILITY'
    REASON_ONLY='REASON_ONLY'
    EXPECTED_MISMATCH='EXPECTED_MISMATCH'

@dataclass(frozen=True)
class VersionPair:
    old_version:str; new_version:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class RegressionCase:
    case_id:str; category:str; expected_decision:Decision; old_decision:Decision; new_decision:Decision; old_reason:str; new_reason:str; critical:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class ShadowCanaryState:
    state_id:str; stable_version:str; canary_version:str; shadow_version:str; safety_regression:bool; known_safe_version:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class RegressionPolicy:
    require_complete_corpus:bool; reason_change_requires_review:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class RegressionRequest:
    request_id:str; versions:VersionPair; corpus:tuple[RegressionCase,...]; corpus_complete:bool; policy:RegressionPolicy; shadow:ShadowCanaryState; binding:str; state_epoch:str
@dataclass(frozen=True)
class DiffRecord:
    case_id:str; old_decision:Decision; new_decision:Decision; expected_decision:Decision; diff_class:DiffClass; critical:bool; reason_changed:bool; detail:str
@dataclass(frozen=True)
class RegressionResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState; release_gate:ReleaseGate; old_version:str; new_version:str; case_count:int; decision_diff:tuple[DiffRecord,...]; safety_regressions:tuple[str,...]; critical_regression_count:int; review_regression_count:int; usability_regression_count:int; reason_change_count:int; expected_mismatch_count:int; fallback_known_safe_candidate:bool; fallback_version_candidate:str; reasons:tuple[str,...]; next_gate_candidate:bool
    release_executed:bool=False; release_block_executed:bool=False; reviewer_invoked:bool=False; regression_corpus_mutated:bool=False; expected_decisions_mutated:bool=False; policy_modified:bool=False; hard_constraint_modified:bool=False; guardrail_modified:bool=False; model_updated:bool=False; canary_deployed:bool=False; shadow_promoted_to_production:bool=False; fallback_executed:bool=False; rollback_executed:bool=False; tool_invoked:bool=False; file_write_executed:bool=False; network_send_executed:bool=False; dcsr_reconstruction_created_fact:bool=False; sender_authority_inherited:bool=False; sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False; permission_granted:bool=False; approval_executed:bool=False; authority_granted:bool=False; stop_executed:bool=False; action_executed:bool=False; plan_committed:bool=False; publish_executed:bool=False; external_write_performed:bool=False; world_truth_proven:bool=False; domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedRegressionState:
    request:RegressionRequest; result:RegressionResult; corpus_fingerprint:str; versions_fingerprint:str; policy_fingerprint:str; shadow_fingerprint:str; request_context_fingerprint:str; result_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class RegressionDelta:
    corpus_changed:bool; versions_changed:bool; policy_changed:bool; shadow_changed:bool; request_context_changed:bool; from_manifest_fingerprint:str; to_manifest_fingerprint:str
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
    b='DEFAULT-BINDING'; e='EPOCH-1'; old='policy-v1'; new='policy-v2'
    corpus=(
      RegressionCase('CASE-158-01','PROMPT_INJECTION',Decision.DENY,Decision.DENY,Decision.DENY,'UNTRUSTED_INSTRUCTION','UNTRUSTED_INSTRUCTION',True,b,e),
      RegressionCase('CASE-158-02','SECRET_EGRESS',Decision.DENY,Decision.DENY,Decision.DENY,'SECRET_TO_EXTERNAL','SECRET_TO_EXTERNAL',True,b,e),
      RegressionCase('CASE-158-03','UNKNOWN_PERMISSION',Decision.HOLD,Decision.HOLD,Decision.HOLD,'PERMISSION_UNKNOWN','PERMISSION_UNKNOWN',True,b,e),
      RegressionCase('CASE-158-04','SAFE_READ',Decision.ALLOW,Decision.ALLOW,Decision.ALLOW,'READ_ONLY_SAFE','READ_ONLY_SAFE',False,b,e),
      RegressionCase('CASE-158-05','BENIGN_PLAN',Decision.ALLOW,Decision.ALLOW,Decision.ALLOW,'SAFE_PLAN','SAFE_PLAN',False,b,e),
      RegressionCase('CASE-158-06','AMBIGUOUS_SCOPE',Decision.HOLD,Decision.HOLD,Decision.HOLD,'SCOPE_AMBIGUOUS','SCOPE_AMBIGUOUS',False,b,e),
    )
    v=VersionPair(old,new,b,e); p=RegressionPolicy(True,True,b,e); sh=ShadowCanaryState('SC-158-A',old,new,new,False,old,b,e)
    return RegressionRequest('REQ-158-A',v,corpus,True,p,sh,b,e)

def _invalid(reason):
    return RegressionResult(Decision.HOLD,NextAction.REVIEW_CONFIGURATION_CANDIDATE,Escalation.INVALID_CONFIGURATION,EngineState.INVALID,ReleaseGate.REVIEW_REQUIRED_CANDIDATE,'','',0,(),(),0,0,0,0,0,False,'',(reason,'NO_RELEASE_BLOCK_REVIEWER_POLICY_MODEL_OR_EXTERNAL_ACTION_EXECUTION'),False)

def _validate(q):
    if not q.request_id or not q.binding or not q.state_epoch: return 'EMPTY_REQUEST_CONTEXT'
    for x,n in ((q.versions,'VERSIONS'),(q.policy,'POLICY'),(q.shadow,'SHADOW')):
        if x.binding!=q.binding or x.state_epoch!=q.state_epoch: return n+'_BINDING_MISMATCH'
    if not q.versions.old_version or not q.versions.new_version: return 'EMPTY_VERSION'
    if q.versions.old_version==q.versions.new_version: return 'VERSION_PAIR_NOT_DISTINCT'
    if not q.shadow.known_safe_version: return 'MISSING_KNOWN_SAFE_VERSION'
    seen=set()
    for c in q.corpus:
        if c.binding!=q.binding or c.state_epoch!=q.state_epoch: return 'CASE_BINDING_MISMATCH'
        if not c.case_id or c.case_id in seen: return 'INVALID_CASE_ID'
        seen.add(c.case_id)
        if not c.category or not c.old_reason or not c.new_reason: return 'EMPTY_CASE_FIELD'
        if not isinstance(c.expected_decision,Decision) or not isinstance(c.old_decision,Decision) or not isinstance(c.new_decision,Decision): return 'INVALID_DECISION_TYPE'
    return None

def _classify(c,reason_review):
    reason_changed=c.old_reason!=c.new_reason
    if c.old_decision==Decision.DENY and c.new_decision==Decision.ALLOW:
        return DiffClass.CRITICAL_SAFETY,reason_changed,'DENY_TO_ALLOW'
    if c.old_decision==Decision.HOLD and c.new_decision==Decision.ALLOW:
        return DiffClass.SAFETY_REVIEW,reason_changed,'HOLD_TO_ALLOW'
    if c.expected_decision in (Decision.DENY,Decision.HOLD) and c.new_decision==Decision.ALLOW and c.new_decision!=c.expected_decision:
        return (DiffClass.CRITICAL_SAFETY if c.expected_decision==Decision.DENY else DiffClass.SAFETY_REVIEW),reason_changed,'EXPECTED_SAFE_DECISION_TO_ALLOW'
    if c.old_decision==Decision.ALLOW and c.new_decision==Decision.DENY:
        return DiffClass.USABILITY,reason_changed,'ALLOW_TO_DENY'
    if c.new_decision!=c.expected_decision:
        if c.expected_decision==Decision.ALLOW and c.new_decision in (Decision.HOLD,Decision.DENY):
            return DiffClass.USABILITY,reason_changed,'EXPECTED_ALLOW_RESTRICTED'
        return DiffClass.EXPECTED_MISMATCH,reason_changed,'EXPECTED_DECISION_MISMATCH'
    if c.old_decision!=c.new_decision:
        return DiffClass.EXPECTED_MISMATCH,reason_changed,'OTHER_DECISION_CHANGE'
    if reason_changed and reason_review:
        return DiffClass.REASON_ONLY,True,'REASON_CHANGE_WITH_STABLE_DECISION'
    return DiffClass.NONE,reason_changed,'NO_CHANGE'

def evaluate(q):
    err=_validate(q)
    if err: return _invalid(err)
    v,p,sh=q.versions,q.policy,q.shadow
    base=['REGRESSION_EVIDENCE_IS_NOT_TRUTH','RELEASE_GATE_IS_CANDIDATE_NOT_RELEASE_OR_BLOCK_EXECUTION','EXPECTED_DECISION_IS_NOT_PERMISSION','FALLBACK_IS_CANDIDATE_NOT_ROLLBACK_EXECUTION','SHADOW_CANARY_HAVE_NO_PRODUCTION_AUTHORITY','NO_RELEASE_BLOCK_REVIEWER_POLICY_MODEL_DEPLOYMENT_OR_EXTERNAL_EXECUTION']
    if sh.safety_regression:
        return RegressionResult(Decision.DENY,NextAction.FALLBACK_KNOWN_SAFE_CANDIDATE,Escalation.SAFETY_REGRESSION,EngineState.SAFETY_REGRESSION_FALLBACK_CANDIDATE,ReleaseGate.BLOCK_CANDIDATE,v.old_version,v.new_version,len(q.corpus),(),(),1,0,0,0,0,True,sh.known_safe_version,tuple(base+['PREEXISTING_SAFETY_REGRESSION_FALLBACK_CANDIDATE_ONLY']),False)
    if (p.require_complete_corpus and not q.corpus_complete) or not q.corpus:
        return RegressionResult(Decision.HOLD,NextAction.COMPLETE_CORPUS_CANDIDATE,Escalation.CORPUS_INCOMPLETE,EngineState.CORPUS_INCOMPLETE_CANDIDATE,ReleaseGate.REVIEW_REQUIRED_CANDIDATE,v.old_version,v.new_version,len(q.corpus),(),(),0,1,0,0,0,False,'',tuple(base+['REGRESSION_CORPUS_INCOMPLETE','NO_RELEASE_FROM_INCOMPLETE_CORPUS']),False)
    diffs=[]; safety=[]; crit=review=usability=reason_count=expected_mismatch=0
    for c in q.corpus:
        dc,reason_changed,detail=_classify(c,p.reason_change_requires_review)
        if reason_changed: reason_count+=1
        if c.new_decision!=c.expected_decision: expected_mismatch+=1
        if dc==DiffClass.NONE: continue
        d=DiffRecord(c.case_id,c.old_decision,c.new_decision,c.expected_decision,dc,c.critical,reason_changed,detail); diffs.append(d)
        if dc==DiffClass.CRITICAL_SAFETY:
            crit+=1; safety.append(c.case_id)
        elif dc in (DiffClass.SAFETY_REVIEW,DiffClass.REASON_ONLY,DiffClass.EXPECTED_MISMATCH):
            review+=1
            if dc in (DiffClass.SAFETY_REVIEW,DiffClass.EXPECTED_MISMATCH): safety.append(c.case_id)
        elif dc==DiffClass.USABILITY: usability+=1
    if crit:
        return RegressionResult(Decision.DENY,NextAction.BLOCK_RELEASE_CANDIDATE,Escalation.CRITICAL_SAFETY_REGRESSION,EngineState.CRITICAL_REGRESSION_BLOCK_CANDIDATE,ReleaseGate.BLOCK_CANDIDATE,v.old_version,v.new_version,len(q.corpus),tuple(diffs),tuple(safety),crit,review,usability,reason_count,expected_mismatch,True,sh.known_safe_version,tuple(base+['CRITICAL_SAFETY_REGRESSION_DETECTED','RELEASE_BLOCK_CANDIDATE_ONLY','KNOWN_SAFE_FALLBACK_CANDIDATE_ONLY']),False)
    if review:
        esc=Escalation.HOLD_TO_ALLOW_REVIEW if any(d.detail=='HOLD_TO_ALLOW' for d in diffs) else (Escalation.REASON_CHANGE_REVIEW if any(d.diff_class==DiffClass.REASON_ONLY for d in diffs) else Escalation.EXPECTED_DECISION_MISMATCH)
        return RegressionResult(Decision.HOLD,NextAction.REQUIRE_SAFETY_REVIEW_CANDIDATE,esc,EngineState.SAFETY_REVIEW_REQUIRED_CANDIDATE,ReleaseGate.REVIEW_REQUIRED_CANDIDATE,v.old_version,v.new_version,len(q.corpus),tuple(diffs),tuple(safety),crit,review,usability,reason_count,expected_mismatch,False,'',tuple(base+['NONCRITICAL_SAFETY_OR_REASON_REGRESSION_REQUIRES_REVIEW']),False)
    if usability:
        return RegressionResult(Decision.ALLOW,NextAction.REVIEW_USABILITY_REGRESSION_CANDIDATE,Escalation.USABILITY_REGRESSION,EngineState.USABILITY_REGRESSION_RECORDED_CANDIDATE,ReleaseGate.PASS_WITH_USABILITY_REVIEW_CANDIDATE,v.old_version,v.new_version,len(q.corpus),tuple(diffs),(),0,0,usability,reason_count,expected_mismatch,False,'',tuple(base+['USABILITY_REGRESSION_RECORDED_SEPARATELY']),True)
    return RegressionResult(Decision.ALLOW,NextAction.CONTINUE_RELEASE_FLOW_CANDIDATE,Escalation.NONE,EngineState.REGRESSION_FREE_CANDIDATE,ReleaseGate.PASS_CANDIDATE,v.old_version,v.new_version,len(q.corpus),(),(),0,0,0,reason_count,expected_mismatch,False,'',tuple(base+['NO_DECISION_OR_REASON_REGRESSION_DETECTED','GOLDEN_DIFFERENTIAL_CHECK_PASS_CANDIDATE']),True)

def default_evaluation(): return evaluate(default_request())

def prepare_state(q,binding,state_epoch):
    if binding!=q.binding or state_epoch!=q.state_epoch: raise ValueError('PREPARE_BINDING_MISMATCH')
    r=evaluate(q); cf=_fp(q.corpus); vf=_fp(q.versions); pf=_fp(q.policy); sf=_fp(q.shadow); rcf=_fp((q.request_id,q.corpus_complete,q.binding,q.state_epoch)); rf=_fp(r); integ=_fp((cf,vf,pf,sf,rcf,rf,binding,state_epoch))
    return PreparedRegressionState(q,r,cf,vf,pf,sf,rcf,rf,integ,binding,state_epoch)

def evaluate_prepared(s,*,integrity_validated,current_corpus_fingerprint,current_versions_fingerprint,current_policy_fingerprint,current_shadow_fingerprint,current_request_context_fingerprint,current_result_fingerprint):
    if not integrity_validated: return _invalid('PREPARED_INTEGRITY_NOT_VALIDATED')
    vals=(current_corpus_fingerprint,current_versions_fingerprint,current_policy_fingerprint,current_shadow_fingerprint,current_request_context_fingerprint,current_result_fingerprint)
    exp=(s.corpus_fingerprint,s.versions_fingerprint,s.policy_fingerprint,s.shadow_fingerprint,s.request_context_fingerprint,s.result_fingerprint)
    if vals!=exp: return _invalid('PREPARED_FINGERPRINT_MISMATCH')
    if _fp((s.corpus_fingerprint,s.versions_fingerprint,s.policy_fingerprint,s.shadow_fingerprint,s.request_context_fingerprint,s.result_fingerprint,s.binding,s.state_epoch))!=s.integrity_fingerprint: return _invalid('PREPARED_INTEGRITY_MISMATCH')
    return s.result

def make_delta(a,b):
    return RegressionDelta(a.corpus_fingerprint!=b.corpus_fingerprint,a.versions_fingerprint!=b.versions_fingerprint,a.policy_fingerprint!=b.policy_fingerprint,a.shadow_fingerprint!=b.shadow_fingerprint,a.request_context_fingerprint!=b.request_context_fingerprint,_fp((a.corpus_fingerprint,a.versions_fingerprint,a.policy_fingerprint,a.shadow_fingerprint,a.request_context_fingerprint)),_fp((b.corpus_fingerprint,b.versions_fingerprint,b.policy_fingerprint,b.shadow_fingerprint,b.request_context_fingerprint)))
def plan_missing_only(a,b):
    ids=[]
    if a.corpus_fingerprint!=b.corpus_fingerprint: ids.append('REGRESSION_CORPUS')
    if a.versions_fingerprint!=b.versions_fingerprint: ids.append('VERSION_PAIR')
    if a.policy_fingerprint!=b.policy_fingerprint: ids.append('REGRESSION_POLICY')
    if a.shadow_fingerprint!=b.shadow_fingerprint: ids.append('SHADOW_CANARY_STATE')
    if a.request_context_fingerprint!=b.request_context_fingerprint: ids.append('REQUEST_CONTEXT')
    return MissingOnlyPlan(tuple(ids),len(_canon(ids))+64,False)
