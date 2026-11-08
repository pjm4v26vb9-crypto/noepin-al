from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Tuple
import hashlib
import json
import math
import re

__version__ = "2.0.0-successor.20261102"
CREATOR = "NOEPIN / のえぴん"


class Decision(str, Enum):
    TYPED_CANDIDATE = "TYPED_CANDIDATE"
    HOLD = "HOLD"
    DENY = "DENY"


class ActionType(str, Enum):
    TOOL_REQUEST = "TOOL_REQUEST"
    DATA_QUERY = "DATA_QUERY"
    FILE_READ = "FILE_READ"
    NETWORK_REQUEST = "NETWORK_REQUEST"
    UI_REQUEST = "UI_REQUEST"


_ALLOWED_TOP = {"version", "action_type", "operation", "target", "purpose", "args", "risk"}
_ALLOWED_RISK = {"external_side_effect", "destructive", "high_privilege", "irreversible"}
_FORBIDDEN_ACTION_TYPES = {"SHELL", "EXEC", "EVAL", "PYTHON_EVAL", "PROCESS_SPAWN", "RAW_COMMAND"}
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_.:/-]{1,160}$")


@dataclass(frozen=True)
class ConversionPolicy:
    policy_version: str = "NOEPIN-AL-024-POLICY-V2"
    max_input_bytes: int = 16384
    max_depth: int = 6
    max_container_items: int = 128
    max_string_length: int = 4096
    max_args_keys: int = 64
    require_purpose: bool = True


@dataclass(frozen=True)
class TypedAction:
    schema_version: str
    action_type: str
    operation: str
    target: str
    purpose: str
    args: Dict[str, Any]
    risk: Dict[str, bool]
    candidate_fingerprint: str


@dataclass(frozen=True)
class ConversionResult:
    decision: str
    reason: str
    typed_action: Optional[TypedAction]
    schema_valid: bool
    authorized: bool = False
    executed: bool = False
    succeeded: bool = False
    committed: bool = False
    from_cache: bool = False

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


class DuplicateKeyError(ValueError):
    pass


def _reject_duplicate_pairs(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise DuplicateKeyError(f"duplicate key: {k}")
        d[k] = v
    return d


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _fingerprint(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _validate_tree(value: Any, policy: ConversionPolicy, depth: int = 0) -> Optional[str]:
    if depth > policy.max_depth:
        return "MAX_DEPTH_EXCEEDED"
    if value is None or isinstance(value, (bool, int)):
        return None
    if isinstance(value, float):
        if not math.isfinite(value):
            return "NON_FINITE_NUMBER"
        return None
    if isinstance(value, str):
        if len(value) > policy.max_string_length:
            return "STRING_TOO_LONG"
        if _CONTROL_RE.search(value):
            return "CONTROL_CHARACTER"
        return None
    if isinstance(value, list):
        if len(value) > policy.max_container_items:
            return "TOO_MANY_ITEMS"
        for item in value:
            err = _validate_tree(item, policy, depth + 1)
            if err:
                return err
        return None
    if isinstance(value, dict):
        if len(value) > policy.max_container_items:
            return "TOO_MANY_KEYS"
        for k, v in value.items():
            if not isinstance(k, str):
                return "NON_STRING_KEY"
            if len(k) > 128 or _CONTROL_RE.search(k):
                return "INVALID_KEY"
            err = _validate_tree(v, policy, depth + 1)
            if err:
                return err
        return None
    return "UNSUPPORTED_TYPE"


class TypedActionConverter:
    """Strictly converts a complete JSON candidate into a non-authoritative TypedAction.

    It never invokes tools, shell, network, files, processes, or commits state.
    """

    def __init__(self, policy: ConversionPolicy | None = None, enable_cache: bool = True):
        self.policy = policy or ConversionPolicy()
        self.enable_cache = enable_cache
        self._cache: Dict[str, ConversionResult] = {}

    def _cache_key(self, raw: str) -> str:
        return _fingerprint({"policy": asdict(self.policy), "raw": raw})

    def convert(self, raw: str) -> ConversionResult:
        if not isinstance(raw, str):
            return self._deny("INPUT_MUST_BE_STRING")
        if len(raw.encode("utf-8")) > self.policy.max_input_bytes:
            return self._deny("INPUT_TOO_LARGE")
        if not raw.strip():
            return self._deny("EMPTY_INPUT")

        key = self._cache_key(raw)
        if self.enable_cache and key in self._cache:
            cached = self._cache[key]
            return ConversionResult(**{**cached.to_dict(), "from_cache": True})

        try:
            obj = json.loads(raw, object_pairs_hook=_reject_duplicate_pairs, parse_constant=lambda x: (_ for _ in ()).throw(ValueError("non-finite")))
        except DuplicateKeyError:
            result = self._deny("DUPLICATE_KEY")
            return self._store(key, result)
        except Exception:
            result = self._deny("INVALID_JSON_OR_NON_JSON_WRAPPER")
            return self._store(key, result)

        if not isinstance(obj, dict):
            result = self._deny("TOP_LEVEL_OBJECT_REQUIRED")
            return self._store(key, result)

        tree_error = _validate_tree(obj, self.policy)
        if tree_error:
            result = self._deny(tree_error)
            return self._store(key, result)

        unknown = set(obj) - _ALLOWED_TOP
        if unknown:
            result = self._deny("UNKNOWN_TOP_LEVEL_FIELD")
            return self._store(key, result)

        required = {"version", "action_type", "operation", "target", "args"}
        if self.policy.require_purpose:
            required.add("purpose")
        if not required.issubset(obj):
            result = self._deny("MISSING_REQUIRED_FIELD")
            return self._store(key, result)

        if obj.get("version") != "1":
            result = self._deny("UNSUPPORTED_SCHEMA_VERSION")
            return self._store(key, result)

        action_type = obj.get("action_type")
        if not isinstance(action_type, str):
            result = self._deny("ACTION_TYPE_MUST_BE_STRING")
            return self._store(key, result)
        if action_type in _FORBIDDEN_ACTION_TYPES:
            result = self._deny("FORBIDDEN_ACTION_TYPE")
            return self._store(key, result)
        if action_type not in {x.value for x in ActionType}:
            result = self._deny("UNKNOWN_ACTION_TYPE")
            return self._store(key, result)

        operation = obj.get("operation")
        target = obj.get("target")
        purpose = obj.get("purpose", "")
        if not isinstance(operation, str) or not _IDENTIFIER_RE.fullmatch(operation):
            result = self._deny("INVALID_OPERATION")
            return self._store(key, result)
        if not isinstance(target, str) or not target.strip() or len(target) > 512 or _CONTROL_RE.search(target):
            result = self._deny("INVALID_TARGET")
            return self._store(key, result)
        if not isinstance(purpose, str) or not purpose.strip() or len(purpose) > 512 or _CONTROL_RE.search(purpose):
            result = self._deny("INVALID_PURPOSE")
            return self._store(key, result)

        args = obj.get("args")
        if not isinstance(args, dict):
            result = self._deny("ARGS_MUST_BE_OBJECT")
            return self._store(key, result)
        if len(args) > self.policy.max_args_keys:
            result = self._deny("TOO_MANY_ARGS")
            return self._store(key, result)

        risk = obj.get("risk", {})
        if not isinstance(risk, dict):
            result = self._deny("RISK_MUST_BE_OBJECT")
            return self._store(key, result)
        if set(risk) - _ALLOWED_RISK:
            result = self._deny("UNKNOWN_RISK_FIELD")
            return self._store(key, result)
        normalized_risk = {k: bool(risk.get(k, False)) for k in sorted(_ALLOWED_RISK)}
        if any(k in risk and not isinstance(risk[k], bool) for k in risk):
            result = self._deny("RISK_VALUES_MUST_BE_BOOL")
            return self._store(key, result)

        # Conversion is intentionally semantic-minimal: no guessed defaults except false risk flags.
        typed_payload = {
            "schema_version": "1",
            "action_type": action_type,
            "operation": operation,
            "target": target.strip(),
            "purpose": purpose.strip(),
            "args": args,
            "risk": normalized_risk,
        }
        candidate = TypedAction(**typed_payload, candidate_fingerprint=_fingerprint(typed_payload))
        result = ConversionResult(
            decision=Decision.TYPED_CANDIDATE.value,
            reason="STRICT_SCHEMA_VALIDATED_DOWNSTREAM_AUTHORIZATION_REQUIRED",
            typed_action=candidate,
            schema_valid=True,
        )
        return self._store(key, result)

    def _store(self, key: str, result: ConversionResult) -> ConversionResult:
        if self.enable_cache:
            self._cache[key] = result
        return result

    @staticmethod
    def _deny(reason: str) -> ConversionResult:
        return ConversionResult(
            decision=Decision.DENY.value,
            reason=reason,
            typed_action=None,
            schema_valid=False,
        )


def conversion_fingerprint(result: ConversionResult) -> str:
    return _fingerprint(result.to_dict())


__all__ = [
    "ActionType", "ConversionPolicy", "ConversionResult", "Decision",
    "TypedAction", "TypedActionConverter", "conversion_fingerprint"
]
