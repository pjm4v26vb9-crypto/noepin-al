"""NOEPIN AL 128 — Responsibility Contribution Allocator — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-128
DCSR: DIRECT INTEGRATION / 直接統合.

Contribution outputs are audit candidates only. They do not prove legal/moral responsibility,
malicious intent, world truth, safety, permission, authority, punishment, trust updates, execution,
or action success. Causal uncertainty is retained rather than forced into single-agent blame.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str, Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class AttributionState(str, Enum):
    ATTRIBUTABLE='ATTRIBUTABLE'; PARTIAL='PARTIAL'; INDETERMINATE='INDETERMINATE'; INVALID='INVALID'
class NextAction(str, Enum):
    RESPONSIBILITY_CONTRIBUTION_CANDIDATE='RESPONSIBILITY_CONTRIBUTION_CANDIDATE'; HOLD_CAUSAL_REVIEW_CANDIDATE='HOLD_CAUSAL_REVIEW_CANDIDATE'; HUMAN_REVIEW_CANDIDATE='HUMAN_REVIEW_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; INSUFFICIENT_CAUSAL_COVERAGE='INSUFFICIENT_CAUSAL_COVERAGE'; UNKNOWN_CAUSAL_RELATION='UNKNOWN_CAUSAL_RELATION'; OUTCOME_UNOBSERVED='OUTCOME_UNOBSERVED'; INVALID_GRAPH='INVALID_GRAPH'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'

@dataclass(frozen=True)
class DecisionNode:
    node_id:str
    agent_id:str|None
    role:str
    counterfactual_effect:float|None
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class CausalEdge:
    source_id:str
    target_id:str
    strength:float|None
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class OutcomeSpec:
    outcome_node_id:str
    observed:bool
    risk_level:str
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class AttributionPolicy:
    min_causal_coverage:float=.70
    high_risk_min_coverage:float=.85
    critical_contributor_threshold:float=.45
    counterfactual_weight:float=.65
    path_weight:float=.35
    unknown_hold_fraction:float=.30
    allow_human_escalation:bool=True

@dataclass(frozen=True)
class AttributionRequest:
    request_id:str
    nodes:tuple[DecisionNode,...]
    edges:tuple[CausalEdge,...]
    outcome:OutcomeSpec
    policy:AttributionPolicy
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class AgentContribution:
    agent_id:str
    contribution_score:float
    uncertainty:float
    supporting_node_ids:tuple[str,...]
    roles:tuple[str,...]

@dataclass(frozen=True)
class AttributionResult:
    decision:Decision
    next_action:NextAction
    escalation:Escalation
    attribution_state:AttributionState
    reasons:tuple[str,...]
    contribution_scores:tuple[AgentContribution,...]
    critical_contributors:tuple[str,...]
    causal_coverage:float
    unresolved_fraction:float
    trace:tuple[str,...]
    next_gate_candidate:bool
    contribution_promoted_to_liability:bool=False
    critical_contributor_promoted_to_sole_responsibility:bool=False
    trust_update_executed:bool=False
    penalty_executed:bool=False
    authority_restriction_executed:bool=False
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
class PreparedAttributionState:
    request:AttributionRequest
    result:AttributionResult
    context_fingerprint:str
    graph_fingerprint:str
    policy_fingerprint:str
    outcome_fingerprint:str
    integrity_fingerprint:str
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class AttributionDelta:
    changed_nodes:tuple[DecisionNode,...]
    removed_node_ids:tuple[str,...]
    changed_edges:tuple[CausalEdge,...]
    removed_edge_ids:tuple[str,...]
    from_manifest_fingerprint:str
    to_manifest_fingerprint:str

@dataclass(frozen=True)
class MissingOnlyPlan:
    missing_or_changed_record_ids:tuple[str,...]
    metadata_bytes_required:int
    full_resend_required:bool

ROLE_WEIGHTS={'ACTION':1.0,'EXECUTION':1.0,'APPROVAL':.62,'PROPOSAL':.72,'DECISION':.82,'EVIDENCE':.42,'REVIEW':.48,'OUTCOME':0.0}


def _obj(v):
    if isinstance(v,Enum): return v.value
    if is_dataclass(v): return {f.name:_obj(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v,dict): return {str(k):_obj(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(tuple,list)): return [_obj(x) for x in v]
    return v

def _canon(v): return json.dumps(_obj(v),ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def _fp(v): return sha256(_canon(v)).hexdigest()
def _finite(x): return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(float(x))
def _edge_id(e:CausalEdge): return f'{e.source_id}->{e.target_id}'
def _manifest_fp(req): return _fp((req.nodes,req.edges,req.outcome,req.binding,req.state_epoch))

def default_policy(): return AttributionPolicy()

def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    nodes=(
        DecisionNode('PROPOSAL-A','AGENT-A','PROPOSAL',.75,b,e),
        DecisionNode('APPROVAL-B','AGENT-B','APPROVAL',.45,b,e),
        DecisionNode('ACTION-A','AGENT-A','ACTION',.95,b,e),
        DecisionNode('REVIEW-C','AGENT-C','REVIEW',.10,b,e),
        DecisionNode('OUTCOME',None,'OUTCOME',None,b,e),
    )
    edges=(
        CausalEdge('PROPOSAL-A','APPROVAL-B',.90,b,e),
        CausalEdge('APPROVAL-B','ACTION-A',.88,b,e),
        CausalEdge('ACTION-A','OUTCOME',.98,b,e),
        CausalEdge('REVIEW-C','ACTION-A',.20,b,e),
    )
    return AttributionRequest('DEFAULT-128',nodes,edges,OutcomeSpec('OUTCOME',True,'HIGH',b,e),default_policy(),b,e)

def _invalid(reason,esc=Escalation.INVALID_CONFIGURATION):
    return AttributionResult(Decision.HOLD,NextAction.HOLD_CAUSAL_REVIEW_CANDIDATE,esc,AttributionState.INVALID,(reason,'NO_SOLE_RESPONSIBILITY_ASSERTION','NO_PENALTY_EXECUTION'),(),(),0.0,1.0,(),False)

def _toposort(nodes:dict[str,DecisionNode],edges:tuple[CausalEdge,...]):
    indeg={k:0 for k in nodes}; out={k:[] for k in nodes}
    for x in edges:
        if x.source_id not in nodes or x.target_id not in nodes: return None,None
        indeg[x.target_id]+=1; out[x.source_id].append(x.target_id)
    q=sorted(k for k,v in indeg.items() if v==0); order=[]
    while q:
        u=q.pop(0); order.append(u)
        for v in sorted(out[u]):
            indeg[v]-=1
            if indeg[v]==0:
                q.append(v); q.sort()
    return (order,out) if len(order)==len(nodes) else (None,None)

def evaluate(req:AttributionRequest)->AttributionResult:
    if not req.request_id or not req.binding or not req.state_epoch: return _invalid('INVALID_REQUEST_IDENTITY')
    p=req.policy; o=req.outcome
    nums=(p.min_causal_coverage,p.high_risk_min_coverage,p.critical_contributor_threshold,p.counterfactual_weight,p.path_weight,p.unknown_hold_fraction)
    if any(not _finite(x) for x in nums): return _invalid('INVALID_POLICY_NUMERIC')
    if any(not (0<=x<=1) for x in nums): return _invalid('INVALID_POLICY_RANGE')
    if p.counterfactual_weight+p.path_weight<=0: return _invalid('INVALID_POLICY_WEIGHTS')
    if o.binding!=req.binding or o.state_epoch!=req.state_epoch or not o.outcome_node_id: return _invalid('OUTCOME_IDENTITY_INVALID')
    ids=[n.node_id for n in req.nodes]
    if any(not x for x in ids) or len(ids)!=len(set(ids)): return _invalid('DUPLICATE_OR_EMPTY_NODE')
    nodes={n.node_id:n for n in req.nodes}
    if o.outcome_node_id not in nodes: return _invalid('OUTCOME_NODE_MISSING',Escalation.INVALID_GRAPH)
    for n in req.nodes:
        if n.binding!=req.binding or n.state_epoch!=req.state_epoch: return _invalid('NODE_IDENTITY_INVALID')
        if n.counterfactual_effect is not None and (not _finite(n.counterfactual_effect) or not 0<=n.counterfactual_effect<=1): return _invalid('COUNTERFACTUAL_EFFECT_INVALID')
        if n.role.upper() not in ROLE_WEIGHTS: return _invalid('UNKNOWN_ROLE')
    eids=[_edge_id(x) for x in req.edges]
    if len(eids)!=len(set(eids)): return _invalid('DUPLICATE_EDGE',Escalation.INVALID_GRAPH)
    for x in req.edges:
        if x.binding!=req.binding or x.state_epoch!=req.state_epoch: return _invalid('EDGE_IDENTITY_INVALID')
        if x.strength is not None and (not _finite(x.strength) or not 0<=x.strength<=1): return _invalid('EDGE_STRENGTH_INVALID')
    order,out=_toposort(nodes,req.edges)
    if order is None: return _invalid('GRAPH_CYCLE_OR_DANGLING_EDGE',Escalation.INVALID_GRAPH)
    if not o.observed:
        return AttributionResult(Decision.HOLD,NextAction.HUMAN_REVIEW_CANDIDATE if p.allow_human_escalation else NextAction.HOLD_CAUSAL_REVIEW_CANDIDATE,Escalation.OUTCOME_UNOBSERVED,AttributionState.INDETERMINATE,('OUTCOME_NOT_OBSERVED','DO_NOT_ASSERT_RESPONSIBILITY'),(),(),0.0,1.0,(),False)
    # Reverse max-path strength to observed outcome. Unknown edges are preserved as unresolved evidence.
    incoming_by_target={k:[] for k in nodes}
    known_edges=0
    for x in req.edges:
        incoming_by_target[x.target_id].append(x)
        if x.strength is not None: known_edges+=1
    path={k:0.0 for k in nodes}; path[o.outcome_node_id]=1.0
    for target in reversed(order):
        if path[target]<=0: continue
        for edge in incoming_by_target[target]:
            if edge.strength is not None:
                path[edge.source_id]=max(path[edge.source_id],path[target]*edge.strength)
    total_edges=max(1,len(req.edges)); edge_coverage=known_edges/total_edges
    actor_nodes=[n for n in req.nodes if n.agent_id and n.node_id!=o.outcome_node_id]
    known_cf=sum(1 for n in actor_nodes if n.counterfactual_effect is not None)
    cf_coverage=known_cf/max(1,len(actor_nodes))
    causal_coverage=(edge_coverage+cf_coverage)/2
    unknown_fraction=1-causal_coverage
    threshold=p.high_risk_min_coverage if o.risk_level.upper() in {'HIGH','CRITICAL'} else p.min_causal_coverage
    traces=[]; raw_by_agent={}; nodes_by_agent={}; roles_by_agent={}; unknown_by_agent={}
    wsum=p.counterfactual_weight+p.path_weight
    for n in sorted(actor_nodes,key=lambda x:x.node_id):
        rw=ROLE_WEIGHTS[n.role.upper()]
        cf=n.counterfactual_effect
        known_cf_value=0.0 if cf is None else cf
        raw=rw*((p.counterfactual_weight*known_cf_value+p.path_weight*path[n.node_id])/wsum)
        if raw>0:
            raw_by_agent[n.agent_id]=raw_by_agent.get(n.agent_id,0.0)+raw
        nodes_by_agent.setdefault(n.agent_id,[]).append(n.node_id)
        roles_by_agent.setdefault(n.agent_id,set()).add(n.role.upper())
        unknown_by_agent[n.agent_id]=unknown_by_agent.get(n.agent_id,0)+(1 if cf is None else 0)
        traces.append(f'{n.node_id}|agent={n.agent_id}|role={n.role.upper()}|path={path[n.node_id]:.6f}|cf={"UNKNOWN" if cf is None else f"{cf:.6f}"}|raw={raw:.6f}')
    if not raw_by_agent or causal_coverage<threshold or unknown_fraction>p.unknown_hold_fraction:
        esc=Escalation.INSUFFICIENT_CAUSAL_COVERAGE if causal_coverage<threshold else Escalation.UNKNOWN_CAUSAL_RELATION
        return AttributionResult(Decision.HOLD,NextAction.HUMAN_REVIEW_CANDIDATE if p.allow_human_escalation else NextAction.HOLD_CAUSAL_REVIEW_CANDIDATE,esc,AttributionState.INDETERMINATE,('CAUSAL_EVIDENCE_INSUFFICIENT','UNCERTAINTY_RETAINED','NO_SOLE_RESPONSIBILITY_ASSERTION'),(),(),causal_coverage,unknown_fraction,tuple(traces),False)
    total=sum(raw_by_agent.values())
    contributions=[]
    for aid in sorted(raw_by_agent):
        score=raw_by_agent[aid]/total if total>0 else 0.0
        un=unknown_by_agent.get(aid,0)/max(1,len(nodes_by_agent[aid]))
        contributions.append(AgentContribution(aid,score,un,tuple(sorted(nodes_by_agent[aid])),tuple(sorted(roles_by_agent[aid]))))
    contributions=tuple(sorted(contributions,key=lambda x:(-x.contribution_score,x.agent_id)))
    critical=tuple(x.agent_id for x in contributions if x.contribution_score>=p.critical_contributor_threshold)
    state=AttributionState.ATTRIBUTABLE if causal_coverage>=.95 else AttributionState.PARTIAL
    return AttributionResult(Decision.ALLOW,NextAction.RESPONSIBILITY_CONTRIBUTION_CANDIDATE,Escalation.NONE,state,('AUDIT_ATTRIBUTION_CANDIDATE_ONLY','CAUSAL_UNCERTAINTY_RETAINED','NO_AUTOMATIC_PENALTY_OR_TRUST_UPDATE'),contributions,critical,causal_coverage,unknown_fraction,tuple(traces),True)

def default_evaluation(): return evaluate(default_request())

def _fps(req,result): return (_fp((req.request_id,req.outcome,req.binding,req.state_epoch)),_fp((req.nodes,req.edges)),_fp(req.policy),_fp(result))
def _integrity_payload(cf,gf,pf,of,b,e): return (cf,gf,pf,of,b,e,'NOEPIN-AL-128-PREPARED-V1')
def prepare_state(req:AttributionRequest,*,binding:str,state_epoch:str)->PreparedAttributionState:
    r=_invalid('PREPARED_BINDING_OR_EPOCH_MISMATCH') if binding!=req.binding or state_epoch!=req.state_epoch else evaluate(req)
    cf,gf,pf,of=_fps(req,r); integ=_fp(_integrity_payload(cf,gf,pf,of,binding,state_epoch))
    return PreparedAttributionState(req,r,cf,gf,pf,of,integ,binding,state_epoch)
def validate_prepared_integrity(st):
    return st.integrity_fingerprint==_fp(_integrity_payload(st.context_fingerprint,st.graph_fingerprint,st.policy_fingerprint,st.outcome_fingerprint,st.binding,st.state_epoch))
def evaluate_prepared(st:PreparedAttributionState,*,integrity_validated:bool,current_context_fingerprint:str,current_graph_fingerprint:str,current_policy_fingerprint:str,current_outcome_fingerprint:str)->AttributionResult:
    ok=(integrity_validated and validate_prepared_integrity(st) and st.binding==st.request.binding and st.state_epoch==st.request.state_epoch and current_context_fingerprint==st.context_fingerprint and current_graph_fingerprint==st.graph_fingerprint and current_policy_fingerprint==st.policy_fingerprint and current_outcome_fingerprint==st.outcome_fingerprint)
    return st.result if ok else _invalid('PREPARED_REUSE_REJECTED')
def make_delta(old:PreparedAttributionState,new:PreparedAttributionState)->AttributionDelta:
    on={x.node_id:x for x in old.request.nodes}; nn={x.node_id:x for x in new.request.nodes}
    oe={_edge_id(x):x for x in old.request.edges}; ne={_edge_id(x):x for x in new.request.edges}
    cn=tuple(nn[k] for k in sorted(nn) if k not in on or _canon(nn[k])!=_canon(on[k])); rn=tuple(sorted(set(on)-set(nn)))
    ce=tuple(ne[k] for k in sorted(ne) if k not in oe or _canon(ne[k])!=_canon(oe[k])); re=tuple(sorted(set(oe)-set(ne)))
    return AttributionDelta(cn,rn,ce,re,_manifest_fp(old.request),_manifest_fp(new.request))
def plan_missing_only(old:PreparedAttributionState,new:PreparedAttributionState)->MissingOnlyPlan:
    d=make_delta(old,new)
    ids=tuple(sorted([f'NODE:{x.node_id}' for x in d.changed_nodes]+[f'REMOVED_NODE:{x}' for x in d.removed_node_ids]+[f'EDGE:{_edge_id(x)}' for x in d.changed_edges]+[f'REMOVED_EDGE:{x}' for x in d.removed_edge_ids]))
    meta=len(_canon({'from':d.from_manifest_fingerprint,'to':d.to_manifest_fingerprint,'ids':ids}))
    return MissingOnlyPlan(ids,meta,False)
