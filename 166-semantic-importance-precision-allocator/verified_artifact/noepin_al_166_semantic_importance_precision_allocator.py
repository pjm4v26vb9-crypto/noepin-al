"""NOEPIN AL 166 — Semantic-Importance Precision Allocator — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-166
DCSR: DIRECT INTEGRATION / 直接統合.

Deterministic, side-effect-free mixed-precision allocation evaluator. Critical elements never fall
below the configured critical floor, and a Critical element with unknown semantic importance or
error sensitivity is conservatively fixed to max bit. Budget pressure is applied to non-Critical
elements first. If the mandatory protected precision cannot fit the budget, the result is HOLD with
Original-retention as a candidate only. No quantization, source mutation, permission grant,
deployment, external write, state promotion, or action execution is performed.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str, Enum): ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class EngineState(str, Enum):
    PRECISION_ALLOCATION_CANDIDATE='PRECISION_ALLOCATION_CANDIDATE'
    ORIGINAL_RETENTION_CANDIDATE='ORIGINAL_RETENTION_CANDIDATE'
    INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_PRECISION_ALLOCATION_CANDIDATE='CONTINUE_PRECISION_ALLOCATION_CANDIDATE'
    RETAIN_ORIGINAL_CANDIDATE='RETAIN_ORIGINAL_CANDIDATE'
    REVIEW_INPUT_CANDIDATE='REVIEW_INPUT_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'; DUPLICATE_ELEMENT_ID='DUPLICATE_ELEMENT_ID'
    NONFINITE_INPUT='NONFINITE_INPUT'; BUDGET_BELOW_MANDATORY_PRECISION='BUDGET_BELOW_MANDATORY_PRECISION'
    INVALID_IMPORTANCE='INVALID_IMPORTANCE'; INVALID_SENSITIVITY='INVALID_SENSITIVITY'; EMPTY_ELEMENTS='EMPTY_ELEMENTS'

@dataclass(frozen=True)
class ElementSpec:
    element_id:str; importance:float|None; error_sensitivity:float|None; critical:bool=False
@dataclass(frozen=True)
class PrecisionAllocationRequest:
    request_id:str; elements:tuple[ElementSpec,...]; min_bit:int; max_bit:int; critical_floor_bit:int
    total_bit_budget:int; binding:str; state_epoch:str
@dataclass(frozen=True)
class AllocationRecord:
    element_id:str; bit_width:int; dcsr_priority:str; critical:bool; importance_used:float
    sensitivity_used:float; unknown_critical:bool; adjusted_for_budget:bool; protection_reason:str
@dataclass(frozen=True)
class PrecisionAllocationResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState; request_id:str
    allocations:tuple[AllocationRecord,...]; estimated_total_bits:int; estimated_total_bytes:int; budget_remaining_bits:int
    critical_count:int; unknown_critical_count:int; budget_adjustment_count:int; budget_feasible:bool
    critical_floor_preserved:bool; unknown_critical_max_preserved:bool; original_retention_candidate:bool
    next_gate_candidate:bool; reasons:tuple[str,...]
    element_specs_mutated:bool=False; bit_allocation_committed:bool=False; quantization_executed:bool=False
    source_values_mutated:bool=False; precision_profile_written:bool=False; authoritative_state_created:bool=False
    cached_state_promoted:bool=False; reconstructed_state_promoted:bool=False; partial_state_promoted:bool=False
    tool_invoked:bool=False; file_write_executed:bool=False; network_send_executed:bool=False
    dcsr_reconstruction_created_fact:bool=False; sender_authority_inherited:bool=False; sender_intent_inherited:bool=False
    sender_agreement_inherited:bool=False; permission_granted:bool=False; approval_executed:bool=False
    authority_granted:bool=False; stop_executed:bool=False; action_executed:bool=False; plan_committed:bool=False
    publish_executed:bool=False; external_write_performed:bool=False; world_truth_proven:bool=False
    domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedPrecisionState:
    request:PrecisionAllocationRequest; result:PrecisionAllocationResult; elements_fingerprint:str
    config_fingerprint:str; result_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class PrecisionDelta:
    changed_element_ids:tuple[str,...]; config_changed:bool; from_fingerprint:str; to_fingerprint:str
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
def _finite01(v): return v is None or (isinstance(v,(int,float)) and math.isfinite(float(v)) and 0.0<=float(v)<=1.0)
def _priority(critical,score):
    if critical: return 'P0'
    if score>=0.75: return 'P1'
    if score>=0.40: return 'P2'
    return 'P3'

def _empty_result(q,reason,esc=Escalation.INVALID_CONFIGURATION,decision=Decision.HOLD):
    return PrecisionAllocationResult(decision,NextAction.REVIEW_INPUT_CANDIDATE,esc,EngineState.INVALID,getattr(q,'request_id',''),(),0,0,0,0,0,0,False,False,False,True,False,(reason,'NO_PRECISION_COMMIT_OR_QUANTIZATION_EXECUTION','ORIGINAL_RETENTION_REMAINS_CANDIDATE','DCSR_STATE_IS_NOT_AUTHORITATIVE_STATE'))

def _validate(q):
    if not q.request_id or not q.binding or not q.state_epoch: return ('EMPTY_REQUEST_CONTEXT',Escalation.INVALID_CONFIGURATION)
    if not q.elements: return ('EMPTY_ELEMENTS',Escalation.EMPTY_ELEMENTS)
    if not isinstance(q.min_bit,int) or not isinstance(q.max_bit,int) or not isinstance(q.critical_floor_bit,int): return ('INVALID_BIT_CONFIGURATION',Escalation.INVALID_CONFIGURATION)
    if q.min_bit<2 or q.max_bit>16 or q.min_bit>q.max_bit or not (q.min_bit<=q.critical_floor_bit<=q.max_bit): return ('INVALID_BIT_CONFIGURATION',Escalation.INVALID_CONFIGURATION)
    if not isinstance(q.total_bit_budget,int) or q.total_bit_budget<=0: return ('INVALID_BIT_BUDGET',Escalation.INVALID_CONFIGURATION)
    ids=[e.element_id for e in q.elements]
    if any(not x for x in ids): return ('EMPTY_ELEMENT_ID',Escalation.INVALID_CONFIGURATION)
    if len(set(ids))!=len(ids): return ('DUPLICATE_ELEMENT_ID',Escalation.DUPLICATE_ELEMENT_ID)
    for e in q.elements:
        if not _finite01(e.importance): return ('INVALID_IMPORTANCE',Escalation.INVALID_IMPORTANCE if e.importance is not None and math.isfinite(float(e.importance)) else Escalation.NONFINITE_INPUT)
        if not _finite01(e.error_sensitivity): return ('INVALID_SENSITIVITY',Escalation.INVALID_SENSITIVITY if e.error_sensitivity is not None and math.isfinite(float(e.error_sensitivity)) else Escalation.NONFINITE_INPUT)
    return None

def _normalized(e):
    unknown_critical=e.critical and (e.importance is None or e.error_sensitivity is None)
    if unknown_critical: return 1.0,1.0,True
    if e.importance is None and e.error_sensitivity is None: return 0.5,0.5,False
    if e.importance is None: return float(e.error_sensitivity),float(e.error_sensitivity),False
    if e.error_sensitivity is None: return float(e.importance),float(e.importance),False
    return float(e.importance),float(e.error_sensitivity),False

def evaluate(q):
    bad=_validate(q)
    if bad: return _empty_result(q,bad[0],bad[1],Decision.DENY if bad[1]==Escalation.DUPLICATE_ELEMENT_ID else Decision.HOLD)
    work=[]
    for e in q.elements:
        imp,sens,unk=_normalized(e); score=0.65*imp+0.35*sens
        if unk: bit=q.max_bit; reason='CRITICAL_IMPORTANCE_OR_SENSITIVITY_UNKNOWN_MAX_BIT_FIXED'
        else:
            bit=q.min_bit+int(round(score*(q.max_bit-q.min_bit)))
            bit=max(q.min_bit,min(q.max_bit,bit))
            if e.critical and bit<q.critical_floor_bit: bit=q.critical_floor_bit
            reason='CRITICAL_FLOOR_PROTECTED' if e.critical else ('LOW_IMPORTANCE_COARSE_PRECISION_CANDIDATE' if score<0.35 else 'SEMANTIC_IMPORTANCE_MAPPED_PRECISION_CANDIDATE')
        work.append({'e':e,'imp':imp,'sens':sens,'score':score,'unk':unk,'bit':bit,'original_bit':bit,'reason':reason})
    mandatory=sum((q.max_bit if x['unk'] else q.critical_floor_bit) if x['e'].critical else q.min_bit for x in work)
    if q.total_bit_budget<mandatory:
        reasons=('BUDGET_BELOW_MANDATORY_PROTECTED_PRECISION','CRITICAL_PRECISION_NOT_DEGRADED_TO_FIT_BUDGET','ORIGINAL_RETENTION_CANDIDATE_ONLY','NO_PRECISION_COMMIT_OR_QUANTIZATION_EXECUTION')
        return PrecisionAllocationResult(Decision.HOLD,NextAction.RETAIN_ORIGINAL_CANDIDATE,Escalation.BUDGET_BELOW_MANDATORY_PRECISION,EngineState.ORIGINAL_RETENTION_CANDIDATE,q.request_id,(),mandatory,(mandatory+7)//8,q.total_bit_budget-mandatory,sum(x['e'].critical for x in work),sum(x['unk'] for x in work),0,False,True,True,True,False,reasons)
    total=sum(x['bit'] for x in work)
    adjusted=0
    # Budget pressure applies to non-Critical elements first, lowest semantic score first.
    for x in sorted((z for z in work if not z['e'].critical),key=lambda z:(z['score'],z['e'].element_id)):
        while total>q.total_bit_budget and x['bit']>q.min_bit:
            x['bit']-=1; total-=1; adjusted+=1
    # Only after all non-Critical reductions are exhausted may known Critical values fall to their floor.
    for x in sorted((z for z in work if z['e'].critical and not z['unk']),key=lambda z:(z['score'],z['e'].element_id)):
        while total>q.total_bit_budget and x['bit']>q.critical_floor_bit:
            x['bit']-=1; total-=1; adjusted+=1
    if total>q.total_bit_budget:
        reasons=('BUDGET_REMAINS_INFEASIBLE_AFTER_NONCRITICAL_ADJUSTMENT','CRITICAL_FLOOR_AND_UNKNOWN_CRITICAL_MAX_PRESERVED','ORIGINAL_RETENTION_CANDIDATE_ONLY','NO_PRECISION_COMMIT_OR_QUANTIZATION_EXECUTION')
        return PrecisionAllocationResult(Decision.HOLD,NextAction.RETAIN_ORIGINAL_CANDIDATE,Escalation.BUDGET_BELOW_MANDATORY_PRECISION,EngineState.ORIGINAL_RETENTION_CANDIDATE,q.request_id,(),total,(total+7)//8,q.total_bit_budget-total,sum(x['e'].critical for x in work),sum(x['unk'] for x in work),adjusted,False,True,True,True,False,reasons)
    alloc=tuple(AllocationRecord(x['e'].element_id,x['bit'],_priority(x['e'].critical,x['score']),x['e'].critical,x['imp'],x['sens'],x['unk'],x['bit']!=x['original_bit'],x['reason']) for x in sorted(work,key=lambda z:z['e'].element_id))
    floor_ok=all((not a.critical) or a.bit_width>=q.critical_floor_bit for a in alloc)
    unk_ok=all((not a.unknown_critical) or a.bit_width==q.max_bit for a in alloc)
    reasons=('SEMANTIC_IMPORTANCE_AND_ERROR_SENSITIVITY_MAPPED','CRITICAL_FLOOR_PRESERVED','UNKNOWN_CRITICAL_MAX_BIT_PRESERVED','BUDGET_ADJUSTMENT_NONCRITICAL_FIRST','DCSR_CRITICAL_STATE_PRIORITY_P0','PRECISION_ALLOCATION_IS_CANDIDATE_NOT_COMMIT','ORIGINAL_RETENTION_REMAINS_FALLBACK_CANDIDATE','NO_PERMISSION_WRITE_DEPLOYMENT_OR_ACTION_EXECUTION')
    return PrecisionAllocationResult(Decision.ALLOW,NextAction.CONTINUE_PRECISION_ALLOCATION_CANDIDATE,Escalation.NONE,EngineState.PRECISION_ALLOCATION_CANDIDATE,q.request_id,alloc,total,(total+7)//8,q.total_bit_budget-total,sum(a.critical for a in alloc),sum(a.unknown_critical for a in alloc),adjusted,True,floor_ok,unk_ok,True,True,reasons)

def default_request():
    els=[]
    crit={0,127,255,511}
    for i in range(512):
        imp=((i*37)%101)/100.0; sens=((i*53+11)%101)/100.0
        if i==255: imp=None
        els.append(ElementSpec(f'EL-{i:04d}',imp,sens,i in crit))
    return PrecisionAllocationRequest('SIPA-166-A',tuple(els),4,12,10,3600,'DEFAULT-BINDING','EPOCH-1')
def default_evaluation(): return evaluate(default_request())

def _elements_fp(q): return _fp(q.elements)
def _config_fp(q): return _fp((q.min_bit,q.max_bit,q.critical_floor_bit,q.total_bit_budget,q.binding,q.state_epoch))
def prepare_state(q,binding,state_epoch):
    if q.binding!=binding or q.state_epoch!=state_epoch:
        r=_empty_result(q,'PREPARED_BINDING_MISMATCH'); return PreparedPrecisionState(q,r,'0'*64,'0'*64,'0'*64,'0'*64,binding,state_epoch)
    r=evaluate(q); ef=_elements_fp(q); cf=_config_fp(q); rf=_fp(r); integ=_fp((ef,cf,rf,binding,state_epoch))
    return PreparedPrecisionState(q,r,ef,cf,rf,integ,binding,state_epoch)
def evaluate_prepared(st,*,integrity_validated,current_elements_fingerprint,current_config_fingerprint,current_result_fingerprint):
    q=st.request
    if not integrity_validated: return _empty_result(q,'PREPARED_INTEGRITY_NOT_VALIDATED')
    if current_elements_fingerprint!=st.elements_fingerprint: return _empty_result(q,'PREPARED_ELEMENTS_FINGERPRINT_MISMATCH')
    if current_config_fingerprint!=st.config_fingerprint: return _empty_result(q,'PREPARED_CONFIG_FINGERPRINT_MISMATCH')
    if current_result_fingerprint!=st.result_fingerprint: return _empty_result(q,'PREPARED_RESULT_FINGERPRINT_MISMATCH')
    if _fp((st.elements_fingerprint,st.config_fingerprint,st.result_fingerprint,st.binding,st.state_epoch))!=st.integrity_fingerprint: return _empty_result(q,'PREPARED_INTEGRITY_FINGERPRINT_MISMATCH')
    return st.result
def make_delta(a,b):
    amap={e.element_id:_fp(e) for e in a.request.elements}; bmap={e.element_id:_fp(e) for e in b.request.elements}
    changed=tuple(sorted(k for k in set(amap)|set(bmap) if amap.get(k)!=bmap.get(k)))
    af=_fp((a.elements_fingerprint,a.config_fingerprint)); bf=_fp((b.elements_fingerprint,b.config_fingerprint))
    return PrecisionDelta(changed,a.config_fingerprint!=b.config_fingerprint,af,bf)
def plan_missing_only(a,b):
    d=make_delta(a,b); ids=list(d.changed_element_ids)
    if d.config_changed: ids.append('PRECISION_CONFIG')
    return MissingOnlyPlan(tuple(ids),108+len(ids)*14,False)
