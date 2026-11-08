"""NOEPIN AL 092 — Bayesian Uncertainty Fusion — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Pure uncertainty-fusion control algorithm. It combines priors, evidence likelihoods,
source reliability, dependency discounting and risk into posterior confidence and
control candidates. It never promotes cached confidence to Truth/Authority, grants
permission, executes an action, commits/publishes state, writes externally, proves
safety, or proves action success.

Canonical identity: NOEPIN-AL-092
DCSR level: LIMITED INTEGRATION / 限定適用.
Provenance note: exact registered Origin GUID was not freshly reverified in this
completion session and is intentionally not guessed or regenerated.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str,Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class RiskLevel(str,Enum):
    LOW='LOW'; MEDIUM='MEDIUM'; HIGH='HIGH'; CRITICAL='CRITICAL'

@dataclass(frozen=True)
class FusionRequest:
    request_id:str; target_hypothesis_id:str; risk:RiskLevel; decision_time:int
    observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class Hypothesis:
    hypothesis_id:str; prior:float; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class SourceReliability:
    source_id:str; reliability:float; observed:bool; source_version:str
    source_fingerprint:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id:str; source_id:str; likelihoods:tuple[tuple[str,float],...]
    dependency_group:str; model_known:bool; observed:bool; evidence_fingerprint:str
    source_version:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class FusionPolicy:
    allow_threshold:float; deny_threshold:float
    max_interval_low:float; max_interval_medium:float; max_interval_high:float; max_interval_critical:float
    unknown_model_weight:float; dependency_discount_strength:float; min_source_reliability:float
    binding:str; state_epoch:str; revoked:bool=False
@dataclass(frozen=True)
class FusionResult:
    decision:Decision; reasons:tuple[str,...]; posterior:tuple[tuple[str,float],...]
    target_posterior:float; credible_interval:tuple[float,float]; interval_width:float
    decision_confidence:float; effective_evidence_weight:float; dependency_penalty:float
    unknown_model_count:int; source_reliability_mean:float
    next_gate_candidate:bool; refutation_candidate:bool; reevaluation_candidate:bool
    permission_granted:bool=False; action_executed:bool=False; plan_committed:bool=False
    atomic_publish_executed:bool=False; external_write_performed:bool=False
    world_truth_proven:bool=False; authority_promoted:bool=False; safety_proven:bool=False
    action_success:bool=False
@dataclass(frozen=True)
class PreparedFusionState:
    request:FusionRequest; hypotheses:tuple[Hypothesis,...]; evidence:tuple[EvidenceRecord,...]
    sources:tuple[SourceReliability,...]; policy:FusionPolicy
    record_fingerprints:tuple[tuple[str,str],...]; context_fingerprint:str
    dependency_fingerprint:str; calibration_fingerprint:str; registry_fingerprint:str
    precomputed_result:FusionResult; binding:str; state_epoch:str
@dataclass(frozen=True)
class FusionStateDelta:
    base_fingerprint:str; target_fingerprint:str
    changed_hypotheses:tuple[Hypothesis,...]; removed_hypothesis_ids:tuple[str,...]
    changed_evidence:tuple[EvidenceRecord,...]; removed_evidence_ids:tuple[str,...]
    changed_sources:tuple[SourceReliability,...]; removed_source_ids:tuple[str,...]
    target_request:FusionRequest|None; target_policy:FusionPolicy|None
    binding:str; state_epoch:str
@dataclass(frozen=True)
class FusionSyncPlan:
    missing_or_changed_record_ids:tuple[str,...]; metadata_bytes_required:int; full_resend_required:bool

def _cv(x):
    if isinstance(x,Enum): return x.value
    if hasattr(x,'__dataclass_fields__'): return {k:_cv(getattr(x,k)) for k in x.__dataclass_fields__}
    if isinstance(x,tuple): return [_cv(v) for v in x]
    if isinstance(x,list): return [_cv(v) for v in x]
    if isinstance(x,dict): return {str(k):_cv(x[k]) for k in sorted(x)}
    return x
def _canon(x)->bytes: return json.dumps(_cv(x),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def _fp(x)->str: return sha256(_canon(x)).hexdigest()
def _clamp(x,lo=0.0,hi=1.0): return lo if x<lo else hi if x>hi else x

def _hold(reason,posterior=(),target=0.0,interval=(0.0,1.0),weight=0.0,dep=0.0,unknown=0,rel=0.0):
    return FusionResult(Decision.HOLD,(reason,),tuple(posterior),target,interval,interval[1]-interval[0],0.0,weight,dep,unknown,rel,False,False,True)

def _validate(req,hypotheses,evidence,sources,policy):
    if policy.revoked: return 'POLICY_REVOKED'
    if req.binding!=policy.binding or req.state_epoch!=policy.state_epoch: return 'REQUEST_SCOPE_MISMATCH'
    if not req.observed or not req.request_id or not req.target_hypothesis_id: return 'REQUEST_UNOBSERVED_OR_INVALID'
    vals=[policy.allow_threshold,policy.deny_threshold,policy.max_interval_low,policy.max_interval_medium,policy.max_interval_high,policy.max_interval_critical,policy.unknown_model_weight,policy.dependency_discount_strength,policy.min_source_reliability]
    if any(not isinstance(v,(int,float)) or not math.isfinite(v) for v in vals): return 'INVALID_POLICY_NUMBER'
    if not (0<policy.deny_threshold<policy.allow_threshold<1): return 'INVALID_POLICY_THRESHOLDS'
    if not (0<policy.unknown_model_weight<=1 and 0<=policy.dependency_discount_strength<=1 and 0<=policy.min_source_reliability<=1): return 'INVALID_POLICY_WEIGHTS'
    hids=[h.hypothesis_id for h in hypotheses]
    if len(hids)<2 or len(hids)!=len(set(hids)): return 'HYPOTHESIS_SET_INVALID'
    if req.target_hypothesis_id not in hids: return 'TARGET_HYPOTHESIS_MISSING'
    ps=0.0
    for h in hypotheses:
        if not h.observed or h.binding!=policy.binding or h.state_epoch!=policy.state_epoch: return 'HYPOTHESIS_SCOPE_OR_OBSERVATION_INVALID'
        if not math.isfinite(h.prior) or h.prior<=0: return 'INVALID_PRIOR'
        ps+=h.prior
    if ps<=0: return 'INVALID_PRIOR_TOTAL'
    sids=[s.source_id for s in sources]
    if len(sids)!=len(set(sids)): return 'DUPLICATE_SOURCE_ID'
    sm={s.source_id:s for s in sources}
    for s in sources:
        if not s.observed or s.binding!=policy.binding or s.state_epoch!=policy.state_epoch: return 'SOURCE_SCOPE_OR_OBSERVATION_INVALID'
        if not s.source_version or not s.source_fingerprint or not math.isfinite(s.reliability) or not (0<=s.reliability<=1): return 'SOURCE_INVALID'
    eids=[e.evidence_id for e in evidence]
    if not eids or len(eids)!=len(set(eids)): return 'EVIDENCE_SET_INVALID'
    for e in evidence:
        if not e.observed or e.binding!=policy.binding or e.state_epoch!=policy.state_epoch: return 'EVIDENCE_SCOPE_OR_OBSERVATION_INVALID'
        if e.source_id not in sm: return 'EVIDENCE_SOURCE_MISSING'
        if e.source_version!=sm[e.source_id].source_version: return 'SOURCE_VERSION_MISMATCH'
        if not e.evidence_fingerprint: return 'EVIDENCE_FINGERPRINT_MISSING'
        lm=dict(e.likelihoods)
        if set(lm)!=set(hids): return 'LIKELIHOOD_COVERAGE_INVALID'
        for v in lm.values():
            if not math.isfinite(v) or not (0<v<=1): return 'LIKELIHOOD_INVALID'
    return None

def evaluate(req:FusionRequest,hypotheses:tuple[Hypothesis,...],evidence:tuple[EvidenceRecord,...],sources:tuple[SourceReliability,...],policy:FusionPolicy)->FusionResult:
    hypotheses=tuple(sorted(hypotheses,key=lambda x:x.hypothesis_id)); evidence=tuple(sorted(evidence,key=lambda x:x.evidence_id)); sources=tuple(sorted(sources,key=lambda x:x.source_id))
    err=_validate(req,hypotheses,evidence,sources,policy)
    if err: return _hold(err)
    priors={h.hypothesis_id:h.prior for h in hypotheses}; total=sum(priors.values()); priors={k:v/total for k,v in priors.items()}
    sm={s.source_id:s for s in sources}
    group_counts={}
    for e in evidence: group_counts[e.dependency_group]=group_counts.get(e.dependency_group,0)+1
    logs={hid:math.log(max(p,1e-300)) for hid,p in priors.items()}
    effective=0.0; unknown=0; rels=[]; dep_discount_total=0.0
    for e in evidence:
        s=sm[e.source_id]; rel=max(policy.min_source_reliability,s.reliability); rels.append(s.reliability)
        dep_factor=1.0/(1.0+policy.dependency_discount_strength*max(0,group_counts[e.dependency_group]-1))
        model_factor=1.0 if e.model_known else policy.unknown_model_weight
        if not e.model_known: unknown+=1
        w=rel*dep_factor*model_factor; effective+=w; dep_discount_total+=(1.0-dep_factor)
        lm=dict(e.likelihoods)
        for hid in logs: logs[hid]+=w*math.log(max(lm[hid],1e-300))
    m=max(logs.values()); ex={k:math.exp(v-m) for k,v in logs.items()}; z=sum(ex.values()); post={k:v/z for k,v in ex.items()}
    target=post[req.target_hypothesis_id]
    n=max(1,len(evidence)); dep_penalty=dep_discount_total/n; unknown_ratio=unknown/n
    half=_clamp(0.34/math.sqrt(1.0+effective)+0.10*dep_penalty+0.08*unknown_ratio,0.02,0.49)
    interval=(_clamp(target-half),_clamp(target+half)); width=interval[1]-interval[0]
    confidence=_clamp(target*(1.0-width)*(1.0-0.35*unknown_ratio)*(1.0-0.25*dep_penalty))
    posterior=tuple(sorted(post.items()))
    relmean=sum(rels)/len(rels)
    maxwidth={RiskLevel.LOW:policy.max_interval_low,RiskLevel.MEDIUM:policy.max_interval_medium,RiskLevel.HIGH:policy.max_interval_high,RiskLevel.CRITICAL:policy.max_interval_critical}[req.risk]
    if req.risk in (RiskLevel.HIGH,RiskLevel.CRITICAL) and unknown>0:
        return _hold('UNKNOWN_MODEL_HIGH_RISK',posterior,target,interval,effective,dep_penalty,unknown,relmean)
    if width>maxwidth:
        return _hold('CREDIBLE_INTERVAL_TOO_WIDE',posterior,target,interval,effective,dep_penalty,unknown,relmean)
    if interval[1] <= policy.deny_threshold or target <= policy.deny_threshold:
        return FusionResult(Decision.DENY,('REFUTATION_EVIDENCE_DOMINANT',),posterior,target,interval,width,confidence,effective,dep_penalty,unknown,relmean,False,True,False)
    if interval[0] >= policy.allow_threshold:
        return FusionResult(Decision.ALLOW,('POSTERIOR_CONFIDENCE_SUFFICIENT',),posterior,target,interval,width,confidence,effective,dep_penalty,unknown,relmean,True,False,False)
    return FusionResult(Decision.HOLD,('POSTERIOR_NOT_DECISIVE',),posterior,target,interval,width,confidence,effective,dep_penalty,unknown,relmean,False,False,True)

def default_request(): return FusionRequest('REQ-92','H-SAFE',RiskLevel.LOW,1_800_000_000,True,'BUF-BIND','STATE-EPOCH-1')
def default_policy(): return FusionPolicy(0.62,0.25,0.50,0.42,0.24,0.18,0.25,0.75,0.05,'BUF-BIND','STATE-EPOCH-1')
def default_hypotheses():
    p=default_policy(); return (Hypothesis('H-SAFE',0.5,True,p.binding,p.state_epoch),Hypothesis('H-UNSAFE',0.5,True,p.binding,p.state_epoch))
def default_sources():
    p=default_policy(); return (SourceReliability('SRC-A',0.95,True,'V1','SRC-A-FP',p.binding,p.state_epoch),SourceReliability('SRC-B',0.90,True,'V1','SRC-B-FP',p.binding,p.state_epoch))
def default_evidence():
    p=default_policy(); return (
      EvidenceRecord('E-A','SRC-A',( ('H-SAFE',0.96),('H-UNSAFE',0.04) ),'G-A',True,True,'E-A-FP','V1',p.binding,p.state_epoch),
      EvidenceRecord('E-B','SRC-B',( ('H-SAFE',0.92),('H-UNSAFE',0.08) ),'G-B',True,True,'E-B-FP','V1',p.binding,p.state_epoch),
      EvidenceRecord('E-C','SRC-A',( ('H-SAFE',0.88),('H-UNSAFE',0.12) ),'G-C',True,True,'E-C-FP','V1',p.binding,p.state_epoch),
      EvidenceRecord('E-D','SRC-B',( ('H-SAFE',0.90),('H-UNSAFE',0.10) ),'G-D',True,True,'E-D-FP','V1',p.binding,p.state_epoch),
    )
def default_evaluation(): return evaluate(default_request(),default_hypotheses(),default_evidence(),default_sources(),default_policy())

def _canon_sets(h,e,s): return tuple(sorted(h,key=lambda x:x.hypothesis_id)),tuple(sorted(e,key=lambda x:x.evidence_id)),tuple(sorted(s,key=lambda x:x.source_id))
def _record_fps(h,e,s):
    rows=[]
    for x in h: rows.append((f'HYP:{x.hypothesis_id}',_fp(x)))
    for x in e: rows.append((f'EVID:{x.evidence_id}',_fp(x)))
    for x in s: rows.append((f'SRC:{x.source_id}',_fp(x)))
    return tuple(sorted(rows))
def prepare_state(req,hypotheses,evidence,sources,policy,*,binding,state_epoch):
    h,e,s=_canon_sets(hypotheses,evidence,sources); r=evaluate(req,h,e,s,policy); rec=_record_fps(h,e,s)
    context=_fp((req,h)); dep=_fp((e,s)); cal=_fp((policy.allow_threshold,policy.deny_threshold,policy.max_interval_low,policy.max_interval_medium,policy.max_interval_high,policy.max_interval_critical,policy.unknown_model_weight,policy.dependency_discount_strength,policy.min_source_reliability)); reg=_fp(rec)
    return PreparedFusionState(req,h,e,s,policy,rec,context,dep,cal,reg,r,binding,state_epoch)
def validate_prepared_integrity(st):
    if st.binding!=st.policy.binding or st.state_epoch!=st.policy.state_epoch: return False
    h,e,s=_canon_sets(st.hypotheses,st.evidence,st.sources); rec=_record_fps(h,e,s)
    return rec==st.record_fingerprints and st.context_fingerprint==_fp((st.request,h)) and st.dependency_fingerprint==_fp((e,s)) and st.calibration_fingerprint==_fp((st.policy.allow_threshold,st.policy.deny_threshold,st.policy.max_interval_low,st.policy.max_interval_medium,st.policy.max_interval_high,st.policy.max_interval_critical,st.policy.unknown_model_weight,st.policy.dependency_discount_strength,st.policy.min_source_reliability)) and st.registry_fingerprint==_fp(rec) and st.precomputed_result==evaluate(st.request,h,e,s,st.policy)
def evaluate_prepared(st,*,current_context_fingerprint,current_dependency_fingerprint,current_calibration_fingerprint,current_registry_fingerprint,prepared_integrity_validated):
    if not prepared_integrity_validated: return _hold('PREPARED_INTEGRITY_NOT_VALIDATED')
    if current_context_fingerprint!=st.context_fingerprint: return _hold('CONTEXT_FINGERPRINT_MISMATCH')
    if current_dependency_fingerprint!=st.dependency_fingerprint: return _hold('DEPENDENCY_FINGERPRINT_MISMATCH')
    if current_calibration_fingerprint!=st.calibration_fingerprint: return _hold('CALIBRATION_FINGERPRINT_MISMATCH')
    if current_registry_fingerprint!=st.registry_fingerprint: return _hold('REGISTRY_FINGERPRINT_MISMATCH')
    return st.precomputed_result

def _diff(base,target,prefix,key):
    bm={key(x):x for x in base}; tm={key(x):x for x in target}
    changed=tuple(tm[k] for k in sorted(tm) if k not in bm or _fp(tm[k])!=_fp(bm[k])); removed=tuple(sorted(k for k in bm if k not in tm)); return changed,removed
def make_delta(base,target):
    ch,rm=_diff(base.hypotheses,target.hypotheses,'HYP',lambda x:x.hypothesis_id); ce,re=_diff(base.evidence,target.evidence,'EVID',lambda x:x.evidence_id); cs,rs=_diff(base.sources,target.sources,'SRC',lambda x:x.source_id)
    return FusionStateDelta(base.registry_fingerprint,target.registry_fingerprint,ch,rm,ce,re,cs,rs,None if base.request==target.request else target.request,None if base.policy==target.policy else target.policy,target.binding,target.state_epoch)
def apply_delta(base,delta):
    if base.registry_fingerprint!=delta.base_fingerprint: raise ValueError('BASE_FINGERPRINT_MISMATCH')
    hm={x.hypothesis_id:x for x in base.hypotheses}; em={x.evidence_id:x for x in base.evidence}; sm={x.source_id:x for x in base.sources}
    for k in delta.removed_hypothesis_ids: hm.pop(k,None)
    for x in delta.changed_hypotheses: hm[x.hypothesis_id]=x
    for k in delta.removed_evidence_ids: em.pop(k,None)
    for x in delta.changed_evidence: em[x.evidence_id]=x
    for k in delta.removed_source_ids: sm.pop(k,None)
    for x in delta.changed_sources: sm[x.source_id]=x
    out=prepare_state(delta.target_request or base.request,tuple(hm.values()),tuple(em.values()),tuple(sm.values()),delta.target_policy or base.policy,binding=delta.binding,state_epoch=delta.state_epoch)
    if out.registry_fingerprint!=delta.target_fingerprint: raise ValueError('TARGET_FINGERPRINT_MISMATCH')
    return out
def missing_only_sync_plan(target,known_record_fingerprints:dict[str,str]):
    miss=tuple(sorted(k for k,v in target.record_fingerprints if known_record_fingerprints.get(k)!=v)); metadata=len(_canon(miss)); full= len(miss)>max(1000,int(len(target.record_fingerprints)*0.75)); return FusionSyncPlan(miss,metadata,full)
def full_registry_bytes(st): return len(_canon({'request':st.request,'hypotheses':st.hypotheses,'evidence':st.evidence,'sources':st.sources,'policy':st.policy}))
def delta_bytes(delta): return len(_canon(delta))
