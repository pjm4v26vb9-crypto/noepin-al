"""NOEPIN AL 111 — Stop-Condition Synthesizer — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Pure deterministic predicate synthesis and runtime-monitor evidence. This module converts
observable success/failure criteria plus budget and step bounds into an explicit stop
monitor. Ambiguous, unobservable, or contradictory criteria HOLD before long-horizon
operation. Runtime evaluation prioritizes abort conditions over completion conditions.
It never executes stop/action operations, grants permission/approval, mutates external
state, proves world truth/safety, or claims action success.

Canonical identity: NOEPIN-AL-111
DCSR level: AUXILIARY INTEGRATION / 補助統合.
Provenance note: exact registered Origin GUID was not freshly reverified in this
completion session and is intentionally not guessed or regenerated.
Pre-existing Notion V1 attachment byte identity was not freshly reverified.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str, Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class PredicateKind(str, Enum): SUCCESS='SUCCESS'; FAILURE='FAILURE'; BUDGET='BUDGET'; MAX_STEPS='MAX_STEPS'
class Operator(str, Enum): EQ='EQ'; NE='NE'; GE='GE'; GT='GT'; LE='LE'; LT='LT'; TRUE='TRUE'; FALSE='FALSE'
class NextAction(str, Enum):
    MONITOR_READY_CANDIDATE='MONITOR_READY_CANDIDATE'
    CONTINUE_CANDIDATE='CONTINUE_CANDIDATE'
    NORMAL_STOP_CANDIDATE='NORMAL_STOP_CANDIDATE'
    ABORT_STOP_CANDIDATE='ABORT_STOP_CANDIDATE'
    HOLD_CONFIGURATION_CANDIDATE='HOLD_CONFIGURATION_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; OBSERVABILITY_GAP='OBSERVABILITY_GAP'; PREDICATE_CONFLICT='PREDICATE_CONFLICT'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'

@dataclass(frozen=True)
class PredicateSpec:
    predicate_id: str
    field: str
    operator: Operator
    expected: object
    observable: bool
    description: str
    predicate_version: str
    predicate_fingerprint: str
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class BudgetLimit:
    resource: str
    maximum: float
    unit: str
    budget_version: str
    budget_fingerprint: str
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class StopSynthesisRequest:
    request_id: str
    goal: str
    success_criteria: tuple[PredicateSpec,...]
    failure_criteria: tuple[PredicateSpec,...]
    budgets: tuple[BudgetLimit,...]
    max_steps: int
    long_horizon: bool
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class SynthesizedPredicate:
    predicate_id: str
    kind: PredicateKind
    field: str
    operator: Operator
    expected: object
    priority: int
    description: str

@dataclass(frozen=True)
class SynthesisResult:
    decision: Decision
    next_action: NextAction
    escalation: Escalation
    reasons: tuple[str,...]
    stop_predicates: tuple[SynthesizedPredicate,...]
    completion_predicate_ids: tuple[str,...]
    abort_predicate_ids: tuple[str,...]
    observable_coverage_complete: bool
    conflict_free: bool
    budget_bounds_present: bool
    max_steps_bound_present: bool
    runtime_monitor_ready: bool
    next_gate_candidate: bool
    permission_granted: bool=False
    approval_executed: bool=False
    stop_executed: bool=False
    action_executed: bool=False
    plan_committed: bool=False
    external_write_performed: bool=False
    world_truth_proven: bool=False
    domain_authority_promoted: bool=False
    safety_proven: bool=False
    action_success: bool=False

@dataclass(frozen=True)
class RuntimeState:
    observations: tuple[tuple[str,object],...]
    budget_usage: tuple[tuple[str,float],...]
    step_count: int
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class RuntimeDecision:
    decision: Decision
    next_action: NextAction
    escalation: Escalation
    reasons: tuple[str,...]
    triggered_predicate_ids: tuple[str,...]
    completion_reached: bool
    abort_reached: bool
    budget_exceeded: bool
    max_steps_reached: bool
    next_gate_candidate: bool
    permission_granted: bool=False
    approval_executed: bool=False
    stop_executed: bool=False
    action_executed: bool=False
    external_write_performed: bool=False
    world_truth_proven: bool=False
    safety_proven: bool=False
    action_success: bool=False

@dataclass(frozen=True)
class PreparedStopState:
    request: StopSynthesisRequest
    predicate_fingerprints: tuple[tuple[str,str],...]
    budget_fingerprints: tuple[tuple[str,str],...]
    context_fingerprint: str
    dependency_fingerprint: str
    policy_fingerprint: str
    budget_fingerprint: str
    registry_fingerprint: str
    monitor_fingerprint: str
    precomputed_result: SynthesisResult
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class StopStateDelta:
    base_registry_fingerprint: str
    target_registry_fingerprint: str
    changed_success_predicates: tuple[PredicateSpec,...]
    changed_failure_predicates: tuple[PredicateSpec,...]
    changed_budgets: tuple[BudgetLimit,...]
    removed_record_ids: tuple[str,...]
    max_steps_replacement: int|None
    goal_replacement: str|None
    binding: str
    state_epoch: str

@dataclass(frozen=True)
class StopSyncPlan:
    missing_or_changed_record_ids: tuple[str,...]
    metadata_bytes_required: int
    full_resend_required: bool


def _j(v):
    if isinstance(v,Enum): return v.value
    if is_dataclass(v): return {f.name:_j(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v,dict): return {str(k):_j(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(tuple,list)): return [_j(x) for x in v]
    if isinstance(v,float):
        if not math.isfinite(v): return str(v)
        return float(format(v,'.15g'))
    return v

def _canon(v): return json.dumps(_j(v),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
def _fp(v): return sha256(_canon(v)).hexdigest()

def _hold(reason, escalation=Escalation.INVALID_CONFIGURATION):
    return SynthesisResult(Decision.HOLD,NextAction.HOLD_CONFIGURATION_CANDIDATE,escalation,(reason,),(),(),(),False,False,False,False,False,False)

def _finite_number(v): return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(float(v))

def _predicate_valid(p:PredicateSpec, binding:str, epoch:str):
    if not isinstance(p,PredicateSpec) or not p.predicate_id or not p.field or not p.description: return False
    if p.binding!=binding or p.state_epoch!=epoch: return False
    if p.operator in (Operator.GE,Operator.GT,Operator.LE,Operator.LT) and not _finite_number(p.expected): return False
    if p.operator in (Operator.TRUE,Operator.FALSE) and p.expected not in (True,False,None): return False
    return True

def _budget_valid(b:BudgetLimit, binding:str, epoch:str):
    return isinstance(b,BudgetLimit) and bool(b.resource) and bool(b.unit) and b.binding==binding and b.state_epoch==epoch and _finite_number(b.maximum) and b.maximum>=0

def _criterion_signature(p:PredicateSpec): return (p.field,p.operator.value,_j(p.expected))

def _validate(req:StopSynthesisRequest):
    if not isinstance(req,StopSynthesisRequest): return 'TYPE_INVALID',Escalation.INVALID_CONFIGURATION
    if not req.request_id or not req.goal or not req.binding or not req.state_epoch: return 'REQUEST_INVALID',Escalation.INVALID_CONFIGURATION
    if req.max_steps<=0: return 'MAX_STEPS_INVALID',Escalation.INVALID_CONFIGURATION
    if not req.success_criteria: return 'SUCCESS_CRITERIA_MISSING',Escalation.OBSERVABILITY_GAP
    if not req.failure_criteria: return 'FAILURE_CRITERIA_MISSING',Escalation.OBSERVABILITY_GAP
    allp=req.success_criteria+req.failure_criteria
    ids=[p.predicate_id for p in allp]
    if len(ids)!=len(set(ids)): return 'DUPLICATE_PREDICATE_ID',Escalation.INVALID_CONFIGURATION
    if any(not _predicate_valid(p,req.binding,req.state_epoch) for p in allp): return 'PREDICATE_INVALID',Escalation.INVALID_CONFIGURATION
    if any(not p.observable for p in allp): return 'UNOBSERVABLE_CRITERION',Escalation.OBSERVABILITY_GAP
    bids=[b.resource for b in req.budgets]
    if len(bids)!=len(set(bids)): return 'DUPLICATE_BUDGET_RESOURCE',Escalation.INVALID_CONFIGURATION
    if any(not _budget_valid(b,req.binding,req.state_epoch) for b in req.budgets): return 'BUDGET_INVALID',Escalation.INVALID_CONFIGURATION
    ss={_criterion_signature(p) for p in req.success_criteria}; fs={_criterion_signature(p) for p in req.failure_criteria}
    if ss & fs: return 'SUCCESS_FAILURE_PREDICATE_CONFLICT',Escalation.PREDICATE_CONFLICT
    return None,None

def synthesize(req:StopSynthesisRequest)->SynthesisResult:
    err,esc=_validate(req)
    if err: return _hold(err,esc)
    out=[]
    for p in sorted(req.failure_criteria,key=lambda x:x.predicate_id):
        out.append(SynthesizedPredicate(p.predicate_id,PredicateKind.FAILURE,p.field,p.operator,p.expected,10,p.description))
    for b in sorted(req.budgets,key=lambda x:x.resource):
        out.append(SynthesizedPredicate(f'BUDGET:{b.resource}',PredicateKind.BUDGET,b.resource,Operator.GT,b.maximum,20,f'{b.resource} usage exceeds hard budget {b.maximum} {b.unit}'))
    out.append(SynthesizedPredicate('MAX_STEPS',PredicateKind.MAX_STEPS,'step_count',Operator.GE,req.max_steps,30,'maximum step bound reached'))
    for p in sorted(req.success_criteria,key=lambda x:x.predicate_id):
        out.append(SynthesizedPredicate(p.predicate_id,PredicateKind.SUCCESS,p.field,p.operator,p.expected,100,p.description))
    out=tuple(sorted(out,key=lambda x:(x.priority,x.predicate_id)))
    return SynthesisResult(Decision.ALLOW,NextAction.MONITOR_READY_CANDIDATE,Escalation.NONE,('STOP_MONITOR_SYNTHESIZED','OBSERVABLE_CRITERIA_CONFIRMED','PREDICATE_CONFLICT_CHECK_PASS','ABORT_PRECEDENCE_FIXED'),out,tuple(p.predicate_id for p in out if p.kind==PredicateKind.SUCCESS),tuple(p.predicate_id for p in out if p.kind!=PredicateKind.SUCCESS),True,True,bool(req.budgets),True,True,True)

def _cmp(value,op,expected):
    if op==Operator.EQ: return value==expected
    if op==Operator.NE: return value!=expected
    if op==Operator.TRUE: return value is True
    if op==Operator.FALSE: return value is False
    if not _finite_number(value) or not _finite_number(expected): return False
    a=float(value); b=float(expected)
    if op==Operator.GE: return a>=b
    if op==Operator.GT: return a>b
    if op==Operator.LE: return a<=b
    if op==Operator.LT: return a<b
    return False

def evaluate_runtime(req:StopSynthesisRequest, monitor:SynthesisResult, state:RuntimeState)->RuntimeDecision:
    if monitor.decision!=Decision.ALLOW or not monitor.runtime_monitor_ready:
        return RuntimeDecision(Decision.HOLD,NextAction.HOLD_CONFIGURATION_CANDIDATE,Escalation.INVALID_CONFIGURATION,('MONITOR_NOT_READY',),(),False,False,False,False,False)
    if state.binding!=req.binding or state.state_epoch!=req.state_epoch:
        return RuntimeDecision(Decision.HOLD,NextAction.HOLD_CONFIGURATION_CANDIDATE,Escalation.INVALID_CONFIGURATION,('RUNTIME_BINDING_MISMATCH',),(),False,False,False,False,False)
    obs=dict(state.observations); usage=dict(state.budget_usage)
    if len(obs)!=len(state.observations) or len(usage)!=len(state.budget_usage) or state.step_count<0:
        return RuntimeDecision(Decision.HOLD,NextAction.HOLD_CONFIGURATION_CANDIDATE,Escalation.INVALID_CONFIGURATION,('RUNTIME_STATE_INVALID',),(),False,False,False,False,False)
    hits=[]; budget=False; steps=False; failure=False; success_hits=[]; success_total=0
    for p in monitor.stop_predicates:
        if p.kind==PredicateKind.BUDGET:
            hit=_cmp(usage.get(p.field,0.0),p.operator,p.expected); budget=budget or hit
        elif p.kind==PredicateKind.MAX_STEPS:
            hit=_cmp(state.step_count,p.operator,p.expected); steps=steps or hit
        else:
            if p.field not in obs: hit=False
            else: hit=_cmp(obs[p.field],p.operator,p.expected)
            if p.kind==PredicateKind.FAILURE: failure=failure or hit
            if p.kind==PredicateKind.SUCCESS:
                success_total += 1
                if hit: success_hits.append(p.predicate_id)
        if hit: hits.append(p.predicate_id)
    success=(success_total>0 and len(success_hits)==success_total)
    abort=failure or budget or steps
    if abort:
        rs=[]
        if failure: rs.append('FAILURE_PREDICATE_TRUE')
        if budget: rs.append('BUDGET_EXCEEDED')
        if steps: rs.append('MAX_STEPS_REACHED')
        if success: rs.append('SUCCESS_ALSO_TRUE_ABORT_PRECEDENCE')
        return RuntimeDecision(Decision.ALLOW,NextAction.ABORT_STOP_CANDIDATE,Escalation.NONE,tuple(rs),tuple(hits),False,True,budget,steps,True)
    if success:
        return RuntimeDecision(Decision.ALLOW,NextAction.NORMAL_STOP_CANDIDATE,Escalation.NONE,('SUCCESS_PREDICATE_TRUE',),tuple(hits),True,False,False,False,True)
    return RuntimeDecision(Decision.ALLOW,NextAction.CONTINUE_CANDIDATE,Escalation.NONE,('NO_STOP_PREDICATE_TRUE',),tuple(hits),False,False,False,False,True)

def default_request():
    b='STOP-BIND'; e='STATE-EPOCH-1'
    succ=(PredicateSpec('SUCCESS:TESTS','tests_passed',Operator.EQ,160,True,'all required tests passed','V1','FP-SUCCESS-TESTS',b,e),PredicateSpec('SUCCESS:ARTIFACT','artifact_frozen',Operator.TRUE,True,True,'final artifact is frozen','V1','FP-SUCCESS-ARTIFACT',b,e))
    fail=(PredicateSpec('FAIL:SAFETY','safety_violation',Operator.TRUE,True,True,'safety violation observed','V1','FP-FAIL-SAFETY',b,e),PredicateSpec('FAIL:DIVERGENCE','replay_divergence',Operator.GT,0,True,'replay divergence observed','V1','FP-FAIL-DIV',b,e))
    budgets=(BudgetLimit('risk_units',100.0,'risk-units','V1','FP-BUDGET-RISK',b,e),BudgetLimit('tool_calls',200.0,'calls','V1','FP-BUDGET-TOOLS',b,e),BudgetLimit('tokens',100000.0,'tokens','V1','FP-BUDGET-TOKENS',b,e))
    return StopSynthesisRequest('REQ-111','Produce a verified artifact without unsafe unbounded retry',succ,fail,budgets,500,True,b,e)

def default_synthesis(): return synthesize(default_request())
def default_runtime_state():
    q=default_request(); return RuntimeState((('artifact_frozen',False),('replay_divergence',0),('safety_violation',False),('tests_passed',120)),(('risk_units',20.0),('tokens',20000.0),('tool_calls',40.0)),100,q.binding,q.state_epoch)
def default_runtime_evaluation(): return evaluate_runtime(default_request(),default_synthesis(),default_runtime_state())

def _predicate_fps(req):
    rows=[]
    for p in sorted(req.success_criteria,key=lambda x:x.predicate_id): rows.append((f'SUCCESS:{p.predicate_id}',_fp(p)))
    for p in sorted(req.failure_criteria,key=lambda x:x.predicate_id): rows.append((f'FAILURE:{p.predicate_id}',_fp(p)))
    return tuple(rows)
def _budget_fps(req): return tuple((f'BUDGET:{b.resource}',_fp(b)) for b in sorted(req.budgets,key=lambda x:x.resource))
def _context_fp(req): return _fp((req.request_id,req.goal,req.long_horizon,req.binding,req.state_epoch))
def _dependency_fp(req): return _fp(tuple((p.predicate_id,p.field,p.operator,p.observable,p.predicate_version,p.predicate_fingerprint) for p in sorted(req.success_criteria+req.failure_criteria,key=lambda x:x.predicate_id)))
def _policy_fp(req): return _fp(('ABORT_PRECEDENCE',req.max_steps,'NO_UNOBSERVABLE_LONG_HORIZON','STOP_CANDIDATE_NOT_EXECUTION'))
def _budget_fp(req): return _fp(tuple(sorted(req.budgets,key=lambda x:x.resource)))
def _registry_fp(req): return _fp((_predicate_fps(req),_budget_fps(req),req.max_steps,req.goal))
def _monitor_fp(req): return _fp(synthesize(req))

def prepare_state(req,*,binding,state_epoch):
    return PreparedStopState(req,_predicate_fps(req),_budget_fps(req),_context_fp(req),_dependency_fp(req),_policy_fp(req),_budget_fp(req),_registry_fp(req),_monitor_fp(req),synthesize(req),binding,state_epoch)
def validate_prepared_integrity(st):
    q=st.request
    return (st.binding==q.binding and st.state_epoch==q.state_epoch and st.predicate_fingerprints==_predicate_fps(q) and st.budget_fingerprints==_budget_fps(q) and st.context_fingerprint==_context_fp(q) and st.dependency_fingerprint==_dependency_fp(q) and st.policy_fingerprint==_policy_fp(q) and st.budget_fingerprint==_budget_fp(q) and st.registry_fingerprint==_registry_fp(q) and st.monitor_fingerprint==_monitor_fp(q) and st.precomputed_result==synthesize(q))
def evaluate_prepared(st,*,integrity_validated,current_context_fingerprint,current_dependency_fingerprint,current_policy_fingerprint,current_budget_fingerprint,current_registry_fingerprint,current_monitor_fingerprint):
    if not integrity_validated: return _hold('PREPARED_INTEGRITY_NOT_VALIDATED')
    if (st.context_fingerprint!=current_context_fingerprint or st.dependency_fingerprint!=current_dependency_fingerprint or st.policy_fingerprint!=current_policy_fingerprint or st.budget_fingerprint!=current_budget_fingerprint or st.registry_fingerprint!=current_registry_fingerprint or st.monitor_fingerprint!=current_monitor_fingerprint):
        return _hold('PREPARED_FINGERPRINT_MISMATCH_REEVALUATION_REQUIRED')
    return st.precomputed_result

def make_delta(base,target):
    bp=dict(base.predicate_fingerprints); tp=dict(target.predicate_fingerprints); bb=dict(base.budget_fingerprints); tb=dict(target.budget_fingerprints)
    smap={f'SUCCESS:{p.predicate_id}':p for p in target.request.success_criteria}; fmap={f'FAILURE:{p.predicate_id}':p for p in target.request.failure_criteria}; bmap={f'BUDGET:{b.resource}':b for b in target.request.budgets}
    cs=tuple(smap[k] for k,v in tp.items() if k.startswith('SUCCESS:') and bp.get(k)!=v)
    cf=tuple(fmap[k] for k,v in tp.items() if k.startswith('FAILURE:') and bp.get(k)!=v)
    cb=tuple(bmap[k] for k,v in tb.items() if bb.get(k)!=v)
    removed=tuple(sorted([k for k in bp if k not in tp]+[k for k in bb if k not in tb]))
    return StopStateDelta(base.registry_fingerprint,target.registry_fingerprint,cs,cf,cb,removed,target.request.max_steps if base.request.max_steps!=target.request.max_steps else None,target.request.goal if base.request.goal!=target.request.goal else None,target.binding,target.state_epoch)
def plan_missing_only(local,target):
    lm=dict(local.predicate_fingerprints+local.budget_fingerprints); tm=dict(target.predicate_fingerprints+target.budget_fingerprints)
    ids=[k for k,v in tm.items() if lm.get(k)!=v]
    if local.request.max_steps!=target.request.max_steps: ids.append('META:MAX_STEPS')
    if local.request.goal!=target.request.goal: ids.append('META:GOAL')
    ids=tuple(sorted(ids)); return StopSyncPlan(ids,len(_canon(ids)),False)
