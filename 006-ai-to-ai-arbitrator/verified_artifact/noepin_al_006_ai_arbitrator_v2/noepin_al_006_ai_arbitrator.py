from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Tuple
import hashlib
import json
import time


class ArbitrationDecision(str, Enum):
    SELECT_CANDIDATE = "SELECT_CANDIDATE"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    HOLD = "HOLD"
    REJECT_ALL = "REJECT_ALL"


@dataclass(frozen=True)
class ArbitrationPolicy:
    min_evidence_score: int = 50
    max_risk_for_auto_select: int = 40
    min_margin_for_auto_select: int = 15
    require_evidence_refs: bool = True
    require_validated_authority_for_action_candidate: bool = True
    policy_version: str = "1"


@dataclass(frozen=True)
class Proposal:
    proposal_id: str
    agent_id: str
    recommendation: str
    evidence_score: int
    risk_score: int
    policy_compatible: bool
    authority_validated: bool
    action_candidate: bool = False
    evidence_refs: Tuple[str, ...] = ()
    source_fingerprint: Optional[str] = None
    rationale: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ArbitrationRequest:
    topic_id: str
    proposals: Tuple[Proposal, ...]
    human_override_proposal_id: Optional[str] = None
    human_approval_ref: Optional[str] = None
    schema_version: str = "1"
    context: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ArbitrationResult:
    decision: ArbitrationDecision
    reason_codes: Tuple[str, ...]
    request_fingerprint: str
    selected_proposal_id: Optional[str]
    eligible_proposal_ids: Tuple[str, ...]
    rejected_proposal_ids: Tuple[str, ...]
    authoritative: bool = False
    truth_established: bool = False
    action_executed: bool = False
    action_succeeded: bool = False
    cache_reused: bool = False
    created_unix_ns: int = 0

    def stable_payload(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reason_codes": list(self.reason_codes),
            "request_fingerprint": self.request_fingerprint,
            "selected_proposal_id": self.selected_proposal_id,
            "eligible_proposal_ids": list(self.eligible_proposal_ids),
            "rejected_proposal_ids": list(self.rejected_proposal_ids),
            "authoritative": self.authoritative,
            "truth_established": self.truth_established,
            "action_executed": self.action_executed,
            "action_succeeded": self.action_succeeded,
            "cache_reused": self.cache_reused,
        }


class AIArbitrator:
    """
    NOEPIN AL 006 — AI-to-AI Arbitrator.

    Ranks and filters proposals. It does not establish truth and does not execute actions.

    Invariants:
      Majority != Truth
      Evidence score != Truth
      Agent claim != Authority
      Selected proposal != Action Success
      Human override evidence != Action execution
      Fingerprint match != Authority match
      Cached arbitration != New authority
    """

    def __init__(self, policy: ArbitrationPolicy, *, enable_exact_state_cache: bool = True) -> None:
        if not policy.policy_version:
            raise ValueError("policy_version required")
        self.policy = policy
        self.enable_exact_state_cache = bool(enable_exact_state_cache)
        self._cache: Dict[Tuple[str, str], ArbitrationResult] = {}

    @staticmethod
    def _normalize(v: Any) -> Any:
        if isinstance(v, Mapping):
            return {str(k): AIArbitrator._normalize(v[k]) for k in sorted(v, key=lambda x: str(x))}
        if isinstance(v, (list, tuple)):
            return [AIArbitrator._normalize(x) for x in v]
        if isinstance(v, set):
            return sorted(AIArbitrator._normalize(x) for x in v)
        if isinstance(v, Enum):
            return v.value
        if v is None or isinstance(v, (str, int, float, bool)):
            return v
        return str(v)

    @classmethod
    def fingerprint(cls, req: ArbitrationRequest) -> str:
        raw = json.dumps(cls._normalize(asdict(req)), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _valid_score(v: int) -> bool:
        return isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 100

    @staticmethod
    def _valid_sha256(v: Optional[str]) -> bool:
        if v is None:
            return True
        if len(v) != 64:
            return False
        try:
            int(v, 16)
            return True
        except ValueError:
            return False

    def _eligible(self, p: Proposal) -> Tuple[bool, str]:
        if not p.proposal_id or not p.agent_id or not p.recommendation:
            return False, "MISSING_PROPOSAL_FIELD"
        if not self._valid_score(p.evidence_score) or not self._valid_score(p.risk_score):
            return False, "INVALID_SCORE"
        if not self._valid_sha256(p.source_fingerprint):
            return False, "INVALID_SOURCE_FINGERPRINT"
        if not p.policy_compatible:
            return False, "POLICY_INCOMPATIBLE"
        if p.evidence_score < self.policy.min_evidence_score:
            return False, "EVIDENCE_BELOW_MINIMUM"
        if self.policy.require_evidence_refs and not p.evidence_refs:
            return False, "EVIDENCE_REFERENCE_REQUIRED"
        if p.action_candidate and self.policy.require_validated_authority_for_action_candidate and not p.authority_validated:
            return False, "ACTION_AUTHORITY_NOT_VALIDATED"
        return True, "ELIGIBLE"

    @staticmethod
    def _rank_key(p: Proposal) -> Tuple[int, int, int, str]:
        utility = p.evidence_score - p.risk_score
        return (utility, p.evidence_score, -p.risk_score, p.proposal_id)

    def _evaluate_uncached(self, req: ArbitrationRequest) -> ArbitrationResult:
        fp = self.fingerprint(req)

        if not req.topic_id or not req.schema_version:
            return self._make(ArbitrationDecision.HOLD, ("MISSING_TOPIC_OR_SCHEMA",), fp, None, (), ())

        if not req.proposals:
            return self._make(ArbitrationDecision.HOLD, ("NO_PROPOSALS",), fp, None, (), ())

        ids = [p.proposal_id for p in req.proposals]
        if len(ids) != len(set(ids)):
            return self._make(ArbitrationDecision.HOLD, ("DUPLICATE_PROPOSAL_ID",), fp, None, (), tuple(sorted(set(ids))))

        by_id = {p.proposal_id: p for p in req.proposals}

        if req.human_override_proposal_id is not None:
            if req.human_override_proposal_id not in by_id:
                return self._make(ArbitrationDecision.HOLD, ("HUMAN_OVERRIDE_TARGET_NOT_FOUND",), fp, None, (), tuple(sorted(ids)))
            if not req.human_approval_ref:
                return self._make(ArbitrationDecision.HOLD, ("HUMAN_OVERRIDE_REQUIRES_APPROVAL_REF",), fp, None, (), tuple(sorted(ids)))
            p = by_id[req.human_override_proposal_id]
            ok, reason = self._eligible(p)
            if not ok:
                return self._make(ArbitrationDecision.HOLD, ("HUMAN_OVERRIDE_TARGET_INELIGIBLE", reason), fp, None, (), tuple(sorted(ids)))
            return self._make(
                ArbitrationDecision.SELECT_CANDIDATE,
                ("HUMAN_OVERRIDE_SELECTS_CANDIDATE_ONLY",),
                fp,
                p.proposal_id,
                (p.proposal_id,),
                tuple(sorted(x for x in ids if x != p.proposal_id)),
            )

        eligible = []
        rejected = []
        rejection_reasons = []
        for p in req.proposals:
            ok, reason = self._eligible(p)
            if ok:
                eligible.append(p)
            else:
                rejected.append(p.proposal_id)
                rejection_reasons.append(f"{p.proposal_id}:{reason}")

        if not eligible:
            return self._make(
                ArbitrationDecision.REJECT_ALL,
                tuple(["NO_ELIGIBLE_PROPOSALS"] + sorted(rejection_reasons)),
                fp, None, (), tuple(sorted(rejected))
            )

        ranked = sorted(eligible, key=self._rank_key, reverse=True)
        top = ranked[0]
        eligible_ids = tuple(sorted(p.proposal_id for p in eligible))
        rejected_ids = tuple(sorted(rejected))

        if top.risk_score > self.policy.max_risk_for_auto_select:
            return self._make(
                ArbitrationDecision.HUMAN_REVIEW,
                ("TOP_CANDIDATE_RISK_REQUIRES_HUMAN_REVIEW",),
                fp, None, eligible_ids, rejected_ids
            )

        if len(ranked) > 1:
            second = ranked[1]
            top_utility = top.evidence_score - top.risk_score
            second_utility = second.evidence_score - second.risk_score
            margin = top_utility - second_utility
            if margin < self.policy.min_margin_for_auto_select:
                return self._make(
                    ArbitrationDecision.HUMAN_REVIEW,
                    ("TOP_CANDIDATES_TOO_CLOSE",),
                    fp, None, eligible_ids, rejected_ids
                )
            if top.recommendation != second.recommendation and top.risk_score >= self.policy.max_risk_for_auto_select - 10:
                return self._make(
                    ArbitrationDecision.HUMAN_REVIEW,
                    ("MATERIAL_CONFLICT_NEAR_RISK_BOUNDARY",),
                    fp, None, eligible_ids, rejected_ids
                )

        return self._make(
            ArbitrationDecision.SELECT_CANDIDATE,
            ("BEST_ELIGIBLE_CANDIDATE_SELECTED",),
            fp, top.proposal_id, eligible_ids, rejected_ids
        )

    def _make(self, decision, reasons, fp, selected, eligible, rejected) -> ArbitrationResult:
        return ArbitrationResult(
            decision=decision,
            reason_codes=tuple(reasons),
            request_fingerprint=fp,
            selected_proposal_id=selected,
            eligible_proposal_ids=tuple(eligible),
            rejected_proposal_ids=tuple(rejected),
            authoritative=False,
            truth_established=False,
            action_executed=False,
            action_succeeded=False,
            cache_reused=False,
            created_unix_ns=time.time_ns(),
        )

    def arbitrate(self, req: ArbitrationRequest) -> ArbitrationResult:
        fp = self.fingerprint(req)
        key = (fp, self.policy.policy_version)
        if self.enable_exact_state_cache and key in self._cache:
            c = self._cache[key]
            return ArbitrationResult(
                decision=c.decision,
                reason_codes=c.reason_codes,
                request_fingerprint=fp,
                selected_proposal_id=c.selected_proposal_id,
                eligible_proposal_ids=c.eligible_proposal_ids,
                rejected_proposal_ids=c.rejected_proposal_ids,
                authoritative=False,
                truth_established=False,
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
