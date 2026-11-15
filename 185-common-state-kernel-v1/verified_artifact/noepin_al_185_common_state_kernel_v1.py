"""NOEPIN AL 185 — Common State Kernel V1 completion successor.

Pure in-memory state infrastructure. It does not grant domain authority, execute actions,
or perform filesystem/network/process I/O. Kernel outputs remain non-authoritative candidates.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
from hashlib import sha256
import json
from typing import Any

class Decision(str,Enum): ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class NextAction(str,Enum):
 USE_DIRECT_STATE_CANDIDATE='USE_DIRECT_STATE_CANDIDATE'; USE_PREPARED_STATE_CANDIDATE='USE_PREPARED_STATE_CANDIDATE'; USE_LAZY_MATERIALIZATION_CANDIDATE='USE_LAZY_MATERIALIZATION_CANDIDATE'; NORMAL_COMPUTATION_FALLBACK_CANDIDATE='NORMAL_COMPUTATION_FALLBACK_CANDIDATE'; RETAIN_NO_EXECUTION_CANDIDATE='RETAIN_NO_EXECUTION_CANDIDATE'
class Escalation(str,Enum):
 NONE='NONE'; UNKNOWN_OR_AMBIGUOUS='UNKNOWN_OR_AMBIGUOUS'; SCHEMA_MISMATCH='SCHEMA_MISMATCH'; AUTHORITY_MISMATCH='AUTHORITY_MISMATCH'; DEPENDENCY_CYCLE='DEPENDENCY_CYCLE'; DEPTH_OVERFLOW='DEPTH_OVERFLOW'; BUDGET_OVERFLOW='BUDGET_OVERFLOW'; STALE_STATE='STALE_STATE'; PARTIAL_PUBLICATION='PARTIAL_PUBLICATION'; PREPARED_STATE_STALE='PREPARED_STATE_STALE'; INVALID_INPUT='INVALID_INPUT'
class EngineState(str,Enum):
 DIRECT_STATE_CANDIDATE='DIRECT_STATE_CANDIDATE'; PREPARED_STATE_CANDIDATE='PREPARED_STATE_CANDIDATE'; MATERIALIZED_STATE_CANDIDATE='MATERIALIZED_STATE_CANDIDATE'; FALLBACK_CANDIDATE='FALLBACK_CANDIDATE'; HOLD_CANDIDATE='HOLD_CANDIDATE'; INVALID_REQUEST='INVALID_REQUEST'

@dataclass(frozen=True)
class StateAddress:
 domain:str; resource:str; version:str; scope:str=''; variant:str=''; qualifiers:tuple[tuple[str,str],...]=()
@dataclass(frozen=True)
class StateMeta:
 schema_version:str='1'; authority_version:str|None=None; authority_reference:str|None=None; context_fingerprint:str|None=None; temporal_sequence:int|None=None; dependency_fingerprint:str|None=None; expires_at:int|None=None; semantics:str='state-fragment'
@dataclass(frozen=True)
class StateEntry: value:Any; meta:StateMeta; fingerprint:str
@dataclass(frozen=True)
class PreparedSpec: parts:tuple[Any,...]; operation:str; meta:StateMeta
@dataclass(frozen=True)
class GeneratorSpec: dependencies:tuple[str,...]; operation:str; meta:StateMeta
@dataclass(frozen=True)
class ResolveRequest:
 kernel_id:str; address:StateAddress|str; schema_version:str='1'; authority_version:str|None='auth-v1'; context_fingerprint:str|None='ctx'; temporal_sequence:int|None=7; dependency_fingerprint:str|None=None; known:bool=True; ambiguous:bool=False; unsupported:bool=False; now:int=0
@dataclass(frozen=True)
class ResolveResult:
 decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState; kernel_id:str; address:str; value:Any; source:str|None; result_fingerprint:str; authoritative:bool; authority_reference:str|None; next_gate_candidate:bool; full_recompute_candidate:bool; reason:str
 prepared_state_reused:bool=False
 permission_granted:bool=False; permit_issued:bool=False; approval_executed:bool=False; human_approval_executed:bool=False; tool_invoked:bool=False; action_executed:bool=False; action_success:bool=False; stop_executed:bool=False; file_write_executed:bool=False; network_send_executed:bool=False; external_write_performed:bool=False
 world_truth_proven:bool=False; domain_authority_promoted:bool=False; memory_promoted_to_truth:bool=False; belief_promoted_to_truth:bool=False; candidate_promoted_to_actual:bool=False; intent_promoted_to_action:bool=False; action_request_promoted_to_success:bool=False; private_state_promoted_to_world_fact:bool=False; cached_result_promoted_to_authoritative:bool=False; materialized_state_promoted_to_semantically_existing:bool=False; unknown_promoted_to_known:bool=False; safety_proven:bool=False
 dcsr_invented_state:bool=False; dcsr_bypassed_authority:bool=False; dcsr_bypassed_schema:bool=False; dcsr_bypassed_dependency:bool=False; dcsr_promoted_cache_to_truth:bool=False
@dataclass(frozen=True)
class KernelSnapshot:
 schema_version:str; materialized:tuple[tuple[str,StateEntry],...]; cache:tuple[tuple[str,StateEntry],...]; fingerprint:str
@dataclass(frozen=True)
class PreparedState:
 request:ResolveRequest; result:ResolveResult; request_fingerprint:str; result_fingerprint:str; integrity_fingerprint:str
@dataclass(frozen=True)
class StateDelta: kernel_id:str; changed_fields:tuple[str,...]; values:tuple[tuple[str,Any],...]; fingerprint:str
@dataclass(frozen=True)
class MissingOnlyPlan: missing_or_changed_record_ids:tuple[str,...]; metadata_bytes_required:int; full_resend_required:bool

_FALSE_FIELDS=('permission_granted','permit_issued','approval_executed','human_approval_executed','tool_invoked','action_executed','action_success','stop_executed','file_write_executed','network_send_executed','external_write_performed','world_truth_proven','domain_authority_promoted','memory_promoted_to_truth','belief_promoted_to_truth','candidate_promoted_to_actual','intent_promoted_to_action','action_request_promoted_to_success','private_state_promoted_to_world_fact','cached_result_promoted_to_authoritative','materialized_state_promoted_to_semantically_existing','unknown_promoted_to_known','safety_proven','dcsr_invented_state','dcsr_bypassed_authority','dcsr_bypassed_schema','dcsr_bypassed_dependency','dcsr_promoted_cache_to_truth')

def _norm(v):
 if isinstance(v,Enum): return v.value
 if is_dataclass(v): return {f.name:_norm(getattr(v,f.name)) for f in fields(v)}
 if isinstance(v,dict): return {str(k):_norm(v[k]) for k in sorted(v,key=lambda x:str(x))}
 if isinstance(v,(tuple,list)): return [_norm(x) for x in v]
 if isinstance(v,(set,frozenset)): return sorted((_norm(x) for x in v),key=lambda x:json.dumps(x,sort_keys=True,separators=(',',':')))
 return v

def _canon(v)->bytes: return json.dumps(_norm(v),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def _fp(v)->str: return sha256(_canon(v)).hexdigest()

def canonicalize_address(a:StateAddress|str)->str:
 if isinstance(a,str):
  if not a.strip(): raise ValueError('address string required')
  return a.strip()
 if not isinstance(a,StateAddress): raise TypeError('StateAddress or string required')
 if not a.domain.strip() or not a.resource.strip() or not a.version.strip(): raise ValueError('domain/resource/version required')
 q=tuple(sorted(((str(k),str(v)) for k,v in a.qualifiers),key=lambda x:x[0]))
 return f"{a.domain.strip().lower()}::{a.resource.strip()}::{a.version.strip()}::{a.scope.strip()}::{a.variant.strip()}::{_fp(q)}"

def dependency_fingerprint(deps:tuple[tuple[str,str|None],...]|tuple=())->str:
 norm=tuple(sorted(((canonicalize_address(a),fp) for a,fp in deps),key=lambda x:x[0]))
 return _fp(norm)

def cache_key(req:ResolveRequest)->str:
 return _fp((canonicalize_address(req.address),req.authority_version,req.context_fingerprint,req.temporal_sequence,req.dependency_fingerprint,req.schema_version))

def _compose(parts:tuple[Any,...],op:str):
 if op=='SUM': return sum(parts)
 if op=='CONCAT': return ''.join(str(x) for x in parts)
 if op=='TUPLE': return tuple(parts)
 if op=='MERGE_DICT':
  out={}
  for p in parts:
   if not isinstance(p,dict): raise ValueError('MERGE_DICT requires dict parts')
   out.update(p)
  return out
 if op=='FIRST': return parts[0] if parts else None
 raise ValueError('unsupported composition operation')

def _generate(dep_values:tuple[Any,...],op:str):
 if op=='SUM': return sum(dep_values)
 if op=='MERGE_DICT': return _compose(dep_values,'MERGE_DICT')
 if op=='TUPLE': return tuple(dep_values)
 if op=='FIRST': return dep_values[0] if dep_values else None
 raise ValueError('unsupported generator operation')

class CommonStateKernel:
 def __init__(self,schema_version='1',max_materializations_per_resolve=64,max_dependency_depth=32):
  if not str(schema_version).strip(): raise ValueError('schema_version required')
  if not isinstance(max_materializations_per_resolve,int) or max_materializations_per_resolve<1: raise ValueError('materialization budget invalid')
  if not isinstance(max_dependency_depth,int) or max_dependency_depth<0: raise ValueError('dependency depth invalid')
  self.schema_version=str(schema_version); self.max_materializations_per_resolve=max_materializations_per_resolve; self.max_dependency_depth=max_dependency_depth
  self.materialized={}; self.prepared={}; self.generators={}; self.cache={}; self.index={}; self.staging={}
 def _index(self,address):
  p=address.split('::'); d=p[0]; r=p[1] if len(p)>1 else ''
  self.index.setdefault(d,{}).setdefault(r,set()).add(address)
 def query_index(self,domain,resource): return tuple(sorted(self.index.get(str(domain).lower(),{}).get(resource,set())))
 def register_materialized(self,address,value,meta=StateMeta()):
  a=canonicalize_address(address); mf=replace(meta,dependency_fingerprint=meta.dependency_fingerprint or dependency_fingerprint(())); e=StateEntry(value,mf,_fp(value)); self.materialized[a]=e; self._index(a); return e.fingerprint
 def register_prepared(self,address,parts,operation,meta=StateMeta()):
  a=canonicalize_address(address); self.prepared[a]=PreparedSpec(tuple(parts),operation,meta); self._index(a)
 def register_generator(self,address,dependencies,operation,meta=StateMeta()):
  a=canonicalize_address(address); deps=tuple(canonicalize_address(d) for d in dependencies); self.generators[a]=GeneratorSpec(deps,operation,meta); self._index(a)
 def _valid(self,meta,req):
  if meta.schema_version!=req.schema_version: return False,'schema-mismatch'
  if req.authority_version is not None and meta.authority_version is not None and meta.authority_version!=req.authority_version: return False,'authority-mismatch'
  if req.context_fingerprint is not None and meta.context_fingerprint is not None and meta.context_fingerprint!=req.context_fingerprint: return False,'context-mismatch'
  if req.temporal_sequence is not None and meta.temporal_sequence is not None and meta.temporal_sequence!=req.temporal_sequence: return False,'temporal-mismatch'
  if req.dependency_fingerprint is not None and meta.dependency_fingerprint is not None and meta.dependency_fingerprint!=req.dependency_fingerprint: return False,'dependency-mismatch'
  if meta.expires_at is not None and meta.expires_at<req.now: return False,'stale'
  return True,''
 def cache_put(self,req,value,meta): self.cache[cache_key(req)]=StateEntry(value,meta,_fp(value)); return cache_key(req)
 def cache_get(self,req):
  e=self.cache.get(cache_key(req));
  if e is None: return None
  ok,_=self._valid(e.meta,req); return e if ok else None
 def stage_publication(self,token,address,value,meta=StateMeta()):
  if not token or token in self.staging: raise ValueError('unique token required')
  self.staging[token]=(canonicalize_address(address),value,meta); return token
 def commit_publication(self,token,validation_evidence):
  if token not in self.staging: raise ValueError('unknown stage token')
  item=self.staging.pop(token)
  if validation_evidence is not True: raise ValueError('publication validation failed')
  return self.register_materialized(*item)
 def abort_publication(self,token): return self.staging.pop(token,None) is not None
 def _result(self,req,decision,next_action,esc,state,value=None,source=None,authority_reference=None,next_gate=False,full=False,reason=''):
  a=canonicalize_address(req.address); fp=_fp((req.kernel_id,a,value,source,decision.value,next_action.value,esc.value,state.value,reason))
  return ResolveResult(decision,next_action,esc,state,req.kernel_id,a,value,source,fp,False,authority_reference,next_gate,full,reason)
 def resolve(self,req):
  if not isinstance(req,ResolveRequest): raise TypeError('ResolveRequest required')
  try: a=canonicalize_address(req.address)
  except Exception as e: return self._result(replace(req,address='invalid::invalid::invalid'),Decision.DENY,NextAction.RETAIN_NO_EXECUTION_CANDIDATE,Escalation.INVALID_INPUT,EngineState.INVALID_REQUEST,reason=str(e))
  if not req.kernel_id.strip(): return self._result(req,Decision.DENY,NextAction.RETAIN_NO_EXECUTION_CANDIDATE,Escalation.INVALID_INPUT,EngineState.INVALID_REQUEST,reason='kernel_id required')
  if not req.known or req.ambiguous or req.unsupported: return self._result(req,Decision.HOLD,NextAction.NORMAL_COMPUTATION_FALLBACK_CANDIDATE,Escalation.UNKNOWN_OR_AMBIGUOUS,EngineState.FALLBACK_CANDIDATE,full=True,reason='unknown/ambiguous/unsupported; normal computation required')
  c=self.cache_get(req)
  if c is not None: return self._result(req,Decision.ALLOW,NextAction.USE_DIRECT_STATE_CANDIDATE,Escalation.NONE,EngineState.DIRECT_STATE_CANDIDATE,c.value,'cache',c.meta.authority_reference,True,False,'Integrity/context/authority matched cache candidate.')
  direct=self.materialized.get(a)
  if direct is not None:
   ok,why=self._valid(direct.meta,req)
   if ok: return self._result(req,Decision.ALLOW,NextAction.USE_DIRECT_STATE_CANDIDATE,Escalation.NONE,EngineState.DIRECT_STATE_CANDIDATE,direct.value,'materialized',direct.meta.authority_reference,True,False,'Direct state candidate matched.')
   if why in {'schema-mismatch','authority-mismatch','dependency-mismatch'}:
    esc={'schema-mismatch':Escalation.SCHEMA_MISMATCH,'authority-mismatch':Escalation.AUTHORITY_MISMATCH,'dependency-mismatch':Escalation.AUTHORITY_MISMATCH}[why]
    return self._result(req,Decision.HOLD,NextAction.NORMAL_COMPUTATION_FALLBACK_CANDIDATE,esc,EngineState.HOLD_CANDIDATE,full=True,reason=why)
  ps=self.prepared.get(a)
  if ps is not None:
   ok,why=self._valid(ps.meta,req)
   if ok:
    try: v=_compose(ps.parts,ps.operation)
    except Exception as e: return self._result(req,Decision.HOLD,NextAction.NORMAL_COMPUTATION_FALLBACK_CANDIDATE,Escalation.INVALID_INPUT,EngineState.FALLBACK_CANDIDATE,full=True,reason='prepared composition failed: '+str(e))
    return self._result(req,Decision.ALLOW,NextAction.USE_PREPARED_STATE_CANDIDATE,Escalation.NONE,EngineState.PREPARED_STATE_CANDIDATE,v,'prepared',ps.meta.authority_reference,True,False,'Prepared parts candidate composed.')
  try:
   got=self._materialize(a,req,(),0,[0])
  except RuntimeError as e:
   code=str(e); mapping={'DEPENDENCY_CYCLE':Escalation.DEPENDENCY_CYCLE,'DEPTH_OVERFLOW':Escalation.DEPTH_OVERFLOW,'BUDGET_OVERFLOW':Escalation.BUDGET_OVERFLOW,'SCHEMA_MISMATCH':Escalation.SCHEMA_MISMATCH,'AUTHORITY_MISMATCH':Escalation.AUTHORITY_MISMATCH}
   return self._result(req,Decision.HOLD,NextAction.NORMAL_COMPUTATION_FALLBACK_CANDIDATE,mapping.get(code,Escalation.INVALID_INPUT),EngineState.HOLD_CANDIDATE,full=True,reason=code)
  if got is not None: return self._result(req,Decision.ALLOW,NextAction.USE_LAZY_MATERIALIZATION_CANDIDATE,Escalation.NONE,EngineState.MATERIALIZED_STATE_CANDIDATE,got.value,'lazy-materialization',got.meta.authority_reference,True,False,'Lazy materialization candidate composed.')
  return self._result(req,Decision.HOLD,NextAction.NORMAL_COMPUTATION_FALLBACK_CANDIDATE,Escalation.UNKNOWN_OR_AMBIGUOUS,EngineState.FALLBACK_CANDIDATE,full=True,reason='normal computation required')
 def _materialize(self,address,req,path,depth,budget):
  if depth>self.max_dependency_depth: raise RuntimeError('DEPTH_OVERFLOW')
  if address in path: raise RuntimeError('DEPENDENCY_CYCLE')
  budget[0]+=1
  if budget[0]>self.max_materializations_per_resolve: raise RuntimeError('BUDGET_OVERFLOW')
  direct=self.materialized.get(address)
  if direct is not None:
   ok,why=self._valid(direct.meta,req)
   if ok: return direct
   if why=='schema-mismatch': raise RuntimeError('SCHEMA_MISMATCH')
   if why=='authority-mismatch': raise RuntimeError('AUTHORITY_MISMATCH')
  spec=self.generators.get(address)
  if spec is None: return None
  if spec.meta.schema_version!=req.schema_version: raise RuntimeError('SCHEMA_MISMATCH')
  if req.authority_version is not None and spec.meta.authority_version is not None and spec.meta.authority_version!=req.authority_version: raise RuntimeError('AUTHORITY_MISMATCH')
  vals=[]
  for d in spec.dependencies:
   e=self._materialize(d,req,path+(address,),depth+1,budget)
   if e is None: return None
   vals.append(e.value)
  v=_generate(tuple(vals),spec.operation)
  meta=replace(spec.meta,context_fingerprint=req.context_fingerprint,temporal_sequence=req.temporal_sequence,dependency_fingerprint=dependency_fingerprint(tuple((d,self.materialized[d].fingerprint if d in self.materialized else None) for d in spec.dependencies)),semantics='materialized-candidate')
  return StateEntry(v,meta,_fp(v))
 def snapshot(self):
  mat=tuple(sorted(self.materialized.items())); cache=tuple(sorted(self.cache.items())); fp=_fp((self.schema_version,mat,cache)); return KernelSnapshot(self.schema_version,mat,cache,fp)

def default_address(): return StateAddress('MEMORY','profile','v1','user','',(('locale','ja-JP'),))
def default_meta(): return StateMeta('1','auth-v1','domain://memory','ctx',7,dependency_fingerprint(()),None,'memory-candidate')
def default_request(): return ResolveRequest('CSK-185-A',default_address(),'1','auth-v1','ctx',7,dependency_fingerprint(()),True,False,False,0)
def make_request(**kwargs): return replace(default_request(),**kwargs)
def build_default_kernel():
 k=CommonStateKernel('1'); k.register_materialized(default_address(),{'display_name':'NOEPIN','locale':'ja-JP'},default_meta()); return k
def evaluate(req): return build_default_kernel().resolve(req)
def default_evaluation(): return evaluate(default_request())

def prepare_state(req):
 r=evaluate(req); rf=_fp(req); sf=r.result_fingerprint; integ=_fp((rf,sf,'NOEPIN_AL_185_PREPARED_V1')); return PreparedState(req,r,rf,sf,integ)
def evaluate_prepared(st,*,integrity_validated,current_request_fingerprint,current_result_fingerprint,current_integrity_fingerprint,current_request):
 cur=_fp(current_request); expected=_fp((st.request_fingerprint,st.result_fingerprint,'NOEPIN_AL_185_PREPARED_V1'))
 if not integrity_validated or current_request_fingerprint!=st.request_fingerprint or current_result_fingerprint!=st.result_fingerprint or current_integrity_fingerprint!=st.integrity_fingerprint or st.integrity_fingerprint!=expected or cur!=st.request_fingerprint:
  r=evaluate(current_request); return replace(r,decision=Decision.HOLD,next_action=NextAction.NORMAL_COMPUTATION_FALLBACK_CANDIDATE,escalation=Escalation.PREPARED_STATE_STALE,engine_state=EngineState.HOLD_CANDIDATE,next_gate_candidate=False,full_recompute_candidate=True,reason='Prepared state did not independently match current request/result/integrity.',prepared_state_reused=False)
 return replace(st.result,prepared_state_reused=True)
def make_delta(old,new):
 changed=[]; vals=[]
 for f in fields(ResolveRequest):
  if getattr(old,f.name)!=getattr(new,f.name): changed.append(f.name); vals.append((f.name,getattr(new,f.name)))
 return StateDelta(new.kernel_id,tuple(changed),tuple(vals),_fp((new.kernel_id,changed,vals)))
def plan_missing_only(old,new):
 d=make_delta(old,new)
 if old.kernel_id!=new.kernel_id or old.schema_version!=new.schema_version:
  ids=('FULL_KERNEL_STATE',); full=True
 else:
  ids=tuple('REQUEST_FIELD:'+x for x in d.changed_fields); full=False
 return MissingOnlyPlan(ids,len(_canon((ids,d.values))),full)
