"""NOEPIN AL 090 — Partial-Failure Containment Manager — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Pure failure-containment decision algorithm. It computes a deterministic containment
closure from failed nodes, downstream dependencies and shared resources, then emits
safe branch-continuation / recovery candidates. It does not execute, stop, isolate,
compensate, grant permission, mutate locks/resources, commit/publish state, prove
World Truth/Safety, or establish Action Success.

Canonical identity: NOEPIN-AL-090
DCSR level: DIRECT INTEGRATION / 直接統合.
Provenance note: exact registered Origin GUID was not freshly reverified in this
completion session and is intentionally not guessed or regenerated.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json

class Decision(str,Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class RiskLevel(str,Enum):
    LOW='LOW'; MEDIUM='MEDIUM'; HIGH='HIGH'; CRITICAL='CRITICAL'
class StepState(str,Enum):
    PENDING='PENDING'; RUNNING='RUNNING'; SUCCESS='SUCCESS'; FAILED='FAILED'; UNKNOWN='UNKNOWN'
class ContainmentState(str,Enum):
    NO_FAILURE='NO_FAILURE'; SAFE_CONTINUE='SAFE_CONTINUE'; RECOVERY_REQUIRED='RECOVERY_REQUIRED'; FULL_STOP='FULL_STOP'; HOLD='HOLD'

_RISK={RiskLevel.LOW:0,RiskLevel.MEDIUM:1,RiskLevel.HIGH:2,RiskLevel.CRITICAL:3}

@dataclass(frozen=True)
class ExecutionStep:
    step_id:str; dependencies:tuple[str,...]; resources:tuple[str,...]; criticality:RiskLevel
    observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class StepStateRecord:
    step_id:str; state:StepState; failure_code:str; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class CompensationRecord:
    step_id:str; compensation_id:str; coverage:float; risk:RiskLevel; available:bool
    observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class ContainmentRequest:
    request_id:str; graph_id:str; blast_radius_known:bool; resource_map_complete:bool
    observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class ContainmentPolicy:
    min_compensation_coverage:float; max_compensation_risk:RiskLevel; critical_resources:tuple[str,...]
    allow_independent_continue:bool; binding:str; state_epoch:str; revoked:bool=False
@dataclass(frozen=True)
class ContainmentResult:
    decision:Decision; containment_state:ContainmentState; reasons:tuple[str,...]
    failed_step_ids:tuple[str,...]; containment_set:tuple[str,...]; continue_step_ids:tuple[str,...]
    stopped_step_ids:tuple[str,...]; recovery_plan:tuple[tuple[str,str],...]
    next_gate_candidate:bool; continue_candidate:bool; full_stop_candidate:bool; recovery_candidate:bool; incident_candidate:bool
    permission_granted:bool=False; action_executed:bool=False; branch_execution_started:bool=False
    isolation_executed:bool=False; compensation_executed:bool=False; resource_lock_mutated:bool=False
    plan_committed:bool=False; atomic_publish_executed:bool=False; external_write_performed:bool=False
    world_truth_proven:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedContainmentState:
    request:ContainmentRequest; steps:tuple[ExecutionStep,...]; states:tuple[StepStateRecord,...]
    compensations:tuple[CompensationRecord,...]; policy:ContainmentPolicy
    record_fingerprints:tuple[tuple[str,str],...]; context_fingerprint:str; dependency_fingerprint:str
    policy_fingerprint:str; registry_fingerprint:str; precomputed_result:ContainmentResult
    binding:str; state_epoch:str
@dataclass(frozen=True)
class ContainmentStateDelta:
    base_fingerprint:str; target_fingerprint:str
    changed_steps:tuple[ExecutionStep,...]; removed_step_ids:tuple[str,...]
    changed_states:tuple[StepStateRecord,...]; removed_state_ids:tuple[str,...]
    changed_compensations:tuple[CompensationRecord,...]; removed_compensation_ids:tuple[str,...]
    target_request:ContainmentRequest|None; target_policy:ContainmentPolicy|None
    binding:str; state_epoch:str
@dataclass(frozen=True)
class ContainmentSyncPlan:
    missing_or_changed_record_ids:tuple[str,...]; metadata_bytes_required:int; full_resend_required:bool

def _cv(x):
    if isinstance(x,Enum): return x.value
    if hasattr(x,'__dataclass_fields__'): return {k:_cv(getattr(x,k)) for k in x.__dataclass_fields__}
    if isinstance(x,tuple): return [_cv(v) for v in x]
    if isinstance(x,list): return [_cv(v) for v in x]
    if isinstance(x,dict): return {str(k):_cv(x[k]) for k in sorted(x)}
    return x
def _canon(x)->bytes: return json.dumps(_cv(x),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def _fp(x)->str: return sha256(_canon(x)).hexdigest()

def _result(decision,state,reasons,failed=(),containment=(),cont=(),stopped=(),recovery=(),next_gate=False,continue_candidate=False,full_stop=False,recovery_candidate=False,incident=False):
    return ContainmentResult(decision,state,tuple(reasons),tuple(failed),tuple(containment),tuple(cont),tuple(stopped),tuple(recovery),next_gate,continue_candidate,full_stop,recovery_candidate,incident)
def _hold(reason,steps=(),failed=(),full_stop=False,incident=False):
    ids=tuple(sorted(s.step_id for s in steps)) if full_stop else ()
    return _result(Decision.HOLD,ContainmentState.FULL_STOP if full_stop else ContainmentState.HOLD,(reason,),failed,ids,(),ids,(),False,False,full_stop,False,incident)

def _validate(req,steps,states,comps,policy):
    if policy.revoked: return 'POLICY_REVOKED'
    if req.binding!=policy.binding or req.state_epoch!=policy.state_epoch: return 'REQUEST_SCOPE_MISMATCH'
    if not req.request_id or not req.graph_id: return 'INCOMPLETE_REQUEST_IDENTITY'
    ids=[s.step_id for s in steps]
    if len(ids)!=len(set(ids)): return 'DUPLICATE_STEP_ID'
    sm={s.step_id:s for s in steps}
    if not sm: return 'EMPTY_EXECUTION_GRAPH'
    for s in steps:
        if s.binding!=policy.binding or s.state_epoch!=policy.state_epoch: return 'STEP_SCOPE_MISMATCH'
        if not s.step_id or not s.observed: return 'STEP_UNOBSERVED_OR_INVALID'
        if any(d not in sm for d in s.dependencies): return 'MISSING_DEPENDENCY'
    stids=[x.step_id for x in states]
    if len(stids)!=len(set(stids)): return 'DUPLICATE_STEP_STATE'
    if set(stids)!=set(ids): return 'STEP_STATE_COVERAGE_INCOMPLETE'
    for x in states:
        if x.binding!=policy.binding or x.state_epoch!=policy.state_epoch: return 'STEP_STATE_SCOPE_MISMATCH'
        if not x.observed: return 'STEP_STATE_UNOBSERVED'
    for c in comps:
        if c.step_id not in sm: return 'COMPENSATION_UNKNOWN_STEP'
        if c.binding!=policy.binding or c.state_epoch!=policy.state_epoch: return 'COMPENSATION_SCOPE_MISMATCH'
        if not (0.0<=c.coverage<=1.0): return 'COMPENSATION_COVERAGE_INVALID'
    # DAG cycle check
    visiting=set(); done=set()
    def visit(n):
        if n in done: return True
        if n in visiting: return False
        visiting.add(n)
        for d in sm[n].dependencies:
            if not visit(d): return False
        visiting.remove(n); done.add(n); return True
    if not all(visit(n) for n in sorted(sm)): return 'EXECUTION_GRAPH_CYCLE'
    return None

def evaluate(req:ContainmentRequest,steps:tuple[ExecutionStep,...],states:tuple[StepStateRecord,...],comps:tuple[CompensationRecord,...],policy:ContainmentPolicy)->ContainmentResult:
    steps=tuple(sorted(steps,key=lambda x:x.step_id)); states=tuple(sorted(states,key=lambda x:x.step_id)); comps=tuple(sorted(comps,key=lambda x:(x.step_id,x.compensation_id)))
    err=_validate(req,steps,states,comps,policy)
    if err: return _hold(err,steps)
    if not req.observed: return _hold('REQUEST_UNOBSERVED',steps)
    sm={s.step_id:s for s in steps}; stm={x.step_id:x for x in states}
    unknown=tuple(sorted(k for k,v in stm.items() if v.state==StepState.UNKNOWN))
    if unknown: return _hold('STEP_STATE_UNKNOWN',steps,unknown,full_stop=True,incident=True)
    failed=tuple(sorted(k for k,v in stm.items() if v.state==StepState.FAILED))
    if not failed:
        ready=tuple(sorted(s.step_id for s in steps if stm[s.step_id].state==StepState.PENDING and all(stm[d].state==StepState.SUCCESS for d in s.dependencies)))
        return _result(Decision.ALLOW,ContainmentState.NO_FAILURE,('NO_FAILED_STEP',),(),(),ready,(),(),True,bool(ready),False,False,False)
    if not req.blast_radius_known: return _hold('BLAST_RADIUS_UNKNOWN',steps,failed,full_stop=True,incident=True)
    if not req.resource_map_complete: return _hold('RESOURCE_MAP_INCOMPLETE',steps,failed,full_stop=True,incident=True)
    # dependent closure
    children={k:set() for k in sm}
    for s in steps:
        for d in s.dependencies: children[d].add(s.step_id)
    contained=set(failed)
    changed=True
    while changed:
        changed=False
        for x in list(contained):
            for c in children[x]:
                if c not in contained: contained.add(c); changed=True
        touched=set(r for sid in contained for r in sm[sid].resources)
        for s in steps:
            if s.step_id not in contained and touched.intersection(s.resources):
                contained.add(s.step_id); changed=True
    # Critical shared resource means global stop.
    for r in policy.critical_resources:
        users={s.step_id for s in steps if r in s.resources}
        if len(users)>1 and users.intersection(failed):
            return _hold('CRITICAL_SHARED_RESOURCE_AFFECTED',steps,failed,full_stop=True,incident=True)
    continue_ids=tuple(sorted(s.step_id for s in steps if s.step_id not in contained and stm[s.step_id].state==StepState.PENDING and all((d not in contained and stm[d].state==StepState.SUCCESS) for d in s.dependencies)))
    recovery=[]
    for sid in failed:
        candidates=[c for c in comps if c.step_id==sid and c.observed and c.available and c.coverage>=policy.min_compensation_coverage and _RISK[c.risk]<=_RISK[policy.max_compensation_risk]]
        if candidates:
            candidates.sort(key=lambda c:(-c.coverage,_RISK[c.risk],c.compensation_id))
            recovery.append((sid,candidates[0].compensation_id))
    containment=tuple(sorted(contained)); stopped=containment
    if continue_ids and policy.allow_independent_continue:
        reasons=['FAILED_BRANCH_CONTAINED','INDEPENDENT_BRANCH_AVAILABLE']
        if recovery: reasons.append('RECOVERY_PLAN_AVAILABLE')
        return _result(Decision.ALLOW,ContainmentState.SAFE_CONTINUE,reasons,failed,containment,continue_ids,stopped,tuple(recovery),True,True,False,bool(recovery),False)
    if recovery:
        return _result(Decision.HOLD,ContainmentState.RECOVERY_REQUIRED,('NO_SAFE_INDEPENDENT_BRANCH','RECOVERY_PLAN_AVAILABLE'),failed,containment,(),stopped,tuple(recovery),False,False,True,True,False)
    return _result(Decision.HOLD,ContainmentState.FULL_STOP,('NO_SAFE_INDEPENDENT_BRANCH','RECOVERY_NOT_ESTABLISHED'),failed,tuple(sorted(sm)),(),tuple(sorted(sm)),(),False,False,True,False,True)

def default_request(): return ContainmentRequest('REQ-90','GRAPH-90',True,True,True,'CONT-BIND','STATE-EPOCH-1')
def default_policy(): return ContainmentPolicy(0.8,RiskLevel.MEDIUM,('GLOBAL-LEDGER',),True,'CONT-BIND','STATE-EPOCH-1')
def default_steps():
    b,e='CONT-BIND','STATE-EPOCH-1'
    return (
      ExecutionStep('A',(),('DB-A',),RiskLevel.HIGH,True,b,e),
      ExecutionStep('B',('A',),('DB-A',),RiskLevel.MEDIUM,True,b,e),
      ExecutionStep('C',(),('QUEUE-C',),RiskLevel.LOW,True,b,e),
      ExecutionStep('D',('C',),('QUEUE-D',),RiskLevel.LOW,True,b,e),
    )
def default_states():
    b,e='CONT-BIND','STATE-EPOCH-1'
    return (
      StepStateRecord('A',StepState.FAILED,'ERR-A',True,b,e),StepStateRecord('B',StepState.PENDING,'',True,b,e),
      StepStateRecord('C',StepState.PENDING,'',True,b,e),StepStateRecord('D',StepState.PENDING,'',True,b,e),
    )
def default_compensations():
    return (CompensationRecord('A','COMP-A',1.0,RiskLevel.LOW,True,True,'CONT-BIND','STATE-EPOCH-1'),)
def default_evaluation(): return evaluate(default_request(),default_steps(),default_states(),default_compensations(),default_policy())

def _record_fps(steps,states,comps):
    rows=[]
    rows += [(f'STEP:{x.step_id}',_fp(x)) for x in sorted(steps,key=lambda x:x.step_id)]
    rows += [(f'STATE:{x.step_id}',_fp(x)) for x in sorted(states,key=lambda x:x.step_id)]
    rows += [(f'COMP:{x.step_id}:{x.compensation_id}',_fp(x)) for x in sorted(comps,key=lambda x:(x.step_id,x.compensation_id))]
    return tuple(rows)
def _registry_fp(req,steps,states,comps,policy): return _fp({'request':req,'steps':tuple(sorted(steps,key=lambda x:x.step_id)),'states':tuple(sorted(states,key=lambda x:x.step_id)),'compensations':tuple(sorted(comps,key=lambda x:(x.step_id,x.compensation_id))),'policy':policy})
def prepare_state(req,steps,states,comps,policy,*,binding,state_epoch):
    steps=tuple(sorted(steps,key=lambda x:x.step_id)); states=tuple(sorted(states,key=lambda x:x.step_id)); comps=tuple(sorted(comps,key=lambda x:(x.step_id,x.compensation_id)))
    fps=_record_fps(steps,states,comps); context=_fp({'request':req,'policy':policy}); dep=_fp({'records':fps}); pfp=_fp(policy); reg=_registry_fp(req,steps,states,comps,policy)
    return PreparedContainmentState(req,steps,states,comps,policy,fps,context,dep,pfp,reg,evaluate(req,steps,states,comps,policy),binding,state_epoch)
def validate_prepared_integrity(st):
    if st.binding!=st.policy.binding or st.state_epoch!=st.policy.state_epoch: return False
    if st.record_fingerprints!=_record_fps(st.steps,st.states,st.compensations): return False
    if st.context_fingerprint!=_fp({'request':st.request,'policy':st.policy}): return False
    if st.dependency_fingerprint!=_fp({'records':st.record_fingerprints}): return False
    if st.policy_fingerprint!=_fp(st.policy): return False
    if st.registry_fingerprint!=_registry_fp(st.request,st.steps,st.states,st.compensations,st.policy): return False
    return st.precomputed_result==evaluate(st.request,st.steps,st.states,st.compensations,st.policy)
def evaluate_prepared(st,*,current_context_fingerprint,current_dependency_fingerprint,current_policy_fingerprint,current_registry_fingerprint,prepared_integrity_validated):
    if not prepared_integrity_validated: return _hold('PREPARED_INTEGRITY_UNVERIFIED',st.steps)
    if (current_context_fingerprint,current_dependency_fingerprint,current_policy_fingerprint,current_registry_fingerprint)!=(st.context_fingerprint,st.dependency_fingerprint,st.policy_fingerprint,st.registry_fingerprint): return _hold('PREPARED_STATE_CHANGED_REEVALUATION_REQUIRED',st.steps)
    return st.precomputed_result

def _delta_collection(base_items,target_items,keyfn):
    bm={keyfn(x):x for x in base_items}; tm={keyfn(x):x for x in target_items}
    changed=tuple(tm[k] for k in sorted(tm) if k not in bm or _fp(tm[k])!=_fp(bm[k])); removed=tuple(k for k in sorted(bm) if k not in tm)
    return changed,removed
def make_delta(base,target):
    if base.binding!=target.binding or base.state_epoch!=target.state_epoch: raise ValueError('DELTA_SCOPE_MISMATCH')
    cs,rs=_delta_collection(base.steps,target.steps,lambda x:x.step_id); cst,rst=_delta_collection(base.states,target.states,lambda x:x.step_id); cc,rc=_delta_collection(base.compensations,target.compensations,lambda x:f'{x.step_id}:{x.compensation_id}')
    tr=target.request if _fp(base.request)!=_fp(target.request) else None; tp=target.policy if _fp(base.policy)!=_fp(target.policy) else None
    return ContainmentStateDelta(base.registry_fingerprint,target.registry_fingerprint,cs,rs,cst,rst,cc,rc,tr,tp,base.binding,base.state_epoch)
def apply_delta(base,delta):
    if delta.base_fingerprint!=base.registry_fingerprint: raise ValueError('DELTA_BASE_FINGERPRINT_MISMATCH')
    if delta.binding!=base.binding or delta.state_epoch!=base.state_epoch: raise ValueError('DELTA_SCOPE_MISMATCH')
    sm={x.step_id:x for x in base.steps}; stm={x.step_id:x for x in base.states}; cm={f'{x.step_id}:{x.compensation_id}':x for x in base.compensations}
    for k in delta.removed_step_ids: sm.pop(k,None)
    for x in delta.changed_steps: sm[x.step_id]=x
    for k in delta.removed_state_ids: stm.pop(k,None)
    for x in delta.changed_states: stm[x.step_id]=x
    for k in delta.removed_compensation_ids: cm.pop(k,None)
    for x in delta.changed_compensations: cm[f'{x.step_id}:{x.compensation_id}']=x
    st=prepare_state(delta.target_request or base.request,tuple(sm.values()),tuple(stm.values()),tuple(cm.values()),delta.target_policy or base.policy,binding=base.binding,state_epoch=base.state_epoch)
    if st.registry_fingerprint!=delta.target_fingerprint: raise ValueError('DELTA_TARGET_FINGERPRINT_MISMATCH')
    return st
def missing_only_sync_plan(target,known_record_fingerprints:dict[str,str]):
    missing=tuple(k for k,v in target.record_fingerprints if known_record_fingerprints.get(k)!=v); meta={'record_ids':missing,'target':target.registry_fingerprint}
    return ContainmentSyncPlan(missing,len(_canon(meta)),False)
def full_registry_bytes(st): return len(_canon({'request':st.request,'steps':st.steps,'states':st.states,'compensations':st.compensations,'policy':st.policy}))
def delta_bytes(delta): return len(_canon(delta))
