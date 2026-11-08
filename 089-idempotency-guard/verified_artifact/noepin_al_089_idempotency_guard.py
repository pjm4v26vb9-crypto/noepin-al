"""NOEPIN AL 089 — Idempotency Guard — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Pure idempotency decision algorithm. It compares an Intent fingerprint, Action,
Idempotency Key and observed Execution History to classify a request as NEW,
REPLAY, DUPLICATE_SUSPECTED or HOLD and emits a safe retry method. It does not
mutate an idempotency/history store, consume/register a key, execute an Action,
grant permission, commit/publish state, promote a receipt to Truth, prove World
Truth/Safety, or establish Action Success.

Canonical identity: NOEPIN-AL-089
DCSR level: DIRECT INTEGRATION / 直接統合.
Provenance note: exact registered Origin GUID was not freshly reverified in this
completion session and is intentionally not guessed or regenerated.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json

class Decision(str, Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class RiskLevel(str, Enum):
    LOW='LOW'; MEDIUM='MEDIUM'; HIGH='HIGH'; CRITICAL='CRITICAL'
class ExecutionStatus(str, Enum):
    SUCCESS='SUCCESS'; FAILED='FAILED'; IN_FLIGHT='IN_FLIGHT'; UNKNOWN='UNKNOWN'
class IdempotencyState(str, Enum):
    NEW='NEW'; REPLAY='REPLAY'; DUPLICATE='DUPLICATE'; READ_RETRY='READ_RETRY'; KEY_CONFLICT='KEY_CONFLICT'; HOLD='HOLD'
class SafeRetryMethod(str, Enum):
    NEW_EXECUTION_CANDIDATE='NEW_EXECUTION_CANDIDATE'; REUSE_PREVIOUS_RESULT='REUSE_PREVIOUS_RESULT'; SAME_KEY_RETRY='SAME_KEY_RETRY'; READ_RETRY='READ_RETRY'; REQUEST_IDEMPOTENCY_KEY='REQUEST_IDEMPOTENCY_KEY'; NO_RETRY='NO_RETRY'

@dataclass(frozen=True)
class IdempotencyRequest:
    request_id:str; intent_fingerprint:str; action_id:str; action_fingerprint:str; idempotency_key:str
    side_effecting:bool; risk:RiskLevel; history_store_available:bool; history_complete:bool
    observed:bool; binding:str; state_epoch:str

@dataclass(frozen=True)
class ExecutionHistoryRecord:
    record_id:str; idempotency_key:str; intent_fingerprint:str; action_fingerprint:str
    status:ExecutionStatus; result_fingerprint:str; observed:bool; binding:str; state_epoch:str

@dataclass(frozen=True)
class IdempotencyPolicy:
    require_key_for_side_effects:bool; allow_retry_after_failed_same_key:bool
    duplicate_success_blocks:bool; binding:str; state_epoch:str; revoked:bool=False

@dataclass(frozen=True)
class IdempotencyResult:
    decision:Decision; idempotency_state:IdempotencyState; reasons:tuple[str,...]
    safe_retry_method:SafeRetryMethod; matched_record_ids:tuple[str,...]
    duplicate_record_ids:tuple[str,...]; prior_result_fingerprint:str
    generated_key_candidate:str; next_gate_candidate:bool
    history_registration_candidate:bool; result_reuse_candidate:bool; retry_candidate:bool
    request_promoted_to_success:bool=False; history_store_mutated:bool=False; key_registered:bool=False
    permission_granted:bool=False; action_executed:bool=False; plan_committed:bool=False
    atomic_publish_executed:bool=False; external_write_performed:bool=False
    receipt_promoted_to_truth:bool=False; world_truth_proven:bool=False
    safety_proven:bool=False; action_success:bool=False

@dataclass(frozen=True)
class PreparedIdempotencyState:
    request:IdempotencyRequest; histories:tuple[ExecutionHistoryRecord,...]; policy:IdempotencyPolicy
    history_fingerprints:tuple[tuple[str,str],...]
    context_fingerprint:str; dependency_fingerprint:str; policy_fingerprint:str; registry_fingerprint:str
    precomputed_result:IdempotencyResult; binding:str; state_epoch:str

@dataclass(frozen=True)
class IdempotencyStateDelta:
    base_fingerprint:str; target_fingerprint:str
    changed_histories:tuple[ExecutionHistoryRecord,...]; removed_record_ids:tuple[str,...]
    target_request:IdempotencyRequest|None; target_policy:IdempotencyPolicy|None
    binding:str; state_epoch:str

@dataclass(frozen=True)
class IdempotencySyncPlan:
    missing_or_changed_record_ids:tuple[str,...]; metadata_bytes_required:int; full_resend_required:bool

def _cv(x):
    if isinstance(x,Enum): return x.value
    if hasattr(x,'__dataclass_fields__'): return {k:_cv(getattr(x,k)) for k in x.__dataclass_fields__}
    if isinstance(x,tuple): return [_cv(v) for v in x]
    if isinstance(x,list): return [_cv(v) for v in x]
    if isinstance(x,dict): return {str(k):_cv(x[k]) for k in sorted(x)}
    return x

def _canon(x)->bytes:
    return json.dumps(_cv(x),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def _fp(x)->str: return sha256(_canon(x)).hexdigest()

def _generated_key(req:IdempotencyRequest)->str:
    return 'IDEM-' + sha256(f'{req.intent_fingerprint}|{req.action_fingerprint}|{req.binding}|{req.state_epoch}'.encode()).hexdigest()[:24]

def _hold(reason:str, *, state=IdempotencyState.HOLD, matched=(), dup=(), key=''):
    return IdempotencyResult(Decision.HOLD,state,(reason,),SafeRetryMethod.NO_RETRY,tuple(matched),tuple(dup),'',key,False,False,False,False)

def _validate(req,histories,policy):
    if policy.revoked: return 'POLICY_REVOKED'
    if req.binding!=policy.binding or req.state_epoch!=policy.state_epoch: return 'REQUEST_SCOPE_MISMATCH'
    if not req.request_id or not req.intent_fingerprint or not req.action_id or not req.action_fingerprint: return 'INCOMPLETE_REQUEST_IDENTITY'
    if len({h.record_id for h in histories})!=len(histories): return 'DUPLICATE_HISTORY_RECORD_ID'
    for h in histories:
        if h.binding!=policy.binding or h.state_epoch!=policy.state_epoch: return 'HISTORY_SCOPE_MISMATCH'
        if not h.record_id or not h.idempotency_key or not h.intent_fingerprint or not h.action_fingerprint: return 'INCOMPLETE_HISTORY_IDENTITY'
    return None

def evaluate(req:IdempotencyRequest,histories:tuple[ExecutionHistoryRecord,...],policy:IdempotencyPolicy)->IdempotencyResult:
    err=_validate(req,histories,policy)
    if err: return _hold(err)
    if not req.observed: return _hold('REQUEST_UNOBSERVED')
    ordered=tuple(sorted(histories,key=lambda x:x.record_id))
    # Side-effect-free reads are retryable without relying on history authority.
    if not req.side_effecting:
        return IdempotencyResult(Decision.ALLOW,IdempotencyState.READ_RETRY,('SIDE_EFFECT_FREE_READ',),SafeRetryMethod.READ_RETRY,(),(),'','',True,False,False,True)
    if not req.history_store_available:
        return _hold('HISTORY_STORE_UNAVAILABLE')
    if not req.history_complete:
        return _hold('HISTORY_INCOMPLETE')
    if policy.require_key_for_side_effects and not req.idempotency_key:
        return IdempotencyResult(Decision.HOLD,IdempotencyState.HOLD,('IDEMPOTENCY_KEY_REQUIRED',),SafeRetryMethod.REQUEST_IDEMPOTENCY_KEY,(),(),'',_generated_key(req),False,False,False,False)
    key_matches=tuple(h for h in ordered if h.idempotency_key==req.idempotency_key and h.observed)
    key_unobserved=tuple(h for h in ordered if h.idempotency_key==req.idempotency_key and not h.observed)
    if key_unobserved:
        return _hold('MATCHING_KEY_HISTORY_UNOBSERVED',matched=tuple(h.record_id for h in key_unobserved))
    conflicting=tuple(h for h in key_matches if h.intent_fingerprint!=req.intent_fingerprint or h.action_fingerprint!=req.action_fingerprint)
    if conflicting:
        return IdempotencyResult(Decision.DENY,IdempotencyState.KEY_CONFLICT,('IDEMPOTENCY_KEY_CONFLICT',),SafeRetryMethod.NO_RETRY,tuple(h.record_id for h in key_matches),tuple(h.record_id for h in conflicting),'','',False,False,False,False)
    success=tuple(h for h in key_matches if h.status==ExecutionStatus.SUCCESS)
    if success:
        prior=next((h.result_fingerprint for h in success if h.result_fingerprint),'')
        return IdempotencyResult(Decision.DENY,IdempotencyState.REPLAY,('SAME_KEY_SUCCESS_ALREADY_RECORDED',),SafeRetryMethod.REUSE_PREVIOUS_RESULT,tuple(h.record_id for h in success),(),prior,'',False,False,bool(prior),False)
    inflight=tuple(h for h in key_matches if h.status==ExecutionStatus.IN_FLIGHT)
    if inflight:
        return _hold('SAME_KEY_IN_FLIGHT',state=IdempotencyState.REPLAY,matched=tuple(h.record_id for h in inflight))
    unknown=tuple(h for h in key_matches if h.status==ExecutionStatus.UNKNOWN)
    if unknown:
        return _hold('SAME_KEY_HISTORY_UNKNOWN',state=IdempotencyState.REPLAY,matched=tuple(h.record_id for h in unknown))
    failed=tuple(h for h in key_matches if h.status==ExecutionStatus.FAILED)
    if failed:
        if policy.allow_retry_after_failed_same_key:
            return IdempotencyResult(Decision.ALLOW,IdempotencyState.REPLAY,('SAME_KEY_PREVIOUS_FAILED',),SafeRetryMethod.SAME_KEY_RETRY,tuple(h.record_id for h in failed),(),'','',True,False,False,True)
        return _hold('FAILED_SAME_KEY_RETRY_DISABLED',state=IdempotencyState.REPLAY,matched=tuple(h.record_id for h in failed))
    duplicate=tuple(h for h in ordered if h.observed and h.idempotency_key!=req.idempotency_key and h.intent_fingerprint==req.intent_fingerprint and h.status in (ExecutionStatus.SUCCESS,ExecutionStatus.IN_FLIGHT,ExecutionStatus.UNKNOWN))
    if duplicate:
        return IdempotencyResult(Decision.HOLD,IdempotencyState.DUPLICATE,('SAME_INTENT_DIFFERENT_KEY_SUSPECTED',),SafeRetryMethod.NO_RETRY,(),tuple(h.record_id for h in duplicate),'','',False,False,False,False)
    return IdempotencyResult(Decision.ALLOW,IdempotencyState.NEW,('NO_DUPLICATE_HISTORY_FOUND',),SafeRetryMethod.NEW_EXECUTION_CANDIDATE,(),(),'','',True,True,False,False)

def default_policy():
    return IdempotencyPolicy(True,True,True,'IDEM-BIND','STATE-EPOCH-1')
def default_request():
    return IdempotencyRequest('REQ-1','INTENT-NEW','ACTION-SEND','ACTION-FP-SEND','KEY-NEW',True,RiskLevel.MEDIUM,True,True,True,'IDEM-BIND','STATE-EPOCH-1')
def default_histories():
    b,e='IDEM-BIND','STATE-EPOCH-1'
    return (
        ExecutionHistoryRecord('HIST-1','KEY-OLD','INTENT-OLD','ACTION-FP-OLD',ExecutionStatus.SUCCESS,'RESULT-OLD',True,b,e),
        ExecutionHistoryRecord('HIST-2','KEY-FAIL','INTENT-FAIL','ACTION-FP-FAIL',ExecutionStatus.FAILED,'',True,b,e),
    )
def default_evaluation(): return evaluate(default_request(),default_histories(),default_policy())

def _policy_fp(policy): return _fp(policy)
def _registry_fp(req,histories,policy): return _fp({'request':req,'histories':tuple(sorted(histories,key=lambda x:x.record_id)),'policy':policy})

def prepare_state(req,histories,policy,*,binding:str,state_epoch:str):
    histories=tuple(sorted(histories,key=lambda x:x.record_id))
    fps=tuple((h.record_id,_fp(h)) for h in histories)
    context=_fp({'request':req,'policy':policy})
    dependency=_fp({'history_fingerprints':fps})
    pfp=_policy_fp(policy)
    registry=_registry_fp(req,histories,policy)
    return PreparedIdempotencyState(req,histories,policy,fps,context,dependency,pfp,registry,evaluate(req,histories,policy),binding,state_epoch)

def validate_prepared_integrity(st):
    if st.binding!=st.policy.binding or st.state_epoch!=st.policy.state_epoch: return False
    if st.histories!=tuple(sorted(st.histories,key=lambda x:x.record_id)): return False
    if st.history_fingerprints!=tuple((h.record_id,_fp(h)) for h in st.histories): return False
    if st.context_fingerprint!=_fp({'request':st.request,'policy':st.policy}): return False
    if st.dependency_fingerprint!=_fp({'history_fingerprints':st.history_fingerprints}): return False
    if st.policy_fingerprint!=_policy_fp(st.policy): return False
    if st.registry_fingerprint!=_registry_fp(st.request,st.histories,st.policy): return False
    return st.precomputed_result==evaluate(st.request,st.histories,st.policy)

def evaluate_prepared(st,*,current_context_fingerprint,current_dependency_fingerprint,current_policy_fingerprint,current_registry_fingerprint,prepared_integrity_validated):
    if not prepared_integrity_validated: return _hold('PREPARED_INTEGRITY_UNVERIFIED')
    current=(current_context_fingerprint,current_dependency_fingerprint,current_policy_fingerprint,current_registry_fingerprint)
    expected=(st.context_fingerprint,st.dependency_fingerprint,st.policy_fingerprint,st.registry_fingerprint)
    if current!=expected: return _hold('PREPARED_HISTORY_CHANGED_REEVALUATION_REQUIRED')
    return st.precomputed_result

def make_delta(base,target):
    if base.binding!=target.binding or base.state_epoch!=target.state_epoch: raise ValueError('DELTA_SCOPE_MISMATCH')
    bm={h.record_id:h for h in base.histories}; tm={h.record_id:h for h in target.histories}
    changed=tuple(tm[k] for k in sorted(tm) if k not in bm or _fp(tm[k])!=_fp(bm[k]))
    removed=tuple(k for k in sorted(bm) if k not in tm)
    tr=target.request if _fp(base.request)!=_fp(target.request) else None
    tp=target.policy if _fp(base.policy)!=_fp(target.policy) else None
    return IdempotencyStateDelta(base.registry_fingerprint,target.registry_fingerprint,changed,removed,tr,tp,base.binding,base.state_epoch)

def apply_delta(base,delta):
    if delta.base_fingerprint!=base.registry_fingerprint: raise ValueError('DELTA_BASE_FINGERPRINT_MISMATCH')
    if delta.binding!=base.binding or delta.state_epoch!=base.state_epoch: raise ValueError('DELTA_SCOPE_MISMATCH')
    hm={h.record_id:h for h in base.histories}
    for k in delta.removed_record_ids: hm.pop(k,None)
    for h in delta.changed_histories: hm[h.record_id]=h
    st=prepare_state(delta.target_request or base.request,tuple(hm.values()),delta.target_policy or base.policy,binding=base.binding,state_epoch=base.state_epoch)
    if st.registry_fingerprint!=delta.target_fingerprint: raise ValueError('DELTA_TARGET_FINGERPRINT_MISMATCH')
    return st

def missing_only_sync_plan(target,known_history_fingerprints:dict[str,str]):
    missing=tuple(k for k,v in target.history_fingerprints if known_history_fingerprints.get(k)!=v)
    meta={'record_ids':missing,'target':target.registry_fingerprint}
    return IdempotencySyncPlan(missing,len(_canon(meta)),False)

def full_registry_bytes(st): return len(_canon({'request':st.request,'histories':st.histories,'policy':st.policy}))
def delta_bytes(delta): return len(_canon(delta))
