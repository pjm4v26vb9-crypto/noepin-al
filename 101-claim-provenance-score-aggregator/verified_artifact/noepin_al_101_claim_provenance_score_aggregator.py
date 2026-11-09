"""NOEPIN AL 101 — Claim Provenance Score Aggregator — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Pure provenance-scoring candidate evidence. The module traces a claim's provenance
DAG backward to source roots, applies source trust and transform-loss penalties,
identifies broken lineage and weakest links, rewards only genuinely independent
high-trust roots, and emits decision candidates. It never promotes provenance,
Memory, Mention, derived representations, or scores to Truth, Permission,
Production Authority, Safety Proof, Action Execution, or Action Success.

Canonical identity: NOEPIN-AL-101
DCSR level: LIMITED INTEGRATION / 限定適用.
Provenance note: exact registered Origin GUID was not freshly reverified in this
completion session and is intentionally not guessed or regenerated.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, IntEnum
from hashlib import sha256
import json, math

class Decision(str,Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class NodeKind(str,Enum):
    SOURCE='SOURCE'; TRANSFORM='TRANSFORM'; CLAIM='CLAIM'; MEMORY='MEMORY'; MENTION='MENTION'
class RiskClass(IntEnum):
    LOW=0; MEDIUM=1; HIGH=2; CRITICAL=3
class NextAction(str,Enum):
    PROVENANCE_SCORE_CANDIDATE='PROVENANCE_SCORE_CANDIDATE'; TRACE_REPAIR_CANDIDATE='TRACE_REPAIR_CANDIDATE'; REVALIDATION_CANDIDATE='REVALIDATION_CANDIDATE'; HOLD_UNRESOLVED='HOLD_UNRESOLVED'

@dataclass(frozen=True)
class ClaimRequest:
    request_id:str; claim_id:str; claim_node_id:str; risk:RiskClass; importance:float
    observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class ProvenanceNode:
    node_id:str; kind:NodeKind; parent_ids:tuple[str,...]; source_trust:float; transform_retention:float
    independent_group:str; source_version:str; source_fingerprint:str; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class ProvenancePolicy:
    allow_threshold_low:float; allow_threshold_medium:float; allow_threshold_high:float; allow_threshold_critical:float
    untrusted_root_threshold:float; untrusted_root_score_cap:float; broken_lineage_score_cap:float
    independent_root_bonus:float; independent_bonus_cap:float; excessive_transform_hops:int; excessive_transform_penalty:float
    min_independent_roots_for_bonus:int; critical_broken_lineage_hold:bool; high_broken_lineage_hold:bool
    binding:str; state_epoch:str; revoked:bool=False
@dataclass(frozen=True)
class ClaimProvenanceResult:
    decision:Decision; next_action:NextAction; reasons:tuple[str,...]
    provenance_score:float; weakest_link:float; root_count:int; independent_root_count:int; max_transform_hops:int
    broken_lineage:bool; untrusted_root_present:bool; trace:tuple[str,...]; next_gate_candidate:bool
    memory_promoted_to_truth:bool=False; mention_promoted_to_memory:bool=False; provenance_promoted_to_truth:bool=False
    score_promoted_to_authority:bool=False; permission_granted:bool=False; action_executed:bool=False
    plan_committed:bool=False; atomic_publish_executed:bool=False; external_write_performed:bool=False
    world_truth_proven:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedProvenanceState:
    request:ClaimRequest; nodes:tuple[ProvenanceNode,...]; policy:ProvenancePolicy
    node_fingerprints:tuple[tuple[str,str],...]; context_fingerprint:str; dependency_fingerprint:str
    policy_fingerprint:str; registry_fingerprint:str; precomputed_result:ClaimProvenanceResult
    binding:str; state_epoch:str
@dataclass(frozen=True)
class ProvenanceStateDelta:
    base_fingerprint:str; target_fingerprint:str; changed_nodes:tuple[ProvenanceNode,...]; removed_node_ids:tuple[str,...]
    target_request:ClaimRequest|None; target_policy:ProvenancePolicy|None; binding:str; state_epoch:str
@dataclass(frozen=True)
class ProvenanceSyncPlan:
    missing_or_changed_node_ids:tuple[str,...]; metadata_bytes_required:int; full_resend_required:bool

def _cv(x):
    if isinstance(x,Enum): return x.name if isinstance(x,IntEnum) else x.value
    if hasattr(x,'__dataclass_fields__'): return {k:_cv(getattr(x,k)) for k in x.__dataclass_fields__}
    if isinstance(x,tuple): return [_cv(v) for v in x]
    if isinstance(x,list): return [_cv(v) for v in x]
    if isinstance(x,dict): return {str(k):_cv(x[k]) for k in sorted(x)}
    return x
def _canon(x)->bytes: return json.dumps(_cv(x),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def _fp(x)->str: return sha256(_canon(x)).hexdigest()
def _clamp(x): return max(0.0,min(1.0,x))
def _threshold(r,p):
    return {RiskClass.LOW:p.allow_threshold_low,RiskClass.MEDIUM:p.allow_threshold_medium,RiskClass.HIGH:p.allow_threshold_high,RiskClass.CRITICAL:p.allow_threshold_critical}[r]

def _validate(req,nodes,p):
    if p.revoked: return 'POLICY_REVOKED'
    if not req.observed or not req.request_id or not req.claim_id or not req.claim_node_id: return 'REQUEST_INVALID'
    if req.binding!=p.binding or req.state_epoch!=p.state_epoch: return 'REQUEST_SCOPE_MISMATCH'
    if not math.isfinite(req.importance) or not 0<=req.importance<=1: return 'REQUEST_VALUE_INVALID'
    vals=(p.allow_threshold_low,p.allow_threshold_medium,p.allow_threshold_high,p.allow_threshold_critical,p.untrusted_root_threshold,p.untrusted_root_score_cap,p.broken_lineage_score_cap,p.independent_root_bonus,p.independent_bonus_cap,p.excessive_transform_penalty)
    if any(not math.isfinite(v) or not 0<=v<=1 for v in vals): return 'POLICY_RANGE_INVALID'
    if not (p.allow_threshold_low<=p.allow_threshold_medium<=p.allow_threshold_high<=p.allow_threshold_critical): return 'POLICY_THRESHOLD_NONMONOTONIC'
    if p.excessive_transform_hops<0 or p.min_independent_roots_for_bonus<2: return 'POLICY_PARAMETER_INVALID'
    ids=[n.node_id for n in nodes]
    if len(ids)!=len(set(ids)): return 'DUPLICATE_NODE_ID'
    for n in nodes:
        if not n.observed or not n.node_id or not n.source_version or not n.source_fingerprint: return 'NODE_INVALID'
        if n.binding!=p.binding or n.state_epoch!=p.state_epoch: return 'NODE_SCOPE_MISMATCH'
        if not math.isfinite(n.source_trust) or not math.isfinite(n.transform_retention): return 'NODE_VALUE_INVALID'
        if not 0<=n.source_trust<=1 or not 0<=n.transform_retention<=1: return 'NODE_RANGE_INVALID'
        if n.node_id in n.parent_ids: return 'SELF_CYCLE'
    return None

def evaluate(req:ClaimRequest,nodes:tuple[ProvenanceNode,...],p:ProvenancePolicy)->ClaimProvenanceResult:
    nodes=tuple(nodes); err=_validate(req,nodes,p)
    if err:
        return ClaimProvenanceResult(Decision.HOLD,NextAction.HOLD_UNRESOLVED,(err,),0.0,0.0,0,0,0,True,False,(),False)
    by={n.node_id:n for n in nodes}
    if req.claim_node_id not in by:
        return ClaimProvenanceResult(Decision.HOLD,NextAction.TRACE_REPAIR_CANDIDATE,('CLAIM_NODE_MISSING',),0.0,0.0,0,0,0,True,False,(),False)
    paths=[]; trace=[]; broken=False; cycle=False
    def walk(node_id,retention,hops,seen,path):
        nonlocal broken,cycle
        if node_id not in by:
            broken=True; trace.append('MISSING:'+node_id); return
        if node_id in seen:
            cycle=True; trace.append('CYCLE:'+node_id); return
        n=by[node_id]; trace.append(f'{n.kind.value}:{n.node_id}')
        newret=retention*(n.transform_retention if n.kind in (NodeKind.TRANSFORM,NodeKind.MEMORY,NodeKind.MENTION) else 1.0)
        newh=hops+(1 if n.kind in (NodeKind.TRANSFORM,NodeKind.MEMORY,NodeKind.MENTION) else 0)
        if not n.parent_ids:
            if n.kind!=NodeKind.SOURCE: broken=True
            paths.append((n,newret,newh,path+(n.node_id,))); return
        for par in n.parent_ids:
            walk(par,newret,newh,seen|{node_id},path+(n.node_id,))
    walk(req.claim_node_id,1.0,0,set(),tuple())
    if cycle:
        return ClaimProvenanceResult(Decision.HOLD,NextAction.TRACE_REPAIR_CANDIDATE,('PROVENANCE_CYCLE',),0.0,0.0,0,0,0,True,False,tuple(dict.fromkeys(trace)),False)
    roots=[]; weighted=[]; weakest=1.0; maxh=0; groups=set(); untrusted=False
    for root,ret,hops,_ in paths:
        roots.append(root.node_id); maxh=max(maxh,hops)
        link=_clamp(root.source_trust*ret); weakest=min(weakest,link); weighted.append(link)
        if root.independent_group: groups.add(root.independent_group)
        if root.source_trust<p.untrusted_root_threshold: untrusted=True
    if not weighted: broken=True; weakest=0.0; base=0.0
    else: base=sum(weighted)/len(weighted)
    indep=len(groups)
    score=base
    if indep>=p.min_independent_roots_for_bonus:
        score=min(1.0,score+min(p.independent_bonus_cap,p.independent_root_bonus*(indep-1)))
    if maxh>p.excessive_transform_hops:
        score*=max(0.0,1.0-p.excessive_transform_penalty*(maxh-p.excessive_transform_hops))
    if broken: score=min(score,p.broken_lineage_score_cap)
    if untrusted: score=min(score,p.untrusted_root_score_cap)
    score=_clamp(score)
    threshold=_threshold(req.risk,p)
    reasons=[]
    if broken: reasons.append('BROKEN_LINEAGE_CONFIDENCE_DECAY')
    if untrusted: reasons.append('UNTRUSTED_ROOT_SCORE_CAP')
    if maxh>p.excessive_transform_hops: reasons.append('EXCESSIVE_TRANSFORM_DECAY')
    if indep>=p.min_independent_roots_for_bonus: reasons.append('INDEPENDENT_HIGH_QUALITY_ROOTS_BONUS_CANDIDATE')
    important=req.importance>=.70 or req.risk>=RiskClass.HIGH
    if broken and important and (req.risk==RiskClass.CRITICAL and p.critical_broken_lineage_hold or req.risk>=RiskClass.HIGH and p.high_broken_lineage_hold):
        decision=Decision.HOLD; action=NextAction.TRACE_REPAIR_CANDIDATE; next_gate=False; reasons.append('IMPORTANT_CLAIM_BROKEN_LINEAGE_HOLD')
    elif score>=threshold and not untrusted:
        decision=Decision.ALLOW; action=NextAction.PROVENANCE_SCORE_CANDIDATE; next_gate=True; reasons.append('PROVENANCE_SCORE_THRESHOLD_MET')
    else:
        decision=Decision.HOLD; action=NextAction.REVALIDATION_CANDIDATE; next_gate=False; reasons.append('PROVENANCE_SCORE_INSUFFICIENT')
    # Memory ≠ Truth and Mention ≠ Memory remain invariant regardless of score.
    if any(n.kind==NodeKind.MEMORY for n in nodes): reasons.append('MEMORY_NOT_TRUTH')
    if any(n.kind==NodeKind.MENTION for n in nodes): reasons.append('MENTION_NOT_MEMORY')
    return ClaimProvenanceResult(decision,action,tuple(dict.fromkeys(reasons)),round(score,12),round(weakest,12),len(set(roots)),indep,maxh,broken,untrusted,tuple(dict.fromkeys(trace)),next_gate)

def default_policy():
    return ProvenancePolicy(.55,.65,.75,.85,.40,.45,.50,.03,.08,4,.08,2,True,True,'CPSA-BIND','STATE-EPOCH-1')
def default_request():
    p=default_policy(); return ClaimRequest('REQ-101','CLAIM-A','C-A',RiskClass.LOW,.50,True,p.binding,p.state_epoch)
def default_nodes():
    p=default_policy(); b=p.binding; e=p.state_epoch
    return (
      ProvenanceNode('S-1',NodeKind.SOURCE,(),.94,1.0,'ROOT-A','SRC-V1','SF-S1',True,b,e),
      ProvenanceNode('S-2',NodeKind.SOURCE,(),.90,1.0,'ROOT-B','SRC-V2','SF-S2',True,b,e),
      ProvenanceNode('T-1',NodeKind.TRANSFORM,('S-1','S-2'),1.0,.96,'','TR-V1','SF-T1',True,b,e),
      ProvenanceNode('C-A',NodeKind.CLAIM,('T-1',),1.0,1.0,'','CLAIM-V1','SF-CA',True,b,e),
    )
def default_evaluation(): return evaluate(default_request(),default_nodes(),default_policy())

def _node_fps(nodes): return tuple((f'NODE:{n.node_id}',_fp(n)) for n in sorted(nodes,key=lambda x:x.node_id))
def _context_fp(req): return _fp(req)
def _dependency_fp(nodes): return _fp(_node_fps(nodes))
def _policy_fp(p): return _fp(p)
def _registry_fp(req,nodes,p): return _fp((req,_node_fps(nodes),p))
def prepare_state(req,nodes,p,*,binding:str,state_epoch:str):
    nodes=tuple(nodes); fps=_node_fps(nodes)
    return PreparedProvenanceState(req,nodes,p,fps,_context_fp(req),_dependency_fp(nodes),_policy_fp(p),_registry_fp(req,nodes,p),evaluate(req,nodes,p),binding,state_epoch)
def validate_prepared_integrity(st):
    return (st.binding==st.policy.binding==st.request.binding and st.state_epoch==st.policy.state_epoch==st.request.state_epoch and
            st.node_fingerprints==_node_fps(st.nodes) and st.context_fingerprint==_context_fp(st.request) and
            st.dependency_fingerprint==_dependency_fp(st.nodes) and st.policy_fingerprint==_policy_fp(st.policy) and
            st.registry_fingerprint==_registry_fp(st.request,st.nodes,st.policy) and st.precomputed_result==evaluate(st.request,st.nodes,st.policy))
def evaluate_prepared(st,*,integrity_validated:bool,current_context_fingerprint:str,current_dependency_fingerprint:str,current_policy_fingerprint:str,current_registry_fingerprint:str):
    # Integrity must be validated independently once. Reuse then compares already-known
    # current state fingerprints rather than rehashing the full provenance registry.
    if not integrity_validated:
        return ClaimProvenanceResult(Decision.HOLD,NextAction.HOLD_UNRESOLVED,('PREPARED_INTEGRITY_NOT_VALIDATED',),0,0,0,0,0,True,False,(),False)
    if (st.context_fingerprint!=current_context_fingerprint or st.dependency_fingerprint!=current_dependency_fingerprint or
        st.policy_fingerprint!=current_policy_fingerprint or st.registry_fingerprint!=current_registry_fingerprint):
        return ClaimProvenanceResult(Decision.HOLD,NextAction.REVALIDATION_CANDIDATE,('PREPARED_FINGERPRINT_MISMATCH_REEVALUATION_REQUIRED',),0,0,0,0,0,True,False,(),False)
    return st.precomputed_result

def make_delta(base:PreparedProvenanceState,target:PreparedProvenanceState):
    bm=dict(base.node_fingerprints); tm=dict(target.node_fingerprints); tby={n.node_id:n for n in target.nodes}
    changed=tuple(tby[k[5:]] for k,v in tm.items() if bm.get(k)!=v)
    removed=tuple(k[5:] for k in bm if k not in tm)
    return ProvenanceStateDelta(base.registry_fingerprint,target.registry_fingerprint,changed,removed,target.request if base.context_fingerprint!=target.context_fingerprint else None,target.policy if base.policy_fingerprint!=target.policy_fingerprint else None,target.binding,target.state_epoch)
def plan_missing_only(local:PreparedProvenanceState,target:PreparedProvenanceState):
    lm=dict(local.node_fingerprints); tm=dict(target.node_fingerprints); ids=tuple(k[5:] for k,v in tm.items() if lm.get(k)!=v)
    meta=len(_canon(ids)); return ProvenanceSyncPlan(ids,meta,False)
