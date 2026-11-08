from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Tuple
import hashlib
import json
import time


class ToolDecision(str, Enum):
    ALLOW_PREPARE = "ALLOW_PREPARE"
    DENY = "DENY"
    HOLD = "HOLD"
    HUMAN_CONFIRM = "HUMAN_CONFIRM"


@dataclass(frozen=True)
class ToolPermit:
    permit_id: str
    agent_id: str
    server_id: str
    tool_name: str
    operations: Tuple[str, ...]
    scopes: Tuple[str, ...]
    expires_at_epoch_s: int
    permit_version: int
    issuer_ref: str
    revoked: bool = False


@dataclass(frozen=True)
class ToolControllerPolicy:
    allowed_servers: Tuple[str, ...]
    allowed_tools: Tuple[str, ...]
    high_risk_operations: Tuple[str, ...] = (
        "delete", "publish", "purchase", "external_send", "execute", "write_production"
    )
    max_risk_without_confirmation: int = 35
    policy_version: str = "1"


@dataclass(frozen=True)
class ToolRequest:
    request_id: str
    agent_id: str
    server_id: str
    tool_name: str
    operation: str
    required_scope: str
    observed_epoch_s: int
    risk_score: int
    permit: Optional[ToolPermit]
    expected_permit_version: Optional[int] = None
    oauth_authenticated: bool = False
    oidc_authenticated: bool = False
    external_side_effect: bool = False
    human_approved: bool = False
    approval_ref: Optional[str] = None
    schema_version: str = "1"
    context: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolPermissionResult:
    decision: ToolDecision
    reason_codes: Tuple[str, ...]
    request_fingerprint: str
    permit_validated: bool
    scope_validated: bool
    authoritative: bool = False
    tool_called: bool = False
    action_executed: bool = False
    action_succeeded: bool = False
    cache_reused: bool = False
    created_unix_ns: int = 0

    def stable_payload(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reason_codes": list(self.reason_codes),
            "request_fingerprint": self.request_fingerprint,
            "permit_validated": self.permit_validated,
            "scope_validated": self.scope_validated,
            "authoritative": self.authoritative,
            "tool_called": self.tool_called,
            "action_executed": self.action_executed,
            "action_succeeded": self.action_succeeded,
            "cache_reused": self.cache_reused,
        }


class ToolPermissionController:
    """
    NOEPIN AL 009 — MCP / Tool Permission Controller.

    Permission decision only. It never invokes an MCP server or external tool.

    Invariants:
      Tool discoverability != Tool authority
      OAuth/OIDC authentication != Operation authorization
      Tool allowlist != Operation allow
      Permit presence != Valid permit
      Scope match is required independently
      Expired/Revoked permit != Authority
      Cached allow != Current authority
      Permission decision != Tool call / Action success
    """

    def __init__(self, policy: ToolControllerPolicy, *, enable_exact_state_cache: bool = True) -> None:
        if not policy.allowed_servers or not policy.allowed_tools:
            raise ValueError("allowed_servers and allowed_tools are required")
        if not policy.policy_version:
            raise ValueError("policy_version is required")
        self.policy = policy
        self.enable_exact_state_cache = bool(enable_exact_state_cache)
        self._cache: Dict[Tuple[str, str], ToolPermissionResult] = {}

    @staticmethod
    def _normalize(v: Any) -> Any:
        if isinstance(v, Mapping):
            return {str(k): ToolPermissionController._normalize(v[k]) for k in sorted(v, key=lambda x: str(x))}
        if isinstance(v, (list, tuple)):
            return [ToolPermissionController._normalize(x) for x in v]
        if isinstance(v, set):
            return sorted(ToolPermissionController._normalize(x) for x in v)
        if isinstance(v, Enum):
            return v.value
        if v is None or isinstance(v, (str, int, float, bool)):
            return v
        return str(v)

    @classmethod
    def fingerprint(cls, req: ToolRequest) -> str:
        raw = json.dumps(cls._normalize(asdict(req)), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _valid_int(v: Any) -> bool:
        return isinstance(v, int) and not isinstance(v, bool)

    @staticmethod
    def _scope_match(required: str, granted: Tuple[str, ...]) -> bool:
        for scope in granted:
            if scope == "*":
                return True
            if required == scope or required.startswith(scope.rstrip("/") + "/"):
                return True
        return False

    def _make(self, decision, reasons, fp, permit_ok, scope_ok):
        return ToolPermissionResult(
            decision=decision,
            reason_codes=tuple(reasons),
            request_fingerprint=fp,
            permit_validated=bool(permit_ok),
            scope_validated=bool(scope_ok),
            authoritative=False,
            tool_called=False,
            action_executed=False,
            action_succeeded=False,
            cache_reused=False,
            created_unix_ns=time.time_ns(),
        )

    def _evaluate_uncached(self, req: ToolRequest) -> ToolPermissionResult:
        fp = self.fingerprint(req)

        if not req.request_id or not req.agent_id or not req.server_id or not req.tool_name or not req.operation or not req.required_scope or not req.schema_version:
            return self._make(ToolDecision.HOLD, ("MISSING_REQUIRED_FIELD",), fp, False, False)

        if req.server_id not in set(self.policy.allowed_servers):
            return self._make(ToolDecision.DENY, ("SERVER_NOT_ALLOWLISTED",), fp, False, False)

        if req.tool_name not in set(self.policy.allowed_tools):
            return self._make(ToolDecision.DENY, ("TOOL_NOT_ALLOWLISTED",), fp, False, False)

        if not self._valid_int(req.observed_epoch_s) or req.observed_epoch_s < 0:
            return self._make(ToolDecision.HOLD, ("INVALID_OBSERVED_TIME",), fp, False, False)

        if not self._valid_int(req.risk_score) or not (0 <= req.risk_score <= 100):
            return self._make(ToolDecision.HOLD, ("INVALID_RISK_SCORE",), fp, False, False)

        permit = req.permit
        if permit is None:
            return self._make(ToolDecision.DENY, ("TOOL_PERMIT_REQUIRED",), fp, False, False)

        if not permit.permit_id or not permit.agent_id or not permit.server_id or not permit.tool_name or not permit.issuer_ref:
            return self._make(ToolDecision.DENY, ("MALFORMED_TOOL_PERMIT",), fp, False, False)

        if not self._valid_int(permit.permit_version) or permit.permit_version < 1:
            return self._make(ToolDecision.HOLD, ("INVALID_PERMIT_VERSION",), fp, False, False)

        if not self._valid_int(permit.expires_at_epoch_s):
            return self._make(ToolDecision.HOLD, ("INVALID_PERMIT_EXPIRY",), fp, False, False)

        if permit.revoked:
            return self._make(ToolDecision.DENY, ("TOOL_PERMIT_REVOKED",), fp, False, False)

        if req.expected_permit_version is not None and req.expected_permit_version != permit.permit_version:
            return self._make(ToolDecision.HOLD, ("PERMIT_VERSION_MISMATCH",), fp, False, False)

        if permit.agent_id != req.agent_id:
            return self._make(ToolDecision.DENY, ("PERMIT_AGENT_MISMATCH",), fp, False, False)

        if permit.server_id != req.server_id:
            return self._make(ToolDecision.DENY, ("PERMIT_SERVER_MISMATCH",), fp, False, False)

        if permit.tool_name != req.tool_name:
            return self._make(ToolDecision.DENY, ("PERMIT_TOOL_MISMATCH",), fp, False, False)

        if req.observed_epoch_s >= permit.expires_at_epoch_s:
            return self._make(ToolDecision.DENY, ("TOOL_PERMIT_EXPIRED",), fp, False, False)

        if req.operation not in set(permit.operations) and "*" not in set(permit.operations):
            return self._make(ToolDecision.DENY, ("OPERATION_NOT_GRANTED",), fp, True, False)

        if not self._scope_match(req.required_scope, permit.scopes):
            return self._make(ToolDecision.DENY, ("SCOPE_NOT_GRANTED",), fp, True, False)

        # Authentication may be required by an outer identity provider, but authentication
        # alone never creates authorization. We record it only as request state.
        high_risk = (
            req.operation in set(self.policy.high_risk_operations)
            or req.risk_score > self.policy.max_risk_without_confirmation
            or req.external_side_effect
        )
        if high_risk and not (req.human_approved and req.approval_ref):
            return self._make(ToolDecision.HUMAN_CONFIRM, ("HIGH_RISK_TOOL_OPERATION_REQUIRES_HUMAN_CONFIRMATION",), fp, True, True)

        return self._make(ToolDecision.ALLOW_PREPARE, ("TOOL_PERMISSION_VALID_PREPARE_ONLY",), fp, True, True)

    def evaluate(self, req: ToolRequest) -> ToolPermissionResult:
        fp = self.fingerprint(req)
        key = (fp, self.policy.policy_version)
        if self.enable_exact_state_cache and key in self._cache:
            c = self._cache[key]
            return ToolPermissionResult(
                decision=c.decision,
                reason_codes=c.reason_codes,
                request_fingerprint=fp,
                permit_validated=c.permit_validated,
                scope_validated=c.scope_validated,
                authoritative=False,
                tool_called=False,
                action_executed=False,
                action_succeeded=False,
                cache_reused=True,
                created_unix_ns=time.time_ns(),
            )
        result = self._evaluate_uncached(req)
        if self.enable_exact_state_cache:
            self._cache[key] = result
        return result

    def clear_cache(self) -> None:
        self._cache.clear()

    def cache_size(self) -> int:
        return len(self._cache)
