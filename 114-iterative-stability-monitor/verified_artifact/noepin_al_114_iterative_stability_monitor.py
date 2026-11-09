"""NOEPIN AL 114 — Iterative Stability Monitor — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Pure deterministic evidence monitor for iterative processes. It evaluates typed goal-distance
and error histories using bounded trend, positive CUSUM, change-span and alternating/period-2
signals. The result classifies the observed iteration evidence as CONVERGING, STABLE,
OSCILLATING, DIVERGING, or UNKNOWN and returns only a Continue / Replan / Stop Hint
candidate. It never stops an external process, grants permission, executes an action, or
promotes observed metrics to World Truth, Safety Proof, or Action Success.

Canonical identity: NOEPIN-AL-114
DCSR level: AUXILIARY INTEGRATION / 補助統合.
Provenance note: exact registered Origin GUID was not freshly reverified in this
completion session and is intentionally not guessed or regenerated.
Pre-existing Notion V1 attachment byte identity was not freshly reverified.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
from hashlib import sha256
import json, math, statistics

class Decision(str, Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class StabilityClass(str, Enum):
    CONVERGING='CONVERGING'; STABLE='STABLE'; OSCILLATING='OSCILLATING'; DIVERGING='DIVERGING'; UNKNOWN='UNKNOWN'
class NextAction(str, Enum):
    CONTINUE_CANDIDATE='CONTINUE_CANDIDATE'
    MONITOR_CONTINUE_CANDIDATE='MONITOR_CONTINUE_CANDIDATE'
    REPLAN_CANDIDATE='REPLAN_CANDIDATE'
    STOP_HINT_CANDIDATE='STOP_HINT_CANDIDATE'
    STOP_REPLAN_HINT_CANDIDATE='STOP_REPLAN_HINT_CANDIDATE'
    HOLD_REVIEW_CANDIDATE='HOLD_REVIEW_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; INSUFFICIENT_EVIDENCE='INSUFFICIENT_EVIDENCE'; STAGNATION_LIMIT='STAGNATION_LIMIT'; OSCILLATION='OSCILLATION'; DIVERGENCE='DIVERGENCE'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'

@dataclass(frozen=True)
class IterationSample:
    step: int
    goal_distance: float
    error_metric: float
    state_fingerprint: str
    action_id: str
    sample_version: str
    sample_fingerprint: str
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class StabilityPolicy:
    min_samples: int
    trend_window: int
    max_iterations: int
    convergence_slope_threshold: float
    divergence_slope_threshold: float
    stable_delta_threshold: float
    oscillation_min_alternations: int
    oscillation_amplitude_threshold: float
    cusum_threshold: float

@dataclass(frozen=True)
class StabilityRequest:
    request_id: str
    samples: tuple[IterationSample,...]
    policy: StabilityPolicy
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class StabilityResult:
    decision: Decision
    stability: StabilityClass
    next_action: NextAction
    escalation: Escalation
    reasons: tuple[str,...]
    sample_count: int
    latest_step: int|None
    trend_slope: float|None
    recent_mean_delta: float|None
    positive_cusum: float|None
    alternating_transitions: int
    periodicity_score: float|None
    stop_hint: bool
    replan_hint: bool
    next_gate_candidate: bool
    stop_hint_promoted_to_stop_execution: bool=False
    replan_hint_promoted_to_permission: bool=False
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
class PreparedStabilityState:
    request: StabilityRequest
    sample_fingerprints: tuple[tuple[int,str],...]
    context_fingerprint: str
    history_fingerprint: str
    policy_fingerprint: str
    registry_fingerprint: str
    analysis_fingerprint: str
    precomputed_result: StabilityResult
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class StabilityStateDelta:
    base_registry_fingerprint: str
    target_registry_fingerprint: str
    changed_samples: tuple[IterationSample,...]
    removed_steps: tuple[int,...]
    policy_replacement: StabilityPolicy|None
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class StabilitySyncPlan:
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
def _hold(reason, escalation=Escalation.INVALID_CONFIGURATION, count=0, latest=None):
    return StabilityResult(Decision.HOLD,StabilityClass.UNKNOWN,NextAction.HOLD_REVIEW_CANDIDATE,escalation,(reason,),count,latest,None,None,None,0,None,False,False,False)

def _validate(req:StabilityRequest):
    if not isinstance(req,StabilityRequest): return 'TYPE_INVALID'
    if not req.request_id or not req.binding or not req.state_epoch: return 'REQUEST_INVALID'
    p=req.policy
    if not isinstance(p,StabilityPolicy): return 'POLICY_INVALID'
    ints=(p.min_samples,p.trend_window,p.max_iterations,p.oscillation_min_alternations)
    if any(not isinstance(x,int) or isinstance(x,bool) or x<=0 for x in ints): return 'POLICY_INTEGER_INVALID'
    if p.min_samples<3 or p.trend_window<p.min_samples or p.max_iterations<p.min_samples: return 'POLICY_WINDOW_INVALID'
    vals=(p.convergence_slope_threshold,p.divergence_slope_threshold,p.stable_delta_threshold,p.oscillation_amplitude_threshold,p.cusum_threshold)
    if any(not _finite(x) or float(x)<0 for x in vals): return 'POLICY_THRESHOLD_INVALID'
    if not req.samples: return None
    steps=[]
    for s in req.samples:
        if not isinstance(s,IterationSample): return 'SAMPLE_TYPE_INVALID'
        if not isinstance(s.step,int) or isinstance(s.step,bool) or s.step<0: return 'SAMPLE_STEP_INVALID'
        if not _finite(s.goal_distance) or not _finite(s.error_metric) or s.goal_distance<0 or s.error_metric<0: return 'SAMPLE_METRIC_INVALID'
        if not s.state_fingerprint or not s.action_id or not s.sample_version or not s.sample_fingerprint: return 'SAMPLE_IDENTITY_INVALID'
        if s.binding!=req.binding or s.state_epoch!=req.state_epoch: return 'SAMPLE_BINDING_INVALID'
        steps.append(s.step)
    if len(steps)!=len(set(steps)): return 'DUPLICATE_SAMPLE_STEP'
    return None

def _ordered(req:StabilityRequest): return tuple(sorted(req.samples,key=lambda s:s.step))
def _composite(s:IterationSample): return (float(s.goal_distance)+float(s.error_metric))/2.0

def _slope(vals:tuple[float,...]):
    n=len(vals)
    if n<2: return 0.0
    xm=(n-1)/2.0; ym=sum(vals)/n
    den=sum((i-xm)**2 for i in range(n))
    if den==0: return 0.0
    return sum((i-xm)*(vals[i]-ym) for i in range(n))/den

def _positive_cusum(vals:tuple[float,...]):
    if len(vals)<2: return 0.0
    diffs=[vals[i]-vals[i-1] for i in range(1,len(vals))]
    baseline=statistics.median(diffs)
    c=0.0; mx=0.0
    for d in diffs:
        c=max(0.0,c+(d-min(baseline,0.0)))
        mx=max(mx,c)
    return mx

def _alternations(vals:tuple[float,...], eps:float):
    if len(vals)<3: return 0
    signs=[]
    for i in range(1,len(vals)):
        d=vals[i]-vals[i-1]
        if abs(d)<=eps: signs.append(0)
        else: signs.append(1 if d>0 else -1)
    nz=[s for s in signs if s]
    return sum(1 for a,b in zip(nz,nz[1:]) if a!=b)

def _periodicity_score(vals:tuple[float,...]):
    if len(vals)<4: return 0.0
    span=max(vals)-min(vals)
    if span<=0: return 0.0
    diffs=[abs(vals[i]-vals[i-2]) for i in range(2,len(vals))]
    return max(0.0,1.0-(sum(diffs)/len(diffs))/span)

def evaluate(req:StabilityRequest)->StabilityResult:
    err=_validate(req)
    if err: return _hold(err,count=len(req.samples),latest=max((s.step for s in req.samples),default=None))
    ordered=_ordered(req); n=len(ordered); p=req.policy
    latest=ordered[-1].step if ordered else None
    if n<p.min_samples:
        return _hold('INSUFFICIENT_SAMPLES',Escalation.INSUFFICIENT_EVIDENCE,n,latest)
    recent=ordered[-min(p.trend_window,n):]
    vals=tuple(_composite(s) for s in recent)
    deltas=tuple(vals[i]-vals[i-1] for i in range(1,len(vals)))
    slope=_slope(vals); mean_delta=sum(deltas)/len(deltas) if deltas else 0.0
    cusum=_positive_cusum(vals); alt=_alternations(vals,float(p.stable_delta_threshold)); periodicity=_periodicity_score(vals)
    amplitude=max(vals)-min(vals)
    # Safety-side precedence: strong positive trend or accumulated positive excursion -> divergence.
    if slope>=float(p.divergence_slope_threshold) or cusum>=float(p.cusum_threshold):
        return StabilityResult(Decision.HOLD,StabilityClass.DIVERGING,NextAction.STOP_REPLAN_HINT_CANDIDATE,Escalation.DIVERGENCE,('DIVERGENCE_DETECTED','AUTO_CONTINUE_BLOCKED'),n,latest,slope,mean_delta,cusum,alt,periodicity,True,True,False)
    # Persistent alternating direction with material amplitude and period-2 resemblance -> oscillation.
    if alt>=p.oscillation_min_alternations and amplitude>=float(p.oscillation_amplitude_threshold) and periodicity>=0.55:
        return StabilityResult(Decision.HOLD,StabilityClass.OSCILLATING,NextAction.REPLAN_CANDIDATE,Escalation.OSCILLATION,('PERIODIC_OSCILLATION_DETECTED','AUTO_CONTINUE_BLOCKED'),n,latest,slope,mean_delta,cusum,alt,periodicity,False,True,False)
    # Stable/flat evidence. Reaching bounded iteration limit produces Stop Hint, not Stop Execution.
    if max((abs(d) for d in deltas),default=0.0)<=float(p.stable_delta_threshold):
        if n>=p.max_iterations or (latest is not None and latest>=p.max_iterations-1):
            return StabilityResult(Decision.HOLD,StabilityClass.STABLE,NextAction.STOP_HINT_CANDIDATE,Escalation.STAGNATION_LIMIT,('STAGNATION_ITERATION_LIMIT','STOP_HINT_ONLY'),n,latest,slope,mean_delta,cusum,alt,periodicity,True,False,False)
        return StabilityResult(Decision.ALLOW,StabilityClass.STABLE,NextAction.MONITOR_CONTINUE_CANDIDATE,Escalation.NONE,('STABLE_WITHIN_ITERATION_BOUND','CONTINUE_MONITORING'),n,latest,slope,mean_delta,cusum,alt,periodicity,False,False,True)
    if slope<=-float(p.convergence_slope_threshold) and mean_delta<0:
        return StabilityResult(Decision.ALLOW,StabilityClass.CONVERGING,NextAction.CONTINUE_CANDIDATE,Escalation.NONE,('CONVERGENCE_TREND','AUTO_STOP_NOT_EXECUTED'),n,latest,slope,mean_delta,cusum,alt,periodicity,False,False,True)
    return StabilityResult(Decision.HOLD,StabilityClass.UNKNOWN,NextAction.HOLD_REVIEW_CANDIDATE,Escalation.INSUFFICIENT_EVIDENCE,('TREND_UNRESOLVED','AUTO_CONTINUE_BLOCKED'),n,latest,slope,mean_delta,cusum,alt,periodicity,False,False,False)

def _fingerprints(req:StabilityRequest):
    ordered=_ordered(req)
    sf=tuple((s.step,s.sample_fingerprint) for s in ordered)
    ctx=_fp((req.request_id,req.binding,req.state_epoch))
    hist=_fp(tuple((s.step,s.goal_distance,s.error_metric,s.state_fingerprint,s.action_id,s.sample_version,s.sample_fingerprint) for s in ordered))
    pol=_fp(req.policy); reg=_fp(sf)
    return sf,ctx,hist,pol,reg

def prepare_state(req:StabilityRequest,*,binding:str,state_epoch:str)->PreparedStabilityState:
    if binding!=req.binding or state_epoch!=req.state_epoch: raise ValueError('PREPARE_BINDING_EPOCH_MISMATCH')
    err=_validate(req)
    if err: raise ValueError(err)
    sf,ctx,hist,pol,reg=_fingerprints(req); result=evaluate(req); af=_fp(result)
    return PreparedStabilityState(req,sf,ctx,hist,pol,reg,af,result,binding,state_epoch)

def validate_prepared_integrity(st:PreparedStabilityState)->bool:
    try:
        if not isinstance(st,PreparedStabilityState): return False
        if st.binding!=st.request.binding or st.state_epoch!=st.request.state_epoch: return False
        sf,ctx,hist,pol,reg=_fingerprints(st.request)
        return (sf,ctx,hist,pol,reg,_fp(st.precomputed_result))==(st.sample_fingerprints,st.context_fingerprint,st.history_fingerprint,st.policy_fingerprint,st.registry_fingerprint,st.analysis_fingerprint)
    except Exception: return False

def evaluate_prepared(st:PreparedStabilityState,*,integrity_validated:bool,current_context_fingerprint:str,current_history_fingerprint:str,current_policy_fingerprint:str,current_registry_fingerprint:str,current_analysis_fingerprint:str)->StabilityResult:
    if not integrity_validated: return _hold('PREPARED_INTEGRITY_NOT_VALIDATED')
    expected=(st.context_fingerprint,st.history_fingerprint,st.policy_fingerprint,st.registry_fingerprint,st.analysis_fingerprint)
    current=(current_context_fingerprint,current_history_fingerprint,current_policy_fingerprint,current_registry_fingerprint,current_analysis_fingerprint)
    if current!=expected: return _hold('PREPARED_FINGERPRINT_MISMATCH')
    return st.precomputed_result

def make_delta(base:PreparedStabilityState,target:PreparedStabilityState)->StabilityStateDelta:
    bs={s.step:s for s in base.request.samples}; ts={s.step:s for s in target.request.samples}
    changed=tuple(ts[k] for k in sorted(ts) if k not in bs or _fp(ts[k])!=_fp(bs[k]))
    removed=tuple(sorted(k for k in bs if k not in ts))
    policy=None if _fp(base.request.policy)==_fp(target.request.policy) else target.request.policy
    return StabilityStateDelta(base.registry_fingerprint,target.registry_fingerprint,changed,removed,policy,target.binding,target.state_epoch)

def plan_missing_only(base:PreparedStabilityState,target:PreparedStabilityState)->StabilitySyncPlan:
    d=make_delta(base,target); ids=[f'SAMPLE:{s.step}' for s in d.changed_samples]+[f'SAMPLE:{k}' for k in d.removed_steps]
    if d.policy_replacement is not None: ids.append('POLICY')
    metadata=len(_canon((d.base_registry_fingerprint,d.target_registry_fingerprint,d.binding,d.state_epoch)))
    return StabilitySyncPlan(tuple(sorted(ids)),metadata,False)

def default_request()->StabilityRequest:
    b='NOEPIN-AL-114-DEFAULT'; e='EPOCH-1'
    vals=(10.0,8.6,7.1,5.9,4.5,3.2,2.1,1.3)
    samples=tuple(IterationSample(i,v,v*0.5,f'STATE-{i}',f'ACTION-{i}','V1',f'FP-S-{i}',b,e) for i,v in enumerate(vals))
    p=StabilityPolicy(min_samples=5,trend_window=8,max_iterations=20,convergence_slope_threshold=0.05,divergence_slope_threshold=0.08,stable_delta_threshold=0.02,oscillation_min_alternations=4,oscillation_amplitude_threshold=0.5,cusum_threshold=2.0)
    return StabilityRequest('REQ-114-DEFAULT',samples,p,b,e)

def default_evaluation(): return evaluate(default_request())

__all__=['Decision','StabilityClass','NextAction','Escalation','IterationSample','StabilityPolicy','StabilityRequest','StabilityResult','PreparedStabilityState','StabilityStateDelta','StabilitySyncPlan','evaluate','prepare_state','validate_prepared_integrity','evaluate_prepared','make_delta','plan_missing_only','default_request','default_evaluation','_canon','_fp']
