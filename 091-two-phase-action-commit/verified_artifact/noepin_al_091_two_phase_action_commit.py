"""NOEPIN AL 091 — Two-Phase Action Commit — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Pure 2PC-inspired coordination decision algorithm. It evaluates participant Prepare
Evidence, approval binding and coordinator-restart continuity, then emits Commit or
Abort candidates. It never performs prepare requests, permission checks, resource
locks, approval execution, commit/abort notifications, action execution, compensation,
state commit/publish, external writes, World Truth/Safety proof, or Action Success.

Canonical identity: NOEPIN-AL-091
DCSR level: DIRECT INTEGRATION / 直接統合.
Provenance note: exact registered Origin GUID was not freshly reverified in this
completion session and is intentionally not guessed or regenerated.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json

class Decision(str,Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class PrepareStatus(str,Enum):
    PREPARED='PREPARED'; REJECTED='REJECTED'; TIMEOUT='TIMEOUT'; UNKNOWN='UNKNOWN'
class CommitObservationStatus(str,Enum):
    NOT_OBSERVED='NOT_OBSERVED'; SUCCESS='SUCCESS'; FAILED='FAILED'; UNKNOWN='UNKNOWN'
class TransactionState(str,Enum):
    PREPARE='PREPARE'; COMMIT_CANDIDATE='COMMIT_CANDIDATE'; ABORT_CANDIDATE='ABORT_CANDIDATE'; INCIDENT_HOLD='INCIDENT_HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'

@dataclass(frozen=True)
class ActionSpec:
    action_id:str; participant_ids:tuple[str,...]; effect_fingerprint:str; side_effecting:bool
    observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class Participant:
    participant_id:str; resource_scope:str; mandatory:bool; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class PrepareRecord:
    participant_id:str; tx_id:str; status:PrepareStatus; preconditions_ok:bool
    permission_evidence_valid:bool; resource_ready_evidence:bool; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class ApprovalEvidence:
    approval_id:str; tx_id:str; approved:bool; approval_binding_digest:str; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class CommitOutcomeEvidence:
    participant_id:str; tx_id:str; status:CommitObservationStatus; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class CommitRequest:
    request_id:str; tx_id:str; coordinator_epoch:str; approval_binding_digest:str
    coordinator_restarted:bool; recovered_prepare_fingerprint:str; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class CommitPolicy:
    required_approvals:int; require_all_mandatory:bool; require_resource_ready_for_side_effects:bool
    allow_commit_candidate:bool; binding:str; state_epoch:str; revoked:bool=False
@dataclass(frozen=True)
class TwoPhaseCommitResult:
    decision:Decision; transaction_state:TransactionState; reasons:tuple[str,...]
    prepared_participant_ids:tuple[str,...]; rejected_participant_ids:tuple[str,...]
    timeout_participant_ids:tuple[str,...]; unknown_participant_ids:tuple[str,...]
    commit_candidate:bool; abort_candidate:bool; human_approval_candidate:bool
    incident_candidate:bool; compensation_candidate:bool; coordinator_recovery_validated:bool
    next_gate_candidate:bool
    permission_granted:bool=False; approval_executed:bool=False; prepare_request_executed:bool=False
    resource_lock_mutated:bool=False; commit_executed:bool=False; abort_executed:bool=False
    action_executed:bool=False; compensation_executed:bool=False; plan_committed:bool=False
    atomic_publish_executed:bool=False; external_write_performed:bool=False
    world_truth_proven:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedCommitState:
    request:CommitRequest; actions:tuple[ActionSpec,...]; participants:tuple[Participant,...]
    prepares:tuple[PrepareRecord,...]; approvals:tuple[ApprovalEvidence,...]
    outcomes:tuple[CommitOutcomeEvidence,...]; policy:CommitPolicy
    record_fingerprints:tuple[tuple[str,str],...]; context_fingerprint:str
    dependency_fingerprint:str; policy_fingerprint:str; registry_fingerprint:str
    prepare_set_fingerprint:str; precomputed_result:TwoPhaseCommitResult; binding:str; state_epoch:str
@dataclass(frozen=True)
class CommitStateDelta:
    base_fingerprint:str; target_fingerprint:str
    changed_actions:tuple[ActionSpec,...]; removed_action_ids:tuple[str,...]
    changed_participants:tuple[Participant,...]; removed_participant_ids:tuple[str,...]
    changed_prepares:tuple[PrepareRecord,...]; removed_prepare_ids:tuple[str,...]
    changed_approvals:tuple[ApprovalEvidence,...]; removed_approval_ids:tuple[str,...]
    changed_outcomes:tuple[CommitOutcomeEvidence,...]; removed_outcome_ids:tuple[str,...]
    target_request:CommitRequest|None; target_policy:CommitPolicy|None; binding:str; state_epoch:str
@dataclass(frozen=True)
class CommitSyncPlan:
    missing_or_changed_record_ids:tuple[str,...]; metadata_bytes_required:int; full_resend_required:bool

def _cv(x):
    if isinstance(x,Enum): return x.value
    if hasattr(x,'__dataclass_fields__'): return {k:_cv(getattr(x,k)) for k in x.__dataclass_fields__}
    if isinstance(x,tuple): return [_cv(v) for v in x]
    if isinstance(x,list): return [_cv(v) for v in x]
    if isinstance(x,dict): return {str(k):_cv(x[k]) for k in sorted(x)}
    return x
def _canon(x)->bytes: return json.dumps(_cv(x),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def _fp(x)->str: return sha256(_canon(x)).hexdigest()
def _prepare_fp(prepares):
    rows=tuple(sorted((p.participant_id,p.tx_id,p.status.value,p.preconditions_ok,p.permission_evidence_valid,p.resource_ready_evidence,p.observed,p.binding,p.state_epoch) for p in prepares))
    return _fp(rows)

def _result(decision,state,reasons=(),prepared=(),rejected=(),timeouts=(),unknown=(),commit=False,abort=False,human=False,incident=False,comp=False,recovery=False,next_gate=False):
    return TwoPhaseCommitResult(decision,state,tuple(reasons),tuple(prepared),tuple(rejected),tuple(timeouts),tuple(unknown),commit,abort,human,incident,comp,recovery,next_gate)
def _hold(reason,*,prepared=(),rejected=(),timeouts=(),unknown=(),abort=True,incident=False,comp=False,recovery=False):
    state=TransactionState.INCIDENT_HOLD if incident else TransactionState.ABORT_CANDIDATE if abort else TransactionState.PREPARE
    return _result(Decision.HOLD,state,(reason,),prepared,rejected,timeouts,unknown,False,abort,False,incident,comp,recovery,False)

def _validate(req,actions,participants,prepares,approvals,outcomes,policy):
    if policy.revoked: return 'POLICY_REVOKED'
    if req.binding!=policy.binding or req.state_epoch!=policy.state_epoch: return 'REQUEST_SCOPE_MISMATCH'
    if not req.request_id or not req.tx_id or not req.coordinator_epoch or not req.approval_binding_digest: return 'INCOMPLETE_REQUEST_IDENTITY'
    if policy.required_approvals<0: return 'INVALID_APPROVAL_REQUIREMENT'
    pids=[p.participant_id for p in participants]
    if not pids: return 'EMPTY_PARTICIPANT_SET'
    if len(pids)!=len(set(pids)): return 'DUPLICATE_PARTICIPANT_ID'
    pm={p.participant_id:p for p in participants}
    for p in participants:
        if not p.observed or not p.participant_id: return 'PARTICIPANT_UNOBSERVED_OR_INVALID'
        if p.binding!=policy.binding or p.state_epoch!=policy.state_epoch: return 'PARTICIPANT_SCOPE_MISMATCH'
    aids=[a.action_id for a in actions]
    if not aids or len(aids)!=len(set(aids)): return 'EMPTY_OR_DUPLICATE_ACTION_ID'
    for a in actions:
        if not a.observed or not a.action_id or not a.effect_fingerprint: return 'ACTION_UNOBSERVED_OR_INVALID'
        if a.binding!=policy.binding or a.state_epoch!=policy.state_epoch: return 'ACTION_SCOPE_MISMATCH'
        if not a.participant_ids or any(x not in pm for x in a.participant_ids): return 'ACTION_PARTICIPANT_UNKNOWN'
    prids=[p.participant_id for p in prepares]
    if len(prids)!=len(set(prids)): return 'DUPLICATE_PREPARE_RECORD'
    if set(prids)!=set(pids): return 'PREPARE_COVERAGE_INCOMPLETE'
    for p in prepares:
        if not p.observed: return 'PREPARE_UNOBSERVED'
        if p.tx_id!=req.tx_id: return 'PREPARE_TRANSACTION_MISMATCH'
        if p.binding!=policy.binding or p.state_epoch!=policy.state_epoch: return 'PREPARE_SCOPE_MISMATCH'
    appids=[a.approval_id for a in approvals]
    if len(appids)!=len(set(appids)): return 'DUPLICATE_APPROVAL_ID'
    for a in approvals:
        if a.tx_id!=req.tx_id: return 'APPROVAL_TRANSACTION_MISMATCH'
        if a.binding!=policy.binding or a.state_epoch!=policy.state_epoch: return 'APPROVAL_SCOPE_MISMATCH'
    oids=[o.participant_id for o in outcomes]
    if len(oids)!=len(set(oids)): return 'DUPLICATE_COMMIT_OUTCOME'
    for o in outcomes:
        if o.participant_id not in pm: return 'COMMIT_OUTCOME_UNKNOWN_PARTICIPANT'
        if o.tx_id!=req.tx_id: return 'COMMIT_OUTCOME_TRANSACTION_MISMATCH'
        if o.binding!=policy.binding or o.state_epoch!=policy.state_epoch: return 'COMMIT_OUTCOME_SCOPE_MISMATCH'
    return None

def evaluate(req:CommitRequest,actions:tuple[ActionSpec,...],participants:tuple[Participant,...],prepares:tuple[PrepareRecord,...],approvals:tuple[ApprovalEvidence,...],outcomes:tuple[CommitOutcomeEvidence,...],policy:CommitPolicy)->TwoPhaseCommitResult:
    actions=tuple(sorted(actions,key=lambda x:x.action_id)); participants=tuple(sorted(participants,key=lambda x:x.participant_id)); prepares=tuple(sorted(prepares,key=lambda x:x.participant_id)); approvals=tuple(sorted(approvals,key=lambda x:x.approval_id)); outcomes=tuple(sorted(outcomes,key=lambda x:x.participant_id))
    err=_validate(req,actions,participants,prepares,approvals,outcomes,policy)
    if err: return _hold(err,abort=True)
    if not req.observed: return _hold('REQUEST_UNOBSERVED',abort=True)
    prepared=tuple(p.participant_id for p in prepares if p.status==PrepareStatus.PREPARED)
    rejected=tuple(p.participant_id for p in prepares if p.status==PrepareStatus.REJECTED or not p.preconditions_ok or not p.permission_evidence_valid)
    timeouts=tuple(p.participant_id for p in prepares if p.status==PrepareStatus.TIMEOUT)
    unknown=tuple(p.participant_id for p in prepares if p.status==PrepareStatus.UNKNOWN)
    # External commit outcome evidence is analyzed only as evidence; this module never executes commit.
    failed_outcomes=tuple(o.participant_id for o in outcomes if o.observed and o.status==CommitObservationStatus.FAILED)
    unknown_outcomes=tuple(o.participant_id for o in outcomes if (not o.observed) or o.status==CommitObservationStatus.UNKNOWN)
    if failed_outcomes:
        return _hold('COMMIT_FAILURE_EVIDENCE',prepared=prepared,rejected=rejected,timeouts=timeouts,unknown=unknown,abort=False,incident=True,comp=True)
    if unknown_outcomes:
        return _hold('COMMIT_OUTCOME_UNCERTAIN',prepared=prepared,rejected=rejected,timeouts=timeouts,unknown=unknown,abort=False,incident=True,comp=True)
    if timeouts:
        return _hold('PARTICIPANT_PREPARE_TIMEOUT',prepared=prepared,rejected=rejected,timeouts=timeouts,unknown=unknown,abort=True)
    if unknown:
        return _hold('PARTICIPANT_PREPARE_UNKNOWN',prepared=prepared,rejected=rejected,timeouts=timeouts,unknown=unknown,abort=True)
    # A participant can report PREPARED only if its checks are valid.
    if rejected:
        return _result(Decision.DENY,TransactionState.ABORT_CANDIDATE,('PARTICIPANT_REJECTED_OR_CHECK_FAILED',),prepared,rejected,timeouts,unknown,False,True,False,False,False,False,False)
    side_effect_participants={pid for a in actions if a.side_effecting for pid in a.participant_ids}
    not_ready=tuple(sorted(p.participant_id for p in prepares if p.participant_id in side_effect_participants and policy.require_resource_ready_for_side_effects and not p.resource_ready_evidence))
    if not_ready:
        return _result(Decision.DENY,TransactionState.ABORT_CANDIDATE,('RESOURCE_NOT_READY',),prepared,not_ready,timeouts,unknown,False,True,False,False,False,False,False)
    mandatory={p.participant_id for p in participants if p.mandatory}
    if policy.require_all_mandatory and not mandatory.issubset(set(prepared)):
        return _result(Decision.DENY,TransactionState.ABORT_CANDIDATE,('MANDATORY_PARTICIPANT_NOT_PREPARED',),prepared,tuple(sorted(mandatory-set(prepared))),timeouts,unknown,False,True,False,False,False,False,False)
    # Coordinator restart continuity: recovered prepare-set identity must match current typed Prepare Evidence.
    recovery_valid=False
    if req.coordinator_restarted:
        cur=_prepare_fp(prepares)
        if not req.recovered_prepare_fingerprint or req.recovered_prepare_fingerprint!=cur:
            return _hold('COORDINATOR_RECOVERY_FINGERPRINT_MISMATCH',prepared=prepared,abort=True)
        recovery_valid=True
    valid_approvals=tuple(a for a in approvals if a.observed and a.approved and a.approval_binding_digest==req.approval_binding_digest)
    malformed_observed=tuple(a for a in approvals if a.observed and a.approved and a.approval_binding_digest!=req.approval_binding_digest)
    if malformed_observed:
        return _hold('APPROVAL_BINDING_MISMATCH',prepared=prepared,abort=True,recovery=recovery_valid)
    if len(valid_approvals)<policy.required_approvals:
        return _result(Decision.HUMAN_APPROVAL,TransactionState.HUMAN_APPROVAL,('APPROVAL_INSUFFICIENT',),prepared,(),(),(),False,False,True,False,False,recovery_valid,False)
    if not policy.allow_commit_candidate:
        return _hold('POLICY_DISALLOWS_COMMIT_CANDIDATE',prepared=prepared,abort=True,recovery=recovery_valid)
    if set(prepared)!=set(p.participant_id for p in participants):
        return _hold('NOT_ALL_PARTICIPANTS_PREPARED',prepared=prepared,abort=True,recovery=recovery_valid)
    return _result(Decision.ALLOW,TransactionState.COMMIT_CANDIDATE,('ALL_PARTICIPANTS_PREPARED','APPROVAL_REVALIDATED'),prepared,(),(),(),True,False,False,False,False,recovery_valid,True)

def default_request(): return CommitRequest('REQ-91','TX-91','COORD-EPOCH-1','APPROVAL-BIND-91',False,'',True,'TPC-BIND','STATE-EPOCH-1')
def default_policy(): return CommitPolicy(1,True,True,True,'TPC-BIND','STATE-EPOCH-1')
def default_actions():
    p=default_policy()
    return (ActionSpec('A',('P-A',),'EFF-A',True,True,p.binding,p.state_epoch),ActionSpec('B',('P-B',),'EFF-B',True,True,p.binding,p.state_epoch))
def default_participants():
    p=default_policy()
    return (Participant('P-A','RESOURCE-A',True,True,p.binding,p.state_epoch),Participant('P-B','RESOURCE-B',True,True,p.binding,p.state_epoch))
def default_prepares():
    r=default_request(); p=default_policy()
    return (PrepareRecord('P-A',r.tx_id,PrepareStatus.PREPARED,True,True,True,True,p.binding,p.state_epoch),PrepareRecord('P-B',r.tx_id,PrepareStatus.PREPARED,True,True,True,True,p.binding,p.state_epoch))
def default_approvals():
    r=default_request(); p=default_policy()
    return (ApprovalEvidence('APP-1',r.tx_id,True,r.approval_binding_digest,True,p.binding,p.state_epoch),)
def default_outcomes(): return ()
def default_evaluation(): return evaluate(default_request(),default_actions(),default_participants(),default_prepares(),default_approvals(),default_outcomes(),default_policy())

def _canon_sets(actions,participants,prepares,approvals,outcomes):
    return (tuple(sorted(actions,key=lambda x:x.action_id)),tuple(sorted(participants,key=lambda x:x.participant_id)),tuple(sorted(prepares,key=lambda x:x.participant_id)),tuple(sorted(approvals,key=lambda x:x.approval_id)),tuple(sorted(outcomes,key=lambda x:x.participant_id)))
def _record_fps(actions,participants,prepares,approvals,outcomes):
    rows=[]
    rows += [(f'ACTION:{x.action_id}',_fp(x)) for x in actions]
    rows += [(f'PARTICIPANT:{x.participant_id}',_fp(x)) for x in participants]
    rows += [(f'PREPARE:{x.participant_id}',_fp(x)) for x in prepares]
    rows += [(f'APPROVAL:{x.approval_id}',_fp(x)) for x in approvals]
    rows += [(f'OUTCOME:{x.participant_id}',_fp(x)) for x in outcomes]
    return tuple(sorted(rows))
def prepare_state(req,actions,participants,prepares,approvals,outcomes,policy,*,binding,state_epoch):
    actions,participants,prepares,approvals,outcomes=_canon_sets(actions,participants,prepares,approvals,outcomes)
    result=evaluate(req,actions,participants,prepares,approvals,outcomes,policy)
    context=_fp((req,actions)); dependency=_fp((participants,prepares,approvals,outcomes)); policy_fp=_fp(policy); records=_record_fps(actions,participants,prepares,approvals,outcomes); registry=_fp(records); prep_fp=_prepare_fp(prepares)
    return PreparedCommitState(req,actions,participants,prepares,approvals,outcomes,policy,records,context,dependency,policy_fp,registry,prep_fp,result,binding,state_epoch)
def validate_prepared_integrity(st):
    return (st.context_fingerprint==_fp((st.request,st.actions)) and st.dependency_fingerprint==_fp((st.participants,st.prepares,st.approvals,st.outcomes)) and st.policy_fingerprint==_fp(st.policy) and st.record_fingerprints==_record_fps(st.actions,st.participants,st.prepares,st.approvals,st.outcomes) and st.registry_fingerprint==_fp(st.record_fingerprints) and st.prepare_set_fingerprint==_prepare_fp(st.prepares) and st.precomputed_result==evaluate(st.request,st.actions,st.participants,st.prepares,st.approvals,st.outcomes,st.policy))
def evaluate_prepared(st,*,current_context_fingerprint,current_dependency_fingerprint,current_policy_fingerprint,current_registry_fingerprint,prepared_integrity_validated):
    # Integrity is independently validated once before reuse. Recomputing full registry
    # integrity here would defeat prepared-result reuse and duplicate the validator.
    if not prepared_integrity_validated: return _hold('PREPARED_INTEGRITY_UNVERIFIED',abort=True)
    if st.binding!=st.policy.binding or st.state_epoch!=st.policy.state_epoch: return _hold('PREPARED_SCOPE_MISMATCH',abort=True)
    if current_context_fingerprint!=st.context_fingerprint or current_dependency_fingerprint!=st.dependency_fingerprint or current_policy_fingerprint!=st.policy_fingerprint or current_registry_fingerprint!=st.registry_fingerprint:
        return _hold('PREPARED_STATE_STALE',abort=True)
    return st.precomputed_result

def make_delta(base,target):
    def diff(old,new,key):
        om={key(x):x for x in old}; nm={key(x):x for x in new}
        changed=tuple(nm[k] for k in sorted(nm) if k not in om or om[k]!=nm[k]); removed=tuple(sorted(set(om)-set(nm)))
        return changed,removed
    ca,ra=diff(base.actions,target.actions,lambda x:x.action_id); cp,rp=diff(base.participants,target.participants,lambda x:x.participant_id); cpr,rpr=diff(base.prepares,target.prepares,lambda x:x.participant_id); cap,rap=diff(base.approvals,target.approvals,lambda x:x.approval_id); co,ro=diff(base.outcomes,target.outcomes,lambda x:x.participant_id)
    return CommitStateDelta(base.registry_fingerprint,target.registry_fingerprint,ca,ra,cp,rp,cpr,rpr,cap,rap,co,ro,target.request if base.request!=target.request else None,target.policy if base.policy!=target.policy else None,target.binding,target.state_epoch)
def apply_delta(base,delta):
    if base.registry_fingerprint!=delta.base_fingerprint: raise ValueError('BASE_FINGERPRINT_MISMATCH')
    def apply(old,changed,removed,key):
        d={key(x):x for x in old}
        for k in removed: d.pop(k,None)
        for x in changed: d[key(x)]=x
        return tuple(d[k] for k in sorted(d))
    actions=apply(base.actions,delta.changed_actions,delta.removed_action_ids,lambda x:x.action_id); participants=apply(base.participants,delta.changed_participants,delta.removed_participant_ids,lambda x:x.participant_id); prepares=apply(base.prepares,delta.changed_prepares,delta.removed_prepare_ids,lambda x:x.participant_id); approvals=apply(base.approvals,delta.changed_approvals,delta.removed_approval_ids,lambda x:x.approval_id); outcomes=apply(base.outcomes,delta.changed_outcomes,delta.removed_outcome_ids,lambda x:x.participant_id)
    req=delta.target_request if delta.target_request is not None else base.request; policy=delta.target_policy if delta.target_policy is not None else base.policy
    target=prepare_state(req,actions,participants,prepares,approvals,outcomes,policy,binding=delta.binding,state_epoch=delta.state_epoch)
    if target.registry_fingerprint!=delta.target_fingerprint: raise ValueError('TARGET_FINGERPRINT_MISMATCH')
    return target
def missing_only_sync_plan(target,known_record_fingerprints:dict[str,str]):
    missing=tuple(sorted(k for k,v in target.record_fingerprints if known_record_fingerprints.get(k)!=v))
    return CommitSyncPlan(missing,len(_canon(missing)),False)
def full_registry_bytes(st): return len(_canon({'request':st.request,'actions':st.actions,'participants':st.participants,'prepares':st.prepares,'approvals':st.approvals,'outcomes':st.outcomes,'policy':st.policy}))
def delta_bytes(delta): return len(_canon(delta))
