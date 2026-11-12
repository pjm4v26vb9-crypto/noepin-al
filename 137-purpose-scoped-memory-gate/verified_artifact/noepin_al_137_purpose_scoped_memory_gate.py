"""NOEPIN AL 137 — Purpose-Scoped Memory Gate — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-137
DCSR: LIMITED INTEGRATION / 限定適用.

The output is a minimum-necessary Memory supply candidate, not an execution path.
Memory != Truth. Mention != Memory. Allowed Memory Set Candidate != Reasoner Transfer Execution.
Purpose Match != Permission Grant. Permission Evidence != Permission Execution.
Sensitivity classification != Truth. Unknown purpose/relevance/necessity is fail-closed.
No candidate performs Memory writes, reasoner transfer, external retrieval, permission grants,
approvals, authority changes, destructive mutation, or action execution.
DCSR reconstruction does not create a new Memory or known Fact.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str,Enum): ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class GateState(str,Enum):
    ALLOWED_SET_CANDIDATE='ALLOWED_SET_CANDIDATE'; EXCLUDED_ONLY='EXCLUDED_ONLY'; AMBIGUOUS_GOAL_HOLD='AMBIGUOUS_GOAL_HOLD'
    SENSITIVE_HOLD='SENSITIVE_HOLD'; MENTION_ONLY='MENTION_ONLY'; EMPTY='EMPTY'; INVALID='INVALID'
class NextAction(str,Enum):
    MEMORY_SUPPLY_CANDIDATE='MEMORY_SUPPLY_CANDIDATE'; EXCLUDED_AUDIT_CANDIDATE='EXCLUDED_AUDIT_CANDIDATE'
    PURPOSE_CLARIFICATION_CANDIDATE='PURPOSE_CLARIFICATION_CANDIDATE'; PERMISSION_REVIEW_CANDIDATE='PERMISSION_REVIEW_CANDIDATE'
    NO_MEMORY_CANDIDATE='NO_MEMORY_CANDIDATE'
class Escalation(str,Enum):
    NONE='NONE'; PURPOSE_AMBIGUOUS='PURPOSE_AMBIGUOUS'; SENSITIVE_RELEVANCE_UNKNOWN='SENSITIVE_RELEVANCE_UNKNOWN'
    SENSITIVE_PERMISSION_MISSING='SENSITIVE_PERMISSION_MISSING'; UNKNOWN_SENSITIVITY='UNKNOWN_SENSITIVITY'
    INVALID_CONFIGURATION='INVALID_CONFIGURATION'
class RecordKind(str,Enum): MEMORY='MEMORY'; MENTION='MENTION'
class Sensitivity(str,Enum): PUBLIC='PUBLIC'; INTERNAL='INTERNAL'; SENSITIVE='SENSITIVE'; RESTRICTED='RESTRICTED'; UNKNOWN='UNKNOWN'

@dataclass(frozen=True)
class MemoryMetadata:
    memory_id:str; semantic_key:str; purpose_tags:tuple[str,...]; sensitivity:Sensitivity
    relevance:float|None; necessity:float|None; trust:float; access_permission_evidence:bool
    active:bool; kind:RecordKind; source_id:str|None; recorded_at:int|None; binding:str; state_epoch:str

@dataclass(frozen=True)
class PurposeGatePolicy:
    min_relevance:float=.68
    min_necessity:float=.66
    min_trust:float=.55
    sensitive_requires_permission:bool=True
    restricted_requires_permission:bool=True
    unknown_sensitivity_exclude:bool=True
    unknown_score_exclude:bool=True
    minimum_necessary_per_semantic_key:bool=True
    require_goal_clarity:bool=True

@dataclass(frozen=True)
class PurposeGateRequest:
    request_id:str; current_goal:str; goal_purpose_tags:tuple[str,...]; goal_clarity:bool
    memories:tuple[MemoryMetadata,...]; policy:PurposeGatePolicy; binding:str; state_epoch:str

@dataclass(frozen=True)
class MemoryGateDisposition:
    memory_id:str; purpose_matched:bool; relevance_confirmed:bool; necessity_confirmed:bool
    permission_evidence_present:bool; allowed_candidate:bool; excluded:bool; reasons:tuple[str,...]

@dataclass(frozen=True)
class PurposeGateResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; gate_state:GateState; reasons:tuple[str,...]
    allowed_memory_ids:tuple[str,...]; excluded_memory_ids:tuple[str,...]; dispositions:tuple[MemoryGateDisposition,...]
    next_gate_candidate:bool
    memory_promoted_to_truth:bool=False; mention_promoted_to_memory:bool=False; allowed_set_transferred_to_reasoner:bool=False
    purpose_match_promoted_to_permission:bool=False; permission_evidence_promoted_to_permission_execution:bool=False
    sensitivity_promoted_to_truth:bool=False; external_retrieval_executed:bool=False; memory_write_performed:bool=False
    dcsr_reconstruction_created_memory:bool=False; sender_authority_inherited:bool=False; sender_intent_inherited:bool=False
    sender_agreement_inherited:bool=False; permission_granted:bool=False; approval_executed:bool=False; authority_granted:bool=False
    stop_executed:bool=False; action_executed:bool=False; plan_committed:bool=False; publish_executed:bool=False
    external_write_performed:bool=False; world_truth_proven:bool=False; domain_authority_promoted:bool=False
    safety_proven:bool=False; action_success:bool=False

@dataclass(frozen=True)
class PreparedPurposeGateState:
    request:PurposeGateRequest; result:PurposeGateResult; context_fingerprint:str; memory_fingerprint:str
    policy_fingerprint:str; outcome_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str

@dataclass(frozen=True)
class PurposeGateDelta:
    changed_memories:tuple[MemoryMetadata,...]; removed_memory_ids:tuple[str,...]; goal_changed:bool
    purpose_tags_changed:bool; goal_clarity_changed:bool; policy_changed:bool
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
def _manifest_fp(req): return _fp((req.current_goal,req.goal_purpose_tags,req.goal_clarity,req.memories,req.policy,req.binding,req.state_epoch))

def default_policy(): return PurposeGatePolicy()
def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    memories=(MemoryMetadata('MEM-1','SEM-DRAWING-GUIDE',('DRAWING_SUPPORT','CREATIVE_WORK'),Sensitivity.INTERNAL,.96,.94,.93,True,True,RecordKind.MEMORY,'SRC-1',1,b,e),)
    return PurposeGateRequest('REQ-137','Help with the current drawing task',('DRAWING_SUPPORT',),True,memories,default_policy(),b,e)

def _invalid(reason):
    return PurposeGateResult(Decision.HOLD,NextAction.EXCLUDED_AUDIT_CANDIDATE,Escalation.INVALID_CONFIGURATION,GateState.INVALID,(reason,'NO_REASONER_TRANSFER','NO_MEMORY_WRITE'),(),(),(),False)

def _validate(req):
    p=req.policy
    nums=(p.min_relevance,p.min_necessity,p.min_trust)
    if not all(_finite(x) for x in nums): return 'NONFINITE_POLICY'
    if not all(0<=x<=1 for x in nums): return 'POLICY_RANGE'
    if not isinstance(req.current_goal,str): return 'INVALID_CURRENT_GOAL'
    ids=set()
    for x in req.memories:
        if x.memory_id in ids: return 'DUPLICATE_MEMORY_ID'
        ids.add(x.memory_id)
        if x.binding!=req.binding or x.state_epoch!=req.state_epoch: return 'STATE_BINDING_MISMATCH'
        if not _finite(x.trust) or not 0<=x.trust<=1: return 'TRUST_RANGE_OR_NONFINITE'
        for score in (x.relevance,x.necessity):
            if score is not None and (not _finite(score) or not 0<=score<=1): return 'MEMORY_SCORE_RANGE_OR_NONFINITE'
        if not x.memory_id or not x.semantic_key: return 'EMPTY_MEMORY_KEY'
    return None

def _goal_tags(req): return tuple(sorted(set(t.strip() for t in req.goal_purpose_tags if isinstance(t,str) and t.strip())))
def _purpose_match(x,tags): return bool(set(x.purpose_tags).intersection(tags))
def _score(x):
    assert x.relevance is not None and x.necessity is not None
    return float(x.necessity)*.45 + float(x.relevance)*.40 + float(x.trust)*.15

def evaluate(req):
    err=_validate(req)
    if err: return _invalid(err)
    memories=tuple(sorted((x for x in req.memories if x.kind==RecordKind.MEMORY),key=lambda x:x.memory_id))
    mentions=tuple(x for x in req.memories if x.kind==RecordKind.MENTION)
    if not memories:
        state=GateState.MENTION_ONLY if mentions else GateState.EMPTY
        return PurposeGateResult(Decision.ALLOW,NextAction.NO_MEMORY_CANDIDATE,Escalation.NONE,state,('NO_MEMORY_RECORDS','MENTION_NOT_PROMOTED_TO_MEMORY','NO_REASONER_TRANSFER'),(),(),(),True)
    tags=_goal_tags(req); p=req.policy
    if (p.require_goal_clarity and not req.goal_clarity) or not tags or not req.current_goal.strip():
        disp=tuple(MemoryGateDisposition(x.memory_id,False,False,False,x.access_permission_evidence,False,True,('PURPOSE_AMBIGUOUS','FAIL_CLOSED')) for x in memories)
        return PurposeGateResult(Decision.HOLD,NextAction.PURPOSE_CLARIFICATION_CANDIDATE,Escalation.PURPOSE_AMBIGUOUS,GateState.AMBIGUOUS_GOAL_HOLD,('CURRENT_GOAL_PURPOSE_AMBIGUOUS','NO_MEMORY_SUPPLY','NO_REASONER_TRANSFER'),(),tuple(x.memory_id for x in memories),disp,False)
    dispositions=[]; provisional=[]; excluded=[]; sensitive_unknown=[]; permission_missing=[]; unknown_sensitivity=[]
    for x in memories:
        reasons=[]; pm=_purpose_match(x,tags); rel=False; nec=False; allowed=False
        if not x.active:
            reasons.append('INACTIVE_MEMORY')
        if not x.purpose_tags:
            reasons.append('MEMORY_PURPOSE_UNKNOWN')
        if not pm:
            reasons.append('PURPOSE_OUT_OF_SCOPE')
        else:
            reasons.append('PURPOSE_MATCHED')
        if x.sensitivity==Sensitivity.UNKNOWN:
            reasons.append('SENSITIVITY_UNKNOWN')
            if pm and p.unknown_sensitivity_exclude: unknown_sensitivity.append(x.memory_id)
        if x.relevance is None:
            reasons.append('RELEVANCE_UNKNOWN')
            if pm and x.sensitivity in (Sensitivity.SENSITIVE,Sensitivity.RESTRICTED): sensitive_unknown.append(x.memory_id)
        else:
            rel=x.relevance>=p.min_relevance
            reasons.append('RELEVANCE_CONFIRMED' if rel else 'RELEVANCE_BELOW_THRESHOLD')
        if x.necessity is None:
            reasons.append('NECESSITY_UNKNOWN')
            if pm and x.sensitivity in (Sensitivity.SENSITIVE,Sensitivity.RESTRICTED): sensitive_unknown.append(x.memory_id)
        else:
            nec=x.necessity>=p.min_necessity
            reasons.append('NECESSITY_CONFIRMED' if nec else 'NOT_MINIMUM_NECESSARY')
        if x.trust<p.min_trust: reasons.append('TRUST_BELOW_THRESHOLD')
        sensitive=x.sensitivity in (Sensitivity.SENSITIVE,Sensitivity.RESTRICTED)
        permission_required=(x.sensitivity==Sensitivity.SENSITIVE and p.sensitive_requires_permission) or (x.sensitivity==Sensitivity.RESTRICTED and p.restricted_requires_permission)
        # Permission is relevant only after purpose/relevance/necessity are confirmed. Unnecessary sensitive Memory is simply excluded.
        if x.active and pm and rel and nec and x.trust>=p.min_trust and x.sensitivity!=Sensitivity.UNKNOWN:
            if permission_required and not x.access_permission_evidence:
                reasons.append('EXPLICIT_PERMISSION_EVIDENCE_REQUIRED'); permission_missing.append(x.memory_id)
            else:
                allowed=True; provisional.append(x); reasons.append('ALLOWED_MEMORY_CANDIDATE_ONLY')
        if not allowed: excluded.append(x.memory_id)
        dispositions.append(MemoryGateDisposition(x.memory_id,pm,rel,nec,x.access_permission_evidence,allowed,not allowed,tuple(reasons)))
    # Minimum necessary: keep one highest-scoring candidate for each semantic key and exclude redundant equivalents.
    selected=[]; redundant=set()
    if p.minimum_necessary_per_semantic_key:
        by_sem={}
        for x in provisional: by_sem.setdefault(x.semantic_key,[]).append(x)
        for key in sorted(by_sem):
            group=sorted(by_sem[key],key=lambda x:(-_score(x),x.memory_id)); selected.append(group[0]); redundant.update(x.memory_id for x in group[1:])
    else: selected=list(provisional)
    if redundant:
        new=[]
        for d in dispositions:
            if d.memory_id in redundant:
                rs=tuple(r for r in d.reasons if r!='ALLOWED_MEMORY_CANDIDATE_ONLY')+('REDUNDANT_NOT_MINIMUM_NECESSARY',)
                new.append(MemoryGateDisposition(d.memory_id,d.purpose_matched,d.relevance_confirmed,d.necessity_confirmed,d.permission_evidence_present,False,True,rs)); excluded.append(d.memory_id)
            else: new.append(d)
        dispositions=new
    allowed_ids=tuple(sorted(x.memory_id for x in selected if x.memory_id not in redundant)); excluded_ids=tuple(sorted(set(excluded))); dispositions=tuple(sorted(dispositions,key=lambda d:d.memory_id))
    if sensitive_unknown:
        return PurposeGateResult(Decision.HOLD,NextAction.PURPOSE_CLARIFICATION_CANDIDATE,Escalation.SENSITIVE_RELEVANCE_UNKNOWN,GateState.SENSITIVE_HOLD,('SENSITIVE_MEMORY_RELEVANCE_OR_NECESSITY_UNKNOWN','FAIL_CLOSED','NO_REASONER_TRANSFER'),allowed_ids,excluded_ids,dispositions,False)
    if unknown_sensitivity:
        return PurposeGateResult(Decision.HOLD,NextAction.PURPOSE_CLARIFICATION_CANDIDATE,Escalation.UNKNOWN_SENSITIVITY,GateState.SENSITIVE_HOLD,('PURPOSE_MATCHED_MEMORY_SENSITIVITY_UNKNOWN','FAIL_CLOSED','NO_REASONER_TRANSFER'),allowed_ids,excluded_ids,dispositions,False)
    if permission_missing:
        return PurposeGateResult(Decision.HOLD,NextAction.PERMISSION_REVIEW_CANDIDATE,Escalation.SENSITIVE_PERMISSION_MISSING,GateState.SENSITIVE_HOLD,('SENSITIVE_MEMORY_PERMISSION_EVIDENCE_MISSING','PERMISSION_EVIDENCE_NOT_PERMISSION_EXECUTION','NO_REASONER_TRANSFER'),allowed_ids,excluded_ids,dispositions,False)
    if allowed_ids:
        return PurposeGateResult(Decision.ALLOW,NextAction.MEMORY_SUPPLY_CANDIDATE,Escalation.NONE,GateState.ALLOWED_SET_CANDIDATE,('PURPOSE_RELEVANT_MINIMUM_NECESSARY_SET','SUPPLY_CANDIDATE_ONLY','NO_REASONER_TRANSFER','NO_MEMORY_WRITE'),allowed_ids,excluded_ids,dispositions,True)
    return PurposeGateResult(Decision.ALLOW,NextAction.EXCLUDED_AUDIT_CANDIDATE,Escalation.NONE,GateState.EXCLUDED_ONLY,('NO_MEMORY_PASSED_PURPOSE_NECESSITY_GATE','EXCLUSIONS_AUDITABLE','NO_REASONER_TRANSFER'),(),excluded_ids,dispositions,True)

def default_evaluation(): return evaluate(default_request())

def _fps(req,res):
    return (_fp((req.request_id,req.current_goal,req.goal_purpose_tags,req.goal_clarity,req.binding,req.state_epoch)),_fp(req.memories),_fp(req.policy),_fp(res))
def prepare_state(req,binding,state_epoch):
    if binding!=req.binding or state_epoch!=req.state_epoch: raise ValueError('PREPARED_BINDING_MISMATCH')
    res=evaluate(req); c,m,p,o=_fps(req,res); integ=_fp((c,m,p,o,binding,state_epoch))
    return PreparedPurposeGateState(req,res,c,m,p,o,integ,binding,state_epoch)
def validate_prepared_integrity(st): return st.integrity_fingerprint==_fp((st.context_fingerprint,st.memory_fingerprint,st.policy_fingerprint,st.outcome_fingerprint,st.binding,st.state_epoch))
def evaluate_prepared(st,*,integrity_validated,current_context_fingerprint,current_memory_fingerprint,current_policy_fingerprint,current_outcome_fingerprint):
    if not integrity_validated or not validate_prepared_integrity(st): return _invalid('PREPARED_INTEGRITY_NOT_VALIDATED')
    if (current_context_fingerprint,current_memory_fingerprint,current_policy_fingerprint,current_outcome_fingerprint)!=(st.context_fingerprint,st.memory_fingerprint,st.policy_fingerprint,st.outcome_fingerprint): return _invalid('PREPARED_FINGERPRINT_MISMATCH')
    return st.result

def make_delta(old,new):
    a={x.memory_id:x for x in old.request.memories}; b={x.memory_id:x for x in new.request.memories}
    changed=tuple(b[k] for k in sorted(b) if k not in a or a[k]!=b[k]); removed=tuple(sorted(set(a)-set(b)))
    return PurposeGateDelta(changed,removed,old.request.current_goal!=new.request.current_goal,old.request.goal_purpose_tags!=new.request.goal_purpose_tags,old.request.goal_clarity!=new.request.goal_clarity,old.policy_fingerprint!=new.policy_fingerprint,_manifest_fp(old.request),_manifest_fp(new.request))
def plan_missing_only(old,new):
    d=make_delta(old,new); ids=[f'MEMORY:{x.memory_id}' for x in d.changed_memories]+[f'MEMORY:{x}' for x in d.removed_memory_ids]
    if d.goal_changed: ids.append('CURRENT_GOAL')
    if d.purpose_tags_changed: ids.append('GOAL_PURPOSE_TAGS')
    if d.goal_clarity_changed: ids.append('GOAL_CLARITY')
    if d.policy_changed: ids.append('PURPOSE_GATE_POLICY')
    meta=len(_canon((tuple(ids),d.from_manifest_fingerprint,d.to_manifest_fingerprint)))
    return MissingOnlyPlan(tuple(ids),meta,False)
