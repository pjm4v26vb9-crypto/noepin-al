from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Tuple
import hashlib, json, time

class PermissionDecision(str, Enum):
    ALLOW_PREPARE="ALLOW_PREPARE"; DENY="DENY"; HOLD="HOLD"; HUMAN_CONFIRM="HUMAN_CONFIRM"

@dataclass(frozen=True)
class AgentIdentity:
    agent_id:str
    role:str
    identity_version:int
    disabled:bool=False
    external:bool=False

@dataclass(frozen=True)
class Permit:
    permit_id:str
    agent_id:str
    role:str
    resource_scope:Tuple[str,...]
    action_scope:Tuple[str,...]
    expires_at_epoch_s:int
    permit_version:int
    issuer_ref:str
    revoked:bool=False
    attributes:Mapping[str,Any]=field(default_factory=dict)

@dataclass(frozen=True)
class BrokerPolicy:
    high_risk_actions:Tuple[str,...]=("delete","publish","purchase","external_send","privilege_change")
    require_human_for_external_high_risk:bool=True
    policy_version:str="1"

@dataclass(frozen=True)
class PermissionRequest:
    request_id:str
    identity:AgentIdentity
    permit:Optional[Permit]
    resource:str
    action:str
    observed_epoch_s:int
    risk_score:int=0
    expected_identity_version:Optional[int]=None
    expected_permit_version:Optional[int]=None
    human_approved:bool=False
    approval_ref:Optional[str]=None
    schema_version:str="1"
    context:Mapping[str,Any]=field(default_factory=dict)

@dataclass(frozen=True)
class PermissionResult:
    decision:PermissionDecision
    reason_codes:Tuple[str,...]
    request_fingerprint:str
    identity_validated:bool
    permit_validated:bool
    authoritative:bool=False
    action_executed:bool=False
    action_succeeded:bool=False
    cache_reused:bool=False
    created_unix_ns:int=0
    def stable_payload(self):
        return {
            "decision":self.decision.value,"reason_codes":list(self.reason_codes),
            "request_fingerprint":self.request_fingerprint,
            "identity_validated":self.identity_validated,"permit_validated":self.permit_validated,
            "authoritative":self.authoritative,"action_executed":self.action_executed,
            "action_succeeded":self.action_succeeded,"cache_reused":self.cache_reused
        }

class AgentPermissionBroker:
    """
    NOEPIN AL 008 — Agent ID / Permission Broker.
    Decision-only broker. It never executes the requested action.

    Invariants:
      Agent ID != Authority
      Role claim != Granted Role
      Permit presence != Valid Permit
      Expired/Revoked Permit != Authority
      Cached allow != Current Authority
      Permission decision != Action Success
    """
    def __init__(self, policy:BrokerPolicy, *, enable_exact_state_cache:bool=True):
        if not policy.policy_version: raise ValueError("policy_version required")
        self.policy=policy; self.enable_exact_state_cache=bool(enable_exact_state_cache)
        self._cache:Dict[Tuple[str,str],PermissionResult]={}

    @staticmethod
    def _norm(v):
        if isinstance(v,Mapping): return {str(k):AgentPermissionBroker._norm(v[k]) for k in sorted(v,key=lambda x:str(x))}
        if isinstance(v,(list,tuple)): return [AgentPermissionBroker._norm(x) for x in v]
        if isinstance(v,set): return sorted(AgentPermissionBroker._norm(x) for x in v)
        if isinstance(v,Enum): return v.value
        if v is None or isinstance(v,(str,int,float,bool)): return v
        return str(v)

    @classmethod
    def fingerprint(cls,req):
        raw=json.dumps(cls._norm(asdict(req)),ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _valid_int(v): return isinstance(v,int) and not isinstance(v,bool)

    @staticmethod
    def _scope_match(value:str, scopes:Tuple[str,...])->bool:
        for s in scopes:
            if s=="*": return True
            if value==s or value.startswith(s.rstrip("/")+"/"): return True
        return False

    def _make(self,d,reasons,fp,iv,pv):
        return PermissionResult(d,tuple(reasons),fp,iv,pv,False,False,False,False,time.time_ns())

    def _evaluate_uncached(self,req:PermissionRequest)->PermissionResult:
        fp=self.fingerprint(req)
        if not req.request_id or not req.schema_version or not req.resource or not req.action:
            return self._make(PermissionDecision.HOLD,("MISSING_REQUIRED_FIELD",),fp,False,False)
        ident=req.identity
        if not ident.agent_id or not ident.role or not self._valid_int(ident.identity_version) or ident.identity_version<1:
            return self._make(PermissionDecision.HOLD,("INVALID_IDENTITY",),fp,False,False)
        if ident.disabled:
            return self._make(PermissionDecision.DENY,("IDENTITY_DISABLED",),fp,False,False)
        if req.expected_identity_version is not None and req.expected_identity_version!=ident.identity_version:
            return self._make(PermissionDecision.HOLD,("IDENTITY_VERSION_MISMATCH",),fp,False,False)
        if not self._valid_int(req.observed_epoch_s) or req.observed_epoch_s<0:
            return self._make(PermissionDecision.HOLD,("INVALID_OBSERVED_TIME",),fp,True,False)
        if not self._valid_int(req.risk_score) or not (0<=req.risk_score<=100):
            return self._make(PermissionDecision.HOLD,("INVALID_RISK_SCORE",),fp,True,False)
        p=req.permit
        if p is None:
            return self._make(PermissionDecision.DENY,("PERMIT_REQUIRED",),fp,True,False)
        if not p.permit_id or not p.agent_id or not p.role or not p.issuer_ref:
            return self._make(PermissionDecision.DENY,("MALFORMED_PERMIT",),fp,True,False)
        if not self._valid_int(p.permit_version) or p.permit_version<1:
            return self._make(PermissionDecision.HOLD,("INVALID_PERMIT_VERSION",),fp,True,False)
        if not self._valid_int(p.expires_at_epoch_s):
            return self._make(PermissionDecision.HOLD,("INVALID_PERMIT_EXPIRY",),fp,True,False)
        if p.revoked:
            return self._make(PermissionDecision.DENY,("PERMIT_REVOKED",),fp,True,False)
        if req.expected_permit_version is not None and req.expected_permit_version!=p.permit_version:
            return self._make(PermissionDecision.HOLD,("PERMIT_VERSION_MISMATCH",),fp,True,False)
        if p.agent_id!=ident.agent_id:
            return self._make(PermissionDecision.DENY,("PERMIT_AGENT_MISMATCH",),fp,True,False)
        if p.role!=ident.role:
            return self._make(PermissionDecision.DENY,("PERMIT_ROLE_MISMATCH",),fp,True,False)
        if req.observed_epoch_s>=p.expires_at_epoch_s:
            return self._make(PermissionDecision.DENY,("PERMIT_EXPIRED",),fp,True,False)
        if not self._scope_match(req.resource,p.resource_scope):
            return self._make(PermissionDecision.DENY,("RESOURCE_SCOPE_DENIED",),fp,True,False)
        if not self._scope_match(req.action,p.action_scope):
            return self._make(PermissionDecision.DENY,("ACTION_SCOPE_DENIED",),fp,True,False)

        high=req.action in set(self.policy.high_risk_actions) or req.risk_score>50
        if high and ident.external and self.policy.require_human_for_external_high_risk:
            if not (req.human_approved and req.approval_ref):
                return self._make(PermissionDecision.HUMAN_CONFIRM,("EXTERNAL_HIGH_RISK_REQUIRES_HUMAN_CONFIRMATION",),fp,True,True)
        return self._make(PermissionDecision.ALLOW_PREPARE,("PERMISSION_VALID_PREPARE_ONLY",),fp,True,True)

    def evaluate(self,req:PermissionRequest)->PermissionResult:
        fp=self.fingerprint(req); key=(fp,self.policy.policy_version)
        # cache is safe only because all authoritative state (identity/permit/version/revocation/expiry)
        # is included in the request fingerprint; changed authoritative state yields a new key.
        if self.enable_exact_state_cache and key in self._cache:
            c=self._cache[key]
            return PermissionResult(c.decision,c.reason_codes,fp,c.identity_validated,c.permit_validated,
                                    False,False,False,True,time.time_ns())
        r=self._evaluate_uncached(req)
        if self.enable_exact_state_cache: self._cache[key]=r
        return r
    def clear_cache(self): self._cache.clear()
    def cache_size(self): return len(self._cache)
