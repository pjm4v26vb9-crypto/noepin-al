"""NOEPIN AL 162 — Shared Correction Profile Dictionary — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-162
DCSR: DIRECT INTEGRATION / 直接統合.

Exact-safe shared profile registry evaluator. It shares a correction/configuration profile only when
compatibility fingerprint, critical attributes, use tag, and profile content are exact matches.
Unknown, corrupt, incompatible, or ambiguous cases remain individual. Shared / reconstructed / cached
state is never promoted to authoritative state, originals are never deleted, and no external mutation,
permission grant, deployment, action execution, or Action Success is performed.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json

class Decision(str, Enum):
    ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class EngineState(str, Enum):
    SHARED_PROFILE_CANDIDATE='SHARED_PROFILE_CANDIDATE'
    INDIVIDUAL_FALLBACK_CANDIDATE='INDIVIDUAL_FALLBACK_CANDIDATE'
    MIXED_SHARED_AND_INDIVIDUAL_CANDIDATE='MIXED_SHARED_AND_INDIVIDUAL_CANDIDATE'
    INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_SHARED_PROFILE_CANDIDATE='CONTINUE_SHARED_PROFILE_CANDIDATE'
    RETAIN_INDIVIDUAL_PROFILE_CANDIDATE='RETAIN_INDIVIDUAL_PROFILE_CANDIDATE'
    REVIEW_INPUT_CANDIDATE='REVIEW_INPUT_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; INCOMPATIBLE='INCOMPATIBLE'; CRITICAL_ATTRIBUTE_MISMATCH='CRITICAL_ATTRIBUTE_MISMATCH'; PROFILE_MISMATCH='PROFILE_MISMATCH'; UNKNOWN_COMPATIBILITY='UNKNOWN_COMPATIBILITY'; CORRUPT_INPUT='CORRUPT_INPUT'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'

@dataclass(frozen=True)
class ProfileField:
    key:str; value:str
@dataclass(frozen=True)
class TargetProfile:
    target_id:str
    compatibility_fingerprint:str
    profile:tuple[ProfileField,...]
    usage_tag:str
    critical_attributes:tuple[str,...]
    compatibility_known:bool
    integrity_verified:bool
    binding:str
    state_epoch:str
@dataclass(frozen=True)
class SharedProfile:
    profile_id:str
    compatibility_fingerprint:str
    profile_fingerprint:str
    usage_tag:str
    critical_attributes:tuple[str,...]
    profile:tuple[ProfileField,...]
    member_target_ids:tuple[str,...]
@dataclass(frozen=True)
class TargetReference:
    target_id:str; mode:str; profile_id:str|None; reason:str
@dataclass(frozen=True)
class SharedProfileRequest:
    request_id:str; targets:tuple[TargetProfile,...]; binding:str; state_epoch:str
@dataclass(frozen=True)
class SharedProfileResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState
    request_id:str; shared_profiles:tuple[SharedProfile,...]; target_references:tuple[TargetReference,...]
    shared_profile_count:int; shared_target_count:int; individual_target_count:int; duplicate_profiles_removed_candidate:int
    reconstruction_fallback_original_candidate:bool; reasons:tuple[str,...]; next_gate_candidate:bool
    profile_registry_written:bool=False; target_reference_written:bool=False; original_profile_deleted:bool=False
    source_profile_mutated:bool=False; profile_content_mutated:bool=False; authoritative_state_created:bool=False
    cached_state_promoted:bool=False; reconstructed_state_promoted:bool=False; partial_state_promoted:bool=False
    fallback_executed:bool=False; tool_invoked:bool=False; file_write_executed:bool=False; network_send_executed:bool=False
    dcsr_reconstruction_created_fact:bool=False; sender_authority_inherited:bool=False; sender_intent_inherited:bool=False
    sender_agreement_inherited:bool=False; permission_granted:bool=False; approval_executed:bool=False; authority_granted:bool=False
    stop_executed:bool=False; action_executed:bool=False; plan_committed:bool=False; publish_executed:bool=False
    external_write_performed:bool=False; world_truth_proven:bool=False; domain_authority_promoted:bool=False
    safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedSharedProfileState:
    request:SharedProfileRequest; result:SharedProfileResult; targets_fingerprint:str; request_context_fingerprint:str
    result_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class SharedProfileDelta:
    targets_changed:bool; request_context_changed:bool; from_manifest_fingerprint:str; to_manifest_fingerprint:str
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
def _is_hex64(s):
    if len(s)!=64: return False
    try: int(s,16); return True
    except ValueError: return False

def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    p=(ProfileField('gain','1.000'),ProfileField('offset','0.125'),ProfileField('mode','SAFE'))
    p3=(ProfileField('gain','0.875'),ProfileField('offset','0.000'),ProfileField('mode','SAFE'))
    fp_a=sha256(b'COMPAT-162-A').hexdigest(); fp_b=sha256(b'COMPAT-162-B').hexdigest()
    t1=TargetProfile('TARGET-162-A1',fp_a,p,'AVATAR_CORRECTION',('SKELETON-V1','UNIT-METER'),True,True,b,e)
    t2=TargetProfile('TARGET-162-A2',fp_a,p,'AVATAR_CORRECTION',('SKELETON-V1','UNIT-METER'),True,True,b,e)
    t3=TargetProfile('TARGET-162-B1',fp_b,p3,'ASSET_CORRECTION',('MESH-V2','UNIT-METER'),True,True,b,e)
    return SharedProfileRequest('SPR-162-A',(t1,t2,t3),b,e)

def _invalid(reason, request_id=''):
    return SharedProfileResult(Decision.HOLD,NextAction.REVIEW_INPUT_CANDIDATE,Escalation.INVALID_CONFIGURATION,EngineState.INVALID,request_id,(),(),0,0,0,0,True,(reason,'NO_SHARED_OR_RECONSTRUCTED_STATE_AUTHORITY','ORIGINAL_DATA_RETAINED'),False)

def _validate(q):
    if not q.request_id or not q.binding or not q.state_epoch: return 'EMPTY_REQUEST_CONTEXT'
    if not q.targets: return 'EMPTY_TARGETS'
    seen=set()
    for t in q.targets:
        if t.binding!=q.binding or t.state_epoch!=q.state_epoch: return 'TARGET_BINDING_MISMATCH'
        if not t.target_id or t.target_id in seen: return 'INVALID_OR_DUPLICATE_TARGET_ID'
        seen.add(t.target_id)
        if not t.usage_tag: return 'EMPTY_USAGE_TAG'
        if not t.compatibility_fingerprint or not _is_hex64(t.compatibility_fingerprint): return 'INVALID_COMPATIBILITY_FINGERPRINT'
        if not t.profile: return 'EMPTY_PROFILE'
        keys=[]
        for f in t.profile:
            if not f.key: return 'EMPTY_PROFILE_KEY'
            keys.append(f.key)
        if len(set(keys))!=len(keys): return 'DUPLICATE_PROFILE_KEY'
        if not t.critical_attributes: return 'EMPTY_CRITICAL_ATTRIBUTES'
    return None

def _profile_fp(t): return _fp(t.profile)

def evaluate(q):
    bad=_validate(q)
    if bad: return _invalid(bad,getattr(q,'request_id',''))
    common=(
        'FINGERPRINT_MATCH_IS_COMPATIBILITY_EVIDENCE_NOT_TRUTH',
        'SHARED_PROFILE_REFERENCE_IS_COMPRESSION_CANDIDATE_NOT_AUTHORITATIVE_STATE',
        'RECONSTRUCTED_PARTIAL_CACHED_STATE_IS_NOT_AUTHORITATIVE_STATE',
        'FINAL_MISMATCH_REQUIRES_FULL_ORIGINAL_FALLBACK_CANDIDATE',
        'ORIGINAL_PROFILE_IS_RETAINED',
        'NO_EXTERNAL_WRITE_PERMISSION_ACTION_OR_SUCCESS_EXECUTION',
    )
    refs=[]; shared=[]; reasons=[]
    # Candidate groups only from known + integrity-verified records.
    usable=[t for t in q.targets if t.compatibility_known and t.integrity_verified]
    blocked=[t for t in q.targets if t not in usable]
    for t in blocked:
        why='UNKNOWN_COMPATIBILITY_INDIVIDUAL' if not t.compatibility_known else 'INTEGRITY_UNVERIFIED_INDIVIDUAL'
        refs.append(TargetReference(t.target_id,'INDIVIDUAL',None,why)); reasons.append(why+':'+t.target_id)

    by_fp={}
    for t in usable: by_fp.setdefault(t.compatibility_fingerprint,[]).append(t)
    for compat_fp,members in sorted(by_fp.items()):
        crit_sigs={m.critical_attributes for m in members}
        if len(crit_sigs)>1:
            for m in members: refs.append(TargetReference(m.target_id,'INDIVIDUAL',None,'CRITICAL_ATTRIBUTE_MISMATCH'))
            reasons.append('CRITICAL_ATTRIBUTE_MISMATCH:'+compat_fp)
            continue
        by_tag={}
        for m in members: by_tag.setdefault(m.usage_tag,[]).append(m)
        for tag,tag_members in sorted(by_tag.items()):
            by_profile={}
            for m in tag_members: by_profile.setdefault(_profile_fp(m),[]).append(m)
            for pfp,p_members in sorted(by_profile.items()):
                if len(p_members)>=2:
                    first=p_members[0]
                    member_ids=tuple(sorted(x.target_id for x in p_members))
                    pid='SP-'+sha256((compat_fp+'|'+tag+'|'+pfp+'|'+'|'.join(first.critical_attributes)).encode()).hexdigest()[:16].upper()
                    sp=SharedProfile(pid,compat_fp,pfp,tag,first.critical_attributes,first.profile,member_ids)
                    shared.append(sp)
                    for m in p_members: refs.append(TargetReference(m.target_id,'SHARED',pid,'EXACT_MATCH_SHARED_CANDIDATE'))
                else:
                    m=p_members[0]; refs.append(TargetReference(m.target_id,'INDIVIDUAL',None,'NO_EQUIVALENT_PROFILE_PEER'))
            if len(by_profile)>1: reasons.append('PROFILE_CONTENT_MISMATCH_SPLIT:'+compat_fp+':'+tag)
        if len(by_tag)>1: reasons.append('USAGE_TAG_MISMATCH_SPLIT:'+compat_fp)

    refs=tuple(sorted(refs,key=lambda r:r.target_id)); shared=tuple(sorted(shared,key=lambda s:s.profile_id))
    shared_targets=sum(len(s.member_target_ids) for s in shared); individual=len(q.targets)-shared_targets
    removed=sum(max(0,len(s.member_target_ids)-1) for s in shared)
    if shared and individual:
        state=EngineState.MIXED_SHARED_AND_INDIVIDUAL_CANDIDATE; action=NextAction.CONTINUE_SHARED_PROFILE_CANDIDATE; decision=Decision.ALLOW; esc=Escalation.NONE
    elif shared:
        state=EngineState.SHARED_PROFILE_CANDIDATE; action=NextAction.CONTINUE_SHARED_PROFILE_CANDIDATE; decision=Decision.ALLOW; esc=Escalation.NONE
    else:
        state=EngineState.INDIVIDUAL_FALLBACK_CANDIDATE; action=NextAction.RETAIN_INDIVIDUAL_PROFILE_CANDIDATE; decision=Decision.HOLD
        if blocked: esc=Escalation.UNKNOWN_COMPATIBILITY if any(not t.compatibility_known for t in blocked) else Escalation.CORRUPT_INPUT
        elif any('CRITICAL_ATTRIBUTE_MISMATCH' in x for x in reasons): esc=Escalation.CRITICAL_ATTRIBUTE_MISMATCH
        elif any('PROFILE_CONTENT_MISMATCH' in x for x in reasons): esc=Escalation.PROFILE_MISMATCH
        else: esc=Escalation.INCOMPATIBLE
    return SharedProfileResult(decision,action,esc,state,q.request_id,shared,refs,len(shared),shared_targets,individual,removed,individual>0,tuple(reasons)+common,True)

def default_evaluation(): return evaluate(default_request())

def prepare_state(q,binding,state_epoch):
    if binding!=q.binding or state_epoch!=q.state_epoch: raise ValueError('PREPARED_BINDING_MISMATCH')
    r=evaluate(q); tf=_fp(q.targets); cf=_fp((q.request_id,q.binding,q.state_epoch)); rf=_fp(r)
    integ=_fp((tf,cf,rf,binding,state_epoch))
    return PreparedSharedProfileState(q,r,tf,cf,rf,integ,binding,state_epoch)

def evaluate_prepared(st,*,integrity_validated,current_targets_fingerprint,current_request_context_fingerprint,current_result_fingerprint):
    if not integrity_validated: return _invalid('PREPARED_INTEGRITY_NOT_VALIDATED',st.request.request_id)
    expected=_fp((st.targets_fingerprint,st.request_context_fingerprint,st.result_fingerprint,st.binding,st.state_epoch))
    if expected!=st.integrity_fingerprint: return _invalid('PREPARED_INTEGRITY_FINGERPRINT_MISMATCH',st.request.request_id)
    if current_targets_fingerprint!=st.targets_fingerprint: return _invalid('PREPARED_TARGETS_STALE',st.request.request_id)
    if current_request_context_fingerprint!=st.request_context_fingerprint: return _invalid('PREPARED_CONTEXT_STALE',st.request.request_id)
    if current_result_fingerprint!=st.result_fingerprint: return _invalid('PREPARED_RESULT_STALE',st.request.request_id)
    return st.result

def make_delta(a,b):
    ff=_fp((a.targets_fingerprint,a.request_context_fingerprint)); tf=_fp((b.targets_fingerprint,b.request_context_fingerprint))
    return SharedProfileDelta(a.targets_fingerprint!=b.targets_fingerprint,a.request_context_fingerprint!=b.request_context_fingerprint,ff,tf)

def plan_missing_only(a,b):
    d=make_delta(a,b); ids=[]
    if d.targets_changed: ids.append('TARGETS')
    if d.request_context_changed: ids.append('REQUEST_CONTEXT')
    return MissingOnlyPlan(tuple(ids),80+len(ids)*9,False)
