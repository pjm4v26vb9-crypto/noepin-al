from __future__ import annotations

import copy
import hashlib
import json
import math
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple


CREATOR = "NOEPIN / のえぴん"
VERSION = "2.0.0-successor.20261102"


class SnapshotMode(str, Enum):
    FULL = "FULL"
    DELTA = "DELTA"


class SnapshotDecision(str, Enum):
    SNAPSHOT_PREPARE = "SNAPSHOT_PREPARE"
    ROLLBACK_PREPARE = "ROLLBACK_PREPARE"
    HOLD = "HOLD"
    DENY = "DENY"


class SnapshotError(ValueError):
    pass


@dataclass(frozen=True)
class SnapshotPolicy:
    policy_version: str = "snapshot-policy-v2"
    max_depth: int = 32
    max_nodes: int = 50000
    max_delta_ratio: float = 0.35
    require_target_version: bool = True
    require_base_match_for_delta: bool = True


@dataclass(frozen=True)
class SnapshotRequest:
    request_id: str
    target_ref: str
    target_version: str
    current_state: Mapping[str, Any]
    previous_state: Optional[Mapping[str, Any]] = None
    previous_snapshot_id: Optional[str] = None
    previous_snapshot_fingerprint: Optional[str] = None
    reason: str = "pre_action"
    context: str = ""


@dataclass(frozen=True)
class SnapshotPlan:
    decision: SnapshotDecision
    reasons: Tuple[str, ...]
    mode: Optional[SnapshotMode]
    snapshot_id: Optional[str]
    target_ref: str
    target_version: str
    base_snapshot_id: Optional[str]
    base_fingerprint: Optional[str]
    state_fingerprint: Optional[str]
    checkpoint_fingerprint: Optional[str]
    full_state: Optional[Mapping[str, Any]]
    delta: Tuple[Tuple[str, str, Any], ...]
    authoritative: bool = False
    snapshot_persisted: bool = False
    rollback_executed: bool = False
    rollback_succeeded: bool = False
    state_committed: bool = False


@dataclass(frozen=True)
class RollbackRequest:
    request_id: str
    target_ref: str
    current_target_version: str
    current_state: Mapping[str, Any]
    snapshot_plan: SnapshotPlan
    base_state: Optional[Mapping[str, Any]] = None
    expected_snapshot_id: Optional[str] = None
    context: str = ""


@dataclass(frozen=True)
class RollbackPlan:
    decision: SnapshotDecision
    reasons: Tuple[str, ...]
    target_ref: str
    current_target_version: str
    snapshot_id: Optional[str]
    restored_candidate: Optional[Mapping[str, Any]]
    restored_fingerprint: Optional[str]
    authoritative: bool = False
    rollback_executed: bool = False
    rollback_succeeded: bool = False
    state_committed: bool = False


def _canonicalize(value: Any, *, depth: int = 0, max_depth: int = 32, counter: Optional[List[int]] = None, max_nodes: int = 50000) -> Any:
    if counter is None:
        counter = [0]
    counter[0] += 1
    if counter[0] > max_nodes:
        raise SnapshotError("state exceeds max_nodes")
    if depth > max_depth:
        raise SnapshotError("state exceeds max_depth")
    if value is None or isinstance(value, (bool, str, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise SnapshotError("non-finite float not allowed")
        return value
    if isinstance(value, Mapping):
        out: Dict[str, Any] = {}
        for k in sorted(value.keys(), key=lambda x: str(x)):
            if not isinstance(k, str):
                raise SnapshotError("mapping keys must be strings")
            out[k] = _canonicalize(value[k], depth=depth + 1, max_depth=max_depth, counter=counter, max_nodes=max_nodes)
        return out
    if isinstance(value, (list, tuple)):
        return [_canonicalize(v, depth=depth + 1, max_depth=max_depth, counter=counter, max_nodes=max_nodes) for v in value]
    raise SnapshotError(f"unsupported value type: {type(value).__name__}")


def canonical_json(value: Any, policy: SnapshotPolicy) -> str:
    canon = _canonicalize(value, max_depth=policy.max_depth, max_nodes=policy.max_nodes)
    return json.dumps(canon, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def fingerprint(value: Any, policy: SnapshotPolicy) -> str:
    return hashlib.sha256(canonical_json(value, policy).encode("utf-8")).hexdigest()


def _escape_path_segment(segment: str) -> str:
    return segment.replace("~", "~0").replace("/", "~1")


def _unescape_path_segment(segment: str) -> str:
    return segment.replace("~1", "/").replace("~0", "~")


def _diff_dict(base: Mapping[str, Any], current: Mapping[str, Any], prefix: str = "") -> List[Tuple[str, str, Any]]:
    ops: List[Tuple[str, str, Any]] = []
    base_keys = set(base.keys())
    cur_keys = set(current.keys())
    for k in sorted(base_keys - cur_keys):
        path = f"{prefix}/{_escape_path_segment(k)}"
        ops.append(("remove", path, None))
    for k in sorted(cur_keys - base_keys):
        path = f"{prefix}/{_escape_path_segment(k)}"
        ops.append(("set", path, copy.deepcopy(current[k])))
    for k in sorted(base_keys & cur_keys):
        bv, cv = base[k], current[k]
        path = f"{prefix}/{_escape_path_segment(k)}"
        if isinstance(bv, Mapping) and isinstance(cv, Mapping):
            ops.extend(_diff_dict(bv, cv, path))
        elif bv != cv:
            ops.append(("set", path, copy.deepcopy(cv)))
    return ops


def _apply_delta(base: Mapping[str, Any], delta: Iterable[Tuple[str, str, Any]]) -> Dict[str, Any]:
    state: Dict[str, Any] = copy.deepcopy(dict(base))
    for op, path, value in delta:
        if not path.startswith("/"):
            raise SnapshotError("invalid delta path")
        parts = [_unescape_path_segment(p) for p in path.split("/")[1:]]
        if not parts:
            raise SnapshotError("root replacement is not supported")
        cursor: Dict[str, Any] = state
        for p in parts[:-1]:
            if p not in cursor or not isinstance(cursor[p], dict):
                if op == "set":
                    cursor[p] = {}
                else:
                    raise SnapshotError("remove path missing")
            cursor = cursor[p]
        leaf = parts[-1]
        if op == "set":
            cursor[leaf] = copy.deepcopy(value)
        elif op == "remove":
            if leaf not in cursor:
                raise SnapshotError("remove path missing")
            del cursor[leaf]
        else:
            raise SnapshotError("invalid delta op")
    return state


def _snapshot_id(target_ref: str, target_version: str, state_fp: str, base_fp: Optional[str]) -> str:
    material = json.dumps({"target_ref": target_ref, "target_version": target_version, "state_fp": state_fp, "base_fp": base_fp}, sort_keys=True, separators=(",", ":"))
    return "snap-" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]


def _checkpoint_fingerprint(plan_material: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(plan_material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


class SnapshotControl:
    """Pure planning / reconstruction control. It never writes target state or performs rollback."""

    def __init__(self, policy: SnapshotPolicy = SnapshotPolicy()):
        self.policy = policy
        self._cache: Dict[str, SnapshotPlan] = {}

    def _request_key(self, request: SnapshotRequest) -> str:
        material = {
            "policy_version": self.policy.policy_version,
            "request_id": request.request_id,
            "target_ref": request.target_ref,
            "target_version": request.target_version,
            "current_state_fp": fingerprint(request.current_state, self.policy),
            "previous_state_fp": fingerprint(request.previous_state, self.policy) if request.previous_state is not None else None,
            "previous_snapshot_id": request.previous_snapshot_id,
            "previous_snapshot_fingerprint": request.previous_snapshot_fingerprint,
            "reason": request.reason,
            "context": request.context,
        }
        return fingerprint(material, self.policy)

    def prepare_snapshot(self, request: SnapshotRequest, *, use_cache: bool = True) -> SnapshotPlan:
        if not request.request_id or not request.target_ref:
            return SnapshotPlan(SnapshotDecision.DENY, ("missing request_id or target_ref",), None, None, request.target_ref, request.target_version, None, None, None, None, None, tuple())
        if self.policy.require_target_version and not request.target_version:
            return SnapshotPlan(SnapshotDecision.HOLD, ("missing target_version",), None, None, request.target_ref, request.target_version, None, None, None, None, None, tuple())

        try:
            key = self._request_key(request)
        except SnapshotError as e:
            return SnapshotPlan(SnapshotDecision.DENY, (str(e),), None, None, request.target_ref, request.target_version, None, None, None, None, None, tuple())
        if use_cache and key in self._cache:
            return self._cache[key]

        try:
            current = _canonicalize(request.current_state, max_depth=self.policy.max_depth, max_nodes=self.policy.max_nodes)
        except SnapshotError as e:
            return SnapshotPlan(SnapshotDecision.DENY, (str(e),), None, None, request.target_ref, request.target_version, None, None, None, None, None, tuple())

        state_fp = fingerprint(current, self.policy)
        mode = SnapshotMode.FULL
        full_state: Optional[Mapping[str, Any]] = current
        delta: Tuple[Tuple[str, str, Any], ...] = tuple()
        base_fp: Optional[str] = None
        base_id: Optional[str] = None

        if request.previous_state is not None:
            try:
                previous = _canonicalize(request.previous_state, max_depth=self.policy.max_depth, max_nodes=self.policy.max_nodes)
            except SnapshotError as e:
                return SnapshotPlan(SnapshotDecision.DENY, ("invalid previous_state: " + str(e),), None, None, request.target_ref, request.target_version, None, None, None, None, None, tuple())
            base_fp = fingerprint(previous, self.policy)
            if self.policy.require_base_match_for_delta and request.previous_snapshot_fingerprint and request.previous_snapshot_fingerprint != base_fp:
                return SnapshotPlan(SnapshotDecision.HOLD, ("previous snapshot fingerprint mismatch",), None, None, request.target_ref, request.target_version, request.previous_snapshot_id, base_fp, state_fp, None, None, tuple())
            ops = _diff_dict(previous, current)
            full_size = len(canonical_json(current, self.policy).encode("utf-8"))
            delta_size = len(json.dumps(ops, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
            if full_size > 0 and delta_size / full_size <= self.policy.max_delta_ratio:
                mode = SnapshotMode.DELTA
                full_state = None
                delta = tuple((op, path, value) for op, path, value in ops)
                base_id = request.previous_snapshot_id

        sid = _snapshot_id(request.target_ref, request.target_version, state_fp, base_fp if mode == SnapshotMode.DELTA else None)
        checkpoint_material = {
            "policy_version": self.policy.policy_version,
            "snapshot_id": sid,
            "target_ref": request.target_ref,
            "target_version": request.target_version,
            "mode": mode.value,
            "base_snapshot_id": base_id,
            "base_fingerprint": base_fp if mode == SnapshotMode.DELTA else None,
            "state_fingerprint": state_fp,
            "full_state": full_state,
            "delta": delta,
        }
        checkpoint_fp = _checkpoint_fingerprint(checkpoint_material)
        plan = SnapshotPlan(
            decision=SnapshotDecision.SNAPSHOT_PREPARE,
            reasons=("snapshot candidate prepared; persistence is separate authority",),
            mode=mode,
            snapshot_id=sid,
            target_ref=request.target_ref,
            target_version=request.target_version,
            base_snapshot_id=base_id,
            base_fingerprint=base_fp if mode == SnapshotMode.DELTA else None,
            state_fingerprint=state_fp,
            checkpoint_fingerprint=checkpoint_fp,
            full_state=full_state,
            delta=delta,
        )
        if use_cache:
            self._cache[key] = plan
        return plan

    def verify_snapshot_plan(self, plan: SnapshotPlan, *, base_state: Optional[Mapping[str, Any]] = None) -> bool:
        if plan.decision != SnapshotDecision.SNAPSHOT_PREPARE or not plan.snapshot_id or not plan.state_fingerprint or not plan.checkpoint_fingerprint or not plan.mode:
            return False
        if plan.mode == SnapshotMode.FULL:
            if plan.full_state is None or plan.delta:
                return False
            reconstructed = _canonicalize(plan.full_state, max_depth=self.policy.max_depth, max_nodes=self.policy.max_nodes)
        else:
            if base_state is None or plan.full_state is not None or not plan.base_fingerprint:
                return False
            canonical_base = _canonicalize(base_state, max_depth=self.policy.max_depth, max_nodes=self.policy.max_nodes)
            if fingerprint(canonical_base, self.policy) != plan.base_fingerprint:
                return False
            reconstructed = _apply_delta(canonical_base, plan.delta)
        if fingerprint(reconstructed, self.policy) != plan.state_fingerprint:
            return False
        checkpoint_material = {
            "policy_version": self.policy.policy_version,
            "snapshot_id": plan.snapshot_id,
            "target_ref": plan.target_ref,
            "target_version": plan.target_version,
            "mode": plan.mode.value,
            "base_snapshot_id": plan.base_snapshot_id,
            "base_fingerprint": plan.base_fingerprint,
            "state_fingerprint": plan.state_fingerprint,
            "full_state": plan.full_state,
            "delta": plan.delta,
        }
        return _checkpoint_fingerprint(checkpoint_material) == plan.checkpoint_fingerprint

    def prepare_rollback(self, request: RollbackRequest) -> RollbackPlan:
        plan = request.snapshot_plan
        if plan.decision != SnapshotDecision.SNAPSHOT_PREPARE:
            return RollbackPlan(SnapshotDecision.HOLD, ("snapshot plan is not restorable candidate",), request.target_ref, request.current_target_version, plan.snapshot_id, None, None)
        if request.expected_snapshot_id and plan.snapshot_id != request.expected_snapshot_id:
            return RollbackPlan(SnapshotDecision.HOLD, ("snapshot id mismatch",), request.target_ref, request.current_target_version, plan.snapshot_id, None, None)
        if plan.target_ref != request.target_ref:
            return RollbackPlan(SnapshotDecision.DENY, ("target mismatch",), request.target_ref, request.current_target_version, plan.snapshot_id, None, None)
        if request.current_target_version == "":
            return RollbackPlan(SnapshotDecision.HOLD, ("current target version required",), request.target_ref, request.current_target_version, plan.snapshot_id, None, None)
        if not self.verify_snapshot_plan(plan, base_state=request.base_state):
            return RollbackPlan(SnapshotDecision.HOLD, ("snapshot verification failed",), request.target_ref, request.current_target_version, plan.snapshot_id, None, None)

        if plan.mode == SnapshotMode.FULL:
            restored = copy.deepcopy(dict(plan.full_state or {}))
        else:
            assert request.base_state is not None
            restored = _apply_delta(_canonicalize(request.base_state, max_depth=self.policy.max_depth, max_nodes=self.policy.max_nodes), plan.delta)
        restored_fp = fingerprint(restored, self.policy)
        return RollbackPlan(
            decision=SnapshotDecision.ROLLBACK_PREPARE,
            reasons=("rollback candidate prepared; execution is separate authority",),
            target_ref=request.target_ref,
            current_target_version=request.current_target_version,
            snapshot_id=plan.snapshot_id,
            restored_candidate=restored,
            restored_fingerprint=restored_fp,
        )

    def clear_cache(self) -> None:
        self._cache.clear()
