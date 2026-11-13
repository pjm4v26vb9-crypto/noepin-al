"""NOEPIN AL 152 — Guardrailed Online Threshold Tuner — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-152
DCSR: DIRECT INTEGRATION / 直接統合.

Produces bounded threshold-change candidates from outcome evidence. Shadow/Canary state has no
Production Authority. Proposed Threshold != Production Threshold Mutation. Expected Gain != Safety
Proof. Canary Candidate != Deployment. Fallback Candidate != Rollback Execution. This core performs
no policy mutation, threshold deployment, canary launch, rollback, file/network/tool execution, or
external write. DCSR reconstruction cannot create Truth, Domain Authority, Permission, Safety Proof,
Approval, Action, or Action Success.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json

class Decision(str,Enum): ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class EngineState(str,Enum):
    CANARY_PROPOSAL_CANDIDATE='CANARY_PROPOSAL_CANDIDATE'; NO_CHANGE_CANDIDATE='NO_CHANGE_CANDIDATE'; REJECTED_CANDIDATE='REJECTED_CANDIDATE'; INVALID='INVALID'
class NextAction(str,Enum):
    CONTINUE_CANARY_CANDIDATE='CONTINUE_CANARY_CANDIDATE'; KEEP_CURRENT_CANDIDATE='KEEP_CURRENT_CANDIDATE'; REJECT_PROPOSAL_CANDIDATE='REJECT_PROPOSAL_CANDIDATE'; REVIEW_TUNING_CANDIDATE='REVIEW_TUNING_CANDIDATE'
class Escalation(str,Enum):
    NONE='NONE'; DATA_INSUFFICIENT='DATA_INSUFFICIENT'; GUARDRAIL_VIOLATION='GUARDRAIL_VIOLATION'; CRITICAL_FALSE_ALLOW_REGRESSION='CRITICAL_FALSE_ALLOW_REGRESSION'; NO_GAIN='NO_GAIN'; DISTRIBUTION_SHIFT='DISTRIBUTION_SHIFT'; SHADOW_FAILED='SHADOW_FAILED'; POLICY_UNVERIFIED='POLICY_UNVERIFIED'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'
@dataclass(frozen=True)
class Outcome: outcome_id:str; score:float; should_hold:bool; critical:bool; weight:float; binding:str; state_epoch:str
@dataclass(frozen=True)
class ThresholdState: threshold_id:str; current:float; lower:float; upper:float; step:float; version:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class CostMatrix: matrix_id:str; false_allow_cost:float; critical_false_allow_cost:float; false_hold_cost:float; binding:str; state_epoch:str
@dataclass(frozen=True)
class GuardrailBounds: guardrail_id:str; min_samples:int; max_distribution_shift:float; min_expected_gain:float; policy_verified:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class ShadowState: shadow_id:str; evaluation_passed:bool; distribution_shift:float; stable_version:str; canary_version:str; shadow_version:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class ThresholdTuningRequest:
    request_id:str; outcomes:tuple[Outcome,...]; threshold:ThresholdState; costs:CostMatrix; guardrails:GuardrailBounds; shadow:ShadowState; binding:str; state_epoch:str
@dataclass(frozen=True)
class ThresholdTuningResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState; current_threshold:float; proposed_threshold:float; expected_gain:float; bound_check:bool; current_loss:float; proposed_loss:float; current_critical_false_allow:int; proposed_critical_false_allow:int; canary_candidate:bool; fallback_threshold:float; reasons:tuple[str,...]; next_gate_candidate:bool
    threshold_mutated:bool=False; policy_modified:bool=False; guardrail_modified:bool=False; canary_deployed:bool=False; shadow_promoted_to_production:bool=False; rollback_executed:bool=False; model_updated:bool=False; online_learning_committed:bool=False; tool_invoked:bool=False; file_write_executed:bool=False; network_send_executed:bool=False; dcsr_reconstruction_created_fact:bool=False; sender_authority_inherited:bool=False; sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False; permission_granted:bool=False; approval_executed:bool=False; authority_granted:bool=False; stop_executed:bool=False; action_executed:bool=False; plan_committed:bool=False; publish_executed:bool=False; external_write_performed:bool=False; world_truth_proven:bool=False; domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedThresholdState:
    request:ThresholdTuningRequest; result:ThresholdTuningResult; outcome_fingerprint:str; threshold_fingerprint:str; cost_fingerprint:str; guardrail_fingerprint:str; shadow_fingerprint:str; request_context_fingerprint:str; outcome_result_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class ThresholdDelta:
    outcome_changed:bool; threshold_changed:bool; cost_changed:bool; guardrail_changed:bool; shadow_changed:bool; request_context_changed:bool; from_manifest_fingerprint:str; to_manifest_fingerprint:str
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
    outs=(Outcome('O1',0.85,True,True,1,b,e),Outcome('O2',0.78,True,False,1,b,e),Outcome('O3',0.72,True,False,1,b,e),Outcome('O4',0.55,False,False,1,b,e),Outcome('O5',0.58,False,False,1,b,e),Outcome('O6',0.20,False,False,1,b,e),Outcome('O7',0.30,False,False,1,b,e),Outcome('O8',0.90,True,True,1,b,e))
    t=ThresholdState('TH-152-A',0.50,0.40,0.70,0.05,'stable-v1',b,e)
    c=CostMatrix('COST-152-A',4,12,1,b,e)
    g=GuardrailBounds('GR-152-A',8,0.20,0.10,True,b,e)
    s=ShadowState('SH-152-A',True,0.02,'stable-v1','canary-v2','shadow-v2',b,e)
    return ThresholdTuningRequest('REQ-152-A',outs,t,c,g,s,b,e)
def _invalid(req,reason):
    cur=getattr(getattr(req,'threshold',None),'current',0.0)
    return ThresholdTuningResult(Decision.HOLD,NextAction.REVIEW_TUNING_CANDIDATE,Escalation.INVALID_CONFIGURATION,EngineState.INVALID,cur,cur,0.0,False,0.0,0.0,0,0,False,cur,(reason,'NO_PRODUCTION_THRESHOLD_MUTATION','NO_CANARY_DEPLOYMENT'),False)
def _validate(q):
    if not q.request_id or not q.binding or not q.state_epoch:return 'EMPTY_REQUEST_CONTEXT'
    for x,n in ((q.threshold,'THRESHOLD'),(q.costs,'COST'),(q.guardrails,'GUARDRAIL'),(q.shadow,'SHADOW')):
        if x.binding!=q.binding or x.state_epoch!=q.state_epoch:return n+'_BINDING_MISMATCH'
    for o in q.outcomes:
        if o.binding!=q.binding or o.state_epoch!=q.state_epoch:return 'OUTCOME_BINDING_MISMATCH'
        if not o.outcome_id or not (0<=o.score<=1) or o.weight<=0:return 'INVALID_OUTCOME'
    t=q.threshold
    if not t.threshold_id or not (0<=t.lower<=t.current<=t.upper<=1) or t.step<=0:return 'INVALID_THRESHOLD_BOUNDS'
    c=q.costs
    if min(c.false_allow_cost,c.critical_false_allow_cost,c.false_hold_cost)<0:return 'INVALID_COST_MATRIX'
    g=q.guardrails
    if g.min_samples<1 or g.max_distribution_shift<0 or g.min_expected_gain<0:return 'INVALID_GUARDRAIL'
    return None
def _loss(q,thr):
    loss=0.0; crit=0
    for o in q.outcomes:
        predicted_hold=o.score>=thr
        if o.should_hold and not predicted_hold:
            if o.critical: crit+=1; loss+=q.costs.critical_false_allow_cost*o.weight
            else: loss+=q.costs.false_allow_cost*o.weight
        elif (not o.should_hold) and predicted_hold: loss+=q.costs.false_hold_cost*o.weight
    return loss,crit
def evaluate(q):
    bad=_validate(q)
    if bad:return _invalid(q,bad)
    t,g,s=q.threshold,q.guardrails,q.shadow
    base=('PROPOSED_THRESHOLD_IS_CANDIDATE_NOT_PRODUCTION_MUTATION','EXPECTED_GAIN_IS_NOT_SAFETY_PROOF','SHADOW_CANARY_HAVE_NO_PRODUCTION_AUTHORITY','NO_THRESHOLD_DEPLOYMENT')
    cur_loss,cur_crit=_loss(q,t.current)
    if not g.policy_verified:
        return ThresholdTuningResult(Decision.HOLD,NextAction.KEEP_CURRENT_CANDIDATE,Escalation.POLICY_UNVERIFIED,EngineState.NO_CHANGE_CANDIDATE,t.current,t.current,0,True,cur_loss,cur_loss,cur_crit,cur_crit,False,t.current,base+('POLICY_UNVERIFIED_KEEP_CURRENT',),False)
    if len(q.outcomes)<g.min_samples:
        return ThresholdTuningResult(Decision.HOLD,NextAction.KEEP_CURRENT_CANDIDATE,Escalation.DATA_INSUFFICIENT,EngineState.NO_CHANGE_CANDIDATE,t.current,t.current,0,True,cur_loss,cur_loss,cur_crit,cur_crit,False,t.current,base+('DATA_INSUFFICIENT_KEEP_CURRENT',),False)
    if s.distribution_shift>g.max_distribution_shift:
        return ThresholdTuningResult(Decision.HOLD,NextAction.KEEP_CURRENT_CANDIDATE,Escalation.DISTRIBUTION_SHIFT,EngineState.NO_CHANGE_CANDIDATE,t.current,t.current,0,True,cur_loss,cur_loss,cur_crit,cur_crit,False,t.current,base+('DISTRIBUTION_SHIFT_KEEP_CURRENT',),False)
    candidates=[]; x=t.current-4*t.step
    while x<=t.current+4*t.step+1e-12:
        v=round(x,10)
        if t.lower<=v<=t.upper:
            ls,cr=_loss(q,v); candidates.append((ls,cr,v))
        x+=t.step
    if not candidates:return _invalid(q,'NO_BOUNDED_CANDIDATES')
    safe=[z for z in candidates if z[1]<=cur_crit]
    if not safe:
        return ThresholdTuningResult(Decision.DENY,NextAction.REJECT_PROPOSAL_CANDIDATE,Escalation.CRITICAL_FALSE_ALLOW_REGRESSION,EngineState.REJECTED_CANDIDATE,t.current,t.current,0,True,cur_loss,cur_loss,cur_crit,cur_crit,False,t.current,base+('ALL_CANDIDATES_CRITICAL_FALSE_ALLOW_REGRESSION',),False)
    best=min(safe,key=lambda z:(z[0],abs(z[2]-t.current),z[2])); ploss,pcrit,pthr=best
    gain=cur_loss-ploss
    if not (t.lower<=pthr<=t.upper):
        return ThresholdTuningResult(Decision.DENY,NextAction.REJECT_PROPOSAL_CANDIDATE,Escalation.GUARDRAIL_VIOLATION,EngineState.REJECTED_CANDIDATE,t.current,t.current,0,False,cur_loss,cur_loss,cur_crit,cur_crit,False,t.current,base+('GUARDRAIL_REJECT',),False)
    if pcrit>cur_crit:
        return ThresholdTuningResult(Decision.DENY,NextAction.REJECT_PROPOSAL_CANDIDATE,Escalation.CRITICAL_FALSE_ALLOW_REGRESSION,EngineState.REJECTED_CANDIDATE,t.current,t.current,0,True,cur_loss,cur_loss,cur_crit,cur_crit,False,t.current,base+('CRITICAL_FALSE_ALLOW_REGRESSION_REJECT',),False)
    if gain<g.min_expected_gain:
        return ThresholdTuningResult(Decision.HOLD,NextAction.KEEP_CURRENT_CANDIDATE,Escalation.NO_GAIN,EngineState.NO_CHANGE_CANDIDATE,t.current,t.current,gain,True,cur_loss,cur_loss,cur_crit,cur_crit,False,t.current,base+('NO_SUFFICIENT_GAIN_KEEP_CURRENT',),False)
    if not s.evaluation_passed:
        return ThresholdTuningResult(Decision.HOLD,NextAction.KEEP_CURRENT_CANDIDATE,Escalation.SHADOW_FAILED,EngineState.NO_CHANGE_CANDIDATE,t.current,t.current,gain,True,cur_loss,cur_loss,cur_crit,cur_crit,False,t.current,base+('SHADOW_FAILED_KEEP_CURRENT',),False)
    return ThresholdTuningResult(Decision.ALLOW,NextAction.CONTINUE_CANARY_CANDIDATE,Escalation.NONE,EngineState.CANARY_PROPOSAL_CANDIDATE,t.current,pthr,gain,True,cur_loss,ploss,cur_crit,pcrit,True,t.current,base+('SUFFICIENT_IMPROVEMENT_CANARY_CANDIDATE',),True)
def default_evaluation(): return evaluate(default_request())
def prepare_state(q,binding,state_epoch):
    if q.binding!=binding or q.state_epoch!=state_epoch: raise ValueError('PREPARE_BINDING_MISMATCH')
    r=evaluate(q); of=_fp(q.outcomes); tf=_fp(q.threshold); cf=_fp(q.costs); gf=_fp(q.guardrails); sf=_fp(q.shadow); rf=_fp((q.request_id,q.binding,q.state_epoch)); rr=_fp(r)
    integ=_fp((of,tf,cf,gf,sf,rf,rr,binding,state_epoch))
    return PreparedThresholdState(q,r,of,tf,cf,gf,sf,rf,rr,integ,binding,state_epoch)
def evaluate_prepared(st,*,integrity_validated,current_outcome_fingerprint,current_threshold_fingerprint,current_cost_fingerprint,current_guardrail_fingerprint,current_shadow_fingerprint,current_request_context_fingerprint,current_outcome_result_fingerprint):
    if not integrity_validated:return _invalid(st.request,'PREPARED_INTEGRITY_NOT_VALIDATED')
    vals=(current_outcome_fingerprint,current_threshold_fingerprint,current_cost_fingerprint,current_guardrail_fingerprint,current_shadow_fingerprint,current_request_context_fingerprint,current_outcome_result_fingerprint)
    exp=(st.outcome_fingerprint,st.threshold_fingerprint,st.cost_fingerprint,st.guardrail_fingerprint,st.shadow_fingerprint,st.request_context_fingerprint,st.outcome_result_fingerprint)
    if vals!=exp:return _invalid(st.request,'PREPARED_FINGERPRINT_MISMATCH')
    if _fp(exp+(st.binding,st.state_epoch))!=st.integrity_fingerprint:return _invalid(st.request,'PREPARED_INTEGRITY_MISMATCH')
    return st.result
def _manifest(st):return _fp((st.outcome_fingerprint,st.threshold_fingerprint,st.cost_fingerprint,st.guardrail_fingerprint,st.shadow_fingerprint,st.request_context_fingerprint,st.outcome_result_fingerprint))
def make_delta(a,b):
    return ThresholdDelta(a.outcome_fingerprint!=b.outcome_fingerprint,a.threshold_fingerprint!=b.threshold_fingerprint,a.cost_fingerprint!=b.cost_fingerprint,a.guardrail_fingerprint!=b.guardrail_fingerprint,a.shadow_fingerprint!=b.shadow_fingerprint,a.request_context_fingerprint!=b.request_context_fingerprint,_manifest(a),_manifest(b))
def plan_missing_only(a,b):
    d=make_delta(a,b); names=[]
    for flag,name in ((d.outcome_changed,'OUTCOME_STREAM'),(d.threshold_changed,'CURRENT_THRESHOLDS'),(d.cost_changed,'COST_MATRIX'),(d.guardrail_changed,'GUARDRAIL_BOUNDS'),(d.shadow_changed,'SHADOW_CANARY_STATE'),(d.request_context_changed,'REQUEST_CONTEXT')):
        if flag:names.append(name)
    meta=len(_canon({'missing_or_changed_record_ids':names,'from':d.from_manifest_fingerprint,'to':d.to_manifest_fingerprint}))
    return MissingOnlyPlan(tuple(names),meta,False)
