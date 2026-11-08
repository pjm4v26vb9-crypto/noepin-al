"""NOEPIN AL 080 — Adversarial Contrarian Verifier — Sequential Successor V2.

Creator / Originator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED

Deterministic contrarian verifier. It holds the Primary Plan immutable and searches
supplied constraints/environment for failure conditions and counterexamples only.
No absence of counterexamples is promoted to safety proof, permission, execution,
or world truth.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Sequence

class Decision(str,Enum):
    ALLOW='ALLOW'; DENY='DENY'; HOLD='HOLD'; HUMAN_APPROVAL='HUMAN_APPROVAL'
class Severity(str,Enum):
    LOW='LOW'; MEDIUM='MEDIUM'; HIGH='HIGH'; CRITICAL='CRITICAL'

@dataclass(frozen=True)
class PlanAction:
    action_id:str; operation:str; target:str; effect_tags:tuple[str,...]
    assumptions:tuple[tuple[str,str],...]; binding:str; state_epoch:str
@dataclass(frozen=True)
class PrimaryPlan:
    plan_id:str; actions:tuple[PlanAction,...]; plan_fingerprint:str
    binding:str; state_epoch:str
@dataclass(frozen=True)
class ConstraintRule:
    constraint_id:str; forbidden_effects:tuple[str,...]
    required_env:tuple[tuple[str,str],...]; severity:Severity; observed:bool
    binding:str; state_epoch:str
@dataclass(frozen=True)
class EnvironmentFact:
    key:str; value:str; observed:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class RiskModel:
    binding:str; state_epoch:str; min_coverage:float=0.80
    critical_denies:bool=True; high_holds:bool=True; revoked:bool=False
@dataclass(frozen=True)
class VerificationRequest:
    request_id:str; plan_id:str; constraint_ids:tuple[str,...]
    binding:str; state_epoch:str
@dataclass(frozen=True)
class Counterexample:
    counterexample_id:str; action_id:str; constraint_id:str
    severity:Severity; condition:str; reproducible:bool; resolved:bool
@dataclass(frozen=True)
class VerificationResult:
    decision:Decision; reasons:tuple[str,...]
    counterexamples:tuple[Counterexample,...]
    failure_conditions:tuple[str,...]; coverage:float
    risk_addition:float; next_gate_candidate:bool
    plan_mutated:bool=False; permission_granted:bool=False
    counterexample_executed:bool=False; environment_written:bool=False
    action_executed:bool=False; plan_committed:bool=False
    world_truth_proven:bool=False; safety_proven:bool=False
    action_success:bool=False
@dataclass(frozen=True)
class PreparedVerifierState:
    risk_model:RiskModel; constraints:tuple[ConstraintRule,...]
    environment:tuple[EnvironmentFact,...]
    constraint_fingerprints:tuple[tuple[str,str],...]
    environment_fingerprints:tuple[tuple[str,str],...]
    risk_model_fingerprint:str; registry_fingerprint:str
    constraint_index:tuple[tuple[str,ConstraintRule],...]
    environment_index:tuple[tuple[str,EnvironmentFact],...]
    binding:str; state_epoch:str
@dataclass(frozen=True)
class VerifierRegistryDelta:
    base_fingerprint:str; target_fingerprint:str
    changed_constraints:tuple[ConstraintRule,...]; removed_constraint_ids:tuple[str,...]
    changed_environment:tuple[EnvironmentFact,...]; removed_environment_keys:tuple[str,...]
    target_risk_model:RiskModel; binding:str; state_epoch:str
@dataclass(frozen=True)
class VerifierSyncPlan:
    missing_or_changed_constraints:tuple[str,...]
    missing_or_changed_environment:tuple[str,...]
    metadata_bytes_required:int; full_resend_required:bool

def _canon(v)->bytes:
    def cv(x):
        if isinstance(x,Enum): return x.value
        if hasattr(x,'__dataclass_fields__'): return {k:cv(getattr(x,k)) for k in x.__dataclass_fields__}
        if isinstance(x,tuple): return [cv(i) for i in x]
        if isinstance(x,list): return [cv(i) for i in x]
        if isinstance(x,dict): return {str(k):cv(x[k]) for k in sorted(x)}
        if isinstance(x,float): return round(x,12)
        return x
    return json.dumps(cv(v),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def _fp(v)->str: return sha256(_canon(v)).hexdigest()
def _idx(items,key): return tuple(sorted(((getattr(x,key),x) for x in items),key=lambda z:z[0]))
def _lookup(index,key):
    lo,hi=0,len(index)
    while lo<hi:
        m=(lo+hi)//2
        if index[m][0]<key: lo=m+1
        else: hi=m
    return index[lo][1] if lo<len(index) and index[lo][0]==key else None
def _uniq(items,attr):
    ids=[getattr(x,attr) for x in items]; return len(ids)==len(set(ids))
def _registry_fp(risk,constraints,environment):
    return _fp({'risk':_fp(risk),'constraints':sorted((x.constraint_id,_fp(x)) for x in constraints),'environment':sorted((x.key,_fp(x)) for x in environment)})
def plan_fingerprint(actions): return _fp(tuple(actions))

def default_actions():
    b,e='ADV-BIND','STATE-EPOCH-1'
    return (
      PlanAction('A1','READ','DOC',('READ_ONLY',),(('network','OFF'),),b,e),
      PlanAction('A2','ANALYZE','DOC',('LOCAL_ANALYSIS',),(('network','OFF'),),b,e),
    )
def default_plan():
    a=default_actions(); return PrimaryPlan('PLAN-1',a,plan_fingerprint(a),'ADV-BIND','STATE-EPOCH-1')
def default_constraints():
    b,e='ADV-BIND','STATE-EPOCH-1'
    return (
      ConstraintRule('C-NO-WRITE',('EXTERNAL_WRITE','DELETE','PERMISSION_CHANGE'),(('network','OFF'),),Severity.CRITICAL,True,b,e),
      ConstraintRule('C-LOCAL',('EXTERNAL_SEND',),(('network','OFF'),),Severity.HIGH,True,b,e),
      ConstraintRule('C-BOUNDARY',('UNBOUNDED_SCAN',),(),Severity.MEDIUM,True,b,e),
    )
def default_environment():
    b,e='ADV-BIND','STATE-EPOCH-1'
    return (EnvironmentFact('network','OFF',True,b,e),EnvironmentFact('workspace','SANDBOX',True,b,e))
def default_risk_model(): return RiskModel('ADV-BIND','STATE-EPOCH-1')
def default_request(): return VerificationRequest('REQ-1','PLAN-1',('C-NO-WRITE','C-LOCAL','C-BOUNDARY'),'ADV-BIND','STATE-EPOCH-1')

def _hold(reason): return VerificationResult(Decision.HOLD,(reason,),(),(),0.0,0.0,False)
def _severity_risk(s): return {Severity.LOW:.05,Severity.MEDIUM:.15,Severity.HIGH:.35,Severity.CRITICAL:.60}[s]
def _env_map(environment): return {x.key:x for x in environment}
def _validate_plan(plan): return isinstance(plan,PrimaryPlan) and plan.plan_fingerprint==plan_fingerprint(plan.actions) and _uniq(plan.actions,'action_id')
def _evaluate(req,plan,risk,constraints,environment):
    if not _validate_plan(plan): return _hold('PRIMARY_PLAN_FINGERPRINT_OR_STRUCTURE_INVALID')
    if plan.plan_id!=req.plan_id: return _hold('PLAN_ID_MISMATCH')
    if risk.revoked: return _hold('RISK_MODEL_REVOKED')
    if not (0<risk.min_coverage<=1): return _hold('INVALID_RISK_MODEL')
    if req.binding!=risk.binding or req.state_epoch!=risk.state_epoch: return _hold('REQUEST_RISK_BINDING_MISMATCH')
    if plan.binding!=risk.binding or plan.state_epoch!=risk.state_epoch: return _hold('PLAN_BINDING_MISMATCH')
    if not _uniq(constraints,'constraint_id') or not _uniq(environment,'key'): return _hold('DUPLICATE_CONSTRAINT_OR_ENVIRONMENT_KEY')
    ci={x.constraint_id:x for x in constraints}; em=_env_map(environment)
    selected=[]
    if len(req.constraint_ids)!=len(set(req.constraint_ids)): return _hold('DUPLICATE_REQUEST_CONSTRAINT')
    for cid in req.constraint_ids:
        c=ci.get(cid)
        if c is None: return _hold('CONSTRAINT_UNKNOWN')
        selected.append(c)
    if not selected: return _hold('NO_CONSTRAINTS_REQUESTED')
    ces=[]; failures=[]; covered=0; risk_add=0.0
    for c in selected:
        if c.binding!=risk.binding or c.state_epoch!=risk.state_epoch: return _hold('CONSTRAINT_BINDING_MISMATCH')
        if not c.observed:
            failures.append(f'{c.constraint_id}:CONSTRAINT_UNOBSERVED'); continue
        env_ok=True; unresolved=False
        for k,v in c.required_env:
            f=em.get(k)
            if f is None or not f.observed:
                unresolved=True; env_ok=False; failures.append(f'{c.constraint_id}:ENV_UNOBSERVED:{k}'); break
            if f.binding!=risk.binding or f.state_epoch!=risk.state_epoch: return _hold('ENVIRONMENT_BINDING_MISMATCH')
            if f.value!=v: env_ok=False; failures.append(f'{c.constraint_id}:ENV_MISMATCH:{k}'); break
        if unresolved: continue
        covered+=1
        for a in plan.actions:
            if a.binding!=risk.binding or a.state_epoch!=risk.state_epoch: return _hold('ACTION_BINDING_MISMATCH')
            hit=tuple(sorted(set(a.effect_tags)&set(c.forbidden_effects)))
            if hit and env_ok:
                ce=Counterexample(f'CE-{c.constraint_id}-{a.action_id}',a.action_id,c.constraint_id,c.severity,'FORBIDDEN_EFFECT:'+','.join(hit),True,False)
                ces.append(ce); risk_add += _severity_risk(c.severity)
            # Assumption contradiction is a boundary counterexample if directly observable.
            for k,v in a.assumptions:
                f=em.get(k)
                if f is not None and f.observed and f.value!=v:
                    ce=Counterexample(f'CE-ASSUME-{c.constraint_id}-{a.action_id}-{k}',a.action_id,c.constraint_id,c.severity,f'ASSUMPTION_CONTRADICTION:{k}',True,False)
                    ces.append(ce); risk_add += _severity_risk(c.severity)
    coverage=covered/len(selected)
    # de-duplicate deterministic counterexamples
    uniq={x.counterexample_id:x for x in ces}; ces=tuple(uniq[k] for k in sorted(uniq))
    failures=tuple(sorted(set(failures)))
    critical=[x for x in ces if x.severity==Severity.CRITICAL and x.reproducible and not x.resolved]
    high=[x for x in ces if x.severity==Severity.HIGH and x.reproducible and not x.resolved]
    if critical and risk.critical_denies:
        return VerificationResult(Decision.DENY,('REPRODUCIBLE_CRITICAL_COUNTEREXAMPLE',),ces,failures,round(coverage,12),round(risk_add,12),False)
    if high and risk.high_holds:
        return VerificationResult(Decision.HOLD,('REPRODUCIBLE_HIGH_COUNTEREXAMPLE',),ces,failures,round(coverage,12),round(risk_add,12),False)
    if coverage<risk.min_coverage:
        return VerificationResult(Decision.HOLD,('COUNTEREXAMPLE_COVERAGE_INSUFFICIENT',),ces,failures,round(coverage,12),round(risk_add,12),False)
    if ces:
        return VerificationResult(Decision.ALLOW,('ONLY_NONMAJOR_COUNTEREXAMPLES_WITHIN_COVERAGE',),ces,failures,round(coverage,12),round(risk_add,12),True)
    return VerificationResult(Decision.ALLOW,('NO_REPRODUCIBLE_COUNTEREXAMPLE_WITH_SUFFICIENT_COVERAGE',),(),failures,round(coverage,12),0.0,True)

def evaluate(req:VerificationRequest,plan:PrimaryPlan,risk:RiskModel,constraints:Sequence[ConstraintRule],environment:Sequence[EnvironmentFact])->VerificationResult:
    if not isinstance(req,VerificationRequest) or not isinstance(plan,PrimaryPlan) or not isinstance(risk,RiskModel): return _hold('INVALID_TYPED_INPUT')
    return _evaluate(req,plan,risk,tuple(constraints),tuple(environment))

def prepare_state(risk,constraints,environment,*,binding:str)->PreparedVerifierState:
    cc=tuple(constraints); ee=tuple(environment)
    return PreparedVerifierState(risk,cc,ee,tuple(sorted((x.constraint_id,_fp(x)) for x in cc)),tuple(sorted((x.key,_fp(x)) for x in ee)),_fp(risk),_registry_fp(risk,cc,ee),_idx(cc,'constraint_id'),_idx(ee,'key'),binding,risk.state_epoch)
def validate_prepared_integrity(st:PreparedVerifierState)->bool:
    if not isinstance(st,PreparedVerifierState): return False
    if st.binding!=st.risk_model.binding or st.state_epoch!=st.risk_model.state_epoch: return False
    if st.risk_model_fingerprint!=_fp(st.risk_model): return False
    if st.constraint_fingerprints!=tuple(sorted((x.constraint_id,_fp(x)) for x in st.constraints)): return False
    if st.environment_fingerprints!=tuple(sorted((x.key,_fp(x)) for x in st.environment)): return False
    if st.registry_fingerprint!=_registry_fp(st.risk_model,st.constraints,st.environment): return False
    if st.constraint_index!=_idx(st.constraints,'constraint_id') or st.environment_index!=_idx(st.environment,'key'): return False
    return _uniq(st.constraints,'constraint_id') and _uniq(st.environment,'key')
def evaluate_prepared(req,plan,st:PreparedVerifierState,*,current_risk_fingerprint:str,current_registry_fingerprint:str,prepared_integrity_validated:bool)->VerificationResult:
    if not isinstance(req,VerificationRequest) or not isinstance(plan,PrimaryPlan) or not isinstance(st,PreparedVerifierState): return _hold('INVALID_TYPED_INPUT')
    if not prepared_integrity_validated: return _hold('PREPARED_INTEGRITY_NOT_VALIDATED')
    if current_risk_fingerprint!=st.risk_model_fingerprint: return _hold('CURRENT_RISK_FINGERPRINT_MISMATCH')
    if current_registry_fingerprint!=st.registry_fingerprint: return _hold('CURRENT_REGISTRY_FINGERPRINT_MISMATCH')
    # Reuse validated registries but materialize only requested constraints.
    selected=[]
    for cid in req.constraint_ids:
        c=_lookup(st.constraint_index,cid)
        if c is None: return _hold('CONSTRAINT_UNKNOWN')
        selected.append(c)
    return _evaluate(req,plan,st.risk_model,tuple(selected),st.environment)
def make_delta(a:PreparedVerifierState,b:PreparedVerifierState)->VerifierRegistryDelta:
    ac,bc=dict(a.constraint_fingerprints),dict(b.constraint_fingerprints); ae,be=dict(a.environment_fingerprints),dict(b.environment_fingerprints)
    cm={x.constraint_id:x for x in b.constraints}; em={x.key:x for x in b.environment}
    cc=tuple(cm[k] for k in sorted(bc) if ac.get(k)!=bc[k]); rc=tuple(sorted(set(ac)-set(bc)))
    ce=tuple(em[k] for k in sorted(be) if ae.get(k)!=be[k]); re=tuple(sorted(set(ae)-set(be)))
    return VerifierRegistryDelta(a.registry_fingerprint,b.registry_fingerprint,cc,rc,ce,re,b.risk_model,b.binding,b.state_epoch)
def apply_delta(base:PreparedVerifierState,d:VerifierRegistryDelta)->PreparedVerifierState:
    if d.base_fingerprint!=base.registry_fingerprint: raise ValueError('BASE_FINGERPRINT_MISMATCH')
    cm={x.constraint_id:x for x in base.constraints}; em={x.key:x for x in base.environment}
    for k in d.removed_constraint_ids: cm.pop(k,None)
    for x in d.changed_constraints: cm[x.constraint_id]=x
    for k in d.removed_environment_keys: em.pop(k,None)
    for x in d.changed_environment: em[x.key]=x
    out=prepare_state(d.target_risk_model,tuple(cm[k] for k in sorted(cm)),tuple(em[k] for k in sorted(em)),binding=d.binding)
    if out.registry_fingerprint!=d.target_fingerprint: raise ValueError('TARGET_FINGERPRINT_MISMATCH')
    return out
def missing_only_sync_plan(target:PreparedVerifierState,known_constraints:dict[str,str],known_environment:dict[str,str])->VerifierSyncPlan:
    cf=dict(target.constraint_fingerprints); ef=dict(target.environment_fingerprints)
    mc=tuple(k for k in sorted(cf) if known_constraints.get(k)!=cf[k]); me=tuple(k for k in sorted(ef) if known_environment.get(k)!=ef[k])
    meta=len(_canon({'constraints':mc,'environment':me,'risk':target.risk_model_fingerprint,'registry':target.registry_fingerprint}))
    return VerifierSyncPlan(mc,me,meta,False)
def full_registry_bytes(st): return len(_canon({'risk':st.risk_model,'constraints':st.constraints,'environment':st.environment}))
def delta_bytes(d): return len(_canon(d))
