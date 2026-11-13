"""NOEPIN AL 164 — Quantization Residual Sidecar Generator — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-164
DCSR: DIRECT INTEGRATION / 直接統合.

Deterministic quantization evaluator that partitions a numeric state into a quantized Base and
Residual Sidecar. Critical indices always retain residuals. Noncritical residuals are retained only
when they exceed the configured threshold. The result is a candidate representation only: it never
mutates the original values, writes files, deploys state, or promotes reconstructed/cached state to
authority. Invalid quantization or non-beneficial compression falls back to Original retention.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str, Enum): ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class EngineState(str, Enum):
    QUANTIZED_SIDECAR_CANDIDATE='QUANTIZED_SIDECAR_CANDIDATE'
    ORIGINAL_RETENTION_CANDIDATE='ORIGINAL_RETENTION_CANDIDATE'
    INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_QUANTIZED_SIDECAR_CANDIDATE='CONTINUE_QUANTIZED_SIDECAR_CANDIDATE'
    RETAIN_ORIGINAL_CANDIDATE='RETAIN_ORIGINAL_CANDIDATE'
    REVIEW_INPUT_CANDIDATE='REVIEW_INPUT_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; NONFINITE_INPUT='NONFINITE_INPUT'; INVALID_BIT_WIDTH='INVALID_BIT_WIDTH'; INVALID_THRESHOLD='INVALID_THRESHOLD'; INVALID_CRITICAL_INDEX='INVALID_CRITICAL_INDEX'; NO_COMPRESSION_BENEFIT='NO_COMPRESSION_BENEFIT'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'

@dataclass(frozen=True)
class QuantizationRequest:
    request_id:str; values:tuple[float,...]; bit_width:int; residual_threshold:float; critical_indices:tuple[int,...]; importance:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class ResidualEntry:
    index:int; residual:float; critical:bool
@dataclass(frozen=True)
class CompressionStats:
    original_bytes:int; candidate_bytes:int; saved_bytes:int; compression_ratio:float; beneficial:bool
@dataclass(frozen=True)
class QuantizationResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState; request_id:str
    quantized_base:tuple[int,...]; scale:float; zero_point:float; residual_sidecar:tuple[ResidualEntry,...]
    compression_stats:CompressionStats; manifest_fingerprint:str; reconstruction_max_abs_error:float
    original_retention_candidate:bool; next_gate_candidate:bool; reasons:tuple[str,...]
    original_values_mutated:bool=False; quantized_base_committed:bool=False; residual_sidecar_written:bool=False; manifest_written:bool=False
    authoritative_state_created:bool=False; cached_state_promoted:bool=False; reconstructed_state_promoted:bool=False; partial_state_promoted:bool=False
    original_deleted:bool=False; fallback_executed:bool=False; tool_invoked:bool=False; file_write_executed:bool=False; network_send_executed:bool=False
    dcsr_reconstruction_created_fact:bool=False; sender_authority_inherited:bool=False; sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False
    permission_granted:bool=False; approval_executed:bool=False; authority_granted:bool=False; stop_executed:bool=False; action_executed:bool=False
    plan_committed:bool=False; publish_executed:bool=False; external_write_performed:bool=False; world_truth_proven:bool=False
    domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedQuantizationState:
    request:QuantizationRequest; result:QuantizationResult; values_fingerprint:str; config_fingerprint:str; result_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class QuantizationDelta:
    values_changed:bool; config_changed:bool; from_manifest_fingerprint:str; to_manifest_fingerprint:str
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
    vals=tuple((i-256)*0.00390625 + ((i%7)-3)*0.00007 for i in range(512))
    return QuantizationRequest('QRS-164-A',vals,8,0.003,(0,127,255,511),'MIXED','DEFAULT-BINDING','EPOCH-1')

def _empty_stats(n=0): return CompressionStats(n*8,n*8,0,1.0,False)
def _invalid(reason, request_id='', n=0, escalation=Escalation.INVALID_CONFIGURATION):
    return QuantizationResult(Decision.HOLD,NextAction.REVIEW_INPUT_CANDIDATE,escalation,EngineState.INVALID,request_id,(),0.0,0.0,(),_empty_stats(n),'0'*64,0.0,True,False,(reason,'RECONSTRUCTED_PARTIAL_CACHED_STATE_IS_NOT_AUTHORITATIVE_STATE','ORIGINAL_RETAINED'))

def _validate(q):
    if not q.request_id or not q.binding or not q.state_epoch: return ('EMPTY_REQUEST_CONTEXT',Escalation.INVALID_CONFIGURATION)
    if not q.values: return ('EMPTY_VALUES',Escalation.INVALID_CONFIGURATION)
    if not isinstance(q.bit_width,int) or q.bit_width<2 or q.bit_width>16: return ('INVALID_BIT_WIDTH',Escalation.INVALID_BIT_WIDTH)
    if not math.isfinite(q.residual_threshold) or q.residual_threshold<0: return ('INVALID_THRESHOLD',Escalation.INVALID_THRESHOLD)
    if any(not math.isfinite(float(x)) for x in q.values): return ('NONFINITE_INPUT',Escalation.NONFINITE_INPUT)
    if len(set(q.critical_indices))!=len(q.critical_indices): return ('DUPLICATE_CRITICAL_INDEX',Escalation.INVALID_CRITICAL_INDEX)
    if any((not isinstance(i,int)) or i<0 or i>=len(q.values) for i in q.critical_indices): return ('INVALID_CRITICAL_INDEX',Escalation.INVALID_CRITICAL_INDEX)
    if not q.importance: return ('EMPTY_IMPORTANCE',Escalation.INVALID_CONFIGURATION)
    return None

def _reconstruct(base, scale, zero, sidecar):
    vals=[zero + q*scale for q in base]
    for r in sidecar: vals[r.index]+=r.residual
    return tuple(vals)

def evaluate(q):
    bad=_validate(q)
    if bad: return _invalid(bad[0],getattr(q,'request_id',''),len(getattr(q,'values',())),bad[1])
    vals=tuple(float(x) for x in q.values); n=len(vals); mn=min(vals); mx=max(vals); qmax=(1<<q.bit_width)-1
    if mx==mn:
        scale=1.0; zero=mn; base=tuple(0 for _ in vals)
    else:
        scale=(mx-mn)/qmax; zero=mn; base=tuple(max(0,min(qmax,int(round((x-zero)/scale)))) for x in vals)
    crit=set(q.critical_indices); side=[]
    approx=[zero+b*scale for b in base]
    for idx,(x,a) in enumerate(zip(vals,approx)):
        residual=x-a
        if idx in crit or abs(residual)>q.residual_threshold:
            side.append(ResidualEntry(idx,residual,idx in crit))
    side=tuple(side)
    recon=_reconstruct(base,scale,zero,side)
    max_err=max(abs(a-b) for a,b in zip(vals,recon)) if vals else 0.0
    base_bytes=(n*q.bit_width+7)//8
    metadata_bytes=32
    sidecar_bytes=len(side)*17
    candidate=base_bytes+metadata_bytes+sidecar_bytes
    original=n*8
    saved=original-candidate
    stats=CompressionStats(original,candidate,max(0,saved),candidate/original if original else 1.0,candidate<original)
    manifest=_fp((base,scale,zero,side,q.bit_width,q.residual_threshold,q.critical_indices,q.binding,q.state_epoch))
    common=(
        'QUANTIZED_BASE_AND_RESIDUAL_SIDECAR_ARE_CANDIDATE_STATE_NOT_AUTHORITATIVE_STATE',
        'CRITICAL_INDICES_ALWAYS_RETAIN_RESIDUAL',
        'NONCRITICAL_RESIDUALS_AT_OR_BELOW_THRESHOLD_MAY_BE_OMITTED',
        'BASE_AND_SIDECAR_ARE_BOUND_BY_MANIFEST_FINGERPRINT',
        'RECONSTRUCTED_PARTIAL_CACHED_STATE_IS_NOT_AUTHORITATIVE_STATE',
        'ORIGINAL_VALUES_ARE_RETAINED',
        'NO_EXTERNAL_WRITE_PERMISSION_ACTION_OR_SUCCESS_EXECUTION',
    )
    if not stats.beneficial:
        return QuantizationResult(Decision.HOLD,NextAction.RETAIN_ORIGINAL_CANDIDATE,Escalation.NO_COMPRESSION_BENEFIT,EngineState.ORIGINAL_RETENTION_CANDIDATE,q.request_id,base,scale,zero,side,stats,manifest,max_err,True,True,common+('NO_COMPRESSION_BENEFIT_RETAIN_ORIGINAL',))
    return QuantizationResult(Decision.ALLOW,NextAction.CONTINUE_QUANTIZED_SIDECAR_CANDIDATE,Escalation.NONE,EngineState.QUANTIZED_SIDECAR_CANDIDATE,q.request_id,base,scale,zero,side,stats,manifest,max_err,False,True,common)

def default_evaluation(): return evaluate(default_request())
def prepare_state(q,binding,state_epoch):
    if q.binding!=binding or q.state_epoch!=state_epoch:
        r=_invalid('PREPARED_BINDING_MISMATCH',q.request_id,len(q.values)); return PreparedQuantizationState(q,r,'0'*64,'0'*64,'0'*64,'0'*64,binding,state_epoch)
    r=evaluate(q); vf=_fp(q.values); cf=_fp((q.request_id,q.bit_width,q.residual_threshold,q.critical_indices,q.importance,q.binding,q.state_epoch)); rf=_fp(r); integ=_fp((vf,cf,rf,binding,state_epoch))
    return PreparedQuantizationState(q,r,vf,cf,rf,integ,binding,state_epoch)
def evaluate_prepared(st,*,integrity_validated,current_values_fingerprint,current_config_fingerprint,current_result_fingerprint):
    if not integrity_validated: return _invalid('PREPARED_INTEGRITY_NOT_VALIDATED',st.request.request_id,len(st.request.values))
    if current_values_fingerprint!=st.values_fingerprint: return _invalid('PREPARED_VALUES_FINGERPRINT_MISMATCH',st.request.request_id,len(st.request.values))
    if current_config_fingerprint!=st.config_fingerprint: return _invalid('PREPARED_CONFIG_FINGERPRINT_MISMATCH',st.request.request_id,len(st.request.values))
    if current_result_fingerprint!=st.result_fingerprint: return _invalid('PREPARED_RESULT_FINGERPRINT_MISMATCH',st.request.request_id,len(st.request.values))
    if _fp((st.values_fingerprint,st.config_fingerprint,st.result_fingerprint,st.binding,st.state_epoch))!=st.integrity_fingerprint: return _invalid('PREPARED_INTEGRITY_FINGERPRINT_MISMATCH',st.request.request_id,len(st.request.values))
    return st.result
def make_delta(a,b):
    ff=_fp((a.values_fingerprint,a.config_fingerprint)); tf=_fp((b.values_fingerprint,b.config_fingerprint))
    return QuantizationDelta(a.values_fingerprint!=b.values_fingerprint,a.config_fingerprint!=b.config_fingerprint,ff,tf)
def plan_missing_only(a,b):
    d=make_delta(a,b); ids=[]
    if d.values_changed: ids.append('VALUES')
    if d.config_changed: ids.append('CONFIG')
    return MissingOnlyPlan(tuple(ids),88+len(ids)*8,False)
