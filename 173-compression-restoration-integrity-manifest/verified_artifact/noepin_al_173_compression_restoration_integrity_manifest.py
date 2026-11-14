"""NOEPIN AL 173 — Compression-Restoration Integrity Manifest — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-173
DCSR: DIRECT INTEGRATION / 直接統合.

Deterministic, side-effect-free manifest builder/verifier for binding Base/Profile/Delta/Residual
bytes to one target ID, algorithm version, and metadata fingerprint. It computes SHA-256 for
each component and for the manifest payload itself, then verifies all bindings before returning a
candidate to continue restoration. Hash/target mismatch is DENY; algorithm-version mismatch is
HOLD; full match is ALLOW. No reconstruction, decompression, cache promotion, publication,
permission grant, fallback execution, external I/O, or authoritative-state promotion occurs.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str, Enum): ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class ComponentKind(str, Enum): BASE='BASE'; PROFILE='PROFILE'; DELTA='DELTA'; RESIDUAL='RESIDUAL'; SIDECAR='SIDECAR'
class EngineState(str, Enum):
    INTEGRITY_VERIFIED_CANDIDATE='INTEGRITY_VERIFIED_CANDIDATE'
    ORIGINAL_RETENTION_CANDIDATE='ORIGINAL_RETENTION_CANDIDATE'
    INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_RESTORATION_CANDIDATE='CONTINUE_RESTORATION_CANDIDATE'
    RETAIN_ORIGINAL_CANDIDATE='RETAIN_ORIGINAL_CANDIDATE'
    REVIEW_INPUT_CANDIDATE='REVIEW_INPUT_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'; INVALID_VALUE='INVALID_VALUE'
    MANIFEST_HASH_MISMATCH='MANIFEST_HASH_MISMATCH'; TARGET_MISMATCH='TARGET_MISMATCH'
    VERSION_INCOMPATIBLE='VERSION_INCOMPATIBLE'; COMPONENT_SET_MISMATCH='COMPONENT_SET_MISMATCH'
    COMPONENT_HASH_MISMATCH='COMPONENT_HASH_MISMATCH'; METADATA_MISMATCH='METADATA_MISMATCH'
    COMPONENT_UNAVAILABLE='COMPONENT_UNAVAILABLE'

@dataclass(frozen=True)
class ComponentBytes:
    component_id:str
    kind:ComponentKind
    payload:bytes
    required:bool=True
    available:bool=True

@dataclass(frozen=True)
class ManifestEntry:
    component_id:str
    kind:ComponentKind
    required:bool
    size_bytes:int
    sha256:str

@dataclass(frozen=True)
class CompressionRestorationManifest:
    schema:str
    target_id:str
    algorithm_version:str
    entries:tuple[ManifestEntry,...]
    metadata_fingerprint:str
    manifest_hash:str

@dataclass(frozen=True)
class IntegrityRequest:
    request_id:str
    target_id:str
    algorithm_version:str
    components:tuple[ComponentBytes,...]
    metadata:tuple[tuple[str,str],...]
    expected_manifest:CompressionRestorationManifest
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class IntegrityResult:
    decision:Decision
    next_action:NextAction
    escalation:Escalation
    engine_state:EngineState
    request_id:str
    target_match:bool
    version_match:bool
    manifest_hash_valid:bool
    metadata_match:bool
    component_set_match:bool
    component_hashes_match:bool
    required_components_available:bool
    checked_component_count:int
    matched_component_count:int
    manifest_hash:str
    next_gate_candidate:bool
    reasons:tuple[str,...]
    source_components_mutated:bool=False
    manifest_persisted:bool=False
    reconstruction_executed:bool=False
    decompression_executed:bool=False
    residual_applied:bool=False
    transfer_executed:bool=False
    plan_committed:bool=False
    authoritative_state_created:bool=False
    cached_state_promoted:bool=False
    reconstructed_state_promoted:bool=False
    partial_state_promoted:bool=False
    publish_executed:bool=False
    fallback_executed:bool=False
    original_deleted:bool=False
    tool_invoked:bool=False
    file_write_executed:bool=False
    network_send_executed:bool=False
    dcsr_reconstruction_created_fact:bool=False
    sender_authority_inherited:bool=False
    sender_intent_inherited:bool=False
    sender_agreement_inherited:bool=False
    permission_granted:bool=False
    approval_executed:bool=False
    authority_granted:bool=False
    stop_executed:bool=False
    action_executed:bool=False
    external_write_performed:bool=False
    world_truth_proven:bool=False
    domain_authority_promoted:bool=False
    safety_proven:bool=False
    action_success:bool=False

@dataclass(frozen=True)
class PreparedIntegrityState:
    request:IntegrityRequest
    result:IntegrityResult
    components_fingerprint:str
    manifest_fingerprint:str
    config_fingerprint:str
    result_fingerprint:str
    integrity_fingerprint:str
    binding:str
    state_epoch:str

@dataclass(frozen=True)
class IntegrityChange:
    components_changed:bool
    manifest_changed:bool
    config_changed:bool
    from_fingerprint:str
    to_fingerprint:str

@dataclass(frozen=True)
class MissingOnlyPlan:
    missing_or_changed_record_ids:tuple[str,...]
    metadata_bytes_required:int
    full_resend_required:bool


def _obj(v):
    if isinstance(v,Enum): return v.value
    if is_dataclass(v): return {f.name:_obj(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v,dict): return {str(k):_obj(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(tuple,list)): return [_obj(x) for x in v]
    if isinstance(v,bytes): return {'sha256':sha256(v).hexdigest(),'size':len(v)}
    if isinstance(v,float):
        if not math.isfinite(v): raise ValueError('non-finite float')
        return v
    return v

def _canon(v): return json.dumps(_obj(v),ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def _fp(v): return sha256(_canon(v)).hexdigest()
def _metadata_fp(metadata): return _fp(tuple(sorted((str(k),str(v)) for k,v in metadata)))
def _component_entry(c): return ManifestEntry(c.component_id,c.kind,c.required,len(c.payload),sha256(c.payload).hexdigest())

def _manifest_payload(schema,target_id,algorithm_version,entries,metadata_fingerprint):
    return {'schema':schema,'target_id':target_id,'algorithm_version':algorithm_version,'entries':entries,'metadata_fingerprint':metadata_fingerprint}

def build_manifest(target_id,algorithm_version,components,metadata):
    if not target_id or not algorithm_version: raise ValueError('target_id and algorithm_version are required')
    entries=tuple(sorted((_component_entry(c) for c in components),key=lambda e:(e.kind.value,e.component_id)))
    mfp=_metadata_fp(metadata); schema='NOEPIN_AL_COMPRESSION_RESTORATION_MANIFEST_V1'
    mh=_fp(_manifest_payload(schema,target_id,algorithm_version,entries,mfp))
    return CompressionRestorationManifest(schema,target_id,algorithm_version,entries,mfp,mh)

def _manifest_hash_valid(m):
    return m.manifest_hash==_fp(_manifest_payload(m.schema,m.target_id,m.algorithm_version,m.entries,m.metadata_fingerprint))

def _invalid(q,reason,esc,decision=Decision.HOLD):
    return IntegrityResult(decision,NextAction.REVIEW_INPUT_CANDIDATE,esc,EngineState.INVALID,getattr(q,'request_id',''),False,False,False,False,False,False,False,0,0,getattr(getattr(q,'expected_manifest',None),'manifest_hash',''),False,(reason,'NO_RESTORATION_EXECUTION','NO_AUTHORITATIVE_STATE_PROMOTION','DCSR_STATE_IS_NOT_AUTHORITATIVE_STATE'))

def _validate(q):
    if not q.request_id or not q.binding or not q.state_epoch: return ('EMPTY_REQUEST_CONTEXT',Escalation.INVALID_CONFIGURATION)
    if not q.target_id or not q.algorithm_version: return ('EMPTY_TARGET_OR_VERSION',Escalation.INVALID_CONFIGURATION)
    if not q.components: return ('EMPTY_COMPONENT_SET',Escalation.INVALID_CONFIGURATION)
    ids=[c.component_id for c in q.components]
    if any(not x for x in ids) or len(ids)!=len(set(ids)): return ('INVALID_OR_DUPLICATE_COMPONENT_ID',Escalation.INVALID_CONFIGURATION)
    if any(not isinstance(c.payload,bytes) for c in q.components): return ('NON_BYTES_COMPONENT',Escalation.INVALID_VALUE)
    if any(not isinstance(k,str) or not isinstance(v,str) for k,v in q.metadata): return ('INVALID_METADATA',Escalation.INVALID_VALUE)
    m=q.expected_manifest
    if not m.schema or not m.target_id or not m.algorithm_version or not m.manifest_hash: return ('INVALID_EXPECTED_MANIFEST',Escalation.INVALID_CONFIGURATION)
    mids=[e.component_id for e in m.entries]
    if any(not x for x in mids) or len(mids)!=len(set(mids)): return ('INVALID_MANIFEST_COMPONENT_IDS',Escalation.INVALID_CONFIGURATION)
    return None

def evaluate(q):
    v=_validate(q)
    if v: return _invalid(q,*v)
    m=q.expected_manifest
    mh_ok=_manifest_hash_valid(m)
    if not mh_ok:
        return IntegrityResult(Decision.DENY,NextAction.RETAIN_ORIGINAL_CANDIDATE,Escalation.MANIFEST_HASH_MISMATCH,EngineState.ORIGINAL_RETENTION_CANDIDATE,q.request_id,False,False,False,False,False,False,False,0,0,m.manifest_hash,False,('MANIFEST_HASH_MISMATCH','RESTORATION_NOT_AUTHORIZED_BY_THIS_RESULT','ORIGINAL_RETENTION_REMAINS_CANDIDATE'))
    target_ok=q.target_id==m.target_id
    if not target_ok:
        return IntegrityResult(Decision.DENY,NextAction.RETAIN_ORIGINAL_CANDIDATE,Escalation.TARGET_MISMATCH,EngineState.ORIGINAL_RETENTION_CANDIDATE,q.request_id,False,False,True,False,False,False,False,0,0,m.manifest_hash,False,('TARGET_ID_MISMATCH','RESTORATION_NOT_AUTHORIZED_BY_THIS_RESULT','ORIGINAL_RETENTION_REMAINS_CANDIDATE'))
    version_ok=q.algorithm_version==m.algorithm_version
    if not version_ok:
        return IntegrityResult(Decision.HOLD,NextAction.RETAIN_ORIGINAL_CANDIDATE,Escalation.VERSION_INCOMPATIBLE,EngineState.ORIGINAL_RETENTION_CANDIDATE,q.request_id,True,False,True,False,False,False,False,0,0,m.manifest_hash,False,('ALGORITHM_VERSION_INCOMPATIBLE','RESTORATION_NOT_AUTHORIZED_BY_THIS_RESULT','ORIGINAL_RETENTION_REMAINS_CANDIDATE'))
    metadata_ok=_metadata_fp(q.metadata)==m.metadata_fingerprint
    if not metadata_ok:
        return IntegrityResult(Decision.DENY,NextAction.RETAIN_ORIGINAL_CANDIDATE,Escalation.METADATA_MISMATCH,EngineState.ORIGINAL_RETENTION_CANDIDATE,q.request_id,True,True,True,False,False,False,False,0,0,m.manifest_hash,False,('METADATA_FINGERPRINT_MISMATCH','RESTORATION_NOT_AUTHORIZED_BY_THIS_RESULT','ORIGINAL_RETENTION_REMAINS_CANDIDATE'))
    current={c.component_id:c for c in q.components}; expected={e.component_id:e for e in m.entries}
    set_ok=set(current)==set(expected)
    if not set_ok:
        return IntegrityResult(Decision.DENY,NextAction.RETAIN_ORIGINAL_CANDIDATE,Escalation.COMPONENT_SET_MISMATCH,EngineState.ORIGINAL_RETENTION_CANDIDATE,q.request_id,True,True,True,True,False,False,False,len(expected),0,m.manifest_hash,False,('COMPONENT_SET_MISMATCH','RESTORATION_NOT_AUTHORIZED_BY_THIS_RESULT','ORIGINAL_RETENTION_REMAINS_CANDIDATE'))
    required_available=all((not expected[cid].required) or current[cid].available for cid in expected)
    if not required_available:
        return IntegrityResult(Decision.HOLD,NextAction.RETAIN_ORIGINAL_CANDIDATE,Escalation.COMPONENT_UNAVAILABLE,EngineState.ORIGINAL_RETENTION_CANDIDATE,q.request_id,True,True,True,True,True,False,False,len(expected),0,m.manifest_hash,False,('REQUIRED_COMPONENT_UNAVAILABLE','RESTORATION_NOT_AUTHORIZED_BY_THIS_RESULT','ORIGINAL_RETENTION_REMAINS_CANDIDATE'))
    matched=0
    for cid,e in expected.items():
        c=current[cid]
        if c.kind!=e.kind or c.required!=e.required or len(c.payload)!=e.size_bytes or sha256(c.payload).hexdigest()!=e.sha256:
            return IntegrityResult(Decision.DENY,NextAction.RETAIN_ORIGINAL_CANDIDATE,Escalation.COMPONENT_HASH_MISMATCH,EngineState.ORIGINAL_RETENTION_CANDIDATE,q.request_id,True,True,True,True,True,False,True,len(expected),matched,m.manifest_hash,False,(f'COMPONENT_HASH_OR_BINDING_MISMATCH:{cid}','RESTORATION_NOT_AUTHORIZED_BY_THIS_RESULT','ORIGINAL_RETENTION_REMAINS_CANDIDATE'))
        matched+=1
    return IntegrityResult(Decision.ALLOW,NextAction.CONTINUE_RESTORATION_CANDIDATE,Escalation.NONE,EngineState.INTEGRITY_VERIFIED_CANDIDATE,q.request_id,True,True,True,True,True,True,True,len(expected),matched,m.manifest_hash,True,('ALL_MANIFEST_BINDINGS_MATCH','RESTORATION_REMAINS_CANDIDATE','NO_PERMISSION_OR_EXECUTION_GRANTED','DCSR_STATE_IS_NOT_AUTHORITATIVE_STATE'))

def _component_fp(q): return _fp(tuple(q.components))
def _manifest_fp(q): return _fp(q.expected_manifest)
def _config_fp(q): return _fp((q.request_id,q.target_id,q.algorithm_version,q.metadata,q.binding,q.state_epoch))
def _integrity_fp(req,res,cf,mf,gf,rf,binding,epoch): return _fp((req,res,cf,mf,gf,rf,binding,epoch))

def prepare_state(q,binding,state_epoch):
    if binding!=q.binding or state_epoch!=q.state_epoch: raise ValueError('binding/state_epoch mismatch')
    r=evaluate(q); cf=_component_fp(q); mf=_manifest_fp(q); gf=_config_fp(q); rf=_fp(r)
    return PreparedIntegrityState(q,r,cf,mf,gf,rf,_integrity_fp(q,r,cf,mf,gf,rf,binding,state_epoch),binding,state_epoch)

def evaluate_prepared(st,*,integrity_validated,current_components_fingerprint,current_manifest_fingerprint,current_config_fingerprint,current_result_fingerprint):
    valid=bool(integrity_validated and st.integrity_fingerprint==_integrity_fp(st.request,st.result,st.components_fingerprint,st.manifest_fingerprint,st.config_fingerprint,st.result_fingerprint,st.binding,st.state_epoch) and current_components_fingerprint==st.components_fingerprint and current_manifest_fingerprint==st.manifest_fingerprint and current_config_fingerprint==st.config_fingerprint and current_result_fingerprint==st.result_fingerprint)
    return st.result if valid else _invalid(st.request,'PREPARED_STATE_INTEGRITY_OR_FINGERPRINT_MISMATCH',Escalation.INVALID_CONFIGURATION)

def make_delta(a,b):
    return IntegrityChange(a.components_fingerprint!=b.components_fingerprint,a.manifest_fingerprint!=b.manifest_fingerprint,a.config_fingerprint!=b.config_fingerprint,a.integrity_fingerprint,b.integrity_fingerprint)

def plan_missing_only(a,b):
    d=make_delta(a,b); ids=[]
    if d.components_changed: ids.append('COMPONENT_BYTES')
    if d.manifest_changed: ids.append('INTEGRITY_MANIFEST')
    if d.config_changed: ids.append('INTEGRITY_CONFIG')
    return MissingOnlyPlan(tuple(ids),len(_canon(tuple(ids)))+96,False)

def default_components():
    return (
      ComponentBytes('BASE-001',ComponentKind.BASE,b'BASE:'+bytes(range(64))*8),
      ComponentBytes('PROFILE-001',ComponentKind.PROFILE,b'PROFILE:'+b'P'*384),
      ComponentBytes('DELTA-001',ComponentKind.DELTA,b'DELTA:'+bytes(reversed(range(64)))*4),
      ComponentBytes('RESIDUAL-001',ComponentKind.RESIDUAL,b'RESIDUAL:'+b'R'*512),
      ComponentBytes('SIDECAR-001',ComponentKind.SIDECAR,b'SIDECAR:'+b'S'*192,required=False),
    )

def default_metadata(): return (('asset_class','MODEL_BUNDLE'),('compression_family','MIXED'),('manifest_policy','STRICT_BINDING'),('creator','NOEPIN / のえぴん'))
def default_request():
    cs=default_components(); md=default_metadata(); m=build_manifest('ASSET-173-A','ALGO-173-v2',cs,md)
    return IntegrityRequest('CRIM-173-A','ASSET-173-A','ALGO-173-v2',cs,md,m,'DEFAULT-BINDING','EPOCH-1')
def default_evaluation(): return evaluate(default_request())

if __name__=='__main__':
    print(json.dumps(_obj(default_evaluation()),ensure_ascii=False,sort_keys=True,indent=2))
