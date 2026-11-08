"""NOEPIN AL 069 — Dependency Order Verifier — Sequential Successor V2.

Creator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
Implementation / analysis / documentation support: AI-assisted using ChatGPT
License / Rights: NOT SPECIFIED

Pure algorithm/control-plane evaluator. It verifies whether a proposed action sequence respects
explicit preconditions, postconditions, current observed state, dependency ordering, cycle safety,
and explicit forbidden order constraints. It proposes a legal order when possible but never
rewrites a plan, grants permission, mutates state, executes actions, deploys, proves truth/safety,
or promotes Action Success.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, is_dataclass
from enum import Enum
from hashlib import sha256
import heapq
import json
from typing import Any, Mapping, Sequence

CREATOR = "NOEPIN / のえぴん"
AI_SUPPORT = "AI-assisted implementation / analysis / documentation support using ChatGPT"
LICENSE_RIGHTS = "NOT SPECIFIED"
CANONICAL_ID = "NOEPIN-AL-069"

class Decision(str, Enum):
    ALLOW="ALLOW"; DENY="DENY"; HOLD="HOLD"; HUMAN_APPROVAL="HUMAN_APPROVAL"

@dataclass(frozen=True, order=True)
class Predicate:
    name: str
    value: str

@dataclass(frozen=True)
class ActionSpec:
    action_id: str
    preconditions: tuple[Predicate,...]
    postconditions: tuple[Predicate,...]
    binding: str
    verified: bool
    revoked: bool
    policy_id: str
    policy_version: str
    authority_epoch: str

@dataclass(frozen=True)
class StateObservation:
    predicate: Predicate
    known: bool
    verified: bool
    revoked: bool
    binding: str
    policy_id: str
    policy_version: str
    authority_epoch: str

@dataclass(frozen=True)
class ForbiddenOrder:
    before_action_id: str
    after_action_id: str
    reason: str
    binding: str
    verified: bool
    revoked: bool
    policy_id: str
    policy_version: str
    authority_epoch: str

@dataclass(frozen=True)
class PlanRequest:
    request_id: str
    action_sequence: tuple[str,...]
    binding: str
    expected_policy_id: str
    expected_policy_version: str
    expected_authority_epoch: str
    created_at: int
    expires_at: int

@dataclass(frozen=True)
class DependencyPolicy:
    policy_id: str
    version: str
    authority_epoch: str
    valid_from: int
    expires_at: int
    revoked: bool
    max_request_age_seconds: int
    require_verified_observations: bool
    require_unique_producer: bool

@dataclass(frozen=True)
class PreparedDependencyState:
    binding: str
    valid: bool
    validation_reasons: tuple[str,...]
    policy: DependencyPolicy
    policy_fingerprint: str
    registry_fingerprint: str
    action_fingerprints: tuple[tuple[str,str],...]
    observation_fingerprints: tuple[tuple[str,str],...]
    forbidden_fingerprints: tuple[tuple[str,str],...]
    actions: tuple[ActionSpec,...]
    observations: tuple[StateObservation,...]
    forbidden_orders: tuple[ForbiddenOrder,...]
    producer_index: tuple[tuple[str,str],...]
    generated_at: int

@dataclass(frozen=True)
class DependencyRegistryDelta:
    base_fingerprint: str
    target_fingerprint: str
    changed_actions: tuple[ActionSpec,...]
    removed_action_ids: tuple[str,...]
    added_actions: tuple[ActionSpec,...]
    changed_observations: tuple[StateObservation,...]
    removed_observation_keys: tuple[str,...]
    added_observations: tuple[StateObservation,...]
    changed_forbidden_orders: tuple[ForbiddenOrder,...]
    removed_forbidden_keys: tuple[str,...]
    added_forbidden_orders: tuple[ForbiddenOrder,...]

@dataclass(frozen=True)
class DependencySyncPlan:
    registry_fingerprint: str
    missing_or_changed_action_ids: tuple[str,...]
    missing_or_changed_observation_keys: tuple[str,...]
    missing_or_changed_forbidden_keys: tuple[str,...]
    metadata_bytes_required: int
    full_bytes: int
    full_resend_required: bool
    permission_granted: bool=False
    plan_rewrite_authorized: bool=False
    state_write_authorized: bool=False
    action_execution_authorized: bool=False
    action_success_authorized: bool=False

@dataclass(frozen=True)
class DependencyResult:
    decision: Decision
    reasons: tuple[str,...]
    legal_order: tuple[str,...]
    violating_actions: tuple[str,...]
    unmet_dependencies: tuple[str,...]
    unknown_dependencies: tuple[str,...]
    cycle_nodes: tuple[str,...]
    forbidden_violations: tuple[str,...]
    reorder_required: bool
    next_gate_candidate: bool
    input_fingerprint: str
    permission_granted: bool=False
    plan_rewritten: bool=False
    state_written: bool=False
    action_executed: bool=False
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

def predicate_key(p: Predicate) -> str:
    return f"{p.name}={p.value}"

def forbidden_key(f: ForbiddenOrder) -> str:
    return f"{f.before_action_id}>{f.after_action_id}"

def _fps(items: Sequence[Any], key_fn) -> tuple[tuple[str,str],...]:
    return tuple(sorted((str(key_fn(x)),fingerprint(x)) for x in items))

def _registry_from_fps(binding: str, policy_fp: str, afp, ofp, ffp) -> str:
    return fingerprint({"binding":binding,"policy_fingerprint":policy_fp,"action_fingerprints":tuple(sorted(afp)),"observation_fingerprints":tuple(sorted(ofp)),"forbidden_fingerprints":tuple(sorted(ffp))})

def registry_fingerprint(policy,actions,observations,forbidden_orders,binding: str) -> str:
    return _registry_from_fps(binding,fingerprint(policy),_fps(actions,lambda x:x.action_id),_fps(observations,lambda x:predicate_key(x.predicate)),_fps(forbidden_orders,forbidden_key))

def _unique(items,key_fn) -> bool:
    vals=[key_fn(x) for x in items]; return len(vals)==len(set(vals))

def _policy_valid(p: DependencyPolicy, now: int) -> bool:
    return bool(p.policy_id and p.version and p.authority_epoch and not p.revoked and p.valid_from<=now<=p.expires_at and p.max_request_age_seconds>=0)

def _common_valid(x, binding: str, p: DependencyPolicy) -> bool:
    return bool(x.verified and not x.revoked and x.binding==binding and x.policy_id==p.policy_id and x.policy_version==p.version and x.authority_epoch==p.authority_epoch)

def _producer_index(actions: Sequence[ActionSpec], require_unique: bool) -> tuple[tuple[str,str],...]:
    d: dict[str,list[str]]={}
    for a in actions:
        for post in a.postconditions:
            d.setdefault(predicate_key(post),[]).append(a.action_id)
    out=[]
    for k,ids in sorted(d.items()):
        ids=sorted(set(ids))
        if len(ids)==1:
            out.append((k,ids[0]))
        elif not require_unique:
            out.append((k,ids[0]))
    return tuple(out)

def _validation(policy,actions,observations,forbidden_orders,binding: str,now: int) -> tuple[str,...]:
    r=[]
    if not binding: r.append("EMPTY_BINDING")
    if not _policy_valid(policy,now): r.append("INVALID_POLICY")
    if not _unique(actions,lambda x:x.action_id): r.append("DUPLICATE_ACTION")
    if not _unique(observations,lambda x:predicate_key(x.predicate)): r.append("DUPLICATE_OBSERVATION")
    if not _unique(forbidden_orders,forbidden_key): r.append("DUPLICATE_FORBIDDEN_ORDER")
    ids={a.action_id for a in actions}
    producers: dict[str,list[str]]={}
    for a in actions:
        if not a.action_id or not _common_valid(a,binding,policy): r.append(f"INVALID_ACTION:{a.action_id}")
        if len(set(predicate_key(x) for x in a.preconditions))!=len(a.preconditions): r.append(f"DUPLICATE_PRECONDITION:{a.action_id}")
        if len(set(predicate_key(x) for x in a.postconditions))!=len(a.postconditions): r.append(f"DUPLICATE_POSTCONDITION:{a.action_id}")
        for p in a.postconditions: producers.setdefault(predicate_key(p),[]).append(a.action_id)
    if policy.require_unique_producer:
        for k,v in producers.items():
            if len(set(v))>1: r.append(f"MULTIPLE_PRODUCERS:{k}")
    for o in observations:
        if not o.predicate.name or not _common_valid(o,binding,policy): r.append(f"INVALID_OBSERVATION:{predicate_key(o.predicate)}")
        if policy.require_verified_observations and not o.verified: r.append(f"UNVERIFIED_OBSERVATION:{predicate_key(o.predicate)}")
    for f in forbidden_orders:
        if f.before_action_id not in ids or f.after_action_id not in ids: r.append(f"UNKNOWN_FORBIDDEN_ACTION:{forbidden_key(f)}")
        if f.before_action_id==f.after_action_id: r.append(f"SELF_FORBIDDEN_ORDER:{forbidden_key(f)}")
        if not f.reason or not _common_valid(f,binding,policy): r.append(f"INVALID_FORBIDDEN_ORDER:{forbidden_key(f)}")
    return tuple(sorted(set(r)))

def prepare_state(policy,actions,observations,forbidden_orders,*,binding: str,now: int) -> PreparedDependencyState:
    actions=tuple(actions); observations=tuple(observations); forbidden_orders=tuple(forbidden_orders)
    afp=_fps(actions,lambda x:x.action_id); ofp=_fps(observations,lambda x:predicate_key(x.predicate)); ffp=_fps(forbidden_orders,forbidden_key); pfp=fingerprint(policy)
    reasons=_validation(policy,actions,observations,forbidden_orders,binding,now)
    return PreparedDependencyState(binding,not reasons,reasons,policy,pfp,_registry_from_fps(binding,pfp,afp,ofp,ffp),afp,ofp,ffp,actions,observations,forbidden_orders,_producer_index(actions,policy.require_unique_producer),now)

def validate_prepared_integrity(st: PreparedDependencyState) -> bool:
    afp=_fps(st.actions,lambda x:x.action_id); ofp=_fps(st.observations,lambda x:predicate_key(x.predicate)); ffp=_fps(st.forbidden_orders,forbidden_key); pfp=fingerprint(st.policy)
    if afp!=st.action_fingerprints or ofp!=st.observation_fingerprints or ffp!=st.forbidden_fingerprints or pfp!=st.policy_fingerprint: return False
    if _registry_from_fps(st.binding,pfp,afp,ofp,ffp)!=st.registry_fingerprint: return False
    if _producer_index(st.actions,st.policy.require_unique_producer)!=st.producer_index: return False
    return True

def _request_valid(req: PlanRequest,p: DependencyPolicy,binding: str,now: int) -> tuple[str,...]:
    r=[]
    if req.binding!=binding: r.append("BINDING_MISMATCH")
    if req.expected_policy_id!=p.policy_id or req.expected_policy_version!=p.version or req.expected_authority_epoch!=p.authority_epoch: r.append("POLICY_IDENTITY_MISMATCH")
    if req.expires_at<req.created_at or now>req.expires_at or now<req.created_at or now-req.created_at>p.max_request_age_seconds: r.append("REQUEST_TIME_INVALID")
    if not req.action_sequence: r.append("EMPTY_PLAN")
    if len(set(req.action_sequence))!=len(req.action_sequence): r.append("DUPLICATE_PLAN_ACTION")
    return tuple(sorted(set(r)))

def _toposort(nodes: Sequence[str], edges: Sequence[tuple[str,str]], preferred: Mapping[str,int]) -> tuple[tuple[str,...],tuple[str,...]]:
    nodes=tuple(dict.fromkeys(nodes)); indeg={n:0 for n in nodes}; out={n:[] for n in nodes}
    for a,b in edges:
        if a in indeg and b in indeg and b not in out[a]: out[a].append(b); indeg[b]+=1
    heap=[]
    for n,d in indeg.items():
        if d==0: heapq.heappush(heap,(preferred.get(n,10**9),n))
    order=[]
    while heap:
        _,n=heapq.heappop(heap); order.append(n)
        for b in sorted(out[n]):
            indeg[b]-=1
            if indeg[b]==0: heapq.heappush(heap,(preferred.get(b,10**9),b))
    if len(order)!=len(nodes):
        cyc=tuple(sorted(n for n,d in indeg.items() if d>0)); return tuple(order),cyc
    return tuple(order),()

def _result(decision: Decision,reasons,legal_order=(),violating_actions=(),unmet=(),unknown=(),cycle=(),forbidden=(),reorder=False,next_gate=False,input_fp="") -> DependencyResult:
    return DependencyResult(decision,tuple(sorted(set(reasons))),tuple(legal_order),tuple(sorted(set(violating_actions))),tuple(sorted(set(unmet))),tuple(sorted(set(unknown))),tuple(sorted(set(cycle))),tuple(sorted(set(forbidden))),bool(reorder),bool(next_gate),input_fp)

def evaluate_prepared(req: PlanRequest,st: PreparedDependencyState,*,current_policy_fingerprint: str,current_registry_fingerprint: str,prepared_integrity_validated: bool,now: int) -> DependencyResult:
    inp=fingerprint({"request":req,"registry_fingerprint":current_registry_fingerprint,"policy_fingerprint":current_policy_fingerprint,"now":now})
    rr=list(_request_valid(req,st.policy,st.binding,now))
    if not prepared_integrity_validated: rr.append("PREPARED_INTEGRITY_NOT_VALIDATED")
    if current_policy_fingerprint!=st.policy_fingerprint: rr.append("POLICY_FINGERPRINT_MISMATCH")
    if current_registry_fingerprint!=st.registry_fingerprint: rr.append("REGISTRY_FINGERPRINT_MISMATCH")
    if not st.valid: rr.extend(st.validation_reasons)
    if rr: return _result(Decision.HOLD,rr,input_fp=inp)
    amap={a.action_id:a for a in st.actions}; omap={predicate_key(o.predicate):o for o in st.observations}; pmap=dict(st.producer_index)
    unknown_actions=[x for x in req.action_sequence if x not in amap]
    if unknown_actions: return _result(Decision.HOLD,["UNKNOWN_PLAN_ACTION"],violating_actions=unknown_actions,input_fp=inp)
    idx={a:i for i,a in enumerate(req.action_sequence)}; selected=set(req.action_sequence)
    forbidden=[]
    for f in st.forbidden_orders:
        if f.before_action_id in idx and f.after_action_id in idx and idx[f.before_action_id] < idx[f.after_action_id]: forbidden.append(forbidden_key(f))
    if forbidden: return _result(Decision.DENY,["FORBIDDEN_ORDER"],forbidden=forbidden,violating_actions=tuple(x.split('>')[0] for x in forbidden),input_fp=inp)
    edges=[]; unmet=[]; unknown=[]
    for aid in req.action_sequence:
        a=amap[aid]
        for pre in a.preconditions:
            k=predicate_key(pre); obs=omap.get(k); producer=pmap.get(k)
            if obs is not None and obs.known and obs.verified and not obs.revoked:
                continue
            if producer is not None and producer in selected:
                if producer!=aid: edges.append((producer,aid))
                else: edges.append((producer,aid))
                continue
            if producer is not None and producer not in selected:
                unmet.append(f"MISSING_ACTION:{producer}->{aid}:{k}")
            elif obs is None or not obs.known or not obs.verified:
                unknown.append(f"UNOBSERVABLE:{aid}:{k}")
            else:
                unmet.append(f"UNSATISFIED:{aid}:{k}")
    order,cycle=_toposort(req.action_sequence,edges,idx)
    if cycle: return _result(Decision.HOLD,["CYCLIC_DEPENDENCY"],legal_order=order,cycle=cycle,violating_actions=cycle,input_fp=inp)
    if unknown: return _result(Decision.HOLD,["UNOBSERVABLE_PRECONDITION"],legal_order=order,unknown=unknown,violating_actions=tuple(x.split(':')[1] for x in unknown),input_fp=inp)
    if unmet: return _result(Decision.HOLD,["UNMET_DEPENDENCY"],legal_order=order,unmet=unmet,violating_actions=tuple(x.split(':')[1].split('->')[-1] if x.startswith('MISSING_ACTION:') else x.split(':')[1] for x in unmet),input_fp=inp)
    violations=[]
    for a,b in edges:
        if idx[a] > idx[b]: violations.extend([a,b])
    if violations:
        return _result(Decision.HOLD,["ORDER_VIOLATION"],legal_order=order,violating_actions=violations,reorder=True,input_fp=inp)
    return _result(Decision.ALLOW,["LEGAL_DEPENDENCY_ORDER"],legal_order=req.action_sequence,next_gate=True,input_fp=inp)

def evaluate(req,policy,actions,observations,forbidden_orders,*,now: int) -> DependencyResult:
    st=prepare_state(policy,actions,observations,forbidden_orders,binding=req.binding,now=now)
    return evaluate_prepared(req,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=validate_prepared_integrity(st),now=now)

def _diff(base,target,key_fn):
    b={key_fn(x):x for x in base}; t={key_fn(x):x for x in target}; changed=[]; added=[]; removed=[]
    for k in sorted(t):
        if k not in b: added.append(t[k])
        elif fingerprint(t[k])!=fingerprint(b[k]): changed.append(t[k])
    for k in sorted(b):
        if k not in t: removed.append(k)
    return tuple(changed),tuple(removed),tuple(added)

def make_delta(base: PreparedDependencyState,target: PreparedDependencyState) -> DependencyRegistryDelta:
    if base.binding!=target.binding or base.policy_fingerprint!=target.policy_fingerprint: raise ValueError("DELTA_POLICY_OR_BINDING_MISMATCH")
    ca,ra,aa=_diff(base.actions,target.actions,lambda x:x.action_id)
    co,ro,ao=_diff(base.observations,target.observations,lambda x:predicate_key(x.predicate))
    cf,rf,af=_diff(base.forbidden_orders,target.forbidden_orders,forbidden_key)
    return DependencyRegistryDelta(base.registry_fingerprint,target.registry_fingerprint,ca,ra,aa,co,ro,ao,cf,rf,af)

def apply_delta(base: PreparedDependencyState,d: DependencyRegistryDelta,*,now: int) -> PreparedDependencyState:
    if base.registry_fingerprint!=d.base_fingerprint: raise ValueError("DELTA_BASE_MISMATCH")
    def apply(items,changed,removed,added,key_fn):
        m={key_fn(x):x for x in items}
        for k in removed: m.pop(k,None)
        for x in changed: m[key_fn(x)]=x
        for x in added: m[key_fn(x)]=x
        return tuple(m[k] for k in sorted(m))
    actions=apply(base.actions,d.changed_actions,d.removed_action_ids,d.added_actions,lambda x:x.action_id)
    obs=apply(base.observations,d.changed_observations,d.removed_observation_keys,d.added_observations,lambda x:predicate_key(x.predicate))
    forb=apply(base.forbidden_orders,d.changed_forbidden_orders,d.removed_forbidden_keys,d.added_forbidden_orders,forbidden_key)
    st=prepare_state(base.policy,actions,obs,forb,binding=base.binding,now=now)
    if st.registry_fingerprint!=d.target_fingerprint: raise ValueError("DELTA_TARGET_MISMATCH")
    return st

def missing_only_sync_plan(st: PreparedDependencyState,remote: Mapping[str,Mapping[str,str]]) -> DependencySyncPlan:
    def miss(local,remote_map): return tuple(sorted(k for k,v in local if remote_map.get(k)!=v))
    a=miss(st.action_fingerprints,remote.get("actions",{})); o=miss(st.observation_fingerprints,remote.get("observations",{})); f=miss(st.forbidden_fingerprints,remote.get("forbidden_orders",{}))
    metadata=len(canonical_json({"registry_fingerprint":st.registry_fingerprint,"actions":a,"observations":o,"forbidden_orders":f}).encode("utf-8"))
    full=full_registry_bytes(st)
    return DependencySyncPlan(st.registry_fingerprint,a,o,f,metadata,full,False)

def full_registry_bytes(st: PreparedDependencyState) -> int:
    return len(canonical_json({"binding":st.binding,"policy":st.policy,"actions":st.actions,"observations":st.observations,"forbidden_orders":st.forbidden_orders}).encode("utf-8"))

def delta_bytes(d: DependencyRegistryDelta) -> int:
    return len(canonical_json(d).encode("utf-8"))

def default_policy(now: int) -> DependencyPolicy:
    return DependencyPolicy("DOV-POLICY","1","DOV-EPOCH",now-1000,now+100000,False,3600,True,True)

def _common():
    return dict(binding="DOV-BIND",verified=True,revoked=False,policy_id="DOV-POLICY",policy_version="1",authority_epoch="DOV-EPOCH")

def default_actions() -> tuple[ActionSpec,...]:
    c=_common()
    return (
        ActionSpec("A-SNAPSHOT",(Predicate("workspace_ready","true"),),(Predicate("snapshot_exists","true"),),**c),
        ActionSpec("A-APPLY",(Predicate("snapshot_exists","true"),),(Predicate("config_applied","true"),),**c),
        ActionSpec("A-VERIFY",(Predicate("config_applied","true"),),(Predicate("config_verified","true"),),**c),
        ActionSpec("A-CLEANUP",(Predicate("config_verified","true"),),(Predicate("cleanup_done","true"),),**c),
    )

def default_observations() -> tuple[StateObservation,...]:
    c=_common()
    return (
        StateObservation(Predicate("workspace_ready","true"),True,**c),
        StateObservation(Predicate("snapshot_exists","true"),False,**c),
        StateObservation(Predicate("config_applied","true"),False,**c),
        StateObservation(Predicate("config_verified","true"),False,**c),
        StateObservation(Predicate("cleanup_done","true"),False,**c),
    )

def default_forbidden_orders() -> tuple[ForbiddenOrder,...]:
    c=_common(); return (ForbiddenOrder("A-CLEANUP","A-VERIFY","cleanup-before-verification-is-forbidden",**c),)

def default_request(now: int, sequence: tuple[str,...]|None=None) -> PlanRequest:
    if sequence is None: sequence=("A-SNAPSHOT","A-APPLY","A-VERIFY","A-CLEANUP")
    return PlanRequest("REQ-DOV",sequence,"DOV-BIND","DOV-POLICY","1","DOV-EPOCH",now-1,now+1000)
