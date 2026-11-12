"""NOEPIN AL 136 — Episodic Isolation Manager — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-136
DCSR: LIMITED INTEGRATION / 限定適用.

Isolation and promotion outputs are audit/control candidates only.
Memory != Truth. Mention != Memory. Promotion Candidate != Long-term Memory Write.
Approval Evidence != Approval Execution. Same-task visibility != cross-task sharing authority.
Sensitivity classification != Truth. Cross-scope access is deny-by-default.
No candidate performs memory writes, long-term promotion, permission grants, approvals, authority changes,
external retrieval, or action execution. DCSR reconstruction does not create a new memory or known fact.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str,Enum): ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class IsolationState(str,Enum):
    PROMOTION_CANDIDATE='PROMOTION_CANDIDATE'; SAME_SCOPE_VISIBLE='SAME_SCOPE_VISIBLE'; ISOLATED='ISOLATED'
    BLOCKED_CROSS_SCOPE='BLOCKED_CROSS_SCOPE'; HUMAN_APPROVAL_REQUIRED='HUMAN_APPROVAL_REQUIRED'
    UNKNOWN_SCOPE_ISOLATED='UNKNOWN_SCOPE_ISOLATED'; MENTION_ONLY='MENTION_ONLY'; EMPTY='EMPTY'; INVALID='INVALID'
class NextAction(str,Enum):
    LONG_TERM_PROMOTION_CANDIDATE='LONG_TERM_PROMOTION_CANDIDATE'; SAME_SCOPE_REFERENCE_CANDIDATE='SAME_SCOPE_REFERENCE_CANDIDATE'
    ISOLATED_STORE_CANDIDATE='ISOLATED_STORE_CANDIDATE'; BLOCKED_TRANSFER_CANDIDATE='BLOCKED_TRANSFER_CANDIDATE'
    HUMAN_APPROVAL_CANDIDATE='HUMAN_APPROVAL_CANDIDATE'; NO_MEMORY_CANDIDATE='NO_MEMORY_CANDIDATE'
class Escalation(str,Enum):
    NONE='NONE'; CROSS_SCOPE_BLOCKED='CROSS_SCOPE_BLOCKED'; SENSITIVE_APPROVAL_REQUIRED='SENSITIVE_APPROVAL_REQUIRED'
    PROMOTION_APPROVAL_REQUIRED='PROMOTION_APPROVAL_REQUIRED'; UNKNOWN_TASK_SCOPE='UNKNOWN_TASK_SCOPE'
    UNKNOWN_SENSITIVITY='UNKNOWN_SENSITIVITY'; LOW_TRUST='LOW_TRUST'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'
class RecordKind(str,Enum): MEMORY='MEMORY'; MENTION='MENTION'
class ScopeMode(str,Enum): TASK='TASK'; SESSION_ONLY='SESSION_ONLY'
class Sensitivity(str,Enum): PUBLIC='PUBLIC'; INTERNAL='INTERNAL'; SENSITIVE='SENSITIVE'; RESTRICTED='RESTRICTED'; UNKNOWN='UNKNOWN'

@dataclass(frozen=True)
class SessionMemory:
    memory_id:str; value:str; task_id:str|None; session_id:str|None; scope_mode:ScopeMode; sensitivity:Sensitivity
    reusable_value:float; trust:float; promotion_approval_evidence:bool; kind:RecordKind; source_id:str|None
    purpose_id:str; binding:str; state_epoch:str

@dataclass(frozen=True)
class PromotionPolicy:
    min_reusable_value:float=.72
    min_trust:float=.70
    require_approval_for_all_promotions:bool=True
    sensitive_requires_explicit_approval:bool=True
    deny_cross_task_by_default:bool=True
    deny_cross_session_for_session_only:bool=True
    unknown_task_isolate:bool=True
    unknown_sensitivity_isolate:bool=True

@dataclass(frozen=True)
class IsolationRequest:
    request_id:str; memories:tuple[SessionMemory,...]; target_task_id:str|None; target_session_id:str|None
    promotion_requested:bool; policy:PromotionPolicy; binding:str; state_epoch:str

@dataclass(frozen=True)
class MemoryDisposition:
    memory_id:str; visible_same_scope:bool; isolated:bool; blocked_transfer:bool; promotion_eligible:bool
    approval_evidence_present:bool; reasons:tuple[str,...]

@dataclass(frozen=True)
class IsolationResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; isolation_state:IsolationState; reasons:tuple[str,...]
    visible_memory_ids:tuple[str,...]; isolated_memory_ids:tuple[str,...]; promotion_candidate_ids:tuple[str,...]
    blocked_transfer_ids:tuple[str,...]; human_approval_ids:tuple[str,...]; dispositions:tuple[MemoryDisposition,...]
    next_gate_candidate:bool
    memory_promoted_to_truth:bool=False; mention_promoted_to_memory:bool=False; promotion_written_to_long_term:bool=False
    approval_evidence_promoted_to_approval_execution:bool=False; same_scope_visibility_promoted_to_cross_scope_authority:bool=False
    sensitivity_promoted_to_truth:bool=False; blocked_transfer_executed:bool=False; memory_write_performed:bool=False
    dcsr_reconstruction_created_memory:bool=False; sender_authority_inherited:bool=False; sender_intent_inherited:bool=False
    sender_agreement_inherited:bool=False; permission_granted:bool=False; approval_executed:bool=False; authority_granted:bool=False
    stop_executed:bool=False; action_executed:bool=False; plan_committed:bool=False; publish_executed:bool=False
    external_write_performed:bool=False; world_truth_proven:bool=False; domain_authority_promoted:bool=False
    safety_proven:bool=False; action_success:bool=False

@dataclass(frozen=True)
class PreparedIsolationState:
    request:IsolationRequest; result:IsolationResult; context_fingerprint:str; memory_fingerprint:str
    policy_fingerprint:str; outcome_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str

@dataclass(frozen=True)
class IsolationDelta:
    changed_memories:tuple[SessionMemory,...]; removed_memory_ids:tuple[str,...]; target_task_changed:bool
    target_session_changed:bool; promotion_request_changed:bool; policy_changed:bool
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
def _finite(x): return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(float(x))
def _manifest_fp(req): return _fp((req.memories,req.target_task_id,req.target_session_id,req.promotion_requested,req.policy,req.binding,req.state_epoch))

def default_policy(): return PromotionPolicy()
def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    memories=(SessionMemory('MEM-1','safe reusable note','TASK-A','SESSION-1',ScopeMode.TASK,Sensitivity.INTERNAL,.94,.92,True,RecordKind.MEMORY,'SRC-1','PURPOSE-A',b,e),)
    return IsolationRequest('REQ-136',memories,'TASK-A','SESSION-2',True,default_policy(),b,e)

def _invalid(reason):
    return IsolationResult(Decision.HOLD,NextAction.ISOLATED_STORE_CANDIDATE,Escalation.INVALID_CONFIGURATION,IsolationState.INVALID,(reason,'NO_MEMORY_WRITE'),(),(),(),(),(),(),False)

def _validate(req):
    p=req.policy
    if not (_finite(p.min_reusable_value) and _finite(p.min_trust)): return 'NONFINITE_POLICY'
    if not (0<=p.min_reusable_value<=1 and 0<=p.min_trust<=1): return 'POLICY_RANGE'
    ids=set()
    for x in req.memories:
        if x.memory_id in ids: return 'DUPLICATE_MEMORY_ID'
        ids.add(x.memory_id)
        if x.binding!=req.binding or x.state_epoch!=req.state_epoch: return 'STATE_BINDING_MISMATCH'
        if not (_finite(x.reusable_value) and _finite(x.trust)): return 'NONFINITE_MEMORY_SCORE'
        if not (0<=x.reusable_value<=1 and 0<=x.trust<=1): return 'MEMORY_SCORE_RANGE'
    return None

def _same_scope(x,req):
    if not x.task_id or not req.target_task_id: return False,'TASK_SCOPE_UNKNOWN'
    if x.task_id!=req.target_task_id: return False,'CROSS_TASK'
    if x.scope_mode==ScopeMode.SESSION_ONLY:
        if not x.session_id or not req.target_session_id: return False,'SESSION_SCOPE_UNKNOWN'
        if x.session_id!=req.target_session_id: return False,'CROSS_SESSION'
    return True,'SAME_SCOPE'

def evaluate(req):
    err=_validate(req)
    if err: return _invalid(err)
    memories=tuple(sorted((x for x in req.memories if x.kind==RecordKind.MEMORY),key=lambda x:x.memory_id))
    mentions=tuple(x for x in req.memories if x.kind==RecordKind.MENTION)
    if not memories:
        state=IsolationState.MENTION_ONLY if mentions else IsolationState.EMPTY
        return IsolationResult(Decision.ALLOW,NextAction.NO_MEMORY_CANDIDATE,Escalation.NONE,state,('NO_MEMORY_RECORDS','MENTION_NOT_PROMOTED_TO_MEMORY','NO_MEMORY_WRITE'),(),(),(),(),(),(),True)
    vis=[]; iso=[]; promos=[]; blocked=[]; human=[]; disp=[]; unknown_scope=[]; unknown_sens=[]; low_trust=[]
    p=req.policy
    for x in memories:
        reasons=[]; same,why=_same_scope(x,req); reasons.append(why)
        visible=False; isolated=False; blocked_transfer=False; promotion=False; approval_need=False
        if why in ('TASK_SCOPE_UNKNOWN','SESSION_SCOPE_UNKNOWN'):
            isolated=True; unknown_scope.append(x.memory_id); reasons.append('UNKNOWN_SCOPE_ISOLATED')
        elif not same:
            if (why=='CROSS_TASK' and p.deny_cross_task_by_default) or (why=='CROSS_SESSION' and p.deny_cross_session_for_session_only):
                isolated=True; blocked_transfer=True; blocked.append(x.memory_id); reasons.append('CROSS_SCOPE_DENY_BY_DEFAULT')
            else:
                isolated=True; reasons.append('CROSS_SCOPE_NOT_VISIBLE')
        else:
            visible=True; vis.append(x.memory_id); reasons.append('SAME_SCOPE_VISIBLE')
        if x.sensitivity==Sensitivity.UNKNOWN:
            unknown_sens.append(x.memory_id); reasons.append('UNKNOWN_SENSITIVITY')
        if x.trust<p.min_trust:
            low_trust.append(x.memory_id); reasons.append('TRUST_BELOW_PROMOTION_THRESHOLD')
        if req.promotion_requested and same and visible:
            safe_sens=x.sensitivity!=Sensitivity.UNKNOWN
            quality=x.reusable_value>=p.min_reusable_value and x.trust>=p.min_trust
            if not safe_sens and p.unknown_sensitivity_isolate:
                isolated=True; reasons.append('PROMOTION_BLOCKED_UNKNOWN_SENSITIVITY')
            elif quality:
                sensitive=x.sensitivity in (Sensitivity.SENSITIVE,Sensitivity.RESTRICTED)
                approval_required=p.require_approval_for_all_promotions or (p.sensitive_requires_explicit_approval and sensitive)
                if approval_required and not x.promotion_approval_evidence:
                    approval_need=True; human.append(x.memory_id); reasons.append('EXPLICIT_APPROVAL_EVIDENCE_REQUIRED')
                else:
                    promotion=True; promos.append(x.memory_id); reasons.append('PROMOTION_CANDIDATE_ONLY')
            else:
                isolated=True; reasons.append('PROMOTION_QUALITY_THRESHOLD_NOT_MET')
        if isolated: iso.append(x.memory_id)
        disp.append(MemoryDisposition(x.memory_id,visible,isolated,blocked_transfer,promotion,x.promotion_approval_evidence,tuple(reasons)))
    vis=tuple(sorted(set(vis))); iso=tuple(sorted(set(iso))); promos=tuple(sorted(set(promos))); blocked=tuple(sorted(set(blocked))); human=tuple(sorted(set(human)))
    disp=tuple(sorted(disp,key=lambda d:d.memory_id))
    if unknown_scope:
        return IsolationResult(Decision.HOLD,NextAction.ISOLATED_STORE_CANDIDATE,Escalation.UNKNOWN_TASK_SCOPE,IsolationState.UNKNOWN_SCOPE_ISOLATED,('TASK_OR_SESSION_BOUNDARY_UNKNOWN','NO_LONG_TERM_PROMOTION','NO_MEMORY_WRITE'),vis,iso,promos,blocked,human,disp,False)
    if blocked and not vis and not promos and not human:
        return IsolationResult(Decision.ALLOW,NextAction.BLOCKED_TRANSFER_CANDIDATE,Escalation.CROSS_SCOPE_BLOCKED,IsolationState.BLOCKED_CROSS_SCOPE,('CROSS_SCOPE_DENIED_BY_DEFAULT','BLOCK_AUDIT_CANDIDATE_ONLY','NO_TRANSFER_EXECUTION'),vis,iso,promos,blocked,human,disp,True)
    if unknown_sens and req.promotion_requested:
        return IsolationResult(Decision.HOLD,NextAction.ISOLATED_STORE_CANDIDATE,Escalation.UNKNOWN_SENSITIVITY,IsolationState.ISOLATED,('SENSITIVITY_UNKNOWN','NO_LONG_TERM_PROMOTION','NO_MEMORY_WRITE'),vis,iso,promos,blocked,human,disp,False)
    if human:
        esc=Escalation.SENSITIVE_APPROVAL_REQUIRED if any(x.sensitivity in (Sensitivity.SENSITIVE,Sensitivity.RESTRICTED) and x.memory_id in human for x in memories) else Escalation.PROMOTION_APPROVAL_REQUIRED
        return IsolationResult(Decision.HUMAN_APPROVAL,NextAction.HUMAN_APPROVAL_CANDIDATE,esc,IsolationState.HUMAN_APPROVAL_REQUIRED,('PROMOTION_REQUIRES_APPROVAL_EVIDENCE','APPROVAL_EVIDENCE_NOT_APPROVAL_EXECUTION','NO_MEMORY_WRITE'),vis,iso,promos,blocked,human,disp,False)
    if promos:
        return IsolationResult(Decision.ALLOW,NextAction.LONG_TERM_PROMOTION_CANDIDATE,Escalation.NONE,IsolationState.PROMOTION_CANDIDATE,('EXPLICIT_PROMOTION_RULES_SATISFIED','PROMOTION_CANDIDATE_ONLY','NO_MEMORY_WRITE'),vis,iso,promos,blocked,human,disp,True)
    if vis:
        esc=Escalation.LOW_TRUST if low_trust else Escalation.NONE
        return IsolationResult(Decision.ALLOW,NextAction.SAME_SCOPE_REFERENCE_CANDIDATE,esc,IsolationState.SAME_SCOPE_VISIBLE,('SAME_SCOPE_REFERENCE_ONLY','NO_CROSS_SCOPE_AUTHORITY','NO_MEMORY_WRITE'),vis,iso,promos,blocked,human,disp,True)
    return IsolationResult(Decision.ALLOW,NextAction.ISOLATED_STORE_CANDIDATE,Escalation.NONE,IsolationState.ISOLATED,('ISOLATED_EPISODIC_MEMORY','NO_MEMORY_WRITE'),vis,iso,promos,blocked,human,disp,True)

def default_evaluation(): return evaluate(default_request())

def _fps(req,res):
    return (_fp((req.request_id,req.target_task_id,req.target_session_id,req.promotion_requested,req.binding,req.state_epoch)),_fp(req.memories),_fp(req.policy),_fp(res))
def prepare_state(req,binding,state_epoch):
    if binding!=req.binding or state_epoch!=req.state_epoch: raise ValueError('PREPARED_BINDING_MISMATCH')
    res=evaluate(req); c,m,p,o=_fps(req,res); integ=_fp((c,m,p,o,binding,state_epoch))
    return PreparedIsolationState(req,res,c,m,p,o,integ,binding,state_epoch)
def validate_prepared_integrity(st): return st.integrity_fingerprint==_fp((st.context_fingerprint,st.memory_fingerprint,st.policy_fingerprint,st.outcome_fingerprint,st.binding,st.state_epoch))
def evaluate_prepared(st,*,integrity_validated,current_context_fingerprint,current_memory_fingerprint,current_policy_fingerprint,current_outcome_fingerprint):
    if not integrity_validated or not validate_prepared_integrity(st): return _invalid('PREPARED_INTEGRITY_NOT_VALIDATED')
    if (current_context_fingerprint,current_memory_fingerprint,current_policy_fingerprint,current_outcome_fingerprint)!=(st.context_fingerprint,st.memory_fingerprint,st.policy_fingerprint,st.outcome_fingerprint): return _invalid('PREPARED_FINGERPRINT_MISMATCH')
    return st.result

def make_delta(old,new):
    a={x.memory_id:x for x in old.request.memories}; b={x.memory_id:x for x in new.request.memories}
    changed=tuple(b[k] for k in sorted(b) if k not in a or a[k]!=b[k]); removed=tuple(sorted(set(a)-set(b)))
    return IsolationDelta(changed,removed,old.request.target_task_id!=new.request.target_task_id,old.request.target_session_id!=new.request.target_session_id,old.request.promotion_requested!=new.request.promotion_requested,old.policy_fingerprint!=new.policy_fingerprint,_manifest_fp(old.request),_manifest_fp(new.request))
def plan_missing_only(old,new):
    d=make_delta(old,new); ids=[f'MEMORY:{x.memory_id}' for x in d.changed_memories]+[f'MEMORY:{x}' for x in d.removed_memory_ids]
    if d.target_task_changed: ids.append('TARGET_TASK')
    if d.target_session_changed: ids.append('TARGET_SESSION')
    if d.promotion_request_changed: ids.append('PROMOTION_REQUEST')
    if d.policy_changed: ids.append('PROMOTION_POLICY')
    meta=len(_canon((tuple(ids),d.from_manifest_fingerprint,d.to_manifest_fingerprint)))
    return MissingOnlyPlan(tuple(ids),meta,False)
