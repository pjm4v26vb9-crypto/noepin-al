"""NOEPIN AL 163 — Exact-Equivalent Asset Reference Merger — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-163
DCSR: DIRECT INTEGRATION / 直接統合.

Exact-safe asset reference merger evaluator. A merge candidate is produced only when payload,
import-settings, and behavior/state fingerprints are all known, integrity-verified, and exactly equal.
The evaluator only produces canonical/reference replacement plans; it never rewrites references,
deletes assets, mutates payload/import/state, or promotes reconstructed/cached state to authority.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json

class Decision(str, Enum): ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class EngineState(str, Enum):
    EXACT_EQUIVALENT_MERGE_CANDIDATE='EXACT_EQUIVALENT_MERGE_CANDIDATE'
    ORIGINAL_RETENTION_CANDIDATE='ORIGINAL_RETENTION_CANDIDATE'
    MIXED_MERGE_AND_ORIGINAL_CANDIDATE='MIXED_MERGE_AND_ORIGINAL_CANDIDATE'
    INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_REFERENCE_MERGE_CANDIDATE='CONTINUE_REFERENCE_MERGE_CANDIDATE'
    RETAIN_ORIGINAL_ASSETS_CANDIDATE='RETAIN_ORIGINAL_ASSETS_CANDIDATE'
    REVIEW_INPUT_CANDIDATE='REVIEW_INPUT_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; PAYLOAD_MISMATCH='PAYLOAD_MISMATCH'; IMPORT_SETTINGS_MISMATCH='IMPORT_SETTINGS_MISMATCH'; STATE_MISMATCH='STATE_MISMATCH'; UNKNOWN_FINGERPRINT='UNKNOWN_FINGERPRINT'; CORRUPT_INPUT='CORRUPT_INPUT'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'

@dataclass(frozen=True)
class AssetRecord:
    asset_id:str; payload_hash:str; import_settings_hash:str; state_hash:str; references:tuple[str,...]
    payload_known:bool; import_known:bool; state_known:bool; integrity_verified:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class CanonicalAssetCandidate:
    canonical_asset_id:str; member_asset_ids:tuple[str,...]; payload_hash:str; import_settings_hash:str; state_hash:str
@dataclass(frozen=True)
class ReferenceReplacementPlan:
    source_asset_id:str; canonical_asset_id:str; references:tuple[str,...]; reason:str
@dataclass(frozen=True)
class AssetMergeRequest:
    request_id:str; assets:tuple[AssetRecord,...]; binding:str; state_epoch:str
@dataclass(frozen=True)
class AssetMergeResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState; request_id:str
    canonical_assets:tuple[CanonicalAssetCandidate,...]; replacement_plans:tuple[ReferenceReplacementPlan,...]
    original_retained_asset_ids:tuple[str,...]; merge_group_count:int; merged_duplicate_asset_count:int; retained_original_count:int
    full_original_fallback_candidate:bool; reasons:tuple[str,...]; next_gate_candidate:bool
    canonical_reference_written:bool=False; reference_rewrite_executed:bool=False; source_asset_deleted:bool=False
    payload_mutated:bool=False; import_settings_mutated:bool=False; behavior_state_mutated:bool=False
    authoritative_state_created:bool=False; cached_state_promoted:bool=False; reconstructed_state_promoted:bool=False; partial_state_promoted:bool=False
    fallback_executed:bool=False; tool_invoked:bool=False; file_write_executed:bool=False; network_send_executed:bool=False
    dcsr_reconstruction_created_fact:bool=False; sender_authority_inherited:bool=False; sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False
    permission_granted:bool=False; approval_executed:bool=False; authority_granted:bool=False; stop_executed:bool=False; action_executed:bool=False
    plan_committed:bool=False; publish_executed:bool=False; external_write_performed:bool=False; world_truth_proven:bool=False
    domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedAssetMergeState:
    request:AssetMergeRequest; result:AssetMergeResult; assets_fingerprint:str; request_context_fingerprint:str
    result_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class AssetMergeDelta:
    assets_changed:bool; request_context_changed:bool; from_manifest_fingerprint:str; to_manifest_fingerprint:str
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
    p=sha256(b'ASSET163-PAYLOAD-A').hexdigest(); i=sha256(b'ASSET163-IMPORT-A').hexdigest(); s=sha256(b'ASSET163-STATE-A').hexdigest()
    p2=sha256(b'ASSET163-PAYLOAD-B').hexdigest(); i2=sha256(b'ASSET163-IMPORT-B').hexdigest(); s2=sha256(b'ASSET163-STATE-B').hexdigest()
    a1=AssetRecord('ASSET-163-A1',p,i,s,('REF-A','REF-B'),True,True,True,True,b,e)
    a2=AssetRecord('ASSET-163-A2',p,i,s,('REF-C',),True,True,True,True,b,e)
    a3=AssetRecord('ASSET-163-B1',p2,i2,s2,('REF-D',),True,True,True,True,b,e)
    return AssetMergeRequest('AMR-163-A',(a1,a2,a3),b,e)

def _invalid(reason,request_id=''):
    return AssetMergeResult(Decision.HOLD,NextAction.REVIEW_INPUT_CANDIDATE,Escalation.INVALID_CONFIGURATION,EngineState.INVALID,request_id,(),(),(),0,0,0,True,(reason,'RECONSTRUCTED_PARTIAL_CACHED_STATE_IS_NOT_AUTHORITATIVE_STATE','ORIGINAL_ASSETS_RETAINED'),False)

def _validate(q):
    if not q.request_id or not q.binding or not q.state_epoch: return 'EMPTY_REQUEST_CONTEXT'
    if not q.assets: return 'EMPTY_ASSETS'
    seen=set()
    for a in q.assets:
        if a.binding!=q.binding or a.state_epoch!=q.state_epoch: return 'ASSET_BINDING_MISMATCH'
        if not a.asset_id or a.asset_id in seen: return 'INVALID_OR_DUPLICATE_ASSET_ID'
        seen.add(a.asset_id)
        for name,v in (('PAYLOAD',a.payload_hash),('IMPORT',a.import_settings_hash),('STATE',a.state_hash)):
            if not v or not _is_hex64(v): return 'INVALID_'+name+'_HASH'
        if len(set(a.references))!=len(a.references): return 'DUPLICATE_REFERENCE_ID'
    return None

def evaluate(q):
    bad=_validate(q)
    if bad: return _invalid(bad,getattr(q,'request_id',''))
    common=(
        'THREE_FINGERPRINT_MATCH_IS_EQUIVALENCE_EVIDENCE_NOT_TRUTH',
        'CANONICAL_ASSET_CANDIDATE_IS_NOT_AUTHORITATIVE_STATE',
        'REFERENCE_REPLACEMENT_PLAN_IS_NOT_REFERENCE_REWRITE_EXECUTION',
        'RECONSTRUCTED_PARTIAL_CACHED_STATE_IS_NOT_AUTHORITATIVE_STATE',
        'FINAL_MISMATCH_REQUIRES_FULL_ORIGINAL_FALLBACK_CANDIDATE',
        'ORIGINAL_ASSETS_ARE_RETAINED',
        'NO_EXTERNAL_WRITE_PERMISSION_ACTION_OR_SUCCESS_EXECUTION',
    )
    usable=[]; retained=[]; reasons=[]
    for a in q.assets:
        if not a.integrity_verified:
            retained.append(a.asset_id); reasons.append('INTEGRITY_UNVERIFIED_RETAIN_ORIGINAL:'+a.asset_id); continue
        if not (a.payload_known and a.import_known and a.state_known):
            retained.append(a.asset_id); reasons.append('UNKNOWN_FINGERPRINT_RETAIN_ORIGINAL:'+a.asset_id); continue
        usable.append(a)
    groups={}
    for a in usable: groups.setdefault((a.payload_hash,a.import_settings_hash,a.state_hash),[]).append(a)
    cands=[]; plans=[]
    for key,members in sorted(groups.items()):
        members=sorted(members,key=lambda x:x.asset_id)
        if len(members)<2:
            retained.append(members[0].asset_id); continue
        canon=members[0]
        ids=tuple(x.asset_id for x in members)
        cands.append(CanonicalAssetCandidate(canon.asset_id,ids,*key))
        for src in members[1:]: plans.append(ReferenceReplacementPlan(src.asset_id,canon.asset_id,src.references,'EXACT_THREE_FINGERPRINT_MATCH_CANDIDATE'))
    retained=tuple(sorted(set(retained)))
    cands=tuple(sorted(cands,key=lambda x:x.canonical_asset_id)); plans=tuple(sorted(plans,key=lambda x:x.source_asset_id))
    merged=len(plans)
    if cands and retained:
        decision=Decision.ALLOW; action=NextAction.CONTINUE_REFERENCE_MERGE_CANDIDATE; state=EngineState.MIXED_MERGE_AND_ORIGINAL_CANDIDATE; esc=Escalation.NONE
    elif cands:
        decision=Decision.ALLOW; action=NextAction.CONTINUE_REFERENCE_MERGE_CANDIDATE; state=EngineState.EXACT_EQUIVALENT_MERGE_CANDIDATE; esc=Escalation.NONE
    else:
        decision=Decision.HOLD; action=NextAction.RETAIN_ORIGINAL_ASSETS_CANDIDATE; state=EngineState.ORIGINAL_RETENTION_CANDIDATE
        if any(x.startswith('UNKNOWN_FINGERPRINT') for x in reasons): esc=Escalation.UNKNOWN_FINGERPRINT
        elif any(x.startswith('INTEGRITY_UNVERIFIED') for x in reasons): esc=Escalation.CORRUPT_INPUT
        else: esc=Escalation.NONE
    return AssetMergeResult(decision,action,esc,state,q.request_id,cands,plans,retained,len(cands),merged,len(retained),True,tuple(common+tuple(sorted(reasons))),True)

def default_evaluation(): return evaluate(default_request())
def prepare_state(q,binding,state_epoch):
    if q.binding!=binding or q.state_epoch!=state_epoch: return PreparedAssetMergeState(q,_invalid('PREPARED_BINDING_MISMATCH',q.request_id),'0'*64,'0'*64,'0'*64,'0'*64,binding,state_epoch)
    r=evaluate(q); af=_fp(q.assets); cf=_fp((q.request_id,q.binding,q.state_epoch)); rf=_fp(r); integ=_fp((af,cf,rf,binding,state_epoch))
    return PreparedAssetMergeState(q,r,af,cf,rf,integ,binding,state_epoch)
def evaluate_prepared(st,*,integrity_validated,current_assets_fingerprint,current_request_context_fingerprint,current_result_fingerprint):
    if not integrity_validated: return _invalid('PREPARED_INTEGRITY_NOT_VALIDATED',st.request.request_id)
    if current_assets_fingerprint!=st.assets_fingerprint: return _invalid('PREPARED_ASSETS_FINGERPRINT_MISMATCH',st.request.request_id)
    if current_request_context_fingerprint!=st.request_context_fingerprint: return _invalid('PREPARED_CONTEXT_FINGERPRINT_MISMATCH',st.request.request_id)
    if current_result_fingerprint!=st.result_fingerprint: return _invalid('PREPARED_RESULT_FINGERPRINT_MISMATCH',st.request.request_id)
    if _fp((st.assets_fingerprint,st.request_context_fingerprint,st.result_fingerprint,st.binding,st.state_epoch))!=st.integrity_fingerprint: return _invalid('PREPARED_INTEGRITY_FINGERPRINT_MISMATCH',st.request.request_id)
    return st.result
def make_delta(a,b):
    ff=_fp((a.assets_fingerprint,a.request_context_fingerprint)); tf=_fp((b.assets_fingerprint,b.request_context_fingerprint))
    return AssetMergeDelta(a.assets_fingerprint!=b.assets_fingerprint,a.request_context_fingerprint!=b.request_context_fingerprint,ff,tf)
def plan_missing_only(a,b):
    d=make_delta(a,b); ids=[]
    if d.assets_changed: ids.append('ASSETS')
    if d.request_context_changed: ids.append('REQUEST_CONTEXT')
    return MissingOnlyPlan(tuple(ids),80+len(ids)*9,False)
