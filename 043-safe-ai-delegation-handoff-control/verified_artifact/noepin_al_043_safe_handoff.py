"""NOEPIN AL 043 — Safe AI Delegation / Handoff Control.

Pure control-plane implementation for Delegation Token candidate evaluation,
Scope Attenuation, Parent-child Trace, and DCSR Context Manifest transfer.
It performs no permission grant, agent invocation, tool execution, network
transmission, persistence, or handoff execution.

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
TECHNOLOGY_ID = "NOEPIN-AL-043"


class ControlDecision(str, Enum):
    ALLOW = "ALLOW"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"
    HOLD = "HOLD"
    DENY = "DENY"


@dataclass(frozen=True)
class DelegationPolicy:
    policy_id: str
    version: str
    authority_epoch: int
    issued_at: int
    expires_at: int
    allowed_operations: FrozenSet[str]
    allowed_scopes: FrozenSet[str]
    allowed_capabilities: FrozenSet[str]
    human_approval_scopes: FrozenSet[str]
    allowed_context_classifications: FrozenSet[str]
    required_context_keys: FrozenSet[str]
    max_hops: int = 4
    max_token_ttl_seconds: int = 3600
    max_context_bytes: int = 2_000_000
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
        if now < self.issued_at or now >= self.expires_at:
            raise ValueError("policy not currently valid")
        if not self.allowed_operations or not self.allowed_scopes:
            raise ValueError("allowed operations/scopes required")
        if not self.human_approval_scopes.issubset(self.allowed_scopes):
            raise ValueError("human approval scopes must be allowed")
        if self.max_hops < 0 or self.max_token_ttl_seconds <= 0 or self.max_context_bytes < 0:
            raise ValueError("invalid delegation limits")


@dataclass(frozen=True)
class AuthorityContext:
    active_agents: FrozenSet[str]
    child_scope_ceiling: Mapping[str, FrozenSet[str]]
    child_capability_ceiling: Mapping[str, FrozenSet[str]]
    authority_epoch: int
    authority_binding: str

    def validate(self) -> None:
        if self.authority_epoch < 1 or not self.authority_binding:
            raise ValueError("authority context invalid")
        if any(not agent for agent in self.active_agents):
            raise ValueError("invalid active agent")


@dataclass(frozen=True)
class ContextItem:
    context_id: str
    key: str
    classification: str
    purpose: str
    version: str
    content_fingerprint: str
    byte_length: int

    def validate(self) -> None:
        if not self.context_id or not self.key or not self.classification or not self.purpose or not self.version:
            raise ValueError("context identity/binding required")
        if self.byte_length < 0:
            raise ValueError("byte_length must be non-negative")
        fp = self.content_fingerprint.lower()
        if len(fp) != 64 or any(c not in "0123456789abcdef" for c in fp):
            raise ValueError("content_fingerprint must be 64 hex chars")


@dataclass(frozen=True)
class DelegationRequest:
    delegation_id: str
    parent_agent_id: str
    child_agent_id: str
    task_id: str
    intent: str
    operation: str
    parent_scopes: FrozenSet[str]
    parent_capabilities: FrozenSet[str]
    requested_scopes: FrozenSet[str]
    requested_capabilities: FrozenSet[str]
    context_items: Tuple[ContextItem, ...]
    expected_policy_id: str
    expected_policy_version: str
    expected_authority_epoch: int
    evidence_binding: str
    issued_at: int
    expires_at: int
    hop_count: int
    parent_trace_hash: str = ""

    def validate(self) -> None:
        for value in (self.delegation_id, self.parent_agent_id, self.child_agent_id, self.task_id,
                      self.intent, self.operation, self.expected_policy_id, self.expected_policy_version,
                      self.evidence_binding):
            if not value:
                raise ValueError("delegation request identity/binding required")
        if self.expected_authority_epoch < 1:
            raise ValueError("expected_authority_epoch must be >=1")
        if self.issued_at < 0 or self.expires_at <= self.issued_at:
            raise ValueError("invalid request lifetime")
        if self.hop_count < 0:
            raise ValueError("hop_count must be non-negative")
        if self.hop_count > 0 and not self.parent_trace_hash:
            raise ValueError("delegated child trace requires parent_trace_hash")
        if self.hop_count == 0 and self.parent_trace_hash:
            raise ValueError("root delegation must not invent parent trace")
        ids = [x.context_id for x in self.context_items]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate context_id")
        keys = [x.key for x in self.context_items]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate context key")
        for item in self.context_items:
            item.validate()


@dataclass(frozen=True)
class PreparedContextManifest:
    items: Tuple[ContextItem, ...]
    manifest_fingerprint: str
    item_fingerprints: Mapping[str, str]
    by_key: Mapping[str, ContextItem]
    total_bytes: int


@dataclass(frozen=True)
class ContextDelta:
    base_fingerprint: str
    target_fingerprint: str
    changed_items: Tuple[ContextItem, ...]
    removed_item_ids: Tuple[str, ...]
    added_items: Tuple[ContextItem, ...]


@dataclass(frozen=True)
class TransferPlan:
    manifest_fingerprint: str
    missing_context_ids: Tuple[str, ...]
    already_known_context_ids: Tuple[str, ...]
    bytes_required: int
    full_resend_required: bool = False


@dataclass(frozen=True)
class DelegationAssessment:
    decision: ControlDecision
    reasons: Tuple[str, ...]
    delegation_id: str
    attenuated_scopes: Tuple[str, ...]
    attenuated_capabilities: Tuple[str, ...]
    context_manifest_fingerprint: str
    context_transfer_plan: TransferPlan
    trace_hash: str
    token_candidate_fingerprint: str
    policy_fingerprint: str
    request_fingerprint: str
    permission_granted: bool = False
    handoff_executed: bool = False
    action_success: bool = False
    context_truth_established: bool = False


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


def content_fingerprint(payload: bytes) -> str:
    return sha256(payload).hexdigest()


def normalize_context(items: Iterable[ContextItem]) -> Tuple[ContextItem, ...]:
    result = tuple(sorted(items, key=lambda x: (x.context_id, x.key)))
    ids = [x.context_id for x in result]
    keys = [x.key for x in result]
    if len(ids) != len(set(ids)) or len(keys) != len(set(keys)):
        raise ValueError("duplicate context identity/key")
    for item in result:
        item.validate()
    return result


def prepare_context(items: Iterable[ContextItem]) -> PreparedContextManifest:
    normalized = normalize_context(items)
    by_key = {x.key: x for x in normalized}
    item_fps = {x.context_id: fingerprint(x) for x in normalized}
    return PreparedContextManifest(
        items=normalized,
        manifest_fingerprint=fingerprint(normalized),
        item_fingerprints=item_fps,
        by_key=by_key,
        total_bytes=sum(x.byte_length for x in normalized),
    )


def plan_context_transfer(prepared: PreparedContextManifest, remote_known_fingerprints: Mapping[str, str]) -> TransferPlan:
    missing = []
    known = []
    bytes_required = 0
    by_id = {x.context_id: x for x in prepared.items}
    for cid, fp in sorted(prepared.item_fingerprints.items()):
        if remote_known_fingerprints.get(cid) == fp:
            known.append(cid)
        else:
            missing.append(cid)
            bytes_required += by_id[cid].byte_length
    return TransferPlan(prepared.manifest_fingerprint, tuple(missing), tuple(known), bytes_required, False)


def compute_context_delta(base: Sequence[ContextItem], target: Sequence[ContextItem]) -> ContextDelta:
    b = {x.context_id: x for x in normalize_context(base)}
    t = {x.context_id: x for x in normalize_context(target)}
    changed = tuple(t[k] for k in sorted(set(b) & set(t)) if fingerprint(b[k]) != fingerprint(t[k]))
    removed = tuple(sorted(set(b) - set(t)))
    added = tuple(t[k] for k in sorted(set(t) - set(b)))
    return ContextDelta(fingerprint(tuple(b[k] for k in sorted(b))), fingerprint(tuple(t[k] for k in sorted(t))), changed, removed, added)


def apply_context_delta(base: Sequence[ContextItem], delta: ContextDelta) -> Tuple[ContextItem, ...]:
    normalized = normalize_context(base)
    if fingerprint(normalized) != delta.base_fingerprint:
        raise ValueError("base fingerprint mismatch")
    state = {x.context_id: x for x in normalized}
    for cid in delta.removed_item_ids:
        if cid not in state:
            raise ValueError("removed context missing from base")
        del state[cid]
    for item in delta.changed_items:
        if item.context_id not in state:
            raise ValueError("changed context missing from base")
        state[item.context_id] = item
    for item in delta.added_items:
        if item.context_id in state:
            raise ValueError("added context already exists")
        state[item.context_id] = item
    target = normalize_context(state.values())
    if fingerprint(target) != delta.target_fingerprint:
        raise ValueError("target fingerprint mismatch")
    return target


def _empty_plan() -> TransferPlan:
    return TransferPlan(fingerprint(tuple()), tuple(), tuple(), 0, False)


def _assessment(decision: ControlDecision, reasons: Iterable[str], request: DelegationRequest,
                policy: DelegationPolicy, manifest: PreparedContextManifest | None,
                scopes: Iterable[str] = (), caps: Iterable[str] = (),
                remote_known_fingerprints: Mapping[str, str] | None = None) -> DelegationAssessment:
    scopes_t = tuple(sorted(set(scopes)))
    caps_t = tuple(sorted(set(caps)))
    plan = _empty_plan() if manifest is None else plan_context_transfer(manifest, remote_known_fingerprints or {})
    trace_payload = {
        "parent_trace_hash": request.parent_trace_hash,
        "delegation_id": request.delegation_id,
        "parent": request.parent_agent_id,
        "child": request.child_agent_id,
        "task": request.task_id,
        "intent": request.intent,
        "scopes": scopes_t,
        "capabilities": caps_t,
        "manifest": plan.manifest_fingerprint,
        "hop_count": request.hop_count,
    }
    trace_hash = fingerprint(trace_payload)
    token_payload = {
        "delegation_id": request.delegation_id,
        "parent": request.parent_agent_id,
        "child": request.child_agent_id,
        "task_id": request.task_id,
        "intent": request.intent,
        "operation": request.operation,
        "scopes": scopes_t,
        "capabilities": caps_t,
        "expires_at": request.expires_at,
        "trace_hash": trace_hash,
        "context_manifest_fingerprint": plan.manifest_fingerprint,
        "candidate_only": True,
    }
    return DelegationAssessment(
        decision=decision,
        reasons=tuple(sorted(set(reasons))),
        delegation_id=request.delegation_id,
        attenuated_scopes=scopes_t,
        attenuated_capabilities=caps_t,
        context_manifest_fingerprint=plan.manifest_fingerprint,
        context_transfer_plan=plan,
        trace_hash=trace_hash,
        token_candidate_fingerprint=fingerprint(token_payload),
        policy_fingerprint=fingerprint(policy),
        request_fingerprint=fingerprint(request),
    )


def evaluate_prepared(request: DelegationRequest, policy: DelegationPolicy, authority: AuthorityContext,
                      manifest: PreparedContextManifest, *, now: int,
                      remote_known_fingerprints: Mapping[str, str] | None = None) -> DelegationAssessment:
    try:
        request.validate(); policy.validate(now); authority.validate()
    except (ValueError, TypeError) as exc:
        return _assessment(ControlDecision.HOLD, ("INVALID_INPUT", type(exc).__name__), request, policy, manifest)

    hold = []
    if request.expected_policy_id != policy.policy_id: hold.append("POLICY_ID_MISMATCH")
    if request.expected_policy_version != policy.version: hold.append("POLICY_VERSION_MISMATCH")
    if request.expected_authority_epoch != policy.authority_epoch: hold.append("POLICY_AUTHORITY_EPOCH_MISMATCH")
    if request.expected_authority_epoch != authority.authority_epoch: hold.append("AUTHORITY_EPOCH_MISMATCH")
    if now < request.issued_at: hold.append("REQUEST_NOT_YET_VALID")
    if now >= request.expires_at: hold.append("REQUEST_EXPIRED")
    if request.expires_at - request.issued_at > policy.max_token_ttl_seconds: hold.append("TOKEN_TTL_EXCEEDS_POLICY")
    if request.parent_agent_id not in authority.active_agents: hold.append("PARENT_AGENT_INACTIVE")
    if request.child_agent_id not in authority.active_agents: hold.append("CHILD_AGENT_INACTIVE")
    if request.hop_count > policy.max_hops: hold.append("MAX_HOPS_EXCEEDED")
    if hold:
        return _assessment(ControlDecision.HOLD, hold, request, policy, manifest)

    deny = []
    if request.parent_agent_id == request.child_agent_id: deny.append("SELF_DELEGATION_FORBIDDEN")
    if request.operation not in policy.allowed_operations: deny.append("OPERATION_NOT_ALLOWED")
    if not request.requested_scopes.issubset(request.parent_scopes): deny.append("SCOPE_EXPANDS_PARENT_AUTHORITY")
    if not request.requested_scopes.issubset(policy.allowed_scopes): deny.append("SCOPE_OUTSIDE_POLICY")
    if not request.requested_capabilities.issubset(request.parent_capabilities): deny.append("CAPABILITY_EXPANDS_PARENT_AUTHORITY")
    if not request.requested_capabilities.issubset(policy.allowed_capabilities): deny.append("CAPABILITY_OUTSIDE_POLICY")
    child_scope = authority.child_scope_ceiling.get(request.child_agent_id, frozenset())
    child_cap = authority.child_capability_ceiling.get(request.child_agent_id, frozenset())
    if not request.requested_scopes.issubset(child_scope): deny.append("SCOPE_EXCEEDS_CHILD_CEILING")
    if not request.requested_capabilities.issubset(child_cap): deny.append("CAPABILITY_EXCEEDS_CHILD_CEILING")
    if manifest.total_bytes > policy.max_context_bytes: deny.append("CONTEXT_BYTES_EXCEED_POLICY")
    bad_class = [x.context_id for x in manifest.items if x.classification not in policy.allowed_context_classifications]
    if bad_class: deny.append("CONTEXT_CLASSIFICATION_NOT_ALLOWED")
    if deny:
        return _assessment(ControlDecision.DENY, deny, request, policy, manifest)

    present_keys = frozenset(manifest.by_key)
    if not policy.required_context_keys.issubset(present_keys):
        return _assessment(ControlDecision.HOLD, ("REQUIRED_CONTEXT_MISSING",), request, policy, manifest)
    if any(x.purpose != request.intent for x in manifest.items):
        return _assessment(ControlDecision.HOLD, ("CONTEXT_PURPOSE_BINDING_MISMATCH",), request, policy, manifest)

    reasons = ["SCOPE_ATTENUATION_VALID", "PARENT_CHILD_TRACE_CANDIDATE", "CONTEXT_MANIFEST_VALID"]
    decision = ControlDecision.ALLOW
    if request.requested_scopes & policy.human_approval_scopes:
        decision = ControlDecision.HUMAN_APPROVAL
        reasons.append("HUMAN_APPROVAL_SCOPE_PRESENT")
    else:
        reasons.append("DELEGATION_CANDIDATE_ALLOWED")
    return _assessment(decision, reasons, request, policy, manifest,
                       request.requested_scopes, request.requested_capabilities,
                       remote_known_fingerprints)


def evaluate(request: DelegationRequest, policy: DelegationPolicy, authority: AuthorityContext, *, now: int,
             remote_known_fingerprints: Mapping[str, str] | None = None) -> DelegationAssessment:
    try:
        manifest = prepare_context(request.context_items)
    except (ValueError, TypeError):
        manifest = prepare_context(())
    return evaluate_prepared(request, policy, authority, manifest, now=now,
                             remote_known_fingerprints=remote_known_fingerprints)


def default_policy(now: int = 1_800_000_000) -> DelegationPolicy:
    return DelegationPolicy(
        policy_id="DELEGATION-POLICY", version="1", authority_epoch=1,
        issued_at=now-1000, expires_at=now+86400,
        allowed_operations=frozenset({"ANALYZE", "VERIFY", "SUMMARIZE", "BUILD_CANDIDATE"}),
        allowed_scopes=frozenset({"READ_CONTEXT", "ANALYZE", "VERIFY", "BUILD_CANDIDATE", "SENSITIVE_REVIEW"}),
        allowed_capabilities=frozenset({"LOCAL_COMPUTE", "READ_SHARED_STATE", "WRITE_LOCAL_ARTIFACT"}),
        human_approval_scopes=frozenset({"SENSITIVE_REVIEW"}),
        allowed_context_classifications=frozenset({"PUBLIC", "INTERNAL", "CONFIDENTIAL"}),
        required_context_keys=frozenset({"task", "authority"}),
        max_hops=4, max_token_ttl_seconds=3600, max_context_bytes=2_000_000,
    )


def default_authority() -> AuthorityContext:
    common_scopes = frozenset({"READ_CONTEXT", "ANALYZE", "VERIFY", "BUILD_CANDIDATE", "SENSITIVE_REVIEW"})
    common_caps = frozenset({"LOCAL_COMPUTE", "READ_SHARED_STATE", "WRITE_LOCAL_ARTIFACT"})
    return AuthorityContext(
        active_agents=frozenset({"AI-A", "AI-B", "AI-C"}),
        child_scope_ceiling={"AI-B": common_scopes, "AI-C": frozenset({"READ_CONTEXT", "ANALYZE", "VERIFY"})},
        child_capability_ceiling={"AI-B": common_caps, "AI-C": frozenset({"LOCAL_COMPUTE", "READ_SHARED_STATE"})},
        authority_epoch=1, authority_binding="AUTH-E1",
    )


def make_context(context_id: str, key: str, purpose: str, *, classification: str = "INTERNAL",
                 version: str = "1", payload: bytes | None = None) -> ContextItem:
    data = payload if payload is not None else f"{context_id}:{key}:{purpose}:{version}".encode()
    return ContextItem(context_id, key, classification, purpose, version, content_fingerprint(data), len(data))


def default_request(now: int = 1_800_000_000, *, child: str = "AI-B", hop_count: int = 0,
                    parent_trace_hash: str = "") -> DelegationRequest:
    intent = "verify_build"
    items = (
        make_context("CTX-TASK", "task", intent),
        make_context("CTX-AUTH", "authority", intent),
        make_context("CTX-STATE", "state", intent),
    )
    return DelegationRequest(
        delegation_id="DEL-001", parent_agent_id="AI-A", child_agent_id=child,
        task_id="TASK-001", intent=intent, operation="VERIFY",
        parent_scopes=frozenset({"READ_CONTEXT", "ANALYZE", "VERIFY", "BUILD_CANDIDATE"}),
        parent_capabilities=frozenset({"LOCAL_COMPUTE", "READ_SHARED_STATE", "WRITE_LOCAL_ARTIFACT"}),
        requested_scopes=frozenset({"READ_CONTEXT", "VERIFY"}),
        requested_capabilities=frozenset({"LOCAL_COMPUTE", "READ_SHARED_STATE"}),
        context_items=items, expected_policy_id="DELEGATION-POLICY", expected_policy_version="1",
        expected_authority_epoch=1, evidence_binding="EVIDENCE-001",
        issued_at=now-10, expires_at=now+600, hop_count=hop_count,
        parent_trace_hash=parent_trace_hash,
    )


__all__ = [name for name in globals() if not name.startswith("_")]
