"""NOEPIN AL 151 — Capability Escrow — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-151
DCSR: AUXILIARY INTEGRATION / 補助統合.

Evaluates whether a high-privilege capability may be represented as a one-time escrowed
proxy-execution candidate without directly returning capability or secret material to an agent.
Outputs are Escrow Grant / Proxy Execution / Receipt / Expiry candidates only.
Permit Evidence != Permission Grant. Escrow Grant Candidate != Capability Handoff.
Proxy Execution Candidate != Proxy Execution. Receipt Candidate != Action Success Proof.
This core performs no vault access, credential issue, secret retrieval, tool invocation, file write,
network send, permit consumption, receipt issuance, policy mutation, approval, stop, or external action.
DCSR reconstruction cannot create Truth, Domain Authority, Permission, Safety Proof, Approval,
Action, or Action Success.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json

class Decision(str, Enum):
    ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class EngineState(str, Enum):
    PROXY_EXECUTION_CANDIDATE='PROXY_EXECUTION_CANDIDATE'
    DIRECT_HANDOFF_BLOCKED_CANDIDATE='DIRECT_HANDOFF_BLOCKED_CANDIDATE'
    EXPIRED_CANDIDATE='EXPIRED_CANDIDATE'
    REVIEW_CANDIDATE='REVIEW_CANDIDATE'
    INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_PROXY_CANDIDATE='CONTINUE_PROXY_CANDIDATE'
    REJECT_HANDOFF_CANDIDATE='REJECT_HANDOFF_CANDIDATE'
    RENEW_PERMIT_CANDIDATE='RENEW_PERMIT_CANDIDATE'
    REVIEW_ESCROW_CANDIDATE='REVIEW_ESCROW_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'
    DIRECT_CAPABILITY_REQUEST='DIRECT_CAPABILITY_REQUEST'
    CONDITIONS_UNKNOWN='CONDITIONS_UNKNOWN'
    NOT_SINGLE_USE='NOT_SINGLE_USE'
    PERMIT_INVALID='PERMIT_INVALID'
    PERMIT_EXPIRED='PERMIT_EXPIRED'
    PERMIT_BINDING_MISMATCH='PERMIT_BINDING_MISMATCH'
    REPLAY_DETECTED='REPLAY_DETECTED'
    AGENT_IDENTITY_UNVERIFIED='AGENT_IDENTITY_UNVERIFIED'
    ESCROW_UNAVAILABLE='ESCROW_UNAVAILABLE'
    PROXY_UNAVAILABLE='PROXY_UNAVAILABLE'
    POLICY_UNVERIFIED='POLICY_UNVERIFIED'
    CAPABILITY_NOT_ALLOWED='CAPABILITY_NOT_ALLOWED'
    TTL_POLICY_VIOLATION='TTL_POLICY_VIOLATION'
    INVALID_CONFIGURATION='INVALID_CONFIGURATION'
class CapabilityClass(str, Enum):
    SECRET_KEY_USE='SECRET_KEY_USE'
    PROD_ADMIN_API='PROD_ADMIN_API'
    DELETE_PRIVILEGE='DELETE_PRIVILEGE'

@dataclass(frozen=True)
class RequestedCapability:
    capability_id:str; capability_class:CapabilityClass; vault_ref:str; proxy_supported:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class EscrowConditions:
    condition_id:str; known:bool; single_use:bool; purpose:str; target_ref:str; required_claims:tuple[str,...]; binding:str; state_epoch:str
@dataclass(frozen=True)
class AgentIdentity:
    agent_id:str; verified:bool; trust_domain:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class PermitEvidence:
    permit_id:str; valid:bool; approved:bool; capability_id:str; agent_id:str; purpose:str; target_ref:str
    issued_at:int; expires_at:int; nonce:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class EscrowPolicy:
    policy_id:str; verified:bool; allow_proxy:bool; require_single_use:bool; max_ttl:int
    allowed_capability_classes:tuple[CapabilityClass,...]; allowed_capability_ids:tuple[str,...]; binding:str; state_epoch:str
@dataclass(frozen=True)
class CapabilityEscrowRequest:
    request_id:str; capability:RequestedCapability; conditions:EscrowConditions; agent:AgentIdentity; permit:PermitEvidence; policy:EscrowPolicy
    direct_material_requested:bool; replay_detected:bool; escrow_available:bool; current_tick:int; binding:str; state_epoch:str
@dataclass(frozen=True)
class CapabilityEscrowResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState
    capability_id:str; agent_id:str; grant_candidate_id:str|None; proxy_execution_candidate:bool; receipt_candidate_id:str|None; expiry:int|None
    reasons:tuple[str,...]; next_gate_candidate:bool
    secret_material_returned:bool=False; capability_handoff_executed:bool=False; proxy_execution_executed:bool=False
    permit_consumed:bool=False; receipt_issued:bool=False; permit_promoted_to_permission:bool=False; escrow_grant_promoted_to_authority:bool=False
    receipt_promoted_to_action_success:bool=False; vault_accessed:bool=False; delegated_credential_issued:bool=False; tool_invoked:bool=False
    file_write_executed:bool=False; network_send_executed:bool=False; policy_modified:bool=False; permit_modified:bool=False
    dlp_replaced:bool=False; authentication_replaced:bool=False; encryption_replaced:bool=False; dcsr_reconstruction_created_fact:bool=False
    sender_authority_inherited:bool=False; sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False
    permission_granted:bool=False; approval_executed:bool=False; authority_granted:bool=False; stop_executed:bool=False
    action_executed:bool=False; plan_committed:bool=False; publish_executed:bool=False; external_write_performed:bool=False
    world_truth_proven:bool=False; domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedCapabilityEscrowState:
    request:CapabilityEscrowRequest; result:CapabilityEscrowResult; capability_fingerprint:str; conditions_fingerprint:str
    agent_fingerprint:str; permit_fingerprint:str; policy_fingerprint:str; request_context_fingerprint:str; outcome_fingerprint:str
    integrity_fingerprint:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class CapabilityEscrowDelta:
    capability_changed:bool; conditions_changed:bool; agent_changed:bool; permit_changed:bool; policy_changed:bool; request_context_changed:bool
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

def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    c=RequestedCapability('CAP-151-A',CapabilityClass.PROD_ADMIN_API,'vault-ref://prod-admin-api',True,b,e)
    cond=EscrowConditions('COND-151-A',True,True,'deploy-approved-release','service://production',('CHANGE-TICKET','OWNER-INTENT'),b,e)
    agent=AgentIdentity('AGENT-151-A',True,'NOEPIN-AL',b,e)
    permit=PermitEvidence('PERMIT-151-A',True,True,c.capability_id,agent.agent_id,cond.purpose,cond.target_ref,100,200,'NONCE-151-A',b,e)
    policy=EscrowPolicy('POL-151-A',True,True,True,120,(CapabilityClass.PROD_ADMIN_API,), (c.capability_id,), b,e)
    return CapabilityEscrowRequest('REQ-151-A',c,cond,agent,permit,policy,False,False,True,150,b,e)

def _invalid(req,reason):
    return CapabilityEscrowResult(Decision.HOLD,NextAction.REVIEW_ESCROW_CANDIDATE,Escalation.INVALID_CONFIGURATION,EngineState.INVALID,
        getattr(req.capability,'capability_id',''),getattr(req.agent,'agent_id',''),None,False,None,None,
        (reason,'NO_CAPABILITY_HANDOFF','NO_PROXY_EXECUTION','NO_AUTHORITY_PROMOTION'),False)

def _validate(req):
    if not req.request_id or not req.binding or not req.state_epoch: return 'EMPTY_REQUEST_CONTEXT'
    if req.current_tick < 0: return 'INVALID_CURRENT_TICK'
    for x,name in ((req.capability,'CAPABILITY'),(req.conditions,'CONDITIONS'),(req.agent,'AGENT'),(req.permit,'PERMIT'),(req.policy,'POLICY')):
        if x.binding!=req.binding or x.state_epoch!=req.state_epoch: return f'{name}_BINDING_MISMATCH'
    if not req.capability.capability_id or not req.capability.vault_ref: return 'EMPTY_CAPABILITY_ID'
    if not req.conditions.condition_id or not req.conditions.purpose or not req.conditions.target_ref: return 'EMPTY_CONDITIONS'
    if not req.agent.agent_id or not req.agent.trust_domain: return 'EMPTY_AGENT_IDENTITY'
    if not req.permit.permit_id or not req.permit.nonce: return 'EMPTY_PERMIT_EVIDENCE'
    if req.permit.issued_at < 0 or req.permit.expires_at < req.permit.issued_at: return 'INVALID_PERMIT_TIME_RANGE'
    if not req.policy.policy_id or req.policy.max_ttl < 0: return 'INVALID_POLICY'
    return None

def _candidate_ids(req):
    seed={'request_id':req.request_id,'capability_id':req.capability.capability_id,'agent_id':req.agent.agent_id,
          'permit_id':req.permit.permit_id,'nonce':req.permit.nonce,'purpose':req.conditions.purpose,'target':req.conditions.target_ref,
          'expiry':req.permit.expires_at,'binding':req.binding,'state_epoch':req.state_epoch}
    h=_fp(seed)
    return f'ESCROW-GRANT-CANDIDATE-{h[:20]}',f'RECEIPT-CANDIDATE-{h[20:40]}'

def evaluate(req):
    bad=_validate(req)
    if bad: return _invalid(req,bad)
    c,cond,a,p,pol=req.capability,req.conditions,req.agent,req.permit,req.policy
    base=('PERMIT_EVIDENCE_IS_NOT_PERMISSION_GRANT','ESCROW_GRANT_IS_CANDIDATE_NOT_CAPABILITY_HANDOFF',
          'PROXY_EXECUTION_IS_CANDIDATE_NOT_EXECUTION','RECEIPT_IS_CANDIDATE_NOT_ACTION_SUCCESS','NO_SECRET_MATERIAL_RETURN')
    if req.direct_material_requested:
        return CapabilityEscrowResult(Decision.DENY,NextAction.REJECT_HANDOFF_CANDIDATE,Escalation.DIRECT_CAPABILITY_REQUEST,
            EngineState.DIRECT_HANDOFF_BLOCKED_CANDIDATE,c.capability_id,a.agent_id,None,False,None,None,
            ('DIRECT_CAPABILITY_OR_SECRET_MATERIAL_REQUEST_BLOCKED',)+base,True)
    if not cond.known:
        return CapabilityEscrowResult(Decision.HOLD,NextAction.REVIEW_ESCROW_CANDIDATE,Escalation.CONDITIONS_UNKNOWN,
            EngineState.REVIEW_CANDIDATE,c.capability_id,a.agent_id,None,False,None,None,('ESCROW_CONDITIONS_UNKNOWN',)+base,True)
    if pol.require_single_use and not cond.single_use:
        return CapabilityEscrowResult(Decision.DENY,NextAction.REJECT_HANDOFF_CANDIDATE,Escalation.NOT_SINGLE_USE,
            EngineState.DIRECT_HANDOFF_BLOCKED_CANDIDATE,c.capability_id,a.agent_id,None,False,None,None,('NON_SINGLE_USE_REQUEST_DENIED',)+base,True)
    if not pol.verified:
        return CapabilityEscrowResult(Decision.HOLD,NextAction.REVIEW_ESCROW_CANDIDATE,Escalation.POLICY_UNVERIFIED,
            EngineState.REVIEW_CANDIDATE,c.capability_id,a.agent_id,None,False,None,None,('ESCROW_POLICY_UNVERIFIED',)+base,True)
    if not a.verified:
        return CapabilityEscrowResult(Decision.HOLD,NextAction.REVIEW_ESCROW_CANDIDATE,Escalation.AGENT_IDENTITY_UNVERIFIED,
            EngineState.REVIEW_CANDIDATE,c.capability_id,a.agent_id,None,False,None,None,('AGENT_IDENTITY_UNVERIFIED',)+base,True)
    if req.replay_detected:
        return CapabilityEscrowResult(Decision.DENY,NextAction.REJECT_HANDOFF_CANDIDATE,Escalation.REPLAY_DETECTED,
            EngineState.DIRECT_HANDOFF_BLOCKED_CANDIDATE,c.capability_id,a.agent_id,None,False,None,None,('ONE_TIME_PERMIT_REPLAY_DETECTED',)+base,True)
    if req.current_tick > p.expires_at:
        return CapabilityEscrowResult(Decision.DENY,NextAction.RENEW_PERMIT_CANDIDATE,Escalation.PERMIT_EXPIRED,
            EngineState.EXPIRED_CANDIDATE,c.capability_id,a.agent_id,None,False,None,p.expires_at,('PERMIT_EXPIRED',)+base,True)
    if not p.valid or not p.approved:
        return CapabilityEscrowResult(Decision.DENY,NextAction.REJECT_HANDOFF_CANDIDATE,Escalation.PERMIT_INVALID,
            EngineState.DIRECT_HANDOFF_BLOCKED_CANDIDATE,c.capability_id,a.agent_id,None,False,None,p.expires_at,('PERMIT_INVALID_OR_UNAPPROVED',)+base,True)
    if p.capability_id!=c.capability_id or p.agent_id!=a.agent_id or p.purpose!=cond.purpose or p.target_ref!=cond.target_ref:
        return CapabilityEscrowResult(Decision.DENY,NextAction.REJECT_HANDOFF_CANDIDATE,Escalation.PERMIT_BINDING_MISMATCH,
            EngineState.DIRECT_HANDOFF_BLOCKED_CANDIDATE,c.capability_id,a.agent_id,None,False,None,p.expires_at,('PERMIT_SCOPE_BINDING_MISMATCH',)+base,True)
    if (p.expires_at-p.issued_at) > pol.max_ttl:
        return CapabilityEscrowResult(Decision.DENY,NextAction.RENEW_PERMIT_CANDIDATE,Escalation.TTL_POLICY_VIOLATION,
            EngineState.EXPIRED_CANDIDATE,c.capability_id,a.agent_id,None,False,None,p.expires_at,('PERMIT_TTL_EXCEEDS_POLICY',)+base,True)
    if c.capability_class not in pol.allowed_capability_classes or (pol.allowed_capability_ids and c.capability_id not in pol.allowed_capability_ids):
        return CapabilityEscrowResult(Decision.DENY,NextAction.REJECT_HANDOFF_CANDIDATE,Escalation.CAPABILITY_NOT_ALLOWED,
            EngineState.DIRECT_HANDOFF_BLOCKED_CANDIDATE,c.capability_id,a.agent_id,None,False,None,p.expires_at,('CAPABILITY_NOT_ALLOWED_BY_POLICY',)+base,True)
    if not req.escrow_available:
        return CapabilityEscrowResult(Decision.HOLD,NextAction.REVIEW_ESCROW_CANDIDATE,Escalation.ESCROW_UNAVAILABLE,
            EngineState.REVIEW_CANDIDATE,c.capability_id,a.agent_id,None,False,None,p.expires_at,('ESCROW_SERVICE_UNAVAILABLE',)+base,True)
    if not c.proxy_supported or not pol.allow_proxy:
        return CapabilityEscrowResult(Decision.DENY,NextAction.REJECT_HANDOFF_CANDIDATE,Escalation.PROXY_UNAVAILABLE,
            EngineState.DIRECT_HANDOFF_BLOCKED_CANDIDATE,c.capability_id,a.agent_id,None,False,None,p.expires_at,('PROXY_EXECUTION_UNAVAILABLE',)+base,True)
    grant,receipt=_candidate_ids(req)
    return CapabilityEscrowResult(Decision.ALLOW,NextAction.CONTINUE_PROXY_CANDIDATE,Escalation.NONE,
        EngineState.PROXY_EXECUTION_CANDIDATE,c.capability_id,a.agent_id,grant,True,receipt,p.expires_at,
        ('ONE_TIME_ESCROW_CONDITIONS_MATCHED','PERMIT_EVIDENCE_MATCHED','IDENTITY_EVIDENCE_MATCHED','PROXY_EXECUTION_CANDIDATE_ONLY')+base,True)

def prepare_state(req,binding,state_epoch):
    if binding!=req.binding or state_epoch!=req.state_epoch: return PreparedCapabilityEscrowState(req,_invalid(req,'PREPARE_BINDING_MISMATCH'),'','','','','','','','',binding,state_epoch)
    result=evaluate(req)
    cf=_fp(req.capability); xf=_fp(req.conditions); af=_fp(req.agent); pf=_fp(req.permit); polf=_fp(req.policy)
    rcf=_fp((req.direct_material_requested,req.replay_detected,req.escrow_available,req.current_tick,req.request_id,req.binding,req.state_epoch))
    of=_fp(result); integ=_fp((cf,xf,af,pf,polf,rcf,of,binding,state_epoch))
    return PreparedCapabilityEscrowState(req,result,cf,xf,af,pf,polf,rcf,of,integ,binding,state_epoch)

def evaluate_prepared(st,*,integrity_validated,current_capability_fingerprint,current_conditions_fingerprint,current_agent_fingerprint,
        current_permit_fingerprint,current_policy_fingerprint,current_request_context_fingerprint,current_outcome_fingerprint):
    vals=(current_capability_fingerprint,current_conditions_fingerprint,current_agent_fingerprint,current_permit_fingerprint,
          current_policy_fingerprint,current_request_context_fingerprint,current_outcome_fingerprint)
    exp=(st.capability_fingerprint,st.conditions_fingerprint,st.agent_fingerprint,st.permit_fingerprint,st.policy_fingerprint,
         st.request_context_fingerprint,st.outcome_fingerprint)
    integrity=_fp(exp+(st.binding,st.state_epoch))
    if not integrity_validated or vals!=exp or integrity!=st.integrity_fingerprint:
        return _invalid(st.request,'PREPARED_STATE_INTEGRITY_MISMATCH')
    return st.result

def make_delta(old,new):
    changes=(old.capability_fingerprint!=new.capability_fingerprint,old.conditions_fingerprint!=new.conditions_fingerprint,
             old.agent_fingerprint!=new.agent_fingerprint,old.permit_fingerprint!=new.permit_fingerprint,
             old.policy_fingerprint!=new.policy_fingerprint,old.request_context_fingerprint!=new.request_context_fingerprint)
    return CapabilityEscrowDelta(*changes,_fp((old.capability_fingerprint,old.conditions_fingerprint,old.agent_fingerprint,old.permit_fingerprint,old.policy_fingerprint,old.request_context_fingerprint)),
        _fp((new.capability_fingerprint,new.conditions_fingerprint,new.agent_fingerprint,new.permit_fingerprint,new.policy_fingerprint,new.request_context_fingerprint)))

def plan_missing_only(old,new):
    ids=[]
    if old.capability_fingerprint!=new.capability_fingerprint: ids.append('REQUESTED_CAPABILITY')
    if old.conditions_fingerprint!=new.conditions_fingerprint: ids.append('CONDITIONS')
    if old.agent_fingerprint!=new.agent_fingerprint: ids.append('AGENT_IDENTITY')
    if old.permit_fingerprint!=new.permit_fingerprint: ids.append('PERMIT')
    if old.policy_fingerprint!=new.policy_fingerprint: ids.append('ESCROW_POLICY')
    if old.request_context_fingerprint!=new.request_context_fingerprint: ids.append('REQUEST_CONTEXT')
    metadata=len(_canon(tuple(ids)))+96 if ids else 0
    return MissingOnlyPlan(tuple(ids),metadata,False)

def default_evaluation(): return evaluate(default_request())
