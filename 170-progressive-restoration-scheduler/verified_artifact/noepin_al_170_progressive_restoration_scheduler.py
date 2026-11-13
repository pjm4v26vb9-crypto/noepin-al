"""NOEPIN AL 170 — Progressive Restoration Scheduler — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-170
DCSR: DIRECT INTEGRATION / 直接統合.

Deterministic, side-effect-free scheduler for progressive restoration candidates.
Stage0 always contains the required Base. Detail chunks are ranked by DCSR priority
(P1 Critical, then P2-P4 details) and deterministic importance/cost score. Required
Detail budget is reserved so Optional chunks can never crowd mandatory Detail out.
If the Base or any required Detail is unavailable or cannot fit the byte/latency budget,
the result is HOLD. Base-only continuation is allowed only when explicitly enabled by policy.
The output is a restoration schedule candidate only: no transfer, reconstruction, write,
state promotion, permission grant, fallback execution, or Action Success is performed.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str, Enum): ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class EngineState(str, Enum):
    PROGRESSIVE_RESTORATION_CANDIDATE='PROGRESSIVE_RESTORATION_CANDIDATE'
    FULL_ORIGINAL_RETENTION_CANDIDATE='FULL_ORIGINAL_RETENTION_CANDIDATE'
    INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_PROGRESSIVE_RESTORATION_CANDIDATE='CONTINUE_PROGRESSIVE_RESTORATION_CANDIDATE'
    RETAIN_FULL_ORIGINAL_CANDIDATE='RETAIN_FULL_ORIGINAL_CANDIDATE'
    REVIEW_INPUT_CANDIDATE='REVIEW_INPUT_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'; INVALID_VALUE='INVALID_VALUE'
    BASE_UNAVAILABLE='BASE_UNAVAILABLE'; BASE_BUDGET_INSUFFICIENT='BASE_BUDGET_INSUFFICIENT'
    REQUIRED_DETAIL_MISSING='REQUIRED_DETAIL_MISSING'; MANDATORY_BUDGET_INSUFFICIENT='MANDATORY_BUDGET_INSUFFICIENT'
    BASE_ONLY_NOT_ALLOWED='BASE_ONLY_NOT_ALLOWED'

@dataclass(frozen=True)
class DetailChunk:
    chunk_id:str
    importance:float
    size_bytes:int
    latency_ms:float
    critical:bool
    required:bool
    quality_gain:float
    available:bool=True

@dataclass(frozen=True)
class ProgressiveRestorationRequest:
    request_id:str
    base_id:str
    base_size_bytes:int
    base_latency_ms:float
    base_quality:float
    base_available:bool
    detail_chunks:tuple[DetailChunk,...]
    byte_budget:int
    latency_budget_ms:float
    allow_base_only:bool
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class RestorationStage:
    stage_index:int
    stage_kind:str
    item_id:str
    priority:str
    cumulative_quality:float
    cumulative_bytes:int
    cumulative_latency_ms:float

@dataclass(frozen=True)
class ProgressiveRestorationResult:
    decision:Decision
    next_action:NextAction
    escalation:Escalation
    engine_state:EngineState
    request_id:str
    stage_order:tuple[RestorationStage,...]
    scheduled_detail_ids:tuple[str,...]
    deferred_detail_ids:tuple[str,...]
    required_detail_ids:tuple[str,...]
    required_details_complete:bool
    critical_detail_ids:tuple[str,...]
    critical_scheduled_ids:tuple[str,...]
    base_only:bool
    base_only_policy_explicitly_allowed:bool
    estimated_final_quality:float
    bytes_consumed:int
    latency_consumed_ms:float
    byte_budget:int
    latency_budget_ms:float
    budget_feasible:bool
    next_gate_candidate:bool
    reasons:tuple[str,...]
    source_chunks_mutated:bool=False
    restoration_executed:bool=False
    transfer_executed:bool=False
    stage_committed:bool=False
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
    plan_committed:bool=False
    external_write_performed:bool=False
    world_truth_proven:bool=False
    domain_authority_promoted:bool=False
    safety_proven:bool=False
    action_success:bool=False

@dataclass(frozen=True)
class PreparedProgressiveRestorationState:
    request:ProgressiveRestorationRequest
    result:ProgressiveRestorationResult
    base_fingerprint:str
    detail_fingerprint:str
    config_fingerprint:str
    result_fingerprint:str
    integrity_fingerprint:str
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class ProgressiveRestorationChange:
    base_changed:bool
    detail_changed:bool
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
def _valid_number(v): return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(float(v))

def _priority(c:DetailChunk)->int:
    if c.critical: return 1
    if c.required or c.importance>=0.80: return 2
    if c.importance>=0.45: return 3
    return 4

def _score(c:DetailChunk)->float:
    cost=max(1.0,float(c.size_bytes)/256.0 + float(c.latency_ms)*8.0)
    return float(c.importance)/cost

def _invalid(q,reason,esc,decision=Decision.HOLD):
    return ProgressiveRestorationResult(decision,NextAction.REVIEW_INPUT_CANDIDATE,esc,EngineState.INVALID,getattr(q,'request_id',''),(),(),(),(),False,(),(),False,False,0.0,0,0.0,getattr(q,'byte_budget',0),float(getattr(q,'latency_budget_ms',0.0) or 0.0),False,False,(reason,'NO_AUTHORITATIVE_STATE_PROMOTION','FULL_ORIGINAL_RETENTION_REMAINS_CANDIDATE','DCSR_STATE_IS_NOT_AUTHORITATIVE_STATE'))

def _validate(q):
    if not q.request_id or not q.base_id or not q.binding or not q.state_epoch: return ('EMPTY_REQUEST_CONTEXT',Escalation.INVALID_CONFIGURATION)
    if not isinstance(q.base_size_bytes,int) or isinstance(q.base_size_bytes,bool) or q.base_size_bytes<=0: return ('INVALID_BASE_SIZE',Escalation.INVALID_CONFIGURATION)
    if not _valid_number(q.base_latency_ms) or float(q.base_latency_ms)<0: return ('INVALID_BASE_LATENCY',Escalation.INVALID_VALUE)
    if not _valid_number(q.base_quality) or not 0.0<=float(q.base_quality)<=1.0: return ('INVALID_BASE_QUALITY',Escalation.INVALID_VALUE)
    if not isinstance(q.byte_budget,int) or isinstance(q.byte_budget,bool) or q.byte_budget<0: return ('INVALID_BYTE_BUDGET',Escalation.INVALID_CONFIGURATION)
    if not _valid_number(q.latency_budget_ms) or float(q.latency_budget_ms)<0: return ('INVALID_LATENCY_BUDGET',Escalation.INVALID_VALUE)
    ids=[c.chunk_id for c in q.detail_chunks]
    if any(not x for x in ids) or len(ids)!=len(set(ids)): return ('INVALID_OR_DUPLICATE_CHUNK_ID',Escalation.INVALID_CONFIGURATION)
    for c in q.detail_chunks:
        if not _valid_number(c.importance) or not 0.0<=float(c.importance)<=1.0: return ('INVALID_CHUNK_IMPORTANCE',Escalation.INVALID_VALUE)
        if not isinstance(c.size_bytes,int) or isinstance(c.size_bytes,bool) or c.size_bytes<=0: return ('INVALID_CHUNK_SIZE',Escalation.INVALID_CONFIGURATION)
        if not _valid_number(c.latency_ms) or float(c.latency_ms)<0: return ('INVALID_CHUNK_LATENCY',Escalation.INVALID_VALUE)
        if not _valid_number(c.quality_gain) or float(c.quality_gain)<0: return ('INVALID_QUALITY_GAIN',Escalation.INVALID_VALUE)
    return None

def _hold(q,esc,reason,stages=(),scheduled=(),deferred=(),required=(),critical=(),critical_scheduled=(),bytes_used=0,latency_used=0.0,quality=0.0):
    return ProgressiveRestorationResult(Decision.HOLD,NextAction.RETAIN_FULL_ORIGINAL_CANDIDATE,esc,EngineState.FULL_ORIGINAL_RETENTION_CANDIDATE,q.request_id,tuple(stages),tuple(scheduled),tuple(deferred),tuple(required),False,tuple(critical),tuple(critical_scheduled),len(scheduled)==0,False,round(float(quality),12),int(bytes_used),round(float(latency_used),12),q.byte_budget,float(q.latency_budget_ms),False,False,(reason,'INCOMPLETE_RESTORATION_NOT_TREATED_AS_COMPLETE','FULL_ORIGINAL_RETENTION_CANDIDATE','NO_PERMISSION_WRITE_TRANSFER_OR_ACTION_EXECUTION'))

def evaluate(q):
    bad=_validate(q)
    if bad:
        deny={Escalation.INVALID_VALUE}
        return _invalid(q,bad[0],bad[1],Decision.DENY if bad[1] in deny else Decision.HOLD)
    required=tuple(c.chunk_id for c in q.detail_chunks if c.required)
    critical=tuple(c.chunk_id for c in q.detail_chunks if c.critical)
    unavailable_required=tuple(c.chunk_id for c in q.detail_chunks if c.required and not c.available)
    if not q.base_available:
        return _hold(q,Escalation.BASE_UNAVAILABLE,'REQUIRED_BASE_UNAVAILABLE',required=required,critical=critical)
    if q.base_size_bytes>q.byte_budget or float(q.base_latency_ms)>float(q.latency_budget_ms):
        return _hold(q,Escalation.BASE_BUDGET_INSUFFICIENT,'BASE_DOES_NOT_FIT_BUDGET',required=required,critical=critical)
    base_stage=RestorationStage(0,'BASE',q.base_id,'P0',round(float(q.base_quality),12),q.base_size_bytes,round(float(q.base_latency_ms),12))
    if unavailable_required:
        return _hold(q,Escalation.REQUIRED_DETAIL_MISSING,'REQUIRED_DETAIL_UNAVAILABLE',stages=(base_stage,),deferred=tuple(c.chunk_id for c in q.detail_chunks),required=required,critical=critical,bytes_used=q.base_size_bytes,latency_used=q.base_latency_ms,quality=q.base_quality)
    req_chunks=[c for c in q.detail_chunks if c.required]
    mandatory_bytes=q.base_size_bytes+sum(c.size_bytes for c in req_chunks)
    mandatory_latency=float(q.base_latency_ms)+sum(float(c.latency_ms) for c in req_chunks)
    if mandatory_bytes>q.byte_budget or mandatory_latency>float(q.latency_budget_ms):
        return _hold(q,Escalation.MANDATORY_BUDGET_INSUFFICIENT,'REQUIRED_DETAIL_DOES_NOT_FIT_BUDGET',stages=(base_stage,),deferred=tuple(c.chunk_id for c in q.detail_chunks),required=required,critical=critical,bytes_used=q.base_size_bytes,latency_used=q.base_latency_ms,quality=q.base_quality)
    ordered=sorted((c for c in q.detail_chunks if c.available),key=lambda c:(_priority(c),-_score(c),-float(c.importance),c.size_bytes,float(c.latency_ms),c.chunk_id))
    bytes_used=q.base_size_bytes; latency_used=float(q.base_latency_ms); quality=float(q.base_quality)
    stages=[base_stage]; scheduled=[]; deferred=[]
    remaining_required={c.chunk_id:c for c in req_chunks}
    for c in ordered:
        reserve_bytes=sum(x.size_bytes for k,x in remaining_required.items() if k!=c.chunk_id)
        reserve_latency=sum(float(x.latency_ms) for k,x in remaining_required.items() if k!=c.chunk_id)
        fits=(bytes_used+c.size_bytes+reserve_bytes<=q.byte_budget and latency_used+float(c.latency_ms)+reserve_latency<=float(q.latency_budget_ms))
        if c.required:
            fits=True  # mandatory precheck + optional reservation make this safe
        if fits:
            bytes_used+=c.size_bytes; latency_used+=float(c.latency_ms); quality=min(1.0,quality+float(c.quality_gain)); scheduled.append(c.chunk_id)
            if c.chunk_id in remaining_required: remaining_required.pop(c.chunk_id,None)
            stages.append(RestorationStage(len(stages),'DETAIL',c.chunk_id,f'P{_priority(c)}',round(quality,12),bytes_used,round(latency_used,12)))
        else:
            deferred.append(c.chunk_id)
    unavailable_optional=[c.chunk_id for c in q.detail_chunks if not c.available and not c.required]
    deferred.extend(x for x in unavailable_optional if x not in deferred)
    required_complete=all(x in scheduled for x in required)
    critical_scheduled=tuple(x for x in scheduled if x in set(critical))
    if not required_complete:
        return _hold(q,Escalation.MANDATORY_BUDGET_INSUFFICIENT,'REQUIRED_DETAIL_NOT_SCHEDULED',stages=stages,scheduled=scheduled,deferred=deferred,required=required,critical=critical,critical_scheduled=critical_scheduled,bytes_used=bytes_used,latency_used=latency_used,quality=quality)
    base_only=(len(scheduled)==0)
    if base_only and not q.allow_base_only:
        return _hold(q,Escalation.BASE_ONLY_NOT_ALLOWED,'BASE_ONLY_POLICY_NOT_ALLOWED',stages=stages,scheduled=scheduled,deferred=deferred,required=required,critical=critical,critical_scheduled=critical_scheduled,bytes_used=bytes_used,latency_used=latency_used,quality=quality)
    reasons=['BASE_STAGE0_SCHEDULED','REQUIRED_DETAILS_COMPLETE','CRITICAL_DETAILS_PRIORITIZED','OPTIONAL_OVER_BUDGET_DEFERRED','SCHEDULE_IS_CANDIDATE_NOT_EXECUTION','NO_AUTHORITATIVE_STATE_PROMOTION','NO_PERMISSION_WRITE_TRANSFER_OR_ACTION_EXECUTION']
    if base_only: reasons.append('BASE_ONLY_POLICY_EXPLICITLY_ALLOWED')
    return ProgressiveRestorationResult(Decision.ALLOW,NextAction.CONTINUE_PROGRESSIVE_RESTORATION_CANDIDATE,Escalation.NONE,EngineState.PROGRESSIVE_RESTORATION_CANDIDATE,q.request_id,tuple(stages),tuple(scheduled),tuple(deferred),required,True,critical,critical_scheduled,base_only,bool(q.allow_base_only and base_only),round(quality,12),bytes_used,round(latency_used,12),q.byte_budget,float(q.latency_budget_ms),True,True,tuple(reasons))

def default_request():
    chunks=(
        DetailChunk('CRIT-A',1.00,360,1.5,True,True,0.12,True),
        DetailChunk('CRIT-B',0.98,420,1.8,True,True,0.10,True),
        DetailChunk('CRIT-C',0.94,520,2.4,True,False,0.08,True),
        DetailChunk('REQ-A',0.88,300,1.2,False,True,0.06,True),
        DetailChunk('DETAIL-H1',0.86,410,1.8,False,False,0.055,True),
        DetailChunk('DETAIL-H2',0.79,450,2.0,False,False,0.050,True),
        DetailChunk('DETAIL-M1',0.68,560,2.6,False,False,0.045,True),
        DetailChunk('DETAIL-M2',0.55,620,3.0,False,False,0.040,True),
        DetailChunk('DETAIL-L1',0.32,920,4.5,False,False,0.030,True),
        DetailChunk('DETAIL-L2',0.18,1100,5.5,False,False,0.020,True),
    )
    return ProgressiveRestorationRequest('PRS-170-A','BASE-170',800,4.0,0.35,True,chunks,4300,25.0,False,'DEFAULT-BINDING','EPOCH-1')
def default_evaluation(): return evaluate(default_request())

def _base_fp(q): return _fp((q.base_id,q.base_size_bytes,q.base_latency_ms,q.base_quality,q.base_available))
def _detail_fp(q): return _fp(q.detail_chunks)
def _config_fp(q): return _fp((q.byte_budget,q.latency_budget_ms,q.allow_base_only,q.binding,q.state_epoch))
def prepare_state(q,binding,state_epoch):
    if q.binding!=binding or q.state_epoch!=state_epoch:
        r=_invalid(q,'PREPARED_BINDING_MISMATCH',Escalation.INVALID_CONFIGURATION)
        return PreparedProgressiveRestorationState(q,r,'0'*64,'0'*64,'0'*64,'0'*64,'0'*64,binding,state_epoch)
    r=evaluate(q); bf=_base_fp(q); df=_detail_fp(q); cf=_config_fp(q); rf=_fp(r); integ=_fp((bf,df,cf,rf,binding,state_epoch))
    return PreparedProgressiveRestorationState(q,r,bf,df,cf,rf,integ,binding,state_epoch)
def evaluate_prepared(st,*,integrity_validated,current_base_fingerprint,current_detail_fingerprint,current_config_fingerprint,current_result_fingerprint):
    q=st.request
    if not integrity_validated: return _invalid(q,'PREPARED_INTEGRITY_NOT_VALIDATED',Escalation.INVALID_CONFIGURATION)
    if current_base_fingerprint!=st.base_fingerprint: return _invalid(q,'PREPARED_BASE_FINGERPRINT_MISMATCH',Escalation.INVALID_CONFIGURATION)
    if current_detail_fingerprint!=st.detail_fingerprint: return _invalid(q,'PREPARED_DETAIL_FINGERPRINT_MISMATCH',Escalation.INVALID_CONFIGURATION)
    if current_config_fingerprint!=st.config_fingerprint: return _invalid(q,'PREPARED_CONFIG_FINGERPRINT_MISMATCH',Escalation.INVALID_CONFIGURATION)
    if current_result_fingerprint!=st.result_fingerprint: return _invalid(q,'PREPARED_RESULT_FINGERPRINT_MISMATCH',Escalation.INVALID_CONFIGURATION)
    if _fp((st.base_fingerprint,st.detail_fingerprint,st.config_fingerprint,st.result_fingerprint,st.binding,st.state_epoch))!=st.integrity_fingerprint: return _invalid(q,'PREPARED_INTEGRITY_FINGERPRINT_MISMATCH',Escalation.INVALID_CONFIGURATION)
    return st.result

def make_delta(a,b):
    return ProgressiveRestorationChange(a.base_fingerprint!=b.base_fingerprint,a.detail_fingerprint!=b.detail_fingerprint,a.config_fingerprint!=b.config_fingerprint,_fp((a.base_fingerprint,a.detail_fingerprint,a.config_fingerprint)),_fp((b.base_fingerprint,b.detail_fingerprint,b.config_fingerprint)))
def plan_missing_only(a,b):
    d=make_delta(a,b); ids=[]
    if d.base_changed: ids.append('BASE_STATE')
    if d.detail_changed: ids.append('DETAIL_CHUNKS')
    if d.config_changed: ids.append('RESTORATION_SCHEDULER_CONFIG')
    return MissingOnlyPlan(tuple(ids),104+len(ids)*19,False)
