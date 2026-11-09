"""NOEPIN AL 109 — Deadline-Aware Safe Scheduler — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Pure deterministic scheduling evidence. The scheduler builds and validates a dependency
DAG, preserves mandatory safety/verification tasks, computes critical-path information,
and orders ready tasks with deadline slack and risk-aware verification priority. If a
deadline is infeasible, it never deletes required safety work to manufacture a feasible
schedule; it emits HUMAN_APPROVAL candidate evidence instead. Returned schedule evidence
never grants permission, executes tasks, commits/publishes, proves safety/world truth, or
establishes action success.

Canonical identity: NOEPIN-AL-109
DCSR level: AUXILIARY INTEGRATION / 補助統合.
Provenance note: exact registered Origin GUID was not freshly reverified in this
completion session and is intentionally not guessed or regenerated.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, IntEnum
from hashlib import sha256
import json, math, heapq

class Decision(str, Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class RiskClass(IntEnum): LOW=0; MEDIUM=1; HIGH=2; CRITICAL=3
class Escalation(str, Enum):
    NONE='NONE'; DEADLINE_TIGHT_CANDIDATE='DEADLINE_TIGHT_CANDIDATE'; HUMAN_REVIEW_CANDIDATE='HUMAN_REVIEW_CANDIDATE'; REPLAN_CANDIDATE='REPLAN_CANDIDATE'
class NextAction(str, Enum):
    SAFE_SCHEDULE_CANDIDATE='SAFE_SCHEDULE_CANDIDATE'
    HUMAN_REVIEW_CANDIDATE='HUMAN_REVIEW_CANDIDATE'
    HOLD_REPLAN_CANDIDATE='HOLD_REPLAN_CANDIDATE'

@dataclass(frozen=True)
class TaskRecord:
    task_id:str; duration_estimate:float; dependencies:tuple[str,...]; risk:float
    mandatory_safety:bool; verification_step:bool; critical_step:bool
    hard_constraint_passed:bool; policy_allowed:bool; observed:bool
    task_version:str; task_fingerprint:str; binding:str; state_epoch:str

@dataclass(frozen=True)
class ScheduleRequest:
    request_id:str; start_time:float; deadline:float; risk_class:RiskClass
    requested_omissions:tuple[str,...]; observed:bool; binding:str; state_epoch:str

@dataclass(frozen=True)
class SchedulePolicy:
    low_risk_cap:float; medium_risk_cap:float; high_risk_cap:float; critical_risk_cap:float
    tight_slack_fraction:float; critical_verification_risk_threshold:float; max_tasks:int
    require_hard_constraints:bool; require_policy_allowed:bool; binding:str; state_epoch:str; revoked:bool=False

@dataclass(frozen=True)
class ScheduledTask:
    task_id:str; start_time:float; end_time:float; duration:float; risk:float
    mandatory_safety:bool; verification_step:bool; slack_at_dispatch:float

@dataclass(frozen=True)
class ScheduleResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; reasons:tuple[str,...]
    safe_schedule:tuple[ScheduledTask,...]; critical_path:tuple[str,...]
    missed_deadline_risk:float; final_finish_time:float|None; deadline_feasible:bool
    required_safety_preserved:bool; omitted_tasks:tuple[str,...]; next_gate_candidate:bool
    schedule_promoted_to_permission:bool=False; permission_granted:bool=False; authority_granted:bool=False
    action_executed:bool=False; plan_committed:bool=False; atomic_publish_executed:bool=False
    external_write_performed:bool=False; world_truth_proven:bool=False; domain_authority_promoted:bool=False
    safety_proven:bool=False; action_success:bool=False

@dataclass(frozen=True)
class PreparedScheduleState:
    request:ScheduleRequest; tasks:tuple[TaskRecord,...]; policy:SchedulePolicy
    record_fingerprints:tuple[tuple[str,str],...]; context_fingerprint:str; dependency_fingerprint:str
    policy_fingerprint:str; registry_fingerprint:str; frontier_fingerprint:str; schedule_fingerprint:str
    precomputed_result:ScheduleResult; binding:str; state_epoch:str

@dataclass(frozen=True)
class ScheduleStateDelta:
    base_fingerprint:str; target_fingerprint:str; changed_tasks:tuple[TaskRecord,...]; removed_record_ids:tuple[str,...]
    target_request:ScheduleRequest|None; target_policy:SchedulePolicy|None; binding:str; state_epoch:str

@dataclass(frozen=True)
class ScheduleSyncPlan:
    missing_or_changed_record_ids:tuple[str,...]; metadata_bytes_required:int; full_resend_required:bool

def _cv(x):
    if isinstance(x,Enum): return x.name if isinstance(x,IntEnum) else x.value
    if hasattr(x,'__dataclass_fields__'): return {k:_cv(getattr(x,k)) for k in x.__dataclass_fields__}
    if isinstance(x,tuple): return [_cv(v) for v in x]
    if isinstance(x,list): return [_cv(v) for v in x]
    if isinstance(x,dict): return {str(k):_cv(x[k]) for k in sorted(x)}
    return x

def _canon(x)->bytes: return json.dumps(_cv(x),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def _fp(x)->str: return sha256(_canon(x)).hexdigest()
def _risk_cap(r,p): return {RiskClass.LOW:p.low_risk_cap,RiskClass.MEDIUM:p.medium_risk_cap,RiskClass.HIGH:p.high_risk_cap,RiskClass.CRITICAL:p.critical_risk_cap}[r]

def _hold(reason, *, escalation=Escalation.REPLAN_CANDIDATE, omitted=()):
    return ScheduleResult(Decision.HOLD,NextAction.HOLD_REPLAN_CANDIDATE,escalation,(reason,),(),(),1.0,None,False,False,tuple(sorted(omitted)),False)

def _validate(q,tasks,p):
    if p.revoked: return 'POLICY_REVOKED'
    if not q.observed or not q.request_id: return 'REQUEST_INVALID'
    if q.binding!=p.binding or q.state_epoch!=p.state_epoch: return 'SCOPE_MISMATCH'
    nums=(q.start_time,q.deadline,p.low_risk_cap,p.medium_risk_cap,p.high_risk_cap,p.critical_risk_cap,p.tight_slack_fraction,p.critical_verification_risk_threshold)
    if any(not math.isfinite(v) for v in nums): return 'NUMERIC_INVALID'
    if q.deadline<=q.start_time: return 'DEADLINE_INVALID'
    if not (p.low_risk_cap>=p.medium_risk_cap>=p.high_risk_cap>=p.critical_risk_cap>=0): return 'POLICY_RISK_CAP_NONMONOTONIC'
    if not (0<=p.tight_slack_fraction<=1) or p.critical_verification_risk_threshold<0 or p.max_tasks<=0: return 'POLICY_INVALID'
    if len(tasks)==0 or len(tasks)>p.max_tasks: return 'TASK_COUNT_INVALID'
    ids=[x.task_id for x in tasks]
    if len(ids)!=len(set(ids)): return 'DUPLICATE_TASK_ID'
    idset=set(ids)
    for x in tasks:
        if not x.observed or not x.task_id or not x.task_version or not x.task_fingerprint: return 'TASK_INVALID'
        if x.binding!=p.binding or x.state_epoch!=p.state_epoch: return 'TASK_SCOPE_MISMATCH'
        if not math.isfinite(x.duration_estimate) or not math.isfinite(x.risk) or x.duration_estimate<=0 or x.risk<0: return 'TASK_NUMERIC_INVALID'
        if x.task_id in x.dependencies: return 'SELF_DEPENDENCY'
        if any(d not in idset for d in x.dependencies): return 'MISSING_DEPENDENCY'
    if any(x not in idset for x in q.requested_omissions): return 'UNKNOWN_OMISSION_REQUEST'
    return None

def _topological(tasks):
    by={x.task_id:x for x in tasks}; indeg={x.task_id:0 for x in tasks}; out={x.task_id:[] for x in tasks}
    for x in tasks:
        for d in x.dependencies:
            indeg[x.task_id]+=1; out[d].append(x.task_id)
    ready=sorted(k for k,v in indeg.items() if v==0); order=[]
    while ready:
        n=ready.pop(0); order.append(n)
        for y in sorted(out[n]):
            indeg[y]-=1
            if indeg[y]==0:
                ready.append(y); ready.sort()
    return tuple(order) if len(order)==len(tasks) else None

def _critical_remaining(tasks, topo):
    by={x.task_id:x for x in tasks}; children={x.task_id:[] for x in tasks}
    for x in tasks:
        for d in x.dependencies: children[d].append(x.task_id)
    rem={}
    for tid in reversed(topo):
        tail=max((rem[c] for c in children[tid]),default=0.0)
        rem[tid]=by[tid].duration_estimate+tail
    return rem,children

def _critical_path(tasks, topo, rem, children):
    roots=[x.task_id for x in tasks if not x.dependencies]
    if not roots: return ()
    cur=max(sorted(roots),key=lambda t:(rem[t],t)); path=[cur]
    while children[cur]:
        cur=max(sorted(children[cur]),key=lambda t:(rem[t],t)); path.append(cur)
    return tuple(path)

def evaluate(q:ScheduleRequest,tasks:tuple[TaskRecord,...],p:SchedulePolicy)->ScheduleResult:
    tasks=tuple(tasks); err=_validate(q,tasks,p)
    if err: return _hold(err)
    topo=_topological(tasks)
    if topo is None: return _hold('DEPENDENCY_CYCLE')
    by={x.task_id:x for x in tasks}; omitted=set(q.requested_omissions)
    required_safety={x.task_id for x in tasks if x.mandatory_safety}
    unsafe_omissions=required_safety & omitted
    if unsafe_omissions: return _hold('MANDATORY_SAFETY_OMISSION_FORBIDDEN',omitted=unsafe_omissions)
    # This scheduler never silently drops normal tasks either; omission requests must be handled upstream by replanning.
    if omitted: return _hold('TASK_OMISSION_REQUIRES_REPLAN',omitted=omitted)
    cap=_risk_cap(q.risk_class,p)
    for x in tasks:
        if p.require_hard_constraints and not x.hard_constraint_passed: return _hold(f'HARD_CONSTRAINT:{x.task_id}')
        if p.require_policy_allowed and not x.policy_allowed: return _hold(f'POLICY_DENIED:{x.task_id}')
        if x.risk>cap: return _hold(f'RISK_LIMIT:{x.task_id}')
    rem,children=_critical_remaining(tasks,topo); cpath=_critical_path(tasks,topo,rem,children)
    window=q.deadline-q.start_time; total_duration=sum(x.duration_estimate for x in tasks)
    # Single-executor safe schedule model: all required tasks must fit; never delete safety work to fake feasibility.
    deadline_feasible=total_duration<=window+1e-12
    done=set(); now=q.start_time; schedule=[]; reasons=[]
    indeg={x.task_id:len(x.dependencies) for x in tasks}
    def ready_key(x):
        critical_verify=(x.critical_step and x.verification_step and x.risk>=p.critical_verification_risk_threshold)
        # slack = deadline-now-critical_remaining; at a fixed dispatch instant, smaller slack means larger remaining critical path.
        return (0 if critical_verify else 1, -rem[x.task_id], 0 if x.mandatory_safety else 1, -x.risk, x.task_id)
    ready=[]
    for x in tasks:
        if indeg[x.task_id]==0: heapq.heappush(ready,(ready_key(x),x.task_id))
    while len(done)<len(tasks):
        if not ready: return _hold('SCHEDULER_STALLED')
        _k,tid=heapq.heappop(ready); x=by[tid]; slack=q.deadline-now-rem[x.task_id]
        schedule.append(ScheduledTask(x.task_id,now,now+x.duration_estimate,x.duration_estimate,x.risk,x.mandatory_safety,x.verification_step,slack))
        now+=x.duration_estimate; done.add(x.task_id)
        if x.critical_step and x.verification_step and x.risk>=p.critical_verification_risk_threshold:
            reasons.append('CRITICAL_HIGH_RISK_VERIFICATION_PRIORITIZED')
        for child in children[x.task_id]:
            indeg[child]-=1
            if indeg[child]==0: heapq.heappush(ready,(ready_key(by[child]),child))
    finish=now; slack=max(0.0,q.deadline-finish); utilization=min(1.0,total_duration/window) if window>0 else 1.0
    maxrisk=max(x.risk for x in tasks); risk_component=min(1.0,maxrisk/max(cap,1e-12)) if cap>0 else (1.0 if maxrisk>0 else 0.0)
    missed=min(1.0,0.8*utilization+0.2*risk_component)
    preserved=required_safety.issubset({x.task_id for x in schedule})
    if not preserved: return _hold('MANDATORY_SAFETY_NOT_PRESERVED')
    if not deadline_feasible or finish>q.deadline+1e-12:
        rs=tuple(dict.fromkeys(reasons+['DEADLINE_INFEASIBLE_NO_SAFETY_SKIP']))
        return ScheduleResult(Decision.HUMAN_APPROVAL,NextAction.HUMAN_REVIEW_CANDIDATE,Escalation.HUMAN_REVIEW_CANDIDATE,rs,tuple(schedule),cpath,1.0,finish,False,True,(),False)
    slack_fraction=slack/window
    if slack_fraction<=p.tight_slack_fraction:
        rs=tuple(dict.fromkeys(reasons+['DEADLINE_TIGHT_SAFETY_PRESERVED']))
        return ScheduleResult(Decision.HUMAN_APPROVAL,NextAction.HUMAN_REVIEW_CANDIDATE,Escalation.DEADLINE_TIGHT_CANDIDATE,rs,tuple(schedule),cpath,missed,finish,True,True,(),False)
    rs=tuple(dict.fromkeys(reasons+['SAFE_SCHEDULE_WITH_DEADLINE_SLACK']))
    return ScheduleResult(Decision.ALLOW,NextAction.SAFE_SCHEDULE_CANDIDATE,Escalation.NONE,rs,tuple(schedule),cpath,missed,finish,True,True,(),True)

def default_policy():
    return SchedulePolicy(4.0,3.0,2.0,1.2,.10,.75,10000,True,True,'DEADLINE-BIND','STATE-EPOCH-1')
def default_request():
    p=default_policy(); return ScheduleRequest('REQ-109',0.0,14.0,RiskClass.LOW,(),True,p.binding,p.state_epoch)
def default_tasks():
    p=default_policy(); b=p.binding; e=p.state_epoch
    return (
        TaskRecord('SECURITY-VERIFY',1.0,(),.9,True,True,True,True,True,True,'V1','FP-SEC',b,e),
        TaskRecord('PREPARE',2.0,(),.2,False,False,False,True,True,True,'V1','FP-PREP',b,e),
        TaskRecord('BUILD',3.0,('PREPARE','SECURITY-VERIFY'),.5,False,False,False,True,True,True,'V1','FP-BUILD',b,e),
        TaskRecord('TEST',2.0,('BUILD',),.7,True,True,False,True,True,True,'V1','FP-TEST',b,e),
        TaskRecord('PUBLISH',1.0,('TEST',),.6,False,False,False,True,True,True,'V1','FP-PUB',b,e),
    )
def default_evaluation(): return evaluate(default_request(),default_tasks(),default_policy())

def _record_fps(tasks): return tuple((f'TASK:{x.task_id}',_fp(x)) for x in sorted(tasks,key=lambda y:y.task_id))
def _context_fp(q): return _fp(q)
def _dependency_fp(tasks): return _fp(tuple((x.task_id,x.dependencies,x.task_version,x.task_fingerprint) for x in sorted(tasks,key=lambda y:y.task_id)))
def _policy_fp(p): return _fp(p)
def _registry_fp(q,tasks,p): return _fp((q,_record_fps(tasks),p))
def _frontier_fp(q,tasks): return _fp((q.deadline,q.start_time,q.risk_class,tuple((x.task_id,x.duration_estimate,x.dependencies,x.risk,x.mandatory_safety,x.verification_step,x.critical_step,x.hard_constraint_passed,x.policy_allowed) for x in sorted(tasks,key=lambda y:y.task_id))))
def _schedule_fp(q,tasks,p): return _fp((q.requested_omissions,p.tight_slack_fraction,p.critical_verification_risk_threshold,_risk_cap(q.risk_class,p),_dependency_fp(tasks)))

def prepare_state(q,tasks,p,*,binding,state_epoch):
    tasks=tuple(tasks); fps=_record_fps(tasks)
    return PreparedScheduleState(q,tasks,p,fps,_context_fp(q),_dependency_fp(tasks),_policy_fp(p),_registry_fp(q,tasks,p),_frontier_fp(q,tasks),_schedule_fp(q,tasks,p),evaluate(q,tasks,p),binding,state_epoch)
def validate_prepared_integrity(st):
    return (st.binding==st.request.binding==st.policy.binding and st.state_epoch==st.request.state_epoch==st.policy.state_epoch and
            st.record_fingerprints==_record_fps(st.tasks) and st.context_fingerprint==_context_fp(st.request) and
            st.dependency_fingerprint==_dependency_fp(st.tasks) and st.policy_fingerprint==_policy_fp(st.policy) and
            st.registry_fingerprint==_registry_fp(st.request,st.tasks,st.policy) and st.frontier_fingerprint==_frontier_fp(st.request,st.tasks) and
            st.schedule_fingerprint==_schedule_fp(st.request,st.tasks,st.policy) and st.precomputed_result==evaluate(st.request,st.tasks,st.policy))
def evaluate_prepared(st,*,integrity_validated,current_context_fingerprint,current_dependency_fingerprint,current_policy_fingerprint,current_registry_fingerprint,current_frontier_fingerprint,current_schedule_fingerprint):
    if not integrity_validated: return _hold('PREPARED_INTEGRITY_NOT_VALIDATED')
    if (st.context_fingerprint!=current_context_fingerprint or st.dependency_fingerprint!=current_dependency_fingerprint or
        st.policy_fingerprint!=current_policy_fingerprint or st.registry_fingerprint!=current_registry_fingerprint or
        st.frontier_fingerprint!=current_frontier_fingerprint or st.schedule_fingerprint!=current_schedule_fingerprint):
        return _hold('PREPARED_FINGERPRINT_MISMATCH_REEVALUATION_REQUIRED')
    return st.precomputed_result

def make_delta(base,target):
    bm=dict(base.record_fingerprints); tm=dict(target.record_fingerprints); mm={f'TASK:{x.task_id}':x for x in target.tasks}
    changed=tuple(mm[k] for k,v in tm.items() if bm.get(k)!=v); removed=tuple(k for k in bm if k not in tm)
    return ScheduleStateDelta(base.registry_fingerprint,target.registry_fingerprint,changed,removed,target.request if base.request!=target.request else None,target.policy if base.policy!=target.policy else None,target.binding,target.state_epoch)
def plan_missing_only(local,target):
    lm=dict(local.record_fingerprints); tm=dict(target.record_fingerprints); ids=tuple(k for k,v in tm.items() if lm.get(k)!=v)
    return ScheduleSyncPlan(ids,len(_canon(ids)),False)
