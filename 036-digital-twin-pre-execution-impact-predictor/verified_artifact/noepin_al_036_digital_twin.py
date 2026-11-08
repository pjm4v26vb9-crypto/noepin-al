from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Tuple, Dict, Mapping
from types import MappingProxyType
import hashlib, json, math

VERSION = "2.0.0-successor.20261103"
CREATOR = "NOEPIN / のえぴん"

class Decision(str, Enum):
    ALLOW_CANDIDATE = "ALLOW_CANDIDATE"
    HUMAN_CONFIRM = "HUMAN_CONFIRM"
    HOLD = "HOLD"
    DENY = "DENY"

class Criticality(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass(frozen=True)
class StateItem:
    item_id: str
    value_fingerprint: str
    criticality: Criticality = Criticality.LOW
    protected: bool = False

@dataclass(frozen=True)
class Snapshot:
    snapshot_id: str
    snapshot_version: str
    observed_epoch_ms: int
    items: Tuple[StateItem, ...]
    declared_fingerprint: str
    base_production_fingerprint: str = ""

@dataclass(frozen=True)
class PlannedChange:
    target_id: str
    expected_before_fingerprint: str
    after_fingerprint: str
    change_kind: str = "UPDATE"
    reversible: bool = True
    side_effect_targets: Tuple[str, ...] = ()
    unknown_side_effects: bool = False

@dataclass(frozen=True)
class SimulationRequest:
    request_id: str
    policy_version: str
    authority_version: str
    target_production_version: str
    observed_epoch_ms: int
    max_snapshot_age_ms: int
    context_fingerprint: str
    actions: Tuple[PlannedChange, ...]
    impact_human_threshold: int = 5
    require_human_for_high_criticality: bool = True
    human_approval_evidence: bool = False

@dataclass(frozen=True)
class PreparedSnapshot:
    snapshot_id: str
    snapshot_version: str
    observed_epoch_ms: int
    fingerprint: str
    base_production_fingerprint: str
    items: Tuple[StateItem, ...]
    index: Mapping[str, StateItem]

@dataclass(frozen=True)
class ImpactDiff:
    changed_targets: Tuple[str, ...]
    side_effect_targets: Tuple[str, ...]
    high_or_critical_targets: Tuple[str, ...]
    irreversible_targets: Tuple[str, ...]
    resulting_twin_fingerprint: str

@dataclass(frozen=True)
class SimulationResult:
    decision: Decision
    reasons: Tuple[str, ...]
    request_fingerprint: str
    production_fingerprint: str
    twin_fingerprint: str
    impact: ImpactDiff
    simulation_performed: bool = True
    production_executed: bool = False
    production_succeeded: bool = False
    permission_granted: bool = False
    state_committed: bool = False
    authoritative: bool = False

@dataclass(frozen=True)
class SnapshotDelta:
    base_fingerprint: str
    target_fingerprint: str
    base_version: str
    target_version: str
    changed_items: Tuple[StateItem, ...]
    removed_item_ids: Tuple[str, ...]
    target_snapshot_id: str
    target_observed_epoch_ms: int
    target_base_production_fingerprint: str

class DigitalTwinImpactPredictor:
    def __init__(self):
        self._prepared_cache: Dict[Tuple[str, str, str], PreparedSnapshot] = {}

    @staticmethod
    def _canonical(obj) -> str:
        return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @staticmethod
    def _bad_text(value: str) -> bool:
        if not isinstance(value, str) or not value.strip():
            return True
        if len(value) > 512:
            return True
        return any(ord(ch) < 32 for ch in value)

    @classmethod
    def snapshot_fingerprint(cls, items: Tuple[StateItem, ...]) -> str:
        serial = []
        for x in sorted(items, key=lambda i: i.item_id):
            serial.append({
                "item_id": x.item_id,
                "value_fingerprint": x.value_fingerprint,
                "criticality": x.criticality.value,
                "protected": x.protected,
            })
        return hashlib.sha256(cls._canonical(serial).encode("utf-8")).hexdigest()

    @classmethod
    def request_fingerprint(cls, req: SimulationRequest, production_fp: str, twin_fp: str) -> str:
        payload = asdict(req)
        payload["production_fingerprint"] = production_fp
        payload["twin_fingerprint"] = twin_fp
        return hashlib.sha256(cls._canonical(payload).encode("utf-8")).hexdigest()

    def _validate_snapshot(self, snap: Snapshot) -> Tuple[str, ...]:
        reasons = []
        for name, value in (("SNAPSHOT_ID", snap.snapshot_id), ("SNAPSHOT_VERSION", snap.snapshot_version), ("DECLARED_FINGERPRINT", snap.declared_fingerprint)):
            if self._bad_text(value): reasons.append(f"INVALID_{name}")
        if snap.observed_epoch_ms < 0: reasons.append("INVALID_SNAPSHOT_TIME")
        if not snap.items: reasons.append("EMPTY_SNAPSHOT")
        if len(snap.items) > 100_000: reasons.append("SNAPSHOT_TOO_LARGE")
        ids = set()
        for item in snap.items:
            if self._bad_text(item.item_id): reasons.append("INVALID_ITEM_ID")
            if self._bad_text(item.value_fingerprint): reasons.append("INVALID_ITEM_FINGERPRINT")
            if item.item_id in ids: reasons.append("DUPLICATE_ITEM_ID")
            ids.add(item.item_id)
        if snap.base_production_fingerprint and self._bad_text(snap.base_production_fingerprint): reasons.append("INVALID_BASE_PRODUCTION_FINGERPRINT")
        return tuple(sorted(set(reasons)))

    def prepare_snapshot(self, snap: Snapshot) -> PreparedSnapshot:
        validation = self._validate_snapshot(snap)
        if validation:
            raise ValueError(";".join(validation))
        key = (snap.snapshot_id, snap.snapshot_version, snap.declared_fingerprint)
        cached = self._prepared_cache.get(key)
        if cached is not None:
            # Snapshot is immutable; still bind base fingerprint and timestamp to prevent alias reuse.
            if cached.observed_epoch_ms == snap.observed_epoch_ms and cached.base_production_fingerprint == snap.base_production_fingerprint and cached.items == snap.items:
                return cached
        actual = self.snapshot_fingerprint(snap.items)
        if actual != snap.declared_fingerprint:
            raise ValueError("SNAPSHOT_FINGERPRINT_MISMATCH")
        index = MappingProxyType({x.item_id: x for x in snap.items})
        prepared = PreparedSnapshot(snap.snapshot_id, snap.snapshot_version, snap.observed_epoch_ms, actual, snap.base_production_fingerprint, tuple(sorted(snap.items, key=lambda i: i.item_id)), index)
        self._prepared_cache[key] = prepared
        return prepared

    def _validate_request(self, req: SimulationRequest) -> Tuple[str, ...]:
        reasons = []
        for name, value in (("REQUEST_ID", req.request_id), ("POLICY_VERSION", req.policy_version), ("AUTHORITY_VERSION", req.authority_version),
                            ("TARGET_PRODUCTION_VERSION", req.target_production_version), ("CONTEXT_FINGERPRINT", req.context_fingerprint)):
            if self._bad_text(value): reasons.append(f"INVALID_{name}")
        if req.observed_epoch_ms < 0 or req.max_snapshot_age_ms < 0: reasons.append("INVALID_TIME_BOUND")
        if req.impact_human_threshold < 1: reasons.append("INVALID_IMPACT_THRESHOLD")
        if not req.actions: reasons.append("NO_ACTIONS")
        if len(req.actions) > 10_000: reasons.append("TOO_MANY_ACTIONS")
        targets = set()
        for a in req.actions:
            if self._bad_text(a.target_id): reasons.append("INVALID_TARGET_ID")
            if self._bad_text(a.expected_before_fingerprint): reasons.append("INVALID_EXPECTED_BEFORE")
            if self._bad_text(a.after_fingerprint): reasons.append("INVALID_AFTER_FINGERPRINT")
            if self._bad_text(a.change_kind): reasons.append("INVALID_CHANGE_KIND")
            if a.target_id in targets: reasons.append("DUPLICATE_ACTION_TARGET")
            targets.add(a.target_id)
            if len(a.side_effect_targets) > 1000: reasons.append("TOO_MANY_SIDE_EFFECT_TARGETS")
            if any(self._bad_text(x) for x in a.side_effect_targets): reasons.append("INVALID_SIDE_EFFECT_TARGET")
        return tuple(sorted(set(reasons)))

    @classmethod
    def _resulting_fingerprint(cls, twin: PreparedSnapshot, actions: Tuple[PlannedChange, ...]) -> str:
        # DCSR prepared-state digest: bind the verified Twin base fingerprint to the
        # exact action delta without re-hashing the full known snapshot. This digest
        # is a candidate-state binding, not an authoritative committed-state hash.
        patches = []
        for a in sorted(actions, key=lambda x: x.target_id):
            patches.append({
                "target_id": a.target_id,
                "expected_before_fingerprint": a.expected_before_fingerprint,
                "after_fingerprint": a.after_fingerprint,
                "change_kind": a.change_kind,
                "reversible": a.reversible,
                "side_effect_targets": sorted(a.side_effect_targets),
                "unknown_side_effects": a.unknown_side_effects,
            })
        payload = {"verified_twin_base_fingerprint": twin.fingerprint, "action_delta": patches}
        return hashlib.sha256(cls._canonical(payload).encode("utf-8")).hexdigest()

    def evaluate_prepared(self, production: PreparedSnapshot, twin: PreparedSnapshot, req: SimulationRequest) -> SimulationResult:
        validation = self._validate_request(req)
        empty_impact = ImpactDiff((), (), (), (), twin.fingerprint)
        fp = self.request_fingerprint(req, production.fingerprint, twin.fingerprint)
        if validation:
            return SimulationResult(Decision.DENY, validation, fp, production.fingerprint, twin.fingerprint, empty_impact, False)

        reasons = []
        decision = Decision.ALLOW_CANDIDATE

        if production.snapshot_version != req.target_production_version:
            decision = Decision.HOLD; reasons.append("PRODUCTION_VERSION_MISMATCH")
        if twin.base_production_fingerprint != production.fingerprint:
            decision = Decision.HOLD; reasons.append("STALE_OR_UNBOUND_TWIN_BASE")
        if twin.snapshot_version != production.snapshot_version:
            decision = Decision.HOLD; reasons.append("TWIN_VERSION_MISMATCH")
        for name, snap in (("PRODUCTION", production), ("TWIN", twin)):
            age = req.observed_epoch_ms - snap.observed_epoch_ms
            if age < 0:
                decision = Decision.HOLD; reasons.append(f"{name}_SNAPSHOT_FROM_FUTURE")
            elif age > req.max_snapshot_age_ms:
                decision = Decision.HOLD; reasons.append(f"{name}_SNAPSHOT_STALE")

        changed = []
        side = set()
        critical = []
        irreversible = []
        unknown_side_effect = False

        for a in req.actions:
            p = production.index.get(a.target_id)
            t = twin.index.get(a.target_id)
            if p is None or t is None:
                decision = Decision.HOLD; reasons.append("TARGET_NOT_PRESENT_IN_BOTH_SNAPSHOTS"); continue
            if p.value_fingerprint != t.value_fingerprint:
                decision = Decision.HOLD; reasons.append("PRODUCTION_TWIN_TARGET_DRIFT")
            if a.expected_before_fingerprint != p.value_fingerprint:
                decision = Decision.HOLD; reasons.append("EXPECTED_BEFORE_MISMATCH")
            if p.protected:
                decision = Decision.DENY; reasons.append("PROTECTED_TARGET")
            if a.after_fingerprint == p.value_fingerprint:
                reasons.append("NOOP_CHANGE")
            else:
                changed.append(a.target_id)
            if p.criticality in (Criticality.HIGH, Criticality.CRITICAL):
                critical.append(a.target_id)
            if not a.reversible:
                irreversible.append(a.target_id)
            side.update(a.side_effect_targets)
            if a.unknown_side_effects:
                unknown_side_effect = True

        # Unknown side effects are not safe to promote to a production-ready candidate.
        if unknown_side_effect and decision != Decision.DENY:
            decision = Decision.HOLD; reasons.append("UNKNOWN_SIDE_EFFECTS")
        elif decision not in (Decision.DENY, Decision.HOLD):
            if len(changed) + len(side) >= req.impact_human_threshold:
                decision = Decision.HUMAN_CONFIRM; reasons.append("IMPACT_THRESHOLD_REACHED")
            if req.require_human_for_high_criticality and critical:
                decision = Decision.HUMAN_CONFIRM; reasons.append("HIGH_OR_CRITICAL_TARGET")
            if irreversible:
                decision = Decision.HUMAN_CONFIRM; reasons.append("IRREVERSIBLE_CHANGE")
            if decision == Decision.HUMAN_CONFIRM and req.human_approval_evidence:
                decision = Decision.ALLOW_CANDIDATE; reasons.append("HUMAN_APPROVAL_EVIDENCE_PRESENT")

        if decision in (Decision.DENY, Decision.HOLD) or any(a.target_id not in twin.index for a in req.actions):
            resulting = twin.fingerprint
        else:
            resulting = self._resulting_fingerprint(twin, req.actions)
        impact = ImpactDiff(tuple(sorted(set(changed))), tuple(sorted(side)), tuple(sorted(set(critical))), tuple(sorted(set(irreversible))), resulting)
        if not reasons:
            reasons.append("DRY_RUN_IMPACT_WITHIN_RECORDED_LIMITS")
        return SimulationResult(decision, tuple(reasons), fp, production.fingerprint, twin.fingerprint, impact)

    def evaluate(self, production: Snapshot, twin: Snapshot, req: SimulationRequest) -> SimulationResult:
        try:
            pp = self.prepare_snapshot(production)
            tp = self.prepare_snapshot(twin)
        except ValueError as e:
            empty = ImpactDiff((), (), (), (), "")
            fp = hashlib.sha256((repr(production)+repr(twin)+repr(req)).encode()).hexdigest()
            return SimulationResult(Decision.DENY, tuple(str(e).split(";")), fp, "", "", empty, False)
        return self.evaluate_prepared(pp, tp, req)

    @classmethod
    def make_delta(cls, base: PreparedSnapshot, target: PreparedSnapshot) -> SnapshotDelta:
        b = base.index; t = target.index
        changed = tuple(sorted((item for k, item in t.items() if k not in b or b[k] != item), key=lambda x: x.item_id))
        removed = tuple(sorted(k for k in b if k not in t))
        return SnapshotDelta(base.fingerprint, target.fingerprint, base.snapshot_version, target.snapshot_version, changed, removed,
                             target.snapshot_id, target.observed_epoch_ms, target.base_production_fingerprint)

    @classmethod
    def reconstruct_candidate(cls, base: PreparedSnapshot, delta: SnapshotDelta) -> PreparedSnapshot:
        if base.fingerprint != delta.base_fingerprint or base.snapshot_version != delta.base_version:
            raise ValueError("DELTA_BASE_MISMATCH")
        items = {k: v for k, v in base.index.items()}
        for rid in delta.removed_item_ids:
            items.pop(rid, None)
        for item in delta.changed_items:
            items[item.item_id] = item
        ordered = tuple(sorted(items.values(), key=lambda x: x.item_id))
        fp = cls.snapshot_fingerprint(ordered)
        if fp != delta.target_fingerprint:
            raise ValueError("DELTA_TARGET_FINGERPRINT_MISMATCH")
        return PreparedSnapshot(delta.target_snapshot_id, delta.target_version, delta.target_observed_epoch_ms, fp,
                                delta.target_base_production_fingerprint, ordered, MappingProxyType({x.item_id: x for x in ordered}))
