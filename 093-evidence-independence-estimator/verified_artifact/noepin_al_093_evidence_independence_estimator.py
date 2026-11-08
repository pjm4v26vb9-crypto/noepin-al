"""NOEPIN AL 093 — Evidence Independence Estimator — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Pure uncertainty / provenance control algorithm. It estimates whether multiple
Evidence records are genuinely independent from provenance, model, URL/document,
content fingerprint, and citation lineage. Unknown lineage is conservatively not
promoted to full independence. It never promotes independence scores or caches to
Truth/Authority, grants permission, executes actions, writes externally, commits
state, proves safety, or proves action success.

Canonical identity: NOEPIN-AL-093
DCSR level: LIMITED INTEGRATION / 限定適用.
Provenance note: exact registered Origin GUID was not freshly reverified in this
completion session and is intentionally not guessed or regenerated.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str,Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class RiskLevel(str,Enum):
    LOW='LOW'; MEDIUM='MEDIUM'; HIGH='HIGH'; CRITICAL='CRITICAL'
class Relation(str,Enum):
    CITES='CITES'; DERIVED_FROM='DERIVED_FROM'; REGENERATED_FROM='REGENERATED_FROM'; SHARES_SOURCE='SHARES_SOURCE'

@dataclass(frozen=True)
class IndependenceRequest:
    request_id:str; risk:RiskLevel; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id:str; source_id:str; model_id:str; url_id:str; document_id:str
    parent_evidence_ids:tuple[str,...]; lineage_known:bool; observed:bool
    source_version:str; evidence_fingerprint:str; content_fingerprint:str
    binding:str; state_epoch:str
@dataclass(frozen=True)
class LineageEdge:
    parent_id:str; child_id:str; relation:Relation; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class IndependencePolicy:
    same_source_dependence:float; same_model_dependence:float; same_url_dependence:float
    same_document_dependence:float; same_content_dependence:float; citation_dependence:float
    shared_ancestor_dependence:float; unknown_lineage_dependence:float; cluster_threshold:float
    min_effective_low:float; min_effective_medium:float; min_effective_high:float; min_effective_critical:float
    min_mean_independence:float; binding:str; state_epoch:str; revoked:bool=False
@dataclass(frozen=True)
class IndependenceResult:
    decision:Decision; reasons:tuple[str,...]
    independence_matrix:tuple[tuple[str,str,float],...]
    clusters:tuple[tuple[str,...],...]
    effective_evidence_count:float; mean_independence:float; mean_dependence:float
    unknown_lineage_count:int; strong_dependence_pairs:int
    next_gate_candidate:bool; reevaluation_candidate:bool
    permission_granted:bool=False; action_executed:bool=False; plan_committed:bool=False
    atomic_publish_executed:bool=False; external_write_performed:bool=False
    world_truth_proven:bool=False; authority_promoted:bool=False; safety_proven:bool=False
    action_success:bool=False
@dataclass(frozen=True)
class PreparedIndependenceState:
    request:IndependenceRequest; evidence:tuple[EvidenceRecord,...]; edges:tuple[LineageEdge,...]
    policy:IndependencePolicy; record_fingerprints:tuple[tuple[str,str],...]
    context_fingerprint:str; dependency_fingerprint:str; calibration_fingerprint:str
    registry_fingerprint:str; precomputed_result:IndependenceResult; binding:str; state_epoch:str
@dataclass(frozen=True)
class IndependenceStateDelta:
    base_fingerprint:str; target_fingerprint:str
    changed_evidence:tuple[EvidenceRecord,...]; removed_evidence_ids:tuple[str,...]
    changed_edges:tuple[LineageEdge,...]; removed_edge_ids:tuple[str,...]
    target_request:IndependenceRequest|None; target_policy:IndependencePolicy|None
    binding:str; state_epoch:str
@dataclass(frozen=True)
class IndependenceSyncPlan:
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
def _clamp(v,lo=0.0,hi=1.0): return max(lo,min(hi,v))
def _hold(reason,* ,matrix=(),clusters=(),effective=0.0,mean_ind=0.0,unknown=0,strong=0):
    return IndependenceResult(Decision.HOLD,(reason,),tuple(matrix),tuple(clusters),effective,mean_ind,1.0-mean_ind if matrix else 0.0,unknown,strong,False,True)
def _edge_id(e:LineageEdge)->str: return f'{e.parent_id}>{e.child_id}:{e.relation.value}'

def _validate(req,evidence,edges,policy):
    if policy.revoked: return 'POLICY_REVOKED'
    if not req.observed: return 'REQUEST_UNOBSERVED'
    if req.binding!=policy.binding or req.state_epoch!=policy.state_epoch: return 'REQUEST_SCOPE_MISMATCH'
    vals=(policy.same_source_dependence,policy.same_model_dependence,policy.same_url_dependence,policy.same_document_dependence,policy.same_content_dependence,policy.citation_dependence,policy.shared_ancestor_dependence,policy.unknown_lineage_dependence,policy.cluster_threshold,policy.min_mean_independence)
    if any((not math.isfinite(v) or v<0 or v>1) for v in vals): return 'POLICY_RANGE_INVALID'
    mins=(policy.min_effective_low,policy.min_effective_medium,policy.min_effective_high,policy.min_effective_critical)
    if any((not math.isfinite(v) or v<1) for v in mins): return 'POLICY_EFFECTIVE_THRESHOLD_INVALID'
    if not evidence: return 'EVIDENCE_EMPTY'
    ids=[e.evidence_id for e in evidence]
    if len(ids)!=len(set(ids)): return 'DUPLICATE_EVIDENCE_ID'
    em={e.evidence_id:e for e in evidence}
    for e in evidence:
        if not e.evidence_id or not e.evidence_fingerprint or not e.source_version: return 'EVIDENCE_IDENTITY_INVALID'
        if not e.observed or e.binding!=policy.binding or e.state_epoch!=policy.state_epoch: return 'EVIDENCE_SCOPE_OR_OBSERVATION_INVALID'
        if e.evidence_id in e.parent_evidence_ids: return 'SELF_PARENT_INVALID'
        for p in e.parent_evidence_ids:
            if p not in em: return 'PARENT_EVIDENCE_MISSING'
    edgeids=[]
    for edge in edges:
        eid=_edge_id(edge); edgeids.append(eid)
        if not edge.observed or edge.binding!=policy.binding or edge.state_epoch!=policy.state_epoch: return 'EDGE_SCOPE_OR_OBSERVATION_INVALID'
        if edge.parent_id not in em or edge.child_id not in em or edge.parent_id==edge.child_id: return 'EDGE_ENDPOINT_INVALID'
    if len(edgeids)!=len(set(edgeids)): return 'DUPLICATE_EDGE'
    return None

def _graph(evidence,edges):
    em={e.evidence_id:e for e in evidence}; parents={k:set(v.parent_evidence_ids) for k,v in em.items()}
    for edge in edges: parents[edge.child_id].add(edge.parent_id)
    memo={}
    visiting=set()
    def anc(k):
        if k in memo: return memo[k]
        if k in visiting: return set()
        visiting.add(k); out=set(parents[k])
        for p in list(parents[k]): out |= anc(p)
        visiting.remove(k); memo[k]=out; return out
    for k in em: anc(k)
    return em,parents,memo

def _pair_dependence(a,b,parents,ancestors,policy):
    dep=0.0
    if a.source_id and b.source_id and a.source_id==b.source_id: dep=max(dep,policy.same_source_dependence)
    if a.model_id and b.model_id and a.model_id==b.model_id: dep=max(dep,policy.same_model_dependence)
    if a.url_id and b.url_id and a.url_id==b.url_id: dep=max(dep,policy.same_url_dependence)
    if a.document_id and b.document_id and a.document_id==b.document_id: dep=max(dep,policy.same_document_dependence)
    if a.content_fingerprint and b.content_fingerprint and a.content_fingerprint==b.content_fingerprint: dep=max(dep,policy.same_content_dependence)
    if a.evidence_id in ancestors[b.evidence_id] or b.evidence_id in ancestors[a.evidence_id]: dep=max(dep,policy.citation_dependence)
    common=(ancestors[a.evidence_id] & ancestors[b.evidence_id]) - {a.evidence_id,b.evidence_id}
    if common: dep=max(dep,policy.shared_ancestor_dependence)
    if not a.lineage_known or not b.lineage_known: dep=max(dep,policy.unknown_lineage_dependence)
    return _clamp(dep)

def evaluate(req:IndependenceRequest,evidence:tuple[EvidenceRecord,...],edges:tuple[LineageEdge,...],policy:IndependencePolicy)->IndependenceResult:
    evidence=tuple(sorted(evidence,key=lambda x:x.evidence_id)); edges=tuple(sorted(edges,key=_edge_id))
    err=_validate(req,evidence,edges,policy)
    if err: return _hold(err)
    em,parents,anc=_graph(evidence,edges); ids=tuple(sorted(em))
    matrix=[]; deps=[]; strong=0
    # union-find clusters by strong dependence threshold
    parent={k:k for k in ids}
    def find(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]]; x=parent[x]
        return x
    def union(a,b):
        ra,rb=find(a),find(b)
        if ra!=rb: parent[rb]=ra
    for i,a_id in enumerate(ids):
        a=em[a_id]
        for b_id in ids[i+1:]:
            b=em[b_id]; dep=_pair_dependence(a,b,parents,anc,policy); ind=1.0-dep
            matrix.append((a_id,b_id,round(ind,12))); deps.append(dep)
            if dep>=policy.cluster_threshold: strong+=1; union(a_id,b_id)
    groups={}
    for k in ids: groups.setdefault(find(k),[]).append(k)
    clusters=tuple(sorted((tuple(sorted(v)) for v in groups.values()),key=lambda x:x[0]))
    n=len(ids); mean_dep=(sum(deps)/len(deps)) if deps else 0.0; mean_ind=1.0-mean_dep
    effective=float(n) if n<=1 else n/(1.0+(n-1)*mean_dep)
    effective=max(1.0,min(float(n),effective)); unknown=sum(1 for e in evidence if not e.lineage_known)
    threshold={RiskLevel.LOW:policy.min_effective_low,RiskLevel.MEDIUM:policy.min_effective_medium,RiskLevel.HIGH:policy.min_effective_high,RiskLevel.CRITICAL:policy.min_effective_critical}[req.risk]
    if req.risk in (RiskLevel.HIGH,RiskLevel.CRITICAL) and unknown:
        return _hold('UNKNOWN_LINEAGE_HIGH_RISK',matrix=matrix,clusters=clusters,effective=effective,mean_ind=mean_ind,unknown=unknown,strong=strong)
    if effective < threshold:
        return _hold('EFFECTIVE_EVIDENCE_INSUFFICIENT',matrix=matrix,clusters=clusters,effective=effective,mean_ind=mean_ind,unknown=unknown,strong=strong)
    if mean_ind < policy.min_mean_independence:
        return _hold('MEAN_INDEPENDENCE_TOO_LOW',matrix=matrix,clusters=clusters,effective=effective,mean_ind=mean_ind,unknown=unknown,strong=strong)
    reasons=['INDEPENDENCE_SUFFICIENT']
    if unknown: reasons.append('UNKNOWN_LINEAGE_CONSERVATIVELY_DISCOUNTED')
    return IndependenceResult(Decision.ALLOW,tuple(reasons),tuple(matrix),clusters,effective,mean_ind,mean_dep,unknown,strong,True,False)

def default_request(): return IndependenceRequest('REQ-93',RiskLevel.LOW,True,'EIE-BIND','STATE-EPOCH-1')
def default_policy(): return IndependencePolicy(.95,.60,.90,.90,.98,.82,.72,.50,.60,1.5,2.0,2.5,3.5,.40,'EIE-BIND','STATE-EPOCH-1')
def default_evidence():
    p=default_policy(); return (
      EvidenceRecord('E-A','SRC-A','MODEL-A','URL-A','DOC-A',(),True,True,'V1','E-A-FP','CONTENT-A',p.binding,p.state_epoch),
      EvidenceRecord('E-B','SRC-B','MODEL-B','URL-B','DOC-B',(),True,True,'V1','E-B-FP','CONTENT-B',p.binding,p.state_epoch),
      EvidenceRecord('E-C','SRC-C','MODEL-C','URL-C','DOC-C',(),True,True,'V1','E-C-FP','CONTENT-C',p.binding,p.state_epoch),
      EvidenceRecord('E-D','SRC-D','MODEL-D','URL-D','DOC-D',(),True,True,'V1','E-D-FP','CONTENT-D',p.binding,p.state_epoch),
    )
def default_edges(): return ()
def default_evaluation(): return evaluate(default_request(),default_evidence(),default_edges(),default_policy())

def _canon_sets(evidence,edges): return tuple(sorted(evidence,key=lambda x:x.evidence_id)),tuple(sorted(edges,key=_edge_id))
def _record_fps(evidence,edges):
    rows=[]
    for x in evidence: rows.append((f'EVID:{x.evidence_id}',_fp(x)))
    for x in edges: rows.append((f'EDGE:{_edge_id(x)}',_fp(x)))
    return tuple(sorted(rows))
def prepare_state(req,evidence,edges,policy,*,binding,state_epoch):
    e,g=_canon_sets(evidence,edges); r=evaluate(req,e,g,policy); rec=_record_fps(e,g)
    context=_fp(req); dep=_fp((e,g)); cal=_fp((policy.same_source_dependence,policy.same_model_dependence,policy.same_url_dependence,policy.same_document_dependence,policy.same_content_dependence,policy.citation_dependence,policy.shared_ancestor_dependence,policy.unknown_lineage_dependence,policy.cluster_threshold,policy.min_effective_low,policy.min_effective_medium,policy.min_effective_high,policy.min_effective_critical,policy.min_mean_independence)); reg=_fp(rec)
    return PreparedIndependenceState(req,e,g,policy,rec,context,dep,cal,reg,r,binding,state_epoch)
def validate_prepared_integrity(st):
    if st.binding!=st.policy.binding or st.state_epoch!=st.policy.state_epoch: return False
    e,g=_canon_sets(st.evidence,st.edges); rec=_record_fps(e,g)
    cal=_fp((st.policy.same_source_dependence,st.policy.same_model_dependence,st.policy.same_url_dependence,st.policy.same_document_dependence,st.policy.same_content_dependence,st.policy.citation_dependence,st.policy.shared_ancestor_dependence,st.policy.unknown_lineage_dependence,st.policy.cluster_threshold,st.policy.min_effective_low,st.policy.min_effective_medium,st.policy.min_effective_high,st.policy.min_effective_critical,st.policy.min_mean_independence))
    return rec==st.record_fingerprints and st.context_fingerprint==_fp(st.request) and st.dependency_fingerprint==_fp((e,g)) and st.calibration_fingerprint==cal and st.registry_fingerprint==_fp(rec) and st.precomputed_result==evaluate(st.request,e,g,st.policy)
def evaluate_prepared(st,*,current_context_fingerprint,current_dependency_fingerprint,current_calibration_fingerprint,current_registry_fingerprint,prepared_integrity_validated):
    if not prepared_integrity_validated: return _hold('PREPARED_INTEGRITY_NOT_VALIDATED')
    if current_context_fingerprint!=st.context_fingerprint: return _hold('CONTEXT_FINGERPRINT_MISMATCH')
    if current_dependency_fingerprint!=st.dependency_fingerprint: return _hold('DEPENDENCY_FINGERPRINT_MISMATCH')
    if current_calibration_fingerprint!=st.calibration_fingerprint: return _hold('CALIBRATION_FINGERPRINT_MISMATCH')
    if current_registry_fingerprint!=st.registry_fingerprint: return _hold('REGISTRY_FINGERPRINT_MISMATCH')
    return st.precomputed_result

def _diff(base,target,key):
    bm={key(x):x for x in base}; tm={key(x):x for x in target}
    changed=tuple(tm[k] for k in sorted(tm) if k not in bm or _fp(tm[k])!=_fp(bm[k])); removed=tuple(sorted(k for k in bm if k not in tm)); return changed,removed
def make_delta(base,target):
    ce,re=_diff(base.evidence,target.evidence,lambda x:x.evidence_id); cg,rg=_diff(base.edges,target.edges,_edge_id)
    return IndependenceStateDelta(base.registry_fingerprint,target.registry_fingerprint,ce,re,cg,rg,None if base.request==target.request else target.request,None if base.policy==target.policy else target.policy,target.binding,target.state_epoch)
def apply_delta(base,delta):
    if base.registry_fingerprint!=delta.base_fingerprint: raise ValueError('BASE_FINGERPRINT_MISMATCH')
    em={x.evidence_id:x for x in base.evidence}; gm={_edge_id(x):x for x in base.edges}
    for k in delta.removed_evidence_ids: em.pop(k,None)
    for x in delta.changed_evidence: em[x.evidence_id]=x
    for k in delta.removed_edge_ids: gm.pop(k,None)
    for x in delta.changed_edges: gm[_edge_id(x)]=x
    out=prepare_state(delta.target_request or base.request,tuple(em.values()),tuple(gm.values()),delta.target_policy or base.policy,binding=delta.binding,state_epoch=delta.state_epoch)
    if out.registry_fingerprint!=delta.target_fingerprint: raise ValueError('TARGET_FINGERPRINT_MISMATCH')
    return out
def missing_only_sync_plan(target,known_record_fingerprints:dict[str,str]):
    miss=tuple(sorted(k for k,v in target.record_fingerprints if known_record_fingerprints.get(k)!=v)); metadata=len(_canon(miss)); full=len(miss)>max(1000,int(len(target.record_fingerprints)*0.75)); return IndependenceSyncPlan(miss,metadata,full)
def full_registry_bytes(st): return len(_canon({'request':st.request,'evidence':st.evidence,'edges':st.edges,'policy':st.policy}))
def delta_bytes(delta): return len(_canon(delta))
