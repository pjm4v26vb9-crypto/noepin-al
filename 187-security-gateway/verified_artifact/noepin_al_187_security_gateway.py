"""NOEPIN AL Sequential Slot 187 — 00｜AL Security Gateway completion successor.

Pure deterministic security-gateway decision model. It performs no network, filesystem,
process, permission, credential, permit, approval, tool, or action execution. An ALLOW
result means only that the request may continue to a separately authorized permit/execution
gate. Permit data emitted here is a bound candidate/fingerprint, never an issued credential.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
from fnmatch import fnmatchcase
from hashlib import sha256
import hmac, json
from typing import Any

class Decision(str, Enum):
    ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class NextAction(str, Enum):
    CONTINUE_TO_PERMIT_GATE_CANDIDATE='CONTINUE_TO_PERMIT_GATE_CANDIDATE'
    REQUEST_HUMAN_APPROVAL_EVIDENCE='REQUEST_HUMAN_APPROVAL_EVIDENCE'
    RETAIN_NO_EXECUTION_CANDIDATE='RETAIN_NO_EXECUTION_CANDIDATE'
    REFRESH_DYNAMIC_SECURITY_STATE='REFRESH_DYNAMIC_SECURITY_STATE'
    FULL_SECURITY_REEVALUATION='FULL_SECURITY_REEVALUATION'
class Escalation(str, Enum):
    NONE='NONE'; MISSING_FIELD='MISSING_FIELD'; AUTHENTICATION_FAILED='AUTHENTICATION_FAILED'
    ROLE_POLICY_MISSING='ROLE_POLICY_MISSING'; REPLAY_DETECTED='REPLAY_DETECTED'
    RATE_LIMIT='RATE_LIMIT'; ACTION_SCOPE='ACTION_SCOPE'; TARGET_SCOPE='TARGET_SCOPE'
    PARAMETER_SCOPE='PARAMETER_SCOPE'; SEMANTIC_DENY='SEMANTIC_DENY'; SEMANTIC_HOLD='SEMANTIC_HOLD'
    SEMANTIC_UNKNOWN='SEMANTIC_UNKNOWN'; HUMAN_APPROVAL_REQUIRED='HUMAN_APPROVAL_REQUIRED'
    APPROVAL_BINDING_MISMATCH='APPROVAL_BINDING_MISMATCH'; PREPARED_STATE_STALE='PREPARED_STATE_STALE'
    PERMIT_CANDIDATE_INVALID='PERMIT_CANDIDATE_INVALID'
class EngineState(str, Enum):
    SECURITY_CHAIN_CANDIDATE='SECURITY_CHAIN_CANDIDATE'; HOLD_CANDIDATE='HOLD_CANDIDATE'
    DENY_CANDIDATE='DENY_CANDIDATE'; HUMAN_APPROVAL_CANDIDATE='HUMAN_APPROVAL_CANDIDATE'

@dataclass(frozen=True)
class GatewayRequest:
    request_id:str; principal_id:str; api_key:str; nonce:str; action:str; target:str
    parameters:tuple[tuple[str,str],...]=(); now_ms:int=1_000_000
@dataclass(frozen=True)
class RolePolicy:
    policy_id:str; principal_id:str; api_key_sha256:str; allowed_actions:tuple[str,...]
    allowed_target_patterns:tuple[str,...]; allowed_parameter_keys:tuple[str,...]
    approval_actions:tuple[str,...]=(); max_requests_per_window:int=10; policy_version:str='1'
@dataclass(frozen=True)
class DynamicSecurityState:
    seen_nonces:tuple[str,...]=(); requests_in_window:int=0; semantic_decision:str='ALLOW'
    human_approval_id:str=''; approval_request_fingerprint:str=''; approval_valid:bool=False
    used_permit_candidate_ids:tuple[str,...]=(); window_id:str='W1'
@dataclass(frozen=True)
class GatewayResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState
    request_id:str; principal_id:str; auth_verified:bool; role_policy_match:bool; action_allowed:bool
    target_allowed:bool; parameter_keys_allowed:bool; replay_clear:bool; rate_clear:bool
    semantic_decision:str; human_approval_required:bool; human_approval_evidence_match:bool
    request_fingerprint:str; policy_fingerprint:str; dynamic_state_fingerprint:str
    permit_candidate_id:str; permit_candidate_fingerprint:str; permit_candidate_expiry_ms:int
    permit_candidate_bound:bool; audit_candidate_fingerprint:str; next_gate_candidate:bool
    authoritative:bool; reason:str; prepared_state_reused:bool=False
    permission_granted:bool=False; permit_issued:bool=False; credential_minted:bool=False
    approval_executed:bool=False; human_approval_executed:bool=False; tool_invoked:bool=False
    action_executed:bool=False; action_success:bool=False; stop_executed:bool=False
    file_write_executed:bool=False; network_send_executed:bool=False; external_write_performed:bool=False
    world_truth_proven:bool=False; memory_promoted_to_truth:bool=False; belief_promoted_to_truth:bool=False
    candidate_promoted_to_actual:bool=False; intent_promoted_to_action:bool=False
    action_request_promoted_to_success:bool=False; policy_allow_promoted_to_permission:bool=False
    human_approval_evidence_promoted_to_execution:bool=False; permit_candidate_promoted_to_issued:bool=False
    cached_result_promoted_to_authoritative:bool=False; fingerprint_match_promoted_to_authority:bool=False
    safety_proven:bool=False; dcsr_bypassed_authentication:bool=False; dcsr_bypassed_replay:bool=False
    dcsr_bypassed_rate_limit:bool=False; dcsr_bypassed_semantic_policy:bool=False
    dcsr_reused_human_approval:bool=False; dcsr_minted_permission:bool=False
@dataclass(frozen=True)
class PreparedGatewayState:
    request:GatewayRequest; policy:RolePolicy; dynamic:DynamicSecurityState; result:GatewayResult
    request_fingerprint:str; policy_fingerprint:str; dynamic_fingerprint:str; result_fingerprint:str
    integrity_fingerprint:str
@dataclass(frozen=True)
class GatewayDelta:
    reused_fields:tuple[str,...]; missing_or_changed_fields:tuple[str,...]; metadata_bytes:int
    full_reevaluation_required:bool; fingerprint:str
@dataclass(frozen=True)
class MissingOnlyPlan:
    missing_or_changed_fields:tuple[str,...]; metadata_bytes_required:int; full_reevaluation_required:bool

FALSE_FIELDS=(
'permission_granted','permit_issued','credential_minted','approval_executed','human_approval_executed','tool_invoked',
'action_executed','action_success','stop_executed','file_write_executed','network_send_executed','external_write_performed',
'world_truth_proven','memory_promoted_to_truth','belief_promoted_to_truth','candidate_promoted_to_actual',
'intent_promoted_to_action','action_request_promoted_to_success','policy_allow_promoted_to_permission',
'human_approval_evidence_promoted_to_execution','permit_candidate_promoted_to_issued',
'cached_result_promoted_to_authoritative','fingerprint_match_promoted_to_authority','safety_proven',
'dcsr_bypassed_authentication','dcsr_bypassed_replay','dcsr_bypassed_rate_limit','dcsr_bypassed_semantic_policy',
'dcsr_reused_human_approval','dcsr_minted_permission')

def _norm(v:Any)->Any:
    if isinstance(v,Enum): return v.value
    if is_dataclass(v): return {f.name:_norm(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v,dict): return {str(k):_norm(v[k]) for k in sorted(v,key=lambda x:str(x))}
    if isinstance(v,(tuple,list)): return [_norm(x) for x in v]
    if isinstance(v,(set,frozenset)): return sorted((_norm(x) for x in v),key=lambda x:json.dumps(x,sort_keys=True,separators=(',',':')))
    return v

def _canon(v:Any)->bytes: return json.dumps(_norm(v),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def fingerprint(v:Any)->str: return sha256(_canon(v)).hexdigest()
def api_key_sha256(v:str)->str: return sha256(v.encode()).hexdigest()
def _constant_time_eq(a:str,b:str)->bool: return hmac.compare_digest(a.encode(),b.encode())

def request_fingerprint(req:GatewayRequest)->str:
    # Exclude raw api_key from candidate/audit fingerprint; include its hash instead.
    return fingerprint((req.request_id,req.principal_id,api_key_sha256(req.api_key),req.nonce,req.action,req.target,tuple(sorted(req.parameters)),req.now_ms))

def policy_fingerprint(policy:RolePolicy)->str: return fingerprint(policy)
def dynamic_fingerprint(dynamic:DynamicSecurityState)->str: return fingerprint(dynamic)
def candidate_context_fingerprint(dynamic:DynamicSecurityState)->str:
    # Stable permit-candidate context excludes only the used-candidate ledger, so consuming
    # a candidate cannot cause its own identity to change and evade replay/one-time-use checks.
    return fingerprint((dynamic.seen_nonces,dynamic.requests_in_window,dynamic.semantic_decision,dynamic.human_approval_id,dynamic.approval_request_fingerprint,dynamic.approval_valid,dynamic.window_id))

def approval_binding_fingerprint(req:GatewayRequest)->str:
    return fingerprint(('HUMAN_APPROVAL_BINDING_V1',req.request_id,req.principal_id,req.action,req.target,tuple(sorted(req.parameters))))

def _empty_result(req:GatewayRequest,policy:RolePolicy,dynamic:DynamicSecurityState,decision:Decision,next_action:NextAction,esc:Escalation,state:EngineState,reason:str,**kw)->GatewayResult:
    base=dict(
      decision=decision,next_action=next_action,escalation=esc,engine_state=state,request_id=req.request_id,principal_id=req.principal_id,
      auth_verified=False,role_policy_match=False,action_allowed=False,target_allowed=False,parameter_keys_allowed=False,replay_clear=False,rate_clear=False,
      semantic_decision=dynamic.semantic_decision,human_approval_required=False,human_approval_evidence_match=False,
      request_fingerprint=request_fingerprint(req),policy_fingerprint=policy_fingerprint(policy),dynamic_state_fingerprint=dynamic_fingerprint(dynamic),
      permit_candidate_id='',permit_candidate_fingerprint='',permit_candidate_expiry_ms=0,permit_candidate_bound=False,audit_candidate_fingerprint='',
      next_gate_candidate=False,authoritative=False,reason=reason)
    base.update(kw); return GatewayResult(**base)

def evaluate(req:GatewayRequest,policy:RolePolicy,dynamic:DynamicSecurityState)->GatewayResult:
    required=(req.request_id,req.principal_id,req.api_key,req.nonce,req.action,req.target,policy.policy_id,policy.principal_id,policy.api_key_sha256)
    if not all(required):
        return _empty_result(req,policy,dynamic,Decision.HOLD,NextAction.RETAIN_NO_EXECUTION_CANDIDATE,Escalation.MISSING_FIELD,EngineState.HOLD_CANDIDATE,'Required field missing.')
    auth=_constant_time_eq(api_key_sha256(req.api_key),policy.api_key_sha256) and req.principal_id==policy.principal_id
    if not auth:
        return _empty_result(req,policy,dynamic,Decision.DENY,NextAction.RETAIN_NO_EXECUTION_CANDIDATE,Escalation.AUTHENTICATION_FAILED,EngineState.DENY_CANDIDATE,'Authentication failed.')
    role_match=(req.principal_id==policy.principal_id and bool(policy.allowed_actions) and bool(policy.allowed_target_patterns))
    if not role_match:
        return _empty_result(req,policy,dynamic,Decision.DENY,NextAction.RETAIN_NO_EXECUTION_CANDIDATE,Escalation.ROLE_POLICY_MISSING,EngineState.DENY_CANDIDATE,'No effective role policy.',auth_verified=True)
    if req.nonce in set(dynamic.seen_nonces):
        return _empty_result(req,policy,dynamic,Decision.DENY,NextAction.RETAIN_NO_EXECUTION_CANDIDATE,Escalation.REPLAY_DETECTED,EngineState.DENY_CANDIDATE,'Replay nonce detected.',auth_verified=True,role_policy_match=True)
    rate_clear=(policy.max_requests_per_window>0 and dynamic.requests_in_window < policy.max_requests_per_window)
    if not rate_clear:
        return _empty_result(req,policy,dynamic,Decision.HOLD,NextAction.REFRESH_DYNAMIC_SECURITY_STATE,Escalation.RATE_LIMIT,EngineState.HOLD_CANDIDATE,'Rate limit reached.',auth_verified=True,role_policy_match=True,replay_clear=True)
    action_allowed=req.action in set(policy.allowed_actions)
    if not action_allowed:
        return _empty_result(req,policy,dynamic,Decision.DENY,NextAction.RETAIN_NO_EXECUTION_CANDIDATE,Escalation.ACTION_SCOPE,EngineState.DENY_CANDIDATE,'Action outside allowlist.',auth_verified=True,role_policy_match=True,replay_clear=True,rate_clear=True)
    target_allowed=any(fnmatchcase(req.target,p) for p in policy.allowed_target_patterns)
    if not target_allowed:
        return _empty_result(req,policy,dynamic,Decision.DENY,NextAction.RETAIN_NO_EXECUTION_CANDIDATE,Escalation.TARGET_SCOPE,EngineState.DENY_CANDIDATE,'Target outside scope.',auth_verified=True,role_policy_match=True,replay_clear=True,rate_clear=True,action_allowed=True)
    keys={k for k,_ in req.parameters}; param_allowed=keys.issubset(set(policy.allowed_parameter_keys))
    if not param_allowed:
        return _empty_result(req,policy,dynamic,Decision.DENY,NextAction.RETAIN_NO_EXECUTION_CANDIDATE,Escalation.PARAMETER_SCOPE,EngineState.DENY_CANDIDATE,'Parameter key outside scope.',auth_verified=True,role_policy_match=True,replay_clear=True,rate_clear=True,action_allowed=True,target_allowed=True)
    sem=dynamic.semantic_decision.upper().strip()
    common=dict(auth_verified=True,role_policy_match=True,replay_clear=True,rate_clear=True,action_allowed=True,target_allowed=True,parameter_keys_allowed=True)
    if sem=='DENY':
        return _empty_result(req,policy,dynamic,Decision.DENY,NextAction.RETAIN_NO_EXECUTION_CANDIDATE,Escalation.SEMANTIC_DENY,EngineState.DENY_CANDIDATE,'Semantic policy denied.',**common)
    if sem=='HOLD':
        return _empty_result(req,policy,dynamic,Decision.HOLD,NextAction.FULL_SECURITY_REEVALUATION,Escalation.SEMANTIC_HOLD,EngineState.HOLD_CANDIDATE,'Semantic policy held.',**common)
    if sem=='HUMAN_APPROVAL':
        approval_required=True
    elif sem=='ALLOW':
        approval_required=req.action in set(policy.approval_actions)
    else:
        return _empty_result(req,policy,dynamic,Decision.HOLD,NextAction.FULL_SECURITY_REEVALUATION,Escalation.SEMANTIC_UNKNOWN,EngineState.HOLD_CANDIDATE,'Unknown semantic decision.',**common)
    approval_match=(dynamic.approval_valid and bool(dynamic.human_approval_id) and dynamic.approval_request_fingerprint==approval_binding_fingerprint(req))
    if approval_required and not approval_match:
        esc=Escalation.APPROVAL_BINDING_MISMATCH if dynamic.approval_valid or dynamic.human_approval_id or dynamic.approval_request_fingerprint else Escalation.HUMAN_APPROVAL_REQUIRED
        return _empty_result(req,policy,dynamic,Decision.HUMAN_APPROVAL,NextAction.REQUEST_HUMAN_APPROVAL_EVIDENCE,esc,EngineState.HUMAN_APPROVAL_CANDIDATE,'Bound human approval evidence required.',**common,human_approval_required=True,human_approval_evidence_match=False)
    rfp=request_fingerprint(req); pfp=policy_fingerprint(policy); dfp=dynamic_fingerprint(dynamic)
    candidate_id='PC-'+fingerprint(('permit-candidate-id',rfp,pfp,candidate_context_fingerprint(dynamic)))[:24]
    expiry=req.now_ms+30_000
    binding=fingerprint(('PERMIT_CANDIDATE_V1',candidate_id,rfp,pfp,req.principal_id,req.action,req.target,tuple(sorted(req.parameters)),expiry))
    audit=fingerprint(('AUDIT_CANDIDATE_V1',rfp,pfp,dfp,Decision.ALLOW.value,binding))
    used=candidate_id in set(dynamic.used_permit_candidate_ids)
    if used:
        return _empty_result(req,policy,dynamic,Decision.DENY,NextAction.RETAIN_NO_EXECUTION_CANDIDATE,Escalation.PERMIT_CANDIDATE_INVALID,EngineState.DENY_CANDIDATE,'Permit candidate already marked used.',**common,human_approval_required=approval_required,human_approval_evidence_match=approval_match)
    return _empty_result(req,policy,dynamic,Decision.ALLOW,NextAction.CONTINUE_TO_PERMIT_GATE_CANDIDATE,Escalation.NONE,EngineState.SECURITY_CHAIN_CANDIDATE,
      'Security checks satisfied; continue only to a separately authorized permit/execution gate.',**common,
      human_approval_required=approval_required,human_approval_evidence_match=approval_match,permit_candidate_id=candidate_id,
      permit_candidate_fingerprint=binding,permit_candidate_expiry_ms=expiry,permit_candidate_bound=True,audit_candidate_fingerprint=audit,next_gate_candidate=True)

def validate_permit_candidate(result:GatewayResult,current_request:GatewayRequest,current_policy:RolePolicy,current_dynamic:DynamicSecurityState)->bool:
    if result.decision!=Decision.ALLOW or not result.permit_candidate_bound or not result.next_gate_candidate: return False
    if current_request.now_ms>result.permit_candidate_expiry_ms: return False
    if result.request_fingerprint!=request_fingerprint(current_request) or result.policy_fingerprint!=policy_fingerprint(current_policy): return False
    # Dynamic state is intentionally part of the binding: nonce/rate/approval state must be fresh.
    if result.dynamic_state_fingerprint!=dynamic_fingerprint(current_dynamic): return False
    expected=fingerprint(('PERMIT_CANDIDATE_V1',result.permit_candidate_id,result.request_fingerprint,result.policy_fingerprint,current_request.principal_id,current_request.action,current_request.target,tuple(sorted(current_request.parameters)),result.permit_candidate_expiry_ms))
    return hmac.compare_digest(expected,result.permit_candidate_fingerprint)

def prepare_state(req:GatewayRequest,policy:RolePolicy,dynamic:DynamicSecurityState)->PreparedGatewayState:
    r=evaluate(req,policy,dynamic); rf=request_fingerprint(req); pf=policy_fingerprint(policy); df=dynamic_fingerprint(dynamic); res=fingerprint(r)
    integ=fingerprint(('PREPARED_SECURITY_GATEWAY_V1',rf,pf,df,res))
    return PreparedGatewayState(req,policy,dynamic,r,rf,pf,df,res,integ)

def evaluate_prepared(prepared:PreparedGatewayState,*,integrity_validated:bool,current_request:GatewayRequest,current_policy:RolePolicy,current_dynamic:DynamicSecurityState,current_result_fingerprint:str,current_integrity_fingerprint:str)->GatewayResult:
    rf=request_fingerprint(current_request); pf=policy_fingerprint(current_policy); df=dynamic_fingerprint(current_dynamic)
    expected_integ=fingerprint(('PREPARED_SECURITY_GATEWAY_V1',prepared.request_fingerprint,prepared.policy_fingerprint,prepared.dynamic_fingerprint,prepared.result_fingerprint))
    valid=(integrity_validated and prepared.integrity_fingerprint==expected_integ==current_integrity_fingerprint and
           prepared.request_fingerprint==rf and prepared.policy_fingerprint==pf and prepared.dynamic_fingerprint==df and
           prepared.result_fingerprint==current_result_fingerprint and fingerprint(prepared.result)==prepared.result_fingerprint)
    if not valid:
        return replace(_empty_result(current_request,current_policy,current_dynamic,Decision.HOLD,NextAction.FULL_SECURITY_REEVALUATION,Escalation.PREPARED_STATE_STALE,EngineState.HOLD_CANDIDATE,'Prepared security state stale or integrity mismatch.'),prepared_state_reused=False)
    # Even valid prepared state does not skip dynamic checks; exact fingerprints prove the same evaluated state only.
    return replace(prepared.result,prepared_state_reused=True)

def make_delta(req:GatewayRequest,policy:RolePolicy,dynamic:DynamicSecurityState,known:dict[str,str]|None=None)->GatewayDelta:
    known=known or {}
    current={'REQUEST':request_fingerprint(req),'POLICY':policy_fingerprint(policy),'DYNAMIC_SECURITY_STATE':dynamic_fingerprint(dynamic)}
    reused=tuple(sorted(k for k,v in current.items() if known.get(k)==v))
    missing=tuple(sorted(k for k,v in current.items() if known.get(k)!=v))
    # Dynamic security state is never safely omitted unless exact fingerprint matches.
    full=('REQUEST' in missing and 'POLICY' in missing and 'DYNAMIC_SECURITY_STATE' in missing)
    metadata=64+sum(len(k)+64 for k in missing)
    fp=fingerprint(('GATEWAY_DELTA_V1',reused,missing,metadata,full))
    return GatewayDelta(reused,missing,metadata,full,fp)

def plan_missing_only(req:GatewayRequest,policy:RolePolicy,dynamic:DynamicSecurityState,known:dict[str,str]|None=None)->MissingOnlyPlan:
    d=make_delta(req,policy,dynamic,known); return MissingOnlyPlan(d.missing_or_changed_fields,d.metadata_bytes,d.full_reevaluation_required)

def default_request()->GatewayRequest:
    return GatewayRequest('REQ-00-A','agent-safe','key-safe-001','nonce-001','tool.read','workspace://safe/item',(('mode','metadata'),),1_000_000)
def default_policy()->RolePolicy:
    return RolePolicy('POL-00-A','agent-safe',api_key_sha256('key-safe-001'),('tool.read','tool.write'),('workspace://safe/*',),('mode','value'),('tool.write',),10,'1')
def default_dynamic()->DynamicSecurityState:
    return DynamicSecurityState((),1,'ALLOW','','',False,(),'W1')
def default_evaluation()->GatewayResult:
    return evaluate(default_request(),default_policy(),default_dynamic())
