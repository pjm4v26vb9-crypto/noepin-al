from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Tuple
import hashlib
import json
import time


class RiskDecision(str, Enum):
    LOW_RISK_CANDIDATE = "LOW_RISK_CANDIDATE"
    HUMAN_CONFIRM = "HUMAN_CONFIRM"
    HOLD = "HOLD"
    DENY = "DENY"


class OperationKind(str, Enum):
    READ = "READ"
    WRITE = "WRITE"
    DELETE = "DELETE"
    PUBLISH = "PUBLISH"
    PRIVILEGE_CHANGE = "PRIVILEGE_CHANGE"
    PURCHASE = "PURCHASE"
    EXTERNAL_SEND = "EXTERNAL_SEND"
    EXECUTE = "EXECUTE"
    CONFIG_CHANGE = "CONFIG_CHANGE"


@dataclass(frozen=True)
class RiskPolicy:
    human_threshold: int = 40
    deny_threshold: int = 90
    amount_human_threshold: int = 10_000
    amount_deny_threshold: int = 1_000_000
    large_scope_threshold: int = 100
    max_uncertainty_without_hold: int = 60
    policy_version: str = "1"


@dataclass(frozen=True)
class RiskRequest:
    request_id: str
    actor_id: str
    operation: OperationKind
    target_id: str
    target_version: str
    evidence_fingerprint: str
    evidence_version: int
    amount: int = 0
    items_affected: int = 1
    destructive: bool = False
    public_effect: bool = False
    privilege_change: bool = False
    external_side_effect: bool = False
    irreversible: bool = False
    production: bool = False
    sensitive_data: bool = False
    critical_resource: bool = False
    uncertainty: int = 0
    reversibility: int = 100
    human_approved: bool = False
    approval_ref: Optional[str] = None
    schema_version: str = "1"
    context: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RiskResult:
    decision: RiskDecision
    reason_codes: Tuple[str, ...]
    request_fingerprint: str
    risk_score: int
    human_required: bool
    evidence_bound: bool
    authoritative: bool = False
    approval_granted: bool = False
    action_executed: bool = False
    action_succeeded: bool = False
    state_committed: bool = False
    cache_reused: bool = False
    created_unix_ns: int = 0

    def stable_payload(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reason_codes": list(self.reason_codes),
            "request_fingerprint": self.request_fingerprint,
            "risk_score": self.risk_score,
            "human_required": self.human_required,
            "evidence_bound": self.evidence_bound,
            "authoritative": self.authoritative,
            "approval_granted": self.approval_granted,
            "action_executed": self.action_executed,
            "action_succeeded": self.action_succeeded,
            "state_committed": self.state_committed,
            "cache_reused": self.cache_reused,
        }


class HumanApprovalRiskScorer:
    """
    NOEPIN AL 016 — Human Approval Risk Scorer.

    Risk scoring / approval-routing only. It does not authorize or execute actions.

    Invariants:
      Low risk != Authorization
      Risk score != Truth
      Human approval evidence != Action execution
      Human approval evidence != Action success
      Evidence fingerprint match != Evidence freshness
      Cache hit != Verification PASS
      Scorer decision != Policy authority
    """

    def __init__(self, policy: RiskPolicy, *, enable_exact_state_cache: bool = True) -> None:
        if not policy.policy_version:
            raise ValueError("policy_version required")
        for v in (policy.human_threshold, policy.deny_threshold, policy.max_uncertainty_without_hold):
            if not isinstance(v, int) or isinstance(v, bool) or not (0 <= v <= 100):
                raise ValueError("invalid policy threshold")
        if policy.human_threshold >= policy.deny_threshold:
            raise ValueError("human_threshold must be below deny_threshold")
        self.policy = policy
        self.enable_exact_state_cache = bool(enable_exact_state_cache)
        self._cache: Dict[Tuple[str, str], RiskResult] = {}

    @staticmethod
    def _normalize(v: Any) -> Any:
        if isinstance(v, Mapping):
            return {str(k): HumanApprovalRiskScorer._normalize(v[k]) for k in sorted(v, key=lambda x: str(x))}
        if isinstance(v, (list, tuple)):
            return [HumanApprovalRiskScorer._normalize(x) for x in v]
        if isinstance(v, set):
            return sorted(HumanApprovalRiskScorer._normalize(x) for x in v)
        if isinstance(v, Enum):
            return v.value
        if v is None or isinstance(v, (str, int, float, bool)):
            return v
        return str(v)

    @classmethod
    def fingerprint(cls, req: RiskRequest) -> str:
        raw = json.dumps(cls._normalize(asdict(req)), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _valid_sha256(value: Any) -> bool:
        if not isinstance(value, str) or len(value) != 64:
            return False
        try:
            int(value, 16)
            return True
        except ValueError:
            return False

    @staticmethod
    def _valid_int(value: Any) -> bool:
        return isinstance(value, int) and not isinstance(value, bool)

    @staticmethod
    def _clamp(value: int) -> int:
        return max(0, min(100, int(value)))

    def _score(self, req: RiskRequest) -> Tuple[int, Tuple[str, ...]]:
        score = 0
        reasons = []

        op_weights = {
            OperationKind.READ: 0,
            OperationKind.WRITE: 12,
            OperationKind.DELETE: 35,
            OperationKind.PUBLISH: 30,
            OperationKind.PRIVILEGE_CHANGE: 45,
            OperationKind.PURCHASE: 25,
            OperationKind.EXTERNAL_SEND: 28,
            OperationKind.EXECUTE: 30,
            OperationKind.CONFIG_CHANGE: 22,
        }
        score += op_weights[req.operation]

        flags = (
            ("DESTRUCTIVE", req.destructive, 25),
            ("PUBLIC_EFFECT", req.public_effect, 18),
            ("PRIVILEGE_CHANGE", req.privilege_change, 30),
            ("EXTERNAL_SIDE_EFFECT", req.external_side_effect, 18),
            ("IRREVERSIBLE", req.irreversible, 25),
            ("PRODUCTION", req.production, 18),
            ("SENSITIVE_DATA", req.sensitive_data, 22),
            ("CRITICAL_RESOURCE", req.critical_resource, 20),
        )
        for name, enabled, weight in flags:
            if enabled:
                score += weight
                reasons.append(name)

        if req.amount >= self.policy.amount_deny_threshold:
            score += 50
            reasons.append("VERY_HIGH_AMOUNT")
        elif req.amount >= self.policy.amount_human_threshold:
            score += 25
            reasons.append("HIGH_AMOUNT")
        elif req.amount > 0:
            score += 5
            reasons.append("MONETARY_EFFECT")

        if req.items_affected >= self.policy.large_scope_threshold:
            score += 20
            reasons.append("LARGE_IMPACT_SCOPE")
        elif req.items_affected > 1:
            score += 8
            reasons.append("MULTI_ITEM_SCOPE")

        if req.uncertainty >= 50:
            score += 20
            reasons.append("HIGH_UNCERTAINTY")
        elif req.uncertainty >= 20:
            score += 8
            reasons.append("MODERATE_UNCERTAINTY")

        if req.reversibility <= 20:
            score += 20
            reasons.append("LOW_REVERSIBILITY")
        elif req.reversibility < 80:
            score += 8
            reasons.append("PARTIAL_REVERSIBILITY")

        return self._clamp(score), tuple(reasons)

    def _make(self, decision, reasons, fp, score, human_required, evidence_bound) -> RiskResult:
        return RiskResult(
            decision=decision,
            reason_codes=tuple(reasons),
            request_fingerprint=fp,
            risk_score=score,
            human_required=bool(human_required),
            evidence_bound=bool(evidence_bound),
            authoritative=False,
            approval_granted=False,
            action_executed=False,
            action_succeeded=False,
            state_committed=False,
            cache_reused=False,
            created_unix_ns=time.time_ns(),
        )

    def _evaluate_uncached(self, req: RiskRequest) -> RiskResult:
        fp = self.fingerprint(req)

        if not req.request_id or not req.actor_id or not req.target_id or not req.target_version or not req.schema_version:
            return self._make(RiskDecision.HOLD, ("MISSING_REQUIRED_FIELD",), fp, 100, True, False)

        if not self._valid_sha256(req.evidence_fingerprint):
            return self._make(RiskDecision.HOLD, ("INVALID_EVIDENCE_FINGERPRINT",), fp, 100, True, False)

        if not self._valid_int(req.evidence_version) or req.evidence_version < 1:
            return self._make(RiskDecision.HOLD, ("INVALID_EVIDENCE_VERSION",), fp, 100, True, False)

        for name, value, minimum in (
            ("amount", req.amount, 0),
            ("items_affected", req.items_affected, 1),
            ("uncertainty", req.uncertainty, 0),
            ("reversibility", req.reversibility, 0),
        ):
            if not self._valid_int(value) or value < minimum:
                return self._make(RiskDecision.HOLD, (f"INVALID_{name.upper()}",), fp, 100, True, True)

        if req.uncertainty > 100 or req.reversibility > 100:
            return self._make(RiskDecision.HOLD, ("INVALID_PERCENTAGE_RANGE",), fp, 100, True, True)

        if req.uncertainty > self.policy.max_uncertainty_without_hold:
            return self._make(RiskDecision.HOLD, ("UNCERTAINTY_REQUIRES_NEW_EVIDENCE",), fp, 100, True, True)

        score, reasons = self._score(req)
        human_required = score >= self.policy.human_threshold

        # Certain operation classes require human confirmation regardless of aggregate score.
        hard_human = (
            req.operation in {
                OperationKind.DELETE, OperationKind.PUBLISH, OperationKind.PRIVILEGE_CHANGE,
                OperationKind.PURCHASE, OperationKind.EXTERNAL_SEND, OperationKind.EXECUTE
            }
            or req.destructive or req.public_effect or req.privilege_change
            or req.external_side_effect or req.irreversible or req.production
            or req.sensitive_data or req.critical_resource
        )
        human_required = human_required or hard_human

        # Deny is reserved for extreme risk; even approval evidence does not auto-lower it.
        if score >= self.policy.deny_threshold:
            return self._make(
                RiskDecision.DENY,
                tuple(reasons) + ("RISK_AT_OR_ABOVE_DENY_THRESHOLD",),
                fp, score, True, True
            )

        if human_required:
            if req.human_approved and req.approval_ref:
                # Still routed as HUMAN_CONFIRM: scorer acknowledges evidence but cannot grant authority.
                return self._make(
                    RiskDecision.HUMAN_CONFIRM,
                    tuple(reasons) + ("APPROVAL_EVIDENCE_PRESENT_REVALIDATION_REQUIRED",),
                    fp, score, True, True
                )
            return self._make(
                RiskDecision.HUMAN_CONFIRM,
                tuple(reasons) + ("HUMAN_CONFIRMATION_REQUIRED",),
                fp, score, True, True
            )

        return self._make(
            RiskDecision.LOW_RISK_CANDIDATE,
            tuple(reasons) + ("LOW_RISK_CANDIDATE_ONLY",),
            fp, score, False, True
        )

    def evaluate(self, req: RiskRequest) -> RiskResult:
        fp = self.fingerprint(req)
        key = (fp, self.policy.policy_version)

        if self.enable_exact_state_cache and key in self._cache:
            r = self._cache[key]
            return RiskResult(
                decision=r.decision,
                reason_codes=r.reason_codes,
                request_fingerprint=fp,
                risk_score=r.risk_score,
                human_required=r.human_required,
                evidence_bound=r.evidence_bound,
                authoritative=False,
                approval_granted=False,
                action_executed=False,
                action_succeeded=False,
                state_committed=False,
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
