"""NOEPIN AL 186 — Distributed Common State Reconstruction V1 completion successor.

Pure deterministic distributed-state planning/reconstruction model. It performs no network,
filesystem, process, permission, approval, or action execution. DCSR remains State
Infrastructure Authority only; reconstructed/cached/partial state is never promoted to
Domain Authority or Truth.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
from hashlib import sha256
import json
from typing import Any

class Decision(str,Enum): ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class NextAction(str,Enum):
 REQUEST_DELTA_CANDIDATE='REQUEST_DELTA_CANDIDATE'; REUSE_SHARED_STATE_CANDIDATE='REUSE_SHARED_STATE_CANDIDATE'; REMOTE_LAZY_MATERIALIZATION_CANDIDATE='REMOTE_LAZY_MATERIALIZATION_CANDIDATE'; FULL_TRANSFER_FALLBACK_CANDIDATE='FULL_TRANSFER_FALLBACK_CANDIDATE'; NORMAL_COMPUTATION_FALLBACK_CANDIDATE='NORMAL_COMPUTATION_FALLBACK_CANDIDATE'; RETAIN_NO_EXECUTION_CANDIDATE='RETAIN_NO_EXECUTION_CANDIDATE'
class Escalation(str,Enum):
 NONE='NONE'; SCHEMA_MISMATCH='SCHEMA_MISMATCH'; AUTHORITY_MISMATCH='AUTHORITY_MISMATCH'; DEPENDENCY_MISMATCH='DEPENDENCY_MISMATCH'; FINGERPRINT_MISMATCH='FINGERPRINT_MISMATCH'; PARTIAL_STATE='PARTIAL_STATE'; LOW_SHARED_RATIO='LOW_SHARED_RATIO'; TIMEOUT_RISK='TIMEOUT_RISK'; INVALID_INPUT='INVALID_INPUT'; PREPARED_STATE_STALE='PREPARED_STATE_STALE'
class EngineState(str,Enum):
 DELTA_TRANSFER_CANDIDATE='DELTA_TRANSFER_CANDIDATE'; SHARED_REUSE_CANDIDATE='SHARED_REUSE_CANDIDATE'; REMOTE_LAZY_CANDIDATE='REMOTE_LAZY_CANDIDATE'; FULL_TRANSFER_FALLBACK_CANDIDATE='FULL_TRANSFER_FALLBACK_CANDIDATE'; HOLD_CANDIDATE='HOLD_CANDIDATE'; INVALID_REQUEST='INVALID_REQUEST'

@dataclass(frozen=True)
class StateRecord:
 record_id:str; canonical_address:str; schema_version:str; authority_reference:str; dependency_fingerprint:str; content_fingerprint:str; payload_bytes:int; priority:int=100; prepared_available:bool=False; generator_available:bool=False
@dataclass(frozen=True)
class StateManifest:
 node_id:str; records:tuple[StateRecord,...]; schema_version:str='1'; manifest_fingerprint:str=''
@dataclass(frozen=True)
class NetworkCondition:
 bandwidth_bytes_per_sec:int=1_000_000; latency_ms:float=20.0; max_chunk_bytes:int=262_144; timeout_ms:float=3000.0; min_shared_ratio_for_dcsr:float=0.20
@dataclass(frozen=True)
class ReconstructionRequest:
 transfer_id:str; sender:StateManifest; receiver:StateManifest; network:NetworkCondition=NetworkCondition(); allow_remote_lazy:bool=True; integrity_validated:bool=True; require_final_validation:bool=True
@dataclass(frozen=True)
class ReconstructionResult:
 decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState; transfer_id:str; shared_record_ids:tuple[str,...]; delta_record_ids:tuple[str,...]; lazy_record_ids:tuple[str,...]; progressive_order:tuple[str,...]; final_candidate_fingerprint:str; sender_manifest_fingerprint:str; receiver_manifest_fingerprint:str; shared_ratio:float; full_payload_bytes:int; delta_payload_bytes:int; estimated_full_ms:float; estimated_dcsr_ms:float; final_validation_required:bool; final_validation_passed:bool; reconstructed_complete:bool; authoritative:bool; reason:str; next_gate_candidate:bool; full_transfer_candidate:bool; normal_computation_candidate:bool; prepared_state_reused:bool=False
 permission_granted:bool=False; permit_issued:bool=False; approval_executed:bool=False; human_approval_executed:bool=False; tool_invoked:bool=False; action_executed:bool=False; action_success:bool=False; stop_executed:bool=False; file_write_executed:bool=False; network_send_executed:bool=False; external_write_performed:bool=False
 world_truth_proven:bool=False; domain_authority_promoted:bool=False; memory_promoted_to_truth:bool=False; belief_promoted_to_truth:bool=False; candidate_promoted_to_actual:bool=False; intent_promoted_to_action:bool=False; action_request_promoted_to_success:bool=False; partial_state_promoted_to_complete:bool=False; reconstructed_state_promoted_to_authoritative:bool=False; fingerprint_match_promoted_to_authority:bool=False; safety_proven:bool=False
 dcsr_invented_state:bool=False; dcsr_invented_fingerprint:bool=False; dcsr_bypassed_authority:bool=False; dcsr_bypassed_schema:bool=False; dcsr_bypassed_dependency:bool=False; dcsr_bypassed_final_validation:bool=False; dcsr_reconstructed_unknown_without_data:bool=False; dcsr_removed_communication_requirement:bool=False
@dataclass(frozen=True)
class PreparedState:
 request:ReconstructionRequest; result:ReconstructionResult; request_fingerprint:str; result_fingerprint:str; integrity_fingerprint:str
@dataclass(frozen=True)
class ManifestDelta:
 transfer_id:str; requested_record_ids:tuple[str,...]; reused_record_ids:tuple[str,...]; lazy_record_ids:tuple[str,...]; metadata_bytes:int; full_resend_required:bool; fingerprint:str
@dataclass(frozen=True)
class MissingOnlyPlan:
 missing_or_changed_record_ids:tuple[str,...]; metadata_bytes_required:int; full_resend_required:bool

_FALSE_FIELDS=('permission_granted','permit_issued','approval_executed','human_approval_executed','tool_invoked','action_executed','action_success','stop_executed','file_write_executed','network_send_executed','external_write_performed','world_truth_proven','domain_authority_promoted','memory_promoted_to_truth','belief_promoted_to_truth','candidate_promoted_to_actual','intent_promoted_to_action','action_request_promoted_to_success','partial_state_promoted_to_complete','reconstructed_state_promoted_to_authoritative','fingerprint_match_promoted_to_authority','safety_proven','dcsr_invented_state','dcsr_invented_fingerprint','dcsr_bypassed_authority','dcsr_bypassed_schema','dcsr_bypassed_dependency','dcsr_bypassed_final_validation','dcsr_reconstructed_unknown_without_data','dcsr_removed_communication_requirement')

def _norm(v):
 if isinstance(v,Enum): return v.value
 if is_dataclass(v): return {f.name:_norm(getattr(v,f.name)) for f in fields(v)}
 if isinstance(v,dict): return {str(k):_norm(v[k]) for k in sorted(v,key=lambda x:str(x))}
 if isinstance(v,(tuple,list)): return [_norm(x) for x in v]
 if isinstance(v,(set,frozenset)): return sorted((_norm(x) for x in v),key=lambda x:json.dumps(x,sort_keys=True,separators=(',',':')))
 return v

def _canon(v)->bytes: return json.dumps(_norm(v),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def _fp(v)->str: return sha256(_canon(v)).hexdigest()

def payload_fingerprint(value:Any)->str: return _fp(value)
def dependency_fingerprint(values:tuple[str,...]=())->str: return _fp(tuple(sorted(values)))

def make_record(record_id:str,address:str,value:Any,payload_bytes:int,*,schema='1',authority='domain://state',dependencies:tuple[str,...]=(),priority=100,prepared=False,generator=False)->StateRecord:
 if not record_id or not address or payload_bytes<0: raise ValueError('invalid record')
 return StateRecord(record_id,address,schema,authority,dependency_fingerprint(dependencies),payload_fingerprint(value),payload_bytes,int(priority),bool(prepared),bool(generator))

def make_manifest(node_id:str,records:tuple[StateRecord,...],schema='1')->StateManifest:
 if not node_id: raise ValueError('node_id required')
 ids=[r.record_id for r in records]
 if len(ids)!=len(set(ids)): raise ValueError('duplicate record id')
 ordered=tuple(sorted(records,key=lambda r:r.record_id))
 fp=_fp((node_id,schema,ordered))
 return StateManifest(node_id,ordered,schema,fp)

def _record_map(m:StateManifest): return {r.record_id:r for r in m.records}

def _estimated_ms(payload_bytes:int,n_records:int,network:NetworkCondition)->float:
 if network.bandwidth_bytes_per_sec<=0 or network.max_chunk_bytes<=0 or network.latency_ms<0 or network.timeout_ms<=0: raise ValueError('invalid network condition')
 chunks=0 if payload_bytes==0 else (payload_bytes+network.max_chunk_bytes-1)//network.max_chunk_bytes
 return (payload_bytes/network.bandwidth_bytes_per_sec)*1000.0 + network.latency_ms*max(1,chunks if n_records else 1)

def evaluate(req:ReconstructionRequest)->ReconstructionResult:
 try:
  if not req.transfer_id or not req.integrity_validated: raise ValueError('invalid request/integrity')
  if req.sender.schema_version!=req.receiver.schema_version:
   return _hold(req,Escalation.SCHEMA_MISMATCH,'Manifest schema mismatch.',full=True)
  s=_record_map(req.sender); r=_record_map(req.receiver)
  shared=[]; delta=[]; lazy=[]; mismatch_authority=[]; mismatch_dependency=[]
  for rid,sr in s.items():
   rr=r.get(rid)
   if rr is None:
    if req.allow_remote_lazy and (sr.prepared_available or sr.generator_available): lazy.append(rid)
    else: delta.append(rid)
    continue
   if rr.schema_version!=sr.schema_version: return _hold(req,Escalation.SCHEMA_MISMATCH,f'Record schema mismatch: {rid}.',full=True)
   if rr.authority_reference!=sr.authority_reference: mismatch_authority.append(rid); continue
   if rr.dependency_fingerprint!=sr.dependency_fingerprint: mismatch_dependency.append(rid); continue
   if rr.content_fingerprint==sr.content_fingerprint: shared.append(rid)
   else: delta.append(rid)
  if mismatch_authority: return _hold(req,Escalation.AUTHORITY_MISMATCH,'Authority mismatch: '+','.join(sorted(mismatch_authority)),full=True)
  if mismatch_dependency: return _hold(req,Escalation.DEPENDENCY_MISMATCH,'Dependency mismatch: '+','.join(sorted(mismatch_dependency)),full=True)
  total=len(s); shared_ratio=(len(shared)/total if total else 1.0)
  full_bytes=sum(x.payload_bytes for x in s.values())
  delta_bytes=sum(s[x].payload_bytes for x in delta)
  # Lazy materialization carries metadata only in this model; it never invents content.
  delta_bytes += sum(min(256,max(64,s[x].payload_bytes//1024)) for x in lazy)
  try:
   full_ms=_estimated_ms(full_bytes,total,req.network); dcsr_ms=_estimated_ms(delta_bytes,len(delta)+len(lazy),req.network)
  except ValueError:
   return _invalid(req,'Invalid network condition.')
  if total and shared_ratio<req.network.min_shared_ratio_for_dcsr and not lazy:
   return _hold(req,Escalation.LOW_SHARED_RATIO,'Shared ratio below DCSR threshold.',full=True,full_bytes=full_bytes,delta_bytes=delta_bytes,shared=shared,delta=delta,lazy=lazy,full_ms=full_ms,dcsr_ms=dcsr_ms)
  if dcsr_ms>req.network.timeout_ms and full_ms<=req.network.timeout_ms:
   return _hold(req,Escalation.TIMEOUT_RISK,'DCSR path exceeds timeout while full transfer is viable.',full=True,full_bytes=full_bytes,delta_bytes=delta_bytes,shared=shared,delta=delta,lazy=lazy,full_ms=full_ms,dcsr_ms=dcsr_ms)
  progressive=tuple(sorted(delta+lazy,key=lambda x:(s[x].priority,x)))
  complete=(len(delta)==0 and len(lazy)==0)
  validation_passed=bool(complete and req.require_final_validation and req.sender.manifest_fingerprint==req.receiver.manifest_fingerprint)
  if complete:
   na=NextAction.REUSE_SHARED_STATE_CANDIDATE; es=EngineState.SHARED_REUSE_CANDIDATE; reason='All sender records already shared and fingerprint-equivalent.'
  elif lazy and not delta:
   na=NextAction.REMOTE_LAZY_MATERIALIZATION_CANDIDATE; es=EngineState.REMOTE_LAZY_CANDIDATE; reason='Missing records have prepared/generator candidates; final validation remains required.'
  else:
   na=NextAction.REQUEST_DELTA_CANDIDATE; es=EngineState.DELTA_TRANSFER_CANDIDATE; reason='Request only missing/stale records; final validation remains required.'
  final_fp=_fp((req.sender.manifest_fingerprint,tuple(shared),tuple(delta),tuple(lazy),progressive))
  return ReconstructionResult(Decision.ALLOW,na,Escalation.NONE,es,req.transfer_id,tuple(sorted(shared)),tuple(sorted(delta)),tuple(sorted(lazy)),progressive,final_fp,req.sender.manifest_fingerprint,req.receiver.manifest_fingerprint,shared_ratio,full_bytes,delta_bytes,full_ms,dcsr_ms,req.require_final_validation,validation_passed,complete,False,reason,True,False,False)
 except (TypeError,ValueError):
  return _invalid(req,'Invalid reconstruction request.')

def _invalid(req,reason):
 return ReconstructionResult(Decision.DENY,NextAction.RETAIN_NO_EXECUTION_CANDIDATE,Escalation.INVALID_INPUT,EngineState.INVALID_REQUEST,getattr(req,'transfer_id',''),(),(),(),(),_fp(('invalid',reason)),getattr(getattr(req,'sender',None),'manifest_fingerprint',''),getattr(getattr(req,'receiver',None),'manifest_fingerprint',''),0.0,0,0,0.0,0.0,True,False,False,False,reason,False,False,False)

def _hold(req,esc,reason,*,full=False,full_bytes=0,delta_bytes=0,shared=(),delta=(),lazy=(),full_ms=0.0,dcsr_ms=0.0):
 return ReconstructionResult(Decision.HOLD,NextAction.FULL_TRANSFER_FALLBACK_CANDIDATE if full else NextAction.NORMAL_COMPUTATION_FALLBACK_CANDIDATE,esc,EngineState.FULL_TRANSFER_FALLBACK_CANDIDATE if full else EngineState.HOLD_CANDIDATE,req.transfer_id,tuple(sorted(shared)),tuple(sorted(delta)),tuple(sorted(lazy)),(),_fp(('hold',esc.value,reason)),req.sender.manifest_fingerprint,req.receiver.manifest_fingerprint,(len(shared)/len(req.sender.records) if req.sender.records else 1.0),full_bytes,delta_bytes,full_ms,dcsr_ms,True,False,False,False,reason,False,full,not full)

def validate_final(req:ReconstructionRequest,received_manifest:StateManifest)->ReconstructionResult:
 base=evaluate(req)
 # A low-shared-ratio or timeout-risk planning HOLD may legitimately choose a Full Transfer.
 # Final validation must still be able to validate that completed fallback transfer.
 if base.decision==Decision.DENY: return base
 if base.decision==Decision.HOLD and base.escalation not in (Escalation.LOW_SHARED_RATIO,Escalation.TIMEOUT_RISK): return base
 if received_manifest.schema_version!=req.sender.schema_version: return _hold(req,Escalation.SCHEMA_MISMATCH,'Final manifest schema mismatch.',full=True)
 sm=_record_map(req.sender); fm=_record_map(received_manifest)
 if set(sm)!=set(fm): return _hold(req,Escalation.PARTIAL_STATE,'Final reconstructed state is partial.',full=True)
 for rid,sr in sm.items():
  fr=fm[rid]
  if fr.authority_reference!=sr.authority_reference: return _hold(req,Escalation.AUTHORITY_MISMATCH,f'Final authority mismatch: {rid}.',full=True)
  if fr.dependency_fingerprint!=sr.dependency_fingerprint: return _hold(req,Escalation.DEPENDENCY_MISMATCH,f'Final dependency mismatch: {rid}.',full=True)
  if fr.content_fingerprint!=sr.content_fingerprint: return _hold(req,Escalation.FINGERPRINT_MISMATCH,f'Final fingerprint mismatch: {rid}.',full=True)
 return replace(base,decision=Decision.ALLOW,next_action=NextAction.REUSE_SHARED_STATE_CANDIDATE,escalation=Escalation.NONE,engine_state=EngineState.SHARED_REUSE_CANDIDATE,shared_record_ids=tuple(sorted(sm)),delta_record_ids=(),lazy_record_ids=(),progressive_order=(),receiver_manifest_fingerprint=received_manifest.manifest_fingerprint,shared_ratio=1.0,delta_payload_bytes=0,final_candidate_fingerprint=req.sender.manifest_fingerprint,final_validation_passed=True,reconstructed_complete=True,next_gate_candidate=True,full_transfer_candidate=False,normal_computation_candidate=False,reason='Final fingerprint/schema/authority/dependency validation passed after selected transfer/fallback path; result remains non-authoritative.')

def prepare_state(req:ReconstructionRequest)->PreparedState:
 r=evaluate(req); qf=_fp(req); rf=_fp(r); integ=_fp((qf,rf,'DCSR-186-PREPARED'))
 return PreparedState(req,r,qf,rf,integ)

def evaluate_prepared(st:PreparedState,*,integrity_validated:bool,current_request_fingerprint:str,current_result_fingerprint:str,current_integrity_fingerprint:str,current_request:ReconstructionRequest)->ReconstructionResult:
 if not integrity_validated or current_request_fingerprint!=st.request_fingerprint or current_result_fingerprint!=st.result_fingerprint or current_integrity_fingerprint!=st.integrity_fingerprint or _fp(current_request)!=st.request_fingerprint:
  return _hold(current_request,Escalation.PREPARED_STATE_STALE,'Prepared DCSR state did not pass current integrity/request/result binding.',full=False)
 return replace(st.result,prepared_state_reused=True)

def make_delta(req:ReconstructionRequest)->ManifestDelta:
 r=evaluate(req); ids=tuple(sorted(r.delta_record_ids)); lazy=tuple(sorted(r.lazy_record_ids)); reused=tuple(sorted(r.shared_record_ids)); meta=len(_canon((ids,lazy,reused,req.sender.manifest_fingerprint)))
 full=(r.decision!=Decision.ALLOW or r.full_transfer_candidate)
 return ManifestDelta(req.transfer_id,ids,reused,lazy,meta,full,_fp((req.transfer_id,ids,reused,lazy,meta,full)))

def plan_missing_only(req:ReconstructionRequest)->MissingOnlyPlan:
 d=make_delta(req)
 if d.full_resend_required: return MissingOnlyPlan(('FULL_STATE',),d.metadata_bytes,True)
 ids=tuple(f'RECORD:{x}' for x in d.requested_record_ids)+tuple(f'LAZY:{x}' for x in d.lazy_record_ids)
 return MissingOnlyPlan(ids,d.metadata_bytes,False)

def default_request()->ReconstructionRequest:
 vals={'A':{'kind':'intent','v':1},'B':{'kind':'context','v':2},'C':{'kind':'evidence','v':3},'D':{'kind':'artifact','v':4}}
 sender=make_manifest('sender',tuple(make_record(k,f'al://state/{k.lower()}',v,100_000+10_000*i,authority='domain://control',priority=i+1,prepared=(k=='D')) for i,(k,v) in enumerate(vals.items())))
 # Receiver shares A/B/C exactly; D is absent and can be materialized only from an explicitly advertised prepared candidate.
 receiver=make_manifest('receiver',sender.records[:3])
 return ReconstructionRequest('DCSR-186-A',sender,receiver,NetworkCondition(),True,True,True)

def default_evaluation()->ReconstructionResult: return evaluate(default_request())
