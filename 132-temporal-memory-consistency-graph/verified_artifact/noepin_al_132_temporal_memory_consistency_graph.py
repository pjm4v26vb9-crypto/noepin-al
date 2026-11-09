"""NOEPIN AL 132 — Temporal Memory Consistency Graph — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-132
DCSR: LIMITED INTEGRATION / 限定適用.

Memory references, temporal current candidates, conflicts and reconstructed indexes are audit/reference
candidates only. Memory != Truth. Mention != Memory. Reconstruction does not create a new memory,
known fact, permission, authority, safety proof, execution, or action success.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str, Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class TemporalState(str, Enum):
    CURRENT_CANDIDATE='CURRENT_CANDIDATE'; HISTORICAL_CANDIDATE='HISTORICAL_CANDIDATE'; CONFLICT='CONFLICT'; UNKNOWN_TIME='UNKNOWN_TIME'; NO_MATCH='NO_MATCH'; INVALID='INVALID'
class NextAction(str, Enum):
    MEMORY_REFERENCE_CANDIDATE='MEMORY_REFERENCE_CANDIDATE'; HISTORICAL_REFERENCE_CANDIDATE='HISTORICAL_REFERENCE_CANDIDATE'; HOLD_RECONFIRM_CANDIDATE='HOLD_RECONFIRM_CANDIDATE'; CONTINUE_NO_MATCH_CANDIDATE='CONTINUE_NO_MATCH_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; TEMPORAL_CONFLICT='TEMPORAL_CONFLICT'; CRITICAL_TEMPORAL_CONFLICT='CRITICAL_TEMPORAL_CONFLICT'; UNKNOWN_TIME='UNKNOWN_TIME'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'; NO_CURRENT_CANDIDATE='NO_CURRENT_CANDIDATE'
class RecordKind(str, Enum): MEMORY='MEMORY'; MENTION='MENTION'
class NodeStatus(str, Enum):
    CURRENT='CURRENT'; HISTORICAL='HISTORICAL'; SUPERSEDED='SUPERSEDED'; UNKNOWN_TIME='UNKNOWN_TIME'; MENTION_ONLY='MENTION_ONLY'; BELOW_TRUST='BELOW_TRUST'; OUT_OF_QUERY='OUT_OF_QUERY'

@dataclass(frozen=True)
class MemoryRecord:
    memory_id:str
    entity_id:str
    relation:str
    value:str
    source_id:str
    validity_start:int|None
    validity_end:int|None
    branch_id:str
    supersedes:tuple[str,...]
    kind:RecordKind
    trust:float
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class TemporalPolicy:
    min_trust:float=.60
    unknown_time_blocks_current:bool=True
    critical_conflict_holds:bool=True

@dataclass(frozen=True)
class TemporalMemoryRequest:
    request_id:str
    memories:tuple[MemoryRecord,...]
    query_entity_id:str
    query_relation:str
    query_time:int|None
    critical_use:bool
    policy:TemporalPolicy
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class TemporalNode:
    memory_id:str
    entity_id:str
    relation:str
    value:str
    branch_id:str
    validity_start:int|None
    validity_end:int|None
    status:NodeStatus
    superseded_by:tuple[str,...]
    reasons:tuple[str,...]

@dataclass(frozen=True)
class TemporalConflict:
    entity_id:str
    relation:str
    memory_ids:tuple[str,...]
    values:tuple[str,...]
    branch_ids:tuple[str,...]
    reason:str

@dataclass(frozen=True)
class CurrentCandidate:
    memory_id:str
    value:str
    branch_id:str
    source_id:str
    trust:float

@dataclass(frozen=True)
class TemporalMemoryResult:
    decision:Decision
    next_action:NextAction
    escalation:Escalation
    temporal_state:TemporalState
    reasons:tuple[str,...]
    graph:tuple[TemporalNode,...]
    conflicts:tuple[TemporalConflict,...]
    current_candidates:tuple[CurrentCandidate,...]
    next_gate_candidate:bool
    memory_promoted_to_truth:bool=False
    mention_promoted_to_memory:bool=False
    current_candidate_promoted_to_truth:bool=False
    dcsr_reconstruction_created_memory:bool=False
    sender_authority_inherited:bool=False
    sender_intent_inherited:bool=False
    sender_agreement_inherited:bool=False
    permission_granted:bool=False
    approval_executed:bool=False
    authority_granted:bool=False
    stop_executed:bool=False
    action_executed:bool=False
    plan_committed:bool=False
    publish_executed:bool=False
    external_write_performed:bool=False
    world_truth_proven:bool=False
    domain_authority_promoted:bool=False
    safety_proven:bool=False
    action_success:bool=False

@dataclass(frozen=True)
class PreparedTemporalMemoryState:
    request:TemporalMemoryRequest
    result:TemporalMemoryResult
    context_fingerprint:str
    memory_fingerprint:str
    policy_fingerprint:str
    outcome_fingerprint:str
    integrity_fingerprint:str
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class TemporalMemoryDelta:
    changed_memories:tuple[MemoryRecord,...]
    removed_memory_ids:tuple[str,...]
    query_changed:bool
    policy_changed:bool
    from_manifest_fingerprint:str
    to_manifest_fingerprint:str

@dataclass(frozen=True)
class MissingOnlyPlan:
    missing_or_changed_record_ids:tuple[str,...]
    metadata_bytes_required:int
    full_resend_required:bool


def _obj(v):
    if isinstance(v,Enum): return v.value
    if is_dataclass(v): return {f.name:_obj(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v,dict): return {str(k):_obj(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(tuple,list)): return [_obj(x) for x in v]
    return v

def _canon(v): return json.dumps(_obj(v),ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def _fp(v): return sha256(_canon(v)).hexdigest()
def _finite(x): return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(float(x))
def _manifest_fp(req): return _fp((req.memories,req.query_entity_id,req.query_relation,req.query_time,req.critical_use,req.policy,req.binding,req.state_epoch))

def default_policy(): return TemporalPolicy()

def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    memories=(
        MemoryRecord('MEM-OLD','ENTITY-1','STATUS','A','SRC-1',10,None,'MAIN',(),RecordKind.MEMORY,.90,b,e),
        MemoryRecord('MEM-NEW','ENTITY-1','STATUS','B','SRC-2',20,None,'MAIN',('MEM-OLD',),RecordKind.MEMORY,.92,b,e),
        MemoryRecord('MENTION-1','ENTITY-1','STATUS','C','SRC-3',30,None,'MAIN',(),RecordKind.MENTION,.99,b,e),
        MemoryRecord('MEM-OTHER','ENTITY-2','STATUS','X','SRC-4',10,None,'MAIN',(),RecordKind.MEMORY,.85,b,e),
    )
    return TemporalMemoryRequest('DEFAULT-132',memories,'ENTITY-1','STATUS',None,False,default_policy(),b,e)

def _invalid(reason):
    return TemporalMemoryResult(Decision.HOLD,NextAction.HOLD_RECONFIRM_CANDIDATE,Escalation.INVALID_CONFIGURATION,TemporalState.INVALID,(reason,'MEMORY_NOT_PROMOTED_TO_TRUTH','MENTION_NOT_PROMOTED_TO_MEMORY'),(),(),(),False)

def _validate(req:TemporalMemoryRequest):
    if not req.request_id or not req.binding or not req.state_epoch or not req.query_entity_id or not req.query_relation: return 'INVALID_REQUEST_IDENTITY'
    if req.query_time is not None and (not isinstance(req.query_time,int) or isinstance(req.query_time,bool)): return 'INVALID_QUERY_TIME'
    p=req.policy
    if not _finite(p.min_trust) or not 0<=p.min_trust<=1: return 'INVALID_MIN_TRUST'
    ids=[]; byid={}
    for m in req.memories:
        if not m.memory_id or not m.entity_id or not m.relation or not m.source_id or not m.branch_id: return 'INVALID_MEMORY_IDENTITY'
        if m.binding!=req.binding or m.state_epoch!=req.state_epoch: return 'MEMORY_BINDING_MISMATCH'
        if not isinstance(m.kind,RecordKind): return 'INVALID_RECORD_KIND'
        if not _finite(m.trust) or not 0<=m.trust<=1: return 'INVALID_MEMORY_TRUST'
        if m.validity_start is not None and (not isinstance(m.validity_start,int) or isinstance(m.validity_start,bool)): return 'INVALID_VALIDITY_START'
        if m.validity_end is not None and (not isinstance(m.validity_end,int) or isinstance(m.validity_end,bool)): return 'INVALID_VALIDITY_END'
        if m.validity_start is not None and m.validity_end is not None and m.validity_end<=m.validity_start: return 'INVALID_VALIDITY_INTERVAL'
        if m.memory_id in ids: return 'DUPLICATE_MEMORY_ID'
        ids.append(m.memory_id); byid[m.memory_id]=m
    for m in req.memories:
        if m.memory_id in m.supersedes: return 'SELF_SUPERSEDE'
        if len(set(m.supersedes))!=len(m.supersedes): return 'DUPLICATE_SUPERSEDE_TARGET'
        for sid in m.supersedes:
            if sid not in byid: return 'UNKNOWN_SUPERSEDE_TARGET'
            target=byid[sid]
            if target.entity_id!=m.entity_id or target.relation!=m.relation: return 'CROSS_SUBJECT_SUPERSEDE'
    # Detect supersede cycles.
    graph={m.memory_id:set(m.supersedes) for m in req.memories}
    visiting=set(); done=set()
    def visit(x):
        if x in visiting: return False
        if x in done: return True
        visiting.add(x)
        for y in graph.get(x,()):
            if not visit(y): return False
        visiting.remove(x); done.add(x); return True
    for x in graph:
        if not visit(x): return 'SUPERSEDE_CYCLE'
    return None

def _applies(m:MemoryRecord,qt:int|None)->bool:
    if m.validity_start is None: return False
    if qt is None: return m.validity_end is None
    return m.validity_start<=qt and (m.validity_end is None or qt<m.validity_end)

def evaluate(req:TemporalMemoryRequest)->TemporalMemoryResult:
    bad=_validate(req)
    if bad: return _invalid(bad)
    byid={m.memory_id:m for m in req.memories}
    superseded_by={mid:[] for mid in byid}
    for m in req.memories:
        for sid in m.supersedes: superseded_by[sid].append(m.memory_id)
    relevant=[m for m in req.memories if m.entity_id==req.query_entity_id and m.relation==req.query_relation]
    graph=[]; eligible=[]; unknown=[]
    for m in sorted(req.memories,key=lambda x:x.memory_id):
        reasons=[]
        status=NodeStatus.OUT_OF_QUERY
        if m.kind==RecordKind.MENTION:
            status=NodeStatus.MENTION_ONLY; reasons.append('MENTION_IS_NOT_MEMORY')
        elif m.entity_id!=req.query_entity_id or m.relation!=req.query_relation:
            reasons.append('OUT_OF_QUERY_SUBJECT')
        elif m.trust<req.policy.min_trust:
            status=NodeStatus.BELOW_TRUST; reasons.append('BELOW_MEMORY_REFERENCE_TRUST_THRESHOLD')
        elif m.validity_start is None:
            status=NodeStatus.UNKNOWN_TIME; reasons.append('UNKNOWN_TIME_CANNOT_ESTABLISH_CURRENT')
            unknown.append(m)
        elif superseded_by[m.memory_id]:
            status=NodeStatus.SUPERSEDED; reasons.append('EXPLICITLY_SUPERSEDED')
        elif _applies(m,req.query_time):
            status=NodeStatus.CURRENT if req.query_time is None else NodeStatus.HISTORICAL
            reasons.append('APPLIES_TO_QUERY_TIME')
            eligible.append(m)
        else:
            status=NodeStatus.HISTORICAL; reasons.append('OUTSIDE_QUERY_INTERVAL')
        graph.append(TemporalNode(m.memory_id,m.entity_id,m.relation,m.value,m.branch_id,m.validity_start,m.validity_end,status,tuple(sorted(superseded_by[m.memory_id])),tuple(reasons)))
    if not relevant:
        return TemporalMemoryResult(Decision.ALLOW,NextAction.CONTINUE_NO_MATCH_CANDIDATE,Escalation.NONE,TemporalState.NO_MATCH,('NO_RELEVANT_MEMORY','NO_FACT_OR_TRUTH_INFERRED'),tuple(graph),(),(),True)
    if req.policy.unknown_time_blocks_current and unknown:
        return TemporalMemoryResult(Decision.HOLD,NextAction.HOLD_RECONFIRM_CANDIDATE,Escalation.UNKNOWN_TIME,TemporalState.UNKNOWN_TIME,('RELEVANT_MEMORY_HAS_UNKNOWN_TIME','CURRENT_NOT_ASSERTED','RECONFIRM_OR_RETRIEVE_TIME_EVIDENCE'),tuple(graph),(),(),False)
    # Build conflict only among unsuperseded applicable memory records. Same value is corroborating memory, not conflict.
    values=sorted(set(m.value for m in eligible))
    conflicts=()
    if len(values)>1:
        mids=tuple(sorted(m.memory_id for m in eligible)); branches=tuple(sorted(set(m.branch_id for m in eligible)))
        reason='PARALLEL_BRANCH_CURRENT_AMBIGUITY' if len(branches)>1 else 'OVERLAPPING_TEMPORAL_CONTRADICTION'
        conflicts=(TemporalConflict(req.query_entity_id,req.query_relation,mids,tuple(values),branches,reason),)
        esc=Escalation.CRITICAL_TEMPORAL_CONFLICT if req.critical_use and req.policy.critical_conflict_holds else Escalation.TEMPORAL_CONFLICT
        return TemporalMemoryResult(Decision.HOLD,NextAction.HOLD_RECONFIRM_CANDIDATE,esc,TemporalState.CONFLICT,(reason,'LATEST_ONLY_OVERWRITE_FORBIDDEN','CURRENT_TRUTH_NOT_ASSERTED'),tuple(graph),conflicts,(),False)
    if not eligible:
        return TemporalMemoryResult(Decision.HOLD,NextAction.HOLD_RECONFIRM_CANDIDATE,Escalation.NO_CURRENT_CANDIDATE,TemporalState.HISTORICAL_CANDIDATE,('NO_UNAMBIGUOUS_MEMORY_APPLIES_TO_QUERY_TIME','RECONFIRM_REQUIRED'),tuple(graph),(),(),False)
    cands=tuple(CurrentCandidate(m.memory_id,m.value,m.branch_id,m.source_id,m.trust) for m in sorted(eligible,key=lambda x:(x.memory_id,x.source_id)))
    state=TemporalState.CURRENT_CANDIDATE if req.query_time is None else TemporalState.HISTORICAL_CANDIDATE
    action=NextAction.MEMORY_REFERENCE_CANDIDATE if req.query_time is None else NextAction.HISTORICAL_REFERENCE_CANDIDATE
    return TemporalMemoryResult(Decision.ALLOW,action,Escalation.NONE,state,('TEMPORALLY_CONSISTENT_MEMORY_REFERENCE_CANDIDATE','MEMORY_NOT_PROMOTED_TO_TRUTH','NO_PERMISSION_OR_ACTION_PROMOTION'),tuple(graph),(),cands,True)

def default_evaluation(): return evaluate(default_request())

def _fps(req,result): return (_fp((req.request_id,req.query_entity_id,req.query_relation,req.query_time,req.critical_use,req.binding,req.state_epoch)),_fp(req.memories),_fp(req.policy),_fp(result))
def _integrity_payload(cf,mf,pf,of,b,e): return (cf,mf,pf,of,b,e,'NOEPIN-AL-132-PREPARED-V1','LIMITED_DCSR_NO_MEMORY_CREATION')
def prepare_state(req:TemporalMemoryRequest,*,binding:str,state_epoch:str)->PreparedTemporalMemoryState:
    rr=_invalid('PREPARED_BINDING_OR_EPOCH_MISMATCH') if binding!=req.binding or state_epoch!=req.state_epoch else evaluate(req)
    cf,mf,pf,of=_fps(req,rr); integ=_fp(_integrity_payload(cf,mf,pf,of,binding,state_epoch))
    return PreparedTemporalMemoryState(req,rr,cf,mf,pf,of,integ,binding,state_epoch)
def validate_prepared_integrity(st):
    return isinstance(st,PreparedTemporalMemoryState) and st.integrity_fingerprint==_fp(_integrity_payload(st.context_fingerprint,st.memory_fingerprint,st.policy_fingerprint,st.outcome_fingerprint,st.binding,st.state_epoch))
def evaluate_prepared(st:PreparedTemporalMemoryState,*,integrity_validated:bool,current_context_fingerprint:str,current_memory_fingerprint:str,current_policy_fingerprint:str,current_outcome_fingerprint:str)->TemporalMemoryResult:
    if not integrity_validated or not validate_prepared_integrity(st): return _invalid('PREPARED_INTEGRITY_NOT_VALIDATED')
    if (current_context_fingerprint,current_memory_fingerprint,current_policy_fingerprint,current_outcome_fingerprint)!=(st.context_fingerprint,st.memory_fingerprint,st.policy_fingerprint,st.outcome_fingerprint): return _invalid('PREPARED_FINGERPRINT_MISMATCH')
    return st.result

def make_delta(old:PreparedTemporalMemoryState,new:PreparedTemporalMemoryState)->TemporalMemoryDelta:
    om={x.memory_id:x for x in old.request.memories}; nm={x.memory_id:x for x in new.request.memories}
    cm=tuple(nm[k] for k in sorted(nm) if k not in om or _canon(nm[k])!=_canon(om[k])); rm=tuple(k for k in sorted(om) if k not in nm)
    oq=(old.request.query_entity_id,old.request.query_relation,old.request.query_time,old.request.critical_use)
    nq=(new.request.query_entity_id,new.request.query_relation,new.request.query_time,new.request.critical_use)
    return TemporalMemoryDelta(cm,rm,oq!=nq,old.request.policy!=new.request.policy,_manifest_fp(old.request),_manifest_fp(new.request))

def plan_missing_only(old:PreparedTemporalMemoryState,new:PreparedTemporalMemoryState)->MissingOnlyPlan:
    d=make_delta(old,new); ids=[]
    ids += [f'MEMORY:{x.memory_id}' for x in d.changed_memories]; ids += [f'MEMORY_REMOVED:{x}' for x in d.removed_memory_ids]
    if d.query_changed: ids.append('QUERY_CONTEXT')
    if d.policy_changed: ids.append('POLICY')
    ids=tuple(sorted(ids)); meta=len(_canon((d.from_manifest_fingerprint,d.to_manifest_fingerprint,ids,'LIMITED_DCSR_NO_MEMORY_CREATION')))
    return MissingOnlyPlan(ids,meta,False)
