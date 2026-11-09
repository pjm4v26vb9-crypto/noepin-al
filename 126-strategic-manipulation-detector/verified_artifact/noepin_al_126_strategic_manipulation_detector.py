"""NOEPIN AL 126 — Strategic Manipulation Detector — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-126
DCSR: DIRECT INTEGRATION / 直接統合.

Manipulation risk is an audit/control candidate only. It does not prove malicious intent, world truth,
identity authority, permission, authority revocation, action execution, safety, or action success.
Received DCSR state never automatically inherits sender authority, intent, agreement, permission,
or action-success authority.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str, Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class ManipulationClass(str, Enum):
    NO_SIGNAL='NO_SIGNAL'; CALIBRATION_ONLY='CALIBRATION_ONLY'; SUSPECT='SUSPECT'; HIGH_RISK='HIGH_RISK'; UNVERIFIABLE='UNVERIFIABLE'; INVALID='INVALID'
class NextAction(str, Enum):
    NORMAL_WEIGHT_CANDIDATE='NORMAL_WEIGHT_CANDIDATE'; CALIBRATION_CANDIDATE='CALIBRATION_CANDIDATE'; WEIGHT_REDUCTION_CANDIDATE='WEIGHT_REDUCTION_CANDIDATE'; AUTHORITY_RESTRICTION_CANDIDATE='AUTHORITY_RESTRICTION_CANDIDATE'; HOLD_REVIEW_CANDIDATE='HOLD_REVIEW_CANDIDATE'; HUMAN_REVIEW_CANDIDATE='HUMAN_REVIEW_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; SINGLE_ERROR='SINGLE_ERROR'; SELF_INTEREST_MISMATCH='SELF_INTEREST_MISMATCH'; EVIDENCE_OMISSION='EVIDENCE_OMISSION'; REPEATED_PATTERN='REPEATED_PATTERN'; UNVERIFIABLE='UNVERIFIABLE'; MIXED_HIGH_RISK='MIXED_HIGH_RISK'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'

@dataclass(frozen=True)
class ClaimAuditRecord:
    claim_id:str
    agent_id:str
    metric_id:str
    claimed_value:float
    observed_value:float|None
    tolerance:float
    self_interest_score:float
    incentive_direction:int
    evidence_ids:tuple[str,...]
    expected_evidence_ids:tuple[str,...]
    omitted_evidence_ids:tuple[str,...]
    prior_material_mismatch_count:int
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class ManipulationPolicy:
    mismatch_threshold:float=.15
    major_mismatch_threshold:float=.35
    self_interest_threshold:float=.60
    omission_ratio_threshold:float=.25
    repeated_pattern_threshold:int=3
    high_risk_vote_weight_cap:float=.20
    unverifiable_vote_weight_cap:float=.35
    calibration_trust_delta:float=-.02
    suspect_trust_delta:float=-.10
    high_risk_trust_delta:float=-.30
    allow_human_escalation:bool=True

@dataclass(frozen=True)
class ManipulationRequest:
    request_id:str
    records:tuple[ClaimAuditRecord,...]
    policy:ManipulationPolicy
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class MismatchTrace:
    claim_id:str
    agent_id:str
    mismatch:float|None
    mismatch_ratio:float|None
    omission_ratio:float
    self_interest_aligned:bool
    repeated_pattern:bool
    unverifiable:bool
    reasons:tuple[str,...]

@dataclass(frozen=True)
class AgentAdjustment:
    agent_id:str
    manipulation_class:ManipulationClass
    trust_delta:float
    vote_weight_cap:float
    authority_restriction_candidate:bool
    contributing_claim_ids:tuple[str,...]

@dataclass(frozen=True)
class ManipulationResult:
    decision:Decision
    next_action:NextAction
    escalation:Escalation
    manipulation_class:ManipulationClass
    reasons:tuple[str,...]
    mismatch_trace:tuple[MismatchTrace,...]
    trust_adjustments:tuple[AgentAdjustment,...]
    high_risk_agent_ids:tuple[str,...]
    unverifiable_claim_ids:tuple[str,...]
    next_gate_candidate:bool
    manipulation_promoted_to_malicious_intent:bool=False
    mismatch_promoted_to_intent_proof:bool=False
    trust_adjustment_executed:bool=False
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
class PreparedManipulationState:
    request:ManipulationRequest
    result:ManipulationResult
    context_fingerprint:str
    record_fingerprint:str
    policy_fingerprint:str
    outcome_fingerprint:str
    integrity_fingerprint:str
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class ManipulationDelta:
    changed_records:tuple[ClaimAuditRecord,...]
    removed_claim_ids:tuple[str,...]
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
def _manifest_fp(req): return _fp((req.records,req.binding,req.state_epoch))

def default_policy(): return ManipulationPolicy()

def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    records=(
        ClaimAuditRecord('C1','AGENT-A','QUALITY',.82,.80,.08,.15,1,('E1','E2'),('E1','E2'),(),0,b,e),
        ClaimAuditRecord('C2','AGENT-B','COST',.41,.44,.06,.10,-1,('E3',),('E3',),(),0,b,e),
        ClaimAuditRecord('C3','AGENT-A','TIME',.55,.58,.07,.20,-1,('E4','E5'),('E4','E5'),(),0,b,e),
    )
    return ManipulationRequest('DEFAULT-126',records,default_policy(),b,e)

def _invalid(reason):
    return ManipulationResult(Decision.HOLD,NextAction.HOLD_REVIEW_CANDIDATE,Escalation.INVALID_CONFIGURATION,ManipulationClass.INVALID,(reason,'NO_INTENT_PROOF','NO_AUTHORITY_EXECUTION'),(),(),(),(),False)

def _safe_scale(obs:float)->float: return max(abs(obs),1.0)

def _trace(rec:ClaimAuditRecord,p:ManipulationPolicy)->MismatchTrace:
    expected=set(rec.expected_evidence_ids)
    omitted=set(rec.omitted_evidence_ids)
    omission_ratio=(len(omitted & expected)/len(expected)) if expected else 0.0
    if rec.observed_value is None:
        return MismatchTrace(rec.claim_id,rec.agent_id,None,None,omission_ratio,False,rec.prior_material_mismatch_count>=p.repeated_pattern_threshold,True,('OUTCOME_UNVERIFIABLE','NO_TRUTH_INFERENCE'))
    delta=float(rec.claimed_value)-float(rec.observed_value)
    mismatch=abs(delta)
    ratio=mismatch/_safe_scale(float(rec.observed_value))
    direction=0 if abs(delta)<=float(rec.tolerance) else (1 if delta>0 else -1)
    aligned=(direction!=0 and rec.incentive_direction!=0 and direction==rec.incentive_direction and rec.self_interest_score>=p.self_interest_threshold)
    repeated=rec.prior_material_mismatch_count>=p.repeated_pattern_threshold
    reasons=[]
    if mismatch<=float(rec.tolerance): reasons.append('WITHIN_TOLERANCE')
    elif mismatch<p.mismatch_threshold: reasons.append('SMALL_ERROR')
    elif mismatch<p.major_mismatch_threshold: reasons.append('MATERIAL_MISMATCH')
    else: reasons.append('MAJOR_MISMATCH')
    if aligned: reasons.append('SELF_INTEREST_DIRECTION_ALIGNED')
    if omission_ratio>=p.omission_ratio_threshold: reasons.append('EVIDENCE_OMISSION_MATERIAL')
    if repeated: reasons.append('REPEATED_PATTERN')
    return MismatchTrace(rec.claim_id,rec.agent_id,mismatch,ratio,omission_ratio,aligned,repeated,False,tuple(reasons))

def evaluate(req:ManipulationRequest)->ManipulationResult:
    if not req.request_id or not req.binding or not req.state_epoch: return _invalid('INVALID_REQUEST_IDENTITY')
    p=req.policy
    nums=(p.mismatch_threshold,p.major_mismatch_threshold,p.self_interest_threshold,p.omission_ratio_threshold,p.high_risk_vote_weight_cap,p.unverifiable_vote_weight_cap,p.calibration_trust_delta,p.suspect_trust_delta,p.high_risk_trust_delta)
    if any(not _finite(x) for x in nums): return _invalid('INVALID_POLICY_NUMERIC')
    if not (0<=p.mismatch_threshold<=p.major_mismatch_threshold): return _invalid('INVALID_MISMATCH_THRESHOLDS')
    if not (0<=p.self_interest_threshold<=1 and 0<=p.omission_ratio_threshold<=1 and 0<=p.high_risk_vote_weight_cap<=1 and 0<=p.unverifiable_vote_weight_cap<=1): return _invalid('INVALID_POLICY_RANGE')
    if p.repeated_pattern_threshold<1: return _invalid('INVALID_REPEATED_PATTERN_THRESHOLD')
    ids=[r.claim_id for r in req.records]
    if any(not x for x in ids) or len(ids)!=len(set(ids)): return _invalid('DUPLICATE_OR_EMPTY_CLAIM')
    for r in req.records:
        if not r.agent_id or not r.metric_id or r.binding!=req.binding or r.state_epoch!=req.state_epoch: return _invalid('RECORD_IDENTITY_INVALID')
        if not _finite(r.claimed_value) or (r.observed_value is not None and not _finite(r.observed_value)) or not _finite(r.tolerance) or r.tolerance<0: return _invalid('VALUE_INVALID')
        if not _finite(r.self_interest_score) or not 0<=float(r.self_interest_score)<=1 or r.incentive_direction not in (-1,0,1) or r.prior_material_mismatch_count<0: return _invalid('INCENTIVE_OR_HISTORY_INVALID')
        if len(set(r.evidence_ids))!=len(r.evidence_ids) or len(set(r.expected_evidence_ids))!=len(r.expected_evidence_ids) or len(set(r.omitted_evidence_ids))!=len(r.omitted_evidence_ids): return _invalid('DUPLICATE_EVIDENCE_ID')
        if any(not x for x in (*r.evidence_ids,*r.expected_evidence_ids,*r.omitted_evidence_ids)): return _invalid('EMPTY_EVIDENCE_ID')
        if not set(r.omitted_evidence_ids).issubset(set(r.expected_evidence_ids)): return _invalid('OMITTED_EVIDENCE_NOT_EXPECTED')
    traces=tuple(_trace(r,p) for r in sorted(req.records,key=lambda x:(x.agent_id,x.claim_id)))
    by_agent={}
    for t in traces: by_agent.setdefault(t.agent_id,[]).append(t)
    adjustments=[]; high=[]; unverifiable=[]
    overall=ManipulationClass.NO_SIGNAL
    escalation=Escalation.NONE
    reasons=['AUDIT_SIGNAL_ONLY','NO_MALICIOUS_INTENT_PROOF']
    for aid in sorted(by_agent):
        ts=by_agent[aid]
        high_claims=[]; suspect_claims=[]; calibration=[]; unv=[]
        for t in ts:
            if t.unverifiable:
                unv.append(t.claim_id); unverifiable.append(t.claim_id); continue
            rec=next(r for r in req.records if r.claim_id==t.claim_id)
            major=(t.mismatch is not None and t.mismatch>=p.major_mismatch_threshold)
            material=(t.mismatch is not None and t.mismatch>=p.mismatch_threshold)
            omission=t.omission_ratio>=p.omission_ratio_threshold
            if major and t.self_interest_aligned:
                high_claims.append(t.claim_id)
            elif t.repeated_pattern and material and (t.self_interest_aligned or omission):
                high_claims.append(t.claim_id)
            elif material and (t.self_interest_aligned or omission):
                suspect_claims.append(t.claim_id)
            elif t.mismatch is not None and t.mismatch>rec.tolerance:
                calibration.append(t.claim_id)
        if high_claims:
            cls=ManipulationClass.HIGH_RISK; delta=p.high_risk_trust_delta; cap=p.high_risk_vote_weight_cap; auth=True; high.append(aid)
            overall=ManipulationClass.HIGH_RISK; escalation=Escalation.MIXED_HIGH_RISK if len(high_claims)>1 else Escalation.SELF_INTEREST_MISMATCH
        elif suspect_claims:
            cls=ManipulationClass.SUSPECT; delta=p.suspect_trust_delta; cap=max(p.high_risk_vote_weight_cap,.50); auth=False
            if overall not in (ManipulationClass.HIGH_RISK,): overall=ManipulationClass.SUSPECT
            if escalation==Escalation.NONE: escalation=Escalation.EVIDENCE_OMISSION if any(next(t for t in ts if t.claim_id==cid).omission_ratio>=p.omission_ratio_threshold for cid in suspect_claims) else Escalation.SELF_INTEREST_MISMATCH
        elif unv:
            cls=ManipulationClass.UNVERIFIABLE; delta=0.0; cap=p.unverifiable_vote_weight_cap; auth=False
            if overall==ManipulationClass.NO_SIGNAL: overall=ManipulationClass.UNVERIFIABLE
            if escalation==Escalation.NONE: escalation=Escalation.UNVERIFIABLE
        elif calibration:
            cls=ManipulationClass.CALIBRATION_ONLY; delta=p.calibration_trust_delta; cap=1.0; auth=False
            if overall==ManipulationClass.NO_SIGNAL: overall=ManipulationClass.CALIBRATION_ONLY
            if escalation==Escalation.NONE: escalation=Escalation.SINGLE_ERROR
        else:
            cls=ManipulationClass.NO_SIGNAL; delta=0.0; cap=1.0; auth=False
        contrib=tuple(sorted(high_claims+suspect_claims+calibration+unv))
        adjustments.append(AgentAdjustment(aid,cls,float(delta),float(cap),auth,contrib))
    if high:
        decision=Decision.HOLD
        next_action=NextAction.AUTHORITY_RESTRICTION_CANDIDATE
        reasons += ['MATERIAL_SELF_INTEREST_MISMATCH_OR_REPEAT','VOTE_AND_AUTHORITY_REDUCTION_CANDIDATE_ONLY']
        next_gate=False
    elif overall==ManipulationClass.SUSPECT:
        decision=Decision.ALLOW
        next_action=NextAction.WEIGHT_REDUCTION_CANDIDATE
        reasons += ['SUSPECT_PATTERN','WEIGHT_REDUCTION_CANDIDATE_ONLY']
        next_gate=True
    elif overall==ManipulationClass.UNVERIFIABLE:
        decision=Decision.ALLOW
        next_action=NextAction.WEIGHT_REDUCTION_CANDIDATE
        reasons += ['UNVERIFIABLE_CLAIM','LIMIT_WEIGHT_WITHOUT_TRUTH_INFERENCE']
        next_gate=True
    elif overall==ManipulationClass.CALIBRATION_ONLY:
        decision=Decision.ALLOW
        next_action=NextAction.CALIBRATION_CANDIDATE
        reasons += ['SIMPLE_ERROR_OR_NON_STRATEGIC_MISMATCH','CALIBRATION_NOT_MANIPULATION_PROOF']
        next_gate=True
    else:
        decision=Decision.ALLOW
        next_action=NextAction.NORMAL_WEIGHT_CANDIDATE
        reasons += ['NO_MATERIAL_STRATEGIC_SIGNAL']
        next_gate=True
    return ManipulationResult(decision,next_action,escalation,overall,tuple(reasons),traces,tuple(adjustments),tuple(sorted(high)),tuple(sorted(unverifiable)),next_gate)

def default_evaluation(): return evaluate(default_request())

def _fps(req,result):
    return (_fp((req.request_id,req.binding,req.state_epoch)),_fp(req.records),_fp(req.policy),_fp(result))
def _integrity_payload(cf,rf,pf,of,b,e): return (cf,rf,pf,of,b,e,'NOEPIN-AL-126-PREPARED-V1')
def prepare_state(req:ManipulationRequest,*,binding:str,state_epoch:str)->PreparedManipulationState:
    r=_invalid('PREPARED_BINDING_OR_EPOCH_MISMATCH') if binding!=req.binding or state_epoch!=req.state_epoch else evaluate(req)
    cf,rf,pf,of=_fps(req,r); integ=_fp(_integrity_payload(cf,rf,pf,of,binding,state_epoch))
    return PreparedManipulationState(req,r,cf,rf,pf,of,integ,binding,state_epoch)
def validate_prepared_integrity(st):
    return st.integrity_fingerprint==_fp(_integrity_payload(st.context_fingerprint,st.record_fingerprint,st.policy_fingerprint,st.outcome_fingerprint,st.binding,st.state_epoch))
def evaluate_prepared(st:PreparedManipulationState,*,integrity_validated:bool,current_context_fingerprint:str,current_record_fingerprint:str,current_policy_fingerprint:str,current_outcome_fingerprint:str)->ManipulationResult:
    ok=(integrity_validated and validate_prepared_integrity(st) and st.binding==st.request.binding and st.state_epoch==st.request.state_epoch and current_context_fingerprint==st.context_fingerprint and current_record_fingerprint==st.record_fingerprint and current_policy_fingerprint==st.policy_fingerprint and current_outcome_fingerprint==st.outcome_fingerprint)
    return st.result if ok else _invalid('PREPARED_REUSE_REJECTED')
def make_delta(old:PreparedManipulationState,new:PreparedManipulationState)->ManipulationDelta:
    oo={x.claim_id:x for x in old.request.records}; nn={x.claim_id:x for x in new.request.records}
    changed=tuple(nn[k] for k in sorted(nn) if k not in oo or _canon(nn[k])!=_canon(oo[k])); removed=tuple(sorted(set(oo)-set(nn)))
    return ManipulationDelta(changed,removed,_manifest_fp(old.request),_manifest_fp(new.request))
def plan_missing_only(old:PreparedManipulationState,new:PreparedManipulationState)->MissingOnlyPlan:
    d=make_delta(old,new); ids=tuple(sorted([f'CLAIM:{x.claim_id}' for x in d.changed_records]+[f'REMOVED_CLAIM:{x}' for x in d.removed_claim_ids])); meta=len(_canon({'from':d.from_manifest_fingerprint,'to':d.to_manifest_fingerprint,'ids':ids})); return MissingOnlyPlan(ids,meta,False)
