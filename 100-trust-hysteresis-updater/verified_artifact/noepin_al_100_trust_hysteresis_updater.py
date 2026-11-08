"""NOEPIN AL 100 — Trust Hysteresis Updater — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Pure trust-state candidate evidence. This module applies asymmetric trust updates:
failures reduce trust faster than successes restore it, serious incidents impose
recovery requirements, inactivity decays elevated trust toward a neutral baseline,
and tier transitions use hysteresis thresholds to avoid oscillation. It never
promotes Trust Score or Trust Tier to Truth, Permission, Production Authority,
Action Execution, Safety Proof, or Action Success. Shadow/Canary state is never
Production Authority.

Canonical identity: NOEPIN-AL-100
DCSR level: DIRECT INTEGRATION / 直接統合.
Provenance note: exact registered Origin GUID was not freshly reverified in this
completion session and is intentionally not guessed or regenerated.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, IntEnum
from hashlib import sha256
import json, math

class Decision(str, Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class Severity(IntEnum):
    INFO=0; LOW=1; MEDIUM=2; HIGH=3; CRITICAL=4
class EventOutcome(str, Enum):
    SUCCESS='SUCCESS'; FAILURE='FAILURE'; CORRECTION='CORRECTION'; UNKNOWN='UNKNOWN'
class TrustTier(IntEnum):
    UNTRUSTED=0; RESTRICTED=1; LIMITED=2; STANDARD=3; HIGH=4
class RecoveryRequirement(str, Enum):
    NONE='NONE'; CONSECUTIVE_SUCCESS='CONSECUTIVE_SUCCESS'; REVALIDATION='REVALIDATION'; HUMAN_REVIEW='HUMAN_REVIEW'
class DeploymentLane(str, Enum):
    STABLE='STABLE'; CANARY='CANARY'; SHADOW='SHADOW'
class NextAction(str, Enum):
    TRUST_UPDATE_CANDIDATE='TRUST_UPDATE_CANDIDATE'; ISOLATION_CANDIDATE='ISOLATION_CANDIDATE'; RECOVERY_CANDIDATE='RECOVERY_CANDIDATE'; HOLD_UNRESOLVED='HOLD_UNRESOLVED'

@dataclass(frozen=True)
class TrustQuery:
    request_id:str; entity_id:str; current_trust:float; current_tier:TrustTier; current_success_streak:int
    serious_incident_active:bool; recovery_verified:bool; lane:DeploymentLane; last_event_time:float; reference_time:float
    observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class TrustEvent:
    event_id:str; outcome:EventOutcome; severity:Severity; event_time:float; evidence_strength:float; sequence_index:int
    model_version:str; policy_version:str; metric_version:str; source_fingerprint:str
    observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class TrustPolicy:
    failure_drop_low:float; failure_drop_medium:float; failure_drop_high:float; failure_drop_critical:float
    success_gain_base:float; success_streak_bonus:float; success_gain_cap:float
    critical_trust_cap:float; high_trust_cap:float; correction_gain_cap:float
    minimum_event_evidence:float; uncertain_event_change_cap:float
    recovery_successes_high:int; recovery_successes_critical:int
    inactivity_grace:float; inactivity_half_life:float; neutral_trust:float
    enter_limited:float; exit_limited:float; enter_standard:float; exit_standard:float; enter_high:float; exit_high:float
    binding:str; state_epoch:str; revoked:bool=False
@dataclass(frozen=True)
class TrustResult:
    decision:Decision; next_action:NextAction; reasons:tuple[str,...]
    updated_trust:float; trust_tier:TrustTier; recovery_requirement:RecoveryRequirement
    success_streak:int; serious_incident_active:bool; recovery_ready_candidate:bool; isolation_candidate:bool
    lane:DeploymentLane; next_gate_candidate:bool
    trust_applied:bool=False; trust_tier_applied:bool=False; recovery_executed:bool=False; isolation_executed:bool=False
    cache_promoted_to_truth:bool=False; cache_promoted_to_authority:bool=False; production_authority_granted:bool=False
    permission_granted:bool=False; action_executed:bool=False; plan_committed:bool=False; atomic_publish_executed:bool=False
    external_write_performed:bool=False; world_truth_proven:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedTrustState:
    query:TrustQuery; events:tuple[TrustEvent,...]; policy:TrustPolicy
    event_fingerprints:tuple[tuple[str,str],...]; context_fingerprint:str; dependency_fingerprint:str
    policy_fingerprint:str; registry_fingerprint:str; precomputed_result:TrustResult
    binding:str; state_epoch:str
@dataclass(frozen=True)
class TrustStateDelta:
    base_fingerprint:str; target_fingerprint:str; changed_events:tuple[TrustEvent,...]; removed_event_ids:tuple[str,...]
    target_query:TrustQuery|None; target_policy:TrustPolicy|None; binding:str; state_epoch:str
@dataclass(frozen=True)
class TrustSyncPlan:
    missing_or_changed_event_ids:tuple[str,...]; metadata_bytes_required:int; full_resend_required:bool

def _cv(x):
    if isinstance(x,Enum): return x.name if isinstance(x,IntEnum) else x.value
    if hasattr(x,'__dataclass_fields__'): return {k:_cv(getattr(x,k)) for k in x.__dataclass_fields__}
    if isinstance(x,tuple): return [_cv(v) for v in x]
    if isinstance(x,list): return [_cv(v) for v in x]
    if isinstance(x,dict): return {str(k):_cv(x[k]) for k in sorted(x)}
    return x
def _canon(x)->bytes: return json.dumps(_cv(x),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def _fp(x)->str: return sha256(_canon(x)).hexdigest()
def _clamp(x): return max(0.0,min(1.0,x))
def _drop(sev,p):
    return {Severity.INFO:0.0,Severity.LOW:p.failure_drop_low,Severity.MEDIUM:p.failure_drop_medium,Severity.HIGH:p.failure_drop_high,Severity.CRITICAL:p.failure_drop_critical}[sev]
def _required_successes(sev,p): return p.recovery_successes_critical if sev>=Severity.CRITICAL else p.recovery_successes_high

def _hold(reason,q,p,trust=None,tier=None,streak=None,incident=None,req=RecoveryRequirement.REVALIDATION,lane=None):
    return TrustResult(Decision.HOLD,NextAction.HOLD_UNRESOLVED,(reason,),q.current_trust if trust is None else trust,q.current_tier if tier is None else tier,req,q.current_success_streak if streak is None else streak,q.serious_incident_active if incident is None else incident,False,False,q.lane if lane is None else lane,False)

def _validate(q,events,p):
    if p.revoked: return 'POLICY_REVOKED'
    if not q.observed or not q.request_id or not q.entity_id: return 'QUERY_INVALID'
    if q.binding!=p.binding or q.state_epoch!=p.state_epoch: return 'QUERY_SCOPE_MISMATCH'
    if not math.isfinite(q.current_trust) or not 0<=q.current_trust<=1 or q.current_success_streak<0 or not math.isfinite(q.last_event_time) or not math.isfinite(q.reference_time) or q.last_event_time>q.reference_time: return 'QUERY_VALUE_INVALID'
    vals=(p.failure_drop_low,p.failure_drop_medium,p.failure_drop_high,p.failure_drop_critical,p.success_gain_base,p.success_streak_bonus,p.success_gain_cap,p.critical_trust_cap,p.high_trust_cap,p.correction_gain_cap,p.minimum_event_evidence,p.uncertain_event_change_cap,p.neutral_trust,p.enter_limited,p.exit_limited,p.enter_standard,p.exit_standard,p.enter_high,p.exit_high)
    if any(not math.isfinite(v) for v in vals): return 'POLICY_VALUE_INVALID'
    if any(not 0<=v<=1 for v in vals): return 'POLICY_RANGE_INVALID'
    if not (p.failure_drop_low<=p.failure_drop_medium<=p.failure_drop_high<=p.failure_drop_critical): return 'POLICY_FAILURE_NONMONOTONIC'
    if not (p.exit_limited<=p.enter_limited<=p.exit_standard<=p.enter_standard<=p.exit_high<=p.enter_high): return 'POLICY_HYSTERESIS_INVALID'
    if p.recovery_successes_high<1 or p.recovery_successes_critical<p.recovery_successes_high or p.inactivity_grace<0 or p.inactivity_half_life<=0: return 'POLICY_PARAMETER_INVALID'
    ids=[e.event_id for e in events]
    if len(ids)!=len(set(ids)): return 'DUPLICATE_EVENT_ID'
    last=-float('inf')
    for e in sorted(events,key=lambda x:(x.event_time,x.sequence_index,x.event_id)):
        if not e.observed or not e.event_id or not e.model_version or not e.policy_version or not e.metric_version or not e.source_fingerprint: return 'EVENT_INVALID'
        if e.binding!=p.binding or e.state_epoch!=p.state_epoch: return 'EVENT_SCOPE_MISMATCH'
        if not math.isfinite(e.event_time) or e.event_time>q.reference_time or e.event_time<last: return 'EVENT_TIME_INVALID'
        if not math.isfinite(e.evidence_strength) or not 0<=e.evidence_strength<=1 or e.sequence_index<0: return 'EVENT_VALUE_INVALID'
        last=e.event_time
    return None

def _decay_high_trust(trust,elapsed,p):
    if elapsed<=p.inactivity_grace or trust<=p.neutral_trust: return trust
    active=elapsed-p.inactivity_grace
    factor=0.5**(active/p.inactivity_half_life)
    return p.neutral_trust+(trust-p.neutral_trust)*factor

def _tier_from_score(score,current,p,incident):
    # Hysteresis: demotion and promotion use different thresholds.
    if incident:
        if score < p.exit_limited: return TrustTier.UNTRUSTED if score<0.20 else TrustTier.RESTRICTED
        return min(current,TrustTier.LIMITED)
    if current==TrustTier.HIGH:
        if score>=p.exit_high: return TrustTier.HIGH
        current=TrustTier.STANDARD
    if current==TrustTier.STANDARD:
        if score>=p.enter_high: return TrustTier.HIGH
        if score>=p.exit_standard: return TrustTier.STANDARD
        current=TrustTier.LIMITED
    if current==TrustTier.LIMITED:
        if score>=p.enter_standard: return TrustTier.STANDARD
        if score>=p.exit_limited: return TrustTier.LIMITED
        current=TrustTier.RESTRICTED
    if current==TrustTier.RESTRICTED:
        if score>=p.enter_limited: return TrustTier.LIMITED
        return TrustTier.RESTRICTED if score>=0.20 else TrustTier.UNTRUSTED
    if score>=p.enter_limited: return TrustTier.LIMITED
    return TrustTier.RESTRICTED if score>=0.20 else TrustTier.UNTRUSTED

def evaluate(q:TrustQuery,events:tuple[TrustEvent,...],p:TrustPolicy)->TrustResult:
    events=tuple(sorted(events,key=lambda x:(x.event_time,x.sequence_index,x.event_id)))
    err=_validate(q,events,p)
    if err: return _hold(err,q,p)
    trust=q.current_trust; tier=q.current_tier; streak=q.current_success_streak; incident=q.serious_incident_active
    req=RecoveryRequirement.REVALIDATION if incident else RecoveryRequirement.NONE
    reasons=[]; isolation=False; recovery_ready=False; last_time=q.last_event_time
    # Inactivity only decays elevated trust; it never repairs low trust or clears incidents.
    for e in events:
        # If there is a gap from the previous event, decay elevated trust toward neutral.
        if e.event_time>last_time:
            trust=_decay_high_trust(trust,e.event_time-last_time,p)
        strong=e.evidence_strength>=p.minimum_event_evidence
        if e.outcome==EventOutcome.FAILURE:
            streak=0
            change=_drop(e.severity,p)*e.evidence_strength
            if not strong: change=min(change,p.uncertain_event_change_cap)
            trust=_clamp(trust-change)
            if e.severity>=Severity.CRITICAL:
                trust=min(trust,p.critical_trust_cap); incident=True; isolation=True; req=RecoveryRequirement.HUMAN_REVIEW; reasons.append('CRITICAL_FAILURE_FAST_TRUST_DROP')
            elif e.severity>=Severity.HIGH:
                trust=min(trust,p.high_trust_cap); incident=True; isolation=True; req=RecoveryRequirement.REVALIDATION; reasons.append('HIGH_FAILURE_FAST_TRUST_DROP')
            else:
                reasons.append('FAILURE_TRUST_DECREASE')
        elif e.outcome==EventOutcome.SUCCESS:
            streak+=1
            gain=min(p.success_gain_cap,p.success_gain_base+p.success_streak_bonus*max(0,streak-1))*e.evidence_strength
            if not strong: gain=min(gain,p.uncertain_event_change_cap)
            trust=_clamp(trust+gain)
            if incident:
                req=RecoveryRequirement.CONSECUTIVE_SUCCESS
                needed=p.recovery_successes_critical if trust<=p.critical_trust_cap+1e-12 else p.recovery_successes_high
                recovery_ready=streak>=needed
                if recovery_ready and q.recovery_verified:
                    incident=False; req=RecoveryRequirement.NONE; reasons.append('RECOVERY_VERIFIED_AFTER_CONSECUTIVE_SUCCESS')
                elif recovery_ready:
                    reasons.append('RECOVERY_READY_REVALIDATION_REQUIRED')
                else:
                    reasons.append('POST_INCIDENT_SINGLE_OR_INSUFFICIENT_SUCCESS')
            else:
                reasons.append('SUCCESS_GRADUAL_TRUST_RECOVERY')
        elif e.outcome==EventOutcome.CORRECTION:
            # Correction can undo a small portion of a prior trust loss but cannot erase serious-incident requirements by itself.
            gain=min(p.correction_gain_cap,p.correction_gain_cap*e.evidence_strength)
            if not strong: gain=min(gain,p.uncertain_event_change_cap)
            trust=_clamp(trust+gain); streak=0
            reasons.append('CORRECTION_PARTIAL_TRUST_RESTORE')
            if incident: req=RecoveryRequirement.REVALIDATION
        else:
            # Evidence-insufficient/unknown event changes trust only minimally and causes HOLD.
            trust=_clamp(trust-p.uncertain_event_change_cap*(1.0-e.evidence_strength)); streak=0
            reasons.append('UNKNOWN_EVENT_CONSERVATIVE_SMALL_CHANGE')
        tier=_tier_from_score(trust,tier,p,incident)
        last_time=e.event_time
    # Decay from last event to reference time.
    if events and q.reference_time>last_time:
        trust=_decay_high_trust(trust,q.reference_time-last_time,p); tier=_tier_from_score(trust,tier,p,incident)
    if not events:
        trust=_decay_high_trust(trust,max(0.0,q.reference_time-q.last_event_time),p); tier=_tier_from_score(trust,tier,p,incident); reasons.append('NO_NEW_EVENT_INACTIVITY_DECAY_ONLY')
    if not reasons: reasons=['NO_MATERIAL_TRUST_CHANGE']
    unknown=any(e.outcome==EventOutcome.UNKNOWN for e in events)
    severe_fail=any(e.outcome==EventOutcome.FAILURE and e.severity>=Severity.HIGH for e in events)
    if incident or severe_fail or unknown:
        decision=Decision.HOLD; next_action=NextAction.ISOLATION_CANDIDATE if isolation else (NextAction.RECOVERY_CANDIDATE if recovery_ready else NextAction.HOLD_UNRESOLVED); next_gate=False
    else:
        decision=Decision.ALLOW; next_action=NextAction.TRUST_UPDATE_CANDIDATE; next_gate=True
    # Canary/Shadow never has Production Authority. STABLE still only emits candidate evidence.
    return TrustResult(decision,next_action,tuple(dict.fromkeys(reasons)),round(trust,12),tier,req,streak,incident,recovery_ready,isolation,q.lane,next_gate)

def default_policy():
    return TrustPolicy(.03,.10,.25,.55,.01,.005,.03,.25,.45,.05,.60,.01,3,5,7.0,30.0,.50,.45,.38,.68,.58,.86,.76,'THU-BIND','STATE-EPOCH-1')
def default_query():
    p=default_policy(); return TrustQuery('REQ-100','ENTITY-A',.72,TrustTier.STANDARD,2,False,False,DeploymentLane.STABLE,999.0,1000.0,True,p.binding,p.state_epoch)
def default_events():
    p=default_policy(); return (TrustEvent('EV-100',EventOutcome.SUCCESS,Severity.LOW,1000.0,1.0,1,'MODEL-V1','POLICY-V1','METRIC-V1','SF-EV-100',True,p.binding,p.state_epoch),)
def default_evaluation(): return evaluate(default_query(),default_events(),default_policy())

def _event_fingerprints(events): return tuple((f'EV:{e.event_id}',_fp(e)) for e in sorted(events,key=lambda x:x.event_id))
def _context_fp(q,p): return _fp((q.request_id,q.entity_id,q.current_trust,q.current_tier,q.current_success_streak,q.serious_incident_active,q.recovery_verified,q.lane,q.last_event_time,q.reference_time,q.binding,q.state_epoch))
def _dependency_fp(events): return _fp(_event_fingerprints(events))
def _policy_fp(p): return _fp(p)
def _registry_fp(q,events,p): return _fp((q,_event_fingerprints(events),p))
def prepare_state(q,events,p,*,binding:str,state_epoch:str):
    events=tuple(sorted(events,key=lambda x:(x.event_time,x.sequence_index,x.event_id))); fps=_event_fingerprints(events)
    return PreparedTrustState(q,events,p,fps,_context_fp(q,p),_dependency_fp(events),_policy_fp(p),_registry_fp(q,events,p),evaluate(q,events,p),binding,state_epoch)
def validate_prepared_integrity(st):
    if st.binding!=st.policy.binding or st.state_epoch!=st.policy.state_epoch: return False
    if st.event_fingerprints!=_event_fingerprints(st.events): return False
    if st.context_fingerprint!=_context_fp(st.query,st.policy): return False
    if st.dependency_fingerprint!=_dependency_fp(st.events): return False
    if st.policy_fingerprint!=_policy_fp(st.policy): return False
    if st.registry_fingerprint!=_registry_fp(st.query,st.events,st.policy): return False
    return st.precomputed_result==evaluate(st.query,st.events,st.policy)
def evaluate_prepared(st,*,current_context_fingerprint,current_dependency_fingerprint,current_policy_fingerprint,current_registry_fingerprint,prepared_integrity_validated):
    if not prepared_integrity_validated: return _hold('PREPARED_INTEGRITY_NOT_VALIDATED',st.query,st.policy)
    if current_context_fingerprint!=st.context_fingerprint: return _hold('PREPARED_CONTEXT_MISMATCH',st.query,st.policy)
    if current_dependency_fingerprint!=st.dependency_fingerprint: return _hold('PREPARED_DEPENDENCY_MISMATCH',st.query,st.policy)
    if current_policy_fingerprint!=st.policy_fingerprint: return _hold('PREPARED_POLICY_MISMATCH',st.query,st.policy)
    if current_registry_fingerprint!=st.registry_fingerprint: return _hold('PREPARED_REGISTRY_MISMATCH',st.query,st.policy)
    return st.precomputed_result

def make_delta(base,target):
    bb={x.event_id:x for x in base.events}; tb={x.event_id:x for x in target.events}
    changed=tuple(tb[k] for k in sorted(tb) if k not in bb or _fp(tb[k])!=_fp(bb[k]))
    return TrustStateDelta(base.registry_fingerprint,target.registry_fingerprint,changed,tuple(sorted(set(bb)-set(tb))),target.query if target.query!=base.query else None,target.policy if target.policy!=base.policy else None,target.binding,target.state_epoch)
def apply_delta(base,d):
    if base.registry_fingerprint!=d.base_fingerprint: raise ValueError('BASE_FINGERPRINT_MISMATCH')
    bm={x.event_id:x for x in base.events}
    for k in d.removed_event_ids: bm.pop(k,None)
    for x in d.changed_events: bm[x.event_id]=x
    out=prepare_state(d.target_query or base.query,tuple(bm.values()),d.target_policy or base.policy,binding=d.binding,state_epoch=d.state_epoch)
    if out.registry_fingerprint!=d.target_fingerprint: raise ValueError('TARGET_FINGERPRINT_MISMATCH')
    return out
def missing_only_sync_plan(target,known_event_fingerprints):
    missing=tuple(k for k,v in target.event_fingerprints if known_event_fingerprints.get(k)!=v)
    meta=len(_canon({'context':target.context_fingerprint,'dependency':target.dependency_fingerprint,'policy':target.policy_fingerprint,'registry':target.registry_fingerprint,'missing':missing}))
    return TrustSyncPlan(missing,meta,False)
def full_registry_bytes(st): return len(_canon((st.query,st.events,st.policy)))
def delta_bytes(d): return len(_canon(d))
