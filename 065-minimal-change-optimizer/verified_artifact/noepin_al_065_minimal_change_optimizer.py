"""NOEPIN AL 065 — Minimal-Change Optimizer — Sequential Successor V2.

Creator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
Implementation / analysis / documentation support: AI-assisted using ChatGPT
License / Rights: NOT SPECIFIED

Pure planning/control-plane optimizer. It computes a minimal candidate change set under the
supplied current/goal/change/policy model. It never edits files or objects, writes state,
commits a patch, deploys, grants permission, executes actions, or claims world truth,
safety, or action success.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, is_dataclass, replace
from enum import Enum
from hashlib import sha256
from itertools import combinations
import json
from typing import Any, Mapping, Sequence

CREATOR = "NOEPIN / のえぴん"
AI_SUPPORT = "AI-assisted implementation / analysis / documentation support using ChatGPT"
LICENSE_RIGHTS = "NOT SPECIFIED"
CANONICAL_ID = "NOEPIN-AL-065"

class Decision(str, Enum):
    ALLOW="ALLOW"; DENY="DENY"; HOLD="HOLD"; HUMAN_APPROVAL="HUMAN_APPROVAL"

@dataclass(frozen=True)
class ChangeSpec:
    change_id: str
    target: str
    contributes: tuple[str, ...]
    change_cost: float
    blast_radius: float
    risk_weight: float
    reversible: bool | None
    binding: str
    verified: bool
    revoked: bool
    policy_id: str
    policy_version: str
    authority_epoch: str

@dataclass(frozen=True)
class GoalClause:
    clause_id: str
    alternatives: tuple[str, ...]
    binding: str
    verified: bool
    revoked: bool

@dataclass(frozen=True)
class ApprovalEvidence:
    approval_id: str
    request_id: str
    role: str
    binding: str
    verified: bool
    revoked: bool
    independent: bool
    decision: str
    valid_from: int
    expires_at: int
    policy_id: str
    policy_version: str
    authority_epoch: str

@dataclass(frozen=True)
class ChangeRequest:
    request_id: str
    current_state_facts: tuple[str, ...]
    goal_state_id: str
    candidate_change_ids: tuple[str, ...]
    binding: str
    expected_policy_id: str
    expected_policy_version: str
    expected_authority_epoch: str
    created_at: int
    expires_at: int

@dataclass(frozen=True)
class ChangePolicy:
    policy_id: str
    version: str
    authority_epoch: str
    valid_from: int
    expires_at: int
    revoked: bool
    protected_targets: frozenset[str]
    approval_required_targets: frozenset[str]
    exact_search_limit: int
    max_candidate_changes: int
    max_request_age_seconds: int
    approval_role: str
    cost_weight: float
    blast_weight: float
    risk_weight: float

@dataclass(frozen=True)
class PreparedChangeState:
    binding: str
    valid: bool
    validation_reasons: tuple[str, ...]
    policy: ChangePolicy
    policy_fingerprint: str
    registry_fingerprint: str
    change_fingerprints: tuple[tuple[str,str], ...]
    goal_fingerprints: tuple[tuple[str,str], ...]
    changes: tuple[ChangeSpec, ...]
    goals: tuple[GoalClause, ...]
    contributions_index: tuple[tuple[str,tuple[str,...]], ...]
    generated_at: int

@dataclass(frozen=True)
class ChangeRegistryDelta:
    base_fingerprint: str
    target_fingerprint: str
    changed_changes: tuple[ChangeSpec, ...]
    removed_change_ids: tuple[str, ...]
    added_changes: tuple[ChangeSpec, ...]
    changed_goals: tuple[GoalClause, ...]
    removed_goal_ids: tuple[str, ...]
    added_goals: tuple[GoalClause, ...]

@dataclass(frozen=True)
class ChangeSyncPlan:
    registry_fingerprint: str
    missing_or_changed_change_ids: tuple[str, ...]
    missing_or_changed_goal_ids: tuple[str, ...]
    metadata_bytes_required: int
    full_bytes: int
    full_resend_required: bool
    permission_granted: bool=False
    write_authorized: bool=False
    patch_committed: bool=False
    deployment_authorized: bool=False
    action_execution_authorized: bool=False
    action_success_authorized: bool=False

@dataclass(frozen=True)
class MinimalChangeResult:
    decision: Decision
    reasons: tuple[str, ...]
    selected_change_candidate: tuple[str, ...]
    excluded_changes: tuple[str, ...]
    protected_change_ids: tuple[str, ...]
    uncovered_goal_clauses: tuple[str, ...]
    total_change_cost: float
    total_blast_radius: float
    total_risk_weight: float
    reversibility_score: int
    minimality_confirmed_under_supplied_model: bool
    next_gate_candidate: bool
    permission_granted: bool=False
    write_performed: bool=False
    patch_committed: bool=False
    deployment_executed: bool=False
    approval_executed: bool=False
    world_truth_proven: bool=False
    safety_proven: bool=False
    action_success: bool=False


def _norm(v: Any) -> Any:
    if isinstance(v, Enum): return v.value
    if is_dataclass(v): return {k:_norm(x) for k,x in asdict(v).items()}
    if isinstance(v, dict): return {str(k):_norm(v[k]) for k in sorted(v,key=lambda x:str(x))}
    if isinstance(v,(tuple,list)): return [_norm(x) for x in v]
    if isinstance(v,(set,frozenset)): return [_norm(x) for x in sorted(v,key=lambda x:str(x))]
    return v

def canonical_json(v: Any) -> str:
    return json.dumps(_norm(v),sort_keys=True,separators=(",",":"),ensure_ascii=False)

def fingerprint(v: Any) -> str:
    return sha256(canonical_json(v).encode("utf-8")).hexdigest()

def _fps(items: Sequence[Any], key: str) -> tuple[tuple[str,str], ...]:
    return tuple(sorted((str(getattr(x,key)),fingerprint(x)) for x in items))

def _registry_from_fps(binding: str, policy_fp: str, change_fp, goal_fp) -> str:
    return fingerprint({"binding":binding,"policy_fingerprint":policy_fp,"change_fingerprints":tuple(sorted(change_fp)),"goal_fingerprints":tuple(sorted(goal_fp))})

def registry_fingerprint(policy, changes, goals, binding: str) -> str:
    return _registry_from_fps(binding,fingerprint(policy),_fps(changes,"change_id"),_fps(goals,"clause_id"))


def prepare_state(policy: ChangePolicy, changes: Sequence[ChangeSpec], goals: Sequence[GoalClause], *, binding: str, now: int) -> PreparedChangeState:
    reasons=[]
    cids=[x.change_id for x in changes]; gids=[x.clause_id for x in goals]
    if len(cids)!=len(set(cids)): reasons.append("DUPLICATE_CHANGE_ID")
    if len(gids)!=len(set(gids)): reasons.append("DUPLICATE_GOAL_ID")
    if not binding: reasons.append("EMPTY_BINDING")
    if policy.revoked or not (policy.valid_from<=now<=policy.expires_at): reasons.append("POLICY_INVALID")
    if policy.exact_search_limit<0 or policy.max_candidate_changes<0: reasons.append("POLICY_LIMIT_INVALID")
    if min(policy.cost_weight,policy.blast_weight,policy.risk_weight)<0: reasons.append("POLICY_WEIGHT_INVALID")
    for c in changes:
        if not c.change_id or not c.target or not c.contributes: reasons.append("CHANGE_INCOMPLETE")
        if not c.verified or c.revoked: reasons.append("CHANGE_UNVERIFIED_OR_REVOKED")
        if c.binding!=binding: reasons.append("CHANGE_BINDING_MISMATCH")
        if (c.policy_id,c.policy_version,c.authority_epoch)!=(policy.policy_id,policy.version,policy.authority_epoch): reasons.append("CHANGE_POLICY_MISMATCH")
        if min(c.change_cost,c.blast_radius,c.risk_weight)<0: reasons.append("CHANGE_METRIC_INVALID")
    for g in goals:
        if not g.clause_id or not g.alternatives: reasons.append("GOAL_INCOMPLETE")
        if not g.verified or g.revoked: reasons.append("GOAL_UNVERIFIED_OR_REVOKED")
        if g.binding!=binding: reasons.append("GOAL_BINDING_MISMATCH")
    idx={}
    for c in changes:
        for fact in c.contributes: idx.setdefault(fact,[]).append(c.change_id)
    cfp=_fps(changes,"change_id"); gfp=_fps(goals,"clause_id"); pfp=fingerprint(policy)
    return PreparedChangeState(binding,not reasons,tuple(sorted(set(reasons))),policy,pfp,_registry_from_fps(binding,pfp,cfp,gfp),cfp,gfp,tuple(changes),tuple(goals),tuple(sorted((k,tuple(sorted(v))) for k,v in idx.items())),now)

def validate_prepared_integrity(p: PreparedChangeState) -> bool:
    return p.registry_fingerprint==_registry_from_fps(p.binding,p.policy_fingerprint,p.change_fingerprints,p.goal_fingerprints)

def _hold(reason: str, req: ChangeRequest, *, excluded=(), uncovered=()) -> MinimalChangeResult:
    return MinimalChangeResult(Decision.HOLD,(reason,),(),tuple(sorted(set(excluded))),(),tuple(sorted(set(uncovered))),0.0,0.0,0.0,0,False,False)

def _approval_valid(a: ApprovalEvidence|None, req: ChangeRequest, p: ChangePolicy, now: int) -> bool:
    return bool(a and a.verified and not a.revoked and a.independent and a.decision=="APPROVE" and a.request_id==req.request_id and a.role==p.approval_role and a.binding==req.binding and a.valid_from<=now<=a.expires_at and (a.policy_id,a.policy_version,a.authority_epoch)==(p.policy_id,p.version,p.authority_epoch))

def _covers(goals: Sequence[GoalClause], current: set[str], selected: Sequence[ChangeSpec]) -> tuple[bool, tuple[str,...]]:
    facts=set(current)
    for c in selected: facts.update(c.contributes)
    missing=tuple(sorted(g.clause_id for g in goals if not any(x in facts for x in g.alternatives)))
    return not missing,missing

def _score(sel: Sequence[ChangeSpec], p: ChangePolicy):
    cost=sum(x.change_cost for x in sel); blast=sum(x.blast_radius for x in sel); risk=sum(x.risk_weight for x in sel)
    weighted=p.cost_weight*cost+p.blast_weight*blast+p.risk_weight*risk
    return weighted,len(sel),cost,blast,risk

def evaluate_prepared(req: ChangeRequest, prepared: PreparedChangeState, approval: ApprovalEvidence|None=None, *, current_policy_fingerprint: str, current_registry_fingerprint: str, prepared_integrity_validated: bool, now: int) -> MinimalChangeResult:
    if not prepared_integrity_validated: return _hold("PREPARED_INTEGRITY_NOT_VALIDATED",req)
    if current_policy_fingerprint!=prepared.policy_fingerprint: return _hold("POLICY_FINGERPRINT_MISMATCH",req)
    if current_registry_fingerprint!=prepared.registry_fingerprint: return _hold("REGISTRY_FINGERPRINT_MISMATCH",req)
    if not prepared.valid: return _hold("PREPARED_STATE_INVALID:"+",".join(prepared.validation_reasons),req)
    p=prepared.policy
    if p.revoked or not (p.valid_from<=now<=p.expires_at): return _hold("POLICY_INVALID",req)
    if (req.expected_policy_id,req.expected_policy_version,req.expected_authority_epoch)!=(p.policy_id,p.version,p.authority_epoch): return _hold("POLICY_IDENTITY_MISMATCH",req)
    if req.binding!=prepared.binding: return _hold("REQUEST_BINDING_MISMATCH",req)
    if req.created_at>now or req.expires_at<now or now-req.created_at>p.max_request_age_seconds: return _hold("REQUEST_STALE_OR_EXPIRED",req)
    if len(req.candidate_change_ids)!=len(set(req.candidate_change_ids)): return _hold("DUPLICATE_CANDIDATE_CHANGE",req)
    if len(req.candidate_change_ids)>p.max_candidate_changes: return _hold("TOO_MANY_CANDIDATE_CHANGES",req)
    cmap={x.change_id:x for x in prepared.changes}
    if any(cid not in cmap for cid in req.candidate_change_ids): return _hold("UNKNOWN_CANDIDATE_CHANGE",req)
    candidates=[cmap[cid] for cid in req.candidate_change_ids]
    current=set(req.current_state_facts)
    # Goal facts already true -> no change is the exact minimum.
    done,missing0=_covers(prepared.goals,current,())
    if done:
        return MinimalChangeResult(Decision.ALLOW,("GOAL_ALREADY_SATISFIED_NO_CHANGE",),(),tuple(sorted(req.candidate_change_ids)),(),(),0.0,0.0,0.0,0,True,True)
    goal_facts={a for g in prepared.goals for a in g.alternatives}
    relevant=[c for c in candidates if any(f in goal_facts for f in c.contributes)]
    excluded_noncontrib=tuple(sorted(c.change_id for c in candidates if c not in relevant))
    protected=tuple(sorted(c.change_id for c in relevant if c.target in p.protected_targets))
    if protected:
        return MinimalChangeResult(Decision.DENY,("PROTECTED_TARGET_CHANGE",),(),excluded_noncontrib,protected,missing0,0.0,0.0,0.0,0,False,False)
    if not relevant: return _hold("GOAL_UNREACHABLE",req,excluded=excluded_noncontrib,uncovered=missing0)
    if len(relevant)>p.exact_search_limit: return _hold("EXACT_MINIMALITY_NOT_CONFIRMED_SEARCH_LIMIT",req,excluded=excluded_noncontrib,uncovered=missing0)
    feasible=[]
    for k in range(1,len(relevant)+1):
        for combo in combinations(relevant,k):
            ok,_=_covers(prepared.goals,current,combo)
            if ok: feasible.append(combo)
    if not feasible: return _hold("GOAL_UNREACHABLE",req,excluded=excluded_noncontrib,uncovered=missing0)
    ranked=[]
    for combo in feasible:
        weighted,count,cost,blast,risk=_score(combo,p)
        ranked.append((round(weighted,12),count,round(cost,12),round(blast,12),round(risk,12),combo))
    best_primary=min(x[:5] for x in ranked)
    tied=[x[-1] for x in ranked if x[:5]==best_primary]
    # Canonical fail-safe: equal solutions require safety/reversibility comparison.
    if len(tied)>1:
        if any(any(c.reversible is None for c in combo) for combo in tied):
            return _hold("TIED_SOLUTION_SAFETY_NOT_COMPARABLE",req,excluded=excluded_noncontrib)
        rev_scores=[sum(1 for c in combo if c.reversible is True) for combo in tied]
        best_rev=max(rev_scores)
        tied=[combo for combo,rs in zip(tied,rev_scores) if rs==best_rev]
    # If still equal and all safety fields are known/equal, deterministic ID order is non-authoritative tie breaking.
    selected=min(tied,key=lambda combo:tuple(sorted(c.change_id for c in combo)))
    selected_ids=tuple(sorted(c.change_id for c in selected))
    excluded=tuple(sorted(set(req.candidate_change_ids)-set(selected_ids)))
    _,_,cost,blast,risk=_score(selected,p)
    rev=sum(1 for c in selected if c.reversible is True)
    approval_needed=any(c.target in p.approval_required_targets for c in selected)
    reasons=["MINIMAL_CHANGE_CANDIDATE"]
    if excluded_noncontrib: reasons.append("NON_CONTRIBUTING_CHANGES_EXCLUDED")
    if len(feasible)>1: reasons.append("MINIMAL_OBJECTIVE_SELECTED")
    if approval_needed and not _approval_valid(approval,req,p,now):
        reasons.append("HUMAN_APPROVAL_REQUIRED")
        return MinimalChangeResult(Decision.HUMAN_APPROVAL,tuple(reasons),selected_ids,excluded,(),(),cost,blast,risk,rev,True,False)
    return MinimalChangeResult(Decision.ALLOW,tuple(reasons),selected_ids,excluded,(),(),cost,blast,risk,rev,True,True)

def evaluate(req: ChangeRequest, policy: ChangePolicy, changes: Sequence[ChangeSpec], goals: Sequence[GoalClause], approval: ApprovalEvidence|None=None, *, now: int) -> MinimalChangeResult:
    ps=prepare_state(policy,changes,goals,binding=req.binding,now=now)
    return evaluate_prepared(req,ps,approval,current_policy_fingerprint=ps.policy_fingerprint,current_registry_fingerprint=ps.registry_fingerprint,prepared_integrity_validated=validate_prepared_integrity(ps),now=now)


def _diff(base_items,target_items,key):
    b={getattr(x,key):x for x in base_items}; t={getattr(x,key):x for x in target_items}
    changed=tuple(t[k] for k in sorted(set(b)&set(t)) if fingerprint(b[k])!=fingerprint(t[k]))
    removed=tuple(sorted(set(b)-set(t))); added=tuple(t[k] for k in sorted(set(t)-set(b)))
    return changed,removed,added

def build_delta(base: PreparedChangeState,target: PreparedChangeState) -> ChangeRegistryDelta:
    cc,rc,ac=_diff(base.changes,target.changes,"change_id"); cg,rg,ag=_diff(base.goals,target.goals,"clause_id")
    return ChangeRegistryDelta(base.registry_fingerprint,target.registry_fingerprint,cc,rc,ac,cg,rg,ag)

def apply_delta(base: PreparedChangeState, delta: ChangeRegistryDelta, *, now: int) -> PreparedChangeState:
    if base.registry_fingerprint!=delta.base_fingerprint: raise ValueError("DELTA_BASE_FINGERPRINT_MISMATCH")
    c={x.change_id:x for x in base.changes}; g={x.clause_id:x for x in base.goals}
    for k in delta.removed_change_ids: c.pop(k,None)
    for x in delta.changed_changes+delta.added_changes: c[x.change_id]=x
    for k in delta.removed_goal_ids: g.pop(k,None)
    for x in delta.changed_goals+delta.added_goals: g[x.clause_id]=x
    out=prepare_state(base.policy,tuple(c[k] for k in sorted(c)),tuple(g[k] for k in sorted(g)),binding=base.binding,now=now)
    if out.registry_fingerprint!=delta.target_fingerprint: raise ValueError("DELTA_TARGET_FINGERPRINT_MISMATCH")
    return out

def full_registry_bytes(p: PreparedChangeState) -> int:
    return len(canonical_json({"binding":p.binding,"policy":p.policy,"changes":p.changes,"goals":p.goals}).encode())

def delta_bytes(d: ChangeRegistryDelta) -> int: return len(canonical_json(d).encode())

def missing_only_sync_plan(p: PreparedChangeState, remote_fingerprints: Mapping[str,Mapping[str,str]]) -> ChangeSyncPlan:
    cf=dict(p.change_fingerprints); gf=dict(p.goal_fingerprints); rc=remote_fingerprints.get("changes",{}); rg=remote_fingerprints.get("goals",{})
    mc=tuple(sorted(k for k,v in cf.items() if rc.get(k)!=v)); mg=tuple(sorted(k for k,v in gf.items() if rg.get(k)!=v))
    meta=canonical_json({"changes":{k:cf[k] for k in mc},"goals":{k:gf[k] for k in mg},"registry":p.registry_fingerprint})
    fb=full_registry_bytes(p); mb=len(meta.encode())
    return ChangeSyncPlan(p.registry_fingerprint,mc,mg,mb,fb,mb>=fb)


def default_policy(now: int) -> ChangePolicy:
    return ChangePolicy("MC-POLICY","1","MC-EPOCH",now-1000,now+100000,False,frozenset({"TARGET-PROTECTED"}),frozenset({"TARGET-APPROVAL"}),16,32,3600,"OWNER_APPROVER",1.0,2.0,3.0)

def default_changes() -> tuple[ChangeSpec,...]:
    common=dict(binding="MC-BIND",verified=True,revoked=False,policy_id="MC-POLICY",policy_version="1",authority_epoch="MC-EPOCH")
    return (
      ChangeSpec("CHG-MIN","TARGET-A",("GOAL-A","GOAL-B"),1.0,0.2,0.1,True,**common),
      ChangeSpec("CHG-A","TARGET-A",("GOAL-A",),0.7,0.2,0.1,True,**common),
      ChangeSpec("CHG-B","TARGET-B",("GOAL-B",),0.7,0.2,0.1,True,**common),
      ChangeSpec("CHG-NOISE","TARGET-NOISE",("OTHER",),0.1,0.1,0.1,True,**common),
      ChangeSpec("CHG-PROTECTED","TARGET-PROTECTED",("GOAL-A",),0.1,0.0,0.0,True,**common),
      ChangeSpec("CHG-APPROVAL","TARGET-APPROVAL",("GOAL-A","GOAL-B"),0.5,0.1,0.1,True,**common),
      ChangeSpec("CHG-TIE-REV","TARGET-C",("GOAL-A","GOAL-B"),1.0,0.2,0.1,True,**common),
      ChangeSpec("CHG-TIE-IRREV","TARGET-D",("GOAL-A","GOAL-B"),1.0,0.2,0.1,False,**common),
      ChangeSpec("CHG-TIE-UNKNOWN","TARGET-E",("GOAL-A","GOAL-B"),1.0,0.2,0.1,None,**common),
    )

def default_goals() -> tuple[GoalClause,...]:
    return (GoalClause("G1",("GOAL-A",),"MC-BIND",True,False),GoalClause("G2",("GOAL-B",),"MC-BIND",True,False))

def default_request(now: int) -> ChangeRequest:
    return ChangeRequest("REQ-065",(),"GOAL-STATE-1",("CHG-MIN","CHG-A","CHG-B","CHG-NOISE"),"MC-BIND","MC-POLICY","1","MC-EPOCH",now-10,now+1000)

def default_approval(now: int) -> ApprovalEvidence:
    return ApprovalEvidence("APR-065","REQ-065","OWNER_APPROVER","MC-BIND",True,False,True,"APPROVE",now-10,now+1000,"MC-POLICY","1","MC-EPOCH")
