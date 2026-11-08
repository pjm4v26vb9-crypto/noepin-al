"""NOEPIN AL 059 — External AI / Tool Trust Score.

Pure control-plane evaluator for external AI/tool reputation, trust tier and probation
candidates. It evaluates caller-supplied entity profiles and trust evidence with
freshness, revocation, binding and privilege constraints. It does not connect to an
external AI/tool, grant permission or high privilege, establish trust truth, complete
probation, or prove future safety/action success.

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
class EntityType(str, Enum):
    AI='AI'; TOOL='TOOL'; SERVICE='SERVICE'
class TrustTier(str, Enum):
    BLOCKED='BLOCKED'; UNTRUSTED='UNTRUSTED'; PROBATION='PROBATION'; LIMITED='LIMITED'; ESTABLISHED='ESTABLISHED'
class TrustOperation(str, Enum):
    ASSESS='ASSESS'; CONNECT='CONNECT'; REQUEST_PRIVILEGE='REQUEST_PRIVILEGE'
class PrivilegeLevel(str, Enum):
    NONE='NONE'; READ_ONLY='READ_ONLY'; STANDARD='STANDARD'; HIGH='HIGH'; ADMIN='ADMIN'
class EvidenceKind(str, Enum):
    SIGNATURE='SIGNATURE'; RELIABILITY='RELIABILITY'; INCIDENT='INCIDENT'; POLICY='POLICY'; PROBATION='PROBATION'; PERMISSION_REQUEST='PERMISSION_REQUEST'

@dataclass(frozen=True)
class TrustPolicy:
    policy_id:str; version:str; authority_epoch:int; issued_at:int; expires_at:int
    trusted_providers:FrozenSet[str]; allowed_entity_types:FrozenSet[EntityType]
    min_evidence_for_limited:int; min_evidence_for_established:int
    probation_score:int; limited_score:int; established_score:int; deny_score:int
    max_evidence_age_seconds:int; high_privilege_min_score:int; high_privilege_min_positive_events:int
    disallowed_privileges:FrozenSet[PrivilegeLevel]; revoked:bool=False
    def validate(self,now:int)->None:
        if not self.policy_id or not self.version or self.authority_epoch<1: raise ValueError('policy identity invalid')
        if self.issued_at<0 or self.expires_at<=self.issued_at or not self.issued_at<=now<self.expires_at: raise ValueError('policy not current')
        if not self.trusted_providers or not self.allowed_entity_types: raise ValueError('policy allowlist empty')
        if not (0<=self.deny_score<self.probation_score<=self.limited_score<=self.established_score<=100): raise ValueError('trust thresholds invalid')
        if not (0<=self.high_privilege_min_score<=100): raise ValueError('high privilege threshold invalid')
        if self.min_evidence_for_limited<1 or self.min_evidence_for_established<self.min_evidence_for_limited: raise ValueError('evidence thresholds invalid')
        if self.max_evidence_age_seconds<1 or self.high_privilege_min_positive_events<1: raise ValueError('policy numeric limits invalid')
        if self.revoked: raise ValueError('policy revoked')

@dataclass(frozen=True)
class ExternalEntityProfile:
    entity_id:str; entity_type:EntityType; provider_id:str; identity_fingerprint:str
    registered_at:int; last_verified_at:int; verified:bool; evidence_binding:str; revoked:bool=False
    def validate(self)->None:
        if not all((self.entity_id,self.provider_id,self.identity_fingerprint,self.evidence_binding)): raise ValueError('profile identity invalid')
        if self.registered_at<0 or self.last_verified_at<self.registered_at: raise ValueError('profile time invalid')

@dataclass(frozen=True)
class TrustEvidence:
    evidence_id:str; entity_id:str; kind:EvidenceKind; observed_at:int; expires_at:int
    impact:int; verified:bool; independent:bool; source_id:str; evidence_binding:str; revoked:bool=False
    def validate(self)->None:
        if not all((self.evidence_id,self.entity_id,self.source_id,self.evidence_binding)): raise ValueError('evidence identity invalid')
        if self.observed_at<0 or self.expires_at<=self.observed_at: raise ValueError('evidence time invalid')
        if not -40<=self.impact<=40: raise ValueError('evidence impact invalid')

@dataclass(frozen=True)
class TrustRequest:
    request_id:str; operation:TrustOperation; entity_id:str; expected_identity_fingerprint:str
    requested_privilege:PrivilegeLevel; expected_policy_id:str; expected_policy_version:str; expected_authority_epoch:int
    evidence_binding:str; high_impact_context:bool=False
    def validate(self)->None:
        if not all((self.request_id,self.entity_id,self.expected_identity_fingerprint,self.expected_policy_id,self.expected_policy_version,self.evidence_binding)): raise ValueError('request identity invalid')
        if self.expected_authority_epoch<1: raise ValueError('request authority invalid')

@dataclass(frozen=True)
class PreparedTrustRegistry:
    registry_fingerprint:str; policy_fingerprint:str; profiles:Tuple[ExternalEntityProfile,...]; evidence:Tuple[TrustEvidence,...]
    profile_fingerprints:Mapping[str,str]; evidence_fingerprints:Mapping[str,str]
    entity_evidence_index:Mapping[str,Tuple[str,...]]; provider_index:Mapping[str,Tuple[str,...]]

@dataclass(frozen=True)
class TrustRegistryDelta:
    base_fingerprint:str; target_fingerprint:str
    changed_profiles:Tuple[ExternalEntityProfile,...]; removed_profile_ids:Tuple[str,...]; added_profiles:Tuple[ExternalEntityProfile,...]
    changed_evidence:Tuple[TrustEvidence,...]; removed_evidence_ids:Tuple[str,...]; added_evidence:Tuple[TrustEvidence,...]

@dataclass(frozen=True)
class RegistrySyncPlan:
    missing_or_changed_profile_ids:Tuple[str,...]; missing_or_changed_evidence_ids:Tuple[str,...]
    metadata_bytes_required:int; full_metadata_bytes:int; full_resend_required:bool
    permission_granted:bool=False; connection_authorized:bool=False; high_privilege_authorized:bool=False; probation_completion_authorized:bool=False

@dataclass(frozen=True)
class TrustAssessment:
    decision:ControlDecision; request_id:str; entity_id:str; reasons:Tuple[str,...]
    trust_score:int; trust_tier:TrustTier; probation_candidate:bool; connection_candidate:bool; privilege_candidate:PrivilegeLevel
    active_evidence_count:int; positive_evidence_count:int; negative_evidence_count:int
    registry_fingerprint:str; policy_fingerprint:str; request_fingerprint:str
    permission_granted:bool=False; connection_established:bool=False; high_privilege_granted:bool=False
    probation_completed:bool=False; trust_truth_proven:bool=False; future_safety_proven:bool=False; action_success:bool=False

def _canonical(v:Any)->Any:
    if isinstance(v,Enum): return v.value
    if is_dataclass(v): return {f.name:_canonical(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v,Mapping): return {str(k):_canonical(x) for k,x in sorted(v.items(),key=lambda kv:str(kv[0]))}
    if isinstance(v,(set,frozenset)): return sorted((_canonical(x) for x in v),key=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')))
    if isinstance(v,(tuple,list)): return [_canonical(x) for x in v]
    return v

def canonical_json(v:Any)->str: return json.dumps(_canonical(v),ensure_ascii=False,sort_keys=True,separators=(',',':'))
def fingerprint(v:Any)->str: return sha256(canonical_json(v).encode()).hexdigest()
def _profiles(xs:Iterable[ExternalEntityProfile])->Tuple[ExternalEntityProfile,...]: return tuple(sorted(xs,key=lambda x:x.entity_id))
def _evidence(xs:Iterable[TrustEvidence])->Tuple[TrustEvidence,...]: return tuple(sorted(xs,key=lambda x:x.evidence_id))
def registry_fingerprint(profiles,evidence)->str: return fingerprint({'profiles':_profiles(profiles),'evidence':_evidence(evidence)})

def prepare_registry(policy:TrustPolicy,profiles:Iterable[ExternalEntityProfile],evidence:Iterable[TrustEvidence],*,now:int)->PreparedTrustRegistry:
    policy.validate(now); ps=_profiles(profiles); es=_evidence(evidence)
    for p in ps: p.validate()
    for e in es: e.validate()
    if len({p.entity_id for p in ps})!=len(ps): raise ValueError('duplicate entity id')
    if len({e.evidence_id for e in es})!=len(es): raise ValueError('duplicate evidence id')
    entity_ids={p.entity_id for p in ps}
    if any(e.entity_id not in entity_ids for e in es): raise ValueError('evidence references unknown entity')
    ei={}; pi={}
    for e in es: ei.setdefault(e.entity_id,[]).append(e.evidence_id)
    for p in ps: pi.setdefault(p.provider_id,[]).append(p.entity_id)
    return PreparedTrustRegistry(registry_fingerprint(ps,es),fingerprint(policy),ps,es,{p.entity_id:fingerprint(p) for p in ps},{e.evidence_id:fingerprint(e) for e in es},{k:tuple(sorted(v)) for k,v in ei.items()},{k:tuple(sorted(v)) for k,v in pi.items()})

def _empty(req:TrustRequest,policy:TrustPolicy,reg:PreparedTrustRegistry,decision:ControlDecision,reasons:Tuple[str,...])->TrustAssessment:
    return TrustAssessment(decision,getattr(req,'request_id',''),getattr(req,'entity_id',''),reasons,0,TrustTier.UNTRUSTED,False,False,PrivilegeLevel.NONE,0,0,0,getattr(reg,'registry_fingerprint',''),fingerprint(policy),fingerprint(req))

def _tier(score:int,count:int,policy:TrustPolicy)->TrustTier:
    if score<policy.deny_score: return TrustTier.BLOCKED
    if score<policy.probation_score: return TrustTier.UNTRUSTED
    if score<policy.limited_score or count<policy.min_evidence_for_limited: return TrustTier.PROBATION
    if score<policy.established_score or count<policy.min_evidence_for_established: return TrustTier.LIMITED
    return TrustTier.ESTABLISHED

def evaluate_prepared(req:TrustRequest,policy:TrustPolicy,reg:PreparedTrustRegistry,*,now:int)->TrustAssessment:
    try: policy.validate(now); req.validate()
    except ValueError as e: return _empty(req,policy,reg,ControlDecision.HOLD,(f'INVALID_INPUT:{e}',))
    if reg.registry_fingerprint!=registry_fingerprint(reg.profiles,reg.evidence): return _empty(req,policy,reg,ControlDecision.HOLD,('PREPARED_REGISTRY_FINGERPRINT_MISMATCH',))
    if reg.policy_fingerprint!=fingerprint(policy): return _empty(req,policy,reg,ControlDecision.HOLD,('PREPARED_POLICY_FINGERPRINT_MISMATCH',))
    if req.expected_policy_id!=policy.policy_id: return _empty(req,policy,reg,ControlDecision.HOLD,('POLICY_ID_MISMATCH',))
    if req.expected_policy_version!=policy.version: return _empty(req,policy,reg,ControlDecision.HOLD,('POLICY_VERSION_MISMATCH',))
    if req.expected_authority_epoch!=policy.authority_epoch: return _empty(req,policy,reg,ControlDecision.HOLD,('AUTHORITY_EPOCH_MISMATCH',))
    pmap={p.entity_id:p for p in reg.profiles}; profile=pmap.get(req.entity_id)
    if profile is None: return _empty(req,policy,reg,ControlDecision.HOLD,('ENTITY_PROFILE_MISSING',))
    if profile.entity_type not in policy.allowed_entity_types: return _empty(req,policy,reg,ControlDecision.DENY,('ENTITY_TYPE_NOT_ALLOWED',))
    if profile.provider_id not in policy.trusted_providers: return _empty(req,policy,reg,ControlDecision.HUMAN_APPROVAL,('PROVIDER_NOT_TRUSTED',))
    if profile.revoked: return _empty(req,policy,reg,ControlDecision.DENY,('ENTITY_REVOKED',))
    if not profile.verified: return _empty(req,policy,reg,ControlDecision.HOLD,('ENTITY_PROFILE_UNVERIFIED',))
    if profile.identity_fingerprint!=req.expected_identity_fingerprint: return _empty(req,policy,reg,ControlDecision.DENY,('IDENTITY_FINGERPRINT_MISMATCH',))
    if profile.evidence_binding!=req.evidence_binding: return _empty(req,policy,reg,ControlDecision.HOLD,('PROFILE_EVIDENCE_BINDING_MISMATCH',))
    active=[]
    for e in reg.evidence:
        if e.entity_id!=req.entity_id: continue
        if e.revoked or not e.verified or not e.independent: continue
        if e.evidence_binding!=req.evidence_binding: continue
        if not e.observed_at<=now<e.expires_at: continue
        if now-e.observed_at>policy.max_evidence_age_seconds: continue
        active.append(e)
    score=max(0,min(100,50+sum(e.impact for e in active)))
    pos=sum(1 for e in active if e.impact>0); neg=sum(1 for e in active if e.impact<0)
    tier=_tier(score,len(active),policy)
    reasons=['TRUST_SCORE_CANDIDATE',f'TIER_{tier.value}']
    probation=tier in {TrustTier.UNTRUSTED,TrustTier.PROBATION}
    connection=tier in {TrustTier.PROBATION,TrustTier.LIMITED,TrustTier.ESTABLISHED}
    privilege=PrivilegeLevel.NONE
    if req.requested_privilege in policy.disallowed_privileges:
        return TrustAssessment(ControlDecision.DENY,req.request_id,req.entity_id,tuple(reasons+['PRIVILEGE_DISALLOWED']),score,tier,probation,False,PrivilegeLevel.NONE,len(active),pos,neg,reg.registry_fingerprint,fingerprint(policy),fingerprint(req))
    if tier is TrustTier.BLOCKED:
        return TrustAssessment(ControlDecision.DENY,req.request_id,req.entity_id,tuple(reasons+['TRUST_SCORE_BELOW_DENY_THRESHOLD']),score,tier,False,False,PrivilegeLevel.NONE,len(active),pos,neg,reg.registry_fingerprint,fingerprint(policy),fingerprint(req))
    if tier is TrustTier.UNTRUSTED:
        return TrustAssessment(ControlDecision.HUMAN_APPROVAL,req.request_id,req.entity_id,tuple(reasons+['PROBATION_REQUIRED']),score,tier,True,False,PrivilegeLevel.NONE,len(active),pos,neg,reg.registry_fingerprint,fingerprint(policy),fingerprint(req))
    if req.operation is TrustOperation.ASSESS:
        return TrustAssessment(ControlDecision.ALLOW,req.request_id,req.entity_id,tuple(reasons+['ASSESSMENT_CANDIDATE']),score,tier,probation,False,PrivilegeLevel.NONE,len(active),pos,neg,reg.registry_fingerprint,fingerprint(policy),fingerprint(req))
    if req.operation is TrustOperation.CONNECT:
        decision=ControlDecision.HUMAN_APPROVAL if probation or req.high_impact_context else ControlDecision.ALLOW
        return TrustAssessment(decision,req.request_id,req.entity_id,tuple(reasons+([ 'PROBATION_CONNECTION_CANDIDATE' ] if probation else ['CONNECTION_CANDIDATE'])),score,tier,probation,True,PrivilegeLevel.NONE,len(active),pos,neg,reg.registry_fingerprint,fingerprint(policy),fingerprint(req))
    # privilege request
    rp=req.requested_privilege
    if rp in {PrivilegeLevel.HIGH,PrivilegeLevel.ADMIN}:
        if tier is not TrustTier.ESTABLISHED or score<policy.high_privilege_min_score or pos<policy.high_privilege_min_positive_events or neg>0:
            return TrustAssessment(ControlDecision.HUMAN_APPROVAL,req.request_id,req.entity_id,tuple(reasons+['HIGH_PRIVILEGE_NOT_AUTOMATICALLY_ELIGIBLE']),score,tier,probation,False,PrivilegeLevel.NONE,len(active),pos,neg,reg.registry_fingerprint,fingerprint(policy),fingerprint(req))
        return TrustAssessment(ControlDecision.HUMAN_APPROVAL,req.request_id,req.entity_id,tuple(reasons+['HIGH_PRIVILEGE_HUMAN_AUTHORITY_REQUIRED']),score,tier,False,False,rp,len(active),pos,neg,reg.registry_fingerprint,fingerprint(policy),fingerprint(req))
    if probation and rp not in {PrivilegeLevel.NONE,PrivilegeLevel.READ_ONLY}:
        return TrustAssessment(ControlDecision.HUMAN_APPROVAL,req.request_id,req.entity_id,tuple(reasons+['PROBATION_PRIVILEGE_RESTRICTED']),score,tier,True,False,PrivilegeLevel.READ_ONLY,len(active),pos,neg,reg.registry_fingerprint,fingerprint(policy),fingerprint(req))
    privilege=rp
    return TrustAssessment(ControlDecision.ALLOW,req.request_id,req.entity_id,tuple(reasons+['PRIVILEGE_CANDIDATE']),score,tier,probation,False,privilege,len(active),pos,neg,reg.registry_fingerprint,fingerprint(policy),fingerprint(req))

def evaluate(req,policy,profiles,evidence,*,now:int)->TrustAssessment:
    try: reg=prepare_registry(policy,profiles,evidence,now=now)
    except ValueError as e:
        dummy=PreparedTrustRegistry('',fingerprint(policy),(),(),{}, {}, {}, {})
        return _empty(req,policy,dummy,ControlDecision.HOLD,(f'INVALID_REGISTRY:{e}',))
    return evaluate_prepared(req,policy,reg,now=now)

def make_registry_delta(base_profiles,base_evidence,target_profiles,target_evidence)->TrustRegistryDelta:
    bp={p.entity_id:p for p in _profiles(base_profiles)}; tp={p.entity_id:p for p in _profiles(target_profiles)}
    be={e.evidence_id:e for e in _evidence(base_evidence)}; te={e.evidence_id:e for e in _evidence(target_evidence)}
    cp=tuple(sorted((p for k,p in tp.items() if k in bp and fingerprint(p)!=fingerprint(bp[k])),key=lambda x:x.entity_id))
    rp=tuple(sorted(k for k in bp if k not in tp)); ap=tuple(sorted((p for k,p in tp.items() if k not in bp),key=lambda x:x.entity_id))
    ce=tuple(sorted((e for k,e in te.items() if k in be and fingerprint(e)!=fingerprint(be[k])),key=lambda x:x.evidence_id))
    re=tuple(sorted(k for k in be if k not in te)); ae=tuple(sorted((e for k,e in te.items() if k not in be),key=lambda x:x.evidence_id))
    return TrustRegistryDelta(registry_fingerprint(base_profiles,base_evidence),registry_fingerprint(target_profiles,target_evidence),cp,rp,ap,ce,re,ae)

def apply_registry_delta(base_profiles,base_evidence,delta:TrustRegistryDelta):
    if registry_fingerprint(base_profiles,base_evidence)!=delta.base_fingerprint: raise ValueError('delta base fingerprint mismatch')
    ps={p.entity_id:p for p in _profiles(base_profiles)}; es={e.evidence_id:e for e in _evidence(base_evidence)}
    for k in delta.removed_profile_ids:
        if k not in ps: raise ValueError('invalid profile removal')
        del ps[k]
    for p in delta.changed_profiles:
        if p.entity_id not in ps: raise ValueError('invalid profile change')
        ps[p.entity_id]=p
    for p in delta.added_profiles:
        if p.entity_id in ps: raise ValueError('invalid profile add')
        ps[p.entity_id]=p
    for k in delta.removed_evidence_ids:
        if k not in es: raise ValueError('invalid evidence removal')
        del es[k]
    for e in delta.changed_evidence:
        if e.evidence_id not in es: raise ValueError('invalid evidence change')
        es[e.evidence_id]=e
    for e in delta.added_evidence:
        if e.evidence_id in es: raise ValueError('invalid evidence add')
        es[e.evidence_id]=e
    po=_profiles(ps.values()); eo=_evidence(es.values())
    if registry_fingerprint(po,eo)!=delta.target_fingerprint: raise ValueError('delta target fingerprint mismatch')
    return po,eo

def plan_registry_sync(profiles,evidence,remote_profile_fps:Mapping[str,str],remote_evidence_fps:Mapping[str,str])->RegistrySyncPlan:
    ps=_profiles(profiles); es=_evidence(evidence)
    pids=tuple(p.entity_id for p in ps if remote_profile_fps.get(p.entity_id)!=fingerprint(p))
    eids=tuple(e.evidence_id for e in es if remote_evidence_fps.get(e.evidence_id)!=fingerprint(e))
    pm={p.entity_id:p for p in ps}; em={e.evidence_id:e for e in es}
    meta=len(canonical_json({'profiles':[pm[k] for k in pids],'evidence':[em[k] for k in eids]}).encode())
    full=len(canonical_json({'profiles':ps,'evidence':es}).encode())
    return RegistrySyncPlan(pids,eids,meta,full,full>0 and meta/full>=0.8)

def assessment_digest(a:TrustAssessment)->str: return fingerprint(a)

def default_policy(now:int)->TrustPolicy:
    return TrustPolicy('TRUST-059','1',1,now-100,now+10000,frozenset({'PROVIDER-059'}),frozenset({EntityType.AI,EntityType.TOOL}),2,4,40,60,80,25,3600,85,4,frozenset({PrivilegeLevel.ADMIN}),False)
def default_profile(now:int)->ExternalEntityProfile:
    return ExternalEntityProfile('EXT-059',EntityType.TOOL,'PROVIDER-059','FP-EXT-059',now-1000,now-10,True,'BIND-059',False)
def default_evidence(now:int):
    return (
      TrustEvidence('EV-059-SIG','EXT-059',EvidenceKind.SIGNATURE,now-100,now+3000,15,True,True,'VERIFIER-1','BIND-059',False),
      TrustEvidence('EV-059-REL','EXT-059',EvidenceKind.RELIABILITY,now-90,now+3000,12,True,True,'MONITOR-1','BIND-059',False),
      TrustEvidence('EV-059-POL','EXT-059',EvidenceKind.POLICY,now-80,now+3000,8,True,True,'AUDIT-1','BIND-059',False),
      TrustEvidence('EV-059-PROB','EXT-059',EvidenceKind.PROBATION,now-70,now+3000,10,True,True,'SANDBOX-1','BIND-059',False),
    )
def default_request(now:int)->TrustRequest:
    return TrustRequest('REQ-059',TrustOperation.CONNECT,'EXT-059','FP-EXT-059',PrivilegeLevel.NONE,'TRUST-059','1',1,'BIND-059',False)
