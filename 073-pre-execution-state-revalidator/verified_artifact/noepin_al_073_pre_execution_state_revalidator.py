"""NOEPIN AL 073 — Pre-Execution State Revalidator / Sequential Successor V2.

Pure TOCTOU-oriented pre-execution state verifier. It compares the decision-time
snapshot with the pre-execution snapshot for the exact Dependency Keys that were
fixed when the permit/approval decision was made.

This module never grants permission, refreshes a permit, mutates files/world
state, commits a transaction, executes a tool/action, or promotes a snapshot
match to action success.

DCSR is used only for canonical state preparation/reconstruction, deterministic
fingerprints, verified delta application, and missing-only synchronization.
Prepared state is not authoritative current state.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from hashlib import sha256
import json
from typing import Iterable, Tuple

SCHEMA_VERSION = "NOEPIN-AL-073-V2"

class Decision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    HOLD = "HOLD"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"

SAFETY_CATEGORIES = frozenset({
    "TARGET", "AUTHORITY", "CONFIDENTIALITY", "POLICY",
    "DEPENDENCY", "RESOURCE", "IDENTITY", "PERMISSION"
})

@dataclass(frozen=True)
class SnapshotValue:
    key: str
    value_fingerprint: str
    version: str
    observed: bool
    category: str
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class DecisionSnapshot:
    snapshot_id: str
    permit_id: str
    policy_fingerprint: str
    target_fingerprint: str
    authority_fingerprint: str
    confidentiality_fingerprint: str
    values: Tuple[SnapshotValue, ...]
    captured_at: int
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class PreExecutionSnapshot:
    snapshot_id: str
    permit_id: str
    policy_fingerprint: str
    target_fingerprint: str
    authority_fingerprint: str
    confidentiality_fingerprint: str
    values: Tuple[SnapshotValue, ...]
    captured_at: int
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class RevalidationPolicy:
    policy_id: str
    binding: str
    state_epoch: str
    max_decision_age: int
    max_preexecution_age: int
    critical_keys: Tuple[str, ...]
    safety_categories: Tuple[str, ...] = tuple(sorted(SAFETY_CATEGORIES))
    revoked: bool = False

@dataclass(frozen=True)
class PreparedRevalidationState:
    policy: RevalidationPolicy
    decision_snapshot: DecisionSnapshot
    dependency_keys: Tuple[str, ...]
    binding: str
    state_epoch: str
    policy_fingerprint: str
    decision_fingerprint: str
    registry_fingerprint: str
    value_fingerprints: Tuple[Tuple[str, str], ...]
    decision_index: Tuple[Tuple[str, SnapshotValue], ...]

@dataclass(frozen=True)
class RevalidationDelta:
    base_fingerprint: str
    target_fingerprint: str
    policy: RevalidationPolicy
    decision_snapshot_header: DecisionSnapshot
    dependency_keys: Tuple[str, ...]
    binding: str
    state_epoch: str
    upsert_values: Tuple[SnapshotValue, ...]
    remove_keys: Tuple[str, ...]

@dataclass(frozen=True)
class RevalidationSyncPlan:
    missing_or_changed_keys: Tuple[str, ...]
    metadata_bytes_required: int
    full_resend_required: bool

@dataclass(frozen=True)
class RelevantDiff:
    key: str
    category: str
    decision_fingerprint: str
    preexecution_fingerprint: str
    reason: str

@dataclass(frozen=True)
class RevalidationResult:
    decision: Decision
    reasons: Tuple[str, ...]
    permit_id: str
    decision_snapshot_id: str
    preexecution_snapshot_id: str
    relevant_diffs: Tuple[RelevantDiff, ...]
    irrelevant_diff_keys: Tuple[str, ...]
    unobservable_keys: Tuple[str, ...]
    permit_validity: str
    recheck_required: bool
    next_gate_candidate: bool
    atomic_publish_candidate: bool
    permission_granted: bool = False
    permit_refreshed: bool = False
    snapshot_written: bool = False
    state_mutated: bool = False
    tool_executed: bool = False
    transaction_committed: bool = False
    external_write_performed: bool = False
    world_truth_proven: bool = False
    safety_proven: bool = False
    action_success: bool = False

def _ser(obj) -> bytes:
    def norm(x):
        if isinstance(x, Enum):
            return x.value
        if hasattr(x, "__dataclass_fields__"):
            return {k: norm(getattr(x, k)) for k in sorted(x.__dataclass_fields__)}
        if isinstance(x, tuple):
            return [norm(v) for v in x]
        if isinstance(x, list):
            return [norm(v) for v in x]
        if isinstance(x, dict):
            return {str(k): norm(v) for k, v in sorted(x.items(), key=lambda kv: str(kv[0]))}
        return x
    return json.dumps(norm(obj), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()

def _fp(obj) -> str:
    return sha256(_ser(obj)).hexdigest()

def _canon_values(values: Iterable[SnapshotValue]) -> Tuple[SnapshotValue, ...]:
    out=[]
    seen=set()
    for v in values:
        if not v.key or v.key in seen:
            raise ValueError("INVALID_OR_DUPLICATE_SNAPSHOT_KEY")
        seen.add(v.key)
        out.append(replace(v, category=str(v.category).upper()))
    return tuple(sorted(out, key=lambda x:x.key))

def _canon_keys(keys: Iterable[str]) -> Tuple[str, ...]:
    out=tuple(sorted(str(k) for k in keys))
    if not out or any(not k for k in out) or len(out)!=len(set(out)):
        raise ValueError("INVALID_OR_DUPLICATE_DEPENDENCY_KEY")
    return out

def canonical_decision_snapshot(s: DecisionSnapshot) -> DecisionSnapshot:
    return replace(s, values=_canon_values(s.values))

def canonical_preexecution_snapshot(s: PreExecutionSnapshot) -> PreExecutionSnapshot:
    return replace(s, values=_canon_values(s.values))

def default_policy() -> RevalidationPolicy:
    return RevalidationPolicy(
        "PREEXEC-POLICY","PREEXEC-BIND","STATE-EPOCH-1",
        max_decision_age=600,max_preexecution_age=30,
        critical_keys=("target","authority","confidentiality","policy")
    )

def default_decision_snapshot(now: int) -> DecisionSnapshot:
    vals=(
        SnapshotValue("target","TGT-FP-1","v1",True,"TARGET","PREEXEC-BIND","STATE-EPOCH-1"),
        SnapshotValue("authority","AUTH-FP-1","v1",True,"AUTHORITY","PREEXEC-BIND","STATE-EPOCH-1"),
        SnapshotValue("confidentiality","CONF-FP-1","v1",True,"CONFIDENTIALITY","PREEXEC-BIND","STATE-EPOCH-1"),
        SnapshotValue("policy","POL-FP-1","v7",True,"POLICY","PREEXEC-BIND","STATE-EPOCH-1"),
        SnapshotValue("ui_theme","THEME-DARK","v2",True,"IRRELEVANT","PREEXEC-BIND","STATE-EPOCH-1"),
    )
    return DecisionSnapshot(
        "DEC-SNAP-73","PERMIT-73","POL-FP-1","TGT-FP-1","AUTH-FP-1","CONF-FP-1",
        vals,now-5,"PREEXEC-BIND","STATE-EPOCH-1"
    )

def matching_preexecution_snapshot(decision: DecisionSnapshot, now: int) -> PreExecutionSnapshot:
    d=canonical_decision_snapshot(decision)
    return PreExecutionSnapshot(
        "PRE-SNAP-73",d.permit_id,d.policy_fingerprint,d.target_fingerprint,
        d.authority_fingerprint,d.confidentiality_fingerprint,d.values,now,
        d.binding,d.state_epoch
    )

def default_dependency_keys() -> Tuple[str, ...]:
    return ("target","authority","confidentiality","policy","ui_theme")

def _invalid_result(decision: Decision, reason: str, d: DecisionSnapshot, p: PreExecutionSnapshot, *, recheck=True) -> RevalidationResult:
    return RevalidationResult(
        decision,(reason,),d.permit_id,d.snapshot_id,p.snapshot_id,(),(),(),
        "INVALID" if decision==Decision.DENY else "SUSPENDED",
        recheck,False,False
    )

def _validate_common(policy: RevalidationPolicy, d: DecisionSnapshot, p: PreExecutionSnapshot, dep_keys: Tuple[str,...], now: int):
    if policy.revoked:
        return (Decision.HOLD,"POLICY_REVOKED")
    if not policy.binding or not policy.state_epoch or d.binding!=policy.binding or p.binding!=policy.binding:
        return (Decision.HOLD,"BINDING_MISMATCH")
    if d.state_epoch!=policy.state_epoch or p.state_epoch!=policy.state_epoch:
        return (Decision.HOLD,"STATE_EPOCH_MISMATCH")
    if d.permit_id!=p.permit_id:
        return (Decision.HOLD,"PERMIT_ID_MISMATCH")
    if d.captured_at>now or p.captured_at>now:
        return (Decision.HOLD,"SNAPSHOT_TIME_IN_FUTURE")
    if now-d.captured_at>policy.max_decision_age:
        return (Decision.HOLD,"DECISION_SNAPSHOT_STALE")
    if now-p.captured_at>policy.max_preexecution_age:
        return (Decision.HOLD,"PREEXECUTION_SNAPSHOT_STALE")
    if not dep_keys:
        return (Decision.HOLD,"NO_DEPENDENCY_KEYS")
    return None

def evaluate(
    decision_snapshot: DecisionSnapshot,
    preexecution_snapshot: PreExecutionSnapshot,
    dependency_keys: Iterable[str],
    policy: RevalidationPolicy,
    *,
    now: int
) -> RevalidationResult:
    try:
        d=canonical_decision_snapshot(decision_snapshot)
        p=canonical_preexecution_snapshot(preexecution_snapshot)
        keys=_canon_keys(dependency_keys)
    except Exception:
        # preserve identifiers where possible, but fail closed
        return _invalid_result(Decision.HOLD,"INVALID_TYPED_INPUT",decision_snapshot,preexecution_snapshot)
    common=_validate_common(policy,d,p,keys,int(now))
    if common:
        return _invalid_result(common[0],common[1],d,p)
    dmap={v.key:v for v in d.values}
    pmap={v.key:v for v in p.values}
    unobs=[]
    relevant=[]
    irrelevant=[]
    critical=set(policy.critical_keys)
    safety=set(policy.safety_categories)
    # Header-level safety state is always relevant and cannot be excluded by dependency list.
    header_pairs=(
        ("policy","POLICY",d.policy_fingerprint,p.policy_fingerprint),
        ("target","TARGET",d.target_fingerprint,p.target_fingerprint),
        ("authority","AUTHORITY",d.authority_fingerprint,p.authority_fingerprint),
        ("confidentiality","CONFIDENTIALITY",d.confidentiality_fingerprint,p.confidentiality_fingerprint),
    )
    for key,cat,a,b in header_pairs:
        if not a or not b:
            unobs.append(key)
        elif a!=b:
            relevant.append(RelevantDiff(key,cat,a,b,"HEADER_SAFETY_STATE_CHANGED"))
    for key in keys:
        dv=dmap.get(key); pv=pmap.get(key)
        if dv is None or pv is None or not dv.observed or not pv.observed:
            unobs.append(key); continue
        if dv.binding!=policy.binding or pv.binding!=policy.binding or dv.state_epoch!=policy.state_epoch or pv.state_epoch!=policy.state_epoch:
            unobs.append(key); continue
        changed=(dv.value_fingerprint!=pv.value_fingerprint or dv.version!=pv.version or dv.category!=pv.category)
        if not changed:
            continue
        category=(pv.category or dv.category).upper()
        if key in critical or category in safety or dv.category in safety or pv.category in safety:
            relevant.append(RelevantDiff(key,category,dv.value_fingerprint,pv.value_fingerprint,"SAFETY_RELEVANT_STATE_CHANGED"))
        else:
            irrelevant.append(key)
    unobs=tuple(sorted(set(unobs)))
    if unobs:
        return RevalidationResult(
            Decision.HOLD,("SAFETY_STATE_UNOBSERVABLE",),d.permit_id,d.snapshot_id,p.snapshot_id,
            tuple(relevant),tuple(sorted(set(irrelevant))),unobs,"SUSPENDED",True,False,False
        )
    if relevant:
        return RevalidationResult(
            Decision.HOLD,("RELEVANT_STATE_CHANGED_RECHECK_REQUIRED",),d.permit_id,d.snapshot_id,p.snapshot_id,
            tuple(sorted(relevant,key=lambda x:(x.key,x.reason))),tuple(sorted(set(irrelevant))),(),
            "INVALIDATED_PENDING_RECHECK",True,False,False
        )
    reasons=("STATE_REVALIDATED_NO_RELEVANT_DIFF",) if not irrelevant else ("ONLY_IRRELEVANT_DIFFS",)
    return RevalidationResult(
        Decision.ALLOW,reasons,d.permit_id,d.snapshot_id,p.snapshot_id,(),
        tuple(sorted(set(irrelevant))),(),"VALID_CANDIDATE_ONLY",False,True,True
    )

def prepare_state(
    policy: RevalidationPolicy,
    decision_snapshot: DecisionSnapshot,
    dependency_keys: Iterable[str],
    *,
    binding: str
) -> PreparedRevalidationState:
    d=canonical_decision_snapshot(decision_snapshot)
    keys=_canon_keys(dependency_keys)
    vals=tuple((v.key,_fp(v)) for v in d.values)
    pfp=_fp(policy); dfp=_fp(d)
    reg=_fp({"schema":SCHEMA_VERSION,"policy":policy,"decision":d,"dependency_keys":keys,"binding":binding,"state_epoch":policy.state_epoch})
    return PreparedRevalidationState(
        policy,d,keys,binding,policy.state_epoch,pfp,dfp,reg,vals,tuple((v.key,v) for v in d.values)
    )

def validate_prepared_integrity(st: PreparedRevalidationState) -> bool:
    try:
        if st.binding!=st.policy.binding or st.state_epoch!=st.policy.state_epoch:
            return False
        if st.policy_fingerprint!=_fp(st.policy):
            return False
        d=canonical_decision_snapshot(st.decision_snapshot)
        if st.decision_fingerprint!=_fp(d):
            return False
        if tuple((v.key,_fp(v)) for v in d.values)!=st.value_fingerprints:
            return False
        if tuple((v.key,v) for v in d.values)!=st.decision_index:
            return False
        if st.dependency_keys!=_canon_keys(st.dependency_keys):
            return False
        expect=_fp({"schema":SCHEMA_VERSION,"policy":st.policy,"decision":d,"dependency_keys":st.dependency_keys,"binding":st.binding,"state_epoch":st.state_epoch})
        return expect==st.registry_fingerprint
    except Exception:
        return False

def evaluate_prepared(
    preexecution_snapshot: PreExecutionSnapshot,
    st: PreparedRevalidationState,
    *,
    current_policy_fingerprint: str,
    current_decision_fingerprint: str,
    current_registry_fingerprint: str,
    prepared_integrity_validated: bool,
    now: int
) -> RevalidationResult:
    d=st.decision_snapshot
    try:
        p=canonical_preexecution_snapshot(preexecution_snapshot)
    except Exception:
        return _invalid_result(Decision.HOLD,"INVALID_TYPED_INPUT",d,preexecution_snapshot)
    if not prepared_integrity_validated:
        return _invalid_result(Decision.HOLD,"PREPARED_INTEGRITY_NOT_VALIDATED",d,p)
    if current_policy_fingerprint!=st.policy_fingerprint:
        return _invalid_result(Decision.HOLD,"PREPARED_POLICY_STALE",d,p)
    if current_decision_fingerprint!=st.decision_fingerprint:
        return _invalid_result(Decision.HOLD,"DECISION_SNAPSHOT_STALE",d,p)
    if current_registry_fingerprint!=st.registry_fingerprint:
        return _invalid_result(Decision.HOLD,"PREPARED_REGISTRY_STALE",d,p)
    common=_validate_common(st.policy,d,p,st.dependency_keys,int(now))
    if common:
        return _invalid_result(common[0],common[1],d,p)
    dmap=dict(st.decision_index)
    pmap={v.key:v for v in p.values}
    unobs=[]; relevant=[]; irrelevant=[]
    critical=set(st.policy.critical_keys); safety=set(st.policy.safety_categories)
    header_pairs=(
        ("policy","POLICY",d.policy_fingerprint,p.policy_fingerprint),
        ("target","TARGET",d.target_fingerprint,p.target_fingerprint),
        ("authority","AUTHORITY",d.authority_fingerprint,p.authority_fingerprint),
        ("confidentiality","CONFIDENTIALITY",d.confidentiality_fingerprint,p.confidentiality_fingerprint),
    )
    for key,cat,a,b in header_pairs:
        if not a or not b: unobs.append(key)
        elif a!=b: relevant.append(RelevantDiff(key,cat,a,b,"HEADER_SAFETY_STATE_CHANGED"))
    for key in st.dependency_keys:
        dv=dmap.get(key); pv=pmap.get(key)
        if dv is None or pv is None or not dv.observed or not pv.observed:
            unobs.append(key); continue
        if dv.binding!=st.binding or pv.binding!=st.binding or dv.state_epoch!=st.state_epoch or pv.state_epoch!=st.state_epoch:
            unobs.append(key); continue
        changed=(dv.value_fingerprint!=pv.value_fingerprint or dv.version!=pv.version or dv.category!=pv.category)
        if not changed: continue
        category=(pv.category or dv.category).upper()
        if key in critical or category in safety or dv.category in safety or pv.category in safety:
            relevant.append(RelevantDiff(key,category,dv.value_fingerprint,pv.value_fingerprint,"SAFETY_RELEVANT_STATE_CHANGED"))
        else: irrelevant.append(key)
    unobs=tuple(sorted(set(unobs)))
    if unobs:
        return RevalidationResult(Decision.HOLD,("SAFETY_STATE_UNOBSERVABLE",),d.permit_id,d.snapshot_id,p.snapshot_id,tuple(relevant),tuple(sorted(set(irrelevant))),unobs,"SUSPENDED",True,False,False)
    if relevant:
        return RevalidationResult(Decision.HOLD,("RELEVANT_STATE_CHANGED_RECHECK_REQUIRED",),d.permit_id,d.snapshot_id,p.snapshot_id,tuple(sorted(relevant,key=lambda x:(x.key,x.reason))),tuple(sorted(set(irrelevant))),(),"INVALIDATED_PENDING_RECHECK",True,False,False)
    return RevalidationResult(Decision.ALLOW,("ONLY_IRRELEVANT_DIFFS",) if irrelevant else ("STATE_REVALIDATED_NO_RELEVANT_DIFF",),d.permit_id,d.snapshot_id,p.snapshot_id,(),tuple(sorted(set(irrelevant))),(),"VALID_CANDIDATE_ONLY",False,True,True)

def make_delta(base: PreparedRevalidationState, target: PreparedRevalidationState) -> RevalidationDelta:
    b=dict(base.decision_index); t=dict(target.decision_index)
    up=tuple(t[k] for k in sorted(t) if k not in b or _fp(t[k])!=_fp(b[k]))
    rem=tuple(sorted(set(b)-set(t)))
    header=replace(target.decision_snapshot, values=())
    return RevalidationDelta(base.registry_fingerprint,target.registry_fingerprint,target.policy,header,target.dependency_keys,target.binding,target.state_epoch,up,rem)

def apply_delta(base: PreparedRevalidationState, delta: RevalidationDelta) -> PreparedRevalidationState:
    if base.registry_fingerprint!=delta.base_fingerprint:
        raise ValueError("DELTA_BASE_MISMATCH")
    cur=dict(base.decision_index)
    for k in delta.remove_keys: cur.pop(k,None)
    for v in delta.upsert_values: cur[v.key]=v
    ds=replace(delta.decision_snapshot_header, values=tuple(cur[k] for k in sorted(cur)))
    out=prepare_state(delta.policy,ds,delta.dependency_keys,binding=delta.binding)
    if out.registry_fingerprint!=delta.target_fingerprint:
        raise ValueError("DELTA_TARGET_MISMATCH")
    return out

def missing_only_sync_plan(st: PreparedRevalidationState, remote_fingerprints: dict[str,str]) -> RevalidationSyncPlan:
    local=dict(st.value_fingerprints)
    missing=tuple(sorted(k for k,v in local.items() if remote_fingerprints.get(k)!=v))
    meta=len(_ser({"keys":missing,"registry":st.registry_fingerprint,"decision":st.decision_fingerprint}))
    return RevalidationSyncPlan(missing,meta,False)

def full_registry_bytes(st: PreparedRevalidationState) -> int:
    return len(_ser(st))

def delta_bytes(delta: RevalidationDelta) -> int:
    return len(_ser(delta))
