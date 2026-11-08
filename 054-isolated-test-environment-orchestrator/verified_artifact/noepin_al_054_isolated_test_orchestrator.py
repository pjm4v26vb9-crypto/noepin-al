"""NOEPIN AL 054 — Isolated Test Environment Orchestrator.

Pure control-plane evaluator for ephemeral sandbox plans and externally observed
sandbox-run evidence. It never launches code, tools, MCPs, networks, containers,
or production actions. It validates isolation metadata and returns a deterministic
candidate verdict only.

Creator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support using ChatGPT
License / Rights: NOT SPECIFIED
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
from hashlib import sha256
import json
from typing import Any, FrozenSet, Iterable, Mapping, Tuple

class ControlDecision(str, Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class TestRisk(str, Enum):
    LOW='LOW'; MEDIUM='MEDIUM'; HIGH='HIGH'; CRITICAL='CRITICAL'

@dataclass(frozen=True)
class SandboxPolicy:
    policy_id:str; version:str; authority_epoch:int; issued_at:int; expires_at:int
    allowed_subject_types:FrozenSet[str]; allowed_network_modes:FrozenSet[str]
    allowed_filesystem_modes:FrozenSet[str]; max_run_seconds:int; max_output_bytes:int
    max_evidence_age_seconds:int; require_ephemeral:bool=True; require_fake_secrets:bool=True
    forbid_privileged:bool=True; forbid_persistence:bool=True; forbid_external_services:bool=True
    high_risk_requires_human:bool=True; revoked:bool=False
    def validate(self, now:int)->None:
        if not self.policy_id or not self.version or self.authority_epoch<1: raise ValueError('policy identity invalid')
        if self.issued_at<0 or self.expires_at<=self.issued_at or not self.issued_at<=now<self.expires_at: raise ValueError('policy not current')
        if not self.allowed_subject_types or not self.allowed_network_modes or not self.allowed_filesystem_modes: raise ValueError('policy allowsets required')
        if self.max_run_seconds<1 or self.max_output_bytes<1 or self.max_evidence_age_seconds<1: raise ValueError('policy limits invalid')

@dataclass(frozen=True)
class SandboxProfile:
    profile_id:str; ephemeral:bool; fake_secrets_only:bool; real_secrets_mounted:bool
    network_mode:str; filesystem_mode:str; privileged:bool; persistence_enabled:bool
    external_service_access:bool; created_at:int; evidence_binding:str; revoked:bool=False
    def validate(self)->None:
        if not self.profile_id or not self.network_mode or not self.filesystem_mode or not self.evidence_binding: raise ValueError('profile identity required')
        if self.created_at<0: raise ValueError('profile timestamp invalid')

@dataclass(frozen=True)
class SandboxRunEvidence:
    evidence_id:str; run_id:str; observer_id:str; independent_observer:bool; verified:bool
    started_at:int; ended_at:int; network_attempted:bool; network_escaped:bool
    real_secret_accessed:bool; filesystem_persisted:bool; privileged_used:bool
    host_mutation_observed:bool; external_service_contacted:bool; output_bytes:int
    terminated:bool; evidence_binding:str; revoked:bool=False
    def validate(self)->None:
        if not self.evidence_id or not self.run_id or not self.observer_id or not self.evidence_binding: raise ValueError('evidence identity required')
        if self.started_at<0 or self.ended_at<self.started_at or self.output_bytes<0: raise ValueError('evidence metrics invalid')

@dataclass(frozen=True)
class TestRequest:
    run_id:str; subject_id:str; subject_type:str; artifact_fingerprint:str; risk:TestRisk
    requested_profile_id:str; requested_network_mode:str; requested_filesystem_mode:str
    max_run_seconds:int; expected_policy_id:str; expected_policy_version:str
    expected_authority_epoch:int; evidence_binding:str
    def validate(self)->None:
        if not self.run_id or not self.subject_id or not self.subject_type or not self.requested_profile_id: raise ValueError('request identity required')
        _sha(self.artifact_fingerprint)
        if self.max_run_seconds<1 or not self.expected_policy_id or not self.expected_policy_version or self.expected_authority_epoch<1 or not self.evidence_binding: raise ValueError('request metadata invalid')

@dataclass(frozen=True)
class PreparedSandboxRegistry:
    registry_fingerprint:str; policy_fingerprint:str
    profiles:Tuple[SandboxProfile,...]; evidence:Tuple[SandboxRunEvidence,...]
    profile_fingerprints:Mapping[str,str]; evidence_fingerprints:Mapping[str,str]
    run_evidence_index:Mapping[str,Tuple[str,...]]

@dataclass(frozen=True)
class SandboxRegistryDelta:
    base_fingerprint:str; target_fingerprint:str
    changed_profiles:Tuple[SandboxProfile,...]; removed_profile_ids:Tuple[str,...]; added_profiles:Tuple[SandboxProfile,...]
    changed_evidence:Tuple[SandboxRunEvidence,...]; removed_evidence_ids:Tuple[str,...]; added_evidence:Tuple[SandboxRunEvidence,...]

@dataclass(frozen=True)
class RegistrySyncPlan:
    missing_or_changed_profile_ids:Tuple[str,...]; missing_or_changed_evidence_ids:Tuple[str,...]
    metadata_bytes_required:int; full_metadata_bytes:int; full_resend_required:bool
    permission_granted:bool=False; sandbox_execution_authorized:bool=False
    production_execution_authorized:bool=False; real_secret_access_authorized:bool=False
    network_egress_authorized:bool=False

@dataclass(frozen=True)
class SandboxVerdict:
    decision:ControlDecision; reasons:Tuple[str,...]; run_id:str; subject_id:str
    profile_id:str; valid_evidence_ids:Tuple[str,...]; sandbox_ready_candidate:bool
    sandbox_pass_candidate:bool; human_review_candidate:bool
    registry_fingerprint:str; policy_fingerprint:str; request_fingerprint:str
    permission_granted:bool=False; sandbox_execution_started:bool=False
    production_execution_started:bool=False; real_secret_accessed:bool=False
    network_egress_performed:bool=False; host_mutation_performed:bool=False
    production_safe_proven:bool=False; action_success:bool=False

def _sha(v:str)->None:
    if len(v)!=64 or any(c not in '0123456789abcdef' for c in v.lower()): raise ValueError('sha256 invalid')
def _canonical(v:Any)->Any:
    if isinstance(v,Enum): return v.value
    if is_dataclass(v): return {f.name:_canonical(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v,Mapping): return {str(k):_canonical(x) for k,x in sorted(v.items(),key=lambda kv:str(kv[0]))}
    if isinstance(v,(set,frozenset)): return sorted((_canonical(x) for x in v),key=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')))
    if isinstance(v,(tuple,list)): return [_canonical(x) for x in v]
    return v
def canonical_json(v:Any)->str: return json.dumps(_canonical(v),ensure_ascii=False,sort_keys=True,separators=(',',':'))
def fingerprint(v:Any)->str: return sha256(canonical_json(v).encode()).hexdigest()
def _profiles(xs:Iterable[SandboxProfile])->Tuple[SandboxProfile,...]: return tuple(sorted(xs,key=lambda x:x.profile_id))
def _evidence(xs:Iterable[SandboxRunEvidence])->Tuple[SandboxRunEvidence,...]: return tuple(sorted(xs,key=lambda x:x.evidence_id))
def registry_fingerprint(ps:Iterable[SandboxProfile], es:Iterable[SandboxRunEvidence])->str: return fingerprint((_profiles(ps),_evidence(es)))

def prepare_registry(policy:SandboxPolicy, profiles:Iterable[SandboxProfile], evidence:Iterable[SandboxRunEvidence], *, now:int)->PreparedSandboxRegistry:
    policy.validate(now); ps=_profiles(profiles); es=_evidence(evidence)
    for x in ps: x.validate()
    for x in es: x.validate()
    if len({x.profile_id for x in ps})!=len(ps) or len({x.evidence_id for x in es})!=len(es): raise ValueError('duplicate registry id')
    ridx={}
    for x in es: ridx.setdefault(x.run_id,[]).append(x.evidence_id)
    return PreparedSandboxRegistry(registry_fingerprint(ps,es),fingerprint(policy),ps,es,
        {x.profile_id:fingerprint(x) for x in ps},{x.evidence_id:fingerprint(x) for x in es},
        {k:tuple(sorted(v)) for k,v in ridx.items()})

def _verdict(dec,req,policy,reg,reasons=(),profile_id='',evidence_ids=(),ready=False,passed=False,human=False):
    return SandboxVerdict(dec,tuple(reasons),req.run_id,req.subject_id,profile_id,tuple(evidence_ids),ready,passed,human,reg.registry_fingerprint,fingerprint(policy),fingerprint(req))

def evaluate_prepared(req:TestRequest, policy:SandboxPolicy, reg:PreparedSandboxRegistry, *, now:int)->SandboxVerdict:
    try: req.validate(); policy.validate(now)
    except ValueError as e:
        return SandboxVerdict(ControlDecision.HOLD,(f'INVALID_INPUT:{e}',),getattr(req,'run_id',''),getattr(req,'subject_id',''),'',(),False,False,False,getattr(reg,'registry_fingerprint',''),fingerprint(policy),fingerprint(req))
    if policy.revoked: return _verdict(ControlDecision.HOLD,req,policy,reg,('POLICY_REVOKED',))
    if req.expected_policy_id!=policy.policy_id: return _verdict(ControlDecision.HOLD,req,policy,reg,('POLICY_ID_MISMATCH',))
    if req.expected_policy_version!=policy.version: return _verdict(ControlDecision.HOLD,req,policy,reg,('POLICY_VERSION_MISMATCH',))
    if req.expected_authority_epoch!=policy.authority_epoch: return _verdict(ControlDecision.HOLD,req,policy,reg,('AUTHORITY_EPOCH_MISMATCH',))
    if reg.policy_fingerprint!=fingerprint(policy): return _verdict(ControlDecision.HOLD,req,policy,reg,('PREPARED_POLICY_FINGERPRINT_MISMATCH',))
    if reg.registry_fingerprint!=registry_fingerprint(reg.profiles,reg.evidence): return _verdict(ControlDecision.HOLD,req,policy,reg,('PREPARED_REGISTRY_FINGERPRINT_MISMATCH',))
    if req.subject_type not in policy.allowed_subject_types: return _verdict(ControlDecision.DENY,req,policy,reg,('SUBJECT_TYPE_NOT_ALLOWED',))
    if req.requested_network_mode not in policy.allowed_network_modes: return _verdict(ControlDecision.DENY,req,policy,reg,('REQUESTED_NETWORK_MODE_NOT_ALLOWED',))
    if req.requested_filesystem_mode not in policy.allowed_filesystem_modes: return _verdict(ControlDecision.DENY,req,policy,reg,('REQUESTED_FILESYSTEM_MODE_NOT_ALLOWED',))
    if req.max_run_seconds>policy.max_run_seconds: return _verdict(ControlDecision.DENY,req,policy,reg,('RUN_DURATION_LIMIT_EXCEEDED',))
    prof=next((x for x in reg.profiles if x.profile_id==req.requested_profile_id and not x.revoked),None)
    if prof is None: return _verdict(ControlDecision.HOLD,req,policy,reg,('ACTIVE_SANDBOX_PROFILE_REQUIRED',))
    if prof.evidence_binding!=req.evidence_binding: return _verdict(ControlDecision.HOLD,req,policy,reg,('PROFILE_EVIDENCE_BINDING_MISMATCH',),prof.profile_id)
    if policy.require_ephemeral and not prof.ephemeral: return _verdict(ControlDecision.DENY,req,policy,reg,('SANDBOX_NOT_EPHEMERAL',),prof.profile_id)
    if policy.require_fake_secrets and (not prof.fake_secrets_only or prof.real_secrets_mounted): return _verdict(ControlDecision.DENY,req,policy,reg,('REAL_SECRET_ISOLATION_VIOLATION',),prof.profile_id)
    if prof.network_mode!=req.requested_network_mode or prof.network_mode not in policy.allowed_network_modes: return _verdict(ControlDecision.DENY,req,policy,reg,('NETWORK_ISOLATION_MISMATCH',),prof.profile_id)
    if prof.filesystem_mode!=req.requested_filesystem_mode or prof.filesystem_mode not in policy.allowed_filesystem_modes: return _verdict(ControlDecision.DENY,req,policy,reg,('FILESYSTEM_ISOLATION_MISMATCH',),prof.profile_id)
    if policy.forbid_privileged and prof.privileged: return _verdict(ControlDecision.DENY,req,policy,reg,('PRIVILEGED_SANDBOX_FORBIDDEN',),prof.profile_id)
    if policy.forbid_persistence and prof.persistence_enabled: return _verdict(ControlDecision.DENY,req,policy,reg,('PERSISTENT_SANDBOX_FORBIDDEN',),prof.profile_id)
    if policy.forbid_external_services and prof.external_service_access: return _verdict(ControlDecision.DENY,req,policy,reg,('EXTERNAL_SERVICE_ACCESS_FORBIDDEN',),prof.profile_id)
    evs=[]
    for e in reg.evidence:
        if e.run_id!=req.run_id or e.revoked or not e.verified or not e.independent_observer: continue
        if e.evidence_binding!=req.evidence_binding: continue
        if e.ended_at>now or now-e.ended_at>policy.max_evidence_age_seconds: continue
        evs.append(e)
    if not evs: return _verdict(ControlDecision.HOLD,req,policy,reg,('INDEPENDENT_RUN_EVIDENCE_REQUIRED',),prof.profile_id,ready=True)
    ids=tuple(sorted(x.evidence_id for x in evs))
    if any(x.ended_at-x.started_at>req.max_run_seconds for x in evs): return _verdict(ControlDecision.DENY,req,policy,reg,('OBSERVED_RUN_DURATION_EXCEEDED',),prof.profile_id,ids,True)
    if any(x.output_bytes>policy.max_output_bytes for x in evs): return _verdict(ControlDecision.DENY,req,policy,reg,('OUTPUT_LIMIT_EXCEEDED',),prof.profile_id,ids,True)
    if any(x.network_escaped or (prof.network_mode=='DENY' and x.network_attempted) for x in evs): return _verdict(ControlDecision.DENY,req,policy,reg,('NETWORK_ISOLATION_BREACH',),prof.profile_id,ids,True)
    if any(x.real_secret_accessed for x in evs): return _verdict(ControlDecision.DENY,req,policy,reg,('REAL_SECRET_ACCESS_OBSERVED',),prof.profile_id,ids,True)
    if any(x.filesystem_persisted or x.host_mutation_observed for x in evs): return _verdict(ControlDecision.DENY,req,policy,reg,('HOST_OR_PERSISTENCE_MUTATION_OBSERVED',),prof.profile_id,ids,True)
    if any(x.privileged_used for x in evs): return _verdict(ControlDecision.DENY,req,policy,reg,('PRIVILEGED_USE_OBSERVED',),prof.profile_id,ids,True)
    if any(x.external_service_contacted for x in evs): return _verdict(ControlDecision.DENY,req,policy,reg,('EXTERNAL_SERVICE_CONTACT_OBSERVED',),prof.profile_id,ids,True)
    if any(not x.terminated for x in evs): return _verdict(ControlDecision.HOLD,req,policy,reg,('RUN_TERMINATION_EVIDENCE_REQUIRED',),prof.profile_id,ids,True)
    if policy.high_risk_requires_human and req.risk in (TestRisk.HIGH,TestRisk.CRITICAL):
        return _verdict(ControlDecision.HUMAN_APPROVAL,req,policy,reg,('HIGH_RISK_PRODUCTION_PROMOTION_REQUIRES_HUMAN',),prof.profile_id,ids,True,True,True)
    return _verdict(ControlDecision.ALLOW,req,policy,reg,('SANDBOX_ISOLATION_EVIDENCE_PASS',),prof.profile_id,ids,True,True,False)

def evaluate(req:TestRequest, policy:SandboxPolicy, profiles:Iterable[SandboxProfile], evidence:Iterable[SandboxRunEvidence], *, now:int)->SandboxVerdict:
    try: reg=prepare_registry(policy,profiles,evidence,now=now)
    except ValueError as e:
        return SandboxVerdict(ControlDecision.HOLD,(f'INVALID_REGISTRY:{e}',),getattr(req,'run_id',''),getattr(req,'subject_id',''),'',(),False,False,False,'',fingerprint(policy),fingerprint(req))
    return evaluate_prepared(req,policy,reg,now=now)

def make_registry_delta(base_profiles,base_evidence,target_profiles,target_evidence)->SandboxRegistryDelta:
    bp={x.profile_id:x for x in base_profiles}; be={x.evidence_id:x for x in base_evidence}; tp={x.profile_id:x for x in target_profiles}; te={x.evidence_id:x for x in target_evidence}
    cp=tuple(sorted((v for k,v in tp.items() if k in bp and fingerprint(v)!=fingerprint(bp[k])),key=lambda x:x.profile_id))
    ap=tuple(sorted((v for k,v in tp.items() if k not in bp),key=lambda x:x.profile_id)); rp=tuple(sorted(k for k in bp if k not in tp))
    ce=tuple(sorted((v for k,v in te.items() if k in be and fingerprint(v)!=fingerprint(be[k])),key=lambda x:x.evidence_id))
    ae=tuple(sorted((v for k,v in te.items() if k not in be),key=lambda x:x.evidence_id)); re=tuple(sorted(k for k in be if k not in te))
    return SandboxRegistryDelta(registry_fingerprint(base_profiles,base_evidence),registry_fingerprint(target_profiles,target_evidence),cp,rp,ap,ce,re,ae)

def apply_registry_delta(base_profiles,base_evidence,delta:SandboxRegistryDelta):
    if registry_fingerprint(base_profiles,base_evidence)!=delta.base_fingerprint: raise ValueError('delta base fingerprint mismatch')
    ps={x.profile_id:x for x in base_profiles}; es={x.evidence_id:x for x in base_evidence}
    for k in delta.removed_profile_ids:
        if k not in ps: raise ValueError('invalid profile removal')
        del ps[k]
    for x in delta.changed_profiles:
        if x.profile_id not in ps: raise ValueError('invalid profile change')
        ps[x.profile_id]=x
    for x in delta.added_profiles:
        if x.profile_id in ps: raise ValueError('invalid profile add')
        ps[x.profile_id]=x
    for k in delta.removed_evidence_ids:
        if k not in es: raise ValueError('invalid evidence removal')
        del es[k]
    for x in delta.changed_evidence:
        if x.evidence_id not in es: raise ValueError('invalid evidence change')
        es[x.evidence_id]=x
    for x in delta.added_evidence:
        if x.evidence_id in es: raise ValueError('invalid evidence add')
        es[x.evidence_id]=x
    outp=_profiles(ps.values()); oute=_evidence(es.values())
    if registry_fingerprint(outp,oute)!=delta.target_fingerprint: raise ValueError('delta target fingerprint mismatch')
    return outp,oute

def plan_registry_sync(profiles,evidence,remote_known:Mapping[str,str])->RegistrySyncPlan:
    ps=_profiles(profiles); es=_evidence(evidence)
    mp=tuple(x.profile_id for x in ps if remote_known.get('profile:'+x.profile_id)!=fingerprint(x))
    me=tuple(x.evidence_id for x in es if remote_known.get('evidence:'+x.evidence_id)!=fingerprint(x))
    pmap={x.profile_id:x for x in ps}; emap={x.evidence_id:x for x in es}
    selected={'profiles':[pmap[k] for k in mp],'evidence':[emap[k] for k in me]}
    meta=len(canonical_json(selected).encode()); full=len(canonical_json({'profiles':ps,'evidence':es}).encode())
    return RegistrySyncPlan(mp,me,meta,full,full>0 and meta/full>=0.8)

def default_policy(now:int)->SandboxPolicy:
    return SandboxPolicy('SANDBOX-054','1',1,now-100,now+10000,frozenset({'AI','MCP','CODE','TOOL'}),frozenset({'DENY','LOOPBACK_ONLY'}),frozenset({'TEMP_ONLY'}),120,1_000_000,3600,True,True,True,True,True,True,False)
def default_request(now:int)->TestRequest:
    return TestRequest('RUN-054','SUBJECT-054','MCP',fingerprint(('artifact',54)),TestRisk.MEDIUM,'PROFILE-054','DENY','TEMP_ONLY',60,'SANDBOX-054','1',1,'BIND-054')
def default_registry(now:int):
    p=(SandboxProfile('PROFILE-054',True,True,False,'DENY','TEMP_ONLY',False,False,False,now-50,'BIND-054',False),)
    e=(SandboxRunEvidence('EVID-054','RUN-054','MONITOR-054',True,True,now-30,now-20,False,False,False,False,False,False,False,2048,True,'BIND-054',False),)
    return p,e
