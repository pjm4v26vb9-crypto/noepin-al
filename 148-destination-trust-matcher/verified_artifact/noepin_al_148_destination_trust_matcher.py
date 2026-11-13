"""NOEPIN AL 148 — Destination Trust Matcher — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-148
DCSR: AUXILIARY INTEGRATION / 補助統合.

Compares data sensitivity with destination identity, trust, ownership, region and service policy.
Outputs are destination decision / mismatch / alternative candidates only. Destination Trust != Permission.
Destination Identity Evidence != Identity Authority. Alternative Destination Candidate != Routing Execution.
ALLOW Candidate != Data Transfer Execution. HOLD/DENY Candidate != Stop Execution.
This core does not send data, resolve DNS over a network, invoke tools, mutate policy, grant permission,
or replace authentication/encryption/Policy/DLP. DCSR reconstruction cannot create Truth, Authority,
Permission, Approval, Action, Data Transfer, or Action Success.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
from hashlib import sha256
import json

class Decision(str, Enum):
    ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class EngineState(str, Enum):
    TRUSTED_DESTINATION_CANDIDATE='TRUSTED_DESTINATION_CANDIDATE'
    ALTERNATIVE_DESTINATION_CANDIDATE='ALTERNATIVE_DESTINATION_CANDIDATE'
    DESTINATION_BLOCKED_CANDIDATE='DESTINATION_BLOCKED_CANDIDATE'
    REVIEW_CANDIDATE='REVIEW_CANDIDATE'; INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_DESTINATION_CANDIDATE='CONTINUE_DESTINATION_CANDIDATE'
    USE_ALTERNATIVE_CANDIDATE='USE_ALTERNATIVE_CANDIDATE'
    BLOCK_DESTINATION_CANDIDATE='BLOCK_DESTINATION_CANDIDATE'
    REVIEW_DESTINATION_CANDIDATE='REVIEW_DESTINATION_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; UNKNOWN_DESTINATION='UNKNOWN_DESTINATION'; TRUST_INSUFFICIENT='TRUST_INSUFFICIENT'
    REGION_VIOLATION='REGION_VIOLATION'; OWNERSHIP_MISMATCH='OWNERSHIP_MISMATCH'
    SPOOF_SUSPECTED='SPOOF_SUSPECTED'; POLICY_MISMATCH='POLICY_MISMATCH'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'
class Sensitivity(str, Enum):
    PUBLIC='PUBLIC'; INTERNAL='INTERNAL'; CONFIDENTIAL='CONFIDENTIAL'; SECRET='SECRET'
class TrustTier(str, Enum):
    UNKNOWN='UNKNOWN'; LOW='LOW'; MEDIUM='MEDIUM'; HIGH='HIGH'; CRITICAL='CRITICAL'

@dataclass(frozen=True)
class DataLabel:
    data_id:str; sensitivity:Sensitivity; provenance_ids:tuple[str,...]; binding:str; state_epoch:str
@dataclass(frozen=True)
class DestinationIdentity:
    destination_id:str; verified:bool; trust_tier:TrustTier; owner_org:str; region:str; service_type:str
    service_identity_digest:str; spoof_suspected:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class AlternativeDestination:
    destination_id:str; verified:bool; trust_tier:TrustTier; owner_org:str; region:str; service_type:str
@dataclass(frozen=True)
class NetworkServicePolicy:
    allowed_regions:tuple[str,...]; allowed_owner_orgs:tuple[str,...]
    minimum_trust_public:TrustTier; minimum_trust_internal:TrustTier
    minimum_trust_confidential:TrustTier; minimum_trust_secret:TrustTier
    allowed_service_types:tuple[str,...]; alternatives:tuple[AlternativeDestination,...]
    binding:str; state_epoch:str
@dataclass(frozen=True)
class DestinationRequest:
    request_id:str; data_labels:tuple[DataLabel,...]; destination:DestinationIdentity; policy:NetworkServicePolicy
    binding:str; state_epoch:str
@dataclass(frozen=True)
class DestinationResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState
    effective_sensitivity:Sensitivity; destination_id:str; mismatch:tuple[str,...]
    alternative_destination_ids:tuple[str,...]; reasons:tuple[str,...]; trace:tuple[str,...]; next_gate_candidate:bool
    destination_trust_promoted_to_permission:bool=False; destination_identity_promoted_to_identity_authority:bool=False
    alternative_destination_routed:bool=False; data_transfer_executed:bool=False; external_send_executed:bool=False
    dns_resolution_executed:bool=False; service_call_executed:bool=False; tool_invoked:bool=False; policy_modified:bool=False
    dlp_replaced:bool=False; authentication_replaced:bool=False; encryption_replaced:bool=False
    dcsr_reconstruction_created_fact:bool=False; sender_authority_inherited:bool=False; sender_intent_inherited:bool=False
    sender_agreement_inherited:bool=False; permission_granted:bool=False; approval_executed:bool=False
    authority_granted:bool=False; stop_executed:bool=False; action_executed:bool=False; plan_committed:bool=False
    publish_executed:bool=False; external_write_performed:bool=False; world_truth_proven:bool=False
    domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedDestinationState:
    request:DestinationRequest; result:DestinationResult; labels_fingerprint:str; destination_fingerprint:str
    policy_fingerprint:str; outcome_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class DestinationDelta:
    labels_changed:bool; destination_changed:bool; policy_changed:bool
    from_manifest_fingerprint:str; to_manifest_fingerprint:str
@dataclass(frozen=True)
class MissingOnlyPlan:
    missing_or_changed_record_ids:tuple[str,...]; metadata_bytes_required:int; full_resend_required:bool

def _obj(v):
    if isinstance(v,Enum): return v.value
    if is_dataclass(v): return {f.name:_obj(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v,dict): return {str(k):_obj(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(tuple,list)): return [_obj(x) for x in v]
    return v

def _canon(v): return json.dumps(_obj(v),ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def _fp(v): return sha256(_canon(v)).hexdigest()

_SENS_RANK={Sensitivity.PUBLIC:0,Sensitivity.INTERNAL:1,Sensitivity.CONFIDENTIAL:2,Sensitivity.SECRET:3}
_TRUST_RANK={TrustTier.UNKNOWN:0,TrustTier.LOW:1,TrustTier.MEDIUM:2,TrustTier.HIGH:3,TrustTier.CRITICAL:4}

def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    dl=(DataLabel('DATA-148-A',Sensitivity.INTERNAL,('SRC-148-A',),b,e),)
    d=DestinationIdentity('DEST-148-A',True,TrustTier.HIGH,'NOEPIN','JP','INTERNAL_API','svc:148:trusted',False,b,e)
    p=NetworkServicePolicy(('JP',),('NOEPIN',),TrustTier.LOW,TrustTier.MEDIUM,TrustTier.HIGH,TrustTier.CRITICAL,
        ('INTERNAL_API','CLOUD_STORAGE'),(),b,e)
    return DestinationRequest('REQ-148',dl,d,p,b,e)

def _invalid(req,reason):
    sens=Sensitivity.SECRET if not req.data_labels else max((x.sensitivity for x in req.data_labels),key=lambda s:_SENS_RANK[s])
    return DestinationResult(Decision.HOLD,NextAction.REVIEW_DESTINATION_CANDIDATE,Escalation.INVALID_CONFIGURATION,
        EngineState.INVALID,sens,getattr(req.destination,'destination_id',''),(reason,),(),
        (reason,'NO_DATA_TRANSFER_EXECUTION','NO_PERMISSION_GRANT'),(),False)

def _validate(req):
    if not req.request_id or not req.binding or not req.state_epoch: return 'EMPTY_REQUEST_CONTEXT'
    if not req.data_labels: return 'NO_DATA_LABELS'
    ids=[x.data_id for x in req.data_labels]
    if len(set(ids))!=len(ids) or any(not x for x in ids): return 'INVALID_DATA_IDS'
    for x in req.data_labels:
        if x.binding!=req.binding or x.state_epoch!=req.state_epoch: return 'DATA_BINDING_MISMATCH'
        if len(set(x.provenance_ids))!=len(x.provenance_ids) or any(not p for p in x.provenance_ids): return 'INVALID_PROVENANCE'
    d=req.destination
    if d.binding!=req.binding or d.state_epoch!=req.state_epoch: return 'DESTINATION_BINDING_MISMATCH'
    if not d.destination_id or not d.service_type: return 'INVALID_DESTINATION_IDENTITY'
    p=req.policy
    if p.binding!=req.binding or p.state_epoch!=req.state_epoch: return 'POLICY_BINDING_MISMATCH'
    if len(set(p.allowed_regions))!=len(p.allowed_regions) or len(set(p.allowed_owner_orgs))!=len(p.allowed_owner_orgs): return 'DUPLICATE_POLICY_VALUES'
    if len(set(p.allowed_service_types))!=len(p.allowed_service_types): return 'DUPLICATE_SERVICE_TYPES'
    aids=[a.destination_id for a in p.alternatives]
    if len(set(aids))!=len(aids) or any(not x for x in aids): return 'INVALID_ALTERNATIVES'
    return None

def _effective_sensitivity(labels): return max((x.sensitivity for x in labels),key=lambda s:_SENS_RANK[s])
def _required_trust(p,s):
    return {Sensitivity.PUBLIC:p.minimum_trust_public,Sensitivity.INTERNAL:p.minimum_trust_internal,
            Sensitivity.CONFIDENTIAL:p.minimum_trust_confidential,Sensitivity.SECRET:p.minimum_trust_secret}[s]

def _alternative_candidates(req,sens):
    p=req.policy; need=_required_trust(p,sens); out=[]
    for a in p.alternatives:
        if not a.verified: continue
        if _TRUST_RANK[a.trust_tier] < _TRUST_RANK[need]: continue
        if p.allowed_regions and a.region not in p.allowed_regions: continue
        if p.allowed_owner_orgs and a.owner_org not in p.allowed_owner_orgs: continue
        if p.allowed_service_types and a.service_type not in p.allowed_service_types: continue
        out.append(a.destination_id)
    return tuple(sorted(out))

def evaluate(req):
    bad=_validate(req)
    if bad: return _invalid(req,bad)
    p=req.policy; d=req.destination; sens=_effective_sensitivity(req.data_labels); need=_required_trust(p,sens)
    mismatch=[]; trace=[f'SENSITIVITY:{sens.value}',f'DEST:{d.destination_id}',f'TRUST:{d.trust_tier.value}',f'REQUIRED:{need.value}']
    if d.spoof_suspected: mismatch.append('SPOOF_SUSPECTED')
    if not d.verified: mismatch.append('DESTINATION_UNVERIFIED')
    if _TRUST_RANK[d.trust_tier] < _TRUST_RANK[need]: mismatch.append('TRUST_INSUFFICIENT')
    if p.allowed_regions and d.region not in p.allowed_regions: mismatch.append('REGION_VIOLATION')
    if p.allowed_owner_orgs and d.owner_org not in p.allowed_owner_orgs: mismatch.append('OWNERSHIP_MISMATCH')
    if p.allowed_service_types and d.service_type not in p.allowed_service_types: mismatch.append('SERVICE_POLICY_MISMATCH')
    alts=_alternative_candidates(req,sens)

    # Fail-safe: unverified/unknown destination carrying sensitive data is denied as a candidate.
    if sens!=Sensitivity.PUBLIC and (not d.verified or d.trust_tier==TrustTier.UNKNOWN):
        esc=Escalation.SPOOF_SUSPECTED if d.spoof_suspected else Escalation.UNKNOWN_DESTINATION
        return DestinationResult(Decision.DENY,NextAction.BLOCK_DESTINATION_CANDIDATE,esc,
            EngineState.DESTINATION_BLOCKED_CANDIDATE,sens,d.destination_id,tuple(mismatch),alts,
            ('SENSITIVE_DESTINATION_IDENTITY_NOT_VERIFIED','DENY_IS_CANDIDATE_NOT_STOP_EXECUTION','NO_DATA_TRANSFER_EXECUTION'),tuple(trace),True)
    if d.spoof_suspected:
        return DestinationResult(Decision.DENY,NextAction.BLOCK_DESTINATION_CANDIDATE,Escalation.SPOOF_SUSPECTED,
            EngineState.DESTINATION_BLOCKED_CANDIDATE,sens,d.destination_id,tuple(mismatch),alts,
            ('SPOOF_SUSPECTED','NO_DNS_OR_SERVICE_EXECUTION'),tuple(trace),True)
    # Public data is not auto-approved when destination identity is unknown; classify the identity uncertainty explicitly.
    if sens==Sensitivity.PUBLIC and not d.verified:
        return DestinationResult(Decision.HOLD,NextAction.REVIEW_DESTINATION_CANDIDATE,Escalation.UNKNOWN_DESTINATION,
            EngineState.REVIEW_CANDIDATE,sens,d.destination_id,tuple(mismatch),alts,
            ('PUBLIC_DATA_BUT_DESTINATION_UNVERIFIED','REVIEW_BEFORE_TRANSFER'),tuple(trace),True)
    if 'REGION_VIOLATION' in mismatch:
        return DestinationResult(Decision.DENY if sens!=Sensitivity.PUBLIC else Decision.HOLD,
            NextAction.USE_ALTERNATIVE_CANDIDATE if alts else NextAction.BLOCK_DESTINATION_CANDIDATE,
            Escalation.REGION_VIOLATION,EngineState.ALTERNATIVE_DESTINATION_CANDIDATE if alts else EngineState.DESTINATION_BLOCKED_CANDIDATE,
            sens,d.destination_id,tuple(mismatch),alts,('REGION_POLICY_MISMATCH','ALTERNATIVE_IS_CANDIDATE_ONLY'),tuple(trace),True)
    if 'OWNERSHIP_MISMATCH' in mismatch:
        return DestinationResult(Decision.DENY if _SENS_RANK[sens]>=2 else Decision.HOLD,
            NextAction.USE_ALTERNATIVE_CANDIDATE if alts else NextAction.REVIEW_DESTINATION_CANDIDATE,
            Escalation.OWNERSHIP_MISMATCH,EngineState.ALTERNATIVE_DESTINATION_CANDIDATE if alts else EngineState.REVIEW_CANDIDATE,
            sens,d.destination_id,tuple(mismatch),alts,('OWNERSHIP_POLICY_MISMATCH','NO_PERMISSION_GRANT'),tuple(trace),True)
    if 'TRUST_INSUFFICIENT' in mismatch:
        return DestinationResult(Decision.DENY if _SENS_RANK[sens]>=2 else Decision.HOLD,
            NextAction.USE_ALTERNATIVE_CANDIDATE if alts else NextAction.REVIEW_DESTINATION_CANDIDATE,
            Escalation.TRUST_INSUFFICIENT,EngineState.ALTERNATIVE_DESTINATION_CANDIDATE if alts else EngineState.REVIEW_CANDIDATE,
            sens,d.destination_id,tuple(mismatch),alts,('TRUST_TIER_BELOW_REQUIREMENT','NO_DATA_TRANSFER_EXECUTION'),tuple(trace),True)
    if 'SERVICE_POLICY_MISMATCH' in mismatch:
        return DestinationResult(Decision.HOLD,NextAction.USE_ALTERNATIVE_CANDIDATE if alts else NextAction.REVIEW_DESTINATION_CANDIDATE,
            Escalation.POLICY_MISMATCH,EngineState.ALTERNATIVE_DESTINATION_CANDIDATE if alts else EngineState.REVIEW_CANDIDATE,
            sens,d.destination_id,tuple(mismatch),alts,('SERVICE_TYPE_POLICY_MISMATCH',),tuple(trace),True)
    return DestinationResult(Decision.ALLOW,NextAction.CONTINUE_DESTINATION_CANDIDATE,Escalation.NONE,
        EngineState.TRUSTED_DESTINATION_CANDIDATE,sens,d.destination_id,tuple(mismatch),alts,
        ('DESTINATION_POLICY_MATCH_CANDIDATE','ALLOW_IS_NOT_PERMISSION_GRANT','NO_DATA_TRANSFER_EXECUTION'),tuple(trace),True)

def default_evaluation(): return evaluate(default_request())

def prepare_state(req,binding,state_epoch):
    if binding!=req.binding or state_epoch!=req.state_epoch: raise ValueError('PREPARE_BINDING_MISMATCH')
    result=evaluate(req); lf=_fp(req.data_labels); df=_fp(req.destination); pf=_fp(req.policy); of=_fp(result)
    integ=_fp((lf,df,pf,of,binding,state_epoch))
    return PreparedDestinationState(req,result,lf,df,pf,of,integ,binding,state_epoch)

def evaluate_prepared(state,*,integrity_validated,current_labels_fingerprint,current_destination_fingerprint,current_policy_fingerprint,current_outcome_fingerprint):
    expected=_fp((state.labels_fingerprint,state.destination_fingerprint,state.policy_fingerprint,state.outcome_fingerprint,state.binding,state.state_epoch))
    if (not integrity_validated or expected!=state.integrity_fingerprint or current_labels_fingerprint!=state.labels_fingerprint
        or current_destination_fingerprint!=state.destination_fingerprint or current_policy_fingerprint!=state.policy_fingerprint
        or current_outcome_fingerprint!=state.outcome_fingerprint):
        return _invalid(state.request,'PREPARED_STATE_INTEGRITY_MISMATCH')
    return state.result

def make_delta(old,new):
    return DestinationDelta(old.labels_fingerprint!=new.labels_fingerprint,old.destination_fingerprint!=new.destination_fingerprint,
        old.policy_fingerprint!=new.policy_fingerprint,old.integrity_fingerprint,new.integrity_fingerprint)

def plan_missing_only(old,new):
    ids=[]
    if old.labels_fingerprint!=new.labels_fingerprint: ids.append('DATA_LABELS')
    if old.destination_fingerprint!=new.destination_fingerprint: ids.append('DESTINATION_IDENTITY')
    if old.policy_fingerprint!=new.policy_fingerprint: ids.append('NETWORK_SERVICE_POLICY')
    metadata=len(_canon(tuple(ids)))+64
    return MissingOnlyPlan(tuple(ids),metadata,False)
