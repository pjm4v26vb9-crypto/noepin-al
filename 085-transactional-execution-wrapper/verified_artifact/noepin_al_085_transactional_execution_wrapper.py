"""NOEPIN AL 085 — Transactional Execution Wrapper — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Pure transaction-control state machine for Begin / Apply / Verify / Commit / Rollback
boundaries. This module evaluates typed evidence and emits transaction candidates; it
does not execute external actions, commit state, perform rollback, grant permission,
write externally, prove World Truth/Safety, or assert Action Success.

Canonical identity: NOEPIN-AL-085
Provenance note: exact registered Origin GUID was not freshly reverified in this
completion session and is intentionally not guessed or regenerated.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json

class Decision(str,Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class StepStatus(str,Enum):
    APPLIED='APPLIED'; FAILED='FAILED'; TIMEOUT='TIMEOUT'; EXCEPTION='EXCEPTION'
class VerifyStatus(str,Enum):
    MATCH='MATCH'; MISMATCH='MISMATCH'; TIMEOUT='TIMEOUT'; EXCEPTION='EXCEPTION'; UNOBSERVED='UNOBSERVED'
class RollbackStatus(str,Enum):
    NOT_OBSERVED='NOT_OBSERVED'; SUCCEEDED='SUCCEEDED'; FAILED='FAILED'; TIMEOUT='TIMEOUT'
class TransactionState(str,Enum):
    HOLD='HOLD'; APPLYING='APPLYING'; VERIFYING='VERIFYING'; COMMIT_CANDIDATE='COMMIT_CANDIDATE'; ROLLBACK_REQUIRED='ROLLBACK_REQUIRED'; ROLLBACK_VERIFIED='ROLLBACK_VERIFIED'; INCIDENT_HOLD='INCIDENT_HOLD'

@dataclass(frozen=True)
class TransactionRequest:
    request_id:str; transaction_id:str; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class IntentEvidence:
    intent_id:str; transaction_id:str; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class PermitEvidence:
    permit_id:str; transaction_id:str; observed:bool; allow_candidate:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class ActionSpec:
    action_id:str; order:int; required:bool=True
@dataclass(frozen=True)
class ActionPlan:
    transaction_id:str; actions:tuple[ActionSpec,...]; binding:str; state_epoch:str
@dataclass(frozen=True)
class StateSnapshot:
    snapshot_id:str; transaction_id:str; state_fingerprint:str; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class StepEvidence:
    evidence_id:str; transaction_id:str; action_id:str; observed:bool; status:StepStatus; before_fingerprint:str; after_fingerprint:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class VerifyEvidence:
    verify_id:str; transaction_id:str; observed:bool; status:VerifyStatus; final_state_fingerprint:str; expected_final_state_fingerprint:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class RollbackEvidence:
    rollback_id:str; transaction_id:str; observed:bool; status:RollbackStatus; restored_state_fingerprint:str; snapshot_state_fingerprint:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class TransactionPolicy:
    require_permit_evidence:bool; binding:str; state_epoch:str; revoked:bool=False
@dataclass(frozen=True)
class TransactionResult:
    decision:Decision
    transaction_state:TransactionState
    reasons:tuple[str,...]
    applied_action_ids:tuple[str,...]
    failed_action_id:str|None
    commit_candidate:bool
    rollback_candidate:bool
    rollback_verified:bool
    incident_candidate:bool
    commit_result:str
    rollback_result:str
    audit_trail:tuple[str,...]
    next_gate_candidate:bool
    request_promoted_to_success:bool=False
    intent_promoted_to_action:bool=False
    permission_granted:bool=False
    action_executed:bool=False
    commit_executed:bool=False
    rollback_executed:bool=False
    external_write_performed:bool=False
    receipt_promoted_to_truth:bool=False
    world_truth_proven:bool=False
    safety_proven:bool=False
    action_success:bool=False

@dataclass(frozen=True)
class PreparedTransactionState:
    request:TransactionRequest; intent:IntentEvidence; permit:PermitEvidence; plan:ActionPlan
    before_snapshot:StateSnapshot; after_snapshot:StateSnapshot
    steps:tuple[StepEvidence,...]; verify:VerifyEvidence; rollback:RollbackEvidence; policy:TransactionPolicy
    step_fingerprints:tuple[tuple[str,str],...]
    context_fingerprint:str; dependency_fingerprint:str; registry_fingerprint:str
    precomputed_result:TransactionResult; binding:str; state_epoch:str
@dataclass(frozen=True)
class TransactionStateDelta:
    base_fingerprint:str; target_fingerprint:str
    changed_steps:tuple[StepEvidence,...]; removed_evidence_ids:tuple[str,...]
    target_request:TransactionRequest|None; target_intent:IntentEvidence|None; target_permit:PermitEvidence|None; target_plan:ActionPlan|None
    target_before_snapshot:StateSnapshot|None; target_after_snapshot:StateSnapshot|None; target_verify:VerifyEvidence|None; target_rollback:RollbackEvidence|None; target_policy:TransactionPolicy|None
    binding:str; state_epoch:str
@dataclass(frozen=True)
class TransactionSyncPlan:
    missing_or_changed_step_ids:tuple[str,...]; metadata_bytes_required:int; full_resend_required:bool

def _cv(x):
    if isinstance(x,Enum): return x.value
    if hasattr(x,'__dataclass_fields__'): return {k:_cv(getattr(x,k)) for k in x.__dataclass_fields__}
    if isinstance(x,tuple): return [_cv(v) for v in x]
    if isinstance(x,list): return [_cv(v) for v in x]
    if isinstance(x,dict): return {str(k):_cv(x[k]) for k in sorted(x)}
    return x
def _canon(x)->bytes: return json.dumps(_cv(x),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def _fp(x)->str: return sha256(_canon(x)).hexdigest()
def _hold(reason:str, applied=(), failed=None, rollback=False, state=TransactionState.HOLD, rollback_verified=False, incident=False, rollback_result='NOT_REQUIRED'):
    trail=(reason,)
    return TransactionResult(Decision.HOLD,state,(reason,),tuple(applied),failed,False,rollback,rollback_verified,incident,'NOT_COMMITTED',rollback_result,trail,False)

def _validate_common(request,intent,permit,plan,before_snapshot,after_snapshot,steps,verify,rollback,policy):
    if policy.revoked: return 'POLICY_REVOKED'
    ids=(request.transaction_id,intent.transaction_id,permit.transaction_id,plan.transaction_id,before_snapshot.transaction_id,after_snapshot.transaction_id,verify.transaction_id,rollback.transaction_id)
    if len(set(ids))!=1: return 'TRANSACTION_ID_MISMATCH'
    b=policy.binding; e=policy.state_epoch
    objs=(request,intent,permit,plan,before_snapshot,after_snapshot,verify,rollback)
    if any(x.binding!=b for x in objs): return 'BINDING_MISMATCH'
    if any(x.state_epoch!=e for x in objs): return 'STATE_EPOCH_MISMATCH'
    if any(x.transaction_id!=plan.transaction_id or x.binding!=b or x.state_epoch!=e for x in steps): return 'STEP_SCOPE_MISMATCH'
    if len({a.action_id for a in plan.actions})!=len(plan.actions): return 'DUPLICATE_ACTION_ID'
    if len({a.order for a in plan.actions})!=len(plan.actions): return 'DUPLICATE_ACTION_ORDER'
    orders=tuple(sorted(a.order for a in plan.actions))
    if orders and orders!=tuple(range(len(orders))): return 'NONCONTIGUOUS_ACTION_ORDER'
    if len({x.evidence_id for x in steps})!=len(steps): return 'DUPLICATE_STEP_EVIDENCE_ID'
    return None

def evaluate(request:TransactionRequest,intent:IntentEvidence,permit:PermitEvidence,plan:ActionPlan,before_snapshot:StateSnapshot,after_snapshot:StateSnapshot,steps:tuple[StepEvidence,...],verify:VerifyEvidence,rollback:RollbackEvidence,policy:TransactionPolicy)->TransactionResult:
    err=_validate_common(request,intent,permit,plan,before_snapshot,after_snapshot,steps,verify,rollback,policy)
    if err: return _hold(err)
    if not request.observed: return _hold('REQUEST_UNOBSERVED')
    if not intent.observed: return _hold('INTENT_UNOBSERVED')
    if policy.require_permit_evidence and not permit.observed: return _hold('PERMIT_EVIDENCE_UNOBSERVED')
    if policy.require_permit_evidence and not permit.allow_candidate: return _hold('PERMIT_CANDIDATE_NOT_ALLOWED')
    if not before_snapshot.observed: return _hold('BEFORE_SNAPSHOT_UNOBSERVED')
    if not plan.actions: return _hold('EMPTY_ACTION_PLAN')
    by_action={}
    for ev in steps:
        by_action.setdefault(ev.action_id,[]).append(ev)
    applied=[]; trail=['BEGIN_SNAPSHOT_OBSERVED']
    for action in sorted(plan.actions,key=lambda x:(x.order,x.action_id)):
        candidates=by_action.get(action.action_id,[])
        if len(candidates)!=1:
            return _hold('STEP_EVIDENCE_MISSING_OR_AMBIGUOUS',applied,action.action_id,bool(applied),TransactionState.ROLLBACK_REQUIRED if applied else TransactionState.HOLD,rollback_result='REQUIRED' if applied else 'NOT_REQUIRED')
        ev=candidates[0]
        if not ev.observed:
            return _hold('STEP_EVIDENCE_UNOBSERVED',applied,action.action_id,True,TransactionState.ROLLBACK_REQUIRED,rollback_result='REQUIRED')
        if not ev.before_fingerprint:
            return _hold('STEP_BEFORE_FINGERPRINT_MISSING',applied,action.action_id,True,TransactionState.ROLLBACK_REQUIRED,rollback_result='REQUIRED')
        if ev.status==StepStatus.APPLIED:
            if not ev.after_fingerprint:
                return _hold('STEP_AFTER_FINGERPRINT_MISSING',applied,action.action_id,True,TransactionState.ROLLBACK_REQUIRED,rollback_result='REQUIRED')
            applied.append(action.action_id); trail.append('APPLIED:'+action.action_id); continue
        reason={StepStatus.FAILED:'STEP_FAILED',StepStatus.TIMEOUT:'STEP_TIMEOUT',StepStatus.EXCEPTION:'STEP_EXCEPTION'}[ev.status]
        rb=True
        # rollback evidence can close the rollback branch, but never becomes rollback execution by this module
        if rollback.observed:
            if rollback.status==RollbackStatus.SUCCEEDED and rollback.restored_state_fingerprint==before_snapshot.state_fingerprint and rollback.snapshot_state_fingerprint==before_snapshot.state_fingerprint:
                return TransactionResult(Decision.HOLD,TransactionState.ROLLBACK_VERIFIED,(reason,'ROLLBACK_EVIDENCE_VERIFIED'),tuple(applied),action.action_id,False,True,True,False,'NOT_COMMITTED','VERIFIED_SUCCESS',tuple(trail+[reason,'ROLLBACK_EVIDENCE_VERIFIED']),False)
            if rollback.status in (RollbackStatus.FAILED,RollbackStatus.TIMEOUT) or (rollback.status==RollbackStatus.SUCCEEDED and rollback.restored_state_fingerprint!=before_snapshot.state_fingerprint):
                return TransactionResult(Decision.HOLD,TransactionState.INCIDENT_HOLD,(reason,'ROLLBACK_FAILED_OR_UNVERIFIED'),tuple(applied),action.action_id,False,True,False,True,'NOT_COMMITTED','FAILED',tuple(trail+[reason,'ROLLBACK_FAILED_OR_UNVERIFIED']),False)
        return _hold(reason,applied,action.action_id,rb,TransactionState.ROLLBACK_REQUIRED,rollback_result='REQUIRED')
    trail.append('ALL_STEP_EVIDENCE_APPLIED')
    if not after_snapshot.observed:
        return _hold('AFTER_SNAPSHOT_UNOBSERVED',applied,None,True,TransactionState.ROLLBACK_REQUIRED,rollback_result='REQUIRED')
    if not verify.observed or verify.status==VerifyStatus.UNOBSERVED:
        return _hold('VERIFY_EVIDENCE_UNOBSERVED',applied,None,True,TransactionState.ROLLBACK_REQUIRED,rollback_result='REQUIRED')
    if verify.status!=VerifyStatus.MATCH:
        reason={VerifyStatus.MISMATCH:'VERIFY_MISMATCH',VerifyStatus.TIMEOUT:'VERIFY_TIMEOUT',VerifyStatus.EXCEPTION:'VERIFY_EXCEPTION'}[verify.status]
        if rollback.observed:
            if rollback.status==RollbackStatus.SUCCEEDED and rollback.restored_state_fingerprint==before_snapshot.state_fingerprint and rollback.snapshot_state_fingerprint==before_snapshot.state_fingerprint:
                return TransactionResult(Decision.HOLD,TransactionState.ROLLBACK_VERIFIED,(reason,'ROLLBACK_EVIDENCE_VERIFIED'),tuple(applied),None,False,True,True,False,'NOT_COMMITTED','VERIFIED_SUCCESS',tuple(trail+[reason,'ROLLBACK_EVIDENCE_VERIFIED']),False)
            if rollback.status in (RollbackStatus.FAILED,RollbackStatus.TIMEOUT) or (rollback.status==RollbackStatus.SUCCEEDED and rollback.restored_state_fingerprint!=before_snapshot.state_fingerprint):
                return TransactionResult(Decision.HOLD,TransactionState.INCIDENT_HOLD,(reason,'ROLLBACK_FAILED_OR_UNVERIFIED'),tuple(applied),None,False,True,False,True,'NOT_COMMITTED','FAILED',tuple(trail+[reason,'ROLLBACK_FAILED_OR_UNVERIFIED']),False)
        return _hold(reason,applied,None,True,TransactionState.ROLLBACK_REQUIRED,rollback_result='REQUIRED')
    if not verify.final_state_fingerprint or verify.final_state_fingerprint!=verify.expected_final_state_fingerprint:
        return _hold('VERIFY_FINGERPRINT_MISMATCH',applied,None,True,TransactionState.ROLLBACK_REQUIRED,rollback_result='REQUIRED')
    if after_snapshot.state_fingerprint!=verify.final_state_fingerprint:
        return _hold('AFTER_SNAPSHOT_VERIFY_MISMATCH',applied,None,True,TransactionState.ROLLBACK_REQUIRED,rollback_result='REQUIRED')
    trail.extend(('VERIFY_MATCH','COMMIT_CANDIDATE_ONLY'))
    return TransactionResult(Decision.ALLOW,TransactionState.COMMIT_CANDIDATE,('ALL_STEPS_AND_VERIFY_SATISFIED',),tuple(applied),None,True,False,False,False,'CANDIDATE_ONLY','NOT_REQUIRED',tuple(trail),True)

def default_policy(): return TransactionPolicy(True,'TX-BIND','STATE-EPOCH-1')
def default_request(): return TransactionRequest('REQ-1','TX-1',True,'TX-BIND','STATE-EPOCH-1')
def default_intent(): return IntentEvidence('INT-1','TX-1',True,'TX-BIND','STATE-EPOCH-1')
def default_permit(): return PermitEvidence('PERMIT-1','TX-1',True,True,'TX-BIND','STATE-EPOCH-1')
def default_plan(): return ActionPlan('TX-1',(ActionSpec('A1',0),ActionSpec('A2',1)),'TX-BIND','STATE-EPOCH-1')
def default_before(): return StateSnapshot('SNAP-B','TX-1','STATE-BEFORE',True,'TX-BIND','STATE-EPOCH-1')
def default_after(): return StateSnapshot('SNAP-A','TX-1','STATE-AFTER',True,'TX-BIND','STATE-EPOCH-1')
def default_steps():
    b,e='TX-BIND','STATE-EPOCH-1'
    return (StepEvidence('S1','TX-1','A1',True,StepStatus.APPLIED,'STATE-BEFORE','STATE-MID',b,e),StepEvidence('S2','TX-1','A2',True,StepStatus.APPLIED,'STATE-MID','STATE-AFTER',b,e))
def default_verify(): return VerifyEvidence('V1','TX-1',True,VerifyStatus.MATCH,'STATE-AFTER','STATE-AFTER','TX-BIND','STATE-EPOCH-1')
def default_rollback(): return RollbackEvidence('RB1','TX-1',False,RollbackStatus.NOT_OBSERVED,'','STATE-BEFORE','TX-BIND','STATE-EPOCH-1')

def _registry_fp(request,intent,permit,plan,before_snapshot,after_snapshot,steps,verify,rollback,policy):
    return _fp({'request':request,'intent':intent,'permit':permit,'plan':plan,'before':before_snapshot,'after':after_snapshot,'steps':sorted((x.evidence_id,_fp(x)) for x in steps),'verify':verify,'rollback':rollback,'policy':policy})
def prepare_state(request,intent,permit,plan,before_snapshot,after_snapshot,steps,verify,rollback,policy,*,binding:str,state_epoch:str):
    if binding!=policy.binding or state_epoch!=policy.state_epoch: raise ValueError('PREPARED_BINDING_OR_EPOCH_MISMATCH')
    steps=tuple(sorted(steps,key=lambda x:x.evidence_id))
    sf=tuple((x.evidence_id,_fp(x)) for x in steps)
    context=_fp({'request':request,'intent':intent,'permit':permit,'plan':plan,'before':before_snapshot,'after':after_snapshot,'verify':verify,'rollback':rollback,'policy':policy})
    dep=_fp({'steps':sf})
    reg=_registry_fp(request,intent,permit,plan,before_snapshot,after_snapshot,steps,verify,rollback,policy)
    result=evaluate(request,intent,permit,plan,before_snapshot,after_snapshot,steps,verify,rollback,policy)
    return PreparedTransactionState(request,intent,permit,plan,before_snapshot,after_snapshot,steps,verify,rollback,policy,sf,context,dep,reg,result,binding,state_epoch)
def validate_prepared_integrity(st):
    if st.binding!=st.policy.binding or st.state_epoch!=st.policy.state_epoch: return False
    if st.step_fingerprints!=tuple(sorted((x.evidence_id,_fp(x)) for x in st.steps)): return False
    c=_fp({'request':st.request,'intent':st.intent,'permit':st.permit,'plan':st.plan,'before':st.before_snapshot,'after':st.after_snapshot,'verify':st.verify,'rollback':st.rollback,'policy':st.policy})
    if c!=st.context_fingerprint or _fp({'steps':st.step_fingerprints})!=st.dependency_fingerprint: return False
    if st.registry_fingerprint!=_registry_fp(st.request,st.intent,st.permit,st.plan,st.before_snapshot,st.after_snapshot,st.steps,st.verify,st.rollback,st.policy): return False
    return st.precomputed_result==evaluate(st.request,st.intent,st.permit,st.plan,st.before_snapshot,st.after_snapshot,st.steps,st.verify,st.rollback,st.policy)
def evaluate_prepared(st,*,current_context_fingerprint,current_dependency_fingerprint,current_registry_fingerprint,prepared_integrity_validated):
    if not prepared_integrity_validated: return _hold('PREPARED_INTEGRITY_UNVERIFIED')
    if (current_context_fingerprint,current_dependency_fingerprint,current_registry_fingerprint)!=(st.context_fingerprint,st.dependency_fingerprint,st.registry_fingerprint): return _hold('PREPARED_STATE_STALE')
    return st.precomputed_result
def make_delta(base,target):
    bs={x.evidence_id:x for x in base.steps}; ts={x.evidence_id:x for x in target.steps}
    changed=tuple(ts[k] for k in sorted(ts) if k not in bs or _fp(ts[k])!=_fp(bs[k])); removed=tuple(sorted(set(bs)-set(ts)))
    pick=lambda a,b: b if _fp(a)!=_fp(b) else None
    return TransactionStateDelta(base.registry_fingerprint,target.registry_fingerprint,changed,removed,pick(base.request,target.request),pick(base.intent,target.intent),pick(base.permit,target.permit),pick(base.plan,target.plan),pick(base.before_snapshot,target.before_snapshot),pick(base.after_snapshot,target.after_snapshot),pick(base.verify,target.verify),pick(base.rollback,target.rollback),pick(base.policy,target.policy),target.binding,target.state_epoch)
def apply_delta(base,delta):
    if base.registry_fingerprint!=delta.base_fingerprint: raise ValueError('DELTA_BASE_MISMATCH')
    steps={x.evidence_id:x for x in base.steps}
    for k in delta.removed_evidence_ids: steps.pop(k,None)
    for x in delta.changed_steps: steps[x.evidence_id]=x
    request=delta.target_request or base.request; intent=delta.target_intent or base.intent; permit=delta.target_permit or base.permit; plan=delta.target_plan or base.plan
    before=delta.target_before_snapshot or base.before_snapshot; after=delta.target_after_snapshot or base.after_snapshot; verify=delta.target_verify or base.verify; rollback=delta.target_rollback or base.rollback; policy=delta.target_policy or base.policy
    st=prepare_state(request,intent,permit,plan,before,after,tuple(steps[k] for k in sorted(steps)),verify,rollback,policy,binding=delta.binding,state_epoch=delta.state_epoch)
    if st.registry_fingerprint!=delta.target_fingerprint: raise ValueError('DELTA_TARGET_MISMATCH')
    return st
def missing_only_sync_plan(target,known_step_fps):
    missing=tuple(k for k,v in target.step_fingerprints if known_step_fps.get(k)!=v)
    meta=len(_canon({'steps':missing,'context':target.context_fingerprint,'dependency':target.dependency_fingerprint}))
    return TransactionSyncPlan(missing,meta,len(missing)>=max(1,len(target.step_fingerprints)))
def full_registry_bytes(st): return len(_canon({'request':st.request,'intent':st.intent,'permit':st.permit,'plan':st.plan,'before':st.before_snapshot,'after':st.after_snapshot,'steps':st.steps,'verify':st.verify,'rollback':st.rollback,'policy':st.policy,'context':st.context_fingerprint,'dependency':st.dependency_fingerprint}))
def delta_bytes(delta): return len(_canon(delta))
def default_evaluation(): return evaluate(default_request(),default_intent(),default_permit(),default_plan(),default_before(),default_after(),default_steps(),default_verify(),default_rollback(),default_policy())
