"""NOEPIN AL 097 — Conflict Mass Aggregator — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Pure uncertainty-control evidence. The module preserves disagreement as explicit
Conflict Mass rather than averaging opposing evidence into a false neutral/safe
state. It never promotes evidence, support/opposition scores, conflict mass, or
cache state to Truth/Authority; it never grants permission, executes actions,
commits, publishes, writes externally, proves Safety, or asserts Action Success.

Canonical identity: NOEPIN-AL-097
DCSR level: LIMITED INTEGRATION / 限定適用.
Provenance note: exact registered Origin GUID was not freshly reverified in this
completion session and is intentionally not guessed or regenerated.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, IntEnum
from hashlib import sha256
import json, math

class Decision(str, Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class RiskLevel(IntEnum):
    LOW=1; MEDIUM=2; HIGH=3; CRITICAL=4
class DecisionHint(str, Enum):
    CONTINUE_CANDIDATE='CONTINUE_CANDIDATE'; DENY_CANDIDATE='DENY_CANDIDATE'; HOLD_CONFLICT='HOLD_CONFLICT'; HOLD_INSUFFICIENT='HOLD_INSUFFICIENT'; HOLD_AMBIGUOUS='HOLD_AMBIGUOUS'

@dataclass(frozen=True)
class ConflictQuery:
    request_id:str; claim_id:str; risk:RiskLevel; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class EvidenceBelief:
    evidence_id:str; support_mass:float; opposition_mass:float; uncertainty_mass:float
    source_reliability:float; independence_score:float; source_id:str; source_version:str
    source_fingerprint:str; claim_fingerprint:str; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class ConflictRelation:
    relation_id:str; evidence_a:str; evidence_b:str; contradiction_strength:float
    independence_factor:float; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class ConflictPolicy:
    conflict_threshold_low:float; conflict_threshold_medium:float; conflict_threshold_high:float; conflict_threshold_critical:float
    dominance_margin_low:float; dominance_margin_medium:float; dominance_margin_high:float; dominance_margin_critical:float
    minimum_effective_evidence_low:float; minimum_effective_evidence_medium:float; minimum_effective_evidence_high:float; minimum_effective_evidence_critical:float
    allow_support_threshold:float; deny_opposition_threshold:float; binding:str; state_epoch:str; revoked:bool=False
@dataclass(frozen=True)
class ConflictResult:
    decision:Decision; decision_hint:DecisionHint; reasons:tuple[str,...]
    support:float; opposition:float; uncertainty:float; conflict_mass:float
    effective_evidence_count:float; dominance_margin:float; conflict_threshold:float
    reevaluation_candidate:bool; next_gate_candidate:bool
    cache_promoted_to_truth:bool=False; cache_promoted_to_authority:bool=False
    permission_granted:bool=False; action_executed:bool=False; plan_committed:bool=False
    atomic_publish_executed:bool=False; external_write_performed:bool=False
    world_truth_proven:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedConflictState:
    query:ConflictQuery; beliefs:tuple[EvidenceBelief,...]; relations:tuple[ConflictRelation,...]; policy:ConflictPolicy
    record_fingerprints:tuple[tuple[str,str],...]; context_fingerprint:str; dependency_fingerprint:str
    calibration_fingerprint:str; registry_fingerprint:str; precomputed_result:ConflictResult
    binding:str; state_epoch:str
@dataclass(frozen=True)
class ConflictStateDelta:
    base_fingerprint:str; target_fingerprint:str; changed_beliefs:tuple[EvidenceBelief,...]
    changed_relations:tuple[ConflictRelation,...]; removed_belief_ids:tuple[str,...]; removed_relation_ids:tuple[str,...]
    target_query:ConflictQuery|None; target_policy:ConflictPolicy|None; binding:str; state_epoch:str
@dataclass(frozen=True)
class ConflictSyncPlan:
    missing_or_changed_record_ids:tuple[str,...]; metadata_bytes_required:int; full_resend_required:bool

def _cv(x):
    if isinstance(x,Enum): return x.name if isinstance(x,IntEnum) else x.value
    if hasattr(x,'__dataclass_fields__'): return {k:_cv(getattr(x,k)) for k in x.__dataclass_fields__}
    if isinstance(x,tuple): return [_cv(v) for v in x]
    if isinstance(x,list): return [_cv(v) for v in x]
    if isinstance(x,dict): return {str(k):_cv(x[k]) for k in sorted(x)}
    return x
def _canon(x)->bytes: return json.dumps(_cv(x),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def _fp(x)->str: return sha256(_canon(x)).hexdigest()
def _clamp01(x:float)->float: return max(0.0,min(1.0,x))
def _threshold(risk:RiskLevel,p:ConflictPolicy)->float:
    return {RiskLevel.LOW:p.conflict_threshold_low,RiskLevel.MEDIUM:p.conflict_threshold_medium,RiskLevel.HIGH:p.conflict_threshold_high,RiskLevel.CRITICAL:p.conflict_threshold_critical}[risk]
def _margin(risk:RiskLevel,p:ConflictPolicy)->float:
    return {RiskLevel.LOW:p.dominance_margin_low,RiskLevel.MEDIUM:p.dominance_margin_medium,RiskLevel.HIGH:p.dominance_margin_high,RiskLevel.CRITICAL:p.dominance_margin_critical}[risk]
def _minimum(risk:RiskLevel,p:ConflictPolicy)->float:
    return {RiskLevel.LOW:p.minimum_effective_evidence_low,RiskLevel.MEDIUM:p.minimum_effective_evidence_medium,RiskLevel.HIGH:p.minimum_effective_evidence_high,RiskLevel.CRITICAL:p.minimum_effective_evidence_critical}[risk]
def _hold(reason:str,q:ConflictQuery,*,hint:DecisionHint=DecisionHint.HOLD_AMBIGUOUS,support:float=0.0,opposition:float=0.0,uncertainty:float=1.0,conflict:float=0.0,effective:float=0.0,margin:float=0.0,threshold:float=0.0):
    return ConflictResult(Decision.HOLD,hint,(reason,),_clamp01(support),_clamp01(opposition),_clamp01(uncertainty),_clamp01(conflict),max(0.0,effective),max(0.0,margin),_clamp01(threshold),True,False)

def _validate(q,beliefs,relations,p):
    if p.revoked: return 'POLICY_REVOKED'
    if not q.observed or not q.request_id or not q.claim_id: return 'QUERY_INVALID'
    if q.binding!=p.binding or q.state_epoch!=p.state_epoch: return 'QUERY_SCOPE_MISMATCH'
    vals=(p.conflict_threshold_low,p.conflict_threshold_medium,p.conflict_threshold_high,p.conflict_threshold_critical,p.dominance_margin_low,p.dominance_margin_medium,p.dominance_margin_high,p.dominance_margin_critical,p.allow_support_threshold,p.deny_opposition_threshold)
    if any((not math.isfinite(v) or not 0<=v<=1) for v in vals): return 'POLICY_THRESHOLD_INVALID'
    mins=(p.minimum_effective_evidence_low,p.minimum_effective_evidence_medium,p.minimum_effective_evidence_high,p.minimum_effective_evidence_critical)
    if any((not math.isfinite(v) or v<0) for v in mins): return 'POLICY_MINIMUM_INVALID'
    ids=[b.evidence_id for b in beliefs]
    if not ids: return 'NO_EVIDENCE'
    if len(ids)!=len(set(ids)): return 'DUPLICATE_EVIDENCE_ID'
    for b in beliefs:
        if not b.observed or not all((b.evidence_id,b.source_id,b.source_version,b.source_fingerprint,b.claim_fingerprint)): return 'EVIDENCE_RECORD_INVALID'
        if b.binding!=p.binding or b.state_epoch!=p.state_epoch: return 'EVIDENCE_SCOPE_MISMATCH'
        masses=(b.support_mass,b.opposition_mass,b.uncertainty_mass,b.source_reliability,b.independence_score)
        if any((not math.isfinite(v) or not 0<=v<=1) for v in masses): return 'EVIDENCE_MASS_INVALID'
        if abs((b.support_mass+b.opposition_mass+b.uncertainty_mass)-1.0)>1e-9: return 'EVIDENCE_MASS_NOT_NORMALIZED'
    rids=[r.relation_id for r in relations]
    if len(rids)!=len(set(rids)): return 'DUPLICATE_RELATION_ID'
    known=set(ids)
    for r in relations:
        if not r.observed or not r.relation_id or r.evidence_a==r.evidence_b or r.evidence_a not in known or r.evidence_b not in known: return 'RELATION_RECORD_INVALID'
        if r.binding!=p.binding or r.state_epoch!=p.state_epoch: return 'RELATION_SCOPE_MISMATCH'
        if not (math.isfinite(r.contradiction_strength) and math.isfinite(r.independence_factor) and 0<=r.contradiction_strength<=1 and 0<=r.independence_factor<=1): return 'RELATION_VALUE_INVALID'
    return None

def evaluate(q:ConflictQuery,beliefs:tuple[EvidenceBelief,...],relations:tuple[ConflictRelation,...],p:ConflictPolicy)->ConflictResult:
    beliefs=tuple(sorted(beliefs,key=lambda b:b.evidence_id)); relations=tuple(sorted(relations,key=lambda r:r.relation_id))
    err=_validate(q,beliefs,relations,p); threshold=_threshold(q.risk,p)
    if err: return _hold(err,q,threshold=threshold)
    weights=[]; sw=ow=uw=0.0
    by={b.evidence_id:b for b in beliefs}
    for b in beliefs:
        w=b.source_reliability*b.independence_score
        weights.append(w); sw+=w*b.support_mass; ow+=w*b.opposition_mass; uw+=w*b.uncertainty_mass
    total=sum(weights)
    if total<=1e-15: return _hold('NO_EFFECTIVE_EVIDENCE',q,hint=DecisionHint.HOLD_INSUFFICIENT,threshold=threshold)
    support=sw/total; opposition=ow/total; uncertainty=uw/total
    # Preserve simultaneous strong support/opposition as conflict instead of averaging.
    bipolar=_clamp01(2.0*min(support,opposition))
    relation_weight=relation_conflict=0.0
    for r in relations:
        a=by[r.evidence_a]; b=by[r.evidence_b]
        wa=a.source_reliability*a.independence_score; wb=b.source_reliability*b.independence_score
        pair_weight=min(wa,wb)*r.independence_factor
        if pair_weight<=0: continue
        # stance separation is high when one record supports while the other opposes.
        stance=abs((a.support_mass-a.opposition_mass)-(b.support_mass-b.opposition_mass))/2.0
        relation_conflict += pair_weight*r.contradiction_strength*stance
        relation_weight += pair_weight
    relational=(relation_conflict/relation_weight) if relation_weight>0 else 0.0
    conflict=_clamp01(max(bipolar,relational))
    effective=sum(weights); margin=abs(support-opposition); min_eff=_minimum(q.risk,p); req_margin=_margin(q.risk,p)
    if conflict>=threshold:
        return _hold('CONFLICT_MASS_EXCEEDS_THRESHOLD',q,hint=DecisionHint.HOLD_CONFLICT,support=support,opposition=opposition,uncertainty=uncertainty,conflict=conflict,effective=effective,margin=margin,threshold=threshold)
    if effective<min_eff:
        return _hold('EFFECTIVE_EVIDENCE_INSUFFICIENT',q,hint=DecisionHint.HOLD_INSUFFICIENT,support=support,opposition=opposition,uncertainty=uncertainty,conflict=conflict,effective=effective,margin=margin,threshold=threshold)
    if support>=p.allow_support_threshold and support>opposition and margin>=req_margin:
        return ConflictResult(Decision.ALLOW,DecisionHint.CONTINUE_CANDIDATE,('SUPPORT_DOMINANT_LOW_CONFLICT',),support,opposition,uncertainty,conflict,effective,margin,threshold,False,True)
    if opposition>=p.deny_opposition_threshold and opposition>support and margin>=req_margin:
        return ConflictResult(Decision.DENY,DecisionHint.DENY_CANDIDATE,('OPPOSITION_DOMINANT_LOW_CONFLICT',),support,opposition,uncertainty,conflict,effective,margin,threshold,False,False)
    if support+opposition<0.40:
        return _hold('BOTH_SIDES_WEAK',q,hint=DecisionHint.HOLD_INSUFFICIENT,support=support,opposition=opposition,uncertainty=uncertainty,conflict=conflict,effective=effective,margin=margin,threshold=threshold)
    return _hold('AMBIGUOUS_WITHOUT_SAFE_DOMINANCE',q,hint=DecisionHint.HOLD_AMBIGUOUS,support=support,opposition=opposition,uncertainty=uncertainty,conflict=conflict,effective=effective,margin=margin,threshold=threshold)

def default_policy():
    return ConflictPolicy(.55,.45,.30,.20,.20,.22,.25,.30,.80,1.20,1.60,2.00,.65,.65,'CMA-BIND','STATE-EPOCH-1')
def default_query():
    p=default_policy(); return ConflictQuery('REQ-97','CLAIM-1',RiskLevel.LOW,True,p.binding,p.state_epoch)
def default_beliefs():
    p=default_policy()
    return (
        EvidenceBelief('E1',.88,.04,.08,.95,.95,'SRC-1','V1','SFP-1','CFP-1',True,p.binding,p.state_epoch),
        EvidenceBelief('E2',.82,.06,.12,.90,.90,'SRC-2','V1','SFP-2','CFP-2',True,p.binding,p.state_epoch),
    )
def default_relations(): return ()
def default_evaluation(): return evaluate(default_query(),default_beliefs(),default_relations(),default_policy())

def _record_fingerprints(beliefs,relations):
    return tuple([(f'BELIEF:{b.evidence_id}',_fp(b)) for b in sorted(beliefs,key=lambda x:x.evidence_id)]+[(f'REL:{r.relation_id}',_fp(r)) for r in sorted(relations,key=lambda x:x.relation_id)])
def _context_fp(q,p): return _fp((q,p.binding,p.state_epoch))
def _dependency_fp(beliefs,relations): return _fp(_record_fingerprints(beliefs,relations))
def _calibration_fp(p): return _fp((p.conflict_threshold_low,p.conflict_threshold_medium,p.conflict_threshold_high,p.conflict_threshold_critical,p.dominance_margin_low,p.dominance_margin_medium,p.dominance_margin_high,p.dominance_margin_critical,p.minimum_effective_evidence_low,p.minimum_effective_evidence_medium,p.minimum_effective_evidence_high,p.minimum_effective_evidence_critical,p.allow_support_threshold,p.deny_opposition_threshold))
def _registry_fp(q,beliefs,relations,p): return _fp((q,_record_fingerprints(beliefs,relations),p))

def prepare_state(q,beliefs,relations,p,*,binding:str,state_epoch:str):
    beliefs=tuple(sorted(beliefs,key=lambda b:b.evidence_id)); relations=tuple(sorted(relations,key=lambda r:r.relation_id)); fps=_record_fingerprints(beliefs,relations)
    return PreparedConflictState(q,beliefs,relations,p,fps,_context_fp(q,p),_dependency_fp(beliefs,relations),_calibration_fp(p),_registry_fp(q,beliefs,relations,p),evaluate(q,beliefs,relations,p),binding,state_epoch)
def validate_prepared_integrity(st):
    if st.binding!=st.policy.binding or st.state_epoch!=st.policy.state_epoch: return False
    if st.record_fingerprints!=_record_fingerprints(st.beliefs,st.relations): return False
    if st.context_fingerprint!=_context_fp(st.query,st.policy): return False
    if st.dependency_fingerprint!=_dependency_fp(st.beliefs,st.relations): return False
    if st.calibration_fingerprint!=_calibration_fp(st.policy): return False
    if st.registry_fingerprint!=_registry_fp(st.query,st.beliefs,st.relations,st.policy): return False
    return st.precomputed_result==evaluate(st.query,st.beliefs,st.relations,st.policy)
def evaluate_prepared(st,*,current_context_fingerprint,current_dependency_fingerprint,current_calibration_fingerprint,current_registry_fingerprint,prepared_integrity_validated):
    if not prepared_integrity_validated: return _hold('PREPARED_INTEGRITY_NOT_VALIDATED',st.query,threshold=_threshold(st.query.risk,st.policy))
    if current_context_fingerprint!=st.context_fingerprint: return _hold('PREPARED_CONTEXT_MISMATCH',st.query,threshold=_threshold(st.query.risk,st.policy))
    if current_dependency_fingerprint!=st.dependency_fingerprint: return _hold('PREPARED_DEPENDENCY_MISMATCH',st.query,threshold=_threshold(st.query.risk,st.policy))
    if current_calibration_fingerprint!=st.calibration_fingerprint: return _hold('PREPARED_CALIBRATION_MISMATCH',st.query,threshold=_threshold(st.query.risk,st.policy))
    if current_registry_fingerprint!=st.registry_fingerprint: return _hold('PREPARED_REGISTRY_MISMATCH',st.query,threshold=_threshold(st.query.risk,st.policy))
    return st.precomputed_result

def make_delta(base,target):
    bb={b.evidence_id:b for b in base.beliefs}; tb={b.evidence_id:b for b in target.beliefs}; br={r.relation_id:r for r in base.relations}; tr={r.relation_id:r for r in target.relations}
    cb=tuple(tb[k] for k in sorted(tb) if k not in bb or _fp(tb[k])!=_fp(bb[k])); cr=tuple(tr[k] for k in sorted(tr) if k not in br or _fp(tr[k])!=_fp(br[k]))
    return ConflictStateDelta(base.registry_fingerprint,target.registry_fingerprint,cb,cr,tuple(sorted(set(bb)-set(tb))),tuple(sorted(set(br)-set(tr))),target.query if target.query!=base.query else None,target.policy if target.policy!=base.policy else None,target.binding,target.state_epoch)
def apply_delta(base,d):
    if base.registry_fingerprint!=d.base_fingerprint: raise ValueError('BASE_FINGERPRINT_MISMATCH')
    bm={b.evidence_id:b for b in base.beliefs}; rm={r.relation_id:r for r in base.relations}
    for k in d.removed_belief_ids: bm.pop(k,None)
    for k in d.removed_relation_ids: rm.pop(k,None)
    for b in d.changed_beliefs: bm[b.evidence_id]=b
    for r in d.changed_relations: rm[r.relation_id]=r
    out=prepare_state(d.target_query or base.query,tuple(bm.values()),tuple(rm.values()),d.target_policy or base.policy,binding=d.binding,state_epoch=d.state_epoch)
    if out.registry_fingerprint!=d.target_fingerprint: raise ValueError('TARGET_FINGERPRINT_MISMATCH')
    return out
def missing_only_sync_plan(target,known_record_fingerprints):
    missing=tuple(k for k,v in target.record_fingerprints if known_record_fingerprints.get(k)!=v)
    meta=len(_canon({'context':target.context_fingerprint,'dependency':target.dependency_fingerprint,'calibration':target.calibration_fingerprint,'registry':target.registry_fingerprint,'missing':missing}))
    return ConflictSyncPlan(missing,meta,False)
def full_registry_bytes(st): return len(_canon((st.query,st.beliefs,st.relations,st.policy)))
def delta_bytes(d): return len(_canon(d))
