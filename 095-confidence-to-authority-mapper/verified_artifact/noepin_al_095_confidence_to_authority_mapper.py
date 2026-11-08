"""NOEPIN AL 095 — Confidence-to-Authority Mapper — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Pure control-candidate mapping. Adjusted confidence is combined with Action Risk,
Capability constraints and Policy caps to derive an Authority Tier Candidate,
Required Approval Candidate, and Capability Limits. This module never grants
permission, mutates authority, executes actions, approves actions, commits,
publishes, writes externally, proves Truth/Safety, or asserts Action Success.

Canonical identity: NOEPIN-AL-095
DCSR level: AUXILIARY INTEGRATION / 補助統合.
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
class RiskLevel(IntEnum):
    LOW=1; MEDIUM=2; HIGH=3; CRITICAL=4
class AuthorityTier(IntEnum):
    NONE=0; READ_ONLY=1; ASSISTED=2; LIMITED_WRITE=3; AUTONOMOUS=4
class ApprovalLevel(IntEnum):
    NONE=0; OPERATOR=1; HUMAN=2; DUAL_HUMAN=3

@dataclass(frozen=True)
class AuthorityRequest:
    request_id:str; adjusted_confidence:float; action_risk:RiskLevel
    task_class:str; observed:bool; confidence_calibrated:bool
    calibration_fingerprint:str; policy_version:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class CapabilityLevel:
    capability_id:str; minimum_tier:AuthorityTier; maximum_risk:RiskLevel
    side_effecting:bool; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class AuthorityPolicy:
    readonly_threshold:float; assisted_threshold:float; limited_write_threshold:float; autonomous_threshold:float
    max_low:AuthorityTier; max_medium:AuthorityTier; max_high:AuthorityTier; max_critical:AuthorityTier
    global_max:AuthorityTier; high_risk_approval:ApprovalLevel; critical_risk_approval:ApprovalLevel
    allow_uncalibrated_low_risk:bool; binding:str; state_epoch:str; revoked:bool=False
@dataclass(frozen=True)
class AuthorityMappingResult:
    decision:Decision; reasons:tuple[str,...]; adjusted_confidence:float; action_risk:RiskLevel
    confidence_tier:AuthorityTier; risk_cap:AuthorityTier; policy_cap:AuthorityTier
    authority_tier_candidate:AuthorityTier; required_approval_candidate:ApprovalLevel
    allowed_capability_candidates:tuple[str,...]; blocked_capabilities:tuple[str,...]
    limits:tuple[str,...]; next_gate_candidate:bool; reevaluation_candidate:bool
    authority_granted:bool=False; permission_granted:bool=False; approval_executed:bool=False
    capability_mutated:bool=False; action_executed:bool=False; plan_committed:bool=False
    atomic_publish_executed:bool=False; external_write_performed:bool=False
    world_truth_proven:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedAuthorityState:
    request:AuthorityRequest; capabilities:tuple[CapabilityLevel,...]; policy:AuthorityPolicy
    record_fingerprints:tuple[tuple[str,str],...]; context_fingerprint:str
    dependency_fingerprint:str; constraint_fingerprint:str; registry_fingerprint:str
    precomputed_result:AuthorityMappingResult; binding:str; state_epoch:str
@dataclass(frozen=True)
class AuthorityStateDelta:
    base_fingerprint:str; target_fingerprint:str; changed_capabilities:tuple[CapabilityLevel,...]
    removed_capability_ids:tuple[str,...]; target_request:AuthorityRequest|None
    target_policy:AuthorityPolicy|None; binding:str; state_epoch:str
@dataclass(frozen=True)
class AuthoritySyncPlan:
    missing_or_changed_record_ids:tuple[str,...]; metadata_bytes_required:int; full_resend_required:bool

def _cv(x):
    if isinstance(x,Enum): return x.name if isinstance(x,IntEnum) else x.value
    if hasattr(x,'__dataclass_fields__'): return {k:_cv(getattr(x,k)) for k in x.__dataclass_fields__}
    if isinstance(x,tuple): return [_cv(v) for v in x]
    if isinstance(x,list): return [_cv(v) for v in x]
    if isinstance(x,dict): return {str(k):_cv(x[k]) for k in sorted(x)}
    return x
def _canon(x)->bytes: return json.dumps(_cv(x),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def _fp(x)->str: return sha256(_canon(x)).hexdigest()
def _hold(reason,req,*,tier=AuthorityTier.NONE,approval=ApprovalLevel.NONE,allowed=(),blocked=(),limits=()):
    return AuthorityMappingResult(Decision.HOLD,(reason,),req.adjusted_confidence,req.action_risk,tier,AuthorityTier.NONE,AuthorityTier.NONE,tier,approval,tuple(allowed),tuple(blocked),tuple(limits),False,True)

def _validate(req,caps,policy):
    if policy.revoked: return 'POLICY_REVOKED'
    if not req.observed: return 'REQUEST_UNOBSERVED'
    if not req.request_id or not req.task_class or not req.policy_version: return 'REQUEST_IDENTITY_INVALID'
    if req.binding!=policy.binding or req.state_epoch!=policy.state_epoch: return 'REQUEST_SCOPE_MISMATCH'
    if not math.isfinite(req.adjusted_confidence) or not 0<=req.adjusted_confidence<=1: return 'CONFIDENCE_INVALID'
    if not req.calibration_fingerprint: return 'CALIBRATION_FINGERPRINT_MISSING'
    ts=(policy.readonly_threshold,policy.assisted_threshold,policy.limited_write_threshold,policy.autonomous_threshold)
    if any((not math.isfinite(v) or not 0<=v<=1) for v in ts): return 'POLICY_THRESHOLD_INVALID'
    if not (ts[0] <= ts[1] <= ts[2] <= ts[3]): return 'POLICY_THRESHOLD_ORDER_INVALID'
    ids=[c.capability_id for c in caps]
    if len(ids)!=len(set(ids)): return 'DUPLICATE_CAPABILITY_ID'
    for c in caps:
        if not c.capability_id or not c.observed: return 'CAPABILITY_INVALID'
        if c.binding!=policy.binding or c.state_epoch!=policy.state_epoch: return 'CAPABILITY_SCOPE_MISMATCH'
    return None

def _confidence_tier(c,policy):
    if c < policy.readonly_threshold: return AuthorityTier.NONE
    if c < policy.assisted_threshold: return AuthorityTier.READ_ONLY
    if c < policy.limited_write_threshold: return AuthorityTier.ASSISTED
    if c < policy.autonomous_threshold: return AuthorityTier.LIMITED_WRITE
    return AuthorityTier.AUTONOMOUS

def _risk_cap(risk,policy):
    return {RiskLevel.LOW:policy.max_low,RiskLevel.MEDIUM:policy.max_medium,RiskLevel.HIGH:policy.max_high,RiskLevel.CRITICAL:policy.max_critical}[risk]

def evaluate(req:AuthorityRequest,capabilities:tuple[CapabilityLevel,...],policy:AuthorityPolicy)->AuthorityMappingResult:
    capabilities=tuple(sorted(capabilities,key=lambda c:c.capability_id))
    err=_validate(req,capabilities,policy)
    if err: return _hold(err,req,blocked=tuple(c.capability_id for c in capabilities))
    if not req.confidence_calibrated and not (req.action_risk==RiskLevel.LOW and policy.allow_uncalibrated_low_risk):
        return _hold('UNCALIBRATED_CONFIDENCE',req,blocked=tuple(c.capability_id for c in capabilities),limits=('CALIBRATION_REQUIRED',))
    ct=_confidence_tier(req.adjusted_confidence,policy)
    rc=_risk_cap(req.action_risk,policy)
    pc=policy.global_max
    candidate=AuthorityTier(min(int(ct),int(rc),int(pc)))
    allowed=tuple(c.capability_id for c in capabilities if c.minimum_tier<=candidate and req.action_risk<=c.maximum_risk)
    blocked=tuple(c.capability_id for c in capabilities if c.capability_id not in allowed)
    limits=[]; reasons=[]
    if candidate < ct: reasons.append('AUTHORITY_CAPPED_BY_RISK_OR_POLICY')
    if blocked: limits.append('CAPABILITY_FILTER_APPLIED')
    if req.adjusted_confidence < policy.readonly_threshold:
        return AuthorityMappingResult(Decision.HOLD,('CONFIDENCE_TOO_LOW',),req.adjusted_confidence,req.action_risk,ct,rc,pc,AuthorityTier.NONE,ApprovalLevel.NONE,(),tuple(c.capability_id for c in capabilities),('NO_AUTHORITY_CANDIDATE',),False,True)
    if ct==AuthorityTier.READ_ONLY:
        return AuthorityMappingResult(Decision.HOLD,('LOW_CONFIDENCE_READ_ONLY_HOLD',),req.adjusted_confidence,req.action_risk,ct,rc,pc,candidate,ApprovalLevel.NONE,allowed,blocked,tuple(limits+['READ_ONLY_LIMIT']),False,True)
    approval=ApprovalLevel.NONE
    if req.action_risk==RiskLevel.HIGH: approval=policy.high_risk_approval
    elif req.action_risk==RiskLevel.CRITICAL: approval=policy.critical_risk_approval
    if req.action_risk==RiskLevel.CRITICAL:
        reasons.append('CRITICAL_RISK_HUMAN_APPROVAL_REQUIRED')
        return AuthorityMappingResult(Decision.HUMAN_APPROVAL,tuple(reasons),req.adjusted_confidence,req.action_risk,ct,rc,pc,candidate,approval,allowed,blocked,tuple(limits+['CRITICAL_RISK_CAP']),False,True)
    if approval!=ApprovalLevel.NONE:
        reasons.append('RISK_APPROVAL_REQUIRED')
        return AuthorityMappingResult(Decision.HUMAN_APPROVAL,tuple(reasons),req.adjusted_confidence,req.action_risk,ct,rc,pc,candidate,approval,allowed,blocked,tuple(limits),False,True)
    if not reasons: reasons.append('AUTHORITY_CANDIDATE_WITHIN_LIMITS')
    return AuthorityMappingResult(Decision.ALLOW,tuple(reasons),req.adjusted_confidence,req.action_risk,ct,rc,pc,candidate,approval,allowed,blocked,tuple(limits),True,False)

def default_policy():
    return AuthorityPolicy(.35,.55,.70,.88,AuthorityTier.AUTONOMOUS,AuthorityTier.LIMITED_WRITE,AuthorityTier.ASSISTED,AuthorityTier.READ_ONLY,AuthorityTier.AUTONOMOUS,ApprovalLevel.HUMAN,ApprovalLevel.DUAL_HUMAN,False,'CAM-BIND','STATE-EPOCH-1')
def default_request():
    return AuthorityRequest('REQ-95',.92,RiskLevel.LOW,'LOW_RISK_AUTOMATION',True,True,'CAL-94-VALID','POLICY-95-V1','CAM-BIND','STATE-EPOCH-1')
def default_capabilities():
    p=default_policy()
    return (
        CapabilityLevel('READ',AuthorityTier.READ_ONLY,RiskLevel.CRITICAL,False,True,p.binding,p.state_epoch),
        CapabilityLevel('PROPOSE',AuthorityTier.ASSISTED,RiskLevel.CRITICAL,False,True,p.binding,p.state_epoch),
        CapabilityLevel('WRITE_SANDBOX',AuthorityTier.LIMITED_WRITE,RiskLevel.MEDIUM,True,True,p.binding,p.state_epoch),
        CapabilityLevel('AUTOMATE_LOW_RISK',AuthorityTier.AUTONOMOUS,RiskLevel.LOW,True,True,p.binding,p.state_epoch),
    )
def default_evaluation(): return evaluate(default_request(),default_capabilities(),default_policy())

def _records(caps): return tuple(sorted(caps,key=lambda c:c.capability_id))
def _record_fps(caps): return tuple(sorted((f'CAP:{c.capability_id}',_fp(c)) for c in caps))
def _constraint_fp(policy):
    return _fp((policy.readonly_threshold,policy.assisted_threshold,policy.limited_write_threshold,policy.autonomous_threshold,policy.max_low,policy.max_medium,policy.max_high,policy.max_critical,policy.global_max,policy.high_risk_approval,policy.critical_risk_approval,policy.allow_uncalibrated_low_risk))
def prepare_state(req,capabilities,policy,*,binding,state_epoch):
    caps=_records(capabilities); res=evaluate(req,caps,policy); rec=_record_fps(caps)
    return PreparedAuthorityState(req,caps,policy,rec,_fp(req),_fp(caps),_constraint_fp(policy),_fp(rec),res,binding,state_epoch)
def validate_prepared_integrity(st):
    if st.binding!=st.policy.binding or st.state_epoch!=st.policy.state_epoch: return False
    caps=_records(st.capabilities); rec=_record_fps(caps)
    return rec==st.record_fingerprints and st.context_fingerprint==_fp(st.request) and st.dependency_fingerprint==_fp(caps) and st.constraint_fingerprint==_constraint_fp(st.policy) and st.registry_fingerprint==_fp(rec) and st.precomputed_result==evaluate(st.request,caps,st.policy)
def evaluate_prepared(st,*,current_context_fingerprint,current_dependency_fingerprint,current_constraint_fingerprint,current_registry_fingerprint,prepared_integrity_validated):
    if not prepared_integrity_validated: return _hold('PREPARED_INTEGRITY_NOT_VALIDATED',st.request)
    if current_context_fingerprint!=st.context_fingerprint: return _hold('CONTEXT_FINGERPRINT_MISMATCH',st.request)
    if current_dependency_fingerprint!=st.dependency_fingerprint: return _hold('DEPENDENCY_FINGERPRINT_MISMATCH',st.request)
    if current_constraint_fingerprint!=st.constraint_fingerprint: return _hold('CONSTRAINT_FINGERPRINT_MISMATCH',st.request)
    if current_registry_fingerprint!=st.registry_fingerprint: return _hold('REGISTRY_FINGERPRINT_MISMATCH',st.request)
    return st.precomputed_result

def make_delta(base,target):
    bm={x.capability_id:x for x in base.capabilities}; tm={x.capability_id:x for x in target.capabilities}
    changed=tuple(tm[k] for k in sorted(tm) if k not in bm or _fp(tm[k])!=_fp(bm[k])); removed=tuple(sorted(k for k in bm if k not in tm))
    return AuthorityStateDelta(base.registry_fingerprint,target.registry_fingerprint,changed,removed,None if base.request==target.request else target.request,None if base.policy==target.policy else target.policy,target.binding,target.state_epoch)
def apply_delta(base,delta):
    if base.registry_fingerprint!=delta.base_fingerprint: raise ValueError('BASE_FINGERPRINT_MISMATCH')
    m={x.capability_id:x for x in base.capabilities}
    for k in delta.removed_capability_ids: m.pop(k,None)
    for x in delta.changed_capabilities: m[x.capability_id]=x
    out=prepare_state(delta.target_request or base.request,tuple(m.values()),delta.target_policy or base.policy,binding=delta.binding,state_epoch=delta.state_epoch)
    if out.registry_fingerprint!=delta.target_fingerprint: raise ValueError('TARGET_FINGERPRINT_MISMATCH')
    return out
def missing_only_sync_plan(target,known_record_fingerprints:dict[str,str]):
    miss=tuple(sorted(k for k,v in target.record_fingerprints if known_record_fingerprints.get(k)!=v)); metadata=len(_canon(miss)); full=len(miss)>max(1000,int(len(target.record_fingerprints)*.75)); return AuthoritySyncPlan(miss,metadata,full)
def full_registry_bytes(st): return len(_canon({'request':st.request,'capabilities':st.capabilities,'policy':st.policy}))
def delta_bytes(delta): return len(_canon(delta))
