"""NOEPIN AL 135 — Contradiction-Aware Memory Resolver — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-135
DCSR: LIMITED INTEGRATION / 限定適用.

Memory resolution outputs are audit/reference candidates only.
Memory != Truth. Mention != Memory. Selected Memory Candidate != known Fact / World Truth.
Source Trust != Source Authority. Recency != Truth. Refresh Request Candidate != external retrieval execution.
No resolution candidate performs a memory write, permission grant, approval, authority change or action execution.
DCSR reconstruction does not create a new memory or known fact.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str,Enum): ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class ResolutionState(str,Enum): SELECTED_CANDIDATE='SELECTED_CANDIDATE'; CONTEXT_PARALLEL='CONTEXT_PARALLEL'; UNRESOLVED_CONFLICT='UNRESOLVED_CONFLICT'; REFRESH_NEEDED='REFRESH_NEEDED'; NO_CONFLICT='NO_CONFLICT'; MENTION_ONLY='MENTION_ONLY'; EMPTY='EMPTY'; INVALID='INVALID'
class NextAction(str,Enum): SELECTED_MEMORY_CANDIDATE='SELECTED_MEMORY_CANDIDATE'; PARALLEL_MEMORY_CANDIDATE='PARALLEL_MEMORY_CANDIDATE'; HOLD_CONFLICT_RECHECK='HOLD_CONFLICT_RECHECK'; REFRESH_REQUEST_CANDIDATE='REFRESH_REQUEST_CANDIDATE'; NO_MEMORY_CANDIDATE='NO_MEMORY_CANDIDATE'
class Escalation(str,Enum): NONE='NONE'; SOURCE_UNKNOWN='SOURCE_UNKNOWN'; CONTEXT_PARALLEL='CONTEXT_PARALLEL'; IMPORTANT_CONFLICT='IMPORTANT_CONFLICT'; NO_DECISIVE_EVIDENCE='NO_DECISIVE_EVIDENCE'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'
class RecordKind(str,Enum): MEMORY='MEMORY'; MENTION='MENTION'

@dataclass(frozen=True)
class MemoryRecord:
    memory_id:str; entity_id:str; relation:str; value:str; context_scope:str; source_id:str|None
    source_trust:float; timestamp:int|None; explicit_latest:bool; critical:bool; kind:RecordKind
    purpose_id:str; binding:str; state_epoch:str

@dataclass(frozen=True)
class ResolutionPolicy:
    min_source_trust:float=.55
    unknown_source_trust_cap:float=.20
    decisive_margin:float=.14
    trust_weight:float=.55
    context_weight:float=.25
    freshness_weight:float=.20
    explicit_latest_bonus:float=.18
    max_freshness_age:int=1000
    unresolved_hold:bool=True
    critical_hold:bool=True

@dataclass(frozen=True)
class ResolutionRequest:
    request_id:str; memories:tuple[MemoryRecord,...]; target_context:str; now:int; policy:ResolutionPolicy
    binding:str; state_epoch:str

@dataclass(frozen=True)
class CandidateAssessment:
    memory_id:str; effective_trust:float; context_match:float; freshness:float; score:float
    source_known:bool; reasons:tuple[str,...]

@dataclass(frozen=True)
class ConflictExplanation:
    group_key:str; memory_ids:tuple[str,...]; values:tuple[str,...]; status:str; reasons:tuple[str,...]

@dataclass(frozen=True)
class ResolutionResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; resolution_state:ResolutionState; reasons:tuple[str,...]
    selected_memory_ids:tuple[str,...]; unresolved_memory_ids:tuple[str,...]; refresh_memory_ids:tuple[str,...]
    assessments:tuple[CandidateAssessment,...]; conflict_explanations:tuple[ConflictExplanation,...]; next_gate_candidate:bool
    memory_promoted_to_truth:bool=False; mention_promoted_to_memory:bool=False; selected_promoted_to_known_fact:bool=False
    source_trust_promoted_to_source_authority:bool=False; recency_promoted_to_truth:bool=False; conflict_auto_overwritten:bool=False
    refresh_executed:bool=False; memory_write_performed:bool=False; dcsr_reconstruction_created_memory:bool=False
    sender_authority_inherited:bool=False; sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False
    permission_granted:bool=False; approval_executed:bool=False; authority_granted:bool=False; stop_executed:bool=False
    action_executed:bool=False; plan_committed:bool=False; publish_executed:bool=False; external_write_performed:bool=False
    world_truth_proven:bool=False; domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False

@dataclass(frozen=True)
class PreparedResolutionState:
    request:ResolutionRequest; result:ResolutionResult; context_fingerprint:str; memory_fingerprint:str
    policy_fingerprint:str; outcome_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str

@dataclass(frozen=True)
class ResolutionDelta:
    changed_memories:tuple[MemoryRecord,...]; removed_memory_ids:tuple[str,...]; context_changed:bool; now_changed:bool
    policy_changed:bool; from_manifest_fingerprint:str; to_manifest_fingerprint:str

@dataclass(frozen=True)
class MissingOnlyPlan:
    missing_or_changed_record_ids:tuple[str,...]; metadata_bytes_required:int; full_resend_required:bool

def _obj(v):
    if isinstance(v,Enum): return v.value
    if is_dataclass(v): return {f.name:_obj(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v,dict): return {str(k):_obj(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(tuple,list)): return [_obj(x) for x in v]
    return v

def _canon(v): return json.dumps(_obj(v),ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def _fp(v): return sha256(_canon(v)).hexdigest()
def _finite(x): return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(float(x))
def _manifest_fp(req): return _fp((req.memories,req.target_context,req.now,req.policy,req.binding,req.state_epoch))

def default_policy(): return ResolutionPolicy()
def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    memories=(
      MemoryRecord('MEM-OLD','ENTITY-1','setting','A','ROOM','SRC-OLD',.82,100,False,False,RecordKind.MEMORY,'PURPOSE-1',b,e),
      MemoryRecord('MEM-NEW','ENTITY-1','setting','B','ROOM','SRC-NEW',.94,200,True,False,RecordKind.MEMORY,'PURPOSE-1',b,e),
    )
    return ResolutionRequest('REQ-135',memories,'ROOM',220,default_policy(),b,e)

def _invalid(reason):
    return ResolutionResult(Decision.HOLD,NextAction.HOLD_CONFLICT_RECHECK,Escalation.INVALID_CONFIGURATION,ResolutionState.INVALID,(reason,'NO_MEMORY_WRITE'),(),(),(),(),(),False)

def _validate(req):
    p=req.policy
    nums=(p.min_source_trust,p.unknown_source_trust_cap,p.decisive_margin,p.trust_weight,p.context_weight,p.freshness_weight,p.explicit_latest_bonus)
    if not all(_finite(x) for x in nums): return 'NONFINITE_POLICY'
    if not (0<=p.min_source_trust<=1 and 0<=p.unknown_source_trust_cap<=1 and 0<=p.decisive_margin<=1): return 'POLICY_RANGE'
    if min(p.trust_weight,p.context_weight,p.freshness_weight,p.explicit_latest_bonus)<0 or p.max_freshness_age<=0: return 'POLICY_RANGE'
    if not isinstance(req.now,int) or isinstance(req.now,bool): return 'INVALID_NOW'
    ids=set()
    for x in req.memories:
        if x.memory_id in ids: return 'DUPLICATE_MEMORY_ID'
        ids.add(x.memory_id)
        if x.binding!=req.binding or x.state_epoch!=req.state_epoch: return 'STATE_BINDING_MISMATCH'
        if not _finite(x.source_trust) or not 0<=x.source_trust<=1: return 'INVALID_SOURCE_TRUST'
        if x.timestamp is not None and (not isinstance(x.timestamp,int) or isinstance(x.timestamp,bool)): return 'INVALID_TIMESTAMP'
    return None

def _context_match(scope,target):
    s=(scope or '').strip(); t=(target or '').strip()
    if s in ('*','GLOBAL'): return .75
    if t in ('*','ANY',''): return .65
    return 1.0 if s==t else 0.0

def _assessment(x,req):
    p=req.policy; known=bool(x.source_id and x.source_id.strip())
    trust=x.source_trust if known else min(x.source_trust,p.unknown_source_trust_cap)
    cm=_context_match(x.context_scope,req.target_context)
    if x.timestamp is None: freshness=.20
    else:
        age=max(0,req.now-x.timestamp); freshness=max(0.0,1.0-age/p.max_freshness_age)
    score=trust*p.trust_weight+cm*p.context_weight+freshness*p.freshness_weight+(p.explicit_latest_bonus if x.explicit_latest else 0.0)
    reasons=['SOURCE_KNOWN' if known else 'SOURCE_UNKNOWN_TRUST_CAPPED']
    reasons.append('CONTEXT_EXACT' if cm==1 else ('CONTEXT_GLOBAL' if cm>.7 else ('CONTEXT_OPEN' if cm>0 else 'CONTEXT_MISMATCH')))
    reasons.append('TIMESTAMP_KNOWN' if x.timestamp is not None else 'TIMESTAMP_UNKNOWN')
    if x.explicit_latest: reasons.append('EXPLICIT_LATEST')
    return CandidateAssessment(x.memory_id,round(trust,12),round(cm,12),round(freshness,12),round(score,12),known,tuple(reasons))

def _parallel_by_context(xs,target):
    if target not in ('*','ANY',''): return False
    scopes={x.context_scope for x in xs if x.context_scope not in ('*','GLOBAL')}
    if len(scopes)<2: return False
    by_scope={}
    for x in xs:
        if x.context_scope in ('*','GLOBAL'): return False
        by_scope.setdefault(x.context_scope,set()).add(x.value)
    return all(len(v)==1 for v in by_scope.values()) and len({x.value for x in xs})>1

def evaluate(req):
    err=_validate(req)
    if err: return _invalid(err)
    memories=tuple(sorted((x for x in req.memories if x.kind==RecordKind.MEMORY),key=lambda x:(x.entity_id,x.relation,x.context_scope,x.memory_id)))
    mentions=tuple(x for x in req.memories if x.kind==RecordKind.MENTION)
    if not memories:
        state=ResolutionState.MENTION_ONLY if mentions else ResolutionState.EMPTY
        return ResolutionResult(Decision.ALLOW,NextAction.NO_MEMORY_CANDIDATE,Escalation.NONE,state,('NO_MEMORY_RECORDS','MENTION_NOT_PROMOTED_TO_MEMORY','NO_MEMORY_WRITE'),(),(),(),(),(),True)
    groups={}
    for x in memories: groups.setdefault((x.entity_id,x.relation),[]).append(x)
    selected=[]; unresolved=[]; refresh=[]; assessments=[]; explanations=[]
    saw_parallel=False; saw_unknown=False; saw_unresolved=False; saw_critical=False
    for key in sorted(groups):
        xs=groups[key]
        vals=sorted({x.value for x in xs})
        amap={a.memory_id:a for a in (_assessment(x,req) for x in xs)}; assessments.extend(amap[x.memory_id] for x in sorted(xs,key=lambda z:z.memory_id))
        group_key=f'{key[0]}::{key[1]}'
        unknown=[x for x in xs if not amap[x.memory_id].source_known]
        if unknown:
            saw_unknown=True; refresh.extend(x.memory_id for x in unknown)
        if len(vals)==1:
            best=max(xs,key=lambda x:(amap[x.memory_id].score,x.timestamp if x.timestamp is not None else -10**18,x.memory_id))
            selected.append(best.memory_id)
            explanations.append(ConflictExplanation(group_key,tuple(sorted(x.memory_id for x in xs)),tuple(vals),'NO_CONFLICT',('SAME_VALUE_NO_CONTRADICTION','BEST_REFERENCE_CANDIDATE_ONLY')))
            continue
        if _parallel_by_context(xs,req.target_context):
            saw_parallel=True; selected.extend(sorted(x.memory_id for x in xs))
            explanations.append(ConflictExplanation(group_key,tuple(sorted(x.memory_id for x in xs)),tuple(vals),'CONTEXT_PARALLEL',('DISTINCT_CONTEXT_SCOPES','VALUES_MAY_COEXIST','NO_CONFLICT_COLLAPSE')))
            continue
        applicable=[x for x in xs if amap[x.memory_id].context_match>0]
        if not applicable: applicable=xs
        ranked=sorted(applicable,key=lambda x:(-amap[x.memory_id].score,-(x.timestamp if x.timestamp is not None else -10**18),x.memory_id))
        top=ranked[0]; second=ranked[1] if len(ranked)>1 else None; ta=amap[top.memory_id]
        decisive=False; why=[]
        if second is None:
            decisive=True; why=['ONLY_APPLICABLE_MEMORY']
        else:
            sa=amap[second.memory_id]; margin=ta.score-sa.score
            if top.explicit_latest and ta.effective_trust>=req.policy.min_source_trust and margin>=req.policy.decisive_margin:
                decisive=True; why=['EXPLICIT_LATEST_HIGH_TRUST','DECISIVE_MARGIN']
            elif ta.context_match==1.0 and sa.context_match==0.0 and ta.effective_trust>=req.policy.min_source_trust:
                decisive=True; why=['CURRENT_CONTEXT_SCOPE_MATCH','OTHER_CONTEXT_NOT_APPLICABLE']
        if decisive:
            selected.append(top.memory_id)
            explanations.append(ConflictExplanation(group_key,tuple(sorted(x.memory_id for x in xs)),tuple(vals),'SELECTED_CANDIDATE',tuple(why+['SELECTION_IS_CANDIDATE_ONLY','RECENCY_NOT_PROMOTED_TO_TRUTH'])))
        else:
            saw_unresolved=True; saw_critical=saw_critical or any(x.critical for x in applicable)
            unresolved.extend(sorted(x.memory_id for x in applicable))
            refresh.extend(x.memory_id for x in applicable if x.timestamp is None or not amap[x.memory_id].source_known)
            explanations.append(ConflictExplanation(group_key,tuple(sorted(x.memory_id for x in xs)),tuple(vals),'UNRESOLVED_CONFLICT',('NO_DECISIVE_EVIDENCE','CONFLICT_PRESERVED','NO_AUTOMATIC_OVERWRITE','REFRESH_OR_RECHECK_REQUIRED')))
    selected=tuple(sorted(set(selected))); unresolved=tuple(sorted(set(unresolved))); refresh=tuple(sorted(set(refresh)))
    assessments=tuple(sorted(assessments,key=lambda a:a.memory_id)); explanations=tuple(explanations)
    base=('MEMORY_NOT_PROMOTED_TO_TRUTH','MENTION_NOT_PROMOTED_TO_MEMORY','NO_MEMORY_WRITE','DCSR_RECONSTRUCTION_CREATES_NO_MEMORY')
    if saw_unresolved and (saw_critical and req.policy.critical_hold or req.policy.unresolved_hold):
        esc=Escalation.IMPORTANT_CONFLICT if saw_critical else (Escalation.SOURCE_UNKNOWN if saw_unknown else Escalation.NO_DECISIVE_EVIDENCE)
        return ResolutionResult(Decision.HOLD,NextAction.HOLD_CONFLICT_RECHECK,esc,ResolutionState.UNRESOLVED_CONFLICT,('UNRESOLVED_CONFLICT_HELD','NO_ARBITRARY_MEMORY_SELECTION')+base,selected,unresolved,refresh,assessments,explanations,False)
    if saw_unresolved:
        esc=Escalation.SOURCE_UNKNOWN if saw_unknown else Escalation.NO_DECISIVE_EVIDENCE
        return ResolutionResult(Decision.ALLOW,NextAction.REFRESH_REQUEST_CANDIDATE,esc,ResolutionState.REFRESH_NEEDED,('REFRESH_REQUEST_CANDIDATE','UNRESOLVED_NOT_PROMOTED_TO_TRUTH')+base,selected,unresolved,refresh,assessments,explanations,True)
    if saw_parallel:
        return ResolutionResult(Decision.ALLOW,NextAction.PARALLEL_MEMORY_CANDIDATE,Escalation.CONTEXT_PARALLEL,ResolutionState.CONTEXT_PARALLEL,('CONTEXT_PARALLEL_PRESERVED','NO_CONFLICT_COLLAPSE')+base,selected,(),refresh,assessments,explanations,True)
    return ResolutionResult(Decision.ALLOW,NextAction.SELECTED_MEMORY_CANDIDATE,Escalation.SOURCE_UNKNOWN if saw_unknown else Escalation.NONE,ResolutionState.SELECTED_CANDIDATE,('SELECTED_MEMORY_CANDIDATE','SELECTION_IS_CONTEXTUAL_REFERENCE_ONLY')+base,selected,(),refresh,assessments,explanations,True)

def default_evaluation(): return evaluate(default_request())

def _fps(req,res):
    return (_fp((req.request_id,req.target_context,req.now,req.binding,req.state_epoch)),_fp(req.memories),_fp(req.policy),_fp(res))
def prepare_state(req,binding,state_epoch):
    if binding!=req.binding or state_epoch!=req.state_epoch: raise ValueError('PREPARED_BINDING_MISMATCH')
    res=evaluate(req); c,m,p,o=_fps(req,res); integ=_fp((c,m,p,o,binding,state_epoch))
    return PreparedResolutionState(req,res,c,m,p,o,integ,binding,state_epoch)
def validate_prepared_integrity(st): return st.integrity_fingerprint==_fp((st.context_fingerprint,st.memory_fingerprint,st.policy_fingerprint,st.outcome_fingerprint,st.binding,st.state_epoch))
def evaluate_prepared(st,*,integrity_validated,current_context_fingerprint,current_memory_fingerprint,current_policy_fingerprint,current_outcome_fingerprint):
    if not integrity_validated or not validate_prepared_integrity(st): return _invalid('PREPARED_INTEGRITY_NOT_VALIDATED')
    if (current_context_fingerprint,current_memory_fingerprint,current_policy_fingerprint,current_outcome_fingerprint)!=(st.context_fingerprint,st.memory_fingerprint,st.policy_fingerprint,st.outcome_fingerprint): return _invalid('PREPARED_FINGERPRINT_MISMATCH')
    return st.result

def make_delta(old,new):
    a={x.memory_id:x for x in old.request.memories}; b={x.memory_id:x for x in new.request.memories}
    changed=tuple(b[k] for k in sorted(b) if k not in a or a[k]!=b[k]); removed=tuple(sorted(set(a)-set(b)))
    return ResolutionDelta(changed,removed,old.request.target_context!=new.request.target_context,old.request.now!=new.request.now,old.policy_fingerprint!=new.policy_fingerprint,_manifest_fp(old.request),_manifest_fp(new.request))
def plan_missing_only(old,new):
    d=make_delta(old,new); ids=[f'MEMORY:{x.memory_id}' for x in d.changed_memories]+[f'MEMORY:{x}' for x in d.removed_memory_ids]
    if d.context_changed: ids.append('TARGET_CONTEXT')
    if d.now_changed: ids.append('NOW')
    if d.policy_changed: ids.append('RESOLUTION_POLICY')
    meta=len(_canon((tuple(ids),d.from_manifest_fingerprint,d.to_manifest_fingerprint)))
    return MissingOnlyPlan(tuple(ids),meta,False)
