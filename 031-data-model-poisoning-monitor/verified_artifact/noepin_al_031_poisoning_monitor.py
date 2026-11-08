from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from hashlib import sha256
import json
import math
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple

VERSION = "2.0.0-successor.20261102"
CREATOR = "NOEPIN / のえぴん"


class AssetKind(str, Enum):
    TRAINING_DATA = "TRAINING_DATA"
    EVAL_DATA = "EVAL_DATA"
    RAG_DOCUMENT = "RAG_DOCUMENT"
    MODEL_ARTIFACT = "MODEL_ARTIFACT"
    INDEX = "INDEX"
    EMBEDDING_SET = "EMBEDDING_SET"


class Decision(str, Enum):
    ALLOW_CANDIDATE = "ALLOW_CANDIDATE"
    HUMAN_CONFIRM = "HUMAN_CONFIRM"
    HOLD = "HOLD"
    QUARANTINE = "QUARANTINE"
    DENY = "DENY"


@dataclass(frozen=True)
class AssetObservation:
    asset_id: str
    asset_kind: AssetKind
    asset_version: str
    baseline_version: str
    baseline_fingerprint: str
    current_fingerprint: str
    signature_verified: bool
    provenance_verified: bool
    source_verified: bool
    anomaly_score: float
    distribution_shift_score: float
    label_shift_score: float
    duplicate_ratio: float
    poisoned_sample_count: int
    total_sample_count: int
    suspicious_marker_count: int
    classification: str
    purpose: str
    expected_purpose: str
    consent_required: bool
    consent_evidence: bool
    policy_version: str
    authority_version: str
    baseline_index_version: str = ""
    current_index_version: str = ""
    context_fingerprint: str = ""


@dataclass(frozen=True)
class MonitorResult:
    decision: Decision
    reason_codes: Tuple[str, ...]
    observation_fingerprint: str
    cache_reused: bool
    anomaly_detected: bool
    changed_from_baseline: bool
    quarantine_candidate: bool
    truth_established: bool = False
    poisoning_proven: bool = False
    data_isolated: bool = False
    model_disabled: bool = False
    classification_changed: bool = False
    consent_changed: bool = False
    purpose_changed: bool = False
    action_executed: bool = False
    action_succeeded: bool = False
    state_committed: bool = False


@dataclass(frozen=True)
class DeltaSummary:
    base_fingerprint: str
    target_fingerprint: str
    changed: Tuple[str, ...]
    added: Tuple[str, ...]
    removed: Tuple[str, ...]
    delta_fingerprint: str


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha(value: Any) -> str:
    return sha256(_canonical(value).encode("utf-8")).hexdigest()


def _validate_score(name: str, value: float) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
        raise ValueError(f"{name.upper()}_NON_FINITE")
    if not 0.0 <= float(value) <= 1.0:
        raise ValueError(f"{name.upper()}_OUT_OF_RANGE")


def _validate_observation(o: AssetObservation) -> None:
    for name in (
        "asset_id", "asset_version", "baseline_version", "baseline_fingerprint",
        "current_fingerprint", "classification", "purpose", "expected_purpose",
        "policy_version", "authority_version"
    ):
        value = getattr(o, name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name.upper()}_REQUIRED")
    if len(o.baseline_fingerprint) < 16 or len(o.current_fingerprint) < 16:
        raise ValueError("FINGERPRINT_TOO_SHORT")
    for name in ("anomaly_score", "distribution_shift_score", "label_shift_score", "duplicate_ratio"):
        _validate_score(name, getattr(o, name))
    for name in ("poisoned_sample_count", "total_sample_count", "suspicious_marker_count"):
        value = getattr(o, name)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"{name.upper()}_INVALID")
    if o.poisoned_sample_count > o.total_sample_count:
        raise ValueError("POISONED_GT_TOTAL")
    if o.consent_required and not isinstance(o.consent_evidence, bool):
        raise ValueError("CONSENT_EVIDENCE_INVALID")


def observation_fingerprint(o: AssetObservation) -> str:
    _validate_observation(o)
    payload = asdict(o)
    payload["asset_kind"] = o.asset_kind.value
    return _sha(payload)


class DataModelPoisoningMonitor:
    """Pure decision control. It never mutates data/models, quarantines storage, or disables models."""

    def __init__(self, *, cache_enabled: bool = True) -> None:
        self.cache_enabled = cache_enabled
        self._cache: Dict[str, MonitorResult] = {}

    def clear_cache(self) -> None:
        self._cache.clear()

    def evaluate(self, observation: AssetObservation) -> MonitorResult:
        try:
            fp = observation_fingerprint(observation)
        except ValueError as exc:
            return MonitorResult(
                decision=Decision.DENY,
                reason_codes=(str(exc),),
                observation_fingerprint="INVALID",
                cache_reused=False,
                anomaly_detected=False,
                changed_from_baseline=False,
                quarantine_candidate=False,
            )

        if self.cache_enabled and fp in self._cache:
            previous = self._cache[fp]
            return MonitorResult(**{**asdict(previous), "decision": previous.decision, "cache_reused": True})

        reasons = []
        changed = observation.current_fingerprint != observation.baseline_fingerprint or observation.asset_version != observation.baseline_version
        anomaly_detected = any((
            observation.anomaly_score >= 0.35,
            observation.distribution_shift_score >= 0.30,
            observation.label_shift_score >= 0.30,
            observation.suspicious_marker_count > 0,
            observation.poisoned_sample_count > 0,
        ))

        if observation.purpose != observation.expected_purpose:
            decision = Decision.HOLD
            reasons.append("PURPOSE_MISMATCH")
        elif observation.consent_required and not observation.consent_evidence:
            decision = Decision.HOLD
            reasons.append("CONSENT_EVIDENCE_REQUIRED")
        elif not observation.signature_verified:
            decision = Decision.QUARANTINE
            reasons.append("SIGNATURE_UNVERIFIED")
        elif not observation.provenance_verified:
            decision = Decision.QUARANTINE
            reasons.append("PROVENANCE_UNVERIFIED")
        elif not observation.source_verified:
            decision = Decision.HOLD
            reasons.append("SOURCE_UNVERIFIED")
        else:
            poisoned_ratio = 0.0 if observation.total_sample_count == 0 else observation.poisoned_sample_count / observation.total_sample_count
            severe = (
                observation.anomaly_score >= 0.85
                or observation.distribution_shift_score >= 0.80
                or observation.label_shift_score >= 0.80
                or poisoned_ratio >= 0.02
                or observation.suspicious_marker_count >= 5
            )
            moderate = (
                observation.anomaly_score >= 0.55
                or observation.distribution_shift_score >= 0.50
                or observation.label_shift_score >= 0.50
                or poisoned_ratio > 0.0
                or observation.suspicious_marker_count > 0
            )
            index_mismatch = bool(observation.baseline_index_version and observation.current_index_version and observation.baseline_index_version != observation.current_index_version)
            if severe:
                decision = Decision.QUARANTINE
                reasons.append("SEVERE_ANOMALY_CANDIDATE")
            elif index_mismatch and changed:
                decision = Decision.HOLD
                reasons.append("INDEX_VERSION_CHANGED")
            elif moderate:
                decision = Decision.HUMAN_CONFIRM
                reasons.append("ANOMALY_REVIEW_REQUIRED")
            elif changed:
                decision = Decision.HUMAN_CONFIRM
                reasons.append("BASELINE_CHANGE_REVIEW_REQUIRED")
            else:
                decision = Decision.ALLOW_CANDIDATE
                reasons.append("BASELINE_MATCH_NO_MATERIAL_ANOMALY")

        result = MonitorResult(
            decision=decision,
            reason_codes=tuple(reasons),
            observation_fingerprint=fp,
            cache_reused=False,
            anomaly_detected=anomaly_detected,
            changed_from_baseline=changed,
            quarantine_candidate=decision == Decision.QUARANTINE,
        )
        if self.cache_enabled:
            self._cache[fp] = result
        return result


def dataset_fingerprint(items: Mapping[str, str], *, version: str) -> str:
    if not isinstance(version, str) or not version.strip():
        raise ValueError("VERSION_REQUIRED")
    clean: Dict[str, str] = {}
    for key, value in items.items():
        if not isinstance(key, str) or not key or not isinstance(value, str) or not value:
            raise ValueError("INVALID_DATASET_ENTRY")
        clean[key] = value
    return _sha({"version": version, "items": clean})


def build_delta(base: Mapping[str, str], target: Mapping[str, str], *, base_version: str, target_version: str) -> DeltaSummary:
    base_fp = dataset_fingerprint(base, version=base_version)
    target_fp = dataset_fingerprint(target, version=target_version)
    changed = tuple(sorted(k for k in base.keys() & target.keys() if base[k] != target[k]))
    added = tuple(sorted(target.keys() - base.keys()))
    removed = tuple(sorted(base.keys() - target.keys()))
    delta_fp = _sha({
        "base_fingerprint": base_fp,
        "target_fingerprint": target_fp,
        "base_version": base_version,
        "target_version": target_version,
        "changed": {k: target[k] for k in changed},
        "added": {k: target[k] for k in added},
        "removed": removed,
    })
    return DeltaSummary(base_fp, target_fp, changed, added, removed, delta_fp)


def reconstruct_delta(base: Mapping[str, str], target_values: Mapping[str, str], delta: DeltaSummary, *, base_version: str, target_version: str) -> Dict[str, str]:
    if dataset_fingerprint(base, version=base_version) != delta.base_fingerprint:
        raise ValueError("BASE_FINGERPRINT_MISMATCH")
    out = dict(base)
    for key in delta.removed:
        out.pop(key, None)
    for key in delta.changed + delta.added:
        if key not in target_values:
            raise ValueError("DELTA_VALUE_MISSING")
        out[key] = target_values[key]
    if dataset_fingerprint(out, version=target_version) != delta.target_fingerprint:
        raise ValueError("TARGET_FINGERPRINT_MISMATCH")
    return out
