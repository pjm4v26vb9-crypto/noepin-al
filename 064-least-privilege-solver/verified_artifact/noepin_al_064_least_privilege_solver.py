"""NOEPIN AL 064 — Least-Privilege Solver — Sequential Successor V2.

Creator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
Implementation / analysis / documentation support: AI-assisted using ChatGPT
License / Rights: NOT SPECIFIED

Pure algorithm/control-plane least-privilege evaluator. It minimizes capability candidates
inside the supplied request/role/policy model. It never grants permission, issues tokens,
mints credentials, changes roles, activates capabilities, executes actions, or claims
world truth / safety / action success.
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
CANONICAL_ID = "NOEPIN-AL-064"


class Decision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    HOLD = "HOLD"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"


@dataclass(frozen=True)
class CapabilitySpec:
    capability_id: str
    binding: str
    verified: bool
    revoked: bool
    valid_from: int
    expires_at: int
    risk_weight: float
    policy_id: str
    policy_version: str
    authority_epoch: str


@dataclass(frozen=True)
class CapabilityEdge:
    edge_id: str
    source_capability: str
    implied_capability: str
    binding: str
    verified: bool
    revoked: bool
    policy_id: str
    policy_version: str
    authority_epoch: str


@dataclass(frozen=True)
class RoleProfile:
    role_id: str
    version: str
    binding: str
    capability_ids: tuple[str, ...]
    parent_role_ids: tuple[str, ...]
    verified: bool
    revoked: bool
    valid_from: int
    expires_at: int
    policy_id: str
    policy_version: str
    authority_epoch: str


@dataclass(frozen=True)
class ActionSpec:
    action_id: str
    goal_id: str
    binding: str
    verified: bool
    revoked: bool


@dataclass(frozen=True)
class RequirementClause:
    clause_id: str
    action_id: str
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
class LeastPrivilegeRequest:
    request_id: str
    goal_id: str
    action_id: str
    role_id: str
    requested_capabilities: tuple[str, ...]
    binding: str
    expected_policy_id: str
    expected_policy_version: str
    expected_authority_epoch: str
    expected_role_version: str
    created_at: int
    expires_at: int


@dataclass(frozen=True)
class LeastPrivilegePolicy:
    policy_id: str
    version: str
    authority_epoch: str
    valid_from: int
    expires_at: int
    revoked: bool
    forbidden_capabilities: frozenset[str]
    approval_required_capabilities: frozenset[str]
    exact_search_limit: int
    max_requested_capabilities: int
    max_request_age_seconds: int
    approval_role: str


@dataclass(frozen=True)
class PreparedPrivilegeState:
    binding: str
    valid: bool
    validation_reasons: tuple[str, ...]
    policy: LeastPrivilegePolicy
    policy_fingerprint: str
    registry_fingerprint: str
    capability_fingerprints: tuple[tuple[str, str], ...]
    edge_fingerprints: tuple[tuple[str, str], ...]
    role_fingerprints: tuple[tuple[str, str], ...]
    action_fingerprints: tuple[tuple[str, str], ...]
    requirement_fingerprints: tuple[tuple[str, str], ...]
    capabilities: tuple[CapabilitySpec, ...]
    edges: tuple[CapabilityEdge, ...]
    roles: tuple[RoleProfile, ...]
    actions: tuple[ActionSpec, ...]
    requirements: tuple[RequirementClause, ...]
    implication_closure: tuple[tuple[str, tuple[str, ...]], ...]
    role_effective_capabilities: tuple[tuple[str, tuple[str, ...]], ...]
    requirements_by_action: tuple[tuple[str, tuple[str, ...]], ...]
    generated_at: int


@dataclass(frozen=True)
class PrivilegeRegistryDelta:
    base_fingerprint: str
    target_fingerprint: str
    changed_capabilities: tuple[CapabilitySpec, ...]
    removed_capability_ids: tuple[str, ...]
    added_capabilities: tuple[CapabilitySpec, ...]
    changed_edges: tuple[CapabilityEdge, ...]
    removed_edge_ids: tuple[str, ...]
    added_edges: tuple[CapabilityEdge, ...]
    changed_roles: tuple[RoleProfile, ...]
    removed_role_ids: tuple[str, ...]
    added_roles: tuple[RoleProfile, ...]
    changed_actions: tuple[ActionSpec, ...]
    removed_action_ids: tuple[str, ...]
    added_actions: tuple[ActionSpec, ...]
    changed_requirements: tuple[RequirementClause, ...]
    removed_requirement_ids: tuple[str, ...]
    added_requirements: tuple[RequirementClause, ...]


@dataclass(frozen=True)
class PrivilegeSyncPlan:
    registry_fingerprint: str
    missing_or_changed_capability_ids: tuple[str, ...]
    missing_or_changed_edge_ids: tuple[str, ...]
    missing_or_changed_role_ids: tuple[str, ...]
    missing_or_changed_action_ids: tuple[str, ...]
    missing_or_changed_requirement_ids: tuple[str, ...]
    metadata_bytes_required: int
    full_bytes: int
    full_resend_required: bool
    permission_granted: bool = False
    token_issued: bool = False
    credential_minted: bool = False
    role_changed: bool = False
    capability_activated: bool = False
    action_execution_authorized: bool = False
    action_success_authorized: bool = False


@dataclass(frozen=True)
class LeastPrivilegeResult:
    decision: Decision
    reasons: tuple[str, ...]
    requested_capabilities: tuple[str, ...]
    minimal_capability_candidate: tuple[str, ...]
    excess_capabilities: tuple[str, ...]
    missing_capability_alternatives: tuple[str, ...]
    effective_role_capabilities: tuple[str, ...]
    covered_requirement_ids: tuple[str, ...]
    minimality_confirmed_under_supplied_model: bool
    approval_required: bool
    next_gate_candidate: bool
    permission_granted: bool = False
    token_issued: bool = False
    credential_minted: bool = False
    capability_activated: bool = False
    role_changed: bool = False
    policy_changed: bool = False
    approval_executed: bool = False
    action_executed: bool = False
    world_truth_proven: bool = False
    safety_proven: bool = False
    action_success: bool = False


def _norm(v: Any) -> Any:
    if isinstance(v, Enum):
        return v.value
    if is_dataclass(v):
        return {k: _norm(x) for k, x in asdict(v).items()}
    if isinstance(v, dict):
        return {str(k): _norm(v[k]) for k in sorted(v, key=lambda x: str(x))}
    if isinstance(v, (tuple, list)):
        return [_norm(x) for x in v]
    if isinstance(v, (set, frozenset)):
        return [_norm(x) for x in sorted(v, key=lambda x: str(x))]
    return v


def canonical_json(v: Any) -> str:
    return json.dumps(_norm(v), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def fingerprint(v: Any) -> str:
    return sha256(canonical_json(v).encode("utf-8")).hexdigest()


def _fps(items: Sequence[Any], key: str) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((str(getattr(x, key)), fingerprint(x)) for x in items))


def _registry_from_fps(binding: str, policy_fp: str, cap_fp, edge_fp, role_fp, action_fp, req_fp) -> str:
    return fingerprint({
        "binding": binding,
        "policy_fingerprint": policy_fp,
        "capability_fingerprints": tuple(sorted(cap_fp)),
        "edge_fingerprints": tuple(sorted(edge_fp)),
        "role_fingerprints": tuple(sorted(role_fp)),
        "action_fingerprints": tuple(sorted(action_fp)),
        "requirement_fingerprints": tuple(sorted(req_fp)),
    })


def registry_fingerprint(policy: LeastPrivilegePolicy, capabilities, edges, roles, actions, requirements, binding: str) -> str:
    return _registry_from_fps(
        binding, fingerprint(policy), _fps(capabilities, "capability_id"), _fps(edges, "edge_id"),
        _fps(roles, "role_id"), _fps(actions, "action_id"), _fps(requirements, "clause_id")
    )


def _has_cycle(nodes: Sequence[str], adjacency: Mapping[str, Sequence[str]]) -> bool:
    state: dict[str, int] = {}
    def dfs(n: str) -> bool:
        if state.get(n) == 1:
            return True
        if state.get(n) == 2:
            return False
        state[n] = 1
        for m in adjacency.get(n, ()):
            if dfs(m):
                return True
        state[n] = 2
        return False
    return any(dfs(n) for n in nodes if state.get(n, 0) == 0)


def _closure(start: str, adjacency: Mapping[str, Sequence[str]]) -> tuple[str, ...]:
    seen: set[str] = set()
    stack = [start]
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        stack.extend(adjacency.get(n, ()))
    return tuple(sorted(seen))


def prepare_state(
    policy: LeastPrivilegePolicy,
    capabilities: Sequence[CapabilitySpec],
    edges: Sequence[CapabilityEdge],
    roles: Sequence[RoleProfile],
    actions: Sequence[ActionSpec],
    requirements: Sequence[RequirementClause],
    *, binding: str, now: int,
) -> PreparedPrivilegeState:
    reasons: list[str] = []
    def uniq(items, key, code):
        vals=[getattr(x,key) for x in items]
        if len(vals) != len(set(vals)): reasons.append(code)
    uniq(capabilities,"capability_id","DUPLICATE_CAPABILITY_ID")
    uniq(edges,"edge_id","DUPLICATE_EDGE_ID")
    uniq(roles,"role_id","DUPLICATE_ROLE_ID")
    uniq(actions,"action_id","DUPLICATE_ACTION_ID")
    uniq(requirements,"clause_id","DUPLICATE_REQUIREMENT_ID")
    capmap={x.capability_id:x for x in capabilities}
    rolemap={x.role_id:x for x in roles}
    actionmap={x.action_id:x for x in actions}
    if not binding: reasons.append("EMPTY_BINDING")
    if policy.revoked or now < policy.valid_from or now > policy.expires_at: reasons.append("POLICY_INVALID")
    if policy.exact_search_limit < 0 or policy.max_requested_capabilities < 0: reasons.append("POLICY_LIMIT_INVALID")
    cap_adj: dict[str,list[str]]={k:[] for k in capmap}
    for e in edges:
        if e.source_capability not in capmap or e.implied_capability not in capmap: reasons.append("EDGE_UNKNOWN_CAPABILITY")
        else: cap_adj[e.source_capability].append(e.implied_capability)
        if not e.verified or e.revoked: reasons.append("EDGE_UNVERIFIED_OR_REVOKED")
        if e.binding != binding: reasons.append("EDGE_BINDING_MISMATCH")
        if (e.policy_id,e.policy_version,e.authority_epoch)!=(policy.policy_id,policy.version,policy.authority_epoch): reasons.append("EDGE_POLICY_MISMATCH")
    if _has_cycle(tuple(capmap),cap_adj): reasons.append("CAPABILITY_DAG_CYCLE")
    role_adj: dict[str,list[str]]={k:list(v.parent_role_ids) for k,v in rolemap.items()}
    for r in roles:
        if any(p not in rolemap for p in r.parent_role_ids): reasons.append("ROLE_UNKNOWN_PARENT")
        if any(c not in capmap for c in r.capability_ids): reasons.append("ROLE_UNKNOWN_CAPABILITY")
    if _has_cycle(tuple(rolemap),role_adj): reasons.append("ROLE_HIERARCHY_CYCLE")
    for a in actions:
        if a.binding != binding or not a.verified or a.revoked: reasons.append("ACTION_INVALID")
    for q in requirements:
        if q.action_id not in actionmap: reasons.append("REQUIREMENT_UNKNOWN_ACTION")
        if not q.alternatives or any(c not in capmap for c in q.alternatives): reasons.append("REQUIREMENT_UNKNOWN_CAPABILITY")
        if q.binding != binding or not q.verified or q.revoked: reasons.append("REQUIREMENT_INVALID")
    implication=tuple(sorted((c,_closure(c,cap_adj)) for c in capmap)) if "CAPABILITY_DAG_CYCLE" not in reasons else tuple((c,(c,)) for c in sorted(capmap))
    effective: list[tuple[str,tuple[str,...]]]=[]
    if "ROLE_HIERARCHY_CYCLE" not in reasons and "ROLE_UNKNOWN_PARENT" not in reasons:
        cache: dict[str,set[str]]={}
        def role_caps(rid: str) -> set[str]:
            if rid in cache: return set(cache[rid])
            r=rolemap[rid]; out=set(r.capability_ids)
            for p in r.parent_role_ids: out |= role_caps(p)
            cache[rid]=set(out); return out
        for rid in sorted(rolemap): effective.append((rid,tuple(sorted(role_caps(rid)))))
    req_by_action: dict[str,list[str]]={a.action_id:[] for a in actions}
    for q in requirements: req_by_action.setdefault(q.action_id,[]).append(q.clause_id)
    cap_fp=_fps(capabilities,"capability_id"); edge_fp=_fps(edges,"edge_id"); role_fp=_fps(roles,"role_id"); action_fp=_fps(actions,"action_id"); req_fp=_fps(requirements,"clause_id")
    reg=_registry_from_fps(binding,fingerprint(policy),cap_fp,edge_fp,role_fp,action_fp,req_fp)
    return PreparedPrivilegeState(
        binding=binding,valid=not reasons,validation_reasons=tuple(sorted(set(reasons))),policy=policy,
        policy_fingerprint=fingerprint(policy),registry_fingerprint=reg,
        capability_fingerprints=cap_fp,edge_fingerprints=edge_fp,role_fingerprints=role_fp,action_fingerprints=action_fp,requirement_fingerprints=req_fp,
        capabilities=tuple(capabilities),edges=tuple(edges),roles=tuple(roles),actions=tuple(actions),requirements=tuple(requirements),
        implication_closure=implication,role_effective_capabilities=tuple(effective),
        requirements_by_action=tuple(sorted((k,tuple(sorted(v))) for k,v in req_by_action.items())),generated_at=now)


def validate_prepared_integrity(p: PreparedPrivilegeState) -> bool:
    return p.registry_fingerprint == _registry_from_fps(
        p.binding,p.policy_fingerprint,p.capability_fingerprints,p.edge_fingerprints,p.role_fingerprints,p.action_fingerprints,p.requirement_fingerprints
    )


def _hold(reason: str, req: LeastPrivilegeRequest, *, effective=(), missing=()) -> LeastPrivilegeResult:
    return LeastPrivilegeResult(Decision.HOLD,(reason,),tuple(sorted(set(req.requested_capabilities))),(),(),tuple(sorted(set(missing))),tuple(sorted(set(effective))),(),False,False,False)


def _approval_valid(a: ApprovalEvidence | None, req: LeastPrivilegeRequest, p: LeastPrivilegePolicy, now: int) -> bool:
    return bool(a and a.verified and not a.revoked and a.independent and a.decision=="APPROVE" and a.request_id==req.request_id and a.binding==req.binding and a.role==p.approval_role and a.valid_from<=now<=a.expires_at and (a.policy_id,a.policy_version,a.authority_epoch)==(p.policy_id,p.version,p.authority_epoch))


def evaluate_prepared(
    req: LeastPrivilegeRequest,
    prepared: PreparedPrivilegeState,
    approval: ApprovalEvidence | None = None,
    *, current_policy_fingerprint: str,
    current_registry_fingerprint: str,
    prepared_integrity_validated: bool,
    now: int,
) -> LeastPrivilegeResult:
    if not prepared_integrity_validated: return _hold("PREPARED_INTEGRITY_NOT_VALIDATED",req)
    if current_policy_fingerprint != prepared.policy_fingerprint: return _hold("POLICY_FINGERPRINT_MISMATCH",req)
    if current_registry_fingerprint != prepared.registry_fingerprint: return _hold("REGISTRY_FINGERPRINT_MISMATCH",req)
    if not prepared.valid: return _hold("PREPARED_STATE_INVALID:"+",".join(prepared.validation_reasons),req)
    p=prepared.policy
    if p.revoked or not (p.valid_from<=now<=p.expires_at): return _hold("POLICY_INVALID",req)
    if (req.expected_policy_id,req.expected_policy_version,req.expected_authority_epoch)!=(p.policy_id,p.version,p.authority_epoch): return _hold("POLICY_IDENTITY_MISMATCH",req)
    if req.expires_at < now or req.created_at > now or now-req.created_at > p.max_request_age_seconds: return _hold("REQUEST_STALE_OR_EXPIRED",req)
    if req.binding != prepared.binding: return _hold("REQUEST_BINDING_MISMATCH",req)
    if len(req.requested_capabilities) != len(set(req.requested_capabilities)): return _hold("DUPLICATE_REQUESTED_CAPABILITY",req)
    if len(req.requested_capabilities) > p.max_requested_capabilities: return _hold("REQUESTED_CAPABILITY_LIMIT_EXCEEDED",req)
    capmap=dict((x.capability_id,x) for x in prepared.capabilities)
    rolemap=dict((x.role_id,x) for x in prepared.roles)
    actionmap=dict((x.action_id,x) for x in prepared.actions)
    reqmap=dict((x.clause_id,x) for x in prepared.requirements)
    closure=dict(prepared.implication_closure)
    effective_map=dict(prepared.role_effective_capabilities)
    req_by_action=dict(prepared.requirements_by_action)
    if req.role_id not in rolemap: return _hold("ROLE_NOT_FOUND",req)
    role=rolemap[req.role_id]
    if role.revoked or not role.verified or not (role.valid_from<=now<=role.expires_at): return _hold("ROLE_INVALID",req)
    if role.binding!=req.binding or role.version!=req.expected_role_version: return _hold("ROLE_IDENTITY_MISMATCH",req)
    if (role.policy_id,role.policy_version,role.authority_epoch)!=(p.policy_id,p.version,p.authority_epoch): return _hold("ROLE_POLICY_MISMATCH",req)
    effective=tuple(effective_map.get(req.role_id,()))
    requested=set(req.requested_capabilities)
    unknown=sorted(requested-set(capmap))
    if unknown: return _hold("UNKNOWN_REQUESTED_CAPABILITY",req,effective=effective,missing=unknown)
    outside=sorted(requested-set(effective))
    if outside: return _hold("REQUESTED_CAPABILITY_OUTSIDE_ROLE",req,effective=effective,missing=outside)
    for cid in sorted(requested):
        c=capmap[cid]
        if not c.verified or c.revoked or not (c.valid_from<=now<=c.expires_at): return _hold("REQUESTED_CAPABILITY_INVALID",req,effective=effective,missing=(cid,))
        if c.binding!=req.binding or (c.policy_id,c.policy_version,c.authority_epoch)!=(p.policy_id,p.version,p.authority_epoch): return _hold("CAPABILITY_IDENTITY_MISMATCH",req,effective=effective,missing=(cid,))
    if req.action_id not in actionmap: return _hold("ACTION_NOT_FOUND",req,effective=effective)
    action=actionmap[req.action_id]
    if not action.verified or action.revoked or action.binding!=req.binding or action.goal_id!=req.goal_id: return _hold("ACTION_GOAL_OR_BINDING_INVALID",req,effective=effective)
    clauses=[reqmap[x] for x in req_by_action.get(action.action_id,())]
    if not clauses: return _hold("NO_REQUIREMENT_CLAUSES",req,effective=effective)
    # A clause whose every explicit alternative is forbidden cannot be satisfied without violating policy.
    for q in clauses:
        if all(c in p.forbidden_capabilities for c in q.alternatives):
            return LeastPrivilegeResult(Decision.DENY,("FORBIDDEN_CAPABILITY_REQUIRED",),tuple(sorted(requested)),(),tuple(sorted(requested)),tuple(sorted(q.alternatives)),tuple(sorted(effective)),(),True,False,False)
    candidates=tuple(sorted(c for c in requested if c not in p.forbidden_capabilities))
    if len(candidates)>p.exact_search_limit: return _hold("MINIMALITY_UNCONFIRMED_SEARCH_LIMIT",req,effective=effective)
    def expanded(subset: Sequence[str]) -> set[str]:
        out:set[str]=set()
        for c in subset: out.update(closure.get(c,(c,)))
        return out
    def covers(subset: Sequence[str]) -> bool:
        e=expanded(subset)
        return all(any(a in e for a in q.alternatives) for q in clauses)
    best: tuple[str,...] | None=None
    best_risk=float("inf")
    for size in range(len(candidates)+1):
        found=[]
        for combo in combinations(candidates,size):
            if covers(combo):
                risk=sum(capmap[c].risk_weight for c in combo)
                found.append((risk,combo))
        if found:
            found.sort(key=lambda x:(x[0],x[1])); best=tuple(found[0][1]); best_risk=found[0][0]; break
    if best is None:
        missing=sorted({a for q in clauses for a in q.alternatives if a not in expanded(candidates) and a not in p.forbidden_capabilities})
        return _hold("CAPABILITY_INSUFFICIENT",req,effective=effective,missing=missing)
    expanded_best=expanded(best)
    covered=tuple(sorted(q.clause_id for q in clauses if any(a in expanded_best for a in q.alternatives)))
    excess=tuple(sorted(requested-set(best)))
    reasons=["MINIMUM_CONFIRMED_UNDER_SUPPLIED_MODEL"]
    if excess: reasons.append("REQUEST_SHRUNK_TO_MINIMUM")
    if any(c in p.forbidden_capabilities for c in requested): reasons.append("FORBIDDEN_EXCESS_REMOVED")
    approval_required=any(c in p.approval_required_capabilities for c in best)
    if approval_required and not _approval_valid(approval,req,p,now):
        return LeastPrivilegeResult(Decision.HUMAN_APPROVAL,tuple(reasons+["INDEPENDENT_APPROVAL_REQUIRED"]),tuple(sorted(requested)),best,excess,(),tuple(sorted(effective)),covered,True,True,False)
    return LeastPrivilegeResult(Decision.ALLOW,tuple(reasons),tuple(sorted(requested)),best,excess,(),tuple(sorted(effective)),covered,True,approval_required,True)


def evaluate(req, policy, capabilities, edges, roles, actions, requirements, approval=None, *, now: int) -> LeastPrivilegeResult:
    prepared=prepare_state(policy,capabilities,edges,roles,actions,requirements,binding=req.binding,now=now)
    return evaluate_prepared(req,prepared,approval,current_policy_fingerprint=fingerprint(policy),current_registry_fingerprint=prepared.registry_fingerprint,prepared_integrity_validated=validate_prepared_integrity(prepared),now=now)


def _diff(base: Sequence[Any], target: Sequence[Any], key: str):
    b={getattr(x,key):x for x in base}; t={getattr(x,key):x for x in target}
    changed=tuple(t[k] for k in sorted(set(b)&set(t)) if fingerprint(b[k])!=fingerprint(t[k]))
    removed=tuple(sorted(set(b)-set(t))); added=tuple(t[k] for k in sorted(set(t)-set(b)))
    return changed,removed,added


def build_delta(base: PreparedPrivilegeState, target: PreparedPrivilegeState) -> PrivilegeRegistryDelta:
    c,cr,ca=_diff(base.capabilities,target.capabilities,"capability_id")
    e,er,ea=_diff(base.edges,target.edges,"edge_id")
    r,rr,ra=_diff(base.roles,target.roles,"role_id")
    a,ar,aa=_diff(base.actions,target.actions,"action_id")
    q,qr,qa=_diff(base.requirements,target.requirements,"clause_id")
    return PrivilegeRegistryDelta(base.registry_fingerprint,target.registry_fingerprint,c,cr,ca,e,er,ea,r,rr,ra,a,ar,aa,q,qr,qa)


def _apply_items(base: Sequence[Any], changed: Sequence[Any], removed: Sequence[str], added: Sequence[Any], key: str):
    d={getattr(x,key):x for x in base}
    for k in removed: d.pop(k,None)
    for x in changed: d[getattr(x,key)]=x
    for x in added: d[getattr(x,key)]=x
    return tuple(d[k] for k in sorted(d))


def apply_delta(base: PreparedPrivilegeState, delta: PrivilegeRegistryDelta, *, now: int) -> PreparedPrivilegeState:
    if base.registry_fingerprint!=delta.base_fingerprint: raise ValueError("BASE_FINGERPRINT_MISMATCH")
    caps=_apply_items(base.capabilities,delta.changed_capabilities,delta.removed_capability_ids,delta.added_capabilities,"capability_id")
    edges=_apply_items(base.edges,delta.changed_edges,delta.removed_edge_ids,delta.added_edges,"edge_id")
    roles=_apply_items(base.roles,delta.changed_roles,delta.removed_role_ids,delta.added_roles,"role_id")
    actions=_apply_items(base.actions,delta.changed_actions,delta.removed_action_ids,delta.added_actions,"action_id")
    reqs=_apply_items(base.requirements,delta.changed_requirements,delta.removed_requirement_ids,delta.added_requirements,"clause_id")
    out=prepare_state(base.policy,caps,edges,roles,actions,reqs,binding=base.binding,now=now)
    if out.registry_fingerprint!=delta.target_fingerprint: raise ValueError("TARGET_FINGERPRINT_MISMATCH")
    return out


def full_registry_bytes(p: PreparedPrivilegeState) -> int:
    return len(canonical_json({"binding":p.binding,"policy":p.policy,"capabilities":p.capabilities,"edges":p.edges,"roles":p.roles,"actions":p.actions,"requirements":p.requirements}).encode("utf-8"))


def delta_bytes(d: PrivilegeRegistryDelta) -> int:
    return len(canonical_json(d).encode("utf-8"))


def missing_only_sync_plan(p: PreparedPrivilegeState, remote: Mapping[str, Mapping[str,str]]) -> PrivilegeSyncPlan:
    groups={
        "capabilities":dict(p.capability_fingerprints),"edges":dict(p.edge_fingerprints),"roles":dict(p.role_fingerprints),
        "actions":dict(p.action_fingerprints),"requirements":dict(p.requirement_fingerprints),
    }
    miss={k:tuple(sorted(i for i,fp in v.items() if remote.get(k,{}).get(i)!=fp)) for k,v in groups.items()}
    meta=len(canonical_json({k:{i:groups[k][i] for i in ids} for k,ids in miss.items()}).encode("utf-8"))
    full=full_registry_bytes(p)
    return PrivilegeSyncPlan(p.registry_fingerprint,miss["capabilities"],miss["edges"],miss["roles"],miss["actions"],miss["requirements"],meta,full,meta>=full)


def default_policy(now: int) -> LeastPrivilegePolicy:
    return LeastPrivilegePolicy("LP-POLICY","1","LP-EPOCH",now-1000,now+10000,False,frozenset({"CAP_WRITE_GLOBAL","CAP_ADMIN"}),frozenset({"CAP_ELEVATED_REVIEW"}),18,24,600,"SECURITY_REVIEWER")


def default_capabilities(now: int) -> tuple[CapabilitySpec,...]:
    def c(cid,risk): return CapabilitySpec(cid,"LP-BIND",True,False,now-1000,now+10000,risk,"LP-POLICY","1","LP-EPOCH")
    return (c("CAP_READ",1),c("CAP_WRITE_SCOPED",2),c("CAP_WRITE_GLOBAL",8),c("CAP_NOTIFY",1),c("CAP_ELEVATED_REVIEW",5),c("CAP_ADMIN",10))


def default_edges(now: int | None=None) -> tuple[CapabilityEdge,...]:
    return (
        CapabilityEdge("EDGE-WRITE-READ","CAP_WRITE_SCOPED","CAP_READ","LP-BIND",True,False,"LP-POLICY","1","LP-EPOCH"),
        CapabilityEdge("EDGE-GLOBAL-READ","CAP_WRITE_GLOBAL","CAP_READ","LP-BIND",True,False,"LP-POLICY","1","LP-EPOCH"),
        CapabilityEdge("EDGE-ADMIN-GLOBAL","CAP_ADMIN","CAP_WRITE_GLOBAL","LP-BIND",True,False,"LP-POLICY","1","LP-EPOCH"),
    )


def default_roles(now: int) -> tuple[RoleProfile,...]:
    return (
        RoleProfile("ROLE_VIEWER","1","LP-BIND",("CAP_READ",),(),True,False,now-1000,now+10000,"LP-POLICY","1","LP-EPOCH"),
        RoleProfile("ROLE_EDITOR","1","LP-BIND",("CAP_WRITE_SCOPED","CAP_NOTIFY","CAP_ELEVATED_REVIEW"),("ROLE_VIEWER",),True,False,now-1000,now+10000,"LP-POLICY","1","LP-EPOCH"),
        RoleProfile("ROLE_ADMIN","1","LP-BIND",("CAP_WRITE_GLOBAL","CAP_ADMIN"),("ROLE_EDITOR",),True,False,now-1000,now+10000,"LP-POLICY","1","LP-EPOCH"),
    )


def default_actions(now: int | None=None) -> tuple[ActionSpec,...]:
    return (ActionSpec("ACT-SAFE","GOAL-UPDATE","LP-BIND",True,False),ActionSpec("ACT-REVIEW","GOAL-REVIEW","LP-BIND",True,False))


def default_requirements(now: int | None=None) -> tuple[RequirementClause,...]:
    return (
        RequirementClause("REQ-WRITE","ACT-SAFE",("CAP_WRITE_SCOPED","CAP_WRITE_GLOBAL"),"LP-BIND",True,False),
        RequirementClause("REQ-READ","ACT-SAFE",("CAP_READ",),"LP-BIND",True,False),
        RequirementClause("REQ-REVIEW","ACT-REVIEW",("CAP_ELEVATED_REVIEW",),"LP-BIND",True,False),
    )


def default_request(now: int) -> LeastPrivilegeRequest:
    return LeastPrivilegeRequest("LP-REQ","GOAL-UPDATE","ACT-SAFE","ROLE_EDITOR",("CAP_READ","CAP_WRITE_SCOPED","CAP_NOTIFY"),"LP-BIND","LP-POLICY","1","LP-EPOCH","1",now-10,now+300)


def default_approval(now: int) -> ApprovalEvidence:
    return ApprovalEvidence("LP-APPROVAL","LP-REQ","SECURITY_REVIEWER","LP-BIND",True,False,True,"APPROVE",now-100,now+300,"LP-POLICY","1","LP-EPOCH")
