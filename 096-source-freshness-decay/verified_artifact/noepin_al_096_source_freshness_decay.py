"""NOEPIN AL 096 — Source Freshness Decay — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Pure freshness-control evidence. Source age, source type, volatility and risk are
combined to derive a Freshness Score, Expired Flag and Refresh Priority Candidate.
This module never promotes freshness to Truth/Authority, grants permission,
executes refreshes/actions, commits, publishes, writes externally, proves Safety,
or asserts Action Success.

Canonical identity: NOEPIN-AL-096
DCSR level: LIMITED INTEGRATION / 限定適用.
Provenance note: exact registered Origin GUID was not freshly reverified in this
completion session and is intentionally not guessed or regenerated.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
from enum import Enum, IntEnum
from hashlib import sha256
import json, math

class Decision(str, Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class SourceType(str, Enum):
    API='API'; CLOUD_STATE='CLOUD_STATE'; HUMAN_STATUS='HUMAN_STATUS'; MEMORY='MEMORY'; STATIC_DOCUMENT='STATIC_DOCUMENT'
class Volatility(IntEnum):
    LOW=1; MEDIUM=2; HIGH=3; UNKNOWN=4
class RiskLevel(IntEnum):
    LOW=1; MEDIUM=2; HIGH=3; CRITICAL=4
class RefreshPriority(IntEnum):
    NONE=0; LOW=1; MEDIUM=2; HIGH=3; IMMEDIATE=4

@dataclass(frozen=True)
class FreshnessQuery:
    request_id:str; source_id:str; claim_id:str; now:float; risk:RiskLevel
    observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class SourceFreshnessRecord:
    source_id:str; source_timestamp:float|None; source_type:SourceType; volatility:Volatility
    source_version:str; source_fingerprint:str; claim_fingerprint:str
    updated_verified:bool; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class FreshnessPolicy:
    half_life_api:float; half_life_cloud:float; half_life_human:float; half_life_memory:float; half_life_static:float
    volatility_low_multiplier:float; volatility_medium_multiplier:float; volatility_high_multiplier:float; volatility_unknown_multiplier:float
    threshold_low:float; threshold_medium:float; threshold_high:float; threshold_critical:float
    unknown_timestamp_low:float; unknown_timestamp_medium:float; unknown_timestamp_high:float; unknown_timestamp_unknown:float
    future_clock_skew_seconds:float; binding:str; state_epoch:str; revoked:bool=False
@dataclass(frozen=True)
class FreshnessResult:
    decision:Decision; reasons:tuple[str,...]; freshness_score:float; expired:bool
    refresh_priority:RefreshPriority; source_age_seconds:float|None; effective_half_life_seconds:float
    required_freshness:float; refresh_candidate:bool; next_gate_candidate:bool; reevaluation_candidate:bool
    cache_promoted_to_truth:bool=False; cache_promoted_to_authority:bool=False
    permission_granted:bool=False; refresh_executed:bool=False; action_executed:bool=False
    plan_committed:bool=False; atomic_publish_executed:bool=False; external_write_performed:bool=False
    world_truth_proven:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedFreshnessState:
    query:FreshnessQuery; sources:tuple[SourceFreshnessRecord,...]; policy:FreshnessPolicy
    record_fingerprints:tuple[tuple[str,str],...]; context_fingerprint:str; dependency_fingerprint:str
    calibration_fingerprint:str; registry_fingerprint:str; precomputed_result:FreshnessResult
    binding:str; state_epoch:str
@dataclass(frozen=True)
class FreshnessStateDelta:
    base_fingerprint:str; target_fingerprint:str; changed_sources:tuple[SourceFreshnessRecord,...]
    removed_source_ids:tuple[str,...]; target_query:FreshnessQuery|None; target_policy:FreshnessPolicy|None
    binding:str; state_epoch:str
@dataclass(frozen=True)
class FreshnessSyncPlan:
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

def _hold(reason:str,q:FreshnessQuery,*,score:float=0.0,expired:bool=True,priority:RefreshPriority=RefreshPriority.HIGH,age:float|None=None,half_life:float=0.0,required:float=1.0):
    return FreshnessResult(Decision.HOLD,(reason,),_clamp01(score),expired,priority,age,half_life,required,True,False,True)

def _half_life(record:SourceFreshnessRecord,p:FreshnessPolicy)->float:
    base={SourceType.API:p.half_life_api,SourceType.CLOUD_STATE:p.half_life_cloud,SourceType.HUMAN_STATUS:p.half_life_human,SourceType.MEMORY:p.half_life_memory,SourceType.STATIC_DOCUMENT:p.half_life_static}[record.source_type]
    mult={Volatility.LOW:p.volatility_low_multiplier,Volatility.MEDIUM:p.volatility_medium_multiplier,Volatility.HIGH:p.volatility_high_multiplier,Volatility.UNKNOWN:p.volatility_unknown_multiplier}[record.volatility]
    return base*mult

def _threshold(risk:RiskLevel,p:FreshnessPolicy)->float:
    return {RiskLevel.LOW:p.threshold_low,RiskLevel.MEDIUM:p.threshold_medium,RiskLevel.HIGH:p.threshold_high,RiskLevel.CRITICAL:p.threshold_critical}[risk]

def _unknown_score(v:Volatility,p:FreshnessPolicy)->float:
    return {Volatility.LOW:p.unknown_timestamp_low,Volatility.MEDIUM:p.unknown_timestamp_medium,Volatility.HIGH:p.unknown_timestamp_high,Volatility.UNKNOWN:p.unknown_timestamp_unknown}[v]

def _validate(q:FreshnessQuery,sources:tuple[SourceFreshnessRecord,...],p:FreshnessPolicy):
    if p.revoked: return 'POLICY_REVOKED'
    if not q.observed: return 'QUERY_UNOBSERVED'
    if not q.request_id or not q.source_id or not q.claim_id: return 'QUERY_IDENTITY_INVALID'
    if q.binding!=p.binding or q.state_epoch!=p.state_epoch: return 'QUERY_SCOPE_MISMATCH'
    if not math.isfinite(q.now): return 'NOW_INVALID'
    vals=(p.half_life_api,p.half_life_cloud,p.half_life_human,p.half_life_memory,p.half_life_static)
    if any((not math.isfinite(v) or v<=0) for v in vals): return 'HALF_LIFE_INVALID'
    mult=(p.volatility_low_multiplier,p.volatility_medium_multiplier,p.volatility_high_multiplier,p.volatility_unknown_multiplier)
    if any((not math.isfinite(v) or v<=0) for v in mult): return 'VOLATILITY_MULTIPLIER_INVALID'
    th=(p.threshold_low,p.threshold_medium,p.threshold_high,p.threshold_critical)
    if any((not math.isfinite(v) or not 0<=v<=1) for v in th): return 'THRESHOLD_INVALID'
    us=(p.unknown_timestamp_low,p.unknown_timestamp_medium,p.unknown_timestamp_high,p.unknown_timestamp_unknown)
    if any((not math.isfinite(v) or not 0<=v<=1) for v in us): return 'UNKNOWN_SCORE_INVALID'
    ids=[s.source_id for s in sources]
    if len(ids)!=len(set(ids)): return 'DUPLICATE_SOURCE_ID'
    for s in sources:
        if not s.source_id or not s.source_version or not s.source_fingerprint or not s.claim_fingerprint or not s.observed: return 'SOURCE_RECORD_INVALID'
        if s.binding!=p.binding or s.state_epoch!=p.state_epoch: return 'SOURCE_SCOPE_MISMATCH'
        if s.source_timestamp is not None and not math.isfinite(s.source_timestamp): return 'SOURCE_TIMESTAMP_INVALID'
    return None

def evaluate(q:FreshnessQuery,sources:tuple[SourceFreshnessRecord,...],p:FreshnessPolicy)->FreshnessResult:
    sources=tuple(sorted(sources,key=lambda s:s.source_id))
    err=_validate(q,sources,p)
    if err: return _hold(err,q)
    by_id={s.source_id:s for s in sources}
    if q.source_id not in by_id: return _hold('SOURCE_NOT_FOUND',q)
    s=by_id[q.source_id]
    required=_threshold(q.risk,p); half_life=_half_life(s,p)
    if s.updated_verified:
        score=1.0; age=0.0
    elif s.source_timestamp is None:
        score=_unknown_score(s.volatility,p); age=None
        if s.volatility in (Volatility.HIGH,Volatility.UNKNOWN):
            pr=RefreshPriority.IMMEDIATE if q.risk in (RiskLevel.HIGH,RiskLevel.CRITICAL) else RefreshPriority.HIGH
            return _hold('UNKNOWN_TIMESTAMP_VOLATILE_SOURCE',q,score=score,expired=True,priority=pr,age=None,half_life=half_life,required=required)
    else:
        age=q.now-s.source_timestamp
        if age < -p.future_clock_skew_seconds:
            return _hold('SOURCE_TIMESTAMP_IN_FUTURE',q,score=0.0,expired=True,priority=RefreshPriority.IMMEDIATE,age=age,half_life=half_life,required=required)
        age=max(0.0,age)
        score=math.exp(-math.log(2.0)*age/half_life)
    score=_clamp01(score); expired=score < required
    if not expired:
        priority=RefreshPriority.NONE if score >= min(1.0,required+.15) else RefreshPriority.LOW
        reason='FRESHNESS_RESET_VERIFIED' if s.updated_verified else 'FRESHNESS_WITHIN_THRESHOLD'
        return FreshnessResult(Decision.ALLOW,(reason,),score,False,priority,age,half_life,required,False,True,False)
    if q.risk==RiskLevel.CRITICAL:
        return _hold('CRITICAL_FRESHNESS_EXPIRED',q,score=score,expired=True,priority=RefreshPriority.IMMEDIATE,age=age,half_life=half_life,required=required)
    if q.risk==RiskLevel.HIGH:
        return _hold('HIGH_RISK_FRESHNESS_EXPIRED',q,score=score,expired=True,priority=RefreshPriority.HIGH,age=age,half_life=half_life,required=required)
    if q.risk==RiskLevel.MEDIUM:
        return _hold('MEDIUM_RISK_FRESHNESS_EXPIRED',q,score=score,expired=True,priority=RefreshPriority.HIGH,age=age,half_life=half_life,required=required)
    return FreshnessResult(Decision.ALLOW,('LOW_RISK_STALE_REFRESH_REQUIRED',),score,True,RefreshPriority.HIGH,age,half_life,required,True,True,True)

def default_policy():
    return FreshnessPolicy(30.0,20.0,120.0,86400.0,2592000.0,2.0,1.0,.5,.35,.45,.60,.75,.85,.55,.30,.10,.08,2.0,'SFD-BIND','STATE-EPOCH-1')
def default_query():
    p=default_policy(); return FreshnessQuery('REQ-96','SRC-1','CLAIM-1',1005.0,RiskLevel.LOW,True,p.binding,p.state_epoch)
def default_sources():
    p=default_policy(); return (SourceFreshnessRecord('SRC-1',1000.0,SourceType.API,Volatility.MEDIUM,'API-V1','SOURCE-FP-1','CLAIM-FP-1',False,True,p.binding,p.state_epoch),)
def default_evaluation(): return evaluate(default_query(),default_sources(),default_policy())

def _record_fingerprints(sources): return tuple((f'SRC:{s.source_id}',_fp(s)) for s in sorted(sources,key=lambda x:x.source_id))
def _context_fp(q,p): return _fp((q,p.binding,p.state_epoch))
def _dependency_fp(sources): return _fp(_record_fingerprints(sources))
def _calibration_fp(p): return _fp((p.half_life_api,p.half_life_cloud,p.half_life_human,p.half_life_memory,p.half_life_static,p.volatility_low_multiplier,p.volatility_medium_multiplier,p.volatility_high_multiplier,p.volatility_unknown_multiplier,p.threshold_low,p.threshold_medium,p.threshold_high,p.threshold_critical,p.unknown_timestamp_low,p.unknown_timestamp_medium,p.unknown_timestamp_high,p.unknown_timestamp_unknown,p.future_clock_skew_seconds))
def _registry_fp(q,sources,p): return _fp((q,_record_fingerprints(sources),p))

def prepare_state(q:FreshnessQuery,sources:tuple[SourceFreshnessRecord,...],p:FreshnessPolicy,*,binding:str,state_epoch:str)->PreparedFreshnessState:
    sources=tuple(sorted(sources,key=lambda s:s.source_id)); fps=_record_fingerprints(sources)
    return PreparedFreshnessState(q,sources,p,fps,_context_fp(q,p),_dependency_fp(sources),_calibration_fp(p),_registry_fp(q,sources,p),evaluate(q,sources,p),binding,state_epoch)

def validate_prepared_integrity(st:PreparedFreshnessState)->bool:
    if st.binding!=st.policy.binding or st.state_epoch!=st.policy.state_epoch: return False
    if st.record_fingerprints!=_record_fingerprints(st.sources): return False
    if st.context_fingerprint!=_context_fp(st.query,st.policy): return False
    if st.dependency_fingerprint!=_dependency_fp(st.sources): return False
    if st.calibration_fingerprint!=_calibration_fp(st.policy): return False
    if st.registry_fingerprint!=_registry_fp(st.query,st.sources,st.policy): return False
    return st.precomputed_result==evaluate(st.query,st.sources,st.policy)

def evaluate_prepared(st:PreparedFreshnessState,*,current_context_fingerprint:str,current_dependency_fingerprint:str,current_calibration_fingerprint:str,current_registry_fingerprint:str,prepared_integrity_validated:bool)->FreshnessResult:
    if not prepared_integrity_validated: return _hold('PREPARED_INTEGRITY_NOT_VALIDATED',st.query)
    if current_context_fingerprint!=st.context_fingerprint: return _hold('PREPARED_CONTEXT_MISMATCH',st.query)
    if current_dependency_fingerprint!=st.dependency_fingerprint: return _hold('PREPARED_DEPENDENCY_MISMATCH',st.query)
    if current_calibration_fingerprint!=st.calibration_fingerprint: return _hold('PREPARED_CALIBRATION_MISMATCH',st.query)
    if current_registry_fingerprint!=st.registry_fingerprint: return _hold('PREPARED_REGISTRY_MISMATCH',st.query)
    return st.precomputed_result

def make_delta(base:PreparedFreshnessState,target:PreparedFreshnessState)->FreshnessStateDelta:
    b={s.source_id:s for s in base.sources}; t={s.source_id:s for s in target.sources}
    changed=tuple(t[k] for k in sorted(t) if k not in b or _fp(t[k])!=_fp(b[k])); removed=tuple(sorted(set(b)-set(t)))
    return FreshnessStateDelta(base.registry_fingerprint,target.registry_fingerprint,changed,removed,target.query if target.query!=base.query else None,target.policy if target.policy!=base.policy else None,target.binding,target.state_epoch)

def apply_delta(base:PreparedFreshnessState,d:FreshnessStateDelta)->PreparedFreshnessState:
    if base.registry_fingerprint!=d.base_fingerprint: raise ValueError('BASE_FINGERPRINT_MISMATCH')
    m={s.source_id:s for s in base.sources}
    for k in d.removed_source_ids: m.pop(k,None)
    for s in d.changed_sources: m[s.source_id]=s
    q=d.target_query or base.query; p=d.target_policy or base.policy
    out=prepare_state(q,tuple(m.values()),p,binding=d.binding,state_epoch=d.state_epoch)
    if out.registry_fingerprint!=d.target_fingerprint: raise ValueError('TARGET_FINGERPRINT_MISMATCH')
    return out

def missing_only_sync_plan(target:PreparedFreshnessState,known_record_fingerprints:dict[str,str])->FreshnessSyncPlan:
    missing=tuple(k for k,v in target.record_fingerprints if known_record_fingerprints.get(k)!=v)
    meta=len(_canon({'context':target.context_fingerprint,'dependency':target.dependency_fingerprint,'calibration':target.calibration_fingerprint,'registry':target.registry_fingerprint,'missing':missing}))
    return FreshnessSyncPlan(missing,meta,False)
def full_registry_bytes(st:PreparedFreshnessState)->int: return len(_canon((st.query,st.sources,st.policy)))
def delta_bytes(d:FreshnessStateDelta)->int: return len(_canon(d))
