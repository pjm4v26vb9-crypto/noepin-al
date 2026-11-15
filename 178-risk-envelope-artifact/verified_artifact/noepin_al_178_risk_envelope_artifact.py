"""NOEPIN AL 178 — Risk Envelope Artifact — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-178
DCSR: DIRECT INTEGRATION / 直接統合.

Typed, deterministic, side-effect-free safety artifact that preserves seven required
risk dimensions, their observed values, allowed limits, critical-dimension labels,
and rationale. It extracts violations without turning Risk into Truth, Permission,
Permit issuance, Approval execution, Tool invocation, Action execution, or Action
Success. Cached or reconstructed Risk is never treated as current merely because a
fingerprint matches; current observed/limit/critical state must be re-bound.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math, re

class Decision(str, Enum):
    ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class EngineState(str, Enum):
    RISK_ENVELOPE_WITHIN_LIMIT_CANDIDATE='RISK_ENVELOPE_WITHIN_LIMIT_CANDIDATE'
    RISK_LIMIT_VIOLATION_CANDIDATE='RISK_LIMIT_VIOLATION_CANDIDATE'
    CRITICAL_RISK_VIOLATION_CANDIDATE='CRITICAL_RISK_VIOLATION_CANDIDATE'
    INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_RISK_POLICY_EVALUATION_CANDIDATE='CONTINUE_RISK_POLICY_EVALUATION_CANDIDATE'
    REVIEW_RISK_VIOLATION_CANDIDATE='REVIEW_RISK_VIOLATION_CANDIDATE'
    REACQUIRE_RISK_ENVELOPE_CANDIDATE='REACQUIRE_RISK_ENVELOPE_CANDIDATE'
    RETAIN_NO_ACTION_CANDIDATE='RETAIN_NO_ACTION_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'
    ENVELOPE_FINGERPRINT_MISMATCH='ENVELOPE_FINGERPRINT_MISMATCH'
    CONTEXT_OR_LIMIT_MISMATCH='CONTEXT_OR_LIMIT_MISMATCH'
    RISK_LIMIT_VIOLATION='RISK_LIMIT_VIOLATION'
    CRITICAL_RISK_VIOLATION='CRITICAL_RISK_VIOLATION'

REQUIRED_DIMENSIONS=(
    'availability','confidentiality','externality','integrity',
    'irreversibility','privilege','uncertainty'
)
REQUIRED_SET=frozenset(REQUIRED_DIMENSIONS)
_WS=re.compile(r'\s+')

def _obj(v):
    if isinstance(v,Enum): return v.value
    if is_dataclass(v): return {f.name:_obj(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v,dict): return {str(k):_obj(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(tuple,list)): return [_obj(x) for x in v]
    if isinstance(v,float):
        if not math.isfinite(v): raise ValueError('non-finite float')
        return v
    return v

def _canon(v): return json.dumps(_obj(v),ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def _fp(v): return sha256(_canon(v)).hexdigest()
def _norm(s): return _WS.sub(' ',str(s).strip())
def _dim(s): return _norm(s).casefold()

def _norm_values(values,name):
    if not isinstance(values,dict): raise ValueError(f'{name} must be a mapping')
    normalized={_dim(k):float(v) for k,v in values.items()}
    if set(normalized)!=REQUIRED_SET: raise ValueError(f'{name} dimensions must exactly match required seven dimensions')
    for k,v in normalized.items():
        if not math.isfinite(v) or not 0.0 <= v <= 1.0: raise ValueError(f'{name} value outside 0..1 for {k}')
    return tuple((k,normalized[k]) for k in REQUIRED_DIMENSIONS)

def _as_dict(items): return {k:v for k,v in items}

@dataclass(frozen=True)
class RiskEnvelope:
    schema:str; envelope_id:str; observed:tuple[tuple[str,float],...]; limits:tuple[tuple[str,float],...]
    critical_dimensions:tuple[str,...]; rationale:str; fingerprint:str

@dataclass(frozen=True)
class RiskEvaluationRequest:
    evaluation_id:str; envelope:RiskEnvelope
    current_observed:tuple[tuple[str,float],...]; current_limits:tuple[tuple[str,float],...]
    current_critical_dimensions:tuple[str,...]; context_id:str; binding:str; state_epoch:str

@dataclass(frozen=True)
class RiskEvaluationResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState
    evaluation_id:str; envelope_fingerprint_valid:bool; observed_match:bool; limits_match:bool
    critical_dimensions_match:bool; violations:tuple[str,...]; critical_violations:tuple[str,...]
    dimension_count:int; violation_count:int; critical_violation_count:int; next_gate_candidate:bool
    envelope_fingerprint:str; reasons:tuple[str,...]
    risk_promoted_to_truth:bool=False; risk_promoted_to_permission:bool=False
    risk_limit_promoted_to_permission:bool=False; violation_promoted_to_stop_execution:bool=False
    critical_violation_promoted_to_denial_execution:bool=False; permission_granted:bool=False
    policy_decision_executed:bool=False; approval_executed:bool=False; human_approval_executed:bool=False
    permit_issued:bool=False; tool_invoked:bool=False; action_executed:bool=False; action_success:bool=False
    stop_executed:bool=False; file_write_executed:bool=False; network_send_executed:bool=False
    external_write_performed:bool=False; authoritative_state_created:bool=False; cached_state_promoted:bool=False
    reconstructed_state_promoted:bool=False; stale_cached_risk_promoted_to_current:bool=False
    dcsr_changed_risk_value:bool=False; dcsr_changed_risk_limit:bool=False; dcsr_created_risk_truth:bool=False
    sender_authority_inherited:bool=False; sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False
    authority_granted:bool=False; world_truth_proven:bool=False; domain_authority_promoted:bool=False; safety_proven:bool=False

@dataclass(frozen=True)
class PreparedRiskState:
    request:RiskEvaluationRequest; result:RiskEvaluationResult; envelope_fingerprint:str
    context_fingerprint:str; result_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str

@dataclass(frozen=True)
class RiskChange:
    observed_changed:tuple[str,...]; limits_changed:tuple[str,...]; critical_changed:bool
    rationale_changed:bool; context_changed:bool; from_fingerprint:str; to_fingerprint:str

@dataclass(frozen=True)
class MissingOnlyPlan:
    missing_or_changed_record_ids:tuple[str,...]; metadata_bytes_required:int; full_resend_required:bool


def _payload(schema,envelope_id,observed,limits,critical_dimensions,rationale):
    return {'schema':schema,'envelope_id':envelope_id,'observed':observed,'limits':limits,
            'critical_dimensions':critical_dimensions,'rationale':rationale}

def build_envelope(*,envelope_id,observed,limits,critical_dimensions,rationale):
    eid=_norm(envelope_id); why=_norm(rationale)
    if not eid: raise ValueError('Envelope ID required')
    if not why: raise ValueError('Rationale required')
    obs=_norm_values(observed,'Observed'); lim=_norm_values(limits,'Limit')
    crit=tuple(sorted({_dim(x) for x in critical_dimensions}))
    if any(x not in REQUIRED_SET for x in crit): raise ValueError('Unknown Critical Dimension')
    schema='NOEPIN_AL_RISK_ENVELOPE_V1'
    p=_payload(schema,eid,obs,lim,crit,why)
    return RiskEnvelope(schema,eid,obs,lim,crit,why,_fp(p))

def _envelope_fp_valid(e):
    try:
        if e.schema!='NOEPIN_AL_RISK_ENVELOPE_V1': return False
        rebuilt=build_envelope(envelope_id=e.envelope_id,observed=_as_dict(e.observed),limits=_as_dict(e.limits),critical_dimensions=e.critical_dimensions,rationale=e.rationale)
        return rebuilt.fingerprint==e.fingerprint and rebuilt.observed==e.observed and rebuilt.limits==e.limits and rebuilt.critical_dimensions==e.critical_dimensions
    except Exception: return False

def _violations(e):
    obs=_as_dict(e.observed); lim=_as_dict(e.limits)
    v=tuple(k for k in REQUIRED_DIMENSIONS if obs[k] > lim[k])
    c=tuple(k for k in v if k in set(e.critical_dimensions))
    return v,c

def _context_fp(q):
    return _fp({'current_observed':q.current_observed,'current_limits':q.current_limits,'current_critical_dimensions':q.current_critical_dimensions,'context_id':q.context_id})

def evaluate(q:RiskEvaluationRequest):
    if not _norm(q.evaluation_id) or not _norm(q.context_id) or not _norm(q.binding) or not _norm(q.state_epoch):
        return RiskEvaluationResult(Decision.HOLD,NextAction.RETAIN_NO_ACTION_CANDIDATE,Escalation.INVALID_CONFIGURATION,EngineState.INVALID,_norm(q.evaluation_id),False,False,False,False,(),(),0,0,0,False,q.envelope.fingerprint,('Missing evaluation metadata',))
    if not _envelope_fp_valid(q.envelope):
        return RiskEvaluationResult(Decision.DENY,NextAction.REACQUIRE_RISK_ENVELOPE_CANDIDATE,Escalation.ENVELOPE_FINGERPRINT_MISMATCH,EngineState.INVALID,q.evaluation_id,False,False,False,False,(),(),0,0,0,False,q.envelope.fingerprint,('Risk Envelope fingerprint or structure mismatch',))
    obs_match=q.current_observed==q.envelope.observed; lim_match=q.current_limits==q.envelope.limits; crit_match=q.current_critical_dimensions==q.envelope.critical_dimensions
    v,c=_violations(q.envelope)
    if not (obs_match and lim_match and crit_match):
        return RiskEvaluationResult(Decision.HOLD,NextAction.REACQUIRE_RISK_ENVELOPE_CANDIDATE,Escalation.CONTEXT_OR_LIMIT_MISMATCH,EngineState.INVALID,q.evaluation_id,True,obs_match,lim_match,crit_match,v,c,len(REQUIRED_DIMENSIONS),len(v),len(c),False,q.envelope.fingerprint,('Current observed/limit/critical state differs from cached Envelope',))
    if c:
        return RiskEvaluationResult(Decision.HOLD,NextAction.REVIEW_RISK_VIOLATION_CANDIDATE,Escalation.CRITICAL_RISK_VIOLATION,EngineState.CRITICAL_RISK_VIOLATION_CANDIDATE,q.evaluation_id,True,True,True,True,v,c,len(REQUIRED_DIMENSIONS),len(v),len(c),False,q.envelope.fingerprint,('Critical risk limit violation candidate requires downstream policy/review',))
    if v:
        return RiskEvaluationResult(Decision.HOLD,NextAction.REVIEW_RISK_VIOLATION_CANDIDATE,Escalation.RISK_LIMIT_VIOLATION,EngineState.RISK_LIMIT_VIOLATION_CANDIDATE,q.evaluation_id,True,True,True,True,v,c,len(REQUIRED_DIMENSIONS),len(v),0,False,q.envelope.fingerprint,('Risk limit violation candidate requires downstream policy/review',))
    return RiskEvaluationResult(Decision.ALLOW,NextAction.CONTINUE_RISK_POLICY_EVALUATION_CANDIDATE,Escalation.NONE,EngineState.RISK_ENVELOPE_WITHIN_LIMIT_CANDIDATE,q.evaluation_id,True,True,True,True,(),(),len(REQUIRED_DIMENSIONS),0,0,True,q.envelope.fingerprint,('Risk Envelope structurally valid, current-state bound, and within listed limits',))

def _query_fp(q): return _fp({'evaluation_id':q.evaluation_id,'context_id':q.context_id,'binding':q.binding,'state_epoch':q.state_epoch})
def prepare_state(q,binding,state_epoch):
    if q.binding!=binding or q.state_epoch!=state_epoch: raise ValueError('binding/state epoch mismatch')
    r=evaluate(q); ef=q.envelope.fingerprint; cf=_context_fp(q); rf=_fp(r); qf=_query_fp(q)
    integ=_fp({'envelope':ef,'context':cf,'query':qf,'result':rf,'binding':binding,'state_epoch':state_epoch})
    return PreparedRiskState(q,r,ef,cf,rf,integ,binding,state_epoch)

def evaluate_prepared(st,*,integrity_validated,current_envelope_fingerprint,current_context_fingerprint,current_result_fingerprint):
    ok=integrity_validated and current_envelope_fingerprint==st.envelope_fingerprint and current_context_fingerprint==st.context_fingerprint and current_result_fingerprint==st.result_fingerprint
    if not ok:
        return RiskEvaluationResult(Decision.HOLD,NextAction.RETAIN_NO_ACTION_CANDIDATE,Escalation.INVALID_CONFIGURATION,EngineState.INVALID,st.request.evaluation_id,False,False,False,False,(),(),0,0,0,False,st.request.envelope.fingerprint,('Prepared state integrity/current fingerprints not validated',))
    # Re-evaluate current observed/limit/critical state; cached PASS is not authority.
    return evaluate(st.request)

def make_delta(old:PreparedRiskState,new:PreparedRiskState):
    oo=_as_dict(old.request.envelope.observed); no=_as_dict(new.request.envelope.observed)
    ol=_as_dict(old.request.envelope.limits); nl=_as_dict(new.request.envelope.limits)
    oc=old.request.envelope.critical_dimensions; nc=new.request.envelope.critical_dimensions
    return RiskChange(tuple(k for k in REQUIRED_DIMENSIONS if oo[k]!=no[k]),tuple(k for k in REQUIRED_DIMENSIONS if ol[k]!=nl[k]),oc!=nc,old.request.envelope.rationale!=new.request.envelope.rationale,_context_fp(old.request)!=_context_fp(new.request),old.integrity_fingerprint,new.integrity_fingerprint)

def plan_missing_only(old:PreparedRiskState,new:PreparedRiskState):
    d=make_delta(old,new); rec=[]
    rec += [f'OBSERVED:{k}' for k in d.observed_changed]
    rec += [f'LIMIT:{k}' for k in d.limits_changed]
    if d.critical_changed: rec.append('CRITICAL_DIMENSIONS')
    if d.rationale_changed: rec.append('RATIONALE')
    # Context ID changes are query/state changes, but envelope value changes already identify the missing state.
    if d.context_changed and not (d.observed_changed or d.limits_changed or d.critical_changed): rec.append('RISK_CONTEXT')
    records=tuple(rec); metadata=len(_canon({'records':records,'from':d.from_fingerprint,'to':d.to_fingerprint}))
    return MissingOnlyPlan(records,metadata,False)

def default_envelope():
    return build_envelope(
        envelope_id='RISK-178-A',
        observed={'confidentiality':0.18,'integrity':0.22,'availability':0.16,'irreversibility':0.12,'externality':0.20,'privilege':0.15,'uncertainty':0.24},
        limits={'confidentiality':0.45,'integrity':0.40,'availability':0.50,'irreversibility':0.30,'externality':0.35,'privilege':0.30,'uncertainty':0.40},
        critical_dimensions=('irreversibility','privilege'),
        rationale='Observed dimensions remain below the declared risk limits; downstream policy still retains authority.'
    )
def default_request():
    e=default_envelope(); return RiskEvaluationRequest('RE-178-A',e,e.observed,e.limits,e.critical_dimensions,'CTX-178-A','DEFAULT-BINDING','EPOCH-1')
def default_evaluation(): return evaluate(default_request())

if __name__=='__main__': print(json.dumps(_obj(default_evaluation()),ensure_ascii=False,sort_keys=True,indent=2))
