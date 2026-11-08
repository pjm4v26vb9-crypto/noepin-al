"""NOEPIN AL 083 — Reversible-First Planner — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Deterministic reversible-first planning control. Among candidate actions that satisfy
an explicit minimum goal-achievement constraint, it prefers higher reversibility,
lower risk, and then lower cost. Irreversible actions without valid human-approval
evidence are not promoted to an executable action. High-risk actions with unknown
reversibility or without a rollback option fail safe to HOLD.

This module never grants permission, executes an action, performs rollback, commits
state, publishes, writes to an external environment, proves World Truth/Safety, or
asserts Action Success.

Canonical identity: NOEPIN-AL-083
Provenance note: exact registered Origin GUID was not freshly reverified in this
completion session and is intentionally not guessed or regenerated.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
import math

class Decision(str, Enum):
    ALLOW='ALLOW'
    DENY='DENY'
    HOLD='HOLD'
    HUMAN_APPROVAL='HUMAN_APPROVAL'

class Risk(str, Enum):
    LOW='LOW'
    MEDIUM='MEDIUM'
    HIGH='HIGH'
    CRITICAL='CRITICAL'

@dataclass(frozen=True)
class Goal:
    goal_id:str
    min_achievement:float
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class CandidateAction:
    action_id:str
    goal_id:str
    achievement:float
    reversibility_score:float|None
    cost:float
    risk:Risk
    rollback_action_id:str|None
    irreversible:bool
    feasible:bool
    approval_evidence_id:str|None
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class ApprovalEvidence:
    evidence_id:str
    action_id:str
    observed:bool
    actor_authorized:bool
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class PlannerPolicy:
    binding:str
    state_epoch:str
    reversible_threshold:float=0.65
    critical_requires_hold:bool=True
    revoked:bool=False

@dataclass(frozen=True)
class RankedAction:
    action_id:str
    achievement:float
    reversibility_score:float|None
    risk:Risk
    cost:float
    rollback_action_id:str|None
    requires_human_approval:bool
    approval_evidence_valid:bool

@dataclass(frozen=True)
class PlanResult:
    decision:Decision
    reasons:tuple[str,...]
    ordered_plan:tuple[RankedAction,...]
    chosen_action_id:str|None
    rollback_option:str|None
    next_gate_candidate:bool
    human_approval_candidate:bool
    permission_granted:bool=False
    approval_executed:bool=False
    action_executed:bool=False
    rollback_executed:bool=False
    plan_committed:bool=False
    external_write_performed:bool=False
    world_truth_proven:bool=False
    safety_proven:bool=False
    action_success:bool=False

@dataclass(frozen=True)
class PreparedPlannerState:
    policy:PlannerPolicy
    goal:Goal
    actions:tuple[CandidateAction,...]
    approvals:tuple[ApprovalEvidence,...]
    action_fingerprints:tuple[tuple[str,str],...]
    approval_fingerprints:tuple[tuple[str,str],...]
    policy_fingerprint:str
    goal_fingerprint:str
    context_fingerprint:str
    dependency_fingerprint:str
    registry_fingerprint:str
    precomputed_result:PlanResult
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class PlannerStateDelta:
    base_fingerprint:str
    target_fingerprint:str
    changed_actions:tuple[CandidateAction,...]
    removed_action_ids:tuple[str,...]
    changed_approvals:tuple[ApprovalEvidence,...]
    removed_approval_ids:tuple[str,...]
    target_goal:Goal
    target_policy:PlannerPolicy
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class PlannerSyncPlan:
    missing_or_changed_action_ids:tuple[str,...]
    missing_or_changed_approval_ids:tuple[str,...]
    metadata_bytes_required:int
    full_resend_required:bool


def _cv(x):
    if isinstance(x,Enum): return x.value
    if hasattr(x,'__dataclass_fields__'): return {k:_cv(getattr(x,k)) for k in x.__dataclass_fields__}
    if isinstance(x,tuple): return [_cv(v) for v in x]
    if isinstance(x,list): return [_cv(v) for v in x]
    if isinstance(x,dict): return {str(k):_cv(x[k]) for k in sorted(x)}
    return x

def _canon(x)->bytes:
    return json.dumps(_cv(x),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()

def _fp(x)->str: return sha256(_canon(x)).hexdigest()

def _risk_rank(r:Risk)->int:
    return {Risk.LOW:0,Risk.MEDIUM:1,Risk.HIGH:2,Risk.CRITICAL:3}[r]

def _finite01(v)->bool:
    return isinstance(v,(int,float)) and math.isfinite(float(v)) and 0.0 <= float(v) <= 1.0

def _valid_cost(v)->bool:
    return isinstance(v,(int,float)) and math.isfinite(float(v)) and float(v)>=0.0

def _approval_map(approvals): return {x.evidence_id:x for x in approvals}

def _valid_approval(action:CandidateAction, approvals:tuple[ApprovalEvidence,...], policy:PlannerPolicy)->bool:
    if not action.approval_evidence_id: return False
    ev=_approval_map(approvals).get(action.approval_evidence_id)
    return bool(ev and ev.action_id==action.action_id and ev.observed and ev.actor_authorized and ev.binding==policy.binding and ev.state_epoch==policy.state_epoch)

def _valid_inputs(goal,actions,approvals,policy):
    if policy.revoked: return False,'POLICY_REVOKED'
    if goal.binding!=policy.binding or goal.state_epoch!=policy.state_epoch: return False,'GOAL_BINDING_OR_EPOCH_MISMATCH'
    if not _finite01(goal.min_achievement): return False,'INVALID_GOAL_THRESHOLD'
    aids=[a.action_id for a in actions]
    if len(aids)!=len(set(aids)): return False,'DUPLICATE_ACTION_ID'
    eids=[e.evidence_id for e in approvals]
    if len(eids)!=len(set(eids)): return False,'DUPLICATE_APPROVAL_EVIDENCE_ID'
    for a in actions:
        if a.binding!=policy.binding or a.state_epoch!=policy.state_epoch: return False,'ACTION_BINDING_OR_EPOCH_MISMATCH'
        if a.goal_id!=goal.goal_id: continue
        if not _finite01(a.achievement): return False,'INVALID_ACHIEVEMENT'
        if a.reversibility_score is not None and not _finite01(a.reversibility_score): return False,'INVALID_REVERSIBILITY'
        if not _valid_cost(a.cost): return False,'INVALID_COST'
        if a.irreversible and a.reversibility_score not in (None,0,0.0): return False,'IRREVERSIBLE_SCORE_CONFLICT'
    for e in approvals:
        if e.binding!=policy.binding or e.state_epoch!=policy.state_epoch: return False,'APPROVAL_BINDING_OR_EPOCH_MISMATCH'
    return True,'VALID'

def _requires_approval(a:CandidateAction, policy:PlannerPolicy)->bool:
    if a.irreversible: return True
    if a.reversibility_score is None: return True
    return a.reversibility_score < policy.reversible_threshold

def _rank_tuple(a:CandidateAction):
    rev=-1.0 if a.reversibility_score is None else float(a.reversibility_score)
    return (-rev,_risk_rank(a.risk),float(a.cost),a.action_id)

def _ranked(a:CandidateAction, approvals, policy):
    return RankedAction(a.action_id,a.achievement,a.reversibility_score,a.risk,a.cost,a.rollback_action_id,_requires_approval(a,policy),_valid_approval(a,approvals,policy))

def evaluate(goal:Goal, actions:tuple[CandidateAction,...], approvals:tuple[ApprovalEvidence,...], policy:PlannerPolicy)->PlanResult:
    ok,why=_valid_inputs(goal,actions,approvals,policy)
    if not ok:
        return PlanResult(Decision.HOLD,(why,),(),None,None,False,False)
    viable=[a for a in actions if a.feasible and a.goal_id==goal.goal_id and a.achievement>=goal.min_achievement]
    if not viable:
        return PlanResult(Decision.HOLD,('NO_GOAL_SATISFYING_ACTION',),(),None,None,False,False)

    # CRITICAL actions are never automatically promoted by this planner.
    noncritical=[a for a in viable if not (policy.critical_requires_hold and a.risk==Risk.CRITICAL)]
    if not noncritical:
        ordered=tuple(_ranked(a,approvals,policy) for a in sorted(viable,key=_rank_tuple))
        return PlanResult(Decision.HOLD,('CRITICAL_ONLY',),ordered,None,None,False,False)

    # Unsafe candidates can remain visible in ordered_plan but cannot outrank a safe reversible candidate.
    safe=[]; approval_needed=[]; hold_only=[]
    for a in noncritical:
        approval_valid=_valid_approval(a,approvals,policy)
        if a.risk in (Risk.HIGH,Risk.CRITICAL) and a.reversibility_score is None:
            hold_only.append(a); continue
        if a.risk==Risk.HIGH and not a.rollback_action_id:
            hold_only.append(a); continue
        if a.reversibility_score is None:
            hold_only.append(a); continue
        if _requires_approval(a,policy) and not approval_valid:
            approval_needed.append(a); continue
        safe.append(a)

    ordered_all=tuple(_ranked(a,approvals,policy) for a in sorted(noncritical,key=_rank_tuple))
    if safe:
        chosen=sorted(safe,key=_rank_tuple)[0]
        reasons=['REVERSIBLE_FIRST_SELECTED']
        if _valid_approval(chosen,approvals,policy): reasons.append('HUMAN_APPROVAL_EVIDENCE_BOUND')
        if any(a.action_id!=chosen.action_id and (a.irreversible or a.reversibility_score is None or (a.reversibility_score or 0)<policy.reversible_threshold) for a in noncritical):
            reasons.append('SAFER_OPTION_PREFERRED')
        return PlanResult(Decision.ALLOW,tuple(reasons),ordered_all,chosen.action_id,chosen.rollback_action_id,True,False)
    if hold_only:
        # HOLD dominates approval solicitation if the only goal-satisfying options lack required rollback/reversibility evidence.
        reasons=[]
        if any(a.risk==Risk.HIGH and a.reversibility_score is None for a in hold_only): reasons.append('HIGH_RISK_REVERSIBILITY_UNKNOWN')
        if any(a.risk==Risk.HIGH and not a.rollback_action_id for a in hold_only): reasons.append('HIGH_RISK_ROLLBACK_MISSING')
        if any(a.reversibility_score is None for a in hold_only): reasons.append('REVERSIBILITY_UNOBSERVED')
        if not reasons: reasons.append('NO_SAFE_REVERSIBLE_ACTION')
        return PlanResult(Decision.HOLD,tuple(dict.fromkeys(reasons)),ordered_all,None,None,False,False)
    if approval_needed:
        chosen=sorted(approval_needed,key=_rank_tuple)[0]
        return PlanResult(Decision.HUMAN_APPROVAL,('IRREVERSIBLE_OR_LOW_REVERSIBILITY_APPROVAL_REQUIRED',),ordered_all,chosen.action_id,chosen.rollback_action_id,False,True)
    return PlanResult(Decision.HOLD,('NO_SAFE_REVERSIBLE_ACTION',),ordered_all,None,None,False,False)


def default_policy()->PlannerPolicy:
    return PlannerPolicy('PLAN-BIND','STATE-EPOCH-1')

def default_goal()->Goal:
    return Goal('GOAL-1',0.90,'PLAN-BIND','STATE-EPOCH-1')

def default_actions()->tuple[CandidateAction,...]:
    b,e='PLAN-BIND','STATE-EPOCH-1'
    return (
        CandidateAction('DELETE','GOAL-1',1.0,0.0,1.0,Risk.HIGH,None,True,True,None,b,e),
        CandidateAction('QUARANTINE','GOAL-1',1.0,0.95,1.2,Risk.LOW,'RESTORE',False,True,None,b,e),
        CandidateAction('ARCHIVE','GOAL-1',0.95,0.80,0.8,Risk.LOW,'UNARCHIVE',False,True,None,b,e),
    )

def default_approvals()->tuple[ApprovalEvidence,...]: return ()


def _registry_fp(goal,actions,approvals,policy):
    return _fp({'goal':_fp(goal),'policy':_fp(policy),'actions':sorted((x.action_id,_fp(x)) for x in actions),'approvals':sorted((x.evidence_id,_fp(x)) for x in approvals)})

def prepare_state(policy:PlannerPolicy,goal:Goal,actions:tuple[CandidateAction,...],approvals:tuple[ApprovalEvidence,...],*,binding:str,state_epoch:str)->PreparedPlannerState:
    if binding!=policy.binding or state_epoch!=policy.state_epoch: raise ValueError('PREPARED_BINDING_OR_EPOCH_MISMATCH')
    # Canonicalize collection order so independently reconstructed Prepared State has exact identity.
    actions=tuple(sorted(actions,key=lambda x:x.action_id))
    approvals=tuple(sorted(approvals,key=lambda x:x.evidence_id))
    af=tuple((x.action_id,_fp(x)) for x in actions)
    ef=tuple((x.evidence_id,_fp(x)) for x in approvals)
    pf,gf=_fp(policy),_fp(goal)
    context=_fp({'policy':pf,'goal':gf})
    dep=_fp({'actions':af,'approvals':ef})
    reg=_registry_fp(goal,actions,approvals,policy)
    result=evaluate(goal,actions,approvals,policy)
    return PreparedPlannerState(policy,goal,actions,approvals,af,ef,pf,gf,context,dep,reg,result,binding,state_epoch)

def validate_prepared_integrity(st:PreparedPlannerState)->bool:
    if st.binding!=st.policy.binding or st.state_epoch!=st.policy.state_epoch: return False
    if st.policy_fingerprint!=_fp(st.policy) or st.goal_fingerprint!=_fp(st.goal): return False
    if st.action_fingerprints!=tuple(sorted((x.action_id,_fp(x)) for x in st.actions)): return False
    if st.approval_fingerprints!=tuple(sorted((x.evidence_id,_fp(x)) for x in st.approvals)): return False
    if st.context_fingerprint!=_fp({'policy':st.policy_fingerprint,'goal':st.goal_fingerprint}): return False
    if st.dependency_fingerprint!=_fp({'actions':st.action_fingerprints,'approvals':st.approval_fingerprints}): return False
    if st.registry_fingerprint!=_registry_fp(st.goal,st.actions,st.approvals,st.policy): return False
    return st.precomputed_result==evaluate(st.goal,st.actions,st.approvals,st.policy)

def evaluate_prepared(st:PreparedPlannerState,*,current_context_fingerprint:str,current_dependency_fingerprint:str,current_registry_fingerprint:str,prepared_integrity_validated:bool)->PlanResult:
    if not prepared_integrity_validated:
        return PlanResult(Decision.HOLD,('PREPARED_INTEGRITY_UNVERIFIED',),(),None,None,False,False)
    if current_context_fingerprint!=st.context_fingerprint or current_dependency_fingerprint!=st.dependency_fingerprint or current_registry_fingerprint!=st.registry_fingerprint:
        return PlanResult(Decision.HOLD,('PREPARED_STATE_STALE',),(),None,None,False,False)
    return st.precomputed_result

def make_delta(base:PreparedPlannerState,target:PreparedPlannerState)->PlannerStateDelta:
    ba={x.action_id:x for x in base.actions}; ta={x.action_id:x for x in target.actions}
    be={x.evidence_id:x for x in base.approvals}; te={x.evidence_id:x for x in target.approvals}
    changed_a=tuple(ta[k] for k in sorted(ta) if k not in ba or _fp(ta[k])!=_fp(ba[k]))
    removed_a=tuple(sorted(set(ba)-set(ta)))
    changed_e=tuple(te[k] for k in sorted(te) if k not in be or _fp(te[k])!=_fp(be[k]))
    removed_e=tuple(sorted(set(be)-set(te)))
    return PlannerStateDelta(base.registry_fingerprint,target.registry_fingerprint,changed_a,removed_a,changed_e,removed_e,target.goal,target.policy,target.binding,target.state_epoch)

def apply_delta(base:PreparedPlannerState,delta:PlannerStateDelta)->PreparedPlannerState:
    if base.registry_fingerprint!=delta.base_fingerprint: raise ValueError('DELTA_BASE_MISMATCH')
    a={x.action_id:x for x in base.actions}; e={x.evidence_id:x for x in base.approvals}
    for k in delta.removed_action_ids: a.pop(k,None)
    for x in delta.changed_actions: a[x.action_id]=x
    for k in delta.removed_approval_ids: e.pop(k,None)
    for x in delta.changed_approvals: e[x.evidence_id]=x
    st=prepare_state(delta.target_policy,delta.target_goal,tuple(a[k] for k in sorted(a)),tuple(e[k] for k in sorted(e)),binding=delta.binding,state_epoch=delta.state_epoch)
    if st.registry_fingerprint!=delta.target_fingerprint: raise ValueError('DELTA_TARGET_MISMATCH')
    return st

def missing_only_sync_plan(target:PreparedPlannerState,known_action_fps:dict[str,str],known_approval_fps:dict[str,str])->PlannerSyncPlan:
    miss_a=tuple(k for k,v in target.action_fingerprints if known_action_fps.get(k)!=v)
    miss_e=tuple(k for k,v in target.approval_fingerprints if known_approval_fps.get(k)!=v)
    meta=len(_canon({'actions':miss_a,'approvals':miss_e,'context':target.context_fingerprint,'dependency':target.dependency_fingerprint}))
    full=(len(miss_a)+len(miss_e)) >= max(1,len(target.action_fingerprints)+len(target.approval_fingerprints))
    return PlannerSyncPlan(miss_a,miss_e,meta,full)

def full_registry_bytes(st:PreparedPlannerState)->int:
    return len(_canon({'goal':st.goal,'policy':st.policy,'actions':st.actions,'approvals':st.approvals,'context':st.context_fingerprint,'dependency':st.dependency_fingerprint}))

def delta_bytes(delta:PlannerStateDelta)->int: return len(_canon(delta))

def default_evaluation()->PlanResult:
    return evaluate(default_goal(),default_actions(),default_approvals(),default_policy())
