"""NOEPIN AL 074 — Sequential Risk Composer / Sequential Successor V2.

Deterministic, side-effect-free risk composition for ordered action chains. The
composer evaluates base risk, time-window decay, explicit interaction rules,
dependency/adjacency interactions, unknown-interaction upper-bound uplift, and
first stop point.

An ALLOW result is only a next-gate candidate. This module never grants
permission, approves a human request, executes a tool/action, mutates external
state, spends a risk budget, or promotes a risk estimate to Safety Truth.

DCSR is auxiliary only: canonical preparation, record fingerprints, prebuilt
indexes, verified delta reconstruction, and missing-only synchronization. A
Prepared state is not authoritative current state.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from hashlib import sha256
import json
from typing import Iterable, Tuple

SCHEMA_VERSION = "NOEPIN-AL-074-V2"

class Decision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    HOLD = "HOLD"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"

@dataclass(frozen=True)
class ActionRisk:
    action_id: str
    interaction_tag: str
    base_risk: int                 # fixed-point risk units; 10000 = policy budget default
    occurred_at: int
    dependencies: Tuple[str, ...]
    observed: bool
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class InteractionRule:
    rule_id: str
    left_tag: str
    right_tag: str
    relation: str                  # ADJACENT / DEPENDENCY / ANY
    risk_delta: int
    hard_deny: bool
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class RiskPolicy:
    policy_id: str
    binding: str
    state_epoch: str
    risk_budget: int
    deny_threshold: int
    unknown_interaction_risk: int
    decay_window_seconds: int
    decay_step: int
    max_sequence_length: int
    revoked: bool = False

@dataclass(frozen=True)
class RiskRequest:
    request_id: str
    sequence: Tuple[str, ...]
    time_window_seconds: int
    evaluated_at: int
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class RiskContribution:
    action_id: str
    effective_base_risk: int
    synergy_risk_added: int
    cumulative_risk: int
    unknown_interactions_added: int

@dataclass(frozen=True)
class SequentialRiskResult:
    decision: Decision
    reasons: Tuple[str, ...]
    cumulative_risk: int
    synergy_risk: int
    unknown_interaction_risk: int
    stop_point: int | None
    stop_action_id: str | None
    contributions: Tuple[RiskContribution, ...]
    next_gate_candidate: bool
    risk_budget_spent: bool = False
    permission_granted: bool = False
    human_approval_executed: bool = False
    tool_executed: bool = False
    transaction_committed: bool = False
    external_write_performed: bool = False
    world_truth_proven: bool = False
    safety_proven: bool = False
    action_success: bool = False

@dataclass(frozen=True)
class PreparedRiskState:
    policy: RiskPolicy
    actions: Tuple[ActionRisk, ...]
    rules: Tuple[InteractionRule, ...]
    binding: str
    state_epoch: str
    policy_fingerprint: str
    action_fingerprints: Tuple[Tuple[str, str], ...]
    rule_fingerprints: Tuple[Tuple[str, str], ...]
    registry_fingerprint: str
    action_index: Tuple[Tuple[str, ActionRisk], ...]
    rule_index: Tuple[Tuple[str, InteractionRule], ...]

@dataclass(frozen=True)
class RiskRegistryDelta:
    base_fingerprint: str
    target_fingerprint: str
    policy: RiskPolicy
    binding: str
    state_epoch: str
    upsert_actions: Tuple[ActionRisk, ...]
    remove_action_ids: Tuple[str, ...]
    upsert_rules: Tuple[InteractionRule, ...]
    remove_rule_ids: Tuple[str, ...]

@dataclass(frozen=True)
class RiskSyncPlan:
    missing_or_changed_actions: Tuple[str, ...]
    missing_or_changed_rules: Tuple[str, ...]
    metadata_bytes_required: int
    full_resend_required: bool


def _ser(obj) -> bytes:
    def norm(x):
        if isinstance(x, Enum): return x.value
        if hasattr(x, "__dataclass_fields__"):
            return {k: norm(getattr(x, k)) for k in sorted(x.__dataclass_fields__)}
        if isinstance(x, tuple): return [norm(v) for v in x]
        if isinstance(x, list): return [norm(v) for v in x]
        if isinstance(x, dict): return {str(k): norm(v) for k,v in sorted(x.items(), key=lambda kv:str(kv[0]))}
        return x
    return json.dumps(norm(obj), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()

def _fp(obj) -> str:
    return sha256(_ser(obj)).hexdigest()

def _canon_actions(actions: Iterable[ActionRisk]) -> Tuple[ActionRisk, ...]:
    out=[]; seen=set()
    for a in actions:
        if not a.action_id or a.action_id in seen: raise ValueError("INVALID_OR_DUPLICATE_ACTION_ID")
        if not a.interaction_tag or a.base_risk < 0: raise ValueError("INVALID_ACTION_RISK")
        deps=tuple(sorted(str(x) for x in a.dependencies))
        if any(not x for x in deps) or len(deps)!=len(set(deps)) or a.action_id in deps: raise ValueError("INVALID_DEPENDENCY")
        seen.add(a.action_id)
        out.append(replace(a, interaction_tag=str(a.interaction_tag).upper(), dependencies=deps))
    return tuple(sorted(out,key=lambda x:x.action_id))

def _canon_rules(rules: Iterable[InteractionRule]) -> Tuple[InteractionRule, ...]:
    out=[]; seen=set()
    for r in rules:
        if not r.rule_id or r.rule_id in seen: raise ValueError("INVALID_OR_DUPLICATE_RULE_ID")
        rel=str(r.relation).upper()
        if rel not in {"ADJACENT","DEPENDENCY","ANY"}: raise ValueError("INVALID_RELATION")
        if not r.left_tag or not r.right_tag or r.risk_delta < 0: raise ValueError("INVALID_RULE")
        seen.add(r.rule_id)
        out.append(replace(r,left_tag=str(r.left_tag).upper(),right_tag=str(r.right_tag).upper(),relation=rel))
    return tuple(sorted(out,key=lambda x:x.rule_id))

def _canon_request(req: RiskRequest) -> RiskRequest:
    seq=tuple(str(x) for x in req.sequence)
    if not seq or any(not x for x in seq) or len(seq)!=len(set(seq)): raise ValueError("INVALID_OR_DUPLICATE_SEQUENCE")
    if req.time_window_seconds <= 0 or req.evaluated_at < 0: raise ValueError("INVALID_TIME_WINDOW_OR_EVALUATION_TIME")
    return replace(req,sequence=seq)

def default_policy() -> RiskPolicy:
    return RiskPolicy("RISK-COMP-POLICY","RISK-BIND","STATE-EPOCH-1",10000,16000,1500,300,500,64)

def default_actions(now: int) -> Tuple[ActionRisk, ...]:
    return (
        ActionRisk("A-READ","READ",1800,now-30,(),True,"RISK-BIND","STATE-EPOCH-1"),
        ActionRisk("A-ANALYZE","ANALYZE",1600,now-20,("A-READ",),True,"RISK-BIND","STATE-EPOCH-1"),
        ActionRisk("A-WRITE","WRITE",2500,now-10,("A-ANALYZE",),True,"RISK-BIND","STATE-EPOCH-1"),
        ActionRisk("A-SEND","SEND",3000,now,("A-WRITE",),True,"RISK-BIND","STATE-EPOCH-1"),
    )

def default_rules() -> Tuple[InteractionRule, ...]:
    return (
        InteractionRule("R-READ-ANALYZE","READ","ANALYZE","ANY",0,False,"RISK-BIND","STATE-EPOCH-1"),
        InteractionRule("R-ANALYZE-WRITE","ANALYZE","WRITE","ANY",500,False,"RISK-BIND","STATE-EPOCH-1"),
        InteractionRule("R-WRITE-SEND","WRITE","SEND","ANY",2500,False,"RISK-BIND","STATE-EPOCH-1"),
        InteractionRule("R-DELETE-SEND","DELETE","SEND","ANY",7000,True,"RISK-BIND","STATE-EPOCH-1"),
        InteractionRule("R-EXPORT-PRIV","EXPORT","PRIVILEGE","ANY",8000,True,"RISK-BIND","STATE-EPOCH-1"),
    )

def default_request() -> RiskRequest:
    return RiskRequest("REQ-74",("A-READ","A-ANALYZE"),600,1_800_000_000,"RISK-BIND","STATE-EPOCH-1")

def _invalid(reason: str) -> SequentialRiskResult:
    return SequentialRiskResult(Decision.HOLD,(reason,),0,0,0,None,None,(),False)

def _rule_lookup(rules: Tuple[InteractionRule,...]):
    idx={}
    for r in rules:
        idx.setdefault((r.left_tag,r.right_tag,r.relation),[]).append(r)
        if r.relation=="ANY":
            idx.setdefault((r.left_tag,r.right_tag,"ADJACENT"),[]).append(r)
            idx.setdefault((r.left_tag,r.right_tag,"DEPENDENCY"),[]).append(r)
    return idx

def _decayed(base: int, action_time: int, end_time: int, policy: RiskPolicy, req_window: int) -> int:
    if action_time > end_time: raise ValueError("ACTION_TIME_IN_FUTURE")
    age=end_time-action_time
    # Request time window is a hard inclusion window. Older actions contribute 0 to this request.
    if age > req_window: return 0
    windows=age//policy.decay_window_seconds
    return max(0, base - windows*policy.decay_step)

def _evaluate_core(req: RiskRequest, policy: RiskPolicy, action_map, rules: Tuple[InteractionRule,...], rule_idx) -> SequentialRiskResult:
    if policy.revoked: return _invalid("POLICY_REVOKED")
    if not policy.binding or req.binding!=policy.binding: return _invalid("BINDING_MISMATCH")
    if not policy.state_epoch or req.state_epoch!=policy.state_epoch: return _invalid("STATE_EPOCH_MISMATCH")
    if len(req.sequence)>policy.max_sequence_length: return _invalid("SEQUENCE_LENGTH_EXCEEDED")
    seq=[]
    for aid in req.sequence:
        a=action_map.get(aid)
        if a is None: return _invalid("UNKNOWN_ACTION")
        if not a.observed: return _invalid("ACTION_RISK_UNOBSERVED")
        if a.binding!=policy.binding or a.state_epoch!=policy.state_epoch: return _invalid("ACTION_BINDING_OR_EPOCH_MISMATCH")
        seq.append(a)
    pos={a.action_id:i for i,a in enumerate(seq)}
    for a in seq:
        for dep in a.dependencies:
            if dep not in action_map: return _invalid("UNKNOWN_DEPENDENCY")
            if dep in pos and pos[dep] >= pos[a.action_id]: return _invalid("DEPENDENCY_ORDER_INVALID")
    end=req.evaluated_at
    cumulative=0; synergy=0; unknown_total=0; contributions=[]
    processed=[]
    for i,a in enumerate(seq):
        try:
            base=_decayed(a.base_risk,a.occurred_at,end,policy,req.time_window_seconds)
        except Exception:
            return _invalid("ACTION_TIME_INVALID")
        if a.base_risk>policy.deny_threshold:
            return SequentialRiskResult(Decision.DENY,("SINGLE_ACTION_RISK_HARD_LIMIT",),cumulative+base,synergy,unknown_total,i,a.action_id,tuple(contributions),False)
        added=0; unknown_added=0; hard=False
        # adjacency relation
        if i>0:
            left=seq[i-1]
            matches=rule_idx.get((left.interaction_tag,a.interaction_tag,"ADJACENT"),[])
            if matches:
                for r in matches:
                    if r.binding!=policy.binding or r.state_epoch!=policy.state_epoch: return _invalid("RULE_BINDING_OR_EPOCH_MISMATCH")
                    added += r.risk_delta
                    hard |= r.hard_deny
            else:
                added += policy.unknown_interaction_risk; unknown_added += policy.unknown_interaction_risk
        # explicit dependencies can interact even if not adjacent
        for dep in a.dependencies:
            if dep in pos and pos[dep] < i:
                left=seq[pos[dep]]
                if i-1==pos[dep]:
                    continue  # already counted as adjacency; avoid double count
                matches=rule_idx.get((left.interaction_tag,a.interaction_tag,"DEPENDENCY"),[])
                if matches:
                    for r in matches:
                        if r.binding!=policy.binding or r.state_epoch!=policy.state_epoch: return _invalid("RULE_BINDING_OR_EPOCH_MISMATCH")
                        added += r.risk_delta; hard |= r.hard_deny
                else:
                    added += policy.unknown_interaction_risk; unknown_added += policy.unknown_interaction_risk
        cumulative += base + added
        synergy += added; unknown_total += unknown_added
        contributions.append(RiskContribution(a.action_id,base,added,cumulative,unknown_added))
        processed.append(a.action_id)
        if hard:
            return SequentialRiskResult(Decision.DENY,("HARD_INTERACTION_PATTERN",),cumulative,synergy,unknown_total,i,a.action_id,tuple(contributions),False)
        if cumulative >= policy.deny_threshold:
            return SequentialRiskResult(Decision.DENY,("RISK_DENY_THRESHOLD_EXCEEDED",),cumulative,synergy,unknown_total,i,a.action_id,tuple(contributions),False)
        if cumulative > policy.risk_budget:
            rs=("RISK_BUDGET_EXCEEDED",)+( ("UNKNOWN_INTERACTION_UPPER_BOUND_APPLIED",) if unknown_total else () )
            return SequentialRiskResult(Decision.HOLD,rs,cumulative,synergy,unknown_total,i,a.action_id,tuple(contributions),False)
    reasons=("RISK_WITHIN_BUDGET",)
    if unknown_total:
        reasons += ("UNKNOWN_INTERACTION_UPPER_BOUND_APPLIED",)
    return SequentialRiskResult(Decision.ALLOW,reasons,cumulative,synergy,unknown_total,None,None,tuple(contributions),True)

def evaluate(request: RiskRequest, policy: RiskPolicy, actions: Iterable[ActionRisk], rules: Iterable[InteractionRule]) -> SequentialRiskResult:
    try:
        req=_canon_request(request); acts=_canon_actions(actions); rls=_canon_rules(rules)
        amap={a.action_id:a for a in acts}; ridx=_rule_lookup(rls)
    except Exception:
        return _invalid("INVALID_TYPED_INPUT")
    return _evaluate_core(req,policy,amap,rls,ridx)

def prepare_state(policy: RiskPolicy, actions: Iterable[ActionRisk], rules: Iterable[InteractionRule], *, binding: str) -> PreparedRiskState:
    acts=_canon_actions(actions); rls=_canon_rules(rules)
    if binding!=policy.binding: raise ValueError("BINDING_MISMATCH")
    if any(a.binding!=binding or a.state_epoch!=policy.state_epoch for a in acts): raise ValueError("ACTION_BINDING_OR_EPOCH_MISMATCH")
    if any(r.binding!=binding or r.state_epoch!=policy.state_epoch for r in rls): raise ValueError("RULE_BINDING_OR_EPOCH_MISMATCH")
    af=tuple((a.action_id,_fp(a)) for a in acts); rf=tuple((r.rule_id,_fp(r)) for r in rls)
    pf=_fp(policy)
    reg=_fp((pf,af,rf,binding,policy.state_epoch))
    rule_index=[]
    for r in rls:
        rule_index.append((f"{r.left_tag}|{r.right_tag}|{r.relation}|{r.rule_id}",r))
    return PreparedRiskState(policy,acts,rls,binding,policy.state_epoch,pf,af,rf,reg,tuple((a.action_id,a) for a in acts),tuple(rule_index))

def validate_prepared_integrity(st: PreparedRiskState) -> bool:
    try:
        acts=_canon_actions(st.actions); rls=_canon_rules(st.rules)
        if _fp(st.policy)!=st.policy_fingerprint: return False
        if tuple((a.action_id,_fp(a)) for a in acts)!=st.action_fingerprints: return False
        if tuple((r.rule_id,_fp(r)) for r in rls)!=st.rule_fingerprints: return False
        if tuple((a.action_id,a) for a in acts)!=st.action_index: return False
        expected_rules=tuple((f"{r.left_tag}|{r.right_tag}|{r.relation}|{r.rule_id}",r) for r in rls)
        if expected_rules!=st.rule_index: return False
        return _fp((st.policy_fingerprint,st.action_fingerprints,st.rule_fingerprints,st.binding,st.state_epoch))==st.registry_fingerprint
    except Exception:
        return False

def evaluate_prepared(request: RiskRequest, st: PreparedRiskState, *, current_policy_fingerprint: str, current_registry_fingerprint: str, prepared_integrity_validated: bool) -> SequentialRiskResult:
    if not prepared_integrity_validated: return _invalid("PREPARED_INTEGRITY_NOT_VALIDATED")
    if current_policy_fingerprint!=st.policy_fingerprint: return _invalid("POLICY_FINGERPRINT_CHANGED")
    if current_registry_fingerprint!=st.registry_fingerprint: return _invalid("REGISTRY_FINGERPRINT_CHANGED")
    try:
        req=_canon_request(request)
        amap=dict(st.action_index)
        ridx=_rule_lookup(st.rules)
    except Exception:
        return _invalid("INVALID_TYPED_INPUT")
    return _evaluate_core(req,st.policy,amap,st.rules,ridx)

def make_delta(base: PreparedRiskState, target: PreparedRiskState) -> RiskRegistryDelta:
    if not validate_prepared_integrity(base) or not validate_prepared_integrity(target): raise ValueError("UNVERIFIED_PREPARED_STATE")
    if base.binding!=target.binding or base.state_epoch!=target.state_epoch: raise ValueError("BINDING_OR_EPOCH_CHANGED")
    ba=dict(base.action_fingerprints); ta=dict(target.action_fingerprints); br=dict(base.rule_fingerprints); tr=dict(target.rule_fingerprints)
    tacts=dict(target.action_index); trules={r.rule_id:r for r in target.rules}
    return RiskRegistryDelta(base.registry_fingerprint,target.registry_fingerprint,target.policy,target.binding,target.state_epoch,
        tuple(tacts[k] for k in sorted(ta) if ba.get(k)!=ta[k]),tuple(sorted(k for k in ba if k not in ta)),
        tuple(trules[k] for k in sorted(tr) if br.get(k)!=tr[k]),tuple(sorted(k for k in br if k not in tr)))

def apply_delta(base: PreparedRiskState, delta: RiskRegistryDelta) -> PreparedRiskState:
    if not validate_prepared_integrity(base) or base.registry_fingerprint!=delta.base_fingerprint: raise ValueError("BASE_FINGERPRINT_MISMATCH")
    amap=dict(base.action_index); rmap={r.rule_id:r for r in base.rules}
    for k in delta.remove_action_ids: amap.pop(k,None)
    for a in delta.upsert_actions: amap[a.action_id]=a
    for k in delta.remove_rule_ids: rmap.pop(k,None)
    for r in delta.upsert_rules: rmap[r.rule_id]=r
    out=prepare_state(delta.policy,amap.values(),rmap.values(),binding=delta.binding)
    if out.registry_fingerprint!=delta.target_fingerprint: raise ValueError("TARGET_FINGERPRINT_MISMATCH")
    return out

def missing_only_sync_plan(target: PreparedRiskState, remote_action_fps: dict[str,str], remote_rule_fps: dict[str,str]) -> RiskSyncPlan:
    if not validate_prepared_integrity(target): raise ValueError("UNVERIFIED_TARGET")
    ma=tuple(k for k,v in target.action_fingerprints if remote_action_fps.get(k)!=v)
    mr=tuple(k for k,v in target.rule_fingerprints if remote_rule_fps.get(k)!=v)
    meta=len(_ser((ma,mr)))
    return RiskSyncPlan(ma,mr,meta,False)

def full_registry_bytes(st: PreparedRiskState) -> int: return len(_ser(st))
def delta_bytes(d: RiskRegistryDelta) -> int: return len(_ser(d))
