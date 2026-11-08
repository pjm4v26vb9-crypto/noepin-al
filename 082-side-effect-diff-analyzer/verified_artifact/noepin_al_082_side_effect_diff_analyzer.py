"""NOEPIN AL 082 — Side-Effect Diff Analyzer — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Deterministic, fail-safe analyzer for before/after state differences. It separates
expected effects from unexpected effects and detects protected-field changes. It
never executes rollback, commits state, grants permission, writes to an external
environment, or promotes a partial observation to authoritative truth.

Canonical identity: NOEPIN-AL-082
Provenance note: exact registered Origin GUID was not freshly reverified in this
completion session and is intentionally not guessed or regenerated.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Sequence


class Decision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    HOLD = "HOLD"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"


class Severity(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ChangeKind(str, Enum):
    ADD = "ADD"
    REMOVE = "REMOVE"
    CHANGE = "CHANGE"


@dataclass(frozen=True)
class StateField:
    path: str
    value: str | None
    exists: bool
    observed: bool
    source_id: str
    binding: str
    state_epoch: str


@dataclass(frozen=True)
class ExpectedEffect:
    effect_id: str
    path: str
    kind: ChangeKind
    expected_before: str | None
    expected_after: str | None
    required: bool
    binding: str
    state_epoch: str


@dataclass(frozen=True)
class ProtectedField:
    rule_id: str
    path: str
    prefix_match: bool
    binding: str
    state_epoch: str


@dataclass(frozen=True)
class SeverityRule:
    rule_id: str
    path: str
    prefix_match: bool
    severity: Severity
    binding: str
    state_epoch: str


@dataclass(frozen=True)
class DiffRequest:
    request_id: str
    intent_id: str
    expected_effect_ids: tuple[str, ...]
    protected_rule_ids: tuple[str, ...]
    before_complete: bool
    after_complete: bool
    minor_allowed_paths: tuple[str, ...]
    binding: str
    state_epoch: str


@dataclass(frozen=True)
class DiffPolicy:
    binding: str
    state_epoch: str
    default_unexpected_severity: Severity = Severity.MEDIUM
    major_threshold: Severity = Severity.HIGH
    large_diff_threshold: int = 100
    revoked: bool = False


@dataclass(frozen=True)
class DiffEntry:
    path: str
    kind: ChangeKind
    before_value: str | None
    after_value: str | None
    severity: Severity
    matched_expected_effect_id: str | None
    protected_rule_id: str | None


@dataclass(frozen=True)
class DiffResult:
    decision: Decision
    reasons: tuple[str, ...]
    expected_diff: tuple[DiffEntry, ...]
    unexpected_diff: tuple[DiffEntry, ...]
    missing_expected_effects: tuple[str, ...]
    highest_severity: Severity
    actual_change_count: int
    next_gate_candidate: bool
    rollback_candidate: bool
    permission_granted: bool = False
    rollback_executed: bool = False
    state_committed: bool = False
    external_write_performed: bool = False
    action_executed: bool = False
    world_truth_proven: bool = False
    safety_proven: bool = False
    action_success: bool = False


@dataclass(frozen=True)
class PreparedDiffState:
    policy: DiffPolicy
    request: DiffRequest
    before_state: tuple[StateField, ...]
    after_state: tuple[StateField, ...]
    expected_effects: tuple[ExpectedEffect, ...]
    protected_fields: tuple[ProtectedField, ...]
    severity_rules: tuple[SeverityRule, ...]
    before_fingerprints: tuple[tuple[str, str], ...]
    after_fingerprints: tuple[tuple[str, str], ...]
    expected_fingerprints: tuple[tuple[str, str], ...]
    protected_fingerprints: tuple[tuple[str, str], ...]
    severity_fingerprints: tuple[tuple[str, str], ...]
    policy_fingerprint: str
    request_fingerprint: str
    registry_fingerprint: str
    before_index: tuple[tuple[str, StateField], ...]
    after_index: tuple[tuple[str, StateField], ...]
    expected_index: tuple[tuple[str, ExpectedEffect], ...]
    protected_index: tuple[tuple[str, ProtectedField], ...]
    severity_index: tuple[tuple[str, SeverityRule], ...]
    binding: str
    state_epoch: str


@dataclass(frozen=True)
class DiffStateDelta:
    base_fingerprint: str
    target_fingerprint: str
    changed_before: tuple[StateField, ...]
    removed_before_paths: tuple[str, ...]
    changed_after: tuple[StateField, ...]
    removed_after_paths: tuple[str, ...]
    changed_expected: tuple[ExpectedEffect, ...]
    removed_expected_ids: tuple[str, ...]
    changed_protected: tuple[ProtectedField, ...]
    removed_protected_ids: tuple[str, ...]
    changed_severity: tuple[SeverityRule, ...]
    removed_severity_ids: tuple[str, ...]
    target_policy: DiffPolicy
    target_request: DiffRequest
    binding: str
    state_epoch: str


@dataclass(frozen=True)
class DiffSyncPlan:
    missing_or_changed_before_paths: tuple[str, ...]
    missing_or_changed_after_paths: tuple[str, ...]
    missing_or_changed_expected_ids: tuple[str, ...]
    missing_or_changed_protected_ids: tuple[str, ...]
    missing_or_changed_severity_ids: tuple[str, ...]
    metadata_bytes_required: int
    full_resend_required: bool


def _canon(value) -> bytes:
    def cv(x):
        if isinstance(x, Enum): return x.value
        if hasattr(x, "__dataclass_fields__"): return {k: cv(getattr(x,k)) for k in x.__dataclass_fields__}
        if isinstance(x, tuple): return [cv(i) for i in x]
        if isinstance(x, list): return [cv(i) for i in x]
        if isinstance(x, dict): return {str(k): cv(x[k]) for k in sorted(x)}
        return x
    return json.dumps(cv(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def _fp(value) -> str: return sha256(_canon(value)).hexdigest()

def _idx(items, key: str): return tuple(sorted(((getattr(x,key),x) for x in items), key=lambda z:z[0]))

def _lookup(index,key):
    lo,hi=0,len(index)
    while lo<hi:
        mid=(lo+hi)//2
        if index[mid][0] < key: lo=mid+1
        else: hi=mid
    return index[lo][1] if lo<len(index) and index[lo][0]==key else None

def _unique(items, attr: str) -> bool:
    vals=[getattr(x,attr) for x in items]
    return len(vals)==len(set(vals))

def _binding_ok(obj, policy: DiffPolicy) -> bool:
    return getattr(obj,'binding',None)==policy.binding and getattr(obj,'state_epoch',None)==policy.state_epoch

def _sev_rank(s: Severity) -> int:
    return {Severity.NONE:0,Severity.LOW:1,Severity.MEDIUM:2,Severity.HIGH:3,Severity.CRITICAL:4}[s]

def _highest(entries: Sequence[DiffEntry]) -> Severity:
    if not entries: return Severity.NONE
    return max((x.severity for x in entries),key=_sev_rank)

def _path_matches(path: str, rule_path: str, prefix: bool) -> bool:
    if not prefix: return path==rule_path
    return path==rule_path or path.startswith(rule_path.rstrip('/') + '/')

def _derive_change(before: StateField, after: StateField):
    if before.exists==after.exists and before.value==after.value: return None
    if not before.exists and after.exists: return ChangeKind.ADD
    if before.exists and not after.exists: return ChangeKind.REMOVE
    return ChangeKind.CHANGE

def _expected_matches(entry_kind: ChangeKind, before: StateField, after: StateField, effect: ExpectedEffect) -> bool:
    if entry_kind != effect.kind or before.path != effect.path: return False
    if effect.expected_before is not None and before.value != effect.expected_before: return False
    if effect.expected_after is not None and after.value != effect.expected_after: return False
    return True

def _registry_fp(policy,request,before_state,after_state,expected,protected,severity) -> str:
    return _fp({
        'policy':_fp(policy),'request':_fp(request),
        'before':sorted((x.path,_fp(x)) for x in before_state),
        'after':sorted((x.path,_fp(x)) for x in after_state),
        'expected':sorted((x.effect_id,_fp(x)) for x in expected),
        'protected':sorted((x.rule_id,_fp(x)) for x in protected),
        'severity':sorted((x.rule_id,_fp(x)) for x in severity),
    })


def default_policy() -> DiffPolicy:
    return DiffPolicy('DIFF-BIND','STATE-EPOCH-1')

def default_request() -> DiffRequest:
    return DiffRequest('REQ-082-1','INTENT-082-1',('E-CONFIG','E-STATUS'),('P-SECRETS',),True,True,('logs/trace',),'DIFF-BIND','STATE-EPOCH-1')

def default_before_state() -> tuple[StateField,...]:
    b,e='DIFF-BIND','STATE-EPOCH-1'
    return (
        StateField('config/mode','old',True,True,'READ-1',b,e),
        StateField('status','PENDING',True,True,'READ-1',b,e),
        StateField('secrets/token','KEEP',True,True,'READ-1',b,e),
        StateField('logs/trace',None,False,True,'READ-1',b,e),
    )

def default_after_state() -> tuple[StateField,...]:
    b,e='DIFF-BIND','STATE-EPOCH-1'
    return (
        StateField('config/mode','new',True,True,'READ-2',b,e),
        StateField('status','READY',True,True,'READ-2',b,e),
        StateField('secrets/token','KEEP',True,True,'READ-2',b,e),
        StateField('logs/trace',None,False,True,'READ-2',b,e),
    )

def default_expected_effects() -> tuple[ExpectedEffect,...]:
    b,e='DIFF-BIND','STATE-EPOCH-1'
    return (
        ExpectedEffect('E-CONFIG','config/mode',ChangeKind.CHANGE,'old','new',True,b,e),
        ExpectedEffect('E-STATUS','status',ChangeKind.CHANGE,'PENDING','READY',True,b,e),
    )

def default_protected_fields() -> tuple[ProtectedField,...]:
    b,e='DIFF-BIND','STATE-EPOCH-1'
    return (ProtectedField('P-SECRETS','secrets',True,b,e),)

def default_severity_rules() -> tuple[SeverityRule,...]:
    b,e='DIFF-BIND','STATE-EPOCH-1'
    return (
        SeverityRule('S-SECRETS','secrets',True,Severity.CRITICAL,b,e),
        SeverityRule('S-PROJECT','project/settings',True,Severity.HIGH,b,e),
        SeverityRule('S-LOGS','logs',True,Severity.LOW,b,e),
    )


def _hold(reason: str, expected=(), unexpected=(), missing=(), highest=Severity.NONE, count=0, rollback=False) -> DiffResult:
    return DiffResult(Decision.HOLD,(reason,),tuple(expected),tuple(unexpected),tuple(missing),highest,count,False,rollback)


def _evaluate(request: DiffRequest, policy: DiffPolicy, before_state: Sequence[StateField], after_state: Sequence[StateField], expected_effects: Sequence[ExpectedEffect], protected_fields: Sequence[ProtectedField], severity_rules: Sequence[SeverityRule], *, before_index=None, after_index=None, expected_index=None, protected_index=None, severity_index=None) -> DiffResult:
    if not isinstance(request,DiffRequest) or not isinstance(policy,DiffPolicy): return _hold('INVALID_TYPED_INPUT')
    if policy.revoked: return _hold('DIFF_POLICY_REVOKED')
    if not _binding_ok(request,policy): return _hold('REQUEST_BINDING_OR_EPOCH_MISMATCH')
    if not request.request_id or not request.intent_id: return _hold('REQUEST_OR_INTENT_ID_MISSING')
    if not request.before_complete or not request.after_complete: return _hold('STATE_DIFF_INCOMPLETE')
    if policy.large_diff_threshold <= 0: return _hold('INVALID_LARGE_DIFF_THRESHOLD')
    if not _unique(before_state,'path') or not _unique(after_state,'path'): return _hold('DUPLICATE_STATE_PATH')
    if not _unique(expected_effects,'effect_id'): return _hold('DUPLICATE_EXPECTED_EFFECT_ID')
    if not _unique(protected_fields,'rule_id'): return _hold('DUPLICATE_PROTECTED_RULE_ID')
    if not _unique(severity_rules,'rule_id'): return _hold('DUPLICATE_SEVERITY_RULE_ID')
    if len(request.expected_effect_ids)!=len(set(request.expected_effect_ids)): return _hold('DUPLICATE_REQUEST_EXPECTED_EFFECT')
    if len(request.protected_rule_ids)!=len(set(request.protected_rule_ids)): return _hold('DUPLICATE_REQUEST_PROTECTED_RULE')
    if len(request.minor_allowed_paths)!=len(set(request.minor_allowed_paths)): return _hold('DUPLICATE_MINOR_ALLOW_PATH')
    for seq,label in ((before_state,'BEFORE'),(after_state,'AFTER'),(expected_effects,'EXPECTED'),(protected_fields,'PROTECTED'),(severity_rules,'SEVERITY')):
        for x in seq:
            if not _binding_ok(x,policy): return _hold(f'{label}_BINDING_OR_EPOCH_MISMATCH')
    if any(not x.observed for x in before_state) or any(not x.observed for x in after_state): return _hold('STATE_FIELD_UNOBSERVED')

    bi=before_index if before_index is not None else _idx(before_state,'path')
    ai=after_index if after_index is not None else _idx(after_state,'path')
    ei=expected_index if expected_index is not None else _idx(expected_effects,'effect_id')
    pi=protected_index if protected_index is not None else _idx(protected_fields,'rule_id')

    selected_expected=[]
    for eid in request.expected_effect_ids:
        x=_lookup(ei,eid)
        if x is None: return _hold('EXPECTED_EFFECT_UNKNOWN')
        selected_expected.append(x)
    selected_protected=[]
    for rid in request.protected_rule_ids:
        x=_lookup(pi,rid)
        if x is None: return _hold('PROTECTED_RULE_UNKNOWN')
        selected_protected.append(x)

    before_map=dict(bi); after_map=dict(ai)
    all_paths=sorted(set(before_map)|set(after_map))
    # A missing record on one side is valid only if the other side explicitly says the path exists/doesn't exist.
    # To avoid inventing observations, synthesize ABSENT only for absent record when the opposite side is observed.
    changes=[]
    matched=set()
    expected_entries=[]; unexpected_entries=[]
    for path in all_paths:
        bf=before_map.get(path)
        af=after_map.get(path)
        if bf is None:
            af0=af; bf=StateField(path,None,False,True,'SYNTH-ABSENT-BEFORE',policy.binding,policy.state_epoch)
            if af0 is None: continue
        if af is None:
            bf0=bf; af=StateField(path,None,False,True,'SYNTH-ABSENT-AFTER',policy.binding,policy.state_epoch)
            if bf0 is None: continue
        kind=_derive_change(bf,af)
        if kind is None: continue
        changes.append(path)
        matched_effect=None
        for effect in selected_expected:
            if _expected_matches(kind,bf,af,effect):
                matched_effect=effect; matched.add(effect.effect_id); break
        protected=None
        for rule in selected_protected:
            if _path_matches(path,rule.path,rule.prefix_match): protected=rule; break
        sev=None
        if protected is not None: sev=Severity.CRITICAL
        else:
            # Most specific matching severity rule wins; tie breaks by rule id deterministically.
            candidates=[x for x in severity_rules if _path_matches(path,x.path,x.prefix_match)]
            if candidates:
                candidates=sorted(candidates,key=lambda x:(len(x.path),_sev_rank(x.severity),x.rule_id),reverse=True)
                sev=candidates[0].severity
            elif path in set(request.minor_allowed_paths): sev=Severity.LOW
            else: sev=policy.default_unexpected_severity
        entry=DiffEntry(path,kind,bf.value if bf.exists else None,af.value if af.exists else None,sev,matched_effect.effect_id if matched_effect else None,protected.rule_id if protected else None)
        if matched_effect is not None and protected is None: expected_entries.append(entry)
        else: unexpected_entries.append(entry)

    missing=sorted(x.effect_id for x in selected_expected if x.required and x.effect_id not in matched)
    expected_entries=tuple(sorted(expected_entries,key=lambda x:(x.path,x.kind.value)))
    unexpected_entries=tuple(sorted(unexpected_entries,key=lambda x:(x.path,x.kind.value)))
    high=_highest(unexpected_entries)
    protected_changed=any(x.protected_rule_id is not None for x in unexpected_entries)

    if protected_changed:
        return DiffResult(Decision.DENY,('PROTECTED_FIELD_CHANGED',),expected_entries,unexpected_entries,tuple(missing),high,len(changes),False,True)
    if missing:
        return _hold('REQUIRED_EXPECTED_EFFECT_NOT_OBSERVED',expected_entries,unexpected_entries,missing,high,len(changes))
    if len(changes) >= policy.large_diff_threshold:
        return _hold('LARGE_DIFF_REQUIRES_REVIEW',expected_entries,unexpected_entries,(),max(high,Severity.HIGH,key=_sev_rank),len(changes))
    if unexpected_entries:
        if _sev_rank(high) >= _sev_rank(policy.major_threshold):
            return _hold('MAJOR_UNEXPECTED_DIFF',expected_entries,unexpected_entries,(),high,len(changes))
        not_minor=[x for x in unexpected_entries if not (x.severity==Severity.LOW and x.path in set(request.minor_allowed_paths))]
        if not_minor:
            return _hold('UNEXPECTED_DIFF_OUTSIDE_MINOR_POLICY',expected_entries,unexpected_entries,(),high,len(changes))
        return DiffResult(Decision.ALLOW,('EXPECTED_DIFF_CONFIRMED','MINOR_UNEXPECTED_DIFF_WITHIN_EXPLICIT_POLICY'),expected_entries,unexpected_entries,(),high,len(changes),True,False)
    return DiffResult(Decision.ALLOW,('EXPECTED_DIFF_ONLY','NO_UNEXPECTED_DIFF'),expected_entries,(),(),Severity.NONE,len(changes),True,False)


def evaluate(request: DiffRequest, policy: DiffPolicy, before_state: Sequence[StateField], after_state: Sequence[StateField], expected_effects: Sequence[ExpectedEffect], protected_fields: Sequence[ProtectedField], severity_rules: Sequence[SeverityRule]) -> DiffResult:
    return _evaluate(request,policy,before_state,after_state,expected_effects,protected_fields,severity_rules)


def prepare_state(policy: DiffPolicy, request: DiffRequest, before_state: Sequence[StateField], after_state: Sequence[StateField], expected_effects: Sequence[ExpectedEffect], protected_fields: Sequence[ProtectedField], severity_rules: Sequence[SeverityRule], *, binding: str) -> PreparedDiffState:
    before=tuple(sorted(before_state,key=lambda x:x.path)); after=tuple(sorted(after_state,key=lambda x:x.path)); expected=tuple(sorted(expected_effects,key=lambda x:x.effect_id)); protected=tuple(sorted(protected_fields,key=lambda x:x.rule_id)); severity=tuple(sorted(severity_rules,key=lambda x:x.rule_id))
    return PreparedDiffState(policy,request,before,after,expected,protected,severity,
        tuple((x.path,_fp(x)) for x in before),tuple((x.path,_fp(x)) for x in after),tuple((x.effect_id,_fp(x)) for x in expected),tuple((x.rule_id,_fp(x)) for x in protected),tuple((x.rule_id,_fp(x)) for x in severity),
        _fp(policy),_fp(request),_registry_fp(policy,request,before,after,expected,protected,severity),
        _idx(before,'path'),_idx(after,'path'),_idx(expected,'effect_id'),_idx(protected,'rule_id'),_idx(severity,'rule_id'),binding,policy.state_epoch)


def validate_prepared_integrity(state: PreparedDiffState) -> bool:
    if not isinstance(state,PreparedDiffState): return False
    if state.binding!=state.policy.binding or state.state_epoch!=state.policy.state_epoch: return False
    if state.policy_fingerprint!=_fp(state.policy) or state.request_fingerprint!=_fp(state.request): return False
    if state.before_fingerprints!=tuple((x.path,_fp(x)) for x in state.before_state): return False
    if state.after_fingerprints!=tuple((x.path,_fp(x)) for x in state.after_state): return False
    if state.expected_fingerprints!=tuple((x.effect_id,_fp(x)) for x in state.expected_effects): return False
    if state.protected_fingerprints!=tuple((x.rule_id,_fp(x)) for x in state.protected_fields): return False
    if state.severity_fingerprints!=tuple((x.rule_id,_fp(x)) for x in state.severity_rules): return False
    if state.before_index!=_idx(state.before_state,'path') or state.after_index!=_idx(state.after_state,'path'): return False
    if state.expected_index!=_idx(state.expected_effects,'effect_id') or state.protected_index!=_idx(state.protected_fields,'rule_id') or state.severity_index!=_idx(state.severity_rules,'rule_id'): return False
    return state.registry_fingerprint==_registry_fp(state.policy,state.request,state.before_state,state.after_state,state.expected_effects,state.protected_fields,state.severity_rules)


def evaluate_prepared(state: PreparedDiffState, *, current_policy_fingerprint: str, current_request_fingerprint: str, current_registry_fingerprint: str, prepared_integrity_validated: bool) -> DiffResult:
    if not isinstance(state,PreparedDiffState): return _hold('INVALID_PREPARED_STATE')
    if not prepared_integrity_validated: return _hold('PREPARED_STATE_INTEGRITY_NOT_VALIDATED')
    if current_policy_fingerprint!=state.policy_fingerprint: return _hold('PREPARED_POLICY_STALE')
    if current_request_fingerprint!=state.request_fingerprint: return _hold('PREPARED_REQUEST_STALE')
    if current_registry_fingerprint!=state.registry_fingerprint: return _hold('PREPARED_REGISTRY_STALE')
    return _evaluate(state.request,state.policy,state.before_state,state.after_state,state.expected_effects,state.protected_fields,state.severity_rules,before_index=state.before_index,after_index=state.after_index,expected_index=state.expected_index,protected_index=state.protected_index,severity_index=state.severity_index)


def make_delta(base: PreparedDiffState,target: PreparedDiffState) -> DiffStateDelta:
    if base.binding!=target.binding or base.state_epoch!=target.state_epoch: raise ValueError('binding/state epoch mismatch')
    bb,tb=dict(base.before_fingerprints),dict(target.before_fingerprints); ba,ta=dict(base.after_fingerprints),dict(target.after_fingerprints); be,te=dict(base.expected_fingerprints),dict(target.expected_fingerprints); bp,tp=dict(base.protected_fingerprints),dict(target.protected_fingerprints); bs,ts=dict(base.severity_fingerprints),dict(target.severity_fingerprints)
    return DiffStateDelta(base.registry_fingerprint,target.registry_fingerprint,
        tuple(x for x in target.before_state if bb.get(x.path)!=tb[x.path]),tuple(sorted(set(bb)-set(tb))),
        tuple(x for x in target.after_state if ba.get(x.path)!=ta[x.path]),tuple(sorted(set(ba)-set(ta))),
        tuple(x for x in target.expected_effects if be.get(x.effect_id)!=te[x.effect_id]),tuple(sorted(set(be)-set(te))),
        tuple(x for x in target.protected_fields if bp.get(x.rule_id)!=tp[x.rule_id]),tuple(sorted(set(bp)-set(tp))),
        tuple(x for x in target.severity_rules if bs.get(x.rule_id)!=ts[x.rule_id]),tuple(sorted(set(bs)-set(ts))),
        target.policy,target.request,target.binding,target.state_epoch)


def apply_delta(base: PreparedDiffState,delta: DiffStateDelta) -> PreparedDiffState:
    if base.registry_fingerprint!=delta.base_fingerprint: raise ValueError('delta base fingerprint mismatch')
    if base.binding!=delta.binding or base.state_epoch!=delta.state_epoch: raise ValueError('delta binding/state epoch mismatch')
    b={x.path:x for x in base.before_state}; a={x.path:x for x in base.after_state}; e={x.effect_id:x for x in base.expected_effects}; p={x.rule_id:x for x in base.protected_fields}; s={x.rule_id:x for x in base.severity_rules}
    for k in delta.removed_before_paths: b.pop(k,None)
    for k in delta.removed_after_paths: a.pop(k,None)
    for k in delta.removed_expected_ids: e.pop(k,None)
    for k in delta.removed_protected_ids: p.pop(k,None)
    for k in delta.removed_severity_ids: s.pop(k,None)
    for x in delta.changed_before: b[x.path]=x
    for x in delta.changed_after: a[x.path]=x
    for x in delta.changed_expected: e[x.effect_id]=x
    for x in delta.changed_protected: p[x.rule_id]=x
    for x in delta.changed_severity: s[x.rule_id]=x
    out=prepare_state(delta.target_policy,delta.target_request,tuple(b.values()),tuple(a.values()),tuple(e.values()),tuple(p.values()),tuple(s.values()),binding=delta.binding)
    if out.registry_fingerprint!=delta.target_fingerprint: raise ValueError('delta target fingerprint mismatch')
    return out


def missing_only_sync_plan(target: PreparedDiffState, known_before: dict[str,str], known_after: dict[str,str], known_expected: dict[str,str], known_protected: dict[str,str], known_severity: dict[str,str]) -> DiffSyncPlan:
    mb=tuple(k for k,fp in target.before_fingerprints if known_before.get(k)!=fp); ma=tuple(k for k,fp in target.after_fingerprints if known_after.get(k)!=fp); me=tuple(k for k,fp in target.expected_fingerprints if known_expected.get(k)!=fp); mp=tuple(k for k,fp in target.protected_fingerprints if known_protected.get(k)!=fp); ms=tuple(k for k,fp in target.severity_fingerprints if known_severity.get(k)!=fp)
    bi={x.path:x for x in target.before_state}; ai={x.path:x for x in target.after_state}; ei={x.effect_id:x for x in target.expected_effects}; pi={x.rule_id:x for x in target.protected_fields}; si={x.rule_id:x for x in target.severity_rules}
    n=sum(len(_canon(bi[k])) for k in mb)+sum(len(_canon(ai[k])) for k in ma)+sum(len(_canon(ei[k])) for k in me)+sum(len(_canon(pi[k])) for k in mp)+sum(len(_canon(si[k])) for k in ms)
    return DiffSyncPlan(mb,ma,me,mp,ms,n,False)


def full_registry_bytes(state: PreparedDiffState) -> int:
    return len(_canon({'policy':state.policy,'request':state.request,'before':state.before_state,'after':state.after_state,'expected':state.expected_effects,'protected':state.protected_fields,'severity':state.severity_rules}))

def delta_bytes(delta: DiffStateDelta) -> int: return len(_canon(delta))
