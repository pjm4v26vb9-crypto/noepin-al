"""NOEPIN AL 098 — Epistemic-Aleatoric Splitter — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Pure uncertainty-control evidence. The module separates model/knowledge uncertainty
(epistemic) from observation/process noise (aleatoric) when evidence supports the
separation. It never claims that epistemic uncertainty is certainly resolvable by
more information, or that aleatoric uncertainty proves intrinsic randomness.
It never promotes scores/cache state to Truth/Authority; never grants permission,
executes research/actions, commits, publishes, writes externally, proves Safety,
or asserts Action Success.

Canonical identity: NOEPIN-AL-098
DCSR level: LIMITED INTEGRATION / 限定適用.
Provenance note: exact registered Origin GUID was not freshly reverified in this
completion session and is intentionally not guessed or regenerated.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, IntEnum
from hashlib import sha256
import json, math

class Decision(str, Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class RiskLevel(IntEnum):
    LOW=1; MEDIUM=2; HIGH=3; CRITICAL=4
class SeparationStatus(str, Enum):
    SEPARATED='SEPARATED'; INSEPARABLE='INSEPARABLE'
class NextAction(str, Enum):
    CONTINUE_CANDIDATE='CONTINUE_CANDIDATE'
    RESEARCH_CANDIDATE='RESEARCH_CANDIDATE'
    RISK_AWARE_DECISION_CANDIDATE='RISK_AWARE_DECISION_CANDIDATE'
    HUMAN_APPROVAL_CANDIDATE='HUMAN_APPROVAL_CANDIDATE'
    HOLD_UNRESOLVED='HOLD_UNRESOLVED'

@dataclass(frozen=True)
class UncertaintyQuery:
    request_id:str; target_id:str; risk:RiskLevel; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class PredictionRecord:
    prediction_id:str; model_id:str; run_id:str; predicted_value:float; observation_noise_variance:float|None
    weight:float; source_id:str; source_version:str; source_fingerprint:str; evidence_fingerprint:str
    observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class UncertaintyPolicy:
    epistemic_threshold_low:float; epistemic_threshold_medium:float; epistemic_threshold_high:float; epistemic_threshold_critical:float
    aleatoric_threshold_low:float; aleatoric_threshold_medium:float; aleatoric_threshold_high:float; aleatoric_threshold_critical:float
    minimum_distinct_models:int; minimum_predictions:int; variance_scale:float
    binding:str; state_epoch:str; revoked:bool=False
@dataclass(frozen=True)
class UncertaintyResult:
    decision:Decision; separation_status:SeparationStatus; next_action:NextAction; reasons:tuple[str,...]
    epistemic_variance:float; aleatoric_variance:float; total_variance:float
    epistemic_score:float; aleatoric_score:float; epistemic_fraction:float; aleatoric_fraction:float
    distinct_models:int; prediction_count:int; noise_observed_count:int
    research_candidate:bool; human_approval_candidate:bool; next_gate_candidate:bool
    cache_promoted_to_truth:bool=False; cache_promoted_to_authority:bool=False
    permission_granted:bool=False; research_executed:bool=False; action_executed:bool=False
    plan_committed:bool=False; atomic_publish_executed:bool=False; external_write_performed:bool=False
    world_truth_proven:bool=False; intrinsic_randomness_proven:bool=False; resolvability_proven:bool=False
    safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedUncertaintyState:
    query:UncertaintyQuery; predictions:tuple[PredictionRecord,...]; policy:UncertaintyPolicy
    record_fingerprints:tuple[tuple[str,str],...]; context_fingerprint:str; dependency_fingerprint:str
    calibration_fingerprint:str; registry_fingerprint:str; precomputed_result:UncertaintyResult
    binding:str; state_epoch:str
@dataclass(frozen=True)
class UncertaintyStateDelta:
    base_fingerprint:str; target_fingerprint:str; changed_predictions:tuple[PredictionRecord,...]
    removed_prediction_ids:tuple[str,...]; target_query:UncertaintyQuery|None; target_policy:UncertaintyPolicy|None
    binding:str; state_epoch:str
@dataclass(frozen=True)
class UncertaintySyncPlan:
    missing_or_changed_record_ids:tuple[str,...]; metadata_bytes_required:int; full_resend_required:bool

def _cv(x):
    if isinstance(x,Enum): return x.name if isinstance(x,IntEnum) else x.value
    if hasattr(x,'__dataclass_fields__'): return {k:_cv(getattr(x,k)) for k in x.__dataclass_fields__}
    if isinstance(x,tuple): return [_cv(v) for v in x]
    if isinstance(x,list): return [_cv(v) for v in x]
    if isinstance(x,dict): return {str(k):_cv(x[k]) for k in sorted(x)}
    return x
def _canon(x)->bytes: return json.dumps(_cv(x),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def _fp(x)->str: return sha256(_canon(x)).hexdigest()
def _clamp01(x:float)->float: return max(0.0,min(1.0,x))
def _eth(r:RiskLevel,p:UncertaintyPolicy)->float:
    return {RiskLevel.LOW:p.epistemic_threshold_low,RiskLevel.MEDIUM:p.epistemic_threshold_medium,RiskLevel.HIGH:p.epistemic_threshold_high,RiskLevel.CRITICAL:p.epistemic_threshold_critical}[r]
def _ath(r:RiskLevel,p:UncertaintyPolicy)->float:
    return {RiskLevel.LOW:p.aleatoric_threshold_low,RiskLevel.MEDIUM:p.aleatoric_threshold_medium,RiskLevel.HIGH:p.aleatoric_threshold_high,RiskLevel.CRITICAL:p.aleatoric_threshold_critical}[r]
def _score(v:float,scale:float)->float:
    if v<=0: return 0.0
    return _clamp01(v/(v+scale))
def _hold(reason:str,q:UncertaintyQuery,*,status=SeparationStatus.INSEPARABLE,next_action=NextAction.HOLD_UNRESOLVED,ev=0.0,av=0.0,distinct=0,count=0,noise_count=0,research=False,human=False,p=None):
    tv=max(0.0,ev)+max(0.0,av); scale=(p.variance_scale if p is not None and p.variance_scale>0 else 1.0)
    es=_score(max(0.0,ev),scale); a_s=_score(max(0.0,av),scale); ef=(max(0.0,ev)/tv if tv>0 else 0.0); af=(max(0.0,av)/tv if tv>0 else 0.0)
    return UncertaintyResult(Decision.HOLD,status,next_action,(reason,),max(0.0,ev),max(0.0,av),tv,es,a_s,ef,af,distinct,count,noise_count,research,human,False)

def _validate(q,preds,p):
    if p.revoked: return 'POLICY_REVOKED'
    if not q.observed or not q.request_id or not q.target_id: return 'QUERY_INVALID'
    if q.binding!=p.binding or q.state_epoch!=p.state_epoch: return 'QUERY_SCOPE_MISMATCH'
    vals=(p.epistemic_threshold_low,p.epistemic_threshold_medium,p.epistemic_threshold_high,p.epistemic_threshold_critical,p.aleatoric_threshold_low,p.aleatoric_threshold_medium,p.aleatoric_threshold_high,p.aleatoric_threshold_critical)
    if any((not math.isfinite(v) or not 0<=v<=1) for v in vals): return 'POLICY_THRESHOLD_INVALID'
    if p.minimum_distinct_models<1 or p.minimum_predictions<1 or not math.isfinite(p.variance_scale) or p.variance_scale<=0: return 'POLICY_PARAMETER_INVALID'
    ids=[x.prediction_id for x in preds]
    if not ids: return 'NO_PREDICTIONS'
    if len(ids)!=len(set(ids)): return 'DUPLICATE_PREDICTION_ID'
    for x in preds:
        if not x.observed or not all((x.prediction_id,x.model_id,x.run_id,x.source_id,x.source_version,x.source_fingerprint,x.evidence_fingerprint)): return 'PREDICTION_RECORD_INVALID'
        if x.binding!=p.binding or x.state_epoch!=p.state_epoch: return 'PREDICTION_SCOPE_MISMATCH'
        if not math.isfinite(x.predicted_value) or not math.isfinite(x.weight) or x.weight<=0: return 'PREDICTION_VALUE_INVALID'
        if x.observation_noise_variance is not None and (not math.isfinite(x.observation_noise_variance) or x.observation_noise_variance<0): return 'NOISE_VARIANCE_INVALID'
    return None

def evaluate(q:UncertaintyQuery,preds:tuple[PredictionRecord,...],p:UncertaintyPolicy)->UncertaintyResult:
    preds=tuple(sorted(preds,key=lambda x:x.prediction_id)); err=_validate(q,preds,p)
    if err: return _hold(err,q,p=p,count=len(preds),distinct=len({x.model_id for x in preds}),noise_count=sum(x.observation_noise_variance is not None for x in preds))
    count=len(preds); distinct=len({x.model_id for x in preds}); noise_count=sum(x.observation_noise_variance is not None for x in preds)
    # Separation is not claimed unless repeated/ensemble prediction diversity and noise estimates exist.
    if count<p.minimum_predictions or distinct<p.minimum_distinct_models or noise_count<count:
        return _hold('UNCERTAINTY_SEPARATION_INSUFFICIENT_EVIDENCE',q,p=p,count=count,distinct=distinct,noise_count=noise_count)
    tw=sum(x.weight for x in preds)
    mean=sum(x.weight*x.predicted_value for x in preds)/tw
    epistemic=sum(x.weight*((x.predicted_value-mean)**2) for x in preds)/tw
    aleatoric=sum(x.weight*(x.observation_noise_variance or 0.0) for x in preds)/tw
    total=epistemic+aleatoric
    es=_score(epistemic,p.variance_scale); als=_score(aleatoric,p.variance_scale)
    ef=epistemic/total if total>0 else 0.0; af=aleatoric/total if total>0 else 0.0
    et=_eth(q.risk,p); at=_ath(q.risk,p)
    if es>=et:
        reasons=['EPISTEMIC_HIGH']
        if als>=at: reasons.append('ALEATORIC_HIGH')
        return UncertaintyResult(Decision.HOLD,SeparationStatus.SEPARATED,NextAction.RESEARCH_CANDIDATE,tuple(reasons),epistemic,aleatoric,total,es,als,ef,af,distinct,count,noise_count,True,q.risk==RiskLevel.CRITICAL and als>=at,False)
    if als>=at:
        if q.risk==RiskLevel.CRITICAL:
            return UncertaintyResult(Decision.HUMAN_APPROVAL,SeparationStatus.SEPARATED,NextAction.HUMAN_APPROVAL_CANDIDATE,('ALEATORIC_HIGH_CRITICAL',),epistemic,aleatoric,total,es,als,ef,af,distinct,count,noise_count,False,True,False)
        return UncertaintyResult(Decision.HOLD,SeparationStatus.SEPARATED,NextAction.RISK_AWARE_DECISION_CANDIDATE,('ALEATORIC_HIGH',),epistemic,aleatoric,total,es,als,ef,af,distinct,count,noise_count,False,False,False)
    return UncertaintyResult(Decision.ALLOW,SeparationStatus.SEPARATED,NextAction.CONTINUE_CANDIDATE,('UNCERTAINTY_LOW',),epistemic,aleatoric,total,es,als,ef,af,distinct,count,noise_count,False,False,True)

def default_policy():
    # Thresholds become stricter as risk rises.
    return UncertaintyPolicy(.65,.55,.45,.35,.75,.65,.50,.35,2,3,.01,'EAS-BIND','STATE-EPOCH-1')
def default_query():
    p=default_policy(); return UncertaintyQuery('REQ-98','TARGET-1',RiskLevel.LOW,True,p.binding,p.state_epoch)
def default_predictions():
    p=default_policy()
    return (
        PredictionRecord('P1','MODEL-A','RUN-1',.50,.001,.95,'SRC-A','V1','SFP-A','EFP-A',True,p.binding,p.state_epoch),
        PredictionRecord('P2','MODEL-B','RUN-1',.51,.001,.95,'SRC-B','V1','SFP-B','EFP-B',True,p.binding,p.state_epoch),
        PredictionRecord('P3','MODEL-C','RUN-1',.49,.001,.95,'SRC-C','V1','SFP-C','EFP-C',True,p.binding,p.state_epoch),
    )
def default_evaluation(): return evaluate(default_query(),default_predictions(),default_policy())

def _record_fingerprints(preds): return tuple((f'PRED:{x.prediction_id}',_fp(x)) for x in sorted(preds,key=lambda x:x.prediction_id))
def _context_fp(q,p): return _fp((q,p.binding,p.state_epoch))
def _dependency_fp(preds): return _fp(_record_fingerprints(preds))
def _calibration_fp(p): return _fp((p.epistemic_threshold_low,p.epistemic_threshold_medium,p.epistemic_threshold_high,p.epistemic_threshold_critical,p.aleatoric_threshold_low,p.aleatoric_threshold_medium,p.aleatoric_threshold_high,p.aleatoric_threshold_critical,p.minimum_distinct_models,p.minimum_predictions,p.variance_scale))
def _registry_fp(q,preds,p): return _fp((q,_record_fingerprints(preds),p))
def prepare_state(q,preds,p,*,binding:str,state_epoch:str):
    preds=tuple(sorted(preds,key=lambda x:x.prediction_id)); fps=_record_fingerprints(preds)
    return PreparedUncertaintyState(q,preds,p,fps,_context_fp(q,p),_dependency_fp(preds),_calibration_fp(p),_registry_fp(q,preds,p),evaluate(q,preds,p),binding,state_epoch)
def validate_prepared_integrity(st):
    if st.binding!=st.policy.binding or st.state_epoch!=st.policy.state_epoch: return False
    if st.record_fingerprints!=_record_fingerprints(st.predictions): return False
    if st.context_fingerprint!=_context_fp(st.query,st.policy): return False
    if st.dependency_fingerprint!=_dependency_fp(st.predictions): return False
    if st.calibration_fingerprint!=_calibration_fp(st.policy): return False
    if st.registry_fingerprint!=_registry_fp(st.query,st.predictions,st.policy): return False
    return st.precomputed_result==evaluate(st.query,st.predictions,st.policy)
def evaluate_prepared(st,*,current_context_fingerprint,current_dependency_fingerprint,current_calibration_fingerprint,current_registry_fingerprint,prepared_integrity_validated):
    if not prepared_integrity_validated: return _hold('PREPARED_INTEGRITY_NOT_VALIDATED',st.query,p=st.policy)
    if current_context_fingerprint!=st.context_fingerprint: return _hold('PREPARED_CONTEXT_MISMATCH',st.query,p=st.policy)
    if current_dependency_fingerprint!=st.dependency_fingerprint: return _hold('PREPARED_DEPENDENCY_MISMATCH',st.query,p=st.policy)
    if current_calibration_fingerprint!=st.calibration_fingerprint: return _hold('PREPARED_CALIBRATION_MISMATCH',st.query,p=st.policy)
    if current_registry_fingerprint!=st.registry_fingerprint: return _hold('PREPARED_REGISTRY_MISMATCH',st.query,p=st.policy)
    return st.precomputed_result

def make_delta(base,target):
    bb={x.prediction_id:x for x in base.predictions}; tb={x.prediction_id:x for x in target.predictions}
    changed=tuple(tb[k] for k in sorted(tb) if k not in bb or _fp(tb[k])!=_fp(bb[k]))
    return UncertaintyStateDelta(base.registry_fingerprint,target.registry_fingerprint,changed,tuple(sorted(set(bb)-set(tb))),target.query if target.query!=base.query else None,target.policy if target.policy!=base.policy else None,target.binding,target.state_epoch)
def apply_delta(base,d):
    if base.registry_fingerprint!=d.base_fingerprint: raise ValueError('BASE_FINGERPRINT_MISMATCH')
    bm={x.prediction_id:x for x in base.predictions}
    for k in d.removed_prediction_ids: bm.pop(k,None)
    for x in d.changed_predictions: bm[x.prediction_id]=x
    out=prepare_state(d.target_query or base.query,tuple(bm.values()),d.target_policy or base.policy,binding=d.binding,state_epoch=d.state_epoch)
    if out.registry_fingerprint!=d.target_fingerprint: raise ValueError('TARGET_FINGERPRINT_MISMATCH')
    return out
def missing_only_sync_plan(target,known_record_fingerprints):
    missing=tuple(k for k,v in target.record_fingerprints if known_record_fingerprints.get(k)!=v)
    meta=len(_canon({'context':target.context_fingerprint,'dependency':target.dependency_fingerprint,'calibration':target.calibration_fingerprint,'registry':target.registry_fingerprint,'missing':missing}))
    return UncertaintySyncPlan(missing,meta,False)
def full_registry_bytes(st): return len(_canon((st.query,st.predictions,st.policy)))
def delta_bytes(d): return len(_canon(d))
