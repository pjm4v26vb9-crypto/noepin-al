"""NOEPIN AL 099 — Abstention Threshold Optimizer — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Pure control-candidate evidence. This module searches abstention thresholds from
calibration outcomes and asymmetric False-Allow / False-Hold costs, then applies
Risk-specific Policy floors/ceilings, sparse-data conservatism, and degradation
raising. It never treats an optimized threshold or minimum Expected Loss as a
Safety Proof, never mutates Policy, grants permission, executes actions, commits,
publishes, writes externally, or asserts Action Success.

Canonical identity: NOEPIN-AL-099
DCSR level: AUXILIARY INTEGRATION / 補助統合.
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
class ThresholdSource(str, Enum):
    OPTIMIZED='OPTIMIZED'; CONSERVATIVE='CONSERVATIVE'; DEGRADED_RAISED='DEGRADED_RAISED'; POLICY_FALLBACK='POLICY_FALLBACK'
class NextAction(str, Enum):
    THRESHOLD_CANDIDATE='THRESHOLD_CANDIDATE'
    CONSERVATIVE_THRESHOLD_CANDIDATE='CONSERVATIVE_THRESHOLD_CANDIDATE'
    REEVALUATION_CANDIDATE='REEVALUATION_CANDIDATE'
    HOLD_UNRESOLVED='HOLD_UNRESOLVED'

@dataclass(frozen=True)
class ThresholdQuery:
    request_id:str; task_class:str; risk:RiskLevel; false_allow_cost:float; false_hold_cost:float
    observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class CalibrationRecord:
    record_id:str; task_class:str; predicted_confidence:float; outcome_success:bool; sequence_index:int
    source_version:str; source_fingerprint:str; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class ThresholdPolicy:
    minimum_threshold_low:float; minimum_threshold_medium:float; minimum_threshold_high:float; minimum_threshold_critical:float
    maximum_threshold:float
    conservative_threshold_low:float; conservative_threshold_medium:float; conservative_threshold_high:float; conservative_threshold_critical:float
    minimum_samples_low:int; minimum_samples_medium:int; minimum_samples_high:int; minimum_samples_critical:int
    grid_step:float; degradation_window:int; degradation_delta:float; degradation_increment:float
    binding:str; state_epoch:str; revoked:bool=False
@dataclass(frozen=True)
class ThresholdResult:
    decision:Decision; threshold_source:ThresholdSource; next_action:NextAction; reasons:tuple[str,...]
    abstention_threshold:float; expected_loss:float; false_allow_count:int; false_hold_count:int; sample_count:int
    recent_accuracy:float|None; previous_accuracy:float|None; degradation_detected:bool; sparse_data:bool
    class_specific_thresholds:tuple[tuple[str,float],...]; next_gate_candidate:bool
    threshold_applied:bool=False; policy_mutated:bool=False; cache_promoted_to_truth:bool=False; cache_promoted_to_authority:bool=False
    permission_granted:bool=False; action_executed:bool=False; plan_committed:bool=False; atomic_publish_executed:bool=False
    external_write_performed:bool=False; world_truth_proven:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedThresholdState:
    query:ThresholdQuery; records:tuple[CalibrationRecord,...]; policy:ThresholdPolicy
    record_fingerprints:tuple[tuple[str,str],...]; context_fingerprint:str; dependency_fingerprint:str
    constraint_fingerprint:str; registry_fingerprint:str; precomputed_result:ThresholdResult
    binding:str; state_epoch:str
@dataclass(frozen=True)
class ThresholdStateDelta:
    base_fingerprint:str; target_fingerprint:str; changed_records:tuple[CalibrationRecord,...]
    removed_record_ids:tuple[str,...]; target_query:ThresholdQuery|None; target_policy:ThresholdPolicy|None
    binding:str; state_epoch:str
@dataclass(frozen=True)
class ThresholdSyncPlan:
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
def _clamp(x,lo,hi): return max(lo,min(hi,x))
def _floor(r,p):
    return {RiskLevel.LOW:p.minimum_threshold_low,RiskLevel.MEDIUM:p.minimum_threshold_medium,RiskLevel.HIGH:p.minimum_threshold_high,RiskLevel.CRITICAL:p.minimum_threshold_critical}[r]
def _conservative(r,p):
    return {RiskLevel.LOW:p.conservative_threshold_low,RiskLevel.MEDIUM:p.conservative_threshold_medium,RiskLevel.HIGH:p.conservative_threshold_high,RiskLevel.CRITICAL:p.conservative_threshold_critical}[r]
def _minimum_samples(r,p):
    return {RiskLevel.LOW:p.minimum_samples_low,RiskLevel.MEDIUM:p.minimum_samples_medium,RiskLevel.HIGH:p.minimum_samples_high,RiskLevel.CRITICAL:p.minimum_samples_critical}[r]
def _hold(reason,q,p,*,threshold=None,source=ThresholdSource.POLICY_FALLBACK,sample_count=0,sparse=False,recent=None,previous=None,degraded=False,class_thresholds=()):
    th=_clamp(_conservative(q.risk,p) if threshold is None else threshold,_floor(q.risk,p),p.maximum_threshold)
    return ThresholdResult(Decision.HOLD,source,NextAction.HOLD_UNRESOLVED,(reason,),th,0.0,0,0,sample_count,recent,previous,degraded,sparse,tuple(class_thresholds),False)

def _validate(q,records,p):
    if p.revoked: return 'POLICY_REVOKED'
    if not q.observed or not q.request_id or not q.task_class: return 'QUERY_INVALID'
    if q.binding!=p.binding or q.state_epoch!=p.state_epoch: return 'QUERY_SCOPE_MISMATCH'
    if not all(math.isfinite(v) and v>0 for v in (q.false_allow_cost,q.false_hold_cost)): return 'COST_INVALID'
    floors=(p.minimum_threshold_low,p.minimum_threshold_medium,p.minimum_threshold_high,p.minimum_threshold_critical)
    cons=(p.conservative_threshold_low,p.conservative_threshold_medium,p.conservative_threshold_high,p.conservative_threshold_critical)
    if any((not math.isfinite(v) or not 0<=v<=1) for v in floors+cons+(p.maximum_threshold,)): return 'POLICY_THRESHOLD_INVALID'
    if any(v>p.maximum_threshold for v in floors+cons): return 'POLICY_BOUND_INVALID'
    if not (floors[0]<=floors[1]<=floors[2]<=floors[3]): return 'POLICY_RISK_FLOOR_NONMONOTONIC'
    if not (0<p.grid_step<=0.25 and p.degradation_window>=1 and 0<=p.degradation_delta<=1 and 0<=p.degradation_increment<=1): return 'POLICY_PARAMETER_INVALID'
    if min(p.minimum_samples_low,p.minimum_samples_medium,p.minimum_samples_high,p.minimum_samples_critical)<1: return 'POLICY_SAMPLE_INVALID'
    ids=[x.record_id for x in records]
    if len(ids)!=len(set(ids)): return 'DUPLICATE_RECORD_ID'
    for x in records:
        if not x.observed or not x.record_id or not x.task_class or not x.source_version or not x.source_fingerprint: return 'CALIBRATION_RECORD_INVALID'
        if x.binding!=p.binding or x.state_epoch!=p.state_epoch: return 'CALIBRATION_SCOPE_MISMATCH'
        if not math.isfinite(x.predicted_confidence) or not 0<=x.predicted_confidence<=1 or x.sequence_index<0: return 'CALIBRATION_VALUE_INVALID'
    return None

def _grid(p,r):
    lo=_floor(r,p); hi=p.maximum_threshold; vals=[]; x=lo
    while x < hi-1e-12:
        vals.append(round(x,10)); x += p.grid_step
    vals.append(round(hi,10)); return tuple(sorted(set(vals)))
def _loss(records,threshold,fa_cost,fh_cost):
    fa=fh=0
    for x in records:
        allow=x.predicted_confidence>=threshold
        if allow and not x.outcome_success: fa+=1
        elif (not allow) and x.outcome_success: fh+=1
    n=max(1,len(records)); return (fa*fa_cost+fh*fh_cost)/n,fa,fh
def _optimize(records,q,p):
    best=None
    for t in _grid(p,q.risk):
        loss,fa,fh=_loss(records,t,q.false_allow_cost,q.false_hold_cost)
        cand=(loss,-t,t,fa,fh)  # tie -> higher / safer threshold
        if best is None or cand<best: best=cand
    assert best is not None
    return best[2],best[0],best[3],best[4]
def _accuracy(records):
    return sum(1 for x in records if x.outcome_success)/len(records) if records else None
def _degradation(records,p):
    rs=sorted(records,key=lambda x:(x.sequence_index,x.record_id)); w=p.degradation_window
    if len(rs)<2*w: return False,None,None
    previous=_accuracy(rs[-2*w:-w]); recent=_accuracy(rs[-w:])
    return bool(previous is not None and recent is not None and previous-recent>=p.degradation_delta),recent,previous

def evaluate(q:ThresholdQuery,records:tuple[CalibrationRecord,...],p:ThresholdPolicy)->ThresholdResult:
    records=tuple(sorted(records,key=lambda x:(x.sequence_index,x.record_id))); err=_validate(q,records,p)
    if err: return _hold(err,q,p,sample_count=len(records))
    target=tuple(x for x in records if x.task_class==q.task_class)
    if not target: return _hold('NO_TASK_CLASS_DATA',q,p,sparse=True)
    optimized,_,_,_=_optimize(target,q,p)
    threshold=_clamp(optimized,_floor(q.risk,p),p.maximum_threshold)
    sparse=len(target)<_minimum_samples(q.risk,p)
    source=ThresholdSource.OPTIMIZED; reasons=[]
    if sparse:
        threshold=max(threshold,_conservative(q.risk,p)); source=ThresholdSource.CONSERVATIVE; reasons.append('SPARSE_DATA_CONSERVATIVE_THRESHOLD')
    degraded,recent,previous=_degradation(target,p)
    if degraded:
        threshold=min(p.maximum_threshold,max(threshold,threshold+p.degradation_increment)); source=ThresholdSource.DEGRADED_RAISED; reasons.append('PERFORMANCE_DEGRADATION_THRESHOLD_RAISED')
    threshold=_clamp(threshold,_floor(q.risk,p),p.maximum_threshold)
    loss,fa,fh=_loss(target,threshold,q.false_allow_cost,q.false_hold_cost)
    classes=[]
    for cls in sorted({x.task_class for x in records}):
        subset=tuple(x for x in records if x.task_class==cls)
        t,_,_,_=_optimize(subset,q,p); classes.append((cls,_clamp(t,_floor(q.risk,p),p.maximum_threshold)))
    if sparse and q.risk>=RiskLevel.HIGH:
        return ThresholdResult(Decision.HOLD,source,NextAction.CONSERVATIVE_THRESHOLD_CANDIDATE,tuple(reasons+['HIGH_RISK_DATA_INSUFFICIENT']),threshold,loss,fa,fh,len(target),recent,previous,degraded,True,tuple(classes),False)
    if degraded and q.risk>=RiskLevel.HIGH:
        return ThresholdResult(Decision.HOLD,source,NextAction.REEVALUATION_CANDIDATE,tuple(reasons+['HIGH_RISK_PERFORMANCE_DEGRADED']),threshold,loss,fa,fh,len(target),recent,previous,True,sparse,tuple(classes),False)
    if not reasons: reasons=['EXPECTED_LOSS_OPTIMIZED_WITHIN_POLICY_BOUNDS']
    next_action=NextAction.CONSERVATIVE_THRESHOLD_CANDIDATE if sparse else (NextAction.REEVALUATION_CANDIDATE if degraded else NextAction.THRESHOLD_CANDIDATE)
    return ThresholdResult(Decision.ALLOW,source,next_action,tuple(reasons),threshold,loss,fa,fh,len(target),recent,previous,degraded,sparse,tuple(classes),True)

def default_policy():
    return ThresholdPolicy(.45,.60,.75,.90,.99,.65,.75,.90,.95,20,30,40,50,.05,10,.20,.05,'ATO-BIND','STATE-EPOCH-1')
def default_query():
    p=default_policy(); return ThresholdQuery('REQ-99','TASK-A',RiskLevel.LOW,8.0,1.0,True,p.binding,p.state_epoch)
def default_records():
    p=default_policy(); out=[]
    for i in range(80):
        c=.40+(i%12)*.05
        success=(c>=.65)
        if i%17==0: success=not success
        out.append(CalibrationRecord(f'A{i:03d}','TASK-A',min(.99,c),success,i,'V1',f'SF-A-{i}',True,p.binding,p.state_epoch))
    for i in range(24):
        c=.45+(i%10)*.05; success=(c>=.70)
        if i%11==0: success=not success
        out.append(CalibrationRecord(f'B{i:03d}','TASK-B',min(.99,c),success,100+i,'V1',f'SF-B-{i}',True,p.binding,p.state_epoch))
    return tuple(out)
def default_evaluation(): return evaluate(default_query(),default_records(),default_policy())

def _record_fingerprints(records): return tuple((f'CAL:{x.record_id}',_fp(x)) for x in sorted(records,key=lambda x:x.record_id))
def _context_fp(q,p): return _fp((q.request_id,q.task_class,q.risk,q.binding,q.state_epoch))
def _dependency_fp(records): return _fp(_record_fingerprints(records))
def _constraint_fp(q,p): return _fp((q.false_allow_cost,q.false_hold_cost,p))
def _registry_fp(q,records,p): return _fp((q,_record_fingerprints(records),p))
def prepare_state(q,records,p,*,binding:str,state_epoch:str):
    records=tuple(sorted(records,key=lambda x:(x.sequence_index,x.record_id))); fps=_record_fingerprints(records)
    return PreparedThresholdState(q,records,p,fps,_context_fp(q,p),_dependency_fp(records),_constraint_fp(q,p),_registry_fp(q,records,p),evaluate(q,records,p),binding,state_epoch)
def validate_prepared_integrity(st):
    if st.binding!=st.policy.binding or st.state_epoch!=st.policy.state_epoch: return False
    if st.record_fingerprints!=_record_fingerprints(st.records): return False
    if st.context_fingerprint!=_context_fp(st.query,st.policy): return False
    if st.dependency_fingerprint!=_dependency_fp(st.records): return False
    if st.constraint_fingerprint!=_constraint_fp(st.query,st.policy): return False
    if st.registry_fingerprint!=_registry_fp(st.query,st.records,st.policy): return False
    return st.precomputed_result==evaluate(st.query,st.records,st.policy)
def evaluate_prepared(st,*,current_context_fingerprint,current_dependency_fingerprint,current_constraint_fingerprint,current_registry_fingerprint,prepared_integrity_validated):
    if not prepared_integrity_validated: return _hold('PREPARED_INTEGRITY_NOT_VALIDATED',st.query,st.policy)
    if current_context_fingerprint!=st.context_fingerprint: return _hold('PREPARED_CONTEXT_MISMATCH',st.query,st.policy)
    if current_dependency_fingerprint!=st.dependency_fingerprint: return _hold('PREPARED_DEPENDENCY_MISMATCH',st.query,st.policy)
    if current_constraint_fingerprint!=st.constraint_fingerprint: return _hold('PREPARED_CONSTRAINT_MISMATCH',st.query,st.policy)
    if current_registry_fingerprint!=st.registry_fingerprint: return _hold('PREPARED_REGISTRY_MISMATCH',st.query,st.policy)
    return st.precomputed_result

def make_delta(base,target):
    bb={x.record_id:x for x in base.records}; tb={x.record_id:x for x in target.records}
    changed=tuple(tb[k] for k in sorted(tb) if k not in bb or _fp(tb[k])!=_fp(bb[k]))
    return ThresholdStateDelta(base.registry_fingerprint,target.registry_fingerprint,changed,tuple(sorted(set(bb)-set(tb))),target.query if target.query!=base.query else None,target.policy if target.policy!=base.policy else None,target.binding,target.state_epoch)
def apply_delta(base,d):
    if base.registry_fingerprint!=d.base_fingerprint: raise ValueError('BASE_FINGERPRINT_MISMATCH')
    bm={x.record_id:x for x in base.records}
    for k in d.removed_record_ids: bm.pop(k,None)
    for x in d.changed_records: bm[x.record_id]=x
    out=prepare_state(d.target_query or base.query,tuple(bm.values()),d.target_policy or base.policy,binding=d.binding,state_epoch=d.state_epoch)
    if out.registry_fingerprint!=d.target_fingerprint: raise ValueError('TARGET_FINGERPRINT_MISMATCH')
    return out
def missing_only_sync_plan(target,known_record_fingerprints):
    missing=tuple(k for k,v in target.record_fingerprints if known_record_fingerprints.get(k)!=v)
    meta=len(_canon({'context':target.context_fingerprint,'dependency':target.dependency_fingerprint,'constraint':target.constraint_fingerprint,'registry':target.registry_fingerprint,'missing':missing}))
    return ThresholdSyncPlan(missing,meta,False)
def full_registry_bytes(st): return len(_canon((st.query,st.records,st.policy)))
def delta_bytes(d): return len(_canon(d))
