"""NOEPIN AL 154 — Drift-Adaptive Risk Calibrator — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-154
DCSR: DIRECT INTEGRATION / 直接統合.

Detects feature/outcome/calibration drift against an immutable baseline and emits conservative
risk/recalibration candidates. Critical drift produces a Restricted Mode candidate; minor drift
produces enhanced-monitoring candidates; validated recalibration produces only a staged-recovery
candidate. Unknown cause increases the HOLD-threshold candidate. Shadow/Canary state has no
Production Authority. Adjusted Risk Candidate != Production Risk Mutation. Restricted Mode Candidate
!= Restriction Execution. Staged Recovery Candidate != Deployment/Authority Restoration. This core
performs no model/policy/threshold mutation, online-learning commit, deployment, rollback, tool/file/
network execution, or external write. DCSR reconstruction cannot create Truth, Domain Authority,
Permission, Safety Proof, Approval, Action, or Action Success.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str,Enum): ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class EngineState(str,Enum):
    STABLE_RISK_CANDIDATE='STABLE_RISK_CANDIDATE'; MONITOR_ENHANCED_CANDIDATE='MONITOR_ENHANCED_CANDIDATE'; RESTRICTED_MODE_CANDIDATE='RESTRICTED_MODE_CANDIDATE'; STAGED_RECOVERY_CANDIDATE='STAGED_RECOVERY_CANDIDATE'; UNKNOWN_CAUSE_HOLD_CANDIDATE='UNKNOWN_CAUSE_HOLD_CANDIDATE'; INVALID='INVALID'
class NextAction(str,Enum):
    CONTINUE_STABLE_CANDIDATE='CONTINUE_STABLE_CANDIDATE'; MONITOR_MORE_CANDIDATE='MONITOR_MORE_CANDIDATE'; ENTER_RESTRICTED_MODE_CANDIDATE='ENTER_RESTRICTED_MODE_CANDIDATE'; CONTINUE_STAGED_RECOVERY_CANDIDATE='CONTINUE_STAGED_RECOVERY_CANDIDATE'; RAISE_HOLD_THRESHOLD_CANDIDATE='RAISE_HOLD_THRESHOLD_CANDIDATE'; REVIEW_CALIBRATION_CANDIDATE='REVIEW_CALIBRATION_CANDIDATE'
class Escalation(str,Enum):
    NONE='NONE'; MINOR_DRIFT='MINOR_DRIFT'; CRITICAL_DRIFT='CRITICAL_DRIFT'; UNKNOWN_CAUSE='UNKNOWN_CAUSE'; RECALIBRATION_VALIDATED='RECALIBRATION_VALIDATED'; DATA_INSUFFICIENT='DATA_INSUFFICIENT'; POLICY_UNVERIFIED='POLICY_UNVERIFIED'; SAFETY_REGRESSION='SAFETY_REGRESSION'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'
@dataclass(frozen=True)
class FeatureOutcome:
    record_id:str; features:tuple[float,...]; risk_prediction:float; outcome_risky:bool; label_available:bool; weight:float; binding:str; state_epoch:str
@dataclass(frozen=True)
class BaselineDistribution:
    baseline_id:str; feature_means:tuple[float,...]; feature_scales:tuple[float,...]; calibration_error:float; positive_rate:float; version:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class DriftPolicy:
    policy_id:str; min_samples:int; warn_drift_score:float; critical_drift_score:float; calibration_error_limit:float; positive_rate_shift_limit:float; conservative_risk_increment:float; hold_threshold_raise:float; policy_verified:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class ShadowCanaryState:
    state_id:str; recalibration_candidate_available:bool; recalibration_validation_passed:bool; safety_regression:bool; stable_version:str; canary_version:str; shadow_version:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class DriftCalibrationRequest:
    request_id:str; stream:tuple[FeatureOutcome,...]; baseline:BaselineDistribution; policy:DriftPolicy; shadow:ShadowCanaryState; cause_attribution_available:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class DriftCalibrationResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState; drift_score:float; feature_drift_scores:tuple[float,...]; calibration_error:float; calibration_degradation:float; positive_rate_shift:float; recalibration_need:bool; adjusted_risk:float; hold_threshold_raise_candidate:float; restricted_mode_candidate:bool; staged_recovery_candidate:bool; cause_summary:str; reasons:tuple[str,...]; next_gate_candidate:bool
    adjusted_risk_committed:bool=False; risk_model_mutated:bool=False; calibration_model_mutated:bool=False; production_threshold_mutated:bool=False; policy_modified:bool=False; guardrail_modified:bool=False; restricted_mode_executed:bool=False; monitor_policy_mutated:bool=False; canary_deployed:bool=False; shadow_promoted_to_production:bool=False; staged_recovery_executed:bool=False; rollback_executed:bool=False; model_updated:bool=False; online_learning_committed:bool=False; tool_invoked:bool=False; file_write_executed:bool=False; network_send_executed:bool=False; dcsr_reconstruction_created_fact:bool=False; sender_authority_inherited:bool=False; sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False; permission_granted:bool=False; approval_executed:bool=False; authority_granted:bool=False; stop_executed:bool=False; action_executed:bool=False; plan_committed:bool=False; publish_executed:bool=False; external_write_performed:bool=False; world_truth_proven:bool=False; domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedDriftState:
    request:DriftCalibrationRequest; result:DriftCalibrationResult; stream_fingerprint:str; baseline_fingerprint:str; policy_fingerprint:str; shadow_fingerprint:str; request_context_fingerprint:str; result_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class DriftDelta:
    stream_changed:bool; baseline_changed:bool; policy_changed:bool; shadow_changed:bool; request_context_changed:bool; from_manifest_fingerprint:str; to_manifest_fingerprint:str
@dataclass(frozen=True)
class MissingOnlyPlan: missing_or_changed_record_ids:tuple[str,...]; metadata_bytes_required:int; full_resend_required:bool

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
    rows=(
        FeatureOutcome('O1',(0.18,0.48,0.79),0.12,False,True,1,b,e),
        FeatureOutcome('O2',(0.22,0.52,0.81),0.20,False,True,1,b,e),
        FeatureOutcome('O3',(0.20,0.50,0.80),0.78,True,True,1,b,e),
        FeatureOutcome('O4',(0.19,0.51,0.82),0.70,True,True,1,b,e),
        FeatureOutcome('O5',(0.21,0.49,0.78),0.16,False,True,1,b,e),
        FeatureOutcome('O6',(0.18,0.52,0.80),0.82,True,True,1,b,e),
        FeatureOutcome('O7',(0.22,0.48,0.80),0.18,False,True,1,b,e),
        FeatureOutcome('O8',(0.20,0.50,0.81),0.75,True,True,1,b,e),
        FeatureOutcome('O9',(0.19,0.49,0.79),0.10,False,True,1,b,e),
        FeatureOutcome('O10',(0.21,0.51,0.80),0.15,False,True,1,b,e),
    )
    base=BaselineDistribution('BASE-154-A',(0.20,0.50,0.80),(0.10,0.10,0.10),0.18,0.40,'stable-v1',b,e)
    pol=DriftPolicy('POL-154-A',8,0.25,0.60,0.30,0.25,0.15,0.10,True,b,e)
    sh=ShadowCanaryState('SC-154-A',False,False,False,'stable-v1','canary-v2','shadow-v2',b,e)
    return DriftCalibrationRequest('REQ-154-A',rows,base,pol,sh,True,b,e)

def _invalid(q,reason):
    return DriftCalibrationResult(Decision.HOLD,NextAction.REVIEW_CALIBRATION_CANDIDATE,Escalation.INVALID_CONFIGURATION,EngineState.INVALID,0.0,(),0.0,0.0,0.0,True,1.0,0.0,False,False,'INVALID',(reason,'NO_PRODUCTION_RISK_MUTATION','NO_RESTRICTED_MODE_EXECUTION'),False)

def _validate(q):
    if not q.request_id or not q.binding or not q.state_epoch:return 'EMPTY_REQUEST_CONTEXT'
    for x,n in ((q.baseline,'BASELINE'),(q.policy,'POLICY'),(q.shadow,'SHADOW')):
        if x.binding!=q.binding or x.state_epoch!=q.state_epoch:return n+'_BINDING_MISMATCH'
    b=q.baseline; p=q.policy
    if not b.baseline_id or not b.feature_means or len(b.feature_means)!=len(b.feature_scales):return 'INVALID_BASELINE'
    if any((not isinstance(x,(int,float))) or not math.isfinite(x) for x in b.feature_means):return 'INVALID_BASELINE_MEAN'
    if any((not isinstance(x,(int,float))) or (not math.isfinite(x)) or x<=0 for x in b.feature_scales):return 'INVALID_BASELINE_SCALE'
    if not (0<=b.calibration_error<=1 and 0<=b.positive_rate<=1):return 'INVALID_BASELINE_RANGE'
    if p.min_samples<1 or not (0<=p.warn_drift_score<p.critical_drift_score<=1):return 'INVALID_DRIFT_BOUNDS'
    if not (0<=p.calibration_error_limit<=1 and 0<p.positive_rate_shift_limit<=1 and 0<=p.conservative_risk_increment<=1 and 0<=p.hold_threshold_raise<=1):return 'INVALID_POLICY_RANGE'
    seen=set()
    for r in q.stream:
        if r.binding!=q.binding or r.state_epoch!=q.state_epoch:return 'STREAM_BINDING_MISMATCH'
        if not r.record_id or r.record_id in seen:return 'INVALID_RECORD_ID'
        seen.add(r.record_id)
        if len(r.features)!=len(b.feature_means):return 'FEATURE_DIMENSION_MISMATCH'
        if any((not isinstance(x,(int,float))) or not math.isfinite(x) for x in r.features):return 'INVALID_FEATURE'
        if not (0<=r.risk_prediction<=1) or r.weight<=0:return 'INVALID_STREAM_RANGE'
    return None

def _metrics(q):
    n=len(q.stream); dim=len(q.baseline.feature_means)
    if not n:return (),0.0,0.0,0.0,0.0,0.0
    sw=sum(r.weight for r in q.stream)
    means=tuple(sum(r.features[j]*r.weight for r in q.stream)/sw for j in range(dim))
    fd=tuple(_clamp(abs(means[j]-q.baseline.feature_means[j])/(2.0*q.baseline.feature_scales[j])) for j in range(dim))
    labeled=[r for r in q.stream if r.label_available]
    if labeled:
        lw=sum(r.weight for r in labeled)
        cal=sum(abs(r.risk_prediction-(1.0 if r.outcome_risky else 0.0))*r.weight for r in labeled)/lw
        pos=sum((1.0 if r.outcome_risky else 0.0)*r.weight for r in labeled)/lw
        pos_shift=abs(pos-q.baseline.positive_rate)
    else: cal=q.baseline.calibration_error; pos_shift=0.0
    cal_deg=max(0.0,cal-q.baseline.calibration_error)
    cal_score=_clamp(cal_deg/max(0.05,q.policy.calibration_error_limit-q.baseline.calibration_error)) if q.policy.calibration_error_limit>q.baseline.calibration_error else _clamp(cal_deg/0.05)
    label_score=_clamp(pos_shift/q.policy.positive_rate_shift_limit)
    drift=max(max(fd) if fd else 0.0,cal_score,label_score)
    mean_risk=sum(r.risk_prediction*r.weight for r in q.stream)/sw
    return fd,cal,cal_deg,pos_shift,drift,mean_risk

def _cause(fd,cal_deg,pos_shift,q):
    parts=[]
    for i,x in enumerate(fd):
        if x>=q.policy.warn_drift_score: parts.append((x,f'FEATURE_{i}'))
    cal_score=_clamp(cal_deg/max(0.05,q.policy.calibration_error_limit-q.baseline.calibration_error)) if q.policy.calibration_error_limit>q.baseline.calibration_error else _clamp(cal_deg/0.05)
    if cal_score>=q.policy.warn_drift_score: parts.append((cal_score,'CALIBRATION'))
    label_score=_clamp(pos_shift/q.policy.positive_rate_shift_limit)
    if label_score>=q.policy.warn_drift_score: parts.append((label_score,'LABEL'))
    if not parts:return 'NONE'
    parts.sort(reverse=True)
    top=parts[0][0]; names=sorted(n for s,n in parts if top-s<=0.08)
    return '+'.join(names)

def evaluate(q):
    bad=_validate(q)
    if bad:return _invalid(q,bad)
    p=q.policy
    base_reasons=('ADJUSTED_RISK_IS_CANDIDATE_NOT_PRODUCTION_MUTATION','DRIFT_SCORE_IS_EVIDENCE_NOT_TRUTH','SHADOW_CANARY_HAVE_NO_PRODUCTION_AUTHORITY','RESTRICTED_MODE_CANDIDATE_IS_NOT_RESTRICTION_EXECUTION','STAGED_RECOVERY_CANDIDATE_IS_NOT_DEPLOYMENT_OR_AUTHORITY_RESTORATION','NO_ONLINE_LEARNING_COMMIT')
    fd,cal,caldeg,pshift,drift,meanrisk=_metrics(q)
    if not p.policy_verified:
        return DriftCalibrationResult(Decision.HOLD,NextAction.REVIEW_CALIBRATION_CANDIDATE,Escalation.POLICY_UNVERIFIED,EngineState.INVALID,drift,fd,cal,caldeg,pshift,True,_clamp(meanrisk+p.conservative_risk_increment),p.hold_threshold_raise,False,False,'POLICY_UNVERIFIED',base_reasons+('POLICY_UNVERIFIED_NO_PRODUCTION_CHANGE',),False)
    if len(q.stream)<p.min_samples:
        return DriftCalibrationResult(Decision.HOLD,NextAction.MONITOR_MORE_CANDIDATE,Escalation.DATA_INSUFFICIENT,EngineState.MONITOR_ENHANCED_CANDIDATE,drift,fd,cal,caldeg,pshift,True,_clamp(meanrisk+p.conservative_risk_increment),p.hold_threshold_raise,False,False,'DATA_INSUFFICIENT',base_reasons+('DATA_INSUFFICIENT_CONSERVATIVE_RISK_CANDIDATE',),False)
    cause=_cause(fd,caldeg,pshift,q)
    critical=drift>=p.critical_drift_score or cal>p.calibration_error_limit
    minor=(not critical) and drift>=p.warn_drift_score
    if q.shadow.safety_regression:
        return DriftCalibrationResult(Decision.HOLD,NextAction.ENTER_RESTRICTED_MODE_CANDIDATE,Escalation.SAFETY_REGRESSION,EngineState.RESTRICTED_MODE_CANDIDATE,max(drift,p.critical_drift_score),fd,cal,caldeg,pshift,True,_clamp(meanrisk+p.conservative_risk_increment),p.hold_threshold_raise,True,False,cause,base_reasons+('SAFETY_REGRESSION_RESTRICTED_MODE_CANDIDATE',),False)
    if critical and not q.cause_attribution_available:
        return DriftCalibrationResult(Decision.HOLD,NextAction.RAISE_HOLD_THRESHOLD_CANDIDATE,Escalation.UNKNOWN_CAUSE,EngineState.UNKNOWN_CAUSE_HOLD_CANDIDATE,drift,fd,cal,caldeg,pshift,True,_clamp(meanrisk+p.conservative_risk_increment),p.hold_threshold_raise,True,False,'UNKNOWN',base_reasons+('UNKNOWN_CAUSE_RAISE_HOLD_THRESHOLD_CANDIDATE',),False)
    if critical:
        if q.shadow.recalibration_candidate_available and q.shadow.recalibration_validation_passed:
            adjusted=_clamp(meanrisk+p.conservative_risk_increment*0.5)
            return DriftCalibrationResult(Decision.ALLOW,NextAction.CONTINUE_STAGED_RECOVERY_CANDIDATE,Escalation.RECALIBRATION_VALIDATED,EngineState.STAGED_RECOVERY_CANDIDATE,drift,fd,cal,caldeg,pshift,True,adjusted,0.0,False,True,cause,base_reasons+('RECALIBRATION_VALIDATED_STAGED_RECOVERY_CANDIDATE',),True)
        adjusted=_clamp(meanrisk+p.conservative_risk_increment)
        return DriftCalibrationResult(Decision.HOLD,NextAction.ENTER_RESTRICTED_MODE_CANDIDATE,Escalation.CRITICAL_DRIFT,EngineState.RESTRICTED_MODE_CANDIDATE,drift,fd,cal,caldeg,pshift,True,adjusted,p.hold_threshold_raise,True,False,cause,base_reasons+('CRITICAL_DRIFT_CONSERVATIVE_RISK_CANDIDATE',),False)
    if minor:
        adjusted=_clamp(meanrisk+p.conservative_risk_increment*0.5)
        return DriftCalibrationResult(Decision.ALLOW,NextAction.MONITOR_MORE_CANDIDATE,Escalation.MINOR_DRIFT,EngineState.MONITOR_ENHANCED_CANDIDATE,drift,fd,cal,caldeg,pshift,True,adjusted,0.0,False,False,cause,base_reasons+('MINOR_DRIFT_MONITOR_ENHANCED_CANDIDATE',),True)
    return DriftCalibrationResult(Decision.ALLOW,NextAction.CONTINUE_STABLE_CANDIDATE,Escalation.NONE,EngineState.STABLE_RISK_CANDIDATE,drift,fd,cal,caldeg,pshift,False,meanrisk,0.0,False,False,cause,base_reasons+('NO_MATERIAL_DRIFT_STABLE_RISK_CANDIDATE',),True)

def default_evaluation(): return evaluate(default_request())
def prepare_state(q,binding,state_epoch):
    if q.binding!=binding or q.state_epoch!=state_epoch: raise ValueError('PREPARE_BINDING_MISMATCH')
    r=evaluate(q); sf=_fp(q.stream); bf=_fp(q.baseline); pf=_fp(q.policy); shf=_fp(q.shadow); rf=_fp((q.request_id,q.cause_attribution_available,q.binding,q.state_epoch)); resf=_fp(r)
    integ=_fp((sf,bf,pf,shf,rf,resf,binding,state_epoch))
    return PreparedDriftState(q,r,sf,bf,pf,shf,rf,resf,integ,binding,state_epoch)
def evaluate_prepared(st,*,integrity_validated,current_stream_fingerprint,current_baseline_fingerprint,current_policy_fingerprint,current_shadow_fingerprint,current_request_context_fingerprint,current_result_fingerprint):
    if not integrity_validated:return _invalid(st.request,'PREPARED_INTEGRITY_NOT_VALIDATED')
    vals=(current_stream_fingerprint,current_baseline_fingerprint,current_policy_fingerprint,current_shadow_fingerprint,current_request_context_fingerprint,current_result_fingerprint)
    exp=(st.stream_fingerprint,st.baseline_fingerprint,st.policy_fingerprint,st.shadow_fingerprint,st.request_context_fingerprint,st.result_fingerprint)
    if vals!=exp:return _invalid(st.request,'PREPARED_FINGERPRINT_MISMATCH')
    if _fp(exp+(st.binding,st.state_epoch))!=st.integrity_fingerprint:return _invalid(st.request,'PREPARED_INTEGRITY_MISMATCH')
    return st.result
def _manifest(st): return _fp((st.stream_fingerprint,st.baseline_fingerprint,st.policy_fingerprint,st.shadow_fingerprint,st.request_context_fingerprint,st.result_fingerprint))
def make_delta(a,b): return DriftDelta(a.stream_fingerprint!=b.stream_fingerprint,a.baseline_fingerprint!=b.baseline_fingerprint,a.policy_fingerprint!=b.policy_fingerprint,a.shadow_fingerprint!=b.shadow_fingerprint,a.request_context_fingerprint!=b.request_context_fingerprint,_manifest(a),_manifest(b))
def plan_missing_only(a,b):
    d=make_delta(a,b); names=[]
    for flag,name in ((d.stream_changed,'FEATURE_OUTCOME_STREAM'),(d.baseline_changed,'BASELINE_DISTRIBUTION'),(d.policy_changed,'DRIFT_POLICY'),(d.shadow_changed,'SHADOW_CANARY_STATE'),(d.request_context_changed,'REQUEST_CONTEXT')):
        if flag:names.append(name)
    meta=len(_canon({'missing_or_changed_record_ids':names,'from':d.from_manifest_fingerprint,'to':d.to_manifest_fingerprint}))
    return MissingOnlyPlan(tuple(names),meta,False)
