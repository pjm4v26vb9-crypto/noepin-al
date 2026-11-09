"""NOEPIN AL 122 — Trust-Weighted Voting — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-122
DCSR: DIRECT INTEGRATION / 直接統合.
Weighted consensus, dissent and confidence are evidence/candidates only. Consensus != Truth; Confidence != Safety Proof; weighted majority != Permission Grant.
Received DCSR state never automatically inherits sender authority, intent, agreement, permission, or action-success authority.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str,Enum): ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class NextAction(str,Enum): WEIGHTED_CONSENSUS_CANDIDATE='WEIGHTED_CONSENSUS_CANDIDATE'; HOLD_DISSENT_REVIEW='HOLD_DISSENT_REVIEW'; HOLD_INSUFFICIENT_EVIDENCE='HOLD_INSUFFICIENT_EVIDENCE'
class Escalation(str,Enum): NONE='NONE'; MAJOR_HIGH_WEIGHT_DISSENT='MAJOR_HIGH_WEIGHT_DISSENT'; INSUFFICIENT_EFFECTIVE_WEIGHT='INSUFFICIENT_EFFECTIVE_WEIGHT'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'

@dataclass(frozen=True)
class AgentVote:
    agent_id:str; choice:str; trust:float; task_expertise:float; evidence_quality:float; independence:float; evidence_present:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class VotingPolicy:
    evidence_missing_factor:float; minimum_effective_weight:float; major_agent_weight_threshold:float; consensus_threshold:float; major_dissent_ratio_threshold:float
@dataclass(frozen=True)
class VotingRequest:
    request_id:str; votes:tuple[AgentVote,...]; policy:VotingPolicy; binding:str; state_epoch:str
@dataclass(frozen=True)
class VotingResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; reasons:tuple[str,...]; weighted_consensus:str|None; weighted_totals:tuple[tuple[str,float],...]; dissent:float; confidence:float; effective_weight:float; next_gate_candidate:bool
    consensus_promoted_to_truth:bool=False; consensus_promoted_to_permission:bool=False; confidence_promoted_to_safety_proof:bool=False; sender_authority_inherited:bool=False; sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False; permission_granted:bool=False; approval_executed:bool=False; authority_granted:bool=False; stop_executed:bool=False; action_executed:bool=False; plan_committed:bool=False; publish_executed:bool=False; external_write_performed:bool=False; world_truth_proven:bool=False; domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedVotingState:
    request:VotingRequest; result:VotingResult; context_fingerprint:str; vote_fingerprint:str; policy_fingerprint:str; outcome_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class VotingDelta:
    changed_votes:tuple[AgentVote,...]; removed_agent_ids:tuple[str,...]; from_manifest_fingerprint:str; to_manifest_fingerprint:str
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
def _finite(x): return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(float(x))
def default_policy(): return VotingPolicy(.20,.15,.45,.55,.30)
def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    votes=(
      AgentVote('AGENT-A','OPTION-A',.90,.90,.90,.95,True,b,e),
      AgentVote('AGENT-B','OPTION-A',.80,.85,.85,.90,True,b,e),
      AgentVote('AGENT-C','OPTION-B',.35,.50,.40,.80,True,b,e),
      AgentVote('AGENT-D','OPTION-A',.60,.70,.65,.75,True,b,e),
    )
    return VotingRequest('DEFAULT-122',votes,default_policy(),b,e)
def _invalid(req,reason): return VotingResult(Decision.HOLD,NextAction.HOLD_INSUFFICIENT_EVIDENCE,Escalation.INVALID_CONFIGURATION,(reason,'NO_AUTOMATIC_AUTHORITY_INHERITANCE'),None,(),1.0,0.0,0.0,False)
def _manifest_fp(req): return _fp((req.votes,req.binding,req.state_epoch))
def _vote_weight(v,p):
    base=v.trust*v.task_expertise*v.evidence_quality*v.independence
    if not v.evidence_present: base*=p.evidence_missing_factor
    return base

def evaluate(req:VotingRequest)->VotingResult:
    if not req.request_id or not req.binding or not req.state_epoch: return _invalid(req,'INVALID_REQUEST_IDENTITY')
    p=req.policy
    vals=(p.evidence_missing_factor,p.minimum_effective_weight,p.major_agent_weight_threshold,p.consensus_threshold,p.major_dissent_ratio_threshold)
    if not all(_finite(x) for x in vals): return _invalid(req,'NONFINITE_POLICY')
    if not (0<=p.evidence_missing_factor<=1 and p.minimum_effective_weight>=0 and 0<=p.major_agent_weight_threshold<=1 and 0<=p.consensus_threshold<=1 and 0<=p.major_dissent_ratio_threshold<=1): return _invalid(req,'POLICY_RANGE_INVALID')
    if not req.votes: return _invalid(req,'EMPTY_VOTE_SET')
    ids=[v.agent_id for v in req.votes]
    if any(not x for x in ids) or len(ids)!=len(set(ids)): return _invalid(req,'DUPLICATE_OR_EMPTY_AGENT_ID')
    for v in req.votes:
        if not v.choice or v.binding!=req.binding or v.state_epoch!=req.state_epoch: return _invalid(req,'VOTE_IDENTITY_INVALID')
        if not all(_finite(x) for x in (v.trust,v.task_expertise,v.evidence_quality,v.independence)): return _invalid(req,'NONFINITE_VOTE_WEIGHT')
        if not all(0<=x<=1 for x in (v.trust,v.task_expertise,v.evidence_quality,v.independence)): return _invalid(req,'VOTE_WEIGHT_RANGE_INVALID')
    weighted=[(v,_vote_weight(v,p)) for v in req.votes]
    effective=sum(w for _,w in weighted)
    if effective<p.minimum_effective_weight:
        return VotingResult(Decision.HOLD,NextAction.HOLD_INSUFFICIENT_EVIDENCE,Escalation.INSUFFICIENT_EFFECTIVE_WEIGHT,('INSUFFICIENT_EFFECTIVE_WEIGHT','CONSENSUS_NOT_PROMOTED_TO_TRUTH'),None,(),1.0,0.0,round(effective,12),False)
    totals={}
    for v,w in weighted: totals[v.choice]=totals.get(v.choice,0.0)+w
    ordered=sorted(totals.items(),key=lambda kv:(-kv[1],kv[0]))
    winner,winw=ordered[0]; confidence=winw/effective if effective else 0.0
    dissent=1.0-confidence
    major_by_choice={}
    for v,w in weighted:
        if w>=p.major_agent_weight_threshold: major_by_choice.setdefault(v.choice,[]).append((v.agent_id,w))
    major_choices=sorted(major_by_choice)
    if len(major_choices)>=2:
        major_weight=sum(w for v,w in weighted if v.choice in major_by_choice)
        major_dissent=(major_weight-winw)/effective if effective else 1.0
        if major_dissent>=p.major_dissent_ratio_threshold or len(major_choices)>=2:
            return VotingResult(Decision.HOLD,NextAction.HOLD_DISSENT_REVIEW,Escalation.MAJOR_HIGH_WEIGHT_DISSENT,('HIGH_WEIGHT_AGENTS_MATERIALLY_DISAGREE','MAJORITY_CANNOT_OVERRIDE_MAJOR_DISSENT','CONSENSUS_NOT_PROMOTED_TO_TRUTH'),winner,tuple((k,round(v,12)) for k,v in sorted(totals.items())),round(dissent,12),round(confidence,12),round(effective,12),False)
    if confidence<p.consensus_threshold:
        return VotingResult(Decision.HOLD,NextAction.HOLD_DISSENT_REVIEW,Escalation.MAJOR_HIGH_WEIGHT_DISSENT,('WEIGHTED_CONSENSUS_BELOW_THRESHOLD','DISSENT_REQUIRES_REVIEW','CONSENSUS_NOT_PROMOTED_TO_TRUTH'),winner,tuple((k,round(v,12)) for k,v in sorted(totals.items())),round(dissent,12),round(confidence,12),round(effective,12),False)
    return VotingResult(Decision.ALLOW,NextAction.WEIGHTED_CONSENSUS_CANDIDATE,Escalation.NONE,('TRUST_EXPERTISE_EVIDENCE_INDEPENDENCE_WEIGHTED','EVIDENCE_MISSING_VOTES_DECAYED','CONSENSUS_IS_CANDIDATE_ONLY'),winner,tuple((k,round(v,12)) for k,v in sorted(totals.items())),round(dissent,12),round(confidence,12),round(effective,12),True)

def default_evaluation(): return evaluate(default_request())
def prepare_state(req,*,binding,state_epoch):
    if binding!=req.binding or state_epoch!=req.state_epoch: raise ValueError('binding/state_epoch mismatch')
    r=evaluate(req); cfp=_fp((req.request_id,binding,state_epoch)); vfp=_fp(req.votes); pfp=_fp(req.policy); ofp=_fp(r); integ=_fp((cfp,vfp,pfp,ofp,binding,state_epoch)); return PreparedVotingState(req,r,cfp,vfp,pfp,ofp,integ,binding,state_epoch)
def validate_prepared_integrity(st): return st.integrity_fingerprint==_fp((st.context_fingerprint,st.vote_fingerprint,st.policy_fingerprint,st.outcome_fingerprint,st.binding,st.state_epoch))
def evaluate_prepared(st,*,integrity_validated,current_context_fingerprint,current_vote_fingerprint,current_policy_fingerprint,current_outcome_fingerprint):
    if not integrity_validated or not validate_prepared_integrity(st): return _invalid(st.request,'PREPARED_INTEGRITY_NOT_VALIDATED')
    if (current_context_fingerprint,current_vote_fingerprint,current_policy_fingerprint,current_outcome_fingerprint)!=(st.context_fingerprint,st.vote_fingerprint,st.policy_fingerprint,st.outcome_fingerprint): return _invalid(st.request,'PREPARED_FINGERPRINT_MISMATCH')
    return st.result
def make_delta(old,new):
    o={x.agent_id:x for x in old.request.votes}; n={x.agent_id:x for x in new.request.votes}; ch=tuple(n[k] for k in sorted(n) if k not in o or _fp(n[k])!=_fp(o[k])); rm=tuple(k for k in sorted(o) if k not in n); return VotingDelta(ch,rm,_manifest_fp(old.request),_manifest_fp(new.request))
def plan_missing_only(old,new):
    d=make_delta(old,new); ids=tuple([f'VOTE:{x.agent_id}' for x in d.changed_votes]+[f'REMOVED_VOTE:{x}' for x in d.removed_agent_ids]); meta=len(_canon({'from':d.from_manifest_fingerprint,'to':d.to_manifest_fingerprint,'ids':ids})); return MissingOnlyPlan(ids,meta,False)
