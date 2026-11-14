"""NOEPIN AL 172 — Lightweighting Strategy Orchestrator — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-172
DCSR: DIRECT INTEGRATION / 直接統合.

Deterministic, side-effect-free strategy planner. For each asset/data record it evaluates
Exact Reuse, Shared Profile, Delta, Quantization+Residual, Lossless, and Original-retention
candidates without executing compression, transfer, mutation, publication, or fallback.
Exact-safe reuse is preferred first. Critical + high-sensitivity records avoid lossy paths.
Any lightweight candidate without reconstruction assurance or positive size benefit is rejected.
If no safe lightweight path is available the source remains a Lossless/Original-retention candidate.
If the resulting safe candidate plan cannot satisfy the size budget, the result is HOLD rather
than silently weakening Critical protection or reconstruction guarantees.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str, Enum): ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class Strategy(str, Enum):
    EXACT_REUSE='EXACT_REUSE'; SHARED_PROFILE='SHARED_PROFILE'; DELTA='DELTA'
    QUANTIZATION_RESIDUAL='QUANTIZATION_RESIDUAL'; LOSSLESS='LOSSLESS'; ORIGINAL='ORIGINAL'
class EngineState(str, Enum):
    LIGHTWEIGHTING_PLAN_CANDIDATE='LIGHTWEIGHTING_PLAN_CANDIDATE'
    LOSSLESS_ORIGINAL_RETENTION_CANDIDATE='LOSSLESS_ORIGINAL_RETENTION_CANDIDATE'
    INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_LIGHTWEIGHTING_PLAN_CANDIDATE='CONTINUE_LIGHTWEIGHTING_PLAN_CANDIDATE'
    RETAIN_LOSSLESS_ORIGINAL_CANDIDATE='RETAIN_LOSSLESS_ORIGINAL_CANDIDATE'
    REVIEW_INPUT_CANDIDATE='REVIEW_INPUT_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'; INVALID_VALUE='INVALID_VALUE'
    SOURCE_UNAVAILABLE='SOURCE_UNAVAILABLE'; SAFE_PLAN_EXCEEDS_BUDGET='SAFE_PLAN_EXCEEDS_BUDGET'

@dataclass(frozen=True)
class AssetDataRecord:
    record_id:str
    original_bytes:int
    importance:float
    sensitivity:float
    critical:bool=False
    available:bool=True
    exact_equivalent:bool=False
    exact_fingerprint_match:bool=False
    exact_reuse_bytes:int=0
    shared_profile_compatible:bool=False
    shared_profile_fingerprint_match:bool=False
    shared_profile_bytes:int=0
    delta_compatible:bool=False
    delta_reversible:bool=False
    delta_bytes:int=0
    numeric:bool=False
    quantization_residual_reversible:bool=False
    quantization_error:float=0.0
    allowed_error:float=0.0
    quantized_bytes:int=0
    residual_bytes:int=0
    lossless_available:bool=True
    lossless_reversible:bool=True
    lossless_bytes:int=0

@dataclass(frozen=True)
class LightweightingRequest:
    request_id:str
    records:tuple[AssetDataRecord,...]
    size_budget_bytes:int
    critical_high_sensitivity_threshold:float
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class StrategySelection:
    record_id:str
    strategy:Strategy
    original_bytes:int
    planned_bytes:int
    expected_savings_bytes:int
    expected_reduction_ratio:float
    critical:bool
    sensitivity:float
    reconstruction_guaranteed:bool
    exact_safe:bool
    lossy_path:bool
    reason:str

@dataclass(frozen=True)
class LightweightingResult:
    decision:Decision
    next_action:NextAction
    escalation:Escalation
    engine_state:EngineState
    request_id:str
    selections:tuple[StrategySelection,...]
    size_budget_bytes:int
    original_total_bytes:int
    planned_total_bytes:int
    expected_savings_bytes:int
    expected_reduction_ratio:float
    budget_feasible:bool
    all_reconstruction_guaranteed:bool
    critical_high_sensitivity_lossy_count:int
    strategy_counts:tuple[tuple[str,int],...]
    next_gate_candidate:bool
    reasons:tuple[str,...]
    source_records_mutated:bool=False
    compression_executed:bool=False
    quantization_executed:bool=False
    residual_applied:bool=False
    transfer_executed:bool=False
    plan_committed:bool=False
    authoritative_state_created:bool=False
    cached_state_promoted:bool=False
    reconstructed_state_promoted:bool=False
    partial_state_promoted:bool=False
    publish_executed:bool=False
    fallback_executed:bool=False
    original_deleted:bool=False
    tool_invoked:bool=False
    file_write_executed:bool=False
    network_send_executed:bool=False
    dcsr_reconstruction_created_fact:bool=False
    sender_authority_inherited:bool=False
    sender_intent_inherited:bool=False
    sender_agreement_inherited:bool=False
    permission_granted:bool=False
    approval_executed:bool=False
    authority_granted:bool=False
    stop_executed:bool=False
    action_executed:bool=False
    external_write_performed:bool=False
    world_truth_proven:bool=False
    domain_authority_promoted:bool=False
    safety_proven:bool=False
    action_success:bool=False

@dataclass(frozen=True)
class PreparedLightweightingState:
    request:LightweightingRequest
    result:LightweightingResult
    records_fingerprint:str
    config_fingerprint:str
    result_fingerprint:str
    integrity_fingerprint:str
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class LightweightingChange:
    records_changed:bool
    config_changed:bool
    from_fingerprint:str
    to_fingerprint:str

@dataclass(frozen=True)
class MissingOnlyPlan:
    missing_or_changed_record_ids:tuple[str,...]
    metadata_bytes_required:int
    full_resend_required:bool

def _obj(v):
    if isinstance(v,Enum): return v.value
    if is_dataclass(v): return {f.name:_obj(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v,dict): return {str(k):_obj(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(tuple,list)): return [_obj(x) for x in v]
    if isinstance(v,float):
        if not math.isfinite(v): raise ValueError('non-finite float')
        return v
    return v

def _canon(v): return json.dumps(_obj(v),ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def _fp(v): return sha256(_canon(v)).hexdigest()
def _num(v): return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(float(v))

def _invalid(q,reason,esc,decision=Decision.HOLD):
    return LightweightingResult(decision,NextAction.REVIEW_INPUT_CANDIDATE,esc,EngineState.INVALID,getattr(q,'request_id',''),(),getattr(q,'size_budget_bytes',0),0,0,0,0.0,False,False,0,(),False,(reason,'NO_AUTHORITATIVE_STATE_PROMOTION','LOSSLESS_ORIGINAL_RETENTION_REMAINS_CANDIDATE','DCSR_STATE_IS_NOT_AUTHORITATIVE_STATE'))

def _validate(q):
    if not q.request_id or not q.binding or not q.state_epoch: return ('EMPTY_REQUEST_CONTEXT',Escalation.INVALID_CONFIGURATION)
    if not isinstance(q.size_budget_bytes,int) or isinstance(q.size_budget_bytes,bool) or q.size_budget_bytes<=0: return ('INVALID_SIZE_BUDGET',Escalation.INVALID_CONFIGURATION)
    if not _num(q.critical_high_sensitivity_threshold) or not 0<=float(q.critical_high_sensitivity_threshold)<=1: return ('INVALID_CRITICAL_SENSITIVITY_THRESHOLD',Escalation.INVALID_VALUE)
    if not q.records: return ('EMPTY_RECORD_SET',Escalation.INVALID_CONFIGURATION)
    ids=[r.record_id for r in q.records]
    if any(not x for x in ids) or len(ids)!=len(set(ids)): return ('INVALID_OR_DUPLICATE_RECORD_ID',Escalation.INVALID_CONFIGURATION)
    for r in q.records:
        ints=(r.original_bytes,r.exact_reuse_bytes,r.shared_profile_bytes,r.delta_bytes,r.quantized_bytes,r.residual_bytes,r.lossless_bytes)
        if any(not isinstance(x,int) or isinstance(x,bool) or x<0 for x in ints) or r.original_bytes<=0: return ('INVALID_SIZE_VALUE',Escalation.INVALID_CONFIGURATION)
        if not _num(r.importance) or not 0<=float(r.importance)<=1: return ('INVALID_IMPORTANCE',Escalation.INVALID_VALUE)
        if not _num(r.sensitivity) or not 0<=float(r.sensitivity)<=1: return ('INVALID_SENSITIVITY',Escalation.INVALID_VALUE)
        if not _num(r.quantization_error) or float(r.quantization_error)<0: return ('INVALID_QUANTIZATION_ERROR',Escalation.INVALID_VALUE)
        if not _num(r.allowed_error) or float(r.allowed_error)<0: return ('INVALID_ALLOWED_ERROR',Escalation.INVALID_VALUE)
    return None

def _benefit(sz,orig): return sz>0 and sz<orig

def _select(r,threshold):
    # 1 Exact equivalence first, only with exact fingerprint evidence and positive size benefit.
    if r.exact_equivalent and r.exact_fingerprint_match and _benefit(r.exact_reuse_bytes,r.original_bytes):
        return StrategySelection(r.record_id,Strategy.EXACT_REUSE,r.original_bytes,r.exact_reuse_bytes,r.original_bytes-r.exact_reuse_bytes,(r.original_bytes-r.exact_reuse_bytes)/r.original_bytes,r.critical,r.sensitivity,True,True,False,'EXACT_EQUIVALENCE_AND_FINGERPRINT_MATCH')
    # Critical + high sensitivity forbids lossy quantization route; prefer reversible lossless/original.
    if r.critical and r.sensitivity>=threshold:
        if r.lossless_available and r.lossless_reversible and _benefit(r.lossless_bytes,r.original_bytes):
            return StrategySelection(r.record_id,Strategy.LOSSLESS,r.original_bytes,r.lossless_bytes,r.original_bytes-r.lossless_bytes,(r.original_bytes-r.lossless_bytes)/r.original_bytes,True,r.sensitivity,True,False,False,'CRITICAL_HIGH_SENSITIVITY_LOSSLESS_PRIORITY')
        return StrategySelection(r.record_id,Strategy.ORIGINAL,r.original_bytes,r.original_bytes,0,0.0,True,r.sensitivity,True,False,False,'CRITICAL_HIGH_SENSITIVITY_ORIGINAL_RETENTION')
    # 2 Shared profile/reference consolidation.
    if r.shared_profile_compatible and r.shared_profile_fingerprint_match and _benefit(r.shared_profile_bytes,r.original_bytes):
        return StrategySelection(r.record_id,Strategy.SHARED_PROFILE,r.original_bytes,r.shared_profile_bytes,r.original_bytes-r.shared_profile_bytes,(r.original_bytes-r.shared_profile_bytes)/r.original_bytes,r.critical,r.sensitivity,True,True,False,'SHARED_PROFILE_FINGERPRINT_MATCH')
    # 3 Reversible Delta.
    if r.delta_compatible and r.delta_reversible and _benefit(r.delta_bytes,r.original_bytes):
        return StrategySelection(r.record_id,Strategy.DELTA,r.original_bytes,r.delta_bytes,r.original_bytes-r.delta_bytes,(r.original_bytes-r.delta_bytes)/r.original_bytes,r.critical,r.sensitivity,True,True,False,'REVERSIBLE_DELTA_CANDIDATE')
    # 4 Quantization + Residual only when explicit error and reversible residual evidence pass.
    qr=r.quantized_bytes+r.residual_bytes
    if r.numeric and r.quantization_residual_reversible and r.quantization_error<=r.allowed_error and _benefit(qr,r.original_bytes):
        return StrategySelection(r.record_id,Strategy.QUANTIZATION_RESIDUAL,r.original_bytes,qr,r.original_bytes-qr,(r.original_bytes-qr)/r.original_bytes,r.critical,r.sensitivity,True,False,True,'QUANTIZATION_ERROR_WITHIN_LIMIT_AND_RESIDUAL_REVERSIBLE')
    # 5 Reversible lossless, else Original.
    if r.lossless_available and r.lossless_reversible and _benefit(r.lossless_bytes,r.original_bytes):
        return StrategySelection(r.record_id,Strategy.LOSSLESS,r.original_bytes,r.lossless_bytes,r.original_bytes-r.lossless_bytes,(r.original_bytes-r.lossless_bytes)/r.original_bytes,r.critical,r.sensitivity,True,False,False,'REVERSIBLE_LOSSLESS_CANDIDATE')
    return StrategySelection(r.record_id,Strategy.ORIGINAL,r.original_bytes,r.original_bytes,0,0.0,r.critical,r.sensitivity,True,False,False,'NO_SAFE_BENEFICIAL_LIGHTWEIGHTING_PATH_ORIGINAL_RETENTION')

def _hold(q,reason,esc,selections=()):
    orig=sum(r.original_bytes for r in q.records if r.available)
    plan=sum(x.planned_bytes for x in selections)
    savings=max(0,orig-plan)
    counts={s.value:0 for s in Strategy}
    for x in selections: counts[x.strategy.value]+=1
    lossy=sum(1 for x in selections if x.critical and x.sensitivity>=q.critical_high_sensitivity_threshold and x.lossy_path)
    return LightweightingResult(Decision.HOLD,NextAction.RETAIN_LOSSLESS_ORIGINAL_CANDIDATE,esc,EngineState.LOSSLESS_ORIGINAL_RETENTION_CANDIDATE,q.request_id,tuple(selections),q.size_budget_bytes,orig,plan,savings,(savings/orig if orig else 0.0),False,all(x.reconstruction_guaranteed for x in selections),lossy,tuple(sorted(counts.items())),False,(reason,'NO_CRITICAL_PROTECTION_WEAKENING','LOSSLESS_ORIGINAL_RETENTION_CANDIDATE','NO_COMPRESSION_TRANSFER_MUTATION_OR_ACTION_EXECUTION'))

def evaluate(q):
    bad=_validate(q)
    if bad: return _invalid(q,bad[0],bad[1],Decision.DENY if bad[1]==Escalation.INVALID_VALUE else Decision.HOLD)
    if any(not r.available for r in q.records): return _hold(q,'SOURCE_RECORD_UNAVAILABLE',Escalation.SOURCE_UNAVAILABLE)
    sels=tuple(sorted((_select(r,float(q.critical_high_sensitivity_threshold)) for r in q.records),key=lambda x:x.record_id))
    orig=sum(x.original_bytes for x in sels); plan=sum(x.planned_bytes for x in sels); savings=orig-plan
    counts={s.value:0 for s in Strategy}
    for x in sels: counts[x.strategy.value]+=1
    all_recon=all(x.reconstruction_guaranteed for x in sels)
    crit_lossy=sum(1 for x in sels if x.critical and x.sensitivity>=q.critical_high_sensitivity_threshold and x.lossy_path)
    feasible=plan<=q.size_budget_bytes
    if not all_recon or crit_lossy:
        return _hold(q,'RECONSTRUCTION_GUARANTEE_OR_CRITICAL_PROTECTION_FAILED',Escalation.SAFE_PLAN_EXCEEDS_BUDGET,sels)
    if not feasible:
        return _hold(q,'SAFE_LIGHTWEIGHTING_PLAN_EXCEEDS_SIZE_BUDGET',Escalation.SAFE_PLAN_EXCEEDS_BUDGET,sels)
    reasons=('EXACT_SAFE_EVALUATED_FIRST','SHARED_PROFILE_DELTA_QUANTIZATION_RESIDUAL_EVALUATED_IN_ORDER','CRITICAL_HIGH_SENSITIVITY_LOSSLESS_ORIGINAL_PROTECTED','NO_BENEFIT_RETURNS_ORIGINAL','RECONSTRUCTION_GUARANTEE_REQUIRED','SIZE_BUDGET_RECHECKED','PLAN_IS_CANDIDATE_NOT_EXECUTION','NO_AUTHORITATIVE_STATE_PROMOTION','NO_PERMISSION_DEPLOYMENT_OR_ACTION_EXECUTION')
    return LightweightingResult(Decision.ALLOW,NextAction.CONTINUE_LIGHTWEIGHTING_PLAN_CANDIDATE,Escalation.NONE,EngineState.LIGHTWEIGHTING_PLAN_CANDIDATE,q.request_id,sels,q.size_budget_bytes,orig,plan,savings,savings/orig,True,True,0,tuple(sorted(counts.items())),True,reasons)

def default_request():
    rs=(
      AssetDataRecord(record_id='EXACT-A',original_bytes=3200,importance=0.95,sensitivity=0.90,exact_equivalent=True,exact_fingerprint_match=True,exact_reuse_bytes=120,lossless_bytes=2500),
      AssetDataRecord(record_id='SHARED-A',original_bytes=2600,importance=0.80,sensitivity=0.65,shared_profile_compatible=True,shared_profile_fingerprint_match=True,shared_profile_bytes=700,lossless_bytes=2100),
      AssetDataRecord(record_id='DELTA-A',original_bytes=2400,importance=0.78,sensitivity=0.62,delta_compatible=True,delta_reversible=True,delta_bytes=620,lossless_bytes=1900),
      AssetDataRecord(record_id='NUM-A',original_bytes=2800,importance=0.70,sensitivity=0.55,numeric=True,quantization_residual_reversible=True,quantization_error=0.004,allowed_error=0.010,quantized_bytes=900,residual_bytes=180,lossless_bytes=1900),
      AssetDataRecord(record_id='CRIT-HIGH',original_bytes=2100,importance=1.0,sensitivity=0.96,critical=True,numeric=True,quantization_residual_reversible=True,quantization_error=0.001,allowed_error=0.010,quantized_bytes=700,residual_bytes=120,lossless_bytes=1750),
      AssetDataRecord(record_id='LOSSLESS-A',original_bytes=1900,importance=0.60,sensitivity=0.50,lossless_available=True,lossless_reversible=True,lossless_bytes=1500),
      AssetDataRecord(record_id='ORIGINAL-A',original_bytes=1500,importance=0.40,sensitivity=0.40,numeric=True,quantization_residual_reversible=False,quantization_error=0.4,allowed_error=0.01,quantized_bytes=1400,residual_bytes=300,lossless_available=True,lossless_reversible=True,lossless_bytes=1500),
      AssetDataRecord(record_id='EXACT-CRIT',original_bytes=1800,importance=1.0,sensitivity=0.98,critical=True,exact_equivalent=True,exact_fingerprint_match=True,exact_reuse_bytes=90,lossless_bytes=1600),
      AssetDataRecord(record_id='DELTA-B',original_bytes=1700,importance=0.72,sensitivity=0.58,delta_compatible=True,delta_reversible=True,delta_bytes=500,lossless_bytes=1450),
      AssetDataRecord(record_id='SHARED-B',original_bytes=1600,importance=0.68,sensitivity=0.52,shared_profile_compatible=True,shared_profile_fingerprint_match=True,shared_profile_bytes=420,lossless_bytes=1300),
    )
    return LightweightingRequest('LSO-172-A',rs,9000,0.85,'DEFAULT-BINDING','EPOCH-1')
def default_evaluation(): return evaluate(default_request())

def _records_fp(q): return _fp(q.records)
def _config_fp(q): return _fp((q.size_budget_bytes,q.critical_high_sensitivity_threshold,q.binding,q.state_epoch))
def prepare_state(q,binding,state_epoch):
    if q.binding!=binding or q.state_epoch!=state_epoch:
        r=_invalid(q,'PREPARED_BINDING_MISMATCH',Escalation.INVALID_CONFIGURATION)
        return PreparedLightweightingState(q,r,'0'*64,'0'*64,'0'*64,'0'*64,binding,state_epoch)
    r=evaluate(q); rf=_records_fp(q); cf=_config_fp(q); of=_fp(r); integ=_fp((rf,cf,of,binding,state_epoch))
    return PreparedLightweightingState(q,r,rf,cf,of,integ,binding,state_epoch)
def evaluate_prepared(st,*,integrity_validated,current_records_fingerprint,current_config_fingerprint,current_result_fingerprint):
    q=st.request
    if not integrity_validated: return _invalid(q,'PREPARED_INTEGRITY_NOT_VALIDATED',Escalation.INVALID_CONFIGURATION)
    if current_records_fingerprint!=st.records_fingerprint: return _invalid(q,'PREPARED_RECORDS_FINGERPRINT_MISMATCH',Escalation.INVALID_CONFIGURATION)
    if current_config_fingerprint!=st.config_fingerprint: return _invalid(q,'PREPARED_CONFIG_FINGERPRINT_MISMATCH',Escalation.INVALID_CONFIGURATION)
    if current_result_fingerprint!=st.result_fingerprint: return _invalid(q,'PREPARED_RESULT_FINGERPRINT_MISMATCH',Escalation.INVALID_CONFIGURATION)
    if _fp((st.records_fingerprint,st.config_fingerprint,st.result_fingerprint,st.binding,st.state_epoch))!=st.integrity_fingerprint: return _invalid(q,'PREPARED_INTEGRITY_FINGERPRINT_MISMATCH',Escalation.INVALID_CONFIGURATION)
    return st.result

def make_delta(a,b):
    return LightweightingChange(a.records_fingerprint!=b.records_fingerprint,a.config_fingerprint!=b.config_fingerprint,_fp((a.records_fingerprint,a.config_fingerprint)),_fp((b.records_fingerprint,b.config_fingerprint)))
def plan_missing_only(a,b):
    d=make_delta(a,b); ids=[]
    if d.records_changed: ids.append('ASSET_DATA_RECORDS')
    if d.config_changed: ids.append('LIGHTWEIGHTING_CONFIG')
    return MissingOnlyPlan(tuple(ids),110+len(ids)*19,False)
