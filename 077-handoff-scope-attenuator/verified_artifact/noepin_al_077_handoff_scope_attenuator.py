"""NOEPIN AL 077 — Handoff Scope Attenuator — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Deterministic typed scope-containment evaluator for agent-to-agent handoff.
It does not grant permission, issue signed delegation tokens, create sub-agents,
execute tools, inherit sender intent/authority/consent, or establish world truth.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Sequence

class Decision(str, Enum):
    ALLOW="ALLOW"; DENY="DENY"; HOLD="HOLD"; HUMAN_APPROVAL="HUMAN_APPROVAL"

@dataclass(frozen=True)
class ScopeSpec:
    scope_id: str
    goals: tuple[str,...]
    data_classes: tuple[str,...]
    actions: tuple[str,...]
    targets: tuple[str,...]
    capabilities: tuple[str,...]
    depth: int
    observed: bool
    authority_confirmed: bool
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class CapabilitySpec:
    capability_id: str
    actions: tuple[str,...]
    data_classes: tuple[str,...]
    targets: tuple[str,...]
    observed: bool
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class HandoffPolicy:
    binding: str
    state_epoch: str
    max_depth: int=8
    revoked: bool=False

@dataclass(frozen=True)
class HandoffRequest:
    request_id: str
    parent_scope_id: str
    child_scope_id: str
    delegation_purpose: tuple[str,...]
    required_capabilities: tuple[str,...]
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class AttenuatedScope:
    goals: tuple[str,...]
    data_classes: tuple[str,...]
    actions: tuple[str,...]
    targets: tuple[str,...]
    capabilities: tuple[str,...]

@dataclass(frozen=True)
class HandoffResult:
    decision: Decision
    reasons: tuple[str,...]
    attenuated_scope: AttenuatedScope|None
    violation_items: tuple[str,...]
    delegation_manifest_digest: str|None
    delegation_permit_candidate: bool
    reproposal_required: bool
    # authority negatives
    permission_granted: bool=False
    signed_delegation_token_issued: bool=False
    capability_activated: bool=False
    child_agent_created: bool=False
    sender_authority_inherited: bool=False
    sender_intent_inherited: bool=False
    sender_consent_inherited: bool=False
    tool_executed: bool=False
    transaction_committed: bool=False
    external_write_performed: bool=False
    world_truth_proven: bool=False
    safety_proven: bool=False
    action_success: bool=False

@dataclass(frozen=True)
class PreparedHandoffState:
    policy: HandoffPolicy
    scopes: tuple[ScopeSpec,...]
    capabilities: tuple[CapabilitySpec,...]
    scope_fingerprints: tuple[tuple[str,str],...]
    capability_fingerprints: tuple[tuple[str,str],...]
    policy_fingerprint: str
    registry_fingerprint: str
    scope_index: tuple[tuple[str,ScopeSpec],...]
    capability_index: tuple[tuple[str,CapabilitySpec],...]
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class HandoffRegistryDelta:
    base_fingerprint: str
    target_fingerprint: str
    changed_scopes: tuple[ScopeSpec,...]
    removed_scope_ids: tuple[str,...]
    changed_capabilities: tuple[CapabilitySpec,...]
    removed_capability_ids: tuple[str,...]
    target_policy: HandoffPolicy
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class HandoffSyncPlan:
    missing_or_changed_scopes: tuple[str,...]
    missing_or_changed_capabilities: tuple[str,...]
    metadata_bytes_required: int
    full_resend_required: bool

def _canon(v)->bytes:
    def cv(x):
        if isinstance(x,Enum): return x.value
        if hasattr(x,'__dataclass_fields__'): return {k:cv(getattr(x,k)) for k in x.__dataclass_fields__}
        if isinstance(x,tuple): return [cv(i) for i in x]
        if isinstance(x,list): return [cv(i) for i in x]
        if isinstance(x,dict): return {str(k):cv(x[k]) for k in sorted(x)}
        return x
    return json.dumps(cv(v),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()

def _fp(v)->str: return sha256(_canon(v)).hexdigest()
def _norm(xs)->tuple[str,...]: return tuple(sorted(set(str(x).strip().upper() for x in xs if str(x).strip())))
def _uniq(items,attr):
    x=[getattr(i,attr) for i in items]; return len(x)==len(set(x))
def _subset(a,b): return set(a).issubset(set(b))
def _registry_fp(policy,scopes,caps):
    return _fp({'policy':_fp(policy),'scopes':sorted((x.scope_id,_fp(x)) for x in scopes),'capabilities':sorted((x.capability_id,_fp(x)) for x in caps)})

def default_policy(): return HandoffPolicy('HANDOFF-BIND','STATE-EPOCH-1')
def default_capabilities():
    b,e='HANDOFF-BIND','STATE-EPOCH-1'
    return (
      CapabilitySpec('CAP-READ',('READ','SUMMARIZE'),('INTERNAL','PUBLIC'),('WORKSPACE',),True,b,e),
      CapabilitySpec('CAP-ANALYZE',('ANALYZE','READ','SUMMARIZE'),('INTERNAL','PUBLIC'),('WORKSPACE',),True,b,e),
      CapabilitySpec('CAP-EXPORT',('EXTERNAL_SEND','READ'),('PUBLIC',),('EXTERNAL-ENDPOINT',),True,b,e),
    )
def default_scopes():
    b,e='HANDOFF-BIND','STATE-EPOCH-1'
    return (
      ScopeSpec('SCOPE-PARENT',('ANALYZE','SUMMARIZE'),('INTERNAL','PUBLIC'),('ANALYZE','READ','SUMMARIZE'),('WORKSPACE',),('CAP-ANALYZE','CAP-READ'),0,True,True,b,e),
      ScopeSpec('SCOPE-CHILD',('SUMMARIZE',),('PUBLIC',),('READ','SUMMARIZE'),('WORKSPACE',),('CAP-READ',),1,True,False,b,e),
      ScopeSpec('SCOPE-EQUAL',('ANALYZE','SUMMARIZE'),('INTERNAL','PUBLIC'),('ANALYZE','READ','SUMMARIZE'),('WORKSPACE',),('CAP-ANALYZE','CAP-READ'),1,True,False,b,e),
      ScopeSpec('SCOPE-EXPANDED',('ANALYZE','EXPORT','SUMMARIZE'),('INTERNAL','PUBLIC'),('ANALYZE','EXTERNAL_SEND','READ','SUMMARIZE'),('EXTERNAL-ENDPOINT','WORKSPACE'),('CAP-ANALYZE','CAP-EXPORT','CAP-READ'),1,True,False,b,e),
      ScopeSpec('SCOPE-GRANDCHILD',('SUMMARIZE',),('PUBLIC',),('READ',),('WORKSPACE',),('CAP-READ',),2,True,False,b,e),
    )
def default_request(): return HandoffRequest('REQ-77','SCOPE-PARENT','SCOPE-CHILD',('SUMMARIZE',),('CAP-READ',),'HANDOFF-BIND','STATE-EPOCH-1')

def _validate_registry(policy,scopes,caps):
    if not isinstance(policy,HandoffPolicy) or policy.revoked or policy.max_depth<1: return False
    if not _uniq(scopes,'scope_id') or not _uniq(caps,'capability_id'): return False
    for x in scopes:
        if not isinstance(x,ScopeSpec) or not x.scope_id or x.depth<0 or x.binding!=policy.binding or x.state_epoch!=policy.state_epoch: return False
        fields=(x.goals,x.data_classes,x.actions,x.targets,x.capabilities)
        if any(tuple(v)!=_norm(v) for v in fields): return False
    for x in caps:
        if not isinstance(x,CapabilitySpec) or not x.capability_id or x.binding!=policy.binding or x.state_epoch!=policy.state_epoch: return False
        if tuple(x.actions)!=_norm(x.actions) or tuple(x.data_classes)!=_norm(x.data_classes) or tuple(x.targets)!=_norm(x.targets): return False
    return True

def _hold(reason): return HandoffResult(Decision.HOLD,(reason,),None,(),None,False,True)
def _intersect(child,parent):
    return AttenuatedScope(tuple(sorted(set(child.goals)&set(parent.goals))),tuple(sorted(set(child.data_classes)&set(parent.data_classes))),tuple(sorted(set(child.actions)&set(parent.actions))),tuple(sorted(set(child.targets)&set(parent.targets))),tuple(sorted(set(child.capabilities)&set(parent.capabilities))))

def _evaluate_indexed(req,policy,sidx,cidx):
    if not isinstance(req,HandoffRequest): return _hold('INVALID_TYPED_INPUT')
    if req.binding!=policy.binding or req.state_epoch!=policy.state_epoch: return _hold('REQUEST_BINDING_MISMATCH')
    parent=sidx.get(req.parent_scope_id); child=sidx.get(req.child_scope_id)
    if parent is None: return _hold('PARENT_SCOPE_UNKNOWN')
    if child is None: return _hold('CHILD_SCOPE_UNKNOWN')
    if not parent.observed or not parent.authority_confirmed: return _hold('PARENT_SCOPE_NOT_AUTHORITATIVELY_CONFIRMED')
    if not child.observed: return _hold('CHILD_SCOPE_UNOBSERVED')
    if child.depth!=parent.depth+1: return _hold('DELEGATION_DEPTH_INCONSISTENT')
    if child.depth>policy.max_depth: return HandoffResult(Decision.DENY,('MAX_DELEGATION_DEPTH_EXCEEDED',),_intersect(child,parent),('DEPTH',),None,False,True)
    purpose=_norm(req.delegation_purpose); reqcaps=_norm(req.required_capabilities)
    if not purpose: return _hold('DELEGATION_PURPOSE_MISSING')
    if tuple(req.delegation_purpose)!=purpose or tuple(req.required_capabilities)!=reqcaps: return _hold('REQUEST_NOT_CANONICAL')
    violations=[]
    for label,a,b in (
      ('GOAL',child.goals,parent.goals),('DATA',child.data_classes,parent.data_classes),('ACTION',child.actions,parent.actions),('TARGET',child.targets,parent.targets),('CAPABILITY',child.capabilities,parent.capabilities)):
        for x in sorted(set(a)-set(b)): violations.append(f'{label}:{x}')
    for x in purpose:
        if x not in parent.goals: violations.append(f'PURPOSE_PARENT:{x}')
        if x not in child.goals: violations.append(f'PURPOSE_CHILD:{x}')
    for x in reqcaps:
        if x not in parent.capabilities: violations.append(f'REQUIRED_CAP_PARENT:{x}')
        if x not in child.capabilities: violations.append(f'REQUIRED_CAP_CHILD:{x}')
    # Capability records must exist and constrain child actions/data/targets.
    if (child.actions or child.data_classes or child.targets) and not child.capabilities:
        return _hold('CHILD_CAPABILITY_EVIDENCE_MISSING')
    selected=[]
    for cid in child.capabilities:
        cap=cidx.get(cid)
        if cap is None: return _hold('CAPABILITY_RECORD_UNKNOWN')
        if not cap.observed: return _hold('CAPABILITY_RECORD_UNOBSERVED')
        selected.append(cap)
    if selected:
        allowed_actions=set().union(*(set(x.actions) for x in selected)); allowed_data=set().union(*(set(x.data_classes) for x in selected)); allowed_targets=set().union(*(set(x.targets) for x in selected))
        for x in sorted(set(child.actions)-allowed_actions): violations.append(f'CAPABILITY_ACTION:{x}')
        for x in sorted(set(child.data_classes)-allowed_data): violations.append(f'CAPABILITY_DATA:{x}')
        for x in sorted(set(child.targets)-allowed_targets): violations.append(f'CAPABILITY_TARGET:{x}')
    atten=_intersect(child,parent)
    if violations:
        return HandoffResult(Decision.DENY,('CHILD_SCOPE_EXCEEDS_PARENT',),atten,tuple(sorted(set(violations))),_fp({'parent':parent.scope_id,'child':child.scope_id,'attenuated':atten,'purpose':purpose}),False,True)
    digest=_fp({'parent':parent.scope_id,'child':child.scope_id,'attenuated':atten,'purpose':purpose,'required_capabilities':reqcaps,'binding':req.binding,'state_epoch':req.state_epoch})
    return HandoffResult(Decision.ALLOW,('SCOPE_CONTAINMENT_VERIFIED',),atten,(),digest,True,False)

def evaluate(req,policy,scopes,caps):
    if not _validate_registry(policy,scopes,caps): return _hold('INVALID_OR_UNTRUSTED_REGISTRY')
    return _evaluate_indexed(req,policy,{x.scope_id:x for x in scopes},{x.capability_id:x for x in caps})

def prepare_state(policy,scopes,caps,*,binding):
    if binding!=policy.binding or not _validate_registry(policy,scopes,caps): raise ValueError('invalid registry/binding')
    sf=tuple(sorted((x.scope_id,_fp(x)) for x in scopes)); cf=tuple(sorted((x.capability_id,_fp(x)) for x in caps))
    return PreparedHandoffState(policy,tuple(scopes),tuple(caps),sf,cf,_fp(policy),_registry_fp(policy,scopes,caps),tuple(sorted((x.scope_id,x) for x in scopes)),tuple(sorted((x.capability_id,x) for x in caps)),policy.binding,policy.state_epoch)

def validate_prepared_integrity(st):
    if not isinstance(st,PreparedHandoffState) or st.binding!=st.policy.binding or st.state_epoch!=st.policy.state_epoch: return False
    if not _validate_registry(st.policy,st.scopes,st.capabilities): return False
    return st.scope_fingerprints==tuple(sorted((x.scope_id,_fp(x)) for x in st.scopes)) and st.capability_fingerprints==tuple(sorted((x.capability_id,_fp(x)) for x in st.capabilities)) and st.policy_fingerprint==_fp(st.policy) and st.registry_fingerprint==_registry_fp(st.policy,st.scopes,st.capabilities) and st.scope_index==tuple(sorted((x.scope_id,x) for x in st.scopes)) and st.capability_index==tuple(sorted((x.capability_id,x) for x in st.capabilities))

def evaluate_prepared(req,st,*,current_policy_fingerprint,current_registry_fingerprint,prepared_integrity_validated):
    if not isinstance(st,PreparedHandoffState): return _hold('INVALID_PREPARED_STATE')
    if not prepared_integrity_validated: return _hold('PREPARED_INTEGRITY_NOT_VALIDATED')
    if current_policy_fingerprint!=st.policy_fingerprint: return _hold('POLICY_FINGERPRINT_CHANGED')
    if current_registry_fingerprint!=st.registry_fingerprint: return _hold('REGISTRY_FINGERPRINT_CHANGED')
    return _evaluate_indexed(req,st.policy,dict(st.scope_index),dict(st.capability_index))

def make_delta(a,b):
    if a.binding!=b.binding or a.state_epoch!=b.state_epoch: raise ValueError('identity mismatch')
    af,bf=dict(a.scope_fingerprints),dict(b.scope_fingerprints); ac,bc=dict(a.capability_fingerprints),dict(b.capability_fingerprints); bi=dict(b.scope_index); bci=dict(b.capability_index)
    return HandoffRegistryDelta(a.registry_fingerprint,b.registry_fingerprint,tuple(bi[k] for k in sorted(bf) if af.get(k)!=bf[k]),tuple(sorted(set(af)-set(bf))),tuple(bci[k] for k in sorted(bc) if ac.get(k)!=bc[k]),tuple(sorted(set(ac)-set(bc))),b.policy,a.binding,a.state_epoch)

def apply_delta(a,d):
    if a.registry_fingerprint!=d.base_fingerprint or a.binding!=d.binding or a.state_epoch!=d.state_epoch: raise ValueError('delta base mismatch')
    s=dict(a.scope_index); c=dict(a.capability_index)
    for k in d.removed_scope_ids: s.pop(k,None)
    for x in d.changed_scopes: s[x.scope_id]=x
    for k in d.removed_capability_ids: c.pop(k,None)
    for x in d.changed_capabilities: c[x.capability_id]=x
    out=prepare_state(d.target_policy,tuple(s.values()),tuple(c.values()),binding=d.binding)
    if out.registry_fingerprint!=d.target_fingerprint: raise ValueError('delta target mismatch')
    return out

def missing_only_sync_plan(target,known_scopes,known_caps):
    if not isinstance(target,PreparedHandoffState): raise ValueError('target')
    sf=dict(target.scope_fingerprints); cf=dict(target.capability_fingerprints)
    ms=tuple(k for k in sorted(sf) if known_scopes.get(k)!=sf[k]); mc=tuple(k for k in sorted(cf) if known_caps.get(k)!=cf[k])
    meta=len(_canon({'scopes':ms,'capabilities':mc,'target':target.registry_fingerprint}))
    return HandoffSyncPlan(ms,mc,meta,False)

def full_registry_bytes(st): return len(_canon({'policy':st.policy,'scopes':st.scopes,'capabilities':st.capabilities}))
def delta_bytes(d): return len(_canon(d))
