"""NOEPIN AL 088 — Decision Freshness Window Verifier — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Pure freshness-window verification algorithm. It evaluates Decision Time, dependency
observation age, volatility, criticality, source/version/evidence fingerprints and
Risk. It emits refresh/re-evaluation/gate candidates only. It does not promote a
freshness cache to Truth or Authority, grant permission, execute actions, commit or
publish state, prove World Truth/Safety, or establish Action Success.

Canonical identity: NOEPIN-AL-088
DCSR level: LIMITED INTEGRATION / 限定適用.
Provenance note: exact registered Origin GUID was not freshly reverified in this
completion session and is intentionally not guessed or regenerated.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
import math

class Decision(str, Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class RiskLevel(str, Enum):
    LOW='LOW'; MEDIUM='MEDIUM'; HIGH='HIGH'; CRITICAL='CRITICAL'
class Criticality(str, Enum):
    LOW='LOW'; MEDIUM='MEDIUM'; HIGH='HIGH'; CRITICAL='CRITICAL'
class FreshnessState(str, Enum):
    FRESH='FRESH'; EXPIRED='EXPIRED'; PARTIAL_EXPIRED='PARTIAL_EXPIRED'; UNKNOWN='UNKNOWN'; HOLD='HOLD'
class ReevaluationFlag(str, Enum):
    NONE='NONE'; REFRESH_FIELDS='REFRESH_FIELDS'; REEVALUATE_DECISION='REEVALUATE_DECISION'

@dataclass(frozen=True)
class FreshnessRequest:
    decision_id:str; decision_time:float; now:float; risk:RiskLevel; observed:bool; binding:str; state_epoch:str

@dataclass(frozen=True)
class DependencyFreshness:
    field_id:str; last_observed_at:float; volatility_score:float|None; criticality:Criticality
    source_id:str; source_version:str; evidence_fingerprint:str; observed:bool; binding:str; state_epoch:str

@dataclass(frozen=True)
class FreshnessPolicy:
    low_window_seconds:float; medium_window_seconds:float; high_window_seconds:float; critical_window_seconds:float
    unknown_volatility_low_window_seconds:float; unknown_volatility_high_window_seconds:float
    min_window_seconds:float; max_clock_skew_seconds:float; binding:str; state_epoch:str; revoked:bool=False

@dataclass(frozen=True)
class FreshnessResult:
    decision:Decision; freshness_state:FreshnessState; reasons:tuple[str,...]
    freshness_window_seconds:float; expired_fields:tuple[str,...]; refresh_required_fields:tuple[str,...]
    unknown_volatility_fields:tuple[str,...]; reevaluation_required:bool; reevaluation_flag:ReevaluationFlag
    next_gate_candidate:bool; cache_reuse_candidate:bool
    cache_promoted_to_truth:bool=False; cache_promoted_to_authority:bool=False
    permission_granted:bool=False; action_executed:bool=False; plan_committed:bool=False
    atomic_publish_executed:bool=False; external_write_performed:bool=False
    world_truth_proven:bool=False; safety_proven:bool=False; action_success:bool=False

@dataclass(frozen=True)
class PreparedFreshnessState:
    request:FreshnessRequest; dependencies:tuple[DependencyFreshness,...]; policy:FreshnessPolicy
    dependency_fingerprints:tuple[tuple[str,str],...]
    context_fingerprint:str; dependency_fingerprint:str; calibration_fingerprint:str; registry_fingerprint:str
    precomputed_result:FreshnessResult; binding:str; state_epoch:str

@dataclass(frozen=True)
class FreshnessStateDelta:
    base_fingerprint:str; target_fingerprint:str
    changed_dependencies:tuple[DependencyFreshness,...]; removed_field_ids:tuple[str,...]
    target_request:FreshnessRequest|None; target_policy:FreshnessPolicy|None
    binding:str; state_epoch:str

@dataclass(frozen=True)
class FreshnessSyncPlan:
    missing_or_changed_field_ids:tuple[str,...]; metadata_bytes_required:int; full_resend_required:bool


def _cv(x):
    if isinstance(x,Enum): return x.value
    if hasattr(x,'__dataclass_fields__'): return {k:_cv(getattr(x,k)) for k in x.__dataclass_fields__}
    if isinstance(x,tuple): return [_cv(v) for v in x]
    if isinstance(x,list): return [_cv(v) for v in x]
    if isinstance(x,dict): return {str(k):_cv(x[k]) for k in sorted(x)}
    return x

def _canon(x)->bytes:
    return json.dumps(_cv(x),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def _fp(x)->str: return sha256(_canon(x)).hexdigest()

def _base_window(risk:RiskLevel,p:FreshnessPolicy)->float:
    return {RiskLevel.LOW:p.low_window_seconds,RiskLevel.MEDIUM:p.medium_window_seconds,RiskLevel.HIGH:p.high_window_seconds,RiskLevel.CRITICAL:p.critical_window_seconds}[risk]

def _criticality_factor(c:Criticality)->float:
    return {Criticality.LOW:1.0,Criticality.MEDIUM:0.75,Criticality.HIGH:0.5,Criticality.CRITICAL:0.25}[c]

def _field_window(dep:DependencyFreshness,risk:RiskLevel,p:FreshnessPolicy)->float:
    base=_base_window(risk,p)*_criticality_factor(dep.criticality)
    if dep.volatility_score is None:
        unknown=p.unknown_volatility_high_window_seconds if risk in (RiskLevel.HIGH,RiskLevel.CRITICAL) else p.unknown_volatility_low_window_seconds
        return max(p.min_window_seconds,min(base,unknown))
    factor=max(0.1,1.0-0.9*dep.volatility_score)
    return max(p.min_window_seconds,base*factor)

def _hold(reason:str,*,state=FreshnessState.HOLD,window=0.0,expired=(),refresh=(),unknown=(),flag=ReevaluationFlag.REEVALUATE_DECISION):
    return FreshnessResult(Decision.HOLD,state,(reason,),float(max(0.0,window)),tuple(expired),tuple(refresh),tuple(unknown),True,flag,False,False)

def _validate_common(req,deps,policy):
    if policy.revoked: return 'POLICY_REVOKED'
    nums=(policy.low_window_seconds,policy.medium_window_seconds,policy.high_window_seconds,policy.critical_window_seconds,policy.unknown_volatility_low_window_seconds,policy.unknown_volatility_high_window_seconds,policy.min_window_seconds,policy.max_clock_skew_seconds,req.decision_time,req.now)
    if not all(math.isfinite(float(x)) for x in nums): return 'NONFINITE_TIME_OR_POLICY'
    if min(policy.low_window_seconds,policy.medium_window_seconds,policy.high_window_seconds,policy.critical_window_seconds,policy.unknown_volatility_low_window_seconds,policy.unknown_volatility_high_window_seconds,policy.min_window_seconds)<=0: return 'INVALID_WINDOW_POLICY'
    if policy.max_clock_skew_seconds<0: return 'INVALID_CLOCK_SKEW_POLICY'
    if req.binding!=policy.binding or req.state_epoch!=policy.state_epoch: return 'REQUEST_SCOPE_MISMATCH'
    if not req.decision_id: return 'EMPTY_DECISION_ID'
    if req.decision_time<0 or req.now<0: return 'INVALID_TIME'
    if len({d.field_id for d in deps})!=len(deps): return 'DUPLICATE_FIELD_ID'
    if not deps: return 'NO_DEPENDENCY_EVIDENCE'
    for d in deps:
        if d.binding!=policy.binding or d.state_epoch!=policy.state_epoch: return 'DEPENDENCY_SCOPE_MISMATCH'
        if not d.field_id: return 'EMPTY_FIELD_ID'
        if d.last_observed_at<0 or not math.isfinite(float(d.last_observed_at)): return 'INVALID_OBSERVATION_TIME'
        if d.volatility_score is not None and (not math.isfinite(float(d.volatility_score)) or d.volatility_score<0 or d.volatility_score>1): return 'INVALID_VOLATILITY_SCORE'
        if not d.source_id or not d.source_version or not d.evidence_fingerprint: return 'INCOMPLETE_EVIDENCE_IDENTITY'
    return None

def evaluate(req:FreshnessRequest,deps:tuple[DependencyFreshness,...],policy:FreshnessPolicy)->FreshnessResult:
    err=_validate_common(req,deps,policy)
    if err: return _hold(err)
    if not req.observed: return _hold('REQUEST_UNOBSERVED')
    skew=policy.max_clock_skew_seconds
    if req.decision_time>req.now+skew: return _hold('DECISION_TIME_AHEAD_OF_CLOCK')
    ordered=tuple(sorted(deps,key=lambda x:x.field_id))
    unobserved=tuple(d.field_id for d in ordered if not d.observed)
    if unobserved:
        return _hold('DEPENDENCY_UNOBSERVED',state=FreshnessState.UNKNOWN,expired=unobserved,refresh=unobserved)
    future=tuple(d.field_id for d in ordered if d.last_observed_at>req.now+skew)
    if future:
        return _hold('DEPENDENCY_TIME_AHEAD_OF_CLOCK',state=FreshnessState.UNKNOWN,expired=future,refresh=future)
    windows={d.field_id:_field_window(d,req.risk,policy) for d in ordered}
    unknown=tuple(d.field_id for d in ordered if d.volatility_score is None)
    expired=tuple(d.field_id for d in ordered if max(0.0,req.now-d.last_observed_at)>windows[d.field_id])
    freshness_window=min(windows.values())
    decision_age=max(0.0,req.now-req.decision_time)
    decision_expired=decision_age>freshness_window
    reasons=[]
    if unknown: reasons.append('UNKNOWN_VOLATILITY_SHORT_WINDOW')
    if decision_expired: reasons.append('DECISION_WINDOW_EXPIRED')
    if expired: reasons.append('DEPENDENCY_WINDOW_EXPIRED')
    if decision_expired or expired:
        critical_expired=any(d.field_id in expired and d.criticality==Criticality.CRITICAL for d in ordered)
        high_risk=req.risk in (RiskLevel.HIGH,RiskLevel.CRITICAL)
        refresh=tuple(sorted(set(expired)))
        if decision_expired or critical_expired or high_risk:
            return FreshnessResult(Decision.HOLD,FreshnessState.EXPIRED,tuple(reasons or ['FRESHNESS_EXPIRED']),freshness_window,expired,refresh,unknown,True,ReevaluationFlag.REEVALUATE_DECISION,False,False)
        return FreshnessResult(Decision.HOLD,FreshnessState.PARTIAL_EXPIRED,tuple(reasons or ['PARTIAL_FRESHNESS_EXPIRED']),freshness_window,expired,refresh,unknown,True,ReevaluationFlag.REFRESH_FIELDS,False,False)
    return FreshnessResult(Decision.ALLOW,FreshnessState.FRESH,tuple(reasons or ['ALL_DEPENDENCIES_FRESH']),freshness_window,(),(),unknown,False,ReevaluationFlag.NONE,True,True)

def default_policy():
    return FreshnessPolicy(300.0,120.0,30.0,10.0,30.0,5.0,1.0,2.0,'FRESH-BIND','STATE-EPOCH-1')
def default_request():
    return FreshnessRequest('DECISION-1',1000.0,1010.0,RiskLevel.MEDIUM,True,'FRESH-BIND','STATE-EPOCH-1')
def default_dependencies():
    b,e='FRESH-BIND','STATE-EPOCH-1'
    return (
        DependencyFreshness('FIELD-A',1005.0,0.10,Criticality.HIGH,'SRC-A','V1','EVID-A',True,b,e),
        DependencyFreshness('FIELD-B',1000.0,0.20,Criticality.MEDIUM,'SRC-B','V1','EVID-B',True,b,e),
    )
def default_evaluation(): return evaluate(default_request(),default_dependencies(),default_policy())

def _calibration_fp(req,policy):
    return _fp({'risk':req.risk,'windows':(policy.low_window_seconds,policy.medium_window_seconds,policy.high_window_seconds,policy.critical_window_seconds,policy.unknown_volatility_low_window_seconds,policy.unknown_volatility_high_window_seconds,policy.min_window_seconds,policy.max_clock_skew_seconds)})
def _registry_fp(req,deps,policy):
    return _fp({'request':req,'dependencies':tuple(sorted(deps,key=lambda x:x.field_id)),'policy':policy})

def prepare_state(req,deps,policy,*,binding:str,state_epoch:str):
    deps=tuple(sorted(deps,key=lambda x:x.field_id))
    fps=tuple((d.field_id,_fp(d)) for d in deps)
    context=_fp({'request':req,'policy':policy})
    dependency=_fp({'dependency_fingerprints':fps})
    calibration=_calibration_fp(req,policy)
    registry=_registry_fp(req,deps,policy)
    return PreparedFreshnessState(req,deps,policy,fps,context,dependency,calibration,registry,evaluate(req,deps,policy),binding,state_epoch)

def validate_prepared_integrity(st):
    if st.binding!=st.policy.binding or st.state_epoch!=st.policy.state_epoch: return False
    if st.dependencies!=tuple(sorted(st.dependencies,key=lambda x:x.field_id)): return False
    if st.dependency_fingerprints!=tuple((d.field_id,_fp(d)) for d in st.dependencies): return False
    if st.context_fingerprint!=_fp({'request':st.request,'policy':st.policy}): return False
    if st.dependency_fingerprint!=_fp({'dependency_fingerprints':st.dependency_fingerprints}): return False
    if st.calibration_fingerprint!=_calibration_fp(st.request,st.policy): return False
    if st.registry_fingerprint!=_registry_fp(st.request,st.dependencies,st.policy): return False
    return st.precomputed_result==evaluate(st.request,st.dependencies,st.policy)

def evaluate_prepared(st,*,current_context_fingerprint,current_dependency_fingerprint,current_calibration_fingerprint,current_registry_fingerprint,prepared_integrity_validated):
    if not prepared_integrity_validated: return _hold('PREPARED_INTEGRITY_UNVERIFIED')
    current=(current_context_fingerprint,current_dependency_fingerprint,current_calibration_fingerprint,current_registry_fingerprint)
    expected=(st.context_fingerprint,st.dependency_fingerprint,st.calibration_fingerprint,st.registry_fingerprint)
    if current!=expected: return _hold('PREPARED_EVIDENCE_CHANGED_REEVALUATION_REQUIRED')
    return st.precomputed_result

def make_delta(base,target):
    if base.binding!=target.binding or base.state_epoch!=target.state_epoch: raise ValueError('DELTA_SCOPE_MISMATCH')
    bm={d.field_id:d for d in base.dependencies}; tm={d.field_id:d for d in target.dependencies}
    changed=tuple(tm[k] for k in sorted(tm) if k not in bm or _fp(tm[k])!=_fp(bm[k]))
    removed=tuple(k for k in sorted(bm) if k not in tm)
    tr=target.request if _fp(base.request)!=_fp(target.request) else None
    tp=target.policy if _fp(base.policy)!=_fp(target.policy) else None
    return FreshnessStateDelta(base.registry_fingerprint,target.registry_fingerprint,changed,removed,tr,tp,base.binding,base.state_epoch)

def apply_delta(base,delta):
    if delta.base_fingerprint!=base.registry_fingerprint: raise ValueError('DELTA_BASE_FINGERPRINT_MISMATCH')
    if delta.binding!=base.binding or delta.state_epoch!=base.state_epoch: raise ValueError('DELTA_SCOPE_MISMATCH')
    dm={d.field_id:d for d in base.dependencies}
    for k in delta.removed_field_ids: dm.pop(k,None)
    for d in delta.changed_dependencies: dm[d.field_id]=d
    st=prepare_state(delta.target_request or base.request,tuple(dm.values()),delta.target_policy or base.policy,binding=base.binding,state_epoch=base.state_epoch)
    if st.registry_fingerprint!=delta.target_fingerprint: raise ValueError('DELTA_TARGET_FINGERPRINT_MISMATCH')
    return st

def missing_only_sync_plan(target,known_dependency_fingerprints:dict[str,str]):
    missing=tuple(k for k,v in target.dependency_fingerprints if known_dependency_fingerprints.get(k)!=v)
    meta={'field_ids':missing,'target':target.registry_fingerprint}
    return FreshnessSyncPlan(missing,len(_canon(meta)),False)

def full_registry_bytes(st): return len(_canon({'request':st.request,'dependencies':st.dependencies,'policy':st.policy}))
def delta_bytes(delta): return len(_canon(delta))
