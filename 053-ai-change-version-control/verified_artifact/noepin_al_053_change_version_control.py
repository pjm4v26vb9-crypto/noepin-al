"""NOEPIN AL 053 — AI Change Management / Version Control.

Pure control-plane evaluator implementing Version, Change Request, Approval,
and Rollback Point checks. It produces a deterministic change-control candidate
without deploying, committing, rolling back, granting permission, or promoting
version/fingerprint evidence to authoritative truth.

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

class ChangeRisk(str, Enum):
    LOW='LOW'; MEDIUM='MEDIUM'; HIGH='HIGH'; CRITICAL='CRITICAL'

@dataclass(frozen=True)
class VersionPolicy:
    policy_id:str; version:str; authority_epoch:int; issued_at:int; expires_at:int
    allowed_component_types:FrozenSet[str]; protected_component_types:FrozenSet[str]
    required_approval_roles:FrozenSet[str]; require_rollback_for_types:FrozenSet[str]
    max_change_components:int; max_evidence_age_seconds:int; revoked:bool=False
    def validate(self, now:int)->None:
        if not self.policy_id or not self.version or self.authority_epoch<1: raise ValueError('policy identity invalid')
        if self.issued_at<0 or self.expires_at<=self.issued_at or not self.issued_at<=now<self.expires_at: raise ValueError('policy not current')
        if not self.allowed_component_types or self.max_change_components<1 or self.max_evidence_age_seconds<1: raise ValueError('policy limits invalid')
        if not self.protected_component_types.issubset(self.allowed_component_types): raise ValueError('protected types outside allowed set')

@dataclass(frozen=True)
class VersionRecord:
    record_id:str; component_id:str; component_type:str; version:str; artifact_fingerprint:str
    parent_fingerprint:str; created_at:int; evidence_binding:str; active:bool; revoked:bool=False
    def validate(self)->None:
        if not self.record_id or not self.component_id or not self.component_type or not self.version: raise ValueError('version identity required')
        _sha(self.artifact_fingerprint); _sha(self.parent_fingerprint)
        if self.created_at<0 or not self.evidence_binding: raise ValueError('version metadata invalid')

@dataclass(frozen=True)
class ApprovalEvidence:
    approval_id:str; change_id:str; actor_id:str; role:str; approved:bool; verified:bool
    issued_at:int; expires_at:int; evidence_binding:str; revoked:bool=False
    def validate(self)->None:
        if not self.approval_id or not self.change_id or not self.actor_id or not self.role or not self.evidence_binding: raise ValueError('approval identity required')
        if self.issued_at<0 or self.expires_at<=self.issued_at: raise ValueError('approval lifetime invalid')

@dataclass(frozen=True)
class RollbackPoint:
    rollback_id:str; component_id:str; version:str; artifact_fingerprint:str; parent_fingerprint:str
    created_at:int; evidence_binding:str; verified:bool; revoked:bool=False
    def validate(self)->None:
        if not self.rollback_id or not self.component_id or not self.version or not self.evidence_binding: raise ValueError('rollback identity required')
        _sha(self.artifact_fingerprint); _sha(self.parent_fingerprint)
        if self.created_at<0: raise ValueError('rollback timestamp invalid')

@dataclass(frozen=True)
class ChangeRequest:
    change_id:str; component_id:str; component_type:str; current_version:str; proposed_version:str
    current_fingerprint:str; proposed_fingerprint:str; parent_fingerprint:str; rollback_point_id:str
    risk:ChangeRisk; reason:str; requested_by:str; requested_at:int
    expected_policy_id:str; expected_policy_version:str; expected_authority_epoch:int; evidence_binding:str
    def validate(self)->None:
        if not self.change_id or not self.component_id or not self.component_type or not self.current_version or not self.proposed_version: raise ValueError('change identity required')
        _sha(self.current_fingerprint); _sha(self.proposed_fingerprint); _sha(self.parent_fingerprint)
        if not self.reason or not self.requested_by or self.requested_at<0 or not self.evidence_binding: raise ValueError('change metadata invalid')
        if not self.expected_policy_id or not self.expected_policy_version or self.expected_authority_epoch<1: raise ValueError('policy binding invalid')

@dataclass(frozen=True)
class PreparedVersionRegistry:
    registry_fingerprint:str; policy_fingerprint:str
    versions:Tuple[VersionRecord,...]; approvals:Tuple[ApprovalEvidence,...]; rollbacks:Tuple[RollbackPoint,...]
    version_fingerprints:Mapping[str,str]; approval_fingerprints:Mapping[str,str]; rollback_fingerprints:Mapping[str,str]
    component_index:Mapping[str,Tuple[str,...]]; change_approval_index:Mapping[str,Tuple[str,...]]; rollback_component_index:Mapping[str,Tuple[str,...]]

@dataclass(frozen=True)
class VersionRegistryDelta:
    base_fingerprint:str; target_fingerprint:str
    changed_versions:Tuple[VersionRecord,...]; removed_version_ids:Tuple[str,...]; added_versions:Tuple[VersionRecord,...]
    changed_approvals:Tuple[ApprovalEvidence,...]; removed_approval_ids:Tuple[str,...]; added_approvals:Tuple[ApprovalEvidence,...]
    changed_rollbacks:Tuple[RollbackPoint,...]; removed_rollback_ids:Tuple[str,...]; added_rollbacks:Tuple[RollbackPoint,...]

@dataclass(frozen=True)
class RegistrySyncPlan:
    missing_or_changed_version_ids:Tuple[str,...]; missing_or_changed_approval_ids:Tuple[str,...]; missing_or_changed_rollback_ids:Tuple[str,...]
    metadata_bytes_required:int; full_metadata_bytes:int; full_resend_required:bool
    permission_granted:bool=False; change_commit_authorized:bool=False; deployment_authorized:bool=False; rollback_execution_authorized:bool=False

@dataclass(frozen=True)
class ChangeVerdict:
    decision:ControlDecision; reasons:Tuple[str,...]; change_id:str; component_id:str
    current_record_id:str; valid_approval_ids:Tuple[str,...]; valid_rollback_point_id:str
    rollback_ready_candidate:bool; human_review_candidate:bool
    registry_fingerprint:str; policy_fingerprint:str; request_fingerprint:str
    permission_granted:bool=False; change_committed:bool=False; deployment_executed:bool=False
    rollback_executed:bool=False; active_version_changed:bool=False; version_truth_proven:bool=False; action_success:bool=False

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

def _sorted_versions(xs:Iterable[VersionRecord])->Tuple[VersionRecord,...]: return tuple(sorted(xs,key=lambda x:x.record_id))
def _sorted_approvals(xs:Iterable[ApprovalEvidence])->Tuple[ApprovalEvidence,...]: return tuple(sorted(xs,key=lambda x:x.approval_id))
def _sorted_rollbacks(xs:Iterable[RollbackPoint])->Tuple[RollbackPoint,...]: return tuple(sorted(xs,key=lambda x:x.rollback_id))
def registry_fingerprint(vs:Iterable[VersionRecord], aps:Iterable[ApprovalEvidence], rbs:Iterable[RollbackPoint])->str:
    return fingerprint((_sorted_versions(vs),_sorted_approvals(aps),_sorted_rollbacks(rbs)))

def prepare_registry(policy:VersionPolicy, versions:Iterable[VersionRecord], approvals:Iterable[ApprovalEvidence], rollbacks:Iterable[RollbackPoint], *, now:int)->PreparedVersionRegistry:
    policy.validate(now)
    vs=_sorted_versions(versions); aps=_sorted_approvals(approvals); rbs=_sorted_rollbacks(rollbacks)
    for x in vs: x.validate()
    for x in aps: x.validate()
    for x in rbs: x.validate()
    if len({x.record_id for x in vs})!=len(vs) or len({x.approval_id for x in aps})!=len(aps) or len({x.rollback_id for x in rbs})!=len(rbs): raise ValueError('duplicate registry id')
    cidx={}
    for x in vs: cidx.setdefault(x.component_id,[]).append(x.record_id)
    aidx={}
    for x in aps: aidx.setdefault(x.change_id,[]).append(x.approval_id)
    ridx={}
    for x in rbs: ridx.setdefault(x.component_id,[]).append(x.rollback_id)
    return PreparedVersionRegistry(registry_fingerprint(vs,aps,rbs),fingerprint(policy),vs,aps,rbs,
        {x.record_id:fingerprint(x) for x in vs},{x.approval_id:fingerprint(x) for x in aps},{x.rollback_id:fingerprint(x) for x in rbs},
        {k:tuple(sorted(v)) for k,v in cidx.items()},{k:tuple(sorted(v)) for k,v in aidx.items()},{k:tuple(sorted(v)) for k,v in ridx.items()})

def _hold(req,pol,reg,*reasons)->ChangeVerdict:
    return ChangeVerdict(ControlDecision.HOLD,tuple(reasons),req.change_id,req.component_id,'',(),'',False,False,reg.registry_fingerprint,fingerprint(pol),fingerprint(req))

def evaluate_prepared(req:ChangeRequest, policy:VersionPolicy, reg:PreparedVersionRegistry, *, now:int)->ChangeVerdict:
    try: req.validate(); policy.validate(now)
    except ValueError as e: return ChangeVerdict(ControlDecision.HOLD,(f'INVALID_INPUT:{e}',),getattr(req,'change_id',''),getattr(req,'component_id',''),'',(),'',False,False,getattr(reg,'registry_fingerprint',''),fingerprint(policy),fingerprint(req))
    if policy.revoked: return _hold(req,policy,reg,'POLICY_REVOKED')
    if req.expected_policy_id!=policy.policy_id: return _hold(req,policy,reg,'POLICY_ID_MISMATCH')
    if req.expected_policy_version!=policy.version: return _hold(req,policy,reg,'POLICY_VERSION_MISMATCH')
    if req.expected_authority_epoch!=policy.authority_epoch: return _hold(req,policy,reg,'AUTHORITY_EPOCH_MISMATCH')
    if reg.policy_fingerprint!=fingerprint(policy): return _hold(req,policy,reg,'PREPARED_POLICY_FINGERPRINT_MISMATCH')
    if reg.registry_fingerprint!=registry_fingerprint(reg.versions,reg.approvals,reg.rollbacks): return _hold(req,policy,reg,'PREPARED_REGISTRY_FINGERPRINT_MISMATCH')
    if req.component_type not in policy.allowed_component_types:
        return ChangeVerdict(ControlDecision.DENY,('COMPONENT_TYPE_NOT_ALLOWED',),req.change_id,req.component_id,'',(),'',False,False,reg.registry_fingerprint,fingerprint(policy),fingerprint(req))
    current=[x for x in reg.versions if x.component_id==req.component_id and x.active and not x.revoked]
    if len(current)!=1: return _hold(req,policy,reg,'CURRENT_VERSION_AMBIGUOUS_OR_MISSING')
    cur=current[0]
    if cur.component_type!=req.component_type: return _hold(req,policy,reg,'COMPONENT_TYPE_MISMATCH')
    if cur.version!=req.current_version: return _hold(req,policy,reg,'CURRENT_VERSION_MISMATCH')
    if cur.artifact_fingerprint!=req.current_fingerprint: return _hold(req,policy,reg,'CURRENT_FINGERPRINT_MISMATCH')
    if req.parent_fingerprint!=cur.artifact_fingerprint:
        return ChangeVerdict(ControlDecision.DENY,('PARENT_FINGERPRINT_MISMATCH',),req.change_id,req.component_id,cur.record_id,(),'',False,False,reg.registry_fingerprint,fingerprint(policy),fingerprint(req))
    if req.proposed_fingerprint==req.current_fingerprint or req.proposed_version==req.current_version:
        return ChangeVerdict(ControlDecision.DENY,('NO_EFFECTIVE_VERSION_CHANGE',),req.change_id,req.component_id,cur.record_id,(),'',False,False,reg.registry_fingerprint,fingerprint(policy),fingerprint(req))
    collisions=[x for x in reg.versions if x.component_id==req.component_id and x.version==req.proposed_version]
    if collisions:
        reason='CHANGE_ALREADY_MATERIALIZED' if any(x.artifact_fingerprint==req.proposed_fingerprint for x in collisions) else 'VERSION_COLLISION'
        dec=ControlDecision.HOLD if reason=='CHANGE_ALREADY_MATERIALIZED' else ControlDecision.DENY
        return ChangeVerdict(dec,(reason,),req.change_id,req.component_id,cur.record_id,(),'',False,False,reg.registry_fingerprint,fingerprint(policy),fingerprint(req))
    # Validate rollback candidate.
    valid_rb=''
    for rb in reg.rollbacks:
        if rb.rollback_id!=req.rollback_point_id: continue
        if rb.revoked or not rb.verified or now-rb.created_at>policy.max_evidence_age_seconds: continue
        if rb.component_id!=req.component_id or rb.version!=req.current_version or rb.artifact_fingerprint!=req.current_fingerprint: continue
        if rb.evidence_binding!=req.evidence_binding: continue
        valid_rb=rb.rollback_id; break
    rollback_required=req.component_type in policy.require_rollback_for_types
    if rollback_required and not valid_rb:
        return _hold(req,policy,reg,'VALID_ROLLBACK_POINT_REQUIRED')
    # Validate approvals.
    valid=[]; roles=set(); actors=set(); explicit_reject=False
    for ap in reg.approvals:
        if ap.change_id!=req.change_id: continue
        if ap.revoked or not ap.verified or not ap.issued_at<=now<ap.expires_at or now-ap.issued_at>policy.max_evidence_age_seconds: continue
        if ap.evidence_binding!=req.evidence_binding: continue
        if not ap.approved: explicit_reject=True; continue
        if ap.actor_id in actors: continue
        actors.add(ap.actor_id); roles.add(ap.role); valid.append(ap.approval_id)
    if explicit_reject:
        return ChangeVerdict(ControlDecision.DENY,('EXPLICIT_APPROVAL_REJECTION',),req.change_id,req.component_id,cur.record_id,tuple(sorted(valid)),valid_rb,bool(valid_rb),False,reg.registry_fingerprint,fingerprint(policy),fingerprint(req))
    needs_approval=req.risk in (ChangeRisk.HIGH,ChangeRisk.CRITICAL) or req.component_type in policy.protected_component_types
    if needs_approval and not policy.required_approval_roles.issubset(roles):
        return ChangeVerdict(ControlDecision.HUMAN_APPROVAL,('REQUIRED_APPROVAL_ROLE_MISSING',),req.change_id,req.component_id,cur.record_id,tuple(sorted(valid)),valid_rb,bool(valid_rb),True,reg.registry_fingerprint,fingerprint(policy),fingerprint(req))
    return ChangeVerdict(ControlDecision.ALLOW,('CHANGE_CONTROL_CANDIDATE_VALID',),req.change_id,req.component_id,cur.record_id,tuple(sorted(valid)),valid_rb,bool(valid_rb),False,reg.registry_fingerprint,fingerprint(policy),fingerprint(req))

def evaluate(req:ChangeRequest, policy:VersionPolicy, versions:Iterable[VersionRecord], approvals:Iterable[ApprovalEvidence], rollbacks:Iterable[RollbackPoint], *, now:int)->ChangeVerdict:
    try: reg=prepare_registry(policy,versions,approvals,rollbacks,now=now)
    except ValueError as e:
        return ChangeVerdict(ControlDecision.HOLD,(f'INVALID_REGISTRY:{e}',),getattr(req,'change_id',''),getattr(req,'component_id',''),'',(),'',False,False,'',fingerprint(policy),fingerprint(req))
    return evaluate_prepared(req,policy,reg,now=now)

def _delta(base,target,key):
    b={key(x):x for x in base}; t={key(x):x for x in target}
    changed=tuple(t[k] for k in sorted(b.keys()&t.keys()) if fingerprint(b[k])!=fingerprint(t[k]))
    removed=tuple(sorted(b.keys()-t.keys())); added=tuple(t[k] for k in sorted(t.keys()-b.keys()))
    return changed,removed,added

def make_registry_delta(bv,ba,br,tv,ta,tr)->VersionRegistryDelta:
    bv=_sorted_versions(bv); ba=_sorted_approvals(ba); br=_sorted_rollbacks(br); tv=_sorted_versions(tv); ta=_sorted_approvals(ta); tr=_sorted_rollbacks(tr)
    cv,rv,av=_delta(bv,tv,lambda x:x.record_id); ca,ra,aa=_delta(ba,ta,lambda x:x.approval_id); cr,rr,ar=_delta(br,tr,lambda x:x.rollback_id)
    return VersionRegistryDelta(registry_fingerprint(bv,ba,br),registry_fingerprint(tv,ta,tr),cv,rv,av,ca,ra,aa,cr,rr,ar)

def apply_registry_delta(bv,ba,br,d:VersionRegistryDelta):
    if registry_fingerprint(bv,ba,br)!=d.base_fingerprint: raise ValueError('delta base fingerprint mismatch')
    def apply(base,changed,removed,added,key):
        m={key(x):x for x in base}
        for k in removed:
            if k not in m: raise ValueError('remove missing id')
            del m[k]
        for x in changed:
            k=key(x)
            if k not in m: raise ValueError('change missing id')
            m[k]=x
        for x in added:
            k=key(x)
            if k in m: raise ValueError('add existing id')
            m[k]=x
        return tuple(m[k] for k in sorted(m))
    v=apply(bv,d.changed_versions,d.removed_version_ids,d.added_versions,lambda x:x.record_id)
    a=apply(ba,d.changed_approvals,d.removed_approval_ids,d.added_approvals,lambda x:x.approval_id)
    r=apply(br,d.changed_rollbacks,d.removed_rollback_ids,d.added_rollbacks,lambda x:x.rollback_id)
    if registry_fingerprint(v,a,r)!=d.target_fingerprint: raise ValueError('delta target fingerprint mismatch')
    return v,a,r

def plan_registry_sync(vs,aps,rbs,known:Mapping[str,str])->RegistrySyncPlan:
    vs=_sorted_versions(vs); aps=_sorted_approvals(aps); rbs=_sorted_rollbacks(rbs)
    mv=tuple(x.record_id for x in vs if known.get('version:'+x.record_id)!=fingerprint(x))
    ma=tuple(x.approval_id for x in aps if known.get('approval:'+x.approval_id)!=fingerprint(x))
    mr=tuple(x.rollback_id for x in rbs if known.get('rollback:'+x.rollback_id)!=fingerprint(x))
    selected=[x for x in vs if x.record_id in mv]+[x for x in aps if x.approval_id in ma]+[x for x in rbs if x.rollback_id in mr]
    metadata=len(canonical_json(selected).encode()); full=len(canonical_json((vs,aps,rbs)).encode())
    return RegistrySyncPlan(mv,ma,mr,metadata,full,metadata>=full)

def verdicts_digest(vs:Iterable[ChangeVerdict])->str: return fingerprint(tuple(vs))

def default_policy(now:int)->VersionPolicy:
    return VersionPolicy('NOEPIN-AL-053-POLICY','2.0.0',1,now-1000,now+100000,
        frozenset({'PROMPT','RULE','MODEL','TOOL_CONFIG'}),frozenset({'RULE','MODEL','TOOL_CONFIG'}),frozenset({'CHANGE_REVIEWER'}),frozenset({'RULE','MODEL','TOOL_CONFIG'}),8,86400,False)

def default_request(now:int)->ChangeRequest:
    cur=fingerprint(('NOEPIN-AL-053','RULE','1.0.0')); prop=fingerprint(('NOEPIN-AL-053','RULE','1.1.0'))
    return ChangeRequest('CHANGE-053','RULESET-CORE','RULE','1.0.0','1.1.0',cur,prop,cur,'RB-053',ChangeRisk.HIGH,'verified rule update','NOEPIN',now-10,'NOEPIN-AL-053-POLICY','2.0.0',1,'CHANGE-EVIDENCE-053')

def default_registry(now:int):
    req=default_request(now)
    versions=(VersionRecord('VER-053-A','RULESET-CORE','RULE','1.0.0',req.current_fingerprint,fingerprint(('parent','0.9.0')),now-500,'CHANGE-EVIDENCE-053',True,False),)
    approvals=(ApprovalEvidence('APR-053',req.change_id,'REVIEWER-1','CHANGE_REVIEWER',True,True,now-30,now+10000,req.evidence_binding,False),)
    rollbacks=(RollbackPoint('RB-053',req.component_id,req.current_version,req.current_fingerprint,fingerprint(('parent','0.9.0')),now-100,req.evidence_binding,True,False),)
    return versions,approvals,rollbacks
