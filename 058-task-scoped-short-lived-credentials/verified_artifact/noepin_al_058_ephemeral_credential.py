"""NOEPIN AL 058 — Task-bound Ephemeral Credential Control.

Pure control-plane evaluator for task/run-bound short-lived credential candidates.
It validates policy, scope, audience, role, TTL, task/run/subject binding, use count,
expiry and revocation metadata. It does not mint secrets/tokens, grant permission,
use credentials, revoke credentials, persist state, or prove task/action success.

Creator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support using ChatGPT
License / Rights: NOT SPECIFIED
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Any, FrozenSet, Iterable, Mapping, Tuple

class ControlDecision(str, Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class CredentialOperation(str, Enum):
    ISSUE='ISSUE'; USE='USE'; REVOKE='REVOKE'; STATUS='STATUS'

@dataclass(frozen=True)
class CredentialPolicy:
    policy_id:str; version:str; authority_epoch:int; issued_at:int; expires_at:int
    max_ttl_seconds:int; max_uses:int; allowed_roles:FrozenSet[str]; allowed_scopes:FrozenSet[str]; allowed_audiences:FrozenSet[str]
    trusted_issuers:FrozenSet[str]; require_run_binding:bool=True; require_verified_record:bool=True; revoked:bool=False
    def validate(self,now:int)->None:
        if not self.policy_id or not self.version or self.authority_epoch<1: raise ValueError('policy identity invalid')
        if self.issued_at<0 or self.expires_at<=self.issued_at or not self.issued_at<=now<self.expires_at: raise ValueError('policy not current')
        if self.max_ttl_seconds<1 or self.max_uses<1: raise ValueError('policy limits invalid')
        if not self.allowed_roles or not self.allowed_scopes or not self.allowed_audiences or not self.trusted_issuers: raise ValueError('policy allowlist empty')
        if self.revoked: raise ValueError('policy revoked')

@dataclass(frozen=True)
class CredentialRecord:
    credential_id:str; task_id:str; run_id:str; subject_id:str; role:str; scopes:FrozenSet[str]; audience:str
    issuer_id:str; issued_at:int; expires_at:int; max_uses:int; use_count:int; verified:bool; evidence_binding:str; revoked:bool=False
    def validate(self)->None:
        if not all((self.credential_id,self.task_id,self.subject_id,self.role,self.audience,self.issuer_id,self.evidence_binding)): raise ValueError('credential identity invalid')
        if self.issued_at<0 or self.expires_at<=self.issued_at: raise ValueError('credential time invalid')
        if self.max_uses<1 or self.use_count<0: raise ValueError('credential use count invalid')
        if not self.scopes: raise ValueError('credential scopes empty')

@dataclass(frozen=True)
class CredentialRequest:
    request_id:str; operation:CredentialOperation; task_id:str; run_id:str; subject_id:str; role:str; scopes:FrozenSet[str]; audience:str
    requested_ttl_seconds:int; expected_policy_id:str; expected_policy_version:str; expected_authority_epoch:int; evidence_binding:str
    credential_id:str=''; task_completed:bool=False
    def validate(self)->None:
        if not all((self.request_id,self.task_id,self.subject_id,self.role,self.audience,self.expected_policy_id,self.expected_policy_version,self.evidence_binding)): raise ValueError('request identity invalid')
        if self.expected_authority_epoch<1: raise ValueError('request authority invalid')
        if self.requested_ttl_seconds<0: raise ValueError('requested ttl invalid')
        if not self.scopes: raise ValueError('request scopes empty')
        if self.operation in {CredentialOperation.USE,CredentialOperation.REVOKE,CredentialOperation.STATUS} and not self.credential_id: raise ValueError('credential id required')

@dataclass(frozen=True)
class PreparedCredentialRegistry:
    registry_fingerprint:str; policy_fingerprint:str; records:Tuple[CredentialRecord,...]
    record_fingerprints:Mapping[str,str]; task_index:Mapping[str,Tuple[str,...]]; run_index:Mapping[str,Tuple[str,...]]; subject_index:Mapping[str,Tuple[str,...]]

@dataclass(frozen=True)
class CredentialRegistryDelta:
    base_fingerprint:str; target_fingerprint:str; changed_records:Tuple[CredentialRecord,...]; removed_credential_ids:Tuple[str,...]; added_records:Tuple[CredentialRecord,...]

@dataclass(frozen=True)
class RegistrySyncPlan:
    missing_or_changed_credential_ids:Tuple[str,...]; metadata_bytes_required:int; full_metadata_bytes:int; full_resend_required:bool
    permission_granted:bool=False; credential_issue_authorized:bool=False; credential_use_authorized:bool=False; revocation_execution_authorized:bool=False

@dataclass(frozen=True)
class CredentialAssessment:
    decision:ControlDecision; operation:CredentialOperation; reasons:Tuple[str,...]; request_id:str; credential_id:str
    credential_candidate_id:str; expires_at_candidate:int; automatic_revoke_candidate:bool; revocation_candidate:bool
    task_bound_candidate:bool; run_bound_candidate:bool; scope_bound_candidate:bool; audience_bound_candidate:bool
    registry_fingerprint:str; policy_fingerprint:str; request_fingerprint:str
    permission_granted:bool=False; credential_issued:bool=False; credential_used:bool=False; revocation_executed:bool=False
    credential_persisted:bool=False; authoritative_credential_state_changed:bool=False; task_success_proven:bool=False; action_success:bool=False

def _canonical(v:Any)->Any:
    if isinstance(v,Enum): return v.value
    if is_dataclass(v): return {f.name:_canonical(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v,Mapping): return {str(k):_canonical(x) for k,x in sorted(v.items(),key=lambda kv:str(kv[0]))}
    if isinstance(v,(set,frozenset)): return sorted((_canonical(x) for x in v),key=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')))
    if isinstance(v,(tuple,list)): return [_canonical(x) for x in v]
    return v

def canonical_json(v:Any)->str: return json.dumps(_canonical(v),ensure_ascii=False,sort_keys=True,separators=(',',':'))
def fingerprint(v:Any)->str: return sha256(canonical_json(v).encode()).hexdigest()
def _records(xs:Iterable[CredentialRecord])->Tuple[CredentialRecord,...]: return tuple(sorted(xs,key=lambda x:x.credential_id))
def registry_fingerprint(records)->str: return fingerprint({'records':_records(records)})

def prepare_registry(policy:CredentialPolicy,records:Iterable[CredentialRecord],*,now:int)->PreparedCredentialRegistry:
    policy.validate(now); rs=_records(records)
    for r in rs: r.validate()
    if len({r.credential_id for r in rs})!=len(rs): raise ValueError('duplicate credential id')
    ti={}; ri={}; si={}
    for r in rs:
        ti.setdefault(r.task_id,[]).append(r.credential_id); ri.setdefault(r.run_id,[]).append(r.credential_id); si.setdefault(r.subject_id,[]).append(r.credential_id)
    return PreparedCredentialRegistry(registry_fingerprint(rs),fingerprint(policy),rs,{r.credential_id:fingerprint(r) for r in rs},{k:tuple(sorted(v)) for k,v in ti.items()},{k:tuple(sorted(v)) for k,v in ri.items()},{k:tuple(sorted(v)) for k,v in si.items()})

def _assessment(dec,req,policy,reg,reasons=(),record:CredentialRecord|None=None,auto=False,revoke=False):
    cid=record.credential_id if record else req.credential_id
    candidate='CRED-CANDIDATE-'+fingerprint({'task':req.task_id,'run':req.run_id,'subject':req.subject_id,'role':req.role,'scopes':req.scopes,'audience':req.audience,'binding':req.evidence_binding})[:20]
    expiry=0 if req.operation is not CredentialOperation.ISSUE else min(policy.expires_at, max(0, req.requested_ttl_seconds)+0)
    if req.operation is CredentialOperation.ISSUE: expiry=0  # filled by caller with absolute candidate time
    return CredentialAssessment(dec,req.operation,tuple(reasons),req.request_id,cid,candidate,expiry,auto,revoke,True,bool(req.run_id),True,True,reg.registry_fingerprint,fingerprint(policy),fingerprint(req))

def _with_expiry(a:CredentialAssessment,expires:int)->CredentialAssessment:
    return CredentialAssessment(a.decision,a.operation,a.reasons,a.request_id,a.credential_id,a.credential_candidate_id,expires,a.automatic_revoke_candidate,a.revocation_candidate,a.task_bound_candidate,a.run_bound_candidate,a.scope_bound_candidate,a.audience_bound_candidate,a.registry_fingerprint,a.policy_fingerprint,a.request_fingerprint)

def evaluate_prepared(req:CredentialRequest,policy:CredentialPolicy,reg:PreparedCredentialRegistry,*,now:int)->CredentialAssessment:
    try: policy.validate(now); req.validate()
    except ValueError as e:
        return CredentialAssessment(ControlDecision.HOLD,getattr(req,'operation',CredentialOperation.STATUS),(f'INVALID_INPUT:{e}',),getattr(req,'request_id',''),getattr(req,'credential_id',''),' ',0,False,False,False,False,False,False,getattr(reg,'registry_fingerprint',''),fingerprint(policy),fingerprint(req))
    if reg.registry_fingerprint!=registry_fingerprint(reg.records): return _assessment(ControlDecision.HOLD,req,policy,reg,('PREPARED_REGISTRY_FINGERPRINT_MISMATCH',))
    if reg.policy_fingerprint!=fingerprint(policy): return _assessment(ControlDecision.HOLD,req,policy,reg,('PREPARED_POLICY_FINGERPRINT_MISMATCH',))
    if req.expected_policy_id!=policy.policy_id: return _assessment(ControlDecision.HOLD,req,policy,reg,('POLICY_ID_MISMATCH',))
    if req.expected_policy_version!=policy.version: return _assessment(ControlDecision.HOLD,req,policy,reg,('POLICY_VERSION_MISMATCH',))
    if req.expected_authority_epoch!=policy.authority_epoch: return _assessment(ControlDecision.HOLD,req,policy,reg,('AUTHORITY_EPOCH_MISMATCH',))
    if req.role not in policy.allowed_roles: return _assessment(ControlDecision.DENY,req,policy,reg,('ROLE_NOT_ALLOWED',))
    if not req.scopes<=policy.allowed_scopes: return _assessment(ControlDecision.DENY,req,policy,reg,('SCOPE_NOT_ALLOWED',))
    if req.audience not in policy.allowed_audiences: return _assessment(ControlDecision.DENY,req,policy,reg,('AUDIENCE_NOT_ALLOWED',))
    if policy.require_run_binding and not req.run_id: return _assessment(ControlDecision.DENY,req,policy,reg,('RUN_BINDING_REQUIRED',))
    if req.operation is CredentialOperation.ISSUE:
        if req.task_completed: return _assessment(ControlDecision.DENY,req,policy,reg,('TASK_ALREADY_COMPLETE',),auto=True,revoke=True)
        if req.requested_ttl_seconds<1: return _assessment(ControlDecision.DENY,req,policy,reg,('TTL_REQUIRED',))
        if req.requested_ttl_seconds>policy.max_ttl_seconds: return _assessment(ControlDecision.DENY,req,policy,reg,('TTL_EXCEEDS_POLICY',))
        dup=[r for r in reg.records if not r.revoked and r.task_id==req.task_id and r.run_id==req.run_id and r.subject_id==req.subject_id and r.role==req.role and r.scopes==req.scopes and r.audience==req.audience and r.evidence_binding==req.evidence_binding and r.expires_at>now and r.use_count<r.max_uses]
        if dup: return _assessment(ControlDecision.HOLD,req,policy,reg,('ACTIVE_MATCHING_CREDENTIAL_EXISTS',),dup[0])
        a=_assessment(ControlDecision.ALLOW,req,policy,reg,('EPHEMERAL_CREDENTIAL_CANDIDATE',),auto=True,revoke=False)
        return _with_expiry(a,min(now+req.requested_ttl_seconds,policy.expires_at))
    rec=next((r for r in reg.records if r.credential_id==req.credential_id),None)
    if rec is None: return _assessment(ControlDecision.HOLD,req,policy,reg,('CREDENTIAL_NOT_FOUND',))
    if policy.require_verified_record and not rec.verified: return _assessment(ControlDecision.HOLD,req,policy,reg,('CREDENTIAL_UNVERIFIED',),rec)
    if rec.issuer_id not in policy.trusted_issuers: return _assessment(ControlDecision.HOLD,req,policy,reg,('UNTRUSTED_ISSUER',),rec)
    if rec.revoked: return _assessment(ControlDecision.DENY,req,policy,reg,('CREDENTIAL_REVOKED',),rec)
    if rec.issued_at>now: return _assessment(ControlDecision.HOLD,req,policy,reg,('CREDENTIAL_FROM_FUTURE',),rec)
    if now>=rec.expires_at: return _assessment(ControlDecision.DENY,req,policy,reg,('CREDENTIAL_EXPIRED',),rec,auto=True,revoke=True)
    if rec.expires_at-rec.issued_at>policy.max_ttl_seconds: return _assessment(ControlDecision.DENY,req,policy,reg,('CREDENTIAL_TTL_POLICY_VIOLATION',),rec,auto=True,revoke=True)
    if rec.max_uses>policy.max_uses: return _assessment(ControlDecision.DENY,req,policy,reg,('CREDENTIAL_USE_LIMIT_POLICY_VIOLATION',),rec,auto=True,revoke=True)
    if rec.evidence_binding!=req.evidence_binding: return _assessment(ControlDecision.DENY,req,policy,reg,('EVIDENCE_BINDING_MISMATCH',),rec)
    if rec.task_id!=req.task_id: return _assessment(ControlDecision.DENY,req,policy,reg,('TASK_BINDING_MISMATCH',),rec)
    if policy.require_run_binding and rec.run_id!=req.run_id: return _assessment(ControlDecision.DENY,req,policy,reg,('RUN_BINDING_MISMATCH',),rec)
    if rec.subject_id!=req.subject_id: return _assessment(ControlDecision.DENY,req,policy,reg,('SUBJECT_BINDING_MISMATCH',),rec)
    if rec.role!=req.role: return _assessment(ControlDecision.DENY,req,policy,reg,('ROLE_BINDING_MISMATCH',),rec)
    if req.scopes!=rec.scopes: return _assessment(ControlDecision.DENY,req,policy,reg,('SCOPE_BINDING_MISMATCH',),rec)
    if req.audience!=rec.audience: return _assessment(ControlDecision.DENY,req,policy,reg,('AUDIENCE_BINDING_MISMATCH',),rec)
    if req.task_completed:
        return _assessment(ControlDecision.DENY,req,policy,reg,('TASK_COMPLETE_AUTOMATIC_REVOKE_CANDIDATE',),rec,auto=True,revoke=True)
    if req.operation is CredentialOperation.USE:
        if rec.use_count>=rec.max_uses: return _assessment(ControlDecision.DENY,req,policy,reg,('USE_LIMIT_EXHAUSTED',),rec,auto=True,revoke=True)
        return _assessment(ControlDecision.ALLOW,req,policy,reg,('CREDENTIAL_USE_CANDIDATE',),rec,auto=(rec.use_count+1>=rec.max_uses),revoke=(rec.use_count+1>=rec.max_uses))
    if req.operation is CredentialOperation.REVOKE:
        return _assessment(ControlDecision.ALLOW,req,policy,reg,('REVOCATION_CANDIDATE',),rec,auto=False,revoke=True)
    return _assessment(ControlDecision.ALLOW,req,policy,reg,('CREDENTIAL_STATUS_CANDIDATE',),rec)

def evaluate(req,policy,records,*,now:int)->CredentialAssessment:
    try: reg=prepare_registry(policy,records,now=now)
    except ValueError as e:
        return CredentialAssessment(ControlDecision.HOLD,getattr(req,'operation',CredentialOperation.STATUS),(f'INVALID_REGISTRY:{e}',),getattr(req,'request_id',''),getattr(req,'credential_id',''),' ',0,False,False,False,False,False,False,'',fingerprint(policy),fingerprint(req))
    return evaluate_prepared(req,policy,reg,now=now)

def make_registry_delta(base_records,target_records)->CredentialRegistryDelta:
    b={r.credential_id:r for r in _records(base_records)}; t={r.credential_id:r for r in _records(target_records)}
    ch=tuple(sorted((r for k,r in t.items() if k in b and fingerprint(r)!=fingerprint(b[k])),key=lambda r:r.credential_id))
    rm=tuple(sorted(k for k in b if k not in t)); ad=tuple(sorted((r for k,r in t.items() if k not in b),key=lambda r:r.credential_id))
    return CredentialRegistryDelta(registry_fingerprint(base_records),registry_fingerprint(target_records),ch,rm,ad)

def apply_registry_delta(base_records,delta:CredentialRegistryDelta):
    if registry_fingerprint(base_records)!=delta.base_fingerprint: raise ValueError('delta base fingerprint mismatch')
    items={r.credential_id:r for r in _records(base_records)}
    for k in delta.removed_credential_ids:
        if k not in items: raise ValueError('invalid removal')
        del items[k]
    for r in delta.changed_records:
        if r.credential_id not in items: raise ValueError('invalid change')
        items[r.credential_id]=r
    for r in delta.added_records:
        if r.credential_id in items: raise ValueError('invalid add')
        items[r.credential_id]=r
    out=tuple(sorted(items.values(),key=lambda r:r.credential_id))
    if registry_fingerprint(out)!=delta.target_fingerprint: raise ValueError('delta target fingerprint mismatch')
    return out

def plan_registry_sync(records,remote_fps:Mapping[str,str])->RegistrySyncPlan:
    rs=_records(records); ids=tuple(r.credential_id for r in rs if remote_fps.get(r.credential_id)!=fingerprint(r)); mp={r.credential_id:r for r in rs}
    meta=len(canonical_json({'records':[mp[k] for k in ids]}).encode()); full=len(canonical_json({'records':rs}).encode())
    return RegistrySyncPlan(ids,meta,full,full>0 and meta/full>=0.8)

def assessment_digest(a:CredentialAssessment)->str: return fingerprint(a)

def default_policy(now:int)->CredentialPolicy:
    return CredentialPolicy('CRED-058','1',1,now-100,now+10000,900,1,frozenset({'TASK_AGENT'}),frozenset({'READ_RESOURCE'}),frozenset({'API-A'}),frozenset({'ISSUER-058'}),True,True,False)
def default_request(now:int)->CredentialRequest:
    return CredentialRequest('REQ-058',CredentialOperation.ISSUE,'TASK-058','RUN-058','AGENT-058','TASK_AGENT',frozenset({'READ_RESOURCE'}),'API-A',300,'CRED-058','1',1,'BIND-058')
def default_records(now:int): return ()
def default_active_record(now:int)->CredentialRecord:
    return CredentialRecord('CRED-058-ACTIVE','TASK-058','RUN-058','AGENT-058','TASK_AGENT',frozenset({'READ_RESOURCE'}),'API-A','ISSUER-058',now-10,now+290,1,0,True,'BIND-058',False)
