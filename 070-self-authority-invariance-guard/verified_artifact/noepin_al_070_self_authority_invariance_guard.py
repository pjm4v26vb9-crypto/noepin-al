"""NOEPIN AL 070 — Self-Authority Invariance Guard / Sequential Successor V2.

Pure control-plane evaluator. It never grants permissions, mutates roles, issues
credentials, executes actions, or proves world truth/safety.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
from enum import Enum
from hashlib import sha256
from typing import Iterable, Mapping, Tuple
import json

SCHEMA_VERSION="NOEPIN-AL-070-V2"

class Decision(str, Enum):
    ALLOW="ALLOW"
    DENY="DENY"
    HOLD="HOLD"
    HUMAN_APPROVAL="HUMAN_APPROVAL"

@dataclass(frozen=True)
class AuthorityRecord:
    principal_id:str
    capabilities:Tuple[str,...]
    binding:str
    verified:bool
    revoked:bool
    policy_id:str
    policy_version:str
    authority_epoch:str

@dataclass(frozen=True)
class ApprovalEvidence:
    approval_id:str
    approver_id:str
    subject_id:str
    actor_id:str
    requested_capabilities:Tuple[str,...]
    signed:bool
    verified:bool
    revoked:bool
    expires_at:int
    binding:str
    policy_id:str
    policy_version:str
    authority_epoch:str

@dataclass(frozen=True)
class GuardPolicy:
    policy_id:str
    policy_version:str
    authority_epoch:str
    binding:str
    trusted_approvers:Tuple[str,...]
    request_max_age:int
    revoked:bool=False

@dataclass(frozen=True)
class AuthorityChangeRequest:
    request_id:str
    actor_id:str
    target_id:str
    requested_capabilities:Tuple[str,...]
    approval_id:str|None
    created_at:int
    binding:str
    expected_policy_version:str
    expected_authority_epoch:str

@dataclass(frozen=True)
class PreparedAuthorityState:
    policy:GuardPolicy
    authorities:Tuple[AuthorityRecord,...]
    approvals:Tuple[ApprovalEvidence,...]
    binding:str
    policy_fingerprint:str
    registry_fingerprint:str
    authority_fingerprints:Tuple[Tuple[str,str],...]
    approval_fingerprints:Tuple[Tuple[str,str],...]
    authority_index:Tuple[Tuple[str,AuthorityRecord],...]
    approval_index:Tuple[Tuple[str,ApprovalEvidence],...]

@dataclass(frozen=True)
class AuthorityRegistryDelta:
    base_fingerprint:str
    target_fingerprint:str
    policy:GuardPolicy
    binding:str
    upsert_authorities:Tuple[AuthorityRecord,...]
    remove_authority_ids:Tuple[str,...]
    upsert_approvals:Tuple[ApprovalEvidence,...]
    remove_approval_ids:Tuple[str,...]

@dataclass(frozen=True)
class AuthoritySyncPlan:
    missing_or_changed_authority_ids:Tuple[str,...]
    missing_or_changed_approval_ids:Tuple[str,...]
    metadata_bytes_required:int
    full_resend_required:bool

@dataclass(frozen=True)
class GuardResult:
    decision:Decision
    reasons:Tuple[str,...]
    actor_id:str
    target_id:str
    current_capabilities:Tuple[str,...]
    requested_capabilities:Tuple[str,...]
    added_capabilities:Tuple[str,...]
    removed_capabilities:Tuple[str,...]
    approver_id:str|None
    independent_approval_valid:bool
    next_gate_candidate:bool
    permission_granted:bool=False
    role_changed:bool=False
    scope_changed:bool=False
    capability_activated:bool=False
    credential_issued:bool=False
    approval_executed:bool=False
    action_executed:bool=False
    world_truth_proven:bool=False
    safety_proven:bool=False
    action_success:bool=False

def _canon_caps(xs:Iterable[str])->Tuple[str,...]:
    return tuple(sorted(set(str(x) for x in xs)))

def _ser(obj)->bytes:
    def norm(x):
        if isinstance(x, Enum): return x.value
        if hasattr(x,"__dataclass_fields__"):
            return {k:norm(getattr(x,k)) for k in sorted(x.__dataclass_fields__)}
        if isinstance(x,tuple): return [norm(v) for v in x]
        if isinstance(x,list): return [norm(v) for v in x]
        if isinstance(x,dict): return {str(k):norm(v) for k,v in sorted(x.items(),key=lambda kv:str(kv[0]))}
        return x
    return json.dumps(norm(obj),ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()

def _fp(obj)->str: return sha256(_ser(obj)).hexdigest()

def default_policy(now:int)->GuardPolicy:
    return GuardPolicy("SAG-POLICY","1","SAG-EPOCH","SAG-BIND",("HUMAN-ADMIN","SECURITY-ADMIN"),600,False)

def default_authorities()->Tuple[AuthorityRecord,...]:
    c=dict(binding="SAG-BIND",verified=True,revoked=False,policy_id="SAG-POLICY",policy_version="1",authority_epoch="SAG-EPOCH")
    return (
        AuthorityRecord("AGENT-1",("READ","WRITE_SCOPED"),**c),
        AuthorityRecord("AGENT-2",("READ",),**c),
        AuthorityRecord("HUMAN-ADMIN",("AUTHORITY_APPROVE","READ"),**c),
        AuthorityRecord("SECURITY-ADMIN",("AUTHORITY_APPROVE","READ"),**c),
    )

def approval_for(request:AuthorityChangeRequest, approver_id:str="HUMAN-ADMIN", now:int=1_800_000_000, *, signed=True, verified=True, revoked=False)->ApprovalEvidence:
    return ApprovalEvidence("APR-1",approver_id,request.target_id,request.actor_id,_canon_caps(request.requested_capabilities),
                            signed,verified,revoked,now+300,"SAG-BIND","SAG-POLICY","1","SAG-EPOCH")

def default_request(now:int)->AuthorityChangeRequest:
    return AuthorityChangeRequest("REQ-1","AGENT-1","AGENT-1",("READ",),None,now,"SAG-BIND","1","SAG-EPOCH")

def _valid_policy(p:GuardPolicy, binding:str)->bool:
    return bool(p.policy_id and p.policy_version and p.authority_epoch and not p.revoked and p.binding==binding and p.request_max_age>=0)

def _authority_map(authorities):
    m={}
    for a in authorities:
        if a.principal_id in m: raise ValueError("DUPLICATE_AUTHORITY_ID")
        m[a.principal_id]=a
    return m

def _approval_map(approvals):
    m={}
    for a in approvals:
        if a.approval_id in m: raise ValueError("DUPLICATE_APPROVAL_ID")
        m[a.approval_id]=a
    return m

def _record_valid(a:AuthorityRecord,p:GuardPolicy,binding:str)->bool:
    return (a.verified and not a.revoked and a.binding==binding and a.policy_id==p.policy_id
            and a.policy_version==p.policy_version and a.authority_epoch==p.authority_epoch)

def _approval_status(ev:ApprovalEvidence|None, req:AuthorityChangeRequest, p:GuardPolicy, auths:Mapping[str,AuthorityRecord], now:int):
    if ev is None: return False,None,("APPROVAL_MISSING",)
    reasons=[]
    if ev.approver_id==req.actor_id or ev.approver_id==req.target_id: reasons.append("APPROVER_NOT_INDEPENDENT")
    if ev.approver_id not in p.trusted_approvers: reasons.append("APPROVER_NOT_TRUSTED")
    ar=auths.get(ev.approver_id)
    if ar is None or not _record_valid(ar,p,req.binding) or "AUTHORITY_APPROVE" not in ar.capabilities: reasons.append("APPROVER_AUTHORITY_UNCONFIRMED")
    if not ev.signed or not ev.verified or ev.revoked: reasons.append("APPROVAL_INVALID")
    if ev.expires_at < now: reasons.append("APPROVAL_EXPIRED")
    if ev.binding!=req.binding or ev.policy_id!=p.policy_id or ev.policy_version!=p.policy_version or ev.authority_epoch!=p.authority_epoch: reasons.append("APPROVAL_BINDING_MISMATCH")
    if ev.subject_id!=req.target_id or ev.actor_id!=req.actor_id: reasons.append("APPROVAL_SUBJECT_MISMATCH")
    if _canon_caps(ev.requested_capabilities)!=_canon_caps(req.requested_capabilities): reasons.append("APPROVAL_DELTA_MISMATCH")
    return not reasons,ev.approver_id,tuple(sorted(set(reasons)))

def _lookup_index(index, key):
    lo=0; hi=len(index)
    while lo<hi:
        mid=(lo+hi)//2
        mk=index[mid][0]
        if mk<key: lo=mid+1
        else: hi=mid
    return index[lo][1] if lo<len(index) and index[lo][0]==key else None

def _evaluate_lookup(req:AuthorityChangeRequest,p:GuardPolicy,get_authority,get_approval,*,now:int)->GuardResult:
    zero=GuardResult(Decision.HOLD,(),req.actor_id,req.target_id,(),_canon_caps(req.requested_capabilities),(),(),None,False,False)
    if not _valid_policy(p,req.binding): return replace(zero,reasons=("POLICY_INVALID_OR_BINDING_MISMATCH",))
    if req.expected_policy_version!=p.policy_version or req.expected_authority_epoch!=p.authority_epoch: return replace(zero,reasons=("REQUEST_POLICY_OR_EPOCH_MISMATCH",))
    if req.created_at>now or now-req.created_at>p.request_max_age: return replace(zero,reasons=("REQUEST_STALE_OR_FUTURE",))
    current=get_authority(req.target_id)
    if current is None or not _record_valid(current,p,req.binding):
        return replace(zero,reasons=("TARGET_AUTHORITY_UNCONFIRMED",))
    requested=_canon_caps(req.requested_capabilities); current_caps=_canon_caps(current.capabilities)
    added=tuple(sorted(set(requested)-set(current_caps))); removed=tuple(sorted(set(current_caps)-set(requested)))
    base=replace(zero,current_capabilities=current_caps,requested_capabilities=requested,added_capabilities=added,removed_capabilities=removed)
    if not added and not removed:
        return replace(base,decision=Decision.ALLOW,reasons=("NO_AUTHORITY_EXPANSION_OR_CHANGE",),next_gate_candidate=True)
    needs_external = bool(added) or req.actor_id!=req.target_id
    if not needs_external:
        return replace(base,decision=Decision.ALLOW,reasons=("SELF_DEGRADATION_CANDIDATE",),next_gate_candidate=True)
    ev=get_approval(req.approval_id) if req.approval_id else None
    # Only the approver authority record is required to validate approval authority.
    auth_view={}
    if ev is not None:
        ar=get_authority(ev.approver_id)
        if ar is not None: auth_view[ev.approver_id]=ar
    valid,approver,approval_reasons=_approval_status(ev,req,p,auth_view,now)
    base=replace(base,approver_id=approver,independent_approval_valid=valid)
    if not valid:
        return replace(base,decision=Decision.DENY,reasons=approval_reasons or ("INDEPENDENT_APPROVAL_UNCONFIRMED",))
    if req.actor_id==req.target_id and added:
        return replace(base,decision=Decision.ALLOW,reasons=("EXTERNAL_INDEPENDENT_APPROVAL_VERIFIED","SELF_ELEVATION_NOT_SELF_GRANTED"),next_gate_candidate=True)
    return replace(base,decision=Decision.ALLOW,reasons=("EXTERNAL_INDEPENDENT_APPROVAL_VERIFIED","PROXY_AUTHORITY_CHANGE_CANDIDATE"),next_gate_candidate=True)

def evaluate(req:AuthorityChangeRequest,p:GuardPolicy,authorities:Tuple[AuthorityRecord,...],approvals:Tuple[ApprovalEvidence,...],*,now:int)->GuardResult:
    zero=GuardResult(Decision.HOLD,(),req.actor_id,req.target_id,(),_canon_caps(req.requested_capabilities),(),(),None,False,False)
    try:
        auths=_authority_map(authorities); aps=_approval_map(approvals)
    except ValueError as e:
        return replace(zero,reasons=(str(e),))
    return _evaluate_lookup(req,p,auths.get,aps.get,now=now)

def _policy_fp(p): return _fp(p)
def _authority_fps(authorities): return tuple(sorted((x.principal_id,_fp(x)) for x in authorities))
def _approval_fps(approvals): return tuple(sorted((x.approval_id,_fp(x)) for x in approvals))
def _registry_fp(p,binding,authorities,approvals):
    return _fp({"policy":_policy_fp(p),"binding":binding,"authorities":_authority_fps(authorities),"approvals":_approval_fps(approvals)})

def prepare_state(p,authorities,approvals,*,binding:str,now:int)->PreparedAuthorityState:
    # now is accepted to keep the interface symmetric; freshness is always rechecked in evaluate_prepared.
    _authority_map(authorities); _approval_map(approvals)
    af=_authority_fps(authorities); pf=_approval_fps(approvals)
    ai=tuple(sorted((x.principal_id,x) for x in authorities)); pi=tuple(sorted((x.approval_id,x) for x in approvals))
    return PreparedAuthorityState(p,tuple(authorities),tuple(approvals),binding,_policy_fp(p),_registry_fp(p,binding,authorities,approvals),af,pf,ai,pi)

def validate_prepared_integrity(st:PreparedAuthorityState)->bool:
    return (st.policy_fingerprint==_policy_fp(st.policy)
            and st.authority_fingerprints==_authority_fps(st.authorities)
            and st.approval_fingerprints==_approval_fps(st.approvals)
            and st.authority_index==tuple(sorted((x.principal_id,x) for x in st.authorities))
            and st.approval_index==tuple(sorted((x.approval_id,x) for x in st.approvals))
            and st.registry_fingerprint==_registry_fp(st.policy,st.binding,st.authorities,st.approvals))

def evaluate_prepared(req,st:PreparedAuthorityState,*,current_policy_fingerprint:str,current_registry_fingerprint:str,prepared_integrity_validated:bool,now:int)->GuardResult:
    if not prepared_integrity_validated:
        z=GuardResult(Decision.HOLD,("PREPARED_INTEGRITY_NOT_VALIDATED",),req.actor_id,req.target_id,(),_canon_caps(req.requested_capabilities),(),(),None,False,False); return z
    if current_policy_fingerprint!=st.policy_fingerprint or current_registry_fingerprint!=st.registry_fingerprint:
        z=GuardResult(Decision.HOLD,("PREPARED_IDENTITY_MISMATCH",),req.actor_id,req.target_id,(),_canon_caps(req.requested_capabilities),(),(),None,False,False); return z
    return _evaluate_lookup(req,st.policy,lambda k:_lookup_index(st.authority_index,k),lambda k:_lookup_index(st.approval_index,k),now=now)

def make_delta(base:PreparedAuthorityState,target:PreparedAuthorityState)->AuthorityRegistryDelta:
    ba=dict(base.authority_fingerprints); ta=dict(target.authority_fingerprints)
    bp=dict(base.approval_fingerprints); tp=dict(target.approval_fingerprints)
    authmap={x.principal_id:x for x in target.authorities}; appmap={x.approval_id:x for x in target.approvals}
    upa=tuple(authmap[k] for k in sorted(ta) if ba.get(k)!=ta[k]); rma=tuple(sorted(set(ba)-set(ta)))
    upp=tuple(appmap[k] for k in sorted(tp) if bp.get(k)!=tp[k]); rmp=tuple(sorted(set(bp)-set(tp)))
    return AuthorityRegistryDelta(base.registry_fingerprint,target.registry_fingerprint,target.policy,target.binding,upa,rma,upp,rmp)

def apply_delta(base:PreparedAuthorityState,d:AuthorityRegistryDelta,*,now:int)->PreparedAuthorityState:
    if base.registry_fingerprint!=d.base_fingerprint: raise ValueError("DELTA_BASE_MISMATCH")
    am={x.principal_id:x for x in base.authorities}; pm={x.approval_id:x for x in base.approvals}
    for k in d.remove_authority_ids: am.pop(k,None)
    for x in d.upsert_authorities: am[x.principal_id]=x
    for k in d.remove_approval_ids: pm.pop(k,None)
    for x in d.upsert_approvals: pm[x.approval_id]=x
    st=prepare_state(d.policy,tuple(am[k] for k in sorted(am)),tuple(pm[k] for k in sorted(pm)),binding=d.binding,now=now)
    if st.registry_fingerprint!=d.target_fingerprint: raise ValueError("DELTA_TARGET_MISMATCH")
    return st

def missing_only_sync_plan(st:PreparedAuthorityState,remote_fingerprints:Mapping[str,Mapping[str,str]])->AuthoritySyncPlan:
    ra=remote_fingerprints.get("authorities",{}); rp=remote_fingerprints.get("approvals",{})
    aa=tuple(k for k,v in st.authority_fingerprints if ra.get(k)!=v)
    ap=tuple(k for k,v in st.approval_fingerprints if rp.get(k)!=v)
    meta=len(_ser({"authorities":aa,"approvals":ap,"target":st.registry_fingerprint}))
    return AuthoritySyncPlan(aa,ap,meta,False)

def full_registry_bytes(st): return len(_ser({"policy":st.policy,"binding":st.binding,"authorities":st.authorities,"approvals":st.approvals}))
def delta_bytes(d): return len(_ser(d))
