"""NOEPIN AL 086 — Compensation Action Planner — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Pure compensation-planning control algorithm. It evaluates typed Forward Actions,
Effect Model, and Available Compensation evidence and emits a deterministic
compensation-plan candidate. It does not execute Forward/Compensation actions,
grant permission, commit/publish state, prove World Truth/Safety, or assert
Action Success.

Canonical identity: NOEPIN-AL-086
Provenance note: exact registered Origin GUID was not freshly reverified in this
completion session and is intentionally not guessed or regenerated.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json

class Decision(str, Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class Risk(str, Enum):
    LOW='LOW'; MEDIUM='MEDIUM'; HIGH='HIGH'; CRITICAL='CRITICAL'; UNKNOWN='UNKNOWN'
class CompensationStatus(str, Enum):
    READY='READY'; FAILED='FAILED'; UNOBSERVED='UNOBSERVED'
class ApprovalState(str, Enum):
    NOT_REQUIRED='NOT_REQUIRED'; REQUIRED='REQUIRED'

RISK_RANK={Risk.LOW:0,Risk.MEDIUM:1,Risk.HIGH:2,Risk.CRITICAL:3,Risk.UNKNOWN:4}
SEVERITY_WEIGHT={Risk.LOW:1.0,Risk.MEDIUM:2.0,Risk.HIGH:4.0,Risk.CRITICAL:8.0,Risk.UNKNOWN:8.0}

@dataclass(frozen=True)
class PlanningRequest:
    request_id:str; plan_id:str; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class IntentEvidence:
    intent_id:str; plan_id:str; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class PermitEvidence:
    permit_id:str; plan_id:str; observed:bool; allow_candidate:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class ForwardAction:
    action_id:str; order:int; risk:Risk; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class EffectRecord:
    effect_id:str; action_id:str; severity:Risk; weight:float; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class CompensationCandidate:
    compensation_id:str; effect_id:str; coverage:float; risk:Risk; status:CompensationStatus; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class CompensationPolicy:
    min_coverage:float; max_residual_risk:float; max_compensation_risk:Risk; require_permit_evidence:bool; binding:str; state_epoch:str; revoked:bool=False
@dataclass(frozen=True)
class CompensationStep:
    compensation_id:str; effect_id:str; action_id:str; reverse_action_order:int; coverage:float; compensation_risk:Risk
@dataclass(frozen=True)
class CompensationResult:
    decision:Decision
    reasons:tuple[str,...]
    compensation_plan:tuple[CompensationStep,...]
    coverage:float
    residual_risk:float
    uncovered_effect_ids:tuple[str,...]
    critical_uncovered_effect_ids:tuple[str,...]
    approval_state:ApprovalState
    plan_attached_candidate:bool
    next_gate_candidate:bool
    request_promoted_to_success:bool=False
    intent_promoted_to_action:bool=False
    permission_granted:bool=False
    forward_action_executed:bool=False
    compensation_executed:bool=False
    plan_committed:bool=False
    atomic_publish_executed:bool=False
    external_write_performed:bool=False
    receipt_promoted_to_truth:bool=False
    world_truth_proven:bool=False
    safety_proven:bool=False
    action_success:bool=False

@dataclass(frozen=True)
class PreparedCompensationState:
    request:PlanningRequest; intent:IntentEvidence; permit:PermitEvidence
    actions:tuple[ForwardAction,...]; effects:tuple[EffectRecord,...]; compensations:tuple[CompensationCandidate,...]; policy:CompensationPolicy
    action_fingerprints:tuple[tuple[str,str],...]; effect_fingerprints:tuple[tuple[str,str],...]; compensation_fingerprints:tuple[tuple[str,str],...]
    context_fingerprint:str; dependency_fingerprint:str; registry_fingerprint:str
    precomputed_result:CompensationResult; binding:str; state_epoch:str
@dataclass(frozen=True)
class CompensationStateDelta:
    base_fingerprint:str; target_fingerprint:str
    changed_actions:tuple[ForwardAction,...]; removed_action_ids:tuple[str,...]
    changed_effects:tuple[EffectRecord,...]; removed_effect_ids:tuple[str,...]
    changed_compensations:tuple[CompensationCandidate,...]; removed_compensation_ids:tuple[str,...]
    target_request:PlanningRequest|None; target_intent:IntentEvidence|None; target_permit:PermitEvidence|None; target_policy:CompensationPolicy|None
    binding:str; state_epoch:str
@dataclass(frozen=True)
class CompensationSyncPlan:
    missing_or_changed_action_ids:tuple[str,...]
    missing_or_changed_effect_ids:tuple[str,...]
    missing_or_changed_compensation_ids:tuple[str,...]
    metadata_bytes_required:int
    full_resend_required:bool

def _cv(x):
    if isinstance(x,Enum): return x.value
    if hasattr(x,'__dataclass_fields__'): return {k:_cv(getattr(x,k)) for k in x.__dataclass_fields__}
    if isinstance(x,tuple): return [_cv(v) for v in x]
    if isinstance(x,list): return [_cv(v) for v in x]
    if isinstance(x,dict): return {str(k):_cv(x[k]) for k in sorted(x)}
    return x

def _canon(x)->bytes:
    return json.dumps(_cv(x),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def _fp(x)->str: return sha256(_canon(x)).hexdigest()
def _hold(reason:str, plan=(), coverage=0.0, residual=1.0, uncovered=(), critical=()):
    return CompensationResult(Decision.HOLD,(reason,),tuple(plan),float(coverage),float(residual),tuple(uncovered),tuple(critical),ApprovalState.NOT_REQUIRED,False,False)
def _human(reason:str, plan, coverage, residual, uncovered, critical):
    return CompensationResult(Decision.HUMAN_APPROVAL,(reason,),tuple(plan),coverage,residual,tuple(uncovered),tuple(critical),ApprovalState.REQUIRED,True,False)

def _validate_common(request,intent,permit,actions,effects,compensations,policy):
    if policy.revoked: return 'POLICY_REVOKED'
    if not 0.0 <= policy.min_coverage <= 1.0: return 'INVALID_MIN_COVERAGE'
    if not 0.0 <= policy.max_residual_risk <= 1.0: return 'INVALID_MAX_RESIDUAL_RISK'
    if request.plan_id!=intent.plan_id or request.plan_id!=permit.plan_id: return 'PLAN_ID_MISMATCH'
    objs=(request,intent,permit)
    if any(x.binding!=policy.binding for x in objs): return 'BINDING_MISMATCH'
    if any(x.state_epoch!=policy.state_epoch for x in objs): return 'STATE_EPOCH_MISMATCH'
    if any(x.binding!=policy.binding or x.state_epoch!=policy.state_epoch for x in actions): return 'ACTION_SCOPE_MISMATCH'
    if any(x.binding!=policy.binding or x.state_epoch!=policy.state_epoch for x in effects): return 'EFFECT_SCOPE_MISMATCH'
    if any(x.binding!=policy.binding or x.state_epoch!=policy.state_epoch for x in compensations): return 'COMPENSATION_SCOPE_MISMATCH'
    if len({x.action_id for x in actions})!=len(actions): return 'DUPLICATE_ACTION_ID'
    if len({x.order for x in actions})!=len(actions): return 'DUPLICATE_ACTION_ORDER'
    orders=tuple(sorted(x.order for x in actions))
    if orders and orders!=tuple(range(len(orders))): return 'NONCONTIGUOUS_ACTION_ORDER'
    if len({x.effect_id for x in effects})!=len(effects): return 'DUPLICATE_EFFECT_ID'
    if len({x.compensation_id for x in compensations})!=len(compensations): return 'DUPLICATE_COMPENSATION_ID'
    action_ids={x.action_id for x in actions}; effect_ids={x.effect_id for x in effects}
    if any(x.action_id not in action_ids for x in effects): return 'UNKNOWN_EFFECT_ACTION'
    if any(x.effect_id not in effect_ids for x in compensations): return 'UNKNOWN_COMPENSATION_EFFECT'
    if any((not 0.0 <= x.coverage <= 1.0) for x in compensations): return 'INVALID_COMPENSATION_COVERAGE'
    if any(x.weight<=0 for x in effects): return 'INVALID_EFFECT_WEIGHT'
    return None

def evaluate(request:PlanningRequest,intent:IntentEvidence,permit:PermitEvidence,actions:tuple[ForwardAction,...],effects:tuple[EffectRecord,...],compensations:tuple[CompensationCandidate,...],policy:CompensationPolicy)->CompensationResult:
    err=_validate_common(request,intent,permit,actions,effects,compensations,policy)
    if err: return _hold(err)
    if not request.observed: return _hold('REQUEST_UNOBSERVED')
    if not intent.observed: return _hold('INTENT_UNOBSERVED')
    if policy.require_permit_evidence and not permit.observed: return _hold('PERMIT_EVIDENCE_UNOBSERVED')
    if policy.require_permit_evidence and not permit.allow_candidate: return _hold('PERMIT_CANDIDATE_NOT_ALLOWED')
    if not actions: return _hold('EMPTY_FORWARD_ACTIONS')
    if not effects: return _hold('EMPTY_EFFECT_MODEL')
    if any(not x.observed for x in actions): return _hold('FORWARD_ACTION_UNOBSERVED')
    if any(not x.observed for x in effects): return _hold('EFFECT_MODEL_UNOBSERVED')
    if any(x.risk==Risk.UNKNOWN for x in actions): return _hold('FORWARD_ACTION_RISK_UNKNOWN')
    if any(x.severity==Risk.UNKNOWN for x in effects): return _hold('EFFECT_SEVERITY_UNKNOWN')
    action_by_id={x.action_id:x for x in actions}
    comps_by_effect={}
    for c in compensations: comps_by_effect.setdefault(c.effect_id,[]).append(c)
    plan=[]; uncovered=[]; critical=[]; covered_weight=0.0; total_weight=0.0; residual_numer=0.0; residual_denom=0.0
    high_risk_comp_effects=[]
    for effect in sorted(effects,key=lambda x:(action_by_id[x.action_id].order,x.effect_id)):
        severity_weight=SEVERITY_WEIGHT[effect.severity]*effect.weight
        total_weight += effect.weight
        residual_denom += severity_weight
        usable=[c for c in comps_by_effect.get(effect.effect_id,()) if c.observed and c.status==CompensationStatus.READY]
        usable.sort(key=lambda c:(-c.coverage,RISK_RANK[c.risk],c.compensation_id))
        chosen=usable[0] if usable else None
        coverage=chosen.coverage if chosen else 0.0
        if chosen and RISK_RANK[chosen.risk]>RISK_RANK[policy.max_compensation_risk]:
            high_risk_comp_effects.append(effect.effect_id)
        if chosen and coverage>0:
            plan.append(CompensationStep(chosen.compensation_id,effect.effect_id,effect.action_id,action_by_id[effect.action_id].order,coverage,chosen.risk))
        if coverage<1.0:
            uncovered.append(effect.effect_id)
            if effect.severity==Risk.CRITICAL: critical.append(effect.effect_id)
        covered_weight += effect.weight*coverage
        residual_numer += severity_weight*(1.0-coverage)
    plan=tuple(sorted(plan,key=lambda x:(-x.reverse_action_order,x.effect_id,x.compensation_id)))
    coverage=covered_weight/total_weight if total_weight else 0.0
    residual=residual_numer/residual_denom if residual_denom else 1.0
    if high_risk_comp_effects:
        return _hold('COMPENSATION_RISK_ABOVE_POLICY',plan,coverage,residual,uncovered,critical)
    if critical:
        return _human('CRITICAL_EFFECT_NOT_FULLY_COMPENSABLE',plan,coverage,residual,uncovered,critical)
    if coverage < policy.min_coverage:
        return _hold('COMPENSATION_COVERAGE_INSUFFICIENT',plan,coverage,residual,uncovered,critical)
    if residual > policy.max_residual_risk:
        return _hold('RESIDUAL_RISK_TOO_HIGH',plan,coverage,residual,uncovered,critical)
    return CompensationResult(Decision.ALLOW,('COMPENSATION_PLAN_ACCEPTABLE',),plan,coverage,residual,tuple(uncovered),tuple(critical),ApprovalState.NOT_REQUIRED,True,True)

def default_policy(): return CompensationPolicy(0.80,0.25,Risk.MEDIUM,True,'COMP-BIND','STATE-EPOCH-1')
def default_request(): return PlanningRequest('REQ-1','PLAN-1',True,'COMP-BIND','STATE-EPOCH-1')
def default_intent(): return IntentEvidence('INT-1','PLAN-1',True,'COMP-BIND','STATE-EPOCH-1')
def default_permit(): return PermitEvidence('PERMIT-1','PLAN-1',True,True,'COMP-BIND','STATE-EPOCH-1')
def default_actions():
    b,e='COMP-BIND','STATE-EPOCH-1'
    return (ForwardAction('A1',0,Risk.MEDIUM,True,b,e),ForwardAction('A2',1,Risk.HIGH,True,b,e))
def default_effects():
    b,e='COMP-BIND','STATE-EPOCH-1'
    return (EffectRecord('E1','A1',Risk.MEDIUM,1.0,True,b,e),EffectRecord('E2','A2',Risk.HIGH,2.0,True,b,e))
def default_compensations():
    b,e='COMP-BIND','STATE-EPOCH-1'
    return (CompensationCandidate('C1','E1',1.0,Risk.LOW,CompensationStatus.READY,True,b,e),CompensationCandidate('C2','E2',1.0,Risk.MEDIUM,CompensationStatus.READY,True,b,e))

def _registry_fp(request,intent,permit,actions,effects,compensations,policy):
    return _fp({'request':request,'intent':intent,'permit':permit,'actions':sorted((x.action_id,_fp(x)) for x in actions),'effects':sorted((x.effect_id,_fp(x)) for x in effects),'compensations':sorted((x.compensation_id,_fp(x)) for x in compensations),'policy':policy})

def prepare_state(request,intent,permit,actions,effects,compensations,policy,*,binding:str,state_epoch:str):
    if binding!=policy.binding or state_epoch!=policy.state_epoch: raise ValueError('PREPARED_BINDING_OR_EPOCH_MISMATCH')
    actions=tuple(sorted(actions,key=lambda x:x.action_id)); effects=tuple(sorted(effects,key=lambda x:x.effect_id)); compensations=tuple(sorted(compensations,key=lambda x:x.compensation_id))
    af=tuple((x.action_id,_fp(x)) for x in actions); ef=tuple((x.effect_id,_fp(x)) for x in effects); cf=tuple((x.compensation_id,_fp(x)) for x in compensations)
    context=_fp({'request':request,'intent':intent,'permit':permit,'policy':policy})
    dep=_fp({'actions':af,'effects':ef,'compensations':cf})
    reg=_registry_fp(request,intent,permit,actions,effects,compensations,policy)
    result=evaluate(request,intent,permit,actions,effects,compensations,policy)
    return PreparedCompensationState(request,intent,permit,actions,effects,compensations,policy,af,ef,cf,context,dep,reg,result,binding,state_epoch)

def validate_prepared_integrity(st):
    if st.binding!=st.policy.binding or st.state_epoch!=st.policy.state_epoch: return False
    if st.action_fingerprints!=tuple(sorted((x.action_id,_fp(x)) for x in st.actions)): return False
    if st.effect_fingerprints!=tuple(sorted((x.effect_id,_fp(x)) for x in st.effects)): return False
    if st.compensation_fingerprints!=tuple(sorted((x.compensation_id,_fp(x)) for x in st.compensations)): return False
    if st.context_fingerprint!=_fp({'request':st.request,'intent':st.intent,'permit':st.permit,'policy':st.policy}): return False
    if st.dependency_fingerprint!=_fp({'actions':st.action_fingerprints,'effects':st.effect_fingerprints,'compensations':st.compensation_fingerprints}): return False
    if st.registry_fingerprint!=_registry_fp(st.request,st.intent,st.permit,st.actions,st.effects,st.compensations,st.policy): return False
    return st.precomputed_result==evaluate(st.request,st.intent,st.permit,st.actions,st.effects,st.compensations,st.policy)

def evaluate_prepared(st,*,current_context_fingerprint,current_dependency_fingerprint,current_registry_fingerprint,prepared_integrity_validated):
    if not prepared_integrity_validated: return _hold('PREPARED_INTEGRITY_UNVERIFIED')
    if (current_context_fingerprint,current_dependency_fingerprint,current_registry_fingerprint)!=(st.context_fingerprint,st.dependency_fingerprint,st.registry_fingerprint): return _hold('PREPARED_STATE_STALE')
    return st.precomputed_result

def make_delta(base,target):
    def diff(base_items,target_items,key):
        bd={getattr(x,key):x for x in base_items}; td={getattr(x,key):x for x in target_items}
        changed=tuple(td[k] for k in sorted(td) if k not in bd or _fp(td[k])!=_fp(bd[k]))
        removed=tuple(sorted(set(bd)-set(td)))
        return changed,removed
    ca,ra=diff(base.actions,target.actions,'action_id'); ce,re=diff(base.effects,target.effects,'effect_id'); cc,rc=diff(base.compensations,target.compensations,'compensation_id')
    pick=lambda a,b: b if _fp(a)!=_fp(b) else None
    return CompensationStateDelta(base.registry_fingerprint,target.registry_fingerprint,ca,ra,ce,re,cc,rc,pick(base.request,target.request),pick(base.intent,target.intent),pick(base.permit,target.permit),pick(base.policy,target.policy),target.binding,target.state_epoch)

def apply_delta(base,delta):
    if base.registry_fingerprint!=delta.base_fingerprint: raise ValueError('DELTA_BASE_MISMATCH')
    def merge(items,changed,removed,key):
        d={getattr(x,key):x for x in items}
        for k in removed: d.pop(k,None)
        for x in changed: d[getattr(x,key)]=x
        return tuple(d[k] for k in sorted(d))
    actions=merge(base.actions,delta.changed_actions,delta.removed_action_ids,'action_id')
    effects=merge(base.effects,delta.changed_effects,delta.removed_effect_ids,'effect_id')
    comps=merge(base.compensations,delta.changed_compensations,delta.removed_compensation_ids,'compensation_id')
    st=prepare_state(delta.target_request or base.request,delta.target_intent or base.intent,delta.target_permit or base.permit,actions,effects,comps,delta.target_policy or base.policy,binding=delta.binding,state_epoch=delta.state_epoch)
    if st.registry_fingerprint!=delta.target_fingerprint: raise ValueError('DELTA_TARGET_MISMATCH')
    return st

def missing_only_sync_plan(target,known_action_fps,known_effect_fps,known_compensation_fps):
    ma=tuple(k for k,v in target.action_fingerprints if known_action_fps.get(k)!=v)
    me=tuple(k for k,v in target.effect_fingerprints if known_effect_fps.get(k)!=v)
    mc=tuple(k for k,v in target.compensation_fingerprints if known_compensation_fps.get(k)!=v)
    meta=len(_canon({'actions':ma,'effects':me,'compensations':mc,'context':target.context_fingerprint,'dependency':target.dependency_fingerprint}))
    total=len(target.action_fingerprints)+len(target.effect_fingerprints)+len(target.compensation_fingerprints)
    missing=len(ma)+len(me)+len(mc)
    return CompensationSyncPlan(ma,me,mc,meta,missing>=max(1,total))

def full_registry_bytes(st):
    return len(_canon({'request':st.request,'intent':st.intent,'permit':st.permit,'actions':st.actions,'effects':st.effects,'compensations':st.compensations,'policy':st.policy,'context':st.context_fingerprint,'dependency':st.dependency_fingerprint}))
def delta_bytes(delta): return len(_canon(delta))
def default_evaluation(): return evaluate(default_request(),default_intent(),default_permit(),default_actions(),default_effects(),default_compensations(),default_policy())
