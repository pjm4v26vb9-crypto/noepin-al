"""NOEPIN AL 159 — Canary Safety Evaluator — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-159
DCSR: DIRECT INTEGRATION / 直接統合.

Pure canary safety evaluation core. It compares Stable and Canary metric evidence over a
bounded low-risk traffic slice. Critical Incident produces a Rollback Candidate; safety
metric degradation produces Hold / Rollback Candidate; utility improvement with maintained
safety produces Staged Promote Candidate; insufficient evidence produces Extension Candidate;
scope leak fails safe. No deployment, promotion, rollback, routing, traffic mutation, policy
mutation, model update, permission grant, tool call, file/network write, or external action is
executed here. Canary Evidence != Truth; Promote/Hold/Rollback Candidate != execution;
Shadow/Canary State != Production Authority; DCSR reconstruction cannot create Truth,
Domain Authority, Permission, Safety Proof, Approval, Action, or Action Success.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json

class Decision(str, Enum):
    ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class CanaryVerdict(str, Enum):
    PROMOTE_CANDIDATE='PROMOTE_CANDIDATE'
    HOLD_CANDIDATE='HOLD_CANDIDATE'
    ROLLBACK_CANDIDATE='ROLLBACK_CANDIDATE'
    EXTEND_CANDIDATE='EXTEND_CANDIDATE'
    INVALID='INVALID'
class EngineState(str, Enum):
    STAGED_PROMOTION_CANDIDATE='STAGED_PROMOTION_CANDIDATE'
    SAFETY_HOLD_CANDIDATE='SAFETY_HOLD_CANDIDATE'
    CRITICAL_ROLLBACK_CANDIDATE='CRITICAL_ROLLBACK_CANDIDATE'
    EVIDENCE_EXTENSION_CANDIDATE='EVIDENCE_EXTENSION_CANDIDATE'
    SCOPE_LEAK_CANDIDATE='SCOPE_LEAK_CANDIDATE'
    INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_PROMOTION_FLOW_CANDIDATE='CONTINUE_PROMOTION_FLOW_CANDIDATE'
    HOLD_CANARY_CANDIDATE='HOLD_CANARY_CANDIDATE'
    ROLLBACK_KNOWN_SAFE_CANDIDATE='ROLLBACK_KNOWN_SAFE_CANDIDATE'
    EXTEND_CANARY_EVIDENCE_CANDIDATE='EXTEND_CANARY_EVIDENCE_CANDIDATE'
    CONTAIN_SCOPE_CANDIDATE='CONTAIN_SCOPE_CANDIDATE'
    REVIEW_CONFIGURATION_CANDIDATE='REVIEW_CONFIGURATION_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'
    SAFETY_METRIC_DEGRADATION='SAFETY_METRIC_DEGRADATION'
    CRITICAL_INCIDENT='CRITICAL_INCIDENT'
    INSUFFICIENT_DATA='INSUFFICIENT_DATA'
    SCOPE_LEAK='SCOPE_LEAK'
    INVALID_CONFIGURATION='INVALID_CONFIGURATION'

@dataclass(frozen=True)
class VersionState:
    stable_version:str; canary_version:str; known_safe_version:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class TrafficSlice:
    slice_id:str; fraction:float; low_risk_only:bool; scope_valid:bool; observed_samples:int; min_required_samples:int; binding:str; state_epoch:str
@dataclass(frozen=True)
class SafetyMetric:
    metric_id:str; stable_value:float; canary_value:float; higher_is_safer:bool; tolerance:float; binding:str; state_epoch:str
@dataclass(frozen=True)
class UtilityMetric:
    metric_id:str; stable_value:float; canary_value:float; min_improvement:float; binding:str; state_epoch:str
@dataclass(frozen=True)
class Incident:
    incident_id:str; critical:bool; confirmed:bool; description:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class CanaryPolicy:
    max_traffic_fraction:float; require_low_risk_scope:bool; require_safety_non_degradation:bool; rollback_on_critical:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class CanaryRequest:
    request_id:str; versions:VersionState; traffic:TrafficSlice; safety_metrics:tuple[SafetyMetric,...]; utility_metrics:tuple[UtilityMetric,...]; incidents:tuple[Incident,...]; policy:CanaryPolicy; binding:str; state_epoch:str
@dataclass(frozen=True)
class MetricDelta:
    metric_id:str; stable_value:float; canary_value:float; delta:float; safety_metric:bool; degraded:bool
@dataclass(frozen=True)
class CanaryResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState; verdict:CanaryVerdict; stable_version:str; canary_version:str; traffic_slice_id:str; sample_count:int; safety_metric_deltas:tuple[MetricDelta,...]; utility_metric_deltas:tuple[MetricDelta,...]; safety_degradation_count:int; critical_incident_count:int; confirmed_incident_count:int; utility_improved:bool; scope_valid:bool; staged_promotion_candidate:bool; fallback_known_safe_candidate:bool; fallback_version_candidate:str; reasons:tuple[str,...]; next_gate_candidate:bool
    deployment_executed:bool=False; promotion_executed:bool=False; rollback_executed:bool=False; traffic_routing_mutated:bool=False; traffic_fraction_mutated:bool=False; canary_scope_mutated:bool=False; policy_modified:bool=False; hard_constraint_modified:bool=False; guardrail_modified:bool=False; model_updated:bool=False; stable_version_mutated:bool=False; canary_version_mutated:bool=False; incident_record_mutated:bool=False; reviewer_invoked:bool=False; tool_invoked:bool=False; file_write_executed:bool=False; network_send_executed:bool=False; dcsr_reconstruction_created_fact:bool=False; sender_authority_inherited:bool=False; sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False; permission_granted:bool=False; approval_executed:bool=False; authority_granted:bool=False; stop_executed:bool=False; action_executed:bool=False; plan_committed:bool=False; publish_executed:bool=False; external_write_performed:bool=False; world_truth_proven:bool=False; domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedCanaryState:
    request:CanaryRequest; result:CanaryResult; versions_fingerprint:str; traffic_fingerprint:str; safety_fingerprint:str; utility_fingerprint:str; incidents_fingerprint:str; policy_fingerprint:str; request_context_fingerprint:str; result_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class CanaryDelta:
    versions_changed:bool; traffic_changed:bool; safety_changed:bool; utility_changed:bool; incidents_changed:bool; policy_changed:bool; request_context_changed:bool; from_manifest_fingerprint:str; to_manifest_fingerprint:str
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

def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'; stable='policy-v2'; canary='policy-v3-canary'
    versions=VersionState(stable,canary,stable,b,e)
    traffic=TrafficSlice('SLICE-159-A',0.05,True,True,1200,1000,b,e)
    safety=(
        SafetyMetric('CRITICAL_FALSE_ALLOW_RATE',0.001,0.001,False,0.0001,b,e),
        SafetyMetric('POLICY_VIOLATION_RATE',0.002,0.0018,False,0.0002,b,e),
        SafetyMetric('SAFE_COMPLETION_RATE',0.970,0.972,True,0.002,b,e),
    )
    utility=(UtilityMetric('UTILITY_SCORE',0.820,0.845,0.010,b,e),)
    policy=CanaryPolicy(0.10,True,True,True,b,e)
    return CanaryRequest('REQ-159-A',versions,traffic,safety,utility,(),policy,b,e)

def _invalid(reason):
    return CanaryResult(Decision.HOLD,NextAction.REVIEW_CONFIGURATION_CANDIDATE,Escalation.INVALID_CONFIGURATION,EngineState.INVALID,CanaryVerdict.INVALID,'','','',0,(),(),0,0,0,False,False,False,False,'',(reason,'NO_DEPLOYMENT_PROMOTION_ROLLBACK_ROUTING_POLICY_MODEL_OR_EXTERNAL_ACTION_EXECUTION'),False)

def _validate(q):
    if not q.request_id or not q.binding or not q.state_epoch: return 'EMPTY_REQUEST_CONTEXT'
    for x,n in ((q.versions,'VERSIONS'),(q.traffic,'TRAFFIC'),(q.policy,'POLICY')):
        if x.binding!=q.binding or x.state_epoch!=q.state_epoch: return n+'_BINDING_MISMATCH'
    if not q.versions.stable_version or not q.versions.canary_version or not q.versions.known_safe_version: return 'EMPTY_VERSION'
    if q.versions.stable_version==q.versions.canary_version: return 'VERSION_PAIR_NOT_DISTINCT'
    if not (0.0 < q.traffic.fraction <= 1.0): return 'INVALID_TRAFFIC_FRACTION'
    if q.traffic.observed_samples<0 or q.traffic.min_required_samples<=0: return 'INVALID_SAMPLE_COUNT'
    if not (0.0 < q.policy.max_traffic_fraction <= 1.0): return 'INVALID_POLICY_TRAFFIC_LIMIT'
    seen=set()
    for m in q.safety_metrics:
        if m.binding!=q.binding or m.state_epoch!=q.state_epoch: return 'SAFETY_BINDING_MISMATCH'
        if not m.metric_id or m.metric_id in seen or m.tolerance<0: return 'INVALID_SAFETY_METRIC'
        seen.add(m.metric_id)
    if not q.safety_metrics: return 'MISSING_SAFETY_METRICS'
    useen=set()
    for m in q.utility_metrics:
        if m.binding!=q.binding or m.state_epoch!=q.state_epoch: return 'UTILITY_BINDING_MISMATCH'
        if not m.metric_id or m.metric_id in useen or m.min_improvement<0: return 'INVALID_UTILITY_METRIC'
        useen.add(m.metric_id)
    if not q.utility_metrics: return 'MISSING_UTILITY_METRICS'
    ids=set()
    for i in q.incidents:
        if i.binding!=q.binding or i.state_epoch!=q.state_epoch: return 'INCIDENT_BINDING_MISMATCH'
        if not i.incident_id or i.incident_id in ids: return 'INVALID_INCIDENT_ID'
        ids.add(i.incident_id)
    return None

def evaluate(q:CanaryRequest)->CanaryResult:
    bad=_validate(q)
    if bad: return _invalid(bad)
    sd=[]; ud=[]
    for m in q.safety_metrics:
        delta=m.canary_value-m.stable_value
        degraded=(delta < -m.tolerance) if m.higher_is_safer else (delta > m.tolerance)
        sd.append(MetricDelta(m.metric_id,m.stable_value,m.canary_value,delta,True,degraded))
    for m in q.utility_metrics:
        delta=m.canary_value-m.stable_value
        ud.append(MetricDelta(m.metric_id,m.stable_value,m.canary_value,delta,False,False))
    degraded=sum(1 for x in sd if x.degraded)
    confirmed=sum(1 for i in q.incidents if i.confirmed)
    critical=sum(1 for i in q.incidents if i.confirmed and i.critical)
    utility_improved=all((m.canary_value-m.stable_value) >= m.min_improvement for m in q.utility_metrics)
    scope_valid=q.traffic.scope_valid and q.traffic.fraction<=q.policy.max_traffic_fraction and (q.traffic.low_risk_only or not q.policy.require_low_risk_scope)
    common=('CANARY_EVIDENCE_IS_NOT_TRUTH','PROMOTE_HOLD_ROLLBACK_ARE_CANDIDATES_NOT_EXECUTION','SHADOW_CANARY_STATE_IS_NOT_PRODUCTION_AUTHORITY','NO_DEPLOYMENT_PROMOTION_ROLLBACK_ROUTING_POLICY_MODEL_OR_EXTERNAL_ACTION_EXECUTION')
    if not scope_valid:
        return CanaryResult(Decision.DENY,NextAction.CONTAIN_SCOPE_CANDIDATE,Escalation.SCOPE_LEAK,EngineState.SCOPE_LEAK_CANDIDATE,CanaryVerdict.ROLLBACK_CANDIDATE,q.versions.stable_version,q.versions.canary_version,q.traffic.slice_id,q.traffic.observed_samples,tuple(sd),tuple(ud),degraded,critical,confirmed,utility_improved,False,False,True,q.versions.known_safe_version,('CANARY_SCOPE_LEAK_OR_POLICY_LIMIT_EXCEEDED',)+common,True)
    if critical and q.policy.rollback_on_critical:
        return CanaryResult(Decision.DENY,NextAction.ROLLBACK_KNOWN_SAFE_CANDIDATE,Escalation.CRITICAL_INCIDENT,EngineState.CRITICAL_ROLLBACK_CANDIDATE,CanaryVerdict.ROLLBACK_CANDIDATE,q.versions.stable_version,q.versions.canary_version,q.traffic.slice_id,q.traffic.observed_samples,tuple(sd),tuple(ud),degraded,critical,confirmed,utility_improved,True,False,True,q.versions.known_safe_version,('CRITICAL_INCIDENT_REQUIRES_ROLLBACK_CANDIDATE',)+common,True)
    if degraded and q.policy.require_safety_non_degradation:
        return CanaryResult(Decision.HOLD,NextAction.ROLLBACK_KNOWN_SAFE_CANDIDATE,Escalation.SAFETY_METRIC_DEGRADATION,EngineState.SAFETY_HOLD_CANDIDATE,CanaryVerdict.ROLLBACK_CANDIDATE,q.versions.stable_version,q.versions.canary_version,q.traffic.slice_id,q.traffic.observed_samples,tuple(sd),tuple(ud),degraded,critical,confirmed,utility_improved,True,False,True,q.versions.known_safe_version,('SAFETY_METRIC_DEGRADATION_DETECTED',)+common,True)
    if q.traffic.observed_samples < q.traffic.min_required_samples:
        return CanaryResult(Decision.HOLD,NextAction.EXTEND_CANARY_EVIDENCE_CANDIDATE,Escalation.INSUFFICIENT_DATA,EngineState.EVIDENCE_EXTENSION_CANDIDATE,CanaryVerdict.EXTEND_CANDIDATE,q.versions.stable_version,q.versions.canary_version,q.traffic.slice_id,q.traffic.observed_samples,tuple(sd),tuple(ud),degraded,critical,confirmed,utility_improved,True,False,False,'',('CANARY_EVIDENCE_INSUFFICIENT_EXTEND_ONLY',)+common,True)
    if utility_improved:
        return CanaryResult(Decision.ALLOW,NextAction.CONTINUE_PROMOTION_FLOW_CANDIDATE,Escalation.NONE,EngineState.STAGED_PROMOTION_CANDIDATE,CanaryVerdict.PROMOTE_CANDIDATE,q.versions.stable_version,q.versions.canary_version,q.traffic.slice_id,q.traffic.observed_samples,tuple(sd),tuple(ud),degraded,critical,confirmed,True,True,True,False,'',('UTILITY_IMPROVED_WITH_SAFETY_MAINTAINED','STAGED_PROMOTION_CANDIDATE_ONLY')+common,True)
    return CanaryResult(Decision.HOLD,NextAction.HOLD_CANARY_CANDIDATE,Escalation.NONE,EngineState.SAFETY_HOLD_CANDIDATE,CanaryVerdict.HOLD_CANDIDATE,q.versions.stable_version,q.versions.canary_version,q.traffic.slice_id,q.traffic.observed_samples,tuple(sd),tuple(ud),degraded,critical,confirmed,False,True,False,False,'',('SAFETY_MAINTAINED_BUT_UTILITY_NOT_IMPROVED',)+common,True)

def default_evaluation(): return evaluate(default_request())

def prepare_state(q,binding,state_epoch):
    if binding!=q.binding or state_epoch!=q.state_epoch: raise ValueError('PREPARED_BINDING_MISMATCH')
    r=evaluate(q)
    pieces=(_fp(q.versions),_fp(q.traffic),_fp(q.safety_metrics),_fp(q.utility_metrics),_fp(q.incidents),_fp(q.policy),_fp((q.request_id,q.binding,q.state_epoch)),_fp(r))
    integ=_fp(pieces+(binding,state_epoch))
    return PreparedCanaryState(q,r,*pieces,integ,binding,state_epoch)

def evaluate_prepared(st,*,integrity_validated,current_versions_fingerprint,current_traffic_fingerprint,current_safety_fingerprint,current_utility_fingerprint,current_incidents_fingerprint,current_policy_fingerprint,current_request_context_fingerprint,current_result_fingerprint):
    if not integrity_validated: return _invalid('PREPARED_INTEGRITY_NOT_VALIDATED')
    cur=(current_versions_fingerprint,current_traffic_fingerprint,current_safety_fingerprint,current_utility_fingerprint,current_incidents_fingerprint,current_policy_fingerprint,current_request_context_fingerprint,current_result_fingerprint)
    exp=(st.versions_fingerprint,st.traffic_fingerprint,st.safety_fingerprint,st.utility_fingerprint,st.incidents_fingerprint,st.policy_fingerprint,st.request_context_fingerprint,st.result_fingerprint)
    if cur!=exp or _fp(exp+(st.binding,st.state_epoch))!=st.integrity_fingerprint: return _invalid('PREPARED_FINGERPRINT_MISMATCH')
    return st.result

def make_delta(a,b):
    fa=_fp((a.versions_fingerprint,a.traffic_fingerprint,a.safety_fingerprint,a.utility_fingerprint,a.incidents_fingerprint,a.policy_fingerprint,a.request_context_fingerprint))
    fb=_fp((b.versions_fingerprint,b.traffic_fingerprint,b.safety_fingerprint,b.utility_fingerprint,b.incidents_fingerprint,b.policy_fingerprint,b.request_context_fingerprint))
    return CanaryDelta(a.versions_fingerprint!=b.versions_fingerprint,a.traffic_fingerprint!=b.traffic_fingerprint,a.safety_fingerprint!=b.safety_fingerprint,a.utility_fingerprint!=b.utility_fingerprint,a.incidents_fingerprint!=b.incidents_fingerprint,a.policy_fingerprint!=b.policy_fingerprint,a.request_context_fingerprint!=b.request_context_fingerprint,fa,fb)

def plan_missing_only(a,b):
    d=make_delta(a,b); ids=[]
    for flag,name in ((d.versions_changed,'VERSIONS'),(d.traffic_changed,'TRAFFIC_SLICE'),(d.safety_changed,'SAFETY_METRICS'),(d.utility_changed,'UTILITY_METRICS'),(d.incidents_changed,'INCIDENTS'),(d.policy_changed,'CANARY_POLICY'),(d.request_context_changed,'REQUEST_CONTEXT')):
        if flag: ids.append(name)
    meta=len(_canon({'missing':ids,'from':d.from_manifest_fingerprint,'to':d.to_manifest_fingerprint}))
    return MissingOnlyPlan(tuple(ids),meta,False)
