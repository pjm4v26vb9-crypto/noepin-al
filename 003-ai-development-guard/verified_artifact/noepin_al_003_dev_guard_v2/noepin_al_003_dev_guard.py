from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import PurePosixPath
from typing import Any, Dict, Mapping, Optional, Tuple
import hashlib
import json
import re
import time


class GuardDecision(str, Enum):
    ALLOW_PREPARE = "ALLOW_PREPARE"
    DENY = "DENY"
    HOLD = "HOLD"
    HUMAN_CONFIRM = "HUMAN_CONFIRM"


class Operation(str, Enum):
    READ = "READ"
    CREATE = "CREATE"
    MODIFY = "MODIFY"
    DELETE = "DELETE"
    RENAME = "RENAME"
    EXECUTE = "EXECUTE"


@dataclass(frozen=True)
class DevelopmentPolicy:
    allowed_roots: Tuple[str, ...]
    protected_prefixes: Tuple[str, ...] = ()
    executable_roots: Tuple[str, ...] = ()
    require_successor_for_modify: bool = True
    require_rollback_for_destructive: bool = True
    require_human_for_delete: bool = True
    require_human_for_overwrite: bool = True
    max_diff_bytes_without_confirmation: int = 262144
    policy_version: str = "1"


@dataclass(frozen=True)
class DevelopmentRequest:
    operation: Operation
    target_path: str
    actor_id: str
    target_exists: bool = False
    overwrite_existing: bool = False
    successor_path: Optional[str] = None
    rollback_ref: Optional[str] = None
    source_sha256: Optional[str] = None
    proposed_sha256: Optional[str] = None
    diff_sha256: Optional[str] = None
    diff_bytes: int = 0
    human_approved: bool = False
    approval_ref: Optional[str] = None
    external_side_effect: bool = False
    requested_execution: bool = False
    context: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = "1"


@dataclass(frozen=True)
class GuardResult:
    decision: GuardDecision
    reason_codes: Tuple[str, ...]
    request_fingerprint: str
    canonical_target: Optional[str]
    canonical_successor: Optional[str]
    authoritative: bool = False
    action_executed: bool = False
    commit_performed: bool = False
    cache_reused: bool = False
    created_unix_ns: int = 0

    def stable_payload(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reason_codes": list(self.reason_codes),
            "request_fingerprint": self.request_fingerprint,
            "canonical_target": self.canonical_target,
            "canonical_successor": self.canonical_successor,
            "authoritative": self.authoritative,
            "action_executed": self.action_executed,
            "commit_performed": self.commit_performed,
            "cache_reused": self.cache_reused,
        }


class DevelopmentGuard:
    """
    NOEPIN AL 003 — AI Development Guard.

    This component validates a proposed development/file operation.
    It NEVER edits, deletes, renames, executes, or commits a file itself.

    Authority invariants:
      Guard ALLOW_PREPARE != Action Success
      Human approval evidence != operation execution
      Prepared change != committed change
      Cached decision != new authority
      Partial/provisional state != safe published state
    """

    _DRIVE_RE = re.compile(r"^[A-Za-z]:")

    def __init__(self, policy: DevelopmentPolicy, *, enable_exact_state_cache: bool = True) -> None:
        if not policy.allowed_roots:
            raise ValueError("at least one allowed root is required")
        if not policy.policy_version:
            raise ValueError("policy_version is required")
        self.policy = policy
        self.enable_exact_state_cache = bool(enable_exact_state_cache)
        self._cache: Dict[Tuple[str, str], GuardResult] = {}

        self._allowed_roots = tuple(self._canonical_policy_path(x) for x in policy.allowed_roots)
        self._protected_prefixes = tuple(self._canonical_policy_path(x) for x in policy.protected_prefixes)
        self._executable_roots = tuple(self._canonical_policy_path(x) for x in policy.executable_roots)

    @staticmethod
    def _canonical_policy_path(path: str) -> str:
        value = (path or "").replace("\\", "/").strip()
        if not value:
            raise ValueError("empty policy path")
        if value.startswith("/") or DevelopmentGuard._DRIVE_RE.match(value):
            raise ValueError("policy paths must be project-relative")
        parts = []
        for p in value.split("/"):
            if p in ("", "."):
                continue
            if p == "..":
                raise ValueError("policy path cannot contain parent traversal")
            parts.append(p)
        if not parts:
            raise ValueError("empty policy path")
        return "/".join(parts)

    @staticmethod
    def canonicalize_request_path(path: str) -> Optional[str]:
        value = (path or "").replace("\\", "/").strip()
        if not value or "\x00" in value:
            return None
        if value.startswith("/") or DevelopmentGuard._DRIVE_RE.match(value):
            return None
        parts = []
        for p in value.split("/"):
            if p in ("", "."):
                continue
            if p == "..":
                return None
            parts.append(p)
        if not parts:
            return None
        return "/".join(parts)

    @staticmethod
    def _under(path: str, prefix: str) -> bool:
        return path == prefix or path.startswith(prefix + "/")

    @staticmethod
    def _is_hex_sha256(value: Optional[str]) -> bool:
        return value is not None and bool(re.fullmatch(r"[0-9a-fA-F]{64}", value))

    @staticmethod
    def _normalize(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {str(k): DevelopmentGuard._normalize(value[k]) for k in sorted(value, key=lambda x: str(x))}
        if isinstance(value, (list, tuple)):
            return [DevelopmentGuard._normalize(v) for v in value]
        if isinstance(value, set):
            return sorted(DevelopmentGuard._normalize(v) for v in value)
        if isinstance(value, Enum):
            return value.value
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        return str(value)

    @classmethod
    def fingerprint_request(cls, request: DevelopmentRequest) -> str:
        payload = cls._normalize(asdict(request))
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def _is_allowed(self, path: str) -> bool:
        return any(self._under(path, root) for root in self._allowed_roots)

    def _is_protected(self, path: str) -> bool:
        return any(self._under(path, prefix) for prefix in self._protected_prefixes)

    def _is_executable_root(self, path: str) -> bool:
        return any(self._under(path, root) for root in self._executable_roots)

    def _evaluate_uncached(
        self, request: DevelopmentRequest, target: Optional[str], successor: Optional[str]
    ) -> Tuple[GuardDecision, Tuple[str, ...]]:
        if not request.actor_id or not request.schema_version:
            return GuardDecision.HOLD, ("MISSING_ACTOR_OR_SCHEMA",)

        if target is None:
            return GuardDecision.DENY, ("INVALID_OR_TRAVERSAL_TARGET_PATH",)

        if not isinstance(request.diff_bytes, int) or isinstance(request.diff_bytes, bool) or request.diff_bytes < 0:
            return GuardDecision.HOLD, ("INVALID_DIFF_SIZE",)

        if not self._is_allowed(target):
            return GuardDecision.DENY, ("TARGET_OUTSIDE_ALLOWED_ROOT",)

        if self._is_protected(target):
            return GuardDecision.DENY, ("PROTECTED_TARGET",)

        if request.source_sha256 is not None and not self._is_hex_sha256(request.source_sha256):
            return GuardDecision.HOLD, ("INVALID_SOURCE_HASH",)
        if request.proposed_sha256 is not None and not self._is_hex_sha256(request.proposed_sha256):
            return GuardDecision.HOLD, ("INVALID_PROPOSED_HASH",)
        if request.diff_sha256 is not None and not self._is_hex_sha256(request.diff_sha256):
            return GuardDecision.HOLD, ("INVALID_DIFF_HASH",)

        if request.operation == Operation.READ:
            if request.requested_execution:
                return GuardDecision.DENY, ("READ_REQUEST_CANNOT_EXECUTE",)
            return GuardDecision.ALLOW_PREPARE, ("READ_WITHIN_ALLOWED_ROOT",)

        if request.operation == Operation.CREATE:
            if request.target_exists or request.overwrite_existing:
                if not request.human_approved or not request.approval_ref:
                    return GuardDecision.HUMAN_CONFIRM, ("CREATE_WOULD_OVERWRITE_EXISTING",)
            if request.proposed_sha256 is None:
                return GuardDecision.HOLD, ("MISSING_PROPOSED_HASH",)
            if request.external_side_effect:
                return GuardDecision.HUMAN_CONFIRM, ("EXTERNAL_SIDE_EFFECT_REQUIRES_CONFIRMATION",)
            return GuardDecision.ALLOW_PREPARE, ("CREATE_CANDIDATE_ALLOWED",)

        if request.operation == Operation.MODIFY:
            if not request.target_exists:
                return GuardDecision.HOLD, ("MODIFY_TARGET_NOT_CONFIRMED_EXISTING",)
            if request.source_sha256 is None or request.proposed_sha256 is None or request.diff_sha256 is None:
                return GuardDecision.HOLD, ("MODIFY_REQUIRES_SOURCE_PROPOSED_AND_DIFF_HASH",)
            if request.source_sha256 == request.proposed_sha256:
                return GuardDecision.HOLD, ("NO_EFFECT_CHANGE",)

            if self.policy.require_successor_for_modify:
                if successor is None:
                    return GuardDecision.HOLD, ("VERSIONED_SUCCESSOR_REQUIRED",)
                if successor == target:
                    return GuardDecision.DENY, ("IN_PLACE_OVERWRITE_FORBIDDEN",)
                if not self._is_allowed(successor):
                    return GuardDecision.DENY, ("SUCCESSOR_OUTSIDE_ALLOWED_ROOT",)
                if self._is_protected(successor):
                    return GuardDecision.DENY, ("SUCCESSOR_IS_PROTECTED",)

            if request.overwrite_existing and self.policy.require_human_for_overwrite:
                if not request.human_approved or not request.approval_ref:
                    return GuardDecision.HUMAN_CONFIRM, ("OVERWRITE_REQUIRES_HUMAN_CONFIRMATION",)

            if request.diff_bytes > self.policy.max_diff_bytes_without_confirmation:
                if not request.human_approved or not request.approval_ref:
                    return GuardDecision.HUMAN_CONFIRM, ("LARGE_DIFF_REQUIRES_HUMAN_CONFIRMATION",)

            if request.external_side_effect:
                return GuardDecision.HUMAN_CONFIRM, ("EXTERNAL_SIDE_EFFECT_REQUIRES_CONFIRMATION",)

            return GuardDecision.ALLOW_PREPARE, ("VERSIONED_SUCCESSOR_PREPARED",)

        if request.operation == Operation.DELETE:
            if self.policy.require_rollback_for_destructive and not request.rollback_ref:
                return GuardDecision.HOLD, ("DELETE_REQUIRES_ROLLBACK_REF",)
            if self.policy.require_human_for_delete and (not request.human_approved or not request.approval_ref):
                return GuardDecision.HUMAN_CONFIRM, ("DELETE_REQUIRES_HUMAN_CONFIRMATION",)
            return GuardDecision.ALLOW_PREPARE, ("DELETE_PREPARED_NOT_EXECUTED",)

        if request.operation == Operation.RENAME:
            if successor is None:
                return GuardDecision.HOLD, ("RENAME_DESTINATION_REQUIRED",)
            if successor == target:
                return GuardDecision.HOLD, ("RENAME_DESTINATION_EQUALS_SOURCE",)
            if not self._is_allowed(successor):
                return GuardDecision.DENY, ("RENAME_DESTINATION_OUTSIDE_ALLOWED_ROOT",)
            if self._is_protected(successor):
                return GuardDecision.DENY, ("RENAME_DESTINATION_PROTECTED",)
            if self.policy.require_rollback_for_destructive and not request.rollback_ref:
                return GuardDecision.HOLD, ("RENAME_REQUIRES_ROLLBACK_REF",)
            if not request.human_approved or not request.approval_ref:
                return GuardDecision.HUMAN_CONFIRM, ("RENAME_REQUIRES_HUMAN_CONFIRMATION",)
            return GuardDecision.ALLOW_PREPARE, ("RENAME_PREPARED_NOT_EXECUTED",)

        if request.operation == Operation.EXECUTE:
            if not self._is_executable_root(target):
                return GuardDecision.DENY, ("EXECUTION_OUTSIDE_EXECUTABLE_ROOT",)
            if not request.requested_execution:
                return GuardDecision.HOLD, ("EXECUTION_INTENT_NOT_EXPLICIT",)
            if not request.human_approved or not request.approval_ref:
                return GuardDecision.HUMAN_CONFIRM, ("EXECUTION_REQUIRES_HUMAN_CONFIRMATION",)
            return GuardDecision.ALLOW_PREPARE, ("EXECUTION_PREPARED_NOT_EXECUTED",)

        return GuardDecision.HOLD, ("UNKNOWN_OPERATION",)

    def evaluate(self, request: DevelopmentRequest) -> GuardResult:
        fp = self.fingerprint_request(request)
        target = self.canonicalize_request_path(request.target_path)
        successor = self.canonicalize_request_path(request.successor_path) if request.successor_path else None
        key = (fp, self.policy.policy_version)

        if self.enable_exact_state_cache and key in self._cache:
            c = self._cache[key]
            return GuardResult(
                decision=c.decision,
                reason_codes=c.reason_codes,
                request_fingerprint=fp,
                canonical_target=target,
                canonical_successor=successor,
                authoritative=False,
                action_executed=False,
                commit_performed=False,
                cache_reused=True,
                created_unix_ns=time.time_ns(),
            )

        decision, reasons = self._evaluate_uncached(request, target, successor)
        result = GuardResult(
            decision=decision,
            reason_codes=reasons,
            request_fingerprint=fp,
            canonical_target=target,
            canonical_successor=successor,
            authoritative=False,
            action_executed=False,
            commit_performed=False,
            cache_reused=False,
            created_unix_ns=time.time_ns(),
        )
        if self.enable_exact_state_cache:
            self._cache[key] = result
        return result

    def cache_size(self) -> int:
        return len(self._cache)

    def clear_cache(self) -> None:
        self._cache.clear()
