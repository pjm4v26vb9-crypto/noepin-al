"""NOEPIN AL 056 — Decision Reason / Explanation Layer.

Pure control-plane explanation evaluator. It validates structured Reason Codes,
Evidence References, and Policy Trace metadata bound to an upstream decision and
returns a deterministic explanation candidate. It does not replace or execute the
upstream decision and does not establish truth, compliance, permission, or safety.

Creator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support using ChatGPT
License / Rights: NOT SPECIFIED
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
from hashlib import sha256
import json
from typing import Any, FrozenSet, Iterable, Mapping, Tuple

class ControlDecision(str, Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'

@dataclass(frozen=True)
class ExplanationPolicy:
    policy_id:str; version:str; authority_epoch:int; issued_at:int; expires_at:int
    max_evidence_age_seconds:int; max_trace_age_seconds:int
    display_sensitivities:FrozenSet[str]; require_verified_evidence:bool=True
    require_verified_trace:bool=True; revoked:bool=False
    def validate(self, now:int)->None:
        if not self.policy_id or not self.version or self.authority_epoch<1: raise ValueError('policy identity invalid')
        if self.issued_at<0 or self.expires_at<=self.issued_at or not self.issued_at<=now<self.expires_at: raise ValueError('policy not current')
        if self.max_evidence_age_seconds<1 or self.max_trace_age_seconds<1: raise ValueError('policy age limit invalid')
        if not self.display_sensitivities: raise ValueError('display sensitivities required')

@dataclass(frozen=True)
class ReasonCodeDefinition:
    reason_code:str; category:str; description:str; applicable_decisions:FrozenSet[str]
    required_evidence_types:FrozenSet[str]; required_policy_rules:FrozenSet[str]; enabled:bool=True
    def validate(self)->None:
        if not self.reason_code or not self.category or not self.description: raise ValueError('reason definition identity required')
        if not self.applicable_decisions: raise ValueError('reason applicable decisions required')
        if any(x not in {d.value for d in ControlDecision} for x in self.applicable_decisions): raise ValueError('reason decision invalid')

@dataclass(frozen=True)
class EvidenceReference:
    evidence_id:str; decision_id:str; evidence_type:str; source_id:str; observed_at:int
    verified:bool; independent:bool; sensitivity:str; display_label:str; evidence_binding:str
    revoked:bool=False
    def validate(self)->None:
        if not self.evidence_id or not self.decision_id or not self.evidence_type or not self.source_id or not self.sensitivity or not self.evidence_binding: raise ValueError('evidence identity required')
        if self.observed_at<0: raise ValueError('evidence time invalid')

@dataclass(frozen=True)
class PolicyTraceStep:
    trace_id:str; decision_id:str; rule_id:str; policy_id:str; policy_version:str
    authority_epoch:int; outcome:str; observed_at:int; verified:bool; evidence_binding:str
    revoked:bool=False
    def validate(self)->None:
        if not self.trace_id or not self.decision_id or not self.rule_id or not self.policy_id or not self.policy_version or not self.outcome or not self.evidence_binding: raise ValueError('trace identity required')
        if self.authority_epoch<1 or self.observed_at<0: raise ValueError('trace metadata invalid')

@dataclass(frozen=True)
class DecisionRecord:
    decision_id:str; request_id:str; upstream_decision:ControlDecision; risk_label:str
    reason_codes:Tuple[str,...]; evidence_ref_ids:Tuple[str,...]; policy_trace_ids:Tuple[str,...]
    expected_policy_id:str; expected_policy_version:str; expected_authority_epoch:int
    explanation_binding:str
    def validate(self)->None:
        if not self.decision_id or not self.request_id or not self.risk_label or not self.explanation_binding: raise ValueError('decision identity required')
        if not self.reason_codes: raise ValueError('at least one reason code required')
        if not self.expected_policy_id or not self.expected_policy_version or self.expected_authority_epoch<1: raise ValueError('decision policy binding invalid')
        if len(set(self.reason_codes))!=len(self.reason_codes): raise ValueError('duplicate reason code')
        if len(set(self.evidence_ref_ids))!=len(self.evidence_ref_ids): raise ValueError('duplicate evidence reference id')
        if len(set(self.policy_trace_ids))!=len(self.policy_trace_ids): raise ValueError('duplicate trace id')

@dataclass(frozen=True)
class PreparedExplanationRegistry:
    registry_fingerprint:str; policy_fingerprint:str
    reasons:Tuple[ReasonCodeDefinition,...]; evidence:Tuple[EvidenceReference,...]; traces:Tuple[PolicyTraceStep,...]
    reason_fingerprints:Mapping[str,str]; evidence_fingerprints:Mapping[str,str]; trace_fingerprints:Mapping[str,str]
    decision_evidence_index:Mapping[str,Tuple[str,...]]; decision_trace_index:Mapping[str,Tuple[str,...]]

@dataclass(frozen=True)
class ExplanationRegistryDelta:
    base_fingerprint:str; target_fingerprint:str
    changed_reasons:Tuple[ReasonCodeDefinition,...]; removed_reason_codes:Tuple[str,...]; added_reasons:Tuple[ReasonCodeDefinition,...]
    changed_evidence:Tuple[EvidenceReference,...]; removed_evidence_ids:Tuple[str,...]; added_evidence:Tuple[EvidenceReference,...]
    changed_traces:Tuple[PolicyTraceStep,...]; removed_trace_ids:Tuple[str,...]; added_traces:Tuple[PolicyTraceStep,...]

@dataclass(frozen=True)
class RegistrySyncPlan:
    missing_or_changed_reason_codes:Tuple[str,...]; missing_or_changed_evidence_ids:Tuple[str,...]; missing_or_changed_trace_ids:Tuple[str,...]
    metadata_bytes_required:int; full_metadata_bytes:int; full_resend_required:bool
    permission_granted:bool=False; decision_override_authorized:bool=False; action_execution_authorized:bool=False
    policy_compliance_proven:bool=False

@dataclass(frozen=True)
class ExplanationAssessment:
    decision:ControlDecision; upstream_decision:ControlDecision; reasons:Tuple[str,...]
    decision_id:str; reason_codes:Tuple[str,...]; evidence_reference_ids:Tuple[str,...]; policy_trace_ids:Tuple[str,...]
    human_summary:Tuple[str,...]; redacted_evidence_ids:Tuple[str,...]
    explanation_complete_candidate:bool; policy_trace_complete_candidate:bool
    registry_fingerprint:str; policy_fingerprint:str; decision_fingerprint:str
    permission_granted:bool=False; upstream_decision_changed:bool=False; action_executed:bool=False
    evidence_truth_proven:bool=False; decision_truth_proven:bool=False; policy_compliance_proven:bool=False
    safety_proven:bool=False; action_success:bool=False

def _canonical(v:Any)->Any:
    if isinstance(v,Enum): return v.value
    if is_dataclass(v): return {f.name:_canonical(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v,Mapping): return {str(k):_canonical(x) for k,x in sorted(v.items(),key=lambda kv:str(kv[0]))}
    if isinstance(v,(set,frozenset)): return sorted((_canonical(x) for x in v),key=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')))
    if isinstance(v,(tuple,list)): return [_canonical(x) for x in v]
    return v

def canonical_json(v:Any)->str: return json.dumps(_canonical(v),ensure_ascii=False,sort_keys=True,separators=(',',':'))
def fingerprint(v:Any)->str: return sha256(canonical_json(v).encode()).hexdigest()
def _reasons(xs:Iterable[ReasonCodeDefinition])->Tuple[ReasonCodeDefinition,...]: return tuple(sorted(xs,key=lambda x:x.reason_code))
def _evidence(xs:Iterable[EvidenceReference])->Tuple[EvidenceReference,...]: return tuple(sorted(xs,key=lambda x:x.evidence_id))
def _traces(xs:Iterable[PolicyTraceStep])->Tuple[PolicyTraceStep,...]: return tuple(sorted(xs,key=lambda x:x.trace_id))
def registry_fingerprint(reasons,evidence,traces)->str: return fingerprint({'reasons':_reasons(reasons),'evidence':_evidence(evidence),'traces':_traces(traces)})

def prepare_registry(policy:ExplanationPolicy,reasons:Iterable[ReasonCodeDefinition],evidence:Iterable[EvidenceReference],traces:Iterable[PolicyTraceStep],*,now:int)->PreparedExplanationRegistry:
    policy.validate(now); rs=_reasons(reasons); es=_evidence(evidence); ts=_traces(traces)
    for x in rs: x.validate()
    for x in es: x.validate()
    for x in ts: x.validate()
    if len({x.reason_code for x in rs})!=len(rs): raise ValueError('duplicate reason definition')
    if len({x.evidence_id for x in es})!=len(es): raise ValueError('duplicate evidence id')
    if len({x.trace_id for x in ts})!=len(ts): raise ValueError('duplicate trace id')
    ei={}
    for x in es: ei.setdefault(x.decision_id,[]).append(x.evidence_id)
    ti={}
    for x in ts: ti.setdefault(x.decision_id,[]).append(x.trace_id)
    return PreparedExplanationRegistry(
        registry_fingerprint(rs,es,ts),fingerprint(policy),rs,es,ts,
        {x.reason_code:fingerprint(x) for x in rs},{x.evidence_id:fingerprint(x) for x in es},{x.trace_id:fingerprint(x) for x in ts},
        {k:tuple(sorted(v)) for k,v in ei.items()},{k:tuple(sorted(v)) for k,v in ti.items()})

def _assessment(dec,record,policy,reg,reasons=(),codes=(),eids=(),tids=(),summary=(),redacted=(),complete=False,trace_complete=False):
    return ExplanationAssessment(dec,record.upstream_decision,tuple(reasons),record.decision_id,tuple(codes),tuple(eids),tuple(tids),tuple(summary),tuple(redacted),complete,trace_complete,reg.registry_fingerprint,fingerprint(policy),fingerprint(record))

def evaluate_prepared(record:DecisionRecord,policy:ExplanationPolicy,reg:PreparedExplanationRegistry,*,now:int)->ExplanationAssessment:
    try: record.validate(); policy.validate(now)
    except ValueError as e:
        return ExplanationAssessment(ControlDecision.HOLD,getattr(record,'upstream_decision',ControlDecision.HOLD),(f'INVALID_INPUT:{e}',),getattr(record,'decision_id',''),(),(),(),(),(),False,False,getattr(reg,'registry_fingerprint',''),fingerprint(policy),fingerprint(record))
    if policy.revoked: return _assessment(ControlDecision.HOLD,record,policy,reg,('POLICY_REVOKED',))
    if record.expected_policy_id!=policy.policy_id: return _assessment(ControlDecision.HOLD,record,policy,reg,('POLICY_ID_MISMATCH',))
    if record.expected_policy_version!=policy.version: return _assessment(ControlDecision.HOLD,record,policy,reg,('POLICY_VERSION_MISMATCH',))
    if record.expected_authority_epoch!=policy.authority_epoch: return _assessment(ControlDecision.HOLD,record,policy,reg,('AUTHORITY_EPOCH_MISMATCH',))
    if reg.policy_fingerprint!=fingerprint(policy): return _assessment(ControlDecision.HOLD,record,policy,reg,('PREPARED_POLICY_FINGERPRINT_MISMATCH',))
    if reg.registry_fingerprint!=registry_fingerprint(reg.reasons,reg.evidence,reg.traces): return _assessment(ControlDecision.HOLD,record,policy,reg,('PREPARED_REGISTRY_FINGERPRINT_MISMATCH',))
    rmap={x.reason_code:x for x in reg.reasons}; emap={x.evidence_id:x for x in reg.evidence}; tmap={x.trace_id:x for x in reg.traces}
    defs=[]
    for code in record.reason_codes:
        d=rmap.get(code)
        if d is None: return _assessment(ControlDecision.HOLD,record,policy,reg,('UNKNOWN_REASON_CODE',code))
        if not d.enabled: return _assessment(ControlDecision.HOLD,record,policy,reg,('REASON_CODE_DISABLED',code))
        if record.upstream_decision.value not in d.applicable_decisions: return _assessment(ControlDecision.HOLD,record,policy,reg,('REASON_DECISION_MISMATCH',code))
        defs.append(d)
    active_e=[]
    for eid in record.evidence_ref_ids:
        e=emap.get(eid)
        if e is None: return _assessment(ControlDecision.HOLD,record,policy,reg,('EVIDENCE_REFERENCE_MISSING',eid))
        if e.decision_id!=record.decision_id or e.evidence_binding!=record.explanation_binding: return _assessment(ControlDecision.HOLD,record,policy,reg,('EVIDENCE_BINDING_MISMATCH',eid))
        if e.revoked: return _assessment(ControlDecision.HOLD,record,policy,reg,('EVIDENCE_REVOKED',eid))
        if policy.require_verified_evidence and not e.verified: return _assessment(ControlDecision.HOLD,record,policy,reg,('EVIDENCE_UNVERIFIED',eid))
        if e.observed_at>now or now-e.observed_at>policy.max_evidence_age_seconds: return _assessment(ControlDecision.HOLD,record,policy,reg,('EVIDENCE_STALE',eid))
        active_e.append(e)
    active_t=[]
    for tid in record.policy_trace_ids:
        t=tmap.get(tid)
        if t is None: return _assessment(ControlDecision.HOLD,record,policy,reg,('POLICY_TRACE_MISSING',tid))
        if t.decision_id!=record.decision_id or t.evidence_binding!=record.explanation_binding: return _assessment(ControlDecision.HOLD,record,policy,reg,('POLICY_TRACE_BINDING_MISMATCH',tid))
        if t.revoked: return _assessment(ControlDecision.HOLD,record,policy,reg,('POLICY_TRACE_REVOKED',tid))
        if policy.require_verified_trace and not t.verified: return _assessment(ControlDecision.HOLD,record,policy,reg,('POLICY_TRACE_UNVERIFIED',tid))
        if t.observed_at>now or now-t.observed_at>policy.max_trace_age_seconds: return _assessment(ControlDecision.HOLD,record,policy,reg,('POLICY_TRACE_STALE',tid))
        if t.policy_id!=policy.policy_id or t.policy_version!=policy.version or t.authority_epoch!=policy.authority_epoch: return _assessment(ControlDecision.HOLD,record,policy,reg,('POLICY_TRACE_POLICY_MISMATCH',tid))
        active_t.append(t)
    etypes={x.evidence_type for x in active_e}; rules={x.rule_id for x in active_t}
    for d in defs:
        miss=sorted(d.required_evidence_types-etypes)
        if miss: return _assessment(ControlDecision.HOLD,record,policy,reg,('REQUIRED_EVIDENCE_TYPE_MISSING',d.reason_code,*miss))
        missr=sorted(d.required_policy_rules-rules)
        if missr: return _assessment(ControlDecision.HOLD,record,policy,reg,('REQUIRED_POLICY_TRACE_MISSING',d.reason_code,*missr))
    redacted=[]; labels=[]
    for e in active_e:
        if e.sensitivity in policy.display_sensitivities:
            labels.append(f'{e.evidence_id}:{e.display_label}')
        else:
            redacted.append(e.evidence_id); labels.append(f'{e.evidence_id}:[REDACTED]')
    summary=[f'UPSTREAM_DECISION:{record.upstream_decision.value}']
    summary.extend(f'REASON:{d.reason_code}:{d.description}' for d in defs)
    summary.extend(f'EVIDENCE:{x}' for x in labels)
    summary.extend(f'TRACE:{t.rule_id}:{t.outcome}' for t in active_t)
    return _assessment(ControlDecision.ALLOW,record,policy,reg,('EXPLANATION_COMPLETE_CANDIDATE',),record.reason_codes,[x.evidence_id for x in active_e],[x.trace_id for x in active_t],summary,redacted,True,True)

def evaluate(record,policy,reasons,evidence,traces,*,now:int)->ExplanationAssessment:
    try: reg=prepare_registry(policy,reasons,evidence,traces,now=now)
    except ValueError as e:
        return ExplanationAssessment(ControlDecision.HOLD,getattr(record,'upstream_decision',ControlDecision.HOLD),(f'INVALID_REGISTRY:{e}',),getattr(record,'decision_id',''),(),(),(),(),(),False,False,'',fingerprint(policy),fingerprint(record))
    return evaluate_prepared(record,policy,reg,now=now)

def make_registry_delta(base_reasons,base_evidence,base_traces,target_reasons,target_evidence,target_traces)->ExplanationRegistryDelta:
    def diff(base,target,key):
        b={key(x):x for x in base}; t={key(x):x for x in target}
        ch=tuple(sorted((x for k,x in t.items() if k in b and fingerprint(x)!=fingerprint(b[k])),key=key))
        rm=tuple(sorted(k for k in b if k not in t)); ad=tuple(sorted((x for k,x in t.items() if k not in b),key=key)); return ch,rm,ad
    cr,rr,ar=diff(_reasons(base_reasons),_reasons(target_reasons),lambda x:x.reason_code)
    ce,re,ae=diff(_evidence(base_evidence),_evidence(target_evidence),lambda x:x.evidence_id)
    ct,rt,at=diff(_traces(base_traces),_traces(target_traces),lambda x:x.trace_id)
    return ExplanationRegistryDelta(registry_fingerprint(base_reasons,base_evidence,base_traces),registry_fingerprint(target_reasons,target_evidence,target_traces),cr,rr,ar,ce,re,ae,ct,rt,at)

def apply_registry_delta(base_reasons,base_evidence,base_traces,delta:ExplanationRegistryDelta):
    if registry_fingerprint(base_reasons,base_evidence,base_traces)!=delta.base_fingerprint: raise ValueError('delta base fingerprint mismatch')
    def apply(base,changed,removed,added,key):
        items={key(x):x for x in base}
        for k in removed:
            if k not in items: raise ValueError('invalid removal')
            del items[k]
        for x in changed:
            if key(x) not in items: raise ValueError('invalid change')
            items[key(x)]=x
        for x in added:
            if key(x) in items: raise ValueError('invalid add')
            items[key(x)]=x
        return tuple(sorted(items.values(),key=key))
    rs=apply(_reasons(base_reasons),delta.changed_reasons,delta.removed_reason_codes,delta.added_reasons,lambda x:x.reason_code)
    es=apply(_evidence(base_evidence),delta.changed_evidence,delta.removed_evidence_ids,delta.added_evidence,lambda x:x.evidence_id)
    ts=apply(_traces(base_traces),delta.changed_traces,delta.removed_trace_ids,delta.added_traces,lambda x:x.trace_id)
    if registry_fingerprint(rs,es,ts)!=delta.target_fingerprint: raise ValueError('delta target fingerprint mismatch')
    return rs,es,ts

def plan_registry_sync(reasons,evidence,traces,remote_reason_fps:Mapping[str,str],remote_evidence_fps:Mapping[str,str],remote_trace_fps:Mapping[str,str])->RegistrySyncPlan:
    rs=_reasons(reasons); es=_evidence(evidence); ts=_traces(traces)
    rids=tuple(x.reason_code for x in rs if remote_reason_fps.get(x.reason_code)!=fingerprint(x))
    eids=tuple(x.evidence_id for x in es if remote_evidence_fps.get(x.evidence_id)!=fingerprint(x))
    tids=tuple(x.trace_id for x in ts if remote_trace_fps.get(x.trace_id)!=fingerprint(x))
    rm={x.reason_code:x for x in rs}; em={x.evidence_id:x for x in es}; tm={x.trace_id:x for x in ts}
    selected={'reasons':[rm[k] for k in rids],'evidence':[em[k] for k in eids],'traces':[tm[k] for k in tids]}
    full={'reasons':rs,'evidence':es,'traces':ts}
    meta=len(canonical_json(selected).encode()); fullb=len(canonical_json(full).encode())
    return RegistrySyncPlan(rids,eids,tids,meta,fullb,fullb>0 and meta/fullb>=0.8)

def assessment_digest(a:ExplanationAssessment)->str: return fingerprint(a)

def default_policy(now:int)->ExplanationPolicy:
    return ExplanationPolicy('EXPLAIN-056','1',1,now-100,now+10000,3600,3600,frozenset({'PUBLIC','INTERNAL'}),True,True,False)
def default_reasons():
    return (ReasonCodeDefinition('LOW_RISK_REQUEST','SAFETY','Request remained within the configured low-risk control boundary.',frozenset({'ALLOW'}),frozenset({'REQUEST_METADATA'}),frozenset({'ALLOW_LOW_RISK'}),True),)
def default_evidence(now:int):
    return (EvidenceReference('EVID-056','DEC-056','REQUEST_METADATA','CONTROL-056',now-20,True,True,'INTERNAL','Bound request metadata','BIND-056',False),)
def default_traces(now:int):
    return (PolicyTraceStep('TRACE-056','DEC-056','ALLOW_LOW_RISK','EXPLAIN-056','1',1,'ALLOW',now-15,True,'BIND-056',False),)
def default_record(now:int)->DecisionRecord:
    return DecisionRecord('DEC-056','REQ-056',ControlDecision.ALLOW,'LOW',('LOW_RISK_REQUEST',),('EVID-056',),('TRACE-056',),'EXPLAIN-056','1',1,'BIND-056')
