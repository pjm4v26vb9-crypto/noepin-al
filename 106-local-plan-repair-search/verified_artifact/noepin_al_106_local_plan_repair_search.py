"""NOEPIN AL 106 — Local Plan Repair Search — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Pure local-plan repair candidate evaluation. A failed plan step is dependency-sliced,
local replacement candidates are checked against boundary state, hard/global
constraints, downstream pre/postconditions and risk policy. If global impact cannot
be excluded, the module returns a Full Replan Candidate rather than pretending a
local patch is safe.

Repaired Subplan is candidate evidence only. It is never Permission Grant, Action
Execution, Commit/Publish, Global Constraint Proof, Safety Proof or Action Success.

Canonical identity: NOEPIN-AL-106
DCSR level: AUXILIARY INTEGRATION / 補助統合.
Provenance note: exact registered Origin GUID was not freshly reverified in this
completion session and is intentionally not guessed or regenerated.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, IntEnum
from hashlib import sha256
import json, math

class Decision(str,Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class RiskClass(IntEnum): LOW=0; MEDIUM=1; HIGH=2; CRITICAL=3
class NextAction(str,Enum):
    LOCAL_REPAIR_CANDIDATE='LOCAL_REPAIR_CANDIDATE'; FULL_REPLAN_CANDIDATE='FULL_REPLAN_CANDIDATE';
    HUMAN_REVIEW_CANDIDATE='HUMAN_REVIEW_CANDIDATE'; HOLD_NO_ALTERNATIVE='HOLD_NO_ALTERNATIVE'

@dataclass(frozen=True)
class PlanStep:
    step_id:str; depends_on:tuple[str,...]; preconditions:tuple[str,...]; postconditions:tuple[str,...]
    risk:float; cost:float; hard_constraint_passed:bool; global_constraint_sensitive:bool
    step_version:str; step_fingerprint:str; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class StateDiff:
    diff_id:str; added_facts:tuple[str,...]; removed_facts:tuple[str,...]
    global_constraint_changed:bool; global_impact_known:bool; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class RepairCandidate:
    candidate_id:str; replaces_step_id:str; preconditions:tuple[str,...]; postconditions:tuple[str,...]
    risk:float; cost:float; hard_constraint_passed:bool; global_impact_known_safe:bool
    candidate_version:str; candidate_fingerprint:str; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class RepairRequest:
    request_id:str; failed_step_id:str; current_facts:tuple[str,...]; risk_class:RiskClass
    max_affected_steps:int; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class RepairPolicy:
    low_risk_cap:float; medium_risk_cap:float; high_risk_cap:float; critical_risk_cap:float
    human_review_risk_increase:float; require_global_impact_known:bool; require_hard_constraints:bool
    binding:str; state_epoch:str; revoked:bool=False
@dataclass(frozen=True)
class RepairResult:
    decision:Decision; next_action:NextAction; reasons:tuple[str,...]; failed_step_id:str
    repaired_subplan:tuple[str,...]; affected_range:tuple[str,...]; chosen_candidate:str|None
    original_affected_risk:float; residual_risk:float; risk_increase:float
    rejected_candidates:tuple[tuple[str,str],...]; downstream_checks:tuple[tuple[str,bool],...]
    next_gate_candidate:bool; full_replan_required:bool
    repair_promoted_to_permission:bool=False; permission_granted:bool=False; action_executed:bool=False
    plan_committed:bool=False; atomic_publish_executed:bool=False; external_write_performed:bool=False
    world_truth_proven:bool=False; global_constraint_proven:bool=False; domain_authority_promoted:bool=False
    safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedRepairState:
    request:RepairRequest; plan:tuple[PlanStep,...]; diff:StateDiff; candidates:tuple[RepairCandidate,...]; policy:RepairPolicy
    record_fingerprints:tuple[tuple[str,str],...]; context_fingerprint:str; dependency_fingerprint:str
    policy_fingerprint:str; registry_fingerprint:str; frontier_fingerprint:str; boundary_fingerprint:str
    precomputed_result:RepairResult; binding:str; state_epoch:str
@dataclass(frozen=True)
class RepairStateDelta:
    base_fingerprint:str; target_fingerprint:str; changed_steps:tuple[PlanStep,...]; changed_candidates:tuple[RepairCandidate,...]
    removed_record_ids:tuple[str,...]; target_request:RepairRequest|None; target_diff:StateDiff|None; target_policy:RepairPolicy|None
    binding:str; state_epoch:str
@dataclass(frozen=True)
class RepairSyncPlan:
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

def _hold(q, reason, affected=(), *, action=NextAction.HOLD_NO_ALTERNATIVE, full_replan=False, rejected=(), downstream=(), original_risk=0.0):
    return RepairResult(Decision.HOLD,action,(reason,),q.failed_step_id,(),tuple(affected),None,original_risk,original_risk,0.0,tuple(sorted(rejected)),tuple(downstream),False,full_replan)

def _validate(q,plan,diff,candidates,p):
    if p.revoked: return 'POLICY_REVOKED'
    if not q.observed or not q.request_id or not q.failed_step_id or q.max_affected_steps<1: return 'REQUEST_INVALID'
    if not diff.observed or not diff.diff_id: return 'STATE_DIFF_INVALID'
    if q.binding!=p.binding or diff.binding!=p.binding or q.state_epoch!=p.state_epoch or diff.state_epoch!=p.state_epoch: return 'SCOPE_MISMATCH'
    vals=(p.low_risk_cap,p.medium_risk_cap,p.high_risk_cap,p.critical_risk_cap,p.human_review_risk_increase)
    if any(not math.isfinite(v) or v<0 for v in vals): return 'POLICY_NUMERIC_INVALID'
    if not (p.low_risk_cap>=p.medium_risk_cap>=p.high_risk_cap>=p.critical_risk_cap>=0): return 'POLICY_RISK_CAP_NONMONOTONIC'
    sids=[s.step_id for s in plan]; cids=[c.candidate_id for c in candidates]
    if len(sids)!=len(set(sids)): return 'DUPLICATE_STEP_ID'
    if len(cids)!=len(set(cids)): return 'DUPLICATE_CANDIDATE_ID'
    for s in plan:
        if not s.observed or not s.step_id or not s.step_version or not s.step_fingerprint or s.binding!=p.binding or s.state_epoch!=p.state_epoch: return 'PLAN_STEP_INVALID'
        if not math.isfinite(s.risk) or not math.isfinite(s.cost) or s.risk<0 or s.cost<0: return 'PLAN_STEP_INVALID'
    for c in candidates:
        if not c.observed or not c.candidate_id or not c.replaces_step_id or not c.candidate_version or not c.candidate_fingerprint or c.binding!=p.binding or c.state_epoch!=p.state_epoch: return 'CANDIDATE_INVALID'
        if not math.isfinite(c.risk) or not math.isfinite(c.cost) or c.risk<0 or c.cost<0: return 'CANDIDATE_INVALID'
    return None

def _dependency_slice(plan,failed):
    by={x.step_id:x for x in plan}
    if failed not in by: return ()
    affected={failed}; changed=True
    while changed:
        changed=False
        for s in plan:
            if s.step_id not in affected and any(d in affected for d in s.depends_on):
                affected.add(s.step_id); changed=True
    return tuple(s.step_id for s in plan if s.step_id in affected)

def evaluate(q:RepairRequest, plan:tuple[PlanStep,...], diff:StateDiff, candidates:tuple[RepairCandidate,...], p:RepairPolicy)->RepairResult:
    plan=tuple(plan); candidates=tuple(sorted(candidates,key=lambda c:c.candidate_id)); err=_validate(q,plan,diff,candidates,p)
    if err: return _hold(q,err)
    by={s.step_id:s for s in plan}; failed=by.get(q.failed_step_id)
    if failed is None: return _hold(q,'FAILED_STEP_NOT_FOUND')
    affected=_dependency_slice(plan,q.failed_step_id); original_risk=sum(by[x].risk for x in affected)
    if len(affected)>q.max_affected_steps:
        return _hold(q,'AFFECTED_RANGE_EXCEEDS_LOCAL_WINDOW',affected,action=NextAction.FULL_REPLAN_CANDIDATE,full_replan=True,original_risk=original_risk)
    # Any changed global constraint or unknown global impact forces global replan if the slice touches a global-sensitive step.
    touches_global=any(by[x].global_constraint_sensitive for x in affected)
    if (diff.global_constraint_changed or (p.require_global_impact_known and not diff.global_impact_known)) and touches_global:
        return _hold(q,'GLOBAL_CONSTRAINT_IMPACT_REQUIRES_FULL_REPLAN',affected,action=NextAction.FULL_REPLAN_CANDIDATE,full_replan=True,original_risk=original_risk)
    facts=(set(q.current_facts)|set(diff.added_facts))-set(diff.removed_facts)
    # Boundary state before failed step: remove postconditions from failed and affected downstream because they are not trusted after failure.
    for sid in affected:
        facts.difference_update(by[sid].postconditions)
    risk_cap=_risk_cap(q.risk_class,p); rejected=[]; viable=[]
    downstream=[by[x] for x in affected if x!=q.failed_step_id]
    for c in candidates:
        reason=None
        if c.replaces_step_id!=q.failed_step_id: reason='WRONG_REPLACEMENT_TARGET'
        elif p.require_hard_constraints and not c.hard_constraint_passed: reason='CANDIDATE_HARD_CONSTRAINT'
        elif p.require_global_impact_known and not c.global_impact_known_safe: reason='CANDIDATE_GLOBAL_IMPACT_UNKNOWN'
        elif not set(c.preconditions).issubset(facts): reason='CANDIDATE_PRECONDITION_FAILED'
        elif c.risk>risk_cap: reason='CANDIDATE_RISK_CAP_EXCEEDED'
        if reason:
            rejected.append((c.candidate_id,reason)); continue
        post=set(c.postconditions); checks=[]; compatible=True
        # Immediate/affected downstream preconditions must remain satisfiable from boundary+replacement effects+unchanged prior facts.
        available=facts|post
        for ds in downstream:
            ok=set(ds.preconditions).issubset(available)
            checks.append((ds.step_id,ok))
            if not ok: compatible=False; break
            available.update(ds.postconditions)
        if not compatible:
            rejected.append((c.candidate_id,'DOWNSTREAM_POSTCONDITION_INCOMPATIBLE')); continue
        residual=c.risk+sum(by[x].risk for x in affected if x!=q.failed_step_id)
        viable.append((residual,c.cost,c.candidate_id,c,tuple(checks)))
    if not viable:
        return _hold(q,'NO_SAFE_LOCAL_ALTERNATIVE',affected,rejected=rejected,original_risk=original_risk)
    residual,cost,_,chosen,checks=min(viable,key=lambda x:(x[0],x[1],x[2]))
    risk_increase=residual-original_risk
    repaired=(chosen.candidate_id,)+tuple(x for x in affected if x!=q.failed_step_id)
    reasons=['LOCAL_DEPENDENCY_SLICE_FIXED','BOUNDARY_STATE_REVALIDATED','DOWNSTREAM_POSTCONDITIONS_COMPATIBLE','GLOBAL_CONSTRAINT_SCOPE_PRESERVED','REPAIR_CANDIDATE_ONLY']
    if rejected: reasons.append('UNSAFE_ALTERNATIVES_REJECTED')
    if risk_increase>=p.human_review_risk_increase:
        return RepairResult(Decision.HUMAN_APPROVAL,NextAction.HUMAN_REVIEW_CANDIDATE,tuple(reasons+['RESIDUAL_RISK_INCREASE_REQUIRES_REVIEW']),q.failed_step_id,repaired,affected,chosen.candidate_id,original_risk,residual,risk_increase,tuple(sorted(rejected)),checks,False,False)
    return RepairResult(Decision.ALLOW,NextAction.LOCAL_REPAIR_CANDIDATE,tuple(reasons),q.failed_step_id,repaired,affected,chosen.candidate_id,original_risk,residual,risk_increase,tuple(sorted(rejected)),checks,True,False)

def default_policy(): return RepairPolicy(3.0,2.0,1.0,.6,.35,True,True,'REPAIR-BIND','STATE-EPOCH-1')
def default_request():
    p=default_policy(); return RepairRequest('REQ-106','BUILD',('source_ready','workspace_ready','tests_ready'),RiskClass.LOW,4,True,p.binding,p.state_epoch)
def default_plan():
    p=default_policy(); b=p.binding; e=p.state_epoch
    return (
        PlanStep('PREP',(),('workspace_ready',),('prepared',),.1,.2,True,False,'V1','FP-PREP',True,b,e),
        PlanStep('BUILD',('PREP',),('source_ready',),('artifact_built',),.4,1.0,True,False,'V1','FP-BUILD',True,b,e),
        PlanStep('TEST',('BUILD',),('artifact_built','tests_ready'),('verified',),.2,.8,True,False,'V1','FP-TEST',True,b,e),
        PlanStep('PUBLISH',('TEST',),('verified',),('published_candidate',),.3,.7,True,True,'V1','FP-PUB',True,b,e),
    )
def default_diff():
    p=default_policy(); return StateDiff('DIFF-106',(),(),False,True,True,p.binding,p.state_epoch)
def default_candidates():
    p=default_policy(); b=p.binding; e=p.state_epoch
    return (
        RepairCandidate('BUILD-SAFE','BUILD',('source_ready',),('artifact_built',),.25,.9,True,True,'V1','FP-C1',True,b,e),
        RepairCandidate('BUILD-RISKY','BUILD',('source_ready',),('artifact_built',),2.8,.1,True,True,'V1','FP-C2',True,b,e),
        RepairCandidate('BUILD-UNKNOWN-GLOBAL','BUILD',('source_ready',),('artifact_built',),.1,.1,True,False,'V1','FP-C3',True,b,e),
        RepairCandidate('BUILD-BROKEN','BUILD',('source_ready',),('other_output',),.05,.1,True,True,'V1','FP-C4',True,b,e),
    )
def default_evaluation(): return evaluate(default_request(),default_plan(),default_diff(),default_candidates(),default_policy())

def _record_fps(plan,candidates):
    return tuple([(f'STEP:{x.step_id}',_fp(x)) for x in plan]+[(f'CANDIDATE:{x.candidate_id}',_fp(x)) for x in sorted(candidates,key=lambda y:y.candidate_id)])
def _context_fp(q,diff): return _fp((q,diff))
def _dependency_fp(plan): return _fp(tuple((s.step_id,s.depends_on,s.preconditions,s.postconditions,s.global_constraint_sensitive) for s in plan))
def _policy_fp(p): return _fp(p)
def _registry_fp(q,plan,diff,candidates,p): return _fp((q,_record_fps(plan,candidates),diff,p))
def _frontier_fp(q,plan,diff,candidates): return _fp((q.failed_step_id,_dependency_slice(plan,q.failed_step_id),diff,tuple((c.candidate_id,c.replaces_step_id,c.preconditions,c.postconditions,c.risk,c.hard_constraint_passed,c.global_impact_known_safe) for c in sorted(candidates,key=lambda x:x.candidate_id))))
def _boundary_fp(q,plan,diff): return _fp((q.current_facts,diff,tuple((s.step_id,s.postconditions) for s in plan if s.step_id in _dependency_slice(plan,q.failed_step_id))))
def prepare_state(q,plan,diff,candidates,p,*,binding,state_epoch):
    plan=tuple(plan); candidates=tuple(candidates); fps=_record_fps(plan,candidates)
    return PreparedRepairState(q,plan,diff,candidates,p,fps,_context_fp(q,diff),_dependency_fp(plan),_policy_fp(p),_registry_fp(q,plan,diff,candidates,p),_frontier_fp(q,plan,diff,candidates),_boundary_fp(q,plan,diff),evaluate(q,plan,diff,candidates,p),binding,state_epoch)
def validate_prepared_integrity(st):
    return (st.binding==st.policy.binding==st.request.binding==st.diff.binding and st.state_epoch==st.policy.state_epoch==st.request.state_epoch==st.diff.state_epoch and st.record_fingerprints==_record_fps(st.plan,st.candidates) and st.context_fingerprint==_context_fp(st.request,st.diff) and st.dependency_fingerprint==_dependency_fp(st.plan) and st.policy_fingerprint==_policy_fp(st.policy) and st.registry_fingerprint==_registry_fp(st.request,st.plan,st.diff,st.candidates,st.policy) and st.frontier_fingerprint==_frontier_fp(st.request,st.plan,st.diff,st.candidates) and st.boundary_fingerprint==_boundary_fp(st.request,st.plan,st.diff) and st.precomputed_result==evaluate(st.request,st.plan,st.diff,st.candidates,st.policy))
def evaluate_prepared(st,*,integrity_validated,current_context_fingerprint,current_dependency_fingerprint,current_policy_fingerprint,current_registry_fingerprint,current_frontier_fingerprint,current_boundary_fingerprint):
    if not integrity_validated: return _hold(st.request,'PREPARED_INTEGRITY_NOT_VALIDATED')
    if (st.context_fingerprint!=current_context_fingerprint or st.dependency_fingerprint!=current_dependency_fingerprint or st.policy_fingerprint!=current_policy_fingerprint or st.registry_fingerprint!=current_registry_fingerprint or st.frontier_fingerprint!=current_frontier_fingerprint or st.boundary_fingerprint!=current_boundary_fingerprint):
        return _hold(st.request,'PREPARED_FINGERPRINT_MISMATCH_REEVALUATION_REQUIRED',action=NextAction.FULL_REPLAN_CANDIDATE,full_replan=True)
    return st.precomputed_result
def make_delta(base,target):
    bm=dict(base.record_fingerprints); tm=dict(target.record_fingerprints); sm={f'STEP:{x.step_id}':x for x in target.plan}; cm={f'CANDIDATE:{x.candidate_id}':x for x in target.candidates}
    changed_s=tuple(sm[k] for k,v in tm.items() if k.startswith('STEP:') and bm.get(k)!=v); changed_c=tuple(cm[k] for k,v in tm.items() if k.startswith('CANDIDATE:') and bm.get(k)!=v); removed=tuple(k for k in bm if k not in tm)
    return RepairStateDelta(base.registry_fingerprint,target.registry_fingerprint,changed_s,changed_c,removed,target.request if base.request!=target.request else None,target.diff if base.diff!=target.diff else None,target.policy if base.policy!=target.policy else None,target.binding,target.state_epoch)
def plan_missing_only(local,target):
    lm=dict(local.record_fingerprints); tm=dict(target.record_fingerprints); ids=tuple(k for k,v in tm.items() if lm.get(k)!=v)
    return RepairSyncPlan(ids,len(_canon(ids)),False)
