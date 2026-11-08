from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from hashlib import sha256
import json
import math
from typing import Dict, Iterable, Mapping, Optional, Sequence, Tuple


CREATOR = "NOEPIN / のえぴん"
VERSION = "2.0.0-successor.20261102"


class Decision(str, Enum):
    ALLOW_CANDIDATE = "ALLOW_CANDIDATE"
    HUMAN_CONFIRM = "HUMAN_CONFIRM"
    HOLD = "HOLD"
    QUARANTINE = "QUARANTINE"
    DENY = "DENY"


class AssetKind(str, Enum):
    DOCUMENT = "DOCUMENT"
    EMBEDDING = "EMBEDDING"
    VECTOR_INDEX = "VECTOR_INDEX"
    RAG_RESULT = "RAG_RESULT"


@dataclass(frozen=True)
class GuardPolicy:
    policy_version: str
    authority_version: str
    expected_embedding_model_id: str
    expected_embedding_model_version: str
    expected_dimension: int
    expected_index_id: str
    expected_index_version: str
    max_anomaly_score: float = 0.35
    quarantine_anomaly_score: float = 0.75
    require_signature: bool = True
    require_provenance: bool = True
    require_source_binding: bool = True
    require_acl_match: bool = True
    require_consent_for_sensitive: bool = True


@dataclass(frozen=True)
class VectorObservation:
    asset_kind: AssetKind
    document_id: str
    source_id: str
    source_version: str
    content_fingerprint: str
    embedding_model_id: str
    embedding_model_version: str
    embedding_dimension: int
    vector_fingerprint: str
    index_id: str
    index_version: str
    index_fingerprint: str
    provenance_verified: bool
    signature_verified: bool
    source_binding_verified: bool
    acl_version: str
    allowed_principals: Tuple[str, ...]
    requester_principal: str
    classification: str
    purpose: str
    consent_evidence: bool
    anomaly_score: float
    suspicious_marker_count: int
    policy_version: str
    authority_version: str
    context_fingerprint: str


@dataclass(frozen=True)
class GuardResult:
    decision: Decision
    reason_codes: Tuple[str, ...]
    observation_fingerprint: str
    cache_reused: bool
    truth_established: bool = False
    source_truth_established: bool = False
    permission_granted: bool = False
    access_executed: bool = False
    data_isolated: bool = False
    index_rebuilt: bool = False
    state_committed: bool = False
    action_succeeded: bool = False


@dataclass(frozen=True)
class IndexEntry:
    document_id: str
    source_version: str
    content_fingerprint: str
    vector_fingerprint: str
    acl_version: str


@dataclass(frozen=True)
class IndexBaseline:
    index_id: str
    index_version: str
    entries: Tuple[IndexEntry, ...]


@dataclass(frozen=True)
class IndexDelta:
    base_fingerprint: str
    target_fingerprint: str
    base_version: str
    target_version: str
    changed_entries: Tuple[IndexEntry, ...]
    removed_document_ids: Tuple[str, ...]


def _canonical(obj) -> str:
    def conv(x):
        if isinstance(x, Enum):
            return x.value
        if hasattr(x, "__dataclass_fields__"):
            return {k: conv(v) for k, v in asdict(x).items()}
        if isinstance(x, dict):
            return {str(k): conv(v) for k, v in sorted(x.items(), key=lambda kv: str(kv[0]))}
        if isinstance(x, (tuple, list)):
            return [conv(v) for v in x]
        return x
    return json.dumps(conv(obj), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _fp(obj) -> str:
    return sha256(_canonical(obj).encode("utf-8")).hexdigest()


def _valid_sha256(value: str) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _valid_nonnegative_finite(value: float) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value) and value >= 0


def _sensitive(classification: str) -> bool:
    return classification.upper() in {"SENSITIVE", "RESTRICTED", "PERSONAL", "HEALTH", "FINANCIAL"}


class VectorIntegrityGuard:
    """Pure-data guard. No DB/network/filesystem mutation or access execution."""

    def __init__(self, policy: GuardPolicy):
        self.policy = policy
        self._cache: Dict[str, GuardResult] = {}

    def _validate(self, o: VectorObservation) -> Tuple[str, ...]:
        reasons = []
        required = {
            "DOCUMENT_ID_MISSING": o.document_id,
            "SOURCE_ID_MISSING": o.source_id,
            "SOURCE_VERSION_MISSING": o.source_version,
            "EMBEDDING_MODEL_ID_MISSING": o.embedding_model_id,
            "EMBEDDING_MODEL_VERSION_MISSING": o.embedding_model_version,
            "INDEX_ID_MISSING": o.index_id,
            "INDEX_VERSION_MISSING": o.index_version,
            "ACL_VERSION_MISSING": o.acl_version,
            "REQUESTER_MISSING": o.requester_principal,
            "PURPOSE_MISSING": o.purpose,
            "POLICY_VERSION_MISSING": o.policy_version,
            "AUTHORITY_VERSION_MISSING": o.authority_version,
            "CONTEXT_FINGERPRINT_MISSING": o.context_fingerprint,
        }
        for code, value in required.items():
            if not isinstance(value, str) or not value.strip():
                reasons.append(code)
        for code, value in (
            ("CONTENT_FINGERPRINT_INVALID", o.content_fingerprint),
            ("VECTOR_FINGERPRINT_INVALID", o.vector_fingerprint),
            ("INDEX_FINGERPRINT_INVALID", o.index_fingerprint),
            ("CONTEXT_FINGERPRINT_INVALID", o.context_fingerprint),
        ):
            if not _valid_sha256(value):
                reasons.append(code)
        if not isinstance(o.embedding_dimension, int) or isinstance(o.embedding_dimension, bool) or o.embedding_dimension <= 0:
            reasons.append("EMBEDDING_DIMENSION_INVALID")
        if not _valid_nonnegative_finite(o.anomaly_score):
            reasons.append("ANOMALY_SCORE_INVALID")
        if not isinstance(o.suspicious_marker_count, int) or isinstance(o.suspicious_marker_count, bool) or o.suspicious_marker_count < 0:
            reasons.append("SUSPICIOUS_MARKER_COUNT_INVALID")
        if (not isinstance(o.allowed_principals, tuple) or not o.allowed_principals
                or any((not isinstance(x, str) or not x.strip()) for x in o.allowed_principals)):
            reasons.append("ACL_PRINCIPALS_INVALID")
        return tuple(sorted(set(reasons)))

    def evaluate(self, o: VectorObservation, *, use_cache: bool = True) -> GuardResult:
        invalid = self._validate(o)
        if invalid:
            return GuardResult(Decision.DENY, invalid, _fp({"invalid": invalid, "document_id": o.document_id}), False)

        obs_fp = _fp(o)
        key = _fp({"observation": obs_fp, "policy": _fp(self.policy)})
        if use_cache and key in self._cache:
            cached = self._cache[key]
            return GuardResult(cached.decision, cached.reason_codes, cached.observation_fingerprint, True)

        reasons = []
        decision = Decision.ALLOW_CANDIDATE

        if o.policy_version != self.policy.policy_version:
            reasons.append("POLICY_VERSION_MISMATCH")
            decision = Decision.HOLD
        if o.authority_version != self.policy.authority_version:
            reasons.append("AUTHORITY_VERSION_MISMATCH")
            decision = Decision.HOLD

        if self.policy.require_signature and not o.signature_verified:
            reasons.append("SIGNATURE_NOT_VERIFIED")
            decision = Decision.QUARANTINE
        if self.policy.require_source_binding and not o.source_binding_verified:
            reasons.append("SOURCE_BINDING_NOT_VERIFIED")
            decision = max_decision(decision, Decision.HOLD)
        if self.policy.require_provenance and not o.provenance_verified:
            reasons.append("PROVENANCE_NOT_VERIFIED")
            decision = max_decision(decision, Decision.HOLD)

        if o.embedding_model_id != self.policy.expected_embedding_model_id:
            reasons.append("EMBEDDING_MODEL_ID_MISMATCH")
            decision = max_decision(decision, Decision.HOLD)
        if o.embedding_model_version != self.policy.expected_embedding_model_version:
            reasons.append("EMBEDDING_MODEL_VERSION_MISMATCH")
            decision = max_decision(decision, Decision.HOLD)
        if o.embedding_dimension != self.policy.expected_dimension:
            reasons.append("EMBEDDING_DIMENSION_MISMATCH")
            decision = max_decision(decision, Decision.HOLD)
        if o.index_id != self.policy.expected_index_id:
            reasons.append("INDEX_ID_MISMATCH")
            decision = max_decision(decision, Decision.HOLD)
        if o.index_version != self.policy.expected_index_version:
            reasons.append("INDEX_VERSION_MISMATCH")
            decision = max_decision(decision, Decision.HOLD)

        if self.policy.require_acl_match and o.requester_principal not in set(o.allowed_principals):
            reasons.append("ACL_DENY")
            decision = Decision.DENY

        if _sensitive(o.classification) and self.policy.require_consent_for_sensitive and not o.consent_evidence:
            reasons.append("CONSENT_EVIDENCE_MISSING")
            decision = Decision.DENY

        if o.suspicious_marker_count > 0:
            reasons.append("SUSPICIOUS_MARKER_PRESENT")
            decision = max_decision(decision, Decision.HUMAN_CONFIRM)
        if o.anomaly_score >= self.policy.quarantine_anomaly_score:
            reasons.append("ANOMALY_QUARANTINE_THRESHOLD")
            decision = max_decision(decision, Decision.QUARANTINE)
        elif o.anomaly_score > self.policy.max_anomaly_score:
            reasons.append("ANOMALY_REVIEW_THRESHOLD")
            decision = max_decision(decision, Decision.HUMAN_CONFIRM)

        result = GuardResult(decision, tuple(sorted(set(reasons))), obs_fp, False)
        if use_cache:
            self._cache[key] = result
        return result


_DECISION_RANK = {
    Decision.ALLOW_CANDIDATE: 0,
    Decision.HUMAN_CONFIRM: 1,
    Decision.HOLD: 2,
    Decision.QUARANTINE: 3,
    Decision.DENY: 4,
}


def max_decision(a: Decision, b: Decision) -> Decision:
    return a if _DECISION_RANK[a] >= _DECISION_RANK[b] else b


def baseline_fingerprint(b: IndexBaseline) -> str:
    normalized = IndexBaseline(
        index_id=b.index_id,
        index_version=b.index_version,
        entries=tuple(sorted(b.entries, key=lambda e: e.document_id)),
    )
    return _fp(normalized)


def build_index_delta(base: IndexBaseline, target: IndexBaseline) -> IndexDelta:
    if base.index_id != target.index_id:
        raise ValueError("index_id mismatch")
    b = {e.document_id: e for e in base.entries}
    t = {e.document_id: e for e in target.entries}
    changed = tuple(sorted((e for doc, e in t.items() if b.get(doc) != e), key=lambda e: e.document_id))
    removed = tuple(sorted(doc for doc in b if doc not in t))
    return IndexDelta(
        base_fingerprint=baseline_fingerprint(base),
        target_fingerprint=baseline_fingerprint(target),
        base_version=base.index_version,
        target_version=target.index_version,
        changed_entries=changed,
        removed_document_ids=removed,
    )


def reconstruct_index(base: IndexBaseline, delta: IndexDelta) -> IndexBaseline:
    if baseline_fingerprint(base) != delta.base_fingerprint:
        raise ValueError("base fingerprint mismatch")
    data = {e.document_id: e for e in base.entries}
    for doc in delta.removed_document_ids:
        data.pop(doc, None)
    for e in delta.changed_entries:
        data[e.document_id] = e
    rebuilt = IndexBaseline(base.index_id, delta.target_version, tuple(sorted(data.values(), key=lambda e: e.document_id)))
    if baseline_fingerprint(rebuilt) != delta.target_fingerprint:
        raise ValueError("target fingerprint mismatch")
    return rebuilt


def package_manifest() -> Mapping[str, str]:
    return {
        "technology": "32",
        "name": "ベクトルDB・埋め込み整合性ガード",
        "creator": CREATOR,
        "version": VERSION,
        "license": "NOT SPECIFIED",
    }
