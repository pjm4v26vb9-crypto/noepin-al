from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from hashlib import sha256
import json
from pathlib import PurePosixPath
from typing import Iterable, Mapping, Sequence

TECHNOLOGY_NUMBER = 34
TECHNOLOGY_NAME = "タスク範囲境界エンフォーサー / Task Scope Boundary Enforcer"
VERSION = "2.0.0-successor.20261102"
CREATOR = "NOEPIN / のえぴん"


class ScopeDecision(str, Enum):
    ALLOW_CANDIDATE = "ALLOW_CANDIDATE"
    HUMAN_CONFIRM = "HUMAN_CONFIRM"
    HOLD = "HOLD"
    DENY = "DENY"


@dataclass(frozen=True)
class ScopeManifest:
    scope_id: str
    owner_user_id: str
    scope_version: str
    authority_version: str
    issued_at_ms: int
    starts_at_ms: int
    expires_at_ms: int
    active: bool
    revoked: bool
    allowed_path_prefixes: tuple[str, ...]
    denied_path_prefixes: tuple[str, ...]
    allowed_hosts: tuple[str, ...]
    allowed_users: tuple[str, ...]
    allowed_actions: tuple[str, ...]
    allowed_target_kinds: tuple[str, ...]
    human_confirm_actions: tuple[str, ...] = ()
    human_confirm_target_kinds: tuple[str, ...] = ()
    max_targets_per_request: int = 1


@dataclass(frozen=True)
class ScopeRequest:
    request_id: str
    actor_user_id: str
    observed_at_ms: int
    scope_version: str
    authority_version: str
    action: str
    target_kind: str
    path: str
    host: str
    target_user_id: str
    target_count: int
    high_impact: bool
    irreversible: bool
    human_approval_evidence: bool
    context_fingerprint: str
    connection_available: bool = False


@dataclass(frozen=True)
class ScopeResult:
    decision: ScopeDecision
    reasons: tuple[str, ...]
    scope_fingerprint: str
    request_fingerprint: str
    path_normalized: str
    path_in_scope: bool
    host_in_scope: bool
    user_in_scope: bool
    action_in_scope: bool
    target_kind_in_scope: bool
    time_in_scope: bool
    version_match: bool
    connected_observed: bool
    permission_granted: bool = False
    action_executed: bool = False
    action_succeeded: bool = False
    state_committed: bool = False
    authoritative: bool = False


class ScopeValidationError(ValueError):
    pass


def _canon(obj: object) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _fp(obj: object) -> str:
    return sha256(_canon(obj)).hexdigest()


def _clean_text(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise ScopeValidationError(f"{name}_NOT_STRING")
    if any(ord(ch) < 32 for ch in value):
        raise ScopeValidationError(f"{name}_CONTROL_CHAR")
    value = value.strip()
    if not value:
        raise ScopeValidationError(f"{name}_EMPTY")
    if len(value) > 512:
        raise ScopeValidationError(f"{name}_TOO_LONG")
    return value


def _normalize_path(path: str) -> str:
    raw = _clean_text(path, "PATH").replace("\\", "/")
    if not raw.startswith("/"):
        raise ScopeValidationError("PATH_NOT_ABSOLUTE")
    parts: list[str] = []
    for part in raw.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            raise ScopeValidationError("PATH_TRAVERSAL")
        parts.append(part)
    normalized = "/" + "/".join(parts)
    return normalized if normalized != "" else "/"


def _normalize_prefix(prefix: str) -> str:
    p = _normalize_path(prefix)
    if p != "/" and p.endswith("/"):
        p = p.rstrip("/")
    return p


def _path_under(path: str, prefix: str) -> bool:
    if prefix == "/":
        return path.startswith("/")
    return path == prefix or path.startswith(prefix + "/")


def _normalize_string_set(values: Iterable[str], name: str, *, lower: bool = False) -> tuple[str, ...]:
    out = []
    for raw in values:
        text = _clean_text(raw, name)
        out.append(text.lower() if lower else text)
    if len(out) != len(set(out)):
        raise ScopeValidationError(f"{name}_DUPLICATE")
    return tuple(sorted(out))


def validate_manifest(manifest: ScopeManifest) -> tuple[tuple[str, ...], tuple[str, ...]]:
    _clean_text(manifest.scope_id, "SCOPE_ID")
    _clean_text(manifest.owner_user_id, "OWNER_USER_ID")
    _clean_text(manifest.scope_version, "SCOPE_VERSION")
    _clean_text(manifest.authority_version, "AUTHORITY_VERSION")
    if manifest.issued_at_ms < 0 or manifest.starts_at_ms < 0 or manifest.expires_at_ms < 0:
        raise ScopeValidationError("MANIFEST_TIME_NEGATIVE")
    if manifest.starts_at_ms > manifest.expires_at_ms:
        raise ScopeValidationError("MANIFEST_TIME_ORDER")
    if manifest.issued_at_ms > manifest.expires_at_ms:
        raise ScopeValidationError("ISSUED_AFTER_EXPIRY")
    if manifest.max_targets_per_request < 1 or manifest.max_targets_per_request > 10000:
        raise ScopeValidationError("MAX_TARGETS_INVALID")
    allowed_paths = tuple(sorted(_normalize_prefix(x) for x in manifest.allowed_path_prefixes))
    denied_paths = tuple(sorted(_normalize_prefix(x) for x in manifest.denied_path_prefixes))
    if not allowed_paths:
        raise ScopeValidationError("ALLOWED_PATHS_EMPTY")
    _normalize_string_set(manifest.allowed_hosts, "ALLOWED_HOST", lower=True)
    _normalize_string_set(manifest.allowed_users, "ALLOWED_USER")
    _normalize_string_set(manifest.allowed_actions, "ALLOWED_ACTION", lower=True)
    _normalize_string_set(manifest.allowed_target_kinds, "ALLOWED_TARGET_KIND", lower=True)
    _normalize_string_set(manifest.human_confirm_actions, "HUMAN_CONFIRM_ACTION", lower=True)
    _normalize_string_set(manifest.human_confirm_target_kinds, "HUMAN_CONFIRM_TARGET_KIND", lower=True)
    return allowed_paths, denied_paths


def canonical_manifest(manifest: ScopeManifest) -> dict:
    allowed_paths, denied_paths = validate_manifest(manifest)
    return {
        "scope_id": manifest.scope_id.strip(),
        "owner_user_id": manifest.owner_user_id.strip(),
        "scope_version": manifest.scope_version.strip(),
        "authority_version": manifest.authority_version.strip(),
        "issued_at_ms": manifest.issued_at_ms,
        "starts_at_ms": manifest.starts_at_ms,
        "expires_at_ms": manifest.expires_at_ms,
        "active": manifest.active,
        "revoked": manifest.revoked,
        "allowed_path_prefixes": list(allowed_paths),
        "denied_path_prefixes": list(denied_paths),
        "allowed_hosts": list(_normalize_string_set(manifest.allowed_hosts, "ALLOWED_HOST", lower=True)),
        "allowed_users": list(_normalize_string_set(manifest.allowed_users, "ALLOWED_USER")),
        "allowed_actions": list(_normalize_string_set(manifest.allowed_actions, "ALLOWED_ACTION", lower=True)),
        "allowed_target_kinds": list(_normalize_string_set(manifest.allowed_target_kinds, "ALLOWED_TARGET_KIND", lower=True)),
        "human_confirm_actions": list(_normalize_string_set(manifest.human_confirm_actions, "HUMAN_CONFIRM_ACTION", lower=True)),
        "human_confirm_target_kinds": list(_normalize_string_set(manifest.human_confirm_target_kinds, "HUMAN_CONFIRM_TARGET_KIND", lower=True)),
        "max_targets_per_request": manifest.max_targets_per_request,
    }


def scope_fingerprint(manifest: ScopeManifest) -> str:
    return _fp(canonical_manifest(manifest))


def request_fingerprint(request: ScopeRequest) -> str:
    # Request is validated through the evaluator before this is used for authority-sensitive reuse.
    return _fp(asdict(request))


class TaskScopeBoundaryEnforcer:
    """Pure decision control. It never touches the target filesystem/network/process."""

    def __init__(self, manifest: ScopeManifest, *, enable_cache: bool = True):
        self._manifest = manifest
        self._enable_cache = bool(enable_cache)
        self._canonical = canonical_manifest(manifest)
        self._scope_fp = _fp(self._canonical)
        self._allowed_paths = tuple(self._canonical["allowed_path_prefixes"])
        self._denied_paths = tuple(self._canonical["denied_path_prefixes"])
        self._allowed_hosts = frozenset(self._canonical["allowed_hosts"])
        self._allowed_users = frozenset(self._canonical["allowed_users"])
        self._allowed_actions = frozenset(self._canonical["allowed_actions"])
        self._allowed_target_kinds = frozenset(self._canonical["allowed_target_kinds"])
        self._human_confirm_actions = frozenset(self._canonical["human_confirm_actions"])
        self._human_confirm_target_kinds = frozenset(self._canonical["human_confirm_target_kinds"])
        self._cache: dict[str, ScopeResult] = {}

    @property
    def scope_fingerprint(self) -> str:
        return self._scope_fp

    def evaluate(self, request: ScopeRequest) -> ScopeResult:
        try:
            normalized_path = _normalize_path(request.path)
            req_id = _clean_text(request.request_id, "REQUEST_ID")
            actor = _clean_text(request.actor_user_id, "ACTOR_USER_ID")
            action = _clean_text(request.action, "ACTION").lower()
            target_kind = _clean_text(request.target_kind, "TARGET_KIND").lower()
            host = _clean_text(request.host, "HOST").lower()
            target_user = _clean_text(request.target_user_id, "TARGET_USER_ID")
            scope_version = _clean_text(request.scope_version, "SCOPE_VERSION")
            authority_version = _clean_text(request.authority_version, "AUTHORITY_VERSION")
            context_fp = _clean_text(request.context_fingerprint, "CONTEXT_FINGERPRINT")
            if request.observed_at_ms < 0:
                raise ScopeValidationError("OBSERVED_TIME_NEGATIVE")
            if request.target_count < 1 or request.target_count > 100000:
                raise ScopeValidationError("TARGET_COUNT_INVALID")
        except ScopeValidationError as exc:
            return ScopeResult(
                decision=ScopeDecision.DENY,
                reasons=(str(exc),),
                scope_fingerprint=self._scope_fp,
                request_fingerprint="INVALID",
                path_normalized="",
                path_in_scope=False,
                host_in_scope=False,
                user_in_scope=False,
                action_in_scope=False,
                target_kind_in_scope=False,
                time_in_scope=False,
                version_match=False,
                connected_observed=bool(request.connection_available),
            )

        req_obj = {
            "request_id": req_id,
            "actor_user_id": actor,
            "observed_at_ms": request.observed_at_ms,
            "scope_version": scope_version,
            "authority_version": authority_version,
            "action": action,
            "target_kind": target_kind,
            "path": normalized_path,
            "host": host,
            "target_user_id": target_user,
            "target_count": request.target_count,
            "high_impact": bool(request.high_impact),
            "irreversible": bool(request.irreversible),
            "human_approval_evidence": bool(request.human_approval_evidence),
            "context_fingerprint": context_fp,
            "connection_available": bool(request.connection_available),
        }
        req_fp = _fp(req_obj)
        cache_key = _fp({"scope": self._scope_fp, "request": req_fp})
        if self._enable_cache and cache_key in self._cache:
            return self._cache[cache_key]

        reasons: list[str] = []
        version_match = scope_version == self._manifest.scope_version and authority_version == self._manifest.authority_version
        time_in_scope = self._manifest.starts_at_ms <= request.observed_at_ms <= self._manifest.expires_at_ms
        path_allowed = any(_path_under(normalized_path, p) for p in self._allowed_paths)
        path_denied = any(_path_under(normalized_path, p) for p in self._denied_paths)
        path_in_scope = path_allowed and not path_denied
        host_in_scope = host in self._allowed_hosts
        user_in_scope = target_user in self._allowed_users and actor in self._allowed_users
        action_in_scope = action in self._allowed_actions
        target_kind_in_scope = target_kind in self._allowed_target_kinds

        decision = ScopeDecision.ALLOW_CANDIDATE
        if not self._manifest.active:
            decision = ScopeDecision.DENY; reasons.append("SCOPE_INACTIVE")
        if self._manifest.revoked:
            decision = ScopeDecision.DENY; reasons.append("SCOPE_REVOKED")
        if not version_match and decision != ScopeDecision.DENY:
            decision = ScopeDecision.HOLD; reasons.append("SCOPE_OR_AUTHORITY_VERSION_MISMATCH")
        if not time_in_scope:
            decision = ScopeDecision.DENY; reasons.append("OUTSIDE_TIME_WINDOW")
        if not path_in_scope:
            decision = ScopeDecision.DENY; reasons.append("PATH_OUT_OF_SCOPE")
        if not host_in_scope:
            decision = ScopeDecision.DENY; reasons.append("HOST_OUT_OF_SCOPE")
        if not user_in_scope:
            decision = ScopeDecision.DENY; reasons.append("USER_OUT_OF_SCOPE")
        if not action_in_scope:
            decision = ScopeDecision.DENY; reasons.append("ACTION_OUT_OF_SCOPE")
        if not target_kind_in_scope:
            decision = ScopeDecision.DENY; reasons.append("TARGET_KIND_OUT_OF_SCOPE")
        if request.target_count > self._manifest.max_targets_per_request:
            decision = ScopeDecision.DENY; reasons.append("TARGET_COUNT_EXCEEDS_SCOPE")

        needs_human = (
            request.high_impact
            or request.irreversible
            or action in self._human_confirm_actions
            or target_kind in self._human_confirm_target_kinds
        )
        if decision == ScopeDecision.ALLOW_CANDIDATE and needs_human and not request.human_approval_evidence:
            decision = ScopeDecision.HUMAN_CONFIRM
            reasons.append("HUMAN_CONFIRM_REQUIRED")
        elif decision == ScopeDecision.ALLOW_CANDIDATE:
            reasons.append("WITHIN_SCOPE_CANDIDATE_ONLY")

        result = ScopeResult(
            decision=decision,
            reasons=tuple(reasons),
            scope_fingerprint=self._scope_fp,
            request_fingerprint=req_fp,
            path_normalized=normalized_path,
            path_in_scope=path_in_scope,
            host_in_scope=host_in_scope,
            user_in_scope=user_in_scope,
            action_in_scope=action_in_scope,
            target_kind_in_scope=target_kind_in_scope,
            time_in_scope=time_in_scope,
            version_match=version_match,
            connected_observed=bool(request.connection_available),
        )
        if self._enable_cache:
            self._cache[cache_key] = result
        return result


_PATCHABLE_LIST_FIELDS = (
    "allowed_path_prefixes", "denied_path_prefixes", "allowed_hosts", "allowed_users",
    "allowed_actions", "allowed_target_kinds", "human_confirm_actions", "human_confirm_target_kinds",
)


def manifest_delta(base: ScopeManifest, target: ScopeManifest) -> dict:
    b = canonical_manifest(base)
    t = canonical_manifest(target)
    scalar_changed = {}
    set_patches = {}
    for k, target_value in t.items():
        if b.get(k) == target_value:
            continue
        if k in _PATCHABLE_LIST_FIELDS:
            before = set(b.get(k, []))
            after = set(target_value)
            set_patches[k] = {"add": sorted(after - before), "remove": sorted(before - after)}
        else:
            scalar_changed[k] = target_value
    return {
        "base_fingerprint": _fp(b),
        "target_fingerprint": _fp(t),
        "scope_id": t["scope_id"],
        "base_scope_version": b["scope_version"],
        "target_scope_version": t["scope_version"],
        "scalar_changed": scalar_changed,
        "set_patches": set_patches,
    }


def apply_manifest_delta(base: ScopeManifest, delta: Mapping[str, object]) -> dict:
    b = canonical_manifest(base)
    if _fp(b) != delta.get("base_fingerprint"):
        raise ScopeValidationError("BASE_FINGERPRINT_MISMATCH")
    out = dict(b)
    scalar_changed = delta.get("scalar_changed")
    set_patches = delta.get("set_patches")
    if not isinstance(scalar_changed, Mapping) or not isinstance(set_patches, Mapping):
        raise ScopeValidationError("DELTA_CHANGED_INVALID")
    out.update(dict(scalar_changed))
    for field, patch in set_patches.items():
        if field not in _PATCHABLE_LIST_FIELDS or not isinstance(patch, Mapping):
            raise ScopeValidationError("DELTA_PATCH_INVALID")
        add = patch.get("add", [])
        remove = patch.get("remove", [])
        if not isinstance(add, list) or not isinstance(remove, list):
            raise ScopeValidationError("DELTA_PATCH_INVALID")
        current = set(out.get(field, []))
        current.difference_update(remove)
        current.update(add)
        out[field] = sorted(current)
    if _fp(out) != delta.get("target_fingerprint"):
        raise ScopeValidationError("TARGET_FINGERPRINT_MISMATCH")
    return out
