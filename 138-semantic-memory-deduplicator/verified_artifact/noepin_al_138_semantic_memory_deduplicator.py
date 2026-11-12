"""NOEPIN AL 138 — Semantic Memory Deduplicator — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-138
DCSR: LIMITED INTEGRATION / 限定適用.

The output is a deduplication / canonicalization candidate, never a destructive Memory mutation.
Memory != Truth. Mention != Memory. Semantic Similarity != Fact Identity.
Canonical Memory Candidate != Memory Write. Merge Link Candidate != Destructive Merge.
Critical differences, different explicit Time/Scope, and importance-unknown approximate differences are not auto-merged.
All provenance and source Memory IDs remain traceable. DCSR reconstruction does not create a new Memory or known Fact.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str,Enum): ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class DedupState(str,Enum):
    DEDUPLICATION_CANDIDATE='DEDUPLICATION_CANDIDATE'; PRESERVED_SEPARATE='PRESERVED_SEPARATE'
    APPROXIMATE_HOLD='APPROXIMATE_HOLD'; MENTION_ONLY='MENTION_ONLY'; EMPTY='EMPTY'; INVALID='INVALID'
class NextAction(str,Enum):
    CANONICAL_MEMORY_CANDIDATE='CANONICAL_MEMORY_CANDIDATE'; PRESERVE_DIFFERENCES_CANDIDATE='PRESERVE_DIFFERENCES_CANDIDATE'
    SEMANTIC_REVIEW_CANDIDATE='SEMANTIC_REVIEW_CANDIDATE'; NO_MEMORY_CANDIDATE='NO_MEMORY_CANDIDATE'
class Escalation(str,Enum): NONE='NONE'; DIFFERENCE_IMPORTANCE_UNKNOWN='DIFFERENCE_IMPORTANCE_UNKNOWN'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'
class RecordKind(str,Enum): MEMORY='MEMORY'; MENTION='MENTION'

@dataclass(frozen=True)
class MemoryClaim:
    memory_id:str; semantic_key:str; claim_text:str; scope:str|None; time_key:str|None
    qualifiers:tuple[str,...]; critical_attributes:tuple[tuple[str,str],...]; semantic_equivalence_score:float
    provenance_ids:tuple[str,...]; trust:float; kind:RecordKind; difference_importance_known:bool
    binding:str; state_epoch:str

@dataclass(frozen=True)
class DedupPolicy:
    min_merge_equivalence:float=.94
    approximate_floor:float=.78
    min_trust:float=.50
    require_same_scope:bool=True
    require_same_time:bool=True
    preserve_all_provenance:bool=True
    hold_when_difference_importance_unknown:bool=True

@dataclass(frozen=True)
class DedupRequest:
    request_id:str; memories:tuple[MemoryClaim,...]; policy:DedupPolicy; binding:str; state_epoch:str

@dataclass(frozen=True)
class CanonicalMemoryCandidate:
    canonical_memory_id:str; semantic_key:str; representative_claim:str; source_memory_ids:tuple[str,...]
    provenance_ids:tuple[str,...]; scope:str|None; time_key:str|None; qualifiers:tuple[str,...]
    critical_attributes:tuple[tuple[str,str],...]

@dataclass(frozen=True)
class MergedLinkCandidate:
    canonical_memory_id:str; merged_memory_id:str; preserved_provenance_ids:tuple[str,...]

@dataclass(frozen=True)
class PreservedDifference:
    memory_ids:tuple[str,...]; reason:str

@dataclass(frozen=True)
class DedupResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; dedup_state:DedupState; reasons:tuple[str,...]
    canonical_memories:tuple[CanonicalMemoryCandidate,...]; merged_links:tuple[MergedLinkCandidate,...]
    preserved_differences:tuple[PreservedDifference,...]; next_gate_candidate:bool
    memory_promoted_to_truth:bool=False; mention_promoted_to_memory:bool=False; semantic_similarity_promoted_to_fact_identity:bool=False
    canonical_memory_written:bool=False; destructive_merge_executed:bool=False; provenance_dropped:bool=False
    difference_suppressed:bool=False; dcsr_reconstruction_created_memory:bool=False; sender_authority_inherited:bool=False
    sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False; permission_granted:bool=False
    approval_executed:bool=False; authority_granted:bool=False; stop_executed:bool=False; action_executed:bool=False
    plan_committed:bool=False; publish_executed:bool=False; external_write_performed:bool=False; world_truth_proven:bool=False
    domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False

@dataclass(frozen=True)
class PreparedDedupState:
    request:DedupRequest; result:DedupResult; context_fingerprint:str; memory_fingerprint:str
    policy_fingerprint:str; outcome_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str

@dataclass(frozen=True)
class DedupDelta:
    changed_memories:tuple[MemoryClaim,...]; removed_memory_ids:tuple[str,...]; policy_changed:bool
    from_manifest_fingerprint:str; to_manifest_fingerprint:str

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
def _manifest_fp(req): return _fp((req.memories,req.policy,req.binding,req.state_epoch))

def default_policy(): return DedupPolicy()
def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    xs=(
        MemoryClaim('MEM-1','RUFA-HOME-LOCATION','Rufa lives in the forest house.','PROJECT-A','T1',('CURRENT',),(('entity','RUFA'),('relation','HOME')), .99,('SRC-1','TRACE-1'),.94,RecordKind.MEMORY,True,b,e),
        MemoryClaim('MEM-2','RUFA-HOME-LOCATION','The forest house is Rufa\'s home.','PROJECT-A','T1',('CURRENT',),(('entity','RUFA'),('relation','HOME')), .98,('SRC-2','TRACE-2'),.91,RecordKind.MEMORY,True,b,e),
    )
    return DedupRequest('REQ-138',xs,default_policy(),b,e)

def _invalid(reason):
    return DedupResult(Decision.HOLD,NextAction.SEMANTIC_REVIEW_CANDIDATE,Escalation.INVALID_CONFIGURATION,DedupState.INVALID,(reason,'NO_DESTRUCTIVE_MERGE','NO_MEMORY_WRITE'),(),(),(),False)

def _validate(req):
    p=req.policy
    nums=(p.min_merge_equivalence,p.approximate_floor,p.min_trust)
    if not all(_finite(x) for x in nums): return 'NONFINITE_POLICY'
    if not all(0<=x<=1 for x in nums): return 'POLICY_RANGE'
    if p.approximate_floor>p.min_merge_equivalence: return 'APPROXIMATE_FLOOR_ABOVE_MERGE_THRESHOLD'
    ids=set()
    for x in req.memories:
        if x.memory_id in ids: return 'DUPLICATE_MEMORY_ID'
        ids.add(x.memory_id)
        if x.binding!=req.binding or x.state_epoch!=req.state_epoch: return 'STATE_BINDING_MISMATCH'
        if not x.memory_id or not x.semantic_key: return 'EMPTY_MEMORY_KEY'
        if not _finite(x.semantic_equivalence_score) or not 0<=x.semantic_equivalence_score<=1: return 'SEMANTIC_SCORE_RANGE_OR_NONFINITE'
        if not _finite(x.trust) or not 0<=x.trust<=1: return 'TRUST_RANGE_OR_NONFINITE'
        if len(set(x.provenance_ids))!=len(x.provenance_ids): return 'DUPLICATE_PROVENANCE_ID'
    return None

def _structural_same(a,b,p):
    if p.require_same_scope and a.scope!=b.scope: return False,'SCOPE_DIFFERENCE'
    if p.require_same_time and a.time_key!=b.time_key: return False,'TIME_DIFFERENCE'
    if a.critical_attributes!=b.critical_attributes: return False,'CRITICAL_DIFFERENCE'
    if a.qualifiers!=b.qualifiers: return False,'QUALIFIER_DIFFERENCE'
    return True,''

def _canonical_from_group(group):
    # representative selection is deterministic evidence ranking only, not Truth selection.
    ordered=sorted(group,key=lambda x:(-x.trust,-x.semantic_equivalence_score,x.memory_id))
    rep=ordered[0]
    provenance=tuple(sorted({p for x in group for p in x.provenance_ids}))
    return CanonicalMemoryCandidate(rep.memory_id,rep.semantic_key,rep.claim_text,tuple(sorted(x.memory_id for x in group)),provenance,rep.scope,rep.time_key,rep.qualifiers,rep.critical_attributes)

def evaluate(req):
    err=_validate(req)
    if err: return _invalid(err)
    memories=tuple(sorted((x for x in req.memories if x.kind==RecordKind.MEMORY),key=lambda x:x.memory_id))
    mentions=tuple(x for x in req.memories if x.kind==RecordKind.MENTION)
    if not memories:
        state=DedupState.MENTION_ONLY if mentions else DedupState.EMPTY
        return DedupResult(Decision.ALLOW,NextAction.NO_MEMORY_CANDIDATE,Escalation.NONE,state,('NO_MEMORY_RECORDS','MENTION_NOT_PROMOTED_TO_MEMORY','NO_MEMORY_WRITE'),(),(),(),True)
    p=req.policy; canonical=[]; links=[]; diffs=[]; unresolved=[]
    by_sem={}
    for x in memories: by_sem.setdefault(x.semantic_key,[]).append(x)
    for sem in sorted(by_sem):
        group=sorted(by_sem[sem],key=lambda x:x.memory_id)
        consumed=set()
        for i,a in enumerate(group):
            if a.memory_id in consumed: continue
            cluster=[a]; consumed.add(a.memory_id)
            for b in group[i+1:]:
                if b.memory_id in consumed: continue
                same,reason=_structural_same(a,b,p)
                if not same:
                    diffs.append(PreservedDifference(tuple(sorted((a.memory_id,b.memory_id))),reason)); continue
                minscore=min(a.semantic_equivalence_score,b.semantic_equivalence_score)
                if minscore>=p.min_merge_equivalence and a.trust>=p.min_trust and b.trust>=p.min_trust:
                    cluster.append(b); consumed.add(b.memory_id)
                elif minscore>=p.approximate_floor:
                    if p.hold_when_difference_importance_unknown and (not a.difference_importance_known or not b.difference_importance_known):
                        unresolved.append(tuple(sorted((a.memory_id,b.memory_id))))
                    else:
                        diffs.append(PreservedDifference(tuple(sorted((a.memory_id,b.memory_id))),'APPROXIMATE_NOT_SAFE_EQUIVALENT'))
                else:
                    diffs.append(PreservedDifference(tuple(sorted((a.memory_id,b.memory_id))),'SEMANTIC_DISTANCE'))
            c=_canonical_from_group(cluster); canonical.append(c)
            for x in sorted(cluster,key=lambda z:z.memory_id):
                if x.memory_id!=c.canonical_memory_id:
                    links.append(MergedLinkCandidate(c.canonical_memory_id,x.memory_id,tuple(sorted(x.provenance_ids))))
    # de-duplicate preserved-difference audit records deterministically.
    uniq={ (d.memory_ids,d.reason):d for d in diffs }
    diffs=tuple(uniq[k] for k in sorted(uniq))
    canonical=tuple(sorted(canonical,key=lambda c:c.canonical_memory_id)); links=tuple(sorted(links,key=lambda x:(x.canonical_memory_id,x.merged_memory_id)))
    if unresolved:
        ud=tuple(PreservedDifference(pair,'DIFFERENCE_IMPORTANCE_UNKNOWN') for pair in sorted(set(unresolved)))
        all_diffs=tuple(sorted(diffs+ud,key=lambda d:(d.memory_ids,d.reason)))
        return DedupResult(Decision.HOLD,NextAction.SEMANTIC_REVIEW_CANDIDATE,Escalation.DIFFERENCE_IMPORTANCE_UNKNOWN,DedupState.APPROXIMATE_HOLD,('APPROXIMATE_MEMORY_DIFFERENCE_IMPORTANCE_UNKNOWN','AUTO_MERGE_BLOCKED','PROVENANCE_PRESERVED','NO_MEMORY_WRITE'),canonical,links,all_diffs,False)
    if links:
        return DedupResult(Decision.ALLOW,NextAction.CANONICAL_MEMORY_CANDIDATE,Escalation.NONE,DedupState.DEDUPLICATION_CANDIDATE,('SAFE_EQUIVALENCE_CANDIDATES_ONLY','ALL_SOURCE_MEMORY_IDS_TRACEABLE','ALL_PROVENANCE_PRESERVED','NO_DESTRUCTIVE_MERGE','NO_MEMORY_WRITE'),canonical,links,diffs,True)
    return DedupResult(Decision.ALLOW,NextAction.PRESERVE_DIFFERENCES_CANDIDATE,Escalation.NONE,DedupState.PRESERVED_SEPARATE,('NO_SAFE_DUPLICATE_MERGE','DIFFERENCES_PRESERVED','NO_DESTRUCTIVE_MERGE','NO_MEMORY_WRITE'),canonical,(),diffs,True)

def default_evaluation(): return evaluate(default_request())

def _fps(req,res): return (_fp((req.request_id,req.binding,req.state_epoch)),_fp(req.memories),_fp(req.policy),_fp(res))
def prepare_state(req,binding,state_epoch):
    if binding!=req.binding or state_epoch!=req.state_epoch: raise ValueError('PREPARED_BINDING_MISMATCH')
    res=evaluate(req); c,m,p,o=_fps(req,res); integ=_fp((c,m,p,o,binding,state_epoch))
    return PreparedDedupState(req,res,c,m,p,o,integ,binding,state_epoch)
def validate_prepared_integrity(st): return st.integrity_fingerprint==_fp((st.context_fingerprint,st.memory_fingerprint,st.policy_fingerprint,st.outcome_fingerprint,st.binding,st.state_epoch))
def evaluate_prepared(st,*,integrity_validated,current_context_fingerprint,current_memory_fingerprint,current_policy_fingerprint,current_outcome_fingerprint):
    if not integrity_validated or not validate_prepared_integrity(st): return _invalid('PREPARED_INTEGRITY_NOT_VALIDATED')
    if (current_context_fingerprint,current_memory_fingerprint,current_policy_fingerprint,current_outcome_fingerprint)!=(st.context_fingerprint,st.memory_fingerprint,st.policy_fingerprint,st.outcome_fingerprint): return _invalid('PREPARED_FINGERPRINT_MISMATCH')
    return st.result

def make_delta(old,new):
    a={x.memory_id:x for x in old.request.memories}; b={x.memory_id:x for x in new.request.memories}
    changed=tuple(b[k] for k in sorted(b) if k not in a or a[k]!=b[k]); removed=tuple(sorted(set(a)-set(b)))
    return DedupDelta(changed,removed,old.policy_fingerprint!=new.policy_fingerprint,_manifest_fp(old.request),_manifest_fp(new.request))
def plan_missing_only(old,new):
    d=make_delta(old,new); ids=[f'MEMORY:{x.memory_id}' for x in d.changed_memories]+[f'MEMORY:{x}' for x in d.removed_memory_ids]
    if d.policy_changed: ids.append('DEDUP_POLICY')
    meta=len(_canon((tuple(ids),d.from_manifest_fingerprint,d.to_manifest_fingerprint)))
    return MissingOnlyPlan(tuple(ids),meta,False)
