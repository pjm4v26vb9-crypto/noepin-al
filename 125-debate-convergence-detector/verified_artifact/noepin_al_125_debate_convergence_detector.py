"""NOEPIN AL 125 — Debate Convergence Detector — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-125
DCSR: DIRECT INTEGRATION / 直接統合.
Convergence/Stop/Continue outputs are control candidates only. They do not become Truth, Safety Proof,
Permission Grant, Stop Execution, Action Execution, or Action Success.
Received DCSR state never automatically inherits sender authority, intent, agreement, permission,
or action-success authority.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str,Enum): ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class RiskClass(str,Enum): LOW='LOW'; MEDIUM='MEDIUM'; HIGH='HIGH'; CRITICAL='CRITICAL'; UNKNOWN='UNKNOWN'
class ConvergenceState(str,Enum): CONVERGED='CONVERGED'; CONTINUING='CONTINUING'; STAGNANT='STAGNANT'; OSCILLATING='OSCILLATING'; UNRESOLVED='UNRESOLVED'; MAX_TURN_STOP='MAX_TURN_STOP'; INVALID='INVALID'
class NextAction(str,Enum): STOP_DEBATE_CANDIDATE='STOP_DEBATE_CANDIDATE'; CONTINUE_DEBATE_CANDIDATE='CONTINUE_DEBATE_CANDIDATE'; HOLD_UNRESOLVED_REVIEW='HOLD_UNRESOLVED_REVIEW'; HUMAN_REVIEW_CANDIDATE='HUMAN_REVIEW_CANDIDATE'
class Escalation(str,Enum): NONE='NONE'; MATERIAL_ISSUE_UNRESOLVED='MATERIAL_ISSUE_UNRESOLVED'; OSCILLATION='OSCILLATION'; STAGNATION='STAGNATION'; MAX_TURNS='MAX_TURNS'; INSUFFICIENT_HISTORY='INSUFFICIENT_HISTORY'; UNKNOWN_RISK='UNKNOWN_RISK'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'
class IssueSeverity(str,Enum): LOW='LOW'; MEDIUM='MEDIUM'; HIGH='HIGH'; CRITICAL='CRITICAL'; UNKNOWN='UNKNOWN'

@dataclass(frozen=True)
class DebateTurn:
    turn_index:int; turn_id:str; agent_id:str; claim_cluster:str; evidence_ids:tuple[str,...]; position:float; binding:str; state_epoch:str
@dataclass(frozen=True)
class DebateIssue:
    issue_id:str; severity:IssueSeverity; resolved:bool
@dataclass(frozen=True)
class ConvergencePolicy:
    min_turns:int=4; window_size:int=4; convergence_novelty_threshold:float=.20; stagnation_novelty_threshold:float=.05; position_span_threshold:float=.12; oscillation_min_flips:int=3; oscillation_magnitude_threshold:float=.25; max_turns:int=20; high_risk_requires_all_material_resolved:bool=True; allow_human_escalation:bool=True
@dataclass(frozen=True)
class DebateRequest:
    request_id:str; risk:RiskClass; turns:tuple[DebateTurn,...]; issues:tuple[DebateIssue,...]; policy:ConvergencePolicy; binding:str; state_epoch:str
@dataclass(frozen=True)
class ConvergenceResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; convergence_state:ConvergenceState; reasons:tuple[str,...]; novelty_rate:float; position_span:float; sign_flips:int; unresolved_issue_ids:tuple[str,...]; unresolved_material_issue_ids:tuple[str,...]; considered_turns:int; max_turn_reached:bool; next_gate_candidate:bool
    convergence_promoted_to_truth:bool=False; confidence_promoted_to_safety_proof:bool=False; stop_candidate_promoted_to_stop_execution:bool=False; continue_candidate_promoted_to_permission:bool=False; sender_authority_inherited:bool=False; sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False; permission_granted:bool=False; approval_executed:bool=False; authority_granted:bool=False; stop_executed:bool=False; action_executed:bool=False; plan_committed:bool=False; publish_executed:bool=False; external_write_performed:bool=False; world_truth_proven:bool=False; domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedDebateState:
    request:DebateRequest; result:ConvergenceResult; context_fingerprint:str; turn_fingerprint:str; issue_fingerprint:str; policy_fingerprint:str; outcome_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class DebateDelta:
    changed_turns:tuple[DebateTurn,...]; removed_turn_ids:tuple[str,...]; changed_issues:tuple[DebateIssue,...]; removed_issue_ids:tuple[str,...]; from_manifest_fingerprint:str; to_manifest_fingerprint:str
@dataclass(frozen=True)
class MissingOnlyPlan:
    missing_or_changed_record_ids:tuple[str,...]; metadata_bytes_required:int; full_resend_required:bool

def _obj(v):
    if isinstance(v,Enum): return v.value
    if is_dataclass(v): return {f.name:_obj(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v,dict): return {str(k):_obj(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(tuple,list)): return [_obj(x) for x in v]
    return v
def _canon(v): return json.dumps(_obj(v),ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def _fp(v): return sha256(_canon(v)).hexdigest()
def _finite(x): return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(float(x))
def _manifest_fp(req): return _fp((req.turns,req.issues,req.binding,req.state_epoch))

def default_policy(): return ConvergencePolicy()
def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    turns=(
      DebateTurn(1,'T1','AGENT-A','PLAN-A',('E1','E2'),.20,b,e),
      DebateTurn(2,'T2','AGENT-B','PLAN-A',('E3',),.16,b,e),
      DebateTurn(3,'T3','AGENT-A','PLAN-A',('E1','E2','E3'),.15,b,e),
      DebateTurn(4,'T4','AGENT-B','PLAN-A',('E1','E2','E3'),.14,b,e),
      DebateTurn(5,'T5','AGENT-A','PLAN-A',('E1','E2','E3'),.13,b,e),
    )
    issues=(DebateIssue('ISSUE-LOW',IssueSeverity.LOW,True),)
    return DebateRequest('DEFAULT-125',RiskClass.MEDIUM,turns,issues,default_policy(),b,e)

def _invalid(reason):
    return ConvergenceResult(Decision.HOLD,NextAction.HOLD_UNRESOLVED_REVIEW,Escalation.INVALID_CONFIGURATION,ConvergenceState.INVALID,(reason,'CONVERGENCE_NOT_PROMOTED_TO_AUTHORITY'),1.0,2.0,0,(),(),0,False,False)

def _material(issue:DebateIssue)->bool: return issue.severity in (IssueSeverity.HIGH,IssueSeverity.CRITICAL,IssueSeverity.UNKNOWN)
def _ordered_turns(req): return tuple(sorted(req.turns,key=lambda t:(t.turn_index,t.turn_id)))

def _window_metrics(turns,policy):
    w=turns[-policy.window_size:]
    prior=turns[:-policy.window_size]
    seen=set()
    for t in prior: seen.update(t.evidence_ids)
    new=0; total=0
    for t in w:
        for eid in sorted(set(t.evidence_ids)):
            total+=1
            if eid not in seen:
                new+=1; seen.add(eid)
    novelty=(new/total) if total else 0.0
    ps=[float(t.position) for t in w]
    span=(max(ps)-min(ps)) if ps else 0.0
    flips=0
    prev=None
    for p in ps:
        s=1 if p>=policy.oscillation_magnitude_threshold else (-1 if p<=-policy.oscillation_magnitude_threshold else 0)
        if s and prev and s!=prev: flips+=1
        if s: prev=s
    return w,novelty,span,flips

def evaluate(req:DebateRequest)->ConvergenceResult:
    if not req.request_id or not req.binding or not req.state_epoch: return _invalid('INVALID_REQUEST_IDENTITY')
    p=req.policy
    nums=(p.convergence_novelty_threshold,p.stagnation_novelty_threshold,p.position_span_threshold,p.oscillation_magnitude_threshold)
    if p.min_turns<2 or p.window_size<2 or p.max_turns<p.min_turns or p.window_size>p.max_turns or p.oscillation_min_flips<1: return _invalid('INVALID_POLICY_COUNTS')
    if any(not _finite(x) for x in nums): return _invalid('INVALID_POLICY_NUMERIC')
    if not (0<=p.stagnation_novelty_threshold<=p.convergence_novelty_threshold<=1) or not (0<=p.position_span_threshold<=2) or not (0<=p.oscillation_magnitude_threshold<=1): return _invalid('INVALID_POLICY_THRESHOLD')
    tids=[t.turn_id for t in req.turns]; idxs=[t.turn_index for t in req.turns]
    if any(not x for x in tids) or len(tids)!=len(set(tids)) or len(idxs)!=len(set(idxs)): return _invalid('DUPLICATE_OR_EMPTY_TURN')
    for t in req.turns:
        if t.turn_index<1 or not t.agent_id or not t.claim_cluster or t.binding!=req.binding or t.state_epoch!=req.state_epoch: return _invalid('TURN_IDENTITY_INVALID')
        if not _finite(t.position) or not -1<=float(t.position)<=1: return _invalid('POSITION_INVALID')
        if any(not x for x in t.evidence_ids): return _invalid('EVIDENCE_ID_INVALID')
    iids=[i.issue_id for i in req.issues]
    if any(not x for x in iids) or len(iids)!=len(set(iids)): return _invalid('DUPLICATE_OR_EMPTY_ISSUE')
    if req.risk==RiskClass.UNKNOWN:
        unr=tuple(sorted(i.issue_id for i in req.issues if not i.resolved))
        mat=tuple(sorted(i.issue_id for i in req.issues if not i.resolved and _material(i)))
        return ConvergenceResult(Decision.HOLD,NextAction.HOLD_UNRESOLVED_REVIEW,Escalation.UNKNOWN_RISK,ConvergenceState.UNRESOLVED,('UNKNOWN_RISK_FAIL_SAFE','CONVERGENCE_NOT_PROMOTED_TO_TRUTH'),1.0,2.0,0,unr,mat,len(req.turns),len(req.turns)>=p.max_turns,False)
    turns=_ordered_turns(req)
    unresolved=tuple(sorted(i.issue_id for i in req.issues if not i.resolved))
    material=tuple(sorted(i.issue_id for i in req.issues if not i.resolved and _material(i)))
    maxed=len(turns)>=p.max_turns
    if len(turns)<p.min_turns:
        return ConvergenceResult(Decision.ALLOW,NextAction.CONTINUE_DEBATE_CANDIDATE,Escalation.INSUFFICIENT_HISTORY,ConvergenceState.CONTINUING,('INSUFFICIENT_HISTORY','CONTINUE_IS_CANDIDATE_ONLY'),1.0,2.0,0,unresolved,material,len(turns),maxed,True)
    w,novelty,span,flips=_window_metrics(turns,p)
    high=req.risk in (RiskClass.HIGH,RiskClass.CRITICAL)
    if high and p.high_risk_requires_all_material_resolved and material:
        return ConvergenceResult(Decision.HOLD,NextAction.HOLD_UNRESOLVED_REVIEW,Escalation.MATERIAL_ISSUE_UNRESOLVED,ConvergenceState.UNRESOLVED,('HIGH_RISK_MATERIAL_ISSUE_UNRESOLVED','NO_FALSE_CONVERGENCE','HOLD_IS_CANDIDATE_ONLY'),novelty,span,flips,unresolved,material,len(turns),maxed,False)
    if flips>=p.oscillation_min_flips:
        dec=Decision.HUMAN_APPROVAL if p.allow_human_escalation else Decision.HOLD
        return ConvergenceResult(dec,NextAction.HUMAN_REVIEW_CANDIDATE if dec==Decision.HUMAN_APPROVAL else NextAction.HOLD_UNRESOLVED_REVIEW,Escalation.OSCILLATION,ConvergenceState.OSCILLATING,('POSITION_OSCILLATION_DETECTED','SIMPLE_MAJORITY_NOT_USED'),novelty,span,flips,unresolved,material,len(turns),maxed,False)
    if novelty<=p.convergence_novelty_threshold and span<=p.position_span_threshold and not material:
        return ConvergenceResult(Decision.ALLOW,NextAction.STOP_DEBATE_CANDIDATE,Escalation.NONE,ConvergenceState.CONVERGED,('LOW_NOVELTY','POSITION_STABLE','NO_MATERIAL_UNRESOLVED_ISSUE','STOP_IS_CANDIDATE_ONLY'),novelty,span,flips,unresolved,material,len(turns),maxed,True)
    if maxed:
        dec=Decision.HUMAN_APPROVAL if p.allow_human_escalation else Decision.HOLD
        return ConvergenceResult(dec,NextAction.HUMAN_REVIEW_CANDIDATE if dec==Decision.HUMAN_APPROVAL else NextAction.HOLD_UNRESOLVED_REVIEW,Escalation.MAX_TURNS,ConvergenceState.MAX_TURN_STOP,('MAX_TURN_REACHED','NOT_PROMOTED_TO_CONVERGENCE'),novelty,span,flips,unresolved,material,len(turns),True,False)
    if novelty<=p.stagnation_novelty_threshold and span>p.position_span_threshold:
        dec=Decision.HUMAN_APPROVAL if p.allow_human_escalation else Decision.HOLD
        return ConvergenceResult(dec,NextAction.HUMAN_REVIEW_CANDIDATE if dec==Decision.HUMAN_APPROVAL else NextAction.HOLD_UNRESOLVED_REVIEW,Escalation.STAGNATION,ConvergenceState.STAGNANT,('LOW_NOVELTY_WITHOUT_POSITION_CONVERGENCE','STAGNATION_NOT_CONVERGENCE'),novelty,span,flips,unresolved,material,len(turns),False,False)
    return ConvergenceResult(Decision.ALLOW,NextAction.CONTINUE_DEBATE_CANDIDATE,Escalation.NONE,ConvergenceState.CONTINUING,('NOVEL_EVIDENCE_OR_POSITION_MOVEMENT_REMAINS','CONTINUE_IS_CANDIDATE_ONLY'),novelty,span,flips,unresolved,material,len(turns),False,True)

def default_evaluation(): return evaluate(default_request())

def _fps(req,result):
    return (_fp((req.request_id,req.risk,req.binding,req.state_epoch)),_fp(req.turns),_fp(req.issues),_fp(req.policy),_fp(result))
def _integrity_payload(cf,tf,ifp,pf,of,b,e): return (cf,tf,ifp,pf,of,b,e,'NOEPIN-AL-125-PREPARED-V1')
def prepare_state(req:DebateRequest,*,binding:str,state_epoch:str)->PreparedDebateState:
    if binding!=req.binding or state_epoch!=req.state_epoch:
        r=_invalid('PREPARED_BINDING_OR_EPOCH_MISMATCH')
    else: r=evaluate(req)
    cf,tf,ifp,pf,of=_fps(req,r); integ=_fp(_integrity_payload(cf,tf,ifp,pf,of,binding,state_epoch))
    return PreparedDebateState(req,r,cf,tf,ifp,pf,of,integ,binding,state_epoch)
def validate_prepared_integrity(st):
    return st.integrity_fingerprint==_fp(_integrity_payload(st.context_fingerprint,st.turn_fingerprint,st.issue_fingerprint,st.policy_fingerprint,st.outcome_fingerprint,st.binding,st.state_epoch))
def evaluate_prepared(st:PreparedDebateState,*,integrity_validated:bool,current_context_fingerprint:str,current_turn_fingerprint:str,current_issue_fingerprint:str,current_policy_fingerprint:str,current_outcome_fingerprint:str)->ConvergenceResult:
    ok=(integrity_validated and validate_prepared_integrity(st) and st.binding==st.request.binding and st.state_epoch==st.request.state_epoch and current_context_fingerprint==st.context_fingerprint and current_turn_fingerprint==st.turn_fingerprint and current_issue_fingerprint==st.issue_fingerprint and current_policy_fingerprint==st.policy_fingerprint and current_outcome_fingerprint==st.outcome_fingerprint)
    return st.result if ok else _invalid('PREPARED_REUSE_REJECTED')

def make_delta(old:PreparedDebateState,new:PreparedDebateState)->DebateDelta:
    ot={x.turn_id:x for x in old.request.turns}; nt={x.turn_id:x for x in new.request.turns}; oi={x.issue_id:x for x in old.request.issues}; ni={x.issue_id:x for x in new.request.issues}
    changed_t=tuple(nt[k] for k in sorted(nt) if k not in ot or _canon(nt[k])!=_canon(ot[k])); removed_t=tuple(sorted(set(ot)-set(nt)))
    changed_i=tuple(ni[k] for k in sorted(ni) if k not in oi or _canon(ni[k])!=_canon(oi[k])); removed_i=tuple(sorted(set(oi)-set(ni)))
    return DebateDelta(changed_t,removed_t,changed_i,removed_i,_manifest_fp(old.request),_manifest_fp(new.request))
def plan_missing_only(old:PreparedDebateState,new:PreparedDebateState)->MissingOnlyPlan:
    d=make_delta(old,new); ids=tuple(sorted([f'TURN:{x.turn_id}' for x in d.changed_turns]+[f'REMOVED_TURN:{x}' for x in d.removed_turn_ids]+[f'ISSUE:{x.issue_id}' for x in d.changed_issues]+[f'REMOVED_ISSUE:{x}' for x in d.removed_issue_ids])); meta=len(_canon({'from':d.from_manifest_fingerprint,'to':d.to_manifest_fingerprint,'ids':ids})); return MissingOnlyPlan(ids,meta,False)
