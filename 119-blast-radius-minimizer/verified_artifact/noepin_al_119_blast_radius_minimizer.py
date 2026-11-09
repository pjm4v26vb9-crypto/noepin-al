"""NOEPIN AL 119 — Blast-Radius Minimizer — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-119
DCSR: AUXILIARY INTEGRATION / 補助統合.

Selects the least-impact candidate that satisfies the supplied goal constraint by expanding
resource dependencies and weighting shared, critical, and authority-boundary resources.
Selected actions and affected sets are candidates/evidence only: no permission or execution.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str,Enum): ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class NextAction(str,Enum):
    BLAST_RADIUS_MINIMIZED_CANDIDATE='BLAST_RADIUS_MINIMIZED_CANDIDATE'
    HUMAN_APPROVAL_LARGE_RADIUS_CANDIDATE='HUMAN_APPROVAL_LARGE_RADIUS_CANDIDATE'
    HOLD_RADIUS_REASSESSMENT_CANDIDATE='HOLD_RADIUS_REASSESSMENT_CANDIDATE'
class Escalation(str,Enum):
    NONE='NONE'; UNKNOWN_RADIUS='UNKNOWN_RADIUS'; ALL_CANDIDATES_LARGE_RADIUS='ALL_CANDIDATES_LARGE_RADIUS'; NO_GOAL_SATISFYING_ACTION='NO_GOAL_SATISFYING_ACTION'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'

@dataclass(frozen=True)
class ResourceNode:
    resource_id:str
    criticality:float
    shared:bool
    authority_boundary:bool
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class DependencyEdge:
    source_resource_id:str
    target_resource_id:str

@dataclass(frozen=True)
class CandidateAction:
    action_id:str
    directly_affected_resources:tuple[str,...]
    goal_coverage:float
    high_risk:bool
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class BlastPolicy:
    minimum_goal_coverage:float
    shared_resource_multiplier:float
    authority_boundary_multiplier:float
    dependency_resource_multiplier:float
    high_radius_threshold:float
    max_dependency_nodes:int

@dataclass(frozen=True)
class BlastRequest:
    request_id:str
    candidates:tuple[CandidateAction,...]
    resources:tuple[ResourceNode,...]
    dependency_graph:tuple[DependencyEdge,...]
    goal_id:str
    policy:BlastPolicy
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class ActionBlastEvaluation:
    action_id:str
    blast_radius_score:float|None
    affected_set:tuple[str,...]
    direct_set:tuple[str,...]
    goal_satisfied:bool
    radius_known:bool
    critical_shared_count:int
    authority_boundary_count:int
    high_risk:bool

@dataclass(frozen=True)
class BlastResult:
    decision:Decision
    next_action:NextAction
    escalation:Escalation
    reasons:tuple[str,...]
    selected_action_candidate:str|None
    blast_radius_score:float|None
    affected_set:tuple[str,...]
    evaluations:tuple[ActionBlastEvaluation,...]
    unknown_radius_candidates:tuple[str,...]
    all_goal_candidates_large_radius:bool
    next_gate_candidate:bool
    selected_action_promoted_to_permission:bool=False
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
class PreparedBlastState:
    request:BlastRequest
    result:BlastResult
    context_fingerprint:str
    candidate_fingerprint:str
    resource_fingerprint:str
    dependency_fingerprint:str
    policy_fingerprint:str
    selection_fingerprint:str
    integrity_fingerprint:str
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class BlastDelta:
    changed_candidates:tuple[CandidateAction,...]
    removed_candidate_ids:tuple[str,...]
    changed_resources:tuple[ResourceNode,...]
    removed_resource_ids:tuple[str,...]
    changed_edges:tuple[DependencyEdge,...]
    from_registry_fingerprint:str
    to_registry_fingerprint:str

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

def _canon(v)->bytes: return json.dumps(_obj(v),ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def _fp(v)->str: return sha256(_canon(v)).hexdigest()
def _finite(x): return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(float(x))

def default_policy(): return BlastPolicy(.90,1.75,2.0,1.10,12.0,5000)

def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    resources=(
      ResourceNode('FILE_A',1.0,False,False,b,e),
      ResourceNode('FILE_B',1.0,False,False,b,e),
      ResourceNode('SHARED_CONFIG',4.0,True,True,b,e),
      ResourceNode('SERVICE_A',2.0,False,False,b,e),
      ResourceNode('SERVICE_B',2.0,False,False,b,e),
      ResourceNode('GLOBAL_DB',5.0,True,True,b,e),
    )
    edges=(
      DependencyEdge('SHARED_CONFIG','SERVICE_A'),
      DependencyEdge('SHARED_CONFIG','SERVICE_B'),
      DependencyEdge('GLOBAL_DB','SERVICE_A'),
      DependencyEdge('GLOBAL_DB','SERVICE_B'),
    )
    candidates=(
      CandidateAction('LOCAL_PATCH',('FILE_A',),1.0,False,b,e),
      CandidateAction('SHARED_CONFIG_CHANGE',('SHARED_CONFIG',),1.0,True,b,e),
      CandidateAction('GLOBAL_DB_CHANGE',('GLOBAL_DB',),1.0,True,b,e),
      CandidateAction('INSUFFICIENT_GOAL',('FILE_B',),.4,False,b,e),
    )
    return BlastRequest('DEFAULT-119',candidates,resources,edges,'GOAL-1',default_policy(),b,e)

def _invalid(req,reason):
    return BlastResult(Decision.HOLD,NextAction.HOLD_RADIUS_REASSESSMENT_CANDIDATE,Escalation.INVALID_CONFIGURATION,(reason,),None,None,(),(),(),False,False)

def _registry_fp(req):
    return _fp((req.candidates,req.resources,req.dependency_graph,req.binding,req.state_epoch))

def _evaluate_action(a:CandidateAction, req:BlastRequest, resource_map, adjacency)->ActionBlastEvaluation:
    p=req.policy
    goal_ok=float(a.goal_coverage)>=float(p.minimum_goal_coverage)
    direct=tuple(sorted(set(a.directly_affected_resources)))
    if not direct:
        return ActionBlastEvaluation(a.action_id,None,(),direct,goal_ok,False,0,0,a.high_risk)
    # Every referenced resource and traversed dependency must be typed and known.
    if any(x not in resource_map for x in direct):
        return ActionBlastEvaluation(a.action_id,None,(),direct,goal_ok,False,0,0,a.high_risk)
    seen=set(); stack=list(reversed(direct)); depth={x:0 for x in direct}
    while stack:
        x=stack.pop()
        if x in seen: continue
        if x not in resource_map:
            return ActionBlastEvaluation(a.action_id,None,tuple(sorted(seen)),direct,goal_ok,False,0,0,a.high_risk)
        seen.add(x)
        if len(seen)>p.max_dependency_nodes:
            return ActionBlastEvaluation(a.action_id,None,tuple(sorted(seen)),direct,goal_ok,False,0,0,a.high_risk)
        for y in sorted(adjacency.get(x,())):
            if y not in resource_map:
                return ActionBlastEvaluation(a.action_id,None,tuple(sorted(seen)),direct,goal_ok,False,0,0,a.high_risk)
            if y not in depth: depth[y]=depth.get(x,0)+1
            if y not in seen: stack.append(y)
    score=0.0; cshared=0; abound=0
    for rid in sorted(seen):
        r=resource_map[rid]; w=float(r.criticality)
        if r.shared: w*=float(p.shared_resource_multiplier)
        if r.authority_boundary: w*=float(p.authority_boundary_multiplier)
        if rid not in direct: w*=float(p.dependency_resource_multiplier)
        score+=w
        if r.shared and r.criticality>=3: cshared+=1
        if r.authority_boundary: abound+=1
    return ActionBlastEvaluation(a.action_id,round(score,12),tuple(sorted(seen)),direct,goal_ok,True,cshared,abound,a.high_risk)

def evaluate(req:BlastRequest)->BlastResult:
    p=req.policy
    if not req.request_id or not req.goal_id or not req.binding or not req.state_epoch: return _invalid(req,'INVALID_REQUEST_IDENTITY')
    nums=(p.minimum_goal_coverage,p.shared_resource_multiplier,p.authority_boundary_multiplier,p.dependency_resource_multiplier,p.high_radius_threshold)
    if not all(_finite(x) for x in nums): return _invalid(req,'POLICY_NONFINITE')
    if not 0<=p.minimum_goal_coverage<=1 or min(p.shared_resource_multiplier,p.authority_boundary_multiplier,p.dependency_resource_multiplier)<=0 or p.high_radius_threshold<0 or not isinstance(p.max_dependency_nodes,int) or p.max_dependency_nodes<1: return _invalid(req,'POLICY_RANGE_INVALID')
    if not req.candidates or not req.resources: return _invalid(req,'EMPTY_CANDIDATE_OR_RESOURCE_SET')
    aids=[a.action_id for a in req.candidates]; rids=[r.resource_id for r in req.resources]
    if len(set(aids))!=len(aids): return _invalid(req,'DUPLICATE_ACTION_ID')
    if len(set(rids))!=len(rids): return _invalid(req,'DUPLICATE_RESOURCE_ID')
    for a in req.candidates:
        if not a.action_id or a.binding!=req.binding or a.state_epoch!=req.state_epoch or not _finite(a.goal_coverage) or not 0<=float(a.goal_coverage)<=1: return _invalid(req,'ACTION_INVALID')
    for r in req.resources:
        if not r.resource_id or r.binding!=req.binding or r.state_epoch!=req.state_epoch or not _finite(r.criticality) or float(r.criticality)<0: return _invalid(req,'RESOURCE_INVALID')
    for ed in req.dependency_graph:
        if not ed.source_resource_id or not ed.target_resource_id: return _invalid(req,'DEPENDENCY_EDGE_INVALID')
    resource_map={r.resource_id:r for r in req.resources}; adjacency={}
    for ed in req.dependency_graph: adjacency.setdefault(ed.source_resource_id,set()).add(ed.target_resource_id)
    evaluations=tuple(sorted((_evaluate_action(a,req,resource_map,adjacency) for a in req.candidates),key=lambda x:x.action_id))
    goal_evals=[x for x in evaluations if x.goal_satisfied]
    if not goal_evals:
        return BlastResult(Decision.HOLD,NextAction.HOLD_RADIUS_REASSESSMENT_CANDIDATE,Escalation.NO_GOAL_SATISFYING_ACTION,('NO_GOAL_SATISFYING_ACTION','NO_AUTOMATIC_CONTINUE'),None,None,(),evaluations,(),False,False)
    unknown=tuple(sorted(x.action_id for x in goal_evals if not x.radius_known))
    known=[x for x in goal_evals if x.radius_known]
    if not known:
        return BlastResult(Decision.HOLD,NextAction.HOLD_RADIUS_REASSESSMENT_CANDIDATE,Escalation.UNKNOWN_RADIUS,('BLAST_RADIUS_UNKNOWN','NO_AUTOMATIC_CONTINUE'),None,None,(),evaluations,unknown,False,False)
    # Deterministic minimum: weighted blast score, affected set size, critical shared count, authority boundary count, action id.
    known.sort(key=lambda x:(float(x.blast_radius_score),len(x.affected_set),x.critical_shared_count,x.authority_boundary_count,x.action_id))
    selected=known[0]
    all_large=all(float(x.blast_radius_score)>float(p.high_radius_threshold) for x in known)
    reasons=['DEPENDENCIES_EXPANDED','CRITICAL_SHARED_AND_AUTHORITY_BOUNDARIES_WEIGHTED','MINIMUM_KNOWN_BLAST_RADIUS_SELECTED','SELECTED_ACTION_IS_CANDIDATE_ONLY']
    if unknown: reasons.append('UNKNOWN_RADIUS_CANDIDATES_EXCLUDED')
    if all_large:
        reasons.append('ALL_GOAL_SATISFYING_KNOWN_CANDIDATES_EXCEED_RADIUS_THRESHOLD')
        return BlastResult(Decision.HUMAN_APPROVAL,NextAction.HUMAN_APPROVAL_LARGE_RADIUS_CANDIDATE,Escalation.ALL_CANDIDATES_LARGE_RADIUS,tuple(reasons),selected.action_id,selected.blast_radius_score,selected.affected_set,evaluations,unknown,True,False)
    return BlastResult(Decision.ALLOW,NextAction.BLAST_RADIUS_MINIMIZED_CANDIDATE,Escalation.UNKNOWN_RADIUS if unknown else Escalation.NONE,tuple(reasons),selected.action_id,selected.blast_radius_score,selected.affected_set,evaluations,unknown,False,True)

def default_evaluation(): return evaluate(default_request())

def prepare_state(req:BlastRequest,*,binding:str,state_epoch:str)->PreparedBlastState:
    if binding!=req.binding or state_epoch!=req.state_epoch: raise ValueError('binding/state_epoch mismatch')
    res=evaluate(req); context=_fp((req.request_id,req.goal_id,binding,state_epoch)); cfp=_fp(req.candidates); rfp=_fp(req.resources); dfp=_fp(req.dependency_graph); pfp=_fp(req.policy); sfp=_fp(res); integ=_fp((context,cfp,rfp,dfp,pfp,sfp,binding,state_epoch))
    return PreparedBlastState(req,res,context,cfp,rfp,dfp,pfp,sfp,integ,binding,state_epoch)

def validate_prepared_integrity(st): return st.integrity_fingerprint==_fp((st.context_fingerprint,st.candidate_fingerprint,st.resource_fingerprint,st.dependency_fingerprint,st.policy_fingerprint,st.selection_fingerprint,st.binding,st.state_epoch))

def evaluate_prepared(st,*,integrity_validated,current_context_fingerprint,current_candidate_fingerprint,current_resource_fingerprint,current_dependency_fingerprint,current_policy_fingerprint,current_selection_fingerprint):
    if not integrity_validated or not validate_prepared_integrity(st): return _invalid(st.request,'PREPARED_INTEGRITY_NOT_VALIDATED')
    if (current_context_fingerprint,current_candidate_fingerprint,current_resource_fingerprint,current_dependency_fingerprint,current_policy_fingerprint,current_selection_fingerprint)!=(st.context_fingerprint,st.candidate_fingerprint,st.resource_fingerprint,st.dependency_fingerprint,st.policy_fingerprint,st.selection_fingerprint): return _invalid(st.request,'PREPARED_FINGERPRINT_MISMATCH')
    return st.result

def make_delta(old,new):
    oa={x.action_id:x for x in old.request.candidates}; na={x.action_id:x for x in new.request.candidates}
    orr={x.resource_id:x for x in old.request.resources}; nrr={x.resource_id:x for x in new.request.resources}
    changed_a=tuple(na[k] for k in sorted(na) if k not in oa or _fp(na[k])!=_fp(oa[k])); removed_a=tuple(k for k in sorted(oa) if k not in na)
    changed_r=tuple(nrr[k] for k in sorted(nrr) if k not in orr or _fp(nrr[k])!=_fp(orr[k])); removed_r=tuple(k for k in sorted(orr) if k not in nrr)
    oe={_fp(x):x for x in old.request.dependency_graph}; ne={_fp(x):x for x in new.request.dependency_graph}; changed_e=tuple(ne[k] for k in sorted(ne) if k not in oe)
    return BlastDelta(changed_a,removed_a,changed_r,removed_r,changed_e,_registry_fp(old.request),_registry_fp(new.request))

def plan_missing_only(old,new):
    d=make_delta(old,new); ids=tuple([f'ACTION:{x.action_id}' for x in d.changed_candidates]+[f'REMOVED_ACTION:{x}' for x in d.removed_candidate_ids]+[f'RESOURCE:{x.resource_id}' for x in d.changed_resources]+[f'REMOVED_RESOURCE:{x}' for x in d.removed_resource_ids]+[f'EDGE:{x.source_resource_id}->{x.target_resource_id}' for x in d.changed_edges]); meta=len(_canon({'from':d.from_registry_fingerprint,'to':d.to_registry_fingerprint,'ids':ids})); return MissingOnlyPlan(ids,meta,False)
