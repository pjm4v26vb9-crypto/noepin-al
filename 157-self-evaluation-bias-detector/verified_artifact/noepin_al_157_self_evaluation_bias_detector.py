"""NOEPIN AL 157 — Self-Evaluation Bias Detector — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-157
DCSR: DIRECT INTEGRATION / 直接統合.

Pure evaluation core. It compares an agent's self scores with independent reviewer scores by task class,
and checks both against observed outcomes. Major systematic overconfidence requires an independent-review
candidate; insufficient data limits self-score weight; sudden bias shift emits a trust-reduction candidate.
Safety-regression state can only emit a known-safe fallback candidate. No reviewer call, trust mutation,
ALLOW execution, learning update, policy/guardrail mutation, deployment, rollback, file/network write,
tool invocation, or external action is executed here. Self Score != Truth; Independent Score != Truth;
Bias Estimate != Fact Authority; Correction Factor != Score Mutation; Reviewer Requirement != Reviewer
Invocation; Trust Reduction Candidate != Trust Mutation; Shadow/Canary State != Production Authority;
DCSR reconstruction cannot create Truth, Domain Authority, Permission, Safety Proof, Approval, Action,
or Action Success.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json

class Decision(str, Enum):
    ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class EngineState(str, Enum):
    CALIBRATED_NORMAL_CANDIDATE='CALIBRATED_NORMAL_CANDIDATE'
    INDEPENDENT_REVIEW_REQUIRED_CANDIDATE='INDEPENDENT_REVIEW_REQUIRED_CANDIDATE'
    SELF_WEIGHT_LIMITED_CANDIDATE='SELF_WEIGHT_LIMITED_CANDIDATE'
    TRUST_REDUCTION_CANDIDATE='TRUST_REDUCTION_CANDIDATE'
    SAFETY_REGRESSION_FALLBACK_CANDIDATE='SAFETY_REGRESSION_FALLBACK_CANDIDATE'
    INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_REVIEW_FLOW_CANDIDATE='CONTINUE_REVIEW_FLOW_CANDIDATE'
    REQUIRE_INDEPENDENT_REVIEWER_CANDIDATE='REQUIRE_INDEPENDENT_REVIEWER_CANDIDATE'
    LIMIT_SELF_SCORE_WEIGHT_CANDIDATE='LIMIT_SELF_SCORE_WEIGHT_CANDIDATE'
    REDUCE_TRUST_CANDIDATE='REDUCE_TRUST_CANDIDATE'
    FALLBACK_KNOWN_SAFE_CANDIDATE='FALLBACK_KNOWN_SAFE_CANDIDATE'
    REVIEW_CONFIGURATION_CANDIDATE='REVIEW_CONFIGURATION_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; OVERCONFIDENCE_BIAS_HIGH='OVERCONFIDENCE_BIAS_HIGH'; INSUFFICIENT_DATA='INSUFFICIENT_DATA'; SUDDEN_BIAS_SHIFT='SUDDEN_BIAS_SHIFT'; OUTCOME_CALIBRATION_GAP='OUTCOME_CALIBRATION_GAP'; SAFETY_REGRESSION='SAFETY_REGRESSION'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'
class ReviewerRequirement(str, Enum):
    NONE='NONE'; INDEPENDENT_PREFERRED='INDEPENDENT_PREFERRED'; INDEPENDENT_REQUIRED='INDEPENDENT_REQUIRED'

@dataclass(frozen=True)
class ScoreSample:
    sample_id:str; task_class:str; self_score:float; independent_score:float; outcome_score:float; binding:str; state_epoch:str
@dataclass(frozen=True)
class BiasPolicy:
    minimum_samples:int; overconfidence_threshold:float; sudden_shift_threshold:float; calibration_tolerance:float; base_self_score_weight:float; insufficient_data_weight_cap:float; overconfidence_weight_cap:float; binding:str; state_epoch:str
@dataclass(frozen=True)
class BiasHistory:
    task_class:str; historical_bias:float; historical_self_outcome_mae:float; historical_independent_outcome_mae:float; binding:str; state_epoch:str
@dataclass(frozen=True)
class ShadowCanaryState:
    state_id:str; stable_version:str; canary_version:str; shadow_version:str; safety_regression:bool; known_safe_version:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class BiasRequest:
    request_id:str; task_class:str; samples:tuple[ScoreSample,...]; policy:BiasPolicy; history:BiasHistory; shadow:ShadowCanaryState; model_policy_version:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class BiasResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState; task_class:str; sample_count:int; bias_estimate:float; self_outcome_mae:float; independent_outcome_mae:float; correction_factor_candidate:float; reviewer_requirement:ReviewerRequirement; self_score_weight_candidate:float; trust_adjustment_candidate:int; fallback_known_safe_candidate:bool; fallback_version_candidate:str; reasons:tuple[str,...]; next_gate_candidate:bool
    reviewer_invoked:bool=False; trust_mutated:bool=False; self_score_mutated:bool=False; correction_applied:bool=False; allow_executed:bool=False; learning_update_committed:bool=False; model_updated:bool=False; risk_model_mutated:bool=False; policy_modified:bool=False; hard_constraint_modified:bool=False; guardrail_modified:bool=False; canary_deployed:bool=False; shadow_promoted_to_production:bool=False; fallback_executed:bool=False; rollback_executed:bool=False; tool_invoked:bool=False; file_write_executed:bool=False; network_send_executed:bool=False; dcsr_reconstruction_created_fact:bool=False; sender_authority_inherited:bool=False; sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False; permission_granted:bool=False; approval_executed:bool=False; authority_granted:bool=False; stop_executed:bool=False; action_executed:bool=False; plan_committed:bool=False; publish_executed:bool=False; external_write_performed:bool=False; world_truth_proven:bool=False; domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedBiasState:
    request:BiasRequest; result:BiasResult; samples_fingerprint:str; policy_fingerprint:str; history_fingerprint:str; shadow_fingerprint:str; request_context_fingerprint:str; result_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class BiasDelta:
    samples_changed:bool; policy_changed:bool; history_changed:bool; shadow_changed:bool; request_context_changed:bool; from_manifest_fingerprint:str; to_manifest_fingerprint:str
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
def _mean(xs): return sum(xs)/len(xs) if xs else 0.0

def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'; t='PLAN_REVIEW'
    vals=(
      ('S1',0.82,0.80,0.79),('S2',0.76,0.74,0.75),('S3',0.88,0.86,0.85),
      ('S4',0.71,0.70,0.69),('S5',0.91,0.89,0.90),('S6',0.67,0.65,0.66),
    )
    samples=tuple(ScoreSample(i,t,ss,ii,oo,b,e) for i,ss,ii,oo in vals)
    p=BiasPolicy(5,0.12,0.15,0.06,0.50,0.25,0.20,b,e)
    h=BiasHistory(t,0.018,0.018,0.012,b,e)
    sh=ShadowCanaryState('SC-157-A','stable-v1','canary-v2','shadow-v2',False,'stable-v1',b,e)
    return BiasRequest('REQ-157-A',t,samples,p,h,sh,'policy-v1',b,e)

def _invalid(reason):
    return BiasResult(Decision.HOLD,NextAction.REVIEW_CONFIGURATION_CANDIDATE,Escalation.INVALID_CONFIGURATION,EngineState.INVALID,'',0,0.0,0.0,0.0,1.0,ReviewerRequirement.INDEPENDENT_REQUIRED,0.0,0,False,'',(reason,'NO_REVIEWER_TRUST_SCORE_POLICY_OR_EXTERNAL_ACTION_EXECUTION'),False)

def _validate(q):
    if not q.request_id or not q.task_class or not q.model_policy_version or not q.binding or not q.state_epoch: return 'EMPTY_REQUEST_CONTEXT'
    for x,n in ((q.policy,'POLICY'),(q.history,'HISTORY'),(q.shadow,'SHADOW')):
        if x.binding!=q.binding or x.state_epoch!=q.state_epoch: return n+'_BINDING_MISMATCH'
    if q.history.task_class!=q.task_class: return 'HISTORY_TASK_CLASS_MISMATCH'
    p=q.policy
    if p.minimum_samples<1 or not (0<p.overconfidence_threshold<=1) or not (0<p.sudden_shift_threshold<=1) or not (0<=p.calibration_tolerance<=1) or not (0<p.base_self_score_weight<=1) or not (0<=p.insufficient_data_weight_cap<=1) or not (0<=p.overconfidence_weight_cap<=1): return 'INVALID_POLICY'
    if not (-1<=q.history.historical_bias<=1) or not (0<=q.history.historical_self_outcome_mae<=1) or not (0<=q.history.historical_independent_outcome_mae<=1): return 'INVALID_HISTORY'
    if not q.shadow.known_safe_version: return 'MISSING_KNOWN_SAFE_VERSION'
    seen=set()
    for s in q.samples:
        if s.binding!=q.binding or s.state_epoch!=q.state_epoch: return 'SAMPLE_BINDING_MISMATCH'
        if not s.sample_id or s.sample_id in seen: return 'INVALID_SAMPLE_ID'
        seen.add(s.sample_id)
        if not s.task_class: return 'EMPTY_SAMPLE_TASK_CLASS'
        if not (0<=s.self_score<=1 and 0<=s.independent_score<=1 and 0<=s.outcome_score<=1): return 'INVALID_SCORE_RANGE'
    return None

def evaluate(q):
    err=_validate(q)
    if err: return _invalid(err)
    p,h,sh=q.policy,q.history,q.shadow
    xs=tuple(s for s in q.samples if s.task_class==q.task_class)
    base=['SELF_SCORE_IS_NOT_TRUTH','INDEPENDENT_SCORE_IS_NOT_TRUTH','BIAS_ESTIMATE_IS_NOT_FACT_AUTHORITY','CORRECTION_FACTOR_IS_CANDIDATE_NOT_SCORE_MUTATION','REVIEWER_REQUIREMENT_IS_NOT_REVIEWER_INVOCATION','TRUST_REDUCTION_IS_CANDIDATE_NOT_TRUST_MUTATION','SHADOW_CANARY_HAVE_NO_PRODUCTION_AUTHORITY','NO_REVIEWER_TRUST_SCORE_POLICY_DEPLOYMENT_OR_EXTERNAL_EXECUTION']
    if sh.safety_regression:
        return BiasResult(Decision.DENY,NextAction.FALLBACK_KNOWN_SAFE_CANDIDATE,Escalation.SAFETY_REGRESSION,EngineState.SAFETY_REGRESSION_FALLBACK_CANDIDATE,q.task_class,len(xs),0.0,0.0,0.0,1.0,ReviewerRequirement.INDEPENDENT_REQUIRED,0.0,-2,True,sh.known_safe_version,tuple(base+['SAFETY_REGRESSION_FALLBACK_CANDIDATE_ONLY']),False)
    if len(xs)<p.minimum_samples:
        w=round(min(p.base_self_score_weight,p.insufficient_data_weight_cap),6)
        return BiasResult(Decision.HOLD,NextAction.LIMIT_SELF_SCORE_WEIGHT_CANDIDATE,Escalation.INSUFFICIENT_DATA,EngineState.SELF_WEIGHT_LIMITED_CANDIDATE,q.task_class,len(xs),0.0,0.0,0.0,1.0,ReviewerRequirement.INDEPENDENT_PREFERRED,w,-1,False,'',tuple(base+['INSUFFICIENT_DATA_SELF_SCORE_WEIGHT_LIMITED','SELF_SCORE_ALONE_CANNOT_ESTABLISH_ALLOW']),False)
    diffs=[s.self_score-s.independent_score for s in xs]
    bias=_mean(diffs)
    self_mae=_mean([abs(s.self_score-s.outcome_score) for s in xs])
    ind_mae=_mean([abs(s.independent_score-s.outcome_score) for s in xs])
    bias_r=round(bias,6); self_r=round(self_mae,6); ind_r=round(ind_mae,6)
    correction=round(_clamp(1.0-bias*0.75,0.25,1.25),6)
    sudden=abs(bias-h.historical_bias)>=p.sudden_shift_threshold
    if bias>=p.overconfidence_threshold:
        w=round(min(p.base_self_score_weight,p.overconfidence_weight_cap),6)
        return BiasResult(Decision.HOLD,NextAction.REQUIRE_INDEPENDENT_REVIEWER_CANDIDATE,Escalation.OVERCONFIDENCE_BIAS_HIGH,EngineState.INDEPENDENT_REVIEW_REQUIRED_CANDIDATE,q.task_class,len(xs),bias_r,self_r,ind_r,correction,ReviewerRequirement.INDEPENDENT_REQUIRED,w,-2,False,'',tuple(base+['SYSTEMATIC_OVERCONFIDENCE_DETECTED','INDEPENDENT_REVIEW_REQUIRED_CANDIDATE','SELF_SCORE_ALONE_CANNOT_ESTABLISH_ALLOW']),False)
    if sudden:
        w=round(min(p.base_self_score_weight,0.35),6)
        return BiasResult(Decision.HOLD,NextAction.REDUCE_TRUST_CANDIDATE,Escalation.SUDDEN_BIAS_SHIFT,EngineState.TRUST_REDUCTION_CANDIDATE,q.task_class,len(xs),bias_r,self_r,ind_r,correction,ReviewerRequirement.INDEPENDENT_PREFERRED,w,-1,False,'',tuple(base+['SUDDEN_BIAS_SHIFT_DETECTED','TRUST_REDUCTION_CANDIDATE_ONLY']),False)
    if self_mae>ind_mae+p.calibration_tolerance and bias>0:
        w=round(min(p.base_self_score_weight,0.35),6)
        return BiasResult(Decision.HOLD,NextAction.LIMIT_SELF_SCORE_WEIGHT_CANDIDATE,Escalation.OUTCOME_CALIBRATION_GAP,EngineState.SELF_WEIGHT_LIMITED_CANDIDATE,q.task_class,len(xs),bias_r,self_r,ind_r,correction,ReviewerRequirement.INDEPENDENT_PREFERRED,w,-1,False,'',tuple(base+['SELF_OUTCOME_CALIBRATION_WORSE_THAN_INDEPENDENT','SELF_SCORE_WEIGHT_LIMITED_CANDIDATE_ONLY']),False)
    rs=list(base)+['TASK_SCOPED_PAIRED_CALIBRATION_EVALUATED']
    if bias<0: rs.append('UNDERCONFIDENCE_OBSERVED_NO_AUTHORITY_PROMOTION')
    else: rs.append('CALIBRATION_WITHIN_ALLOWED_BIAS_BOUND')
    return BiasResult(Decision.ALLOW,NextAction.CONTINUE_REVIEW_FLOW_CANDIDATE,Escalation.NONE,EngineState.CALIBRATED_NORMAL_CANDIDATE,q.task_class,len(xs),bias_r,self_r,ind_r,correction,ReviewerRequirement.NONE,round(p.base_self_score_weight,6),0,False,'',tuple(rs),True)

def default_evaluation(): return evaluate(default_request())

def prepare_state(q,binding,state_epoch):
    if binding!=q.binding or state_epoch!=q.state_epoch: raise ValueError('PREPARE_BINDING_MISMATCH')
    r=evaluate(q); sf=_fp(q.samples); pf=_fp(q.policy); hf=_fp(q.history); shf=_fp(q.shadow); rcf=_fp((q.request_id,q.task_class,q.model_policy_version,q.binding,q.state_epoch)); rf=_fp(r); integ=_fp((sf,pf,hf,shf,rcf,rf,binding,state_epoch))
    return PreparedBiasState(q,r,sf,pf,hf,shf,rcf,rf,integ,binding,state_epoch)

def evaluate_prepared(s,*,integrity_validated,current_samples_fingerprint,current_policy_fingerprint,current_history_fingerprint,current_shadow_fingerprint,current_request_context_fingerprint,current_result_fingerprint):
    if not integrity_validated: return _invalid('PREPARED_INTEGRITY_NOT_VALIDATED')
    vals=(current_samples_fingerprint,current_policy_fingerprint,current_history_fingerprint,current_shadow_fingerprint,current_request_context_fingerprint,current_result_fingerprint)
    exp=(s.samples_fingerprint,s.policy_fingerprint,s.history_fingerprint,s.shadow_fingerprint,s.request_context_fingerprint,s.result_fingerprint)
    if vals!=exp: return _invalid('PREPARED_FINGERPRINT_MISMATCH')
    if _fp((s.samples_fingerprint,s.policy_fingerprint,s.history_fingerprint,s.shadow_fingerprint,s.request_context_fingerprint,s.result_fingerprint,s.binding,s.state_epoch))!=s.integrity_fingerprint: return _invalid('PREPARED_INTEGRITY_MISMATCH')
    return s.result

def make_delta(a,b):
    return BiasDelta(a.samples_fingerprint!=b.samples_fingerprint,a.policy_fingerprint!=b.policy_fingerprint,a.history_fingerprint!=b.history_fingerprint,a.shadow_fingerprint!=b.shadow_fingerprint,a.request_context_fingerprint!=b.request_context_fingerprint,_fp((a.samples_fingerprint,a.policy_fingerprint,a.history_fingerprint,a.shadow_fingerprint,a.request_context_fingerprint)),_fp((b.samples_fingerprint,b.policy_fingerprint,b.history_fingerprint,b.shadow_fingerprint,b.request_context_fingerprint)))
def plan_missing_only(a,b):
    ids=[]
    if a.samples_fingerprint!=b.samples_fingerprint: ids.append('SCORE_SAMPLES')
    if a.policy_fingerprint!=b.policy_fingerprint: ids.append('BIAS_POLICY')
    if a.history_fingerprint!=b.history_fingerprint: ids.append('BIAS_HISTORY')
    if a.shadow_fingerprint!=b.shadow_fingerprint: ids.append('SHADOW_CANARY_STATE')
    if a.request_context_fingerprint!=b.request_context_fingerprint: ids.append('REQUEST_CONTEXT')
    return MissingOnlyPlan(tuple(ids),len(_canon(ids))+64,False)
