"""NOEPIN AL 168 — Shared-Base Delta Compressor — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-168
DCSR: DIRECT INTEGRATION / 直接統合.

Deterministic, side-effect-free evaluator for exact shared-base delta compression candidates.
A shared base is treated as a candidate/reference state only. Compatible variants may become
lossless delta candidates only when exact reconstruction matches the original fingerprint and the
delta representation is smaller than both the full representation and the configured threshold.
Incompatible or non-beneficial variants remain individual-full retention candidates. Critical
variants require reversible exact reconstruction. No storage mutation, deletion, file write,
network transfer, permission grant, authoritative-state promotion, fallback execution, or action
execution is performed.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json

class Decision(str, Enum):
    ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class EngineState(str, Enum):
    SHARED_BASE_DELTA_CANDIDATE='SHARED_BASE_DELTA_CANDIDATE'
    INDIVIDUAL_FULL_RETENTION_CANDIDATE='INDIVIDUAL_FULL_RETENTION_CANDIDATE'
    INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_SHARED_BASE_DELTA_CANDIDATE='CONTINUE_SHARED_BASE_DELTA_CANDIDATE'
    RETAIN_INDIVIDUAL_FULL_CANDIDATE='RETAIN_INDIVIDUAL_FULL_CANDIDATE'
    REVIEW_INPUT_CANDIDATE='REVIEW_INPUT_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'; EMPTY_VARIANTS='EMPTY_VARIANTS'
    DUPLICATE_VARIANT_ID='DUPLICATE_VARIANT_ID'; EMPTY_BASE='EMPTY_BASE'; INVALID_VALUE='INVALID_VALUE'
    INVALID_THRESHOLD='INVALID_THRESHOLD'; BASE_VARIANT_MISSING='BASE_VARIANT_MISSING'
    NO_BENEFICIAL_DELTA='NO_BENEFICIAL_DELTA'

@dataclass(frozen=True)
class Variant:
    variant_id:str
    compatibility_group:str
    values:tuple[int,...]
    critical:bool=False

@dataclass(frozen=True)
class DeltaEntry:
    index:int
    value:int

@dataclass(frozen=True)
class VariantPlan:
    variant_id:str
    compatibility_group:str
    mode:str
    reason:str
    delta:tuple[DeltaEntry,...]
    full_bytes:int
    delta_bytes:int
    delta_ratio:float
    reversible:bool
    reconstruction_match:bool
    source_fingerprint:str
    reconstructed_fingerprint:str

@dataclass(frozen=True)
class SharedBaseDeltaRequest:
    request_id:str
    variants:tuple[Variant,...]
    base_variant_id:str
    delta_ratio_threshold:float
    require_reversible_for_critical:bool
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class SharedBaseDeltaResult:
    decision:Decision
    next_action:NextAction
    escalation:Escalation
    engine_state:EngineState
    request_id:str
    base_variant_id:str|None
    shared_base_fingerprint:str
    variant_plans:tuple[VariantPlan,...]
    delta_variant_count:int
    individual_full_variant_count:int
    incompatible_variant_count:int
    critical_variant_count:int
    critical_reversibility_preserved:bool
    all_reconstructions_exact:bool
    estimated_original_bytes:int
    estimated_candidate_bytes:int
    estimated_savings_bytes:int
    compression_ratio:float
    next_gate_candidate:bool
    reasons:tuple[str,...]
    source_variants_mutated:bool=False
    shared_base_committed:bool=False
    delta_storage_committed:bool=False
    individual_full_storage_committed:bool=False
    source_deleted:bool=False
    fallback_executed:bool=False
    reconstruction_map_written:bool=False
    authoritative_state_created:bool=False
    cached_state_promoted:bool=False
    reconstructed_state_promoted:bool=False
    partial_state_promoted:bool=False
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
    publish_executed:bool=False
    external_write_performed:bool=False
    world_truth_proven:bool=False
    domain_authority_promoted:bool=False
    safety_proven:bool=False
    action_success:bool=False

@dataclass(frozen=True)
class PreparedSharedBaseState:
    request:SharedBaseDeltaRequest
    result:SharedBaseDeltaResult
    variants_fingerprint:str
    config_fingerprint:str
    result_fingerprint:str
    integrity_fingerprint:str
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class SharedBaseDeltaChange:
    changed_variant_ids:tuple[str,...]
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
    return v

def _canon(v):
    return json.dumps(_obj(v),ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()

def _fp(v): return sha256(_canon(v)).hexdigest()

def _valid_int(v): return isinstance(v,int) and not isinstance(v,bool) and -(1<<31) <= v < (1<<31)

def _invalid(q,reason,esc,decision=Decision.HOLD):
    return SharedBaseDeltaResult(
        decision,NextAction.REVIEW_INPUT_CANDIDATE,esc,EngineState.INVALID,getattr(q,'request_id',''),None,'0'*64,(),0,0,0,0,
        False,False,0,0,0,1.0,False,
        (reason,'NO_STORAGE_MUTATION_OR_SOURCE_DELETION','FULL_ORIGINAL_RETENTION_REMAINS_CANDIDATE','DCSR_STATE_IS_NOT_AUTHORITATIVE_STATE')
    )

def _validate(q):
    if not q.request_id or not q.binding or not q.state_epoch: return ('EMPTY_REQUEST_CONTEXT',Escalation.INVALID_CONFIGURATION)
    if not q.variants: return ('EMPTY_VARIANTS',Escalation.EMPTY_VARIANTS)
    ids=[v.variant_id for v in q.variants]
    if any(not x for x in ids): return ('EMPTY_VARIANT_ID',Escalation.INVALID_CONFIGURATION)
    if len(set(ids))!=len(ids): return ('DUPLICATE_VARIANT_ID',Escalation.DUPLICATE_VARIANT_ID)
    if q.base_variant_id not in set(ids): return ('BASE_VARIANT_MISSING',Escalation.BASE_VARIANT_MISSING)
    if not isinstance(q.delta_ratio_threshold,(int,float)) or not 0.0 < float(q.delta_ratio_threshold) < 1.0:
        return ('INVALID_DELTA_RATIO_THRESHOLD',Escalation.INVALID_THRESHOLD)
    for v in q.variants:
        if not v.compatibility_group: return ('EMPTY_COMPATIBILITY_GROUP',Escalation.INVALID_CONFIGURATION)
        if not v.values: return ('EMPTY_BASE_OR_VARIANT',Escalation.EMPTY_BASE)
        if any(not _valid_int(x) for x in v.values): return ('INVALID_VARIANT_VALUE',Escalation.INVALID_VALUE)
    return None

def _compute_delta(base_values,variant_values):
    if len(base_values)!=len(variant_values): return None
    return tuple(DeltaEntry(i,v) for i,v in enumerate(variant_values) if v!=base_values[i])

def _reconstruct(base_values,delta):
    out=list(base_values)
    for e in delta:
        if e.index<0 or e.index>=len(out): return None
        out[e.index]=e.value
    return tuple(out)

def evaluate(q):
    bad=_validate(q)
    if bad:
        deny={Escalation.DUPLICATE_VARIANT_ID,Escalation.INVALID_VALUE}
        return _invalid(q,bad[0],bad[1],Decision.DENY if bad[1] in deny else Decision.HOLD)
    by_id={v.variant_id:v for v in q.variants}
    base=by_id[q.base_variant_id]
    base_fp=_fp(base.values)
    plans=[]
    delta_count=full_count=incompat=critical_count=0
    critical_ok=True; all_exact=True
    original_bytes=sum(len(_canon(v.values)) for v in q.variants)
    candidate_bytes=len(_canon(base.values))
    for v in q.variants:
        if v.critical: critical_count += 1
        src_fp=_fp(v.values)
        if v.variant_id==base.variant_id:
            fb=len(_canon(v.values))
            plans.append(VariantPlan(v.variant_id,v.compatibility_group,'SHARED_BASE','BASE_SELECTED',(),fb,0,0.0,True,True,src_fp,src_fp))
            continue
        fb=len(_canon(v.values))
        if v.compatibility_group!=base.compatibility_group or len(v.values)!=len(base.values):
            incompat += 1; full_count += 1; candidate_bytes += fb
            plans.append(VariantPlan(v.variant_id,v.compatibility_group,'INDIVIDUAL_FULL','INCOMPATIBLE_WITH_BASE',(),fb,fb,1.0,True,True,src_fp,src_fp))
            continue
        delta=_compute_delta(base.values,v.values)
        if delta is None:
            full_count += 1; candidate_bytes += fb
            plans.append(VariantPlan(v.variant_id,v.compatibility_group,'INDIVIDUAL_FULL','DELTA_UNAVAILABLE',(),fb,fb,1.0,False,False,src_fp,'0'*64))
            all_exact=False
            if v.critical: critical_ok=False
            continue
        recon=_reconstruct(base.values,delta)
        recon_fp=_fp(recon) if recon is not None else '0'*64
        exact=(recon is not None and recon==v.values and recon_fp==src_fp)
        reversible=exact
        db=len(_canon(delta)); ratio=(db/fb) if fb else 1.0
        beneficial=(db<fb and ratio<float(q.delta_ratio_threshold))
        critical_allowed=(not v.critical) or (not q.require_reversible_for_critical) or reversible
        if exact and beneficial and critical_allowed:
            delta_count += 1; candidate_bytes += db
            reason='EXACT_REVERSIBLE_DELTA_SMALLER_THAN_FULL'
            plans.append(VariantPlan(v.variant_id,v.compatibility_group,'DELTA',reason,delta,fb,db,ratio,reversible,exact,src_fp,recon_fp))
        else:
            full_count += 1; candidate_bytes += fb
            if not exact: reason='RECONSTRUCTION_MISMATCH_RETAIN_FULL'
            elif not critical_allowed: reason='CRITICAL_REVERSIBILITY_REQUIRED_RETAIN_FULL'
            elif db>=fb: reason='DELTA_NOT_SMALLER_THAN_FULL_RETAIN_FULL'
            else: reason='DELTA_RATIO_THRESHOLD_EXCEEDED_RETAIN_FULL'
            plans.append(VariantPlan(v.variant_id,v.compatibility_group,'INDIVIDUAL_FULL',reason,(),fb,db,ratio,reversible,exact,src_fp,recon_fp))
        if not exact: all_exact=False
        if v.critical and q.require_reversible_for_critical and not reversible: critical_ok=False
    savings=max(0,original_bytes-candidate_bytes)
    compression=(candidate_bytes/original_bytes) if original_bytes else 1.0
    if delta_count==0:
        reasons=('NO_BENEFICIAL_EXACT_DELTA','INDIVIDUAL_FULL_RETENTION_CANDIDATE_ONLY','CRITICAL_REVERSIBILITY_GUARD_ENFORCED','NO_STORAGE_MUTATION_OR_SOURCE_DELETION','DCSR_CANDIDATE_STATE_IS_NOT_AUTHORITATIVE_STATE')
        return SharedBaseDeltaResult(Decision.HOLD,NextAction.RETAIN_INDIVIDUAL_FULL_CANDIDATE,Escalation.NO_BENEFICIAL_DELTA,EngineState.INDIVIDUAL_FULL_RETENTION_CANDIDATE,q.request_id,base.variant_id,base_fp,tuple(plans),delta_count,full_count,incompat,critical_count,critical_ok,all_exact,original_bytes,candidate_bytes,savings,compression,False,reasons)
    reasons=('SHARED_BASE_CANDIDATE_FIXED','COMPATIBLE_VARIANTS_EVALUATED_FOR_EXACT_DELTA','DELTA_SMALLER_THAN_FULL_AND_THRESHOLD_REQUIRED','CRITICAL_REVERSIBILITY_GUARD_ENFORCED','RECONSTRUCTION_FINGERPRINT_VERIFIED','NON_BENEFICIAL_OR_INCOMPATIBLE_VARIANTS_RETAIN_FULL','NO_STORAGE_MUTATION_OR_SOURCE_DELETION','NO_PERMISSION_WRITE_DEPLOYMENT_OR_ACTION_EXECUTION')
    return SharedBaseDeltaResult(Decision.ALLOW,NextAction.CONTINUE_SHARED_BASE_DELTA_CANDIDATE,Escalation.NONE,EngineState.SHARED_BASE_DELTA_CANDIDATE,q.request_id,base.variant_id,base_fp,tuple(plans),delta_count,full_count,incompat,critical_count,critical_ok,all_exact,original_bytes,candidate_bytes,savings,compression,True,reasons)

def default_request():
    base=tuple((i*13 + (i%11)*7) % 4096 for i in range(256))
    variants=[]
    variants.append(Variant('BASE-A','GROUP-A',base,True))
    # 18 compatible sparse variants: exact deltas are beneficial.
    for j in range(1,19):
        x=list(base)
        for k in range(1+(j%4)):
            idx=(j*17+k*43)%256
            x[idx]=(x[idx]+j+k+1)%4096
        variants.append(Variant(f'VAR-{j:02d}','GROUP-A',tuple(x),j in {5,12,18}))
    # One compatible but dense variant: full retention is cheaper than delta.
    dense=tuple((v + (i%97)+1)%4096 for i,v in enumerate(base))
    variants.append(Variant('VAR-DENSE','GROUP-A',dense,False))
    # One incompatible variant remains individually retained.
    other=tuple((i*19+3)%4096 for i in range(256))
    variants.append(Variant('VAR-OTHER','GROUP-B',other,True))
    return SharedBaseDeltaRequest('SBDC-168-A',tuple(variants),'BASE-A',0.45,True,'DEFAULT-BINDING','EPOCH-1')

def default_evaluation(): return evaluate(default_request())

def _variants_fp(q): return _fp(q.variants)
def _config_fp(q): return _fp((q.base_variant_id,q.delta_ratio_threshold,q.require_reversible_for_critical,q.binding,q.state_epoch))
def prepare_state(q,binding,state_epoch):
    if q.binding!=binding or q.state_epoch!=state_epoch:
        r=_invalid(q,'PREPARED_BINDING_MISMATCH',Escalation.INVALID_CONFIGURATION)
        return PreparedSharedBaseState(q,r,'0'*64,'0'*64,'0'*64,'0'*64,binding,state_epoch)
    r=evaluate(q); vf=_variants_fp(q); cf=_config_fp(q); rf=_fp(r); integ=_fp((vf,cf,rf,binding,state_epoch))
    return PreparedSharedBaseState(q,r,vf,cf,rf,integ,binding,state_epoch)
def evaluate_prepared(st,*,integrity_validated,current_variants_fingerprint,current_config_fingerprint,current_result_fingerprint):
    q=st.request
    if not integrity_validated: return _invalid(q,'PREPARED_INTEGRITY_NOT_VALIDATED',Escalation.INVALID_CONFIGURATION)
    if current_variants_fingerprint!=st.variants_fingerprint: return _invalid(q,'PREPARED_VARIANTS_FINGERPRINT_MISMATCH',Escalation.INVALID_CONFIGURATION)
    if current_config_fingerprint!=st.config_fingerprint: return _invalid(q,'PREPARED_CONFIG_FINGERPRINT_MISMATCH',Escalation.INVALID_CONFIGURATION)
    if current_result_fingerprint!=st.result_fingerprint: return _invalid(q,'PREPARED_RESULT_FINGERPRINT_MISMATCH',Escalation.INVALID_CONFIGURATION)
    if _fp((st.variants_fingerprint,st.config_fingerprint,st.result_fingerprint,st.binding,st.state_epoch))!=st.integrity_fingerprint:
        return _invalid(q,'PREPARED_INTEGRITY_FINGERPRINT_MISMATCH',Escalation.INVALID_CONFIGURATION)
    return st.result

def make_delta(a,b):
    am={v.variant_id:v for v in a.request.variants}; bm={v.variant_id:v for v in b.request.variants}
    ids=sorted(set(am)|set(bm)); changed=tuple(i for i in ids if am.get(i)!=bm.get(i))
    af=_fp((a.variants_fingerprint,a.config_fingerprint)); bf=_fp((b.variants_fingerprint,b.config_fingerprint))
    return SharedBaseDeltaChange(changed,a.config_fingerprint!=b.config_fingerprint,af,bf)
def plan_missing_only(a,b):
    d=make_delta(a,b); ids=[f'VARIANT-{x}' for x in d.changed_variant_ids]
    if d.config_changed: ids.append('SHARED_BASE_DELTA_CONFIG')
    return MissingOnlyPlan(tuple(ids),104+len(ids)*18,False)
