from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from hashlib import sha256
from typing import Any, Iterable, Mapping, Sequence
import json
import time

CREATOR = "NOEPIN / のえぴん"
PROJECT_OWNER = CREATOR
ORIGINAL_CONCEPT = CREATOR
ARCHITECTURE_DIRECTION = CREATOR
AI_SUPPORT = "AI-assisted implementation / analysis / documentation support using ChatGPT"
LICENSE_RIGHTS = "NOT SPECIFIED"
TECHNOLOGY_NUMBER = 39
TECHNOLOGY_NAME = "規格・社内ルール照合エンジン"
SCHEMA_VERSION = "NOEPIN_AL_039_V2"


class Decision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    HOLD = "HOLD"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EvidenceStatus(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    UNVERIFIED = "UNVERIFIED"
    REVOKED = "REVOKED"


class Operator(str, Enum):
    EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"
    IN = "IN"
    CONTAINS = "CONTAINS"
    PRESENT = "PRESENT"
    TRUE = "TRUE"
    FALSE = "FALSE"


@dataclass(frozen=True)
class Rule:
    rule_id: str
    source: str
    source_version: str
    control_id: str
    field: str
    operator: Operator
    expected: Any = None
    severity: Severity = Severity.MEDIUM
    required_evidence_type: str | None = None
    requires_human_review: bool = False
    enabled: bool = True

    def validate(self) -> None:
        for name, value in (
            ("rule_id", self.rule_id),
            ("source", self.source),
            ("source_version", self.source_version),
            ("control_id", self.control_id),
            ("field", self.field),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be non-empty")
        if self.operator in {Operator.IN, Operator.CONTAINS} and self.expected is None:
            raise ValueError("expected is required for collection operators")


@dataclass(frozen=True)
class RuleProfile:
    profile_id: str
    profile_version: str
    authority_epoch: int
    issued_at: int
    expires_at: int
    revoked: bool = False
    rules: tuple[Rule, ...] = field(default_factory=tuple)

    def validate(self, now: int) -> None:
        if not self.profile_id or not self.profile_version:
            raise ValueError("profile id/version required")
        if self.authority_epoch < 0:
            raise ValueError("authority_epoch must be non-negative")
        if self.issued_at < 0 or self.expires_at <= self.issued_at:
            raise ValueError("invalid profile lifetime")
        if self.revoked:
            raise ValueError("profile revoked")
        if now < self.issued_at:
            raise ValueError("profile not yet valid")
        if now >= self.expires_at:
            raise ValueError("profile expired")
        ids: set[str] = set()
        for rule in self.rules:
            rule.validate()
            if rule.rule_id in ids:
                raise ValueError("duplicate rule_id")
            ids.add(rule.rule_id)


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    evidence_type: str
    status: EvidenceStatus
    observed_at: int
    expires_at: int
    subject_id: str
    profile_id: str
    profile_version: str
    authority_epoch: int
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def valid_for(self, request: "EvaluationRequest", profile: RuleProfile, now: int) -> bool:
        return bool(
            self.evidence_id
            and self.evidence_type
            and self.status is EvidenceStatus.VALID
            and self.observed_at <= now < self.expires_at
            and self.subject_id == request.subject_id
            and self.profile_id == profile.profile_id
            and self.profile_version == profile.profile_version
            and self.authority_epoch == profile.authority_epoch
        )


@dataclass(frozen=True)
class EvaluationRequest:
    request_id: str
    subject_id: str
    operation: str
    attributes: Mapping[str, Any]
    requested_sources: tuple[str, ...] = field(default_factory=tuple)

    def validate(self) -> None:
        if not self.request_id or not self.subject_id or not self.operation:
            raise ValueError("request_id, subject_id, and operation are required")
        if not isinstance(self.attributes, Mapping):
            raise ValueError("attributes must be a mapping")


@dataclass(frozen=True)
class Finding:
    rule_id: str
    control_id: str
    source: str
    source_version: str
    severity: Severity
    matched: bool
    evidence_valid: bool
    reason: str


@dataclass(frozen=True)
class EvaluationResult:
    decision: Decision
    request_id: str
    subject_id: str
    profile_id: str
    profile_version: str
    authority_epoch: int
    findings: tuple[Finding, ...]
    gap_rule_ids: tuple[str, ...]
    human_review_rule_ids: tuple[str, ...]
    fingerprint: str
    authoritative_compliance_proven: bool = False
    action_executed: bool = False


@dataclass(frozen=True)
class PreparedContext:
    request: EvaluationRequest
    profile: RuleProfile
    evidence: tuple[Evidence, ...]
    now: int
    request_fingerprint: str
    profile_fingerprint: str
    evidence_fingerprint: str
    state_fingerprint: str


@dataclass(frozen=True)
class ProfileDelta:
    base_fingerprint: str
    target_fingerprint: str
    added_rules: tuple[Rule, ...]
    removed_rule_ids: tuple[str, ...]
    changed_rules: tuple[Rule, ...]
    target_profile_id: str
    target_profile_version: str
    target_authority_epoch: int
    target_issued_at: int
    target_expires_at: int
    target_revoked: bool


def _jsonable(value: Any) -> Any:
    if isinstance(value, RuleProfile):
        return {
            "profile_id": value.profile_id,
            "profile_version": value.profile_version,
            "authority_epoch": value.authority_epoch,
            "issued_at": value.issued_at,
            "expires_at": value.expires_at,
            "revoked": value.revoked,
            "rules": [_jsonable(r) for r in sorted(value.rules, key=lambda r: r.rule_id)],
        }
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(k): _jsonable(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (tuple, list, set, frozenset)):
        seq = [_jsonable(v) for v in value]
        if isinstance(value, (set, frozenset)):
            seq.sort(key=lambda x: json.dumps(x, sort_keys=True, ensure_ascii=False))
        return seq
    if hasattr(value, "__dataclass_fields__"):
        return {k: _jsonable(v) for k, v in asdict(value).items()}
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(_jsonable(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _get_field(attributes: Mapping[str, Any], path: str) -> tuple[bool, Any]:
    current: Any = attributes
    for part in path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return False, None
        current = current[part]
    return True, current


def _match(operator: Operator, exists: bool, actual: Any, expected: Any) -> bool:
    if operator is Operator.PRESENT:
        return exists
    if not exists:
        return False
    if operator is Operator.EQUALS:
        return actual == expected
    if operator is Operator.NOT_EQUALS:
        return actual != expected
    if operator is Operator.IN:
        try:
            return actual in expected
        except TypeError:
            return False
    if operator is Operator.CONTAINS:
        try:
            return expected in actual
        except TypeError:
            return False
    if operator is Operator.TRUE:
        return actual is True
    if operator is Operator.FALSE:
        return actual is False
    return False


def prepare_context(
    request: EvaluationRequest,
    profile: RuleProfile,
    evidence: Sequence[Evidence],
    *,
    now: int | None = None,
) -> PreparedContext:
    ts = int(time.time()) if now is None else int(now)
    request.validate()
    profile.validate(ts)
    frozen_evidence = tuple(evidence)
    req_fp = fingerprint(request)
    profile_fp = fingerprint(profile)
    evidence_fp = fingerprint(frozen_evidence)
    return PreparedContext(
        request=request,
        profile=profile,
        evidence=frozen_evidence,
        now=ts,
        request_fingerprint=req_fp,
        profile_fingerprint=profile_fp,
        evidence_fingerprint=evidence_fp,
        state_fingerprint=fingerprint({
            "request": req_fp,
            "profile": profile_fp,
            "evidence": evidence_fp,
            "authority_epoch": profile.authority_epoch,
        }),
    )


def evaluate_prepared(ctx: PreparedContext) -> EvaluationResult:
    request = ctx.request
    profile = ctx.profile
    now = ctx.now
    valid_evidence_by_type: dict[str, list[Evidence]] = {}
    for ev in ctx.evidence:
        if ev.valid_for(request, profile, now):
            valid_evidence_by_type.setdefault(ev.evidence_type, []).append(ev)

    findings: list[Finding] = []
    gaps: list[str] = []
    human: list[str] = []
    critical_gap = False
    high_gap = False

    requested = set(request.requested_sources)
    for rule in sorted(profile.rules, key=lambda r: r.rule_id):
        if not rule.enabled:
            continue
        if requested and rule.source not in requested:
            continue
        exists, actual = _get_field(request.attributes, rule.field)
        matched = _match(rule.operator, exists, actual, rule.expected)
        evidence_valid = True
        if rule.required_evidence_type:
            evidence_valid = bool(valid_evidence_by_type.get(rule.required_evidence_type))
        pass_rule = matched and evidence_valid
        if not pass_rule:
            gaps.append(rule.rule_id)
            if rule.severity is Severity.CRITICAL:
                critical_gap = True
            elif rule.severity is Severity.HIGH:
                high_gap = True
        if rule.requires_human_review:
            human.append(rule.rule_id)
        reason = "matched_with_valid_evidence" if pass_rule else (
            "evidence_missing_or_invalid" if matched and not evidence_valid else "rule_mismatch"
        )
        findings.append(Finding(
            rule_id=rule.rule_id,
            control_id=rule.control_id,
            source=rule.source,
            source_version=rule.source_version,
            severity=rule.severity,
            matched=matched,
            evidence_valid=evidence_valid,
            reason=reason,
        ))

    if not findings:
        decision = Decision.HOLD
    elif critical_gap:
        decision = Decision.DENY
    elif human:
        decision = Decision.HUMAN_APPROVAL
    elif high_gap or gaps:
        decision = Decision.HOLD
    else:
        decision = Decision.ALLOW

    body = {
        "decision": decision.value,
        "request_id": request.request_id,
        "subject_id": request.subject_id,
        "profile_id": profile.profile_id,
        "profile_version": profile.profile_version,
        "authority_epoch": profile.authority_epoch,
        "findings": findings,
        "gap_rule_ids": gaps,
        "human_review_rule_ids": human,
        "state_fingerprint": ctx.state_fingerprint,
    }
    return EvaluationResult(
        decision=decision,
        request_id=request.request_id,
        subject_id=request.subject_id,
        profile_id=profile.profile_id,
        profile_version=profile.profile_version,
        authority_epoch=profile.authority_epoch,
        findings=tuple(findings),
        gap_rule_ids=tuple(gaps),
        human_review_rule_ids=tuple(human),
        fingerprint=fingerprint(body),
        authoritative_compliance_proven=False,
        action_executed=False,
    )


def evaluate(
    request: EvaluationRequest,
    profile: RuleProfile,
    evidence: Sequence[Evidence],
    *,
    now: int | None = None,
) -> EvaluationResult:
    return evaluate_prepared(prepare_context(request, profile, evidence, now=now))


def gap_report(result: EvaluationResult) -> Mapping[str, Any]:
    return {
        "decision": result.decision.value,
        "profile": f"{result.profile_id}@{result.profile_version}",
        "authority_epoch": result.authority_epoch,
        "gaps": [
            {
                "rule_id": f.rule_id,
                "control_id": f.control_id,
                "source": f.source,
                "source_version": f.source_version,
                "severity": f.severity.value,
                "reason": f.reason,
            }
            for f in result.findings if f.rule_id in result.gap_rule_ids
        ],
        "human_review_rule_ids": list(result.human_review_rule_ids),
        "compliance_proven": False,
        "action_executed": False,
    }


def make_profile_delta(base: RuleProfile, target: RuleProfile) -> ProfileDelta:
    base_fp = fingerprint(base)
    target_fp = fingerprint(target)
    base_map = {r.rule_id: r for r in base.rules}
    target_map = {r.rule_id: r for r in target.rules}
    added = tuple(target_map[k] for k in sorted(target_map.keys() - base_map.keys()))
    removed = tuple(sorted(base_map.keys() - target_map.keys()))
    changed = tuple(target_map[k] for k in sorted(base_map.keys() & target_map.keys()) if target_map[k] != base_map[k])
    return ProfileDelta(
        base_fingerprint=base_fp,
        target_fingerprint=target_fp,
        added_rules=added,
        removed_rule_ids=removed,
        changed_rules=changed,
        target_profile_id=target.profile_id,
        target_profile_version=target.profile_version,
        target_authority_epoch=target.authority_epoch,
        target_issued_at=target.issued_at,
        target_expires_at=target.expires_at,
        target_revoked=target.revoked,
    )


def apply_profile_delta(base: RuleProfile, delta: ProfileDelta) -> RuleProfile:
    if fingerprint(base) != delta.base_fingerprint:
        raise ValueError("base fingerprint mismatch")
    rule_map = {r.rule_id: r for r in base.rules}
    for rid in delta.removed_rule_ids:
        rule_map.pop(rid, None)
    for rule in delta.changed_rules:
        rule_map[rule.rule_id] = rule
    for rule in delta.added_rules:
        if rule.rule_id in rule_map:
            raise ValueError("delta add collision")
        rule_map[rule.rule_id] = rule
    result = RuleProfile(
        profile_id=delta.target_profile_id,
        profile_version=delta.target_profile_version,
        authority_epoch=delta.target_authority_epoch,
        issued_at=delta.target_issued_at,
        expires_at=delta.target_expires_at,
        revoked=delta.target_revoked,
        rules=tuple(rule_map[k] for k in sorted(rule_map)),
    )
    if fingerprint(result) != delta.target_fingerprint:
        raise ValueError("target fingerprint mismatch")
    return result


def profile_from_dict(data: Mapping[str, Any]) -> RuleProfile:
    rules = []
    for raw in data.get("rules", []):
        rules.append(Rule(
            rule_id=str(raw["rule_id"]),
            source=str(raw["source"]),
            source_version=str(raw["source_version"]),
            control_id=str(raw["control_id"]),
            field=str(raw["field"]),
            operator=Operator(str(raw["operator"])),
            expected=raw.get("expected"),
            severity=Severity(str(raw.get("severity", "MEDIUM"))),
            required_evidence_type=raw.get("required_evidence_type"),
            requires_human_review=bool(raw.get("requires_human_review", False)),
            enabled=bool(raw.get("enabled", True)),
        ))
    return RuleProfile(
        profile_id=str(data["profile_id"]),
        profile_version=str(data["profile_version"]),
        authority_epoch=int(data["authority_epoch"]),
        issued_at=int(data["issued_at"]),
        expires_at=int(data["expires_at"]),
        revoked=bool(data.get("revoked", False)),
        rules=tuple(rules),
    )
