"""NOEPIN AL 133 — Memory Importance Decay Scheduler — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-133
DCSR: LIMITED INTEGRATION / 限定適用.

Retention/archive/delete/refresh outputs are candidates only. Memory != Truth. Mention != Memory.
No candidate performs deletion, archival, permission, authority, approval, external writes or action success.
DCSR reconstruction does not create a new memory or known fact.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str,Enum): ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class RetentionState(str,Enum): RETAIN='RETAIN'; ARCHIVE='ARCHIVE'; DELETE='DELETE'; REFRESH='REFRESH'; PROTECTED='PROTECTED'; MENTION_ONLY='MENTION_ONLY'; INVALID='INVALID'
class NextAction(str,Enum): RETAIN_CANDIDATE='RETAIN_CANDIDATE'; ARCHIVE_CANDIDATE='ARCHIVE_CANDIDATE'; DELETE_CANDIDATE='DELETE_CANDIDATE'; REFRESH_CANDIDATE='REFRESH_CANDIDATE'; HOLD_PROTECTED_CANDIDATE='HOLD_PROTECTED_CANDIDATE'
class Escalation(str,Enum): NONE='NONE'; LEGAL_HOLD='LEGAL_HOLD'; SAFETY_CRITICAL='SAFETY_CRITICAL'; DELETION_FORBIDDEN='DELETION_FORBIDDEN'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'
class RecordKind(str,Enum): MEMORY='MEMORY'; MENTION='MENTION'

@dataclass(frozen=True)
class MemoryMetadata:
    memory_id:str; source_id:str; purpose_id:str; created_at:int; last_used_at:int|None; usage_count:int
    importance:float; freshness:float; trust:float; purpose_active:bool; legal_hold:bool; safety_critical:bool
    deletion_forbidden:bool; kind:RecordKind; binding:str; state_epoch:str

@dataclass(frozen=True)
class RetentionPolicy:
    now:int=1000
    decay_half_life:float=300.0
    archive_threshold:float=.42
    delete_threshold:float=.20
    refresh_age:float=500.0
    frequent_use_threshold:int=8
    purpose_end_multiplier:float=.70
    min_trust:float=.0

@dataclass(frozen=True)
class DecayRequest:
    request_id:str; memories:tuple[MemoryMetadata,...]; policy:RetentionPolicy; binding:str; state_epoch:str

@dataclass(frozen=True)
class MemoryRetentionCandidate:
    memory_id:str; retention_priority:float; state:RetentionState; next_action:NextAction; escalation:Escalation
    age:float; usage_factor:float; time_factor:float; reasons:tuple[str,...]

@dataclass(frozen=True)
class DecayResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; reasons:tuple[str,...]
    candidates:tuple[MemoryRetentionCandidate,...]; next_gate_candidate:bool
    memory_promoted_to_truth:bool=False; mention_promoted_to_memory:bool=False; delete_executed:bool=False
    archive_executed:bool=False; refresh_executed:bool=False; memory_write_performed:bool=False
    dcsr_reconstruction_created_memory:bool=False; sender_authority_inherited:bool=False; sender_intent_inherited:bool=False
    sender_agreement_inherited:bool=False; permission_granted:bool=False; approval_executed:bool=False
    authority_granted:bool=False; stop_executed:bool=False; action_executed:bool=False; plan_committed:bool=False
    publish_executed:bool=False; external_write_performed:bool=False; world_truth_proven:bool=False
    domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False

@dataclass(frozen=True)
class PreparedDecayState:
    request:DecayRequest; result:DecayResult; context_fingerprint:str; memory_fingerprint:str; policy_fingerprint:str
    outcome_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str

@dataclass(frozen=True)
class DecayDelta:
    changed_memories:tuple[MemoryMetadata,...]; removed_memory_ids:tuple[str,...]; policy_changed:bool
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
def _manifest_fp(req): return _fp((req.memories,req.policy,req.binding,req.state_epoch))

def default_policy(): return RetentionPolicy()
def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    ms=(
      MemoryMetadata('MEM-IMPORTANT','SRC-1','P-CORE',100,900,20,.95,.90,.95,True,False,True,False,RecordKind.MEMORY,b,e),
      MemoryMetadata('MEM-LOW','SRC-2','P-OLD',100,120,0,.10,.10,.70,False,False,False,False,RecordKind.MEMORY,b,e),
      MemoryMetadata('MEM-FREQUENT-OLD','SRC-3','P-LONG',100,200,15,.55,.25,.85,True,False,False,False,RecordKind.MEMORY,b,e),
      MemoryMetadata('MENTION-1','SRC-4','P-CHAT',900,900,1,.9,.9,.9,True,False,False,False,RecordKind.MENTION,b,e),
    )
    return DecayRequest('DEFAULT-133',ms,default_policy(),b,e)

def _invalid(reason):
    return DecayResult(Decision.HOLD,NextAction.HOLD_PROTECTED_CANDIDATE,Escalation.INVALID_CONFIGURATION,(reason,'NO_DESTRUCTIVE_EXECUTION','MEMORY_NOT_PROMOTED_TO_TRUTH'),(),False)

def _validate(req):
    if not req.request_id or not req.binding or not req.state_epoch: return 'INVALID_REQUEST_IDENTITY'
    p=req.policy
    vals=(p.decay_half_life,p.archive_threshold,p.delete_threshold,p.refresh_age,p.purpose_end_multiplier,p.min_trust)
    if not all(_finite(x) for x in vals): return 'NONFINITE_POLICY'
    if p.decay_half_life<=0 or p.refresh_age<0 or p.frequent_use_threshold<0: return 'INVALID_POLICY_RANGE'
    if not (0<=p.delete_threshold<=p.archive_threshold<=1 and 0<=p.purpose_end_multiplier<=1 and 0<=p.min_trust<=1): return 'INVALID_POLICY_THRESHOLDS'
    if not isinstance(p.now,int) or isinstance(p.now,bool): return 'INVALID_POLICY_NOW'
    ids=set()
    for m in req.memories:
        if not m.memory_id or not m.source_id or not m.purpose_id: return 'INVALID_MEMORY_IDENTITY'
        if m.memory_id in ids: return 'DUPLICATE_MEMORY_ID'
        ids.add(m.memory_id)
        if m.binding!=req.binding or m.state_epoch!=req.state_epoch: return 'MEMORY_BINDING_MISMATCH'
        if not isinstance(m.kind,RecordKind): return 'INVALID_RECORD_KIND'
        if not isinstance(m.created_at,int) or isinstance(m.created_at,bool): return 'INVALID_CREATED_AT'
        if m.last_used_at is not None and (not isinstance(m.last_used_at,int) or isinstance(m.last_used_at,bool)): return 'INVALID_LAST_USED_AT'
        if m.created_at>p.now or (m.last_used_at is not None and (m.last_used_at<m.created_at or m.last_used_at>p.now)): return 'INVALID_TIME_ORDER'
        if not isinstance(m.usage_count,int) or isinstance(m.usage_count,bool) or m.usage_count<0: return 'INVALID_USAGE_COUNT'
        if not all(_finite(x) and 0<=x<=1 for x in (m.importance,m.freshness,m.trust)): return 'INVALID_MEMORY_SCORE'
    return None

def _score(m,p):
    age=float(p.now-(m.last_used_at if m.last_used_at is not None else m.created_at))
    time_factor=2.0**(-age/p.decay_half_life)
    usage_factor=min(1.0, math.log1p(m.usage_count)/math.log(11.0)) if m.usage_count>0 else 0.0
    score=.45*m.importance+.25*usage_factor+.20*m.freshness+.10*m.trust
    score*=.55+.45*time_factor
    if not m.purpose_active: score*=p.purpose_end_multiplier
    return max(0.0,min(1.0,score)),age,usage_factor,time_factor

def evaluate(req:DecayRequest)->DecayResult:
    bad=_validate(req)
    if bad: return _invalid(bad)
    out=[]
    for m in sorted(req.memories,key=lambda x:x.memory_id):
        if m.kind==RecordKind.MENTION:
            out.append(MemoryRetentionCandidate(m.memory_id,0.0,RetentionState.MENTION_ONLY,NextAction.RETAIN_CANDIDATE,Escalation.NONE,0.0,0.0,0.0,('MENTION_IS_NOT_MEMORY','NO_RETENTION_MUTATION'))); continue
        score,age,uf,tf=_score(m,req.policy)
        reasons=[]; esc=Escalation.NONE
        if m.legal_hold:
            state=RetentionState.PROTECTED; action=NextAction.RETAIN_CANDIDATE; esc=Escalation.LEGAL_HOLD; reasons+=['LEGAL_HOLD_PROTECTS_MEMORY','DELETE_FORBIDDEN']
        elif m.safety_critical:
            state=RetentionState.PROTECTED; action=NextAction.RETAIN_CANDIDATE; esc=Escalation.SAFETY_CRITICAL; reasons+=['SAFETY_CRITICAL_PROTECTS_MEMORY','DELETE_FORBIDDEN']
        elif m.deletion_forbidden:
            state=RetentionState.PROTECTED; action=NextAction.RETAIN_CANDIDATE; esc=Escalation.DELETION_FORBIDDEN; reasons+=['RETENTION_POLICY_DELETE_FORBIDDEN']
        elif age>=req.policy.refresh_age and m.usage_count>=req.policy.frequent_use_threshold:
            state=RetentionState.REFRESH; action=NextAction.REFRESH_CANDIDATE; reasons+=['OLD_BUT_FREQUENTLY_USED','REFRESH_BEFORE_REUSE']
        elif m.trust<req.policy.min_trust:
            state=RetentionState.REFRESH; action=NextAction.REFRESH_CANDIDATE; reasons+=['BELOW_MIN_TRUST','RECONFIRM_BEFORE_REUSE']
        elif score<req.policy.delete_threshold:
            state=RetentionState.DELETE; action=NextAction.DELETE_CANDIDATE; reasons+=['LOW_PRIORITY_DELETE_CANDIDATE']
        elif score<req.policy.archive_threshold:
            state=RetentionState.ARCHIVE; action=NextAction.ARCHIVE_CANDIDATE; reasons+=['LOW_PRIORITY_ARCHIVE_CANDIDATE']
        else:
            state=RetentionState.RETAIN; action=NextAction.RETAIN_CANDIDATE; reasons+=['RETENTION_PRIORITY_SUFFICIENT']
        if not m.purpose_active: reasons.append('PURPOSE_ENDED_POLICY_APPLIED')
        reasons += ['CANDIDATE_ONLY_NO_MUTATION','MEMORY_NOT_PROMOTED_TO_TRUTH']
        out.append(MemoryRetentionCandidate(m.memory_id,round(score,12),state,action,esc,age,round(uf,12),round(tf,12),tuple(reasons)))
    protected=[x for x in out if x.state==RetentionState.PROTECTED]
    if protected:
        action=NextAction.RETAIN_CANDIDATE; esc=protected[0].escalation
        reasons=('PROTECTED_MEMORY_PRESENT','NO_AUTOMATIC_DELETION','MEMORY_NOT_PROMOTED_TO_TRUTH','NO_PERMISSION_OR_ACTION_PROMOTION')
    elif any(x.state==RetentionState.REFRESH for x in out):
        action=NextAction.REFRESH_CANDIDATE; esc=Escalation.NONE; reasons=('REFRESH_CANDIDATE_PRESENT','NO_AUTOMATIC_REFRESH','NO_DESTRUCTIVE_EXECUTION')
    elif any(x.state==RetentionState.DELETE for x in out):
        action=NextAction.DELETE_CANDIDATE; esc=Escalation.NONE; reasons=('DELETE_CANDIDATE_PRESENT','DELETE_NOT_EXECUTED','NO_DESTRUCTIVE_EXECUTION')
    elif any(x.state==RetentionState.ARCHIVE for x in out):
        action=NextAction.ARCHIVE_CANDIDATE; esc=Escalation.NONE; reasons=('ARCHIVE_CANDIDATE_PRESENT','ARCHIVE_NOT_EXECUTED','NO_DESTRUCTIVE_EXECUTION')
    else:
        action=NextAction.RETAIN_CANDIDATE; esc=Escalation.NONE; reasons=('RETENTION_PLAN_CANDIDATE','NO_DESTRUCTIVE_EXECUTION')
    return DecayResult(Decision.ALLOW,action,esc,reasons,tuple(out),True)

def default_evaluation(): return evaluate(default_request())

def _fps(req,res):
    return (_fp((req.request_id,req.binding,req.state_epoch)),_fp(req.memories),_fp(req.policy),_fp(res))
def prepare_state(req,binding,state_epoch):
    if binding!=req.binding or state_epoch!=req.state_epoch: raise ValueError('PREPARED_BINDING_MISMATCH')
    res=evaluate(req); c,m,p,o=_fps(req,res); integ=_fp((c,m,p,o,binding,state_epoch))
    return PreparedDecayState(req,res,c,m,p,o,integ,binding,state_epoch)
def validate_prepared_integrity(st): return st.integrity_fingerprint==_fp((st.context_fingerprint,st.memory_fingerprint,st.policy_fingerprint,st.outcome_fingerprint,st.binding,st.state_epoch))
def evaluate_prepared(st,*,integrity_validated,current_context_fingerprint,current_memory_fingerprint,current_policy_fingerprint,current_outcome_fingerprint):
    if not integrity_validated or not validate_prepared_integrity(st): return _invalid('PREPARED_INTEGRITY_NOT_VALIDATED')
    if (current_context_fingerprint,current_memory_fingerprint,current_policy_fingerprint,current_outcome_fingerprint)!=(st.context_fingerprint,st.memory_fingerprint,st.policy_fingerprint,st.outcome_fingerprint): return _invalid('PREPARED_FINGERPRINT_MISMATCH')
    return st.result

def make_delta(old,new):
    a={m.memory_id:m for m in old.request.memories}; b={m.memory_id:m for m in new.request.memories}
    changed=tuple(b[k] for k in sorted(b) if k not in a or a[k]!=b[k]); removed=tuple(sorted(set(a)-set(b)))
    return DecayDelta(changed,removed,old.policy_fingerprint!=new.policy_fingerprint,_manifest_fp(old.request),_manifest_fp(new.request))
def plan_missing_only(old,new):
    d=make_delta(old,new); ids=[m.memory_id for m in d.changed_memories]+list(d.removed_memory_ids)
    if d.policy_changed: ids.append('RETENTION_POLICY')
    meta=len(_canon((tuple(ids),d.from_manifest_fingerprint,d.to_manifest_fingerprint)))
    return MissingOnlyPlan(tuple(ids),meta,False)
