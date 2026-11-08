"""NOEPIN AL 038 — AI Memory Retention / Deletion Governor.

Creator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん

AI-assisted implementation / analysis / documentation support using ChatGPT.
License / Rights: NOT SPECIFIED.

This module is a control-plane evaluator. It NEVER persists, deletes, transmits,
or mutates an external memory store. Decisions are candidates for downstream
authoritative enforcement only.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from hashlib import sha256
import json
from typing import FrozenSet, Iterable, Mapping, Optional, Tuple


class Decision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    HOLD = "HOLD"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"


VALID_OPERATIONS = frozenset({"STORE", "USE", "RETAIN", "DELETE"})
VALID_CLASSIFICATIONS = frozenset({"PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"})


@dataclass(frozen=True)
class MemoryPolicy:
    policy_id: str
    version: int
    authority_epoch: int
    allowed_purposes: FrozenSet[str]
    default_retention_seconds: int
    max_retention_seconds: int
    classifications_allowed: FrozenSet[str] = VALID_CLASSIFICATIONS
    delete_requires_human: bool = False
    store_requires_human: bool = False
    revoked: bool = False


@dataclass(frozen=True)
class MemoryRecordMeta:
    memory_id: str
    created_at: int
    expires_at: int
    purposes: FrozenSet[str]
    classification: str
    policy_id: str
    policy_version: int
    authority_epoch: int
    legal_hold: bool = False
    deletion_requested: bool = False


@dataclass(frozen=True)
class MemoryRequest:
    operation: str
    purpose: str
    now: int
    requested_retention_seconds: int = 0
    classification: str = "INTERNAL"
    human_approval_evidence: bool = False
    subject_deletion_request: bool = False
    expected_policy_id: Optional[str] = None
    expected_policy_version: Optional[int] = None
    expected_authority_epoch: Optional[int] = None


@dataclass(frozen=True)
class Evaluation:
    decision: Decision
    reason_codes: Tuple[str, ...]
    action_executed: bool = False
    memory_written: bool = False
    memory_deleted: bool = False
    truth_established: bool = False
    permission_granted: bool = False
    provisional: bool = False


def _canon(obj) -> str:
    def normalize(v):
        if isinstance(v, Enum):
            return v.value
        if isinstance(v, frozenset):
            return sorted(v)
        if isinstance(v, tuple):
            return [normalize(x) for x in v]
        if hasattr(v, "__dataclass_fields__"):
            return {k: normalize(val) for k, val in asdict(v).items()}
        if isinstance(v, Mapping):
            return {str(k): normalize(v[k]) for k in sorted(v, key=lambda x: str(x))}
        if isinstance(v, (list, set)):
            return [normalize(x) for x in v]
        return v
    return json.dumps(normalize(obj), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(obj) -> str:
    return sha256(_canon(obj).encode("utf-8")).hexdigest()


def validate_policy(policy: MemoryPolicy) -> None:
    if not policy.policy_id or policy.version < 1 or policy.authority_epoch < 1:
        raise ValueError("invalid policy identity/version")
    if policy.default_retention_seconds < 0 or policy.max_retention_seconds < 0:
        raise ValueError("negative retention")
    if policy.default_retention_seconds > policy.max_retention_seconds:
        raise ValueError("default retention exceeds max")
    if not policy.allowed_purposes or any((not p or len(p) > 128) for p in policy.allowed_purposes):
        raise ValueError("invalid purposes")
    if not policy.classifications_allowed.issubset(VALID_CLASSIFICATIONS):
        raise ValueError("invalid classification policy")


def validate_record(record: MemoryRecordMeta) -> None:
    if not record.memory_id or record.created_at < 0 or record.expires_at < record.created_at:
        raise ValueError("invalid record metadata")
    if not record.purposes or any(not p for p in record.purposes):
        raise ValueError("invalid record purposes")
    if record.classification not in VALID_CLASSIFICATIONS:
        raise ValueError("invalid record classification")
    if not record.policy_id or record.policy_version < 1 or record.authority_epoch < 1:
        raise ValueError("invalid record authority metadata")


def _invalid(reason: str) -> Evaluation:
    return Evaluation(Decision.DENY, (reason,))


def evaluate(policy: MemoryPolicy, request: MemoryRequest, record: Optional[MemoryRecordMeta] = None) -> Evaluation:
    """Pure evaluation; never performs store/delete/use side effects."""
    try:
        validate_policy(policy)
        if record is not None:
            validate_record(record)
    except (TypeError, ValueError):
        return _invalid("INVALID_METADATA")

    if request.operation not in VALID_OPERATIONS:
        return _invalid("INVALID_OPERATION")
    if not request.purpose or request.now < 0:
        return _invalid("INVALID_REQUEST")
    if request.classification not in VALID_CLASSIFICATIONS:
        return _invalid("INVALID_CLASSIFICATION")
    if policy.revoked:
        return _invalid("POLICY_REVOKED")

    if request.expected_policy_id is not None and request.expected_policy_id != policy.policy_id:
        return _invalid("POLICY_ID_MISMATCH")
    if request.expected_policy_version is not None and request.expected_policy_version != policy.version:
        return _invalid("POLICY_VERSION_MISMATCH")
    if request.expected_authority_epoch is not None and request.expected_authority_epoch != policy.authority_epoch:
        return _invalid("AUTHORITY_EPOCH_MISMATCH")

    if request.purpose not in policy.allowed_purposes:
        return _invalid("PURPOSE_NOT_ALLOWED")
    if request.classification not in policy.classifications_allowed:
        return _invalid("CLASSIFICATION_NOT_ALLOWED")

    op = request.operation
    if op == "STORE":
        if record is not None:
            return _invalid("STORE_REQUIRES_NEW_RECORD")
        retention = request.requested_retention_seconds or policy.default_retention_seconds
        if retention <= 0 or retention > policy.max_retention_seconds:
            return _invalid("RETENTION_OUT_OF_RANGE")
        if policy.store_requires_human and not request.human_approval_evidence:
            return Evaluation(Decision.HUMAN_APPROVAL, ("HUMAN_APPROVAL_REQUIRED_FOR_STORE",))
        return Evaluation(Decision.ALLOW, ("STORE_POLICY_MATCH",))

    if record is None:
        return _invalid("RECORD_REQUIRED")
    if record.policy_id != policy.policy_id:
        return _invalid("RECORD_POLICY_ID_MISMATCH")
    if record.policy_version != policy.version:
        return _invalid("RECORD_POLICY_VERSION_MISMATCH")
    if record.authority_epoch != policy.authority_epoch:
        return _invalid("RECORD_AUTHORITY_EPOCH_MISMATCH")
    if request.purpose not in record.purposes:
        return _invalid("RECORD_PURPOSE_MISMATCH")
    if request.classification != record.classification:
        return _invalid("RECORD_CLASSIFICATION_MISMATCH")

    expired = request.now >= record.expires_at

    if op == "USE":
        if record.deletion_requested:
            return _invalid("DELETION_PENDING_NO_REUSE")
        if expired:
            return _invalid("MEMORY_EXPIRED")
        return Evaluation(Decision.ALLOW, ("USE_POLICY_MATCH",))

    if op == "RETAIN":
        if record.deletion_requested:
            return _invalid("DELETION_PENDING_NO_RETENTION")
        if expired:
            return _invalid("MEMORY_EXPIRED")
        requested = request.requested_retention_seconds or policy.default_retention_seconds
        if requested <= 0 or requested > policy.max_retention_seconds:
            return _invalid("RETENTION_OUT_OF_RANGE")
        if record.created_at + requested < request.now:
            return _invalid("RETENTION_ALREADY_ELAPSED")
        return Evaluation(Decision.ALLOW, ("RETENTION_POLICY_MATCH",))

    # DELETE
    if record.legal_hold:
        return Evaluation(Decision.HOLD, ("LEGAL_HOLD",))
    if policy.delete_requires_human and not (request.human_approval_evidence or request.subject_deletion_request):
        return Evaluation(Decision.HUMAN_APPROVAL, ("HUMAN_APPROVAL_REQUIRED_FOR_DELETE",))
    if expired:
        return Evaluation(Decision.ALLOW, ("DELETE_EXPIRED_CANDIDATE",))
    if request.subject_deletion_request:
        return Evaluation(Decision.ALLOW, ("SUBJECT_DELETE_CANDIDATE",))
    return Evaluation(Decision.ALLOW, ("DELETE_POLICY_MATCH",))


@dataclass(frozen=True)
class PreparedEvaluation:
    request_fingerprint: str
    policy_fingerprint: str
    record_fingerprint: Optional[str]
    authority_epoch: int
    result: Evaluation


def prepare(policy: MemoryPolicy, request: MemoryRequest, record: Optional[MemoryRecordMeta] = None) -> PreparedEvaluation:
    return PreparedEvaluation(
        request_fingerprint=fingerprint(request),
        policy_fingerprint=fingerprint(policy),
        record_fingerprint=fingerprint(record) if record is not None else None,
        authority_epoch=policy.authority_epoch,
        result=evaluate(policy, request, record),
    )


def reuse_prepared(prepared: PreparedEvaluation, policy: MemoryPolicy, request: MemoryRequest, record: Optional[MemoryRecordMeta] = None) -> Optional[Evaluation]:
    """DCSR read-side exact-state reuse only. None means normal evaluation required."""
    if policy.authority_epoch != prepared.authority_epoch:
        return None
    if fingerprint(policy) != prepared.policy_fingerprint:
        return None
    if fingerprint(request) != prepared.request_fingerprint:
        return None
    current_rf = fingerprint(record) if record is not None else None
    if current_rf != prepared.record_fingerprint:
        return None
    return prepared.result


def reuse_prepared_by_fingerprints(
    prepared: PreparedEvaluation,
    *,
    request_fingerprint: str,
    policy_fingerprint: str,
    record_fingerprint: Optional[str],
    authority_epoch: int,
) -> Optional[Evaluation]:
    """Fast DCSR path when canonical fingerprints are already materialized.

    The fingerprints are evidence of exact state identity only. They do not grant
    authority; authority_epoch must still match. A mismatch returns None so the
    caller falls back to normal evaluation.
    """
    if authority_epoch != prepared.authority_epoch:
        return None
    if policy_fingerprint != prepared.policy_fingerprint:
        return None
    if request_fingerprint != prepared.request_fingerprint:
        return None
    if record_fingerprint != prepared.record_fingerprint:
        return None
    return prepared.result


@dataclass(frozen=True)
class MetadataDelta:
    base_fingerprint: str
    target_fingerprint: str
    changed: Tuple[Tuple[str, MemoryRecordMeta], ...]
    removed_ids: Tuple[str, ...]
    added: Tuple[Tuple[str, MemoryRecordMeta], ...]


def registry_fingerprint(registry: Mapping[str, MemoryRecordMeta]) -> str:
    return fingerprint({k: registry[k] for k in sorted(registry)})


def build_metadata_delta(base: Mapping[str, MemoryRecordMeta], target: Mapping[str, MemoryRecordMeta]) -> MetadataDelta:
    changed = []
    added = []
    for key in sorted(target):
        if key not in base:
            added.append((key, target[key]))
        elif target[key] != base[key]:
            changed.append((key, target[key]))
    removed = tuple(sorted(set(base) - set(target)))
    return MetadataDelta(registry_fingerprint(base), registry_fingerprint(target), tuple(changed), removed, tuple(added))


def apply_metadata_delta(base: Mapping[str, MemoryRecordMeta], delta: MetadataDelta) -> Mapping[str, MemoryRecordMeta]:
    if registry_fingerprint(base) != delta.base_fingerprint:
        raise ValueError("base fingerprint mismatch")
    out = dict(base)
    for key in delta.removed_ids:
        out.pop(key, None)
    for key, value in delta.changed:
        out[key] = value
    for key, value in delta.added:
        out[key] = value
    if registry_fingerprint(out) != delta.target_fingerprint:
        raise ValueError("target fingerprint mismatch")
    return out


def decision_digest(values: Iterable[Evaluation]) -> str:
    return sha256("\n".join(_canon(v) for v in values).encode("utf-8")).hexdigest()
