"""NOEPIN AL 145 — Aggregation Sensitivity Detector — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-145
DCSR: AUXILIARY INTEGRATION / 補助統合.

Detects sensitivity that emerges only after fragments are joined and inference rules are applied.
Outputs are candidates/evidence only. Inferred Fact Candidate != World Truth. Aggregate Sensitivity
!= Policy Decision. Leak Risk != Leak Proof. HOLD/DENY Candidate != Stop Execution. This core does
not send data, modify labels, replace authentication/encryption/Policy/DLP, or grant permission.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json

class Decision(str, Enum):
    ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class EngineState(str, Enum):
    AGGREGATE_NORMAL_CANDIDATE='AGGREGATE_NORMAL_CANDIDATE'
    AGGREGATE_SENSITIVE_CANDIDATE='AGGREGATE_SENSITIVE_CANDIDATE'
    REVIEW_CANDIDATE='REVIEW_CANDIDATE'; INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_AGGREGATE_CANDIDATE='CONTINUE_AGGREGATE_CANDIDATE'
    RESTRICT_DISCLOSURE_CANDIDATE='RESTRICT_DISCLOSURE_CANDIDATE'
    POLICY_REVIEW_CANDIDATE='POLICY_REVIEW_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; AGGREGATE_SENSITIVITY='AGGREGATE_SENSITIVITY'
    UNKNOWN_INFERENCE_IMPACT='UNKNOWN_INFERENCE_IMPACT'; AUDIENCE_POLICY='AUDIENCE_POLICY'
    INVALID_CONFIGURATION='INVALID_CONFIGURATION'
class Sensitivity(str, Enum):
    PUBLIC='PUBLIC'; INTERNAL='INTERNAL'; CONFIDENTIAL='CONFIDENTIAL'; RESTRICTED='RESTRICTED'; SECRET='SECRET'

RANK={Sensitivity.PUBLIC:0,Sensitivity.INTERNAL:1,Sensitivity.CONFIDENTIAL:2,Sensitivity.RESTRICTED:3,Sensitivity.SECRET:4}

@dataclass(frozen=True)
class DataFragment:
    fragment_id:str; entity_id:str; attributes:tuple[tuple[str,str],...]; join_values:tuple[tuple[str,str],...]
    sensitivity:Sensitivity; provenance_ids:tuple[str,...]; binding:str; state_epoch:str

@dataclass(frozen=True)
class InferenceRule:
    rule_id:str; required_attributes:tuple[str,...]; inferred_fact_type:str; inferred_sensitivity:Sensitivity
    required_join_key:str; enabled:bool; binding:str; state_epoch:str

@dataclass(frozen=True)
class AudienceContext:
    audience_id:str; external:bool; max_allowed_sensitivity:Sensitivity; policy_verified:bool
    binding:str; state_epoch:str

@dataclass(frozen=True)
class AggregationRequest:
    request_id:str; fragments:tuple[DataFragment,...]; inference_rules:tuple[InferenceRule,...]
    audience:AudienceContext; inference_coverage_known:bool; binding:str; state_epoch:str

@dataclass(frozen=True)
class InferredFactCandidate:
    rule_id:str; entity_id:str; fact_type:str; sensitivity:Sensitivity; source_fragment_ids:tuple[str,...]

@dataclass(frozen=True)
class AggregationResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState
    aggregate_sensitivity:Sensitivity; inferred_facts:tuple[InferredFactCandidate,...]; leak_risk:float
    reasons:tuple[str,...]; trace:tuple[str,...]; next_gate_candidate:bool
    inferred_fact_promoted_to_truth:bool=False; aggregate_sensitivity_promoted_to_policy:bool=False
    leak_risk_promoted_to_leak_proof:bool=False; disclosure_executed:bool=False; external_send_executed:bool=False
    label_mutated:bool=False; policy_modified:bool=False; dlp_replaced:bool=False; authentication_replaced:bool=False
    encryption_replaced:bool=False; tool_invoked:bool=False; dcsr_reconstruction_created_fact:bool=False
    sender_authority_inherited:bool=False; sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False
    permission_granted:bool=False; approval_executed:bool=False; authority_granted:bool=False; stop_executed:bool=False
    action_executed:bool=False; plan_committed:bool=False; publish_executed:bool=False; external_write_performed:bool=False
    world_truth_proven:bool=False; domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False

@dataclass(frozen=True)
class PreparedAggregationState:
    request:AggregationRequest; result:AggregationResult; fragments_fingerprint:str; rules_fingerprint:str
    audience_fingerprint:str; outcome_fingerprint:str; integrity_fingerprint:str; binding:str; state_epoch:str

@dataclass(frozen=True)
class AggregationDelta:
    fragments_changed:bool; rules_changed:bool; audience_changed:bool
    from_manifest_fingerprint:str; to_manifest_fingerprint:str

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

def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    f1=DataFragment('FRAG-145-A','ENTITY-145',(('department','RND'),),(('person_id','P-145'),),Sensitivity.PUBLIC,('SRC-145-A',),b,e)
    f2=DataFragment('FRAG-145-B','ENTITY-145',(('project','ALPHA'),),(('person_id','P-145'),),Sensitivity.PUBLIC,('SRC-145-B',),b,e)
    r=InferenceRule('RULE-145-A',('department','project'),'internal_assignment',Sensitivity.CONFIDENTIAL,'person_id',True,b,e)
    a=AudienceContext('AUD-145-EXTERNAL',True,Sensitivity.PUBLIC,True,b,e)
    return AggregationRequest('REQ-145',(f1,f2),(r,),a,True,b,e)

def _invalid(req,reason):
    return AggregationResult(Decision.HOLD,NextAction.POLICY_REVIEW_CANDIDATE,Escalation.INVALID_CONFIGURATION,EngineState.INVALID,
        Sensitivity.SECRET,(),1.0,(reason,'NO_DISCLOSURE_EXECUTION','NO_LABEL_MUTATION'),(),False)

def _validate(req):
    if not req.request_id or not req.binding or not req.state_epoch: return 'EMPTY_REQUEST_CONTEXT'
    if not req.fragments: return 'NO_FRAGMENTS'
    if not req.audience.audience_id or req.audience.binding!=req.binding or req.audience.state_epoch!=req.state_epoch: return 'AUDIENCE_BINDING_MISMATCH'
    fids=[f.fragment_id for f in req.fragments]
    if len(set(fids))!=len(fids) or any(not x for x in fids): return 'INVALID_FRAGMENT_IDS'
    for f in req.fragments:
        if not f.entity_id or f.binding!=req.binding or f.state_epoch!=req.state_epoch: return 'FRAGMENT_BINDING_MISMATCH'
        if len(set(f.attributes))!=len(f.attributes) or len(set(f.join_values))!=len(f.join_values): return 'DUPLICATE_FRAGMENT_FIELDS'
        if any(not k for k,_ in f.attributes) or any(not k or not v for k,v in f.join_values): return 'INVALID_FRAGMENT_FIELDS'
        if len(set(f.provenance_ids))!=len(f.provenance_ids) or any(not x for x in f.provenance_ids): return 'INVALID_PROVENANCE'
    rids=[r.rule_id for r in req.inference_rules]
    if len(set(rids))!=len(rids) or any(not x for x in rids): return 'INVALID_RULE_IDS'
    for r in req.inference_rules:
        if not r.inferred_fact_type or not r.required_join_key or r.binding!=req.binding or r.state_epoch!=req.state_epoch: return 'RULE_BINDING_MISMATCH'
        if len(set(r.required_attributes))!=len(r.required_attributes) or any(not x for x in r.required_attributes): return 'INVALID_RULE_ATTRIBUTES'
    return None

def _group_fragments(req,join_key):
    groups={}
    for f in req.fragments:
        vals=dict(f.join_values)
        if join_key in vals:
            groups.setdefault(vals[join_key],[]).append(f)
    return groups

def _infer(req):
    facts=[]; trace=[]
    for rule in req.inference_rules:
        if not rule.enabled: continue
        groups=_group_fragments(req,rule.required_join_key)
        for join_value,fs in sorted(groups.items()):
            if len(fs)<2: continue
            attrs={k for f in fs for k,_ in f.attributes}
            if set(rule.required_attributes).issubset(attrs):
                ids=tuple(sorted(f.fragment_id for f in fs))
                entity='|'.join(sorted(set(f.entity_id for f in fs)))
                facts.append(InferredFactCandidate(rule.rule_id,entity,rule.inferred_fact_type,rule.inferred_sensitivity,ids))
                trace.append(f'{rule.rule_id}:{rule.required_join_key}={join_value}:{",".join(ids)}')
    facts=tuple(sorted(set(facts),key=lambda x:(x.rule_id,x.entity_id,x.fact_type,x.source_fragment_ids)))
    return facts,tuple(trace)

def evaluate(req):
    err=_validate(req)
    if err: return _invalid(req,err)
    base=max((f.sensitivity for f in req.fragments),key=lambda s:RANK[s])
    facts,trace=_infer(req)
    agg=base
    if facts:
        agg=max((base,*[f.sensitivity for f in facts]),key=lambda s:RANK[s])
    audience=req.audience
    risk_base=RANK[agg]/4.0
    leak_risk=min(1.0,risk_base+(0.25 if audience.external else 0.0)+(0.15 if facts else 0.0))
    if audience.external and not req.inference_coverage_known:
        return AggregationResult(Decision.HOLD,NextAction.POLICY_REVIEW_CANDIDATE,Escalation.UNKNOWN_INFERENCE_IMPACT,EngineState.REVIEW_CANDIDATE,
            agg,facts,leak_risk,('INFERENCE_IMPACT_UNKNOWN_FOR_EXTERNAL_AUDIENCE','INDIVIDUAL_LABELS_INSUFFICIENT_FOR_SAFE_DECISION','NO_DISCLOSURE_EXECUTION'),trace,True)
    if RANK[agg] > RANK[audience.max_allowed_sensitivity]:
        if audience.external and facts:
            return AggregationResult(Decision.DENY,NextAction.RESTRICT_DISCLOSURE_CANDIDATE,Escalation.AGGREGATE_SENSITIVITY,EngineState.AGGREGATE_SENSITIVE_CANDIDATE,
                agg,facts,leak_risk,('AGGREGATION_RAISED_SENSITIVITY','AUDIENCE_BOUND_EXCEEDED','DENY_IS_CANDIDATE_NOT_STOP_EXECUTION','NO_DISCLOSURE_EXECUTION'),trace,True)
        return AggregationResult(Decision.HOLD,NextAction.POLICY_REVIEW_CANDIDATE,Escalation.AUDIENCE_POLICY,EngineState.REVIEW_CANDIDATE,
            agg,facts,leak_risk,('AUDIENCE_POLICY_BOUND_EXCEEDED','POLICY_EVALUATION_REQUIRED','NO_DISCLOSURE_EXECUTION'),trace,True)
    if not audience.policy_verified:
        return AggregationResult(Decision.HOLD,NextAction.POLICY_REVIEW_CANDIDATE,Escalation.AUDIENCE_POLICY,EngineState.REVIEW_CANDIDATE,
            agg,facts,leak_risk,('AUDIENCE_POLICY_NOT_VERIFIED','NO_DISCLOSURE_EXECUTION'),trace,True)
    state=EngineState.AGGREGATE_SENSITIVE_CANDIDATE if facts and RANK[agg]>RANK[base] else EngineState.AGGREGATE_NORMAL_CANDIDATE
    return AggregationResult(Decision.ALLOW,NextAction.CONTINUE_AGGREGATE_CANDIDATE,Escalation.NONE,state,
        agg,facts,leak_risk,('AGGREGATE_WITHIN_AUDIENCE_BOUND','ALLOW_IS_CANDIDATE_NOT_PERMISSION_GRANT','INFERRED_FACT_CANDIDATE_IS_NOT_WORLD_TRUTH','NO_DISCLOSURE_EXECUTION'),trace,True)

def _fragments_fp(req): return _fp(req.fragments)
def _rules_fp(req): return _fp((req.inference_rules,req.inference_coverage_known))
def _audience_fp(req): return _fp(req.audience)

def prepare_state(req,binding,state_epoch):
    if binding!=req.binding or state_epoch!=req.state_epoch: return None
    r=evaluate(req); ff=_fragments_fp(req); rf=_rules_fp(req); af=_audience_fp(req); of=_fp(r)
    integ=_fp((ff,rf,af,of,binding,state_epoch))
    return PreparedAggregationState(req,r,ff,rf,af,of,integ,binding,state_epoch)

def evaluate_prepared(st,*,integrity_validated,current_fragments_fingerprint,current_rules_fingerprint,current_audience_fingerprint,current_outcome_fingerprint):
    if st is None or not integrity_validated: return _invalid(default_request(),'PREPARED_STATE_NOT_VALIDATED')
    if _fp((st.fragments_fingerprint,st.rules_fingerprint,st.audience_fingerprint,st.outcome_fingerprint,st.binding,st.state_epoch))!=st.integrity_fingerprint:
        return _invalid(st.request,'PREPARED_STATE_INTEGRITY_MISMATCH')
    if current_fragments_fingerprint!=st.fragments_fingerprint or current_rules_fingerprint!=st.rules_fingerprint or current_audience_fingerprint!=st.audience_fingerprint or current_outcome_fingerprint!=st.outcome_fingerprint:
        return _invalid(st.request,'PREPARED_STATE_FINGERPRINT_MISMATCH')
    return st.result

def _manifest_fp(st): return _fp((st.fragments_fingerprint,st.rules_fingerprint,st.audience_fingerprint,st.outcome_fingerprint,st.binding,st.state_epoch))
def make_delta(old,new):
    return AggregationDelta(old.fragments_fingerprint!=new.fragments_fingerprint,old.rules_fingerprint!=new.rules_fingerprint,old.audience_fingerprint!=new.audience_fingerprint,_manifest_fp(old),_manifest_fp(new))
def plan_missing_only(old,new):
    ids=[]
    if old.fragments_fingerprint!=new.fragments_fingerprint: ids.append('FRAGMENTS')
    if old.rules_fingerprint!=new.rules_fingerprint: ids.append('INFERENCE_RULES')
    if old.audience_fingerprint!=new.audience_fingerprint: ids.append('AUDIENCE_CONTEXT')
    return MissingOnlyPlan(tuple(ids),len(_canon(tuple(ids)))+96,False)

def default_evaluation(): return evaluate(default_request())

if __name__=='__main__':
    print(json.dumps(_obj(default_evaluation()),ensure_ascii=False,sort_keys=True))
