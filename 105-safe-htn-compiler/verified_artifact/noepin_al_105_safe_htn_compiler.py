"""NOEPIN AL 105 — Safe HTN Compiler — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Pure hierarchical planning-candidate evidence. This module decomposes a typed
high-level Goal through HTN Methods while enforcing method preconditions, hard
constraints, current capability/authority evidence, and leaf policy guards at
every decomposition step. Unsafe or authority-insufficient methods are rejected;
if no safe decomposition exists the result is HOLD rather than an unsafe fallback.

A Hierarchical Plan is only a planning candidate. It is never Permission Grant,
Authority Grant, Action Execution, Commit/Publish, Production Authority, Safety
Proof, or Action Success.

Canonical identity: NOEPIN-AL-105
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
    HIERARCHICAL_PLAN_CANDIDATE='HIERARCHICAL_PLAN_CANDIDATE'; HUMAN_REVIEW_CANDIDATE='HUMAN_REVIEW_CANDIDATE';
    REPLAN_CANDIDATE='REPLAN_CANDIDATE'; HOLD_UNRESOLVED='HOLD_UNRESOLVED'

@dataclass(frozen=True)
class HTNRequest:
    request_id:str; goal_task:str; risk:RiskClass; max_depth:int; max_leaf_tasks:int
    observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class HTNState:
    state_id:str; facts:tuple[str,...]; capabilities:tuple[str,...]; authority_tier:int
    observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class HTNMethod:
    method_id:str; task_name:str; subtasks:tuple[str,...]; preconditions:tuple[str,...]
    required_authority:int; method_risk:float; hard_constraint_passed:bool; priority:int
    method_version:str; method_fingerprint:str; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class HTNLeaf:
    task_id:str; preconditions:tuple[str,...]; postconditions:tuple[str,...]; required_capabilities:tuple[str,...]
    required_authority:int; risk:float; cost:float; policy_verified:bool; hard_constraint_passed:bool
    leaf_version:str; leaf_fingerprint:str; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class HTNPolicy:
    low_risk_cap:float; medium_risk_cap:float; high_risk_cap:float; critical_risk_cap:float
    max_authority_low:int; max_authority_medium:int; max_authority_high:int; max_authority_critical:int
    approval_risk_threshold:float; require_policy_verified_leaves:bool; require_hard_constraints:bool
    binding:str; state_epoch:str; revoked:bool=False
@dataclass(frozen=True)
class PlanLeaf:
    task_id:str; depth:int; risk:float; cost:float; required_authority:int; required_capabilities:tuple[str,...]
@dataclass(frozen=True)
class HTNResult:
    decision:Decision; next_action:NextAction; reasons:tuple[str,...]; goal_task:str
    hierarchical_plan:tuple[PlanLeaf,...]; method_trace:tuple[str,...]; rejected_methods:tuple[tuple[str,str],...]
    dependencies:tuple[tuple[str,str],...]; total_risk:float; total_cost:float; max_required_authority:int
    next_gate_candidate:bool; plan_promoted_to_permission:bool=False; permission_granted:bool=False
    authority_granted:bool=False; action_executed:bool=False; plan_committed:bool=False
    atomic_publish_executed:bool=False; external_write_performed:bool=False; world_truth_proven:bool=False
    domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedHTNState:
    request:HTNRequest; state:HTNState; methods:tuple[HTNMethod,...]; leaves:tuple[HTNLeaf,...]; policy:HTNPolicy
    registry_fingerprints:tuple[tuple[str,str],...]; context_fingerprint:str; dependency_fingerprint:str
    policy_fingerprint:str; registry_fingerprint:str; frontier_fingerprint:str; decomposition_fingerprint:str
    precomputed_result:HTNResult; binding:str; state_epoch:str
@dataclass(frozen=True)
class HTNStateDelta:
    base_fingerprint:str; target_fingerprint:str; changed_methods:tuple[HTNMethod,...]; changed_leaves:tuple[HTNLeaf,...]
    removed_record_ids:tuple[str,...]; target_request:HTNRequest|None; target_state:HTNState|None; target_policy:HTNPolicy|None
    binding:str; state_epoch:str
@dataclass(frozen=True)
class HTNSyncPlan:
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
def _authority_cap(r,p): return {RiskClass.LOW:p.max_authority_low,RiskClass.MEDIUM:p.max_authority_medium,RiskClass.HIGH:p.max_authority_high,RiskClass.CRITICAL:p.max_authority_critical}[r]

def _validate(q,s,methods,leaves,p):
    if p.revoked: return 'POLICY_REVOKED'
    if not q.observed or not q.request_id or not q.goal_task or q.max_depth<1 or q.max_leaf_tasks<1: return 'REQUEST_INVALID'
    if not s.observed or not s.state_id or s.authority_tier<0: return 'STATE_INVALID'
    if q.binding!=p.binding or s.binding!=p.binding or q.state_epoch!=p.state_epoch or s.state_epoch!=p.state_epoch: return 'SCOPE_MISMATCH'
    vals=(p.low_risk_cap,p.medium_risk_cap,p.high_risk_cap,p.critical_risk_cap,p.approval_risk_threshold)
    if any(not math.isfinite(v) or v<0 for v in vals): return 'POLICY_NUMERIC_INVALID'
    if not (p.low_risk_cap>=p.medium_risk_cap>=p.high_risk_cap>=p.critical_risk_cap>=0): return 'POLICY_RISK_CAP_NONMONOTONIC'
    if not (p.max_authority_low>=p.max_authority_medium>=p.max_authority_high>=p.max_authority_critical>=0): return 'POLICY_AUTHORITY_CAP_NONMONOTONIC'
    mids=[m.method_id for m in methods]; lids=[l.task_id for l in leaves]
    if len(mids)!=len(set(mids)): return 'DUPLICATE_METHOD_ID'
    if len(lids)!=len(set(lids)): return 'DUPLICATE_LEAF_ID'
    for m in methods:
        if not m.observed or not m.method_id or not m.task_name or not m.method_version or not m.method_fingerprint: return 'METHOD_INVALID'
        if m.binding!=p.binding or m.state_epoch!=p.state_epoch or m.required_authority<0 or not math.isfinite(m.method_risk) or m.method_risk<0: return 'METHOD_INVALID'
        if p.require_hard_constraints and not m.hard_constraint_passed and not m.method_id: return 'METHOD_CONSTRAINT_EVIDENCE_INVALID'
    for l in leaves:
        if not l.observed or not l.task_id or not l.leaf_version or not l.leaf_fingerprint: return 'LEAF_INVALID'
        if l.binding!=p.binding or l.state_epoch!=p.state_epoch or l.required_authority<0 or not math.isfinite(l.risk) or not math.isfinite(l.cost) or l.risk<0 or l.cost<0: return 'LEAF_INVALID'
    return None

def _hold(q,reason,rejected=(),*,action=NextAction.HOLD_UNRESOLVED):
    return HTNResult(Decision.HOLD,action,(reason,),q.goal_task,(),(),tuple(sorted(rejected)),(),0.0,0.0,0,False)

def evaluate(q:HTNRequest,s:HTNState,methods:tuple[HTNMethod,...],leaves:tuple[HTNLeaf,...],p:HTNPolicy)->HTNResult:
    methods=tuple(sorted(methods,key=lambda m:m.method_id)); leaves=tuple(sorted(leaves,key=lambda l:l.task_id)); err=_validate(q,s,methods,leaves,p)
    if err: return _hold(q,err)
    facts=set(s.facts); caps=set(s.capabilities); leaf_by={l.task_id:l for l in leaves}; methods_by={}
    for m in methods: methods_by.setdefault(m.task_name,[]).append(m)
    risk_cap=_risk_cap(q.risk,p); auth_cap=min(s.authority_tier,_authority_cap(q.risk,p)); rejected=[]

    def leaf_plan(task,depth):
        l=leaf_by.get(task)
        if l is None: return None,'LEAF_NOT_REGISTERED'
        if depth>q.max_depth: return None,'MAX_DEPTH_EXCEEDED'
        if p.require_hard_constraints and not l.hard_constraint_passed: return None,'LEAF_HARD_CONSTRAINT'
        if p.require_policy_verified_leaves and not l.policy_verified: return None,'LEAF_POLICY_UNVERIFIED'
        if not set(l.preconditions).issubset(facts): return None,'LEAF_PRECONDITION_FAILED'
        if not set(l.required_capabilities).issubset(caps): return None,'LEAF_CAPABILITY_MISSING'
        if l.required_authority>auth_cap: return None,'LEAF_AUTHORITY_INSUFFICIENT'
        if l.risk>risk_cap+1e-12: return None,'LEAF_RISK_CAP_EXCEEDED'
        return (PlanLeaf(l.task_id,depth,l.risk,l.cost,l.required_authority,l.required_capabilities),),None

    visiting=[]
    def decompose(task,depth):
        if depth>q.max_depth: return None,(), 'MAX_DEPTH_EXCEEDED'
        if task in leaf_by:
            lp,why=leaf_plan(task,depth); return lp,(),why
        if task in visiting: return None,(), 'HTN_CYCLE_DETECTED'
        candidates=methods_by.get(task,[])
        if not candidates: return None,(), 'NO_METHOD_FOR_TASK'
        valid=[]
        visiting.append(task)
        try:
            for m in candidates:
                why=None
                if p.require_hard_constraints and not m.hard_constraint_passed: why='METHOD_HARD_CONSTRAINT'
                elif not set(m.preconditions).issubset(facts): why='METHOD_PRECONDITION_FAILED'
                elif m.required_authority>auth_cap: why='METHOD_AUTHORITY_INSUFFICIENT'
                elif m.method_risk>risk_cap+1e-12: why='METHOD_RISK_CAP_EXCEEDED'
                if why:
                    rejected.append((m.method_id,why)); continue
                all_leaves=[]; trace=[m.method_id]; failed=None
                for sub in m.subtasks:
                    pl,tr,subwhy=decompose(sub,depth+1)
                    if pl is None:
                        failed=f'{subwhy}:{sub}'; break
                    all_leaves.extend(pl); trace.extend(tr)
                    if len(all_leaves)>q.max_leaf_tasks:
                        failed='MAX_LEAF_TASKS_EXCEEDED'; break
                if failed:
                    rejected.append((m.method_id,failed)); continue
                total_risk=m.method_risk+sum(x.risk for x in all_leaves); total_cost=sum(x.cost for x in all_leaves); max_auth=max([m.required_authority]+[x.required_authority for x in all_leaves])
                if total_risk>risk_cap*max(1,len(all_leaves))+1e-12:
                    rejected.append((m.method_id,'PLAN_RISK_ACCUMULATION_EXCEEDED')); continue
                valid.append((total_risk,total_cost,-m.priority,m.method_id,tuple(all_leaves),tuple(trace),max_auth))
        finally:
            visiting.pop()
        if not valid: return None,(), 'NO_SAFE_METHOD_DECOMPOSITION'
        valid.sort(key=lambda x:(x[0],x[1],x[2],x[3])); best=valid[0]
        return best[4],best[5],None

    plan,trace,why=decompose(q.goal_task,0)
    if plan is None: return _hold(q,why or 'NO_SAFE_METHOD_DECOMPOSITION',rejected,action=NextAction.REPLAN_CANDIDATE)
    deps=tuple((plan[i].task_id,plan[i+1].task_id) for i in range(len(plan)-1))
    total_risk=sum(x.risk for x in plan); total_cost=sum(x.cost for x in plan); max_auth=max((x.required_authority for x in plan),default=0)
    reasons=['SAFE_HTN_DECOMPOSITION_CANDIDATE','ALL_LEAF_GUARDS_PASSED','AUTHORITY_CAP_PRESERVED','PLAN_CANDIDATE_ONLY']
    if rejected: reasons.append('UNSAFE_METHODS_REJECTED')
    if q.risk in (RiskClass.HIGH,RiskClass.CRITICAL) and total_risk>=p.approval_risk_threshold:
        return HTNResult(Decision.HUMAN_APPROVAL,NextAction.HUMAN_REVIEW_CANDIDATE,tuple(reasons+['RISK_REQUIRES_HUMAN_REVIEW_CANDIDATE']),q.goal_task,tuple(plan),tuple(trace),tuple(sorted(rejected)),deps,total_risk,total_cost,max_auth,False)
    return HTNResult(Decision.ALLOW,NextAction.HIERARCHICAL_PLAN_CANDIDATE,tuple(reasons),q.goal_task,tuple(plan),tuple(trace),tuple(sorted(rejected)),deps,total_risk,total_cost,max_auth,True)

def default_policy():
    return HTNPolicy(4.0,3.0,2.0,1.0,4,3,2,1,1.5,True,True,'HTN-BIND','STATE-EPOCH-1')
def default_request():
    p=default_policy(); return HTNRequest('REQ-105','PROJECT_FIX',RiskClass.LOW,8,16,True,p.binding,p.state_epoch)
def default_state():
    p=default_policy(); return HTNState('S-105',('repo_loaded','tests_available','backup_ready'),('read','edit','test'),3,True,p.binding,p.state_epoch)
def default_methods():
    p=default_policy(); b=p.binding; e=p.state_epoch
    return (
        HTNMethod('M-SAFE','PROJECT_FIX',('INSPECT','PATCH','VERIFY'),('repo_loaded',),2,.20,True,10,'V1','FP-MS',True,b,e),
        HTNMethod('M-UNSAFE','PROJECT_FIX',('DELETE_ALL','PATCH'),('repo_loaded',),4,.01,False,100,'V1','FP-MX',True,b,e),
        HTNMethod('M-NOAUTH','PROJECT_FIX',('INSPECT','PATCH','VERIFY'),('repo_loaded',),5,.01,True,50,'V1','FP-MA',True,b,e),
    )
def default_leaves():
    p=default_policy(); b=p.binding; e=p.state_epoch
    return (
        HTNLeaf('INSPECT',('repo_loaded',),('scope_known',),('read',),1,.10,.5,True,True,'V1','FP-L1',True,b,e),
        HTNLeaf('PATCH',('repo_loaded',),('patch_staged',),('edit',),2,.20,1.0,True,True,'V1','FP-L2',True,b,e),
        HTNLeaf('VERIFY',('tests_available',),('verified',),('test',),1,.10,.8,True,True,'V1','FP-L3',True,b,e),
        HTNLeaf('DELETE_ALL',('repo_loaded',),('destructive',),('edit',),4,10.0,.1,False,False,'V1','FP-LX',True,b,e),
    )
def default_evaluation(): return evaluate(default_request(),default_state(),default_methods(),default_leaves(),default_policy())

def _record_fps(methods,leaves):
    xs=[(f'METHOD:{m.method_id}',_fp(m)) for m in sorted(methods,key=lambda x:x.method_id)]+[(f'LEAF:{l.task_id}',_fp(l)) for l in sorted(leaves,key=lambda x:x.task_id)]
    return tuple(xs)
def _context_fp(q,s): return _fp((q,s))
def _dependency_fp(methods,leaves): return _fp(_record_fps(methods,leaves))
def _policy_fp(p): return _fp(p)
def _registry_fp(q,s,methods,leaves,p): return _fp((q,s,_record_fps(methods,leaves),p))
def _frontier_fp(q,s,methods,leaves,p): return _fp((q.goal_task,q.max_depth,q.max_leaf_tasks,s.facts,s.capabilities,s.authority_tier,tuple((m.method_id,m.task_name,m.subtasks,m.preconditions,m.required_authority,m.method_risk,m.hard_constraint_passed,m.priority) for m in sorted(methods,key=lambda x:x.method_id)),tuple((l.task_id,l.preconditions,l.required_capabilities,l.required_authority,l.risk,l.policy_verified,l.hard_constraint_passed) for l in sorted(leaves,key=lambda x:x.task_id))))
def _decomp_fp(methods,leaves): return _fp((tuple((m.task_name,m.method_id,m.subtasks) for m in sorted(methods,key=lambda x:(x.task_name,x.method_id))),tuple((l.task_id,l.postconditions) for l in sorted(leaves,key=lambda x:x.task_id))))
def prepare_state(q,s,methods,leaves,p,*,binding,state_epoch):
    methods=tuple(methods); leaves=tuple(leaves); fps=_record_fps(methods,leaves)
    return PreparedHTNState(q,s,methods,leaves,p,fps,_context_fp(q,s),_dependency_fp(methods,leaves),_policy_fp(p),_registry_fp(q,s,methods,leaves,p),_frontier_fp(q,s,methods,leaves,p),_decomp_fp(methods,leaves),evaluate(q,s,methods,leaves,p),binding,state_epoch)
def validate_prepared_integrity(st):
    return (st.binding==st.policy.binding==st.request.binding==st.state.binding and st.state_epoch==st.policy.state_epoch==st.request.state_epoch==st.state.state_epoch and st.registry_fingerprints==_record_fps(st.methods,st.leaves) and st.context_fingerprint==_context_fp(st.request,st.state) and st.dependency_fingerprint==_dependency_fp(st.methods,st.leaves) and st.policy_fingerprint==_policy_fp(st.policy) and st.registry_fingerprint==_registry_fp(st.request,st.state,st.methods,st.leaves,st.policy) and st.frontier_fingerprint==_frontier_fp(st.request,st.state,st.methods,st.leaves,st.policy) and st.decomposition_fingerprint==_decomp_fp(st.methods,st.leaves) and st.precomputed_result==evaluate(st.request,st.state,st.methods,st.leaves,st.policy))
def evaluate_prepared(st,*,integrity_validated,current_context_fingerprint,current_dependency_fingerprint,current_policy_fingerprint,current_registry_fingerprint,current_frontier_fingerprint,current_decomposition_fingerprint):
    if not integrity_validated: return _hold(st.request,'PREPARED_INTEGRITY_NOT_VALIDATED')
    if (st.context_fingerprint!=current_context_fingerprint or st.dependency_fingerprint!=current_dependency_fingerprint or st.policy_fingerprint!=current_policy_fingerprint or st.registry_fingerprint!=current_registry_fingerprint or st.frontier_fingerprint!=current_frontier_fingerprint or st.decomposition_fingerprint!=current_decomposition_fingerprint):
        return _hold(st.request,'PREPARED_FINGERPRINT_MISMATCH_REEVALUATION_REQUIRED',action=NextAction.REPLAN_CANDIDATE)
    return st.precomputed_result
def make_delta(base,target):
    bm=dict(base.registry_fingerprints); tm=dict(target.registry_fingerprints); mm={f'METHOD:{x.method_id}':x for x in target.methods}; lm={f'LEAF:{x.task_id}':x for x in target.leaves}
    changed_m=tuple(mm[k] for k,v in tm.items() if k.startswith('METHOD:') and bm.get(k)!=v); changed_l=tuple(lm[k] for k,v in tm.items() if k.startswith('LEAF:') and bm.get(k)!=v); removed=tuple(k for k in bm if k not in tm)
    return HTNStateDelta(base.registry_fingerprint,target.registry_fingerprint,changed_m,changed_l,removed,target.request if base.request!=target.request else None,target.state if base.state!=target.state else None,target.policy if base.policy!=target.policy else None,target.binding,target.state_epoch)
def plan_missing_only(local,target):
    lm=dict(local.registry_fingerprints); tm=dict(target.registry_fingerprints); ids=tuple(k for k,v in tm.items() if lm.get(k)!=v)
    return HTNSyncPlan(ids,len(_canon(ids)),False)
