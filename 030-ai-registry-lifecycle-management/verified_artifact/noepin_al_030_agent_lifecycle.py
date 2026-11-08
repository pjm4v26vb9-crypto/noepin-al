from __future__ import annotations
from dataclasses import dataclass, asdict, replace
from enum import Enum
from typing import Tuple, Optional, Dict, Any
import hashlib, json

CREATOR = "NOEPIN / のえぴん"
VERSION = "2.0.0-successor.20261102"

class LifecycleState(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    EXPIRED = "EXPIRED"
    DECOMMISSIONED = "DECOMMISSIONED"

class Operation(str, Enum):
    REGISTER = "REGISTER"
    ACTIVATE = "ACTIVATE"
    UPDATE = "UPDATE"
    RENEW = "RENEW"
    SUSPEND = "SUSPEND"
    DECOMMISSION = "DECOMMISSION"
    CHECK = "CHECK"

class Decision(str, Enum):
    ALLOW_PREPARE = "ALLOW_PREPARE"
    HOLD = "HOLD"
    HUMAN_CONFIRM = "HUMAN_CONFIRM"
    DENY = "DENY"

@dataclass(frozen=True)
class AgentRecord:
    agent_id: str
    owner_id: str
    role: str
    agent_version: str
    registry_version: int
    authority_version: str
    created_epoch_ns: int
    expires_epoch_ns: int
    lifecycle_state: str = LifecycleState.PENDING.value
    revoked: bool = False
    permit_refs: Tuple[str, ...] = ()
    decommissioned_epoch_ns: Optional[int] = None

@dataclass(frozen=True)
class RegistryState:
    version: int
    authority_version: str
    agents: Tuple[AgentRecord, ...]

@dataclass(frozen=True)
class LifecycleRequest:
    operation: str
    actor_id: str
    actor_role: str
    target_agent_id: str
    expected_registry_version: int
    expected_authority_version: str
    now_epoch_ns: int
    requested_owner_id: str = ""
    requested_role: str = ""
    requested_agent_version: str = ""
    requested_expiry_epoch_ns: int = 0
    human_approval_evidence: bool = False
    reason: str = ""

@dataclass(frozen=True)
class LifecycleResult:
    decision: str
    reason_codes: Tuple[str, ...]
    current_record_fingerprint: Optional[str]
    proposed_record: Optional[AgentRecord]
    proposed_registry_version: Optional[int]
    request_fingerprint: str
    cache_reused: bool
    registered: bool = False
    permission_granted: bool = False
    stop_executed: bool = False
    decommission_executed: bool = False
    state_committed: bool = False
    action_succeeded: bool = False


def _canon(x: Any) -> Any:
    if isinstance(x, Enum): return x.value
    if hasattr(x, "__dataclass_fields__"):
        return {k: _canon(v) for k, v in asdict(x).items()}
    if isinstance(x, dict): return {str(k): _canon(v) for k, v in sorted(x.items(), key=lambda kv: str(kv[0]))}
    if isinstance(x, (tuple, list)): return [_canon(v) for v in x]
    return x

def _sha(x: Any) -> str:
    return hashlib.sha256(json.dumps(_canon(x), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def _validate_record(r: AgentRecord) -> Tuple[str, ...]:
    reasons=[]
    if not r.agent_id: reasons.append("AGENT_ID_REQUIRED")
    if not r.owner_id: reasons.append("OWNER_REQUIRED")
    if not r.role: reasons.append("ROLE_REQUIRED")
    if not r.agent_version: reasons.append("AGENT_VERSION_REQUIRED")
    if r.registry_version < 1: reasons.append("REGISTRY_VERSION_INVALID")
    if not r.authority_version: reasons.append("AUTHORITY_VERSION_REQUIRED")
    if r.created_epoch_ns < 0 or r.expires_epoch_ns < 0: reasons.append("TIME_INVALID")
    if r.expires_epoch_ns <= r.created_epoch_ns: reasons.append("EXPIRY_NOT_AFTER_CREATION")
    if r.lifecycle_state not in {x.value for x in LifecycleState}: reasons.append("LIFECYCLE_STATE_INVALID")
    if len(set(r.permit_refs)) != len(r.permit_refs): reasons.append("DUPLICATE_PERMIT_REF")
    if r.lifecycle_state == LifecycleState.DECOMMISSIONED.value and r.decommissioned_epoch_ns is None:
        reasons.append("DECOMMISSION_TIME_REQUIRED")
    return tuple(reasons)

def _validate_registry(state: RegistryState) -> Tuple[str, ...]:
    reasons=[]
    if state.version < 1: reasons.append("REGISTRY_VERSION_INVALID")
    if not state.authority_version: reasons.append("AUTHORITY_VERSION_REQUIRED")
    ids=set()
    for r in state.agents:
        reasons.extend(_validate_record(r))
        if r.agent_id in ids: reasons.append("DUPLICATE_AGENT_ID")
        ids.add(r.agent_id)
        if r.registry_version > state.version: reasons.append("RECORD_VERSION_AHEAD_OF_REGISTRY")
    return tuple(sorted(set(reasons)))

class AgentLifecycleControl:
    """Pure-data lifecycle decision control. Does not persist, stop, grant or commit."""
    def __init__(self):
        self._cache: Dict[str, LifecycleResult] = {}
        self._state_materialization: Dict[int, Tuple[RegistryState, str, Dict[str, AgentRecord], Tuple[str, ...]]] = {}

    def _materialize_state(self, state: RegistryState) -> Tuple[str, Dict[str, AgentRecord], Tuple[str, ...]]:
        # DCSR direct integration: immutable registry Canonical State/Fingerprint,
        # lookup index and structural validation are materialized once per state object.
        key=id(state)
        hit=self._state_materialization.get(key)
        if hit is not None and hit[0] is state:
            return hit[1], hit[2], hit[3]
        errors=_validate_registry(state)
        fp=_sha(state) if not errors else _sha({"invalid_registry": _canon(state)})
        index={r.agent_id:r for r in state.agents}
        self._state_materialization[key]=(state,fp,index,errors)
        return fp,index,errors

    def _find(self, state: RegistryState, agent_id: str) -> Optional[AgentRecord]:
        return self._materialize_state(state)[1].get(agent_id)

    def _fingerprint_request(self, state: RegistryState, req: LifecycleRequest) -> str:
        # Full authoritative state is still bound; only its canonical materialization is reused.
        state_fp,_,_=self._materialize_state(state)
        return _sha({"registry_fingerprint": state_fp, "request": req, "control_version": VERSION})

    def evaluate(self, state: RegistryState, req: LifecycleRequest, use_cache: bool=True) -> LifecycleResult:
        _,_,registry_errors = self._materialize_state(state)
        if registry_errors:
            return LifecycleResult(Decision.DENY.value, registry_errors, None, None, None, _sha({"invalid": _canon(req)}), False)
        if req.operation not in {x.value for x in Operation}:
            return LifecycleResult(Decision.DENY.value, ("OPERATION_INVALID",), None, None, None, _sha(req), False)
        if not req.actor_id or not req.actor_role or not req.target_agent_id:
            return LifecycleResult(Decision.DENY.value, ("REQUEST_IDENTITY_REQUIRED",), None, None, None, _sha(req), False)
        if req.now_epoch_ns < 0:
            return LifecycleResult(Decision.DENY.value, ("TIME_INVALID",), None, None, None, _sha(req), False)

        key = self._fingerprint_request(state, req)
        if use_cache and key in self._cache:
            return replace(self._cache[key], cache_reused=True)

        current = self._find(state, req.target_agent_id)
        current_fp = _sha(current) if current else None
        reasons=[]
        decision=Decision.HOLD.value
        proposed=None
        next_ver=None

        if req.expected_registry_version != state.version:
            reasons.append("REGISTRY_VERSION_MISMATCH")
        if req.expected_authority_version != state.authority_version:
            reasons.append("AUTHORITY_VERSION_MISMATCH")
        if reasons:
            result = LifecycleResult(Decision.HOLD.value, tuple(reasons), current_fp, None, None, key, False)
            if use_cache: self._cache[key]=result
            return result

        op=Operation(req.operation)
        is_admin=req.actor_role in {"registry_admin", "security_admin"}
        is_owner = bool(current and req.actor_id == current.owner_id)

        if op == Operation.REGISTER:
            if current is not None:
                decision=Decision.DENY.value; reasons=["AGENT_ALREADY_REGISTERED"]
            elif not is_admin:
                decision=Decision.DENY.value; reasons=["REGISTER_ADMIN_REQUIRED"]
            elif not req.requested_owner_id or not req.requested_role or not req.requested_agent_version:
                decision=Decision.DENY.value; reasons=["REGISTRATION_FIELDS_REQUIRED"]
            elif req.requested_expiry_epoch_ns <= req.now_epoch_ns:
                decision=Decision.DENY.value; reasons=["EXPIRY_NOT_FUTURE"]
            else:
                next_ver=state.version+1
                proposed=AgentRecord(req.target_agent_id, req.requested_owner_id, req.requested_role, req.requested_agent_version,
                    next_ver, state.authority_version, req.now_epoch_ns, req.requested_expiry_epoch_ns, LifecycleState.PENDING.value)
                decision=Decision.ALLOW_PREPARE.value; reasons=["REGISTRATION_CANDIDATE"]
        elif current is None:
            decision=Decision.DENY.value; reasons=["AGENT_NOT_REGISTERED"]
        else:
            expired = req.now_epoch_ns >= current.expires_epoch_ns
            decommissioned = current.lifecycle_state == LifecycleState.DECOMMISSIONED.value
            if op == Operation.CHECK:
                if decommissioned:
                    decision=Decision.DENY.value; reasons=["AGENT_DECOMMISSIONED"]
                elif current.revoked:
                    decision=Decision.DENY.value; reasons=["AGENT_REVOKED"]
                elif expired:
                    decision=Decision.HOLD.value; reasons=["AGENT_EXPIRED"]
                elif current.lifecycle_state == LifecycleState.SUSPENDED.value:
                    decision=Decision.HOLD.value; reasons=["AGENT_SUSPENDED"]
                elif current.lifecycle_state == LifecycleState.ACTIVE.value:
                    decision=Decision.ALLOW_PREPARE.value; reasons=["AGENT_ACTIVE_CANDIDATE"]
                else:
                    decision=Decision.HOLD.value; reasons=["AGENT_NOT_ACTIVE"]
            elif decommissioned:
                decision=Decision.DENY.value; reasons=["DECOMMISSION_IRREVERSIBLE"]
            elif current.revoked:
                decision=Decision.DENY.value; reasons=["AGENT_REVOKED"]
            elif op == Operation.ACTIVATE:
                if expired:
                    decision=Decision.DENY.value; reasons=["AGENT_EXPIRED"]
                elif not (is_admin or is_owner):
                    decision=Decision.DENY.value; reasons=["ACTIVATE_AUTHORITY_REQUIRED"]
                elif current.lifecycle_state not in {LifecycleState.PENDING.value, LifecycleState.SUSPENDED.value}:
                    decision=Decision.DENY.value; reasons=["ACTIVATE_STATE_INVALID"]
                else:
                    next_ver=state.version+1; proposed=replace(current, lifecycle_state=LifecycleState.ACTIVE.value, registry_version=next_ver)
                    decision=Decision.ALLOW_PREPARE.value; reasons=["ACTIVATION_CANDIDATE"]
            elif op == Operation.SUSPEND:
                if not (is_admin or is_owner):
                    decision=Decision.DENY.value; reasons=["SUSPEND_AUTHORITY_REQUIRED"]
                elif current.lifecycle_state == LifecycleState.SUSPENDED.value:
                    decision=Decision.HOLD.value; reasons=["ALREADY_SUSPENDED"]
                else:
                    next_ver=state.version+1; proposed=replace(current, lifecycle_state=LifecycleState.SUSPENDED.value, registry_version=next_ver)
                    decision=Decision.ALLOW_PREPARE.value; reasons=["SUSPEND_CANDIDATE"]
            elif op == Operation.RENEW:
                if not (is_admin or is_owner):
                    decision=Decision.DENY.value; reasons=["RENEW_AUTHORITY_REQUIRED"]
                elif req.requested_expiry_epoch_ns <= req.now_epoch_ns or req.requested_expiry_epoch_ns <= current.expires_epoch_ns:
                    decision=Decision.DENY.value; reasons=["RENEW_EXPIRY_INVALID"]
                elif not req.human_approval_evidence:
                    decision=Decision.HUMAN_CONFIRM.value; reasons=["RENEWAL_REQUIRES_HUMAN_CONFIRM"]
                else:
                    next_ver=state.version+1; proposed=replace(current, expires_epoch_ns=req.requested_expiry_epoch_ns, registry_version=next_ver)
                    decision=Decision.ALLOW_PREPARE.value; reasons=["RENEWAL_CANDIDATE"]
            elif op == Operation.UPDATE:
                if not is_admin:
                    decision=Decision.DENY.value; reasons=["UPDATE_ADMIN_REQUIRED"]
                elif expired:
                    decision=Decision.HOLD.value; reasons=["AGENT_EXPIRED_RENEW_FIRST"]
                else:
                    next_ver=state.version+1
                    proposed=replace(current,
                        owner_id=req.requested_owner_id or current.owner_id,
                        role=req.requested_role or current.role,
                        agent_version=req.requested_agent_version or current.agent_version,
                        registry_version=next_ver)
                    decision=Decision.ALLOW_PREPARE.value; reasons=["UPDATE_CANDIDATE"]
            elif op == Operation.DECOMMISSION:
                if not is_admin:
                    decision=Decision.DENY.value; reasons=["DECOMMISSION_ADMIN_REQUIRED"]
                elif not req.human_approval_evidence:
                    decision=Decision.HUMAN_CONFIRM.value; reasons=["DECOMMISSION_REQUIRES_HUMAN_CONFIRM"]
                else:
                    next_ver=state.version+1
                    proposed=replace(current, lifecycle_state=LifecycleState.DECOMMISSIONED.value,
                        registry_version=next_ver, decommissioned_epoch_ns=req.now_epoch_ns)
                    decision=Decision.ALLOW_PREPARE.value; reasons=["DECOMMISSION_CANDIDATE"]

        result=LifecycleResult(decision, tuple(reasons), current_fp, proposed, next_ver, key, False)
        if use_cache: self._cache[key]=result
        return result


def registry_delta(old: RegistryState, new: RegistryState) -> Dict[str, Any]:
    """DCSR-style pure-data delta; no persistence/commit."""
    om={r.agent_id:r for r in old.agents}; nm={r.agent_id:r for r in new.agents}
    changed={k:_canon(v) for k,v in nm.items() if k not in om or _sha(om[k]) != _sha(v)}
    removed=sorted(k for k in om if k not in nm)
    return {
        "base_registry_fingerprint": _sha(old),
        "target_registry_fingerprint": _sha(new),
        "base_version": old.version,
        "target_version": new.version,
        "changed": changed,
        "removed": removed,
    }

def apply_delta_candidate(base: RegistryState, delta: Dict[str, Any]) -> RegistryState:
    if _sha(base) != delta["base_registry_fingerprint"]:
        raise ValueError("BASE_FINGERPRINT_MISMATCH")
    m={r.agent_id:r for r in base.agents}
    for k in delta["removed"]: m.pop(k, None)
    for k,v in delta["changed"].items():
        v=dict(v); v["permit_refs"]=tuple(v.get("permit_refs",()))
        m[k]=AgentRecord(**v)
    out=RegistryState(int(delta["target_version"]), base.authority_version, tuple(sorted(m.values(), key=lambda x:x.agent_id)))
    if _sha(out) != delta["target_registry_fingerprint"]:
        raise ValueError("TARGET_FINGERPRINT_MISMATCH")
    return out
