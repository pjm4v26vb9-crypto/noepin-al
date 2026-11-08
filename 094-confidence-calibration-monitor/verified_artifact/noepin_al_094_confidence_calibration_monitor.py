"""NOEPIN AL 094 — Confidence Calibration Monitor — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Pure uncertainty / calibration control algorithm. It compares predicted confidence
with observed outcomes by task class and time window, computes calibration error,
Brier score, calibration curve, conservative adjusted confidence, sparse-history
uncertainty, and recent degradation. Calibration cache is never promoted to Truth,
Authority, Permission, Safety Proof, Action Execution, or Action Success.

Canonical identity: NOEPIN-AL-094
DCSR level: LIMITED INTEGRATION / 限定適用.
Provenance note: exact registered Origin GUID was not freshly reverified in this
completion session and is intentionally not guessed or regenerated.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str,Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class RiskLevel(str,Enum):
    LOW='LOW'; MEDIUM='MEDIUM'; HIGH='HIGH'; CRITICAL='CRITICAL'

@dataclass(frozen=True)
class CalibrationRequest:
    request_id:str; task_class:str; predicted_confidence:float; risk:RiskLevel
    now:int; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class CalibrationObservation:
    observation_id:str; task_class:str; predicted_confidence:float; observed_outcome:bool
    observed_at:int; source_version:str; model_version:str; evidence_fingerprint:str
    observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class CalibrationPolicy:
    bin_count:int; min_samples:int; recent_window:int; prior_accuracy:float; prior_strength:float
    severe_overconfidence_gap:float; drift_drop_threshold:float; max_ece_high:float
    max_brier_high:float; allow_adjusted_low:float; allow_adjusted_medium:float
    allow_adjusted_high:float; allow_adjusted_critical:float
    binding:str; state_epoch:str; revoked:bool=False
@dataclass(frozen=True)
class CalibrationResult:
    decision:Decision; reasons:tuple[str,...]; task_class:str; sample_count:int
    calibration_error_ece:float; brier_score:float
    calibration_curve:tuple[tuple[float,float,int,float,float,float],...]
    empirical_accuracy:float; mean_predicted_confidence:float; adjusted_confidence:float
    credible_interval:tuple[float,float]; overconfidence_gap:float; underconfidence_gap:float
    drift_detected:bool; recent_accuracy:float|None; previous_accuracy:float|None
    sparse_history:bool; authority_shrink_candidate:bool; warning_candidate:bool
    next_gate_candidate:bool; reevaluation_candidate:bool
    permission_granted:bool=False; action_executed:bool=False; plan_committed:bool=False
    atomic_publish_executed:bool=False; external_write_performed:bool=False
    world_truth_proven:bool=False; authority_promoted:bool=False; safety_proven:bool=False
    action_success:bool=False
@dataclass(frozen=True)
class PreparedCalibrationState:
    request:CalibrationRequest; observations:tuple[CalibrationObservation,...]; policy:CalibrationPolicy
    record_fingerprints:tuple[tuple[str,str],...]; context_fingerprint:str
    dependency_fingerprint:str; calibration_fingerprint:str; registry_fingerprint:str
    precomputed_result:CalibrationResult; binding:str; state_epoch:str
@dataclass(frozen=True)
class CalibrationStateDelta:
    base_fingerprint:str; target_fingerprint:str
    changed_observations:tuple[CalibrationObservation,...]; removed_observation_ids:tuple[str,...]
    target_request:CalibrationRequest|None; target_policy:CalibrationPolicy|None
    binding:str; state_epoch:str
@dataclass(frozen=True)
class CalibrationSyncPlan:
    missing_or_changed_record_ids:tuple[str,...]; metadata_bytes_required:int; full_resend_required:bool

def _cv(x):
    if isinstance(x,Enum): return x.value
    if hasattr(x,'__dataclass_fields__'): return {k:_cv(getattr(x,k)) for k in x.__dataclass_fields__}
    if isinstance(x,tuple): return [_cv(v) for v in x]
    if isinstance(x,list): return [_cv(v) for v in x]
    if isinstance(x,dict): return {str(k):_cv(x[k]) for k in sorted(x)}
    return x
def _canon(x)->bytes: return json.dumps(_cv(x),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def _fp(x)->str: return sha256(_canon(x)).hexdigest()
def _clamp(v,lo=0.0,hi=1.0): return max(lo,min(hi,v))
def _hold(reason,task='',**kw):
    d=dict(sample_count=0,calibration_error_ece=1.0,brier_score=1.0,calibration_curve=(),empirical_accuracy=0.0,mean_predicted_confidence=0.0,adjusted_confidence=0.0,credible_interval=(0.0,1.0),overconfidence_gap=0.0,underconfidence_gap=0.0,drift_detected=False,recent_accuracy=None,previous_accuracy=None,sparse_history=True,authority_shrink_candidate=False,warning_candidate=True,next_gate_candidate=False,reevaluation_candidate=True)
    d.update(kw)
    return CalibrationResult(Decision.HOLD,(reason,),task,**d)

def _validate(req,obs,policy):
    if policy.revoked: return 'POLICY_REVOKED'
    if not req.observed: return 'REQUEST_UNOBSERVED'
    if not req.request_id or not req.task_class: return 'REQUEST_IDENTITY_INVALID'
    if req.binding!=policy.binding or req.state_epoch!=policy.state_epoch: return 'REQUEST_SCOPE_MISMATCH'
    if not math.isfinite(req.predicted_confidence) or not 0<=req.predicted_confidence<=1: return 'REQUEST_CONFIDENCE_INVALID'
    if policy.bin_count<2 or policy.min_samples<1 or policy.recent_window<1: return 'POLICY_COUNT_INVALID'
    floats=(policy.prior_accuracy,policy.severe_overconfidence_gap,policy.drift_drop_threshold,policy.max_ece_high,policy.max_brier_high,policy.allow_adjusted_low,policy.allow_adjusted_medium,policy.allow_adjusted_high,policy.allow_adjusted_critical)
    if any((not math.isfinite(v) or not 0<=v<=1) for v in floats): return 'POLICY_RANGE_INVALID'
    if not math.isfinite(policy.prior_strength) or policy.prior_strength<=0: return 'POLICY_PRIOR_STRENGTH_INVALID'
    ids=[x.observation_id for x in obs]
    if len(ids)!=len(set(ids)): return 'DUPLICATE_OBSERVATION_ID'
    for x in obs:
        if not x.observation_id or not x.source_version or not x.model_version or not x.evidence_fingerprint: return 'OBSERVATION_IDENTITY_INVALID'
        if not x.observed: return 'OBSERVATION_UNOBSERVED'
        if x.binding!=policy.binding or x.state_epoch!=policy.state_epoch: return 'OBSERVATION_SCOPE_MISMATCH'
        if not math.isfinite(x.predicted_confidence) or not 0<=x.predicted_confidence<=1: return 'OBSERVATION_CONFIDENCE_INVALID'
        if x.observed_at>req.now: return 'OBSERVATION_FROM_FUTURE'
    return None

def _curve(rows,bin_count):
    bins=[]
    for i in range(bin_count):
        lo=i/bin_count; hi=(i+1)/bin_count
        selected=[x for x in rows if (lo<=x.predicted_confidence<hi) or (i==bin_count-1 and x.predicted_confidence==1.0)]
        if not selected: continue
        mc=sum(x.predicted_confidence for x in selected)/len(selected)
        acc=sum(1.0 if x.observed_outcome else 0.0 for x in selected)/len(selected)
        bins.append((round(lo,12),round(hi,12),len(selected),round(mc,12),round(acc,12),round(abs(mc-acc),12)))
    return tuple(bins)

def evaluate(req:CalibrationRequest,observations:tuple[CalibrationObservation,...],policy:CalibrationPolicy)->CalibrationResult:
    observations=tuple(sorted(observations,key=lambda x:(x.observed_at,x.observation_id)))
    err=_validate(req,observations,policy)
    if err: return _hold(err,req.task_class)
    rows=tuple(x for x in observations if x.task_class==req.task_class)
    n=len(rows)
    if n==0:
        lo=max(0.0,policy.prior_accuracy-.35); hi=min(1.0,policy.prior_accuracy+.35)
        adjusted=_clamp(.25*req.predicted_confidence+.75*policy.prior_accuracy)
        return _hold('NO_TASK_HISTORY',req.task_class,sample_count=0,adjusted_confidence=adjusted,credible_interval=(lo,hi),sparse_history=True)
    outcomes=[1.0 if x.observed_outcome else 0.0 for x in rows]
    mean_pred=sum(x.predicted_confidence for x in rows)/n
    empirical=sum(outcomes)/n
    brier=sum((x.predicted_confidence-y)**2 for x,y in zip(rows,outcomes))/n
    curve=_curve(rows,policy.bin_count)
    ece=sum((b[2]/n)*b[5] for b in curve)
    sparse=n<policy.min_samples
    # Conservative prior is applied only in sparse-history regions. Once the
    # Canonical minimum history is met, calibration is driven by observed data.
    smoothed=((sum(outcomes)+policy.prior_strength*policy.prior_accuracy)/(n+policy.prior_strength)) if sparse else empirical
    bias=mean_pred-smoothed
    adjusted=_clamp(req.predicted_confidence-bias)
    if sparse:
        alpha=n/policy.min_samples
        adjusted=_clamp(alpha*adjusted+(1-alpha)*policy.prior_accuracy)
    eff_n=(n+policy.prior_strength) if sparse else n
    width=1.96*math.sqrt(max(1e-12,smoothed*(1-smoothed)/eff_n))
    if sparse: width=max(width,(1-n/policy.min_samples)*.25)
    interval=(_clamp(adjusted-width),_clamp(adjusted+width))
    over=max(0.0,mean_pred-empirical); under=max(0.0,empirical-mean_pred)
    recent_acc=previous_acc=None; drift=False
    w=policy.recent_window
    if n>=2*w:
        prev=outcomes[-2*w:-w]; recent=outcomes[-w:]
        previous_acc=sum(prev)/len(prev); recent_acc=sum(recent)/len(recent)
        drift=(previous_acc-recent_acc)>=policy.drift_drop_threshold
    authority_shrink=over>=policy.severe_overconfidence_gap or drift
    threshold={RiskLevel.LOW:policy.allow_adjusted_low,RiskLevel.MEDIUM:policy.allow_adjusted_medium,RiskLevel.HIGH:policy.allow_adjusted_high,RiskLevel.CRITICAL:policy.allow_adjusted_critical}[req.risk]
    reasons=[]
    if sparse: reasons.append('SPARSE_HISTORY_CONSERVATIVE_PRIOR')
    if over>=policy.severe_overconfidence_gap: reasons.append('OVERCONFIDENCE_DETECTED')
    if under>=policy.severe_overconfidence_gap: reasons.append('UNDERCONFIDENCE_DETECTED')
    if drift:
        reasons.append('RAPID_CALIBRATION_DEGRADATION')
        return CalibrationResult(Decision.HOLD,tuple(reasons),req.task_class,n,ece,brier,curve,empirical,mean_pred,adjusted,interval,over,under,drift,recent_acc,previous_acc,sparse,True,True,False,True)
    if req.risk in (RiskLevel.HIGH,RiskLevel.CRITICAL) and sparse:
        reasons.append('SPARSE_HISTORY_HIGH_RISK')
        return CalibrationResult(Decision.HOLD,tuple(reasons),req.task_class,n,ece,brier,curve,empirical,mean_pred,adjusted,interval,over,under,False,recent_acc,previous_acc,True,authority_shrink,True,False,True)
    if req.risk in (RiskLevel.HIGH,RiskLevel.CRITICAL) and (ece>policy.max_ece_high or brier>policy.max_brier_high or over>=policy.severe_overconfidence_gap):
        reasons.append('CALIBRATION_UNSAFE_FOR_HIGH_RISK')
        return CalibrationResult(Decision.HOLD,tuple(reasons),req.task_class,n,ece,brier,curve,empirical,mean_pred,adjusted,interval,over,under,False,recent_acc,previous_acc,sparse,authority_shrink,True,False,True)
    if adjusted < threshold:
        reasons.append('ADJUSTED_CONFIDENCE_BELOW_THRESHOLD')
        return CalibrationResult(Decision.HOLD,tuple(reasons),req.task_class,n,ece,brier,curve,empirical,mean_pred,adjusted,interval,over,under,False,recent_acc,previous_acc,sparse,authority_shrink,True,False,True)
    if not reasons: reasons.append('CALIBRATION_ACCEPTABLE')
    return CalibrationResult(Decision.ALLOW,tuple(reasons),req.task_class,n,ece,brier,curve,empirical,mean_pred,adjusted,interval,over,under,False,recent_acc,previous_acc,sparse,authority_shrink,bool(authority_shrink),True,False)

def default_policy():
    return CalibrationPolicy(10,20,10,.50,8.0,.20,.25,.20,.30,.60,.65,.75,.85,'CCM-BIND','STATE-EPOCH-1')
def default_request(): return CalibrationRequest('REQ-94','FACT_VERIFY',.80,RiskLevel.LOW,1000,True,'CCM-BIND','STATE-EPOCH-1')
def default_observations():
    p=default_policy(); rows=[]
    # 40 samples, exactly 80% correct at predicted confidence 0.80, stable across time.
    for i in range(40):
        rows.append(CalibrationObservation(f'O{i:03d}','FACT_VERIFY',.80,(i%5)!=4,100+i,'SRC-V1','MODEL-V1',f'EFP-{i:03d}',True,p.binding,p.state_epoch))
    return tuple(rows)
def default_evaluation(): return evaluate(default_request(),default_observations(),default_policy())

def _records(obs): return tuple(sorted(obs,key=lambda x:(x.observed_at,x.observation_id)))
def _record_fps(obs): return tuple(sorted((f'OBS:{x.observation_id}',_fp(x)) for x in obs))
def _calibration_fp(policy):
    return _fp((policy.bin_count,policy.min_samples,policy.recent_window,policy.prior_accuracy,policy.prior_strength,policy.severe_overconfidence_gap,policy.drift_drop_threshold,policy.max_ece_high,policy.max_brier_high,policy.allow_adjusted_low,policy.allow_adjusted_medium,policy.allow_adjusted_high,policy.allow_adjusted_critical))
def prepare_state(req,observations,policy,*,binding,state_epoch):
    o=_records(observations); r=evaluate(req,o,policy); rec=_record_fps(o)
    return PreparedCalibrationState(req,o,policy,rec,_fp(req),_fp(o),_calibration_fp(policy),_fp(rec),r,binding,state_epoch)
def validate_prepared_integrity(st):
    if st.binding!=st.policy.binding or st.state_epoch!=st.policy.state_epoch: return False
    o=_records(st.observations); rec=_record_fps(o)
    return rec==st.record_fingerprints and st.context_fingerprint==_fp(st.request) and st.dependency_fingerprint==_fp(o) and st.calibration_fingerprint==_calibration_fp(st.policy) and st.registry_fingerprint==_fp(rec) and st.precomputed_result==evaluate(st.request,o,st.policy)
def evaluate_prepared(st,*,current_context_fingerprint,current_dependency_fingerprint,current_calibration_fingerprint,current_registry_fingerprint,prepared_integrity_validated):
    if not prepared_integrity_validated: return _hold('PREPARED_INTEGRITY_NOT_VALIDATED',st.request.task_class)
    if current_context_fingerprint!=st.context_fingerprint: return _hold('CONTEXT_FINGERPRINT_MISMATCH',st.request.task_class)
    if current_dependency_fingerprint!=st.dependency_fingerprint: return _hold('DEPENDENCY_FINGERPRINT_MISMATCH',st.request.task_class)
    if current_calibration_fingerprint!=st.calibration_fingerprint: return _hold('CALIBRATION_FINGERPRINT_MISMATCH',st.request.task_class)
    if current_registry_fingerprint!=st.registry_fingerprint: return _hold('REGISTRY_FINGERPRINT_MISMATCH',st.request.task_class)
    return st.precomputed_result

def make_delta(base,target):
    bm={x.observation_id:x for x in base.observations}; tm={x.observation_id:x for x in target.observations}
    changed=tuple(tm[k] for k in sorted(tm) if k not in bm or _fp(tm[k])!=_fp(bm[k])); removed=tuple(sorted(k for k in bm if k not in tm))
    return CalibrationStateDelta(base.registry_fingerprint,target.registry_fingerprint,changed,removed,None if base.request==target.request else target.request,None if base.policy==target.policy else target.policy,target.binding,target.state_epoch)
def apply_delta(base,delta):
    if base.registry_fingerprint!=delta.base_fingerprint: raise ValueError('BASE_FINGERPRINT_MISMATCH')
    m={x.observation_id:x for x in base.observations}
    for k in delta.removed_observation_ids: m.pop(k,None)
    for x in delta.changed_observations: m[x.observation_id]=x
    out=prepare_state(delta.target_request or base.request,tuple(m.values()),delta.target_policy or base.policy,binding=delta.binding,state_epoch=delta.state_epoch)
    if out.registry_fingerprint!=delta.target_fingerprint: raise ValueError('TARGET_FINGERPRINT_MISMATCH')
    return out
def missing_only_sync_plan(target,known_record_fingerprints:dict[str,str]):
    miss=tuple(sorted(k for k,v in target.record_fingerprints if known_record_fingerprints.get(k)!=v)); metadata=len(_canon(miss)); full=len(miss)>max(1000,int(len(target.record_fingerprints)*.75)); return CalibrationSyncPlan(miss,metadata,full)
def full_registry_bytes(st): return len(_canon({'request':st.request,'observations':st.observations,'policy':st.policy}))
def delta_bytes(delta): return len(_canon(delta))
