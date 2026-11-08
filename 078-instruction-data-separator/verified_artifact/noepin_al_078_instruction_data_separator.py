"""NOEPIN AL 078 — Instruction-Data Separator — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Deterministic provenance-aware separator for external content. It classifies
instruction-like text as data unless an external authority channel is explicitly
confirmed. It does not grant permission, execute instructions, create policy,
authenticate identities, decrypt content, perform DLP, send data, or prove truth.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json,re
from typing import Sequence

class Decision(str,Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class SourceTrust(str,Enum):
    UNTRUSTED='UNTRUSTED'; UNKNOWN='UNKNOWN'; TRUSTED_USER='TRUSTED_USER'; TRUSTED_POLICY='TRUSTED_POLICY'
class SegmentKind(str,Enum):
    DATA='DATA'; INSTRUCTION_CANDIDATE='INSTRUCTION_CANDIDATE'; POLICY_CANDIDATE='POLICY_CANDIDATE'

@dataclass(frozen=True)
class SourceRecord:
    source_id:str; trust:SourceTrust; observed:bool; authority_confirmed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class ChannelMetadata:
    channel_id:str; channel_type:str; observed:bool; instruction_authority:bool; policy_authority:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class TaskContext:
    task_id:str; task_intent:tuple[str,...]; allowed_user_channels:tuple[str,...]; policy_channels:tuple[str,...]; binding:str; state_epoch:str
@dataclass(frozen=True)
class SeparationPolicy:
    binding:str; state_epoch:str; max_content_chars:int=200000; revoked:bool=False
@dataclass(frozen=True)
class SeparationRequest:
    content_id:str; source_id:str; channel_id:str; external_content:str; task_context:TaskContext; binding:str; state_epoch:str
@dataclass(frozen=True)
class ContentSegment:
    index:int; text:str; kind:SegmentKind; instruction_like:bool; quoted:bool; taint_labels:tuple[str,...]; source_id:str; channel_id:str
@dataclass(frozen=True)
class SeparationResult:
    decision:Decision
    reasons:tuple[str,...]
    data_segments:tuple[ContentSegment,...]
    instruction_candidates:tuple[ContentSegment,...]
    policy_candidates:tuple[ContentSegment,...]
    instruction_execution_candidate:bool
    policy_route_candidate:bool
    user_authority_recheck_candidate:bool
    # authority negatives
    permission_granted:bool=False
    instruction_executed:bool=False
    policy_applied:bool=False
    policy_created:bool=False
    authentication_proven:bool=False
    cryptography_performed:bool=False
    dlp_performed:bool=False
    external_write_performed:bool=False
    data_sent:bool=False
    world_truth_proven:bool=False
    safety_proven:bool=False
    action_success:bool=False
@dataclass(frozen=True)
class PreparedSeparationState:
    policy:SeparationPolicy
    sources:tuple[SourceRecord,...]
    channels:tuple[ChannelMetadata,...]
    source_fingerprints:tuple[tuple[str,str],...]
    channel_fingerprints:tuple[tuple[str,str],...]
    policy_fingerprint:str
    registry_fingerprint:str
    source_index:tuple[tuple[str,SourceRecord],...]
    channel_index:tuple[tuple[str,ChannelMetadata],...]
    binding:str; state_epoch:str
@dataclass(frozen=True)
class SeparationRegistryDelta:
    base_fingerprint:str; target_fingerprint:str
    changed_sources:tuple[SourceRecord,...]; removed_source_ids:tuple[str,...]
    changed_channels:tuple[ChannelMetadata,...]; removed_channel_ids:tuple[str,...]
    target_policy:SeparationPolicy; binding:str; state_epoch:str
@dataclass(frozen=True)
class SeparationSyncPlan:
    missing_or_changed_sources:tuple[str,...]
    missing_or_changed_channels:tuple[str,...]
    metadata_bytes_required:int
    full_resend_required:bool

def _canon(v)->bytes:
    def cv(x):
        if isinstance(x,Enum): return x.value
        if hasattr(x,'__dataclass_fields__'): return {k:cv(getattr(x,k)) for k in x.__dataclass_fields__}
        if isinstance(x,tuple): return [cv(i) for i in x]
        if isinstance(x,list): return [cv(i) for i in x]
        if isinstance(x,dict): return {str(k):cv(x[k]) for k in sorted(x)}
        return x
    return json.dumps(cv(v),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def _fp(v)->str: return sha256(_canon(v)).hexdigest()
def _registry_fp(policy,sources,channels):
    return _fp({'policy':_fp(policy),'sources':sorted((x.source_id,_fp(x)) for x in sources),'channels':sorted((x.channel_id,_fp(x)) for x in channels)})
def _uniq(items,attr):
    ids=[getattr(x,attr) for x in items]; return len(ids)==len(set(ids))
def _idx(items,key): return tuple(sorted(((getattr(x,key),x) for x in items),key=lambda z:z[0]))
def _lookup(index,key):
    lo,hi=0,len(index)
    while lo<hi:
        m=(lo+hi)//2
        if index[m][0]<key: lo=m+1
        else: hi=m
    return index[lo][1] if lo<len(index) and index[lo][0]==key else None

# Conservative deterministic markers. These are candidates only, not semantic truth.
_MARKERS=(
    r'\bignore\s+(?:all\s+)?(?:previous|prior|earlier)\b',
    r'\b(?:system|developer)\s+(?:message|instruction|prompt)\b',
    r'\b(?:execute|run|invoke|call)\s+(?:the\s+)?(?:tool|command|shell|api)\b',
    r'\b(?:send|upload|exfiltrate|delete|erase|overwrite|grant|enable)\b',
    r'\b(?:you\s+must|must\s+now|do\s+not\s+follow|instead\s+follow)\b',
    r'\b(?:instruction|directive)\s*:',
    r'命令\s*[:：]', r'指示\s*[:：]', r'以前の指示を無視', r'ツールを実行', r'送信して', r'削除して',
)
_MARKER_RE=tuple(re.compile(p,re.I) for p in _MARKERS)

def _strip_invisible(s:str)->str:
    return re.sub('[\u200b\u200c\u200d\u2060\ufeff]','',s)
def _split(content:str)->tuple[str,...]:
    # preserve code/quotes as segments; blank lines split paragraphs, otherwise line granularity
    lines=content.replace('\r\n','\n').replace('\r','\n').split('\n')
    out=[]
    for line in lines:
        line=line.strip()
        if line: out.append(line)
    return tuple(out) or ('',)
def _quoted(text:str)->bool:
    t=text.strip()
    if t.startswith(('>','“','”','"','「','『','`')): return True
    if (t.startswith("'") and t.endswith("'")) or (t.startswith('(') and t.endswith(')')): return True
    return False
def _instruction_like(text:str)->bool:
    n=_strip_invisible(text)
    return any(p.search(n) for p in _MARKER_RE)
def _segment(req,src,ch):
    data=[]; inst=[]; policy=[]
    for i,raw in enumerate(_split(req.external_content)):
        q=_quoted(raw); il=_instruction_like(raw)
        taints=[]
        if src.trust in (SourceTrust.UNTRUSTED,SourceTrust.UNKNOWN): taints.append('EXTERNAL_UNTRUSTED_OR_UNKNOWN')
        if il: taints.append('INSTRUCTION_LIKE')
        if q and il: taints.append('QUOTED_INSTRUCTION_DATA')
        # quoted text is always data. Uncertain/external instruction-like text stays data + candidate record.
        if q or not il:
            seg=ContentSegment(i,raw,SegmentKind.DATA,il,q,tuple(sorted(set(taints))),src.source_id,ch.channel_id); data.append(seg); continue
        if src.trust==SourceTrust.TRUSTED_POLICY and src.authority_confirmed and ch.policy_authority:
            seg=ContentSegment(i,raw,SegmentKind.POLICY_CANDIDATE,True,False,tuple(sorted(set(taints+['POLICY_ROUTE_ONLY']))),src.source_id,ch.channel_id); policy.append(seg)
        elif src.trust==SourceTrust.TRUSTED_USER and src.authority_confirmed and ch.instruction_authority:
            seg=ContentSegment(i,raw,SegmentKind.INSTRUCTION_CANDIDATE,True,False,tuple(sorted(set(taints+['USER_AUTHORITY_RECHECK']))),src.source_id,ch.channel_id); inst.append(seg)
        else:
            # keep an audit candidate, but actual segment remains data-only
            d=ContentSegment(i,raw,SegmentKind.DATA,True,False,tuple(sorted(set(taints+['UNTRUSTED_INSTRUCTION_FORCED_TO_DATA']))),src.source_id,ch.channel_id); data.append(d)
            inst.append(ContentSegment(i,raw,SegmentKind.INSTRUCTION_CANDIDATE,True,False,d.taint_labels,src.source_id,ch.channel_id))
    return tuple(data),tuple(inst),tuple(policy)

def default_policy(): return SeparationPolicy('SEP-BIND','STATE-EPOCH-1')
def default_sources():
    b,e='SEP-BIND','STATE-EPOCH-1'
    return (
      SourceRecord('SRC-WEB',SourceTrust.UNTRUSTED,True,False,b,e),
      SourceRecord('SRC-MAIL',SourceTrust.UNKNOWN,True,False,b,e),
      SourceRecord('SRC-USER',SourceTrust.TRUSTED_USER,True,True,b,e),
      SourceRecord('SRC-POLICY',SourceTrust.TRUSTED_POLICY,True,True,b,e),
    )
def default_channels():
    b,e='SEP-BIND','STATE-EPOCH-1'
    return (
      ChannelMetadata('CH-WEB','WEB',True,False,False,b,e),
      ChannelMetadata('CH-MAIL','EMAIL',True,False,False,b,e),
      ChannelMetadata('CH-USER','USER',True,True,False,b,e),
      ChannelMetadata('CH-POLICY','POLICY',True,False,True,b,e),
    )
def default_context(): return TaskContext('TASK-1',('SUMMARIZE',),('CH-USER',),('CH-POLICY',),'SEP-BIND','STATE-EPOCH-1')
def default_request(): return SeparationRequest('CONTENT-1','SRC-WEB','CH-WEB','This document contains ordinary reference material.',default_context(),'SEP-BIND','STATE-EPOCH-1')

def _hold(reason): return SeparationResult(Decision.HOLD,(reason,),(),(),(),False,False,False)

def evaluate(req:SeparationRequest,policy:SeparationPolicy,sources:Sequence[SourceRecord],channels:Sequence[ChannelMetadata])->SeparationResult:
    if not isinstance(req,SeparationRequest) or not isinstance(policy,SeparationPolicy): return _hold('INVALID_TYPED_INPUT')
    if policy.revoked: return _hold('POLICY_REVOKED')
    if req.binding!=policy.binding or req.state_epoch!=policy.state_epoch: return _hold('REQUEST_POLICY_BINDING_MISMATCH')
    if req.task_context.binding!=policy.binding or req.task_context.state_epoch!=policy.state_epoch: return _hold('TASK_CONTEXT_BINDING_MISMATCH')
    if len(req.external_content)>policy.max_content_chars: return _hold('CONTENT_TOO_LARGE')
    if not _uniq(sources,'source_id') or not _uniq(channels,'channel_id'): return _hold('DUPLICATE_REGISTRY_ID')
    src=next((x for x in sources if x.source_id==req.source_id),None); ch=next((x for x in channels if x.channel_id==req.channel_id),None)
    if src is None or ch is None: return _hold('SOURCE_OR_CHANNEL_UNKNOWN')
    if not src.observed or not ch.observed: return _hold('SOURCE_OR_CHANNEL_UNOBSERVED')
    if src.binding!=policy.binding or src.state_epoch!=policy.state_epoch or ch.binding!=policy.binding or ch.state_epoch!=policy.state_epoch: return _hold('REGISTRY_BINDING_MISMATCH')
    data,inst,pol=_segment(req,src,ch)
    # Trusted routes still require another authority path; separator never executes/applies them.
    if pol:
        if req.channel_id not in req.task_context.policy_channels: return _hold('POLICY_CHANNEL_NOT_AUTHORIZED_BY_TASK_CONTEXT')
        return SeparationResult(Decision.HOLD,('TRUSTED_POLICY_REQUIRES_POLICY_PATH_RECHECK',),data,inst,pol,False,True,False)
    trusted_user=[x for x in inst if src.trust==SourceTrust.TRUSTED_USER and src.authority_confirmed and ch.instruction_authority]
    if trusted_user:
        if req.channel_id not in req.task_context.allowed_user_channels: return _hold('USER_CHANNEL_NOT_AUTHORIZED_BY_TASK_CONTEXT')
        return SeparationResult(Decision.HOLD,('USER_INSTRUCTION_REQUIRES_CONTROL_PLANE_RECHECK',),data,tuple(trusted_user),(),False,False,True)
    untrusted=[x for x in inst if 'UNTRUSTED_INSTRUCTION_FORCED_TO_DATA' in x.taint_labels]
    if untrusted:
        return SeparationResult(Decision.DENY,('UNTRUSTED_EXTERNAL_INSTRUCTION_NOT_EXECUTABLE','CONTENT_AVAILABLE_AS_DATA_ONLY'),data,tuple(untrusted),(),False,False,False)
    # No actionable instruction candidates: content may proceed only as data.
    return SeparationResult(Decision.ALLOW,('DATA_ONLY_NO_AUTHORIZED_INSTRUCTION',),data,(),(),False,False,False)

def prepare_state(policy,sources,channels,*,binding:str)->PreparedSeparationState:
    ss=tuple(sources); cc=tuple(channels)
    return PreparedSeparationState(policy,ss,cc,tuple(sorted((x.source_id,_fp(x)) for x in ss)),tuple(sorted((x.channel_id,_fp(x)) for x in cc)),_fp(policy),_registry_fp(policy,ss,cc),_idx(ss,'source_id'),_idx(cc,'channel_id'),binding,policy.state_epoch)
def validate_prepared_integrity(st:PreparedSeparationState)->bool:
    if not isinstance(st,PreparedSeparationState): return False
    if st.binding!=st.policy.binding or st.state_epoch!=st.policy.state_epoch: return False
    if st.policy_fingerprint!=_fp(st.policy): return False
    if st.source_fingerprints!=tuple(sorted((x.source_id,_fp(x)) for x in st.sources)): return False
    if st.channel_fingerprints!=tuple(sorted((x.channel_id,_fp(x)) for x in st.channels)): return False
    if st.registry_fingerprint!=_registry_fp(st.policy,st.sources,st.channels): return False
    if st.source_index!=_idx(st.sources,'source_id') or st.channel_index!=_idx(st.channels,'channel_id'): return False
    return _uniq(st.sources,'source_id') and _uniq(st.channels,'channel_id')
def evaluate_prepared(req,st:PreparedSeparationState,*,current_policy_fingerprint:str,current_registry_fingerprint:str,prepared_integrity_validated:bool)->SeparationResult:
    if not isinstance(req,SeparationRequest) or not isinstance(st,PreparedSeparationState): return _hold('INVALID_TYPED_INPUT')
    if not prepared_integrity_validated: return _hold('PREPARED_INTEGRITY_NOT_VALIDATED')
    if current_policy_fingerprint!=st.policy_fingerprint: return _hold('CURRENT_POLICY_FINGERPRINT_MISMATCH')
    if current_registry_fingerprint!=st.registry_fingerprint: return _hold('CURRENT_REGISTRY_FINGERPRINT_MISMATCH')
    # Fast path still applies identical per-request checks with prebuilt index lookups.
    p=st.policy
    if p.revoked: return _hold('POLICY_REVOKED')
    if req.binding!=p.binding or req.state_epoch!=p.state_epoch: return _hold('REQUEST_POLICY_BINDING_MISMATCH')
    if req.task_context.binding!=p.binding or req.task_context.state_epoch!=p.state_epoch: return _hold('TASK_CONTEXT_BINDING_MISMATCH')
    if len(req.external_content)>p.max_content_chars: return _hold('CONTENT_TOO_LARGE')
    src=_lookup(st.source_index,req.source_id); ch=_lookup(st.channel_index,req.channel_id)
    if src is None or ch is None: return _hold('SOURCE_OR_CHANNEL_UNKNOWN')
    if not src.observed or not ch.observed: return _hold('SOURCE_OR_CHANNEL_UNOBSERVED')
    if src.binding!=p.binding or src.state_epoch!=p.state_epoch or ch.binding!=p.binding or ch.state_epoch!=p.state_epoch: return _hold('REGISTRY_BINDING_MISMATCH')
    data,inst,pol=_segment(req,src,ch)
    if pol:
        if req.channel_id not in req.task_context.policy_channels: return _hold('POLICY_CHANNEL_NOT_AUTHORIZED_BY_TASK_CONTEXT')
        return SeparationResult(Decision.HOLD,('TRUSTED_POLICY_REQUIRES_POLICY_PATH_RECHECK',),data,inst,pol,False,True,False)
    trusted_user=[x for x in inst if src.trust==SourceTrust.TRUSTED_USER and src.authority_confirmed and ch.instruction_authority]
    if trusted_user:
        if req.channel_id not in req.task_context.allowed_user_channels: return _hold('USER_CHANNEL_NOT_AUTHORIZED_BY_TASK_CONTEXT')
        return SeparationResult(Decision.HOLD,('USER_INSTRUCTION_REQUIRES_CONTROL_PLANE_RECHECK',),data,tuple(trusted_user),(),False,False,True)
    untrusted=[x for x in inst if 'UNTRUSTED_INSTRUCTION_FORCED_TO_DATA' in x.taint_labels]
    if untrusted:
        return SeparationResult(Decision.DENY,('UNTRUSTED_EXTERNAL_INSTRUCTION_NOT_EXECUTABLE','CONTENT_AVAILABLE_AS_DATA_ONLY'),data,tuple(untrusted),(),False,False,False)
    return SeparationResult(Decision.ALLOW,('DATA_ONLY_NO_AUTHORIZED_INSTRUCTION',),data,(),(),False,False,False)

def make_delta(a:PreparedSeparationState,b:PreparedSeparationState)->SeparationRegistryDelta:
    af, bf=dict(a.source_fingerprints),dict(b.source_fingerprints); ac,bc=dict(a.channel_fingerprints),dict(b.channel_fingerprints)
    sm={x.source_id:x for x in b.sources}; cm={x.channel_id:x for x in b.channels}
    cs=tuple(sm[k] for k in sorted(bf) if af.get(k)!=bf[k]); rs=tuple(sorted(set(af)-set(bf)))
    cc=tuple(cm[k] for k in sorted(bc) if ac.get(k)!=bc[k]); rc=tuple(sorted(set(ac)-set(bc)))
    return SeparationRegistryDelta(a.registry_fingerprint,b.registry_fingerprint,cs,rs,cc,rc,b.policy,b.binding,b.state_epoch)
def apply_delta(base:PreparedSeparationState,d:SeparationRegistryDelta)->PreparedSeparationState:
    if d.base_fingerprint!=base.registry_fingerprint: raise ValueError('BASE_FINGERPRINT_MISMATCH')
    sm={x.source_id:x for x in base.sources}; cm={x.channel_id:x for x in base.channels}
    for k in d.removed_source_ids: sm.pop(k,None)
    for x in d.changed_sources: sm[x.source_id]=x
    for k in d.removed_channel_ids: cm.pop(k,None)
    for x in d.changed_channels: cm[x.channel_id]=x
    out=prepare_state(d.target_policy,tuple(sm[k] for k in sorted(sm)),tuple(cm[k] for k in sorted(cm)),binding=d.binding)
    if out.registry_fingerprint!=d.target_fingerprint: raise ValueError('TARGET_FINGERPRINT_MISMATCH')
    return out
def missing_only_sync_plan(target:PreparedSeparationState,known_sources:dict[str,str],known_channels:dict[str,str])->SeparationSyncPlan:
    sf=dict(target.source_fingerprints); cf=dict(target.channel_fingerprints)
    ms=tuple(k for k in sorted(sf) if known_sources.get(k)!=sf[k]); mc=tuple(k for k in sorted(cf) if known_channels.get(k)!=cf[k])
    meta=len(_canon({'sources':ms,'channels':mc,'policy':target.policy_fingerprint,'registry':target.registry_fingerprint}))
    return SeparationSyncPlan(ms,mc,meta,False)
def full_registry_bytes(st): return len(_canon({'policy':st.policy,'sources':st.sources,'channels':st.channels}))
def delta_bytes(d): return len(_canon(d))
