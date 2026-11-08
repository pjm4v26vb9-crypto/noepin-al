"""NOEPIN AL 068 — Evidence Sufficiency Stopper — Sequential Successor V2.

Creator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
Implementation / analysis / documentation support: AI-assisted using ChatGPT
License / Rights: NOT SPECIFIED

Pure algorithm/control-plane evaluator. It evaluates whether supplied evidence is sufficient for
an externally defined claim and action-risk level. It does not infer missing evidence, establish
world truth, grant permission, execute approval/action, send data, write evidence, or promote
action success.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, is_dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence

CREATOR = "NOEPIN / のえぴん"
AI_SUPPORT = "AI-assisted implementation / analysis / documentation support using ChatGPT"
LICENSE_RIGHTS = "NOT SPECIFIED"
CANONICAL_ID = "NOEPIN-AL-068"

class Decision(str, Enum):
    ALLOW="ALLOW"; DENY="DENY"; HOLD="HOLD"; HUMAN_APPROVAL="HUMAN_APPROVAL"

class Risk(str, Enum):
    LOW="LOW"; MEDIUM="MEDIUM"; HIGH="HIGH"; CRITICAL="CRITICAL"

class EvidenceKind(str, Enum):
    DIRECT="DIRECT"; INDIRECT="INDIRECT"

class EvidenceState(str, Enum):
    SUPPORTS="SUPPORTS"; CONTRADICTS="CONTRADICTS"; NEUTRAL="NEUTRAL"

@dataclass(frozen=True)
class ClaimSpec:
    claim_id: str
    binding: str
    verified: bool
    revoked: bool
    policy_id: str
    policy_version: str
    authority_epoch: str

@dataclass(frozen=True)
class SourceMetadata:
    source_id: str
    independence_group: str
    source_type: str
    binding: str
    verified: bool
    revoked: bool
    policy_id: str
    policy_version: str
    authority_epoch: str

@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    claim_id: str
    source_id: str
    kind: EvidenceKind
    state: EvidenceState
    confidence: float
    observed_at: int
    expires_at: int
    binding: str
    verified: bool
    revoked: bool
    policy_id: str
    policy_version: str
    authority_epoch: str

@dataclass(frozen=True)
class EvidenceRequest:
    request_id: str
    claim_id: str
    action_risk: Risk
    binding: str
    expected_policy_id: str
    expected_policy_version: str
    expected_authority_epoch: str
    created_at: int
    expires_at: int

@dataclass(frozen=True)
class EvidencePolicy:
    policy_id: str
    version: str
    authority_epoch: str
    valid_from: int
    expires_at: int
    revoked: bool
    max_request_age_seconds: int
    max_fresh_age_seconds: int
    max_acceptable_age_seconds: int
    stale_weight: float
    indirect_weight: float
    min_confidence: float
    low_required_score: float
    medium_required_score: float
    high_required_score: float
    critical_required_score: float
    low_independent_sources: int
    medium_independent_sources: int
    high_independent_sources: int
    critical_independent_sources: int
    low_direct_sources: int
    medium_direct_sources: int
    high_direct_sources: int
    critical_direct_sources: int
    critical_requires_human_approval: bool

@dataclass(frozen=True)
class PreparedEvidenceState:
    binding: str
    valid: bool
    validation_reasons: tuple[str,...]
    policy: EvidencePolicy
    policy_fingerprint: str
    registry_fingerprint: str
    claim_fingerprints: tuple[tuple[str,str],...]
    source_fingerprints: tuple[tuple[str,str],...]
    evidence_fingerprints: tuple[tuple[str,str],...]
    claims: tuple[ClaimSpec,...]
    sources: tuple[SourceMetadata,...]
    evidence: tuple[EvidenceRecord,...]
    claim_evidence_index: tuple[tuple[str,tuple[str,...]],...]
    generated_at: int

@dataclass(frozen=True)
class EvidenceRegistryDelta:
    base_fingerprint: str
    target_fingerprint: str
    changed_claims: tuple[ClaimSpec,...]
    removed_claim_ids: tuple[str,...]
    added_claims: tuple[ClaimSpec,...]
    changed_sources: tuple[SourceMetadata,...]
    removed_source_ids: tuple[str,...]
    added_sources: tuple[SourceMetadata,...]
    changed_evidence: tuple[EvidenceRecord,...]
    removed_evidence_ids: tuple[str,...]
    added_evidence: tuple[EvidenceRecord,...]

@dataclass(frozen=True)
class EvidenceSyncPlan:
    registry_fingerprint: str
    missing_or_changed_claim_ids: tuple[str,...]
    missing_or_changed_source_ids: tuple[str,...]
    missing_or_changed_evidence_ids: tuple[str,...]
    metadata_bytes_required: int
    full_bytes: int
    full_resend_required: bool
    permission_granted: bool=False
    truth_authorized: bool=False
    evidence_write_authorized: bool=False
    action_execution_authorized: bool=False
    action_success_authorized: bool=False

@dataclass(frozen=True)
class EvidenceResult:
    decision: Decision
    reasons: tuple[str,...]
    evidence_score: float
    required_score: float
    independent_source_count: int
    required_independent_sources: int
    direct_source_count: int
    required_direct_sources: int
    fresh_source_count: int
    stale_source_count: int
    duplicate_evidence_ids: tuple[str,...]
    excluded_evidence_ids: tuple[str,...]
    contradictory_evidence_ids: tuple[str,...]
    missing_requirements: tuple[str,...]
    next_gate_candidate: bool
    input_fingerprint: str
    permission_granted: bool=False
    truth_proven: bool=False
    evidence_written: bool=False
    approval_executed: bool=False
    data_sent: bool=False
    action_executed: bool=False
    safety_proven: bool=False
    action_success: bool=False


def _norm(v: Any) -> Any:
    if isinstance(v, Enum): return v.value
    if is_dataclass(v): return {k:_norm(x) for k,x in asdict(v).items()}
    if isinstance(v, dict): return {str(k):_norm(v[k]) for k in sorted(v,key=lambda x:str(x))}
    if isinstance(v,(tuple,list)): return [_norm(x) for x in v]
    if isinstance(v,(set,frozenset)): return [_norm(x) for x in sorted(v,key=lambda x:str(x))]
    return v

def canonical_json(v: Any) -> str:
    return json.dumps(_norm(v),sort_keys=True,separators=(",",":"),ensure_ascii=False)

def fingerprint(v: Any) -> str:
    return sha256(canonical_json(v).encode("utf-8")).hexdigest()

def _fps(items: Sequence[Any], key_fn) -> tuple[tuple[str,str],...]:
    return tuple(sorted((str(key_fn(x)),fingerprint(x)) for x in items))

def _registry_from_fps(binding: str, policy_fp: str, cfp, sfp, efp) -> str:
    return fingerprint({"binding":binding,"policy_fingerprint":policy_fp,"claim_fingerprints":tuple(sorted(cfp)),"source_fingerprints":tuple(sorted(sfp)),"evidence_fingerprints":tuple(sorted(efp))})

def registry_fingerprint(policy,claims,sources,evidence,binding: str) -> str:
    return _registry_from_fps(binding,fingerprint(policy),_fps(claims,lambda x:x.claim_id),_fps(sources,lambda x:x.source_id),_fps(evidence,lambda x:x.evidence_id))

def _unique_ids(items,key_fn) -> bool:
    ids=[key_fn(x) for x in items]; return len(ids)==len(set(ids))

def _policy_valid(p: EvidencePolicy, now: int) -> bool:
    return bool(p.policy_id and p.version and p.authority_epoch and not p.revoked and p.valid_from<=now<=p.expires_at and p.max_request_age_seconds>=0 and p.max_fresh_age_seconds>=0 and p.max_acceptable_age_seconds>=p.max_fresh_age_seconds and 0<=p.stale_weight<=1 and 0<=p.indirect_weight<=1 and 0<=p.min_confidence<=1)

def _record_common_valid(x, binding: str, p: EvidencePolicy) -> bool:
    return bool(x.verified and not x.revoked and x.binding==binding and x.policy_id==p.policy_id and x.policy_version==p.version and x.authority_epoch==p.authority_epoch)

def _risk_req(p: EvidencePolicy,r: Risk):
    if r==Risk.LOW: return p.low_required_score,p.low_independent_sources,p.low_direct_sources
    if r==Risk.MEDIUM: return p.medium_required_score,p.medium_independent_sources,p.medium_direct_sources
    if r==Risk.HIGH: return p.high_required_score,p.high_independent_sources,p.high_direct_sources
    return p.critical_required_score,p.critical_independent_sources,p.critical_direct_sources

def _index(claims: Sequence[ClaimSpec], evidence: Sequence[EvidenceRecord]):
    ids={c.claim_id for c in claims}; d={i:[] for i in ids}
    for e in evidence:
        if e.claim_id in d: d[e.claim_id].append(e.evidence_id)
    return tuple(sorted((k,tuple(sorted(v))) for k,v in d.items()))

def _validation(policy,claims,sources,evidence,binding: str,now: int) -> tuple[str,...]:
    r=[]
    if not binding: r.append("EMPTY_BINDING")
    if not _policy_valid(policy,now): r.append("INVALID_POLICY")
    if not _unique_ids(claims,lambda x:x.claim_id): r.append("DUPLICATE_CLAIM")
    if not _unique_ids(sources,lambda x:x.source_id): r.append("DUPLICATE_SOURCE")
    if not _unique_ids(evidence,lambda x:x.evidence_id): r.append("DUPLICATE_EVIDENCE")
    cids={x.claim_id for x in claims}; sids={x.source_id for x in sources}
    for c in claims:
        if not _record_common_valid(c,binding,policy): r.append(f"INVALID_CLAIM:{c.claim_id}")
    for s in sources:
        if not s.independence_group or not _record_common_valid(s,binding,policy): r.append(f"INVALID_SOURCE:{s.source_id}")
    for e in evidence:
        if e.claim_id not in cids: r.append(f"UNKNOWN_CLAIM:{e.evidence_id}")
        if e.source_id not in sids: r.append(f"UNKNOWN_SOURCE:{e.evidence_id}")
        if not (0<=e.confidence<=1) or not _record_common_valid(e,binding,policy): r.append(f"INVALID_EVIDENCE:{e.evidence_id}")
        if e.expires_at<e.observed_at: r.append(f"INVALID_EVIDENCE_TIME:{e.evidence_id}")
    return tuple(sorted(set(r)))

def prepare_state(policy,claims,sources,evidence,*,binding: str,now: int) -> PreparedEvidenceState:
    claims=tuple(claims); sources=tuple(sources); evidence=tuple(evidence)
    cfp=_fps(claims,lambda x:x.claim_id); sfp=_fps(sources,lambda x:x.source_id); efp=_fps(evidence,lambda x:x.evidence_id); pfp=fingerprint(policy)
    reasons=_validation(policy,claims,sources,evidence,binding,now)
    return PreparedEvidenceState(binding,not reasons,reasons,policy,pfp,_registry_from_fps(binding,pfp,cfp,sfp,efp),cfp,sfp,efp,claims,sources,evidence,_index(claims,evidence),now)

def validate_prepared_integrity(s: PreparedEvidenceState) -> bool:
    # One-time trust-boundary validation binds cached fingerprints to actual record bytes.
    if not s.valid: return False
    cfp=_fps(s.claims,lambda x:x.claim_id); sfp=_fps(s.sources,lambda x:x.source_id); efp=_fps(s.evidence,lambda x:x.evidence_id); pfp=fingerprint(s.policy)
    if cfp!=s.claim_fingerprints or sfp!=s.source_fingerprints or efp!=s.evidence_fingerprints or pfp!=s.policy_fingerprint: return False
    if _registry_from_fps(s.binding,pfp,cfp,sfp,efp)!=s.registry_fingerprint: return False
    if _index(s.claims,s.evidence)!=s.claim_evidence_index: return False
    return True

def _hold(reason: str, request: EvidenceRequest, reqs=(0.0,0,0)) -> EvidenceResult:
    rs,ri,rd=reqs
    return EvidenceResult(Decision.HOLD,(reason,),0.0,float(rs),0,int(ri),0,int(rd),0,0,(),(),(),("UNRESOLVED",),False,fingerprint(request))

def _evaluate_prepared_validated(request: EvidenceRequest,s: PreparedEvidenceState,*,now: int) -> EvidenceResult:
    p=s.policy; reqs=_risk_req(p,request.action_risk)
    if not s.valid: return _hold("PREPARED_STATE_INVALID",request,reqs)
    if request.binding!=s.binding: return _hold("BINDING_MISMATCH",request,reqs)
    if (request.expected_policy_id,request.expected_policy_version,request.expected_authority_epoch)!=(p.policy_id,p.version,p.authority_epoch): return _hold("POLICY_IDENTITY_MISMATCH",request,reqs)
    if not (request.created_at<=now<=request.expires_at) or now-request.created_at>p.max_request_age_seconds: return _hold("REQUEST_STALE_OR_EXPIRED",request,reqs)
    claims={x.claim_id:x for x in s.claims}; sources={x.source_id:x for x in s.sources}
    claim=claims.get(request.claim_id)
    if claim is None or not _record_common_valid(claim,s.binding,p): return _hold("CLAIM_INVALID_OR_UNKNOWN",request,reqs)
    selected=[e for e in s.evidence if e.claim_id==request.claim_id]
    if not selected: return _hold("NO_EVIDENCE",request,reqs)
    excluded=[]; contradict=[]; candidates=[]
    for e in selected:
        src=sources.get(e.source_id)
        if src is None or not _record_common_valid(src,s.binding,p) or not _record_common_valid(e,s.binding,p): excluded.append(e.evidence_id); continue
        age=now-e.observed_at
        if e.expires_at<now or age<0 or age>p.max_acceptable_age_seconds or e.confidence<p.min_confidence: excluded.append(e.evidence_id); continue
        if e.state==EvidenceState.NEUTRAL: excluded.append(e.evidence_id); continue
        if e.state==EvidenceState.CONTRADICTS: contradict.append(e.evidence_id); continue
        freshness=1.0 if age<=p.max_fresh_age_seconds else p.stale_weight
        kindw=1.0 if e.kind==EvidenceKind.DIRECT else p.indirect_weight
        score=e.confidence*freshness*kindw
        candidates.append((src.independence_group,e,score,age<=p.max_fresh_age_seconds))
    # Same independence group counts once: keep the strongest evidence only.
    best={}; duplicates=[]
    for group,e,score,fresh in sorted(candidates,key=lambda x:(x[0],-x[2],x[1].evidence_id)):
        old=best.get(group)
        if old is None: best[group]=(e,score,fresh)
        else: duplicates.append(e.evidence_id)
    evidence_score=sum(v[1] for v in best.values())
    independent=len(best)
    direct=sum(1 for e,_,_ in best.values() if e.kind==EvidenceKind.DIRECT)
    fresh=sum(1 for _,_,f in best.values() if f); stale=independent-fresh
    required_score,required_ind,required_direct=reqs
    missing=[]
    if evidence_score+1e-12<required_score: missing.append("SCORE")
    if independent<required_ind: missing.append("INDEPENDENT_SOURCES")
    if direct<required_direct: missing.append("DIRECT_SOURCES")
    if contradict: missing.append("CONTRADICTORY_EVIDENCE_REQUIRES_RESOLUTION")
    if missing:
        decision=Decision.HOLD; reasons=("EVIDENCE_INSUFFICIENT",)+tuple(missing); next_gate=False
    elif request.action_risk==Risk.CRITICAL and p.critical_requires_human_approval:
        decision=Decision.HUMAN_APPROVAL; reasons=("EVIDENCE_SUFFICIENT_HUMAN_APPROVAL_REQUIRED",); next_gate=False
    else:
        decision=Decision.ALLOW; reasons=("EVIDENCE_SUFFICIENT_CANDIDATE",); next_gate=True
    return EvidenceResult(decision,reasons,round(evidence_score,12),required_score,independent,required_ind,direct,required_direct,fresh,stale,tuple(sorted(duplicates)),tuple(sorted(excluded)),tuple(sorted(contradict)),tuple(missing),next_gate,fingerprint({"request":request,"policy":p,"registry_fingerprint":s.registry_fingerprint,"now":now}))

def evaluate(request,policy,claims,sources,evidence,*,now: int) -> EvidenceResult:
    s=prepare_state(policy,claims,sources,evidence,binding=request.binding,now=now)
    if not validate_prepared_integrity(s): return _hold("PREPARED_INTEGRITY_INVALID",request,_risk_req(policy,request.action_risk) if _policy_valid(policy,now) else (0,0,0))
    return _evaluate_prepared_validated(request,s,now=now)

def evaluate_prepared(request,s: PreparedEvidenceState,*,current_policy_fingerprint: str,current_registry_fingerprint: str,prepared_integrity_validated: bool,now: int) -> EvidenceResult:
    reqs=_risk_req(s.policy,request.action_risk)
    if not prepared_integrity_validated: return _hold("PREPARED_INTEGRITY_NOT_VALIDATED",request,reqs)
    if current_policy_fingerprint!=s.policy_fingerprint: return _hold("CURRENT_POLICY_FINGERPRINT_MISMATCH",request,reqs)
    if current_registry_fingerprint!=s.registry_fingerprint: return _hold("CURRENT_REGISTRY_FINGERPRINT_MISMATCH",request,reqs)
    # Freshness is deliberately recalculated using current 'now'; score cache is never treated as truth.
    return _evaluate_prepared_validated(request,s,now=now)

def _map(items,key): return {key(x):x for x in items}

def _diff(base,target,key):
    b=_map(base,key); t=_map(target,key); changed=[]; added=[]
    for k,v in t.items():
        if k not in b: added.append(v)
        elif fingerprint(b[k])!=fingerprint(v): changed.append(v)
    removed=tuple(sorted(set(b)-set(t)))
    return tuple(changed),removed,tuple(added)

def make_delta(base: PreparedEvidenceState,target: PreparedEvidenceState) -> EvidenceRegistryDelta:
    cc,rc,ac=_diff(base.claims,target.claims,lambda x:x.claim_id)
    cs,rs,as_=_diff(base.sources,target.sources,lambda x:x.source_id)
    ce,re,ae=_diff(base.evidence,target.evidence,lambda x:x.evidence_id)
    return EvidenceRegistryDelta(base.registry_fingerprint,target.registry_fingerprint,cc,rc,ac,cs,rs,as_,ce,re,ae)

def _apply(items,changed,removed,added,key):
    d=_map(items,key)
    for k in removed: d.pop(k,None)
    for v in changed: d[key(v)]=v
    for v in added: d[key(v)]=v
    return tuple(d[k] for k in sorted(d))

def apply_delta(base: PreparedEvidenceState,d: EvidenceRegistryDelta,*,now: int) -> PreparedEvidenceState:
    if base.registry_fingerprint!=d.base_fingerprint: raise ValueError("DELTA_BASE_MISMATCH")
    claims=_apply(base.claims,d.changed_claims,d.removed_claim_ids,d.added_claims,lambda x:x.claim_id)
    sources=_apply(base.sources,d.changed_sources,d.removed_source_ids,d.added_sources,lambda x:x.source_id)
    evidence=_apply(base.evidence,d.changed_evidence,d.removed_evidence_ids,d.added_evidence,lambda x:x.evidence_id)
    out=prepare_state(base.policy,claims,sources,evidence,binding=base.binding,now=now)
    if out.registry_fingerprint!=d.target_fingerprint: raise ValueError("DELTA_TARGET_MISMATCH")
    return out

def missing_only_sync_plan(s: PreparedEvidenceState,remote_known: Mapping[str,Mapping[str,str]]) -> EvidenceSyncPlan:
    local={"claims":dict(s.claim_fingerprints),"sources":dict(s.source_fingerprints),"evidence":dict(s.evidence_fingerprints)}
    miss={}
    for kind in local:
        rr=remote_known.get(kind,{})
        miss[kind]=tuple(sorted(k for k,v in local[kind].items() if rr.get(k)!=v))
    meta=canonical_json({k:miss[k] for k in sorted(miss)}).encode("utf-8")
    full=full_registry_bytes(s)
    missing_count=sum(len(v) for v in miss.values())
    return EvidenceSyncPlan(s.registry_fingerprint,miss["claims"],miss["sources"],miss["evidence"],len(meta),full,missing_count>max(100,int((len(s.claims)+len(s.sources)+len(s.evidence))*.75)))

def full_registry_bytes(s: PreparedEvidenceState) -> int:
    return len(canonical_json({"policy":s.policy,"claims":s.claims,"sources":s.sources,"evidence":s.evidence,"binding":s.binding}).encode("utf-8"))

def delta_bytes(d: EvidenceRegistryDelta) -> int:
    return len(canonical_json(d).encode("utf-8"))

def default_policy(now: int) -> EvidencePolicy:
    return EvidencePolicy("ESS-POLICY","1","ESS-EPOCH",now-1000,now+100000,False,3600,300,3600,.5,.55,.5,.8,1.5,2.1,2.7,1,2,3,4,0,1,2,2,True)

def _common(): return dict(binding="ESS-BIND",verified=True,revoked=False,policy_id="ESS-POLICY",policy_version="1",authority_epoch="ESS-EPOCH")

def default_claims(): return (ClaimSpec("CLAIM-CONFIG-SAFE",**_common()),)

def default_sources():
    c=_common(); return (
        SourceMetadata("SRC-A","GROUP-A","SYSTEM_OBSERVATION",**c),
        SourceMetadata("SRC-B","GROUP-B","SIGNED_REPORT",**c),
        SourceMetadata("SRC-C","GROUP-C","INDEPENDENT_CHECK",**c),
        SourceMetadata("SRC-A-COPY","GROUP-A","MIRROR",**c),
    )

def default_evidence(now: int):
    c=_common(); return (
        EvidenceRecord("E-A","CLAIM-CONFIG-SAFE","SRC-A",EvidenceKind.DIRECT,EvidenceState.SUPPORTS,.95,now-10,now+1000,**c),
        EvidenceRecord("E-B","CLAIM-CONFIG-SAFE","SRC-B",EvidenceKind.DIRECT,EvidenceState.SUPPORTS,.90,now-20,now+1000,**c),
        EvidenceRecord("E-C","CLAIM-CONFIG-SAFE","SRC-C",EvidenceKind.INDIRECT,EvidenceState.SUPPORTS,.85,now-30,now+1000,**c),
        EvidenceRecord("E-A-COPY","CLAIM-CONFIG-SAFE","SRC-A-COPY",EvidenceKind.DIRECT,EvidenceState.SUPPORTS,.94,now-10,now+1000,**c),
    )

def default_request(now: int,risk: Risk=Risk.HIGH):
    return EvidenceRequest("REQ-ESS","CLAIM-CONFIG-SAFE",risk,"ESS-BIND","ESS-POLICY","1","ESS-EPOCH",now-10,now+1000)
