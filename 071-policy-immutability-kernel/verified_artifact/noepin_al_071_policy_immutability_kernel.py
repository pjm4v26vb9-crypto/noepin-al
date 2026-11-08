"""NOEPIN AL 071 — Policy Immutability Kernel / Sequential Successor V2.

Pure control-plane evaluator. It validates candidate policy-version transitions but
never commits policy, writes an append-only store, grants authority, executes an
action, or proves world truth/safety. Cryptographic signature verification is an
upstream authority input represented here as typed evidence; this module verifies
binding, signer authority, version, payload hash, freshness and revocation state.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
from enum import Enum
from hashlib import sha256
from typing import Iterable, Mapping, Tuple
import json

SCHEMA_VERSION = "NOEPIN-AL-071-V2"

class Decision(str, Enum):
    ALLOW="ALLOW"
    DENY="DENY"
    HOLD="HOLD"
    HUMAN_APPROVAL="HUMAN_APPROVAL"

@dataclass(frozen=True)
class PolicySnapshot:
    policy_id:str
    version:int
    policy_hash:str
    binding:str
    authority_epoch:str
    active:bool=True

@dataclass(frozen=True)
class AuthorityRecord:
    principal_id:str
    capabilities:Tuple[str,...]
    binding:str
    authority_epoch:str
    verified:bool=True
    revoked:bool=False

@dataclass(frozen=True)
class VersionRecord:
    version:int
    policy_hash:str
    binding:str
    verified:bool=True
    revoked:bool=False

@dataclass(frozen=True)
class SignatureEvidence:
    signature_id:str
    signer_id:str
    request_fingerprint:str
    signed_policy_hash:str
    expected_version:int
    binding:str
    authority_epoch:str
    verified:bool
    revoked:bool
    expires_at:int

@dataclass(frozen=True)
class KernelPolicy:
    policy_id:str
    binding:str
    authority_epoch:str
    trusted_updaters:Tuple[str,...]
    trusted_signers:Tuple[str,...]
    execution_agents:Tuple[str,...]
    request_max_age:int
    revoked:bool=False

@dataclass(frozen=True)
class ChangeRequest:
    request_id:str
    actor_id:str
    expected_version:int
    new_policy_hash:str
    change_kind:str
    rollback_target_version:int|None
    signature_id:str|None
    created_at:int
    binding:str
    expected_authority_epoch:str

@dataclass(frozen=True)
class PreparedPolicyState:
    kernel_policy:KernelPolicy
    current:PolicySnapshot
    authorities:Tuple[AuthorityRecord,...]
    signatures:Tuple[SignatureEvidence,...]
    versions:Tuple[VersionRecord,...]
    binding:str
    policy_fingerprint:str
    registry_fingerprint:str
    authority_fingerprints:Tuple[Tuple[str,str],...]
    signature_fingerprints:Tuple[Tuple[str,str],...]
    version_fingerprints:Tuple[Tuple[str,str],...]
    authority_index:Tuple[Tuple[str,AuthorityRecord],...]
    signature_index:Tuple[Tuple[str,SignatureEvidence],...]
    version_index:Tuple[Tuple[str,VersionRecord],...]

@dataclass(frozen=True)
class PolicyRegistryDelta:
    base_fingerprint:str
    target_fingerprint:str
    kernel_policy:KernelPolicy
    current:PolicySnapshot
    binding:str
    upsert_authorities:Tuple[AuthorityRecord,...]
    remove_authority_ids:Tuple[str,...]
    upsert_signatures:Tuple[SignatureEvidence,...]
    remove_signature_ids:Tuple[str,...]
    upsert_versions:Tuple[VersionRecord,...]
    remove_versions:Tuple[int,...]

@dataclass(frozen=True)
class PolicySyncPlan:
    missing_or_changed_authority_ids:Tuple[str,...]
    missing_or_changed_signature_ids:Tuple[str,...]
    missing_or_changed_versions:Tuple[int,...]
    metadata_bytes_required:int
    full_resend_required:bool

@dataclass(frozen=True)
class PolicyUpdateResult:
    decision:Decision
    reasons:Tuple[str,...]
    actor_id:str
    signer_id:str|None
    policy_id:str
    current_version:int
    proposed_version:int|None
    current_policy_hash:str
    candidate_policy_hash:str|None
    version_delta:int|None
    rollback_target_version:int|None
    signature_binding_valid:bool
    updater_authority_valid:bool
    next_gate_candidate:bool
    policy_update_committed:bool=False
    policy_store_written:bool=False
    permission_granted:bool=False
    role_changed:bool=False
    capability_activated:bool=False
    signature_created:bool=False
    approval_executed:bool=False
    action_executed:bool=False
    world_truth_proven:bool=False
    safety_proven:bool=False
    action_success:bool=False

def _canon(xs:Iterable[str])->Tuple[str,...]: return tuple(sorted(set(str(x) for x in xs)))

def _ser(obj)->bytes:
    def norm(x):
        if isinstance(x,Enum): return x.value
        if hasattr(x,"__dataclass_fields__"):
            return {k:norm(getattr(x,k)) for k in sorted(x.__dataclass_fields__)}
        if isinstance(x,tuple): return [norm(v) for v in x]
        if isinstance(x,list): return [norm(v) for v in x]
        if isinstance(x,dict): return {str(k):norm(v) for k,v in sorted(x.items(),key=lambda kv:str(kv[0]))}
        return x
    return json.dumps(norm(obj),ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()

def _fp(obj)->str: return sha256(_ser(obj)).hexdigest()

def default_kernel_policy(now:int)->KernelPolicy:
    return KernelPolicy("SAFETY-POLICY","POL-BIND","POL-EPOCH",("HUMAN-ADMIN","SECURITY-ADMIN"),("HUMAN-ADMIN","SECURITY-ADMIN"),("AGENT-1","AGENT-2"),600,False)

def default_snapshot()->PolicySnapshot:
    return PolicySnapshot("SAFETY-POLICY",7,"hash-v7","POL-BIND","POL-EPOCH",True)

def default_authorities()->Tuple[AuthorityRecord,...]:
    c=dict(binding="POL-BIND",authority_epoch="POL-EPOCH",verified=True,revoked=False)
    return (
        AuthorityRecord("AGENT-1",("EXECUTE",),**c),
        AuthorityRecord("AGENT-2",("EXECUTE",),**c),
        AuthorityRecord("HUMAN-ADMIN",("POLICY_UPDATE","POLICY_SIGN"),**c),
        AuthorityRecord("SECURITY-ADMIN",("POLICY_UPDATE","POLICY_SIGN"),**c),
    )

def default_versions()->Tuple[VersionRecord,...]:
    return tuple(VersionRecord(i,f"hash-v{i}","POL-BIND",True,False) for i in range(1,8))

def default_request(now:int)->ChangeRequest:
    return ChangeRequest("REQ-71","HUMAN-ADMIN",7,"hash-v8","UPDATE",None,"SIG-71",now,"POL-BIND","POL-EPOCH")

def request_fingerprint(req:ChangeRequest,current:PolicySnapshot,candidate_hash:str)->str:
    return _fp({
        "request_id":req.request_id,"actor_id":req.actor_id,"policy_id":current.policy_id,
        "expected_version":req.expected_version,"current_hash":current.policy_hash,
        "candidate_hash":candidate_hash,"change_kind":req.change_kind,
        "rollback_target_version":req.rollback_target_version,"created_at":req.created_at,
        "binding":req.binding,"expected_authority_epoch":req.expected_authority_epoch,
    })

def signature_for(req:ChangeRequest,current:PolicySnapshot,*,candidate_hash:str|None=None,signer_id:str="HUMAN-ADMIN",now:int=1_800_000_000,verified:bool=True,revoked:bool=False)->SignatureEvidence:
    ch=candidate_hash if candidate_hash is not None else req.new_policy_hash
    return SignatureEvidence("SIG-71",signer_id,request_fingerprint(req,current,ch),ch,req.expected_version,req.binding,req.expected_authority_epoch,verified,revoked,now+300)

def _valid_kernel(p:KernelPolicy,binding:str)->bool:
    return bool(p.policy_id and p.binding==binding and p.authority_epoch and p.request_max_age>=0 and not p.revoked)

def _valid_authority(a:AuthorityRecord|None,p:KernelPolicy,binding:str,cap:str)->bool:
    return bool(a and a.verified and not a.revoked and a.binding==binding and a.authority_epoch==p.authority_epoch and cap in a.capabilities)

def _build_map(rows,keyfn,dup):
    m={}
    for r in rows:
        k=keyfn(r)
        if k in m: raise ValueError(dup)
        m[k]=r
    return m

def _lookup_index(index,key):
    key=str(key); lo=0; hi=len(index)
    while lo<hi:
        mid=(lo+hi)//2; mk=index[mid][0]
        if mk<key: lo=mid+1
        else: hi=mid
    return index[lo][1] if lo<len(index) and index[lo][0]==key else None

def _candidate(req:ChangeRequest,current:PolicySnapshot,get_version):
    kind=req.change_kind.upper()
    if kind=="UPDATE":
        if not req.new_policy_hash: return None,("NEW_POLICY_HASH_MISSING",)
        if req.rollback_target_version is not None: return None,("UPDATE_HAS_ROLLBACK_TARGET",)
        return req.new_policy_hash,()
    if kind=="ROLLBACK":
        if req.rollback_target_version is None: return None,("ROLLBACK_TARGET_MISSING",)
        if req.rollback_target_version>=current.version: return None,("ROLLBACK_TARGET_NOT_OLDER",)
        vr=get_version(req.rollback_target_version)
        if vr is None or not vr.verified or vr.revoked or vr.binding!=req.binding:
            return None,("ROLLBACK_TARGET_UNVERIFIED",)
        if req.new_policy_hash!=vr.policy_hash: return None,("ROLLBACK_HASH_MISMATCH",)
        return vr.policy_hash,()
    return None,("CHANGE_KIND_UNSUPPORTED",)

def _evaluate_lookup(req:ChangeRequest,p:KernelPolicy,current:PolicySnapshot,get_authority,get_signature,get_version,*,now:int)->PolicyUpdateResult:
    zero=PolicyUpdateResult(Decision.HOLD,(),req.actor_id,None,current.policy_id,current.version,None,current.policy_hash,None,None,req.rollback_target_version,False,False,False)
    if not _valid_kernel(p,req.binding): return replace(zero,reasons=("KERNEL_POLICY_INVALID_OR_BINDING_MISMATCH",))
    if current.policy_id!=p.policy_id or current.binding!=req.binding or current.authority_epoch!=p.authority_epoch or not current.active:
        return replace(zero,reasons=("CURRENT_POLICY_STATE_UNCONFIRMED",))
    if req.expected_authority_epoch!=p.authority_epoch: return replace(zero,decision=Decision.DENY,reasons=("AUTHORITY_EPOCH_MISMATCH",))
    if req.created_at>now or now-req.created_at>p.request_max_age: return replace(zero,reasons=("REQUEST_STALE_OR_FUTURE",))
    if req.expected_version!=current.version: return replace(zero,reasons=("EXPECTED_VERSION_CONFLICT",))
    curvr=get_version(current.version)
    if curvr is None or not curvr.verified or curvr.revoked or curvr.binding!=req.binding or curvr.policy_hash!=current.policy_hash:
        return replace(zero,reasons=("CURRENT_VERSION_RECORD_UNCONFIRMED",))
    if req.actor_id in p.execution_agents:
        return replace(zero,decision=Decision.DENY,reasons=("EXECUTION_AGENT_DIRECT_POLICY_UPDATE_DENIED",))
    actor=get_authority(req.actor_id)
    actor_ok=req.actor_id in p.trusted_updaters and _valid_authority(actor,p,req.binding,"POLICY_UPDATE")
    if not actor_ok:
        return replace(zero,decision=Decision.DENY,reasons=("UPDATER_AUTHORITY_UNCONFIRMED",),updater_authority_valid=False)
    cand,errs=_candidate(req,current,get_version)
    if errs: return replace(zero,decision=Decision.DENY,reasons=errs,updater_authority_valid=True)
    assert cand is not None
    base=replace(zero,candidate_policy_hash=cand,updater_authority_valid=True)
    if not req.signature_id:
        return replace(base,decision=Decision.DENY,reasons=("SIGNATURE_MISSING",))
    sig=get_signature(req.signature_id)
    if sig is None:
        return replace(base,decision=Decision.DENY,reasons=("SIGNATURE_UNKNOWN",))
    reasons=[]
    if sig.signer_id in p.execution_agents: reasons.append("EXECUTION_AGENT_SIGNATURE_DENIED")
    if sig.signer_id not in p.trusted_signers: reasons.append("SIGNER_NOT_TRUSTED")
    signer=get_authority(sig.signer_id)
    if not _valid_authority(signer,p,req.binding,"POLICY_SIGN"): reasons.append("SIGNER_AUTHORITY_UNCONFIRMED")
    if not sig.verified or sig.revoked: reasons.append("SIGNATURE_INVALID_OR_REVOKED")
    if sig.expires_at<now: reasons.append("SIGNATURE_EXPIRED")
    if sig.binding!=req.binding or sig.authority_epoch!=p.authority_epoch: reasons.append("SIGNATURE_BINDING_MISMATCH")
    if sig.expected_version!=req.expected_version: reasons.append("SIGNATURE_VERSION_MISMATCH")
    if sig.signed_policy_hash!=cand: reasons.append("SIGNATURE_POLICY_HASH_MISMATCH")
    if sig.request_fingerprint!=request_fingerprint(req,current,cand): reasons.append("SIGNATURE_REQUEST_FINGERPRINT_MISMATCH")
    if reasons:
        return replace(base,decision=Decision.DENY,reasons=tuple(sorted(set(reasons))),signer_id=sig.signer_id,signature_binding_valid=False)
    proposed=current.version+1
    rs=("ROLLBACK_APPEND_ONLY_VERSION_CANDIDATE",) if req.change_kind.upper()=="ROLLBACK" else ("POLICY_APPEND_ONLY_VERSION_CANDIDATE",)
    return replace(base,decision=Decision.ALLOW,reasons=rs,signer_id=sig.signer_id,signature_binding_valid=True,proposed_version=proposed,version_delta=1,next_gate_candidate=True)

def evaluate(req:ChangeRequest,p:KernelPolicy,current:PolicySnapshot,authorities:Tuple[AuthorityRecord,...],signatures:Tuple[SignatureEvidence,...],versions:Tuple[VersionRecord,...],*,now:int)->PolicyUpdateResult:
    try:
        am=_build_map(authorities,lambda x:x.principal_id,"DUPLICATE_AUTHORITY_ID")
        sm=_build_map(signatures,lambda x:x.signature_id,"DUPLICATE_SIGNATURE_ID")
        vm=_build_map(versions,lambda x:x.version,"DUPLICATE_VERSION")
    except ValueError as e:
        z=PolicyUpdateResult(Decision.HOLD,(str(e),),req.actor_id,None,current.policy_id,current.version,None,current.policy_hash,None,None,req.rollback_target_version,False,False,False)
        return z
    return _evaluate_lookup(req,p,current,am.get,sm.get,vm.get,now=now)

def _registry_fp(p,current,authorities,signatures,versions,binding):
    return _fp({"kernel_policy":p,"current":current,"authorities":tuple(sorted(authorities,key=lambda x:x.principal_id)),"signatures":tuple(sorted(signatures,key=lambda x:x.signature_id)),"versions":tuple(sorted(versions,key=lambda x:x.version)),"binding":binding})

def prepare_state(p:KernelPolicy,current:PolicySnapshot,authorities:Tuple[AuthorityRecord,...],signatures:Tuple[SignatureEvidence,...],versions:Tuple[VersionRecord,...],*,binding:str,now:int)->PreparedPolicyState:
    am=_build_map(authorities,lambda x:x.principal_id,"DUPLICATE_AUTHORITY_ID")
    sm=_build_map(signatures,lambda x:x.signature_id,"DUPLICATE_SIGNATURE_ID")
    vm=_build_map(versions,lambda x:x.version,"DUPLICATE_VERSION")
    af=tuple(sorted((k,_fp(v)) for k,v in am.items())); sf=tuple(sorted((k,_fp(v)) for k,v in sm.items())); vf=tuple(sorted((str(k),_fp(v)) for k,v in vm.items()))
    ai=tuple(sorted(am.items())); si=tuple(sorted(sm.items())); vi=tuple(sorted((str(k),v) for k,v in vm.items()))
    return PreparedPolicyState(p,current,tuple(sorted(authorities,key=lambda x:x.principal_id)),tuple(sorted(signatures,key=lambda x:x.signature_id)),tuple(sorted(versions,key=lambda x:x.version)),binding,_fp({"kernel_policy":p,"current":current,"binding":binding}),_registry_fp(p,current,authorities,signatures,versions,binding),af,sf,vf,ai,si,vi)

def validate_prepared_integrity(st:PreparedPolicyState)->bool:
    try:
        return (
            st.policy_fingerprint==_fp({"kernel_policy":st.kernel_policy,"current":st.current,"binding":st.binding}) and
            st.registry_fingerprint==_registry_fp(st.kernel_policy,st.current,st.authorities,st.signatures,st.versions,st.binding) and
            st.authority_fingerprints==tuple(sorted((a.principal_id,_fp(a)) for a in st.authorities)) and
            st.signature_fingerprints==tuple(sorted((a.signature_id,_fp(a)) for a in st.signatures)) and
            st.version_fingerprints==tuple(sorted((str(v.version),_fp(v)) for v in st.versions)) and
            st.authority_index==tuple(sorted((a.principal_id,a) for a in st.authorities)) and
            st.signature_index==tuple(sorted((a.signature_id,a) for a in st.signatures)) and
            st.version_index==tuple(sorted((str(v.version),v) for v in st.versions))
        )
    except Exception:
        return False

def evaluate_prepared(req:ChangeRequest,st:PreparedPolicyState,*,current_policy_fingerprint:str,current_registry_fingerprint:str,prepared_integrity_validated:bool,now:int)->PolicyUpdateResult:
    zero=PolicyUpdateResult(Decision.HOLD,("PREPARED_STATE_UNTRUSTED",),req.actor_id,None,st.current.policy_id,st.current.version,None,st.current.policy_hash,None,None,req.rollback_target_version,False,False,False)
    if not prepared_integrity_validated: return zero
    if current_policy_fingerprint!=st.policy_fingerprint: return replace(zero,reasons=("CURRENT_POLICY_FINGERPRINT_MISMATCH",))
    if current_registry_fingerprint!=st.registry_fingerprint: return replace(zero,reasons=("CURRENT_REGISTRY_FINGERPRINT_MISMATCH",))
    return _evaluate_lookup(req,st.kernel_policy,st.current,lambda k:_lookup_index(st.authority_index,k),lambda k:_lookup_index(st.signature_index,k),lambda k:_lookup_index(st.version_index,k),now=now)

def make_delta(base:PreparedPolicyState,target:PreparedPolicyState)->PolicyRegistryDelta:
    if base.binding!=target.binding: raise ValueError("DELTA_BINDING_MISMATCH")
    ba=dict(base.authority_index); ta=dict(target.authority_index); bs=dict(base.signature_index); ts=dict(target.signature_index); bv={int(k):v for k,v in base.version_index}; tv={int(k):v for k,v in target.version_index}
    ua=tuple(ta[k] for k in sorted(ta) if k not in ba or _fp(ta[k])!=_fp(ba[k])); ra=tuple(sorted(k for k in ba if k not in ta))
    us=tuple(ts[k] for k in sorted(ts) if k not in bs or _fp(ts[k])!=_fp(bs[k])); rs=tuple(sorted(k for k in bs if k not in ts))
    uv=tuple(tv[k] for k in sorted(tv) if k not in bv or _fp(tv[k])!=_fp(bv[k])); rv=tuple(sorted(k for k in bv if k not in tv))
    return PolicyRegistryDelta(base.registry_fingerprint,target.registry_fingerprint,target.kernel_policy,target.current,target.binding,ua,ra,us,rs,uv,rv)

def apply_delta(base:PreparedPolicyState,d:PolicyRegistryDelta,*,now:int)->PreparedPolicyState:
    if base.registry_fingerprint!=d.base_fingerprint: raise ValueError("DELTA_BASE_MISMATCH")
    if base.binding!=d.binding: raise ValueError("DELTA_BINDING_MISMATCH")
    am=dict(base.authority_index); sm=dict(base.signature_index); vm={int(k):v for k,v in base.version_index}
    for k in d.remove_authority_ids: am.pop(k,None)
    for v in d.upsert_authorities: am[v.principal_id]=v
    for k in d.remove_signature_ids: sm.pop(k,None)
    for v in d.upsert_signatures: sm[v.signature_id]=v
    for k in d.remove_versions: vm.pop(k,None)
    for v in d.upsert_versions: vm[v.version]=v
    st=prepare_state(d.kernel_policy,d.current,tuple(am[k] for k in sorted(am)),tuple(sm[k] for k in sorted(sm)),tuple(vm[k] for k in sorted(vm)),binding=d.binding,now=now)
    if st.registry_fingerprint!=d.target_fingerprint: raise ValueError("DELTA_TARGET_MISMATCH")
    return st

def missing_only_sync_plan(st:PreparedPolicyState,remote_fingerprints:Mapping[str,Mapping[str,str]])->PolicySyncPlan:
    ra=remote_fingerprints.get("authorities",{}); rs=remote_fingerprints.get("signatures",{}); rv=remote_fingerprints.get("versions",{})
    a=tuple(k for k,v in st.authority_fingerprints if ra.get(k)!=v); s=tuple(k for k,v in st.signature_fingerprints if rs.get(k)!=v); vv=tuple(int(k) for k,v in st.version_fingerprints if rv.get(k)!=v)
    meta=len(_ser({"authorities":a,"signatures":s,"versions":vv,"target":st.registry_fingerprint}))
    return PolicySyncPlan(a,s,vv,meta,False)

def full_registry_bytes(st): return len(_ser({"kernel_policy":st.kernel_policy,"current":st.current,"authorities":st.authorities,"signatures":st.signatures,"versions":st.versions,"binding":st.binding}))
def delta_bytes(d): return len(_ser(d))
