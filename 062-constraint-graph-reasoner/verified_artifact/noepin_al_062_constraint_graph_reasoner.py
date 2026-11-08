"""NOEPIN AL 062 — Constraint Graph Reasoner — Sequential Successor V2.

Creator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
Implementation / analysis / documentation support: AI-assisted using ChatGPT
License / Rights: NOT SPECIFIED

Pure control/algorithm-plane reasoner. It never executes actions or grants authority.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict, is_dataclass, replace
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence

CREATOR="NOEPIN / のえぴん"
AI_SUPPORT="AI-assisted implementation / analysis / documentation support using ChatGPT"
LICENSE_RIGHTS="NOT SPECIFIED"
CANONICAL_ID="NOEPIN-AL-062"

class Decision(str,Enum):
    ALLOW="ALLOW"; DENY="DENY"; HOLD="HOLD"; HUMAN_APPROVAL="HUMAN_APPROVAL"
class NodeKind(str,Enum):
    ACTOR="ACTOR"; GOAL="GOAL"; ACTION="ACTION"; TARGET="TARGET"; SCOPE="SCOPE"; PRECONDITION="PRECONDITION"; EFFECT="EFFECT"; CONSTRAINT="CONSTRAINT"; POLICY="POLICY"; AUTHORITY="AUTHORITY"; APPROVAL="APPROVAL"; ENVIRONMENT="ENVIRONMENT"
class EdgeKind(str,Enum):
    REQUIRES="REQUIRES"; FORBIDS="FORBIDS"; IMPLIES="IMPLIES"; CONFLICTS="CONFLICTS"; ALLOWS="ALLOWS"; APPROVAL_REQUIRED="APPROVAL_REQUIRED"
class NodeState(str,Enum):
    SATISFIED="SATISFIED"; UNSATISFIED="UNSATISFIED"; UNKNOWN="UNKNOWN"

@dataclass(frozen=True)
class ConstraintNode:
    node_id:str; kind:NodeKind; state:NodeState; hard:bool; verified:bool; revoked:bool
    binding:str; policy_id:str; policy_version:str; authority_epoch:str
    valid_from:int; expires_at:int; risk:int=0; cycle_resolved:bool=False; label:str=""
@dataclass(frozen=True)
class ConstraintEdge:
    edge_id:str; source:str; target:str; kind:EdgeKind; hard:bool; verified:bool; revoked:bool; binding:str
@dataclass(frozen=True)
class ConstraintGraph:
    graph_id:str; schema_version:str; binding:str; complete:bool
    nodes:tuple[ConstraintNode,...]; edges:tuple[ConstraintEdge,...]
@dataclass(frozen=True)
class ReasonerPolicy:
    policy_id:str; version:str; authority_epoch:str; valid_from:int; expires_at:int; revoked:bool
    schema_version:str; max_request_age_seconds:int; max_nodes:int; max_edges:int
    high_risk_requires_approval:bool; approval_role:str
@dataclass(frozen=True)
class ReasonerRequest:
    request_id:str; actor_node_id:str; goal_node_id:str; action_node_id:str; target_node_id:str; scope_node_id:str
    expected_policy_id:str; expected_policy_version:str; expected_authority_epoch:str; graph_binding:str
    created_at:int; expires_at:int; high_risk:bool=False
@dataclass(frozen=True)
class PreparedGraphState:
    graph:ConstraintGraph; policy_fingerprint:str; graph_fingerprint:str; registry_fingerprint:str
    node_fingerprints:tuple[tuple[str,str],...]; edge_fingerprints:tuple[tuple[str,str],...]
    adjacency:tuple[tuple[str,tuple[tuple[str,str],...]],...]; dependency_sccs:tuple[tuple[str,...],...]
    generated_at:int
@dataclass(frozen=True)
class GraphDelta:
    base_fingerprint:str; target_fingerprint:str
    scalar_changes:tuple[tuple[str,Any],...]
    changed_nodes:tuple[ConstraintNode,...]; removed_node_ids:tuple[str,...]; added_nodes:tuple[ConstraintNode,...]
    changed_edges:tuple[ConstraintEdge,...]; removed_edge_ids:tuple[str,...]; added_edges:tuple[ConstraintEdge,...]
@dataclass(frozen=True)
class GraphSyncPlan:
    graph_fingerprint:str; missing_or_changed_node_ids:tuple[str,...]; missing_or_changed_edge_ids:tuple[str,...]
    metadata_bytes_required:int; full_bytes:int; full_resend_required:bool
    permission_granted:bool=False; action_execution_authorized:bool=False; graph_truth_authorized:bool=False; action_success_authorized:bool=False
@dataclass(frozen=True)
class ReasonerResult:
    decision:Decision; reasons:tuple[str,...]; violations:tuple[str,...]; unsatisfied:tuple[str,...]
    conflict_set:tuple[str,...]; candidate_path:tuple[str,...]; unresolved_cycles:tuple[tuple[str,...],...]
    approval_required:bool; graph_complete_candidate:bool; next_gate_candidate:bool
    permission_granted:bool=False; action_executed:bool=False; commit_performed:bool=False
    approval_executed:bool=False; constraint_truth_proven:bool=False; graph_truth_proven:bool=False
    world_fact_proven:bool=False; safety_proven:bool=False; action_success:bool=False

def _norm(v:Any)->Any:
    if isinstance(v,Enum): return v.value
    if is_dataclass(v): return {k:_norm(x) for k,x in asdict(v).items()}
    if isinstance(v,dict): return {str(k):_norm(v[k]) for k in sorted(v,key=lambda x:str(x))}
    if isinstance(v,(tuple,list,set,frozenset)): return [_norm(x) for x in (sorted(v,key=lambda x:str(x)) if isinstance(v,(set,frozenset)) else v)]
    return v

def canonical_json(v:Any)->str: return json.dumps(_norm(v),sort_keys=True,separators=(",",":"),ensure_ascii=False)
def fingerprint(v:Any)->str: return sha256(canonical_json(v).encode()).hexdigest()

def graph_fingerprint(g:ConstraintGraph)->str:
    return fingerprint({"graph_id":g.graph_id,"schema_version":g.schema_version,"binding":g.binding,"complete":g.complete,"nodes":tuple(sorted(g.nodes,key=lambda x:x.node_id)),"edges":tuple(sorted(g.edges,key=lambda x:x.edge_id))})

def _maps(g:ConstraintGraph):
    return {n.node_id:n for n in g.nodes},{e.edge_id:e for e in g.edges}

def _adjacency(g:ConstraintGraph)->dict[str,list[tuple[str,EdgeKind]]]:
    a={n.node_id:[] for n in g.nodes}
    for e in g.edges: a.setdefault(e.source,[]).append((e.target,e.kind))
    for k in a: a[k].sort(key=lambda x:(x[0],x[1].value))
    return a

def _dependency_sccs(g:ConstraintGraph)->tuple[tuple[str,...],...]:
    # Tarjan over dependency edges only.
    adj={n.node_id:[] for n in g.nodes}
    self_loops=set()
    for e in g.edges:
        if e.kind in (EdgeKind.REQUIRES,EdgeKind.IMPLIES):
            adj.setdefault(e.source,[]).append(e.target)
            if e.source==e.target: self_loops.add(e.source)
    index=0; stack=[]; on=set(); idx={}; low={}; out=[]
    def strong(v):
        nonlocal index
        idx[v]=low[v]=index; index+=1; stack.append(v); on.add(v)
        for w in adj.get(v,()):
            if w not in idx: strong(w); low[v]=min(low[v],low[w])
            elif w in on: low[v]=min(low[v],idx[w])
        if low[v]==idx[v]:
            comp=[]
            while True:
                w=stack.pop(); on.remove(w); comp.append(w)
                if w==v: break
            if len(comp)>1 or v in self_loops: out.append(tuple(sorted(comp)))
    for v in sorted(adj):
        if v not in idx: strong(v)
    return tuple(sorted(out))

def _path(adjacency:Mapping[str,Sequence[tuple[str,EdgeKind]]], start:str, goal:str)->tuple[str,...]:
    allowed={EdgeKind.ALLOWS,EdgeKind.IMPLIES}
    q=[start]; prev={start:None}
    for v in q:
        if v==goal: break
        for w,k in adjacency.get(v,()):
            if k in allowed and w not in prev: prev[w]=v; q.append(w)
    if goal not in prev: return ()
    p=[]; cur=goal
    while cur is not None: p.append(cur); cur=prev[cur]
    return tuple(reversed(p))

def _hold(reason:str,*extra:str)->ReasonerResult:
    return ReasonerResult(Decision.HOLD,(reason,)+tuple(extra),(),(),(),(),(),False,False,False)

def prepare_graph(policy:ReasonerPolicy,g:ConstraintGraph,*,now:int)->PreparedGraphState:
    nm,em=_maps(g); adj=_adjacency(g); scc=_dependency_sccs(g)
    nf=tuple(sorted((k,fingerprint(v)) for k,v in nm.items())); ef=tuple(sorted((k,fingerprint(v)) for k,v in em.items()))
    reg=fingerprint({"nodes":nf,"edges":ef,"graph":graph_fingerprint(g)})
    return PreparedGraphState(g,fingerprint(policy),graph_fingerprint(g),reg,nf,ef,tuple(sorted((k,tuple((w,t.value) for w,t in v)) for k,v in adj.items())),scc,now)

def _evaluate(req:ReasonerRequest,p:ReasonerPolicy,g:ConstraintGraph,adj:Mapping[str,Sequence[tuple[str,EdgeKind]]],sccs:Sequence[tuple[str,...]],*,now:int)->ReasonerResult:
    if p.revoked or not (p.valid_from<=now<=p.expires_at): return _hold("POLICY_INACTIVE")
    if (req.expected_policy_id,req.expected_policy_version,req.expected_authority_epoch)!=(p.policy_id,p.version,p.authority_epoch): return _hold("POLICY_OR_AUTHORITY_MISMATCH")
    if req.expires_at<now or req.created_at>now or now-req.created_at>p.max_request_age_seconds: return _hold("REQUEST_STALE_OR_EXPIRED")
    if g.schema_version!=p.schema_version: return _hold("SCHEMA_VERSION_MISMATCH")
    if g.binding!=req.graph_binding: return _hold("GRAPH_BINDING_MISMATCH")
    if not g.complete: return _hold("GRAPH_INCOMPLETE")
    if len(g.nodes)>p.max_nodes or len(g.edges)>p.max_edges: return _hold("GRAPH_LIMIT_EXCEEDED")
    if len({n.node_id for n in g.nodes})!=len(g.nodes) or len({e.edge_id for e in g.edges})!=len(g.edges): return _hold("DUPLICATE_GRAPH_ID")
    nm={n.node_id:n for n in g.nodes}
    required=((req.actor_node_id,NodeKind.ACTOR),(req.goal_node_id,NodeKind.GOAL),(req.action_node_id,NodeKind.ACTION),(req.target_node_id,NodeKind.TARGET),(req.scope_node_id,NodeKind.SCOPE))
    for nid,kind in required:
        if nid not in nm or nm[nid].kind is not kind: return _hold("REQUIRED_NODE_MISSING_OR_WRONG_KIND",nid)
    for n in g.nodes:
        if not isinstance(n.kind,NodeKind) or not isinstance(n.state,NodeState): return _hold("UNKNOWN_CONSTRAINT_TYPE",n.node_id)
        if not n.verified or n.revoked: return _hold("NODE_EVIDENCE_INVALID",n.node_id)
        if n.binding!=g.binding: return _hold("NODE_BINDING_MISMATCH",n.node_id)
        if (n.policy_id,n.policy_version,n.authority_epoch)!=(p.policy_id,p.version,p.authority_epoch): return _hold("NODE_POLICY_OR_AUTHORITY_MISMATCH",n.node_id)
        if not (n.valid_from<=now<=n.expires_at): return _hold("NODE_STALE_OR_EXPIRED",n.node_id)
    for e in g.edges:
        if not isinstance(e.kind,EdgeKind): return _hold("UNKNOWN_EDGE_TYPE",e.edge_id)
        if e.source not in nm or e.target not in nm: return _hold("EDGE_ENDPOINT_MISSING",e.edge_id)
        if not e.verified or e.revoked or e.binding!=g.binding: return _hold("EDGE_EVIDENCE_INVALID",e.edge_id)
    # Unresolved dependency cycles fail closed.
    unresolved=[]
    for comp in sccs:
        if not all(nm[x].state is NodeState.SATISFIED and nm[x].cycle_resolved for x in comp): unresolved.append(tuple(comp))
    if unresolved:
        return ReasonerResult(Decision.HOLD,("UNRESOLVED_DEPENDENCY_CYCLE",),(),(),(),(),tuple(unresolved),False,False,False)
    violations=[]; unsat=[]; conflicts=[]; approval_needed=False
    # Direct hard scope/authority/constraint failures.
    if nm[req.scope_node_id].state is not NodeState.SATISFIED: violations.append(req.scope_node_id)
    for n in g.nodes:
        if n.kind is NodeKind.AUTHORITY and n.state is NodeState.UNSATISFIED: violations.append(n.node_id)
        if n.kind is NodeKind.CONSTRAINT and n.hard and n.state is NodeState.UNSATISFIED: violations.append(n.node_id)
    if violations:
        return ReasonerResult(Decision.DENY,("HARD_CONSTRAINT_OR_SCOPE_VIOLATION",),tuple(sorted(set(violations))),(),(),(),(),False,False,False)
    for e in g.edges:
        s=nm[e.source]; t=nm[e.target]
        active=s.state is NodeState.SATISFIED
        if e.kind is EdgeKind.FORBIDS and active and t.state is NodeState.SATISFIED:
            violations.append(e.edge_id); conflicts.extend((e.source,e.target))
        elif e.kind is EdgeKind.CONFLICTS and active and t.state is NodeState.SATISFIED:
            violations.append(e.edge_id); conflicts.extend((e.source,e.target))
        elif e.kind in (EdgeKind.REQUIRES,EdgeKind.IMPLIES) and active and t.state is not NodeState.SATISFIED:
            unsat.append(t.node_id)
        elif e.kind is EdgeKind.APPROVAL_REQUIRED and active and t.state is not NodeState.SATISFIED:
            approval_needed=True; unsat.append(t.node_id)
    if violations:
        return ReasonerResult(Decision.DENY,("CONSTRAINT_CONFLICT",),tuple(sorted(set(violations))),(),tuple(sorted(set(conflicts))),(),(),False,False,False)
    if unsat and not approval_needed:
        return ReasonerResult(Decision.HOLD,("REQUIRED_NODE_UNSATISFIED",),(),tuple(sorted(set(unsat))),(),(),(),False,False,False)
    if approval_needed or (req.high_risk and p.high_risk_requires_approval and not any(n.kind is NodeKind.APPROVAL and n.state is NodeState.SATISFIED for n in g.nodes)):
        return ReasonerResult(Decision.HUMAN_APPROVAL,("HUMAN_APPROVAL_REQUIRED",),(),tuple(sorted(set(unsat))),(),(),(),True,True,False)
    path=_path(adj,req.action_node_id,req.goal_node_id)
    if not path: return ReasonerResult(Decision.HOLD,("NO_ALLOWABLE_PATH_TO_GOAL",),(),(),(),(),(),False,True,False)
    return ReasonerResult(Decision.ALLOW,("CONSTRAINT_GRAPH_SATISFIED_CANDIDATE",),(),(),(),path,(),False,True,True)

def evaluate(req:ReasonerRequest,p:ReasonerPolicy,g:ConstraintGraph,*,now:int)->ReasonerResult:
    return _evaluate(req,p,g,_adjacency(g),_dependency_sccs(g),now=now)

def validate_prepared_state(prepared:PreparedGraphState)->bool:
    # Full integrity validation is intentionally explicit and performed once when a prepared
    # state is materialized/received. Repeating it for every evaluation defeats DCSR reuse.
    if graph_fingerprint(prepared.graph)!=prepared.graph_fingerprint: return False
    nm,em=_maps(prepared.graph)
    if tuple(sorted((k,fingerprint(v)) for k,v in nm.items()))!=prepared.node_fingerprints: return False
    if tuple(sorted((k,fingerprint(v)) for k,v in em.items()))!=prepared.edge_fingerprints: return False
    adj=_adjacency(prepared.graph)
    expected_adj=tuple(sorted((k,tuple((w,t.value) for w,t in v)) for k,v in adj.items()))
    if expected_adj!=prepared.adjacency: return False
    if _dependency_sccs(prepared.graph)!=prepared.dependency_sccs: return False
    return fingerprint({"nodes":prepared.node_fingerprints,"edges":prepared.edge_fingerprints,"graph":prepared.graph_fingerprint})==prepared.registry_fingerprint

def evaluate_prepared(req:ReasonerRequest,p:ReasonerPolicy,prepared:PreparedGraphState,*,current_graph_fingerprint:str,now:int)->ReasonerResult:
    # Caller must validate the prepared state once with validate_prepared_state() at materialization.
    # Every evaluation still checks current graph identity and current policy identity.
    if prepared.policy_fingerprint!=fingerprint(p): return _hold("PREPARED_POLICY_FINGERPRINT_MISMATCH")
    if prepared.graph_fingerprint!=current_graph_fingerprint: return _hold("PREPARED_GRAPH_FINGERPRINT_MISMATCH")
    adj={k:tuple((w,EdgeKind(t)) for w,t in vals) for k,vals in prepared.adjacency}
    return _evaluate(req,p,prepared.graph,adj,prepared.dependency_sccs,now=now)

def _idmap(seq,key): return {getattr(x,key):x for x in seq}
def make_graph_delta(base:ConstraintGraph,target:ConstraintGraph)->GraphDelta:
    bn=_idmap(base.nodes,"node_id"); tn=_idmap(target.nodes,"node_id"); be=_idmap(base.edges,"edge_id"); te=_idmap(target.edges,"edge_id")
    chn=tuple(tn[k] for k in sorted(set(bn)&set(tn)) if fingerprint(bn[k])!=fingerprint(tn[k]))
    che=tuple(te[k] for k in sorted(set(be)&set(te)) if fingerprint(be[k])!=fingerprint(te[k]))
    rmn=tuple(sorted(set(bn)-set(tn))); rme=tuple(sorted(set(be)-set(te)))
    adn=tuple(tn[k] for k in sorted(set(tn)-set(bn))); ade=tuple(te[k] for k in sorted(set(te)-set(be)))
    scal=[]
    for k in ("graph_id","schema_version","binding","complete"):
        if getattr(base,k)!=getattr(target,k): scal.append((k,getattr(target,k)))
    return GraphDelta(graph_fingerprint(base),graph_fingerprint(target),tuple(scal),chn,rmn,adn,che,rme,ade)

def apply_graph_delta(base:ConstraintGraph,d:GraphDelta)->ConstraintGraph:
    if graph_fingerprint(base)!=d.base_fingerprint: raise ValueError("DELTA_WRONG_BASE")
    nm=_idmap(base.nodes,"node_id"); em=_idmap(base.edges,"edge_id")
    for k in d.removed_node_ids: nm.pop(k,None)
    for k in d.removed_edge_ids: em.pop(k,None)
    for x in d.changed_nodes:
        if x.node_id not in nm: raise ValueError("DELTA_CHANGED_NODE_MISSING_BASE")
        nm[x.node_id]=x
    for x in d.changed_edges:
        if x.edge_id not in em: raise ValueError("DELTA_CHANGED_EDGE_MISSING_BASE")
        em[x.edge_id]=x
    for x in d.added_nodes:
        if x.node_id in nm: raise ValueError("DELTA_ADDED_NODE_COLLISION")
        nm[x.node_id]=x
    for x in d.added_edges:
        if x.edge_id in em: raise ValueError("DELTA_ADDED_EDGE_COLLISION")
        em[x.edge_id]=x
    vals={"graph_id":base.graph_id,"schema_version":base.schema_version,"binding":base.binding,"complete":base.complete}
    for k,v in d.scalar_changes:
        if k not in vals: raise ValueError("DELTA_UNKNOWN_SCALAR")
        vals[k]=v
    out=ConstraintGraph(vals["graph_id"],vals["schema_version"],vals["binding"],bool(vals["complete"]),tuple(nm[k] for k in sorted(nm)),tuple(em[k] for k in sorted(em)))
    if graph_fingerprint(out)!=d.target_fingerprint: raise ValueError("DELTA_TARGET_FINGERPRINT_MISMATCH")
    return out

def plan_graph_sync(g:ConstraintGraph,remote_node_fingerprints:Mapping[str,str]|Sequence[tuple[str,str]],remote_edge_fingerprints:Mapping[str,str]|Sequence[tuple[str,str]])->GraphSyncPlan:
    ln={n.node_id:fingerprint(n) for n in g.nodes}; le={e.edge_id:fingerprint(e) for e in g.edges}; rn=dict(remote_node_fingerprints); re=dict(remote_edge_fingerprints)
    mn=tuple(sorted(k for k,v in ln.items() if rn.get(k)!=v)); me=tuple(sorted(k for k,v in le.items() if re.get(k)!=v))
    nm=_idmap(g.nodes,"node_id"); em=_idmap(g.edges,"edge_id")
    payload={"nodes":tuple(nm[k] for k in mn),"edges":tuple(em[k] for k in me)}; full={"nodes":g.nodes,"edges":g.edges}
    mb=len(canonical_json(payload).encode()); fb=len(canonical_json(full).encode())
    return GraphSyncPlan(graph_fingerprint(g),mn,me,mb,fb,bool(fb and mb/fb>=.80))

def default_policy(now:int)->ReasonerPolicy:
    return ReasonerPolicy("POL-062","2.0.0","AE-062-A",now-3600,now+86400,False,"CGR-2",600,10000,20000,True,"OWNER")

def _node(nid,kind,state,p,now,binding="BIND-062",hard=False,risk=0,cycle_resolved=False,label=""):
    return ConstraintNode(nid,kind,state,hard,True,False,binding,p.policy_id,p.version,p.authority_epoch,now-60,now+3600,risk,cycle_resolved,label)
def _edge(eid,s,t,k,binding="BIND-062",hard=False): return ConstraintEdge(eid,s,t,k,hard,True,False,binding)

def default_graph(now:int,p:ReasonerPolicy|None=None)->ConstraintGraph:
    p=p or default_policy(now)
    ns=(
      _node("ACTOR",NodeKind.ACTOR,NodeState.SATISFIED,p,now),
      _node("ACTION",NodeKind.ACTION,NodeState.SATISFIED,p,now),
      _node("TARGET",NodeKind.TARGET,NodeState.SATISFIED,p,now),
      _node("GOAL",NodeKind.GOAL,NodeState.SATISFIED,p,now),
      _node("SCOPE",NodeKind.SCOPE,NodeState.SATISFIED,p,now,hard=True),
      _node("AUTH",NodeKind.AUTHORITY,NodeState.SATISFIED,p,now,hard=True),
      _node("PRE",NodeKind.PRECONDITION,NodeState.SATISFIED,p,now),
      _node("SAFE",NodeKind.CONSTRAINT,NodeState.SATISFIED,p,now,hard=True),
    )
    es=(
      _edge("E1","ACTION","PRE",EdgeKind.REQUIRES),
      _edge("E2","ACTION","AUTH",EdgeKind.REQUIRES),
      _edge("E3","ACTION","SCOPE",EdgeKind.REQUIRES),
      _edge("E4","ACTION","TARGET",EdgeKind.ALLOWS),
      _edge("E5","TARGET","GOAL",EdgeKind.ALLOWS),
      _edge("E6","AUTH","SCOPE",EdgeKind.ALLOWS),
    )
    return ConstraintGraph("GRAPH-062","CGR-2","BIND-062",True,ns,es)

def default_request(now:int,p:ReasonerPolicy|None=None)->ReasonerRequest:
    p=p or default_policy(now)
    return ReasonerRequest("REQ-062","ACTOR","GOAL","ACTION","TARGET","SCOPE",p.policy_id,p.version,p.authority_epoch,"BIND-062",now-5,now+300,False)
