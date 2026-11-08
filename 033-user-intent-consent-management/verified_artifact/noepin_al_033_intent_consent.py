from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from hashlib import sha256
from typing import Any, Dict, Iterable, Optional, Tuple
import json
import math


class Decision(str, Enum):
    ALLOW_CANDIDATE = "ALLOW_CANDIDATE"
    HUMAN_CONFIRM = "HUMAN_CONFIRM"
    HOLD = "HOLD"
    DENY = "DENY"


@dataclass(frozen=True)
class IntentContract:
    contract_id: str
    user_id: str
    contract_version: str
    authority_version: str
    purpose: str
    allowed_actions: Tuple[str, ...]
    allowed_resources: Tuple[str, ...]
    allowed_destinations: Tuple[str, ...]
    allowed_roles: Tuple[str, ...]
    explicit_consent: bool
    issued_at: int
    expires_at: int
    revoked: bool = False
    permit_id: str = ""
    permit_version: str = ""
    permit_expires_at: int = 0
    permit_revoked: bool = False
    metadata: Tuple[Tuple[str, str], ...] = ()


@dataclass(frozen=True)
class IntentRequest:
    request_id: str
    user_id: str
    purpose: str
    action: str
    resource: str
    destination: str
    role: str
    contract_version: str
    authority_version: str
    observed_at: int
    permit_id: str = ""
    permit_version: str = ""
    high_impact: bool = False
    irreversible: bool = False
    human_approval_evidence: bool = False
    context_fingerprint: str = ""


@dataclass(frozen=True)
class IntentResult:
    decision: Decision
    reasons: Tuple[str, ...]
    fingerprint: str
    contract_fingerprint: str
    scope_matched: bool
    consent_current: bool
    permission_granted: bool = False
    action_executed: bool = False
    action_succeeded: bool = False
    state_committed: bool = False
    authoritative: bool = False


def _canon(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return [_canon(v) for v in value]
    if isinstance(value, list):
        return [_canon(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _canon(value[k]) for k in sorted(value)}
    if hasattr(value, "__dataclass_fields__"):
        return _canon(asdict(value))
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("non-finite numeric value")
    return value


def fingerprint(value: Any) -> str:
    raw = json.dumps(_canon(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(raw.encode("utf-8")).hexdigest()


def _nonempty(v: str) -> bool:
    return isinstance(v, str) and bool(v.strip())


def _unique_nonempty(items: Iterable[str]) -> bool:
    vals = tuple(items)
    return bool(vals) and all(_nonempty(v) for v in vals) and len(set(vals)) == len(vals)


class IntentConsentControl:
    """Pure decision/control layer. It never executes actions or grants runtime permission."""

    def __init__(self, *, enable_cache: bool = True) -> None:
        self.enable_cache = enable_cache
        self._contract_cache: Dict[IntentContract, Tuple[str, bool, Tuple[str, ...]]] = {}
        self._result_cache: Dict[str, IntentResult] = {}

    def clear_cache(self) -> None:
        self._contract_cache.clear()
        self._result_cache.clear()

    def _materialize_contract(self, c: IntentContract) -> Tuple[str, bool, Tuple[str, ...]]:
        if self.enable_cache and c in self._contract_cache:
            return self._contract_cache[c]
        cf = fingerprint(c)
        reasons = []
        for name in ("contract_id", "user_id", "contract_version", "authority_version", "purpose"):
            if not _nonempty(getattr(c, name)):
                reasons.append(f"INVALID_{name.upper()}")
        if not _unique_nonempty(c.allowed_actions): reasons.append("INVALID_ALLOWED_ACTIONS")
        if not _unique_nonempty(c.allowed_resources): reasons.append("INVALID_ALLOWED_RESOURCES")
        if not _unique_nonempty(c.allowed_destinations): reasons.append("INVALID_ALLOWED_DESTINATIONS")
        if not _unique_nonempty(c.allowed_roles): reasons.append("INVALID_ALLOWED_ROLES")
        if not isinstance(c.issued_at, int) or not isinstance(c.expires_at, int) or c.expires_at <= c.issued_at:
            reasons.append("INVALID_CONTRACT_TIME")
        if c.permit_id or c.permit_version or c.permit_expires_at:
            if not (_nonempty(c.permit_id) and _nonempty(c.permit_version) and isinstance(c.permit_expires_at, int) and c.permit_expires_at > c.issued_at):
                reasons.append("INVALID_PERMIT_BINDING")
        out = (cf, not reasons, tuple(sorted(set(reasons))))
        if self.enable_cache:
            self._contract_cache[c] = out
        return out

    def evaluate(self, contract: IntentContract, req: IntentRequest) -> IntentResult:
        cf, valid, v_reasons = self._materialize_contract(contract)
        # Complete request state plus immutable Contract Fingerprint prevents old scope/version/revocation state from being reused.
        key = fingerprint({"contract_fingerprint": cf, "request": req, "schema": "NOEPIN-AL-033/V2"})
        if self.enable_cache and key in self._result_cache:
            return self._result_cache[key]

        reasons = list(v_reasons)
        decision = Decision.ALLOW_CANDIDATE
        scope_matched = False
        consent_current = False

        # Request structural validation first.
        for name in ("request_id", "user_id", "purpose", "action", "resource", "destination", "role", "contract_version", "authority_version"):
            if not _nonempty(getattr(req, name)):
                reasons.append(f"INVALID_REQUEST_{name.upper()}")
        if not isinstance(req.observed_at, int):
            reasons.append("INVALID_OBSERVED_AT")

        if reasons:
            decision = Decision.DENY
        else:
            if contract.revoked:
                reasons.append("CONTRACT_REVOKED")
                decision = Decision.DENY
            elif req.observed_at < contract.issued_at:
                reasons.append("CONTRACT_NOT_YET_EFFECTIVE")
                decision = Decision.HOLD
            elif req.observed_at >= contract.expires_at:
                reasons.append("CONTRACT_EXPIRED")
                decision = Decision.DENY
            elif req.contract_version != contract.contract_version:
                reasons.append("CONTRACT_VERSION_MISMATCH")
                decision = Decision.HOLD
            elif req.authority_version != contract.authority_version:
                reasons.append("AUTHORITY_VERSION_MISMATCH")
                decision = Decision.HOLD
            elif req.user_id != contract.user_id:
                reasons.append("USER_MISMATCH")
                decision = Decision.DENY
            elif not contract.explicit_consent:
                reasons.append("EXPLICIT_CONSENT_ABSENT")
                decision = Decision.DENY
            else:
                consent_current = True
                if req.purpose != contract.purpose:
                    reasons.append("PURPOSE_OUT_OF_SCOPE")
                    decision = Decision.DENY
                elif req.action not in contract.allowed_actions:
                    reasons.append("ACTION_OUT_OF_SCOPE")
                    decision = Decision.DENY
                elif req.resource not in contract.allowed_resources:
                    reasons.append("RESOURCE_OUT_OF_SCOPE")
                    decision = Decision.DENY
                elif req.destination not in contract.allowed_destinations:
                    reasons.append("DESTINATION_OUT_OF_SCOPE")
                    decision = Decision.DENY
                elif req.role not in contract.allowed_roles:
                    reasons.append("ROLE_OUT_OF_SCOPE")
                    decision = Decision.DENY
                else:
                    scope_matched = True

                    # Permit binding is authoritative state and cannot be resurrected by cache.
                    if contract.permit_id or contract.permit_version or contract.permit_expires_at:
                        if contract.permit_revoked:
                            reasons.append("PERMIT_REVOKED")
                            decision = Decision.DENY
                        elif req.observed_at >= contract.permit_expires_at:
                            reasons.append("PERMIT_EXPIRED")
                            decision = Decision.DENY
                        elif req.permit_id != contract.permit_id or req.permit_version != contract.permit_version:
                            reasons.append("PERMIT_MISMATCH")
                            decision = Decision.HOLD

                    if decision == Decision.ALLOW_CANDIDATE and (req.high_impact or req.irreversible):
                        if not req.human_approval_evidence:
                            reasons.append("HUMAN_CONFIRM_REQUIRED")
                            decision = Decision.HUMAN_CONFIRM
                        else:
                            reasons.append("HUMAN_APPROVAL_EVIDENCE_PRESENT")

        if not reasons and decision == Decision.ALLOW_CANDIDATE:
            reasons.append("INTENT_AND_CONSENT_SCOPE_MATCHED")

        result = IntentResult(
            decision=decision,
            reasons=tuple(reasons),
            fingerprint=key,
            contract_fingerprint=cf,
            scope_matched=scope_matched,
            consent_current=consent_current,
        )
        if self.enable_cache:
            self._result_cache[key] = result
        return result
