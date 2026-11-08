"""NOEPIN AL 044 — Data Classification & Purpose Limitation Engine.

Pure control-plane evaluator. It does not transmit, persist, delete, mutate, or grant
permission. Classification produced from supplied metadata is a candidate label, not
an authoritative truth claim.

Creator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support using ChatGPT
License / Rights: NOT SPECIFIED
"""
from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Any, FrozenSet, Iterable, Mapping, Optional, Sequence, Tuple


class ControlDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    HOLD = "HOLD"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"


class Classification(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"
    PERSONAL = "PERSONAL"


CLASSIFICATION_RANK = {
    Classification.PUBLIC.value: 0,
    Classification.INTERNAL.value: 1,
    Classification.CONFIDENTIAL.value: 2,
    Classification.RESTRICTED.value: 3,
    Classification.PERSONAL.value: 4,
}
VALID_CLASSIFICATIONS = frozenset(CLASSIFICATION_RANK)


@dataclass(frozen=True)
class ClassificationMetadata:
    data_id: str
    public_approved: bool = False
    internal_only: bool = False
    confidential: bool = False
    contains_secret: bool = False
    contains_personal_data: bool = False
    explicit_label: Optional[str] = None
    evidence_binding: str = ""

    def validate(self) -> None:
        if not self.data_id:
            raise ValueError("data_id required")
        if self.explicit_label is not None and self.explicit_label not in VALID_CLASSIFICATIONS:
            raise ValueError("invalid explicit classification")


@dataclass(frozen=True)
class ClassificationResult:
    data_id: str
    classification_candidate: str
    reasons: Tuple[str, ...]
    evidence_binding: str
    classification_authoritative: bool = False
    truth_established: bool = False
    permission_granted: bool = False
    data_sent: bool = False


@dataclass(frozen=True)
class DataPolicy:
    policy_id: str
    version: str
    authority_epoch: int
    issued_at: int
    expires_at: int
    allowed_purposes_by_classification: Mapping[str, FrozenSet[str]]
    allowed_contexts_by_classification: Mapping[str, FrozenSet[str]]
    allowed_recipient_kinds_by_classification: Mapping[str, FrozenSet[str]]
    human_approval_for_external: FrozenSet[str] = field(default_factory=lambda: frozenset({"CONFIDENTIAL", "RESTRICTED", "PERSONAL"}))
    revoked: bool = False

    def validate(self, now: int) -> None:
        if not self.policy_id or not self.version:
            raise ValueError("policy id/version required")
        if self.authority_epoch < 1:
            raise ValueError("authority_epoch must be >=1")
        if self.issued_at < 0 or self.expires_at <= self.issued_at:
            raise ValueError("invalid policy lifetime")
        if not self.issued_at <= now < self.expires_at:
            raise ValueError("policy not current")
        for table in (self.allowed_purposes_by_classification, self.allowed_contexts_by_classification, self.allowed_recipient_kinds_by_classification):
            if set(table) != set(VALID_CLASSIFICATIONS):
                raise ValueError("policy classification table incomplete")
            for c, values in table.items():
                if c not in VALID_CLASSIFICATIONS or not isinstance(values, frozenset):
                    raise ValueError("invalid policy table")
                if any(not isinstance(x, str) or not x for x in values):
                    raise ValueError("invalid policy table value")
        if not self.human_approval_for_external.issubset(VALID_CLASSIFICATIONS):
            raise ValueError("invalid human approval classification")


@dataclass(frozen=True)
class DataState:
    data_id: str
    classification: str
    bound_purposes: FrozenSet[str]
    owner_scope: str
    payload_fingerprint: str
    label_source: str
    evidence_binding: str
    policy_id: str
    policy_version: str
    authority_epoch: int

    def validate(self) -> None:
        if not self.data_id or self.classification not in VALID_CLASSIFICATIONS:
            raise ValueError("invalid data state identity/classification")
        if not self.bound_purposes or any(not isinstance(x, str) or not x for x in self.bound_purposes):
            raise ValueError("bound purposes required")
        if not self.owner_scope or not self.payload_fingerprint or not self.label_source or not self.evidence_binding:
            raise ValueError("data state binding required")
        if not self.policy_id or not self.policy_version or self.authority_epoch < 1:
            raise ValueError("data state policy binding required")


@dataclass(frozen=True)
class DataUseRequest:
    request_id: str
    purpose: str
    context_id: str
    recipient_kind: str
    data_ids: Tuple[str, ...]
    evidence_binding: str
    expected_policy_id: str
    expected_policy_version: str
    expected_authority_epoch: int
    external_send_requested: bool = False
    human_approval_evidence: bool = False

    def validate(self) -> None:
        if not self.request_id or not self.purpose or not self.context_id or not self.recipient_kind:
            raise ValueError("request identity/purpose/context/recipient required")
        if not self.data_ids or len(set(self.data_ids)) != len(self.data_ids):
            raise ValueError("non-empty unique data_ids required")
        if any(not x for x in self.data_ids) or not self.evidence_binding:
            raise ValueError("invalid request data/binding")
        if not self.expected_policy_id or not self.expected_policy_version or self.expected_authority_epoch < 1:
            raise ValueError("expected policy binding required")


@dataclass(frozen=True)
class PreparedDataRegistry:
    registry_fingerprint: str
    policy_fingerprint: str
    states: Tuple[DataState, ...]
    item_fingerprints: Mapping[str, str]


@dataclass(frozen=True)
class MetadataTransferPlan:
    missing_or_changed_ids: Tuple[str, ...]
    metadata_bytes_required: int
    full_metadata_bytes: int
    full_resend_required: bool
    payload_transfer_authorized: bool = False
    permission_granted: bool = False
    data_sent: bool = False


@dataclass(frozen=True)
class DataRegistryDelta:
    base_fingerprint: str
    target_fingerprint: str
    changed: Tuple[DataState, ...]
    removed_ids: Tuple[str, ...]
    added: Tuple[DataState, ...]


@dataclass(frozen=True)
class UseAssessment:
    decision: ControlDecision
    reasons: Tuple[str, ...]
    request_id: str
    allowed_data_ids_candidate: Tuple[str, ...]
    denied_data_ids: Tuple[str, ...]
    human_review_data_ids: Tuple[str, ...]
    registry_fingerprint: str
    policy_fingerprint: str
    request_fingerprint: str
    classification_summary: Tuple[Tuple[str, str], ...]
    permission_granted: bool = False
    data_sent: bool = False
    external_transfer_executed: bool = False
    truth_established: bool = False
    classification_authoritative: bool = False
    action_success: bool = False


def _canonical(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {f.name: _canonical(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (set, frozenset)):
        vals = [_canonical(v) for v in value]
        return sorted(vals, key=lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    if isinstance(value, (tuple, list)):
        return [_canonical(v) for v in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(_canonical(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def classify_candidate(metadata: ClassificationMetadata) -> ClassificationResult:
    """Derive a classification *candidate* from caller-supplied metadata only."""
    metadata.validate()
    reasons: list[str] = []
    if metadata.explicit_label is not None:
        candidate = metadata.explicit_label
        reasons.append("EXPLICIT_LABEL_SUPPLIED")
    elif metadata.contains_personal_data:
        candidate = Classification.PERSONAL.value
        reasons.append("PERSONAL_DATA_SIGNAL")
    elif metadata.contains_secret:
        candidate = Classification.RESTRICTED.value
        reasons.append("SECRET_SIGNAL")
    elif metadata.confidential:
        candidate = Classification.CONFIDENTIAL.value
        reasons.append("CONFIDENTIAL_SIGNAL")
    elif metadata.internal_only:
        candidate = Classification.INTERNAL.value
        reasons.append("INTERNAL_ONLY_SIGNAL")
    elif metadata.public_approved:
        candidate = Classification.PUBLIC.value
        reasons.append("PUBLIC_APPROVAL_SIGNAL")
    else:
        candidate = Classification.INTERNAL.value
        reasons.append("DEFAULT_INTERNAL_FAIL_SAFE")
    return ClassificationResult(metadata.data_id, candidate, tuple(reasons), metadata.evidence_binding)


def _normalize_states(states: Iterable[DataState]) -> Tuple[DataState, ...]:
    ordered = tuple(sorted(states, key=lambda x: x.data_id))
    ids = [x.data_id for x in ordered]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate data_id")
    for state in ordered:
        state.validate()
    return ordered


def registry_fingerprint(states: Iterable[DataState]) -> str:
    return fingerprint(_normalize_states(states))


def prepare_registry(policy: DataPolicy, states: Iterable[DataState], *, now: int) -> PreparedDataRegistry:
    policy.validate(now)
    if policy.revoked:
        raise ValueError("policy revoked")
    normalized = _normalize_states(states)
    item_fps = {s.data_id: fingerprint(s) for s in normalized}
    return PreparedDataRegistry(fingerprint(normalized), fingerprint(policy), normalized, item_fps)


def _hold(request: DataUseRequest, policy_fp: str, registry_fp: str, reasons: Iterable[str]) -> UseAssessment:
    return UseAssessment(
        ControlDecision.HOLD, tuple(sorted(set(reasons))), request.request_id, (), tuple(sorted(request.data_ids)), (),
        registry_fp, policy_fp, fingerprint(request), ()
    )


def evaluate_prepared(request: DataUseRequest, policy: DataPolicy, prepared: PreparedDataRegistry, *, now: int) -> UseAssessment:
    """Evaluate data-use eligibility without sending, persisting, or granting anything."""
    policy_fp = fingerprint(policy)
    try:
        request.validate()
        policy.validate(now)
    except (ValueError, TypeError) as exc:
        return _hold(request, policy_fp, prepared.registry_fingerprint, (f"INVALID_REQUEST_OR_POLICY:{exc}",))

    if policy.revoked:
        return _hold(request, policy_fp, prepared.registry_fingerprint, ("POLICY_REVOKED",))
    if policy_fp != prepared.policy_fingerprint:
        return _hold(request, policy_fp, prepared.registry_fingerprint, ("PREPARED_POLICY_FINGERPRINT_MISMATCH",))
    if request.expected_policy_id != policy.policy_id:
        return _hold(request, policy_fp, prepared.registry_fingerprint, ("POLICY_ID_MISMATCH",))
    if request.expected_policy_version != policy.version:
        return _hold(request, policy_fp, prepared.registry_fingerprint, ("POLICY_VERSION_MISMATCH",))
    if request.expected_authority_epoch != policy.authority_epoch:
        return _hold(request, policy_fp, prepared.registry_fingerprint, ("AUTHORITY_EPOCH_MISMATCH",))

    by_id = {s.data_id: s for s in prepared.states}
    missing = tuple(sorted(d for d in request.data_ids if d not in by_id))
    if missing:
        return _hold(request, policy_fp, prepared.registry_fingerprint, ("DATA_STATE_MISSING",) + missing)

    allowed: list[str] = []
    denied: list[str] = []
    review: list[str] = []
    reasons: list[str] = []
    summary: list[Tuple[str, str]] = []

    for data_id in sorted(request.data_ids):
        s = by_id[data_id]
        summary.append((s.data_id, s.classification))
        local_reasons: list[str] = []
        if s.policy_id != policy.policy_id:
            local_reasons.append("STATE_POLICY_ID_MISMATCH")
        if s.policy_version != policy.version:
            local_reasons.append("STATE_POLICY_VERSION_MISMATCH")
        if s.authority_epoch != policy.authority_epoch:
            local_reasons.append("STATE_AUTHORITY_EPOCH_MISMATCH")
        if s.evidence_binding != request.evidence_binding:
            local_reasons.append("EVIDENCE_BINDING_MISMATCH")
        if request.purpose not in s.bound_purposes:
            local_reasons.append("STATE_PURPOSE_NOT_BOUND")
        if request.purpose not in policy.allowed_purposes_by_classification[s.classification]:
            local_reasons.append("POLICY_PURPOSE_NOT_ALLOWED")
        if request.context_id not in policy.allowed_contexts_by_classification[s.classification]:
            local_reasons.append("CONTEXT_NOT_ALLOWED_FOR_CLASSIFICATION")
        if request.recipient_kind not in policy.allowed_recipient_kinds_by_classification[s.classification]:
            local_reasons.append("RECIPIENT_NOT_ALLOWED_FOR_CLASSIFICATION")

        if local_reasons:
            denied.append(data_id)
            reasons.extend(f"{data_id}:{r}" for r in local_reasons)
            continue

        if request.external_send_requested and s.classification in policy.human_approval_for_external:
            if request.human_approval_evidence:
                # Evidence allows this control to produce a candidate, but never grants permission or sends data.
                allowed.append(data_id)
                reasons.append(f"{data_id}:EXTERNAL_HUMAN_EVIDENCE_PRESENT_CANDIDATE_ONLY")
            else:
                review.append(data_id)
                reasons.append(f"{data_id}:HUMAN_APPROVAL_REQUIRED_FOR_EXTERNAL")
            continue

        allowed.append(data_id)
        reasons.append(f"{data_id}:PURPOSE_CONTEXT_CLASSIFICATION_MATCH")

    if denied:
        decision = ControlDecision.DENY
    elif review:
        decision = ControlDecision.HUMAN_APPROVAL
    else:
        decision = ControlDecision.ALLOW

    return UseAssessment(
        decision=decision,
        reasons=tuple(sorted(reasons)),
        request_id=request.request_id,
        allowed_data_ids_candidate=tuple(sorted(allowed)),
        denied_data_ids=tuple(sorted(denied)),
        human_review_data_ids=tuple(sorted(review)),
        registry_fingerprint=prepared.registry_fingerprint,
        policy_fingerprint=policy_fp,
        request_fingerprint=fingerprint(request),
        classification_summary=tuple(summary),
    )


def evaluate(request: DataUseRequest, policy: DataPolicy, states: Iterable[DataState], *, now: int) -> UseAssessment:
    try:
        prepared = prepare_registry(policy, states, now=now)
    except (ValueError, TypeError) as exc:
        # Fail closed without accepting caller data as authority.
        empty_fp = fingerprint(())
        return _hold(request, fingerprint(policy), empty_fp, (f"REGISTRY_OR_POLICY_INVALID:{exc}",))
    return evaluate_prepared(request, policy, prepared, now=now)


def compute_registry_delta(base: Sequence[DataState], target: Sequence[DataState]) -> DataRegistryDelta:
    b = _normalize_states(base)
    t = _normalize_states(target)
    bm = {x.data_id: x for x in b}
    tm = {x.data_id: x for x in t}
    changed = tuple(tm[k] for k in sorted(set(bm) & set(tm)) if fingerprint(bm[k]) != fingerprint(tm[k]))
    removed = tuple(sorted(set(bm) - set(tm)))
    added = tuple(tm[k] for k in sorted(set(tm) - set(bm)))
    return DataRegistryDelta(fingerprint(b), fingerprint(t), changed, removed, added)


def apply_registry_delta(base: Sequence[DataState], delta: DataRegistryDelta) -> Tuple[DataState, ...]:
    b = _normalize_states(base)
    if fingerprint(b) != delta.base_fingerprint:
        raise ValueError("base fingerprint mismatch")
    m = {x.data_id: x for x in b}
    for rid in delta.removed_ids:
        if rid not in m:
            raise ValueError("remove target missing")
        del m[rid]
    for x in delta.changed:
        if x.data_id not in m:
            raise ValueError("changed target missing")
        x.validate(); m[x.data_id] = x
    for x in delta.added:
        if x.data_id in m:
            raise ValueError("added target already exists")
        x.validate(); m[x.data_id] = x
    result = tuple(sorted(m.values(), key=lambda x: x.data_id))
    if fingerprint(result) != delta.target_fingerprint:
        raise ValueError("target fingerprint mismatch")
    return result


def plan_metadata_sync(prepared: PreparedDataRegistry, remote_known_item_fingerprints: Mapping[str, str]) -> MetadataTransferPlan:
    missing = tuple(sorted(
        data_id for data_id, fp in prepared.item_fingerprints.items()
        if remote_known_item_fingerprints.get(data_id) != fp
    ))
    by_id = {s.data_id: s for s in prepared.states}
    metadata_bytes = len(canonical_json(tuple(by_id[x] for x in missing)).encode("utf-8"))
    full_bytes = len(canonical_json(prepared.states).encode("utf-8"))
    # Metadata full resend is only a transport fallback hint, never an authority decision.
    full_resend = bool(full_bytes and metadata_bytes / full_bytes > 0.80)
    return MetadataTransferPlan(missing, metadata_bytes, full_bytes, full_resend)


def assessment_digest(values: Iterable[UseAssessment]) -> str:
    return fingerprint(tuple(values))


def default_policy(now: int = 1_800_000_000) -> DataPolicy:
    purposes = {
        "PUBLIC": frozenset({"publish", "analysis", "support", "verification"}),
        "INTERNAL": frozenset({"analysis", "support", "verification", "build"}),
        "CONFIDENTIAL": frozenset({"analysis", "verification", "build"}),
        "RESTRICTED": frozenset({"verification", "security_review"}),
        "PERSONAL": frozenset({"support", "subject_service", "verification"}),
    }
    contexts = {
        "PUBLIC": frozenset({"public", "internal", "secure", "subject"}),
        "INTERNAL": frozenset({"internal", "secure", "subject"}),
        "CONFIDENTIAL": frozenset({"secure", "subject"}),
        "RESTRICTED": frozenset({"secure"}),
        "PERSONAL": frozenset({"subject", "secure"}),
    }
    recipients = {
        "PUBLIC": frozenset({"local_ai", "trusted_ai", "external_ai", "human"}),
        "INTERNAL": frozenset({"local_ai", "trusted_ai", "human"}),
        "CONFIDENTIAL": frozenset({"local_ai", "trusted_ai", "human"}),
        "RESTRICTED": frozenset({"local_ai", "human"}),
        "PERSONAL": frozenset({"local_ai", "trusted_ai", "human"}),
    }
    return DataPolicy(
        policy_id="NOEPIN-AL-044-DEFAULT",
        version="1",
        authority_epoch=1,
        issued_at=now-3600,
        expires_at=now+86400,
        allowed_purposes_by_classification=purposes,
        allowed_contexts_by_classification=contexts,
        allowed_recipient_kinds_by_classification=recipients,
    )


def make_state(data_id: str, classification: str, purposes: Iterable[str], *, evidence_binding: str = "BIND-044", payload_seed: str = "payload") -> DataState:
    return DataState(
        data_id=data_id,
        classification=classification,
        bound_purposes=frozenset(purposes),
        owner_scope="NOEPIN-AL",
        payload_fingerprint=sha256((payload_seed+":"+data_id).encode("utf-8")).hexdigest(),
        label_source="CALLER_BOUND_METADATA",
        evidence_binding=evidence_binding,
        policy_id="NOEPIN-AL-044-DEFAULT",
        policy_version="1",
        authority_epoch=1,
    )


def default_states() -> Tuple[DataState, ...]:
    return (
        make_state("D-PUB", "PUBLIC", {"publish", "analysis", "verification"}),
        make_state("D-INT", "INTERNAL", {"analysis", "support", "verification", "build"}),
        make_state("D-CONF", "CONFIDENTIAL", {"analysis", "verification", "build"}),
        make_state("D-RES", "RESTRICTED", {"verification", "security_review"}),
        make_state("D-PER", "PERSONAL", {"support", "subject_service", "verification"}),
    )


def default_request(now: int = 1_800_000_000, *, data_ids: Sequence[str] = ("D-INT",), purpose: str = "verification", context_id: str = "internal", recipient_kind: str = "local_ai") -> DataUseRequest:
    p = default_policy(now)
    return DataUseRequest(
        request_id="REQ-044",
        purpose=purpose,
        context_id=context_id,
        recipient_kind=recipient_kind,
        data_ids=tuple(data_ids),
        evidence_binding="BIND-044",
        expected_policy_id=p.policy_id,
        expected_policy_version=p.version,
        expected_authority_epoch=p.authority_epoch,
    )
