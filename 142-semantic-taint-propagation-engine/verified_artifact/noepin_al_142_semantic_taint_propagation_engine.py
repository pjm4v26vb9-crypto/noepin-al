"""NOEPIN AL 142 — Semantic Taint Propagation Engine — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-142
DCSR: AUXILIARY INTEGRATION / 補助統合.

Propagates typed semantic taint labels through transformations, merges and sinks without
executing tools, writing data, granting permission, or replacing authentication, encryption,
Policy, or DLP. Unknown transforms preserve taint. Sanitizer evidence may reduce only labels
explicitly covered by verified evidence. Taint != Truth. Taint Sink Candidate != Sink Execution.
DENY/HOLD Candidate != Stop Execution. DCSR reconstruction does not create Truth, Authority,
Permission, Approval, Action, Action Success, authentication, encryption, Policy, or DLP proof.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json

class Decision(str, Enum):
    ALLOW='ALLOW'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'; DENY='DENY'
class EngineState(str, Enum):
    CLEAR_CANDIDATE='CLEAR_CANDIDATE'; TAINTED_CANDIDATE='TAINTED_CANDIDATE'; RISK_SINK_CANDIDATE='RISK_SINK_CANDIDATE'; INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_CANDIDATE='CONTINUE_CANDIDATE'; REVIEW_FLOW_CANDIDATE='REVIEW_FLOW_CANDIDATE'; BLOCK_FLOW_CANDIDATE='BLOCK_FLOW_CANDIDATE'; REVIEW_CANDIDATE='REVIEW_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; TAINTED_SINK='TAINTED_SINK'; UNKNOWN_TRANSFORM='UNKNOWN_TRANSFORM'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'
class TaintLabel(str, Enum):
    UNTRUSTED='UNTRUSTED'; SENSITIVE='SENSITIVE'; EXTERNAL_INSTRUCTION='EXTERNAL_INSTRUCTION'; SECRET='SECRET'; PERSONAL='PERSONAL'; POLICY_RELEVANT='POLICY_RELEVANT'
class TransformKind(str, Enum):
    IDENTITY='IDENTITY'; SUMMARY='SUMMARY'; PARAPHRASE='PARAPHRASE'; MERGE='MERGE'; FILTER='FILTER'; SANITIZER='SANITIZER'; UNKNOWN='UNKNOWN'
class SinkKind(str, Enum):
    INTERNAL='INTERNAL'; MEMORY='MEMORY'; EXTERNAL='EXTERNAL'; EXECUTION='EXECUTION'; TOOL='TOOL'; LOG='LOG'

@dataclass(frozen=True)
class DataItem:
    item_id:str; labels:tuple[TaintLabel,...]; provenance_ids:tuple[str,...]; binding:str; state_epoch:str

@dataclass(frozen=True)
class Transformation:
    transform_id:str; kind:TransformKind; input_ids:tuple[str,...]; output_id:str
    sanitizer_evidence_id:str=''; sanitizer_removes:tuple[TaintLabel,...]=()

@dataclass(frozen=True)
class FlowEdge:
    source_id:str; sink_id:str

@dataclass(frozen=True)
class Sink:
    sink_id:str; kind:SinkKind

@dataclass(frozen=True)
class TaintRequest:
    request_id:str; data_items:tuple[DataItem,...]; transformations:tuple[Transformation,...]
    flow_edges:tuple[FlowEdge,...]; sinks:tuple[Sink,...]; binding:str; state_epoch:str

@dataclass(frozen=True)
class TraceEntry:
    node_id:str; source_ids:tuple[str,...]; transform_kind:str; inherited_labels:tuple[TaintLabel,...]
    removed_labels:tuple[TaintLabel,...]; sanitizer_evidence_id:str; reasons:tuple[str,...]

@dataclass(frozen=True)
class SinkFinding:
    sink_id:str; sink_kind:SinkKind; source_node_id:str; labels:tuple[TaintLabel,...]; severity:str; reasons:tuple[str,...]

@dataclass(frozen=True)
class TaintResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState
    propagated_labels:tuple[tuple[str,tuple[TaintLabel,...]],...]; tainted_sinks:tuple[SinkFinding,...]; trace:tuple[TraceEntry,...]
    unknown_transform_ids:tuple[str,...]; reasons:tuple[str,...]; next_gate_candidate:bool
    taint_promoted_to_truth:bool=False; source_promoted_to_authority:bool=False
    sanitizer_evidence_promoted_to_safety_proof:bool=False; taint_sink_executed:bool=False
    external_send_executed:bool=False; execution_sink_invoked:bool=False; tool_invoked:bool=False
    memory_write_performed:bool=False; label_write_performed:bool=False; policy_modified:bool=False
    dlp_replaced:bool=False; authentication_replaced:bool=False; encryption_replaced:bool=False
    dcsr_reconstruction_created_fact:bool=False; sender_authority_inherited:bool=False; sender_intent_inherited:bool=False
    sender_agreement_inherited:bool=False; permission_granted:bool=False; approval_executed:bool=False
    authority_granted:bool=False; stop_executed:bool=False; action_executed:bool=False; plan_committed:bool=False
    publish_executed:bool=False; external_write_performed:bool=False; world_truth_proven:bool=False
    domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False

@dataclass(frozen=True)
class PreparedTaintState:
    request:TaintRequest; result:TaintResult; data_fingerprint:str; transform_fingerprint:str
    flow_fingerprint:str; sink_fingerprint:str; outcome_fingerprint:str; integrity_fingerprint:str
    binding:str; state_epoch:str

@dataclass(frozen=True)
class TaintDelta:
    changed_data_items:tuple[DataItem,...]; removed_data_item_ids:tuple[str,...]
    changed_transformations:tuple[Transformation,...]; removed_transform_ids:tuple[str,...]
    flow_changed:bool; sinks_changed:bool; from_manifest_fingerprint:str; to_manifest_fingerprint:str

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
def _sorted_labels(labels): return tuple(sorted(set(labels),key=lambda x:x.value))
def _manifest_fp(req): return _fp((req.data_items,req.transformations,req.flow_edges,req.sinks,req.binding,req.state_epoch))

def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    d=DataItem('DOC-142-A',(TaintLabel.UNTRUSTED,TaintLabel.EXTERNAL_INSTRUCTION),('SRC-142-A',),b,e)
    t=Transformation('SUM-142-A',TransformKind.SUMMARY,('DOC-142-A',),'SUMMARY-142-A')
    s=Sink('EXEC-142-A',SinkKind.EXECUTION)
    return TaintRequest('REQ-142',(d,),(t,),(FlowEdge('SUMMARY-142-A','EXEC-142-A'),),(s,),b,e)

def _invalid(reason):
    return TaintResult(Decision.HOLD,NextAction.REVIEW_CANDIDATE,Escalation.INVALID_CONFIGURATION,EngineState.INVALID,(),(),(),(),(reason,'NO_ACTION_EXECUTION','NO_LABEL_WRITE'),False)

def _validate(req):
    if not req.request_id or not req.binding or not req.state_epoch: return 'EMPTY_REQUEST_CONTEXT'
    ids=set()
    for x in req.data_items:
        if not x.item_id: return 'EMPTY_DATA_ITEM_ID'
        if x.item_id in ids: return 'DUPLICATE_DATA_ITEM_ID'
        ids.add(x.item_id)
        if x.binding!=req.binding or x.state_epoch!=req.state_epoch: return 'DATA_STATE_BINDING_MISMATCH'
        if len(set(x.labels))!=len(x.labels): return 'DUPLICATE_TAINT_LABEL'
        if len(set(x.provenance_ids))!=len(x.provenance_ids) or any(not p for p in x.provenance_ids): return 'INVALID_PROVENANCE'
    tids=set(); outputs=set(ids)
    for t in req.transformations:
        if not t.transform_id or t.transform_id in tids: return 'INVALID_TRANSFORM_ID'
        tids.add(t.transform_id)
        if not t.output_id or t.output_id in outputs: return 'DUPLICATE_OUTPUT_ID'
        outputs.add(t.output_id)
        if not t.input_ids or len(set(t.input_ids))!=len(t.input_ids): return 'INVALID_TRANSFORM_INPUTS'
        if t.kind!=TransformKind.SANITIZER and (t.sanitizer_evidence_id or t.sanitizer_removes): return 'SANITIZER_METADATA_ON_NON_SANITIZER'
        if t.kind==TransformKind.SANITIZER and t.sanitizer_removes and not t.sanitizer_evidence_id: return 'SANITIZER_REMOVAL_WITHOUT_EVIDENCE'
    sink_ids=set()
    for s in req.sinks:
        if not s.sink_id or s.sink_id in sink_ids: return 'INVALID_SINK_ID'
        sink_ids.add(s.sink_id)
    for e in req.flow_edges:
        if not e.source_id or not e.sink_id: return 'EMPTY_FLOW_EDGE_ENDPOINT'
        if e.sink_id not in sink_ids: return 'UNKNOWN_SINK_ID'
    return None

def _propagate_transform(t, label_map):
    inherited=set()
    missing=[]
    for i in t.input_ids:
        if i not in label_map: missing.append(i)
        else: inherited.update(label_map[i])
    if missing:
        return None, TraceEntry(t.output_id,t.input_ids,t.kind.value,(),(),t.sanitizer_evidence_id,('MISSING_TRANSFORM_INPUT',)+tuple(sorted(missing)))
    removed=()
    reasons=[]
    if t.kind==TransformKind.SANITIZER:
        if t.sanitizer_evidence_id:
            removed=tuple(sorted(set(t.sanitizer_removes)&inherited,key=lambda x:x.value))
            inherited.difference_update(removed)
            reasons.extend(('VERIFIED_SANITIZER_EVIDENCE_PRESENT','ONLY_EXPLICIT_LABEL_REDUCTION'))
        else:
            reasons.append('SANITIZER_WITHOUT_EVIDENCE_PRESERVES_TAINT')
    elif t.kind==TransformKind.UNKNOWN:
        reasons.extend(('UNKNOWN_TRANSFORM_PRESERVES_TAINT','FAIL_SAFE_LABEL_RETENTION'))
    elif t.kind==TransformKind.MERGE:
        reasons.append('MERGE_LABEL_JOIN')
    else:
        reasons.append('TAINT_PROPAGATED')
    out=_sorted_labels(inherited)
    return out, TraceEntry(t.output_id,t.input_ids,t.kind.value,out,removed,t.sanitizer_evidence_id,tuple(reasons))

def _sink_finding(sink, source_id, labels):
    ls=set(labels); reasons=[]; sev='INFO'
    if sink.kind in (SinkKind.EXECUTION,SinkKind.TOOL) and TaintLabel.EXTERNAL_INSTRUCTION in ls and TaintLabel.UNTRUSTED in ls:
        sev='CRITICAL'; reasons.append('UNTRUSTED_EXTERNAL_INSTRUCTION_TO_EXECUTION_SINK')
    elif sink.kind==SinkKind.EXTERNAL and (TaintLabel.SECRET in ls or TaintLabel.SENSITIVE in ls or TaintLabel.PERSONAL in ls):
        sev='CRITICAL' if TaintLabel.SECRET in ls else 'HIGH'; reasons.append('SENSITIVE_DATA_TO_EXTERNAL_SINK')
    elif labels:
        sev='MEDIUM'; reasons.append('TAINT_REACHES_SINK')
    if not labels: reasons.append('NO_TAINT_AT_SINK')
    return SinkFinding(sink.sink_id,sink.kind,source_id,_sorted_labels(labels),sev,tuple(reasons))

def evaluate(req):
    err=_validate(req)
    if err: return _invalid(err)
    label_map={x.item_id:_sorted_labels(x.labels) for x in req.data_items}
    trace=[]; unknown=[]; pending=list(req.transformations); guard=0
    # Dependency-aware deterministic evaluation. Unknown transform means unknown semantics, not missing input.
    while pending and guard<=len(req.transformations)+1:
        guard+=1; nxt=[]; progressed=False
        for t in pending:
            if all(i in label_map for i in t.input_ids):
                out,tr=_propagate_transform(t,label_map)
                label_map[t.output_id]=out or (); trace.append(tr); progressed=True
                if t.kind==TransformKind.UNKNOWN: unknown.append(t.transform_id)
            else: nxt.append(t)
        if not progressed and nxt:
            return _invalid('UNRESOLVED_TRANSFORM_DEPENDENCY')
        pending=nxt
    sinks={s.sink_id:s for s in req.sinks}; findings=[]
    for edge in sorted(req.flow_edges,key=lambda x:(x.sink_id,x.source_id)):
        if edge.source_id not in label_map: return _invalid('UNKNOWN_FLOW_SOURCE')
        findings.append(_sink_finding(sinks[edge.sink_id],edge.source_id,label_map[edge.source_id]))
    critical=any(f.severity=='CRITICAL' for f in findings)
    high=any(f.severity=='HIGH' for f in findings)
    if critical:
        decision=Decision.DENY; action=NextAction.BLOCK_FLOW_CANDIDATE; escalation=Escalation.TAINTED_SINK; state=EngineState.RISK_SINK_CANDIDATE
    elif high or unknown:
        decision=Decision.HOLD; action=NextAction.REVIEW_FLOW_CANDIDATE; escalation=Escalation.UNKNOWN_TRANSFORM if unknown else Escalation.TAINTED_SINK; state=EngineState.TAINTED_CANDIDATE
    else:
        decision=Decision.ALLOW; action=NextAction.CONTINUE_CANDIDATE; escalation=Escalation.NONE; state=EngineState.TAINTED_CANDIDATE if any(label_map.values()) else EngineState.CLEAR_CANDIDATE
    reasons=['PURE_ANALYSIS_ONLY','NO_SINK_EXECUTION','NO_PERMISSION_GRANT','TAINT_NOT_TRUTH','DCSR_AUXILIARY_ONLY']
    if unknown: reasons.append('UNKNOWN_TRANSFORM_TAINT_PRESERVED')
    if critical or high: reasons.append('RISK_SINK_CANDIDATE_ONLY')
    prop=tuple((k,label_map[k]) for k in sorted(label_map))
    return TaintResult(decision,action,escalation,state,prop,tuple(findings),tuple(trace),tuple(sorted(unknown)),tuple(reasons),True)

def default_evaluation(): return evaluate(default_request())

def prepare_state(req,binding,state_epoch):
    if binding!=req.binding or state_epoch!=req.state_epoch:
        r=_invalid('PREPARE_CONTEXT_MISMATCH')
    else: r=evaluate(req)
    data_fp=_fp(req.data_items); transform_fp=_fp(req.transformations); flow_fp=_fp(req.flow_edges); sink_fp=_fp(req.sinks); outcome_fp=_fp(r)
    integrity=_fp((data_fp,transform_fp,flow_fp,sink_fp,outcome_fp,binding,state_epoch))
    return PreparedTaintState(req,r,data_fp,transform_fp,flow_fp,sink_fp,outcome_fp,integrity,binding,state_epoch)

def validate_prepared_integrity(st):
    return st.integrity_fingerprint==_fp((st.data_fingerprint,st.transform_fingerprint,st.flow_fingerprint,st.sink_fingerprint,st.outcome_fingerprint,st.binding,st.state_epoch)) and st.outcome_fingerprint==_fp(st.result)

def evaluate_prepared(st,*,integrity_validated,current_data_fingerprint,current_transform_fingerprint,current_flow_fingerprint,current_sink_fingerprint,current_outcome_fingerprint):
    if not integrity_validated or not validate_prepared_integrity(st): return _invalid('PREPARED_INTEGRITY_NOT_VALIDATED')
    if st.binding!=st.request.binding or st.state_epoch!=st.request.state_epoch: return _invalid('PREPARED_CONTEXT_MISMATCH')
    if current_data_fingerprint!=st.data_fingerprint: return _invalid('STALE_DATA_STATE')
    if current_transform_fingerprint!=st.transform_fingerprint: return _invalid('STALE_TRANSFORM_STATE')
    if current_flow_fingerprint!=st.flow_fingerprint: return _invalid('STALE_FLOW_STATE')
    if current_sink_fingerprint!=st.sink_fingerprint: return _invalid('STALE_SINK_STATE')
    if current_outcome_fingerprint!=st.outcome_fingerprint: return _invalid('STALE_OUTCOME_STATE')
    return st.result

def _index(xs,key): return {key(x):x for x in xs}
def make_delta(old,new):
    oi=_index(old.request.data_items,lambda x:x.item_id); ni=_index(new.request.data_items,lambda x:x.item_id)
    changed_data=tuple(ni[k] for k in sorted(ni) if k not in oi or _fp(ni[k])!=_fp(oi[k])); removed_data=tuple(sorted(set(oi)-set(ni)))
    ot=_index(old.request.transformations,lambda x:x.transform_id); nt=_index(new.request.transformations,lambda x:x.transform_id)
    changed_t=tuple(nt[k] for k in sorted(nt) if k not in ot or _fp(nt[k])!=_fp(ot[k])); removed_t=tuple(sorted(set(ot)-set(nt)))
    return TaintDelta(changed_data,removed_data,changed_t,removed_t,_fp(old.request.flow_edges)!=_fp(new.request.flow_edges),_fp(old.request.sinks)!=_fp(new.request.sinks),_manifest_fp(old.request),_manifest_fp(new.request))

def plan_missing_only(old,new):
    d=make_delta(old,new); ids=[]
    ids += [f'DATA:{x.item_id}' for x in d.changed_data_items] + [f'DATA:{x}' for x in d.removed_data_item_ids]
    ids += [f'TRANSFORM:{x.transform_id}' for x in d.changed_transformations] + [f'TRANSFORM:{x}' for x in d.removed_transform_ids]
    if d.flow_changed: ids.append('FLOW_GRAPH')
    if d.sinks_changed: ids.append('SINK_SET')
    meta=len(_canon((tuple(ids),d.from_manifest_fingerprint,d.to_manifest_fingerprint)))
    return MissingOnlyPlan(tuple(ids),meta,False)
