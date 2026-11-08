"""NOEPIN AL 049 — Model Selection / Trust Router.

Pure control-plane evaluator for Model Policy / Local-Cloud Split / Sensitivity Routing.
It selects a deterministic model *route candidate* from caller-supplied model metadata,
without invoking any model, transmitting task data, granting permission, or treating
trust/fingerprint/cache results as truth, verification proof, or execution success.

Creator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support using ChatGPT
License / Rights: NOT SPECIFIED
"""
from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
from hashlib import sha256
import json
from typing import Any, FrozenSet, Iterable, Mapping, Tuple


class ControlDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    HOLD = "HOLD"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"


class ModelLocation(str, Enum):
    LOCAL = "LOCAL"
    EDGE = "EDGE"
    CLOUD = "CLOUD"


class Sensitivity(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"


@dataclass(frozen=True)
class RoutePolicy:
    policy_id: str
    version: str
    authority_epoch: int
    issued_at: int
    expires_at: int
    trusted_providers: FrozenSet[str]
    allowed_locations: FrozenSet[ModelLocation]
    local_required_sensitivities: FrozenSet[Sensitivity]
    cloud_allowed_sensitivities: FrozenSet[Sensitivity]
    cloud_approval_sensitivities: FrozenSet[Sensitivity]
    min_trust_by_sensitivity: Mapping[str, float]
    high_risk_threshold: float
    high_risk_min_trust: float
    max_models: int
    require_verified_model_evidence: bool = True
    revoked: bool = False

    def validate(self, now: int) -> None:
        if not self.policy_id or not self.version:
            raise ValueError("policy id/version required")
        if self.authority_epoch < 1:
            raise ValueError("authority_epoch must be >=1")
        if self.issued_at < 0 or self.expires_at <= self.issued_at:
            raise ValueError("invalid policy lifetime")
        if not self.issued_at <= now < self.expires_at:
            raise ValueError("policy not current")
        if not self.trusted_providers or not self.allowed_locations:
            raise ValueError("trusted providers/locations required")
        if not 0 <= self.high_risk_threshold <= 1 or not 0 <= self.high_risk_min_trust <= 1:
            raise ValueError("invalid risk/trust threshold")
        if self.max_models < 1:
            raise ValueError("max_models must be >=1")
        for s in Sensitivity:
            if s.value not in self.min_trust_by_sensitivity:
                raise ValueError("missing sensitivity trust threshold")
            v=float(self.min_trust_by_sensitivity[s.value])
            if not 0 <= v <= 1:
                raise ValueError("invalid sensitivity trust threshold")
        if not self.local_required_sensitivities <= frozenset(Sensitivity):
            raise ValueError("invalid local-required sensitivity")
        if not self.cloud_allowed_sensitivities <= frozenset(Sensitivity):
            raise ValueError("invalid cloud sensitivity")
        if not self.cloud_approval_sensitivities <= self.cloud_allowed_sensitivities:
            raise ValueError("cloud approval sensitivity must also be cloud-allowed")


@dataclass(frozen=True)
class ModelProfile:
    model_id: str
    provider_id: str
    location: ModelLocation
    capabilities: FrozenSet[str]
    allowed_sensitivities: FrozenSet[Sensitivity]
    trust_score: float
    max_risk: float
    issued_at: int
    expires_at: int
    evidence_binding: str
    evidence_verified: bool
    profile_version: str = "1"
    revoked: bool = False

    def validate(self, now: int) -> None:
        if not self.model_id or not self.provider_id or not self.profile_version:
            raise ValueError("model/provider/version required")
        if not self.capabilities or not self.allowed_sensitivities:
            raise ValueError("capabilities/sensitivities required")
        if not 0 <= self.trust_score <= 1 or not 0 <= self.max_risk <= 1:
            raise ValueError("invalid model trust/risk")
        if self.issued_at < 0 or self.expires_at <= self.issued_at:
            raise ValueError("invalid model lifetime")
        if not self.issued_at <= now < self.expires_at:
            raise ValueError("model profile not current")
        if not self.evidence_binding:
            raise ValueError("model evidence binding required")


@dataclass(frozen=True)
class RouteRequest:
    request_id: str
    task_id: str
    purpose: str
    sensitivity: Sensitivity
    risk_score: float
    required_capabilities: FrozenSet[str]
    evidence_binding: str
    expected_policy_id: str
    expected_policy_version: str
    expected_authority_epoch: int
    external_processing_allowed: bool
    human_approval_evidence_verified: bool = False

    def validate(self) -> None:
        if not self.request_id or not self.task_id or not self.purpose or not self.evidence_binding:
            raise ValueError("request/task/purpose/evidence required")
        if not self.required_capabilities:
            raise ValueError("required capabilities required")
        if not 0 <= self.risk_score <= 1:
            raise ValueError("risk score out of range")
        if not self.expected_policy_id or not self.expected_policy_version or self.expected_authority_epoch < 1:
            raise ValueError("expected policy binding required")


@dataclass(frozen=True)
class PreparedModelRegistry:
    registry_fingerprint: str
    policy_fingerprint: str
    profiles: Tuple[ModelProfile, ...]
    profile_fingerprints: Mapping[str, str]
    capability_index: Mapping[str, Tuple[str, ...]]
    sensitivity_index: Mapping[str, Tuple[str, ...]]
    location_index: Mapping[str, Tuple[str, ...]]


@dataclass(frozen=True)
class RegistryDelta:
    base_fingerprint: str
    target_fingerprint: str
    changed_profiles: Tuple[ModelProfile, ...]
    removed_model_ids: Tuple[str, ...]
    added_profiles: Tuple[ModelProfile, ...]


@dataclass(frozen=True)
class RegistrySyncPlan:
    missing_or_changed_model_ids: Tuple[str, ...]
    metadata_bytes_required: int
    full_metadata_bytes: int
    full_resend_required: bool
    permission_granted: bool = False
    model_invocation_authorized: bool = False
    data_transfer_authorized: bool = False


@dataclass(frozen=True)
class RouteAssessment:
    decision: ControlDecision
    reasons: Tuple[str, ...]
    request_id: str
    task_id: str
    selected_model_id: str | None
    selected_location: str | None
    selected_provider_id: str | None
    eligible_model_ids: Tuple[str, ...]
    rejected_model_reasons: Mapping[str, Tuple[str, ...]]
    registry_fingerprint: str
    policy_fingerprint: str
    request_fingerprint: str
    permission_granted: bool = False
    model_invoked: bool = False
    data_transferred: bool = False
    action_success: bool = False
    trust_truth_established: bool = False
    verification_pass_proven: bool = False


def _canonical(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {f.name:_canonical(getattr(value,f.name)) for f in fields(value)}
    if isinstance(value, Mapping):
        return {str(k):_canonical(v) for k,v in sorted(value.items(), key=lambda kv:str(kv[0]))}
    if isinstance(value, (set,frozenset)):
        vals=[_canonical(v) for v in value]
        return sorted(vals,key=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":")))
    if isinstance(value,(tuple,list)):
        return [_canonical(v) for v in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(_canonical(value),ensure_ascii=False,sort_keys=True,separators=(",",":"))


def fingerprint(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _normalize_profiles(profiles: Iterable[ModelProfile], *, now: int | None = None) -> Tuple[ModelProfile, ...]:
    out=tuple(sorted(profiles,key=lambda p:p.model_id))
    ids=[p.model_id for p in out]
    if len(ids)!=len(set(ids)):
        raise ValueError("duplicate model_id")
    if now is not None:
        for p in out: p.validate(now)
    return out


def registry_fingerprint(profiles: Iterable[ModelProfile]) -> str:
    return fingerprint(_normalize_profiles(profiles))


def prepare_registry(policy: RoutePolicy, profiles: Iterable[ModelProfile], *, now: int) -> PreparedModelRegistry:
    policy.validate(now)
    if policy.revoked:
        raise ValueError("policy revoked")
    items=_normalize_profiles(profiles,now=now)
    if len(items)>policy.max_models:
        raise ValueError("model count exceeds policy")
    fps={p.model_id:fingerprint(p) for p in items}
    cap:dict[str,list[str]]={}; sens:dict[str,list[str]]={}; loc:dict[str,list[str]]={}
    for p in items:
        for c in p.capabilities: cap.setdefault(c,[]).append(p.model_id)
        for s in p.allowed_sensitivities: sens.setdefault(s.value,[]).append(p.model_id)
        loc.setdefault(p.location.value,[]).append(p.model_id)
    return PreparedModelRegistry(
        registry_fingerprint=registry_fingerprint(items),
        policy_fingerprint=fingerprint(policy),
        profiles=items,
        profile_fingerprints=fps,
        capability_index={k:tuple(sorted(v)) for k,v in sorted(cap.items())},
        sensitivity_index={k:tuple(sorted(v)) for k,v in sorted(sens.items())},
        location_index={k:tuple(sorted(v)) for k,v in sorted(loc.items())},
    )


def _empty(req: RouteRequest, profiles: Iterable[ModelProfile], policy: RoutePolicy, decision: ControlDecision, reasons: Tuple[str,...]) -> RouteAssessment:
    try: rf=registry_fingerprint(profiles)
    except Exception: rf=fingerprint(tuple())
    try: pf=fingerprint(policy)
    except Exception: pf=fingerprint("INVALID_POLICY")
    try: qf=fingerprint(req)
    except Exception: qf=fingerprint("INVALID_REQUEST")
    return RouteAssessment(decision,tuple(sorted(set(reasons))),getattr(req,"request_id",""),getattr(req,"task_id",""),None,None,None,tuple(),{},rf,pf,qf)


def _profile_rejection_reasons(req: RouteRequest, policy: RoutePolicy, p: ModelProfile, *, now: int) -> Tuple[str,...]:
    reasons=[]
    try: p.validate(now)
    except ValueError as exc:
        return (f"PROFILE_INVALID:{exc}",)
    if p.revoked: reasons.append("MODEL_REVOKED")
    if p.provider_id not in policy.trusted_providers: reasons.append("UNTRUSTED_PROVIDER")
    if p.location not in policy.allowed_locations: reasons.append("LOCATION_NOT_ALLOWED")
    if req.sensitivity not in p.allowed_sensitivities: reasons.append("SENSITIVITY_NOT_SUPPORTED")
    if req.sensitivity in policy.local_required_sensitivities and p.location != ModelLocation.LOCAL:
        reasons.append("LOCAL_REQUIRED")
    if p.location == ModelLocation.CLOUD:
        if req.sensitivity not in policy.cloud_allowed_sensitivities: reasons.append("CLOUD_SENSITIVITY_NOT_ALLOWED")
        if not req.external_processing_allowed: reasons.append("EXTERNAL_PROCESSING_NOT_ALLOWED")
    if not req.required_capabilities <= p.capabilities: reasons.append("CAPABILITY_GAP")
    min_trust=float(policy.min_trust_by_sensitivity[req.sensitivity.value])
    if p.trust_score < min_trust: reasons.append("TRUST_BELOW_SENSITIVITY_THRESHOLD")
    if req.risk_score >= policy.high_risk_threshold and p.trust_score < policy.high_risk_min_trust:
        reasons.append("TRUST_BELOW_HIGH_RISK_THRESHOLD")
    if req.risk_score > p.max_risk: reasons.append("MODEL_RISK_CEILING_EXCEEDED")
    if policy.require_verified_model_evidence and not p.evidence_verified: reasons.append("MODEL_EVIDENCE_UNVERIFIED")
    if p.evidence_binding != req.evidence_binding: reasons.append("EVIDENCE_BINDING_MISMATCH")
    return tuple(sorted(set(reasons)))


def _rank_key(req: RouteRequest, p: ModelProfile) -> tuple:
    # Deterministic and sensitivity-aware: stronger location privacy first, then trust.
    loc_rank={ModelLocation.LOCAL:0,ModelLocation.EDGE:1,ModelLocation.CLOUD:2}
    # PUBLIC tasks may use any trusted model; trust remains dominant after location privacy.
    return (loc_rank[p.location], -p.trust_score, -p.max_risk, p.provider_id, p.model_id)


def evaluate_prepared(req: RouteRequest, policy: RoutePolicy, profiles: Iterable[ModelProfile], prepared: PreparedModelRegistry, *, now: int) -> RouteAssessment:
    try:
        req.validate(); policy.validate(now)
    except ValueError as exc:
        return _empty(req,profiles,policy,ControlDecision.HOLD,(f"VALIDATION_FAILED:{exc}",))
    if policy.revoked: return _empty(req,profiles,policy,ControlDecision.HOLD,("POLICY_REVOKED",))
    if (req.expected_policy_id,req.expected_policy_version,req.expected_authority_epoch)!=(policy.policy_id,policy.version,policy.authority_epoch):
        return _empty(req,profiles,policy,ControlDecision.HOLD,("POLICY_BINDING_MISMATCH",))
    if prepared.policy_fingerprint != fingerprint(policy):
        return _empty(req,profiles,policy,ControlDecision.HOLD,("PREPARED_POLICY_FINGERPRINT_MISMATCH",))
    if prepared.registry_fingerprint != registry_fingerprint(profiles):
        return _empty(req,profiles,policy,ControlDecision.HOLD,("PREPARED_REGISTRY_FINGERPRINT_MISMATCH",))

    rejected={}; eligible=[]
    for p in prepared.profiles:
        rs=_profile_rejection_reasons(req,policy,p,now=now)
        if rs: rejected[p.model_id]=rs
        else: eligible.append(p)
    if not eligible:
        return RouteAssessment(ControlDecision.DENY,("NO_ELIGIBLE_MODEL",),req.request_id,req.task_id,None,None,None,tuple(),rejected,prepared.registry_fingerprint,prepared.policy_fingerprint,fingerprint(req))

    eligible=sorted(eligible,key=lambda p:_rank_key(req,p))
    selected=eligible[0]
    reasons={"ROUTE_CANDIDATE_SELECTED"}
    decision=ControlDecision.ALLOW
    if selected.location == ModelLocation.CLOUD and req.sensitivity in policy.cloud_approval_sensitivities and not req.human_approval_evidence_verified:
        decision=ControlDecision.HUMAN_APPROVAL
        reasons.add("CLOUD_ROUTE_REQUIRES_HUMAN_APPROVAL_EVIDENCE")
    elif selected.location == ModelLocation.CLOUD and req.sensitivity in policy.cloud_approval_sensitivities:
        reasons.add("HUMAN_APPROVAL_EVIDENCE_PRESENT")
    if selected.location == ModelLocation.LOCAL: reasons.add("LOCAL_ROUTE_PREFERRED")
    elif selected.location == ModelLocation.EDGE: reasons.add("EDGE_ROUTE_SELECTED")
    else: reasons.add("CLOUD_ROUTE_SELECTED")
    return RouteAssessment(
        decision=decision,reasons=tuple(sorted(reasons)),request_id=req.request_id,task_id=req.task_id,
        selected_model_id=selected.model_id,selected_location=selected.location.value,selected_provider_id=selected.provider_id,
        eligible_model_ids=tuple(p.model_id for p in eligible),rejected_model_reasons={k:rejected[k] for k in sorted(rejected)},
        registry_fingerprint=prepared.registry_fingerprint,policy_fingerprint=prepared.policy_fingerprint,request_fingerprint=fingerprint(req)
    )


def evaluate(req: RouteRequest, policy: RoutePolicy, profiles: Iterable[ModelProfile], *, now: int) -> RouteAssessment:
    profiles=tuple(profiles)
    try: prepared=prepare_registry(policy,profiles,now=now)
    except ValueError as exc: return _empty(req,profiles,policy,ControlDecision.HOLD,(f"PREPARE_FAILED:{exc}",))
    return evaluate_prepared(req,policy,profiles,prepared,now=now)


def build_registry_delta(base: Iterable[ModelProfile], target: Iterable[ModelProfile]) -> RegistryDelta:
    b={p.model_id:p for p in _normalize_profiles(base)}; t={p.model_id:p for p in _normalize_profiles(target)}
    changed=tuple(t[k] for k in sorted(b.keys()&t.keys()) if fingerprint(b[k])!=fingerprint(t[k]))
    removed=tuple(sorted(b.keys()-t.keys())); added=tuple(t[k] for k in sorted(t.keys()-b.keys()))
    return RegistryDelta(registry_fingerprint(b.values()),registry_fingerprint(t.values()),changed,removed,added)


def apply_registry_delta(base: Iterable[ModelProfile], delta: RegistryDelta) -> Tuple[ModelProfile,...]:
    if registry_fingerprint(base)!=delta.base_fingerprint: raise ValueError("base fingerprint mismatch")
    d={p.model_id:p for p in _normalize_profiles(base)}
    for k in delta.removed_model_ids: d.pop(k,None)
    for p in delta.changed_profiles+delta.added_profiles: d[p.model_id]=p
    target=_normalize_profiles(d.values())
    if registry_fingerprint(target)!=delta.target_fingerprint: raise ValueError("target fingerprint mismatch")
    return target


def plan_registry_sync(prepared: PreparedModelRegistry, known_profile_fingerprints: Mapping[str,str]) -> RegistrySyncPlan:
    missing=tuple(sorted(k for k,v in prepared.profile_fingerprints.items() if known_profile_fingerprints.get(k)!=v))
    m={p.model_id:p for p in prepared.profiles}
    payload=tuple(m[k] for k in missing)
    needed=len(canonical_json(payload).encode("utf-8")); full=len(canonical_json(prepared.profiles).encode("utf-8"))
    return RegistrySyncPlan(missing,needed,full,needed>=full)


def assessment_digest(items: Iterable[RouteAssessment]) -> str:
    return fingerprint(tuple(items))


def default_policy(now: int) -> RoutePolicy:
    return RoutePolicy(
        policy_id="MODEL-ROUTE-POLICY-1",version="1",authority_epoch=1,issued_at=now-100,expires_at=now+10000,
        trusted_providers=frozenset({"NOEPIN_LOCAL","TRUSTED_EDGE","TRUSTED_CLOUD"}),
        allowed_locations=frozenset({ModelLocation.LOCAL,ModelLocation.EDGE,ModelLocation.CLOUD}),
        local_required_sensitivities=frozenset({Sensitivity.RESTRICTED}),
        cloud_allowed_sensitivities=frozenset({Sensitivity.PUBLIC,Sensitivity.INTERNAL,Sensitivity.CONFIDENTIAL}),
        cloud_approval_sensitivities=frozenset({Sensitivity.CONFIDENTIAL}),
        min_trust_by_sensitivity={"PUBLIC":0.50,"INTERNAL":0.70,"CONFIDENTIAL":0.85,"RESTRICTED":0.90},
        high_risk_threshold=0.70,high_risk_min_trust=0.90,max_models=10000,
    )


def default_profiles(now: int) -> Tuple[ModelProfile,...]:
    b="MODEL-ROUTE-EVIDENCE-49"
    return (
        ModelProfile("LOCAL-TRUST-1","NOEPIN_LOCAL",ModelLocation.LOCAL,frozenset({"TEXT","CODE","ANALYSIS"}),frozenset(Sensitivity),0.96,0.95,now-100,now+10000,b,True),
        ModelProfile("EDGE-TRUST-1","TRUSTED_EDGE",ModelLocation.EDGE,frozenset({"TEXT","ANALYSIS"}),frozenset({Sensitivity.PUBLIC,Sensitivity.INTERNAL,Sensitivity.CONFIDENTIAL}),0.90,0.85,now-100,now+10000,b,True),
        ModelProfile("CLOUD-TRUST-1","TRUSTED_CLOUD",ModelLocation.CLOUD,frozenset({"TEXT","CODE","ANALYSIS"}),frozenset({Sensitivity.PUBLIC,Sensitivity.INTERNAL,Sensitivity.CONFIDENTIAL}),0.94,0.95,now-100,now+10000,b,True),
    )


def default_request(now: int) -> RouteRequest:
    p=default_policy(now)
    return RouteRequest("REQ-49","TASK-49","BUILD_SUCCESSOR",Sensitivity.INTERNAL,0.40,frozenset({"TEXT","ANALYSIS"}),"MODEL-ROUTE-EVIDENCE-49",p.policy_id,p.version,p.authority_epoch,True,False)


__all__=[
    "ControlDecision","ModelLocation","Sensitivity","RoutePolicy","ModelProfile","RouteRequest","PreparedModelRegistry","RegistryDelta","RegistrySyncPlan","RouteAssessment",
    "canonical_json","fingerprint","registry_fingerprint","prepare_registry","evaluate","evaluate_prepared","build_registry_delta","apply_registry_delta","plan_registry_sync","assessment_digest",
    "default_policy","default_profiles","default_request"
]
