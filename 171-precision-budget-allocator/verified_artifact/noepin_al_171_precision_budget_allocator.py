"""NOEPIN AL 171 — Precision Budget Allocator — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-171
DCSR: DIRECT INTEGRATION / 直接統合.

Deterministic, side-effect-free precision budget allocation evaluator.
It first reserves each Component's minimum precision (including explicit Critical floors),
then distributes the remaining effective bit budget according to Importance x Sensitivity,
rounds allocations to whole per-element bit widths, rechecks the total budget, and spends
rounding surplus in deterministic high-importance order. If mandatory floors alone exceed
available bit/byte budget, the result is HOLD and the Full/Original retention path remains
only a candidate. Outputs are allocation candidates only: no quantization, mutation,
transfer, deployment, permission grant, authoritative-state promotion, or Action Success.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str, Enum): ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class EngineState(str, Enum):
    PRECISION_BUDGET_CANDIDATE='PRECISION_BUDGET_CANDIDATE'
    FULL_ORIGINAL_RETENTION_CANDIDATE='FULL_ORIGINAL_RETENTION_CANDIDATE'
    INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_PRECISION_ALLOCATION_CANDIDATE='CONTINUE_PRECISION_ALLOCATION_CANDIDATE'
    RETAIN_FULL_ORIGINAL_CANDIDATE='RETAIN_FULL_ORIGINAL_CANDIDATE'
    REVIEW_INPUT_CANDIDATE='REVIEW_INPUT_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'; INVALID_VALUE='INVALID_VALUE'
    COMPONENT_UNAVAILABLE='COMPONENT_UNAVAILABLE'; MINIMUM_BUDGET_INSUFFICIENT='MINIMUM_BUDGET_INSUFFICIENT'

@dataclass(frozen=True)
class PrecisionComponent:
    component_id:str
    element_count:int
    importance:float
    sensitivity:float
    min_bits:int
    max_bits:int
    critical:bool=False
    critical_floor_bits:int=0
    available:bool=True

@dataclass(frozen=True)
class PrecisionBudgetRequest:
    request_id:str
    components:tuple[PrecisionComponent,...]
    total_bit_budget:int
    total_byte_budget:int
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class ComponentAllocation:
    component_id:str
    critical:bool
    element_count:int
    floor_bits:int
    allocated_bits:int
    allocation_total_bits:int
    importance:float
    sensitivity:float
    weight:float
    floor_preserved:bool
    at_max_precision:bool

@dataclass(frozen=True)
class PrecisionBudgetResult:
    decision:Decision
    next_action:NextAction
    escalation:Escalation
    engine_state:EngineState
    request_id:str
    allocations:tuple[ComponentAllocation,...]
    effective_bit_budget:int
    requested_bit_budget:int
    requested_byte_budget:int
    minimum_required_bits:int
    allocated_total_bits:int
    estimated_total_bytes:int
    unused_bits:int
    critical_component_ids:tuple[str,...]
    critical_floor_preserved_ids:tuple[str,...]
    all_minimum_floors_preserved:bool
    all_critical_floors_preserved:bool
    budget_feasible:bool
    next_gate_candidate:bool
    reasons:tuple[str,...]
    source_components_mutated:bool=False
    quantization_executed:bool=False
    allocation_committed:bool=False
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
class PreparedPrecisionBudgetState:
    request:PrecisionBudgetRequest
    result:PrecisionBudgetResult
    components_fingerprint:str
    config_fingerprint:str
    result_fingerprint:str
    integrity_fingerprint:str
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class PrecisionBudgetChange:
    components_changed:bool
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
def _floor_bits(c): return max(int(c.min_bits), int(c.critical_floor_bits) if c.critical else int(c.min_bits))
def _weight(c): return float(c.importance)*float(c.sensitivity)

def _invalid(q,reason,esc,decision=Decision.HOLD):
    return PrecisionBudgetResult(decision,NextAction.REVIEW_INPUT_CANDIDATE,esc,EngineState.INVALID,getattr(q,'request_id',''),(),0,getattr(q,'total_bit_budget',0),getattr(q,'total_byte_budget',0),0,0,0,0,(),(),False,False,False,False,(reason,'NO_AUTHORITATIVE_STATE_PROMOTION','FULL_ORIGINAL_RETENTION_REMAINS_CANDIDATE','DCSR_STATE_IS_NOT_AUTHORITATIVE_STATE'))

def _validate(q):
    if not q.request_id or not q.binding or not q.state_epoch: return ('EMPTY_REQUEST_CONTEXT',Escalation.INVALID_CONFIGURATION)
    if not isinstance(q.total_bit_budget,int) or isinstance(q.total_bit_budget,bool) or q.total_bit_budget<0: return ('INVALID_BIT_BUDGET',Escalation.INVALID_CONFIGURATION)
    if not isinstance(q.total_byte_budget,int) or isinstance(q.total_byte_budget,bool) or q.total_byte_budget<0: return ('INVALID_BYTE_BUDGET',Escalation.INVALID_CONFIGURATION)
    if not q.components: return ('EMPTY_COMPONENT_SET',Escalation.INVALID_CONFIGURATION)
    ids=[c.component_id for c in q.components]
    if any(not x for x in ids) or len(ids)!=len(set(ids)): return ('INVALID_OR_DUPLICATE_COMPONENT_ID',Escalation.INVALID_CONFIGURATION)
    for c in q.components:
        if not isinstance(c.element_count,int) or isinstance(c.element_count,bool) or c.element_count<=0: return ('INVALID_ELEMENT_COUNT',Escalation.INVALID_CONFIGURATION)
        if not _valid_number(c.importance) or not 0.0<=float(c.importance)<=1.0: return ('INVALID_IMPORTANCE',Escalation.INVALID_VALUE)
        if not _valid_number(c.sensitivity) or not 0.0<=float(c.sensitivity)<=1.0: return ('INVALID_SENSITIVITY',Escalation.INVALID_VALUE)
        if not isinstance(c.min_bits,int) or isinstance(c.min_bits,bool) or not 1<=c.min_bits<=32: return ('INVALID_MIN_BITS',Escalation.INVALID_CONFIGURATION)
        if not isinstance(c.max_bits,int) or isinstance(c.max_bits,bool) or not c.min_bits<=c.max_bits<=32: return ('INVALID_MAX_BITS',Escalation.INVALID_CONFIGURATION)
        if not isinstance(c.critical_floor_bits,int) or isinstance(c.critical_floor_bits,bool) or c.critical_floor_bits<0 or c.critical_floor_bits>32: return ('INVALID_CRITICAL_FLOOR',Escalation.INVALID_CONFIGURATION)
        if c.critical and c.critical_floor_bits and c.critical_floor_bits>c.max_bits: return ('CRITICAL_FLOOR_EXCEEDS_MAX_BITS',Escalation.INVALID_CONFIGURATION)
    return None

def _hold(q,esc,reason,minimum_required_bits=0,effective_budget=0):
    critical=tuple(c.component_id for c in q.components if c.critical)
    return PrecisionBudgetResult(Decision.HOLD,NextAction.RETAIN_FULL_ORIGINAL_CANDIDATE,esc,EngineState.FULL_ORIGINAL_RETENTION_CANDIDATE,q.request_id,(),int(effective_budget),q.total_bit_budget,q.total_byte_budget,int(minimum_required_bits),0,0,max(0,int(effective_budget)),critical,(),False,False,False,False,(reason,'MINIMUM_PRECISION_NOT_RELAXED','FULL_ORIGINAL_RETENTION_CANDIDATE','NO_QUANTIZATION_COMMIT_DEPLOYMENT_OR_ACTION_EXECUTION'))

def evaluate(q):
    bad=_validate(q)
    if bad:
        return _invalid(q,bad[0],bad[1],Decision.DENY if bad[1]==Escalation.INVALID_VALUE else Decision.HOLD)
    unavailable=tuple(c.component_id for c in q.components if not c.available)
    if unavailable:
        return _hold(q,Escalation.COMPONENT_UNAVAILABLE,'REQUIRED_COMPONENT_EVIDENCE_UNAVAILABLE')
    effective=min(q.total_bit_budget,q.total_byte_budget*8)
    floors={c.component_id:_floor_bits(c) for c in q.components}
    minimum=sum(c.element_count*floors[c.component_id] for c in q.components)
    if minimum>effective:
        return _hold(q,Escalation.MINIMUM_BUDGET_INSUFFICIENT,'MINIMUM_PRECISION_SUM_EXCEEDS_EFFECTIVE_BUDGET',minimum,effective)
    alloc={c.component_id:floors[c.component_id] for c in q.components}
    remaining=effective-minimum
    weighted=[c for c in q.components if c.max_bits>alloc[c.component_id] and _weight(c)>0.0]
    total_weight=sum(_weight(c) for c in weighted)
    # First pass: proportional Importance x Sensitivity share rounded down to whole bit-width steps.
    if remaining>0 and total_weight>0:
        for c in sorted(weighted,key=lambda x:(not x.critical,-_weight(x),-x.importance,-x.sensitivity,x.component_id)):
            capacity_steps=c.max_bits-alloc[c.component_id]
            share=remaining*(_weight(c)/total_weight)
            steps=min(capacity_steps,int(share//c.element_count))
            if steps>0:
                alloc[c.component_id]+=steps
    used=sum(c.element_count*alloc[c.component_id] for c in q.components)
    surplus=effective-used
    # Second pass: deterministic high-importance redistribution of rounding surplus.
    while True:
        eligible=[c for c in q.components if alloc[c.component_id]<c.max_bits and c.element_count<=surplus]
        if not eligible: break
        c=sorted(eligible,key=lambda x:(not x.critical,-_weight(x),-x.importance,-x.sensitivity,x.element_count,x.component_id))[0]
        alloc[c.component_id]+=1; surplus-=c.element_count
    allocations=[]
    critical_ids=[]; critical_preserved=[]
    for c in q.components:
        floor=floors[c.component_id]; bits=alloc[c.component_id]
        preserved=bits>=floor
        if c.critical:
            critical_ids.append(c.component_id)
            if preserved: critical_preserved.append(c.component_id)
        allocations.append(ComponentAllocation(c.component_id,c.critical,c.element_count,floor,bits,c.element_count*bits,round(float(c.importance),12),round(float(c.sensitivity),12),round(_weight(c),12),preserved,bits==c.max_bits))
    allocations=tuple(sorted(allocations,key=lambda a:a.component_id))
    total=sum(a.allocation_total_bits for a in allocations)
    all_min=all(a.floor_preserved for a in allocations)
    all_crit=set(critical_ids)==set(critical_preserved)
    if total>effective or not all_min or not all_crit:
        return _hold(q,Escalation.MINIMUM_BUDGET_INSUFFICIENT,'POST_ALLOCATION_BUDGET_OR_FLOOR_CHECK_FAILED',minimum,effective)
    reasons=('MINIMUM_PRECISION_RESERVED_FIRST','CRITICAL_FLOORS_PRESERVED','REMAINING_BUDGET_WEIGHTED_BY_IMPORTANCE_X_SENSITIVITY','BIT_WIDTHS_ROUNDED_TO_WHOLE_STEPS','SURPLUS_REDISTRIBUTED_HIGH_IMPORTANCE_FIRST','ALLOCATION_IS_CANDIDATE_NOT_QUANTIZATION_EXECUTION','NO_AUTHORITATIVE_STATE_PROMOTION','NO_PERMISSION_DEPLOYMENT_OR_ACTION_EXECUTION')
    return PrecisionBudgetResult(Decision.ALLOW,NextAction.CONTINUE_PRECISION_ALLOCATION_CANDIDATE,Escalation.NONE,EngineState.PRECISION_BUDGET_CANDIDATE,q.request_id,allocations,effective,q.total_bit_budget,q.total_byte_budget,minimum,total,(total+7)//8,effective-total,tuple(critical_ids),tuple(critical_preserved),all_min,all_crit,True,True,reasons)

def default_request():
    cs=(
        PrecisionComponent('CRIT-A',96,1.00,1.00,8,14,True,10,True),
        PrecisionComponent('CRIT-B',80,0.98,0.95,7,14,True,9,True),
        PrecisionComponent('CRIT-C',64,0.94,0.92,7,13,True,9,True),
        PrecisionComponent('HIGH-A',128,0.90,0.88,6,12,False,0,True),
        PrecisionComponent('HIGH-B',112,0.84,0.82,6,12,False,0,True),
        PrecisionComponent('HIGH-C',96,0.78,0.80,5,11,False,0,True),
        PrecisionComponent('MID-A',144,0.66,0.70,5,10,False,0,True),
        PrecisionComponent('MID-B',128,0.60,0.62,5,10,False,0,True),
        PrecisionComponent('MID-C',120,0.52,0.55,4,9,False,0,True),
        PrecisionComponent('LOW-A',160,0.34,0.40,4,8,False,0,True),
        PrecisionComponent('LOW-B',144,0.25,0.32,4,8,False,0,True),
        PrecisionComponent('LOW-C',128,0.18,0.25,3,7,False,0,True),
    )
    return PrecisionBudgetRequest('PBA-171-A',cs,13500,1700,'DEFAULT-BINDING','EPOCH-1')
def default_evaluation(): return evaluate(default_request())

def _components_fp(q): return _fp(q.components)
def _config_fp(q): return _fp((q.total_bit_budget,q.total_byte_budget,q.binding,q.state_epoch))
def prepare_state(q,binding,state_epoch):
    if q.binding!=binding or q.state_epoch!=state_epoch:
        r=_invalid(q,'PREPARED_BINDING_MISMATCH',Escalation.INVALID_CONFIGURATION)
        return PreparedPrecisionBudgetState(q,r,'0'*64,'0'*64,'0'*64,'0'*64,binding,state_epoch)
    r=evaluate(q); cf=_components_fp(q); gf=_config_fp(q); rf=_fp(r); integ=_fp((cf,gf,rf,binding,state_epoch))
    return PreparedPrecisionBudgetState(q,r,cf,gf,rf,integ,binding,state_epoch)
def evaluate_prepared(st,*,integrity_validated,current_components_fingerprint,current_config_fingerprint,current_result_fingerprint):
    q=st.request
    if not integrity_validated: return _invalid(q,'PREPARED_INTEGRITY_NOT_VALIDATED',Escalation.INVALID_CONFIGURATION)
    if current_components_fingerprint!=st.components_fingerprint: return _invalid(q,'PREPARED_COMPONENTS_FINGERPRINT_MISMATCH',Escalation.INVALID_CONFIGURATION)
    if current_config_fingerprint!=st.config_fingerprint: return _invalid(q,'PREPARED_CONFIG_FINGERPRINT_MISMATCH',Escalation.INVALID_CONFIGURATION)
    if current_result_fingerprint!=st.result_fingerprint: return _invalid(q,'PREPARED_RESULT_FINGERPRINT_MISMATCH',Escalation.INVALID_CONFIGURATION)
    if _fp((st.components_fingerprint,st.config_fingerprint,st.result_fingerprint,st.binding,st.state_epoch))!=st.integrity_fingerprint: return _invalid(q,'PREPARED_INTEGRITY_FINGERPRINT_MISMATCH',Escalation.INVALID_CONFIGURATION)
    return st.result

def make_delta(a,b):
    return PrecisionBudgetChange(a.components_fingerprint!=b.components_fingerprint,a.config_fingerprint!=b.config_fingerprint,_fp((a.components_fingerprint,a.config_fingerprint)),_fp((b.components_fingerprint,b.config_fingerprint)))
def plan_missing_only(a,b):
    d=make_delta(a,b); ids=[]
    if d.components_changed: ids.append('PRECISION_COMPONENTS')
    if d.config_changed: ids.append('PRECISION_BUDGET_CONFIG')
    return MissingOnlyPlan(tuple(ids),108+len(ids)*18,False)
