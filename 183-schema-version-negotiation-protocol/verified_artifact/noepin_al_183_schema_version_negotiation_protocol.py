"""NOEPIN AL 183 — Schema-Version Negotiation Protocol — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-183
DCSR: DIRECT INTEGRATION / 直接統合.

Pure, deterministic, side-effect-free runtime compatibility handshake. Local and
remote components exchange explicitly supported MAJOR.MINOR schema versions. A
version is negotiated only when it is explicitly present on both sides and the
Compatibility Requirement is satisfied. Unsupported, malformed, schema-mismatched,
or fingerprint-mismatched state never causes optimistic connection. DCSR can reuse
an integrity-verified prepared negotiation only when current manifest/schema
fingerprints still match; otherwise the protocol returns HOLD / full-fallback
candidate. A negotiated version is a next-gate candidate only: it is not Truth,
Permission, Approval, connection execution, Tool invocation, Action execution,
Action success, or universal Safety proof.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
from hashlib import sha256
import json, re

class Decision(str, Enum):
    ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class EngineState(str, Enum):
    NEGOTIATED_VERSION_CANDIDATE='NEGOTIATED_VERSION_CANDIDATE'
    NO_COMMON_VERSION_CANDIDATE='NO_COMMON_VERSION_CANDIDATE'
    SCHEMA_COMPATIBILITY_HOLD_CANDIDATE='SCHEMA_COMPATIBILITY_HOLD_CANDIDATE'
    INVALID_VERSION_MANIFEST='INVALID_VERSION_MANIFEST'
    PREPARED_STATE_STALE='PREPARED_STATE_STALE'
class NextAction(str, Enum):
    CONTINUE_CONNECTION_VALIDATION_CANDIDATE='CONTINUE_CONNECTION_VALIDATION_CANDIDATE'
    REQUEST_COMPATIBLE_VERSION_CANDIDATE='REQUEST_COMPATIBLE_VERSION_CANDIDATE'
    FULL_SCHEMA_FALLBACK_CANDIDATE='FULL_SCHEMA_FALLBACK_CANDIDATE'
    RETAIN_NO_CONNECTION_CANDIDATE='RETAIN_NO_CONNECTION_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'
    INVALID_VERSION_FORMAT='INVALID_VERSION_FORMAT'
    EMPTY_SUPPORTED_VERSIONS='EMPTY_SUPPORTED_VERSIONS'
    NO_COMMON_VERSION='NO_COMMON_VERSION'
    SCHEMA_MISMATCH='SCHEMA_MISMATCH'
    FINGERPRINT_MISMATCH='FINGERPRINT_MISMATCH'
    PREPARED_STATE_STALE='PREPARED_STATE_STALE'

_VERSION_RE=re.compile(r'^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$')
_WS=re.compile(r'\s+')

def _norm(v): return _WS.sub(' ',str(v).strip())
def _obj(v):
    if isinstance(v,Enum): return v.value
    if is_dataclass(v): return {f.name:_obj(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v,dict): return {str(k):_obj(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(tuple,list,set,frozenset)):
        seq=[_obj(x) for x in v]
        return sorted(seq,key=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')))
    return v

def _canon(v): return json.dumps(_obj(v),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def _fp(v): return sha256(_canon(v)).hexdigest()

@dataclass(frozen=True, order=True)
class Version:
    major:int; minor:int
    def __str__(self): return f'{self.major}.{self.minor}'

@dataclass(frozen=True)
class CompatibilityRequirement:
    local_schema_id:str; remote_schema_id:str
    local_schema_fingerprint:str; remote_schema_fingerprint:str
    known_compatible_fingerprint_pairs:tuple[tuple[str,str],...]=()
    minimum_version:Version|None=None

@dataclass(frozen=True)
class VersionManifest:
    component_id:str; supported_versions:tuple[Version,...]
    schema_id:str; schema_fingerprint:str; manifest_epoch:str

@dataclass(frozen=True)
class NegotiationRequest:
    negotiation_id:str; local:VersionManifest; remote:VersionManifest
    requirement:CompatibilityRequirement

@dataclass(frozen=True)
class NegotiationResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState
    negotiation_id:str; negotiated_version:Version|None; common_versions:tuple[Version,...]
    schema_id_match:bool; schema_fingerprint_compatible:bool; compatibility_requirement_satisfied:bool
    local_manifest_fingerprint:str; remote_manifest_fingerprint:str; requirement_fingerprint:str
    negotiation_fingerprint:str; next_gate_candidate:bool; full_fallback_candidate:bool; reasons:tuple[str,...]
    negotiated_version_promoted_to_truth:bool=False; compatibility_promoted_to_safety_proof:bool=False
    connection_established:bool=False; connection_executed:bool=False; protocol_session_committed:bool=False
    permission_granted:bool=False; permit_issued:bool=False; approval_executed:bool=False
    human_approval_executed:bool=False; tool_invoked:bool=False; action_executed:bool=False
    action_success:bool=False; stop_executed:bool=False; file_write_executed:bool=False
    network_send_executed:bool=False; external_write_performed:bool=False; authoritative_state_created:bool=False
    cached_state_promoted:bool=False; reconstructed_state_promoted:bool=False; partial_state_promoted:bool=False
    dcsr_selected_unadvertised_version:bool=False; dcsr_bypassed_schema_requirement:bool=False
    dcsr_bypassed_fingerprint_requirement:bool=False; dcsr_created_compatibility_fact:bool=False
    sender_authority_inherited:bool=False; sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False
    authority_granted:bool=False; world_truth_proven:bool=False; domain_authority_promoted:bool=False
    safety_proven:bool=False

@dataclass(frozen=True)
class PreparedNegotiationState:
    request:NegotiationRequest; result:NegotiationResult
    request_fingerprint:str; result_fingerprint:str; integrity_fingerprint:str
    local_manifest_fingerprint:str; remote_manifest_fingerprint:str; requirement_fingerprint:str

@dataclass(frozen=True)
class ManifestDelta:
    record_id:str; component_id:str; added_versions:tuple[Version,...]; removed_versions:tuple[Version,...]
    from_manifest_fingerprint:str; to_manifest_fingerprint:str; delta_fingerprint:str

@dataclass(frozen=True)
class MissingOnlyPlan:
    missing_or_changed_record_ids:tuple[str,...]; metadata_bytes_required:int; full_resend_required:bool


def parse_version(value)->Version:
    s=_norm(value)
    m=_VERSION_RE.fullmatch(s)
    if not m: raise ValueError('version must be strict non-negative MAJOR.MINOR')
    return Version(int(m.group(1)),int(m.group(2)))

def _version(v)->Version:
    if isinstance(v,Version):
        if v.major<0 or v.minor<0: raise ValueError('negative version component')
        return v
    return parse_version(v)

def normalize_versions(values)->tuple[Version,...]:
    if values is None: raise ValueError('supported versions required')
    vals=tuple(values)
    if not vals: raise ValueError('supported versions must not be empty')
    return tuple(sorted({_version(v) for v in vals}))

def build_manifest(component_id,supported_versions,schema_id,schema_fingerprint,manifest_epoch='EPOCH-1'):
    c=_norm(component_id); sid=_norm(schema_id); sf=_norm(schema_fingerprint); e=_norm(manifest_epoch)
    if not c or not sid or not sf or not e: raise ValueError('component/schema/fingerprint/epoch required')
    return VersionManifest(c,normalize_versions(supported_versions),sid,sf,e)

def build_requirement(local_schema_id,remote_schema_id,local_schema_fingerprint,remote_schema_fingerprint,
                      known_compatible_fingerprint_pairs=(),minimum_version=None):
    lsid=_norm(local_schema_id); rsid=_norm(remote_schema_id); lf=_norm(local_schema_fingerprint); rf=_norm(remote_schema_fingerprint)
    if not lsid or not rsid or not lf or not rf: raise ValueError('schema requirement fields required')
    pairs=[]
    for a,b in known_compatible_fingerprint_pairs:
        aa=_norm(a); bb=_norm(b)
        if not aa or not bb: raise ValueError('known compatible fingerprint pair entries must be non-empty')
        pairs.append((aa,bb))
    pairs=tuple(sorted(set(pairs)))
    mv=None if minimum_version is None else _version(minimum_version)
    return CompatibilityRequirement(lsid,rsid,lf,rf,pairs,mv)

def make_request(negotiation_id='SVN-183-A',local_component_id='LOCAL-AL',local_supported_versions=('1.0','1.1','2.0'),
                 local_schema_id='NOEPIN-SCHEMA',local_schema_fingerprint='SCHEMA-FP-V1',local_manifest_epoch='EPOCH-1',
                 remote_component_id='REMOTE.AL',remote_supported_versions=('1.1','2.0'),remote_schema_id='NOEPIN-SCHEMA',
                 remote_schema_fingerprint='SCHEMA-FP-V1',remote_manifest_epoch='EPOCH-1',known_compatible_fingerprint_pairs=(),
                 minimum_version=None):
    nid=_norm(negotiation_id)
    if not nid: raise ValueError('negotiation id required')
    local=build_manifest(local_component_id,local_supported_versions,local_schema_id,local_schema_fingerprint,local_manifest_epoch)
    remote=build_manifest(remote_component_id,remote_supported_versions,remote_schema_id,remote_schema_fingerprint,remote_manifest_epoch)
    req=build_requirement(local_schema_id,remote_schema_id,local_schema_fingerprint,remote_schema_fingerprint,
                          known_compatible_fingerprint_pairs,minimum_version)
    return NegotiationRequest(nid,local,remote,req)

def _fingerprint_compatible(req:CompatibilityRequirement):
    if req.local_schema_fingerprint==req.remote_schema_fingerprint: return True
    pair=(req.local_schema_fingerprint,req.remote_schema_fingerprint)
    rev=(pair[1],pair[0])
    return pair in req.known_compatible_fingerprint_pairs or rev in req.known_compatible_fingerprint_pairs

def _result(q,decision,next_action,escalation,engine_state,negotiated,common,schema_match,fp_compatible,requirement_ok,
            next_gate,full_fallback,reasons):
    lf=_fp(q.local); rf=_fp(q.remote); qf=_fp(q.requirement)
    nf=_fp({'negotiation_id':q.negotiation_id,'local_manifest_fingerprint':lf,'remote_manifest_fingerprint':rf,
            'requirement_fingerprint':qf,'negotiated_version':negotiated,'common_versions':common,
            'decision':decision,'next_action':next_action})
    return NegotiationResult(decision,next_action,escalation,engine_state,q.negotiation_id,negotiated,common,
                             schema_match,fp_compatible,requirement_ok,lf,rf,qf,nf,next_gate,full_fallback,tuple(reasons))

def evaluate(q:NegotiationRequest)->NegotiationResult:
    # Re-validate forged dataclass instances rather than trusting construction-time invariants.
    try:
        local_versions=normalize_versions(q.local.supported_versions)
        remote_versions=normalize_versions(q.remote.supported_versions)
    except ValueError as e:
        return _result(q,Decision.DENY,NextAction.RETAIN_NO_CONNECTION_CANDIDATE,Escalation.INVALID_VERSION_FORMAT,EngineState.INVALID_VERSION_MANIFEST,none,(),False,False,False,False,False,(str(e),))
    schema_match=(q.local.schema_id==q.remote.schema_id==q.requirement.local_schema_id==q.requirement.remote_schema_id)
    if not schema_match:
        return _result(q,Decision.HOLD,NextAction.FULL_SCHEMA_FALLBACK_CANDIDATE,Escalation.SCHEMA_MISMATCH,EngineState.SCHEMA_COMPATIBILITY_HOLD_CANDIDATE,None,(),False,False,False,False,True,('schema mismatch; no connection candidate',))
    req_fp_matches=(q.local.schema_fingerprint==q.requirement.local_schema_fingerprint and q.remote.schema_fingerprint==q.requirement.remote_schema_fingerprint)
    fp_compatible=req_fp_matches and _fingerprint_compatible(q.requirement)
    if not fp_compatible:
        return _result(q,Decision.HOLD,NextAction.FULL_SCHEMA_FALLBACK_CANDIDATE,Escalation.FINGERPRINT_MISMATCH,EngineState.SCHEMA_COMPATIBILITY_HOLD_CANDIDATE,None,(),True,False,False,False,True,('schema fingerprint mismatch; explicit compatible pair not established',))
    common=tuple(sorted(set(local_versions).intersection(remote_versions)))
    if q.requirement.minimum_version is not None:
        common=tuple(v for v in common if v>=q.requirement.minimum_version)
    if not common:
        return _result(q,Decision.HOLD,NextAction.REQUEST_COMPATIBLE_VERSION_CANDIDATE,Escalation.NO_COMMON_VERSION,EngineState.NO_COMMON_VERSION_CANDIDATE,None,(),True,True,False,False,False,('no explicitly supported common version',))
    selected=common[-1]
    return _result(q,Decision.ALLOW,NextAction.CONTINUE_CONNECTION_VALIDATION_CANDIDATE,Escalation.NONE,EngineState.NEGOTIATED_VERSION_CANDIDATE,selected,common,True,True,True,True,False,('highest explicit common version selected as next-gate candidate',))

def prepare_state(q:NegotiationRequest)->PreparedNegotiationState:
    r=evaluate(q); qfp=_fp(q); rfp=_fp(r); lf=_fp(q.local); rf=_fp(q.remote); rq=_fp(q.requirement)
    integrity=_fp({'request_fingerprint':qfp,'result_fingerprint':rfp,'local_manifest_fingerprint':lf,'remote_manifest_fingerprint':rf,'requirement_fingerprint':rq})
    return PreparedNegotiationState(q,r,qfp,rfp,integrity,lf,rf,rq)

def evaluate_prepared(st:PreparedNegotiationState,*,integrity_validated,current_request_fingerprint,current_result_fingerprint,current_local_manifest_fingerprint,current_remote_manifest_fingerprint,current_requirement_fingerprint,current_request:NegotiationRequest):
    expected=_fp({'request_fingerprint':st.request_fingerprint,'result_fingerprint':st.result_fingerprint,'local_manifest_fingerprint':st.local_manifest_fingerprint,'remote_manifest_fingerprint':st.remote_manifest_fingerprint,'requirement_fingerprint':st.requirement_fingerprint})
    current=evaluate(current_request)
    stale=(not integrity_validated or st.integrity_fingerprint!=expected or current_request_fingerprint!=st.request_fingerprint or current_result_fingerprint!=st.result_fingerprint or current_local_manifest_fingerprint!=st.local_manifest_fingerprint or current_remote_manifest_fingerprint!=st.remote_manifest_fingerprint or current_requirement_fingerprint!=st.requirement_fingerprint or _fp(current_request)!=st.request_fingerprint)
    if stale:
        return replace(current,decision=Decision.HOLD,next_action=NextAction.FULL_SCHEMA_FALLBACK_CANDIDATE,escalation=Escalation.PREPARED_STATE_STALE,engine_state=EngineState.PREPARED_STATE_STALE,next_gate_candidate=False,full_fallback_candidate=True,reasons=('prepared integrity/current manifest fingerprint mismatch; full fallback candidate',))
    # Current Authority-side request is always evaluated. Cached result is evidence, not Authority.
    return current

def make_delta(old_manifest:VersionManifest,new_manifest:VersionManifest)->ManifestDelta:
    if old_manifest.component_id!=new_manifest.component_id: raise ValueError('component mismatch requires full resend')
    old=set(old_manifest.supported_versions); new=set(new_manifest.supported_versions)
    added=tuple(sorted(new-old)); removed=tuple(sorted(old-new)); ofp=_fp(old_manifest); nfp=_fp(new_manifest)
    return ManifestDelta('SUPPORTED_VERSIONS',new_manifest.component_id,added,removed,ofp,nfp,_fp({'component_id':new_manifest.component_id,'added':added,'removed':removed,'from':ofp,'to':nfp}))

def plan_missing_only(old_manifest:VersionManifest,new_manifest:VersionManifest)->MissingOnlyPlan:
    if old_manifest.component_id!=new_manifest.component_id: return MissingOnlyPlan(('FULL_VERSION_MANIFEST',),len(_canon(new_manifest)),True)
    schema_changed=(old_manifest.schema_id!=new_manifest.schema_id or old_manifest.schema_fingerprint!=new_manifest.schema_fingerprint)
    if schema_changed: return MissingOnlyPlan(('FULL_SCHEMA_MANIFEST',),len(_canon(new_manifest)),True)
    d=make_delta(old_manifest,new_manifest)
    ids=() if not d.added_versions and not d.removed_versions and old_manifest.manifest_epoch==new_manifest.manifest_epoch else ('SUPPORTED_VERSIONS',)
    return MissingOnlyPlan(ids,0 if not ids else len(_canon(d)),False)

def default_request(): return make_request()
def default_evaluation(): return evaluate(default_request())
