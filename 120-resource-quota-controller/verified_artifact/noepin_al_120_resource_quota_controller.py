"""NOEPIN AL 120 — Resource Quota Controller — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-120
DCSR: AUXILIARY INTEGRATION / 補助統合.

Controls multiple runtime resource quotas using current usage and short-horizon forecasts.
Continue/Throttle/Stop outputs are candidates/evidence only. They do not grant permission,
execute throttling/stopping, spend resources, or prove success/safety/world truth.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str,Enum): ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class NextAction(str,Enum):
    CONTINUE_CANDIDATE='CONTINUE_CANDIDATE'
    THROTTLE_CANDIDATE='THROTTLE_CANDIDATE'
    STOP_CANDIDATE='STOP_CANDIDATE'
    CONSERVATIVE_THROTTLE_CANDIDATE='CONSERVATIVE_THROTTLE_CANDIDATE'
class Escalation(str,Enum):
    NONE='NONE'; SOFT_THRESHOLD='SOFT_THRESHOLD'; FORECAST_OVERAGE='FORECAST_OVERAGE'; HARD_QUOTA_REACHED='HARD_QUOTA_REACHED'; MEASUREMENT_UNKNOWN='MEASUREMENT_UNKNOWN'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'

@dataclass(frozen=True)
class ResourceQuota:
    resource_id:str
    hard_quota:float
    soft_threshold_ratio:float
    paid_or_high_load:bool
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class ResourceUsage:
    resource_id:str
    current_usage:float|None
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class ResourceForecast:
    resource_id:str
    forecast_additional_usage:float|None
    horizon_seconds:float
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class QuotaPolicy:
    minimum_soft_threshold_ratio:float
    maximum_soft_threshold_ratio:float
    forecast_guard_ratio:float
    low_priority_throttle_multiplier:float

@dataclass(frozen=True)
class QuotaRequest:
    request_id:str
    quotas:tuple[ResourceQuota,...]
    current_usage:tuple[ResourceUsage,...]
    forecasts:tuple[ResourceForecast,...]
    task_priority:float
    policy:QuotaPolicy
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class ResourceQuotaEvaluation:
    resource_id:str
    hard_quota:float
    current_usage:float|None
    remaining_quota:float|None
    forecast_additional_usage:float|None
    projected_usage:float|None
    soft_threshold:float
    state:str
    paid_or_high_load:bool
    throttle_factor_candidate:float

@dataclass(frozen=True)
class QuotaResult:
    decision:Decision
    next_action:NextAction
    escalation:Escalation
    reasons:tuple[str,...]
    evaluations:tuple[ResourceQuotaEvaluation,...]
    limiting_resources:tuple[str,...]
    remaining_quota:tuple[tuple[str,float|None],...]
    forecast:tuple[tuple[str,float|None],...]
    throttle_factor_candidate:float
    stop_candidate:bool
    next_gate_candidate:bool
    continue_promoted_to_permission:bool=False
    throttle_promoted_to_permission:bool=False
    stop_promoted_to_execution:bool=False
    permission_granted:bool=False
    approval_executed:bool=False
    authority_granted:bool=False
    stop_executed:bool=False
    action_executed:bool=False
    plan_committed:bool=False
    publish_executed:bool=False
    external_write_performed:bool=False
    resource_spend_authorized:bool=False
    world_truth_proven:bool=False
    domain_authority_promoted:bool=False
    safety_proven:bool=False
    action_success:bool=False

@dataclass(frozen=True)
class PreparedQuotaState:
    request:QuotaRequest
    result:QuotaResult
    context_fingerprint:str
    quota_fingerprint:str
    usage_fingerprint:str
    forecast_fingerprint:str
    policy_fingerprint:str
    decision_fingerprint:str
    integrity_fingerprint:str
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class QuotaDelta:
    changed_quotas:tuple[ResourceQuota,...]
    removed_quota_ids:tuple[str,...]
    changed_usage:tuple[ResourceUsage,...]
    removed_usage_ids:tuple[str,...]
    changed_forecasts:tuple[ResourceForecast,...]
    removed_forecast_ids:tuple[str,...]
    from_registry_fingerprint:str
    to_registry_fingerprint:str

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

def _canon(v)->bytes: return json.dumps(_obj(v),ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def _fp(v)->str: return sha256(_canon(v)).hexdigest()
def _finite(x): return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(float(x))

def default_policy(): return QuotaPolicy(.50,.98,.97,.75)

def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    quotas=(
      ResourceQuota('CPU_SECONDS',100.0,.80,True,b,e),
      ResourceQuota('MEMORY_MB',4096.0,.85,True,b,e),
      ResourceQuota('TOKENS',100000.0,.80,True,b,e),
      ResourceQuota('API_CALLS',1000.0,.80,True,b,e),
      ResourceQuota('COST_USD',25.0,.75,True,b,e),
      ResourceQuota('DISK_MB',10000.0,.90,False,b,e),
    )
    usage=(
      ResourceUsage('CPU_SECONDS',20.0,b,e), ResourceUsage('MEMORY_MB',1200.0,b,e),
      ResourceUsage('TOKENS',20000.0,b,e), ResourceUsage('API_CALLS',150.0,b,e),
      ResourceUsage('COST_USD',4.0,b,e), ResourceUsage('DISK_MB',2000.0,b,e),
    )
    forecasts=(
      ResourceForecast('CPU_SECONDS',5.0,60.0,b,e), ResourceForecast('MEMORY_MB',150.0,60.0,b,e),
      ResourceForecast('TOKENS',5000.0,60.0,b,e), ResourceForecast('API_CALLS',30.0,60.0,b,e),
      ResourceForecast('COST_USD',1.0,60.0,b,e), ResourceForecast('DISK_MB',100.0,60.0,b,e),
    )
    return QuotaRequest('DEFAULT-120',quotas,usage,forecasts,.5,default_policy(),b,e)

def _invalid(req,reason):
    return QuotaResult(Decision.HOLD,NextAction.CONSERVATIVE_THROTTLE_CANDIDATE,Escalation.INVALID_CONFIGURATION,(reason,'NO_AUTOMATIC_RESOURCE_CONSUMPTION'),(),(),(),(),0.0,False,False)

def _registry_fp(req): return _fp((req.quotas,req.current_usage,req.forecasts,req.binding,req.state_epoch))

def evaluate(req:QuotaRequest)->QuotaResult:
    p=req.policy
    if not req.request_id or not req.binding or not req.state_epoch: return _invalid(req,'INVALID_REQUEST_IDENTITY')
    nums=(p.minimum_soft_threshold_ratio,p.maximum_soft_threshold_ratio,p.forecast_guard_ratio,p.low_priority_throttle_multiplier,req.task_priority)
    if not all(_finite(x) for x in nums): return _invalid(req,'POLICY_OR_PRIORITY_NONFINITE')
    if not (0<=p.minimum_soft_threshold_ratio<=p.maximum_soft_threshold_ratio<=1): return _invalid(req,'SOFT_THRESHOLD_POLICY_INVALID')
    if not 0<p.forecast_guard_ratio<=1 or not 0<p.low_priority_throttle_multiplier<=1 or not 0<=req.task_priority<=1: return _invalid(req,'POLICY_RANGE_INVALID')
    if not req.quotas: return _invalid(req,'EMPTY_QUOTA_SET')
    qids=[x.resource_id for x in req.quotas]; uids=[x.resource_id for x in req.current_usage]; fids=[x.resource_id for x in req.forecasts]
    if len(set(qids))!=len(qids) or len(set(uids))!=len(uids) or len(set(fids))!=len(fids): return _invalid(req,'DUPLICATE_RESOURCE_ID')
    if set(qids)!=set(uids) or set(qids)!=set(fids): return _invalid(req,'RESOURCE_VECTOR_MISMATCH')
    for q in req.quotas:
        if not q.resource_id or q.binding!=req.binding or q.state_epoch!=req.state_epoch or not _finite(q.hard_quota) or float(q.hard_quota)<=0 or not _finite(q.soft_threshold_ratio) or not p.minimum_soft_threshold_ratio<=float(q.soft_threshold_ratio)<=p.maximum_soft_threshold_ratio: return _invalid(req,'QUOTA_INVALID')
    for u in req.current_usage:
        if not u.resource_id or u.binding!=req.binding or u.state_epoch!=req.state_epoch or (u.current_usage is not None and (not _finite(u.current_usage) or float(u.current_usage)<0)): return _invalid(req,'USAGE_INVALID')
    for f in req.forecasts:
        if not f.resource_id or f.binding!=req.binding or f.state_epoch!=req.state_epoch or not _finite(f.horizon_seconds) or float(f.horizon_seconds)<=0 or (f.forecast_additional_usage is not None and (not _finite(f.forecast_additional_usage) or float(f.forecast_additional_usage)<0)): return _invalid(req,'FORECAST_INVALID')
    um={x.resource_id:x for x in req.current_usage}; fm={x.resource_id:x for x in req.forecasts}
    ev=[]; hard=[]; unknown=[]; forecast_over=[]; soft=[]; limiting=[]; throttle_factors=[]
    for q in sorted(req.quotas,key=lambda x:x.resource_id):
        u=um[q.resource_id].current_usage; f=fm[q.resource_id].forecast_additional_usage
        soft_limit=float(q.hard_quota)*float(q.soft_threshold_ratio)
        if u is None or f is None:
            state='MEASUREMENT_UNKNOWN'; remaining=None if u is None else max(0.0,float(q.hard_quota)-float(u)); projected=None
            factor=.10 if q.paid_or_high_load else .25
            unknown.append(q.resource_id); limiting.append(q.resource_id); throttle_factors.append(factor)
        else:
            u=float(u); f=float(f); remaining=max(0.0,float(q.hard_quota)-u); projected=u+f
            if u>=float(q.hard_quota):
                state='HARD_QUOTA_REACHED'; factor=0.0; hard.append(q.resource_id); limiting.append(q.resource_id); throttle_factors.append(factor)
            elif projected>=float(q.hard_quota)*float(p.forecast_guard_ratio):
                state='FORECAST_OVERAGE'; factor=max(.05,min(.50,remaining/max(f,1e-12)*.45)); forecast_over.append(q.resource_id); limiting.append(q.resource_id); throttle_factors.append(factor)
            elif u>=soft_limit or projected>=soft_limit:
                state='SOFT_THRESHOLD'; pressure=max(u,projected)/float(q.hard_quota); base=max(.10,min(.80,1.0-pressure)); priority_adjust=(p.low_priority_throttle_multiplier+(1-p.low_priority_throttle_multiplier)*float(req.task_priority)); factor=max(.05,min(.80,base*priority_adjust)); soft.append(q.resource_id); limiting.append(q.resource_id); throttle_factors.append(factor)
            else:
                state='CONTINUE'; factor=1.0
        ev.append(ResourceQuotaEvaluation(q.resource_id,float(q.hard_quota),u,remaining,f,projected,soft_limit,state,q.paid_or_high_load,round(factor,12)))
    evaluations=tuple(ev); remaining_tuple=tuple((x.resource_id,x.remaining_quota) for x in evaluations); forecast_tuple=tuple((x.resource_id,x.forecast_additional_usage) for x in evaluations)
    limiting_tuple=tuple(sorted(set(limiting))); tf=round(min(throttle_factors) if throttle_factors else 1.0,12)
    if hard:
        return QuotaResult(Decision.DENY,NextAction.STOP_CANDIDATE,Escalation.HARD_QUOTA_REACHED,('HARD_QUOTA_REACHED','STOP_IS_CANDIDATE_ONLY','NO_ADDITIONAL_RESOURCE_CONSUMPTION_AUTHORIZED'),evaluations,limiting_tuple,remaining_tuple,forecast_tuple,0.0,True,False)
    if unknown:
        return QuotaResult(Decision.HOLD,NextAction.CONSERVATIVE_THROTTLE_CANDIDATE,Escalation.MEASUREMENT_UNKNOWN,('RESOURCE_MEASUREMENT_UNKNOWN','PAID_OR_HIGH_LOAD_UNKNOWN_REMAINS_CONSERVATIVE','NO_AUTOMATIC_RESOURCE_CONSUMPTION'),evaluations,limiting_tuple,remaining_tuple,forecast_tuple,tf,False,False)
    if forecast_over:
        return QuotaResult(Decision.ALLOW,NextAction.THROTTLE_CANDIDATE,Escalation.FORECAST_OVERAGE,('PREDICTED_QUOTA_PRESSURE','PREEMPTIVE_THROTTLE_CANDIDATE','THROTTLE_IS_NOT_PERMISSION'),evaluations,limiting_tuple,remaining_tuple,forecast_tuple,tf,False,True)
    if soft:
        return QuotaResult(Decision.ALLOW,NextAction.THROTTLE_CANDIDATE,Escalation.SOFT_THRESHOLD,('SOFT_THRESHOLD_REACHED','THROTTLE_CANDIDATE','THROTTLE_IS_NOT_PERMISSION'),evaluations,limiting_tuple,remaining_tuple,forecast_tuple,tf,False,True)
    return QuotaResult(Decision.ALLOW,NextAction.CONTINUE_CANDIDATE,Escalation.NONE,('QUOTAS_WITHIN_GUARD_BANDS','CONTINUE_IS_CANDIDATE_ONLY'),evaluations,(),remaining_tuple,forecast_tuple,1.0,False,True)

def default_evaluation(): return evaluate(default_request())

def prepare_state(req:QuotaRequest,*,binding:str,state_epoch:str)->PreparedQuotaState:
    if binding!=req.binding or state_epoch!=req.state_epoch: raise ValueError('binding/state_epoch mismatch')
    res=evaluate(req); cfp=_fp((req.request_id,req.task_priority,binding,state_epoch)); qfp=_fp(req.quotas); ufp=_fp(req.current_usage); ffp=_fp(req.forecasts); pfp=_fp(req.policy); dfp=_fp(res); integ=_fp((cfp,qfp,ufp,ffp,pfp,dfp,binding,state_epoch))
    return PreparedQuotaState(req,res,cfp,qfp,ufp,ffp,pfp,dfp,integ,binding,state_epoch)

def validate_prepared_integrity(st): return st.integrity_fingerprint==_fp((st.context_fingerprint,st.quota_fingerprint,st.usage_fingerprint,st.forecast_fingerprint,st.policy_fingerprint,st.decision_fingerprint,st.binding,st.state_epoch))

def evaluate_prepared(st,*,integrity_validated,current_context_fingerprint,current_quota_fingerprint,current_usage_fingerprint,current_forecast_fingerprint,current_policy_fingerprint,current_decision_fingerprint):
    if not integrity_validated or not validate_prepared_integrity(st): return _invalid(st.request,'PREPARED_INTEGRITY_NOT_VALIDATED')
    if (current_context_fingerprint,current_quota_fingerprint,current_usage_fingerprint,current_forecast_fingerprint,current_policy_fingerprint,current_decision_fingerprint)!=(st.context_fingerprint,st.quota_fingerprint,st.usage_fingerprint,st.forecast_fingerprint,st.policy_fingerprint,st.decision_fingerprint): return _invalid(st.request,'PREPARED_FINGERPRINT_MISMATCH')
    return st.result

def make_delta(old,new):
    oq={x.resource_id:x for x in old.request.quotas}; nq={x.resource_id:x for x in new.request.quotas}
    ou={x.resource_id:x for x in old.request.current_usage}; nu={x.resource_id:x for x in new.request.current_usage}
    of={x.resource_id:x for x in old.request.forecasts}; nf={x.resource_id:x for x in new.request.forecasts}
    cq=tuple(nq[k] for k in sorted(nq) if k not in oq or _fp(nq[k])!=_fp(oq[k])); rq=tuple(k for k in sorted(oq) if k not in nq)
    cu=tuple(nu[k] for k in sorted(nu) if k not in ou or _fp(nu[k])!=_fp(ou[k])); ru=tuple(k for k in sorted(ou) if k not in nu)
    cf=tuple(nf[k] for k in sorted(nf) if k not in of or _fp(nf[k])!=_fp(of[k])); rf=tuple(k for k in sorted(of) if k not in nf)
    return QuotaDelta(cq,rq,cu,ru,cf,rf,_registry_fp(old.request),_registry_fp(new.request))

def plan_missing_only(old,new):
    d=make_delta(old,new); ids=tuple([f'QUOTA:{x.resource_id}' for x in d.changed_quotas]+[f'REMOVED_QUOTA:{x}' for x in d.removed_quota_ids]+[f'USAGE:{x.resource_id}' for x in d.changed_usage]+[f'REMOVED_USAGE:{x}' for x in d.removed_usage_ids]+[f'FORECAST:{x.resource_id}' for x in d.changed_forecasts]+[f'REMOVED_FORECAST:{x}' for x in d.removed_forecast_ids]); meta=len(_canon({'from':d.from_registry_fingerprint,'to':d.to_registry_fingerprint,'ids':ids})); return MissingOnlyPlan(ids,meta,False)
