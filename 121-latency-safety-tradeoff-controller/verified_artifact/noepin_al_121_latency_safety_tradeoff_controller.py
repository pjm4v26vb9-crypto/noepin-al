"""NOEPIN AL 121 — Latency-Safety Tradeoff Controller — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-121
DCSR: AUXILIARY INTEGRATION / 補助統合.
Selected checks, latency and residual-risk values are control candidates/evidence only; they do not grant permission, execute checks/actions, or prove safety/world truth/action success.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str,Enum): ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class RiskClass(str,Enum): LOW='LOW'; MEDIUM='MEDIUM'; HIGH='HIGH'; CRITICAL='CRITICAL'
class NextAction(str,Enum): FAST_PATH_CHECK_SET_CANDIDATE='FAST_PATH_CHECK_SET_CANDIDATE'; STANDARD_CHECK_SET_CANDIDATE='STANDARD_CHECK_SET_CANDIDATE'; DEEP_CHECK_SET_CANDIDATE='DEEP_CHECK_SET_CANDIDATE'; HOLD_CHECK_REQUIREMENTS='HOLD_CHECK_REQUIREMENTS'
class Escalation(str,Enum): NONE='NONE'; MANDATORY_CHECK_UNAVAILABLE='MANDATORY_CHECK_UNAVAILABLE'; MANDATORY_CHECK_TIMEOUT='MANDATORY_CHECK_TIMEOUT'; LATENCY_BUDGET_INSUFFICIENT='LATENCY_BUDGET_INSUFFICIENT'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'
RANK={RiskClass.LOW:0,RiskClass.MEDIUM:1,RiskClass.HIGH:2,RiskClass.CRITICAL:3}
BASE_RISK={RiskClass.LOW:.20,RiskClass.MEDIUM:.45,RiskClass.HIGH:.70,RiskClass.CRITICAL:1.0}

@dataclass(frozen=True)
class SafetyCheck:
    check_id:str; latency_ms:float; safety_value:float; mandatory_from_risk:RiskClass|None; available:bool; timed_out:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class TradeoffPolicy:
    minimum_latency_budget_ms:float; residual_risk_floor:float; deep_check_headroom_ratio:float
@dataclass(frozen=True)
class TradeoffRequest:
    request_id:str; latency_budget_ms:float; risk_class:RiskClass; checks:tuple[SafetyCheck,...]; policy:TradeoffPolicy; binding:str; state_epoch:str
@dataclass(frozen=True)
class TradeoffResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; reasons:tuple[str,...]; selected_check_set:tuple[str,...]; mandatory_check_set:tuple[str,...]; expected_latency_ms:float; residual_risk:float; unused_latency_ms:float; next_gate_candidate:bool
    selected_checks_promoted_to_permission:bool=False; check_execution_performed:bool=False; permission_granted:bool=False; approval_executed:bool=False; authority_granted:bool=False; stop_executed:bool=False; action_executed:bool=False; plan_committed:bool=False; publish_executed:bool=False; external_write_performed:bool=False; world_truth_proven:bool=False; domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedTradeoffState:
    request:TradeoffRequest; result:TradeoffResult; context_fingerprint:str; check_fingerprint:str; policy_fingerprint:str; selection_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class TradeoffDelta:
    changed_checks:tuple[SafetyCheck,...]; removed_check_ids:tuple[str,...]; from_registry_fingerprint:str; to_registry_fingerprint:str
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
def _finite(x): return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(float(x))
def default_policy(): return TradeoffPolicy(.1,0.0,.25)
def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    c=(
      SafetyCheck('IDENTITY',.4,.12,RiskClass.LOW,True,False,b,e),
      SafetyCheck('POLICY',.8,.20,RiskClass.MEDIUM,True,False,b,e),
      SafetyCheck('AUTHORITY',1.0,.22,RiskClass.HIGH,True,False,b,e),
      SafetyCheck('SIDE_EFFECT',1.4,.28,RiskClass.CRITICAL,True,False,b,e),
      SafetyCheck('CONTEXT_DEEP',1.6,.16,None,True,False,b,e),
      SafetyCheck('COUNTEREXAMPLE',1.2,.14,None,True,False,b,e),
    )
    return TradeoffRequest('DEFAULT-121',4.0,RiskClass.MEDIUM,c,default_policy(),b,e)
def _invalid(req,reason): return TradeoffResult(Decision.HOLD,NextAction.HOLD_CHECK_REQUIREMENTS,Escalation.INVALID_CONFIGURATION,(reason,'NO_AUTOMATIC_EXECUTION'),(),(),0.0,1.0,max(0.0,float(getattr(req,'latency_budget_ms',0) or 0)),False)
def _registry_fp(req): return _fp((req.checks,req.binding,req.state_epoch))
def _is_mandatory(c,risk): return c.mandatory_from_risk is not None and RANK[risk]>=RANK[c.mandatory_from_risk]

def evaluate(req:TradeoffRequest)->TradeoffResult:
    if not req.request_id or not req.binding or not req.state_epoch: return _invalid(req,'INVALID_REQUEST_IDENTITY')
    if not isinstance(req.risk_class,RiskClass): return _invalid(req,'INVALID_RISK_CLASS')
    p=req.policy
    if not all(_finite(x) for x in (req.latency_budget_ms,p.minimum_latency_budget_ms,p.residual_risk_floor,p.deep_check_headroom_ratio)): return _invalid(req,'NONFINITE_CONFIGURATION')
    if req.latency_budget_ms<0 or p.minimum_latency_budget_ms<0 or not 0<=p.residual_risk_floor<=1 or not 0<=p.deep_check_headroom_ratio<=1: return _invalid(req,'POLICY_RANGE_INVALID')
    if not req.checks: return _invalid(req,'EMPTY_CHECK_SET')
    ids=[c.check_id for c in req.checks]
    if any(not x for x in ids) or len(ids)!=len(set(ids)): return _invalid(req,'DUPLICATE_OR_EMPTY_CHECK_ID')
    for c in req.checks:
        if c.binding!=req.binding or c.state_epoch!=req.state_epoch or not _finite(c.latency_ms) or c.latency_ms<0 or not _finite(c.safety_value) or not 0<=c.safety_value<=1: return _invalid(req,'CHECK_INVALID')
    mandatory=tuple(sorted((c for c in req.checks if _is_mandatory(c,req.risk_class)),key=lambda x:x.check_id))
    unavailable=[c.check_id for c in mandatory if not c.available]
    timed=[c.check_id for c in mandatory if c.timed_out]
    mandatory_ids=tuple(c.check_id for c in mandatory)
    if unavailable: return TradeoffResult(Decision.HOLD,NextAction.HOLD_CHECK_REQUIREMENTS,Escalation.MANDATORY_CHECK_UNAVAILABLE,('MANDATORY_CHECK_UNAVAILABLE','MANDATORY_CHECKS_CANNOT_BE_SKIPPED'),(),mandatory_ids,0.0,BASE_RISK[req.risk_class],req.latency_budget_ms,False)
    if timed: return TradeoffResult(Decision.HOLD,NextAction.HOLD_CHECK_REQUIREMENTS,Escalation.MANDATORY_CHECK_TIMEOUT,('MANDATORY_CHECK_TIMEOUT','TIMEOUT_DOES_NOT_AUTHORIZE_SKIP'),(),mandatory_ids,0.0,BASE_RISK[req.risk_class],req.latency_budget_ms,False)
    mandatory_cost=sum(c.latency_ms for c in mandatory)
    if mandatory_cost>req.latency_budget_ms+1e-12:
        return TradeoffResult(Decision.HOLD,NextAction.HOLD_CHECK_REQUIREMENTS,Escalation.LATENCY_BUDGET_INSUFFICIENT,('MANDATORY_CHECKS_EXCEED_LATENCY_BUDGET','SPEED_NOT_PRIORITIZED_OVER_REQUIRED_SAFETY'),(),mandatory_ids,round(mandatory_cost,12),BASE_RISK[req.risk_class],0.0,False)
    selected=list(mandatory); selected_ids=set(mandatory_ids); remaining=req.latency_budget_ms-mandatory_cost
    optional=[c for c in req.checks if c.check_id not in selected_ids and c.available and not c.timed_out]
    optional.sort(key=lambda c:(-c.safety_value/max(c.latency_ms,1e-12),-c.safety_value,c.latency_ms,c.check_id))
    for c in optional:
        if c.latency_ms<=remaining+1e-12:
            selected.append(c); selected_ids.add(c.check_id); remaining-=c.latency_ms
    selected=sorted(selected,key=lambda c:c.check_id)
    latency=sum(c.latency_ms for c in selected)
    reduction=sum(c.safety_value for c in selected)
    residual=max(p.residual_risk_floor,BASE_RISK[req.risk_class]-reduction)
    optional_selected=len(selected)-len(mandatory)
    headroom=(req.latency_budget_ms-latency)/max(req.latency_budget_ms,1e-12) if req.latency_budget_ms else 0
    if req.risk_class==RiskClass.LOW and optional_selected==0: na=NextAction.FAST_PATH_CHECK_SET_CANDIDATE
    elif optional_selected>0 and headroom<=p.deep_check_headroom_ratio: na=NextAction.DEEP_CHECK_SET_CANDIDATE
    else: na=NextAction.STANDARD_CHECK_SET_CANDIDATE
    return TradeoffResult(Decision.ALLOW,na,Escalation.NONE,('MANDATORY_CHECKS_INCLUDED','OPTIONAL_CHECKS_SELECTED_WITHIN_LATENCY_BUDGET','SELECTED_CHECK_SET_IS_CANDIDATE_ONLY'),tuple(c.check_id for c in selected),mandatory_ids,round(latency,12),round(residual,12),round(max(0.0,req.latency_budget_ms-latency),12),True)

def default_evaluation(): return evaluate(default_request())
def prepare_state(req,*,binding,state_epoch):
    if binding!=req.binding or state_epoch!=req.state_epoch: raise ValueError('binding/state_epoch mismatch')
    r=evaluate(req); cfp=_fp((req.request_id,req.latency_budget_ms,req.risk_class,binding,state_epoch)); chfp=_fp(req.checks); pfp=_fp(req.policy); sfp=_fp(r); integ=_fp((cfp,chfp,pfp,sfp,binding,state_epoch)); return PreparedTradeoffState(req,r,cfp,chfp,pfp,sfp,integ,binding,state_epoch)
def validate_prepared_integrity(st): return st.integrity_fingerprint==_fp((st.context_fingerprint,st.check_fingerprint,st.policy_fingerprint,st.selection_fingerprint,st.binding,st.state_epoch))
def evaluate_prepared(st,*,integrity_validated,current_context_fingerprint,current_check_fingerprint,current_policy_fingerprint,current_selection_fingerprint):
    if not integrity_validated or not validate_prepared_integrity(st): return _invalid(st.request,'PREPARED_INTEGRITY_NOT_VALIDATED')
    if (current_context_fingerprint,current_check_fingerprint,current_policy_fingerprint,current_selection_fingerprint)!=(st.context_fingerprint,st.check_fingerprint,st.policy_fingerprint,st.selection_fingerprint): return _invalid(st.request,'PREPARED_FINGERPRINT_MISMATCH')
    return st.result
def make_delta(old,new):
    o={x.check_id:x for x in old.request.checks}; n={x.check_id:x for x in new.request.checks}; ch=tuple(n[k] for k in sorted(n) if k not in o or _fp(n[k])!=_fp(o[k])); rm=tuple(k for k in sorted(o) if k not in n); return TradeoffDelta(ch,rm,_registry_fp(old.request),_registry_fp(new.request))
def plan_missing_only(old,new):
    d=make_delta(old,new); ids=tuple([f'CHECK:{x.check_id}' for x in d.changed_checks]+[f'REMOVED_CHECK:{x}' for x in d.removed_check_ids]); meta=len(_canon({'from':d.from_registry_fingerprint,'to':d.to_registry_fingerprint,'ids':ids})); return MissingOnlyPlan(ids,meta,False)
