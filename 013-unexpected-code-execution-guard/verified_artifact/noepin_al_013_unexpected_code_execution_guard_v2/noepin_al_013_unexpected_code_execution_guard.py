from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Tuple
import hashlib, json, re, time

class ExecutionDecision(str, Enum):
    ALLOW_PREPARE = "ALLOW_PREPARE"
    HUMAN_CONFIRM = "HUMAN_CONFIRM"
    HOLD = "HOLD"
    DENY = "DENY"

class OriginKind(str, Enum):
    USER = "USER"
    GENERATED = "GENERATED"
    TOOL = "TOOL"
    FILE = "FILE"
    WEB = "WEB"
    EXTERNAL_AI = "EXTERNAL_AI"
    UNKNOWN = "UNKNOWN"

@dataclass(frozen=True)
class TypedAction:
    action_type: str
    operation: str
    target: str
    args_fingerprint: str
    code_sha256: Optional[str] = None
    requested_capabilities: Tuple[str, ...] = ()
    sandbox_required: bool = True
    sandbox_id: Optional[str] = None
    origin: OriginKind = OriginKind.GENERATED
    raw_shell_requested: bool = False
    dynamic_eval_requested: bool = False
    process_spawn_requested: bool = False
    network_requested: bool = False
    filesystem_write_requested: bool = False
    protected_target: bool = False
    external_side_effect: bool = False
    risk_score: int = 0
    schema_version: str = "1"
    metadata: Mapping[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class ExecutionPolicy:
    allowed_action_types: Tuple[str, ...]
    allowed_operations: Tuple[str, ...]
    allowed_capabilities: Tuple[str, ...]
    forbidden_operations: Tuple[str, ...] = ("exec_raw", "eval", "shell_raw", "privilege_escalation")
    require_sandbox_for_generated: bool = True
    require_human_for_process_spawn: bool = True
    require_human_for_network: bool = True
    require_human_for_filesystem_write: bool = True
    max_risk_without_confirmation: int = 35
    policy_version: str = "1"

@dataclass(frozen=True)
class ExecutionRequest:
    request_id: str
    actor_id: str
    action: TypedAction
    human_approved: bool = False
    approval_ref: Optional[str] = None
    capability_authorized: bool = False
    authorization_ref: Optional[str] = None
    observed_policy_version: Optional[str] = None
    schema_version: str = "1"
    context: Mapping[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class ExecutionGuardResult:
    decision: ExecutionDecision
    reason_codes: Tuple[str, ...]
    request_fingerprint: str
    typed_action_valid: bool
    sandbox_validated: bool
    capability_validated: bool
    authoritative: bool = False
    code_executed: bool = False
    action_succeeded: bool = False
    state_committed: bool = False
    cache_reused: bool = False
    created_unix_ns: int = 0

    def stable_payload(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reason_codes": list(self.reason_codes),
            "request_fingerprint": self.request_fingerprint,
            "typed_action_valid": self.typed_action_valid,
            "sandbox_validated": self.sandbox_validated,
            "capability_validated": self.capability_validated,
            "authoritative": self.authoritative,
            "code_executed": self.code_executed,
            "action_succeeded": self.action_succeeded,
            "state_committed": self.state_committed,
            "cache_reused": self.cache_reused,
        }

class UnexpectedCodeExecutionGuard:
    """
    NOEPIN AL 013 — Unexpected Code Execution Guard.

    Validates a typed action generated from natural language/code.
    It NEVER executes shell/code/process/network/filesystem operations itself.

    Invariants:
      Generated text != Executable command
      Code candidate != Approved Typed Action
      Typed Action validation != Execution success
      Capability declaration != Capability authorization
      Human approval evidence != Execution
      Sandbox selection != Sandbox containment proof
      Cached allow != New authority
      Partial/provisional state != committed state
    """

    def __init__(self, policy: ExecutionPolicy, *, enable_exact_state_cache: bool = True) -> None:
        if not policy.allowed_action_types or not policy.allowed_operations or not policy.policy_version:
            raise ValueError("policy allowlists and policy_version are required")
        self.policy = policy
        self.enable_exact_state_cache = bool(enable_exact_state_cache)
        self._cache: Dict[Tuple[str, str], ExecutionGuardResult] = {}

    @staticmethod
    def _norm(v: Any) -> Any:
        if isinstance(v, Mapping):
            return {str(k): UnexpectedCodeExecutionGuard._norm(v[k]) for k in sorted(v, key=lambda x: str(x))}
        if isinstance(v, (list, tuple)):
            return [UnexpectedCodeExecutionGuard._norm(x) for x in v]
        if isinstance(v, set):
            return sorted(UnexpectedCodeExecutionGuard._norm(x) for x in v)
        if isinstance(v, Enum):
            return v.value
        if v is None or isinstance(v, (str, int, float, bool)):
            return v
        return str(v)

    @classmethod
    def fingerprint(cls, request: ExecutionRequest) -> str:
        raw = json.dumps(cls._norm(asdict(request)), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _valid_hash(v: Optional[str], allow_none: bool=False) -> bool:
        if v is None:
            return allow_none
        if not isinstance(v, str) or len(v) != 64:
            return False
        try:
            int(v, 16)
            return True
        except ValueError:
            return False

    @staticmethod
    def _valid_risk(v: Any) -> bool:
        return isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 100

    def _make(self, decision, reasons, fp, typed_ok, sandbox_ok, cap_ok):
        return ExecutionGuardResult(
            decision=decision,
            reason_codes=tuple(reasons),
            request_fingerprint=fp,
            typed_action_valid=bool(typed_ok),
            sandbox_validated=bool(sandbox_ok),
            capability_validated=bool(cap_ok),
            authoritative=False,
            code_executed=False,
            action_succeeded=False,
            state_committed=False,
            cache_reused=False,
            created_unix_ns=time.time_ns(),
        )

    def _evaluate_uncached(self, request: ExecutionRequest) -> ExecutionGuardResult:
        fp = self.fingerprint(request)
        a = request.action

        if not request.request_id or not request.actor_id or not request.schema_version:
            return self._make(ExecutionDecision.HOLD, ("MISSING_REQUEST_FIELD",), fp, False, False, False)
        if request.observed_policy_version is not None and request.observed_policy_version != self.policy.policy_version:
            return self._make(ExecutionDecision.HOLD, ("POLICY_VERSION_MISMATCH",), fp, False, False, False)
        if not a.action_type or not a.operation or not a.target or not a.schema_version:
            return self._make(ExecutionDecision.HOLD, ("MISSING_TYPED_ACTION_FIELD",), fp, False, False, False)
        if not self._valid_hash(a.args_fingerprint):
            return self._make(ExecutionDecision.HOLD, ("INVALID_ARGS_FINGERPRINT",), fp, False, False, False)
        if not self._valid_hash(a.code_sha256, allow_none=True):
            return self._make(ExecutionDecision.HOLD, ("INVALID_CODE_HASH",), fp, False, False, False)
        if not self._valid_risk(a.risk_score):
            return self._make(ExecutionDecision.HOLD, ("INVALID_RISK_SCORE",), fp, False, False, False)

        if a.action_type not in set(self.policy.allowed_action_types):
            return self._make(ExecutionDecision.DENY, ("ACTION_TYPE_NOT_ALLOWLISTED",), fp, False, False, False)
        if a.operation in set(self.policy.forbidden_operations):
            return self._make(ExecutionDecision.DENY, ("FORBIDDEN_OPERATION",), fp, True, False, False)
        if a.operation not in set(self.policy.allowed_operations):
            return self._make(ExecutionDecision.DENY, ("OPERATION_NOT_ALLOWLISTED",), fp, True, False, False)
        if a.protected_target:
            return self._make(ExecutionDecision.DENY, ("PROTECTED_TARGET",), fp, True, False, False)

        # Direct/raw execution primitives are always denied.
        if a.raw_shell_requested:
            return self._make(ExecutionDecision.DENY, ("RAW_SHELL_EXECUTION_DENIED",), fp, True, False, False)
        if a.dynamic_eval_requested:
            return self._make(ExecutionDecision.DENY, ("DYNAMIC_EVAL_DENIED",), fp, True, False, False)

        requested = set(a.requested_capabilities)
        allowed = set(self.policy.allowed_capabilities)
        if not requested.issubset(allowed):
            return self._make(ExecutionDecision.DENY, ("CAPABILITY_NOT_ALLOWLISTED",), fp, True, False, False)
        if requested and not (request.capability_authorized and request.authorization_ref):
            return self._make(ExecutionDecision.HOLD, ("CAPABILITY_AUTHORIZATION_REQUIRED",), fp, True, False, False)
        cap_ok = (not requested) or bool(request.capability_authorized and request.authorization_ref)

        generated = a.origin in {OriginKind.GENERATED, OriginKind.TOOL, OriginKind.FILE, OriginKind.WEB, OriginKind.EXTERNAL_AI, OriginKind.UNKNOWN}
        if generated and self.policy.require_sandbox_for_generated:
            if not a.sandbox_required or not a.sandbox_id:
                return self._make(ExecutionDecision.HOLD, ("GENERATED_ACTION_REQUIRES_SANDBOX",), fp, True, False, cap_ok)
        sandbox_ok = (not generated) or bool(a.sandbox_required and a.sandbox_id)

        needs_human = False
        reasons = []
        if a.process_spawn_requested and self.policy.require_human_for_process_spawn:
            needs_human = True; reasons.append("PROCESS_SPAWN_REQUIRES_HUMAN_CONFIRMATION")
        if a.network_requested and self.policy.require_human_for_network:
            needs_human = True; reasons.append("NETWORK_REQUIRES_HUMAN_CONFIRMATION")
        if a.filesystem_write_requested and self.policy.require_human_for_filesystem_write:
            needs_human = True; reasons.append("FILESYSTEM_WRITE_REQUIRES_HUMAN_CONFIRMATION")
        if a.external_side_effect:
            needs_human = True; reasons.append("EXTERNAL_SIDE_EFFECT_REQUIRES_HUMAN_CONFIRMATION")
        if a.risk_score > self.policy.max_risk_without_confirmation:
            needs_human = True; reasons.append("RISK_REQUIRES_HUMAN_CONFIRMATION")

        if needs_human and not (request.human_approved and request.approval_ref):
            return self._make(ExecutionDecision.HUMAN_CONFIRM, tuple(reasons), fp, True, sandbox_ok, cap_ok)

        return self._make(
            ExecutionDecision.ALLOW_PREPARE,
            tuple(reasons) if reasons else ("TYPED_ACTION_VALID_PREPARE_ONLY",),
            fp, True, sandbox_ok, cap_ok
        )

    def evaluate(self, request: ExecutionRequest) -> ExecutionGuardResult:
        fp = self.fingerprint(request)
        key = (fp, self.policy.policy_version)
        if self.enable_exact_state_cache and key in self._cache:
            r = self._cache[key]
            return ExecutionGuardResult(
                decision=r.decision, reason_codes=r.reason_codes, request_fingerprint=fp,
                typed_action_valid=r.typed_action_valid, sandbox_validated=r.sandbox_validated,
                capability_validated=r.capability_validated, authoritative=False, code_executed=False,
                action_succeeded=False, state_committed=False, cache_reused=True, created_unix_ns=time.time_ns()
            )
        result = self._evaluate_uncached(request)
        if self.enable_exact_state_cache:
            self._cache[key] = result
        return result

    def clear_cache(self) -> None:
        self._cache.clear()

    def cache_size(self) -> int:
        return len(self._cache)
