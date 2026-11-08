"""NOEPIN AL 087 — Permit Lease Manager — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Pure permit-lease validation algorithm. It evaluates typed Permit lease evidence,
TTL, usage limits, nonce-store evidence, State/Scope fingerprints and clock-skew
policy. It returns consume/reissue/gate candidates only. It does not grant
permission, mutate a nonce store, consume a permit, execute an action, commit or
publish state, prove World Truth/Safety, or establish Action Success.

Canonical identity: NOEPIN-AL-087
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
class LeaseState(str, Enum):
    ACTIVE='ACTIVE'; EXPIRED='EXPIRED'; EXHAUSTED='EXHAUSTED'; INVALID='INVALID'; STATE_MISMATCH='STATE_MISMATCH'; REPLAY='REPLAY'; HOLD='HOLD'
class ConsumeState(str, Enum):
    CONSUME_CANDIDATE='CONSUME_CANDIDATE'; DENIED='DENIED'; HOLD='HOLD'

@dataclass(frozen=True)
class PermitLease:
    permit_id:str; issued_at:float; ttl_seconds:float; max_usage_count:int; usage_count:int
    permit_nonce:str; state_fingerprint:str; scope_fingerprint:str
    signature_verified:bool; observed:bool; binding:str; state_epoch:str

@dataclass(frozen=True)
class ConsumeRequest:
    request_id:str; permit_id:str; now:float; attempt_nonce:str
    current_state_fingerprint:str; current_scope_fingerprint:str; expected_usage_count:int
    observed:bool; binding:str; state_epoch:str

@dataclass(frozen=True)
class NonceLeaseRecord:
    permit_nonce:str; permit_id:str; active:bool; usage_count:int; seen_attempt_nonces:tuple[str,...]
    observed:bool; binding:str; state_epoch:str

@dataclass(frozen=True)
class LeasePolicy:
    max_clock_skew_seconds:float; require_signature_verified:bool; require_nonce_store:bool
    binding:str; state_epoch:str; revoked:bool=False

@dataclass(frozen=True)
class LeaseResult:
    decision:Decision; lease_state:LeaseState; reasons:tuple[str,...]
    remaining_ttl:float; consume_state:ConsumeState; next_usage_count:int|None
    consume_candidate:bool; next_gate_candidate:bool; reissue_required:bool; replay_detected:bool
    request_promoted_to_success:bool=False; permit_promoted_to_permission:bool=False
    nonce_store_mutated:bool=False; usage_consumed:bool=False; permission_granted:bool=False
    action_executed:bool=False; plan_committed:bool=False; atomic_publish_executed:bool=False
    external_write_performed:bool=False; receipt_promoted_to_truth:bool=False
    world_truth_proven:bool=False; safety_proven:bool=False; action_success:bool=False

@dataclass(frozen=True)
class PreparedPermitLeaseState:
    request:ConsumeRequest; permits:tuple[PermitLease,...]; nonce_records:tuple[NonceLeaseRecord,...]; policy:LeasePolicy
    permit_fingerprints:tuple[tuple[str,str],...]; nonce_fingerprints:tuple[tuple[str,str],...]
    context_fingerprint:str; dependency_fingerprint:str; registry_fingerprint:str
    precomputed_result:LeaseResult; binding:str; state_epoch:str

@dataclass(frozen=True)
class PermitLeaseStateDelta:
    base_fingerprint:str; target_fingerprint:str
    changed_permits:tuple[PermitLease,...]; removed_permit_ids:tuple[str,...]
    changed_nonce_records:tuple[NonceLeaseRecord,...]; removed_nonce_ids:tuple[str,...]
    target_request:ConsumeRequest|None; target_policy:LeasePolicy|None
    binding:str; state_epoch:str

@dataclass(frozen=True)
class PermitLeaseSyncPlan:
    missing_or_changed_permit_ids:tuple[str,...]
    missing_or_changed_nonce_ids:tuple[str,...]
    metadata_bytes_required:int; full_resend_required:bool

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

def _result(decision,state,reason,remaining=0.0,consume=ConsumeState.HOLD,next_usage=None,consume_candidate=False,next_gate=False,reissue=False,replay=False):
    return LeaseResult(decision,state,(reason,),max(0.0,float(remaining)),consume,next_usage,consume_candidate,next_gate,reissue,replay)

def _validate_common(request,permits,nonce_records,policy):
    if policy.revoked: return 'POLICY_REVOKED'
    if policy.max_clock_skew_seconds < 0: return 'INVALID_CLOCK_SKEW_POLICY'
    if request.binding!=policy.binding or request.state_epoch!=policy.state_epoch: return 'REQUEST_SCOPE_MISMATCH'
    if any(x.binding!=policy.binding or x.state_epoch!=policy.state_epoch for x in permits): return 'PERMIT_SCOPE_MISMATCH'
    if any(x.binding!=policy.binding or x.state_epoch!=policy.state_epoch for x in nonce_records): return 'NONCE_STORE_SCOPE_MISMATCH'
    if len({x.permit_id for x in permits})!=len(permits): return 'DUPLICATE_PERMIT_ID'
    if len({x.permit_nonce for x in nonce_records})!=len(nonce_records): return 'DUPLICATE_NONCE_RECORD'
    for p in permits:
        if p.ttl_seconds<=0: return 'INVALID_TTL'
        if p.max_usage_count<=0: return 'INVALID_MAX_USAGE_COUNT'
        if p.usage_count<0 or p.usage_count>p.max_usage_count: return 'INVALID_USAGE_COUNT'
        if not p.permit_nonce: return 'EMPTY_PERMIT_NONCE'
        if not p.state_fingerprint or not p.scope_fingerprint: return 'EMPTY_PERMIT_FINGERPRINT'
    for n in nonce_records:
        if n.usage_count<0: return 'INVALID_NONCE_USAGE_COUNT'
        if not n.permit_nonce or not n.permit_id: return 'INVALID_NONCE_RECORD'
        if len(set(n.seen_attempt_nonces))!=len(n.seen_attempt_nonces): return 'DUPLICATE_SEEN_ATTEMPT_NONCE'
    if not request.request_id or not request.attempt_nonce: return 'INVALID_CONSUME_REQUEST'
    if request.expected_usage_count<0: return 'INVALID_EXPECTED_USAGE_COUNT'
    return None

def evaluate(request:ConsumeRequest,permits:tuple[PermitLease,...],nonce_records:tuple[NonceLeaseRecord,...],policy:LeasePolicy)->LeaseResult:
    err=_validate_common(request,permits,nonce_records,policy)
    if err: return _result(Decision.HOLD,LeaseState.HOLD,err)
    if not request.observed: return _result(Decision.HOLD,LeaseState.HOLD,'REQUEST_UNOBSERVED')
    permit_map={p.permit_id:p for p in permits}
    permit=permit_map.get(request.permit_id)
    if permit is None: return _result(Decision.DENY,LeaseState.INVALID,'PERMIT_NOT_FOUND',consume=ConsumeState.DENIED)
    if not permit.observed: return _result(Decision.DENY,LeaseState.INVALID,'PERMIT_UNOBSERVED',consume=ConsumeState.DENIED)
    if policy.require_signature_verified and not permit.signature_verified:
        return _result(Decision.DENY,LeaseState.INVALID,'SIGNATURE_UNVERIFIED',consume=ConsumeState.DENIED)
    nonce_map={n.permit_nonce:n for n in nonce_records}
    nonce=nonce_map.get(permit.permit_nonce)
    if policy.require_nonce_store:
        if nonce is None: return _result(Decision.DENY,LeaseState.INVALID,'NONCE_NOT_IN_ACTIVE_STORE',consume=ConsumeState.DENIED)
        if not nonce.observed: return _result(Decision.DENY,LeaseState.INVALID,'NONCE_STORE_UNOBSERVED',consume=ConsumeState.DENIED)
        if nonce.permit_id!=permit.permit_id: return _result(Decision.DENY,LeaseState.INVALID,'NONCE_PERMIT_MISMATCH',consume=ConsumeState.DENIED)
        if not nonce.active: return _result(Decision.DENY,LeaseState.REPLAY,'NONCE_INACTIVE_OR_REPLAYED',consume=ConsumeState.DENIED,replay=True)
        if nonce.usage_count!=permit.usage_count: return _result(Decision.HOLD,LeaseState.HOLD,'NONCE_USAGE_STATE_MISMATCH')
        if request.attempt_nonce in nonce.seen_attempt_nonces:
            return _result(Decision.DENY,LeaseState.REPLAY,'ATTEMPT_NONCE_REPLAY',consume=ConsumeState.DENIED,replay=True)
    if request.expected_usage_count<permit.usage_count:
        return _result(Decision.DENY,LeaseState.REPLAY,'STALE_USAGE_REPLAY',consume=ConsumeState.DENIED,replay=True)
    if request.expected_usage_count>permit.usage_count:
        return _result(Decision.HOLD,LeaseState.HOLD,'EXPECTED_USAGE_AHEAD_OF_STORE')
    skew=policy.max_clock_skew_seconds
    if request.now < permit.issued_at-skew:
        return _result(Decision.HOLD,LeaseState.HOLD,'CLOCK_BEFORE_ISSUE_WINDOW')
    expiry=permit.issued_at+permit.ttl_seconds
    if request.now > expiry+skew:
        return _result(Decision.DENY,LeaseState.EXPIRED,'LEASE_EXPIRED',consume=ConsumeState.DENIED)
    if request.current_scope_fingerprint!=permit.scope_fingerprint:
        return _result(Decision.DENY,LeaseState.INVALID,'SCOPE_FINGERPRINT_MISMATCH',consume=ConsumeState.DENIED,reissue=True)
    if request.current_state_fingerprint!=permit.state_fingerprint:
        return _result(Decision.HOLD,LeaseState.STATE_MISMATCH,'STATE_FINGERPRINT_MISMATCH',reissue=True)
    if permit.usage_count>=permit.max_usage_count:
        return _result(Decision.DENY,LeaseState.EXHAUSTED,'USAGE_LIMIT_EXHAUSTED',consume=ConsumeState.DENIED)
    remaining=max(0.0,expiry-request.now)
    return LeaseResult(Decision.ALLOW,LeaseState.ACTIVE,('LEASE_VALID_CONSUME_CANDIDATE',),remaining,ConsumeState.CONSUME_CANDIDATE,permit.usage_count+1,True,True,False,False)

def default_policy(): return LeasePolicy(2.0,True,True,'LEASE-BIND','STATE-EPOCH-1')
def default_permits():
    return (PermitLease('PERMIT-1',1000.0,60.0,3,0,'PN-1','STATE-FP-1','SCOPE-FP-1',True,True,'LEASE-BIND','STATE-EPOCH-1'),)
def default_nonce_records():
    return (NonceLeaseRecord('PN-1','PERMIT-1',True,0,(),True,'LEASE-BIND','STATE-EPOCH-1'),)
def default_request(): return ConsumeRequest('REQ-1','PERMIT-1',1005.0,'ATTEMPT-1','STATE-FP-1','SCOPE-FP-1',0,True,'LEASE-BIND','STATE-EPOCH-1')
def default_evaluation(): return evaluate(default_request(),default_permits(),default_nonce_records(),default_policy())

def _registry_fp(request,permits,nonce_records,policy):
    return _fp({'request':request,'permits':sorted((x.permit_id,_fp(x)) for x in permits),'nonce_records':sorted((x.permit_nonce,_fp(x)) for x in nonce_records),'policy':policy})

def prepare_state(request,permits,nonce_records,policy,*,binding:str,state_epoch:str):
    if binding!=policy.binding or state_epoch!=policy.state_epoch: raise ValueError('PREPARED_BINDING_OR_EPOCH_MISMATCH')
    permits=tuple(sorted(permits,key=lambda x:x.permit_id)); nonce_records=tuple(sorted(nonce_records,key=lambda x:x.permit_nonce))
    pf=tuple((x.permit_id,_fp(x)) for x in permits); nf=tuple((x.permit_nonce,_fp(x)) for x in nonce_records)
    context=_fp({'request':request,'policy':policy}); dep=_fp({'permits':pf,'nonce_records':nf}); reg=_registry_fp(request,permits,nonce_records,policy)
    result=evaluate(request,permits,nonce_records,policy)
    return PreparedPermitLeaseState(request,permits,nonce_records,policy,pf,nf,context,dep,reg,result,binding,state_epoch)

def validate_prepared_integrity(st):
    if st.binding!=st.policy.binding or st.state_epoch!=st.policy.state_epoch: return False
    if st.permit_fingerprints!=tuple(sorted((x.permit_id,_fp(x)) for x in st.permits)): return False
    if st.nonce_fingerprints!=tuple(sorted((x.permit_nonce,_fp(x)) for x in st.nonce_records)): return False
    if st.context_fingerprint!=_fp({'request':st.request,'policy':st.policy}): return False
    if st.dependency_fingerprint!=_fp({'permits':st.permit_fingerprints,'nonce_records':st.nonce_fingerprints}): return False
    if st.registry_fingerprint!=_registry_fp(st.request,st.permits,st.nonce_records,st.policy): return False
    return st.precomputed_result==evaluate(st.request,st.permits,st.nonce_records,st.policy)

def evaluate_prepared(st,*,current_context_fingerprint,current_dependency_fingerprint,current_registry_fingerprint,prepared_integrity_validated):
    if not prepared_integrity_validated: return _result(Decision.HOLD,LeaseState.HOLD,'PREPARED_INTEGRITY_UNVERIFIED')
    if (current_context_fingerprint,current_dependency_fingerprint,current_registry_fingerprint)!=(st.context_fingerprint,st.dependency_fingerprint,st.registry_fingerprint):
        return _result(Decision.HOLD,LeaseState.HOLD,'PREPARED_STATE_STALE')
    return st.precomputed_result

def make_delta(base,target):
    if base.binding!=target.binding or base.state_epoch!=target.state_epoch: raise ValueError('DELTA_SCOPE_MISMATCH')
    bp={x.permit_id:x for x in base.permits}; tp={x.permit_id:x for x in target.permits}; bn={x.permit_nonce:x for x in base.nonce_records}; tn={x.permit_nonce:x for x in target.nonce_records}
    changed_p=tuple(tp[k] for k in sorted(tp) if k not in bp or _fp(tp[k])!=_fp(bp[k])); removed_p=tuple(k for k in sorted(bp) if k not in tp)
    changed_n=tuple(tn[k] for k in sorted(tn) if k not in bn or _fp(tn[k])!=_fp(bn[k])); removed_n=tuple(k for k in sorted(bn) if k not in tn)
    tr=target.request if _fp(base.request)!=_fp(target.request) else None; tpol=target.policy if _fp(base.policy)!=_fp(target.policy) else None
    return PermitLeaseStateDelta(base.registry_fingerprint,target.registry_fingerprint,changed_p,removed_p,changed_n,removed_n,tr,tpol,base.binding,base.state_epoch)

def apply_delta(base,delta):
    if delta.base_fingerprint!=base.registry_fingerprint: raise ValueError('DELTA_BASE_FINGERPRINT_MISMATCH')
    if delta.binding!=base.binding or delta.state_epoch!=base.state_epoch: raise ValueError('DELTA_SCOPE_MISMATCH')
    pm={x.permit_id:x for x in base.permits}; nm={x.permit_nonce:x for x in base.nonce_records}
    for k in delta.removed_permit_ids: pm.pop(k,None)
    for x in delta.changed_permits: pm[x.permit_id]=x
    for k in delta.removed_nonce_ids: nm.pop(k,None)
    for x in delta.changed_nonce_records: nm[x.permit_nonce]=x
    st=prepare_state(delta.target_request or base.request,tuple(pm.values()),tuple(nm.values()),delta.target_policy or base.policy,binding=base.binding,state_epoch=base.state_epoch)
    if st.registry_fingerprint!=delta.target_fingerprint: raise ValueError('DELTA_TARGET_FINGERPRINT_MISMATCH')
    return st

def missing_only_sync_plan(target,known_permit_fingerprints:dict[str,str],known_nonce_fingerprints:dict[str,str]):
    mp=tuple(k for k,v in target.permit_fingerprints if known_permit_fingerprints.get(k)!=v)
    mn=tuple(k for k,v in target.nonce_fingerprints if known_nonce_fingerprints.get(k)!=v)
    meta={'permit_ids':mp,'nonce_ids':mn,'target':target.registry_fingerprint}
    return PermitLeaseSyncPlan(mp,mn,len(_canon(meta)),False)

def full_registry_bytes(st): return len(_canon({'request':st.request,'permits':st.permits,'nonce_records':st.nonce_records,'policy':st.policy}))
def delta_bytes(delta): return len(_canon(delta))
