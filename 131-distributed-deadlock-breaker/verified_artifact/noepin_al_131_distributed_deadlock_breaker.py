"""NOEPIN AL 131 — Distributed Deadlock Breaker — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-131
DCSR: DIRECT INTEGRATION / 直接統合.

Deadlock cycles, victim choices and release/retry plans are control candidates/audit evidence only.
They do not grant permission, authority, release, retry, execution, safety proof, truth, or action success.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str, Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class DeadlockState(str, Enum):
    NO_CYCLE='NO_CYCLE'; BREAK_CANDIDATE='BREAK_CANDIDATE'; HUMAN_REQUIRED='HUMAN_REQUIRED'; REDESIGN_REQUIRED='REDESIGN_REQUIRED'; INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_CANDIDATE='CONTINUE_CANDIDATE'; RELEASE_RETRY_CANDIDATE='RELEASE_RETRY_CANDIDATE'; HUMAN_REVIEW_CANDIDATE='HUMAN_REVIEW_CANDIDATE'; PLAN_REDESIGN_CANDIDATE='PLAN_REDESIGN_CANDIDATE'; HOLD_DEADLOCK_CANDIDATE='HOLD_DEADLOCK_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; CRITICAL_LOCK='CRITICAL_LOCK'; SAFETY_INVARIANT_RISK='SAFETY_INVARIANT_RISK'; REPEATED_DEADLOCK='REPEATED_DEADLOCK'; NO_SAFE_VICTIM='NO_SAFE_VICTIM'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'
class Risk(str, Enum): LOW='LOW'; MEDIUM='MEDIUM'; HIGH='HIGH'; CRITICAL='CRITICAL'

@dataclass(frozen=True)
class WaitEdge:
    waiter_agent_id:str
    holder_agent_id:str
    resource_id:str
    wait_kind:str
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class ResourceLock:
    resource_id:str
    owner_agent_id:str
    critical:bool
    safe_release:bool
    rollback_cost:float
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class AgentPriority:
    agent_id:str
    priority:int
    risk:float
    rollback_cost:float
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class DeadlockPolicy:
    repeated_deadlock_threshold:int=3
    max_auto_risk:float=.55
    max_auto_rollback_cost:float=.65
    critical_lock_requires_human:bool=True

@dataclass(frozen=True)
class DeadlockRequest:
    request_id:str
    wait_edges:tuple[WaitEdge,...]
    locks:tuple[ResourceLock,...]
    priorities:tuple[AgentPriority,...]
    occurrence_count:int
    policy:DeadlockPolicy
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class CycleTrace:
    agent_ids:tuple[str,...]
    resource_ids:tuple[str,...]

@dataclass(frozen=True)
class VictimEvaluation:
    agent_id:str
    eligible:bool
    priority:int
    risk:float
    rollback_cost:float
    owned_cycle_resources:tuple[str,...]
    reason_codes:tuple[str,...]

@dataclass(frozen=True)
class DeadlockResult:
    decision:Decision
    next_action:NextAction
    escalation:Escalation
    deadlock_state:DeadlockState
    reasons:tuple[str,...]
    cycles:tuple[CycleTrace,...]
    victim_agent_id:str|None
    release_resource_ids:tuple[str,...]
    retry_agent_ids:tuple[str,...]
    evaluations:tuple[VictimEvaluation,...]
    next_gate_candidate:bool
    cycle_promoted_to_truth:bool=False
    victim_promoted_to_permission:bool=False
    release_plan_executed:bool=False
    retry_executed:bool=False
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
class PreparedDeadlockState:
    request:DeadlockRequest
    result:DeadlockResult
    context_fingerprint:str
    wait_fingerprint:str
    lock_fingerprint:str
    policy_fingerprint:str
    outcome_fingerprint:str
    integrity_fingerprint:str
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class DeadlockDelta:
    changed_wait_edges:tuple[WaitEdge,...]
    removed_wait_edge_ids:tuple[str,...]
    changed_locks:tuple[ResourceLock,...]
    removed_lock_ids:tuple[str,...]
    changed_priorities:tuple[AgentPriority,...]
    removed_priority_ids:tuple[str,...]
    occurrence_changed:bool
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
def _edge_id(e): return f'{e.waiter_agent_id}->{e.holder_agent_id}:{e.resource_id}:{e.wait_kind}'
def _manifest_fp(req): return _fp((req.wait_edges,req.locks,req.priorities,req.occurrence_count,req.policy,req.binding,req.state_epoch))

def default_policy(): return DeadlockPolicy()

def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    edges=(
        WaitEdge('AGENT-A','AGENT-B','R-B','RESOURCE',b,e),
        WaitEdge('AGENT-B','AGENT-C','R-C','APPROVAL',b,e),
        WaitEdge('AGENT-C','AGENT-A','R-A','OUTPUT',b,e),
    )
    locks=(
        ResourceLock('R-A','AGENT-A',False,True,.45,b,e),
        ResourceLock('R-B','AGENT-B',False,True,.50,b,e),
        ResourceLock('R-C','AGENT-C',False,True,.20,b,e),
    )
    priorities=(
        AgentPriority('AGENT-A',80,.35,.45,b,e),
        AgentPriority('AGENT-B',70,.30,.50,b,e),
        AgentPriority('AGENT-C',30,.20,.20,b,e),
    )
    return DeadlockRequest('DEFAULT-131',edges,locks,priorities,1,default_policy(),b,e)

def _invalid(reason):
    return DeadlockResult(Decision.HOLD,NextAction.HOLD_DEADLOCK_CANDIDATE,Escalation.INVALID_CONFIGURATION,DeadlockState.INVALID,(reason,'NO_PERMISSION_RELEASE_RETRY_OR_EXECUTION_PROMOTION'),(),None,(),(),(),False)

def _validate(req:DeadlockRequest):
    if not req.request_id or not req.binding or not req.state_epoch: return 'INVALID_REQUEST_IDENTITY'
    if not isinstance(req.occurrence_count,int) or isinstance(req.occurrence_count,bool) or req.occurrence_count<0: return 'INVALID_OCCURRENCE_COUNT'
    p=req.policy
    if not isinstance(p.repeated_deadlock_threshold,int) or isinstance(p.repeated_deadlock_threshold,bool) or p.repeated_deadlock_threshold<1: return 'INVALID_REPEAT_THRESHOLD'
    if any(not _finite(x) for x in (p.max_auto_risk,p.max_auto_rollback_cost)): return 'INVALID_POLICY_NUMERIC'
    if not (0<=p.max_auto_risk<=1 and 0<=p.max_auto_rollback_cost<=1): return 'INVALID_POLICY_RANGE'
    edge_ids=[]
    for x in req.wait_edges:
        if not x.waiter_agent_id or not x.holder_agent_id or not x.resource_id or not x.wait_kind: return 'INVALID_WAIT_EDGE'
        if x.binding!=req.binding or x.state_epoch!=req.state_epoch: return 'WAIT_EDGE_BINDING_MISMATCH'
        edge_ids.append(_edge_id(x))
    if len(edge_ids)!=len(set(edge_ids)): return 'DUPLICATE_WAIT_EDGE'
    lock_ids=[]
    for x in req.locks:
        if not x.resource_id or not x.owner_agent_id: return 'INVALID_LOCK_IDENTITY'
        if x.binding!=req.binding or x.state_epoch!=req.state_epoch: return 'LOCK_BINDING_MISMATCH'
        if not _finite(x.rollback_cost) or not 0<=x.rollback_cost<=1: return 'INVALID_LOCK_COST'
        lock_ids.append(x.resource_id)
    if len(lock_ids)!=len(set(lock_ids)): return 'DUPLICATE_LOCK'
    pri_ids=[]
    for x in req.priorities:
        if not x.agent_id: return 'INVALID_PRIORITY_AGENT'
        if x.binding!=req.binding or x.state_epoch!=req.state_epoch: return 'PRIORITY_BINDING_MISMATCH'
        if not isinstance(x.priority,int) or isinstance(x.priority,bool): return 'INVALID_PRIORITY_VALUE'
        if not _finite(x.risk) or not _finite(x.rollback_cost) or not 0<=x.risk<=1 or not 0<=x.rollback_cost<=1: return 'INVALID_PRIORITY_RISK_COST'
        pri_ids.append(x.agent_id)
    if len(pri_ids)!=len(set(pri_ids)): return 'DUPLICATE_PRIORITY_AGENT'
    owners={x.resource_id:x.owner_agent_id for x in req.locks}
    for x in req.wait_edges:
        if x.resource_id in owners and owners[x.resource_id]!=x.holder_agent_id: return 'LOCK_OWNER_EDGE_HOLDER_MISMATCH'
    return None

def _scc_cycles(edges:tuple[WaitEdge,...])->tuple[tuple[str,...],...]:
    adj={}
    for e in edges:
        adj.setdefault(e.waiter_agent_id,set()).add(e.holder_agent_id)
        adj.setdefault(e.holder_agent_id,set())
    index=0; stack=[]; on=set(); idx={}; low={}; comps=[]
    def visit(v):
        nonlocal index
        idx[v]=low[v]=index; index+=1; stack.append(v); on.add(v)
        for w in sorted(adj.get(v,())):
            if w not in idx:
                visit(w); low[v]=min(low[v],low[w])
            elif w in on: low[v]=min(low[v],idx[w])
        if low[v]==idx[v]:
            c=[]
            while True:
                w=stack.pop(); on.remove(w); c.append(w)
                if w==v: break
            comps.append(tuple(sorted(c)))
    for v in sorted(adj):
        if v not in idx: visit(v)
    cycles=[]
    self_edges={(e.waiter_agent_id,e.holder_agent_id) for e in edges}
    for c in comps:
        if len(c)>1 or (len(c)==1 and (c[0],c[0]) in self_edges): cycles.append(c)
    return tuple(sorted(cycles))

def _cycle_trace(agents,edges):
    aset=set(agents)
    res=sorted({e.resource_id for e in edges if e.waiter_agent_id in aset and e.holder_agent_id in aset})
    return CycleTrace(tuple(sorted(agents)),tuple(res))

def evaluate(req:DeadlockRequest)->DeadlockResult:
    bad=_validate(req)
    if bad: return _invalid(bad)
    cyc_agents=_scc_cycles(req.wait_edges)
    cycles=tuple(_cycle_trace(c,req.wait_edges) for c in cyc_agents)
    if not cycles:
        return DeadlockResult(Decision.ALLOW,NextAction.CONTINUE_CANDIDATE,Escalation.NONE,DeadlockState.NO_CYCLE,('NO_WAIT_FOR_CYCLE_DETECTED','NO_RELEASE_OR_RETRY_EXECUTED'),(),None,(),(),(),True)
    if req.occurrence_count>=req.policy.repeated_deadlock_threshold:
        return DeadlockResult(Decision.HUMAN_APPROVAL,NextAction.PLAN_REDESIGN_CANDIDATE,Escalation.REPEATED_DEADLOCK,DeadlockState.REDESIGN_REQUIRED,('REPEATED_DEADLOCK_REQUIRES_PLAN_REDESIGN','DO_NOT_REPEAT_VICTIM_KILLING_BLINDLY'),cycles,None,(),(),(),False)
    lock_map={x.resource_id:x for x in req.locks}; pri_map={x.agent_id:x for x in req.priorities}
    involved=set(a for c in cycles for a in c.agent_ids)
    involved_resources={r for c in cycles for r in c.resource_ids}
    # Canonical fail-safe: any Critical lock participating in the deadlock blocks automatic release,
    # even when another noncritical victim could technically break the cycle.
    if req.policy.critical_lock_requires_human and any((rid in lock_map and lock_map[rid].critical) for rid in involved_resources):
        return DeadlockResult(Decision.HUMAN_APPROVAL,NextAction.HUMAN_REVIEW_CANDIDATE,Escalation.CRITICAL_LOCK,DeadlockState.HUMAN_REQUIRED,('CRITICAL_LOCK_IN_DEADLOCK_CYCLE','DO_NOT_AUTO_RELEASE_AROUND_CRITICAL_LOCK'),cycles,None,(),(),(),False)
    evals=[]; candidates=[]; critical_seen=False; invariant_risk_seen=False
    for aid in sorted(involved):
        reasons=[]; eligible=True
        ap=pri_map.get(aid)
        if ap is None:
            eligible=False; reasons.append('MISSING_AGENT_PRIORITY')
            priority=10**9; risk=1.0; arcost=1.0
        else:
            priority=ap.priority; risk=ap.risk; arcost=ap.rollback_cost
        owned=tuple(sorted(x.resource_id for x in req.locks if x.owner_agent_id==aid and x.resource_id in {r for c in cycles for r in c.resource_ids}))
        if not owned:
            eligible=False; reasons.append('NO_OWNED_CYCLE_RESOURCE')
        lock_cost=arcost
        for rid in owned:
            lk=lock_map.get(rid)
            if lk is None:
                eligible=False; reasons.append('MISSING_LOCK_STATE'); invariant_risk_seen=True; continue
            lock_cost=max(lock_cost,lk.rollback_cost)
            if lk.critical and req.policy.critical_lock_requires_human:
                eligible=False; reasons.append('CRITICAL_LOCK_REQUIRES_HUMAN'); critical_seen=True
            if not lk.safe_release:
                eligible=False; reasons.append('SAFE_RELEASE_NOT_PROVEN'); invariant_risk_seen=True
        if risk>req.policy.max_auto_risk:
            eligible=False; reasons.append('RISK_ABOVE_AUTO_LIMIT')
        if lock_cost>req.policy.max_auto_rollback_cost:
            eligible=False; reasons.append('ROLLBACK_COST_ABOVE_AUTO_LIMIT')
        if eligible: reasons.append('SAFE_VICTIM_CANDIDATE')
        ev=VictimEvaluation(aid,eligible,priority,risk,lock_cost,owned,tuple(reasons)); evals.append(ev)
        if eligible: candidates.append(ev)
    if not candidates:
        esc=Escalation.CRITICAL_LOCK if critical_seen else (Escalation.SAFETY_INVARIANT_RISK if invariant_risk_seen else Escalation.NO_SAFE_VICTIM)
        decision=Decision.HUMAN_APPROVAL if esc in (Escalation.CRITICAL_LOCK,Escalation.SAFETY_INVARIANT_RISK) else Decision.HOLD
        return DeadlockResult(decision,NextAction.HUMAN_REVIEW_CANDIDATE if decision==Decision.HUMAN_APPROVAL else NextAction.HOLD_DEADLOCK_CANDIDATE,esc,DeadlockState.HUMAN_REQUIRED,('NO_SAFE_AUTOMATIC_RELEASE_CANDIDATE','DO_NOT_BREAK_SAFETY_INVARIANTS_FOR_LIVENESS'),cycles,None,(),(),tuple(evals),False)
    # Lower priority, risk and rollback cost is the preferred victim; agent_id is deterministic tie-break.
    ranked=sorted(candidates,key=lambda x:(x.priority,x.risk,x.rollback_cost,x.agent_id))
    top=ranked[0]
    retry=tuple(sorted(a for a in involved if a!=top.agent_id))
    return DeadlockResult(Decision.ALLOW,NextAction.RELEASE_RETRY_CANDIDATE,Escalation.NONE,DeadlockState.BREAK_CANDIDATE,('SAFE_RELEASE_CANDIDATE_IDENTIFIED','RELEASE_RETRY_NOT_EXECUTED','NO_PERMISSION_OR_ACTION_PROMOTION'),cycles,top.agent_id,top.owned_cycle_resources,retry,tuple(evals),True)

def default_evaluation(): return evaluate(default_request())

def _fps(req,result): return (_fp((req.request_id,req.occurrence_count,req.binding,req.state_epoch)),_fp(req.wait_edges),_fp((req.locks,req.priorities)),_fp(req.policy),_fp(result))
def _integrity_payload(cf,wf,lf,pf,of,b,e): return (cf,wf,lf,pf,of,b,e,'NOEPIN-AL-131-PREPARED-V1')
def prepare_state(req:DeadlockRequest,*,binding:str,state_epoch:str)->PreparedDeadlockState:
    rr=_invalid('PREPARED_BINDING_OR_EPOCH_MISMATCH') if binding!=req.binding or state_epoch!=req.state_epoch else evaluate(req)
    cf,wf,lf,pf,of=_fps(req,rr); integ=_fp(_integrity_payload(cf,wf,lf,pf,of,binding,state_epoch))
    return PreparedDeadlockState(req,rr,cf,wf,lf,pf,of,integ,binding,state_epoch)
def validate_prepared_integrity(st):
    return isinstance(st,PreparedDeadlockState) and st.integrity_fingerprint==_fp(_integrity_payload(st.context_fingerprint,st.wait_fingerprint,st.lock_fingerprint,st.policy_fingerprint,st.outcome_fingerprint,st.binding,st.state_epoch))
def evaluate_prepared(st:PreparedDeadlockState,*,integrity_validated:bool,current_context_fingerprint:str,current_wait_fingerprint:str,current_lock_fingerprint:str,current_policy_fingerprint:str,current_outcome_fingerprint:str)->DeadlockResult:
    if not integrity_validated or not validate_prepared_integrity(st): return _invalid('PREPARED_INTEGRITY_NOT_VALIDATED')
    if (current_context_fingerprint,current_wait_fingerprint,current_lock_fingerprint,current_policy_fingerprint,current_outcome_fingerprint)!=(st.context_fingerprint,st.wait_fingerprint,st.lock_fingerprint,st.policy_fingerprint,st.outcome_fingerprint): return _invalid('PREPARED_FINGERPRINT_MISMATCH')
    return st.result

def make_delta(old:PreparedDeadlockState,new:PreparedDeadlockState)->DeadlockDelta:
    oe={_edge_id(x):x for x in old.request.wait_edges}; ne={_edge_id(x):x for x in new.request.wait_edges}
    cw=tuple(ne[k] for k in sorted(ne) if k not in oe or _canon(ne[k])!=_canon(oe[k])); rw=tuple(k for k in sorted(oe) if k not in ne)
    ol={x.resource_id:x for x in old.request.locks}; nl={x.resource_id:x for x in new.request.locks}
    cl=tuple(nl[k] for k in sorted(nl) if k not in ol or _canon(nl[k])!=_canon(ol[k])); rl=tuple(k for k in sorted(ol) if k not in nl)
    op={x.agent_id:x for x in old.request.priorities}; np={x.agent_id:x for x in new.request.priorities}
    cp=tuple(np[k] for k in sorted(np) if k not in op or _canon(np[k])!=_canon(op[k])); rp=tuple(k for k in sorted(op) if k not in np)
    return DeadlockDelta(cw,rw,cl,rl,cp,rp,old.request.occurrence_count!=new.request.occurrence_count,old.request.policy!=new.request.policy,_manifest_fp(old.request),_manifest_fp(new.request))

def plan_missing_only(old:PreparedDeadlockState,new:PreparedDeadlockState)->MissingOnlyPlan:
    d=make_delta(old,new); ids=[]
    ids += [f'WAIT:{_edge_id(x)}' for x in d.changed_wait_edges]; ids += [f'WAIT_REMOVED:{x}' for x in d.removed_wait_edge_ids]
    ids += [f'LOCK:{x.resource_id}' for x in d.changed_locks]; ids += [f'LOCK_REMOVED:{x}' for x in d.removed_lock_ids]
    ids += [f'PRIORITY:{x.agent_id}' for x in d.changed_priorities]; ids += [f'PRIORITY_REMOVED:{x}' for x in d.removed_priority_ids]
    if d.occurrence_changed: ids.append('OCCURRENCE_COUNT')
    if d.policy_changed: ids.append('POLICY')
    return MissingOnlyPlan(tuple(ids),len(_canon((d.from_manifest_fingerprint,d.to_manifest_fingerprint,ids))),False)
