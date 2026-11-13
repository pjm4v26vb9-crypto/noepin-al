"""NOEPIN AL 165 — Residual Reconstruction Injector — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-165
DCSR: DIRECT INTEGRATION / 直接統合.

Deterministic, side-effect-free reconstruction evaluator. It validates the quantized Base,
source Manifest, Residual Sidecar, progressive stage fingerprints, indices, checksum/fingerprint
constraints, and error limit before producing a reconstructed-array candidate. It never mutates
source data, writes files, deploys state, grants permission, or promotes reconstructed/cached state
to authoritative state. Any uncertain or inconsistent reconstruction remains HOLD/DENY candidate
and preserves Full/Original fallback as a candidate only.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str, Enum): ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class EngineState(str, Enum):
    RECONSTRUCTED_ARRAY_CANDIDATE='RECONSTRUCTED_ARRAY_CANDIDATE'
    BASE_ONLY_RECONSTRUCTION_CANDIDATE='BASE_ONLY_RECONSTRUCTION_CANDIDATE'
    ORIGINAL_FALLBACK_CANDIDATE='ORIGINAL_FALLBACK_CANDIDATE'
    INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_RECONSTRUCTED_ARRAY_CANDIDATE='CONTINUE_RECONSTRUCTED_ARRAY_CANDIDATE'
    CONTINUE_BASE_ONLY_CANDIDATE='CONTINUE_BASE_ONLY_CANDIDATE'
    RETAIN_ORIGINAL_CANDIDATE='RETAIN_ORIGINAL_CANDIDATE'
    REVIEW_INPUT_CANDIDATE='REVIEW_INPUT_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'; MANIFEST_MISMATCH='MANIFEST_MISMATCH'
    RESIDUAL_INDEX_OUT_OF_RANGE='RESIDUAL_INDEX_OUT_OF_RANGE'; DUPLICATE_RESIDUAL_INDEX='DUPLICATE_RESIDUAL_INDEX'
    RESIDUAL_SIDECAR_MISSING='RESIDUAL_SIDECAR_MISSING'; PARTIAL_RESIDUAL_SIDECAR='PARTIAL_RESIDUAL_SIDECAR'
    STAGE_FINGERPRINT_MISMATCH='STAGE_FINGERPRINT_MISMATCH'; CHECKSUM_MISMATCH='CHECKSUM_MISMATCH'
    ERROR_LIMIT_EXCEEDED='ERROR_LIMIT_EXCEEDED'; NONFINITE_INPUT='NONFINITE_INPUT'; CRITICAL_RESIDUAL_MISSING='CRITICAL_RESIDUAL_MISSING'

@dataclass(frozen=True)
class ResidualRecord:
    index:int; residual:float; critical:bool; stage:int
@dataclass(frozen=True)
class ReconstructionManifest:
    source_manifest_fingerprint:str; expected_residual_count:int; expected_residual_indices:tuple[int,...]
    critical_indices:tuple[int,...]; stage_fingerprints:tuple[tuple[int,str],...]
    expected_reconstructed_fingerprint:str; max_abs_error:float; base_only_allowed:bool
@dataclass(frozen=True)
class ReconstructionRequest:
    request_id:str; quantized_base:tuple[int,...]; scale:float; zero_point:float; bit_width:int; residual_threshold:float
    residual_sidecar:tuple[ResidualRecord,...]; manifest:ReconstructionManifest; reference_values:tuple[float,...]
    binding:str; state_epoch:str
@dataclass(frozen=True)
class StageAudit:
    stage:int; applied_count:int; stage_fingerprint:str; verified:bool
@dataclass(frozen=True)
class ReconstructionResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState; request_id:str
    reconstructed_values:tuple[float,...]; reconstruction_max_abs_error:float; applied_residual_count:int
    stage_audit:tuple[StageAudit,...]; reconstructed_fingerprint:str; source_manifest_verified:bool
    residual_sidecar_verified:bool; checksum_verified:bool; error_limit_verified:bool
    base_only_candidate:bool; original_fallback_candidate:bool; next_gate_candidate:bool; reasons:tuple[str,...]
    quantized_base_mutated:bool=False; residual_sidecar_mutated:bool=False; reconstructed_values_committed:bool=False
    source_manifest_written:bool=False; stage_manifest_written:bool=False; original_deleted:bool=False; fallback_executed:bool=False
    authoritative_state_created:bool=False; cached_state_promoted:bool=False; reconstructed_state_promoted:bool=False; partial_state_promoted:bool=False
    tool_invoked:bool=False; file_write_executed:bool=False; network_send_executed:bool=False; dcsr_reconstruction_created_fact:bool=False
    sender_authority_inherited:bool=False; sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False
    permission_granted:bool=False; approval_executed:bool=False; authority_granted:bool=False; stop_executed:bool=False
    action_executed:bool=False; plan_committed:bool=False; publish_executed:bool=False; external_write_performed:bool=False
    world_truth_proven:bool=False; domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedReconstructionState:
    request:ReconstructionRequest; result:ReconstructionResult; base_fingerprint:str; sidecar_fingerprint:str
    manifest_fingerprint:str; result_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class ReconstructionDelta:
    base_changed:bool; sidecar_changed:bool; manifest_changed:bool; from_fingerprint:str; to_fingerprint:str
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
def _stage_fp(records): return _fp(tuple({'index':r.index,'residual':r.residual,'critical':r.critical} for r in records))
def _source_sidecar(records): return tuple({'index':r.index,'residual':r.residual,'critical':r.critical} for r in records)
def _source_manifest(q):
    return _fp((q.quantized_base,q.scale,q.zero_point,_source_sidecar(q.residual_sidecar),q.bit_width,q.residual_threshold,q.manifest.critical_indices,q.binding,q.state_epoch))
def _base_values(q): return tuple(q.zero_point + int(x)*q.scale for x in q.quantized_base)
def _all_finite(xs): return all(math.isfinite(float(x)) for x in xs)

def _empty_result(q,reason,escalation=Escalation.INVALID_CONFIGURATION,decision=Decision.HOLD):
    n=len(getattr(q,'quantized_base',())) if q is not None else 0
    return ReconstructionResult(decision,NextAction.REVIEW_INPUT_CANDIDATE,escalation,EngineState.INVALID,getattr(q,'request_id',''),(),0.0,0,(),'0'*64,False,False,False,False,False,True,False,(reason,'NO_RESIDUAL_INJECTION_ON_INVALID_INPUT','RECONSTRUCTED_PARTIAL_CACHED_STATE_IS_NOT_AUTHORITATIVE_STATE','FULL_ORIGINAL_FALLBACK_RETAINED_AS_CANDIDATE'))

def _validate(q):
    if not q.request_id or not q.binding or not q.state_epoch: return ('EMPTY_REQUEST_CONTEXT',Escalation.INVALID_CONFIGURATION)
    if not q.quantized_base: return ('EMPTY_QUANTIZED_BASE',Escalation.INVALID_CONFIGURATION)
    if not isinstance(q.bit_width,int) or q.bit_width<2 or q.bit_width>16: return ('INVALID_BIT_WIDTH',Escalation.INVALID_CONFIGURATION)
    if not math.isfinite(q.scale) or q.scale<=0 or not math.isfinite(q.zero_point): return ('INVALID_SCALE_OR_ZERO_POINT',Escalation.NONFINITE_INPUT)
    if not math.isfinite(q.residual_threshold) or q.residual_threshold<0: return ('INVALID_RESIDUAL_THRESHOLD',Escalation.INVALID_CONFIGURATION)
    if not math.isfinite(q.manifest.max_abs_error) or q.manifest.max_abs_error<0: return ('INVALID_ERROR_LIMIT',Escalation.INVALID_CONFIGURATION)
    qmax=(1<<q.bit_width)-1
    if any((not isinstance(x,int)) or x<0 or x>qmax for x in q.quantized_base): return ('INVALID_QUANTIZED_BASE_VALUE',Escalation.INVALID_CONFIGURATION)
    if any((not isinstance(r.index,int)) or (not isinstance(r.stage,int)) or r.stage<0 or not math.isfinite(r.residual) for r in q.residual_sidecar): return ('INVALID_RESIDUAL_RECORD',Escalation.NONFINITE_INPUT)
    if q.reference_values and (len(q.reference_values)!=len(q.quantized_base) or not _all_finite(q.reference_values)): return ('INVALID_REFERENCE_VALUES',Escalation.NONFINITE_INPUT)
    if len(q.manifest.source_manifest_fingerprint)!=64 or len(q.manifest.expected_reconstructed_fingerprint)!=64: return ('INVALID_MANIFEST_FINGERPRINT',Escalation.INVALID_CONFIGURATION)
    return None

def evaluate(q):
    bad=_validate(q)
    if bad: return _empty_result(q,bad[0],bad[1])
    n=len(q.quantized_base); records=tuple(q.residual_sidecar); expected_count=q.manifest.expected_residual_count
    indices=[r.index for r in records]
    if any(i<0 or i>=n for i in indices):
        return _empty_result(q,'RESIDUAL_INDEX_OUT_OF_RANGE',Escalation.RESIDUAL_INDEX_OUT_OF_RANGE,Decision.DENY)
    if len(set(indices))!=len(indices):
        return _empty_result(q,'DUPLICATE_RESIDUAL_INDEX',Escalation.DUPLICATE_RESIDUAL_INDEX,Decision.DENY)
    expected_indices=tuple(q.manifest.expected_residual_indices)
    expected_critical=set(q.manifest.critical_indices)
    actual=set(indices); expected=set(expected_indices)
    missing=expected-actual
    missing_critical=missing & expected_critical
    if missing_critical:
        return _empty_result(q,'CRITICAL_RESIDUAL_MISSING',Escalation.CRITICAL_RESIDUAL_MISSING,Decision.HOLD)
    if expected_count>0 and not records:
        if q.manifest.base_only_allowed and not expected_critical:
            base=_base_values(q); err=max(abs(a-b) for a,b in zip(base,q.reference_values)) if q.reference_values else q.manifest.max_abs_error
            fp=_fp(base); check=(not q.reference_values or fp==q.manifest.expected_reconstructed_fingerprint)
            if err>q.manifest.max_abs_error:
                return _empty_result(q,'BASE_ONLY_ERROR_LIMIT_EXCEEDED',Escalation.ERROR_LIMIT_EXCEEDED)
            reasons=('RESIDUAL_SIDECAR_MISSING_BASE_ONLY_POLICY_ALLOWS_CANDIDATE','BASE_ONLY_CANDIDATE_IS_NOT_AUTHORITATIVE_STATE','FULL_ORIGINAL_FALLBACK_RETAINED_AS_CANDIDATE','NO_EXTERNAL_WRITE_PERMISSION_ACTION_OR_SUCCESS_EXECUTION')
            return ReconstructionResult(Decision.ALLOW,NextAction.CONTINUE_BASE_ONLY_CANDIDATE,Escalation.RESIDUAL_SIDECAR_MISSING,EngineState.BASE_ONLY_RECONSTRUCTION_CANDIDATE,q.request_id,base,err,0,(),fp,False,False,check,True,True,False,True,reasons)
        return _empty_result(q,'RESIDUAL_SIDECAR_MISSING',Escalation.RESIDUAL_SIDECAR_MISSING)
    if len(records)!=expected_count or actual!=expected:
        return _empty_result(q,'PARTIAL_RESIDUAL_SIDECAR',Escalation.PARTIAL_RESIDUAL_SIDECAR)
    if _source_manifest(q)!=q.manifest.source_manifest_fingerprint:
        return _empty_result(q,'SOURCE_MANIFEST_MISMATCH',Escalation.MANIFEST_MISMATCH)
    expected_stage=dict(q.manifest.stage_fingerprints); audits=[]
    for stage in sorted({r.stage for r in records}):
        rs=tuple(r for r in records if r.stage==stage); fp=_stage_fp(rs); ok=expected_stage.get(stage)==fp
        audits.append(StageAudit(stage,len(rs),fp,ok))
        if not ok:
            return _empty_result(q,'STAGE_FINGERPRINT_MISMATCH',Escalation.STAGE_FINGERPRINT_MISMATCH)
    if set(expected_stage)!={r.stage for r in records}:
        return _empty_result(q,'STAGE_SET_MISMATCH',Escalation.STAGE_FINGERPRINT_MISMATCH)
    values=list(_base_values(q)); applied=0
    # Progressive injection: each verified stage is applied only after that stage fingerprint passes.
    for stage in sorted(expected_stage):
        for r in (x for x in records if x.stage==stage): values[r.index]+=r.residual; applied+=1
    recon=tuple(values); recon_fp=_fp(recon)
    checksum_ok=recon_fp==q.manifest.expected_reconstructed_fingerprint
    if not checksum_ok:
        return _empty_result(q,'RECONSTRUCTED_CHECKSUM_MISMATCH',Escalation.CHECKSUM_MISMATCH)
    err=max(abs(a-b) for a,b in zip(recon,q.reference_values)) if q.reference_values else 0.0
    if err>q.manifest.max_abs_error+1e-15:
        return _empty_result(q,'RECONSTRUCTION_ERROR_LIMIT_EXCEEDED',Escalation.ERROR_LIMIT_EXCEEDED)
    reasons=('SOURCE_MANIFEST_VERIFIED','ALL_RESIDUAL_INDICES_VERIFIED','EACH_PROGRESSIVE_STAGE_FINGERPRINT_VERIFIED','RECONSTRUCTED_CHECKSUM_VERIFIED','RECONSTRUCTION_ERROR_WITHIN_LIMIT','RECONSTRUCTED_ARRAY_IS_CANDIDATE_NOT_AUTHORITATIVE_STATE','FULL_ORIGINAL_FALLBACK_RETAINED_AS_CANDIDATE','NO_EXTERNAL_WRITE_PERMISSION_ACTION_OR_SUCCESS_EXECUTION')
    return ReconstructionResult(Decision.ALLOW,NextAction.CONTINUE_RECONSTRUCTED_ARRAY_CANDIDATE,Escalation.NONE,EngineState.RECONSTRUCTED_ARRAY_CANDIDATE,q.request_id,recon,err,applied,tuple(audits),recon_fp,True,True,True,True,False,True,True,reasons)

def _fixture_quantization(values,bit_width,residual_threshold,critical_indices,binding,state_epoch):
    vals=tuple(float(x) for x in values); mn=min(vals); mx=max(vals); qmax=(1<<bit_width)-1
    if mx==mn: scale=1.0; zero=mn; base=tuple(0 for _ in vals)
    else:
        scale=(mx-mn)/qmax; zero=mn; base=tuple(max(0,min(qmax,int(round((x-zero)/scale)))) for x in vals)
    approx=[zero+b*scale for b in base]; crit=set(critical_indices); raw=[]
    for idx,(x,a) in enumerate(zip(vals,approx)):
        residual=x-a
        if idx in crit or abs(residual)>residual_threshold: raw.append((idx,residual,idx in crit))
    source_side=tuple({'index':i,'residual':r,'critical':c} for i,r,c in raw)
    source_fp=_fp((base,scale,zero,source_side,bit_width,residual_threshold,tuple(critical_indices),binding,state_epoch))
    recs=tuple(ResidualRecord(i,r,c,0 if c else 1) for i,r,c in raw)
    stages=tuple((s,_stage_fp(tuple(x for x in recs if x.stage==s))) for s in sorted({x.stage for x in recs}))
    recon=list(zero+b*scale for b in base)
    for rr in recs: recon[rr.index]+=rr.residual
    return base,scale,zero,recs,source_fp,stages,tuple(recon)

def default_request():
    vals=tuple((i-256)*0.00390625 + ((i%7)-3)*0.00007 for i in range(512)); bit=8; threshold=0.003; critical=(0,127,255,511); binding='DEFAULT-BINDING'; epoch='EPOCH-1'
    base,scale,zero,recs,source_fp,stages,recon=_fixture_quantization(vals,bit,threshold,critical,binding,epoch)
    manifest=ReconstructionManifest(source_fp,len(recs),tuple(r.index for r in recs),critical,stages,_fp(recon),threshold,False)
    return ReconstructionRequest('RRI-165-A',base,scale,zero,bit,threshold,recs,manifest,vals,binding,epoch)
def default_evaluation(): return evaluate(default_request())

def prepare_state(q,binding,state_epoch):
    if q.binding!=binding or q.state_epoch!=state_epoch:
        r=_empty_result(q,'PREPARED_BINDING_MISMATCH'); return PreparedReconstructionState(q,r,'0'*64,'0'*64,'0'*64,'0'*64,'0'*64,binding,state_epoch)
    r=evaluate(q); bf=_fp((q.quantized_base,q.scale,q.zero_point,q.bit_width,q.residual_threshold)); sf=_fp(q.residual_sidecar); mf=_fp(q.manifest); rf=_fp(r); integ=_fp((bf,sf,mf,rf,binding,state_epoch))
    return PreparedReconstructionState(q,r,bf,sf,mf,rf,integ,binding,state_epoch)
def evaluate_prepared(st,*,integrity_validated,current_base_fingerprint,current_sidecar_fingerprint,current_manifest_fingerprint,current_result_fingerprint):
    q=st.request
    if not integrity_validated: return _empty_result(q,'PREPARED_INTEGRITY_NOT_VALIDATED')
    if current_base_fingerprint!=st.base_fingerprint: return _empty_result(q,'PREPARED_BASE_FINGERPRINT_MISMATCH')
    if current_sidecar_fingerprint!=st.sidecar_fingerprint: return _empty_result(q,'PREPARED_SIDECAR_FINGERPRINT_MISMATCH')
    if current_manifest_fingerprint!=st.manifest_fingerprint: return _empty_result(q,'PREPARED_MANIFEST_FINGERPRINT_MISMATCH')
    if current_result_fingerprint!=st.result_fingerprint: return _empty_result(q,'PREPARED_RESULT_FINGERPRINT_MISMATCH')
    if _fp((st.base_fingerprint,st.sidecar_fingerprint,st.manifest_fingerprint,st.result_fingerprint,st.binding,st.state_epoch))!=st.integrity_fingerprint: return _empty_result(q,'PREPARED_INTEGRITY_FINGERPRINT_MISMATCH')
    return st.result
def make_delta(a,b):
    af=_fp((a.base_fingerprint,a.sidecar_fingerprint,a.manifest_fingerprint)); bf=_fp((b.base_fingerprint,b.sidecar_fingerprint,b.manifest_fingerprint))
    return ReconstructionDelta(a.base_fingerprint!=b.base_fingerprint,a.sidecar_fingerprint!=b.sidecar_fingerprint,a.manifest_fingerprint!=b.manifest_fingerprint,af,bf)
def plan_missing_only(a,b):
    d=make_delta(a,b); ids=[]
    if d.base_changed: ids.append('QUANTIZED_BASE')
    if d.sidecar_changed: ids.append('RESIDUAL_SIDECAR')
    if d.manifest_changed: ids.append('MANIFEST')
    return MissingOnlyPlan(tuple(ids),96+len(ids)*12,False)
