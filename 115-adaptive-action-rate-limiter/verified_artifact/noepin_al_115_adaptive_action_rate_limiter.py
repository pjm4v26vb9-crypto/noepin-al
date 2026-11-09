"""NOEPIN AL 115 — Adaptive Action Rate Limiter — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Deterministic, fail-safe adaptive rate limiting for agent action frequency. The limiter combines
requested Action Rate with bounded Risk, Error Rate, System Load, Trust, critical-error streak,
and stable-window evidence. It produces only an Allowed Rate / Backoff / Cooldown candidate.
It never grants permission, executes a stop/kill, performs an action, or promotes monitoring
metrics to World Truth, Safety Proof, or Action Success.

Canonical identity: NOEPIN-AL-115
DCSR level: AUXILIARY INTEGRATION / 補助統合.
Provenance note: exact registered Origin GUID was not freshly reverified in this completion
session and is intentionally not guessed or regenerated.
Pre-existing Notion V1 attachment byte identity was not freshly reverified.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str, Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class NextAction(str, Enum):
    RATE_LIMIT_CANDIDATE='RATE_LIMIT_CANDIDATE'
    RATE_ZERO_KILL_CANDIDATE='RATE_ZERO_KILL_CANDIDATE'
    LOW_RATE_HOLD_CANDIDATE='LOW_RATE_HOLD_CANDIDATE'
    RECOVERY_RATE_CANDIDATE='RECOVERY_RATE_CANDIDATE'
    HOLD_REVIEW_CANDIDATE='HOLD_REVIEW_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; CRITICAL_ERROR_STREAK='CRITICAL_ERROR_STREAK'; METRIC_UNAVAILABLE='METRIC_UNAVAILABLE'; HIGH_RISK='HIGH_RISK'; LOW_TRUST='LOW_TRUST'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'

@dataclass(frozen=True)
class RateWindow:
    window_id: int
    action_rate: float
    risk: float|None
    error_rate: float|None
    system_load: float|None
    trust: float|None
    critical_error: bool
    metric_version: str
    metric_fingerprint: str
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class RatePolicy:
    hard_max_rate: float
    low_monitor_rate: float
    min_operational_rate: float
    critical_error_rate_threshold: float
    critical_streak_threshold: int
    high_risk_threshold: float
    low_trust_threshold: float
    low_trust_cap_fraction: float
    risk_weight: float
    error_weight: float
    load_weight: float
    trust_penalty_weight: float
    recovery_stable_windows: int
    recovery_step_fraction: float
    base_cooldown_seconds: float
    max_cooldown_seconds: float

@dataclass(frozen=True)
class RateLimitRequest:
    request_id: str
    windows: tuple[RateWindow,...]
    high_risk_action: bool
    policy: RatePolicy
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class RateLimitResult:
    decision: Decision
    next_action: NextAction
    escalation: Escalation
    reasons: tuple[str,...]
    requested_rate: float|None
    allowed_rate: float|None
    effective_cap: float|None
    backoff_factor: float|None
    cooldown_seconds: float|None
    critical_streak: int
    stable_windows: int
    metric_completeness: float
    high_risk_action: bool
    next_gate_candidate: bool
    rate_candidate_promoted_to_permission: bool=False
    kill_candidate_promoted_to_stop_execution: bool=False
    permission_granted: bool=False
    approval_executed: bool=False
    authority_granted: bool=False
    stop_executed: bool=False
    action_executed: bool=False
    plan_committed: bool=False
    publish_executed: bool=False
    external_write_performed: bool=False
    world_truth_proven: bool=False
    domain_authority_promoted: bool=False
    safety_proven: bool=False
    action_success: bool=False

@dataclass(frozen=True)
class PreparedRateState:
    request: RateLimitRequest
    window_fingerprints: tuple[tuple[int,str],...]
    context_fingerprint: str
    metrics_fingerprint: str
    policy_fingerprint: str
    registry_fingerprint: str
    limiter_fingerprint: str
    precomputed_result: RateLimitResult
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class RateStateDelta:
    base_registry_fingerprint: str
    target_registry_fingerprint: str
    changed_windows: tuple[RateWindow,...]
    removed_window_ids: tuple[int,...]
    policy_replacement: RatePolicy|None
    high_risk_action_replacement: bool|None
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class RateSyncPlan:
    missing_or_changed_record_ids: tuple[str,...]
    metadata_bytes_required: int
    full_resend_required: bool


def _j(v):
    if isinstance(v,Enum): return v.value
    if is_dataclass(v): return {f.name:_j(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v,dict): return {str(k):_j(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(tuple,list)): return [_j(x) for x in v]
    if isinstance(v,float):
        if not math.isfinite(v): return str(v)
        return float(format(v,'.15g'))
    return v

def _canon(v): return json.dumps(_j(v),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
def _fp(v): return sha256(_canon(v)).hexdigest()
def _finite(v): return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(float(v))
def _clamp(v,lo,hi): return max(lo,min(hi,v))

def _hold(reason, *, escalation=Escalation.INVALID_CONFIGURATION, requested=None, high=False, completeness=0.0):
    return RateLimitResult(Decision.HOLD,NextAction.HOLD_REVIEW_CANDIDATE,escalation,(reason,),requested,None,None,None,None,0,0,completeness,high,False)

def _validate(req:RateLimitRequest):
    if not isinstance(req,RateLimitRequest): return 'TYPE_INVALID'
    if not req.request_id or not req.binding or not req.state_epoch: return 'REQUEST_INVALID'
    if not isinstance(req.high_risk_action,bool): return 'HIGH_RISK_FLAG_INVALID'
    p=req.policy
    if not isinstance(p,RatePolicy): return 'POLICY_INVALID'
    nums=(p.hard_max_rate,p.low_monitor_rate,p.min_operational_rate,p.critical_error_rate_threshold,p.high_risk_threshold,p.low_trust_threshold,p.low_trust_cap_fraction,p.risk_weight,p.error_weight,p.load_weight,p.trust_penalty_weight,p.recovery_step_fraction,p.base_cooldown_seconds,p.max_cooldown_seconds)
    if any(not _finite(x) or float(x)<0 for x in nums): return 'POLICY_NUMERIC_INVALID'
    if p.hard_max_rate<=0 or p.low_monitor_rate>p.hard_max_rate or p.min_operational_rate>p.hard_max_rate: return 'POLICY_RATE_INVALID'
    if any(float(x)>1 for x in (p.critical_error_rate_threshold,p.high_risk_threshold,p.low_trust_threshold,p.low_trust_cap_fraction,p.risk_weight,p.error_weight,p.load_weight,p.trust_penalty_weight,p.recovery_step_fraction)): return 'POLICY_FRACTION_INVALID'
    if p.max_cooldown_seconds<p.base_cooldown_seconds: return 'POLICY_COOLDOWN_INVALID'
    if not isinstance(p.critical_streak_threshold,int) or isinstance(p.critical_streak_threshold,bool) or p.critical_streak_threshold<=0: return 'POLICY_STREAK_INVALID'
    if not isinstance(p.recovery_stable_windows,int) or isinstance(p.recovery_stable_windows,bool) or p.recovery_stable_windows<=0: return 'POLICY_RECOVERY_INVALID'
    ids=[]
    for w in req.windows:
        if not isinstance(w,RateWindow): return 'WINDOW_TYPE_INVALID'
        if not isinstance(w.window_id,int) or isinstance(w.window_id,bool) or w.window_id<0: return 'WINDOW_ID_INVALID'
        if not _finite(w.action_rate) or float(w.action_rate)<0: return 'ACTION_RATE_INVALID'
        for v in (w.risk,w.error_rate,w.system_load,w.trust):
            if v is not None and (not _finite(v) or float(v)<0 or float(v)>1): return 'METRIC_RANGE_INVALID'
        if not isinstance(w.critical_error,bool): return 'CRITICAL_FLAG_INVALID'
        if not w.metric_version or not w.metric_fingerprint: return 'WINDOW_IDENTITY_INVALID'
        if w.binding!=req.binding or w.state_epoch!=req.state_epoch: return 'WINDOW_BINDING_INVALID'
        ids.append(w.window_id)
    if len(ids)!=len(set(ids)): return 'DUPLICATE_WINDOW_ID'
    return None

def _ordered(req): return tuple(sorted(req.windows,key=lambda w:w.window_id))
def _complete(w): return sum(v is not None for v in (w.risk,w.error_rate,w.system_load,w.trust))/4.0

def _critical_streak(ws, p):
    c=0
    for w in reversed(ws):
        crit=w.critical_error or (w.error_rate is not None and float(w.error_rate)>=float(p.critical_error_rate_threshold))
        if not crit: break
        c+=1
    return c

def _stable(w,p):
    return (w.risk is not None and w.error_rate is not None and w.system_load is not None and w.trust is not None and
            w.risk<=0.25 and w.error_rate<=0.10 and w.system_load<=0.60 and w.trust>=0.75 and not w.critical_error)

def _stable_windows(ws,p):
    c=0
    for w in reversed(ws):
        if not _stable(w,p): break
        c+=1
    return c

def _severity(w,p):
    risk=float(w.risk or 0.0); err=float(w.error_rate or 0.0); load=float(w.system_load or 0.0); trust=float(w.trust if w.trust is not None else 0.0)
    return _clamp(p.risk_weight*risk+p.error_weight*err+p.load_weight*load+p.trust_penalty_weight*(1.0-trust),0.0,1.0)

def evaluate(req:RateLimitRequest)->RateLimitResult:
    err=_validate(req)
    if err: return _hold(err,high=getattr(req,'high_risk_action',False))
    ws=_ordered(req)
    if not ws: return _hold('NO_WINDOWS',escalation=Escalation.METRIC_UNAVAILABLE,high=req.high_risk_action)
    p=req.policy; cur=ws[-1]; requested=min(float(cur.action_rate),float(p.hard_max_rate)); completeness=_complete(cur)
    crit=_critical_streak(ws,p); stable=_stable_windows(ws,p)
    # Critical streak: zero-rate candidate. This is not a kill/stop execution.
    if crit>=p.critical_streak_threshold:
        return RateLimitResult(Decision.HOLD,NextAction.RATE_ZERO_KILL_CANDIDATE,Escalation.CRITICAL_ERROR_STREAK,('CRITICAL_ERROR_STREAK','RATE_ZERO_CANDIDATE_ONLY','KILL_NOT_EXECUTED'),requested,0.0,0.0,0.0,float(p.max_cooldown_seconds),crit,stable,completeness,req.high_risk_action,False)
    missing=completeness<1.0
    if missing:
        cap=min(requested,float(p.low_monitor_rate))
        reason='HIGH_RISK_METRIC_UNAVAILABLE' if req.high_risk_action else 'METRIC_UNAVAILABLE'
        cooldown=min(float(p.max_cooldown_seconds),float(p.base_cooldown_seconds)*8.0)
        return RateLimitResult(Decision.HOLD,NextAction.LOW_RATE_HOLD_CANDIDATE,Escalation.METRIC_UNAVAILABLE,(reason,'LOW_RATE_FIXED_CANDIDATE','AUTO_EXECUTION_BLOCKED'),requested,cap,cap,(cap/requested if requested>0 else 0.0),cooldown,crit,stable,completeness,req.high_risk_action,False)
    severity=_severity(cur,p)
    cap=requested*(1.0-0.80*severity)
    # Direct risk/load/error penalties are monotonic and immediate.
    cap=min(cap,requested*(1.0-0.70*float(cur.risk)),requested*(1.0-0.60*float(cur.error_rate)),requested*(1.0-0.45*float(cur.system_load)))
    escalation=Escalation.NONE
    reasons=['ADAPTIVE_BACKOFF_APPLIED']
    if float(cur.trust)<float(p.low_trust_threshold):
        cap=min(cap,requested*float(p.low_trust_cap_fraction)); escalation=Escalation.LOW_TRUST; reasons.append('LOW_TRUST_CAP')
    if float(cur.risk)>=float(p.high_risk_threshold):
        cap=min(cap,requested*0.20); escalation=Escalation.HIGH_RISK; reasons.append('HIGH_RISK_CAP')
    cap=max(0.0,cap)
    # Recovery is intentionally gradual. A previous window with a lower permitted rate cannot jump to target.
    prev_allowed=None
    if len(ws)>=2:
        prev=ws[-2]; prev_req=min(float(prev.action_rate),float(p.hard_max_rate))
        if _complete(prev)==1.0:
            prev_sev=_severity(prev,p)
            prev_allowed=min(prev_req*(1.0-0.80*prev_sev),prev_req*(1.0-0.70*float(prev.risk)),prev_req*(1.0-0.60*float(prev.error_rate)),prev_req*(1.0-0.45*float(prev.system_load)))
            if float(prev.trust)<float(p.low_trust_threshold): prev_allowed=min(prev_allowed,prev_req*float(p.low_trust_cap_fraction))
            if float(prev.risk)>=float(p.high_risk_threshold): prev_allowed=min(prev_allowed,prev_req*0.20)
            prev_allowed=max(0.0,prev_allowed)
    allowed=cap; next_action=NextAction.RATE_LIMIT_CANDIDATE
    if prev_allowed is not None and cap>prev_allowed:
        if stable>=p.recovery_stable_windows:
            step=max(requested*float(p.recovery_step_fraction),0.0)
            allowed=min(cap,prev_allowed+step); next_action=NextAction.RECOVERY_RATE_CANDIDATE; reasons.append('GRADUAL_RECOVERY')
        else:
            allowed=min(cap,prev_allowed); reasons.append('RECOVERY_WITHHELD_UNTIL_STABLE')
    cooldown=min(float(p.max_cooldown_seconds),float(p.base_cooldown_seconds)*(1.0+9.0*severity))
    backoff=(allowed/requested if requested>0 else 0.0)
    if allowed<float(p.min_operational_rate):
        return RateLimitResult(Decision.HOLD,NextAction.LOW_RATE_HOLD_CANDIDATE,escalation if escalation!=Escalation.NONE else Escalation.HIGH_RISK,tuple(reasons+['BELOW_MIN_OPERATIONAL_RATE']),requested,allowed,cap,backoff,cooldown,crit,stable,completeness,req.high_risk_action,False)
    return RateLimitResult(Decision.ALLOW,next_action,escalation,tuple(reasons+['RATE_CANDIDATE_ONLY']),requested,allowed,cap,backoff,cooldown,crit,stable,completeness,req.high_risk_action,True)

def _fingerprints(req:RateLimitRequest):
    ordered=_ordered(req)
    wf=tuple((w.window_id,_fp(w)) for w in ordered)
    ctx=_fp((req.request_id,req.binding,req.state_epoch,req.high_risk_action))
    metrics=_fp(tuple((w.window_id,w.action_rate,w.risk,w.error_rate,w.system_load,w.trust,w.critical_error) for w in ordered))
    pol=_fp(req.policy); reg=_fp(wf)
    return wf,ctx,metrics,pol,reg

def prepare_state(req:RateLimitRequest,*,binding:str,state_epoch:str)->PreparedRateState:
    if binding!=req.binding or state_epoch!=req.state_epoch: raise ValueError('BINDING_MISMATCH')
    err=_validate(req)
    if err: raise ValueError(err)
    wf,ctx,metrics,pol,reg=_fingerprints(req); result=evaluate(req); lf=_fp(result)
    return PreparedRateState(req,wf,ctx,metrics,pol,reg,lf,result,binding,state_epoch)

def validate_prepared_integrity(st:PreparedRateState)->bool:
    try:
        if not isinstance(st,PreparedRateState): return False
        if st.binding!=st.request.binding or st.state_epoch!=st.request.state_epoch: return False
        wf,ctx,metrics,pol,reg=_fingerprints(st.request)
        return (wf,ctx,metrics,pol,reg,_fp(st.precomputed_result))==(st.window_fingerprints,st.context_fingerprint,st.metrics_fingerprint,st.policy_fingerprint,st.registry_fingerprint,st.limiter_fingerprint)
    except Exception: return False

def evaluate_prepared(st:PreparedRateState,*,integrity_validated:bool,current_context_fingerprint:str,current_metrics_fingerprint:str,current_policy_fingerprint:str,current_registry_fingerprint:str,current_limiter_fingerprint:str)->RateLimitResult:
    if not integrity_validated: return _hold('PREPARED_INTEGRITY_NOT_VALIDATED',escalation=Escalation.INVALID_CONFIGURATION,high=getattr(st.request,'high_risk_action',False))
    if (current_context_fingerprint,current_metrics_fingerprint,current_policy_fingerprint,current_registry_fingerprint,current_limiter_fingerprint)!=(st.context_fingerprint,st.metrics_fingerprint,st.policy_fingerprint,st.registry_fingerprint,st.limiter_fingerprint):
        return _hold('PREPARED_FINGERPRINT_MISMATCH',escalation=Escalation.INVALID_CONFIGURATION,high=st.request.high_risk_action)
    return st.precomputed_result

def make_delta(base:PreparedRateState,target:PreparedRateState)->RateStateDelta:
    bm={w.window_id:_fp(w) for w in base.request.windows}; tm={w.window_id:_fp(w) for w in target.request.windows}
    changed=tuple(w for w in _ordered(target.request) if bm.get(w.window_id)!=tm.get(w.window_id))
    removed=tuple(sorted(set(bm)-set(tm)))
    pr=None if base.policy_fingerprint==target.policy_fingerprint else target.request.policy
    hr=None if base.request.high_risk_action==target.request.high_risk_action else target.request.high_risk_action
    return RateStateDelta(base.registry_fingerprint,target.registry_fingerprint,changed,removed,pr,hr,target.binding,target.state_epoch)

def plan_missing_only(base:PreparedRateState,target:PreparedRateState)->RateSyncPlan:
    d=make_delta(base,target)
    ids=tuple([f'WINDOW:{w.window_id}' for w in d.changed_windows]+[f'REMOVE:{i}' for i in d.removed_window_ids])
    meta=len(_canon({'base':d.base_registry_fingerprint,'target':d.target_registry_fingerprint,'policy':d.policy_replacement is not None,'risk_flag':d.high_risk_action_replacement is not None}))
    full=False
    return RateSyncPlan(ids,meta,full)

def default_request()->RateLimitRequest:
    b='AL115-DEFAULT-BINDING'; e='AL115-EPOCH-1'
    vals=[
        (0,20.0,0.18,0.06,0.42,0.86,False),
        (1,20.0,0.17,0.05,0.40,0.87,False),
        (2,20.0,0.16,0.05,0.39,0.88,False),
        (3,20.0,0.15,0.04,0.38,0.89,False),
        (4,20.0,0.14,0.04,0.37,0.90,False),
        (5,20.0,0.13,0.03,0.36,0.91,False),
    ]
    ws=tuple(RateWindow(i,r,risk,err,load,trust,crit,'V1',f'FP-{i}',b,e) for i,r,risk,err,load,trust,crit in vals)
    p=RatePolicy(100.0,0.25,0.10,0.85,3,0.70,0.40,0.25,0.35,0.25,0.20,0.20,3,0.10,1.0,60.0)
    return RateLimitRequest('AL115-DEFAULT',ws,False,p,b,e)

def default_evaluation(): return evaluate(default_request())
