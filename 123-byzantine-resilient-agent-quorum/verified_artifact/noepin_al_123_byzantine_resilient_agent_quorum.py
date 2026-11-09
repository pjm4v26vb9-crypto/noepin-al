"""NOEPIN AL 123 — Byzantine-Resilient Agent Quorum — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-123
DCSR: DIRECT INTEGRATION / 直接統合.
Quorum is a decision candidate only. Quorum != Truth; quorum satisfaction != Permission Grant or Action Execution.
Received DCSR state never automatically inherits sender authority, intent, agreement, permission, or action-success authority.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math

class Decision(str,Enum): ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class NextAction(str,Enum): QUORUM_DECISION_CANDIDATE='QUORUM_DECISION_CANDIDATE'; HOLD_QUORUM_REVIEW='HOLD_QUORUM_REVIEW'; HOLD_SIGNATURE_REVIEW='HOLD_SIGNATURE_REVIEW'
class Escalation(str,Enum): NONE='NONE'; INSUFFICIENT_INDEPENDENT_QUORUM='INSUFFICIENT_INDEPENDENT_QUORUM'; INVALID_SIGNATURES='INVALID_SIGNATURES'; DOMAIN_EQUIVOCATION='DOMAIN_EQUIVOCATION'; CONFLICTING_QUORUM='CONFLICTING_QUORUM'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'

@dataclass(frozen=True)
class AgentDecision:
    agent_id:str; trust_domain:str; choice:str; trust:float; evidence_quality:float; signature_id:str; signature_valid:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class QuorumPolicy:
    fault_bound:int; minimum_trust:float; minimum_evidence_quality:float; require_signature:bool=True
@dataclass(frozen=True)
class QuorumRequest:
    request_id:str; decisions:tuple[AgentDecision,...]; policy:QuorumPolicy; binding:str; state_epoch:str
@dataclass(frozen=True)
class QuorumResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; reasons:tuple[str,...]; quorum_state:str; quorum_choice:str|None; required_independent_domains:int; eligible_independent_domains:int; agreeing_independent_domains:int; fault_suspects:tuple[str,...]; excluded_agents:tuple[str,...]; next_gate_candidate:bool
    quorum_promoted_to_truth:bool=False; quorum_promoted_to_permission:bool=False; signature_evidence_promoted_to_identity_authority:bool=False; sender_authority_inherited:bool=False; sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False; permission_granted:bool=False; approval_executed:bool=False; authority_granted:bool=False; stop_executed:bool=False; action_executed:bool=False; plan_committed:bool=False; publish_executed:bool=False; external_write_performed:bool=False; world_truth_proven:bool=False; domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedQuorumState:
    request:QuorumRequest; result:QuorumResult; context_fingerprint:str; decision_fingerprint:str; policy_fingerprint:str; outcome_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str
@dataclass(frozen=True)
class QuorumDelta:
    changed_decisions:tuple[AgentDecision,...]; removed_agent_ids:tuple[str,...]; from_manifest_fingerprint:str; to_manifest_fingerprint:str
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
def default_policy(): return QuorumPolicy(1,.40,.40,True)
def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    ds=(
      AgentDecision('AGENT-A','DOMAIN-A','APPROVE',.95,.95,'SIG-A',True,b,e),
      AgentDecision('AGENT-B','DOMAIN-B','APPROVE',.90,.90,'SIG-B',True,b,e),
      AgentDecision('AGENT-C','DOMAIN-C','APPROVE',.85,.85,'SIG-C',True,b,e),
      AgentDecision('AGENT-D','DOMAIN-D','REJECT',.55,.60,'SIG-D',True,b,e),
    )
    return QuorumRequest('DEFAULT-123',ds,default_policy(),b,e)
def _required_domains(p:QuorumPolicy): return 2*p.fault_bound+1
def _invalid(reason):
    return QuorumResult(Decision.HOLD,NextAction.HOLD_QUORUM_REVIEW,Escalation.INVALID_CONFIGURATION,(reason,'QUORUM_NOT_PROMOTED_TO_AUTHORITY'), 'INVALID',None,0,0,0,(),(),False)
def _manifest_fp(req): return _fp((req.decisions,req.binding,req.state_epoch))

def evaluate(req:QuorumRequest)->QuorumResult:
    if not req.request_id or not req.binding or not req.state_epoch: return _invalid('INVALID_REQUEST_IDENTITY')
    p=req.policy
    if isinstance(p.fault_bound,bool) or not isinstance(p.fault_bound,int) or p.fault_bound<0: return _invalid('FAULT_BOUND_INVALID')
    if not all(_finite(x) for x in (p.minimum_trust,p.minimum_evidence_quality)): return _invalid('NONFINITE_POLICY')
    if not (0<=p.minimum_trust<=1 and 0<=p.minimum_evidence_quality<=1): return _invalid('POLICY_RANGE_INVALID')
    if not req.decisions: return _invalid('EMPTY_DECISION_SET')
    ids=[d.agent_id for d in req.decisions]
    if any(not x for x in ids) or len(ids)!=len(set(ids)): return _invalid('DUPLICATE_OR_EMPTY_AGENT_ID')
    for d in req.decisions:
        if not d.trust_domain or not d.choice or d.binding!=req.binding or d.state_epoch!=req.state_epoch: return _invalid('DECISION_IDENTITY_INVALID')
        if not all(_finite(x) for x in (d.trust,d.evidence_quality)): return _invalid('NONFINITE_DECISION_QUALITY')
        if not (0<=d.trust<=1 and 0<=d.evidence_quality<=1): return _invalid('DECISION_QUALITY_RANGE_INVALID')
        if p.require_signature and not d.signature_id: return _invalid('MISSING_SIGNATURE_ID')
    suspects=set(); excluded=set(); domain_map={}
    for d in req.decisions:
        if p.require_signature and not d.signature_valid:
            suspects.add(f'AGENT:{d.agent_id}:INVALID_SIGNATURE'); excluded.add(d.agent_id); continue
        if d.trust<p.minimum_trust or d.evidence_quality<p.minimum_evidence_quality:
            excluded.add(d.agent_id); continue
        domain_map.setdefault(d.trust_domain,[]).append(d)
    domain_votes={}
    for domain,items in sorted(domain_map.items()):
        choices={x.choice for x in items}
        if len(choices)!=1:
            suspects.add(f'DOMAIN:{domain}:EQUIVOCATION')
            excluded.update(x.agent_id for x in items)
            continue
        # Multiple agents in one domain count as one independent domain vote.
        domain_votes[domain]=next(iter(choices))
    required=_required_domains(p)
    eligible_domains=len(domain_votes)
    tally={}
    for domain,choice in domain_votes.items(): tally.setdefault(choice,[]).append(domain)
    qualified=sorted((choice,tuple(sorted(domains))) for choice,domains in tally.items() if len(domains)>=required)
    invalid_sig=any('INVALID_SIGNATURE' in x for x in suspects)
    if len(qualified)>1:
        return QuorumResult(Decision.HOLD,NextAction.HOLD_QUORUM_REVIEW,Escalation.CONFLICTING_QUORUM,('MULTIPLE_CHOICES_MEET_QUORUM','QUORUM_NOT_PROMOTED_TO_TRUTH_OR_PERMISSION'), 'CONFLICTING',None,required,eligible_domains,0,tuple(sorted(suspects)),tuple(sorted(excluded)),False)
    if not qualified:
        esc=Escalation.INVALID_SIGNATURES if invalid_sig and eligible_domains<required else (Escalation.DOMAIN_EQUIVOCATION if any('EQUIVOCATION' in x for x in suspects) else Escalation.INSUFFICIENT_INDEPENDENT_QUORUM)
        nxt=NextAction.HOLD_SIGNATURE_REVIEW if esc==Escalation.INVALID_SIGNATURES else NextAction.HOLD_QUORUM_REVIEW
        return QuorumResult(Decision.HOLD,nxt,esc,('REQUIRED_INDEPENDENT_QUORUM_NOT_MET','SAME_DOMAIN_DUPLICATES_DO_NOT_INCREASE_QUORUM','NO_AUTOMATIC_AUTHORITY_INHERITANCE'), 'INSUFFICIENT',None,required,eligible_domains,max((len(v) for v in tally.values()),default=0),tuple(sorted(suspects)),tuple(sorted(excluded)),False)
    choice,domains=qualified[0]
    reasons=['INDEPENDENT_TRUST_DOMAIN_QUORUM_MET','SIGNATURE_INVALID_VOTES_EXCLUDED','SAME_DOMAIN_DUPLICATES_DEDUPLICATED','QUORUM_IS_CANDIDATE_ONLY']
    return QuorumResult(Decision.ALLOW,NextAction.QUORUM_DECISION_CANDIDATE,Escalation.NONE,tuple(reasons),'QUORUM_MET',choice,required,eligible_domains,len(domains),tuple(sorted(suspects)),tuple(sorted(excluded)),True)

def default_evaluation(): return evaluate(default_request())
def prepare_state(req,*,binding,state_epoch):
    if binding!=req.binding or state_epoch!=req.state_epoch: raise ValueError('binding/state_epoch mismatch')
    r=evaluate(req); cfp=_fp((req.request_id,binding,state_epoch)); dfp=_fp(req.decisions); pfp=_fp(req.policy); ofp=_fp(r); integ=_fp((cfp,dfp,pfp,ofp,binding,state_epoch)); return PreparedQuorumState(req,r,cfp,dfp,pfp,ofp,integ,binding,state_epoch)
def validate_prepared_integrity(st): return st.integrity_fingerprint==_fp((st.context_fingerprint,st.decision_fingerprint,st.policy_fingerprint,st.outcome_fingerprint,st.binding,st.state_epoch))
def evaluate_prepared(st,*,integrity_validated,current_context_fingerprint,current_decision_fingerprint,current_policy_fingerprint,current_outcome_fingerprint):
    if not integrity_validated or not validate_prepared_integrity(st): return _invalid('PREPARED_INTEGRITY_NOT_VALIDATED')
    if (current_context_fingerprint,current_decision_fingerprint,current_policy_fingerprint,current_outcome_fingerprint)!=(st.context_fingerprint,st.decision_fingerprint,st.policy_fingerprint,st.outcome_fingerprint): return _invalid('PREPARED_FINGERPRINT_MISMATCH')
    return st.result
def make_delta(old,new):
    o={x.agent_id:x for x in old.request.decisions}; n={x.agent_id:x for x in new.request.decisions}; ch=tuple(n[k] for k in sorted(n) if k not in o or _fp(n[k])!=_fp(o[k])); rm=tuple(k for k in sorted(o) if k not in n); return QuorumDelta(ch,rm,_manifest_fp(old.request),_manifest_fp(new.request))
def plan_missing_only(old,new):
    d=make_delta(old,new); ids=tuple([f'DECISION:{x.agent_id}' for x in d.changed_decisions]+[f'REMOVED_DECISION:{x}' for x in d.removed_agent_ids]); meta=len(_canon({'from':d.from_manifest_fingerprint,'to':d.to_manifest_fingerprint,'ids':ids})); return MissingOnlyPlan(ids,meta,False)
