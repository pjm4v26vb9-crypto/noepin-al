"""NOEPIN AL 067 — Assumption Verification Graph — Sequential Successor V2.

Creator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
Implementation / analysis / documentation support: AI-assisted using ChatGPT
License / Rights: NOT SPECIFIED

Pure algorithm/control-plane evaluator. It models assumptions, evidence/observations, dependency
edges, and action dependencies. It never changes environment state, edits files, grants
permission, executes an action, proves world truth/safety, or promotes action success.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, is_dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence

CREATOR = "NOEPIN / のえぴん"
AI_SUPPORT = "AI-assisted implementation / analysis / documentation support using ChatGPT"
LICENSE_RIGHTS = "NOT SPECIFIED"
CANONICAL_ID = "NOEPIN-AL-067"

class Decision(str, Enum):
    ALLOW="ALLOW"; DENY="DENY"; HOLD="HOLD"; HUMAN_APPROVAL="HUMAN_APPROVAL"

class EvidenceState(str, Enum):
    VERIFIED="VERIFIED"; UNVERIFIED="UNVERIFIED"; CONTRADICTED="CONTRADICTED"

class Impact(str, Enum):
    LOW="LOW"; MEDIUM="MEDIUM"; HIGH="HIGH"; CRITICAL="CRITICAL"

@dataclass(frozen=True)
class AssumptionSpec:
    assumption_id: str
    impact: Impact
    binding: str
    verified: bool
    revoked: bool
    policy_id: str
    policy_version: str
    authority_epoch: str

@dataclass(frozen=True)
class AssumptionEdge:
    assumption_id: str
    depends_on_id: str

@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    assumption_id: str
    state: EvidenceState
    confidence: float
    provenance_id: str
    observed_at: int
    expires_at: int
    binding: str
    verified: bool
    revoked: bool
    policy_id: str
    policy_version: str
    authority_epoch: str

@dataclass(frozen=True)
class ObservationRecord:
    observation_id: str
    assumption_id: str
    state: EvidenceState
    observed_at: int
    expires_at: int
    binding: str
    verified: bool
    revoked: bool
    policy_id: str
    policy_version: str
    authority_epoch: str

@dataclass(frozen=True)
class ActionSpec:
    action_id: str
    depends_on: tuple[str, ...]
    binding: str
    verified: bool
    revoked: bool
    policy_id: str
    policy_version: str
    authority_epoch: str

@dataclass(frozen=True)
class VerificationRequest:
    request_id: str
    plan_id: str
    selected_action_ids: tuple[str, ...]
    binding: str
    expected_policy_id: str
    expected_policy_version: str
    expected_authority_epoch: str
    created_at: int
    expires_at: int

@dataclass(frozen=True)
class VerificationPolicy:
    policy_id: str
    version: str
    authority_epoch: str
    valid_from: int
    expires_at: int
    revoked: bool
    hold_impacts: frozenset[Impact]
    low_unverified_risk: float
    max_low_unverified_risk: float
    min_verified_confidence: float
    max_request_age_seconds: int

@dataclass(frozen=True)
class PreparedAssumptionState:
    binding: str
    valid: bool
    validation_reasons: tuple[str, ...]
    policy: VerificationPolicy
    policy_fingerprint: str
    registry_fingerprint: str
    assumption_fingerprints: tuple[tuple[str,str], ...]
    edge_fingerprints: tuple[tuple[str,str], ...]
    evidence_fingerprints: tuple[tuple[str,str], ...]
    observation_fingerprints: tuple[tuple[str,str], ...]
    action_fingerprints: tuple[tuple[str,str], ...]
    assumptions: tuple[AssumptionSpec, ...]
    edges: tuple[AssumptionEdge, ...]
    evidence: tuple[EvidenceRecord, ...]
    observations: tuple[ObservationRecord, ...]
    actions: tuple[ActionSpec, ...]
    dependency_closure: tuple[tuple[str,tuple[str,...]], ...]
    action_dependency_closure: tuple[tuple[str,tuple[str,...]], ...]
    generated_at: int

@dataclass(frozen=True)
class AssumptionRegistryDelta:
    base_fingerprint: str
    target_fingerprint: str
    changed_assumptions: tuple[AssumptionSpec,...]
    removed_assumption_ids: tuple[str,...]
    added_assumptions: tuple[AssumptionSpec,...]
    changed_edges: tuple[AssumptionEdge,...]
    removed_edge_keys: tuple[str,...]
    added_edges: tuple[AssumptionEdge,...]
    changed_evidence: tuple[EvidenceRecord,...]
    removed_evidence_ids: tuple[str,...]
    added_evidence: tuple[EvidenceRecord,...]
    changed_observations: tuple[ObservationRecord,...]
    removed_observation_ids: tuple[str,...]
    added_observations: tuple[ObservationRecord,...]
    changed_actions: tuple[ActionSpec,...]
    removed_action_ids: tuple[str,...]
    added_actions: tuple[ActionSpec,...]

@dataclass(frozen=True)
class AssumptionSyncPlan:
    registry_fingerprint: str
    missing_or_changed_assumption_ids: tuple[str,...]
    missing_or_changed_edge_keys: tuple[str,...]
    missing_or_changed_evidence_ids: tuple[str,...]
    missing_or_changed_observation_ids: tuple[str,...]
    missing_or_changed_action_ids: tuple[str,...]
    metadata_bytes_required: int
    full_bytes: int
    full_resend_required: bool
    permission_granted: bool=False
    action_execution_authorized: bool=False
    truth_authorized: bool=False
    action_success_authorized: bool=False

@dataclass(frozen=True)
class VerificationResult:
    decision: Decision
    reasons: tuple[str,...]
    verified_assumption_ids: tuple[str,...]
    unverified_assumption_ids: tuple[str,...]
    contradicted_assumption_ids: tuple[str,...]
    impacted_action_ids: tuple[str,...]
    low_unverified_risk: float
    next_gate_candidate: bool
    input_fingerprint: str
    permission_granted: bool=False
    environment_changed: bool=False
    evidence_written: bool=False
    action_executed: bool=False
    approval_executed: bool=False
    assumption_truth_proven: bool=False
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

def _edge_key(e: AssumptionEdge) -> str:
    return f"{e.assumption_id}->{e.depends_on_id}"

def _fps(items: Sequence[Any], key_fn) -> tuple[tuple[str,str], ...]:
    return tuple(sorted((str(key_fn(x)), fingerprint(x)) for x in items))

def _registry_from_fps(binding: str, policy_fp: str, afp, efp, vfp, ofp, xfp) -> str:
    return fingerprint({"binding":binding,"policy_fingerprint":policy_fp,"assumption_fingerprints":tuple(sorted(afp)),"edge_fingerprints":tuple(sorted(efp)),"evidence_fingerprints":tuple(sorted(vfp)),"observation_fingerprints":tuple(sorted(ofp)),"action_fingerprints":tuple(sorted(xfp))})

def registry_fingerprint(policy, assumptions, edges, evidence, observations, actions, binding: str) -> str:
    return _registry_from_fps(binding,fingerprint(policy),_fps(assumptions,lambda x:x.assumption_id),_fps(edges,_edge_key),_fps(evidence,lambda x:x.evidence_id),_fps(observations,lambda x:x.observation_id),_fps(actions,lambda x:x.action_id))

def request_fingerprint(req: VerificationRequest) -> str:
    return fingerprint(req)

def _cycle_and_closure(assumption_ids: set[str], edges: Sequence[AssumptionEdge]):
    graph={x:[] for x in assumption_ids}
    for e in edges:
        if e.assumption_id in graph and e.depends_on_id in graph:
            graph[e.assumption_id].append(e.depends_on_id)
    color={x:0 for x in graph}; cycle=False
    def dfs_cycle(n):
        nonlocal cycle
        color[n]=1
        for m in graph[n]:
            if color[m]==1: cycle=True
            elif color[m]==0: dfs_cycle(m)
        color[n]=2
    for n in sorted(graph):
        if color[n]==0: dfs_cycle(n)
    closure={}
    if not cycle:
        def walk(n,seen=None):
            seen=set() if seen is None else set(seen)
            out=set()
            for m in graph[n]:
                if m not in seen:
                    out.add(m); out.update(walk(m,seen|{m}))
            return out
        closure={n:tuple(sorted(walk(n))) for n in graph}
    return cycle,closure

def prepare_state(policy: VerificationPolicy, assumptions: Sequence[AssumptionSpec], edges: Sequence[AssumptionEdge], evidence: Sequence[EvidenceRecord], observations: Sequence[ObservationRecord], actions: Sequence[ActionSpec], *, binding: str, now: int) -> PreparedAssumptionState:
    reasons=[]
    aids=[x.assumption_id for x in assumptions]; evids=[x.evidence_id for x in evidence]; oids=[x.observation_id for x in observations]; acts=[x.action_id for x in actions]; edgekeys=[_edge_key(x) for x in edges]
    if len(aids)!=len(set(aids)): reasons.append("DUPLICATE_ASSUMPTION_ID")
    if len(evids)!=len(set(evids)): reasons.append("DUPLICATE_EVIDENCE_ID")
    if len(oids)!=len(set(oids)): reasons.append("DUPLICATE_OBSERVATION_ID")
    if len(acts)!=len(set(acts)): reasons.append("DUPLICATE_ACTION_ID")
    if len(edgekeys)!=len(set(edgekeys)): reasons.append("DUPLICATE_EDGE")
    if not binding: reasons.append("EMPTY_BINDING")
    if policy.revoked or not (policy.valid_from<=now<=policy.expires_at): reasons.append("POLICY_INVALID")
    if policy.low_unverified_risk<0 or policy.max_low_unverified_risk<0 or not (0<=policy.min_verified_confidence<=1): reasons.append("POLICY_THRESHOLD_INVALID")
    aset=set(aids)
    ident=(policy.policy_id,policy.version,policy.authority_epoch)
    for a in assumptions:
        if not a.assumption_id or not a.verified or a.revoked: reasons.append("ASSUMPTION_INVALID")
        if a.binding!=binding: reasons.append("ASSUMPTION_BINDING_MISMATCH")
        if (a.policy_id,a.policy_version,a.authority_epoch)!=ident: reasons.append("ASSUMPTION_POLICY_MISMATCH")
    for e in edges:
        if e.assumption_id not in aset or e.depends_on_id not in aset: reasons.append("EDGE_UNKNOWN_ASSUMPTION")
        if e.assumption_id==e.depends_on_id: reasons.append("SELF_DEPENDENCY")
    for x in evidence:
        if not x.evidence_id or x.assumption_id not in aset or not x.provenance_id: reasons.append("EVIDENCE_INVALID")
        if x.binding!=binding: reasons.append("EVIDENCE_BINDING_MISMATCH")
        if (x.policy_id,x.policy_version,x.authority_epoch)!=ident: reasons.append("EVIDENCE_POLICY_MISMATCH")
        if not (0<=x.confidence<=1): reasons.append("EVIDENCE_CONFIDENCE_INVALID")
    for x in observations:
        if not x.observation_id or x.assumption_id not in aset: reasons.append("OBSERVATION_INVALID")
        if x.binding!=binding: reasons.append("OBSERVATION_BINDING_MISMATCH")
        if (x.policy_id,x.policy_version,x.authority_epoch)!=ident: reasons.append("OBSERVATION_POLICY_MISMATCH")
    for x in actions:
        if not x.action_id or not x.depends_on or not x.verified or x.revoked: reasons.append("ACTION_INVALID")
        if x.binding!=binding: reasons.append("ACTION_BINDING_MISMATCH")
        if (x.policy_id,x.policy_version,x.authority_epoch)!=ident: reasons.append("ACTION_POLICY_MISMATCH")
        if any(a not in aset for a in x.depends_on): reasons.append("ACTION_UNKNOWN_ASSUMPTION")
    cycle,closure=_cycle_and_closure(aset,edges)
    if cycle: reasons.append("ASSUMPTION_CYCLE")
    action_closure={}
    if not cycle:
        for x in actions:
            deps=set(x.depends_on)
            for a in x.depends_on: deps.update(closure.get(a,()))
            action_closure[x.action_id]=tuple(sorted(deps))
    afp=_fps(assumptions,lambda x:x.assumption_id); efp=_fps(edges,_edge_key); vfp=_fps(evidence,lambda x:x.evidence_id); ofp=_fps(observations,lambda x:x.observation_id); xfp=_fps(actions,lambda x:x.action_id); pfp=fingerprint(policy)
    return PreparedAssumptionState(binding,not reasons,tuple(sorted(set(reasons))),policy,pfp,_registry_from_fps(binding,pfp,afp,efp,vfp,ofp,xfp),afp,efp,vfp,ofp,xfp,tuple(assumptions),tuple(edges),tuple(evidence),tuple(observations),tuple(actions),tuple(sorted(closure.items())),tuple(sorted(action_closure.items())),now)

def validate_prepared_integrity(p: PreparedAssumptionState) -> bool:
    # One-time trust-boundary validation must bind metadata fingerprints to the actual records,
    # not merely prove that the stored fingerprint lists are internally self-consistent.
    actual_policy_fp=fingerprint(p.policy)
    actual_afp=_fps(p.assumptions,lambda x:x.assumption_id)
    actual_efp=_fps(p.edges,_edge_key)
    actual_vfp=_fps(p.evidence,lambda x:x.evidence_id)
    actual_ofp=_fps(p.observations,lambda x:x.observation_id)
    actual_xfp=_fps(p.actions,lambda x:x.action_id)
    if actual_policy_fp!=p.policy_fingerprint: return False
    if actual_afp!=p.assumption_fingerprints or actual_efp!=p.edge_fingerprints or actual_vfp!=p.evidence_fingerprints or actual_ofp!=p.observation_fingerprints or actual_xfp!=p.action_fingerprints: return False
    return p.registry_fingerprint==_registry_from_fps(p.binding,actual_policy_fp,actual_afp,actual_efp,actual_vfp,actual_ofp,actual_xfp)

def _hold(req: VerificationRequest, reason: str, *, unverified=(), contradicted=(), impacted=(), risk=0.0) -> VerificationResult:
    return VerificationResult(Decision.HOLD,(reason,),(),tuple(sorted(set(unverified))),tuple(sorted(set(contradicted))),tuple(sorted(set(impacted))),risk,False,request_fingerprint(req))

def _classify(assumption_id: str, evidence: Sequence[EvidenceRecord], observations: Sequence[ObservationRecord], p: VerificationPolicy, now: int) -> EvidenceState:
    states=[]
    for x in evidence:
        if x.assumption_id!=assumption_id or not x.verified or x.revoked or not (x.observed_at<=now<=x.expires_at): continue
        if x.state==EvidenceState.VERIFIED and x.confidence < p.min_verified_confidence: continue
        states.append(x.state)
    for x in observations:
        if x.assumption_id!=assumption_id or not x.verified or x.revoked or not (x.observed_at<=now<=x.expires_at): continue
        states.append(x.state)
    if EvidenceState.CONTRADICTED in states: return EvidenceState.CONTRADICTED
    if EvidenceState.VERIFIED in states: return EvidenceState.VERIFIED
    return EvidenceState.UNVERIFIED

def evaluate_prepared(req: VerificationRequest, prepared: PreparedAssumptionState, *, current_policy_fingerprint: str, current_registry_fingerprint: str, prepared_integrity_validated: bool, now: int) -> VerificationResult:
    if not prepared_integrity_validated: return _hold(req,"PREPARED_INTEGRITY_NOT_VALIDATED")
    if current_policy_fingerprint!=prepared.policy_fingerprint: return _hold(req,"POLICY_FINGERPRINT_MISMATCH")
    if current_registry_fingerprint!=prepared.registry_fingerprint: return _hold(req,"REGISTRY_FINGERPRINT_MISMATCH")
    if not prepared.valid: return _hold(req,"PREPARED_STATE_INVALID:"+",".join(prepared.validation_reasons))
    p=prepared.policy
    if p.revoked or not (p.valid_from<=now<=p.expires_at): return _hold(req,"POLICY_INVALID")
    if (req.expected_policy_id,req.expected_policy_version,req.expected_authority_epoch)!=(p.policy_id,p.version,p.authority_epoch): return _hold(req,"REQUEST_POLICY_MISMATCH")
    if req.binding!=prepared.binding: return _hold(req,"REQUEST_BINDING_MISMATCH")
    if not req.request_id or not req.plan_id or not req.selected_action_ids: return _hold(req,"REQUEST_INCOMPLETE")
    if not (req.created_at<=now<=req.expires_at) or now-req.created_at>p.max_request_age_seconds: return _hold(req,"REQUEST_STALE_OR_EXPIRED")
    amap={x.assumption_id:x for x in prepared.assumptions}; xmap={x.action_id:x for x in prepared.actions}; ac=dict(prepared.action_dependency_closure)
    unknown=tuple(sorted(x for x in req.selected_action_ids if x not in xmap))
    if unknown: return _hold(req,"UNKNOWN_ACTION",impacted=unknown)
    deps=set()
    for aid in req.selected_action_ids: deps.update(ac.get(aid,()))
    verified=[]; unverified=[]; contradicted=[]; risk=0.0
    for aid in sorted(deps):
        state=_classify(aid,prepared.evidence,prepared.observations,p,now)
        if state==EvidenceState.CONTRADICTED: contradicted.append(aid)
        elif state==EvidenceState.VERIFIED: verified.append(aid)
        else:
            unverified.append(aid)
            impact=amap[aid].impact
            if impact==Impact.LOW: risk+=p.low_unverified_risk
    if contradicted:
        return VerificationResult(Decision.DENY,("CONTRADICTED_ASSUMPTION_DEPENDENCY",),tuple(verified),tuple(unverified),tuple(contradicted),tuple(sorted(req.selected_action_ids)),risk,False,request_fingerprint(req))
    blocking=tuple(sorted(a for a in unverified if amap[a].impact in p.hold_impacts or amap[a].impact==Impact.MEDIUM))
    if blocking:
        return VerificationResult(Decision.HOLD,("HIGH_OR_MEDIUM_IMPACT_UNVERIFIED",),tuple(verified),tuple(unverified),(),tuple(sorted(req.selected_action_ids)),risk,False,request_fingerprint(req))
    if risk>p.max_low_unverified_risk:
        return VerificationResult(Decision.HOLD,("LOW_IMPACT_RISK_BUDGET_EXCEEDED",),tuple(verified),tuple(unverified),(),tuple(sorted(req.selected_action_ids)),risk,False,request_fingerprint(req))
    reasons=("ALL_IMPORTANT_ASSUMPTIONS_VERIFIED",) if not unverified else ("ONLY_LOW_IMPACT_UNVERIFIED_WITHIN_RISK_BUDGET",)
    return VerificationResult(Decision.ALLOW,reasons,tuple(verified),tuple(unverified),(),tuple(sorted(req.selected_action_ids)),risk,True,request_fingerprint(req))

def evaluate(req: VerificationRequest, policy: VerificationPolicy, assumptions: Sequence[AssumptionSpec], edges: Sequence[AssumptionEdge], evidence: Sequence[EvidenceRecord], observations: Sequence[ObservationRecord], actions: Sequence[ActionSpec], *, now: int) -> VerificationResult:
    p=prepare_state(policy,assumptions,edges,evidence,observations,actions,binding=req.binding,now=now)
    return evaluate_prepared(req,p,current_policy_fingerprint=p.policy_fingerprint,current_registry_fingerprint=p.registry_fingerprint,prepared_integrity_validated=validate_prepared_integrity(p),now=now)

def _diff(base_items, target_items, key_fn):
    b={key_fn(x):x for x in base_items}; t={key_fn(x):x for x in target_items}
    changed=tuple(t[k] for k in sorted(set(b)&set(t)) if fingerprint(b[k])!=fingerprint(t[k]))
    removed=tuple(sorted(set(b)-set(t))); added=tuple(t[k] for k in sorted(set(t)-set(b)))
    return changed,removed,added

def make_delta(base: PreparedAssumptionState, target: PreparedAssumptionState) -> AssumptionRegistryDelta:
    ca,ra,aa=_diff(base.assumptions,target.assumptions,lambda x:x.assumption_id)
    ce,re,ae=_diff(base.edges,target.edges,_edge_key)
    cv,rv,av=_diff(base.evidence,target.evidence,lambda x:x.evidence_id)
    co,ro,ao=_diff(base.observations,target.observations,lambda x:x.observation_id)
    cx,rx,ax=_diff(base.actions,target.actions,lambda x:x.action_id)
    return AssumptionRegistryDelta(base.registry_fingerprint,target.registry_fingerprint,ca,ra,aa,ce,re,ae,cv,rv,av,co,ro,ao,cx,rx,ax)

def apply_delta(base: PreparedAssumptionState, d: AssumptionRegistryDelta, *, now: int) -> PreparedAssumptionState:
    if base.registry_fingerprint!=d.base_fingerprint: raise ValueError("BASE_FINGERPRINT_MISMATCH")
    def apply(items,changed,removed,added,key_fn):
        m={key_fn(x):x for x in items}
        for k in removed: m.pop(k,None)
        for x in changed: m[key_fn(x)]=x
        for x in added: m[key_fn(x)]=x
        return tuple(m[k] for k in sorted(m))
    a=apply(base.assumptions,d.changed_assumptions,d.removed_assumption_ids,d.added_assumptions,lambda x:x.assumption_id)
    e=apply(base.edges,d.changed_edges,d.removed_edge_keys,d.added_edges,_edge_key)
    v=apply(base.evidence,d.changed_evidence,d.removed_evidence_ids,d.added_evidence,lambda x:x.evidence_id)
    o=apply(base.observations,d.changed_observations,d.removed_observation_ids,d.added_observations,lambda x:x.observation_id)
    x=apply(base.actions,d.changed_actions,d.removed_action_ids,d.added_actions,lambda x:x.action_id)
    out=prepare_state(base.policy,a,e,v,o,x,binding=base.binding,now=now)
    if out.registry_fingerprint!=d.target_fingerprint: raise ValueError("TARGET_FINGERPRINT_MISMATCH")
    return out

def full_registry_bytes(p: PreparedAssumptionState) -> int:
    return len(canonical_json({"binding":p.binding,"policy":p.policy,"assumptions":p.assumptions,"edges":p.edges,"evidence":p.evidence,"observations":p.observations,"actions":p.actions}).encode())

def delta_bytes(d: AssumptionRegistryDelta) -> int:
    return len(canonical_json(d).encode())

def missing_only_sync_plan(p: PreparedAssumptionState, remote_fingerprints: Mapping[str,Mapping[str,str]]) -> AssumptionSyncPlan:
    groups=(
      ("assumptions",dict(p.assumption_fingerprints)),("edges",dict(p.edge_fingerprints)),("evidence",dict(p.evidence_fingerprints)),("observations",dict(p.observation_fingerprints)),("actions",dict(p.action_fingerprints)))
    miss=[]; payload={"registry":p.registry_fingerprint}
    for name,local in groups:
        remote=remote_fingerprints.get(name,{})
        m=tuple(sorted(k for k,v in local.items() if remote.get(k)!=v)); miss.append(m); payload[name]={k:local[k] for k in m}
    fb=full_registry_bytes(p); mb=len(canonical_json(payload).encode())
    return AssumptionSyncPlan(p.registry_fingerprint,*miss,mb,fb,mb>=fb)


def default_policy(now: int) -> VerificationPolicy:
    return VerificationPolicy("AVG-POLICY","1","AVG-EPOCH",now-1000,now+100000,False,frozenset({Impact.HIGH,Impact.CRITICAL}),0.2,0.8,0.8,3600)

def default_assumptions() -> tuple[AssumptionSpec,...]:
    c=dict(binding="AVG-BIND",verified=True,revoked=False,policy_id="AVG-POLICY",policy_version="1",authority_epoch="AVG-EPOCH")
    return (
      AssumptionSpec("ASM-CONFIG-EXISTS",Impact.HIGH,**c),
      AssumptionSpec("ASM-SCHEMA-COMPAT",Impact.HIGH,**c),
      AssumptionSpec("ASM-BACKUP-READY",Impact.MEDIUM,**c),
      AssumptionSpec("ASM-LOG-LABEL",Impact.LOW,**c),
    )

def default_edges() -> tuple[AssumptionEdge,...]:
    return (AssumptionEdge("ASM-SCHEMA-COMPAT","ASM-CONFIG-EXISTS"),)

def default_evidence(now: int) -> tuple[EvidenceRecord,...]:
    c=dict(binding="AVG-BIND",verified=True,revoked=False,policy_id="AVG-POLICY",policy_version="1",authority_epoch="AVG-EPOCH")
    return (
      EvidenceRecord("E-CONFIG","ASM-CONFIG-EXISTS",EvidenceState.VERIFIED,0.99,"PROV-CONFIG",now-10,now+1000,**c),
      EvidenceRecord("E-SCHEMA","ASM-SCHEMA-COMPAT",EvidenceState.VERIFIED,0.95,"PROV-SCHEMA",now-10,now+1000,**c),
      EvidenceRecord("E-BACKUP","ASM-BACKUP-READY",EvidenceState.VERIFIED,0.96,"PROV-BACKUP",now-10,now+1000,**c),
    )

def default_observations(now: int) -> tuple[ObservationRecord,...]:
    c=dict(binding="AVG-BIND",verified=True,revoked=False,policy_id="AVG-POLICY",policy_version="1",authority_epoch="AVG-EPOCH")
    return (ObservationRecord("O-CONFIG","ASM-CONFIG-EXISTS",EvidenceState.VERIFIED,now-5,now+1000,**c),)

def default_actions() -> tuple[ActionSpec,...]:
    c=dict(binding="AVG-BIND",verified=True,revoked=False,policy_id="AVG-POLICY",policy_version="1",authority_epoch="AVG-EPOCH")
    return (
      ActionSpec("ACT-UPDATE-CONFIG",("ASM-SCHEMA-COMPAT","ASM-BACKUP-READY"),**c),
      ActionSpec("ACT-READ-LOG",("ASM-LOG-LABEL",),**c),
    )

def default_request(now: int) -> VerificationRequest:
    return VerificationRequest("REQ-067","PLAN-067",("ACT-UPDATE-CONFIG",),"AVG-BIND","AVG-POLICY","1","AVG-EPOCH",now-10,now+1000)
