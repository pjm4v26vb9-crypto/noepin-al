from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Tuple
import hashlib, json, time

class HijackDecision(str, Enum):
    ALLOW_CONTINUE='ALLOW_CONTINUE'; HOLD='HOLD'; HUMAN_REVIEW='HUMAN_REVIEW'; DENY='DENY'
class SourceKind(str, Enum):
    USER='USER'; SYSTEM='SYSTEM'; DEVELOPER='DEVELOPER'; TOOL='TOOL'; WEB='WEB'; FILE='FILE'; EXTERNAL_AI='EXTERNAL_AI'; UNKNOWN='UNKNOWN'
@dataclass(frozen=True)
class GoalContract:
    goal_id:str; owner_ref:str; goal_fingerprint:str; allowed_scope:Tuple[str,...]
    forbidden_objectives:Tuple[str,...]=(); version:int=1; authority_version:int=1; revoked:bool=False
@dataclass(frozen=True)
class GoalObservation:
    request_id:str; contract:GoalContract; source_kind:SourceKind; proposed_goal_fingerprint:str
    proposed_scope:Tuple[str,...]; semantic_similarity:int; semantic_confidence:int
    external_instruction_attempt:bool=False; unauthorized_goal_change:bool=False
    policy_override_attempt:bool=False; privilege_expansion_attempt:bool=False
    tries_to_ignore_original_goal:bool=False; human_authorized_change:bool=False
    approval_ref:Optional[str]=None; observed_contract_version:Optional[int]=None
    observed_authority_version:Optional[int]=None; schema_version:str='1'; context:Mapping[str,Any]=field(default_factory=dict)
@dataclass(frozen=True)
class HijackResult:
    decision:HijackDecision; reason_codes:Tuple[str,...]; request_fingerprint:str; drift_score:int; goal_authority_preserved:bool
    authoritative:bool=False; goal_changed:bool=False; action_executed:bool=False; cache_reused:bool=False; created_unix_ns:int=0
    def stable_payload(self):
        return {'decision':self.decision.value,'reason_codes':list(self.reason_codes),'request_fingerprint':self.request_fingerprint,
                'drift_score':self.drift_score,'goal_authority_preserved':self.goal_authority_preserved,'authoritative':self.authoritative,
                'goal_changed':self.goal_changed,'action_executed':self.action_executed,'cache_reused':self.cache_reused}

class GoalHijackDetector:
    # Detection only. Never rewrites the authorized goal and never executes a plan.
    # External Content != Goal Authority; Proposal != Authorized Goal; Similarity Score != Truth.
    def __init__(self, *, policy_version='1', enable_exact_state_cache=True, hold_similarity_below=70, deny_similarity_below=35, low_confidence_below=60):
        if not policy_version: raise ValueError('policy_version required')
        self.policy_version=str(policy_version); self.enable_exact_state_cache=bool(enable_exact_state_cache)
        self.hold_similarity_below=hold_similarity_below; self.deny_similarity_below=deny_similarity_below; self.low_confidence_below=low_confidence_below
        self._cache:Dict[Tuple[str,str],HijackResult]={}
    @staticmethod
    def _norm(v):
        if isinstance(v,Mapping): return {str(k):GoalHijackDetector._norm(v[k]) for k in sorted(v,key=lambda x:str(x))}
        if isinstance(v,(list,tuple)): return [GoalHijackDetector._norm(x) for x in v]
        if isinstance(v,set): return sorted(GoalHijackDetector._norm(x) for x in v)
        if isinstance(v,Enum): return v.value
        if v is None or isinstance(v,(str,int,float,bool)): return v
        return str(v)
    @classmethod
    def fingerprint(cls,o):
        raw=json.dumps(cls._norm(asdict(o)),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode(); return hashlib.sha256(raw).hexdigest()
    @staticmethod
    def _valid_hash(v):
        if not isinstance(v,str) or len(v)!=64: return False
        try: int(v,16); return True
        except ValueError: return False
    @staticmethod
    def _valid_score(v): return isinstance(v,int) and not isinstance(v,bool) and 0<=v<=100
    @staticmethod
    def _scope_allowed(proposed,allowed):
        allow=set(allowed); return True if '*' in allow else all(s in allow for s in proposed)
    def _make(self,d,reasons,fp,drift,preserved): return HijackResult(d,tuple(reasons),fp,drift,preserved,False,False,False,False,time.time_ns())
    def _evaluate_uncached(self,o):
        fp=self.fingerprint(o); c=o.contract
        if not o.request_id or not o.schema_version or not c.goal_id or not c.owner_ref: return self._make(HijackDecision.HOLD,('MISSING_REQUIRED_FIELD',),fp,100,False)
        if not self._valid_hash(c.goal_fingerprint) or not self._valid_hash(o.proposed_goal_fingerprint): return self._make(HijackDecision.HOLD,('INVALID_GOAL_FINGERPRINT',),fp,100,False)
        if not isinstance(c.version,int) or isinstance(c.version,bool) or c.version<1: return self._make(HijackDecision.HOLD,('INVALID_CONTRACT_VERSION',),fp,100,False)
        if not isinstance(c.authority_version,int) or isinstance(c.authority_version,bool) or c.authority_version<1: return self._make(HijackDecision.HOLD,('INVALID_AUTHORITY_VERSION',),fp,100,False)
        if c.revoked: return self._make(HijackDecision.DENY,('GOAL_CONTRACT_REVOKED',),fp,100,False)
        if o.observed_contract_version is not None and o.observed_contract_version!=c.version: return self._make(HijackDecision.HOLD,('CONTRACT_VERSION_MISMATCH',),fp,100,False)
        if o.observed_authority_version is not None and o.observed_authority_version!=c.authority_version: return self._make(HijackDecision.HOLD,('AUTHORITY_VERSION_MISMATCH',),fp,100,False)
        if not self._valid_score(o.semantic_similarity) or not self._valid_score(o.semantic_confidence): return self._make(HijackDecision.HOLD,('INVALID_SEMANTIC_SCORE',),fp,100,False)
        drift=100-o.semantic_similarity; untrusted=o.source_kind in {SourceKind.WEB,SourceKind.FILE,SourceKind.TOOL,SourceKind.EXTERNAL_AI,SourceKind.UNKNOWN}
        if o.policy_override_attempt or o.privilege_expansion_attempt or o.tries_to_ignore_original_goal: return self._make(HijackDecision.DENY,('EXPLICIT_GOAL_OR_POLICY_HIJACK_ATTEMPT',),fp,max(drift,90),True)
        if o.external_instruction_attempt and untrusted: return self._make(HijackDecision.DENY,('UNTRUSTED_CONTENT_ATTEMPTS_GOAL_AUTHORITY',),fp,max(drift,90),True)
        if not self._scope_allowed(o.proposed_scope,c.allowed_scope):
            if o.human_authorized_change and o.approval_ref: return self._make(HijackDecision.HUMAN_REVIEW,('AUTHORIZED_SCOPE_CHANGE_REQUIRES_NEW_CONTRACT',),fp,max(drift,60),True)
            return self._make(HijackDecision.DENY,('UNAUTHORIZED_SCOPE_EXPANSION',),fp,max(drift,80),True)
        if any(x in set(o.proposed_scope) for x in c.forbidden_objectives): return self._make(HijackDecision.DENY,('FORBIDDEN_OBJECTIVE_PRESENT',),fp,max(drift,90),True)
        if o.unauthorized_goal_change: return self._make(HijackDecision.DENY,('UNAUTHORIZED_GOAL_CHANGE',),fp,max(drift,80),True)
        if o.proposed_goal_fingerprint==c.goal_fingerprint: return self._make(HijackDecision.ALLOW_CONTINUE,('GOAL_FINGERPRINT_MATCH',),fp,drift,True)
        if o.human_authorized_change:
            if not o.approval_ref: return self._make(HijackDecision.HOLD,('GOAL_CHANGE_APPROVAL_REF_REQUIRED',),fp,drift,True)
            return self._make(HijackDecision.HUMAN_REVIEW,('AUTHORIZED_CHANGE_REQUIRES_NEW_GOAL_CONTRACT',),fp,drift,True)
        if o.semantic_confidence < self.low_confidence_below: return self._make(HijackDecision.HOLD,('LOW_CONFIDENCE_GOAL_COMPARISON',),fp,drift,True)
        if o.semantic_similarity < self.deny_similarity_below: return self._make(HijackDecision.DENY,('SEVERE_GOAL_DRIFT',),fp,drift,True)
        if o.semantic_similarity < self.hold_similarity_below: return self._make(HijackDecision.HUMAN_REVIEW,('MATERIAL_GOAL_DRIFT',),fp,drift,True)
        return self._make(HijackDecision.HOLD,('GOAL_FINGERPRINT_CHANGED_REVIEW_REQUIRED',),fp,drift,True)
    def evaluate(self,o):
        fp=self.fingerprint(o); key=(fp,self.policy_version)
        if self.enable_exact_state_cache and key in self._cache:
            c=self._cache[key]; return HijackResult(c.decision,c.reason_codes,fp,c.drift_score,c.goal_authority_preserved,False,False,False,True,time.time_ns())
        r=self._evaluate_uncached(o)
        if self.enable_exact_state_cache: self._cache[key]=r
        return r
    def clear_cache(self): self._cache.clear()
    def cache_size(self): return len(self._cache)
