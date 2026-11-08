"""NOEPIN AL 052 — Content Authenticity / Provenance Verification.

Pure control-plane evaluator implementing Provenance Metadata, externally
verified Signature Evidence binding, and Trust Labels. It evaluates evidence
about content origin and transformation history. It never promotes provenance,
signature verification evidence, origin identity, trust labels, or fingerprint
matches to authoritative content truth, permission, execution, or success.

Creator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support using ChatGPT
License / Rights: NOT SPECIFIED
"""
from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
from hashlib import sha256
import json
from typing import Any, FrozenSet, Iterable, Mapping, Tuple

GENESIS_SHA256 = "0" * 64


class ControlDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    HOLD = "HOLD"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"


class TrustLabel(str, Enum):
    VERIFIED = "VERIFIED"
    REVIEW = "REVIEW"
    UNKNOWN = "UNKNOWN"
    TAMPERED = "TAMPERED"


@dataclass(frozen=True)
class ProvenancePolicy:
    policy_id: str
    version: str
    authority_epoch: int
    issued_at: int
    expires_at: int
    allowed_purposes: FrozenSet[str]
    trusted_origin_ids: FrozenSet[str]
    trusted_issuer_ids: FrozenSet[str]
    trusted_verifier_ids: FrozenSet[str]
    accepted_signature_schemes: FrozenSet[str]
    min_origin_trust: float
    human_review_origin_trust: float
    min_signer_trust: float
    max_evidence_age_seconds: int
    max_steps: int
    max_signatures: int
    require_verified_signature: bool = True
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
        sets = (
            self.allowed_purposes,
            self.trusted_origin_ids,
            self.trusted_issuer_ids,
            self.trusted_verifier_ids,
            self.accepted_signature_schemes,
        )
        if any(not s for s in sets):
            raise ValueError("policy sets must not be empty")
        if not 0 <= self.human_review_origin_trust < self.min_origin_trust <= 1:
            raise ValueError("invalid origin trust thresholds")
        if not 0 <= self.min_signer_trust <= 1:
            raise ValueError("invalid signer trust threshold")
        if self.max_evidence_age_seconds < 1 or self.max_steps < 1 or self.max_signatures < 1:
            raise ValueError("invalid limits")


@dataclass(frozen=True)
class AuthenticityRequest:
    request_id: str
    content_id: str
    content_sha256: str
    purpose: str
    expected_origin_id: str
    expected_policy_id: str
    expected_policy_version: str
    expected_authority_epoch: int
    evidence_binding: str

    def validate(self) -> None:
        if not self.request_id or not self.content_id or not self.purpose:
            raise ValueError("request/content/purpose required")
        _validate_sha(self.content_sha256)
        if not self.expected_origin_id or not self.evidence_binding:
            raise ValueError("origin/evidence binding required")
        if not self.expected_policy_id or not self.expected_policy_version or self.expected_authority_epoch < 1:
            raise ValueError("policy binding required")


@dataclass(frozen=True)
class ProvenanceStep:
    step_id: str
    content_id: str
    sequence: int
    origin_id: str
    actor_id: str
    issuer_id: str
    occurred_at: int
    input_sha256: str
    output_sha256: str
    operation: str
    origin_trust: float
    evidence_binding: str
    issuer_verified: bool
    revoked: bool = False

    def validate(self) -> None:
        if not self.step_id or not self.content_id or self.sequence < 0:
            raise ValueError("step identity/sequence invalid")
        if not self.origin_id or not self.actor_id or not self.issuer_id or not self.operation:
            raise ValueError("step metadata required")
        if self.occurred_at < 0:
            raise ValueError("occurred_at invalid")
        _validate_sha(self.input_sha256)
        _validate_sha(self.output_sha256)
        if not 0 <= self.origin_trust <= 1:
            raise ValueError("origin trust out of range")
        if not self.evidence_binding:
            raise ValueError("evidence binding required")


@dataclass(frozen=True)
class SignatureEvidence:
    signature_id: str
    content_id: str
    content_sha256: str
    origin_id: str
    signer_id: str
    key_id: str
    scheme: str
    verifier_id: str
    verified_at: int
    evidence_binding: str
    payload_fingerprint: str
    signature_verified: bool
    signer_trust: float
    revoked: bool = False

    def validate(self) -> None:
        if not self.signature_id or not self.content_id or not self.origin_id:
            raise ValueError("signature identity required")
        _validate_sha(self.content_sha256)
        if not self.signer_id or not self.key_id or not self.scheme or not self.verifier_id:
            raise ValueError("signature metadata required")
        if self.verified_at < 0 or not self.evidence_binding:
            raise ValueError("verification metadata invalid")
        _validate_sha(self.payload_fingerprint)
        if not 0 <= self.signer_trust <= 1:
            raise ValueError("signer trust out of range")


@dataclass(frozen=True)
class PreparedAuthenticityRegistry:
    registry_fingerprint: str
    policy_fingerprint: str
    steps: Tuple[ProvenanceStep, ...]
    signatures: Tuple[SignatureEvidence, ...]
    step_fingerprints: Mapping[str, str]
    signature_fingerprints: Mapping[str, str]
    content_step_index: Mapping[str, Tuple[str, ...]]
    content_signature_index: Mapping[str, Tuple[str, ...]]
    origin_index: Mapping[str, Tuple[str, ...]]


@dataclass(frozen=True)
class AuthenticityDelta:
    base_fingerprint: str
    target_fingerprint: str
    changed_steps: Tuple[ProvenanceStep, ...]
    removed_step_ids: Tuple[str, ...]
    added_steps: Tuple[ProvenanceStep, ...]
    changed_signatures: Tuple[SignatureEvidence, ...]
    removed_signature_ids: Tuple[str, ...]
    added_signatures: Tuple[SignatureEvidence, ...]


@dataclass(frozen=True)
class RegistrySyncPlan:
    missing_or_changed_step_ids: Tuple[str, ...]
    missing_or_changed_signature_ids: Tuple[str, ...]
    metadata_bytes_required: int
    full_metadata_bytes: int
    full_resend_required: bool
    permission_granted: bool = False
    content_use_authorized: bool = False
    content_execution_authorized: bool = False
    data_transfer_authorized: bool = False


@dataclass(frozen=True)
class AuthenticityVerdict:
    decision: ControlDecision
    trust_label: TrustLabel
    reasons: Tuple[str, ...]
    request_id: str
    origin_id: str
    chain_step_ids: Tuple[str, ...]
    signature_ids: Tuple[str, ...]
    invalid_or_stale_step_ids: Tuple[str, ...]
    invalid_or_stale_signature_ids: Tuple[str, ...]
    chain_valid: bool
    signature_verification_evidence_valid: bool
    human_review_candidate: bool
    registry_fingerprint: str
    policy_fingerprint: str
    request_fingerprint: str
    permission_granted: bool = False
    content_accepted: bool = False
    content_executed: bool = False
    data_transferred: bool = False
    content_truth_proven: bool = False
    authenticity_truth_proven: bool = False
    action_success: bool = False


def _validate_sha(value: str) -> None:
    if len(value) != 64 or any(c not in "0123456789abcdef" for c in value.lower()):
        raise ValueError("sha256 invalid")


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
    if isinstance(value, tuple):
        return [_canonical(v) for v in value]
    if isinstance(value, list):
        return [_canonical(v) for v in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(_canonical(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def signature_payload_fingerprint(content_id: str, content_sha256: str, origin_id: str, signer_id: str, key_id: str, scheme: str) -> str:
    return fingerprint((content_id, content_sha256, origin_id, signer_id, key_id, scheme))


def _normalize_steps(steps: Iterable[ProvenanceStep]) -> Tuple[ProvenanceStep, ...]:
    items = tuple(steps)
    ids = [x.step_id for x in items]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate step id")
    return tuple(sorted(items, key=lambda x: x.step_id))


def _normalize_signatures(signatures: Iterable[SignatureEvidence]) -> Tuple[SignatureEvidence, ...]:
    items = tuple(signatures)
    ids = [x.signature_id for x in items]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate signature id")
    return tuple(sorted(items, key=lambda x: x.signature_id))


def _fingerprint_pairs(steps: Tuple[ProvenanceStep, ...], signatures: Tuple[SignatureEvidence, ...]) -> Tuple[Mapping[str, str], Mapping[str, str], str]:
    sf = {x.step_id: fingerprint(x) for x in steps}
    gf = {x.signature_id: fingerprint(x) for x in signatures}
    reg = fingerprint((tuple(sorted(sf.items())), tuple(sorted(gf.items()))))
    return sf, gf, reg


def registry_fingerprint(steps: Iterable[ProvenanceStep], signatures: Iterable[SignatureEvidence]) -> str:
    ss = _normalize_steps(steps)
    gs = _normalize_signatures(signatures)
    return _fingerprint_pairs(ss, gs)[2]


def prepare_registry(policy: ProvenancePolicy, steps: Iterable[ProvenanceStep], signatures: Iterable[SignatureEvidence], *, now: int) -> PreparedAuthenticityRegistry:
    policy.validate(now)
    ss = _normalize_steps(steps)
    gs = _normalize_signatures(signatures)
    if len(ss) > policy.max_steps or len(gs) > policy.max_signatures:
        raise ValueError("registry limit exceeded")
    sf, gf, reg = _fingerprint_pairs(ss, gs)
    by_content_steps: dict[str, list[str]] = {}
    by_content_sigs: dict[str, list[str]] = {}
    by_origin: dict[str, list[str]] = {}
    for x in ss:
        by_content_steps.setdefault(x.content_id, []).append(x.step_id)
        by_origin.setdefault(x.origin_id, []).append(x.step_id)
    for x in gs:
        by_content_sigs.setdefault(x.content_id, []).append(x.signature_id)
        by_origin.setdefault(x.origin_id, []).append(x.signature_id)
    return PreparedAuthenticityRegistry(
        registry_fingerprint=reg,
        policy_fingerprint=fingerprint(policy),
        steps=ss,
        signatures=gs,
        step_fingerprints=sf,
        signature_fingerprints=gf,
        content_step_index={k: tuple(sorted(v)) for k, v in sorted(by_content_steps.items())},
        content_signature_index={k: tuple(sorted(v)) for k, v in sorted(by_content_sigs.items())},
        origin_index={k: tuple(sorted(v)) for k, v in sorted(by_origin.items())},
    )


def _prepared_fingerprint(prepared: PreparedAuthenticityRegistry) -> str:
    return fingerprint((tuple(sorted(prepared.step_fingerprints.items())), tuple(sorted(prepared.signature_fingerprints.items()))))


def _hold(request: AuthenticityRequest, policy: ProvenancePolicy, prepared: PreparedAuthenticityRegistry | None, reason: str) -> AuthenticityVerdict:
    return AuthenticityVerdict(
        ControlDecision.HOLD, TrustLabel.UNKNOWN, (reason,), request.request_id, "", (), (), (), (), False, False, False,
        prepared.registry_fingerprint if prepared else "", fingerprint(policy), fingerprint(request)
    )


def _active_step(step: ProvenanceStep, request: AuthenticityRequest, policy: ProvenancePolicy, now: int) -> bool:
    try:
        step.validate()
    except ValueError:
        return False
    if step.revoked or not step.issuer_verified:
        return False
    if step.evidence_binding != request.evidence_binding:
        return False
    if step.issuer_id not in policy.trusted_issuer_ids:
        return False
    if step.origin_id not in policy.trusted_origin_ids:
        return False
    if step.occurred_at > now or now - step.occurred_at > policy.max_evidence_age_seconds:
        return False
    return True


def _active_signature(sig: SignatureEvidence, request: AuthenticityRequest, policy: ProvenancePolicy, now: int) -> bool:
    try:
        sig.validate()
    except ValueError:
        return False
    if sig.revoked:
        return False
    if sig.evidence_binding != request.evidence_binding:
        return False
    if sig.verifier_id not in policy.trusted_verifier_ids or sig.scheme not in policy.accepted_signature_schemes:
        return False
    if sig.verified_at > now or now - sig.verified_at > policy.max_evidence_age_seconds:
        return False
    expected = signature_payload_fingerprint(sig.content_id, sig.content_sha256, sig.origin_id, sig.signer_id, sig.key_id, sig.scheme)
    if sig.payload_fingerprint != expected:
        return False
    return True


def _validate_chain(request: AuthenticityRequest, steps: Tuple[ProvenanceStep, ...]) -> Tuple[bool, str, Tuple[str, ...], float]:
    if not steps:
        return False, "PROVENANCE_MISSING", (), 0.0
    ordered = tuple(sorted(steps, key=lambda x: (x.sequence, x.step_id)))
    seq = [x.sequence for x in ordered]
    if seq != list(range(len(ordered))):
        return False, "PROVENANCE_SEQUENCE_GAP", tuple(x.step_id for x in ordered), 0.0
    origins = {x.origin_id for x in ordered}
    if len(origins) != 1:
        return False, "PROVENANCE_ORIGIN_CONFLICT", tuple(x.step_id for x in ordered), 0.0
    if ordered[0].input_sha256 != GENESIS_SHA256:
        return False, "PROVENANCE_GENESIS_MISMATCH", tuple(x.step_id for x in ordered), 0.0
    for prev, cur in zip(ordered, ordered[1:]):
        if cur.input_sha256 != prev.output_sha256:
            return False, "PROVENANCE_CHAIN_BREAK", tuple(x.step_id for x in ordered), 0.0
    if ordered[-1].output_sha256 != request.content_sha256:
        return False, "CONTENT_HASH_NOT_IN_PROVENANCE_TIP", tuple(x.step_id for x in ordered), 0.0
    return True, "PROVENANCE_CHAIN_VALID", tuple(x.step_id for x in ordered), min(x.origin_trust for x in ordered)


def evaluate_prepared(request: AuthenticityRequest, policy: ProvenancePolicy, prepared: PreparedAuthenticityRegistry, *, now: int) -> AuthenticityVerdict:
    try:
        request.validate()
    except ValueError:
        return _hold(request, policy, prepared, "REQUEST_INVALID")
    try:
        policy.validate(now)
    except ValueError:
        return _hold(request, policy, prepared, "POLICY_INVALID_OR_NOT_CURRENT")
    if policy.revoked:
        return _hold(request, policy, prepared, "POLICY_REVOKED")
    if request.expected_policy_id != policy.policy_id:
        return _hold(request, policy, prepared, "POLICY_ID_MISMATCH")
    if request.expected_policy_version != policy.version:
        return _hold(request, policy, prepared, "POLICY_VERSION_MISMATCH")
    if request.expected_authority_epoch != policy.authority_epoch:
        return _hold(request, policy, prepared, "AUTHORITY_EPOCH_MISMATCH")
    if request.purpose not in policy.allowed_purposes:
        return AuthenticityVerdict(ControlDecision.DENY, TrustLabel.UNKNOWN, ("PURPOSE_NOT_ALLOWED",), request.request_id, "", (), (), (), (), False, False, False, prepared.registry_fingerprint, fingerprint(policy), fingerprint(request))
    if prepared.policy_fingerprint != fingerprint(policy):
        return _hold(request, policy, prepared, "PREPARED_POLICY_FINGERPRINT_MISMATCH")
    if prepared.registry_fingerprint != _prepared_fingerprint(prepared):
        return _hold(request, policy, prepared, "PREPARED_REGISTRY_FINGERPRINT_MISMATCH")

    step_by_id = {x.step_id: x for x in prepared.steps}
    sig_by_id = {x.signature_id: x for x in prepared.signatures}
    step_ids = prepared.content_step_index.get(request.content_id, ())
    sig_ids = prepared.content_signature_index.get(request.content_id, ())
    raw_steps = tuple(step_by_id[x] for x in step_ids)
    raw_sigs = tuple(sig_by_id[x] for x in sig_ids)
    active_steps = tuple(x for x in raw_steps if _active_step(x, request, policy, now))
    invalid_steps = tuple(sorted(x.step_id for x in raw_steps if x not in active_steps))
    active_sigs = tuple(x for x in raw_sigs if _active_signature(x, request, policy, now))
    invalid_sigs = tuple(sorted(x.signature_id for x in raw_sigs if x not in active_sigs))

    chain_valid, chain_reason, chain_ids, origin_trust = _validate_chain(request, active_steps)
    if not active_steps:
        return AuthenticityVerdict(ControlDecision.HOLD, TrustLabel.UNKNOWN, ("PROVENANCE_MISSING_OR_INVALID",), request.request_id, "", (), (), invalid_steps, invalid_sigs, False, False, False, prepared.registry_fingerprint, fingerprint(policy), fingerprint(request))
    origin_id = sorted({x.origin_id for x in active_steps})[0] if active_steps else ""
    if not chain_valid:
        return AuthenticityVerdict(ControlDecision.DENY, TrustLabel.TAMPERED, (chain_reason,), request.request_id, origin_id, chain_ids, (), invalid_steps, invalid_sigs, False, False, False, prepared.registry_fingerprint, fingerprint(policy), fingerprint(request))
    if origin_id != request.expected_origin_id:
        return AuthenticityVerdict(ControlDecision.DENY, TrustLabel.TAMPERED, ("ORIGIN_MISMATCH",), request.request_id, origin_id, chain_ids, (), invalid_steps, invalid_sigs, True, False, False, prepared.registry_fingerprint, fingerprint(policy), fingerprint(request))

    matching_sigs = tuple(x for x in active_sigs if x.content_sha256 == request.content_sha256 and x.origin_id == origin_id)
    explicit_failed = tuple(x for x in matching_sigs if not x.signature_verified)
    verified_sigs = tuple(x for x in matching_sigs if x.signature_verified and x.signer_trust >= policy.min_signer_trust)
    sig_ids_out = tuple(sorted(x.signature_id for x in matching_sigs))
    if explicit_failed:
        return AuthenticityVerdict(ControlDecision.DENY, TrustLabel.TAMPERED, ("SIGNATURE_VERIFICATION_FAILED",), request.request_id, origin_id, chain_ids, sig_ids_out, invalid_steps, invalid_sigs, True, False, False, prepared.registry_fingerprint, fingerprint(policy), fingerprint(request))
    if policy.require_verified_signature and not verified_sigs:
        reason = "VERIFIED_SIGNATURE_MISSING" if not matching_sigs else "SIGNER_TRUST_BELOW_THRESHOLD"
        return AuthenticityVerdict(ControlDecision.HOLD, TrustLabel.UNKNOWN, (reason,), request.request_id, origin_id, chain_ids, sig_ids_out, invalid_steps, invalid_sigs, True, False, False, prepared.registry_fingerprint, fingerprint(policy), fingerprint(request))
    if origin_trust < policy.human_review_origin_trust:
        return AuthenticityVerdict(ControlDecision.DENY, TrustLabel.UNKNOWN, ("ORIGIN_TRUST_TOO_LOW",), request.request_id, origin_id, chain_ids, sig_ids_out, invalid_steps, invalid_sigs, True, bool(verified_sigs), False, prepared.registry_fingerprint, fingerprint(policy), fingerprint(request))
    if origin_trust < policy.min_origin_trust:
        return AuthenticityVerdict(ControlDecision.HUMAN_APPROVAL, TrustLabel.REVIEW, ("ORIGIN_TRUST_REQUIRES_REVIEW",), request.request_id, origin_id, chain_ids, sig_ids_out, invalid_steps, invalid_sigs, True, bool(verified_sigs), True, prepared.registry_fingerprint, fingerprint(policy), fingerprint(request))
    return AuthenticityVerdict(ControlDecision.ALLOW, TrustLabel.VERIFIED, ("PROVENANCE_AND_SIGNATURE_EVIDENCE_MATCH",), request.request_id, origin_id, chain_ids, tuple(sorted(x.signature_id for x in verified_sigs)), invalid_steps, invalid_sigs, True, bool(verified_sigs), False, prepared.registry_fingerprint, fingerprint(policy), fingerprint(request))


def evaluate(request: AuthenticityRequest, policy: ProvenancePolicy, steps: Iterable[ProvenanceStep], signatures: Iterable[SignatureEvidence], *, now: int) -> AuthenticityVerdict:
    try:
        prepared = prepare_registry(policy, steps, signatures, now=now)
    except ValueError:
        return _hold(request, policy, None, "REGISTRY_OR_POLICY_INVALID")
    return evaluate_prepared(request, policy, prepared, now=now)


def make_registry_delta(base_steps: Iterable[ProvenanceStep], base_signatures: Iterable[SignatureEvidence], target_steps: Iterable[ProvenanceStep], target_signatures: Iterable[SignatureEvidence]) -> AuthenticityDelta:
    bs = _normalize_steps(base_steps); bg = _normalize_signatures(base_signatures)
    ts = _normalize_steps(target_steps); tg = _normalize_signatures(target_signatures)
    bm = {x.step_id: x for x in bs}; tm = {x.step_id: x for x in ts}
    bsm = {x.signature_id: x for x in bg}; tsm = {x.signature_id: x for x in tg}
    changed_steps = tuple(tm[k] for k in sorted(set(bm) & set(tm)) if fingerprint(bm[k]) != fingerprint(tm[k]))
    removed_steps = tuple(sorted(set(bm) - set(tm)))
    added_steps = tuple(tm[k] for k in sorted(set(tm) - set(bm)))
    changed_sigs = tuple(tsm[k] for k in sorted(set(bsm) & set(tsm)) if fingerprint(bsm[k]) != fingerprint(tsm[k]))
    removed_sigs = tuple(sorted(set(bsm) - set(tsm)))
    added_sigs = tuple(tsm[k] for k in sorted(set(tsm) - set(bsm)))
    return AuthenticityDelta(
        registry_fingerprint(bs, bg), registry_fingerprint(ts, tg), changed_steps, removed_steps, added_steps,
        changed_sigs, removed_sigs, added_sigs
    )


def apply_registry_delta(base_steps: Iterable[ProvenanceStep], base_signatures: Iterable[SignatureEvidence], delta: AuthenticityDelta) -> Tuple[Tuple[ProvenanceStep, ...], Tuple[SignatureEvidence, ...]]:
    bs = _normalize_steps(base_steps); bg = _normalize_signatures(base_signatures)
    if registry_fingerprint(bs, bg) != delta.base_fingerprint:
        raise ValueError("delta base fingerprint mismatch")
    sm = {x.step_id: x for x in bs}; gm = {x.signature_id: x for x in bg}
    for k in delta.removed_step_ids:
        if k not in sm: raise ValueError("missing step remove")
        del sm[k]
    for x in delta.changed_steps:
        if x.step_id not in sm: raise ValueError("missing step change")
        sm[x.step_id] = x
    for x in delta.added_steps:
        if x.step_id in sm: raise ValueError("duplicate step add")
        sm[x.step_id] = x
    for k in delta.removed_signature_ids:
        if k not in gm: raise ValueError("missing signature remove")
        del gm[k]
    for x in delta.changed_signatures:
        if x.signature_id not in gm: raise ValueError("missing signature change")
        gm[x.signature_id] = x
    for x in delta.added_signatures:
        if x.signature_id in gm: raise ValueError("duplicate signature add")
        gm[x.signature_id] = x
    ss = _normalize_steps(sm.values()); gs = _normalize_signatures(gm.values())
    if registry_fingerprint(ss, gs) != delta.target_fingerprint:
        raise ValueError("delta target fingerprint mismatch")
    return ss, gs


def plan_registry_sync(steps: Iterable[ProvenanceStep], signatures: Iterable[SignatureEvidence], remote_known: Mapping[str, str]) -> RegistrySyncPlan:
    ss = _normalize_steps(steps); gs = _normalize_signatures(signatures)
    missing_steps = tuple(x.step_id for x in ss if remote_known.get("step:" + x.step_id) != fingerprint(x))
    missing_sigs = tuple(x.signature_id for x in gs if remote_known.get("sig:" + x.signature_id) != fingerprint(x))
    sm = {x.step_id: x for x in ss}; gm = {x.signature_id: x for x in gs}
    payload = (
        tuple(sm[k] for k in missing_steps),
        tuple(gm[k] for k in missing_sigs),
    )
    bytes_required = len(canonical_json(payload).encode("utf-8"))
    full_bytes = len(canonical_json((ss, gs)).encode("utf-8"))
    full_resend = full_bytes > 0 and bytes_required >= full_bytes * 0.9
    return RegistrySyncPlan(missing_steps, missing_sigs, bytes_required, full_bytes, full_resend)


def verdicts_digest(verdicts: Iterable[AuthenticityVerdict]) -> str:
    return fingerprint(tuple(verdicts))


def default_policy(now: int) -> ProvenancePolicy:
    return ProvenancePolicy(
        "PROVENANCE-052", "2.0.0", 1, now - 100, now + 100000,
        frozenset({"VERIFY_ORIGIN", "VERIFY_AUTHENTICITY"}),
        frozenset({"NOEPIN-ORIGIN"}),
        frozenset({"NOEPIN-PROV-ISSUER"}),
        frozenset({"VERIFIER-TRUSTED"}),
        frozenset({"ED25519", "ECDSA-P256"}),
        .80, .50, .80, 86400, 10000, 10000, True, False
    )


def default_request(now: int) -> AuthenticityRequest:
    del now
    return AuthenticityRequest(
        "AUTH-REQ-052", "CONTENT-052", fingerprint(("content", "current", 52)), "VERIFY_AUTHENTICITY",
        "NOEPIN-ORIGIN", "PROVENANCE-052", "2.0.0", 1, "PROV-EVIDENCE-052"
    )


def default_evidence(now: int) -> Tuple[Tuple[ProvenanceStep, ...], Tuple[SignatureEvidence, ...]]:
    req = default_request(now)
    origin_hash = fingerprint(("content", "origin", 52))
    steps = (
        ProvenanceStep("STEP-000", req.content_id, 0, "NOEPIN-ORIGIN", "NOEPIN", "NOEPIN-PROV-ISSUER", now - 20, GENESIS_SHA256, origin_hash, "CREATE", .95, req.evidence_binding, True, False),
        ProvenanceStep("STEP-001", req.content_id, 1, "NOEPIN-ORIGIN", "NOEPIN", "NOEPIN-PROV-ISSUER", now - 10, origin_hash, req.content_sha256, "TRANSFORM", .95, req.evidence_binding, True, False),
    )
    sig = SignatureEvidence(
        "SIG-001", req.content_id, req.content_sha256, "NOEPIN-ORIGIN", "NOEPIN", "KEY-052", "ED25519", "VERIFIER-TRUSTED",
        now - 5, req.evidence_binding,
        signature_payload_fingerprint(req.content_id, req.content_sha256, "NOEPIN-ORIGIN", "NOEPIN", "KEY-052", "ED25519"),
        True, .95, False
    )
    return steps, (sig,)
