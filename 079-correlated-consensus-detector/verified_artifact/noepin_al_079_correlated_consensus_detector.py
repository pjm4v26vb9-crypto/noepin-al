"""NOEPIN AL 079 — Correlated Consensus Detector — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Deterministic detector for correlated multi-agent consensus. It discounts votes that
share model/prompt/source/evidence lineage and fails closed when material lineage is
unknown. It does not prove truth, authenticate agents, grant permission, execute
consensus decisions, or inherit sender authority/intent/consent.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Sequence

class Decision(str,Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'

@dataclass(frozen=True)
class AgentOutput:
    output_id:str; agent_id:str; conclusion:str; model_id:str; prompt_family:str
    source_ids:tuple[str,...]; evidence_ids:tuple[str,...]; lineage_observed:bool
    weight:float; binding:str; state_epoch:str
@dataclass(frozen=True)
class ConsensusPolicy:
    binding:str; state_epoch:str; threshold:float=0.66; min_effective_votes:float=2.0
    correlation_edge_threshold:float=0.08; unknown_lineage_weight:float=0.25
    revoked:bool=False
@dataclass(frozen=True)
class ConsensusRequest:
    request_id:str; target_conclusion:str; output_ids:tuple[str,...]
    binding:str; state_epoch:str
@dataclass(frozen=True)
class CorrelationEdge:
    left:str; right:str; similarity:float; reasons:tuple[str,...]
@dataclass(frozen=True)
class CorrelationCluster:
    cluster_id:str; member_ids:tuple[str,...]; conclusion_set:tuple[str,...]
    effective_weight:float; raw_weight:float; avg_similarity:float
@dataclass(frozen=True)
class ConsensusResult:
    decision:Decision; reasons:tuple[str,...]
    independence_score:float; adjusted_consensus:float
    effective_target_support:float; effective_total:float; raw_total:float
    clusters:tuple[CorrelationCluster,...]; edges:tuple[CorrelationEdge,...]
    lineage_unknown_ids:tuple[str,...]; next_gate_candidate:bool
    permission_granted:bool=False; consensus_executed:bool=False
    sender_authority_inherited:bool=False; sender_intent_inherited:bool=False
    sender_consent_inherited:bool=False; authentication_proven:bool=False
    world_truth_proven:bool=False; external_write_performed:bool=False
    action_executed:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedConsensusState:
    policy:ConsensusPolicy; outputs:tuple[AgentOutput,...]
    output_fingerprints:tuple[tuple[str,str],...]; policy_fingerprint:str
    registry_fingerprint:str; output_index:tuple[tuple[str,AgentOutput],...]
    binding:str; state_epoch:str
@dataclass(frozen=True)
class ConsensusRegistryDelta:
    base_fingerprint:str; target_fingerprint:str; changed_outputs:tuple[AgentOutput,...]
    removed_output_ids:tuple[str,...]; target_policy:ConsensusPolicy
    binding:str; state_epoch:str
@dataclass(frozen=True)
class ConsensusSyncPlan:
    missing_or_changed_outputs:tuple[str,...]; metadata_bytes_required:int
    full_resend_required:bool

def _canon(v)->bytes:
    def cv(x):
        if isinstance(x,Enum): return x.value
        if hasattr(x,'__dataclass_fields__'): return {k:cv(getattr(x,k)) for k in x.__dataclass_fields__}
        if isinstance(x,tuple): return [cv(i) for i in x]
        if isinstance(x,list): return [cv(i) for i in x]
        if isinstance(x,dict): return {str(k):cv(x[k]) for k in sorted(x)}
        if isinstance(x,float): return round(x,12)
        return x
    return json.dumps(cv(v),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def _fp(v)->str: return sha256(_canon(v)).hexdigest()
def _uniq(items,attr):
    ids=[getattr(x,attr) for x in items]; return len(ids)==len(set(ids))
def _idx(items,key): return tuple(sorted(((getattr(x,key),x) for x in items),key=lambda z:z[0]))
def _lookup(index,key):
    lo,hi=0,len(index)
    while lo<hi:
        m=(lo+hi)//2
        if index[m][0]<key: lo=m+1
        else: hi=m
    return index[lo][1] if lo<len(index) and index[lo][0]==key else None
def _registry_fp(policy,outputs): return _fp({'policy':_fp(policy),'outputs':sorted((x.output_id,_fp(x)) for x in outputs)})
def _jacc(a,b):
    a,b=set(a),set(b)
    if not a and not b: return 0.0
    return len(a&b)/len(a|b)
def _similarity(a:AgentOutput,b:AgentOutput):
    reasons=[]; s=0.0
    if a.model_id and b.model_id and a.model_id==b.model_id: s+=0.30; reasons.append('SAME_MODEL')
    if a.prompt_family and b.prompt_family and a.prompt_family==b.prompt_family: s+=0.15; reasons.append('SAME_PROMPT_FAMILY')
    js=_jacc(a.source_ids,b.source_ids); je=_jacc(a.evidence_ids,b.evidence_ids)
    if js>0: s+=0.275*js; reasons.append('SHARED_SOURCE')
    if je>0: s+=0.275*je; reasons.append('SHARED_EVIDENCE')
    return min(1.0,s),tuple(reasons)
def _hold(reason,unknown=()):
    return ConsensusResult(Decision.HOLD,(reason,),0.0,0.0,0.0,0.0,0.0,(),(),tuple(unknown),False)

def default_policy(): return ConsensusPolicy('CONS-BIND','STATE-EPOCH-1')
def default_outputs():
    b,e='CONS-BIND','STATE-EPOCH-1'
    return (
      AgentOutput('OUT-A','AGENT-A','YES','MODEL-A','PROMPT-A',('SRC-A',),('EVID-A',),True,1.0,b,e),
      AgentOutput('OUT-B','AGENT-B','YES','MODEL-B','PROMPT-B',('SRC-B',),('EVID-B',),True,1.0,b,e),
      AgentOutput('OUT-C','AGENT-C','NO','MODEL-C','PROMPT-C',('SRC-C',),('EVID-C',),True,1.0,b,e),
    )
def default_request(): return ConsensusRequest('REQ-1','YES',('OUT-A','OUT-B','OUT-C'),'CONS-BIND','STATE-EPOCH-1')

def _validate_policy(p):
    return 0.5<=p.threshold<=1.0 and p.min_effective_votes>0 and 0<=p.correlation_edge_threshold<=1 and 0<=p.unknown_lineage_weight<=1

def _evaluate_selected(req,policy,selected):
    if not selected: return _hold('NO_AGENT_OUTPUTS')
    unknown=tuple(sorted(x.output_id for x in selected if not x.lineage_observed or not x.model_id or not x.prompt_family or (not x.source_ids and not x.evidence_ids)))
    # Unknown lineage must never be treated as independent-vote confidence.
    if unknown:
        return _hold('INDEPENDENCE_LINEAGE_INSUFFICIENT',unknown)
    # Pairwise graph.
    edges=[]; adj={x.output_id:set() for x in selected}; byid={x.output_id:x for x in selected}
    for i,a in enumerate(selected):
        for b in selected[i+1:]:
            sim,rs=_similarity(a,b)
            if sim>=policy.correlation_edge_threshold:
                edges.append(CorrelationEdge(a.output_id,b.output_id,round(sim,12),rs)); adj[a.output_id].add(b.output_id); adj[b.output_id].add(a.output_id)
    # Connected components; conservative cluster effective weight. Fully correlated => max vote only.
    comps=[]; seen=set()
    for oid in sorted(adj):
        if oid in seen: continue
        stack=[oid]; seen.add(oid); members=[]
        while stack:
            q=stack.pop(); members.append(q)
            for n in sorted(adj[q]):
                if n not in seen: seen.add(n); stack.append(n)
        comps.append(tuple(sorted(members)))
    clusters=[]; eff_by_conclusion={}; raw_total=sum(max(0.0,x.weight) for x in selected); effective_total=0.0
    edge_map={(min(e.left,e.right),max(e.left,e.right)):e.similarity for e in edges}
    for ci,members in enumerate(comps):
        xs=[byid[m] for m in members]; raw=sum(max(0.0,x.weight) for x in xs)
        sims=[]
        for i,a in enumerate(members):
            for b in members[i+1:]: sims.append(edge_map.get((min(a,b),max(a,b)),0.0))
        avg=sum(sims)/len(sims) if sims else 0.0
        if len(xs)==1: eff=raw
        else:
            mx=max(max(0.0,x.weight) for x in xs)
            # extra votes count only by residual independence from cluster correlation
            eff=mx + max(0.0,raw-mx)*(1.0-avg)*0.5
        eff=max(0.0,min(raw,eff)); effective_total+=eff
        # Split cluster effective weight by raw conclusion share to avoid correlated mixed cluster double counting.
        byc={}
        for x in xs: byc[x.conclusion]=byc.get(x.conclusion,0.0)+max(0.0,x.weight)
        for c,rw in byc.items(): eff_by_conclusion[c]=eff_by_conclusion.get(c,0.0)+(eff*(rw/raw if raw else 0.0))
        clusters.append(CorrelationCluster(f'CLUSTER-{ci+1:03d}',members,tuple(sorted(byc)),round(eff,12),round(raw,12),round(avg,12)))
    target=eff_by_conclusion.get(req.target_conclusion,0.0)
    adjusted=(target/effective_total) if effective_total>0 else 0.0
    independence=(effective_total/raw_total) if raw_total>0 else 0.0
    reasons=[]
    if effective_total < policy.min_effective_votes:
        decision=Decision.HOLD; reasons.append('EFFECTIVE_INDEPENDENT_SUPPORT_INSUFFICIENT')
    elif adjusted >= policy.threshold:
        decision=Decision.ALLOW; reasons.append('ADJUSTED_CONSENSUS_THRESHOLD_MET')
    elif adjusted <= 1.0-policy.threshold:
        decision=Decision.DENY; reasons.append('ADJUSTED_CONSENSUS_OPPOSES_TARGET')
    else:
        decision=Decision.HOLD; reasons.append('ADJUSTED_CONSENSUS_INCONCLUSIVE')
    if any(len(c.member_ids)>1 for c in clusters): reasons.append('CORRELATION_DISCOUNT_APPLIED')
    return ConsensusResult(decision,tuple(reasons),round(independence,12),round(adjusted,12),round(target,12),round(effective_total,12),round(raw_total,12),tuple(clusters),tuple(edges),(),decision==Decision.ALLOW)

def evaluate(req:ConsensusRequest,policy:ConsensusPolicy,outputs:Sequence[AgentOutput])->ConsensusResult:
    if not isinstance(req,ConsensusRequest) or not isinstance(policy,ConsensusPolicy): return _hold('INVALID_TYPED_INPUT')
    if policy.revoked: return _hold('POLICY_REVOKED')
    if not _validate_policy(policy): return _hold('INVALID_POLICY')
    if req.binding!=policy.binding or req.state_epoch!=policy.state_epoch: return _hold('REQUEST_POLICY_BINDING_MISMATCH')
    outs=tuple(outputs)
    if not _uniq(outs,'output_id') or not _uniq(outs,'agent_id'): return _hold('DUPLICATE_OUTPUT_OR_AGENT_ID')
    for x in outs:
        if x.binding!=policy.binding or x.state_epoch!=policy.state_epoch: return _hold('OUTPUT_BINDING_MISMATCH')
        if x.weight<0 or x.weight>1: return _hold('INVALID_OUTPUT_WEIGHT')
    idx={x.output_id:x for x in outs}; selected=[]
    for oid in req.output_ids:
        if oid not in idx: return _hold('REQUESTED_OUTPUT_UNKNOWN')
        selected.append(idx[oid])
    if len(req.output_ids)!=len(set(req.output_ids)): return _hold('DUPLICATE_REQUEST_OUTPUT_ID')
    return _evaluate_selected(req,policy,tuple(selected))

def prepare_state(policy,outputs,*,binding:str)->PreparedConsensusState:
    oo=tuple(outputs)
    return PreparedConsensusState(policy,oo,tuple(sorted((x.output_id,_fp(x)) for x in oo)),_fp(policy),_registry_fp(policy,oo),_idx(oo,'output_id'),binding,policy.state_epoch)
def validate_prepared_integrity(st:PreparedConsensusState)->bool:
    if not isinstance(st,PreparedConsensusState): return False
    if st.binding!=st.policy.binding or st.state_epoch!=st.policy.state_epoch: return False
    if st.policy_fingerprint!=_fp(st.policy): return False
    if st.output_fingerprints!=tuple(sorted((x.output_id,_fp(x)) for x in st.outputs)): return False
    if st.registry_fingerprint!=_registry_fp(st.policy,st.outputs): return False
    if st.output_index!=_idx(st.outputs,'output_id'): return False
    return _uniq(st.outputs,'output_id') and _uniq(st.outputs,'agent_id') and _validate_policy(st.policy)
def evaluate_prepared(req,st:PreparedConsensusState,*,current_policy_fingerprint:str,current_registry_fingerprint:str,prepared_integrity_validated:bool)->ConsensusResult:
    if not isinstance(req,ConsensusRequest) or not isinstance(st,PreparedConsensusState): return _hold('INVALID_TYPED_INPUT')
    if not prepared_integrity_validated: return _hold('PREPARED_INTEGRITY_NOT_VALIDATED')
    if current_policy_fingerprint!=st.policy_fingerprint: return _hold('CURRENT_POLICY_FINGERPRINT_MISMATCH')
    if current_registry_fingerprint!=st.registry_fingerprint: return _hold('CURRENT_REGISTRY_FINGERPRINT_MISMATCH')
    p=st.policy
    if p.revoked: return _hold('POLICY_REVOKED')
    if req.binding!=p.binding or req.state_epoch!=p.state_epoch: return _hold('REQUEST_POLICY_BINDING_MISMATCH')
    selected=[]
    if len(req.output_ids)!=len(set(req.output_ids)): return _hold('DUPLICATE_REQUEST_OUTPUT_ID')
    for oid in req.output_ids:
        x=_lookup(st.output_index,oid)
        if x is None: return _hold('REQUESTED_OUTPUT_UNKNOWN')
        selected.append(x)
    return _evaluate_selected(req,p,tuple(selected))
def make_delta(a:PreparedConsensusState,b:PreparedConsensusState)->ConsensusRegistryDelta:
    af,bf=dict(a.output_fingerprints),dict(b.output_fingerprints); bm={x.output_id:x for x in b.outputs}
    ch=tuple(bm[k] for k in sorted(bf) if af.get(k)!=bf[k]); rm=tuple(sorted(set(af)-set(bf)))
    return ConsensusRegistryDelta(a.registry_fingerprint,b.registry_fingerprint,ch,rm,b.policy,b.binding,b.state_epoch)
def apply_delta(base:PreparedConsensusState,d:ConsensusRegistryDelta)->PreparedConsensusState:
    if d.base_fingerprint!=base.registry_fingerprint: raise ValueError('BASE_FINGERPRINT_MISMATCH')
    m={x.output_id:x for x in base.outputs}
    for k in d.removed_output_ids: m.pop(k,None)
    for x in d.changed_outputs: m[x.output_id]=x
    out=prepare_state(d.target_policy,tuple(m[k] for k in sorted(m)),binding=d.binding)
    if out.registry_fingerprint!=d.target_fingerprint: raise ValueError('TARGET_FINGERPRINT_MISMATCH')
    return out
def missing_only_sync_plan(target:PreparedConsensusState,known_outputs:dict[str,str])->ConsensusSyncPlan:
    tf=dict(target.output_fingerprints); miss=tuple(k for k in sorted(tf) if known_outputs.get(k)!=tf[k])
    meta=len(_canon({'outputs':miss,'policy':target.policy_fingerprint,'registry':target.registry_fingerprint}))
    return ConsensusSyncPlan(miss,meta,False)
def full_registry_bytes(st): return len(_canon({'policy':st.policy,'outputs':st.outputs}))
def delta_bytes(d): return len(_canon(d))
