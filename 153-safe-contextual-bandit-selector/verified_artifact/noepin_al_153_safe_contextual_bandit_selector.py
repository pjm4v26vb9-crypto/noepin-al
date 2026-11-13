"""NOEPIN AL 153 — Safe Contextual Bandit Selector — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-153
DCSR: DIRECT INTEGRATION / 直接統合.

Filters unsafe arms before reward-based selection, estimates reward only across safe candidates, and
emits a deterministic selection candidate plus a bounded exploration-probability candidate. Unsafe
arms are never explored merely to learn. Shadow/Canary state has no Production Authority. Selected
Arm Candidate != Routing/Tool Execution. Exploration Probability Candidate != Exploration Execution.
Reward Evidence != Truth. Safety Filter PASS != Permission Grant or Safety Proof. This core performs
no model update, reward-history mutation, deployment, rollback, tool/file/network execution, or
external write. DCSR reconstruction cannot create Truth, Domain Authority, Permission, Safety Proof,
Approval, Action, or Action Success.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str,Enum): ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class EngineState(str,Enum):
    SAFE_ARM_SELECTED_CANDIDATE='SAFE_ARM_SELECTED_CANDIDATE'; NO_SAFE_ARM_CANDIDATE='NO_SAFE_ARM_CANDIDATE'; FALLBACK_CANDIDATE='FALLBACK_CANDIDATE'; INVALID='INVALID'
class NextAction(str,Enum):
    CONTINUE_SELECTION_CANDIDATE='CONTINUE_SELECTION_CANDIDATE'; HOLD_NO_SAFE_ARM_CANDIDATE='HOLD_NO_SAFE_ARM_CANDIDATE'; USE_KNOWN_SAFE_FALLBACK_CANDIDATE='USE_KNOWN_SAFE_FALLBACK_CANDIDATE'; REVIEW_BANDIT_CANDIDATE='REVIEW_BANDIT_CANDIDATE'
class Escalation(str,Enum):
    NONE='NONE'; NO_SAFE_ARM='NO_SAFE_ARM'; POLICY_UNVERIFIED='POLICY_UNVERIFIED'; SAFETY_REGRESSION='SAFETY_REGRESSION'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'
@dataclass(frozen=True)
class BanditContext:
    context_id:str; features:tuple[float,...]; critical:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class CandidateArm:
    arm_id:str; feature_weights:tuple[float,...]; prior_reward:float; hard_safe:bool; trust_score:float; enabled:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class RewardRecord:
    record_id:str; arm_id:str; reward:float; safe_outcome:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class SafetyConstraints:
    constraint_id:str; min_trust_for_selection:float; full_exploration_trust:float; max_exploration_probability:float; critical_max_exploration_probability:float; exploration_bonus:float; policy_verified:bool; known_safe_fallback_arm_id:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class ShadowCanaryState:
    state_id:str; stable_version:str; canary_version:str; shadow_version:str; safety_regression:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class BanditRequest:
    request_id:str; context:BanditContext; arms:tuple[CandidateArm,...]; reward_history:tuple[RewardRecord,...]; safety:SafetyConstraints; shadow:ShadowCanaryState; binding:str; state_epoch:str
@dataclass(frozen=True)
class SafetyTraceEntry:
    arm_id:str; included:bool; reason:str; estimated_reward:float; observation_count:int; selection_score:float; trust_limited:bool
@dataclass(frozen=True)
class BanditResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState; selected_arm_id:str|None; exploration_probability:float; safety_filter_trace:tuple[SafetyTraceEntry,...]; eligible_update_arm_ids:tuple[str,...]; fallback_arm_id:str|None; reasons:tuple[str,...]; next_gate_candidate:bool
    arm_executed:bool=False; routing_executed:bool=False; exploration_executed:bool=False; unsafe_arm_explored:bool=False; reward_history_mutated:bool=False; model_updated:bool=False; online_learning_committed:bool=False; safety_constraints_modified:bool=False; policy_modified:bool=False; canary_deployed:bool=False; shadow_promoted_to_production:bool=False; rollback_executed:bool=False; fallback_executed:bool=False; tool_invoked:bool=False; file_write_executed:bool=False; network_send_executed:bool=False; dcsr_reconstruction_created_fact:bool=False; sender_authority_inherited:bool=False; sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False; permission_granted:bool=False; approval_executed:bool=False; authority_granted:bool=False; stop_executed:bool=False; action_executed:bool=False; plan_committed:bool=False; publish_executed:bool=False; external_write_performed:bool=False; world_truth_proven:bool=False; domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedBanditState:
    request:BanditRequest; result:BanditResult; context_fingerprint:str; arms_fingerprint:str; history_fingerprint:str; safety_fingerprint:str; shadow_fingerprint:str; request_context_fingerprint:str; result_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class BanditDelta:
    context_changed:bool; arms_changed:bool; history_changed:bool; safety_changed:bool; shadow_changed:bool; request_context_changed:bool; from_manifest_fingerprint:str; to_manifest_fingerprint:str
@dataclass(frozen=True)
class MissingOnlyPlan: missing_or_changed_record_ids:tuple[str,...]; metadata_bytes_required:int; full_resend_required:bool

def _obj(v):
    if isinstance(v,Enum): return v.value
    if is_dataclass(v): return {f.name:_obj(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v,dict): return {str(k):_obj(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(tuple,list)): return [_obj(x) for x in v]
    return v
def _canon(v): return json.dumps(_obj(v),ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def _fp(v): return sha256(_canon(v)).hexdigest()

def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    ctx=BanditContext('CTX-153-A',(1.0,0.4,0.2),False,b,e)
    arms=(
        CandidateArm('ARM-SAFE-A',(0.75,0.20,0.10),0.60,True,0.92,True,b,e),
        CandidateArm('ARM-SAFE-B',(0.55,0.30,0.25),0.58,True,0.78,True,b,e),
        CandidateArm('ARM-UNSAFE-HIGH',(0.99,0.99,0.99),0.99,False,0.99,True,b,e),
        CandidateArm('ARM-LOW-TRUST',(0.70,0.20,0.20),0.64,True,0.30,True,b,e),
    )
    hist=(
        RewardRecord('R1','ARM-SAFE-A',0.82,True,b,e),RewardRecord('R2','ARM-SAFE-A',0.78,True,b,e),RewardRecord('R3','ARM-SAFE-A',0.80,True,b,e),
        RewardRecord('R4','ARM-SAFE-B',0.62,True,b,e),RewardRecord('R5','ARM-SAFE-B',0.65,True,b,e),
        RewardRecord('R6','ARM-UNSAFE-HIGH',1.00,False,b,e),RewardRecord('R7','ARM-LOW-TRUST',0.90,True,b,e),
    )
    saf=SafetyConstraints('SAFE-153-A',0.20,0.70,0.20,0.05,0.08,True,'ARM-SAFE-A',b,e)
    sh=ShadowCanaryState('SC-153-A','stable-v1','canary-v2','shadow-v2',False,b,e)
    return BanditRequest('REQ-153-A',ctx,arms,hist,saf,sh,b,e)

def _invalid(req,reason):
    return BanditResult(Decision.HOLD,NextAction.REVIEW_BANDIT_CANDIDATE,Escalation.INVALID_CONFIGURATION,EngineState.INVALID,None,0.0,(),(),None,(reason,'NO_ARM_EXECUTION','NO_ONLINE_UPDATE_COMMIT'),False)

def _validate(q):
    if not q.request_id or not q.binding or not q.state_epoch:return 'EMPTY_REQUEST_CONTEXT'
    for x,n in ((q.context,'CONTEXT'),(q.safety,'SAFETY'),(q.shadow,'SHADOW')):
        if x.binding!=q.binding or x.state_epoch!=q.state_epoch:return n+'_BINDING_MISMATCH'
    if not q.context.context_id or not q.context.features:return 'INVALID_CONTEXT'
    if any((not isinstance(v,(int,float))) or not math.isfinite(v) for v in q.context.features):return 'INVALID_CONTEXT_FEATURE'
    seen=set()
    for a in q.arms:
        if a.binding!=q.binding or a.state_epoch!=q.state_epoch:return 'ARM_BINDING_MISMATCH'
        if not a.arm_id or a.arm_id in seen:return 'INVALID_ARM_ID'
        seen.add(a.arm_id)
        if len(a.feature_weights)!=len(q.context.features):return 'ARM_FEATURE_DIMENSION_MISMATCH'
        if not (0<=a.prior_reward<=1 and 0<=a.trust_score<=1):return 'INVALID_ARM_RANGE'
        if any((not isinstance(v,(int,float))) or not math.isfinite(v) for v in a.feature_weights):return 'INVALID_ARM_WEIGHT'
    if not q.arms:return 'NO_ARMS'
    for r in q.reward_history:
        if r.binding!=q.binding or r.state_epoch!=q.state_epoch:return 'REWARD_BINDING_MISMATCH'
        if not r.record_id or r.arm_id not in seen or not (0<=r.reward<=1):return 'INVALID_REWARD_RECORD'
    s=q.safety
    if not s.constraint_id or not (0<=s.min_trust_for_selection<=s.full_exploration_trust<=1):return 'INVALID_TRUST_BOUNDS'
    if not (0<=s.critical_max_exploration_probability<=s.max_exploration_probability<=1):return 'INVALID_EXPLORATION_BOUNDS'
    if s.exploration_bonus<0:return 'INVALID_EXPLORATION_BONUS'
    if s.known_safe_fallback_arm_id and s.known_safe_fallback_arm_id not in seen:return 'INVALID_FALLBACK_ARM'
    return None

def _arm_evidence(q,a):
    rows=[r for r in q.reward_history if r.arm_id==a.arm_id and r.safe_outcome]
    mean=(sum(r.reward for r in rows)/len(rows)) if rows else a.prior_reward
    contextual=sum(x*w for x,w in zip(q.context.features,a.feature_weights))/max(1,len(q.context.features))
    contextual=max(0.0,min(1.0,contextual))
    estimate=max(0.0,min(1.0,0.75*mean+0.25*contextual))
    bonus=q.safety.exploration_bonus/math.sqrt(len(rows)+1)
    return estimate,len(rows),estimate+bonus

def evaluate(q):
    bad=_validate(q)
    if bad:return _invalid(q,bad)
    base=('SELECTED_ARM_IS_CANDIDATE_NOT_ROUTING_EXECUTION','EXPLORATION_PROBABILITY_IS_CANDIDATE_NOT_EXPLORATION_EXECUTION','SHADOW_CANARY_HAVE_NO_PRODUCTION_AUTHORITY','SAFETY_FILTER_PASS_IS_NOT_PERMISSION_OR_SAFETY_PROOF','NO_ONLINE_REWARD_UPDATE_COMMIT')
    if not q.safety.policy_verified:
        return BanditResult(Decision.HOLD,NextAction.REVIEW_BANDIT_CANDIDATE,Escalation.POLICY_UNVERIFIED,EngineState.INVALID,None,0.0,(),(),q.safety.known_safe_fallback_arm_id,base+('POLICY_UNVERIFIED_HOLD',),False)
    trace=[]; eligible=[]
    for a in q.arms:
        est,n,score=_arm_evidence(q,a)
        if not a.enabled:
            trace.append(SafetyTraceEntry(a.arm_id,False,'ARM_DISABLED',est,n,score,False)); continue
        if not a.hard_safe:
            trace.append(SafetyTraceEntry(a.arm_id,False,'HARD_SAFETY_FILTER_REJECT',est,n,score,False)); continue
        if a.trust_score<q.safety.min_trust_for_selection:
            trace.append(SafetyTraceEntry(a.arm_id,False,'TRUST_BELOW_SELECTION_MINIMUM',est,n,score,True)); continue
        limited=a.trust_score<q.safety.full_exploration_trust
        trace.append(SafetyTraceEntry(a.arm_id,True,'SAFE_ARM_TRUST_LIMITED' if limited else 'SAFE_ARM',est,n,score,limited)); eligible.append((score,est,a,n,limited))
    if q.shadow.safety_regression:
        fb=q.safety.known_safe_fallback_arm_id
        return BanditResult(Decision.HOLD,NextAction.USE_KNOWN_SAFE_FALLBACK_CANDIDATE,Escalation.SAFETY_REGRESSION,EngineState.FALLBACK_CANDIDATE,None,0.0,tuple(trace),tuple(sorted(a.arm_id for _,_,a,_,_ in eligible)),fb,base+('SAFETY_REGRESSION_FALLBACK_CANDIDATE_ONLY',),False)
    if not eligible:
        return BanditResult(Decision.HOLD,NextAction.HOLD_NO_SAFE_ARM_CANDIDATE,Escalation.NO_SAFE_ARM,EngineState.NO_SAFE_ARM_CANDIDATE,None,0.0,tuple(trace),(),q.safety.known_safe_fallback_arm_id,base+('NO_SAFE_ARM_DO_NOT_EXPLORE_UNSAFE',),True)
    eligible.sort(key=lambda z:(-z[0],-z[1],z[2].arm_id)); score,est,sel,n,limited=eligible[0]
    p=q.safety.critical_max_exploration_probability if q.context.critical else q.safety.max_exploration_probability
    if limited and q.safety.full_exploration_trust>0:
        p*=max(0.0,min(1.0,sel.trust_score/q.safety.full_exploration_trust))
    p=max(0.0,min(1.0,p))
    reasons=base+('UNSAFE_ARMS_EXCLUDED_BEFORE_REWARD_SELECTION','CRITICAL_EXPLORATION_REDUCED' if q.context.critical else 'BOUNDED_EXPLORATION','TRUST_LIMIT_APPLIED' if limited else 'TRUST_FULL_EXPLORATION_BOUND')
    return BanditResult(Decision.ALLOW,NextAction.CONTINUE_SELECTION_CANDIDATE,Escalation.NONE,EngineState.SAFE_ARM_SELECTED_CANDIDATE,sel.arm_id,p,tuple(trace),tuple(sorted(a.arm_id for _,_,a,_,_ in eligible)),q.safety.known_safe_fallback_arm_id,reasons,True)

def default_evaluation():return evaluate(default_request())
def prepare_state(q,binding,state_epoch):
    if q.binding!=binding or q.state_epoch!=state_epoch: raise ValueError('prepared binding mismatch')
    r=evaluate(q); c=_fp(q.context); a=_fp(q.arms); h=_fp(q.reward_history); s=_fp(q.safety); sh=_fp(q.shadow); rc=_fp((q.request_id,q.binding,q.state_epoch)); rr=_fp(r); integ=_fp((c,a,h,s,sh,rc,rr,binding,state_epoch))
    return PreparedBanditState(q,r,c,a,h,s,sh,rc,rr,integ,binding,state_epoch)
def evaluate_prepared(st,*,integrity_validated,current_context_fingerprint,current_arms_fingerprint,current_history_fingerprint,current_safety_fingerprint,current_shadow_fingerprint,current_request_context_fingerprint,current_result_fingerprint):
    vals=(current_context_fingerprint,current_arms_fingerprint,current_history_fingerprint,current_safety_fingerprint,current_shadow_fingerprint,current_request_context_fingerprint,current_result_fingerprint)
    exp=(st.context_fingerprint,st.arms_fingerprint,st.history_fingerprint,st.safety_fingerprint,st.shadow_fingerprint,st.request_context_fingerprint,st.result_fingerprint)
    if not integrity_validated or vals!=exp:return _invalid(st.request,'PREPARED_STATE_INTEGRITY_MISMATCH')
    integ=_fp((*exp,st.binding,st.state_epoch))
    if integ!=st.integrity_fingerprint:return _invalid(st.request,'PREPARED_INTEGRITY_FINGERPRINT_MISMATCH')
    return st.result
def _manifest(st):return _fp((st.context_fingerprint,st.arms_fingerprint,st.history_fingerprint,st.safety_fingerprint,st.shadow_fingerprint,st.request_context_fingerprint,st.result_fingerprint))
def make_delta(a,b):return BanditDelta(a.context_fingerprint!=b.context_fingerprint,a.arms_fingerprint!=b.arms_fingerprint,a.history_fingerprint!=b.history_fingerprint,a.safety_fingerprint!=b.safety_fingerprint,a.shadow_fingerprint!=b.shadow_fingerprint,a.request_context_fingerprint!=b.request_context_fingerprint,_manifest(a),_manifest(b))
def plan_missing_only(a,b):
    d=make_delta(a,b); names=[]
    for flag,name in ((d.context_changed,'CONTEXT'),(d.arms_changed,'CANDIDATE_ARMS'),(d.history_changed,'REWARD_HISTORY'),(d.safety_changed,'SAFETY_CONSTRAINTS'),(d.shadow_changed,'SHADOW_CANARY_STATE'),(d.request_context_changed,'REQUEST_CONTEXT')):
        if flag:names.append(name)
    meta=len(_canon({'missing_or_changed_record_ids':names,'from':d.from_manifest_fingerprint,'to':d.to_manifest_fingerprint}))
    return MissingOnlyPlan(tuple(names),meta,False)
