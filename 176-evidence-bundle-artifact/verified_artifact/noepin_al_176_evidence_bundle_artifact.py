"""NOEPIN AL 176 — Evidence Bundle Artifact — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-176
DCSR: DIRECT INTEGRATION / 直接統合.

Deterministic, side-effect-free safety artifact for preserving Evidence ID, Source,
Claim, timezone-aware observation time, Provenance SHA-256 digest, Trust score, and
Independence Group in a fingerprinted bundle. It can identify stale/future evidence
and count independent groups, but does not promote evidence to Truth, Domain Authority,
Permission, Safety Proof, Approval Execution, Action Execution, or Action Success.
DCSR may partition/cache known Evidence records and request only missing/stale records;
it may not alter Source/Provenance/Trust/Independence or turn fingerprint agreement into Truth.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import json, math, re

class Decision(str, Enum):
    ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class EngineState(str, Enum):
    EVIDENCE_BUNDLE_FRESH_CANDIDATE='EVIDENCE_BUNDLE_FRESH_CANDIDATE'
    EVIDENCE_REACQUISITION_CANDIDATE='EVIDENCE_REACQUISITION_CANDIDATE'
    INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_DECISION_ENVELOPE_BINDING_CANDIDATE='CONTINUE_DECISION_ENVELOPE_BINDING_CANDIDATE'
    REQUEST_STALE_OR_MISSING_EVIDENCE_CANDIDATE='REQUEST_STALE_OR_MISSING_EVIDENCE_CANDIDATE'
    RETAIN_NO_ACTION_CANDIDATE='RETAIN_NO_ACTION_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'
    INVALID_CONFIGURATION='INVALID_CONFIGURATION'
    BUNDLE_FINGERPRINT_MISMATCH='BUNDLE_FINGERPRINT_MISMATCH'
    STALE_EVIDENCE_PRESENT='STALE_EVIDENCE_PRESENT'
    FUTURE_EVIDENCE_PRESENT='FUTURE_EVIDENCE_PRESENT'

HEX64=re.compile(r'^[0-9a-f]{64}$')
_WS=re.compile(r'\s+')

def _obj(v):
    if isinstance(v,Enum): return v.value
    if is_dataclass(v): return {f.name:_obj(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v,dict): return {str(k):_obj(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(tuple,list)): return [_obj(x) for x in v]
    if isinstance(v,datetime): return v.isoformat()
    if isinstance(v,float):
        if not math.isfinite(v): raise ValueError('non-finite float')
        return v
    return v

def _canon(v): return json.dumps(_obj(v),ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def _fp(v): return sha256(_canon(v)).hexdigest()
def _seed_fp(label:str)->str: return sha256(label.encode()).hexdigest()
def _norm(v:str)->str: return _WS.sub(' ',str(v).strip())
def _parse_aware(s:str)->datetime:
    try: d=datetime.fromisoformat(str(s))
    except Exception as e: raise ValueError('invalid ISO datetime') from e
    if d.tzinfo is None or d.utcoffset() is None: raise ValueError('timezone-aware datetime required')
    return d.astimezone(timezone.utc)
def _valid_hex64(v:str)->bool: return bool(HEX64.fullmatch(str(v)))

@dataclass(frozen=True)
class EvidenceItem:
    evidence_id:str
    source_id:str
    claim:str
    observed_time:str
    provenance_digest:str
    trust:float
    independence_group:str

@dataclass(frozen=True)
class EvidenceBundle:
    schema:str
    items:tuple[EvidenceItem,...]
    fingerprint:str

@dataclass(frozen=True)
class EvidenceEvaluationRequest:
    evaluation_id:str
    bundle:EvidenceBundle
    at_time:str
    max_age_seconds:float
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class EvidenceEvaluationResult:
    decision:Decision
    next_action:NextAction
    escalation:Escalation
    engine_state:EngineState
    evaluation_id:str
    bundle_fingerprint_valid:bool
    stale_ids:tuple[str,...]
    future_ids:tuple[str,...]
    fresh_ids:tuple[str,...]
    independent_group_count:int
    evidence_count:int
    minimum_trust:float
    maximum_trust:float
    next_gate_candidate:bool
    bundle_fingerprint:str
    reasons:tuple[str,...]
    evidence_promoted_to_truth:bool=False
    source_promoted_to_authority:bool=False
    provenance_promoted_to_truth:bool=False
    trust_promoted_to_truth:bool=False
    independence_promoted_to_truth:bool=False
    permission_granted:bool=False
    policy_decision_executed:bool=False
    approval_executed:bool=False
    human_approval_executed:bool=False
    permit_issued:bool=False
    tool_invoked:bool=False
    action_executed:bool=False
    action_success:bool=False
    stop_executed:bool=False
    file_write_executed:bool=False
    network_send_executed:bool=False
    external_write_performed:bool=False
    authoritative_state_created:bool=False
    cached_state_promoted:bool=False
    reconstructed_state_promoted:bool=False
    partial_state_promoted:bool=False
    dcsr_reconstruction_created_fact:bool=False
    sender_authority_inherited:bool=False
    sender_intent_inherited:bool=False
    sender_agreement_inherited:bool=False
    authority_granted:bool=False
    world_truth_proven:bool=False
    domain_authority_promoted:bool=False
    safety_proven:bool=False

@dataclass(frozen=True)
class PreparedEvidenceState:
    request:EvidenceEvaluationRequest
    result:EvidenceEvaluationResult
    bundle_fingerprint:str
    query_fingerprint:str
    result_fingerprint:str
    integrity_fingerprint:str
    item_fingerprints:tuple[tuple[str,str],...]
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class EvidenceChange:
    changed_or_missing_ids:tuple[str,...]
    query_changed:bool
    from_fingerprint:str
    to_fingerprint:str

@dataclass(frozen=True)
class MissingOnlyPlan:
    missing_or_changed_record_ids:tuple[str,...]
    metadata_bytes_required:int
    full_resend_required:bool


def _normalize_item(item:EvidenceItem)->EvidenceItem:
    eid=_norm(item.evidence_id); sid=_norm(item.source_id); claim=_norm(item.claim); group=_norm(item.independence_group)
    if not eid or not sid or not claim or not group: raise ValueError('Evidence ID, Source ID, Claim, and Independence Group are required')
    if not _valid_hex64(item.provenance_digest): raise ValueError('Provenance Digest must be lowercase SHA-256 hex')
    if not isinstance(item.trust,(int,float)) or isinstance(item.trust,bool) or not math.isfinite(float(item.trust)) or not 0.0<=float(item.trust)<=1.0:
        raise ValueError('Trust must be finite and within 0..1')
    observed=_parse_aware(item.observed_time).isoformat()
    return EvidenceItem(eid,sid,claim,observed,str(item.provenance_digest),float(item.trust),group)

def _bundle_payload(schema:str,items:tuple[EvidenceItem,...]):
    return {'schema':schema,'items':items}

def build_bundle(items):
    vals=tuple(_normalize_item(x) for x in items)
    if not vals: raise ValueError('Evidence Bundle must not be empty')
    ids=[x.evidence_id for x in vals]
    if len(ids)!=len(set(ids)): raise ValueError('Duplicate Evidence ID')
    vals=tuple(sorted(vals,key=lambda x:x.evidence_id))
    schema='NOEPIN_AL_EVIDENCE_BUNDLE_V1'
    return EvidenceBundle(schema,vals,_fp(_bundle_payload(schema,vals)))

def _bundle_fp_valid(bundle:EvidenceBundle)->bool:
    try:
        if bundle.schema!='NOEPIN_AL_EVIDENCE_BUNDLE_V1' or not bundle.items: return False
        ids=[]
        norm=[]
        for item in bundle.items:
            x=_normalize_item(item); ids.append(x.evidence_id); norm.append(x)
        if len(ids)!=len(set(ids)): return False
        vals=tuple(sorted(norm,key=lambda x:x.evidence_id))
        if vals!=bundle.items: return False
        return bundle.fingerprint==_fp(_bundle_payload(bundle.schema,vals))
    except Exception: return False

def _query_payload(req:EvidenceEvaluationRequest):
    return {'evaluation_id':req.evaluation_id,'at_time':req.at_time,'max_age_seconds':req.max_age_seconds,'binding':req.binding,'state_epoch':req.state_epoch}

def evaluate(req:EvidenceEvaluationRequest)->EvidenceEvaluationResult:
    eid=_norm(req.evaluation_id)
    if not eid:
        return EvidenceEvaluationResult(Decision.HOLD,NextAction.RETAIN_NO_ACTION_CANDIDATE,Escalation.INVALID_CONFIGURATION,EngineState.INVALID,'',False,(),(),(),0,0,0.0,0.0,False,req.bundle.fingerprint,('evaluation_id required',))
    if not isinstance(req.max_age_seconds,(int,float)) or isinstance(req.max_age_seconds,bool) or not math.isfinite(float(req.max_age_seconds)) or float(req.max_age_seconds)<0:
        return EvidenceEvaluationResult(Decision.HOLD,NextAction.RETAIN_NO_ACTION_CANDIDATE,Escalation.INVALID_CONFIGURATION,EngineState.INVALID,eid,False,(),(),(),0,len(req.bundle.items),0.0,0.0,False,req.bundle.fingerprint,('max_age_seconds must be finite and nonnegative',))
    try: now=_parse_aware(req.at_time)
    except ValueError:
        return EvidenceEvaluationResult(Decision.HOLD,NextAction.RETAIN_NO_ACTION_CANDIDATE,Escalation.INVALID_CONFIGURATION,EngineState.INVALID,eid,False,(),(),(),0,len(req.bundle.items),0.0,0.0,False,req.bundle.fingerprint,('at_time must be timezone-aware',))
    if not _bundle_fp_valid(req.bundle):
        return EvidenceEvaluationResult(Decision.DENY,NextAction.RETAIN_NO_ACTION_CANDIDATE,Escalation.BUNDLE_FINGERPRINT_MISMATCH,EngineState.INVALID,eid,False,(),(),(),0,len(req.bundle.items),0.0,0.0,False,req.bundle.fingerprint,('Evidence Bundle fingerprint or structure mismatch',))
    stale=[]; future=[]; fresh=[]
    groups=set(); trusts=[]
    for item in req.bundle.items:
        groups.add(item.independence_group); trusts.append(float(item.trust)); observed=_parse_aware(item.observed_time)
        age=(now-observed).total_seconds()
        if age<0:
            future.append(item.evidence_id); stale.append(item.evidence_id)
        elif age>float(req.max_age_seconds): stale.append(item.evidence_id)
        else: fresh.append(item.evidence_id)
    stale_t=tuple(stale); future_t=tuple(future); fresh_t=tuple(fresh)
    if future_t:
        return EvidenceEvaluationResult(Decision.HOLD,NextAction.REQUEST_STALE_OR_MISSING_EVIDENCE_CANDIDATE,Escalation.FUTURE_EVIDENCE_PRESENT,EngineState.EVIDENCE_REACQUISITION_CANDIDATE,eid,True,stale_t,future_t,fresh_t,len(groups),len(req.bundle.items),min(trusts),max(trusts),False,req.bundle.fingerprint,('Future timestamp Evidence requires reacquisition/review',))
    if stale_t:
        return EvidenceEvaluationResult(Decision.HOLD,NextAction.REQUEST_STALE_OR_MISSING_EVIDENCE_CANDIDATE,Escalation.STALE_EVIDENCE_PRESENT,EngineState.EVIDENCE_REACQUISITION_CANDIDATE,eid,True,stale_t,(),fresh_t,len(groups),len(req.bundle.items),min(trusts),max(trusts),False,req.bundle.fingerprint,('Stale Evidence present',))
    return EvidenceEvaluationResult(Decision.ALLOW,NextAction.CONTINUE_DECISION_ENVELOPE_BINDING_CANDIDATE,Escalation.NONE,EngineState.EVIDENCE_BUNDLE_FRESH_CANDIDATE,eid,True,(),(),fresh_t,len(groups),len(req.bundle.items),min(trusts),max(trusts),True,req.bundle.fingerprint,('Evidence Bundle structurally valid and fresh as an evidence candidate only',))

def prepare_state(req,binding,state_epoch):
    r=evaluate(req)
    itemfps=tuple((x.evidence_id,_fp(x)) for x in req.bundle.items)
    qfp=_fp(_query_payload(req)); rfp=_fp(r)
    base={'bundle_fingerprint':req.bundle.fingerprint,'query_fingerprint':qfp,'result_fingerprint':rfp,'item_fingerprints':itemfps,'binding':binding,'state_epoch':state_epoch}
    return PreparedEvidenceState(req,r,req.bundle.fingerprint,qfp,rfp,_fp(base),itemfps,binding,state_epoch)

def _prepared_integrity_ok(st:PreparedEvidenceState)->bool:
    base={'bundle_fingerprint':st.bundle_fingerprint,'query_fingerprint':st.query_fingerprint,'result_fingerprint':st.result_fingerprint,'item_fingerprints':st.item_fingerprints,'binding':st.binding,'state_epoch':st.state_epoch}
    return st.integrity_fingerprint==_fp(base)

def evaluate_prepared(st:PreparedEvidenceState,*,integrity_validated,current_bundle_fingerprint,current_query_fingerprint,current_result_fingerprint,current_time):
    if not integrity_validated or not _prepared_integrity_ok(st):
        return EvidenceEvaluationResult(Decision.HOLD,NextAction.RETAIN_NO_ACTION_CANDIDATE,Escalation.INVALID_CONFIGURATION,EngineState.INVALID,st.request.evaluation_id,False,(),(),(),0,len(st.request.bundle.items),0.0,0.0,False,st.request.bundle.fingerprint,('Prepared state integrity not validated',))
    if current_bundle_fingerprint!=st.bundle_fingerprint or current_query_fingerprint!=st.query_fingerprint or current_result_fingerprint!=st.result_fingerprint:
        return EvidenceEvaluationResult(Decision.HOLD,NextAction.RETAIN_NO_ACTION_CANDIDATE,Escalation.INVALID_CONFIGURATION,EngineState.INVALID,st.request.evaluation_id,False,(),(),(),0,len(st.request.bundle.items),0.0,0.0,False,st.request.bundle.fingerprint,('Prepared fingerprints do not match current state',))
    # Freshness must always be re-evaluated at the current time; cached ALLOW is not reused blindly.
    rr=EvidenceEvaluationRequest(st.request.evaluation_id,st.request.bundle,current_time,st.request.max_age_seconds,st.request.binding,st.request.state_epoch)
    return evaluate(rr)

def make_delta(old:PreparedEvidenceState,new:PreparedEvidenceState)->EvidenceChange:
    a=dict(old.item_fingerprints); b=dict(new.item_fingerprints)
    changed=tuple(sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k)))
    return EvidenceChange(changed,old.query_fingerprint!=new.query_fingerprint,old.integrity_fingerprint,new.integrity_fingerprint)

def plan_missing_only(old:PreparedEvidenceState,new:PreparedEvidenceState)->MissingOnlyPlan:
    d=make_delta(old,new); rec=tuple(f'EVIDENCE:{x}' for x in d.changed_or_missing_ids)
    if d.query_changed: rec=rec+('EVIDENCE_QUERY',)
    metadata=len(_canon({'records':rec,'from':d.from_fingerprint,'to':d.to_fingerprint}))
    return MissingOnlyPlan(rec,metadata,False)

def default_bundle():
    items=(
      EvidenceItem('EV-176-001','SRC-A','Observed build manifest matches expected digest','2026-11-13T11:52:00+00:00',_seed_fp('PROV-A'),0.96,'IND-A'),
      EvidenceItem('EV-176-002','SRC-B','Independent verifier reports the same artifact identity','2026-11-13T11:37:00+00:00',_seed_fp('PROV-B'),0.91,'IND-B'),
      EvidenceItem('EV-176-003','SRC-C','Replay evidence reports deterministic result','2026-11-13T11:18:00+00:00',_seed_fp('PROV-C'),0.88,'IND-C'),
      EvidenceItem('EV-176-004','SRC-D','Static safety evidence contains no external execution path','2026-11-13T11:05:00+00:00',_seed_fp('PROV-D'),0.93,'IND-B'),
    )
    return build_bundle(items)

def default_request():
    return EvidenceEvaluationRequest('EB-176-A',default_bundle(),'2026-11-13T12:00:00+00:00',3600.0,'DEFAULT-BINDING','EPOCH-1')
def default_evaluation(): return evaluate(default_request())

if __name__=='__main__': print(json.dumps(_obj(default_evaluation()),ensure_ascii=False,sort_keys=True,indent=2))
