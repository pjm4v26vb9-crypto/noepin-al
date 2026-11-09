"""NOEPIN AL 117 — Safe-Mode State Machine — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Deterministic fail-safe finite-state control candidate generator. It maps typed risk events,
trust, connectivity, policy, and operator signals onto an explicit candidate safety mode and a
capability matrix. Unknown/conflicting transition evidence is resolved toward the more restrictive
state. Recovery is deliberately asymmetric: it requires explicit recovery request plus stricter
clean-state evidence and remains a HUMAN_APPROVAL recovery candidate rather than an executed
permission/permit restoration.

Canonical identity: NOEPIN-AL-117
DCSR level: AUXILIARY INTEGRATION / 補助統合.
Provenance note: exact registered Origin GUID was not freshly reverified and is intentionally not
guessed. Pre-existing Notion V1 attachment byte identity was not freshly reverified.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str, Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class SafetyMode(str, Enum):
    NORMAL='NORMAL'; RESTRICTED='RESTRICTED'; READ_ONLY='READ_ONLY'; OFFLINE='OFFLINE'; EMERGENCY_STOP='EMERGENCY_STOP'
class RiskSeverity(str, Enum):
    INFO='INFO'; LOW='LOW'; MEDIUM='MEDIUM'; HIGH='HIGH'; CRITICAL='CRITICAL'; UNKNOWN='UNKNOWN'
class Connectivity(str, Enum):
    TRUSTED='TRUSTED'; DEGRADED='DEGRADED'; UNTRUSTED='UNTRUSTED'; OFFLINE='OFFLINE'; UNKNOWN='UNKNOWN'
class OperatorSignal(str, Enum):
    NONE='NONE'; RESTRICT='RESTRICT'; READ_ONLY='READ_ONLY'; OFFLINE='OFFLINE'; EMERGENCY_STOP='EMERGENCY_STOP'; RECOVERY_REQUEST='RECOVERY_REQUEST'; UNKNOWN='UNKNOWN'
class NextAction(str, Enum):
    MODE_MAINTAIN_CANDIDATE='MODE_MAINTAIN_CANDIDATE'
    MODE_DEGRADATION_CANDIDATE='MODE_DEGRADATION_CANDIDATE'
    EMERGENCY_STOP_CANDIDATE='EMERGENCY_STOP_CANDIDATE'
    RECOVERY_MODE_CANDIDATE='RECOVERY_MODE_CANDIDATE'
    HOLD_SAFE_MODE_CANDIDATE='HOLD_SAFE_MODE_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; CRITICAL_INCIDENT='CRITICAL_INCIDENT'; CONNECTIVITY_RISK='CONNECTIVITY_RISK'; TRUST_DEGRADED='TRUST_DEGRADED'; UNKNOWN_INPUT='UNKNOWN_INPUT'; CONFLICTING_SIGNALS='CONFLICTING_SIGNALS'; RECOVERY_REVIEW='RECOVERY_REVIEW'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'

@dataclass(frozen=True)
class RiskEvent:
    event_id: str
    severity: RiskSeverity
    active: bool
    category: str
    evidence_version: str
    evidence_fingerprint: str
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class SafeModePolicy:
    trust_restricted_threshold: float
    trust_read_only_threshold: float
    recovery_trust_threshold: float
    recovery_stable_windows: int
    medium_event_restricted_count: int
    unknown_event_mode: SafetyMode
    unknown_connectivity_mode: SafetyMode

@dataclass(frozen=True)
class SafeModeRequest:
    request_id: str
    current_mode: SafetyMode
    risk_events: tuple[RiskEvent,...]
    trust: float|None
    connectivity: Connectivity
    policy: SafeModePolicy
    operator_signals: tuple[OperatorSignal,...]
    stable_windows: int
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class SafeModeResult:
    decision: Decision
    next_action: NextAction
    escalation: Escalation
    reasons: tuple[str,...]
    current_mode: SafetyMode
    safety_mode_candidate: SafetyMode
    allowed_capabilities: tuple[str,...]
    transition_reason: str
    recovery_candidate: bool
    permit_reissue_candidate: bool
    next_gate_candidate: bool
    capability_matrix_promoted_to_permission: bool=False
    mode_change_executed: bool=False
    permit_issued: bool=False
    permission_granted: bool=False
    approval_executed: bool=False
    authority_granted: bool=False
    stop_executed: bool=False
    action_executed: bool=False
    plan_committed: bool=False
    publish_executed: bool=False
    external_write_performed: bool=False
    world_truth_proven: bool=False
    domain_authority_promoted: bool=False
    safety_proven: bool=False
    action_success: bool=False

@dataclass(frozen=True)
class PreparedSafeModeState:
    request: SafeModeRequest
    result: SafeModeResult
    context_fingerprint: str
    event_fingerprint: str
    policy_fingerprint: str
    registry_fingerprint: str
    transition_fingerprint: str
    integrity_fingerprint: str
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class SafeModeDelta:
    changed_events: tuple[RiskEvent,...]
    removed_event_ids: tuple[str,...]
    from_registry_fingerprint: str
    to_registry_fingerprint: str

@dataclass(frozen=True)
class MissingOnlyPlan:
    missing_or_changed_record_ids: tuple[str,...]
    metadata_bytes_required: int
    full_resend_required: bool

_MODE_RANK={SafetyMode.NORMAL:0,SafetyMode.RESTRICTED:1,SafetyMode.READ_ONLY:2,SafetyMode.OFFLINE:3,SafetyMode.EMERGENCY_STOP:4}
_CAPABILITIES={
    SafetyMode.NORMAL:('STATE_READ','LOCAL_ANALYSIS','LOCAL_WRITE_CANDIDATE','NETWORK_READ_CANDIDATE','NETWORK_WRITE_CANDIDATE','TOOL_CALL_CANDIDATE','EXTERNAL_SEND_CANDIDATE'),
    SafetyMode.RESTRICTED:('STATE_READ','LOCAL_ANALYSIS','LOCAL_WRITE_CANDIDATE','NETWORK_READ_CANDIDATE'),
    SafetyMode.READ_ONLY:('STATE_READ','LOCAL_ANALYSIS','NETWORK_READ_CANDIDATE'),
    SafetyMode.OFFLINE:('STATE_READ','LOCAL_ANALYSIS'),
    SafetyMode.EMERGENCY_STOP:('STATE_READ','AUDIT_READ'),
}
_OPERATOR_MODE={OperatorSignal.RESTRICT:SafetyMode.RESTRICTED,OperatorSignal.READ_ONLY:SafetyMode.READ_ONLY,OperatorSignal.OFFLINE:SafetyMode.OFFLINE,OperatorSignal.EMERGENCY_STOP:SafetyMode.EMERGENCY_STOP}

def _obj(v):
    if isinstance(v, Enum): return v.value
    if is_dataclass(v): return {f.name:_obj(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v, dict): return {str(k):_obj(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(tuple,list)): return [_obj(x) for x in v]
    return v

def _canon(v)->bytes: return json.dumps(_obj(v),ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')
def _fp(v)->str: return sha256(_canon(v)).hexdigest()
def _finite(x): return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(float(x))
def _max_mode(*modes:SafetyMode)->SafetyMode: return max(modes,key=lambda m:_MODE_RANK[m])
def _one_step_less_restrictive(mode:SafetyMode)->SafetyMode:
    if mode==SafetyMode.NORMAL: return SafetyMode.NORMAL
    rank=_MODE_RANK[mode]-1
    for m,r in _MODE_RANK.items():
        if r==rank: return m
    return mode

def default_policy():
    return SafeModePolicy(0.70,0.40,0.90,3,2,SafetyMode.READ_ONLY,SafetyMode.READ_ONLY)

def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    ev=(RiskEvent('HEALTH',RiskSeverity.LOW,True,'SYSTEM','V1','FP-HEALTH',b,e),)
    return SafeModeRequest('DEFAULT-117',SafetyMode.NORMAL,ev,0.95,Connectivity.TRUSTED,default_policy(),(OperatorSignal.NONE,),5,b,e)

def _result(req,decision,next_action,escalation,reasons,mode,transition,recovery=False,permit=False,next_gate=False):
    return SafeModeResult(decision,next_action,escalation,tuple(reasons),req.current_mode,mode,_CAPABILITIES[mode],transition,recovery,permit,next_gate)

def _hold_invalid(req,reason):
    mode=_max_mode(req.current_mode,SafetyMode.READ_ONLY)
    return _result(req,Decision.HOLD,NextAction.HOLD_SAFE_MODE_CANDIDATE,Escalation.INVALID_CONFIGURATION,(reason,'FAIL_SAFE_RESTRICTIVE_STATE'),mode,reason,False,False,False)

def evaluate(req:SafeModeRequest)->SafeModeResult:
    p=req.policy
    if not req.request_id or not req.binding or not req.state_epoch: return _hold_invalid(req,'INVALID_REQUEST_IDENTITY')
    vals=(p.trust_restricted_threshold,p.trust_read_only_threshold,p.recovery_trust_threshold)
    if not all(_finite(x) for x in vals): return _hold_invalid(req,'POLICY_NONFINITE')
    if not (0<=p.trust_read_only_threshold<=p.trust_restricted_threshold<=1 and 0<=p.recovery_trust_threshold<=1): return _hold_invalid(req,'POLICY_TRUST_RANGE_INVALID')
    if not isinstance(p.recovery_stable_windows,int) or p.recovery_stable_windows<1 or not isinstance(p.medium_event_restricted_count,int) or p.medium_event_restricted_count<1: return _hold_invalid(req,'POLICY_COUNT_INVALID')
    if _MODE_RANK[p.unknown_event_mode]<_MODE_RANK[SafetyMode.RESTRICTED] or _MODE_RANK[p.unknown_connectivity_mode]<_MODE_RANK[SafetyMode.RESTRICTED]: return _hold_invalid(req,'POLICY_UNKNOWN_MODE_TOO_PERMISSIVE')
    if req.trust is not None and (not _finite(req.trust) or not 0<=float(req.trust)<=1): return _hold_invalid(req,'TRUST_INVALID')
    if not isinstance(req.stable_windows,int) or req.stable_windows<0: return _hold_invalid(req,'STABLE_WINDOWS_INVALID')
    ordered=tuple(sorted(req.risk_events,key=lambda x:x.event_id))
    if len({x.event_id for x in ordered})!=len(ordered): return _hold_invalid(req,'DUPLICATE_EVENT_ID')
    for ev in ordered:
        if not ev.event_id or not ev.category or ev.binding!=req.binding or ev.state_epoch!=req.state_epoch: return _hold_invalid(req,'EVENT_BINDING_OR_IDENTITY_INVALID')
    signals=tuple(sorted(set(req.operator_signals),key=lambda s:s.value))
    if not signals: signals=(OperatorSignal.NONE,)
    unknown_input=False; conflict=False; target=SafetyMode.NORMAL; reasons=[]; esc=Escalation.NONE
    active=[ev for ev in ordered if ev.active]
    if any(ev.severity==RiskSeverity.CRITICAL for ev in active):
        target=SafetyMode.EMERGENCY_STOP; reasons.append('CRITICAL_INCIDENT'); esc=Escalation.CRITICAL_INCIDENT
    elif any(ev.severity==RiskSeverity.UNKNOWN for ev in active):
        target=_max_mode(target,p.unknown_event_mode); reasons.append('UNKNOWN_RISK_EVENT_FAIL_SAFE'); unknown_input=True; esc=Escalation.UNKNOWN_INPUT
    elif any(ev.severity==RiskSeverity.HIGH for ev in active):
        target=_max_mode(target,SafetyMode.RESTRICTED); reasons.append('HIGH_RISK_RESTRICT'); esc=Escalation.TRUST_DEGRADED
    elif sum(1 for ev in active if ev.severity==RiskSeverity.MEDIUM)>=p.medium_event_restricted_count:
        target=_max_mode(target,SafetyMode.RESTRICTED); reasons.append('MULTIPLE_MEDIUM_RISK_RESTRICT'); esc=Escalation.TRUST_DEGRADED
    if req.connectivity==Connectivity.OFFLINE:
        target=_max_mode(target,SafetyMode.OFFLINE); reasons.append('CONNECTIVITY_OFFLINE'); esc=Escalation.CONNECTIVITY_RISK if esc==Escalation.NONE else esc
    elif req.connectivity in (Connectivity.UNTRUSTED,Connectivity.UNKNOWN):
        target=_max_mode(target,p.unknown_connectivity_mode if req.connectivity==Connectivity.UNKNOWN else SafetyMode.READ_ONLY); reasons.append('CONNECTIVITY_UNTRUSTED_OR_UNKNOWN'); unknown_input|=req.connectivity==Connectivity.UNKNOWN; esc=Escalation.UNKNOWN_INPUT if req.connectivity==Connectivity.UNKNOWN else (Escalation.CONNECTIVITY_RISK if esc==Escalation.NONE else esc)
    elif req.connectivity==Connectivity.DEGRADED:
        target=_max_mode(target,SafetyMode.RESTRICTED); reasons.append('CONNECTIVITY_DEGRADED'); esc=Escalation.CONNECTIVITY_RISK if esc==Escalation.NONE else esc
    if req.trust is None:
        target=_max_mode(target,SafetyMode.READ_ONLY); reasons.append('TRUST_UNKNOWN_FAIL_SAFE'); unknown_input=True; esc=Escalation.UNKNOWN_INPUT
    else:
        trust=float(req.trust)
        if trust<p.trust_read_only_threshold:
            target=_max_mode(target,SafetyMode.READ_ONLY); reasons.append('TRUST_BELOW_READ_ONLY_THRESHOLD'); esc=Escalation.TRUST_DEGRADED if esc==Escalation.NONE else esc
        elif trust<p.trust_restricted_threshold:
            target=_max_mode(target,SafetyMode.RESTRICTED); reasons.append('TRUST_BELOW_RESTRICTED_THRESHOLD'); esc=Escalation.TRUST_DEGRADED if esc==Escalation.NONE else esc
    restrictive_signals=[s for s in signals if s in _OPERATOR_MODE]
    recovery_requested=OperatorSignal.RECOVERY_REQUEST in signals
    if OperatorSignal.UNKNOWN in signals:
        target=_max_mode(target,SafetyMode.READ_ONLY); reasons.append('OPERATOR_SIGNAL_UNKNOWN_FAIL_SAFE'); unknown_input=True; esc=Escalation.UNKNOWN_INPUT
    if restrictive_signals:
        forced=_max_mode(*(_OPERATOR_MODE[s] for s in restrictive_signals)); target=_max_mode(target,forced); reasons.append('OPERATOR_RESTRICTION_SIGNAL')
    if recovery_requested and restrictive_signals:
        conflict=True; reasons.append('RECOVERY_CONFLICTS_WITH_RESTRICTION_SIGNAL'); esc=Escalation.CONFLICTING_SIGNALS
    # Never automatically recover. If evidence target is less restrictive than current state,
    # current state remains until explicit recovery request and strict recovery evidence.
    if _MODE_RANK[target] < _MODE_RANK[req.current_mode]:
        if not recovery_requested:
            reasons.append('NO_AUTOMATIC_RECOVERY'); target=req.current_mode
        else:
            recovery_clean=(not conflict and not unknown_input and req.connectivity==Connectivity.TRUSTED and req.trust is not None and float(req.trust)>=p.recovery_trust_threshold and req.stable_windows>=p.recovery_stable_windows and not any(ev.active and ev.severity in (RiskSeverity.HIGH,RiskSeverity.CRITICAL,RiskSeverity.UNKNOWN) for ev in ordered))
            if recovery_clean:
                candidate=_one_step_less_restrictive(req.current_mode)
                return _result(req,Decision.HUMAN_APPROVAL,NextAction.RECOVERY_MODE_CANDIDATE,Escalation.RECOVERY_REVIEW,tuple(reasons)+('STRICT_RECOVERY_EVIDENCE_PASS','RECOVERY_REQUIRES_SEPARATE_APPROVAL'),candidate,'RECOVERY_CANDIDATE_ONLY',True,True,False)
            reasons.append('RECOVERY_EVIDENCE_INSUFFICIENT'); target=req.current_mode; esc=Escalation.RECOVERY_REVIEW
    if _MODE_RANK[target] > _MODE_RANK[req.current_mode]:
        if target==SafetyMode.EMERGENCY_STOP:
            return _result(req,Decision.DENY,NextAction.EMERGENCY_STOP_CANDIDATE,esc or Escalation.CRITICAL_INCIDENT,tuple(reasons)+('MODE_CHANGE_CANDIDATE_ONLY',),target,'DEGRADE_TO_EMERGENCY_CANDIDATE',False,True,False)
        return _result(req,Decision.HOLD,NextAction.MODE_DEGRADATION_CANDIDATE,esc,tuple(reasons)+('MODE_CHANGE_CANDIDATE_ONLY',),target,'DEGRADE_TO_MORE_RESTRICTIVE_MODE',False,True,False)
    if recovery_requested and _MODE_RANK[target]>=_MODE_RANK[req.current_mode] and req.current_mode!=SafetyMode.NORMAL:
        return _result(req,Decision.HOLD,NextAction.HOLD_SAFE_MODE_CANDIDATE,Escalation.RECOVERY_REVIEW,tuple(reasons)+('RECOVERY_NOT_AUTHORIZED',),target,'RECOVERY_HOLD',False,False,False)
    if unknown_input or conflict:
        return _result(req,Decision.HOLD,NextAction.HOLD_SAFE_MODE_CANDIDATE,Escalation.CONFLICTING_SIGNALS if conflict else Escalation.UNKNOWN_INPUT,tuple(reasons)+('FAIL_SAFE_MORE_RESTRICTIVE_OR_CURRENT',),target,'FAIL_SAFE_HOLD',False,False,False)
    return _result(req,Decision.ALLOW,NextAction.MODE_MAINTAIN_CANDIDATE,Escalation.NONE,tuple(reasons)+('CURRENT_MODE_MAINTAIN_CANDIDATE','CAPABILITIES_ARE_CANDIDATES_ONLY'),target,'MAINTAIN_MODE_CANDIDATE',False,False,True)

def default_evaluation(): return evaluate(default_request())

def prepare_state(req:SafeModeRequest,*,binding:str,state_epoch:str)->PreparedSafeModeState:
    if binding!=req.binding or state_epoch!=req.state_epoch: raise ValueError('binding/state_epoch mismatch')
    result=evaluate(req); ordered=tuple(sorted(req.risk_events,key=lambda x:x.event_id)); sig=tuple(sorted(req.operator_signals,key=lambda s:s.value))
    context=_fp((req.request_id,req.current_mode,req.trust,req.connectivity,sig,req.stable_windows,binding,state_epoch))
    ef=_fp(ordered); pf=_fp(req.policy); rf=_fp(tuple((x.event_id,x.evidence_version,x.evidence_fingerprint,x.binding,x.state_epoch) for x in ordered)); tf=_fp(result)
    integ=_fp((context,ef,pf,rf,tf,binding,state_epoch))
    return PreparedSafeModeState(req,result,context,ef,pf,rf,tf,integ,binding,state_epoch)

def validate_prepared_integrity(st:PreparedSafeModeState)->bool:
    return st.integrity_fingerprint==_fp((st.context_fingerprint,st.event_fingerprint,st.policy_fingerprint,st.registry_fingerprint,st.transition_fingerprint,st.binding,st.state_epoch))

def evaluate_prepared(st:PreparedSafeModeState,*,integrity_validated:bool,current_context_fingerprint:str,current_event_fingerprint:str,current_policy_fingerprint:str,current_registry_fingerprint:str,current_transition_fingerprint:str)->SafeModeResult:
    if not integrity_validated or not validate_prepared_integrity(st): return _hold_invalid(st.request,'PREPARED_INTEGRITY_NOT_VALIDATED')
    current=(current_context_fingerprint,current_event_fingerprint,current_policy_fingerprint,current_registry_fingerprint,current_transition_fingerprint)
    saved=(st.context_fingerprint,st.event_fingerprint,st.policy_fingerprint,st.registry_fingerprint,st.transition_fingerprint)
    if current!=saved: return _hold_invalid(st.request,'PREPARED_FINGERPRINT_MISMATCH')
    return st.result

def make_delta(old:PreparedSafeModeState,new:PreparedSafeModeState)->SafeModeDelta:
    om={e.event_id:e for e in old.request.risk_events}; nm={e.event_id:e for e in new.request.risk_events}
    changed=tuple(nm[k] for k in sorted(nm) if k not in om or _fp(nm[k])!=_fp(om[k])); removed=tuple(k for k in sorted(om) if k not in nm)
    return SafeModeDelta(changed,removed,old.registry_fingerprint,new.registry_fingerprint)

def plan_missing_only(old:PreparedSafeModeState,new:PreparedSafeModeState)->MissingOnlyPlan:
    d=make_delta(old,new); ids=tuple([f'EVENT:{e.event_id}' for e in d.changed_events]+[f'REMOVED:{x}' for x in d.removed_event_ids]); meta=len(_canon({'from':d.from_registry_fingerprint,'to':d.to_registry_fingerprint,'ids':ids})); return MissingOnlyPlan(ids,meta,False)
