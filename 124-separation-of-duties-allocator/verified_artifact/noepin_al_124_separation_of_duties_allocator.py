"""NOEPIN AL 124 — Separation-of-Duties Allocator — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-124
DCSR: DIRECT INTEGRATION / 直接統合.
Assignment is a candidate only. Assignment != Permission Grant, Role Authority Grant, Approval Execution, or Action Execution.
Received DCSR state never automatically inherits sender authority, intent, agreement, permission, or action-success authority.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str,Enum): ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class NextAction(str,Enum): ASSIGNMENT_CANDIDATE='ASSIGNMENT_CANDIDATE'; HOLD_SOD_REVIEW='HOLD_SOD_REVIEW'; HUMAN_APPROVAL_CANDIDATE='HUMAN_APPROVAL_CANDIDATE'
class Escalation(str,Enum): NONE='NONE'; CRITICAL_SOD_VIOLATION='CRITICAL_SOD_VIOLATION'; UNASSIGNED_CRITICAL_ROLE='UNASSIGNED_CRITICAL_ROLE'; NO_ALTERNATIVE_AGENT='NO_ALTERNATIVE_AGENT'; INDEPENDENT_REVIEWER_UNAVAILABLE='INDEPENDENT_REVIEWER_UNAVAILABLE'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'

@dataclass(frozen=True)
class RoleRequirement:
    task_id:str; role_id:str; capability:str; critical:bool; minimum_trust:float
@dataclass(frozen=True)
class Agent:
    agent_id:str; capabilities:tuple[str,...]; trust:float; trust_domain:str; available:bool; human:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class ConflictRule:
    role_a:str; role_b:str; same_agent_forbidden:bool=True
@dataclass(frozen=True)
class SoDPolicy:
    require_independent_reviewer:bool=True; reviewer_role_id:str='REVIEWER'; approver_role_id:str='APPROVER'; planner_role_id:str='PLANNER'; executor_role_id:str='EXECUTOR'; allow_human_escalation:bool=True
@dataclass(frozen=True)
class AllocationRequest:
    request_id:str; roles:tuple[RoleRequirement,...]; agents:tuple[Agent,...]; conflicts:tuple[ConflictRule,...]; policy:SoDPolicy; binding:str; state_epoch:str
@dataclass(frozen=True)
class Assignment:
    task_id:str; role_id:str; agent_id:str; trust_domain:str; human:bool
@dataclass(frozen=True)
class AllocationResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; reasons:tuple[str,...]; assignments:tuple[Assignment,...]; sod_violations:tuple[str,...]; unassigned_roles:tuple[str,...]; next_gate_candidate:bool
    assignment_promoted_to_permission:bool=False; assignment_promoted_to_role_authority:bool=False; independent_review_promoted_to_approval_execution:bool=False; sender_authority_inherited:bool=False; sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False; permission_granted:bool=False; approval_executed:bool=False; authority_granted:bool=False; stop_executed:bool=False; action_executed:bool=False; plan_committed:bool=False; publish_executed:bool=False; external_write_performed:bool=False; world_truth_proven:bool=False; domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedAllocationState:
    request:AllocationRequest; result:AllocationResult; context_fingerprint:str; role_fingerprint:str; agent_fingerprint:str; conflict_fingerprint:str; policy_fingerprint:str; outcome_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class AllocationDelta:
    changed_agents:tuple[Agent,...]; removed_agent_ids:tuple[str,...]; changed_roles:tuple[RoleRequirement,...]; removed_role_keys:tuple[str,...]; from_manifest_fingerprint:str; to_manifest_fingerprint:str
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
def _role_key(r): return f'{r.task_id}:{r.role_id}'
def _manifest_fp(req): return _fp((req.roles,req.agents,req.conflicts,req.binding,req.state_epoch))

def default_policy(): return SoDPolicy()
def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    roles=(
      RoleRequirement('TASK-CHANGE','PLANNER','PLAN',True,.70),
      RoleRequirement('TASK-CHANGE','EXECUTOR','EXECUTE',True,.75),
      RoleRequirement('TASK-CHANGE','APPROVER','APPROVE',True,.80),
      RoleRequirement('TASK-CHANGE','REVIEWER','REVIEW',True,.75),
    )
    agents=(
      Agent('AGENT-PLAN',('PLAN','REVIEW'),.92,'DOMAIN-A',True,False,b,e),
      Agent('AGENT-EXEC',('EXECUTE',),.93,'DOMAIN-B',True,False,b,e),
      Agent('AGENT-APPROVE',('APPROVE',),.96,'DOMAIN-C',True,True,b,e),
      Agent('AGENT-REVIEW',('REVIEW','PLAN'),.91,'DOMAIN-D',True,False,b,e),
    )
    conflicts=(
      ConflictRule('PLANNER','APPROVER'),
      ConflictRule('EXECUTOR','APPROVER'),
      ConflictRule('EXECUTOR','REVIEWER'),
      ConflictRule('PLANNER','REVIEWER'),
    )
    return AllocationRequest('DEFAULT-124',roles,agents,conflicts,default_policy(),b,e)

def _invalid(reason):
    return AllocationResult(Decision.HOLD,NextAction.HOLD_SOD_REVIEW,Escalation.INVALID_CONFIGURATION,(reason,'ASSIGNMENT_NOT_PROMOTED_TO_AUTHORITY'),(),(),(),False)

def _conflict_pairs(req):
    pairs=set()
    for c in req.conflicts:
        if c.same_agent_forbidden:
            pairs.add(tuple(sorted((c.role_a,c.role_b))))
    return pairs

def _violations(assignments,req):
    pairs=_conflict_pairs(req); by_task={}
    for a in assignments: by_task.setdefault(a.task_id,[]).append(a)
    out=[]
    for task,items in by_task.items():
        by_agent={}
        for a in items: by_agent.setdefault(a.agent_id,[]).append(a.role_id)
        for aid,roles in by_agent.items():
            for i,x in enumerate(roles):
                for y in roles[i+1:]:
                    if tuple(sorted((x,y))) in pairs: out.append(f'{task}:{aid}:{x}={y}:CONFLICT')
        if req.policy.require_independent_reviewer:
            reviewer=next((a for a in items if a.role_id==req.policy.reviewer_role_id),None)
            if reviewer:
                for rid in (req.policy.planner_role_id,req.policy.executor_role_id,req.policy.approver_role_id):
                    other=next((a for a in items if a.role_id==rid),None)
                    if other and other.agent_id==reviewer.agent_id: out.append(f'{task}:{reviewer.agent_id}:REVIEWER_NOT_INDEPENDENT_OF_{rid}')
    return tuple(sorted(set(out)))

def _candidate_agents(role,req):
    xs=[]
    for a in req.agents:
        if not a.available or role.capability not in a.capabilities or a.trust<role.minimum_trust: continue
        xs.append(a)
    return tuple(sorted(xs,key=lambda a:(-a.trust,not a.human,a.agent_id)))

def evaluate(req:AllocationRequest)->AllocationResult:
    if not req.request_id or not req.binding or not req.state_epoch: return _invalid('INVALID_REQUEST_IDENTITY')
    if not req.roles or not req.agents: return _invalid('EMPTY_ROLE_OR_AGENT_SET')
    role_keys=[_role_key(r) for r in req.roles]; agent_ids=[a.agent_id for a in req.agents]
    if any(not x for x in role_keys) or len(role_keys)!=len(set(role_keys)): return _invalid('DUPLICATE_OR_EMPTY_ROLE')
    if any(not x for x in agent_ids) or len(agent_ids)!=len(set(agent_ids)): return _invalid('DUPLICATE_OR_EMPTY_AGENT_ID')
    role_names={r.role_id for r in req.roles}
    for c in req.conflicts:
        if not c.role_a or not c.role_b or c.role_a==c.role_b: return _invalid('INVALID_CONFLICT_RULE')
        if c.role_a not in role_names or c.role_b not in role_names: return _invalid('CONFLICT_ROLE_UNKNOWN')
    for r in req.roles:
        if not r.task_id or not r.role_id or not r.capability or not _finite(r.minimum_trust) or not 0<=r.minimum_trust<=1: return _invalid('ROLE_INVALID')
    for a in req.agents:
        if not a.agent_id or not a.trust_domain or a.binding!=req.binding or a.state_epoch!=req.state_epoch: return _invalid('AGENT_IDENTITY_INVALID')
        if not _finite(a.trust) or not 0<=a.trust<=1: return _invalid('AGENT_TRUST_INVALID')
    if req.policy.require_independent_reviewer and req.policy.reviewer_role_id not in role_names: return _invalid('REVIEWER_ROLE_REQUIRED_BUT_MISSING')

    conflicts=_conflict_pairs(req); assignments=[]; unassigned=[]; impossible_critical=False; no_alternative=False
    tasks=sorted({r.task_id for r in req.roles})
    for task in tasks:
        rs=[r for r in req.roles if r.task_id==task]
        cand={r.role_id:_candidate_agents(r,req) for r in rs}
        for r in rs:
            if not cand[r.role_id]:
                unassigned.append(_role_key(r)); impossible_critical=impossible_critical or r.critical; no_alternative=True
        if any(not cand[r.role_id] for r in rs): continue
        # Most constrained / critical roles first; deterministic bounded DFS per task.
        order=sorted(rs,key=lambda r:(len(cand[r.role_id]),not r.critical,r.role_id))
        chosen={}; solution=None
        def ok(role,agent):
            for rid,aid in chosen.items():
                if aid.agent_id==agent.agent_id and tuple(sorted((role.role_id,rid))) in conflicts: return False
            if req.policy.require_independent_reviewer:
                if role.role_id==req.policy.reviewer_role_id:
                    for rid in (req.policy.planner_role_id,req.policy.executor_role_id,req.policy.approver_role_id):
                        if rid in chosen and chosen[rid].agent_id==agent.agent_id: return False
                if role.role_id in (req.policy.planner_role_id,req.policy.executor_role_id,req.policy.approver_role_id):
                    if req.policy.reviewer_role_id in chosen and chosen[req.policy.reviewer_role_id].agent_id==agent.agent_id: return False
            return True
        def dfs(i):
            nonlocal solution
            if i==len(order): solution=dict(chosen); return True
            r=order[i]
            for a in cand[r.role_id]:
                if ok(r,a):
                    chosen[r.role_id]=a
                    if dfs(i+1): return True
                    chosen.pop(r.role_id,None)
            return False
        dfs(0)
        if solution is None:
            for r in rs: unassigned.append(_role_key(r))
            impossible_critical=impossible_critical or any(r.critical for r in rs); no_alternative=True
            continue
        for r in rs:
            a=solution[r.role_id]
            assignments.append(Assignment(task,r.role_id,a.agent_id,a.trust_domain,a.human))

    assignments=tuple(sorted(assignments,key=lambda a:(a.task_id,a.role_id,a.agent_id)))
    violations=_violations(assignments,req)
    unassigned=tuple(sorted(set(unassigned)))
    if violations:
        return AllocationResult(Decision.HOLD,NextAction.HOLD_SOD_REVIEW,Escalation.CRITICAL_SOD_VIOLATION,('SOD_CONFLICT_DETECTED','SELF_APPROVAL_OR_NONINDEPENDENT_REVIEW_BLOCKED','ASSIGNMENT_NOT_PROMOTED_TO_PERMISSION'),assignments,violations,unassigned,False)
    if unassigned:
        critical_keys={_role_key(r) for r in req.roles if r.critical}
        critical_unassigned=bool(critical_keys.intersection(unassigned)) or impossible_critical
        if req.policy.allow_human_escalation and no_alternative:
            esc=Escalation.INDEPENDENT_REVIEWER_UNAVAILABLE if any(x.endswith(':'+req.policy.reviewer_role_id) for x in unassigned) else (Escalation.UNASSIGNED_CRITICAL_ROLE if critical_unassigned else Escalation.NO_ALTERNATIVE_AGENT)
            return AllocationResult(Decision.HUMAN_APPROVAL,NextAction.HUMAN_APPROVAL_CANDIDATE,esc,('NO_VALID_AUTOMATIC_SOD_ASSIGNMENT','HUMAN_ESCALATION_CANDIDATE_ONLY','NO_AUTOMATIC_EXECUTION'),assignments,(),unassigned,False)
        esc=Escalation.UNASSIGNED_CRITICAL_ROLE if critical_unassigned else Escalation.NO_ALTERNATIVE_AGENT
        return AllocationResult(Decision.HOLD,NextAction.HOLD_SOD_REVIEW,esc,('REQUIRED_ROLE_UNASSIGNED','AUTOMATIC_EXECUTION_BLOCKED'),assignments,(),unassigned,False)
    return AllocationResult(Decision.ALLOW,NextAction.ASSIGNMENT_CANDIDATE,Escalation.NONE,('ALL_REQUIRED_ROLES_ASSIGNED','SOD_CONFLICT_MATRIX_SATISFIED','INDEPENDENT_REVIEWER_SATISFIED','ASSIGNMENT_IS_CANDIDATE_ONLY'),assignments,(),(),True)

def default_evaluation(): return evaluate(default_request())
def prepare_state(req,*,binding,state_epoch):
    if binding!=req.binding or state_epoch!=req.state_epoch: raise ValueError('binding/state_epoch mismatch')
    r=evaluate(req); cfp=_fp((req.request_id,binding,state_epoch)); rfp=_fp(req.roles); afp=_fp(req.agents); xfp=_fp(req.conflicts); pfp=_fp(req.policy); ofp=_fp(r); integ=_fp((cfp,rfp,afp,xfp,pfp,ofp,binding,state_epoch)); return PreparedAllocationState(req,r,cfp,rfp,afp,xfp,pfp,ofp,integ,binding,state_epoch)
def validate_prepared_integrity(st): return st.integrity_fingerprint==_fp((st.context_fingerprint,st.role_fingerprint,st.agent_fingerprint,st.conflict_fingerprint,st.policy_fingerprint,st.outcome_fingerprint,st.binding,st.state_epoch))
def evaluate_prepared(st,*,integrity_validated,current_context_fingerprint,current_role_fingerprint,current_agent_fingerprint,current_conflict_fingerprint,current_policy_fingerprint,current_outcome_fingerprint):
    if not integrity_validated or not validate_prepared_integrity(st): return _invalid('PREPARED_INTEGRITY_NOT_VALIDATED')
    if (current_context_fingerprint,current_role_fingerprint,current_agent_fingerprint,current_conflict_fingerprint,current_policy_fingerprint,current_outcome_fingerprint)!=(st.context_fingerprint,st.role_fingerprint,st.agent_fingerprint,st.conflict_fingerprint,st.policy_fingerprint,st.outcome_fingerprint): return _invalid('PREPARED_FINGERPRINT_MISMATCH')
    return st.result
def make_delta(old,new):
    oa={x.agent_id:x for x in old.request.agents}; na={x.agent_id:x for x in new.request.agents}; ca=tuple(na[k] for k in sorted(na) if k not in oa or _fp(na[k])!=_fp(oa[k])); ra=tuple(k for k in sorted(oa) if k not in na)
    oroles={_role_key(x):x for x in old.request.roles}; nroles={_role_key(x):x for x in new.request.roles}; cr=tuple(nroles[k] for k in sorted(nroles) if k not in oroles or _fp(nroles[k])!=_fp(oroles[k])); rr=tuple(k for k in sorted(oroles) if k not in nroles)
    return AllocationDelta(ca,ra,cr,rr,_manifest_fp(old.request),_manifest_fp(new.request))
def plan_missing_only(old,new):
    d=make_delta(old,new); ids=tuple([f'AGENT:{x.agent_id}' for x in d.changed_agents]+[f'REMOVED_AGENT:{x}' for x in d.removed_agent_ids]+[f'ROLE:{_role_key(x)}' for x in d.changed_roles]+[f'REMOVED_ROLE:{x}' for x in d.removed_role_keys]); meta=len(_canon({'from':d.from_manifest_fingerprint,'to':d.to_manifest_fingerprint,'ids':ids})); return MissingOnlyPlan(ids,meta,False)
