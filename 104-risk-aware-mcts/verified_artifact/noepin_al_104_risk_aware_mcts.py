"""NOEPIN AL 104 — Risk-Aware Monte Carlo Tree Search — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Pure planning-candidate evidence. This module performs deterministic, replayable
risk-aware Monte Carlo tree-search style UCB allocation over a typed action tree.
Hard-constraint failures are never expanded. Rollout reward is reduced by risk
penalties, action-level risk budgets are enforced, and simulator confidence plus
minimum-simulation gates are checked before a Chosen Action candidate is returned.

A Chosen Action is only a planning candidate. It is never Permission Grant,
Action Execution, Commit/Publish, Production Authority, Safety Proof, or Action
Success.

Canonical identity: NOEPIN-AL-104
DCSR level: AUXILIARY INTEGRATION / 補助統合.
Provenance note: exact registered Origin GUID was not freshly reverified in this
completion session and is intentionally not guessed or regenerated.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, IntEnum
from hashlib import sha256
import json, math

class Decision(str, Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class RiskClass(IntEnum):
    LOW=0; MEDIUM=1; HIGH=2; CRITICAL=3
class NextAction(str, Enum):
    CHOSEN_ACTION_CANDIDATE='CHOSEN_ACTION_CANDIDATE'; HUMAN_REVIEW_CANDIDATE='HUMAN_REVIEW_CANDIDATE';
    SIMULATOR_REVALIDATION_CANDIDATE='SIMULATOR_REVALIDATION_CANDIDATE'; REPLAN_CANDIDATE='REPLAN_CANDIDATE'; HOLD_UNRESOLVED='HOLD_UNRESOLVED'

@dataclass(frozen=True)
class MCTSRequest:
    request_id:str; state_id:str; risk:RiskClass; simulation_budget:int; min_simulations:int
    max_action_risk:float; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class MCTSAction:
    action_id:str; reward_samples:tuple[float,...]; risk_samples:tuple[float,...]; simulator_confidence:float
    hard_constraint_passed:bool; constraint_reason:str; action_version:str; action_fingerprint:str
    observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class MCTSPolicy:
    exploration_c:float; risk_penalty:float; cvar_alpha:float; cvar_weight:float
    low_risk_cap:float; medium_risk_cap:float; high_risk_cap:float; critical_risk_cap:float
    min_simulator_confidence_low:float; min_simulator_confidence_medium:float; min_simulator_confidence_high:float; min_simulator_confidence_critical:float
    min_safe_advantage:float; approval_risk_threshold:float; require_hard_constraints:bool
    binding:str; state_epoch:str; revoked:bool=False
@dataclass(frozen=True)
class VisitStat:
    action_id:str; visits:int; mean_reward:float; mean_risk:float; cvar_risk:float; risk_adjusted_value:float; simulator_confidence:float
@dataclass(frozen=True)
class MCTSResult:
    decision:Decision; next_action:NextAction; reasons:tuple[str,...]; chosen_action:str|None
    visit_stats:tuple[VisitStat,...]; risk_estimate:float|None; simulations_used:int; pruned_actions:tuple[str,...]
    next_gate_candidate:bool; action_candidate_promoted_to_permission:bool=False
    permission_granted:bool=False; action_executed:bool=False; plan_committed:bool=False
    atomic_publish_executed:bool=False; external_write_performed:bool=False; world_truth_proven:bool=False
    domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedMCTSState:
    request:MCTSRequest; actions:tuple[MCTSAction,...]; policy:MCTSPolicy; action_fingerprints:tuple[tuple[str,str],...]
    context_fingerprint:str; dependency_fingerprint:str; policy_fingerprint:str; registry_fingerprint:str
    frontier_fingerprint:str; simulator_fingerprint:str; precomputed_result:MCTSResult; binding:str; state_epoch:str
@dataclass(frozen=True)
class MCTSStateDelta:
    base_fingerprint:str; target_fingerprint:str; changed_actions:tuple[MCTSAction,...]; removed_action_ids:tuple[str,...]
    target_request:MCTSRequest|None; target_policy:MCTSPolicy|None; binding:str; state_epoch:str
@dataclass(frozen=True)
class MCTSSyncPlan:
    missing_or_changed_action_ids:tuple[str,...]; metadata_bytes_required:int; full_resend_required:bool

def _cv(x):
    if isinstance(x,Enum): return x.name if isinstance(x,IntEnum) else x.value
    if hasattr(x,'__dataclass_fields__'): return {k:_cv(getattr(x,k)) for k in x.__dataclass_fields__}
    if isinstance(x,tuple): return [_cv(v) for v in x]
    if isinstance(x,list): return [_cv(v) for v in x]
    if isinstance(x,dict): return {str(k):_cv(x[k]) for k in sorted(x)}
    return x
def _canon(x)->bytes: return json.dumps(_cv(x),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def _fp(x)->str: return sha256(_canon(x)).hexdigest()
def _round(x): return round(float(x),12)
def _risk_cap(r,p): return {RiskClass.LOW:p.low_risk_cap,RiskClass.MEDIUM:p.medium_risk_cap,RiskClass.HIGH:p.high_risk_cap,RiskClass.CRITICAL:p.critical_risk_cap}[r]
def _sim_conf_min(r,p): return {RiskClass.LOW:p.min_simulator_confidence_low,RiskClass.MEDIUM:p.min_simulator_confidence_medium,RiskClass.HIGH:p.min_simulator_confidence_high,RiskClass.CRITICAL:p.min_simulator_confidence_critical}[r]

def _validate(q, actions, p):
    if p.revoked: return 'POLICY_REVOKED'
    if not q.observed or not q.request_id or not q.state_id: return 'REQUEST_INVALID'
    if q.binding!=p.binding or q.state_epoch!=p.state_epoch: return 'REQUEST_SCOPE_MISMATCH'
    if q.simulation_budget<=0 or q.min_simulations<=0 or q.min_simulations>q.simulation_budget: return 'SIMULATION_BUDGET_INVALID'
    vals=(q.max_action_risk,p.exploration_c,p.risk_penalty,p.cvar_alpha,p.cvar_weight,p.low_risk_cap,p.medium_risk_cap,p.high_risk_cap,p.critical_risk_cap,p.min_simulator_confidence_low,p.min_simulator_confidence_medium,p.min_simulator_confidence_high,p.min_simulator_confidence_critical,p.min_safe_advantage,p.approval_risk_threshold)
    if any(not math.isfinite(v) for v in vals): return 'NUMERIC_VALUE_INVALID'
    if q.max_action_risk<0 or p.exploration_c<0 or p.risk_penalty<0 or p.cvar_weight<0 or p.min_safe_advantage<0: return 'NUMERIC_VALUE_INVALID'
    if not (0<p.cvar_alpha<=1): return 'CVAR_ALPHA_INVALID'
    if not (p.low_risk_cap>=p.medium_risk_cap>=p.high_risk_cap>=p.critical_risk_cap>=0): return 'POLICY_RISK_CAP_NONMONOTONIC'
    if any(not (0<=x<=1) for x in (p.min_simulator_confidence_low,p.min_simulator_confidence_medium,p.min_simulator_confidence_high,p.min_simulator_confidence_critical)): return 'SIMULATOR_CONFIDENCE_POLICY_INVALID'
    ids=[a.action_id for a in actions]
    if not ids: return 'ACTION_SPACE_EMPTY'
    if len(ids)!=len(set(ids)): return 'DUPLICATE_ACTION_ID'
    for a in actions:
        if not a.observed or not a.action_id or not a.action_version or not a.action_fingerprint: return 'ACTION_INVALID'
        if a.binding!=p.binding or a.state_epoch!=p.state_epoch: return 'ACTION_SCOPE_MISMATCH'
        if len(a.reward_samples)==0 or len(a.reward_samples)!=len(a.risk_samples): return 'SIMULATOR_SAMPLES_INVALID'
        if any(not math.isfinite(v) for v in a.reward_samples+a.risk_samples): return 'SIMULATOR_SAMPLES_INVALID'
        if any(v<0 for v in a.risk_samples) or not (0<=a.simulator_confidence<=1): return 'SIMULATOR_SAMPLES_INVALID'
        if p.require_hard_constraints and not a.hard_constraint_passed and not a.constraint_reason: return 'CONSTRAINT_EVIDENCE_INVALID'
    return None

def _hold(reason, *, action=NextAction.HOLD_UNRESOLVED, stats=(), used=0, pruned=()):
    return MCTSResult(Decision.HOLD,action,(reason,),None,tuple(stats),None,used,tuple(sorted(pruned)),False)

def _cvar(vals, alpha):
    xs=sorted(vals, reverse=True); n=max(1,math.ceil(len(xs)*alpha)); return sum(xs[:n])/n

def evaluate(q:MCTSRequest, actions:tuple[MCTSAction,...], p:MCTSPolicy)->MCTSResult:
    actions=tuple(sorted(actions,key=lambda a:a.action_id)); err=_validate(q,actions,p)
    if err: return _hold(err)
    cap=min(q.max_action_risk,_risk_cap(q.risk,p))
    safe=[]; pruned=[]
    for a in actions:
        if p.require_hard_constraints and not a.hard_constraint_passed:
            pruned.append(a.action_id); continue
        # Conservative branch prefilter uses worst available simulator risk sample.
        if max(a.risk_samples)>cap+1e-12:
            pruned.append(a.action_id); continue
        safe.append(a)
    if not safe: return _hold('NO_SAFE_ACTION_BRANCH',action=NextAction.REPLAN_CANDIDATE,pruned=pruned)
    # Critical operations with an insufficient simulator are never automatically selected.
    min_conf=_sim_conf_min(q.risk,p)
    if q.risk==RiskClass.CRITICAL and max(a.simulator_confidence for a in safe)<min_conf:
        return _hold('CRITICAL_SIMULATOR_CONFIDENCE_INSUFFICIENT',action=NextAction.SIMULATOR_REVALIDATION_CANDIDATE,pruned=pruned)
    visits={a.action_id:0 for a in safe}; rewards={a.action_id:[] for a in safe}; risks={a.action_id:[] for a in safe}
    by={a.action_id:a for a in safe}; total=0
    # Deterministic UCB allocation. Unvisited actions are explored lexically first.
    for _ in range(q.simulation_budget):
        unvisited=[a for a in safe if visits[a.action_id]==0]
        if unvisited:
            a=unvisited[0]
        else:
            scored=[]
            for a in safe:
                aid=a.action_id; mr=sum(rewards[aid])/len(rewards[aid]); mk=sum(risks[aid])/len(risks[aid]); cv=_cvar(risks[aid],p.cvar_alpha)
                value=mr-p.risk_penalty*mk-p.cvar_weight*cv
                ucb=value+p.exploration_c*math.sqrt(math.log(total+1)/visits[aid])
                scored.append((-ucb,aid,a))
            scored.sort(key=lambda x:(x[0],x[1])); a=scored[0][2]
        aid=a.action_id; idx=visits[aid]%len(a.reward_samples)
        rewards[aid].append(a.reward_samples[idx]); risks[aid].append(a.risk_samples[idx]); visits[aid]+=1; total+=1
    stats=[]
    for a in safe:
        aid=a.action_id; vr=visits[aid]
        if vr==0:
            # Budget may be smaller than the safe action space. Unvisited branches are
            # retained as explicit unevaluated stats and can never outrank visited branches.
            stats.append(VisitStat(aid,0,0.0,0.0,0.0,-1000000000000.0,a.simulator_confidence)); continue
        mr=sum(rewards[aid])/vr; mk=sum(risks[aid])/vr; cv=_cvar(risks[aid],p.cvar_alpha)
        val=mr-p.risk_penalty*mk-p.cvar_weight*cv
        stats.append(VisitStat(aid,vr,_round(mr),_round(mk),_round(cv),_round(val),a.simulator_confidence))
    # Canonical MCTS choice: most visited safe action; ties prefer safer, then higher value, then lexical ID.
    stats.sort(key=lambda s:(-s.visits,s.mean_risk,-s.risk_adjusted_value,s.action_id))
    best=stats[0]
    if total<q.min_simulations: return _hold('EXPLORATION_INSUFFICIENT',action=NextAction.REPLAN_CANDIDATE,stats=stats,used=total,pruned=pruned)
    ba=by[best.action_id]
    if best.mean_risk>cap+1e-12 or best.cvar_risk>cap+1e-12:
        return _hold('RISK_BUDGET_EXCEEDED',action=NextAction.REPLAN_CANDIDATE,stats=stats,used=total,pruned=pruned)
    if ba.simulator_confidence<min_conf:
        return _hold('SIMULATOR_CONFIDENCE_INSUFFICIENT',action=NextAction.SIMULATOR_REVALIDATION_CANDIDATE,stats=stats,used=total,pruned=pruned)
    # Require risk-adjusted advantage against runner-up to avoid unstable automatic choice.
    runner=sorted(stats,key=lambda s:(-s.risk_adjusted_value,s.mean_risk,s.action_id))[1] if len(stats)>1 else None
    advantage=best.risk_adjusted_value-(runner.risk_adjusted_value if runner else -1e9)
    if runner is not None and advantage<p.min_safe_advantage-1e-12:
        return _hold('SAFE_ADVANTAGE_INSUFFICIENT',action=NextAction.REPLAN_CANDIDATE,stats=stats,used=total,pruned=pruned)
    reasons=['SAFE_MCTS_ACTION_CANDIDATE','HARD_CONSTRAINTS_PRESERVED','RISK_BUDGET_PRESERVED','ACTION_CANDIDATE_ONLY']
    if pruned: reasons.append('UNSAFE_BRANCHES_PRUNED')
    if q.risk in (RiskClass.HIGH,RiskClass.CRITICAL) and best.mean_risk>=p.approval_risk_threshold:
        return MCTSResult(Decision.HUMAN_APPROVAL,NextAction.HUMAN_REVIEW_CANDIDATE,tuple(reasons+['RISK_REQUIRES_HUMAN_REVIEW_CANDIDATE']),best.action_id,tuple(stats),best.mean_risk,total,tuple(sorted(pruned)),False)
    return MCTSResult(Decision.ALLOW,NextAction.CHOSEN_ACTION_CANDIDATE,tuple(reasons),best.action_id,tuple(stats),best.mean_risk,total,tuple(sorted(pruned)),True)

def default_policy():
    return MCTSPolicy(1.15,1.25,.25,.80,2.0,1.5,1.0,.55,.50,.60,.75,.90,.05,.65,True,'MCTS-BIND','STATE-EPOCH-1')
def default_request():
    p=default_policy(); return MCTSRequest('REQ-104','S0',RiskClass.LOW,120,60,2.0,True,p.binding,p.state_epoch)
def default_actions():
    p=default_policy(); b=p.binding; e=p.state_epoch
    return (
        MCTSAction('A-SAFE-LONG',(7.0,7.2,6.9,7.1),(0.20,0.25,0.15,0.20),.95,True,'PASS','A1','FP-SAFE',True,b,e),
        MCTSAction('A-RISKY-HIGH',(10.0,11.0,9.5,10.5),(1.8,1.6,1.9,1.7),.96,True,'PASS','A1','FP-RISKY',True,b,e),
        MCTSAction('A-STABLE-LOW',(5.0,5.1,4.9,5.0),(0.05,0.05,0.04,0.06),.98,True,'PASS','A1','FP-STABLE',True,b,e),
        MCTSAction('A-FORBIDDEN',(100.0,),(0.01,),1.0,False,'HARD_CONSTRAINT_VIOLATION','A1','FP-X',True,b,e),
    )
def default_evaluation(): return evaluate(default_request(),default_actions(),default_policy())

def _action_fps(actions): return tuple((f'ACTION:{a.action_id}',_fp(a)) for a in sorted(actions,key=lambda x:x.action_id))
def _context_fp(q): return _fp(q)
def _dependency_fp(actions): return _fp(_action_fps(actions))
def _policy_fp(p): return _fp(p)
def _registry_fp(q,actions,p): return _fp((q,_action_fps(actions),p))
def _frontier_fp(q,actions,p):
    safe=tuple((a.action_id,a.simulator_confidence,a.reward_samples,a.risk_samples) for a in sorted(actions,key=lambda x:x.action_id) if a.hard_constraint_passed)
    return _fp((q.state_id,q.simulation_budget,q.max_action_risk,safe,p.exploration_c,p.risk_penalty,p.cvar_alpha,p.cvar_weight))
def _simulator_fp(actions): return _fp(tuple((a.action_id,a.action_version,a.action_fingerprint,a.simulator_confidence) for a in sorted(actions,key=lambda x:x.action_id)))
def prepare_state(q,actions,p,*,binding:str,state_epoch:str):
    actions=tuple(actions); fps=_action_fps(actions)
    return PreparedMCTSState(q,actions,p,fps,_context_fp(q),_dependency_fp(actions),_policy_fp(p),_registry_fp(q,actions,p),_frontier_fp(q,actions,p),_simulator_fp(actions),evaluate(q,actions,p),binding,state_epoch)
def validate_prepared_integrity(st):
    return (st.binding==st.policy.binding==st.request.binding and st.state_epoch==st.policy.state_epoch==st.request.state_epoch and
            st.action_fingerprints==_action_fps(st.actions) and st.context_fingerprint==_context_fp(st.request) and
            st.dependency_fingerprint==_dependency_fp(st.actions) and st.policy_fingerprint==_policy_fp(st.policy) and
            st.registry_fingerprint==_registry_fp(st.request,st.actions,st.policy) and st.frontier_fingerprint==_frontier_fp(st.request,st.actions,st.policy) and
            st.simulator_fingerprint==_simulator_fp(st.actions) and st.precomputed_result==evaluate(st.request,st.actions,st.policy))
def evaluate_prepared(st,*,integrity_validated:bool,current_context_fingerprint:str,current_dependency_fingerprint:str,current_policy_fingerprint:str,current_registry_fingerprint:str,current_frontier_fingerprint:str,current_simulator_fingerprint:str):
    if not integrity_validated: return _hold('PREPARED_INTEGRITY_NOT_VALIDATED')
    if (st.context_fingerprint!=current_context_fingerprint or st.dependency_fingerprint!=current_dependency_fingerprint or st.policy_fingerprint!=current_policy_fingerprint or st.registry_fingerprint!=current_registry_fingerprint or st.frontier_fingerprint!=current_frontier_fingerprint or st.simulator_fingerprint!=current_simulator_fingerprint):
        return _hold('PREPARED_FINGERPRINT_MISMATCH_REEVALUATION_REQUIRED',action=NextAction.REPLAN_CANDIDATE)
    return st.precomputed_result
def make_delta(base:PreparedMCTSState,target:PreparedMCTSState):
    bm=dict(base.action_fingerprints); tm=dict(target.action_fingerprints); tby={a.action_id:a for a in target.actions}
    changed=tuple(tby[k[7:]] for k,v in tm.items() if bm.get(k)!=v); removed=tuple(k[7:] for k in bm if k not in tm)
    return MCTSStateDelta(base.registry_fingerprint,target.registry_fingerprint,changed,removed,target.request if base.context_fingerprint!=target.context_fingerprint else None,target.policy if base.policy_fingerprint!=target.policy_fingerprint else None,target.binding,target.state_epoch)
def plan_missing_only(local:PreparedMCTSState,target:PreparedMCTSState):
    lm=dict(local.action_fingerprints); tm=dict(target.action_fingerprints); ids=tuple(k[7:] for k,v in tm.items() if lm.get(k)!=v)
    return MCTSSyncPlan(ids,len(_canon(ids)),False)
