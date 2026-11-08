"""NOEPIN AL 060 — AI Stop / Completion Condition Checker.

Pure control-plane evaluator for Success Criteria / Stop Condition / Max Steps.
It evaluates caller-supplied Task Progress, Success Criterion and Dependency State
metadata with freshness, binding, scope and policy constraints. It returns only
completion/stop/continue candidates. It does not stop an AI, commit task success,
expand scope, execute cleanup, or prove production success/safety.

Creator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support using ChatGPT
License / Rights: NOT SPECIFIED
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Any, FrozenSet, Iterable, Mapping, Tuple

class ControlDecision(str, Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class TaskDisposition(str, Enum):
    CONTINUE='CONTINUE'; COMPLETE_CANDIDATE='COMPLETE_CANDIDATE'; STOP_CANDIDATE='STOP_CANDIDATE'; HOLD='HOLD'

@dataclass(frozen=True)
class CompletionPolicy:
    policy_id:str; version:str; authority_epoch:int; issued_at:int; expires_at:int
    max_steps:int; max_elapsed_seconds:int; max_no_progress_steps:int; max_evidence_age_seconds:int
    require_independent_evidence:bool; require_all_required_dependencies:bool; deny_scope_creep:bool
    min_required_criteria:int=1; revoked:bool=False
    def validate(self,now:int)->None:
        if not self.policy_id or not self.version or self.authority_epoch<1: raise ValueError('policy identity invalid')
        if self.issued_at<0 or self.expires_at<=self.issued_at or not self.issued_at<=now<self.expires_at: raise ValueError('policy not current')
        if self.max_steps<1 or self.max_elapsed_seconds<1 or self.max_no_progress_steps<1 or self.max_evidence_age_seconds<1: raise ValueError('policy numeric limits invalid')
        if self.min_required_criteria<1: raise ValueError('criterion threshold invalid')
        if self.revoked: raise ValueError('policy revoked')

@dataclass(frozen=True)
class TaskProgressState:
    progress_id:str; task_id:str; scope_fingerprint:str; current_step:int; elapsed_seconds:int; no_progress_steps:int
    cancelled:bool; fatal_error:bool; requested_extra_work:bool; observed_at:int; expires_at:int
    verified:bool; independent:bool; evidence_binding:str; revoked:bool=False
    def validate(self)->None:
        if not all((self.progress_id,self.task_id,self.scope_fingerprint,self.evidence_binding)): raise ValueError('progress identity invalid')
        if self.current_step<0 or self.elapsed_seconds<0 or self.no_progress_steps<0: raise ValueError('progress counters invalid')
        if self.observed_at<0 or self.expires_at<=self.observed_at: raise ValueError('progress time invalid')

@dataclass(frozen=True)
class SuccessCriterion:
    criterion_id:str; task_id:str; required:bool; satisfied:bool; verified:bool; independent:bool
    observed_at:int; expires_at:int; evidence_binding:str; revoked:bool=False
    def validate(self)->None:
        if not all((self.criterion_id,self.task_id,self.evidence_binding)): raise ValueError('criterion identity invalid')
        if self.observed_at<0 or self.expires_at<=self.observed_at: raise ValueError('criterion time invalid')

@dataclass(frozen=True)
class DependencyState:
    dependency_id:str; task_id:str; required:bool; completed:bool; failed:bool; verified:bool; independent:bool
    observed_at:int; expires_at:int; evidence_binding:str; revoked:bool=False
    def validate(self)->None:
        if not all((self.dependency_id,self.task_id,self.evidence_binding)): raise ValueError('dependency identity invalid')
        if self.observed_at<0 or self.expires_at<=self.observed_at: raise ValueError('dependency time invalid')
        if self.completed and self.failed: raise ValueError('dependency cannot be completed and failed')

@dataclass(frozen=True)
class TaskCheckRequest:
    request_id:str; task_id:str; expected_scope_fingerprint:str; expected_policy_id:str; expected_policy_version:str
    expected_authority_epoch:int; evidence_binding:str
    def validate(self)->None:
        if not all((self.request_id,self.task_id,self.expected_scope_fingerprint,self.expected_policy_id,self.expected_policy_version,self.evidence_binding)): raise ValueError('request identity invalid')
        if self.expected_authority_epoch<1: raise ValueError('request authority invalid')

@dataclass(frozen=True)
class PreparedCompletionRegistry:
    registry_fingerprint:str; policy_fingerprint:str
    progress:Tuple[TaskProgressState,...]; criteria:Tuple[SuccessCriterion,...]; dependencies:Tuple[DependencyState,...]
    progress_fingerprints:Mapping[str,str]; criterion_fingerprints:Mapping[str,str]; dependency_fingerprints:Mapping[str,str]
    task_progress_index:Mapping[str,Tuple[str,...]]; task_criterion_index:Mapping[str,Tuple[str,...]]; task_dependency_index:Mapping[str,Tuple[str,...]]

@dataclass(frozen=True)
class CompletionRegistryDelta:
    base_fingerprint:str; target_fingerprint:str
    changed_progress:Tuple[TaskProgressState,...]; removed_progress_ids:Tuple[str,...]; added_progress:Tuple[TaskProgressState,...]
    changed_criteria:Tuple[SuccessCriterion,...]; removed_criterion_ids:Tuple[str,...]; added_criteria:Tuple[SuccessCriterion,...]
    changed_dependencies:Tuple[DependencyState,...]; removed_dependency_ids:Tuple[str,...]; added_dependencies:Tuple[DependencyState,...]

@dataclass(frozen=True)
class RegistrySyncPlan:
    missing_or_changed_progress_ids:Tuple[str,...]; missing_or_changed_criterion_ids:Tuple[str,...]; missing_or_changed_dependency_ids:Tuple[str,...]
    metadata_bytes_required:int; full_metadata_bytes:int; full_resend_required:bool
    permission_granted:bool=False; task_success_authorized:bool=False; stop_execution_authorized:bool=False; scope_expansion_authorized:bool=False; cleanup_execution_authorized:bool=False

@dataclass(frozen=True)
class CompletionAssessment:
    decision:ControlDecision; disposition:TaskDisposition; request_id:str; task_id:str; reasons:Tuple[str,...]
    completion_candidate:bool; stop_candidate:bool; continue_candidate:bool; scope_creep_detected:bool
    active_required_criteria:int; satisfied_required_criteria:int; active_required_dependencies:int; completed_required_dependencies:int
    current_step:int; elapsed_seconds:int; no_progress_steps:int
    registry_fingerprint:str; policy_fingerprint:str; request_fingerprint:str
    permission_granted:bool=False; task_success_committed:bool=False; stop_executed:bool=False; scope_expansion_committed:bool=False
    cleanup_executed:bool=False; partial_state_authoritative:bool=False; success_truth_proven:bool=False; safety_proven:bool=False; action_success:bool=False

def _canonical(v:Any)->Any:
    if isinstance(v,Enum): return v.value
    if is_dataclass(v): return {f.name:_canonical(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v,Mapping): return {str(k):_canonical(x) for k,x in sorted(v.items(),key=lambda kv:str(kv[0]))}
    if isinstance(v,(set,frozenset)): return sorted((_canonical(x) for x in v),key=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')))
    if isinstance(v,(tuple,list)): return [_canonical(x) for x in v]
    return v

def canonical_json(v:Any)->str: return json.dumps(_canonical(v),ensure_ascii=False,sort_keys=True,separators=(',',':'))
def fingerprint(v:Any)->str: return sha256(canonical_json(v).encode()).hexdigest()
def _progress(xs:Iterable[TaskProgressState])->Tuple[TaskProgressState,...]: return tuple(sorted(xs,key=lambda x:x.progress_id))
def _criteria(xs:Iterable[SuccessCriterion])->Tuple[SuccessCriterion,...]: return tuple(sorted(xs,key=lambda x:x.criterion_id))
def _deps(xs:Iterable[DependencyState])->Tuple[DependencyState,...]: return tuple(sorted(xs,key=lambda x:x.dependency_id))
def registry_fingerprint(progress,criteria,dependencies)->str: return fingerprint({'progress':_progress(progress),'criteria':_criteria(criteria),'dependencies':_deps(dependencies)})

def prepare_registry(policy:CompletionPolicy,progress:Iterable[TaskProgressState],criteria:Iterable[SuccessCriterion],dependencies:Iterable[DependencyState],*,now:int)->PreparedCompletionRegistry:
    policy.validate(now); ps=_progress(progress); cs=_criteria(criteria); ds=_deps(dependencies)
    for x in ps: x.validate()
    for x in cs: x.validate()
    for x in ds: x.validate()
    if len({x.progress_id for x in ps})!=len(ps): raise ValueError('duplicate progress id')
    if len({x.criterion_id for x in cs})!=len(cs): raise ValueError('duplicate criterion id')
    if len({x.dependency_id for x in ds})!=len(ds): raise ValueError('duplicate dependency id')
    tasks={x.task_id for x in ps}
    if any(x.task_id not in tasks for x in cs+ds): raise ValueError('evidence references unknown task')
    pi={}; ci={}; di={}
    for x in ps: pi.setdefault(x.task_id,[]).append(x.progress_id)
    for x in cs: ci.setdefault(x.task_id,[]).append(x.criterion_id)
    for x in ds: di.setdefault(x.task_id,[]).append(x.dependency_id)
    return PreparedCompletionRegistry(
        registry_fingerprint(ps,cs,ds),fingerprint(policy),ps,cs,ds,
        {x.progress_id:fingerprint(x) for x in ps},{x.criterion_id:fingerprint(x) for x in cs},{x.dependency_id:fingerprint(x) for x in ds},
        {k:tuple(sorted(v)) for k,v in pi.items()},{k:tuple(sorted(v)) for k,v in ci.items()},{k:tuple(sorted(v)) for k,v in di.items()})

def _inactive(now:int,observed_at:int,expires_at:int,verified:bool,independent:bool,revoked:bool,binding:str,expected_binding:str,policy:CompletionPolicy)->bool:
    if revoked or not verified or binding!=expected_binding: return True
    if policy.require_independent_evidence and not independent: return True
    if not observed_at<=now<expires_at: return True
    if now-observed_at>policy.max_evidence_age_seconds: return True
    return False

def _empty(req:TaskCheckRequest,policy:CompletionPolicy,reg:PreparedCompletionRegistry,decision:ControlDecision,reasons:Tuple[str,...])->CompletionAssessment:
    return CompletionAssessment(decision,TaskDisposition.HOLD,getattr(req,'request_id',''),getattr(req,'task_id',''),reasons,False,False,False,False,0,0,0,0,0,0,0,getattr(reg,'registry_fingerprint',''),fingerprint(policy),fingerprint(req))

def evaluate_prepared(req:TaskCheckRequest,policy:CompletionPolicy,reg:PreparedCompletionRegistry,*,now:int)->CompletionAssessment:
    try: req.validate(); policy.validate(now)
    except Exception as e: return _empty(req,policy,reg,ControlDecision.HOLD,(f'INVALID_REQUEST_OR_POLICY:{type(e).__name__}',))
    if reg.policy_fingerprint!=fingerprint(policy): return _empty(req,policy,reg,ControlDecision.HOLD,('POLICY_FINGERPRINT_MISMATCH',))
    if reg.registry_fingerprint!=registry_fingerprint(reg.progress,reg.criteria,reg.dependencies): return _empty(req,policy,reg,ControlDecision.HOLD,('REGISTRY_FINGERPRINT_MISMATCH',))
    if (req.expected_policy_id,req.expected_policy_version,req.expected_authority_epoch)!=(policy.policy_id,policy.version,policy.authority_epoch): return _empty(req,policy,reg,ControlDecision.HOLD,('POLICY_BINDING_MISMATCH',))
    progress=[x for x in reg.progress if x.task_id==req.task_id]
    if len(progress)!=1: return _empty(req,policy,reg,ControlDecision.HOLD,('TASK_PROGRESS_NOT_UNIQUE',))
    p=progress[0]
    if _inactive(now,p.observed_at,p.expires_at,p.verified,p.independent,p.revoked,p.evidence_binding,req.evidence_binding,policy): return _empty(req,policy,reg,ControlDecision.HOLD,('TASK_PROGRESS_EVIDENCE_INVALID',))
    if p.scope_fingerprint!=req.expected_scope_fingerprint:
        return CompletionAssessment(ControlDecision.DENY,TaskDisposition.STOP_CANDIDATE,req.request_id,req.task_id,('SCOPE_FINGERPRINT_MISMATCH',),False,True,False,True,0,0,0,0,p.current_step,p.elapsed_seconds,p.no_progress_steps,reg.registry_fingerprint,fingerprint(policy),fingerprint(req))
    raw_cs=[x for x in reg.criteria if x.task_id==req.task_id]
    raw_ds=[x for x in reg.dependencies if x.task_id==req.task_id]
    invalid_required_criteria=[x for x in raw_cs if x.required and _inactive(now,x.observed_at,x.expires_at,x.verified,x.independent,x.revoked,x.evidence_binding,req.evidence_binding,policy)]
    invalid_required_dependencies=[x for x in raw_ds if x.required and _inactive(now,x.observed_at,x.expires_at,x.verified,x.independent,x.revoked,x.evidence_binding,req.evidence_binding,policy)]
    if invalid_required_criteria:
        return _empty(req,policy,reg,ControlDecision.HOLD,('REQUIRED_CRITERION_EVIDENCE_INVALID',))
    if invalid_required_dependencies:
        return _empty(req,policy,reg,ControlDecision.HOLD,('REQUIRED_DEPENDENCY_EVIDENCE_INVALID',))
    cs=[x for x in raw_cs if not _inactive(now,x.observed_at,x.expires_at,x.verified,x.independent,x.revoked,x.evidence_binding,req.evidence_binding,policy)]
    ds=[x for x in raw_ds if not _inactive(now,x.observed_at,x.expires_at,x.verified,x.independent,x.revoked,x.evidence_binding,req.evidence_binding,policy)]
    rc=[x for x in cs if x.required]; rd=[x for x in ds if x.required]
    sat=sum(1 for x in rc if x.satisfied); comp=sum(1 for x in rd if x.completed and not x.failed)
    base=dict(request_id=req.request_id,task_id=req.task_id,active_required_criteria=len(rc),satisfied_required_criteria=sat,active_required_dependencies=len(rd),completed_required_dependencies=comp,current_step=p.current_step,elapsed_seconds=p.elapsed_seconds,no_progress_steps=p.no_progress_steps,registry_fingerprint=reg.registry_fingerprint,policy_fingerprint=fingerprint(policy),request_fingerprint=fingerprint(req))
    if p.cancelled:
        return CompletionAssessment(ControlDecision.DENY,TaskDisposition.STOP_CANDIDATE,reasons=('TASK_CANCELLED',),completion_candidate=False,stop_candidate=True,continue_candidate=False,scope_creep_detected=False,**base)
    if p.fatal_error:
        return CompletionAssessment(ControlDecision.DENY,TaskDisposition.STOP_CANDIDATE,reasons=('FATAL_ERROR',),completion_candidate=False,stop_candidate=True,continue_candidate=False,scope_creep_detected=False,**base)
    if p.requested_extra_work and policy.deny_scope_creep:
        return CompletionAssessment(ControlDecision.DENY,TaskDisposition.STOP_CANDIDATE,reasons=('SCOPE_CREEP_REQUESTED',),completion_candidate=False,stop_candidate=True,continue_candidate=False,scope_creep_detected=True,**base)
    if any(x.failed for x in rd):
        return CompletionAssessment(ControlDecision.DENY,TaskDisposition.STOP_CANDIDATE,reasons=('REQUIRED_DEPENDENCY_FAILED',),completion_candidate=False,stop_candidate=True,continue_candidate=False,scope_creep_detected=False,**base)
    if p.current_step>=policy.max_steps:
        return CompletionAssessment(ControlDecision.DENY,TaskDisposition.STOP_CANDIDATE,reasons=('MAX_STEPS_REACHED',),completion_candidate=False,stop_candidate=True,continue_candidate=False,scope_creep_detected=False,**base)
    if p.elapsed_seconds>=policy.max_elapsed_seconds:
        return CompletionAssessment(ControlDecision.DENY,TaskDisposition.STOP_CANDIDATE,reasons=('MAX_ELAPSED_REACHED',),completion_candidate=False,stop_candidate=True,continue_candidate=False,scope_creep_detected=False,**base)
    if p.no_progress_steps>=policy.max_no_progress_steps:
        return CompletionAssessment(ControlDecision.HUMAN_APPROVAL,TaskDisposition.STOP_CANDIDATE,reasons=('NO_PROGRESS_LIMIT_REACHED',),completion_candidate=False,stop_candidate=True,continue_candidate=False,scope_creep_detected=False,**base)
    if len(rc)<policy.min_required_criteria:
        return CompletionAssessment(ControlDecision.HOLD,TaskDisposition.HOLD,reasons=('INSUFFICIENT_REQUIRED_CRITERIA',),completion_candidate=False,stop_candidate=False,continue_candidate=False,scope_creep_detected=False,**base)
    deps_ok=(not policy.require_all_required_dependencies) or all(x.completed and not x.failed for x in rd)
    if sat==len(rc) and deps_ok:
        return CompletionAssessment(ControlDecision.ALLOW,TaskDisposition.COMPLETE_CANDIDATE,reasons=('SUCCESS_CRITERIA_SATISFIED','DEPENDENCIES_SATISFIED' if rd else 'NO_REQUIRED_DEPENDENCIES'),completion_candidate=True,stop_candidate=False,continue_candidate=False,scope_creep_detected=False,**base)
    reasons=[]
    if sat<len(rc): reasons.append('SUCCESS_CRITERIA_PENDING')
    if policy.require_all_required_dependencies and comp<len(rd): reasons.append('DEPENDENCIES_PENDING')
    return CompletionAssessment(ControlDecision.ALLOW,TaskDisposition.CONTINUE,reasons=tuple(reasons) or ('CONTINUE_WITHIN_LIMITS',),completion_candidate=False,stop_candidate=False,continue_candidate=True,scope_creep_detected=False,**base)

def evaluate(req:TaskCheckRequest,policy:CompletionPolicy,progress,criteria,dependencies,*,now:int)->CompletionAssessment:
    try: reg=prepare_registry(policy,progress,criteria,dependencies,now=now)
    except Exception as e:
        dummy=PreparedCompletionRegistry('',fingerprint(policy),(),(),(),{},{},{},{},{},{})
        return _empty(req,policy,dummy,ControlDecision.HOLD,(f'INVALID_REGISTRY:{type(e).__name__}',))
    return evaluate_prepared(req,policy,reg,now=now)

def make_registry_delta(bp,bc,bd,tp,tc,td)->CompletionRegistryDelta:
    bpm={x.progress_id:x for x in _progress(bp)}; bcm={x.criterion_id:x for x in _criteria(bc)}; bdm={x.dependency_id:x for x in _deps(bd)}
    tpm={x.progress_id:x for x in _progress(tp)}; tcm={x.criterion_id:x for x in _criteria(tc)}; tdm={x.dependency_id:x for x in _deps(td)}
    def parts(b,t):
        removed=tuple(sorted(set(b)-set(t))); added=tuple(t[k] for k in sorted(set(t)-set(b))); changed=tuple(t[k] for k in sorted(set(b)&set(t)) if fingerprint(b[k])!=fingerprint(t[k])); return changed,removed,added
    cp,rp,ap=parts(bpm,tpm); cc,rc,ac=parts(bcm,tcm); cd,rd,ad=parts(bdm,tdm)
    return CompletionRegistryDelta(registry_fingerprint(bp,bc,bd),registry_fingerprint(tp,tc,td),cp,rp,ap,cc,rc,ac,cd,rd,ad)

def apply_registry_delta(bp,bc,bd,delta:CompletionRegistryDelta):
    if registry_fingerprint(bp,bc,bd)!=delta.base_fingerprint: raise ValueError('delta base fingerprint mismatch')
    pm={x.progress_id:x for x in _progress(bp)}; cm={x.criterion_id:x for x in _criteria(bc)}; dm={x.dependency_id:x for x in _deps(bd)}
    def apply(m,changed,removed,added,idattr):
        for k in removed:
            if k not in m: raise ValueError('invalid removal')
            del m[k]
        for x in changed:
            k=getattr(x,idattr)
            if k not in m: raise ValueError('invalid change')
            m[k]=x
        for x in added:
            k=getattr(x,idattr)
            if k in m: raise ValueError('invalid add')
            m[k]=x
    apply(pm,delta.changed_progress,delta.removed_progress_ids,delta.added_progress,'progress_id')
    apply(cm,delta.changed_criteria,delta.removed_criterion_ids,delta.added_criteria,'criterion_id')
    apply(dm,delta.changed_dependencies,delta.removed_dependency_ids,delta.added_dependencies,'dependency_id')
    po,co,do=_progress(pm.values()),_criteria(cm.values()),_deps(dm.values())
    if registry_fingerprint(po,co,do)!=delta.target_fingerprint: raise ValueError('delta target fingerprint mismatch')
    return po,co,do

def plan_registry_sync(progress,criteria,dependencies,remote_progress_fps:Mapping[str,str],remote_criterion_fps:Mapping[str,str],remote_dependency_fps:Mapping[str,str])->RegistrySyncPlan:
    ps=_progress(progress); cs=_criteria(criteria); ds=_deps(dependencies)
    pids=tuple(x.progress_id for x in ps if remote_progress_fps.get(x.progress_id)!=fingerprint(x))
    cids=tuple(x.criterion_id for x in cs if remote_criterion_fps.get(x.criterion_id)!=fingerprint(x))
    dids=tuple(x.dependency_id for x in ds if remote_dependency_fps.get(x.dependency_id)!=fingerprint(x))
    pm={x.progress_id:x for x in ps}; cm={x.criterion_id:x for x in cs}; dm={x.dependency_id:x for x in ds}
    meta=len(canonical_json({'progress':[pm[k] for k in pids],'criteria':[cm[k] for k in cids],'dependencies':[dm[k] for k in dids]}).encode())
    full=len(canonical_json({'progress':ps,'criteria':cs,'dependencies':ds}).encode())
    return RegistrySyncPlan(pids,cids,dids,meta,full,full>0 and meta/full>=0.8)

def assessment_digest(a:CompletionAssessment)->str: return fingerprint(a)

def default_policy(now:int)->CompletionPolicy:
    return CompletionPolicy('COMPLETE-060','1',1,now-100,now+10000,100,7200,8,3600,True,True,True,2,False)
def default_progress(now:int)->Tuple[TaskProgressState,...]:
    return (TaskProgressState('PROG-060','TASK-060','SCOPE-060',20,1200,0,False,False,False,now-30,now+3600,True,True,'BIND-060',False),)
def default_criteria(now:int)->Tuple[SuccessCriterion,...]:
    return (
      SuccessCriterion('CRIT-060-A','TASK-060',True,True,True,True,now-40,now+3600,'BIND-060',False),
      SuccessCriterion('CRIT-060-B','TASK-060',True,True,True,True,now-35,now+3600,'BIND-060',False),
    )
def default_dependencies(now:int)->Tuple[DependencyState,...]:
    return (DependencyState('DEP-060-A','TASK-060',True,True,False,True,True,now-25,now+3600,'BIND-060',False),)
def default_request(now:int)->TaskCheckRequest:
    return TaskCheckRequest('REQ-060','TASK-060','SCOPE-060','COMPLETE-060','1',1,'BIND-060')
