"""NOEPIN AL 146 — Cross-Context Leakage Detector — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-146
DCSR: AUXILIARY INTEGRATION / 補助統合.

Tracks candidate information-flow crossings between project/user/tenant/task contexts. Outputs are
control candidates/evidence only. Crossing Decision != Data Transfer Execution. Bridge Evidence !=
Permission Grant or Approval Execution. Leak Trace != Leak Proof. HOLD/DENY Candidate != Stop
Execution. DCSR does not replace authentication, encryption, Policy, or DLP and reconstruction alone
cannot create Truth, Authority, Permission, Safety Proof, Approval, Action, or Action Success.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json

class Decision(str, Enum):
    ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class EngineState(str, Enum):
    SAME_CONTEXT_CANDIDATE='SAME_CONTEXT_CANDIDATE'
    CROSS_CONTEXT_ALLOWED_CANDIDATE='CROSS_CONTEXT_ALLOWED_CANDIDATE'
    CROSS_CONTEXT_BLOCKED_CANDIDATE='CROSS_CONTEXT_BLOCKED_CANDIDATE'
    REVIEW_CANDIDATE='REVIEW_CANDIDATE'; INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_CONTEXT_CANDIDATE='CONTINUE_CONTEXT_CANDIDATE'
    USE_BRIDGE_CANDIDATE='USE_BRIDGE_CANDIDATE'
    RESTRICT_CONTEXT_CANDIDATE='RESTRICT_CONTEXT_CANDIDATE'
    POLICY_REVIEW_CANDIDATE='POLICY_REVIEW_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; UNAUTHORIZED_CROSSING='UNAUTHORIZED_CROSSING'; BRIDGE_REQUIRED='BRIDGE_REQUIRED'
    UNKNOWN_CONTEXT='UNKNOWN_CONTEXT'; POLICY_UNVERIFIED='POLICY_UNVERIFIED'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'
class DataLabel(str, Enum):
    PUBLIC='PUBLIC'; SHARED='SHARED'; INTERNAL='INTERNAL'; SENSITIVE='SENSITIVE'; SECRET='SECRET'

RANK={DataLabel.PUBLIC:0,DataLabel.SHARED:1,DataLabel.INTERNAL:2,DataLabel.SENSITIVE:3,DataLabel.SECRET:4}

@dataclass(frozen=True)
class ContextRef:
    context_id:str; context_type:str; namespace:str; owner_ref:str; binding:str; state_epoch:str

@dataclass(frozen=True)
class BridgeEvidence:
    bridge_id:str; source_context_id:str; destination_context_id:str; allowed_labels:tuple[DataLabel,...]
    scope_verified:bool; approval_evidence_valid:bool; binding:str; state_epoch:str

@dataclass(frozen=True)
class AccessPolicy:
    policy_id:str; verified:bool; allow_public_crossing:bool; allow_shared_crossing:bool
    shared_context_pairs:tuple[tuple[str,str],...]; bridge_evidence:tuple[BridgeEvidence,...]
    binding:str; state_epoch:str

@dataclass(frozen=True)
class CrossingRequest:
    request_id:str; source_context:ContextRef; destination_context:ContextRef; data_labels:tuple[DataLabel,...]
    access_policy:AccessPolicy; provenance_ids:tuple[str,...]; binding:str; state_epoch:str

@dataclass(frozen=True)
class CrossingResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState
    effective_label:DataLabel; crossing:bool; required_bridge:bool; bridge_candidate_id:str|None
    leak_trace:tuple[str,...]; reasons:tuple[str,...]; next_gate_candidate:bool
    crossing_decision_promoted_to_transfer:bool=False; leak_trace_promoted_to_leak_proof:bool=False
    bridge_evidence_promoted_to_permission:bool=False; bridge_evidence_promoted_to_approval:bool=False
    context_id_promoted_to_identity_authority:bool=False; data_transfer_executed:bool=False
    external_send_executed:bool=False; memory_transfer_executed:bool=False; tool_invoked:bool=False
    policy_modified:bool=False; dlp_replaced:bool=False; authentication_replaced:bool=False
    encryption_replaced:bool=False; dcsr_reconstruction_created_fact:bool=False
    sender_authority_inherited:bool=False; sender_intent_inherited:bool=False; sender_agreement_inherited:bool=False
    permission_granted:bool=False; approval_executed:bool=False; authority_granted:bool=False; stop_executed:bool=False
    action_executed:bool=False; plan_committed:bool=False; publish_executed:bool=False; external_write_performed:bool=False
    world_truth_proven:bool=False; domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False

@dataclass(frozen=True)
class PreparedCrossingState:
    request:CrossingRequest; result:CrossingResult; source_fingerprint:str; destination_fingerprint:str
    labels_fingerprint:str; policy_fingerprint:str; provenance_fingerprint:str; outcome_fingerprint:str
    integrity_fingerprint:str; binding:str; state_epoch:str

@dataclass(frozen=True)
class CrossingDelta:
    source_changed:bool; destination_changed:bool; labels_changed:bool; policy_changed:bool; provenance_changed:bool
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
    s=ContextRef('CTX-146-A','PROJECT','PROJECT-A','OWNER-A',b,e)
    d=ContextRef('CTX-146-A','PROJECT','PROJECT-A','OWNER-A',b,e)
    p=AccessPolicy('POL-146',True,True,False,(),(),b,e)
    return CrossingRequest('REQ-146',s,d,(DataLabel.INTERNAL,),p,('SRC-146-A',),b,e)

def _invalid(req,reason):
    return CrossingResult(Decision.HOLD,NextAction.POLICY_REVIEW_CANDIDATE,Escalation.INVALID_CONFIGURATION,
        EngineState.INVALID,DataLabel.SECRET,True,True,None,(),(reason,'NO_DATA_TRANSFER_EXECUTION','NO_PERMISSION_GRANT'),False)

def _validate_context(c,req):
    if not c.context_id or not c.context_type or not c.namespace or not c.owner_ref: return 'EMPTY_CONTEXT_FIELD'
    if c.binding!=req.binding or c.state_epoch!=req.state_epoch: return 'CONTEXT_BINDING_MISMATCH'
    return None

def _validate(req):
    if not req.request_id or not req.binding or not req.state_epoch: return 'EMPTY_REQUEST_CONTEXT'
    err=_validate_context(req.source_context,req) or _validate_context(req.destination_context,req)
    if err: return err
    if not req.data_labels: return 'NO_DATA_LABELS'
    if len(set(req.data_labels))!=len(req.data_labels): return 'DUPLICATE_DATA_LABELS'
    p=req.access_policy
    if not p.policy_id or p.binding!=req.binding or p.state_epoch!=req.state_epoch: return 'POLICY_BINDING_MISMATCH'
    if len(set(p.shared_context_pairs))!=len(p.shared_context_pairs): return 'DUPLICATE_SHARED_CONTEXT_PAIR'
    for a,b in p.shared_context_pairs:
        if not a or not b: return 'INVALID_SHARED_CONTEXT_PAIR'
    bids=[x.bridge_id for x in p.bridge_evidence]
    if len(set(bids))!=len(bids) or any(not x for x in bids): return 'INVALID_BRIDGE_IDS'
    for br in p.bridge_evidence:
        if not br.source_context_id or not br.destination_context_id or not br.allowed_labels: return 'INVALID_BRIDGE_EVIDENCE'
        if br.binding!=req.binding or br.state_epoch!=req.state_epoch: return 'BRIDGE_BINDING_MISMATCH'
    if len(set(req.provenance_ids))!=len(req.provenance_ids) or any(not x for x in req.provenance_ids): return 'INVALID_PROVENANCE'
    return None

def _effective_label(labels): return max(labels,key=lambda x:RANK[x])
def _pair(s,d): return (s.context_id,d.context_id)

def _find_bridge(req,label):
    for br in sorted(req.access_policy.bridge_evidence,key=lambda x:x.bridge_id):
        if br.source_context_id==req.source_context.context_id and br.destination_context_id==req.destination_context.context_id and label in br.allowed_labels:
            return br
    return None

def evaluate(req):
    err=_validate(req)
    if err: return _invalid(req,err)
    s=req.source_context; d=req.destination_context; p=req.access_policy; label=_effective_label(req.data_labels)
    crossing=(s.context_id!=d.context_id or s.namespace!=d.namespace or s.context_type!=d.context_type or s.owner_ref!=d.owner_ref)
    trace=(f'{s.context_type}:{s.context_id}:{s.namespace}->{d.context_type}:{d.context_id}:{d.namespace}',
           'labels='+','.join(sorted(x.value for x in req.data_labels)),
           'provenance='+','.join(sorted(req.provenance_ids)))
    if not crossing:
        return CrossingResult(Decision.ALLOW,NextAction.CONTINUE_CONTEXT_CANDIDATE,Escalation.NONE,EngineState.SAME_CONTEXT_CANDIDATE,
            label,False,False,None,trace,('SAME_CONTEXT_CANDIDATE','NO_DATA_TRANSFER_EXECUTION','ALLOW_IS_CANDIDATE_NOT_PERMISSION'),True)
    if not p.verified:
        return CrossingResult(Decision.HOLD,NextAction.POLICY_REVIEW_CANDIDATE,Escalation.POLICY_UNVERIFIED,EngineState.REVIEW_CANDIDATE,
            label,True,True,None,trace,('CROSS_CONTEXT_POLICY_UNVERIFIED','NO_DATA_TRANSFER_EXECUTION'),True)
    unknown=(s.context_id.upper() in {'UNKNOWN','UNRESOLVED'} or d.context_id.upper() in {'UNKNOWN','UNRESOLVED'})
    if unknown and RANK[label]>=RANK[DataLabel.SENSITIVE]:
        return CrossingResult(Decision.HOLD,NextAction.POLICY_REVIEW_CANDIDATE,Escalation.UNKNOWN_CONTEXT,EngineState.REVIEW_CANDIDATE,
            label,True,True,None,trace,('SENSITIVE_CONTEXT_ID_UNKNOWN','BOUNDARY_EXIT_NOT_ALLOWED_CANDIDATE','NO_DATA_TRANSFER_EXECUTION'),True)
    if label==DataLabel.PUBLIC and p.allow_public_crossing:
        return CrossingResult(Decision.ALLOW,NextAction.CONTINUE_CONTEXT_CANDIDATE,Escalation.NONE,EngineState.CROSS_CONTEXT_ALLOWED_CANDIDATE,
            label,True,False,None,trace,('PUBLIC_CROSSING_POLICY_CANDIDATE','ALLOW_IS_CANDIDATE_NOT_PERMISSION','NO_DATA_TRANSFER_EXECUTION'),True)
    pair=_pair(s,d)
    if label==DataLabel.SHARED and p.allow_shared_crossing and pair in p.shared_context_pairs:
        return CrossingResult(Decision.ALLOW,NextAction.CONTINUE_CONTEXT_CANDIDATE,Escalation.NONE,EngineState.CROSS_CONTEXT_ALLOWED_CANDIDATE,
            label,True,False,None,trace,('SHARED_PAIR_POLICY_CANDIDATE','ALLOW_IS_CANDIDATE_NOT_PERMISSION','NO_DATA_TRANSFER_EXECUTION'),True)
    br=_find_bridge(req,label)
    if br is not None:
        if br.scope_verified and br.approval_evidence_valid:
            return CrossingResult(Decision.ALLOW,NextAction.USE_BRIDGE_CANDIDATE,Escalation.NONE,EngineState.CROSS_CONTEXT_ALLOWED_CANDIDATE,
                label,True,True,br.bridge_id,trace+(f'bridge={br.bridge_id}',),('BRIDGE_EVIDENCE_VALID_CANDIDATE','BRIDGE_EVIDENCE_NOT_PERMISSION_GRANT','NO_DATA_TRANSFER_EXECUTION'),True)
        return CrossingResult(Decision.HOLD,NextAction.POLICY_REVIEW_CANDIDATE,Escalation.BRIDGE_REQUIRED,EngineState.REVIEW_CANDIDATE,
            label,True,True,br.bridge_id,trace+(f'bridge={br.bridge_id}',),('BRIDGE_EVIDENCE_INSUFFICIENT','NO_DATA_TRANSFER_EXECUTION'),True)
    return CrossingResult(Decision.DENY,NextAction.RESTRICT_CONTEXT_CANDIDATE,Escalation.UNAUTHORIZED_CROSSING,EngineState.CROSS_CONTEXT_BLOCKED_CANDIDATE,
        label,True,True,None,trace,('UNAUTHORIZED_CROSS_CONTEXT_CANDIDATE','DENY_IS_CANDIDATE_NOT_STOP_EXECUTION','NO_DATA_TRANSFER_EXECUTION'),True)

def _source_fp(req): return _fp(req.source_context)
def _destination_fp(req): return _fp(req.destination_context)
def _labels_fp(req): return _fp(req.data_labels)
def _policy_fp(req): return _fp(req.access_policy)
def _provenance_fp(req): return _fp(req.provenance_ids)

def prepare_state(req,binding,state_epoch):
    if binding!=req.binding or state_epoch!=req.state_epoch: return None
    r=evaluate(req); sf=_source_fp(req); df=_destination_fp(req); lf=_labels_fp(req); pf=_policy_fp(req); prf=_provenance_fp(req); of=_fp(r)
    integ=_fp((sf,df,lf,pf,prf,of,binding,state_epoch))
    return PreparedCrossingState(req,r,sf,df,lf,pf,prf,of,integ,binding,state_epoch)

def evaluate_prepared(st,*,integrity_validated,current_source_fingerprint,current_destination_fingerprint,current_labels_fingerprint,current_policy_fingerprint,current_provenance_fingerprint,current_outcome_fingerprint):
    if st is None or not integrity_validated: return _invalid(default_request(),'PREPARED_STATE_NOT_VALIDATED')
    if _fp((st.source_fingerprint,st.destination_fingerprint,st.labels_fingerprint,st.policy_fingerprint,st.provenance_fingerprint,st.outcome_fingerprint,st.binding,st.state_epoch))!=st.integrity_fingerprint:
        return _invalid(st.request,'PREPARED_STATE_INTEGRITY_MISMATCH')
    current=(current_source_fingerprint,current_destination_fingerprint,current_labels_fingerprint,current_policy_fingerprint,current_provenance_fingerprint,current_outcome_fingerprint)
    expected=(st.source_fingerprint,st.destination_fingerprint,st.labels_fingerprint,st.policy_fingerprint,st.provenance_fingerprint,st.outcome_fingerprint)
    if current!=expected: return _invalid(st.request,'PREPARED_STATE_FINGERPRINT_MISMATCH')
    return st.result

def _manifest_fp(st): return _fp((st.source_fingerprint,st.destination_fingerprint,st.labels_fingerprint,st.policy_fingerprint,st.provenance_fingerprint,st.outcome_fingerprint,st.binding,st.state_epoch))
def make_delta(old,new):
    return CrossingDelta(old.source_fingerprint!=new.source_fingerprint,old.destination_fingerprint!=new.destination_fingerprint,
        old.labels_fingerprint!=new.labels_fingerprint,old.policy_fingerprint!=new.policy_fingerprint,old.provenance_fingerprint!=new.provenance_fingerprint,
        _manifest_fp(old),_manifest_fp(new))
def plan_missing_only(old,new):
    ids=[]
    if old.source_fingerprint!=new.source_fingerprint: ids.append('SOURCE_CONTEXT')
    if old.destination_fingerprint!=new.destination_fingerprint: ids.append('DESTINATION_CONTEXT')
    if old.labels_fingerprint!=new.labels_fingerprint: ids.append('DATA_LABELS')
    if old.policy_fingerprint!=new.policy_fingerprint: ids.append('ACCESS_POLICY')
    if old.provenance_fingerprint!=new.provenance_fingerprint: ids.append('PROVENANCE')
    return MissingOnlyPlan(tuple(ids),len(_canon(tuple(ids)))+96,False)

def default_evaluation(): return evaluate(default_request())

if __name__=='__main__': print(json.dumps(_obj(default_evaluation()),ensure_ascii=False,sort_keys=True))
