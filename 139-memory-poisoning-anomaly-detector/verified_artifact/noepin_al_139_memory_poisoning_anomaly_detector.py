"""NOEPIN AL 139 — Memory Poisoning Anomaly Detector — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-139
DCSR: LIMITED INTEGRATION / 限定適用.

Detects anomalous Memory-write candidates from source, content-shift, write-history,
policy/identity impact, purpose and provenance evidence. Outputs are candidates only.
Memory != Truth. Mention != Memory. Anomaly Score != Safety Proof or Fact Proof.
Quarantine Decision != Quarantine Execution. DENY Candidate != Stop Execution.
Source Trust != Source Authority. DCSR reconstruction does not create a new Memory,
known Fact, Permission, Approval, Action, or Action Success.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str, Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class DetectorState(str, Enum):
    CLEAN_CANDIDATE='CLEAN_CANDIDATE'; WARNING_CANDIDATE='WARNING_CANDIDATE'
    QUARANTINE_CANDIDATE='QUARANTINE_CANDIDATE'; CRITICAL_DENY_CANDIDATE='CRITICAL_DENY_CANDIDATE'
    MENTION_ONLY='MENTION_ONLY'; EMPTY='EMPTY'; INVALID='INVALID'
class NextAction(str, Enum):
    MEMORY_CONTINUE_CANDIDATE='MEMORY_CONTINUE_CANDIDATE'; REVIEW_CANDIDATE='REVIEW_CANDIDATE'
    QUARANTINE_CANDIDATE='QUARANTINE_CANDIDATE'; BLOCK_INTEGRATION_CANDIDATE='BLOCK_INTEGRATION_CANDIDATE'
    NO_MEMORY_CANDIDATE='NO_MEMORY_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; BULK_WRITE_WARNING='BULK_WRITE_WARNING'; POISONING_REVIEW='POISONING_REVIEW'
    UNTRUSTED_POLICY_SOURCE='UNTRUSTED_POLICY_SOURCE'; CRITICAL_ANOMALY='CRITICAL_ANOMALY'
    INVALID_CONFIGURATION='INVALID_CONFIGURATION'
class RecordKind(str, Enum): MEMORY='MEMORY'; MENTION='MENTION'

@dataclass(frozen=True)
class MemoryWriteCandidate:
    memory_id:str; content:str; category:str; source_id:str; source_trust:float; purpose:str
    provenance_ids:tuple[str,...]; content_shift:float; taint_labels:tuple[str,...]
    instruction_like:bool; critical:bool; kind:RecordKind; binding:str; state_epoch:str

@dataclass(frozen=True)
class WriteHistoryEntry:
    event_id:str; memory_id:str; logical_time:int; source_id:str; category:str; binding:str; state_epoch:str

@dataclass(frozen=True)
class BaselinePatterns:
    expected_writes_per_window:int=8; window_size:int=10; surge_ratio:float=2.0
    trusted_source_floor:float=.60; review_threshold:float=.40; quarantine_threshold:float=.60
    deny_threshold:float=.80; max_normal_content_shift:float=.35
    allowed_purposes:tuple[str,...]=('PROJECT-A','GENERAL')
    policy_identity_categories:tuple[str,...]=('POLICY','IDENTITY','AUTHORITY')

@dataclass(frozen=True)
class DetectionRequest:
    request_id:str; new_memories:tuple[MemoryWriteCandidate,...]; write_history:tuple[WriteHistoryEntry,...]
    baseline:BaselinePatterns; binding:str; state_epoch:str

@dataclass(frozen=True)
class MemoryAnomalyEvidence:
    memory_id:str; score:float; source_risk:float; content_shift_risk:float; frequency_risk:float
    policy_identity_risk:float; instruction_risk:float; provenance_gap_risk:float; purpose_mismatch_risk:float
    hard_untrusted_policy:bool; critical_high_anomaly:bool; reasons:tuple[str,...]

@dataclass(frozen=True)
class DetectionResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; detector_state:DetectorState
    anomaly_score:float; evidence:tuple[MemoryAnomalyEvidence,...]; affected_memory_ids:tuple[str,...]
    quarantine_candidate_ids:tuple[str,...]; review_candidate_ids:tuple[str,...]; reasons:tuple[str,...]
    next_gate_candidate:bool
    memory_promoted_to_truth:bool=False; mention_promoted_to_memory:bool=False; anomaly_promoted_to_fact_proof:bool=False
    anomaly_promoted_to_safety_proof:bool=False; source_trust_promoted_to_source_authority:bool=False
    quarantine_executed:bool=False; memory_write_performed:bool=False; memory_delete_performed:bool=False
    policy_modified:bool=False; identity_modified:bool=False; dcsr_reconstruction_created_memory:bool=False
    sender_authority_inherited:bool=False; sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False
    permission_granted:bool=False; approval_executed:bool=False; authority_granted:bool=False; stop_executed:bool=False
    action_executed:bool=False; plan_committed:bool=False; publish_executed:bool=False; external_write_performed:bool=False
    world_truth_proven:bool=False; domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False

@dataclass(frozen=True)
class PreparedDetectionState:
    request:DetectionRequest; result:DetectionResult; context_fingerprint:str; new_memory_fingerprint:str
    history_fingerprint:str; baseline_fingerprint:str; outcome_fingerprint:str; integrity_fingerprint:str
    binding:str; state_epoch:str

@dataclass(frozen=True)
class PoisoningDelta:
    changed_new_memories:tuple[MemoryWriteCandidate,...]; removed_memory_ids:tuple[str,...]
    appended_history:tuple[WriteHistoryEntry,...]; baseline_changed:bool
    from_manifest_fingerprint:str; to_manifest_fingerprint:str

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
def _clamp(x): return 0.0 if x<0 else (1.0 if x>1 else float(x))
def _manifest_fp(req): return _fp((req.new_memories,req.write_history,req.baseline,req.binding,req.state_epoch))

def default_baseline(): return BaselinePatterns()
def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    mem=MemoryWriteCandidate('MEM-139-A','The project preference was updated by the owner.','FACT','SRC-TRUSTED',.92,'PROJECT-A',('TRACE-139-A',),.10,(),False,False,RecordKind.MEMORY,b,e)
    hist=tuple(WriteHistoryEntry(f'H-{i}',f'OLD-{i}',i,'SRC-TRUSTED','FACT',b,e) for i in range(5))
    return DetectionRequest('REQ-139',(mem,),hist,default_baseline(),b,e)

def _invalid(reason):
    return DetectionResult(Decision.HOLD,NextAction.REVIEW_CANDIDATE,Escalation.INVALID_CONFIGURATION,DetectorState.INVALID,1.0,(),(),(),(),(reason,'NO_MEMORY_WRITE','NO_QUARANTINE_EXECUTION'),False)

def _validate(req):
    p=req.baseline
    nums=(p.surge_ratio,p.trusted_source_floor,p.review_threshold,p.quarantine_threshold,p.deny_threshold,p.max_normal_content_shift)
    if not all(_finite(x) for x in nums): return 'NONFINITE_BASELINE'
    if p.expected_writes_per_window<0 or p.window_size<=0: return 'INVALID_WINDOW_BASELINE'
    if p.surge_ratio<1: return 'SURGE_RATIO_BELOW_ONE'
    if not (0<=p.trusted_source_floor<=1 and 0<=p.review_threshold<=p.quarantine_threshold<=p.deny_threshold<=1 and 0<=p.max_normal_content_shift<=1): return 'BASELINE_RANGE_OR_THRESHOLD_ORDER'
    ids=set(); events=set()
    for x in req.new_memories:
        if x.memory_id in ids: return 'DUPLICATE_MEMORY_ID'
        ids.add(x.memory_id)
        if x.binding!=req.binding or x.state_epoch!=req.state_epoch: return 'MEMORY_STATE_BINDING_MISMATCH'
        if not x.memory_id or not x.source_id or not x.category: return 'EMPTY_MEMORY_KEY'
        if not _finite(x.source_trust) or not 0<=x.source_trust<=1: return 'SOURCE_TRUST_RANGE_OR_NONFINITE'
        if not _finite(x.content_shift) or not 0<=x.content_shift<=1: return 'CONTENT_SHIFT_RANGE_OR_NONFINITE'
        if len(set(x.provenance_ids))!=len(x.provenance_ids): return 'DUPLICATE_PROVENANCE_ID'
    for h in req.write_history:
        if h.event_id in events: return 'DUPLICATE_HISTORY_EVENT_ID'
        events.add(h.event_id)
        if h.binding!=req.binding or h.state_epoch!=req.state_epoch: return 'HISTORY_STATE_BINDING_MISMATCH'
        if isinstance(h.logical_time,bool) or not isinstance(h.logical_time,int): return 'INVALID_LOGICAL_TIME'
    return None

def _frequency_risk(req):
    p=req.baseline
    if not req.write_history:
        recent=0
    else:
        now=max(h.logical_time for h in req.write_history)
        lo=now-p.window_size+1
        recent=sum(1 for h in req.write_history if h.logical_time>=lo)
    projected=recent+sum(1 for x in req.new_memories if x.kind==RecordKind.MEMORY)
    expected=max(1,p.expected_writes_per_window)
    ratio=projected/expected
    if ratio<=1: return 0.0,ratio,projected
    # Risk reaches 1.0 at twice the configured surge ratio.
    denom=max(.000001,p.surge_ratio)
    return _clamp((ratio-1.0)/denom),ratio,projected

def _evidence_for(x,p,freq_risk):
    source_risk=_clamp((p.trusted_source_floor-x.source_trust)/max(p.trusted_source_floor,.000001)) if x.source_trust<p.trusted_source_floor else 0.0
    shift_risk=_clamp((x.content_shift-p.max_normal_content_shift)/max(1-p.max_normal_content_shift,.000001)) if x.content_shift>p.max_normal_content_shift else _clamp(x.content_shift*.25)
    pol=1.0 if x.category.upper() in set(c.upper() for c in p.policy_identity_categories) else 0.0
    instr=1.0 if x.instruction_like else 0.0
    prov=1.0 if not x.provenance_ids else 0.0
    purpose=1.0 if x.purpose not in p.allowed_purposes else 0.0
    taint=set(t.upper() for t in x.taint_labels)
    if 'UNTRUSTED_EXTERNAL' in taint: source_risk=max(source_risk,.80)
    if 'POLICY_TAINT' in taint: pol=max(pol,1.0)
    if 'INSTRUCTION_TAINT' in taint: instr=max(instr,1.0)
    score=_clamp(.20*source_risk+.18*shift_risk+.16*freq_risk+.22*pol+.14*instr+.05*prov+.05*purpose)
    hard_untrusted=(x.source_trust<p.trusted_source_floor or 'UNTRUSTED_EXTERNAL' in taint) and (pol>0 or instr>0)
    if hard_untrusted: score=max(score,p.quarantine_threshold+.08)
    critical=(x.critical or pol>0) and score>=p.deny_threshold
    reasons=[]
    if source_risk>0: reasons.append('SOURCE_TRUST_ANOMALY')
    if shift_risk>.10: reasons.append('CONTENT_SHIFT_ANOMALY')
    if freq_risk>=.50: reasons.append('WRITE_FREQUENCY_SURGE')
    if pol>0: reasons.append('POLICY_OR_IDENTITY_IMPACT')
    if instr>0: reasons.append('INSTRUCTION_LIKE_CONTENT')
    if prov>0: reasons.append('PROVENANCE_GAP')
    if purpose>0: reasons.append('PURPOSE_MISMATCH')
    if hard_untrusted: reasons.append('UNTRUSTED_POLICY_OR_INSTRUCTION_SOURCE')
    if critical: reasons.append('CRITICAL_HIGH_ANOMALY')
    if not reasons: reasons.append('WITHIN_BASELINE_CANDIDATE')
    return MemoryAnomalyEvidence(x.memory_id,score,source_risk,shift_risk,freq_risk,pol,instr,prov,purpose,hard_untrusted,critical,tuple(reasons))

def evaluate(req):
    err=_validate(req)
    if err: return _invalid(err)
    memories=tuple(sorted((x for x in req.new_memories if x.kind==RecordKind.MEMORY),key=lambda x:x.memory_id))
    mentions=tuple(x for x in req.new_memories if x.kind==RecordKind.MENTION)
    if not memories:
        state=DetectorState.MENTION_ONLY if mentions else DetectorState.EMPTY
        return DetectionResult(Decision.ALLOW,NextAction.NO_MEMORY_CANDIDATE,Escalation.NONE,state,0.0,(),(),(),(),('NO_MEMORY_WRITE_CANDIDATES','MENTION_NOT_PROMOTED_TO_MEMORY','NO_MEMORY_WRITE'),True)
    freq,ratio,projected=_frequency_risk(req); p=req.baseline
    ev=tuple(_evidence_for(x,p,freq) for x in memories)
    max_score=max(e.score for e in ev)
    critical=tuple(e.memory_id for e in ev if e.critical_high_anomaly)
    hardq=tuple(e.memory_id for e in ev if e.hard_untrusted_policy)
    quarantine=tuple(sorted(e.memory_id for e in ev if e.score>=p.quarantine_threshold or e.hard_untrusted_policy or e.critical_high_anomaly))
    review=tuple(sorted(e.memory_id for e in ev if e.score>=p.review_threshold and e.memory_id not in quarantine))
    affected=tuple(sorted(set(quarantine+review)))
    surge=ratio>=p.surge_ratio
    if critical:
        return DetectionResult(Decision.DENY,NextAction.BLOCK_INTEGRATION_CANDIDATE,Escalation.CRITICAL_ANOMALY,DetectorState.CRITICAL_DENY_CANDIDATE,max_score,ev,affected,quarantine,review,('CRITICAL_HIGH_ANOMALY_MEMORY','MEMORY_INTEGRATION_BLOCK_CANDIDATE_ONLY','NO_MEMORY_WRITE','NO_QUARANTINE_EXECUTION'),False)
    if hardq or quarantine:
        esc=Escalation.UNTRUSTED_POLICY_SOURCE if hardq else Escalation.POISONING_REVIEW
        return DetectionResult(Decision.HOLD,NextAction.QUARANTINE_CANDIDATE,esc,DetectorState.QUARANTINE_CANDIDATE,max_score,ev,affected,quarantine,review,('ANOMALOUS_MEMORY_QUARANTINE_CANDIDATE','REVIEW_REQUIRED','NO_MEMORY_WRITE','NO_QUARANTINE_EXECUTION'),False)
    if surge or review:
        ids=affected if affected else tuple(x.memory_id for x in memories)
        esc=Escalation.BULK_WRITE_WARNING if surge else Escalation.POISONING_REVIEW
        return DetectionResult(Decision.HUMAN_APPROVAL,NextAction.REVIEW_CANDIDATE,esc,DetectorState.WARNING_CANDIDATE,max_score,ev,ids,(),review,('WRITE_PATTERN_OR_MEMORY_ANOMALY_WARNING','HUMAN_REVIEW_CANDIDATE','NO_MEMORY_WRITE'),False)
    return DetectionResult(Decision.ALLOW,NextAction.MEMORY_CONTINUE_CANDIDATE,Escalation.NONE,DetectorState.CLEAN_CANDIDATE,max_score,ev,(),(),(),('WITHIN_BASELINE_CANDIDATE','NORMAL_FACT_UPDATE_CONTINUE_CANDIDATE','NO_MEMORY_WRITE'),True)

def default_evaluation(): return evaluate(default_request())

def _fps(req,res): return (_fp((req.request_id,req.binding,req.state_epoch)),_fp(req.new_memories),_fp(req.write_history),_fp(req.baseline),_fp(res))
def prepare_state(req,binding,state_epoch):
    if binding!=req.binding or state_epoch!=req.state_epoch: raise ValueError('PREPARED_BINDING_MISMATCH')
    res=evaluate(req); c,n,h,b,o=_fps(req,res); integ=_fp((c,n,h,b,o,binding,state_epoch))
    return PreparedDetectionState(req,res,c,n,h,b,o,integ,binding,state_epoch)
def validate_prepared_integrity(st): return st.integrity_fingerprint==_fp((st.context_fingerprint,st.new_memory_fingerprint,st.history_fingerprint,st.baseline_fingerprint,st.outcome_fingerprint,st.binding,st.state_epoch))
def evaluate_prepared(st,*,integrity_validated,current_context_fingerprint,current_new_memory_fingerprint,current_history_fingerprint,current_baseline_fingerprint,current_outcome_fingerprint):
    if not integrity_validated or not validate_prepared_integrity(st): return _invalid('PREPARED_INTEGRITY_NOT_VALIDATED')
    if (current_context_fingerprint,current_new_memory_fingerprint,current_history_fingerprint,current_baseline_fingerprint,current_outcome_fingerprint)!=(st.context_fingerprint,st.new_memory_fingerprint,st.history_fingerprint,st.baseline_fingerprint,st.outcome_fingerprint): return _invalid('PREPARED_FINGERPRINT_MISMATCH')
    return st.result

def make_delta(old,new):
    a={x.memory_id:x for x in old.request.new_memories}; b={x.memory_id:x for x in new.request.new_memories}
    changed=tuple(b[k] for k in sorted(b) if k not in a or a[k]!=b[k]); removed=tuple(sorted(set(a)-set(b)))
    old_hist={x.event_id:x for x in old.request.write_history}; appended=tuple(x for x in new.request.write_history if x.event_id not in old_hist or old_hist[x.event_id]!=x)
    return PoisoningDelta(changed,removed,appended,old.baseline_fingerprint!=new.baseline_fingerprint,_manifest_fp(old.request),_manifest_fp(new.request))
def plan_missing_only(old,new):
    d=make_delta(old,new); ids=[f'MEMORY:{x.memory_id}' for x in d.changed_new_memories]+[f'MEMORY:{x}' for x in d.removed_memory_ids]+[f'HISTORY:{x.event_id}' for x in d.appended_history]
    if d.baseline_changed: ids.append('BASELINE_PATTERNS')
    meta=len(_canon((tuple(ids),d.from_manifest_fingerprint,d.to_manifest_fingerprint)))
    return MissingOnlyPlan(tuple(ids),meta,False)
