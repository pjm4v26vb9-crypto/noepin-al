"""NOEPIN AL 042 — AI Incident Response / Evidence Preservation Governor.

Pure control-plane implementation. It constructs deterministic incident/evidence
records and containment *candidates*. It performs no persistence, deletion,
network transmission, process execution, alert execution, or containment action.

Creator / Project Owner / Original Concept / Architecture Direction:
NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support using ChatGPT
License / Rights: NOT SPECIFIED
"""
from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Any, FrozenSet, Iterable, Mapping, Sequence, Tuple

CREATOR = "NOEPIN / のえぴん"
LICENSE_STATUS = "NOT SPECIFIED"
TECHNOLOGY_ID = "NOEPIN-AL-042"


class ControlDecision(str, Enum):
    ALLOW = "ALLOW"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"
    HOLD = "HOLD"
    DENY = "DENY"


class EvidenceType(str, Enum):
    LOG = "LOG"
    INPUT = "INPUT"
    AUTHORITY_STATE = "AUTHORITY_STATE"
    NETWORK_STATE = "NETWORK_STATE"
    CHANGE_DELTA = "CHANGE_DELTA"
    SNAPSHOT = "SNAPSHOT"
    OTHER = "OTHER"


class IncidentSeverity(int, Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class ContainmentCandidate(str, Enum):
    NONE = "NONE"
    REVIEW = "REVIEW"
    RESTRICT_CANDIDATE = "RESTRICT_CANDIDATE"
    ISOLATE_CANDIDATE = "ISOLATE_CANDIDATE"


@dataclass(frozen=True)
class PreservationPolicy:
    policy_id: str
    version: str
    authority_epoch: int
    issued_at: int
    expires_at: int
    required_types: FrozenSet[EvidenceType]
    allowed_classifications: FrozenSet[str]
    human_approval_classifications: FrozenSet[str] = field(default_factory=frozenset)
    max_evidence_age_seconds: int = 86400
    max_future_skew_seconds: int = 300
    containment_review_threshold: IncidentSeverity = IncidentSeverity.MEDIUM
    containment_restrict_threshold: IncidentSeverity = IncidentSeverity.HIGH
    containment_isolate_threshold: IncidentSeverity = IncidentSeverity.CRITICAL
    revoked: bool = False

    def validate(self, now: int) -> None:
        if not self.policy_id or not self.version:
            raise ValueError("policy identity/version required")
        if self.authority_epoch < 1:
            raise ValueError("authority_epoch must be >=1")
        if self.issued_at < 0 or self.expires_at <= self.issued_at:
            raise ValueError("invalid policy lifetime")
        if self.revoked:
            raise ValueError("policy revoked")
        if now < self.issued_at:
            raise ValueError("policy not yet valid")
        if now >= self.expires_at:
            raise ValueError("policy expired")
        if not self.required_types:
            raise ValueError("required evidence types required")
        if not self.allowed_classifications:
            raise ValueError("allowed classifications required")
        if not self.human_approval_classifications.issubset(self.allowed_classifications):
            raise ValueError("human approval classifications must be allowed")
        if any(not isinstance(x, str) or not x.strip() for x in self.allowed_classifications):
            raise ValueError("invalid classification")
        if self.max_evidence_age_seconds < 0 or self.max_future_skew_seconds < 0:
            raise ValueError("invalid evidence timing window")
        if not (
            int(self.containment_review_threshold)
            <= int(self.containment_restrict_threshold)
            <= int(self.containment_isolate_threshold)
        ):
            raise ValueError("invalid containment thresholds")


@dataclass(frozen=True)
class IncidentRequest:
    incident_id: str
    actor_id: str
    observed_at: int
    severity: IncidentSeverity
    trigger: str
    expected_policy_id: str
    expected_policy_version: str
    expected_authority_epoch: int
    evidence_binding: str
    requested_containment_review: bool = True

    def validate(self) -> None:
        if not self.incident_id or not self.actor_id or not self.trigger or not self.evidence_binding:
            raise ValueError("incident identity/trigger/evidence binding required")
        if self.observed_at < 0:
            raise ValueError("observed_at must be non-negative")
        if not self.expected_policy_id or not self.expected_policy_version:
            raise ValueError("expected policy identity/version required")
        if self.expected_authority_epoch < 1:
            raise ValueError("expected_authority_epoch must be >=1")


@dataclass(frozen=True)
class EvidenceSegment:
    segment_id: str
    incident_id: str
    evidence_type: EvidenceType
    captured_at: int
    source_id: str
    source_version: str
    classification: str
    content_sha256: str
    byte_length: int
    sequence: int
    previous_segment_fingerprint: str
    evidence_binding: str
    integrity_verified: bool

    def validate(self) -> None:
        if not self.segment_id or not self.incident_id or not self.source_id or not self.source_version:
            raise ValueError("segment identity/source required")
        if self.captured_at < 0 or self.sequence < 0 or self.byte_length < 0:
            raise ValueError("invalid segment numeric value")
        if not self.classification or not self.evidence_binding:
            raise ValueError("classification/evidence binding required")
        if len(self.content_sha256) != 64 or any(c not in "0123456789abcdef" for c in self.content_sha256.lower()):
            raise ValueError("content_sha256 must be 64 hex chars")
        if self.sequence == 0 and self.previous_segment_fingerprint:
            raise ValueError("first segment must not have previous fingerprint")
        if self.sequence > 0 and not self.previous_segment_fingerprint:
            raise ValueError("non-first segment requires previous fingerprint")


@dataclass(frozen=True)
class IncidentState:
    incident_id: str
    version: str
    authority_epoch: int
    evidence_binding: str
    segments: Tuple[EvidenceSegment, ...]

    def validate(self) -> None:
        if not self.incident_id or not self.version or not self.evidence_binding:
            raise ValueError("incident state identity/version/binding required")
        if self.authority_epoch < 1:
            raise ValueError("authority_epoch must be >=1")
        ids = [s.segment_id for s in self.segments]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate segment_id")
        seqs = [s.sequence for s in self.segments]
        if len(seqs) != len(set(seqs)):
            raise ValueError("duplicate sequence")
        for s in self.segments:
            s.validate()
            if s.incident_id != self.incident_id:
                raise ValueError("segment incident mismatch")
            if s.evidence_binding != self.evidence_binding:
                raise ValueError("segment evidence binding mismatch")


@dataclass(frozen=True)
class PreparedIncidentState:
    state: IncidentState
    state_fingerprint: str
    segments_by_id: Mapping[str, EvidenceSegment]
    segment_fingerprints: Mapping[str, str]
    segments_by_type: Mapping[EvidenceType, Tuple[str, ...]]
    integrity_chain_valid: bool


@dataclass(frozen=True)
class EvidenceDelta:
    base_fingerprint: str
    target_fingerprint: str
    target_incident_id: str
    target_version: str
    target_authority_epoch: int
    target_evidence_binding: str
    changed_segments: Tuple[EvidenceSegment, ...]
    removed_segment_ids: Tuple[str, ...]
    added_segments: Tuple[EvidenceSegment, ...]


@dataclass(frozen=True)
class TransferPlan:
    state_fingerprint: str
    missing_segment_ids: Tuple[str, ...]
    already_known_segment_ids: Tuple[str, ...]
    transfer_required: bool
    full_resend_required: bool = False


@dataclass(frozen=True)
class IncidentAssessment:
    decision: ControlDecision
    incident_id: str
    severity: IncidentSeverity
    reasons: Tuple[str, ...]
    missing_evidence_types: Tuple[EvidenceType, ...]
    segment_ids: Tuple[str, ...]
    integrity_chain_valid: bool
    preservation_complete_candidate: bool
    containment_candidate: ContainmentCandidate
    policy_fingerprint: str
    request_fingerprint: str
    state_fingerprint: str
    bundle_fingerprint: str
    evidence_preserved: bool = False
    persistence_performed: bool = False
    containment_executed: bool = False
    incident_resolved: bool = False
    truth_proven: bool = False
    permission_granted: bool = False
    action_success: bool = False


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {f.name: _jsonable(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, Mapping):
        return {str(k.value if isinstance(k, Enum) else k): _jsonable(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (set, frozenset)):
        return sorted((_jsonable(v) for v in value), key=lambda x: json.dumps(x, sort_keys=True, ensure_ascii=False))
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def fingerprint(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def content_digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def segment_fingerprint(segment: EvidenceSegment) -> str:
    return fingerprint(segment)


def build_segment(
    *,
    segment_id: str,
    incident_id: str,
    evidence_type: EvidenceType,
    captured_at: int,
    source_id: str,
    source_version: str,
    classification: str,
    payload: bytes,
    sequence: int,
    previous_segment_fingerprint: str,
    evidence_binding: str,
    integrity_verified: bool = True,
) -> EvidenceSegment:
    return EvidenceSegment(
        segment_id=segment_id,
        incident_id=incident_id,
        evidence_type=evidence_type,
        captured_at=captured_at,
        source_id=source_id,
        source_version=source_version,
        classification=classification,
        content_sha256=content_digest(payload),
        byte_length=len(payload),
        sequence=sequence,
        previous_segment_fingerprint=previous_segment_fingerprint,
        evidence_binding=evidence_binding,
        integrity_verified=integrity_verified,
    )


def _sorted_segments(segments: Iterable[EvidenceSegment]) -> Tuple[EvidenceSegment, ...]:
    return tuple(sorted(segments, key=lambda s: (s.sequence, s.segment_id)))


def verify_integrity_chain(state: IncidentState) -> bool:
    try:
        state.validate()
    except ValueError:
        return False
    ordered = _sorted_segments(state.segments)
    if not ordered:
        return True
    if ordered[0].sequence != 0 or ordered[0].previous_segment_fingerprint:
        return False
    for index, seg in enumerate(ordered):
        if seg.sequence != index:
            return False
        if not seg.integrity_verified:
            return False
        if index > 0:
            expected = segment_fingerprint(ordered[index - 1])
            if seg.previous_segment_fingerprint != expected:
                return False
    return True


def normalize_state(state: IncidentState) -> IncidentState:
    state.validate()
    return IncidentState(
        incident_id=state.incident_id,
        version=state.version,
        authority_epoch=state.authority_epoch,
        evidence_binding=state.evidence_binding,
        segments=_sorted_segments(state.segments),
    )


def prepare_state(state: IncidentState) -> PreparedIncidentState:
    normalized = normalize_state(state)
    by_id = {s.segment_id: s for s in normalized.segments}
    seg_fps = {sid: segment_fingerprint(seg) for sid, seg in by_id.items()}
    by_type: dict[EvidenceType, list[str]] = {}
    for seg in normalized.segments:
        by_type.setdefault(seg.evidence_type, []).append(seg.segment_id)
    return PreparedIncidentState(
        state=normalized,
        state_fingerprint=fingerprint(normalized),
        segments_by_id=by_id,
        segment_fingerprints=seg_fps,
        segments_by_type={k: tuple(v) for k, v in sorted(by_type.items(), key=lambda kv: kv[0].value)},
        integrity_chain_valid=verify_integrity_chain(normalized),
    )


def _containment_candidate(policy: PreservationPolicy, request: IncidentRequest) -> ContainmentCandidate:
    if not request.requested_containment_review:
        return ContainmentCandidate.NONE
    sev = int(request.severity)
    if sev >= int(policy.containment_isolate_threshold):
        return ContainmentCandidate.ISOLATE_CANDIDATE
    if sev >= int(policy.containment_restrict_threshold):
        return ContainmentCandidate.RESTRICT_CANDIDATE
    if sev >= int(policy.containment_review_threshold):
        return ContainmentCandidate.REVIEW
    return ContainmentCandidate.NONE


def _hold_assessment(request: IncidentRequest, policy: PreservationPolicy, state_fp: str, reasons: Iterable[str]) -> IncidentAssessment:
    reasons_tuple = tuple(sorted(set(reasons)))
    payload = {
        "decision": ControlDecision.HOLD.value,
        "incident_id": request.incident_id,
        "reasons": reasons_tuple,
        "state_fingerprint": state_fp,
    }
    return IncidentAssessment(
        decision=ControlDecision.HOLD,
        incident_id=request.incident_id,
        severity=request.severity,
        reasons=reasons_tuple,
        missing_evidence_types=tuple(),
        segment_ids=tuple(),
        integrity_chain_valid=False,
        preservation_complete_candidate=False,
        containment_candidate=ContainmentCandidate.NONE,
        policy_fingerprint=fingerprint(policy),
        request_fingerprint=fingerprint(request),
        state_fingerprint=state_fp,
        bundle_fingerprint=fingerprint(payload),
    )


def assess_prepared(
    request: IncidentRequest,
    policy: PreservationPolicy,
    prepared: PreparedIncidentState,
    *,
    now: int,
) -> IncidentAssessment:
    try:
        request.validate()
        policy.validate(now)
        prepared.state.validate()
    except (ValueError, TypeError) as exc:
        return _hold_assessment(request, policy, prepared.state_fingerprint, ("INVALID_INPUT", type(exc).__name__))

    reasons: list[str] = []
    if request.expected_policy_id != policy.policy_id:
        reasons.append("POLICY_ID_MISMATCH")
    if request.expected_policy_version != policy.version:
        reasons.append("POLICY_VERSION_MISMATCH")
    if request.expected_authority_epoch != policy.authority_epoch:
        reasons.append("AUTHORITY_EPOCH_MISMATCH")
    if prepared.state.incident_id != request.incident_id:
        reasons.append("INCIDENT_ID_MISMATCH")
    if prepared.state.authority_epoch != request.expected_authority_epoch:
        reasons.append("STATE_AUTHORITY_EPOCH_MISMATCH")
    if prepared.state.evidence_binding != request.evidence_binding:
        reasons.append("EVIDENCE_BINDING_MISMATCH")
    if reasons:
        return _hold_assessment(request, policy, prepared.state_fingerprint, reasons)

    integrity_ok = prepared.integrity_chain_valid
    if not integrity_ok:
        return _hold_assessment(request, policy, prepared.state_fingerprint, ("INTEGRITY_CHAIN_INVALID",))

    disallowed = [s.segment_id for s in prepared.state.segments if s.classification not in policy.allowed_classifications]
    if disallowed:
        payload = {
            "decision": ControlDecision.DENY.value,
            "incident_id": request.incident_id,
            "disallowed_segment_ids": tuple(sorted(disallowed)),
            "state_fingerprint": prepared.state_fingerprint,
        }
        return IncidentAssessment(
            decision=ControlDecision.DENY,
            incident_id=request.incident_id,
            severity=request.severity,
            reasons=("CLASSIFICATION_NOT_ALLOWED",),
            missing_evidence_types=tuple(),
            segment_ids=tuple(s.segment_id for s in prepared.state.segments),
            integrity_chain_valid=True,
            preservation_complete_candidate=False,
            containment_candidate=_containment_candidate(policy, request),
            policy_fingerprint=fingerprint(policy),
            request_fingerprint=fingerprint(request),
            state_fingerprint=prepared.state_fingerprint,
            bundle_fingerprint=fingerprint(payload),
        )

    stale: list[str] = []
    future: list[str] = []
    for s in prepared.state.segments:
        if request.observed_at - s.captured_at > policy.max_evidence_age_seconds:
            stale.append(s.segment_id)
        if s.captured_at - request.observed_at > policy.max_future_skew_seconds:
            future.append(s.segment_id)
    if stale or future:
        why = []
        if stale:
            why.append("EVIDENCE_TOO_OLD")
        if future:
            why.append("EVIDENCE_FROM_FUTURE")
        return _hold_assessment(request, policy, prepared.state_fingerprint, why)

    present_types = frozenset(s.evidence_type for s in prepared.state.segments)
    missing = tuple(sorted(policy.required_types - present_types, key=lambda t: t.value))
    sensitive = any(s.classification in policy.human_approval_classifications for s in prepared.state.segments)

    if missing:
        decision = ControlDecision.HOLD
        reasons = ["REQUIRED_EVIDENCE_MISSING"]
    elif sensitive:
        decision = ControlDecision.HUMAN_APPROVAL
        reasons = ["HUMAN_APPROVAL_CLASSIFICATION_PRESENT"]
    else:
        decision = ControlDecision.ALLOW
        reasons = ["EVIDENCE_SET_COMPLETE_CANDIDATE"]

    containment = _containment_candidate(policy, request)
    payload = {
        "decision": decision.value,
        "incident_id": request.incident_id,
        "severity": int(request.severity),
        "reasons": tuple(reasons),
        "missing": tuple(t.value for t in missing),
        "segment_fingerprints": tuple(sorted(prepared.segment_fingerprints.items())),
        "containment_candidate": containment.value,
        "state_fingerprint": prepared.state_fingerprint,
    }
    return IncidentAssessment(
        decision=decision,
        incident_id=request.incident_id,
        severity=request.severity,
        reasons=tuple(reasons),
        missing_evidence_types=missing,
        segment_ids=tuple(s.segment_id for s in prepared.state.segments),
        integrity_chain_valid=True,
        preservation_complete_candidate=not missing,
        containment_candidate=containment,
        policy_fingerprint=fingerprint(policy),
        request_fingerprint=fingerprint(request),
        state_fingerprint=prepared.state_fingerprint,
        bundle_fingerprint=fingerprint(payload),
    )


def assess(request: IncidentRequest, policy: PreservationPolicy, state: IncidentState, *, now: int) -> IncidentAssessment:
    try:
        prepared = prepare_state(state)
    except (ValueError, TypeError):
        prepared = PreparedIncidentState(state, fingerprint(state), {}, {}, {}, False)
    return assess_prepared(request, policy, prepared, now=now)


def make_evidence_delta(base: IncidentState, target: IncidentState) -> EvidenceDelta:
    b = normalize_state(base)
    t = normalize_state(target)
    if b.incident_id != t.incident_id:
        raise ValueError("incident_id cannot change in delta")
    bmap = {s.segment_id: s for s in b.segments}
    tmap = {s.segment_id: s for s in t.segments}
    removed = tuple(sorted(set(bmap) - set(tmap)))
    added = tuple(tmap[k] for k in sorted(set(tmap) - set(bmap)))
    changed = tuple(tmap[k] for k in sorted(set(bmap) & set(tmap)) if segment_fingerprint(bmap[k]) != segment_fingerprint(tmap[k]))
    return EvidenceDelta(
        base_fingerprint=fingerprint(b),
        target_fingerprint=fingerprint(t),
        target_incident_id=t.incident_id,
        target_version=t.version,
        target_authority_epoch=t.authority_epoch,
        target_evidence_binding=t.evidence_binding,
        changed_segments=changed,
        removed_segment_ids=removed,
        added_segments=added,
    )


def apply_evidence_delta(base: IncidentState, delta: EvidenceDelta) -> IncidentState:
    b = normalize_state(base)
    if fingerprint(b) != delta.base_fingerprint:
        raise ValueError("base fingerprint mismatch")
    if b.incident_id != delta.target_incident_id:
        raise ValueError("target incident mismatch")
    items = {s.segment_id: s for s in b.segments}
    for sid in delta.removed_segment_ids:
        if sid not in items:
            raise ValueError("remove missing segment")
        del items[sid]
    for seg in delta.changed_segments:
        if seg.segment_id not in items:
            raise ValueError("change missing segment")
        items[seg.segment_id] = seg
    for seg in delta.added_segments:
        if seg.segment_id in items:
            raise ValueError("add existing segment")
        items[seg.segment_id] = seg
    target = IncidentState(
        incident_id=delta.target_incident_id,
        version=delta.target_version,
        authority_epoch=delta.target_authority_epoch,
        evidence_binding=delta.target_evidence_binding,
        segments=_sorted_segments(items.values()),
    )
    target = normalize_state(target)
    if fingerprint(target) != delta.target_fingerprint:
        raise ValueError("target fingerprint mismatch")
    return target


def plan_evidence_transfer(prepared: PreparedIncidentState, remote_known_segment_fingerprints: FrozenSet[str]) -> TransferPlan:
    known: list[str] = []
    missing: list[str] = []
    for sid, segfp in sorted(prepared.segment_fingerprints.items()):
        if segfp in remote_known_segment_fingerprints:
            known.append(sid)
        else:
            missing.append(sid)
    return TransferPlan(
        state_fingerprint=prepared.state_fingerprint,
        missing_segment_ids=tuple(missing),
        already_known_segment_ids=tuple(known),
        transfer_required=bool(missing),
        full_resend_required=False,
    )


def assessment_digest(assessments: Iterable[IncidentAssessment]) -> str:
    return fingerprint(tuple(assessments))


def default_policy(now: int = 1_800_000_000) -> PreservationPolicy:
    return PreservationPolicy(
        policy_id="NOEPIN-AL-042-DEFAULT",
        version="1",
        authority_epoch=1,
        issued_at=now - 3600,
        expires_at=now + 86400,
        required_types=frozenset({
            EvidenceType.LOG,
            EvidenceType.INPUT,
            EvidenceType.AUTHORITY_STATE,
            EvidenceType.NETWORK_STATE,
            EvidenceType.CHANGE_DELTA,
        }),
        allowed_classifications=frozenset({"INTERNAL", "RESTRICTED"}),
        human_approval_classifications=frozenset({"RESTRICTED"}),
        max_evidence_age_seconds=86400,
        max_future_skew_seconds=300,
    )


def build_default_state(now: int = 1_800_000_000, *, classification: str = "INTERNAL") -> IncidentState:
    incident_id = "INC-042-DEMO"
    binding = "INC-042-EVIDENCE-BINDING"
    specs = (
        ("S0", EvidenceType.LOG, b"log"),
        ("S1", EvidenceType.INPUT, b"input"),
        ("S2", EvidenceType.AUTHORITY_STATE, b"authority"),
        ("S3", EvidenceType.NETWORK_STATE, b"network"),
        ("S4", EvidenceType.CHANGE_DELTA, b"delta"),
    )
    out: list[EvidenceSegment] = []
    prev = ""
    for seq, (sid, et, payload) in enumerate(specs):
        seg = build_segment(
            segment_id=sid,
            incident_id=incident_id,
            evidence_type=et,
            captured_at=now - 10 + seq,
            source_id=f"SRC-{seq}",
            source_version="1",
            classification=classification,
            payload=payload,
            sequence=seq,
            previous_segment_fingerprint=prev,
            evidence_binding=binding,
            integrity_verified=True,
        )
        out.append(seg)
        prev = segment_fingerprint(seg)
    return IncidentState(incident_id, "1", 1, binding, tuple(out))


def default_request(now: int = 1_800_000_000, *, severity: IncidentSeverity = IncidentSeverity.HIGH) -> IncidentRequest:
    p = default_policy(now)
    s = build_default_state(now)
    return IncidentRequest(
        incident_id=s.incident_id,
        actor_id="NOEPIN-AL",
        observed_at=now,
        severity=severity,
        trigger="behavior_anomaly",
        expected_policy_id=p.policy_id,
        expected_policy_version=p.version,
        expected_authority_epoch=p.authority_epoch,
        evidence_binding=s.evidence_binding,
        requested_containment_review=True,
    )
