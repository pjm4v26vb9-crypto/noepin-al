from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Tuple
import hashlib, json, time

class CredentialKind(str, Enum):
    API_KEY="API_KEY"; OAUTH_TOKEN="OAUTH_TOKEN"; PRIVATE_KEY="PRIVATE_KEY"
    CERTIFICATE="CERTIFICATE"; SESSION_TOKEN="SESSION_TOKEN"; SERVICE_CREDENTIAL="SERVICE_CREDENTIAL"

class CredentialOperation(str, Enum):
    PROXY_CALL="PROXY_CALL"; SIGN="SIGN"; REQUEST_SHORT_LIVED_TOKEN="REQUEST_SHORT_LIVED_TOKEN"
    READ_METADATA="READ_METADATA"

class CredentialDecision(str, Enum):
    ALLOW_PREPARE="ALLOW_PREPARE"; HUMAN_CONFIRM="HUMAN_CONFIRM"; HOLD="HOLD"; DENY="DENY"

@dataclass(frozen=True)
class CredentialRequest:
    request_id: str
    agent_id: str
    role: str
    purpose: str
    credential_ref: str
    credential_kind: CredentialKind
    credential_version: int
    credential_expiry_epoch_s: Optional[int]
    credential_revoked: bool
    vault_attested: bool
    broker_attested: bool
    operation: CredentialOperation
    target_ref: str
    permit_id: str
    permit_version: int
    permit_expiry_epoch_s: Optional[int]
    permit_revoked: bool
    role_authorized: bool
    purpose_authorized: bool
    operation_authorized: bool
    target_authorized: bool
    raw_secret_material_present: bool = False
    high_privilege: bool = False
    external_side_effect: bool = False
    human_approved: bool = False
    approval_ref: Optional[str] = None
    observed_epoch_s: int = 0
    authority_version: int = 1
    schema_version: str = "1"
    context: Mapping[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class CredentialResult:
    decision: CredentialDecision
    reason_codes: Tuple[str, ...]
    request_fingerprint: str
    proxy_plan_created: bool
    secret_exposed: bool = False
    credential_material_returned: bool = False
    short_lived_token_issued: bool = False
    signature_created: bool = False
    action_executed: bool = False
    action_succeeded: bool = False
    state_committed: bool = False
    authoritative: bool = False
    cache_reused: bool = False
    created_unix_ns: int = 0

    def stable_payload(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reason_codes": list(self.reason_codes),
            "request_fingerprint": self.request_fingerprint,
            "proxy_plan_created": self.proxy_plan_created,
            "secret_exposed": self.secret_exposed,
            "credential_material_returned": self.credential_material_returned,
            "short_lived_token_issued": self.short_lived_token_issued,
            "signature_created": self.signature_created,
            "action_executed": self.action_executed,
            "action_succeeded": self.action_succeeded,
            "state_committed": self.state_committed,
            "authoritative": self.authoritative,
            "cache_reused": self.cache_reused,
        }

class SecretCredentialGate:
    """
    NOEPIN AL 022 — Secret Key / Credential Gate.

    The gate evaluates references and authorization state only.
    It never retrieves secret material, issues a token, signs data, or performs the downstream action.

    Invariants:
      Credential Ref != Secret Material
      Permit Present != Permit Valid
      Permit Valid != Action Authority
      Proxy Plan != Action Success
      Short-lived-token request != Token Issued
      Sign request != Signature Created
      Cached allow != New Authority
    """
    def __init__(self, *, policy_version: str="1", enable_exact_state_cache: bool=True,
                 high_privilege_requires_human: bool=True, external_side_effect_requires_human: bool=True):
        if not policy_version: raise ValueError("policy_version required")
        self.policy_version=str(policy_version)
        self.enable_exact_state_cache=bool(enable_exact_state_cache)
        self.high_privilege_requires_human=bool(high_privilege_requires_human)
        self.external_side_effect_requires_human=bool(external_side_effect_requires_human)
        self._cache: Dict[Tuple[str,str], CredentialResult] = {}

    @staticmethod
    def _norm(v: Any)->Any:
        if isinstance(v, Mapping):
            return {str(k):SecretCredentialGate._norm(v[k]) for k in sorted(v,key=lambda x:str(x))}
        if isinstance(v,(tuple,list)): return [SecretCredentialGate._norm(x) for x in v]
        if isinstance(v,set): return sorted(SecretCredentialGate._norm(x) for x in v)
        if isinstance(v,Enum): return v.value
        if v is None or isinstance(v,(str,int,float,bool)): return v
        return str(v)

    @classmethod
    def fingerprint(cls, req: CredentialRequest)->str:
        raw=json.dumps(cls._norm(asdict(req)),ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _valid_int(v: Any)->bool:
        return isinstance(v,int) and not isinstance(v,bool)

    def _make(self, decision, reasons, fp, proxy=False):
        return CredentialResult(
            decision=decision, reason_codes=tuple(reasons), request_fingerprint=fp,
            proxy_plan_created=bool(proxy),
            secret_exposed=False, credential_material_returned=False,
            short_lived_token_issued=False, signature_created=False,
            action_executed=False, action_succeeded=False, state_committed=False,
            authoritative=False, cache_reused=False, created_unix_ns=time.time_ns()
        )

    def _evaluate_uncached(self, r: CredentialRequest)->CredentialResult:
        fp=self.fingerprint(r)
        required=[r.request_id,r.agent_id,r.role,r.purpose,r.credential_ref,r.target_ref,r.permit_id,r.schema_version]
        if any(not x for x in required):
            return self._make(CredentialDecision.HOLD,("REQUIRED_FIELD_MISSING",),fp)
        for v,name in ((r.credential_version,"CREDENTIAL_VERSION"),(r.permit_version,"PERMIT_VERSION"),
                       (r.observed_epoch_s,"OBSERVED_TIME"),(r.authority_version,"AUTHORITY_VERSION")):
            if not self._valid_int(v) or v < 0:
                return self._make(CredentialDecision.HOLD,(f"{name}_INVALID",),fp)
        if r.credential_version < 1 or r.permit_version < 1 or r.authority_version < 1:
            return self._make(CredentialDecision.HOLD,("VERSION_INVALID",),fp)

        # Raw secret material must never enter this boundary.
        if r.raw_secret_material_present:
            return self._make(CredentialDecision.DENY,("RAW_SECRET_MATERIAL_FORBIDDEN",),fp)

        if r.credential_revoked:
            return self._make(CredentialDecision.DENY,("CREDENTIAL_REVOKED",),fp)
        if r.permit_revoked:
            return self._make(CredentialDecision.DENY,("PERMIT_REVOKED",),fp)
        if r.credential_expiry_epoch_s is not None:
            if not self._valid_int(r.credential_expiry_epoch_s):
                return self._make(CredentialDecision.HOLD,("CREDENTIAL_EXPIRY_INVALID",),fp)
            if r.observed_epoch_s >= r.credential_expiry_epoch_s:
                return self._make(CredentialDecision.DENY,("CREDENTIAL_EXPIRED",),fp)
        if r.permit_expiry_epoch_s is not None:
            if not self._valid_int(r.permit_expiry_epoch_s):
                return self._make(CredentialDecision.HOLD,("PERMIT_EXPIRY_INVALID",),fp)
            if r.observed_epoch_s >= r.permit_expiry_epoch_s:
                return self._make(CredentialDecision.DENY,("PERMIT_EXPIRED",),fp)

        if not r.vault_attested:
            return self._make(CredentialDecision.HOLD,("VAULT_ATTESTATION_REQUIRED",),fp)
        if not r.broker_attested:
            return self._make(CredentialDecision.HOLD,("BROKER_ATTESTATION_REQUIRED",),fp)
        if not r.role_authorized:
            return self._make(CredentialDecision.DENY,("ROLE_NOT_AUTHORIZED",),fp)
        if not r.purpose_authorized:
            return self._make(CredentialDecision.DENY,("PURPOSE_NOT_AUTHORIZED",),fp)
        if not r.operation_authorized:
            return self._make(CredentialDecision.DENY,("OPERATION_NOT_AUTHORIZED",),fp)
        if not r.target_authorized:
            return self._make(CredentialDecision.DENY,("TARGET_NOT_AUTHORIZED",),fp)

        requires_human=(self.high_privilege_requires_human and r.high_privilege) or \
                       (self.external_side_effect_requires_human and r.external_side_effect)
        if requires_human:
            if not (r.human_approved and r.approval_ref):
                return self._make(CredentialDecision.HUMAN_CONFIRM,("HUMAN_CONFIRM_REQUIRED",),fp,proxy=False)
            return self._make(CredentialDecision.ALLOW_PREPARE,("APPROVAL_EVIDENCE_PRESENT_PROXY_PREPARE_ONLY",),fp,proxy=True)

        return self._make(CredentialDecision.ALLOW_PREPARE,("REFERENCE_AND_AUTHORIZATION_VALID_PROXY_PREPARE_ONLY",),fp,proxy=True)

    def evaluate(self, r: CredentialRequest)->CredentialResult:
        fp=self.fingerprint(r)
        key=(fp,self.policy_version)
        if self.enable_exact_state_cache and key in self._cache:
            x=self._cache[key]
            return CredentialResult(
                decision=x.decision, reason_codes=x.reason_codes, request_fingerprint=fp,
                proxy_plan_created=x.proxy_plan_created,
                secret_exposed=False, credential_material_returned=False,
                short_lived_token_issued=False, signature_created=False,
                action_executed=False, action_succeeded=False, state_committed=False,
                authoritative=False, cache_reused=True, created_unix_ns=time.time_ns()
            )
        out=self._evaluate_uncached(r)
        if self.enable_exact_state_cache:
            self._cache[key]=out
        return out

    def clear_cache(self)->None: self._cache.clear()
    def cache_size(self)->int: return len(self._cache)
