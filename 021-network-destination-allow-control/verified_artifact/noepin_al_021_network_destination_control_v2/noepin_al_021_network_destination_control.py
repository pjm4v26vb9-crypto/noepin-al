from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Tuple
import hashlib, json, time, ipaddress

class NetDecision(str, Enum):
    ALLOW_PREPARE='ALLOW_PREPARE'; DENY='DENY'; HOLD='HOLD'; HUMAN_CONFIRM='HUMAN_CONFIRM'
class DestinationKind(str, Enum):
    DOMAIN='DOMAIN'; API='API'; IP='IP'; NETWORK='NETWORK'
class Environment(str, Enum):
    DEV='DEV'; STAGING='STAGING'; PROD='PROD'
@dataclass(frozen=True)
class NetworkPermit:
    permit_id:str; agent_id:str; allowed_kinds:Tuple[DestinationKind,...]; allowed_destinations:Tuple[str,...];
    allowed_purposes:Tuple[str,...]; allowed_environments:Tuple[Environment,...]; version:int; expires_epoch_s:int;
    revoked:bool=False; issuer_ref:Optional[str]=None
@dataclass(frozen=True)
class NetworkRequest:
    request_id:str; agent_id:str; destination_kind:DestinationKind; destination:str; purpose:str; environment:Environment;
    now_epoch_s:int; permit:Optional[NetworkPermit]=None; dns_resolved_ip:Optional[str]=None; dns_verified:bool=False;
    tls_required:bool=True; tls_verified:bool=False; private_network:bool=False; unknown_destination:bool=False;
    external_side_effect:bool=False; high_risk:bool=False; human_approved:bool=False; approval_ref:Optional[str]=None;
    schema_version:str='1'; context:Mapping[str,Any]=field(default_factory=dict)
@dataclass(frozen=True)
class NetworkResult:
    decision:NetDecision; reason_codes:Tuple[str,...]; request_fingerprint:str; permit_valid:bool; destination_allowed:bool;
    purpose_allowed:bool; environment_allowed:bool; authoritative:bool=False; network_connected:bool=False;
    data_sent:bool=False; action_succeeded:bool=False; cache_reused:bool=False; created_unix_ns:int=0
    def stable_payload(self):
        return {'decision':self.decision.value,'reason_codes':list(self.reason_codes),'request_fingerprint':self.request_fingerprint,
        'permit_valid':self.permit_valid,'destination_allowed':self.destination_allowed,'purpose_allowed':self.purpose_allowed,
        'environment_allowed':self.environment_allowed,'authoritative':self.authoritative,'network_connected':self.network_connected,
        'data_sent':self.data_sent,'action_succeeded':self.action_succeeded,'cache_reused':self.cache_reused}
class NetworkDestinationControl:
    def __init__(self, policy_version='1', enable_exact_state_cache=True):
        self.policy_version=str(policy_version); self.enable_exact_state_cache=bool(enable_exact_state_cache); self._cache={}
    @staticmethod
    def _norm(v):
        from enum import Enum
        if isinstance(v, Mapping): return {str(k):NetworkDestinationControl._norm(v[k]) for k in sorted(v,key=lambda x:str(x))}
        if isinstance(v,(list,tuple)): return [NetworkDestinationControl._norm(x) for x in v]
        if isinstance(v,Enum): return v.value
        if v is None or isinstance(v,(str,int,float,bool)): return v
        return str(v)
    @classmethod
    def fingerprint(cls,r):
        raw=json.dumps(cls._norm(asdict(r)),sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
        return hashlib.sha256(raw).hexdigest()
    @staticmethod
    def _norm_dest(kind,d):
        d=d.strip().lower()
        if kind in {DestinationKind.DOMAIN,DestinationKind.API}: return d.rstrip('.')
        if kind==DestinationKind.IP:
            try:return str(ipaddress.ip_address(d))
            except ValueError:return d
        if kind==DestinationKind.NETWORK:
            try:return str(ipaddress.ip_network(d,strict=False))
            except ValueError:return d
        return d
    def _make(self,decision,reasons,fp,pv=False,da=False,pa=False,ea=False):
        return NetworkResult(decision,tuple(reasons),fp,pv,da,pa,ea,False,False,False,False,False,time.time_ns())
    def _evaluate_uncached(self,r:NetworkRequest):
        fp=self.fingerprint(r)
        if not r.request_id or not r.agent_id or not r.destination or not r.purpose or not r.schema_version:
            return self._make(NetDecision.HOLD,('MISSING_REQUIRED_FIELD',),fp)
        if not isinstance(r.now_epoch_s,int) or isinstance(r.now_epoch_s,bool) or r.now_epoch_s<0:
            return self._make(NetDecision.HOLD,('INVALID_TIME',),fp)
        p=r.permit
        if p is None:return self._make(NetDecision.DENY,('PERMIT_REQUIRED',),fp)
        if not p.permit_id or not p.agent_id or p.version<1 or p.expires_epoch_s<0:
            return self._make(NetDecision.HOLD,('INVALID_PERMIT',),fp)
        if p.revoked:return self._make(NetDecision.DENY,('PERMIT_REVOKED',),fp)
        if r.now_epoch_s>=p.expires_epoch_s:return self._make(NetDecision.DENY,('PERMIT_EXPIRED',),fp)
        if p.agent_id!=r.agent_id:return self._make(NetDecision.DENY,('AGENT_MISMATCH',),fp)
        if r.destination_kind not in p.allowed_kinds:return self._make(NetDecision.DENY,('DESTINATION_KIND_NOT_ALLOWED',),fp,True)
        nd=self._norm_dest(r.destination_kind,r.destination)
        allowed={self._norm_dest(r.destination_kind,x) for x in p.allowed_destinations}
        da=nd in allowed
        if not da:return self._make(NetDecision.DENY,('DESTINATION_NOT_ALLOWED',),fp,True,False)
        pa=r.purpose in p.allowed_purposes
        if not pa:return self._make(NetDecision.DENY,('PURPOSE_NOT_ALLOWED',),fp,True,True,False)
        ea=r.environment in p.allowed_environments
        if not ea:return self._make(NetDecision.DENY,('ENVIRONMENT_NOT_ALLOWED',),fp,True,True,True,False)
        if r.unknown_destination:return self._make(NetDecision.DENY,('UNKNOWN_DESTINATION',),fp,True,True,True,True)
        if r.destination_kind in {DestinationKind.DOMAIN,DestinationKind.API} and r.dns_resolved_ip is not None:
            try: ipaddress.ip_address(r.dns_resolved_ip)
            except ValueError: return self._make(NetDecision.HOLD,('INVALID_RESOLVED_IP',),fp,True,True,True,True)
            if not r.dns_verified:return self._make(NetDecision.HOLD,('DNS_NOT_VERIFIED',),fp,True,True,True,True)
        if r.tls_required and not r.tls_verified:return self._make(NetDecision.HOLD,('TLS_NOT_VERIFIED',),fp,True,True,True,True)
        if r.environment==Environment.PROD and (r.high_risk or r.external_side_effect):
            if not (r.human_approved and r.approval_ref):
                return self._make(NetDecision.HUMAN_CONFIRM,('PROD_HIGH_RISK_CONFIRM_REQUIRED',),fp,True,True,True,True)
        return self._make(NetDecision.ALLOW_PREPARE,('DESTINATION_POLICY_MATCH',),fp,True,True,True,True)
    def evaluate(self,r):
        fp=self.fingerprint(r); key=(fp,self.policy_version)
        if self.enable_exact_state_cache and key in self._cache:
            x=self._cache[key]
            return NetworkResult(x.decision,x.reason_codes,fp,x.permit_valid,x.destination_allowed,x.purpose_allowed,x.environment_allowed,False,False,False,False,True,time.time_ns())
        x=self._evaluate_uncached(r)
        if self.enable_exact_state_cache:self._cache[key]=x
        return x
    def clear_cache(self): self._cache.clear()
    def cache_size(self): return len(self._cache)
