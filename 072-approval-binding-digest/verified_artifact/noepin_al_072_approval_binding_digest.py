"""NOEPIN AL 072 — Approval-Binding Digest / Sequential Successor V2.

Pure pre-execution verifier for human-approval binding. It cryptographically
checks that an approval evidence record is bound to the exact Request, Action,
Target, Parameters, Policy fingerprint, Nonce, scope, expiry and authority epoch.
It never grants permission, consumes a nonce, writes a replay ledger, performs an
atomic publish, executes a tool/action, or promotes approval evidence to success.

HMAC verification keys are external typed inputs. This module does not create,
store, rotate, distribute, or authorize production keys.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from hashlib import sha256
import hmac
import json
from typing import Iterable, Tuple

SCHEMA_VERSION = "NOEPIN-AL-072-V2"

class Decision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    HOLD = "HOLD"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"

@dataclass(frozen=True)
class ApprovalRequest:
    request_id: str
    actor_id: str
    action: str
    target: str
    parameters: Tuple[Tuple[str, str], ...]
    policy_fingerprint: str
    nonce: str
    approval_scope: str
    intent_fingerprint: str
    created_at: int
    binding: str
    approval_epoch: str

@dataclass(frozen=True)
class ApprovalRecord:
    approval_id: str
    approver_id: str
    key_id: str
    request_fingerprint: str
    approval_digest: str
    mac_hex: str
    nonce: str
    issued_at: int
    expires_at: int
    binding: str
    approval_epoch: str
    single_use: bool = True

@dataclass(frozen=True)
class ApproverAuthority:
    principal_id: str
    key_id: str
    capabilities: Tuple[str, ...]
    binding: str
    approval_epoch: str
    verified: bool = True
    revoked: bool = False

@dataclass(frozen=True)
class VerifierKeyRecord:
    key_id: str
    verifier_key_hex: str
    binding: str
    approval_epoch: str
    verified: bool = True
    revoked: bool = False
    expires_at: int = 2_000_000_000

@dataclass(frozen=True)
class ReplayReceipt:
    approval_digest: str
    nonce: str
    binding: str
    verified: bool = True
    consumed: bool = True

@dataclass(frozen=True)
class ApprovalPolicy:
    policy_id: str
    binding: str
    approval_epoch: str
    trusted_approvers: Tuple[str, ...]
    required_capability: str
    max_request_age: int
    max_approval_lifetime: int
    require_single_use: bool = True
    revoked: bool = False

@dataclass(frozen=True)
class PreparedApprovalState:
    policy: ApprovalPolicy
    approvals: Tuple[ApprovalRecord, ...]
    authorities: Tuple[ApproverAuthority, ...]
    keys: Tuple[VerifierKeyRecord, ...]
    replay_receipts: Tuple[ReplayReceipt, ...]
    binding: str
    policy_fingerprint: str
    registry_fingerprint: str
    approval_fingerprints: Tuple[Tuple[str, str], ...]
    authority_fingerprints: Tuple[Tuple[str, str], ...]
    key_fingerprints: Tuple[Tuple[str, str], ...]
    replay_fingerprints: Tuple[Tuple[str, str], ...]
    approval_index: Tuple[Tuple[str, ApprovalRecord], ...]
    authority_index: Tuple[Tuple[str, ApproverAuthority], ...]
    key_index: Tuple[Tuple[str, VerifierKeyRecord], ...]
    replay_digest_index: Tuple[Tuple[str, ReplayReceipt], ...]
    replay_nonce_index: Tuple[Tuple[str, ReplayReceipt], ...]

@dataclass(frozen=True)
class ApprovalRegistryDelta:
    base_fingerprint: str
    target_fingerprint: str
    policy: ApprovalPolicy
    binding: str
    upsert_approvals: Tuple[ApprovalRecord, ...]
    remove_approval_ids: Tuple[str, ...]
    upsert_authorities: Tuple[ApproverAuthority, ...]
    remove_authority_ids: Tuple[str, ...]
    upsert_keys: Tuple[VerifierKeyRecord, ...]
    remove_key_ids: Tuple[str, ...]
    upsert_replay_receipts: Tuple[ReplayReceipt, ...]
    remove_replay_digests: Tuple[str, ...]

@dataclass(frozen=True)
class ApprovalSyncPlan:
    missing_or_changed_approval_ids: Tuple[str, ...]
    missing_or_changed_authority_ids: Tuple[str, ...]
    missing_or_changed_key_ids: Tuple[str, ...]
    missing_or_changed_replay_digests: Tuple[str, ...]
    metadata_bytes_required: int
    full_resend_required: bool

@dataclass(frozen=True)
class ApprovalVerificationResult:
    decision: Decision
    reasons: Tuple[str, ...]
    request_id: str
    approval_id: str | None
    approver_id: str | None
    request_fingerprint: str
    approval_digest: str | None
    expires_at: int | None
    digest_binding_valid: bool
    authority_valid: bool
    replay_clear: bool
    next_gate_candidate: bool
    atomic_publish_candidate: bool
    reapproval_required: bool
    approval_executed: bool = False
    nonce_consumed: bool = False
    replay_ledger_written: bool = False
    permission_granted: bool = False
    tool_executed: bool = False
    external_send_performed: bool = False
    atomic_publish_performed: bool = False
    world_truth_proven: bool = False
    safety_proven: bool = False
    action_success: bool = False


def _canon_pairs(pairs: Iterable[Tuple[str, str]]) -> Tuple[Tuple[str, str], ...]:
    out = []
    seen = set()
    for k, v in pairs:
        k, v = str(k), str(v)
        if k in seen:
            raise ValueError("DUPLICATE_PARAMETER_KEY")
        seen.add(k)
        out.append((k, v))
    return tuple(sorted(out))


def _ser(obj) -> bytes:
    def norm(x):
        if isinstance(x, Enum):
            return x.value
        if hasattr(x, "__dataclass_fields__"):
            return {k: norm(getattr(x, k)) for k in sorted(x.__dataclass_fields__)}
        if isinstance(x, tuple):
            return [norm(v) for v in x]
        if isinstance(x, list):
            return [norm(v) for v in x]
        if isinstance(x, dict):
            return {str(k): norm(v) for k, v in sorted(x.items(), key=lambda kv: str(kv[0]))}
        return x
    return json.dumps(norm(obj), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def _fp(obj) -> str:
    return sha256(_ser(obj)).hexdigest()


def canonical_request(req: ApprovalRequest) -> ApprovalRequest:
    return replace(req, parameters=_canon_pairs(req.parameters))


def request_fingerprint(req: ApprovalRequest) -> str:
    r = canonical_request(req)
    return _fp({
        "request_id": r.request_id,
        "actor_id": r.actor_id,
        "action": r.action,
        "target": r.target,
        "parameters": r.parameters,
        "policy_fingerprint": r.policy_fingerprint,
        "nonce": r.nonce,
        "approval_scope": r.approval_scope,
        "intent_fingerprint": r.intent_fingerprint,
        "created_at": r.created_at,
        "binding": r.binding,
        "approval_epoch": r.approval_epoch,
    })


def bound_digest(req: ApprovalRequest, approval_id: str, approver_id: str, key_id: str, issued_at: int, expires_at: int, single_use: bool) -> str:
    r = canonical_request(req)
    return _fp({
        "schema": SCHEMA_VERSION,
        "approval_id": approval_id,
        "approver_id": approver_id,
        "key_id": key_id,
        "request_fingerprint": request_fingerprint(r),
        "action": r.action,
        "target": r.target,
        "parameters": r.parameters,
        "policy_fingerprint": r.policy_fingerprint,
        "nonce": r.nonce,
        "approval_scope": r.approval_scope,
        "intent_fingerprint": r.intent_fingerprint,
        "issued_at": int(issued_at),
        "expires_at": int(expires_at),
        "single_use": bool(single_use),
        "binding": r.binding,
        "approval_epoch": r.approval_epoch,
    })


def _mac(key_hex: str, digest_hex: str) -> str:
    try:
        key = bytes.fromhex(key_hex)
    except ValueError:
        return ""
    return hmac.new(key, digest_hex.encode("ascii"), sha256).hexdigest()


def default_policy(now: int) -> ApprovalPolicy:
    return ApprovalPolicy("APPROVAL-POLICY", "APPROVAL-BIND", "APPROVAL-EPOCH", ("HUMAN-ADMIN", "SECURITY-ADMIN"), "APPROVE_HIGH_RISK", 600, 600, True, False)


def default_request(now: int) -> ApprovalRequest:
    return ApprovalRequest("REQ-72", "AGENT-1", "DELETE", "RESOURCE-7", (("mode", "safe"), ("recursive", "false")), "POLICY-FP-7", "NONCE-72", "HIGH_RISK_TOOL_CALL", "INTENT-FP-72", now, "APPROVAL-BIND", "APPROVAL-EPOCH")


def default_authorities() -> Tuple[ApproverAuthority, ...]:
    c = dict(binding="APPROVAL-BIND", approval_epoch="APPROVAL-EPOCH", verified=True, revoked=False)
    return (
        ApproverAuthority("HUMAN-ADMIN", "KEY-HUMAN", ("APPROVE_HIGH_RISK",), **c),
        ApproverAuthority("SECURITY-ADMIN", "KEY-SECURITY", ("APPROVE_HIGH_RISK",), **c),
    )


def default_keys(now: int) -> Tuple[VerifierKeyRecord, ...]:
    return (
        VerifierKeyRecord("KEY-HUMAN", "11" * 32, "APPROVAL-BIND", "APPROVAL-EPOCH", True, False, now + 3600),
        VerifierKeyRecord("KEY-SECURITY", "22" * 32, "APPROVAL-BIND", "APPROVAL-EPOCH", True, False, now + 3600),
    )


def reference_approval(req: ApprovalRequest, *, approval_id: str = "APR-72", approver_id: str = "HUMAN-ADMIN", key_id: str = "KEY-HUMAN", key_hex: str = "11" * 32, issued_at: int = 1_800_000_000, expires_at: int | None = None, single_use: bool = True) -> ApprovalRecord:
    """Deterministic test/reference evidence constructor, not a production approval issuer."""
    if expires_at is None:
        expires_at = issued_at + 300
    rf = request_fingerprint(req)
    d = bound_digest(req, approval_id, approver_id, key_id, issued_at, expires_at, single_use)
    return ApprovalRecord(approval_id, approver_id, key_id, rf, d, _mac(key_hex, d), req.nonce, issued_at, expires_at, req.binding, req.approval_epoch, single_use)


def _valid_policy(p: ApprovalPolicy, binding: str) -> bool:
    return bool(p.policy_id and p.binding == binding and p.approval_epoch and p.required_capability and p.max_request_age >= 0 and p.max_approval_lifetime > 0 and not p.revoked)


def _build_map(rows, keyfn, duplicate_code: str):
    out = {}
    for row in rows:
        key = str(keyfn(row))
        if key in out:
            raise ValueError(duplicate_code)
        out[key] = row
    return out


def _lookup_index(index, key):
    key = str(key)
    lo, hi = 0, len(index)
    while lo < hi:
        mid = (lo + hi) // 2
        mk = index[mid][0]
        if mk < key:
            lo = mid + 1
        else:
            hi = mid
    return index[lo][1] if lo < len(index) and index[lo][0] == key else None


def _zero(req: ApprovalRequest, rf: str, *, approval_id: str | None = None) -> ApprovalVerificationResult:
    return ApprovalVerificationResult(Decision.HOLD, (), req.request_id, approval_id, None, rf, None, None, False, False, False, False, False, False)


def _evaluate_lookup(req: ApprovalRequest, approval_id: str | None, policy: ApprovalPolicy, get_approval, get_authority, get_key, get_replay_digest, get_replay_nonce, *, current_policy_fingerprint: str | None, now: int, replay_state_confirmed: bool) -> ApprovalVerificationResult:
    try:
        req = canonical_request(req)
    except ValueError:
        rf = _fp({"invalid_request": req.request_id})
        return replace(_zero(req, rf, approval_id=approval_id), decision=Decision.DENY, reasons=("REQUEST_PARAMETERS_INVALID",))
    rf = request_fingerprint(req)
    zero = _zero(req, rf, approval_id=approval_id)
    if not _valid_policy(policy, req.binding):
        return replace(zero, reasons=("APPROVAL_POLICY_INVALID_OR_BINDING_MISMATCH",))
    if req.approval_epoch != policy.approval_epoch:
        return replace(zero, decision=Decision.DENY, reasons=("APPROVAL_EPOCH_MISMATCH",), reapproval_required=True)
    if not current_policy_fingerprint:
        return replace(zero, reasons=("CURRENT_POLICY_FINGERPRINT_UNCONFIRMED",))
    if current_policy_fingerprint != req.policy_fingerprint:
        return replace(zero, decision=Decision.DENY, reasons=("CURRENT_POLICY_FINGERPRINT_MISMATCH",), reapproval_required=True)
    if req.created_at > now or now - req.created_at > policy.max_request_age:
        return replace(zero, reasons=("REQUEST_STALE_OR_FUTURE",), reapproval_required=True)
    if not approval_id:
        return replace(zero, decision=Decision.HUMAN_APPROVAL, reasons=("APPROVAL_REQUIRED",), reapproval_required=True)
    apr = get_approval(approval_id)
    if apr is None:
        return replace(zero, decision=Decision.HUMAN_APPROVAL, reasons=("APPROVAL_RECORD_MISSING",), reapproval_required=True)
    base = replace(zero, approval_id=apr.approval_id, approver_id=apr.approver_id, approval_digest=apr.approval_digest, expires_at=apr.expires_at)
    if apr.binding != req.binding or apr.approval_epoch != req.approval_epoch or apr.nonce != req.nonce:
        return replace(base, decision=Decision.DENY, reasons=("APPROVAL_BINDING_MISMATCH",), reapproval_required=True)
    if apr.approver_id not in policy.trusted_approvers:
        return replace(base, decision=Decision.DENY, reasons=("APPROVER_NOT_TRUSTED",), reapproval_required=True)
    auth = get_authority(apr.approver_id)
    if auth is None or not auth.verified or auth.revoked or auth.binding != req.binding or auth.approval_epoch != req.approval_epoch or auth.key_id != apr.key_id or policy.required_capability not in auth.capabilities:
        return replace(base, decision=Decision.DENY, reasons=("APPROVER_AUTHORITY_INVALID",), reapproval_required=True)
    key = get_key(apr.key_id)
    key_material_valid = False
    if key is not None:
        try:
            key_material_valid = len(bytes.fromhex(key.verifier_key_hex)) >= 32
        except ValueError:
            key_material_valid = False
    if key is None or not key.verified or key.revoked or key.binding != req.binding or key.approval_epoch != req.approval_epoch or key.expires_at < now or not key_material_valid:
        return replace(base, decision=Decision.DENY, reasons=("VERIFIER_KEY_INVALID",), authority_valid=True, reapproval_required=True)
    if apr.issued_at < req.created_at or apr.issued_at > now or apr.expires_at <= apr.issued_at or apr.expires_at - apr.issued_at > policy.max_approval_lifetime:
        return replace(base, decision=Decision.DENY, reasons=("APPROVAL_TIME_WINDOW_INVALID",), authority_valid=True, reapproval_required=True)
    if apr.expires_at <= now:
        return replace(base, reasons=("APPROVAL_EXPIRED_REAPPROVAL_REQUIRED",), authority_valid=True, reapproval_required=True)
    if apr.request_fingerprint != rf:
        return replace(base, decision=Decision.DENY, reasons=("REQUEST_FINGERPRINT_MISMATCH",), authority_valid=True, reapproval_required=True)
    d = bound_digest(req, apr.approval_id, apr.approver_id, apr.key_id, apr.issued_at, apr.expires_at, apr.single_use)
    if apr.approval_digest != d:
        return replace(base, decision=Decision.DENY, reasons=("APPROVAL_DIGEST_MISMATCH",), authority_valid=True, reapproval_required=True)
    expected_mac = _mac(key.verifier_key_hex, d)
    if not expected_mac or not hmac.compare_digest(expected_mac, apr.mac_hex):
        return replace(base, decision=Decision.DENY, reasons=("APPROVAL_MAC_INVALID",), authority_valid=True, reapproval_required=True)
    if policy.require_single_use and not apr.single_use:
        return replace(base, decision=Decision.DENY, reasons=("SINGLE_USE_REQUIRED",), digest_binding_valid=True, authority_valid=True, reapproval_required=True)
    if not replay_state_confirmed:
        return replace(base, reasons=("REPLAY_STATE_UNCONFIRMED",), digest_binding_valid=True, authority_valid=True)
    replay_rows = tuple(x for x in (get_replay_digest(d), get_replay_nonce(req.nonce)) if x is not None)
    if replay_rows:
        if any((not x.verified) or (not x.consumed) or x.binding != req.binding for x in replay_rows):
            return replace(base, reasons=("REPLAY_RECEIPT_STATE_UNCONFIRMED",), digest_binding_valid=True, authority_valid=True, replay_clear=False)
        return replace(base, decision=Decision.DENY, reasons=("APPROVAL_REPLAY_DETECTED",), digest_binding_valid=True, authority_valid=True, replay_clear=False, reapproval_required=True)
    return replace(base, decision=Decision.ALLOW, reasons=("APPROVAL_BINDING_VERIFIED",), digest_binding_valid=True, authority_valid=True, replay_clear=True, next_gate_candidate=True, atomic_publish_candidate=True, reapproval_required=False)


def evaluate(req: ApprovalRequest, approval_id: str | None, policy: ApprovalPolicy, approvals: Iterable[ApprovalRecord], authorities: Iterable[ApproverAuthority], keys: Iterable[VerifierKeyRecord], replay_receipts: Iterable[ReplayReceipt], *, current_policy_fingerprint: str | None = None, now: int, replay_state_confirmed: bool = True) -> ApprovalVerificationResult:
    try:
        am = _build_map(approvals, lambda x: x.approval_id, "DUPLICATE_APPROVAL_ID")
        au = _build_map(authorities, lambda x: x.principal_id, "DUPLICATE_AUTHORITY_ID")
        km = _build_map(keys, lambda x: x.key_id, "DUPLICATE_KEY_ID")
        rd = _build_map(replay_receipts, lambda x: x.approval_digest, "DUPLICATE_REPLAY_DIGEST")
        rn = _build_map(replay_receipts, lambda x: x.nonce, "DUPLICATE_REPLAY_NONCE")
    except ValueError as exc:
        rf = request_fingerprint(canonical_request(req))
        return replace(_zero(req, rf, approval_id=approval_id), decision=Decision.DENY, reasons=(str(exc),))
    return _evaluate_lookup(req, approval_id, policy, am.get, au.get, km.get, rd.get, rn.get, current_policy_fingerprint=current_policy_fingerprint, now=now, replay_state_confirmed=replay_state_confirmed)


def _records_fingerprint(policy, approvals, authorities, keys, replay_receipts, binding: str) -> str:
    return _fp({"policy": policy, "binding": binding, "approvals": tuple(sorted(approvals, key=lambda x: x.approval_id)), "authorities": tuple(sorted(authorities, key=lambda x: x.principal_id)), "keys": tuple(sorted(keys, key=lambda x: x.key_id)), "replay": tuple(sorted(replay_receipts, key=lambda x: (x.approval_digest, x.nonce)))})


def prepare_state(policy: ApprovalPolicy, approvals: Iterable[ApprovalRecord], authorities: Iterable[ApproverAuthority], keys: Iterable[VerifierKeyRecord], replay_receipts: Iterable[ReplayReceipt], *, binding: str) -> PreparedApprovalState:
    approvals, authorities, keys, replay_receipts = tuple(approvals), tuple(authorities), tuple(keys), tuple(replay_receipts)
    am = _build_map(approvals, lambda x: x.approval_id, "DUPLICATE_APPROVAL_ID")
    au = _build_map(authorities, lambda x: x.principal_id, "DUPLICATE_AUTHORITY_ID")
    km = _build_map(keys, lambda x: x.key_id, "DUPLICATE_KEY_ID")
    rd = _build_map(replay_receipts, lambda x: x.approval_digest, "DUPLICATE_REPLAY_DIGEST")
    rn = _build_map(replay_receipts, lambda x: x.nonce, "DUPLICATE_REPLAY_NONCE")
    af = tuple(sorted((k, _fp(v)) for k, v in am.items()))
    auf = tuple(sorted((k, _fp(v)) for k, v in au.items()))
    kf = tuple(sorted((k, _fp(v)) for k, v in km.items()))
    rf = tuple(sorted((k, _fp(v)) for k, v in rd.items()))
    pf = _fp({"policy": policy, "binding": binding})
    reg = _records_fingerprint(policy, approvals, authorities, keys, replay_receipts, binding)
    return PreparedApprovalState(policy, tuple(sorted(approvals, key=lambda x: x.approval_id)), tuple(sorted(authorities, key=lambda x: x.principal_id)), tuple(sorted(keys, key=lambda x: x.key_id)), tuple(sorted(replay_receipts, key=lambda x: (x.approval_digest, x.nonce))), binding, pf, reg, af, auf, kf, rf, tuple(sorted(am.items())), tuple(sorted(au.items())), tuple(sorted(km.items())), tuple(sorted(rd.items())), tuple(sorted(rn.items())))


def validate_prepared_integrity(st: PreparedApprovalState) -> bool:
    try:
        rebuilt = prepare_state(st.policy, st.approvals, st.authorities, st.keys, st.replay_receipts, binding=st.binding)
    except Exception:
        return False
    return (
        rebuilt.policy_fingerprint == st.policy_fingerprint
        and rebuilt.registry_fingerprint == st.registry_fingerprint
        and rebuilt.approval_fingerprints == st.approval_fingerprints
        and rebuilt.authority_fingerprints == st.authority_fingerprints
        and rebuilt.key_fingerprints == st.key_fingerprints
        and rebuilt.replay_fingerprints == st.replay_fingerprints
        and rebuilt.approval_index == st.approval_index
        and rebuilt.authority_index == st.authority_index
        and rebuilt.key_index == st.key_index
        and rebuilt.replay_digest_index == st.replay_digest_index
        and rebuilt.replay_nonce_index == st.replay_nonce_index
    )


def evaluate_prepared(req: ApprovalRequest, approval_id: str | None, st: PreparedApprovalState, *, current_approval_policy_fingerprint: str, current_registry_fingerprint: str, current_bound_policy_fingerprint: str | None = None, prepared_integrity_validated: bool, now: int, replay_state_confirmed: bool = True) -> ApprovalVerificationResult:
    rf = request_fingerprint(canonical_request(req))
    if not prepared_integrity_validated:
        return replace(_zero(req, rf, approval_id=approval_id), reasons=("PREPARED_INTEGRITY_NOT_VALIDATED",))
    if current_approval_policy_fingerprint != st.policy_fingerprint or current_registry_fingerprint != st.registry_fingerprint:
        return replace(_zero(req, rf, approval_id=approval_id), reasons=("PREPARED_STATE_STALE",))
    return _evaluate_lookup(req, approval_id, st.policy, lambda k: _lookup_index(st.approval_index, k), lambda k: _lookup_index(st.authority_index, k), lambda k: _lookup_index(st.key_index, k), lambda k: _lookup_index(st.replay_digest_index, k), lambda k: _lookup_index(st.replay_nonce_index, k), current_policy_fingerprint=current_bound_policy_fingerprint, now=now, replay_state_confirmed=replay_state_confirmed)


def make_delta(base: PreparedApprovalState, target: PreparedApprovalState) -> ApprovalRegistryDelta:
    if base.binding != target.binding or base.policy != target.policy:
        raise ValueError("DELTA_POLICY_OR_BINDING_MISMATCH")
    def diff(old_items, new_items, keyfn):
        old = {str(keyfn(x)): x for x in old_items}; new = {str(keyfn(x)): x for x in new_items}
        up = tuple(new[k] for k in sorted(new) if k not in old or _fp(new[k]) != _fp(old[k]))
        rm = tuple(k for k in sorted(old) if k not in new)
        return up, rm
    ua, ra = diff(base.approvals, target.approvals, lambda x: x.approval_id)
    uu, ru = diff(base.authorities, target.authorities, lambda x: x.principal_id)
    uk, rk = diff(base.keys, target.keys, lambda x: x.key_id)
    ur, rr = diff(base.replay_receipts, target.replay_receipts, lambda x: x.approval_digest)
    return ApprovalRegistryDelta(base.registry_fingerprint, target.registry_fingerprint, target.policy, target.binding, ua, ra, uu, ru, uk, rk, ur, rr)


def apply_delta(base: PreparedApprovalState, delta: ApprovalRegistryDelta) -> PreparedApprovalState:
    if base.registry_fingerprint != delta.base_fingerprint or base.binding != delta.binding or base.policy != delta.policy:
        raise ValueError("DELTA_BASE_MISMATCH")
    def patch(items, upserts, removals, keyfn):
        d = {str(keyfn(x)): x for x in items}
        for k in removals: d.pop(str(k), None)
        for x in upserts: d[str(keyfn(x))] = x
        return tuple(d[k] for k in sorted(d))
    approvals = patch(base.approvals, delta.upsert_approvals, delta.remove_approval_ids, lambda x: x.approval_id)
    authorities = patch(base.authorities, delta.upsert_authorities, delta.remove_authority_ids, lambda x: x.principal_id)
    keys = patch(base.keys, delta.upsert_keys, delta.remove_key_ids, lambda x: x.key_id)
    replay = patch(base.replay_receipts, delta.upsert_replay_receipts, delta.remove_replay_digests, lambda x: x.approval_digest)
    out = prepare_state(delta.policy, approvals, authorities, keys, replay, binding=delta.binding)
    if out.registry_fingerprint != delta.target_fingerprint:
        raise ValueError("DELTA_TARGET_MISMATCH")
    return out


def missing_only_sync_plan(target: PreparedApprovalState, remote_fingerprints: dict) -> ApprovalSyncPlan:
    remote_fingerprints = remote_fingerprints or {}
    def missing(local_pairs, remote):
        remote = remote or {}
        return tuple(k for k, fp in local_pairs if remote.get(k) != fp)
    a = missing(target.approval_fingerprints, remote_fingerprints.get("approvals"))
    u = missing(target.authority_fingerprints, remote_fingerprints.get("authorities"))
    k = missing(target.key_fingerprints, remote_fingerprints.get("keys"))
    r = missing(target.replay_fingerprints, remote_fingerprints.get("replay"))
    meta = len(_ser({"approvals": a, "authorities": u, "keys": k, "replay": r}))
    return ApprovalSyncPlan(a, u, k, r, meta, False)


def full_registry_bytes(st: PreparedApprovalState) -> int:
    return len(_ser({"policy": st.policy, "approvals": st.approvals, "authorities": st.authorities, "keys": st.keys, "replay": st.replay_receipts, "binding": st.binding}))


def delta_bytes(delta: ApprovalRegistryDelta) -> int:
    return len(_ser(delta))
