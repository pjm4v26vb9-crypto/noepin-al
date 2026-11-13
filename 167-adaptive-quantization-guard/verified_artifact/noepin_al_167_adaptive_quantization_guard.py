"""NOEPIN AL 167 — Adaptive Quantization Guard — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-167
DCSR: DIRECT INTEGRATION / 直接統合.

Deterministic, side-effect-free adaptive quantization evaluator. Candidate bit widths are trial-quantized
and reconstructed in ascending order. The lightest candidate satisfying both importance-weighted error
and Critical maximum-error limits becomes a next-gate candidate. If every candidate fails, the result is
HOLD with Lossless/Original retention as a candidate only. No source mutation, quantization commit,
file write, deployment, permission grant, authoritative-state promotion, or action execution is performed.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str, Enum): ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class EngineState(str, Enum):
    QUANTIZATION_CANDIDATE='QUANTIZATION_CANDIDATE'
    LOSSLESS_RETENTION_CANDIDATE='LOSSLESS_RETENTION_CANDIDATE'
    INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_QUANTIZATION_CANDIDATE='CONTINUE_QUANTIZATION_CANDIDATE'
    RETAIN_LOSSLESS_ORIGINAL_CANDIDATE='RETAIN_LOSSLESS_ORIGINAL_CANDIDATE'
    REVIEW_INPUT_CANDIDATE='REVIEW_INPUT_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'; EMPTY_DATA='EMPTY_DATA'; LENGTH_MISMATCH='LENGTH_MISMATCH'
    NONFINITE_INPUT='NONFINITE_INPUT'; INVALID_IMPORTANCE='INVALID_IMPORTANCE'; INVALID_BIT_WIDTH='INVALID_BIT_WIDTH'
    ALL_CANDIDATES_REJECTED='ALL_CANDIDATES_REJECTED'; DUPLICATE_BIT_WIDTH='DUPLICATE_BIT_WIDTH'

@dataclass(frozen=True)
class QuantizationGuardRequest:
    request_id:str; values:tuple[float,...]; importance:tuple[float|None,...]; critical:tuple[bool,...]
    candidate_bits:tuple[int,...]; weighted_error_threshold:float; critical_max_error_threshold:float
    binding:str; state_epoch:str
@dataclass(frozen=True)
class CandidateEvaluation:
    bit_width:int; scale:float; weighted_error:float; max_error:float; critical_max_error:float
    weighted_error_pass:bool; critical_error_pass:bool; accepted:bool; reconstructed_fingerprint:str
@dataclass(frozen=True)
class QuantizationGuardResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState; request_id:str
    selected_bit_width:int|None; selected_weighted_error:float; selected_critical_max_error:float
    candidate_evaluations:tuple[CandidateEvaluation,...]; accepted_candidate_count:int; rejected_candidate_count:int
    all_candidates_tested:bool; lightest_acceptable_selected:bool; critical_error_guard_preserved:bool
    lossless_original_retention_candidate:bool; next_gate_candidate:bool; reasons:tuple[str,...]
    source_values_mutated:bool=False; quantization_committed:bool=False; reconstructed_values_committed:bool=False
    lossless_fallback_executed:bool=False; original_deleted:bool=False; candidate_state_written:bool=False
    authoritative_state_created:bool=False; cached_state_promoted:bool=False; reconstructed_state_promoted:bool=False
    partial_state_promoted:bool=False; tool_invoked:bool=False; file_write_executed:bool=False; network_send_executed:bool=False
    dcsr_reconstruction_created_fact:bool=False; sender_authority_inherited:bool=False; sender_intent_inherited:bool=False
    sender_agreement_inherited:bool=False; permission_granted:bool=False; approval_executed:bool=False
    authority_granted:bool=False; stop_executed:bool=False; action_executed:bool=False; plan_committed:bool=False
    publish_executed:bool=False; external_write_performed:bool=False; world_truth_proven:bool=False
    domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedQuantizationState:
    request:QuantizationGuardRequest; result:QuantizationGuardResult; values_fingerprint:str; config_fingerprint:str
    result_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class QuantizationDelta:
    changed_value_indices:tuple[int,...]; config_changed:bool; from_fingerprint:str; to_fingerprint:str
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
def _finite(v): return isinstance(v,(int,float)) and math.isfinite(float(v))
def _finite01_or_none(v): return v is None or (_finite(v) and 0.0<=float(v)<=1.0)

def _invalid(q, reason, esc, decision=Decision.HOLD):
    return QuantizationGuardResult(decision,NextAction.REVIEW_INPUT_CANDIDATE,esc,EngineState.INVALID,getattr(q,'request_id',''),None,0.0,0.0,(),0,0,False,False,False,True,False,(reason,'NO_QUANTIZATION_COMMIT_OR_SOURCE_MUTATION','LOSSLESS_ORIGINAL_RETENTION_REMAINS_CANDIDATE','DCSR_STATE_IS_NOT_AUTHORITATIVE_STATE'))

def _validate(q):
    if not q.request_id or not q.binding or not q.state_epoch: return ('EMPTY_REQUEST_CONTEXT',Escalation.INVALID_CONFIGURATION)
    if not q.values: return ('EMPTY_DATA',Escalation.EMPTY_DATA)
    if len(q.values)!=len(q.importance) or len(q.values)!=len(q.critical): return ('LENGTH_MISMATCH',Escalation.LENGTH_MISMATCH)
    if any(not _finite(v) for v in q.values): return ('NONFINITE_VALUE',Escalation.NONFINITE_INPUT)
    if any(not _finite01_or_none(x) for x in q.importance):
        bad=next(x for x in q.importance if not _finite01_or_none(x))
        return ('INVALID_IMPORTANCE',Escalation.NONFINITE_INPUT if isinstance(bad,(int,float)) and not math.isfinite(float(bad)) else Escalation.INVALID_IMPORTANCE)
    if not q.candidate_bits: return ('EMPTY_CANDIDATE_BITS',Escalation.INVALID_CONFIGURATION)
    if len(set(q.candidate_bits))!=len(q.candidate_bits): return ('DUPLICATE_BIT_WIDTH',Escalation.DUPLICATE_BIT_WIDTH)
    if any((not isinstance(b,int)) or b<2 or b>16 for b in q.candidate_bits): return ('INVALID_BIT_WIDTH',Escalation.INVALID_BIT_WIDTH)
    if not _finite(q.weighted_error_threshold) or q.weighted_error_threshold<0: return ('INVALID_WEIGHTED_ERROR_THRESHOLD',Escalation.INVALID_CONFIGURATION)
    if not _finite(q.critical_max_error_threshold) or q.critical_max_error_threshold<0: return ('INVALID_CRITICAL_ERROR_THRESHOLD',Escalation.INVALID_CONFIGURATION)
    return None

def _importance_weights(q):
    out=[]
    for imp,crit in zip(q.importance,q.critical):
        if imp is None: out.append(1.0 if crit else 0.5)
        else: out.append(float(imp))
    return tuple(out)

def _trial(values, weights, critical, bit):
    lo=min(values); hi=max(values); levels=(1<<bit)-1
    if hi==lo:
        reconstructed=tuple(float(lo) for _ in values); scale=0.0
    else:
        scale=(hi-lo)/levels
        reconstructed=tuple(lo+round((v-lo)/scale)*scale for v in values)
    errors=tuple(abs(a-b) for a,b in zip(values,reconstructed))
    denom=sum(weights)
    weighted=(sum(e*w for e,w in zip(errors,weights))/denom) if denom>0 else (sum(errors)/len(errors))
    maxerr=max(errors) if errors else 0.0
    crit=[e for e,c in zip(errors,critical) if c]
    critmax=max(crit) if crit else 0.0
    return scale,weighted,maxerr,critmax,_fp(reconstructed)

def evaluate(q):
    bad=_validate(q)
    if bad: return _invalid(q,bad[0],bad[1],Decision.DENY if bad[1] in {Escalation.DUPLICATE_BIT_WIDTH,Escalation.INVALID_BIT_WIDTH} else Decision.HOLD)
    weights=_importance_weights(q); evals=[]
    for bit in sorted(q.candidate_bits):
        scale,we,me,ce,rfp=_trial(q.values,weights,q.critical,bit)
        wp=we<=q.weighted_error_threshold; cp=ce<=q.critical_max_error_threshold
        evals.append(CandidateEvaluation(bit,scale,we,me,ce,wp,cp,wp and cp,rfp))
    accepted=[x for x in evals if x.accepted]
    if not accepted:
        reasons=('ALL_CANDIDATE_BIT_WIDTHS_REJECTED','WEIGHTED_AND_CRITICAL_ERROR_GUARDS_ENFORCED','LOSSLESS_ORIGINAL_RETENTION_CANDIDATE_ONLY','NO_QUANTIZATION_COMMIT_OR_SOURCE_MUTATION','DCSR_CANDIDATE_STATE_IS_NOT_AUTHORITATIVE_STATE')
        return QuantizationGuardResult(Decision.HOLD,NextAction.RETAIN_LOSSLESS_ORIGINAL_CANDIDATE,Escalation.ALL_CANDIDATES_REJECTED,EngineState.LOSSLESS_RETENTION_CANDIDATE,q.request_id,None,0.0,0.0,tuple(evals),0,len(evals),True,False,True,True,False,reasons)
    sel=accepted[0]
    lightest=sel.bit_width==min(x.bit_width for x in accepted)
    reasons=('CANDIDATE_BITS_TESTED_ASCENDING','IMPORTANCE_WEIGHTED_ERROR_WITHIN_THRESHOLD','CRITICAL_MAX_ERROR_WITHIN_THRESHOLD','LIGHTEST_ACCEPTABLE_BIT_SELECTED','QUANTIZATION_RESULT_IS_CANDIDATE_NOT_COMMIT','LOSSLESS_ORIGINAL_RETENTION_REMAINS_FALLBACK_CANDIDATE','NO_PERMISSION_WRITE_DEPLOYMENT_OR_ACTION_EXECUTION')
    return QuantizationGuardResult(Decision.ALLOW,NextAction.CONTINUE_QUANTIZATION_CANDIDATE,Escalation.NONE,EngineState.QUANTIZATION_CANDIDATE,q.request_id,sel.bit_width,sel.weighted_error,sel.critical_max_error,tuple(evals),len(accepted),len(evals)-len(accepted),True,lightest,sel.critical_error_pass,True,True,reasons)

def default_request():
    vals=tuple((math.sin(i*0.071)*0.63)+(math.cos(i*0.017)*0.24)+(i%7)*0.003 for i in range(512))
    imp=[]; crit=[]
    critical_ids={0,127,255,511}
    for i in range(512):
        crit.append(i in critical_ids)
        imp.append(None if i==255 else ((i*37)%101)/100.0)
    return QuantizationGuardRequest('AQG-167-A',vals,tuple(imp),tuple(crit),(4,6,8,10,12),0.0018,0.0048,'DEFAULT-BINDING','EPOCH-1')
def default_evaluation(): return evaluate(default_request())

def _values_fp(q): return _fp((q.values,q.importance,q.critical))
def _config_fp(q): return _fp((q.candidate_bits,q.weighted_error_threshold,q.critical_max_error_threshold,q.binding,q.state_epoch))
def prepare_state(q,binding,state_epoch):
    if q.binding!=binding or q.state_epoch!=state_epoch:
        r=_invalid(q,'PREPARED_BINDING_MISMATCH',Escalation.INVALID_CONFIGURATION); return PreparedQuantizationState(q,r,'0'*64,'0'*64,'0'*64,'0'*64,binding,state_epoch)
    r=evaluate(q); vf=_values_fp(q); cf=_config_fp(q); rf=_fp(r); integ=_fp((vf,cf,rf,binding,state_epoch))
    return PreparedQuantizationState(q,r,vf,cf,rf,integ,binding,state_epoch)
def evaluate_prepared(st,*,integrity_validated,current_values_fingerprint,current_config_fingerprint,current_result_fingerprint):
    q=st.request
    if not integrity_validated: return _invalid(q,'PREPARED_INTEGRITY_NOT_VALIDATED',Escalation.INVALID_CONFIGURATION)
    if current_values_fingerprint!=st.values_fingerprint: return _invalid(q,'PREPARED_VALUES_FINGERPRINT_MISMATCH',Escalation.INVALID_CONFIGURATION)
    if current_config_fingerprint!=st.config_fingerprint: return _invalid(q,'PREPARED_CONFIG_FINGERPRINT_MISMATCH',Escalation.INVALID_CONFIGURATION)
    if current_result_fingerprint!=st.result_fingerprint: return _invalid(q,'PREPARED_RESULT_FINGERPRINT_MISMATCH',Escalation.INVALID_CONFIGURATION)
    if _fp((st.values_fingerprint,st.config_fingerprint,st.result_fingerprint,st.binding,st.state_epoch))!=st.integrity_fingerprint: return _invalid(q,'PREPARED_INTEGRITY_FINGERPRINT_MISMATCH',Escalation.INVALID_CONFIGURATION)
    return st.result
def make_delta(a,b):
    av=a.request.values; bv=b.request.values; n=max(len(av),len(bv))
    changed=tuple(i for i in range(n) if (av[i] if i<len(av) else None)!=(bv[i] if i<len(bv) else None))
    af=_fp((a.values_fingerprint,a.config_fingerprint)); bf=_fp((b.values_fingerprint,b.config_fingerprint))
    return QuantizationDelta(changed,a.config_fingerprint!=b.config_fingerprint,af,bf)
def plan_missing_only(a,b):
    d=make_delta(a,b); ids=[f'VALUE-{i:04d}' for i in d.changed_value_indices]
    if d.config_changed: ids.append('QUANTIZATION_GUARD_CONFIG')
    return MissingOnlyPlan(tuple(ids),112+len(ids)*16,False)
