"""NOEPIN AL 143 — Purpose-Limitation Flow Checker — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-143
DCSR: AUXILIARY INTEGRATION / 補助統合.

Checks whether a requested use remains inside the purposes attached to data, with explicit
consent/policy exceptions represented only as evidence. The checker does not execute data use,
grant permission, mutate policy, solicit consent, or replace authentication, encryption, Policy,
or DLP. Purpose Match != Permission Grant. HUMAN_APPROVAL Candidate != Approval Execution.
DCSR reconstruction does not create consent, Truth, Authority, Permission, Safety Proof, Action,
or Action Success.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json

class Decision(str, Enum):
    ALLOW='ALLOW'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'; DENY='DENY'
class EngineState(str, Enum):
    USE_ALLOWED_CANDIDATE='USE_ALLOWED_CANDIDATE'; CONSENT_REQUIRED_CANDIDATE='CONSENT_REQUIRED_CANDIDATE'; PURPOSE_BLOCKED_CANDIDATE='PURPOSE_BLOCKED_CANDIDATE'; INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_USE_CANDIDATE='CONTINUE_USE_CANDIDATE'; REQUEST_CONSENT_CANDIDATE='REQUEST_CONSENT_CANDIDATE'; BLOCK_USE_CANDIDATE='BLOCK_USE_CANDIDATE'; REVIEW_CANDIDATE='REVIEW_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; PURPOSE_MISMATCH='PURPOSE_MISMATCH'; CONSENT_REQUIRED='CONSENT_REQUIRED'; PURPOSE_UNKNOWN='PURPOSE_UNKNOWN'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'
class Sensitivity(str, Enum):
    NON_SENSITIVE='NON_SENSITIVE'; SENSITIVE='SENSITIVE'; SECRET='SECRET'; PERSONAL='PERSONAL'
class MatchKind(str, Enum):
    EXACT='EXACT'; INCLUDED='INCLUDED'; CONSENT_EXCEPTION='CONSENT_EXCEPTION'; POLICY_EXCEPTION='POLICY_EXCEPTION'; MISMATCH='MISMATCH'; UNKNOWN='UNKNOWN'

@dataclass(frozen=True)
class DataItem:
    item_id:str; allowed_purposes:tuple[str,...]; sensitivity:Sensitivity; provenance_ids:tuple[str,...]; binding:str; state_epoch:str

@dataclass(frozen=True)
class ConsentPolicy:
    explicit_consent_purposes:tuple[str,...]=(); policy_exception_purposes:tuple[str,...]=(); reconsent_available:bool=False; consent_known:bool=True

@dataclass(frozen=True)
class PurposeRequest:
    request_id:str; data_items:tuple[DataItem,...]; current_purpose:str; requested_use:str; consent_policy:ConsentPolicy; binding:str; state_epoch:str

@dataclass(frozen=True)
class UseFinding:
    item_id:str; match_kind:MatchKind; allowed:bool; blocked:bool; required_consent:bool; matched_purpose:str; reasons:tuple[str,...]

@dataclass(frozen=True)
class PurposeResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState
    allowed_item_ids:tuple[str,...]; blocked_item_ids:tuple[str,...]; purpose_mismatches:tuple[str,...]; required_consent_item_ids:tuple[str,...]
    findings:tuple[UseFinding,...]; reasons:tuple[str,...]; next_gate_candidate:bool
    purpose_match_promoted_to_permission:bool=False; consent_evidence_promoted_to_approval:bool=False
    policy_exception_promoted_to_authority:bool=False; data_use_executed:bool=False; consent_requested_externally:bool=False
    external_send_executed:bool=False; tool_invoked:bool=False; memory_write_performed:bool=False
    label_write_performed:bool=False; policy_modified:bool=False; dlp_replaced:bool=False
    authentication_replaced:bool=False; encryption_replaced:bool=False; dcsr_reconstruction_created_consent:bool=False
    sender_authority_inherited:bool=False; sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False
    permission_granted:bool=False; approval_executed:bool=False; authority_granted:bool=False; stop_executed:bool=False
    action_executed:bool=False; plan_committed:bool=False; publish_executed:bool=False; external_write_performed:bool=False
    world_truth_proven:bool=False; domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False

@dataclass(frozen=True)
class PreparedPurposeState:
    request:PurposeRequest; result:PurposeResult; data_fingerprint:str; purpose_fingerprint:str; consent_policy_fingerprint:str
    outcome_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str

@dataclass(frozen=True)
class PurposeDelta:
    changed_data_items:tuple[DataItem,...]; removed_data_item_ids:tuple[str,...]; purpose_changed:bool; consent_policy_changed:bool
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
def _norm_purpose(s): return ':'.join(x.strip().lower() for x in s.strip().split(':') if x.strip())
def _purpose_matches(tag,current):
    tag=_norm_purpose(tag); current=_norm_purpose(current)
    if not tag or not current: return False, MatchKind.UNKNOWN
    if tag==current: return True,MatchKind.EXACT
    if tag.endswith(':*') and current.startswith(tag[:-1]): return True,MatchKind.INCLUDED
    if current.startswith(tag+':'): return True,MatchKind.INCLUDED
    return False,MatchKind.MISMATCH

def _manifest_fp(req): return _fp((req.data_items,req.current_purpose,req.requested_use,req.consent_policy,req.binding,req.state_epoch))

def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    d=DataItem('DATA-143-A',('care:medication',),Sensitivity.SENSITIVE,('SRC-143-A',),b,e)
    c=ConsentPolicy((),(),False,True)
    return PurposeRequest('REQ-143',(d,),'care:medication','summarize-for-care-team',c,b,e)

def _invalid(reason):
    return PurposeResult(Decision.HOLD,NextAction.REVIEW_CANDIDATE,Escalation.INVALID_CONFIGURATION,EngineState.INVALID,(),(),(),(),(),(reason,'NO_DATA_USE_EXECUTION','NO_PERMISSION_GRANT'),False)

def _validate(req):
    if not req.request_id or not req.binding or not req.state_epoch: return 'EMPTY_REQUEST_CONTEXT'
    if not _norm_purpose(req.current_purpose): return 'EMPTY_CURRENT_PURPOSE'
    if not req.requested_use.strip(): return 'EMPTY_REQUESTED_USE'
    ids=set()
    for d in req.data_items:
        if not d.item_id or d.item_id in ids: return 'INVALID_DATA_ITEM_ID'
        ids.add(d.item_id)
        if d.binding!=req.binding or d.state_epoch!=req.state_epoch: return 'DATA_STATE_BINDING_MISMATCH'
        if len(set(d.allowed_purposes))!=len(d.allowed_purposes): return 'DUPLICATE_PURPOSE_TAG'
        if any(not _norm_purpose(p) for p in d.allowed_purposes): return 'INVALID_PURPOSE_TAG'
        if len(set(d.provenance_ids))!=len(d.provenance_ids) or any(not p for p in d.provenance_ids): return 'INVALID_PROVENANCE'
    cp=req.consent_policy
    if len(set(cp.explicit_consent_purposes))!=len(cp.explicit_consent_purposes): return 'DUPLICATE_CONSENT_PURPOSE'
    if len(set(cp.policy_exception_purposes))!=len(cp.policy_exception_purposes): return 'DUPLICATE_POLICY_EXCEPTION'
    if any(not _norm_purpose(p) for p in cp.explicit_consent_purposes+cp.policy_exception_purposes): return 'INVALID_EXCEPTION_PURPOSE'
    return None

def _matches_any(tags,current):
    best=MatchKind.MISMATCH
    for tag in tags:
        ok,kind=_purpose_matches(tag,current)
        if ok: return True,kind,_norm_purpose(tag)
        if kind==MatchKind.UNKNOWN: best=MatchKind.UNKNOWN
    return False,best,''

def evaluate(req):
    err=_validate(req)
    if err: return _invalid(err)
    cp=req.consent_policy; current=_norm_purpose(req.current_purpose)
    consent_ok,_,consent_tag=_matches_any(cp.explicit_consent_purposes,current)
    policy_ok,_,policy_tag=_matches_any(cp.policy_exception_purposes,current)
    findings=[]; allowed=[]; blocked=[]; mismatches=[]; consent_needed=[]
    for d in sorted(req.data_items,key=lambda x:x.item_id):
        ok,kind,tag=_matches_any(d.allowed_purposes,current)
        reasons=[]; req_consent=False
        if ok:
            reasons.extend(('PURPOSE_WITHIN_ORIGINAL_SCOPE','PURPOSE_MATCH_IS_NOT_PERMISSION_GRANT'))
            f=UseFinding(d.item_id,kind,True,False,False,tag,tuple(reasons)); allowed.append(d.item_id)
        elif consent_ok and cp.consent_known:
            reasons.extend(('EXPLICIT_CONSENT_EVIDENCE_COVERS_CURRENT_PURPOSE','CONSENT_EVIDENCE_IS_NOT_APPROVAL_EXECUTION'))
            f=UseFinding(d.item_id,MatchKind.CONSENT_EXCEPTION,True,False,False,consent_tag,tuple(reasons)); allowed.append(d.item_id)
        elif policy_ok:
            reasons.extend(('POLICY_EXCEPTION_EVIDENCE_COVERS_CURRENT_PURPOSE','POLICY_EVIDENCE_IS_NOT_DOMAIN_AUTHORITY'))
            f=UseFinding(d.item_id,MatchKind.POLICY_EXCEPTION,True,False,False,policy_tag,tuple(reasons)); allowed.append(d.item_id)
        else:
            mismatches.append(d.item_id)
            sensitive=d.sensitivity!=Sensitivity.NON_SENSITIVE
            if sensitive and not cp.consent_known:
                reasons.extend(('SENSITIVE_DATA_CONSENT_UNKNOWN','FAIL_SAFE_NO_USE'))
                f=UseFinding(d.item_id,MatchKind.UNKNOWN,False,True,False,'',tuple(reasons)); blocked.append(d.item_id)
            elif cp.reconsent_available:
                req_consent=True; reasons.extend(('PURPOSE_MISMATCH','RECONSENT_AVAILABLE','HUMAN_APPROVAL_CANDIDATE_ONLY'))
                f=UseFinding(d.item_id,MatchKind.MISMATCH,False,True,True,'',tuple(reasons)); blocked.append(d.item_id); consent_needed.append(d.item_id)
            else:
                reasons.extend(('PURPOSE_MISMATCH','PURPOSE_LIMITATION_BLOCK_CANDIDATE','NO_USE_EXECUTION'))
                f=UseFinding(d.item_id,MatchKind.MISMATCH,False,True,False,'',tuple(reasons)); blocked.append(d.item_id)
        findings.append(f)
    if any(f.match_kind==MatchKind.UNKNOWN for f in findings):
        decision=Decision.HOLD; action=NextAction.REVIEW_CANDIDATE; esc=Escalation.PURPOSE_UNKNOWN; state=EngineState.PURPOSE_BLOCKED_CANDIDATE
    elif consent_needed:
        decision=Decision.HUMAN_APPROVAL; action=NextAction.REQUEST_CONSENT_CANDIDATE; esc=Escalation.CONSENT_REQUIRED; state=EngineState.CONSENT_REQUIRED_CANDIDATE
    elif blocked:
        decision=Decision.DENY; action=NextAction.BLOCK_USE_CANDIDATE; esc=Escalation.PURPOSE_MISMATCH; state=EngineState.PURPOSE_BLOCKED_CANDIDATE
    else:
        decision=Decision.ALLOW; action=NextAction.CONTINUE_USE_CANDIDATE; esc=Escalation.NONE; state=EngineState.USE_ALLOWED_CANDIDATE
    reasons=('PURE_ANALYSIS_ONLY','NO_DATA_USE_EXECUTION','NO_PERMISSION_GRANT','PURPOSE_MATCH_NOT_PERMISSION','DCSR_AUXILIARY_ONLY','NOT_AUTHENTICATION_OR_ENCRYPTION_OR_POLICY_OR_DLP')
    return PurposeResult(decision,action,esc,state,tuple(allowed),tuple(blocked),tuple(mismatches),tuple(consent_needed),tuple(findings),reasons,True)

def default_evaluation(): return evaluate(default_request())

def prepare_state(req,binding,state_epoch):
    r=evaluate(req) if binding==req.binding and state_epoch==req.state_epoch else _invalid('PREPARE_CONTEXT_MISMATCH')
    data_fp=_fp(req.data_items); purpose_fp=_fp((req.current_purpose,req.requested_use)); cp_fp=_fp(req.consent_policy); outcome_fp=_fp(r)
    integrity=_fp((data_fp,purpose_fp,cp_fp,outcome_fp,binding,state_epoch))
    return PreparedPurposeState(req,r,data_fp,purpose_fp,cp_fp,outcome_fp,integrity,binding,state_epoch)

def validate_prepared_integrity(st):
    return st.integrity_fingerprint==_fp((st.data_fingerprint,st.purpose_fingerprint,st.consent_policy_fingerprint,st.outcome_fingerprint,st.binding,st.state_epoch)) and st.outcome_fingerprint==_fp(st.result)

def evaluate_prepared(st,*,integrity_validated,current_data_fingerprint,current_purpose_fingerprint,current_consent_policy_fingerprint,current_outcome_fingerprint):
    if not integrity_validated or not validate_prepared_integrity(st): return _invalid('PREPARED_INTEGRITY_NOT_VALIDATED')
    if st.binding!=st.request.binding or st.state_epoch!=st.request.state_epoch: return _invalid('PREPARED_CONTEXT_MISMATCH')
    if current_data_fingerprint!=st.data_fingerprint: return _invalid('STALE_DATA_STATE')
    if current_purpose_fingerprint!=st.purpose_fingerprint: return _invalid('STALE_PURPOSE_STATE')
    if current_consent_policy_fingerprint!=st.consent_policy_fingerprint: return _invalid('STALE_CONSENT_POLICY_STATE')
    if current_outcome_fingerprint!=st.outcome_fingerprint: return _invalid('STALE_OUTCOME_STATE')
    return st.result

def _index(xs): return {x.item_id:x for x in xs}
def make_delta(old,new):
    oi=_index(old.request.data_items); ni=_index(new.request.data_items)
    changed=tuple(ni[k] for k in sorted(ni) if k not in oi or _fp(ni[k])!=_fp(oi[k])); removed=tuple(sorted(set(oi)-set(ni)))
    return PurposeDelta(changed,removed,old.purpose_fingerprint!=new.purpose_fingerprint,old.consent_policy_fingerprint!=new.consent_policy_fingerprint,_manifest_fp(old.request),_manifest_fp(new.request))

def plan_missing_only(old,new):
    d=make_delta(old,new); ids=[f'DATA:{x.item_id}' for x in d.changed_data_items]+[f'DATA:{x}' for x in d.removed_data_item_ids]
    if d.purpose_changed: ids.append('PURPOSE_CONTEXT')
    if d.consent_policy_changed: ids.append('CONSENT_POLICY')
    meta=len(_canon((tuple(ids),d.from_manifest_fingerprint,d.to_manifest_fingerprint)))
    return MissingOnlyPlan(tuple(ids),meta,False)
