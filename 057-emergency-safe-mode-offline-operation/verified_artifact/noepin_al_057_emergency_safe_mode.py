"""NOEPIN AL 057 — Emergency Safe Mode / Offline Operation.

Pure control-plane evaluator for degraded/read-only/local-only/offline-safe mode
candidates. It validates incident signals and replay-protection receipt state, then
returns a deterministic candidate mode and restrictions. It does not execute mode
transitions, disconnect networks, disable writes/tools, persist receipts, or prove
system safety/success.

Creator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support using ChatGPT
License / Rights: NOT SPECIFIED
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
from hashlib import sha256
import json
from typing import Any, FrozenSet, Iterable, Mapping, Tuple

class ControlDecision(str, Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'

class SafeMode(str, Enum):
    NORMAL='NORMAL'; DEGRADED='DEGRADED'; READ_ONLY='READ_ONLY'; LOCAL_ONLY='LOCAL_ONLY'; OFFLINE_SAFE='OFFLINE_SAFE'

_SEVERITY={'LOW':1,'MEDIUM':2,'HIGH':3,'CRITICAL':4}
_ALLOWED_CATEGORIES=frozenset({'NETWORK_ANOMALY','EXTERNAL_TOOL_ANOMALY','AUTOMATION_ANOMALY','INTEGRITY_RISK','DEPENDENCY_OUTAGE','AUTHORITY_ANOMALY'})
_ALLOWED_OPERATIONS=frozenset({'MODE_PLAN','READ','WRITE','NETWORK','EXTERNAL_TOOL','AUTOMATION'})

@dataclass(frozen=True)
class SafeModePolicy:
    policy_id:str; version:str; authority_epoch:int; issued_at:int; expires_at:int
    max_signal_age_seconds:int; max_receipt_age_seconds:int
    require_independent_signal:bool=True; revoked:bool=False
    def validate(self,now:int)->None:
        if not self.policy_id or not self.version or self.authority_epoch<1: raise ValueError('policy identity invalid')
        if self.issued_at<0 or self.expires_at<=self.issued_at or not self.issued_at<=now<self.expires_at: raise ValueError('policy not current')
        if self.max_signal_age_seconds<1 or self.max_receipt_age_seconds<1: raise ValueError('policy age limit invalid')
        if self.revoked: raise ValueError('policy revoked')

@dataclass(frozen=True)
class IncidentSignal:
    signal_id:str; incident_id:str; severity:str; categories:FrozenSet[str]; observed_at:int
    verified:bool; independent:bool; evidence_binding:str; revoked:bool=False
    def validate(self)->None:
        if not self.signal_id or not self.incident_id or not self.evidence_binding: raise ValueError('signal identity required')
        if self.severity not in _SEVERITY: raise ValueError('signal severity invalid')
        if not self.categories or not self.categories<=_ALLOWED_CATEGORIES: raise ValueError('signal category invalid')
        if self.observed_at<0: raise ValueError('signal time invalid')

@dataclass(frozen=True)
class ReplayReceipt:
    receipt_id:str; request_id:str; nonce:str; mode_candidate:SafeMode; issued_at:int
    verified:bool; evidence_binding:str; revoked:bool=False
    def validate(self)->None:
        if not self.receipt_id or not self.request_id or not self.nonce or not self.evidence_binding: raise ValueError('receipt identity required')
        if self.issued_at<0: raise ValueError('receipt time invalid')

@dataclass(frozen=True)
class SafeModeRequest:
    request_id:str; incident_id:str; operation_kind:str; current_mode:SafeMode
    expected_policy_id:str; expected_policy_version:str; expected_authority_epoch:int
    evidence_binding:str; nonce:str
    network_required:bool=False; external_tool_required:bool=False; write_required:bool=False; automation_required:bool=False
    def validate(self)->None:
        if not self.request_id or not self.incident_id or not self.evidence_binding or not self.nonce: raise ValueError('request identity required')
        if self.operation_kind not in _ALLOWED_OPERATIONS: raise ValueError('operation invalid')
        if not self.expected_policy_id or not self.expected_policy_version or self.expected_authority_epoch<1: raise ValueError('request policy binding invalid')

@dataclass(frozen=True)
class PreparedSafetyRegistry:
    registry_fingerprint:str; policy_fingerprint:str
    signals:Tuple[IncidentSignal,...]; receipts:Tuple[ReplayReceipt,...]
    signal_fingerprints:Mapping[str,str]; receipt_fingerprints:Mapping[str,str]
    incident_signal_index:Mapping[str,Tuple[str,...]]; request_receipt_index:Mapping[str,Tuple[str,...]]; nonce_receipt_index:Mapping[str,Tuple[str,...]]

@dataclass(frozen=True)
class SafetyRegistryDelta:
    base_fingerprint:str; target_fingerprint:str
    changed_signals:Tuple[IncidentSignal,...]; removed_signal_ids:Tuple[str,...]; added_signals:Tuple[IncidentSignal,...]
    changed_receipts:Tuple[ReplayReceipt,...]; removed_receipt_ids:Tuple[str,...]; added_receipts:Tuple[ReplayReceipt,...]

@dataclass(frozen=True)
class RegistrySyncPlan:
    missing_or_changed_signal_ids:Tuple[str,...]; missing_or_changed_receipt_ids:Tuple[str,...]
    metadata_bytes_required:int; full_metadata_bytes:int; full_resend_required:bool
    permission_granted:bool=False; mode_transition_authorized:bool=False; network_disconnect_authorized:bool=False
    write_disable_authorized:bool=False; external_tool_shutdown_authorized:bool=False; automation_stop_authorized:bool=False
    receipt_persist_authorized:bool=False

@dataclass(frozen=True)
class SafeModeAssessment:
    decision:ControlDecision; mode_candidate:SafeMode; reasons:Tuple[str,...]
    request_id:str; incident_id:str; active_signal_ids:Tuple[str,...]; active_categories:Tuple[str,...]
    replay_detected:bool; receipt_candidate_id:str
    network_disabled_candidate:bool; external_tools_disabled_candidate:bool; auto_execution_disabled_candidate:bool
    read_only_candidate:bool; local_only_candidate:bool
    registry_fingerprint:str; policy_fingerprint:str; request_fingerprint:str
    permission_granted:bool=False; mode_transition_executed:bool=False; network_disconnect_executed:bool=False
    external_tool_shutdown_executed:bool=False; automation_stop_executed:bool=False; writes_disabled_executed:bool=False
    receipt_persisted:bool=False; partial_state_authoritative:bool=False; safety_truth_proven:bool=False; action_success:bool=False

def _canonical(v:Any)->Any:
    if isinstance(v,Enum): return v.value
    if is_dataclass(v): return {f.name:_canonical(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v,Mapping): return {str(k):_canonical(x) for k,x in sorted(v.items(),key=lambda kv:str(kv[0]))}
    if isinstance(v,(set,frozenset)): return sorted((_canonical(x) for x in v),key=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')))
    if isinstance(v,(tuple,list)): return [_canonical(x) for x in v]
    return v

def canonical_json(v:Any)->str: return json.dumps(_canonical(v),ensure_ascii=False,sort_keys=True,separators=(',',':'))
def fingerprint(v:Any)->str: return sha256(canonical_json(v).encode()).hexdigest()
def _signals(xs:Iterable[IncidentSignal])->Tuple[IncidentSignal,...]: return tuple(sorted(xs,key=lambda x:x.signal_id))
def _receipts(xs:Iterable[ReplayReceipt])->Tuple[ReplayReceipt,...]: return tuple(sorted(xs,key=lambda x:x.receipt_id))
def registry_fingerprint(signals,receipts)->str: return fingerprint({'signals':_signals(signals),'receipts':_receipts(receipts)})

def prepare_registry(policy:SafeModePolicy,signals:Iterable[IncidentSignal],receipts:Iterable[ReplayReceipt],*,now:int)->PreparedSafetyRegistry:
    policy.validate(now); ss=_signals(signals); rs=_receipts(receipts)
    for x in ss: x.validate()
    for x in rs: x.validate()
    if len({x.signal_id for x in ss})!=len(ss): raise ValueError('duplicate signal id')
    if len({x.receipt_id for x in rs})!=len(rs): raise ValueError('duplicate receipt id')
    si={}; ri={}; ni={}
    for x in ss: si.setdefault(x.incident_id,[]).append(x.signal_id)
    for x in rs:
        ri.setdefault(x.request_id,[]).append(x.receipt_id); ni.setdefault(x.nonce,[]).append(x.receipt_id)
    return PreparedSafetyRegistry(
        registry_fingerprint(ss,rs),fingerprint(policy),ss,rs,
        {x.signal_id:fingerprint(x) for x in ss},{x.receipt_id:fingerprint(x) for x in rs},
        {k:tuple(sorted(v)) for k,v in si.items()},{k:tuple(sorted(v)) for k,v in ri.items()},{k:tuple(sorted(v)) for k,v in ni.items()})

def _assess(dec,mode,req,policy,reg,reasons=(),active=(),cats=(),replay=False):
    network=mode in {SafeMode.LOCAL_ONLY,SafeMode.OFFLINE_SAFE}
    external=mode is not SafeMode.NORMAL
    auto=mode is not SafeMode.NORMAL
    readonly=mode in {SafeMode.READ_ONLY,SafeMode.OFFLINE_SAFE}
    local=mode in {SafeMode.LOCAL_ONLY,SafeMode.OFFLINE_SAFE}
    receipt_id='RECEIPT-CANDIDATE-'+fingerprint({'request_id':req.request_id,'nonce':req.nonce,'mode':mode.value})[:20]
    return SafeModeAssessment(dec,mode,tuple(reasons),req.request_id,req.incident_id,tuple(active),tuple(cats),replay,receipt_id,
        network,external,auto,readonly,local,reg.registry_fingerprint,fingerprint(policy),fingerprint(req))

def evaluate_prepared(req:SafeModeRequest,policy:SafeModePolicy,reg:PreparedSafetyRegistry,*,now:int)->SafeModeAssessment:
    try:
        policy.validate(now); req.validate()
    except ValueError as e:
        return SafeModeAssessment(ControlDecision.HOLD,SafeMode.NORMAL,(f'INVALID_INPUT:{e}',),getattr(req,'request_id',''),getattr(req,'incident_id',''),(),(),False,'',False,False,False,False,False,getattr(reg,'registry_fingerprint',''),fingerprint(policy),fingerprint(req))
    if reg.registry_fingerprint!=registry_fingerprint(reg.signals,reg.receipts): return _assess(ControlDecision.HOLD,SafeMode.NORMAL,req,policy,reg,('PREPARED_REGISTRY_FINGERPRINT_MISMATCH',))
    if reg.policy_fingerprint!=fingerprint(policy): return _assess(ControlDecision.HOLD,SafeMode.NORMAL,req,policy,reg,('PREPARED_POLICY_FINGERPRINT_MISMATCH',))
    if req.expected_policy_id!=policy.policy_id: return _assess(ControlDecision.HOLD,SafeMode.NORMAL,req,policy,reg,('POLICY_ID_MISMATCH',))
    if req.expected_policy_version!=policy.version: return _assess(ControlDecision.HOLD,SafeMode.NORMAL,req,policy,reg,('POLICY_VERSION_MISMATCH',))
    if req.expected_authority_epoch!=policy.authority_epoch: return _assess(ControlDecision.HOLD,SafeMode.NORMAL,req,policy,reg,('AUTHORITY_EPOCH_MISMATCH',))
    # Replay protection receipt state is evidence only; matching a receipt blocks reuse but never proves prior success.
    for r in reg.receipts:
        if r.nonce!=req.nonce: continue
        if r.revoked or not r.verified or r.evidence_binding!=req.evidence_binding: continue
        if r.issued_at>now or now-r.issued_at>policy.max_receipt_age_seconds: continue
        return _assess(ControlDecision.DENY,r.mode_candidate,req,policy,reg,('REPLAY_NONCE_ALREADY_USED',r.receipt_id),(),(),True)
    active=[]
    for s in reg.signals:
        if s.incident_id!=req.incident_id: continue
        if s.revoked or not s.verified: continue
        if policy.require_independent_signal and not s.independent: continue
        if s.evidence_binding!=req.evidence_binding: continue
        if s.observed_at>now or now-s.observed_at>policy.max_signal_age_seconds: continue
        active.append(s)
    if not active: return _assess(ControlDecision.HOLD,SafeMode.NORMAL,req,policy,reg,('NO_ACTIVE_INDEPENDENT_SIGNAL',))
    maxsev=max(_SEVERITY[x.severity] for x in active); cats=tuple(sorted(set().union(*(x.categories for x in active))))
    if maxsev>=4: mode=SafeMode.OFFLINE_SAFE; dec=ControlDecision.ALLOW; why=['CRITICAL_SIGNAL_OFFLINE_SAFE_CANDIDATE']
    elif maxsev>=3:
        mode=SafeMode.LOCAL_ONLY if any(c in cats for c in ('NETWORK_ANOMALY','DEPENDENCY_OUTAGE','AUTHORITY_ANOMALY')) else SafeMode.READ_ONLY
        dec=ControlDecision.ALLOW; why=['HIGH_SIGNAL_SAFE_MODE_CANDIDATE']
    elif maxsev==2: mode=SafeMode.DEGRADED; dec=ControlDecision.HUMAN_APPROVAL; why=['MEDIUM_SIGNAL_DEGRADED_RECONFIRMATION']
    else: return _assess(ControlDecision.HOLD,SafeMode.NORMAL,req,policy,reg,('LOW_SIGNAL_NO_EMERGENCY_TRANSITION',),[x.signal_id for x in active],cats)
    temp=_assess(dec,mode,req,policy,reg,why,[x.signal_id for x in active],cats)
    conflicts=[]
    if req.network_required and temp.network_disabled_candidate: conflicts.append('NETWORK_REQUIRED_BUT_DISABLED_CANDIDATE')
    if req.external_tool_required and temp.external_tools_disabled_candidate: conflicts.append('EXTERNAL_TOOL_REQUIRED_BUT_DISABLED_CANDIDATE')
    if req.write_required and temp.read_only_candidate: conflicts.append('WRITE_REQUIRED_BUT_READ_ONLY_CANDIDATE')
    if req.automation_required and temp.auto_execution_disabled_candidate: conflicts.append('AUTOMATION_REQUIRED_BUT_DISABLED_CANDIDATE')
    if conflicts: return _assess(ControlDecision.DENY,mode,req,policy,reg,tuple(conflicts),[x.signal_id for x in active],cats)
    return temp

def evaluate(req,policy,signals,receipts,*,now:int)->SafeModeAssessment:
    try: reg=prepare_registry(policy,signals,receipts,now=now)
    except ValueError as e:
        return SafeModeAssessment(ControlDecision.HOLD,SafeMode.NORMAL,(f'INVALID_REGISTRY:{e}',),getattr(req,'request_id',''),getattr(req,'incident_id',''),(),(),False,'',False,False,False,False,False,'',fingerprint(policy),fingerprint(req))
    return evaluate_prepared(req,policy,reg,now=now)

def make_registry_delta(base_signals,base_receipts,target_signals,target_receipts)->SafetyRegistryDelta:
    def diff(base,target,key):
        b={key(x):x for x in base}; t={key(x):x for x in target}
        ch=tuple(sorted((x for k,x in t.items() if k in b and fingerprint(x)!=fingerprint(b[k])),key=key))
        rm=tuple(sorted(k for k in b if k not in t)); ad=tuple(sorted((x for k,x in t.items() if k not in b),key=key)); return ch,rm,ad
    cs,rs,ads=diff(_signals(base_signals),_signals(target_signals),lambda x:x.signal_id)
    cr,rr,adr=diff(_receipts(base_receipts),_receipts(target_receipts),lambda x:x.receipt_id)
    return SafetyRegistryDelta(registry_fingerprint(base_signals,base_receipts),registry_fingerprint(target_signals,target_receipts),cs,rs,ads,cr,rr,adr)

def apply_registry_delta(base_signals,base_receipts,delta:SafetyRegistryDelta):
    if registry_fingerprint(base_signals,base_receipts)!=delta.base_fingerprint: raise ValueError('delta base fingerprint mismatch')
    def apply(base,changed,removed,added,key):
        items={key(x):x for x in base}
        for k in removed:
            if k not in items: raise ValueError('invalid removal')
            del items[k]
        for x in changed:
            if key(x) not in items: raise ValueError('invalid change')
            items[key(x)]=x
        for x in added:
            if key(x) in items: raise ValueError('invalid add')
            items[key(x)]=x
        return tuple(sorted(items.values(),key=key))
    ss=apply(_signals(base_signals),delta.changed_signals,delta.removed_signal_ids,delta.added_signals,lambda x:x.signal_id)
    rs=apply(_receipts(base_receipts),delta.changed_receipts,delta.removed_receipt_ids,delta.added_receipts,lambda x:x.receipt_id)
    if registry_fingerprint(ss,rs)!=delta.target_fingerprint: raise ValueError('delta target fingerprint mismatch')
    return ss,rs

def plan_registry_sync(signals,receipts,remote_signal_fps:Mapping[str,str],remote_receipt_fps:Mapping[str,str])->RegistrySyncPlan:
    ss=_signals(signals); rs=_receipts(receipts)
    sids=tuple(x.signal_id for x in ss if remote_signal_fps.get(x.signal_id)!=fingerprint(x))
    rids=tuple(x.receipt_id for x in rs if remote_receipt_fps.get(x.receipt_id)!=fingerprint(x))
    sm={x.signal_id:x for x in ss}; rm={x.receipt_id:x for x in rs}
    selected={'signals':[sm[k] for k in sids],'receipts':[rm[k] for k in rids]}; full={'signals':ss,'receipts':rs}
    meta=len(canonical_json(selected).encode()); fullb=len(canonical_json(full).encode())
    return RegistrySyncPlan(sids,rids,meta,fullb,fullb>0 and meta/fullb>=0.8)

def assessment_digest(a:SafeModeAssessment)->str: return fingerprint(a)

def default_policy(now:int)->SafeModePolicy:
    return SafeModePolicy('SAFE-MODE-057','1',1,now-100,now+10000,1800,86400,True,False)
def default_request(now:int)->SafeModeRequest:
    return SafeModeRequest('REQ-057','INC-057','MODE_PLAN',SafeMode.NORMAL,'SAFE-MODE-057','1',1,'BIND-057','NONCE-057-001')
def default_signals(now:int):
    return (IncidentSignal('SIG-057','INC-057','HIGH',frozenset({'NETWORK_ANOMALY'}),now-10,True,True,'BIND-057',False),)
def default_receipts(now:int):
    return ()
