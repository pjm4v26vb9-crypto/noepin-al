"""NOEPIN AL 055 — Human-Target Social Engineering Detection.

Pure control-plane evaluator for structured interaction-risk evidence. It does not
infer private intent or execute approvals/actions. It produces deterministic
candidate decisions from caller-supplied, bound evidence.

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
class SignalLevel(str, Enum):
    NONE='NONE'; LOW='LOW'; MEDIUM='MEDIUM'; HIGH='HIGH'; CRITICAL='CRITICAL'

_LEVEL={SignalLevel.NONE:0,SignalLevel.LOW:1,SignalLevel.MEDIUM:2,SignalLevel.HIGH:3,SignalLevel.CRITICAL:4}

@dataclass(frozen=True)
class SocialEngineeringPolicy:
    policy_id:str; version:str; authority_epoch:int; issued_at:int; expires_at:int
    max_evidence_age_seconds:int; review_score:int; deny_score:int; repeated_ask_limit:int
    critical_signal_names:FrozenSet[str]; high_risk_action_types:FrozenSet[str]
    require_independent_observer:bool=True; require_clear_explanation:bool=True
    require_alternatives_for_high_risk:bool=True; revoked:bool=False
    def validate(self, now:int)->None:
        if not self.policy_id or not self.version or self.authority_epoch<1: raise ValueError('policy identity invalid')
        if self.issued_at<0 or self.expires_at<=self.issued_at or not self.issued_at<=now<self.expires_at: raise ValueError('policy not current')
        if self.max_evidence_age_seconds<1 or self.review_score<1 or self.deny_score<=self.review_score or self.repeated_ask_limit<1: raise ValueError('policy limits invalid')
        if not self.critical_signal_names or not self.high_risk_action_types: raise ValueError('policy sets required')

@dataclass(frozen=True)
class InteractionEvidence:
    evidence_id:str; interaction_id:str; observer_id:str; independent_observer:bool; verified:bool
    observed_at:int; urgency:SignalLevel; secrecy:SignalLevel; authority_pressure:SignalLevel
    fear_pressure:SignalLevel; scarcity_pressure:SignalLevel; reciprocity_pressure:SignalLevel
    impersonation:SignalLevel; bypass_request:SignalLevel; credential_request:SignalLevel
    repeated_asks:int; continued_after_decline:bool; explanation_clear:bool; alternatives_offered:bool
    consent_recheck_offered:bool; evidence_binding:str; revoked:bool=False
    def validate(self)->None:
        if not self.evidence_id or not self.interaction_id or not self.observer_id or not self.evidence_binding: raise ValueError('evidence identity required')
        if self.observed_at<0 or self.repeated_asks<0: raise ValueError('evidence metrics invalid')

@dataclass(frozen=True)
class ApprovalContext:
    context_id:str; interaction_id:str; action_type:str; risk_label:str
    current_user_decision:str; requested_scope:str; explanation_present:bool
    expected_policy_id:str; expected_policy_version:str; expected_authority_epoch:int
    evidence_binding:str
    def validate(self)->None:
        if not self.context_id or not self.interaction_id or not self.action_type or not self.risk_label or not self.current_user_decision or not self.requested_scope: raise ValueError('context identity required')
        if not self.expected_policy_id or not self.expected_policy_version or self.expected_authority_epoch<1 or not self.evidence_binding: raise ValueError('context metadata invalid')

@dataclass(frozen=True)
class PreparedInteractionRegistry:
    registry_fingerprint:str; policy_fingerprint:str; evidence:Tuple[InteractionEvidence,...]
    evidence_fingerprints:Mapping[str,str]; interaction_index:Mapping[str,Tuple[str,...]]

@dataclass(frozen=True)
class InteractionRegistryDelta:
    base_fingerprint:str; target_fingerprint:str
    changed_evidence:Tuple[InteractionEvidence,...]; removed_evidence_ids:Tuple[str,...]; added_evidence:Tuple[InteractionEvidence,...]

@dataclass(frozen=True)
class RegistrySyncPlan:
    missing_or_changed_evidence_ids:Tuple[str,...]; metadata_bytes_required:int; full_metadata_bytes:int
    full_resend_required:bool; permission_granted:bool=False; approval_execution_authorized:bool=False
    user_decision_override_authorized:bool=False; message_send_authorized:bool=False

@dataclass(frozen=True)
class SocialEngineeringAssessment:
    decision:ControlDecision; reasons:Tuple[str,...]; interaction_id:str; context_id:str
    valid_evidence_ids:Tuple[str,...]; score:int; signal_names:Tuple[str,...]
    manipulation_risk_candidate:bool; human_reconfirmation_candidate:bool
    registry_fingerprint:str; policy_fingerprint:str; context_fingerprint:str
    permission_granted:bool=False; human_approval_completed:bool=False; approval_executed:bool=False
    user_decision_overridden:bool=False; message_sent:bool=False; intent_truth_proven:bool=False
    persuasion_safe_proven:bool=False; action_success:bool=False

def _canonical(v:Any)->Any:
    if isinstance(v,Enum): return v.value
    if is_dataclass(v): return {f.name:_canonical(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v,Mapping): return {str(k):_canonical(x) for k,x in sorted(v.items(),key=lambda kv:str(kv[0]))}
    if isinstance(v,(set,frozenset)): return sorted((_canonical(x) for x in v),key=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')))
    if isinstance(v,(tuple,list)): return [_canonical(x) for x in v]
    return v

def canonical_json(v:Any)->str: return json.dumps(_canonical(v),ensure_ascii=False,sort_keys=True,separators=(',',':'))
def fingerprint(v:Any)->str: return sha256(canonical_json(v).encode()).hexdigest()
def _evidence(xs:Iterable[InteractionEvidence])->Tuple[InteractionEvidence,...]: return tuple(sorted(xs,key=lambda x:x.evidence_id))
def registry_fingerprint(xs:Iterable[InteractionEvidence])->str: return fingerprint(_evidence(xs))

def prepare_registry(policy:SocialEngineeringPolicy, evidence:Iterable[InteractionEvidence], *, now:int)->PreparedInteractionRegistry:
    policy.validate(now); es=_evidence(evidence)
    for x in es: x.validate()
    if len({x.evidence_id for x in es})!=len(es): raise ValueError('duplicate evidence id')
    idx={}
    for x in es: idx.setdefault(x.interaction_id,[]).append(x.evidence_id)
    return PreparedInteractionRegistry(registry_fingerprint(es),fingerprint(policy),es,{x.evidence_id:fingerprint(x) for x in es},{k:tuple(sorted(v)) for k,v in idx.items()})

def _assess(dec,ctx,policy,reg,reasons=(),ids=(),score=0,signals=(),risk=False,reconfirm=False):
    return SocialEngineeringAssessment(dec,tuple(reasons),ctx.interaction_id,ctx.context_id,tuple(ids),int(score),tuple(sorted(signals)),risk,reconfirm,reg.registry_fingerprint,fingerprint(policy),fingerprint(ctx))

def _signal_score(e:InteractionEvidence):
    vals={
      'URGENCY':e.urgency,'SECRECY':e.secrecy,'AUTHORITY_PRESSURE':e.authority_pressure,
      'FEAR_PRESSURE':e.fear_pressure,'SCARCITY_PRESSURE':e.scarcity_pressure,
      'RECIPROCITY_PRESSURE':e.reciprocity_pressure,'IMPERSONATION':e.impersonation,
      'BYPASS_REQUEST':e.bypass_request,'CREDENTIAL_REQUEST':e.credential_request,
    }
    weights={'URGENCY':2,'SECRECY':3,'AUTHORITY_PRESSURE':3,'FEAR_PRESSURE':3,'SCARCITY_PRESSURE':2,'RECIPROCITY_PRESSURE':1,'IMPERSONATION':5,'BYPASS_REQUEST':5,'CREDENTIAL_REQUEST':6}
    active=[]; score=0
    for name,level in vals.items():
        lv=_LEVEL[level]
        if lv>0: active.append(name); score += weights[name]*lv
    if e.continued_after_decline: active.append('CONTINUED_AFTER_DECLINE'); score+=8
    if e.repeated_asks>1: active.append('REPEATED_ASK'); score+=min(10,e.repeated_asks-1)*2
    if not e.explanation_clear: active.append('UNCLEAR_EXPLANATION'); score+=5
    if not e.alternatives_offered: active.append('NO_ALTERNATIVES'); score+=2
    if not e.consent_recheck_offered: active.append('NO_CONSENT_RECHECK'); score+=3
    return score,tuple(active)

def evaluate_prepared(ctx:ApprovalContext, policy:SocialEngineeringPolicy, reg:PreparedInteractionRegistry, *, now:int)->SocialEngineeringAssessment:
    try: ctx.validate(); policy.validate(now)
    except ValueError as e:
        return SocialEngineeringAssessment(ControlDecision.HOLD,(f'INVALID_INPUT:{e}',),getattr(ctx,'interaction_id',''),getattr(ctx,'context_id',''),(),0,(),False,False,getattr(reg,'registry_fingerprint',''),fingerprint(policy),fingerprint(ctx))
    if policy.revoked: return _assess(ControlDecision.HOLD,ctx,policy,reg,('POLICY_REVOKED',))
    if ctx.expected_policy_id!=policy.policy_id: return _assess(ControlDecision.HOLD,ctx,policy,reg,('POLICY_ID_MISMATCH',))
    if ctx.expected_policy_version!=policy.version: return _assess(ControlDecision.HOLD,ctx,policy,reg,('POLICY_VERSION_MISMATCH',))
    if ctx.expected_authority_epoch!=policy.authority_epoch: return _assess(ControlDecision.HOLD,ctx,policy,reg,('AUTHORITY_EPOCH_MISMATCH',))
    if reg.policy_fingerprint!=fingerprint(policy): return _assess(ControlDecision.HOLD,ctx,policy,reg,('PREPARED_POLICY_FINGERPRINT_MISMATCH',))
    if reg.registry_fingerprint!=registry_fingerprint(reg.evidence): return _assess(ControlDecision.HOLD,ctx,policy,reg,('PREPARED_REGISTRY_FINGERPRINT_MISMATCH',))
    byid={x.evidence_id:x for x in reg.evidence}
    ids=reg.interaction_index.get(ctx.interaction_id,())
    active=[]
    for eid in ids:
        e=byid[eid]
        if e.revoked or not e.verified: continue
        if policy.require_independent_observer and not e.independent_observer: continue
        if e.evidence_binding!=ctx.evidence_binding: continue
        if e.observed_at>now or now-e.observed_at>policy.max_evidence_age_seconds: continue
        active.append(e)
    if not active: return _assess(ControlDecision.HOLD,ctx,policy,reg,('INDEPENDENT_INTERACTION_EVIDENCE_REQUIRED',))
    total=0; signals=[]; reasons=[]
    critical=False
    for e in active:
        s,names=_signal_score(e); total=max(total,s); signals.extend(names)
        for name in names:
            level=None
            mapping={'URGENCY':e.urgency,'SECRECY':e.secrecy,'AUTHORITY_PRESSURE':e.authority_pressure,'FEAR_PRESSURE':e.fear_pressure,'SCARCITY_PRESSURE':e.scarcity_pressure,'RECIPROCITY_PRESSURE':e.reciprocity_pressure,'IMPERSONATION':e.impersonation,'BYPASS_REQUEST':e.bypass_request,'CREDENTIAL_REQUEST':e.credential_request}
            if name in mapping: level=mapping[name]
            if name in policy.critical_signal_names and level in (SignalLevel.HIGH,SignalLevel.CRITICAL): critical=True
        if e.repeated_asks>policy.repeated_ask_limit: critical=True; reasons.append('REPEATED_ASK_LIMIT_EXCEEDED')
    signals=tuple(sorted(set(signals)))
    high_action=ctx.action_type in policy.high_risk_action_types or ctx.risk_label.upper() in {'HIGH','CRITICAL'}
    if critical:
        reasons.append('CRITICAL_MANIPULATION_SIGNAL_CANDIDATE')
        return _assess(ControlDecision.DENY,ctx,policy,reg,reasons,[x.evidence_id for x in active],total,signals,True,True)
    if policy.require_clear_explanation and (not ctx.explanation_present or any(not e.explanation_clear for e in active)):
        reasons.append('CLEAR_APPROVAL_EXPLANATION_REQUIRED')
        return _assess(ControlDecision.HUMAN_APPROVAL,ctx,policy,reg,reasons,[x.evidence_id for x in active],total,signals,True,True)
    if high_action and policy.require_alternatives_for_high_risk and any(not e.alternatives_offered for e in active):
        reasons.append('HIGH_RISK_ALTERNATIVES_REQUIRED')
        return _assess(ControlDecision.HUMAN_APPROVAL,ctx,policy,reg,reasons,[x.evidence_id for x in active],total,signals,True,True)
    if ctx.current_user_decision.upper() in {'DECLINED','DENIED','NO'} and any(e.continued_after_decline for e in active):
        reasons.append('PRESSURE_AFTER_USER_DECLINE')
        return _assess(ControlDecision.DENY,ctx,policy,reg,reasons,[x.evidence_id for x in active],total,signals,True,True)
    if total>=policy.deny_score:
        reasons.append('MANIPULATION_SCORE_DENY_THRESHOLD')
        return _assess(ControlDecision.DENY,ctx,policy,reg,reasons,[x.evidence_id for x in active],total,signals,True,True)
    if total>=policy.review_score or high_action:
        reasons.append('HUMAN_RECONFIRMATION_REQUIRED')
        return _assess(ControlDecision.HUMAN_APPROVAL,ctx,policy,reg,reasons,[x.evidence_id for x in active],total,signals,total>0,True)
    return _assess(ControlDecision.ALLOW,ctx,policy,reg,('LOW_SIGNAL_CANDIDATE',),[x.evidence_id for x in active],total,signals,total>0,False)

def evaluate(ctx:ApprovalContext, policy:SocialEngineeringPolicy, evidence:Iterable[InteractionEvidence], *, now:int)->SocialEngineeringAssessment:
    try: reg=prepare_registry(policy,evidence,now=now)
    except ValueError as e:
        return SocialEngineeringAssessment(ControlDecision.HOLD,(f'INVALID_REGISTRY:{e}',),getattr(ctx,'interaction_id',''),getattr(ctx,'context_id',''),(),0,(),False,False,'',fingerprint(policy),fingerprint(ctx))
    return evaluate_prepared(ctx,policy,reg,now=now)

def make_registry_delta(base, target)->InteractionRegistryDelta:
    be={x.evidence_id:x for x in base}; te={x.evidence_id:x for x in target}
    ch=tuple(sorted((x for k,x in te.items() if k in be and fingerprint(x)!=fingerprint(be[k])),key=lambda x:x.evidence_id))
    rm=tuple(sorted(k for k in be if k not in te)); ad=tuple(sorted((x for k,x in te.items() if k not in be),key=lambda x:x.evidence_id))
    return InteractionRegistryDelta(registry_fingerprint(base),registry_fingerprint(target),ch,rm,ad)

def apply_registry_delta(base, delta:InteractionRegistryDelta):
    if registry_fingerprint(base)!=delta.base_fingerprint: raise ValueError('delta base fingerprint mismatch')
    items={x.evidence_id:x for x in base}
    for k in delta.removed_evidence_ids:
        if k not in items: raise ValueError('invalid evidence removal')
        del items[k]
    for x in delta.changed_evidence:
        if x.evidence_id not in items: raise ValueError('invalid evidence change')
        items[x.evidence_id]=x
    for x in delta.added_evidence:
        if x.evidence_id in items: raise ValueError('invalid evidence add')
        items[x.evidence_id]=x
    out=_evidence(items.values())
    if registry_fingerprint(out)!=delta.target_fingerprint: raise ValueError('delta target fingerprint mismatch')
    return out

def plan_registry_sync(evidence, remote_known:Mapping[str,str])->RegistrySyncPlan:
    es=_evidence(evidence); ids=tuple(x.evidence_id for x in es if remote_known.get(x.evidence_id)!=fingerprint(x)); mp={x.evidence_id:x for x in es}
    selected=[mp[k] for k in ids]; meta=len(canonical_json(selected).encode()); full=len(canonical_json(es).encode())
    return RegistrySyncPlan(ids,meta,full,full>0 and meta/full>=0.8)

def default_policy(now:int)->SocialEngineeringPolicy:
    return SocialEngineeringPolicy('SOCENG-055','1',1,now-100,now+10000,3600,12,26,3,frozenset({'IMPERSONATION','BYPASS_REQUEST','CREDENTIAL_REQUEST'}),frozenset({'GRANT_PERMISSION','SEND_FUNDS','SHARE_SECRET','DEPLOY','DELETE_DATA'}),True,True,True,False)
def default_context(now:int)->ApprovalContext:
    return ApprovalContext('CTX-055','INT-055','VIEW_INFO','LOW','UNDECIDED','LOCAL_READ_ONLY',True,'SOCENG-055','1',1,'BIND-055')
def default_evidence(now:int):
    return (InteractionEvidence('EVID-055','INT-055','MONITOR-055',True,True,now-20,SignalLevel.LOW,SignalLevel.NONE,SignalLevel.NONE,SignalLevel.NONE,SignalLevel.NONE,SignalLevel.NONE,SignalLevel.NONE,SignalLevel.NONE,SignalLevel.NONE,1,False,True,True,True,'BIND-055',False),)
