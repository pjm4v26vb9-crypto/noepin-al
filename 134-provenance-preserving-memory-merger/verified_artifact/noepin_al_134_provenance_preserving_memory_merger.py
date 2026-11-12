"""NOEPIN AL 134 — Provenance-Preserving Memory Merger — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-134
DCSR: LIMITED INTEGRATION / 限定適用.

Composite memory, source links and confidence are audit/reference candidates only.
Memory != Truth. Mention != Memory. Confidence != Fact Proof. Source Link != Source Authority.
No merge candidate performs a memory write, permission grant, approval, authority change or action execution.
DCSR reconstruction does not create a new memory or known fact.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str,Enum): ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class MergeState(str,Enum): COMPOSITE_CANDIDATE='COMPOSITE_CANDIDATE'; CONFLICT_PRESERVED='CONFLICT_PRESERVED'; PROVENANCE_INCOMPLETE='PROVENANCE_INCOMPLETE'; MENTION_ONLY='MENTION_ONLY'; EMPTY='EMPTY'; INVALID='INVALID'
class NextAction(str,Enum): COMPOSITE_MEMORY_CANDIDATE='COMPOSITE_MEMORY_CANDIDATE'; HOLD_PROVENANCE_RECHECK='HOLD_PROVENANCE_RECHECK'; HOLD_CONFLICT_REVIEW='HOLD_CONFLICT_REVIEW'; NO_MEMORY_CANDIDATE='NO_MEMORY_CANDIDATE'
class Escalation(str,Enum): NONE='NONE'; PROVENANCE_MISSING='PROVENANCE_MISSING'; CRITICAL_PRIMARY_SOURCE_MISSING='CRITICAL_PRIMARY_SOURCE_MISSING'; CRITICAL_CONFLICT='CRITICAL_CONFLICT'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'
class RecordKind(str,Enum): MEMORY='MEMORY'; MENTION='MENTION'
class SourceKind(str,Enum): PRIMARY='PRIMARY'; SECONDARY='SECONDARY'; DERIVED='DERIVED'

@dataclass(frozen=True)
class ProvenanceLink:
    source_id:str; parent_source_id:str|None; transform_id:str|None; source_kind:SourceKind; binding:str; state_epoch:str

@dataclass(frozen=True)
class MemoryClaim:
    memory_id:str; claim_id:str; semantic_key:str; value:str; source_id:str; confidence:float; critical:bool
    kind:RecordKind; purpose_id:str; timestamp:int|None; binding:str; state_epoch:str

@dataclass(frozen=True)
class MergePolicy:
    provenance_confidence_cap:float=.50
    min_confidence:float=.0
    critical_require_primary:bool=True
    critical_conflict_hold:bool=True

@dataclass(frozen=True)
class MergeRequest:
    request_id:str; claims:tuple[MemoryClaim,...]; provenance:tuple[ProvenanceLink,...]; policy:MergePolicy; binding:str; state_epoch:str

@dataclass(frozen=True)
class CompositeClaim:
    semantic_key:str; value:str; claim_ids:tuple[str,...]; memory_ids:tuple[str,...]; source_links:tuple[str,...]
    provenance_paths:tuple[tuple[str,...],...]; transform_paths:tuple[tuple[str,...],...]; confidence:float
    conflict:bool; critical:bool; provenance_complete:bool; primary_source_preserved:bool; reasons:tuple[str,...]

@dataclass(frozen=True)
class MergeResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; merge_state:MergeState; reasons:tuple[str,...]
    composites:tuple[CompositeClaim,...]; conflict_keys:tuple[str,...]; next_gate_candidate:bool
    memory_promoted_to_truth:bool=False; mention_promoted_to_memory:bool=False; confidence_promoted_to_fact_proof:bool=False
    source_link_promoted_to_source_authority:bool=False; composite_written_to_memory:bool=False; provenance_rewritten:bool=False
    dcsr_reconstruction_created_memory:bool=False; sender_authority_inherited:bool=False; sender_intent_inherited:bool=False
    sender_agreement_inherited:bool=False; permission_granted:bool=False; approval_executed:bool=False
    authority_granted:bool=False; stop_executed:bool=False; action_executed:bool=False; plan_committed:bool=False
    publish_executed:bool=False; external_write_performed:bool=False; world_truth_proven:bool=False
    domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False

@dataclass(frozen=True)
class PreparedMergeState:
    request:MergeRequest; result:MergeResult; context_fingerprint:str; claim_fingerprint:str; provenance_fingerprint:str
    policy_fingerprint:str; outcome_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str

@dataclass(frozen=True)
class MergeDelta:
    changed_claims:tuple[MemoryClaim,...]; removed_claim_ids:tuple[str,...]; changed_provenance:tuple[ProvenanceLink,...]
    removed_source_ids:tuple[str,...]; policy_changed:bool; from_manifest_fingerprint:str; to_manifest_fingerprint:str

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
def _manifest_fp(req): return _fp((req.claims,req.provenance,req.policy,req.binding,req.state_epoch))

def default_policy(): return MergePolicy()
def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    prov=(
      ProvenanceLink('SRC-PRIMARY',None,None,SourceKind.PRIMARY,b,e),
      ProvenanceLink('SRC-SUMMARY','SRC-PRIMARY','SUMMARIZE-V1',SourceKind.DERIVED,b,e),
      ProvenanceLink('SRC-SECONDARY',None,None,SourceKind.SECONDARY,b,e),
    )
    claims=(
      MemoryClaim('MEM-1','CLM-1','entity.color','blue','SRC-PRIMARY',.92,False,RecordKind.MEMORY,'P-1',100,b,e),
      MemoryClaim('MEM-2','CLM-2','entity.color','blue','SRC-SUMMARY',.88,False,RecordKind.MEMORY,'P-1',110,b,e),
      MemoryClaim('MENTION-1','CLM-M','entity.color','blue','SRC-SECONDARY',.99,False,RecordKind.MENTION,'P-CHAT',120,b,e),
    )
    return MergeRequest('DEFAULT-134',claims,prov,default_policy(),b,e)

def _invalid(reason):
    return MergeResult(Decision.HOLD,NextAction.HOLD_PROVENANCE_RECHECK,Escalation.INVALID_CONFIGURATION,MergeState.INVALID,(reason,'NO_MEMORY_WRITE','MEMORY_NOT_PROMOTED_TO_TRUTH'),(),(),False)

def _validate(req):
    if not req.request_id or not req.binding or not req.state_epoch: return 'INVALID_REQUEST_IDENTITY'
    p=req.policy
    if not _finite(p.provenance_confidence_cap) or not _finite(p.min_confidence): return 'NONFINITE_POLICY'
    if not (0<=p.provenance_confidence_cap<=1 and 0<=p.min_confidence<=1): return 'INVALID_POLICY_RANGE'
    cids=set(); mids=set()
    for c in req.claims:
        if not c.memory_id or not c.claim_id or not c.semantic_key or not c.value or not c.source_id or not c.purpose_id: return 'INVALID_CLAIM_IDENTITY'
        if c.claim_id in cids: return 'DUPLICATE_CLAIM_ID'
        if c.memory_id in mids and c.kind==RecordKind.MEMORY: return 'DUPLICATE_MEMORY_ID'
        cids.add(c.claim_id); mids.add(c.memory_id)
        if c.binding!=req.binding or c.state_epoch!=req.state_epoch: return 'CLAIM_BINDING_MISMATCH'
        if not isinstance(c.kind,RecordKind): return 'INVALID_RECORD_KIND'
        if c.timestamp is not None and (not isinstance(c.timestamp,int) or isinstance(c.timestamp,bool)): return 'INVALID_TIMESTAMP'
        if not _finite(c.confidence) or not 0<=c.confidence<=1: return 'INVALID_CONFIDENCE'
    sids=set()
    for x in req.provenance:
        if not x.source_id: return 'INVALID_SOURCE_ID'
        if x.source_id in sids: return 'DUPLICATE_SOURCE_ID'
        sids.add(x.source_id)
        if x.binding!=req.binding or x.state_epoch!=req.state_epoch: return 'PROVENANCE_BINDING_MISMATCH'
        if not isinstance(x.source_kind,SourceKind): return 'INVALID_SOURCE_KIND'
        if x.parent_source_id==x.source_id: return 'SELF_PROVENANCE_CYCLE'
    return None

def _trace(source_id, pmap):
    path=[]; transforms=[]; seen=set(); cur=source_id; complete=True; primary=False
    while cur:
        if cur in seen: return tuple(path),tuple(transforms),False,False
        seen.add(cur); path.append(cur)
        node=pmap.get(cur)
        if node is None:
            complete=False; break
        if node.source_kind==SourceKind.PRIMARY: primary=True
        if node.transform_id: transforms.append(node.transform_id)
        cur=node.parent_source_id
    return tuple(path),tuple(transforms),complete,primary

def evaluate(req:MergeRequest)->MergeResult:
    bad=_validate(req)
    if bad: return _invalid(bad)
    memory_claims=[c for c in req.claims if c.kind==RecordKind.MEMORY]
    if not memory_claims:
        return MergeResult(Decision.ALLOW,NextAction.NO_MEMORY_CANDIDATE,Escalation.NONE,MergeState.MENTION_ONLY,('MENTION_IS_NOT_MEMORY','NO_COMPOSITE_MEMORY_CREATED','NO_MEMORY_WRITE'),(),(),True)
    pmap={p.source_id:p for p in req.provenance}
    groups={}
    for c in memory_claims: groups.setdefault(c.semantic_key,[]).append(c)
    composites=[]; conflict_keys=[]; critical_prov_failure=False; any_missing=False; critical_conflict=False
    for key in sorted(groups):
        cs=groups[key]
        values=sorted({c.value for c in cs})
        conflict=len(values)>1
        if conflict: conflict_keys.append(key)
        if conflict and any(c.critical for c in cs): critical_conflict=True
        for value in values:
            same=[c for c in cs if c.value==value]
            # deterministic de-dup: same semantic value and same source contribute once; earliest claim id retained.
            by_source={}
            for c in sorted(same,key=lambda x:(x.source_id,x.claim_id)):
                by_source.setdefault(c.source_id,c)
            dedup=list(by_source.values())
            paths=[]; tpaths=[]; links=[]; complete=True; primary=False
            for c in dedup:
                path,tpath,ok,has_primary=_trace(c.source_id,pmap)
                paths.append(path); tpaths.append(tpath); links.extend(path)
                complete=complete and ok; primary=primary or has_primary
            critical=any(c.critical for c in same)
            if not complete: any_missing=True
            if critical and req.policy.critical_require_primary and (not complete or not primary): critical_prov_failure=True
            base=max(c.confidence for c in same)
            conf=max(req.policy.min_confidence,base)
            reasons=['CLAIM_CLUSTERED_BY_EXPLICIT_SEMANTIC_KEY','SOURCE_LINKS_PRESERVED','TRANSFORM_HISTORY_PRESERVED','COMPOSITE_IS_CANDIDATE_ONLY']
            if len(same)>len(dedup): reasons.append('SAME_VALUE_SAME_SOURCE_DEDUP')
            if conflict: reasons+=['CONFLICT_PRESERVED_NOT_COLLAPSED','ALTERNATIVE_VALUE_RETAINED']
            if not complete:
                conf=min(conf,req.policy.provenance_confidence_cap); reasons+=['PROVENANCE_INCOMPLETE','CONFIDENCE_CAPPED']
            if critical:
                reasons.append('CRITICAL_CLAIM')
                if primary: reasons.append('PRIMARY_SOURCE_PRESERVED')
                else: reasons.append('PRIMARY_SOURCE_NOT_VERIFIED')
            reasons+=['MEMORY_NOT_PROMOTED_TO_TRUTH','NO_MEMORY_WRITE']
            composites.append(CompositeClaim(key,value,tuple(sorted(c.claim_id for c in same)),tuple(sorted(c.memory_id for c in same)),tuple(sorted(set(links))),tuple(paths),tuple(tpaths),round(conf,12),conflict,critical,complete,primary,tuple(reasons)))
    composites=tuple(sorted(composites,key=lambda x:(x.semantic_key,x.value)))
    if critical_prov_failure:
        return MergeResult(Decision.HOLD,NextAction.HOLD_PROVENANCE_RECHECK,Escalation.CRITICAL_PRIMARY_SOURCE_MISSING,MergeState.PROVENANCE_INCOMPLETE,('CRITICAL_CLAIM_PRIMARY_SOURCE_NOT_PRESERVED','DO_NOT_STORE_AS_CRITICAL_COMPOSITE','REACQUIRE_PROVENANCE','NO_MEMORY_WRITE'),composites,tuple(conflict_keys),False)
    if critical_conflict and req.policy.critical_conflict_hold:
        return MergeResult(Decision.HOLD,NextAction.HOLD_CONFLICT_REVIEW,Escalation.CRITICAL_CONFLICT,MergeState.CONFLICT_PRESERVED,('CRITICAL_CONFLICT_PRESERVED','NO_CONFLICT_COLLAPSE','HUMAN_OR_RECHECK_REQUIRED','NO_MEMORY_WRITE'),composites,tuple(conflict_keys),False)
    esc=Escalation.PROVENANCE_MISSING if any_missing else Escalation.NONE
    state=MergeState.CONFLICT_PRESERVED if conflict_keys else (MergeState.PROVENANCE_INCOMPLETE if any_missing else MergeState.COMPOSITE_CANDIDATE)
    reasons=['COMPOSITE_MEMORY_CANDIDATE','PROVENANCE_MAP_PRESERVED','NO_MEMORY_WRITE','MEMORY_NOT_PROMOTED_TO_TRUTH']
    if conflict_keys: reasons+=['CONFLICTS_PRESERVED_AS_PARALLEL_VALUES']
    if any_missing: reasons+=['NONCRITICAL_PROVENANCE_INCOMPLETE_CONFIDENCE_CAPPED']
    return MergeResult(Decision.ALLOW,NextAction.COMPOSITE_MEMORY_CANDIDATE,esc,state,tuple(reasons),composites,tuple(conflict_keys),True)

def default_evaluation(): return evaluate(default_request())

def _fps(req,res):
    return (_fp((req.request_id,req.binding,req.state_epoch)),_fp(req.claims),_fp(req.provenance),_fp(req.policy),_fp(res))
def prepare_state(req,binding,state_epoch):
    if binding!=req.binding or state_epoch!=req.state_epoch: raise ValueError('PREPARED_BINDING_MISMATCH')
    res=evaluate(req); c,cl,pr,po,o=_fps(req,res); integ=_fp((c,cl,pr,po,o,binding,state_epoch))
    return PreparedMergeState(req,res,c,cl,pr,po,o,integ,binding,state_epoch)
def validate_prepared_integrity(st): return st.integrity_fingerprint==_fp((st.context_fingerprint,st.claim_fingerprint,st.provenance_fingerprint,st.policy_fingerprint,st.outcome_fingerprint,st.binding,st.state_epoch))
def evaluate_prepared(st,*,integrity_validated,current_context_fingerprint,current_claim_fingerprint,current_provenance_fingerprint,current_policy_fingerprint,current_outcome_fingerprint):
    if not integrity_validated or not validate_prepared_integrity(st): return _invalid('PREPARED_INTEGRITY_NOT_VALIDATED')
    if (current_context_fingerprint,current_claim_fingerprint,current_provenance_fingerprint,current_policy_fingerprint,current_outcome_fingerprint)!=(st.context_fingerprint,st.claim_fingerprint,st.provenance_fingerprint,st.policy_fingerprint,st.outcome_fingerprint): return _invalid('PREPARED_FINGERPRINT_MISMATCH')
    return st.result

def make_delta(old,new):
    a={c.claim_id:c for c in old.request.claims}; b={c.claim_id:c for c in new.request.claims}
    changed_claims=tuple(b[k] for k in sorted(b) if k not in a or a[k]!=b[k]); removed_claims=tuple(sorted(set(a)-set(b)))
    pa={p.source_id:p for p in old.request.provenance}; pb={p.source_id:p for p in new.request.provenance}
    changed_prov=tuple(pb[k] for k in sorted(pb) if k not in pa or pa[k]!=pb[k]); removed_sources=tuple(sorted(set(pa)-set(pb)))
    return MergeDelta(changed_claims,removed_claims,changed_prov,removed_sources,old.policy_fingerprint!=new.policy_fingerprint,_manifest_fp(old.request),_manifest_fp(new.request))
def plan_missing_only(old,new):
    d=make_delta(old,new); ids=[f'CLAIM:{c.claim_id}' for c in d.changed_claims]+[f'CLAIM:{x}' for x in d.removed_claim_ids]+[f'SOURCE:{p.source_id}' for p in d.changed_provenance]+[f'SOURCE:{x}' for x in d.removed_source_ids]
    if d.policy_changed: ids.append('MERGE_POLICY')
    meta=len(_canon((tuple(ids),d.from_manifest_fingerprint,d.to_manifest_fingerprint)))
    return MissingOnlyPlan(tuple(ids),meta,False)
