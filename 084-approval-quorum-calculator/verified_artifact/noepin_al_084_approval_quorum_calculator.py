"""NOEPIN AL 084 — Approval Quorum Calculator — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Policy-driven approval quorum calculation for human approval evidence. The calculator
selects a quorum rule from Risk Level + Blast Radius, removes duplicate actors,
excludes conflict-of-interest / unverifiable approvals, prevents duplicate authority
chains from increasing the effective vote count, and verifies that required roles can
be satisfied by independent authority groups.

An ALLOW result is an execution candidate only. This module never grants permission,
executes approval, executes an action, commits state, writes externally, proves World
Truth/Safety, or asserts Action Success. A signature_verified field is upstream
verification evidence; this module does not perform cryptographic verification.

Canonical identity: NOEPIN-AL-084
Provenance note: exact registered Origin GUID was not freshly reverified in this
completion session and is intentionally not guessed or regenerated.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json

class Decision(str, Enum):
    ALLOW='ALLOW'
    DENY='DENY'
    HOLD='HOLD'
    HUMAN_APPROVAL='HUMAN_APPROVAL'

class RiskLevel(str, Enum):
    LOW='LOW'
    MEDIUM='MEDIUM'
    HIGH='HIGH'
    CRITICAL='CRITICAL'

class BlastRadius(str, Enum):
    LOCAL='LOCAL'
    TEAM='TEAM'
    ORGANIZATION='ORGANIZATION'
    GLOBAL='GLOBAL'

class ApprovalState(str, Enum):
    SATISFIED='SATISFIED'
    PENDING='PENDING'

@dataclass(frozen=True)
class ApprovalProposal:
    proposal_id:str
    risk_level:RiskLevel
    blast_radius:BlastRadius
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class RoleMatrixEntry:
    actor_id:str
    roles:tuple[str,...]
    authority_group:str
    eligible:bool
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class ApprovalEvidence:
    approval_id:str
    proposal_id:str
    actor_id:str
    observed:bool
    signature_verified:bool
    conflict_of_interest:bool
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class QuorumRule:
    level:int
    required_quorum:int
    required_roles:tuple[str,...]

@dataclass(frozen=True)
class QuorumPolicy:
    rules:tuple[QuorumRule,...]
    binding:str
    state_epoch:str
    revoked:bool=False

@dataclass(frozen=True)
class RoleAssignment:
    role:str
    actor_id:str
    authority_group:str

@dataclass(frozen=True)
class QuorumResult:
    decision:Decision
    reasons:tuple[str,...]
    required_quorum:int
    required_roles:tuple[str,...]
    effective_approval_count:int
    eligible_actor_count:int
    effective_actor_ids:tuple[str,...]
    effective_authority_groups:tuple[str,...]
    satisfied_roles:tuple[str,...]
    missing_roles:tuple[str,...]
    role_assignments:tuple[RoleAssignment,...]
    quorum_satisfied:bool
    roles_satisfied:bool
    approval_state:ApprovalState
    next_gate_candidate:bool
    permission_granted:bool=False
    approval_executed:bool=False
    action_executed:bool=False
    plan_committed:bool=False
    external_write_performed:bool=False
    world_truth_proven:bool=False
    safety_proven:bool=False
    action_success:bool=False
    sender_authority_inherited:bool=False
    sender_intent_inherited:bool=False
    consent_inherited:bool=False

@dataclass(frozen=True)
class PreparedQuorumState:
    policy:QuorumPolicy
    proposal:ApprovalProposal
    role_matrix:tuple[RoleMatrixEntry,...]
    approvals:tuple[ApprovalEvidence,...]
    role_fingerprints:tuple[tuple[str,str],...]
    approval_fingerprints:tuple[tuple[str,str],...]
    policy_fingerprint:str
    proposal_fingerprint:str
    context_fingerprint:str
    dependency_fingerprint:str
    registry_fingerprint:str
    precomputed_result:QuorumResult
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class QuorumStateDelta:
    base_fingerprint:str
    target_fingerprint:str
    changed_roles:tuple[RoleMatrixEntry,...]
    removed_actor_ids:tuple[str,...]
    changed_approvals:tuple[ApprovalEvidence,...]
    removed_approval_ids:tuple[str,...]
    target_proposal:ApprovalProposal
    target_policy:QuorumPolicy
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class QuorumSyncPlan:
    missing_or_changed_actor_ids:tuple[str,...]
    missing_or_changed_approval_ids:tuple[str,...]
    metadata_bytes_required:int
    full_resend_required:bool


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

def _risk_rank(x:RiskLevel)->int:
    return {RiskLevel.LOW:0,RiskLevel.MEDIUM:1,RiskLevel.HIGH:2,RiskLevel.CRITICAL:3}[x]

def _blast_rank(x:BlastRadius)->int:
    return {BlastRadius.LOCAL:0,BlastRadius.TEAM:1,BlastRadius.ORGANIZATION:2,BlastRadius.GLOBAL:3}[x]

def _norm_roles(xs):
    return tuple(sorted({str(x).strip().upper() for x in xs if str(x).strip()}))

def _rule_map(policy:QuorumPolicy):
    return {r.level:r for r in policy.rules}

def _validate(policy,proposal,role_matrix,approvals):
    if policy.revoked: return False,'POLICY_REVOKED'
    if policy.binding!=proposal.binding or policy.state_epoch!=proposal.state_epoch: return False,'PROPOSAL_BINDING_OR_EPOCH_MISMATCH'
    levels=[r.level for r in policy.rules]
    if len(levels)!=len(set(levels)): return False,'DUPLICATE_QUORUM_RULE_LEVEL'
    for r in policy.rules:
        if r.level not in (0,1,2,3) or r.required_quorum<1: return False,'INVALID_QUORUM_RULE'
        rr=_norm_roles(r.required_roles)
        if not rr or len(rr)>r.required_quorum: return False,'INVALID_REQUIRED_ROLE_SET'
    actors=[x.actor_id for x in role_matrix]
    if len(actors)!=len(set(actors)): return False,'DUPLICATE_ROLE_MATRIX_ACTOR'
    for x in role_matrix:
        if x.binding!=policy.binding or x.state_epoch!=policy.state_epoch: return False,'ROLE_MATRIX_BINDING_OR_EPOCH_MISMATCH'
        if not x.actor_id or not x.authority_group: return False,'INVALID_ROLE_MATRIX_ENTRY'
        if x.eligible and not _norm_roles(x.roles): return False,'ELIGIBLE_ACTOR_HAS_NO_ROLE'
    ids=[x.approval_id for x in approvals]
    if len(ids)!=len(set(ids)): return False,'DUPLICATE_APPROVAL_ID'
    for x in approvals:
        if x.binding!=policy.binding or x.state_epoch!=policy.state_epoch: return False,'APPROVAL_BINDING_OR_EPOCH_MISMATCH'
        if not x.approval_id or not x.actor_id: return False,'INVALID_APPROVAL_EVIDENCE'
    return True,'VALID'

def _required_rule(policy,proposal):
    level=max(_risk_rank(proposal.risk_level),_blast_rank(proposal.blast_radius))
    return _rule_map(policy).get(level)

def _valid_actor_ids(proposal,role_matrix,approvals):
    matrix={x.actor_id:x for x in role_matrix if x.eligible}
    by_actor={}
    conflicted=set()
    for ev in approvals:
        if ev.proposal_id!=proposal.proposal_id: continue
        if ev.conflict_of_interest:
            conflicted.add(ev.actor_id); continue
        if ev.observed and ev.signature_verified:
            by_actor.setdefault(ev.actor_id,[]).append(ev)
    actors=[]
    for actor in sorted(by_actor):
        if actor in conflicted: continue
        if actor not in matrix: continue
        actors.append(actor)
    return tuple(actors)

def _role_match(required_roles,actors,role_matrix):
    matrix={x.actor_id:x for x in role_matrix}
    options={role:[] for role in required_roles}
    for actor in actors:
        entry=matrix[actor]
        roles=set(_norm_roles(entry.roles))
        for role in required_roles:
            if role in roles:
                options[role].append((entry.authority_group,actor))
    ordered=sorted(required_roles,key=lambda r:(len(options[r]),r))
    chosen=[]
    used_groups=set(); used_actors=set()
    def rec(i):
        if i==len(ordered): return True
        role=ordered[i]
        for group,actor in sorted(options[role],key=lambda x:(x[0],x[1])):
            if group in used_groups or actor in used_actors: continue
            used_groups.add(group); used_actors.add(actor); chosen.append((role,actor,group))
            if rec(i+1): return True
            chosen.pop(); used_actors.remove(actor); used_groups.remove(group)
        return False
    ok=rec(0)
    if not ok: return (),tuple(sorted(required_roles))
    assignments=tuple(RoleAssignment(role,actor,group) for role,actor,group in sorted(chosen))
    satisfied=tuple(sorted(x.role for x in assignments))
    missing=tuple(sorted(set(required_roles)-set(satisfied)))
    return assignments,missing

def evaluate(proposal:ApprovalProposal, role_matrix:tuple[RoleMatrixEntry,...], approvals:tuple[ApprovalEvidence,...], policy:QuorumPolicy)->QuorumResult:
    ok,why=_validate(policy,proposal,role_matrix,approvals)
    if not ok:
        return QuorumResult(Decision.HOLD,(why,),0,(),0,0,(),(),(),(),(),False,False,ApprovalState.PENDING,False)
    rule=_required_rule(policy,proposal)
    if rule is None:
        return QuorumResult(Decision.HOLD,('QUORUM_RULE_MISSING',),0,(),0,0,(),(),(),(),(),False,False,ApprovalState.PENDING,False)
    required_roles=_norm_roles(rule.required_roles)
    actors=_valid_actor_ids(proposal,role_matrix,approvals)
    matrix={x.actor_id:x for x in role_matrix}
    groups=tuple(sorted({matrix[a].authority_group for a in actors}))
    assignments,missing=_role_match(required_roles,actors,role_matrix)
    satisfied=tuple(sorted(x.role for x in assignments))
    quorum_ok=len(groups)>=rule.required_quorum
    roles_ok=not missing and len(assignments)==len(required_roles)
    reasons=[]
    if not quorum_ok: reasons.append('QUORUM_INSUFFICIENT')
    if not roles_ok: reasons.append('REQUIRED_ROLE_MISSING_OR_NOT_INDEPENDENT')
    if not reasons: reasons.append('QUORUM_AND_REQUIRED_ROLES_SATISFIED')
    decision=Decision.ALLOW if quorum_ok and roles_ok else Decision.HOLD
    state=ApprovalState.SATISFIED if decision==Decision.ALLOW else ApprovalState.PENDING
    return QuorumResult(decision,tuple(reasons),rule.required_quorum,required_roles,len(groups),len(actors),actors,groups,satisfied,missing,assignments,quorum_ok,roles_ok,state,decision==Decision.ALLOW)


def default_policy()->QuorumPolicy:
    return QuorumPolicy((
        QuorumRule(0,1,('OPERATOR',)),
        QuorumRule(1,2,('OPERATOR','REVIEWER')),
        QuorumRule(2,3,('OPERATOR','SECURITY','OWNER')),
        QuorumRule(3,4,('OPERATOR','SECURITY','OWNER','LEGAL')),
    ),'QUORUM-BIND','STATE-EPOCH-1')

def default_proposal()->ApprovalProposal:
    return ApprovalProposal('PROP-1',RiskLevel.MEDIUM,BlastRadius.TEAM,'QUORUM-BIND','STATE-EPOCH-1')

def default_role_matrix()->tuple[RoleMatrixEntry,...]:
    b,e='QUORUM-BIND','STATE-EPOCH-1'
    return (
        RoleMatrixEntry('alice',('OPERATOR',),'OPS',True,b,e),
        RoleMatrixEntry('bob',('REVIEWER',),'REVIEW',True,b,e),
        RoleMatrixEntry('carol',('SECURITY',),'SEC',True,b,e),
        RoleMatrixEntry('dave',('OWNER',),'OWNER',True,b,e),
        RoleMatrixEntry('erin',('LEGAL',),'LEGAL',True,b,e),
    )

def default_approvals()->tuple[ApprovalEvidence,...]:
    b,e='QUORUM-BIND','STATE-EPOCH-1'
    return (
        ApprovalEvidence('AP-A','PROP-1','alice',True,True,False,b,e),
        ApprovalEvidence('AP-B','PROP-1','bob',True,True,False,b,e),
    )


def _registry_fp(policy,proposal,role_matrix,approvals):
    return _fp({'policy':_fp(policy),'proposal':_fp(proposal),'roles':sorted((x.actor_id,_fp(x)) for x in role_matrix),'approvals':sorted((x.approval_id,_fp(x)) for x in approvals)})

def prepare_state(policy:QuorumPolicy,proposal:ApprovalProposal,role_matrix:tuple[RoleMatrixEntry,...],approvals:tuple[ApprovalEvidence,...],*,binding:str,state_epoch:str)->PreparedQuorumState:
    if binding!=policy.binding or state_epoch!=policy.state_epoch: raise ValueError('PREPARED_BINDING_OR_EPOCH_MISMATCH')
    role_matrix=tuple(sorted(role_matrix,key=lambda x:x.actor_id))
    approvals=tuple(sorted(approvals,key=lambda x:x.approval_id))
    rf=tuple((x.actor_id,_fp(x)) for x in role_matrix)
    af=tuple((x.approval_id,_fp(x)) for x in approvals)
    pf,qf=_fp(policy),_fp(proposal)
    context=_fp({'policy':pf,'proposal':qf})
    dep=_fp({'roles':rf,'approvals':af})
    reg=_registry_fp(policy,proposal,role_matrix,approvals)
    result=evaluate(proposal,role_matrix,approvals,policy)
    return PreparedQuorumState(policy,proposal,role_matrix,approvals,rf,af,pf,qf,context,dep,reg,result,binding,state_epoch)

def validate_prepared_integrity(st:PreparedQuorumState)->bool:
    if st.binding!=st.policy.binding or st.state_epoch!=st.policy.state_epoch: return False
    if st.policy_fingerprint!=_fp(st.policy) or st.proposal_fingerprint!=_fp(st.proposal): return False
    if st.role_fingerprints!=tuple(sorted((x.actor_id,_fp(x)) for x in st.role_matrix)): return False
    if st.approval_fingerprints!=tuple(sorted((x.approval_id,_fp(x)) for x in st.approvals)): return False
    if st.context_fingerprint!=_fp({'policy':st.policy_fingerprint,'proposal':st.proposal_fingerprint}): return False
    if st.dependency_fingerprint!=_fp({'roles':st.role_fingerprints,'approvals':st.approval_fingerprints}): return False
    if st.registry_fingerprint!=_registry_fp(st.policy,st.proposal,st.role_matrix,st.approvals): return False
    return st.precomputed_result==evaluate(st.proposal,st.role_matrix,st.approvals,st.policy)

def evaluate_prepared(st:PreparedQuorumState,*,current_context_fingerprint:str,current_dependency_fingerprint:str,current_registry_fingerprint:str,prepared_integrity_validated:bool)->QuorumResult:
    if not prepared_integrity_validated:
        return QuorumResult(Decision.HOLD,('PREPARED_INTEGRITY_UNVERIFIED',),0,(),0,0,(),(),(),(),(),False,False,ApprovalState.PENDING,False)
    if current_context_fingerprint!=st.context_fingerprint or current_dependency_fingerprint!=st.dependency_fingerprint or current_registry_fingerprint!=st.registry_fingerprint:
        return QuorumResult(Decision.HOLD,('PREPARED_STATE_STALE',),0,(),0,0,(),(),(),(),(),False,False,ApprovalState.PENDING,False)
    return st.precomputed_result

def make_delta(base:PreparedQuorumState,target:PreparedQuorumState)->QuorumStateDelta:
    br={x.actor_id:x for x in base.role_matrix}; tr={x.actor_id:x for x in target.role_matrix}
    ba={x.approval_id:x for x in base.approvals}; ta={x.approval_id:x for x in target.approvals}
    changed_r=tuple(tr[k] for k in sorted(tr) if k not in br or _fp(tr[k])!=_fp(br[k]))
    removed_r=tuple(sorted(set(br)-set(tr)))
    changed_a=tuple(ta[k] for k in sorted(ta) if k not in ba or _fp(ta[k])!=_fp(ba[k]))
    removed_a=tuple(sorted(set(ba)-set(ta)))
    return QuorumStateDelta(base.registry_fingerprint,target.registry_fingerprint,changed_r,removed_r,changed_a,removed_a,target.proposal,target.policy,target.binding,target.state_epoch)

def apply_delta(base:PreparedQuorumState,delta:QuorumStateDelta)->PreparedQuorumState:
    if base.registry_fingerprint!=delta.base_fingerprint: raise ValueError('DELTA_BASE_MISMATCH')
    r={x.actor_id:x for x in base.role_matrix}; a={x.approval_id:x for x in base.approvals}
    for k in delta.removed_actor_ids: r.pop(k,None)
    for x in delta.changed_roles: r[x.actor_id]=x
    for k in delta.removed_approval_ids: a.pop(k,None)
    for x in delta.changed_approvals: a[x.approval_id]=x
    st=prepare_state(delta.target_policy,delta.target_proposal,tuple(r[k] for k in sorted(r)),tuple(a[k] for k in sorted(a)),binding=delta.binding,state_epoch=delta.state_epoch)
    if st.registry_fingerprint!=delta.target_fingerprint: raise ValueError('DELTA_TARGET_MISMATCH')
    return st

def missing_only_sync_plan(target:PreparedQuorumState,known_role_fps:dict[str,str],known_approval_fps:dict[str,str])->QuorumSyncPlan:
    mr=tuple(k for k,v in target.role_fingerprints if known_role_fps.get(k)!=v)
    ma=tuple(k for k,v in target.approval_fingerprints if known_approval_fps.get(k)!=v)
    meta=len(_canon({'actors':mr,'approvals':ma,'context':target.context_fingerprint,'dependency':target.dependency_fingerprint}))
    full=(len(mr)+len(ma)) >= max(1,len(target.role_fingerprints)+len(target.approval_fingerprints))
    return QuorumSyncPlan(mr,ma,meta,full)

def full_registry_bytes(st:PreparedQuorumState)->int:
    return len(_canon({'policy':st.policy,'proposal':st.proposal,'role_matrix':st.role_matrix,'approvals':st.approvals,'context':st.context_fingerprint,'dependency':st.dependency_fingerprint}))

def delta_bytes(delta:QuorumStateDelta)->int: return len(_canon(delta))

def default_evaluation()->QuorumResult:
    return evaluate(default_proposal(),default_role_matrix(),default_approvals(),default_policy())
