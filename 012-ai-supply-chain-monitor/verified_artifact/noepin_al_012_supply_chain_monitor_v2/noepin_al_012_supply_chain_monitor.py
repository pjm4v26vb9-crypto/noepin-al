from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Tuple
import hashlib, json, time


class ComponentKind(str, Enum):
    MODEL="MODEL"; MCP="MCP"; PLUGIN="PLUGIN"; LIBRARY="LIBRARY"; PROMPT="PROMPT"; DATA_SOURCE="DATA_SOURCE"


class SupplyDecision(str, Enum):
    MATCH="MATCH"; HUMAN_REVIEW="HUMAN_REVIEW"; HOLD="HOLD"; DENY="DENY"


@dataclass(frozen=True)
class ComponentState:
    component_id: str
    kind: ComponentKind
    version: str
    artifact_sha256: str
    config_sha256: Optional[str] = None
    signer_ref: Optional[str] = None
    signature_verified: bool = False
    source_ref: Optional[str] = None
    enabled: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SupplyManifest:
    manifest_id: str
    version: int
    authority_version: int
    components: Tuple[ComponentState, ...]
    manifest_sha256: Optional[str] = None
    approved_change_ref: Optional[str] = None
    revoked: bool = False
    schema_version: str = "1"


@dataclass(frozen=True)
class SupplyAuditRequest:
    request_id: str
    baseline: SupplyManifest
    observed: SupplyManifest
    require_signature_for_kinds: Tuple[ComponentKind, ...] = (
        ComponentKind.MODEL, ComponentKind.MCP, ComponentKind.PLUGIN, ComponentKind.LIBRARY
    )
    expected_baseline_version: Optional[int] = None
    expected_authority_version: Optional[int] = None
    human_approved: bool = False
    approval_ref: Optional[str] = None
    schema_version: str = "1"
    context: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SupplyAuditResult:
    decision: SupplyDecision
    reason_codes: Tuple[str, ...]
    request_fingerprint: str
    added_ids: Tuple[str, ...]
    removed_ids: Tuple[str, ...]
    changed_ids: Tuple[str, ...]
    unchanged_ids: Tuple[str, ...]
    manifest_match: bool
    authoritative: bool = False
    change_approved: bool = False
    action_executed: bool = False
    deployment_succeeded: bool = False
    cache_reused: bool = False
    created_unix_ns: int = 0

    def stable_payload(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reason_codes": list(self.reason_codes),
            "request_fingerprint": self.request_fingerprint,
            "added_ids": list(self.added_ids),
            "removed_ids": list(self.removed_ids),
            "changed_ids": list(self.changed_ids),
            "unchanged_ids": list(self.unchanged_ids),
            "manifest_match": self.manifest_match,
            "authoritative": self.authoritative,
            "change_approved": self.change_approved,
            "action_executed": self.action_executed,
            "deployment_succeeded": self.deployment_succeeded,
            "cache_reused": self.cache_reused,
        }


class AISupplyChainMonitor:
    """
    NOEPIN AL 012 — AI Supply Chain Monitor.

    Compares an approved baseline manifest with an observed AI dependency manifest.
    It never deploys, installs, updates, enables, or removes a component.

    Invariants:
      Fingerprint match != Authority match
      Signature present != Signature verified
      Version change != Approved change
      Manifest match != Deployment success
      Monitor decision != Action success
      Cached audit != New authority
    """

    def __init__(self, *, policy_version: str = "1", enable_exact_state_cache: bool = True) -> None:
        if not policy_version:
            raise ValueError("policy_version required")
        self.policy_version = str(policy_version)
        self.enable_exact_state_cache = bool(enable_exact_state_cache)
        self._cache: Dict[Tuple[str, str], SupplyAuditResult] = {}

    @staticmethod
    def _norm(v: Any) -> Any:
        if isinstance(v, Mapping):
            return {str(k): AISupplyChainMonitor._norm(v[k]) for k in sorted(v, key=lambda x: str(x))}
        if isinstance(v, (list, tuple)):
            return [AISupplyChainMonitor._norm(x) for x in v]
        if isinstance(v, set):
            return sorted(AISupplyChainMonitor._norm(x) for x in v)
        if isinstance(v, Enum):
            return v.value
        if v is None or isinstance(v, (str, int, float, bool)):
            return v
        return str(v)

    @classmethod
    def fingerprint(cls, request: SupplyAuditRequest) -> str:
        raw = json.dumps(cls._norm(asdict(request)), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _valid_hash(value: Optional[str], allow_none: bool = False) -> bool:
        if value is None:
            return allow_none
        if not isinstance(value, str) or len(value) != 64:
            return False
        try:
            int(value, 16)
            return True
        except ValueError:
            return False

    @staticmethod
    def _valid_int(value: Any) -> bool:
        return isinstance(value, int) and not isinstance(value, bool)

    @classmethod
    def canonical_manifest_hash(cls, manifest: SupplyManifest) -> str:
        # Intentionally excludes manifest_sha256 itself.
        payload = {
            "manifest_id": manifest.manifest_id,
            "version": manifest.version,
            "authority_version": manifest.authority_version,
            "components": cls._norm(manifest.components),
            "approved_change_ref": manifest.approved_change_ref,
            "revoked": manifest.revoked,
            "schema_version": manifest.schema_version,
        }
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _component_map(manifest: SupplyManifest) -> Dict[str, ComponentState]:
        return {c.component_id: c for c in manifest.components}

    def _validate_manifest(self, manifest: SupplyManifest, label: str) -> Optional[Tuple[SupplyDecision, str]]:
        if not manifest.manifest_id or not manifest.schema_version:
            return (SupplyDecision.HOLD, f"{label}_MANIFEST_REQUIRED_FIELD_MISSING")
        if not self._valid_int(manifest.version) or manifest.version < 1:
            return (SupplyDecision.HOLD, f"{label}_MANIFEST_VERSION_INVALID")
        if not self._valid_int(manifest.authority_version) or manifest.authority_version < 1:
            return (SupplyDecision.HOLD, f"{label}_AUTHORITY_VERSION_INVALID")
        if manifest.revoked:
            return (SupplyDecision.DENY, f"{label}_MANIFEST_REVOKED")
        ids = [c.component_id for c in manifest.components]
        if len(ids) != len(set(ids)):
            return (SupplyDecision.HOLD, f"{label}_DUPLICATE_COMPONENT_ID")
        for c in manifest.components:
            if not c.component_id or not c.version:
                return (SupplyDecision.HOLD, f"{label}_COMPONENT_REQUIRED_FIELD_MISSING")
            if not self._valid_hash(c.artifact_sha256):
                return (SupplyDecision.HOLD, f"{label}_ARTIFACT_HASH_INVALID")
            if not self._valid_hash(c.config_sha256, allow_none=True):
                return (SupplyDecision.HOLD, f"{label}_CONFIG_HASH_INVALID")
        if manifest.manifest_sha256 is not None:
            if not self._valid_hash(manifest.manifest_sha256):
                return (SupplyDecision.HOLD, f"{label}_MANIFEST_HASH_INVALID")
            if manifest.manifest_sha256 != self.canonical_manifest_hash(manifest):
                return (SupplyDecision.DENY, f"{label}_MANIFEST_HASH_MISMATCH")
        return None

    def _diff(self, baseline: SupplyManifest, observed: SupplyManifest):
        b = self._component_map(baseline)
        o = self._component_map(observed)
        b_ids, o_ids = set(b), set(o)
        added = tuple(sorted(o_ids - b_ids))
        removed = tuple(sorted(b_ids - o_ids))
        changed, unchanged = [], []
        for cid in sorted(b_ids & o_ids):
            if self._norm(b[cid]) == self._norm(o[cid]):
                unchanged.append(cid)
            else:
                changed.append(cid)
        return added, removed, tuple(changed), tuple(unchanged)

    def _make(self, decision, reasons, fp, added, removed, changed, unchanged, manifest_match):
        return SupplyAuditResult(
            decision=decision,
            reason_codes=tuple(reasons),
            request_fingerprint=fp,
            added_ids=tuple(added),
            removed_ids=tuple(removed),
            changed_ids=tuple(changed),
            unchanged_ids=tuple(unchanged),
            manifest_match=bool(manifest_match),
            authoritative=False,
            change_approved=False,
            action_executed=False,
            deployment_succeeded=False,
            cache_reused=False,
            created_unix_ns=time.time_ns(),
        )

    def _evaluate_uncached(self, request: SupplyAuditRequest) -> SupplyAuditResult:
        fp = self.fingerprint(request)

        if not request.request_id or not request.schema_version:
            return self._make(SupplyDecision.HOLD, ("MISSING_REQUEST_OR_SCHEMA",), fp, (), (), (), (), False)

        baseline_error = self._validate_manifest(request.baseline, "BASELINE")
        if baseline_error:
            d, reason = baseline_error
            return self._make(d, (reason,), fp, (), (), (), (), False)

        observed_error = self._validate_manifest(request.observed, "OBSERVED")
        if observed_error:
            d, reason = observed_error
            return self._make(d, (reason,), fp, (), (), (), (), False)

        if request.expected_baseline_version is not None and request.expected_baseline_version != request.baseline.version:
            return self._make(SupplyDecision.HOLD, ("BASELINE_VERSION_MISMATCH",), fp, (), (), (), (), False)
        if request.expected_authority_version is not None and request.expected_authority_version != request.baseline.authority_version:
            return self._make(SupplyDecision.HOLD, ("AUTHORITY_VERSION_MISMATCH",), fp, (), (), (), (), False)

        added, removed, changed, unchanged = self._diff(request.baseline, request.observed)
        manifest_match = not added and not removed and not changed

        # Required signatures are verified independently of hashes.
        observed_map = self._component_map(request.observed)
        for cid, comp in observed_map.items():
            if comp.kind in set(request.require_signature_for_kinds):
                if not comp.signer_ref:
                    return self._make(SupplyDecision.HOLD, (f"SIGNER_REQUIRED:{cid}",), fp, added, removed, changed, unchanged, manifest_match)
                if not comp.signature_verified:
                    return self._make(SupplyDecision.DENY, (f"SIGNATURE_NOT_VERIFIED:{cid}",), fp, added, removed, changed, unchanged, manifest_match)

        if manifest_match:
            return self._make(SupplyDecision.MATCH, ("MANIFEST_MATCH",), fp, added, removed, changed, unchanged, True)

        # Any supply-chain delta requires explicit human review; an approval reference
        # is evidence for review, not an auto-deployment authority.
        if request.human_approved and request.approval_ref:
            return self._make(
                SupplyDecision.HUMAN_REVIEW,
                ("CHANGE_APPROVAL_EVIDENCE_PRESENT_REVIEW_REQUIRED",),
                fp, added, removed, changed, unchanged, False
            )

        return self._make(
            SupplyDecision.HUMAN_REVIEW,
            ("SUPPLY_CHAIN_DELTA_REQUIRES_HUMAN_REVIEW",),
            fp, added, removed, changed, unchanged, False
        )

    def evaluate(self, request: SupplyAuditRequest) -> SupplyAuditResult:
        fp = self.fingerprint(request)
        key = (fp, self.policy_version)
        if self.enable_exact_state_cache and key in self._cache:
            r = self._cache[key]
            return SupplyAuditResult(
                decision=r.decision, reason_codes=r.reason_codes, request_fingerprint=fp,
                added_ids=r.added_ids, removed_ids=r.removed_ids, changed_ids=r.changed_ids,
                unchanged_ids=r.unchanged_ids, manifest_match=r.manifest_match,
                authoritative=False, change_approved=False, action_executed=False,
                deployment_succeeded=False, cache_reused=True, created_unix_ns=time.time_ns()
            )
        result = self._evaluate_uncached(request)
        if self.enable_exact_state_cache:
            self._cache[key] = result
        return result

    def clear_cache(self) -> None:
        self._cache.clear()

    def cache_size(self) -> int:
        return len(self._cache)
