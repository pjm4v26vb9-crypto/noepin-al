"""Actual NOEPIN AL production-gate use for Technology 040.

This script consumes already-completed AL 037/038/039 modules. It is a build-time
verification helper; it does not change those artifacts or grant production authority.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from enum import Enum
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def stable(v):
    if isinstance(v, Enum):
        return v.value
    if hasattr(v, "__dataclass_fields__"):
        return {k: stable(x) for k, x in asdict(v).items()}
    if isinstance(v, dict):
        return {str(k): stable(x) for k, x in sorted(v.items())}
    if isinstance(v, (set, frozenset, tuple, list)):
        vals = [stable(x) for x in v]
        if isinstance(v, (set, frozenset)):
            vals.sort(key=lambda x: json.dumps(x, sort_keys=True, ensure_ascii=False))
        return vals
    return v


def file_sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--al037", type=Path, required=True)
    ap.add_argument("--al038", type=Path, required=True)
    ap.add_argument("--al039", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    a37 = load("al037", args.al037)
    a38 = load("al038", args.al038)
    a39 = load("al039", args.al039)
    now = 1_800_000_000

    profile37 = a37.SafeProfile(
        profile_id="NOEPIN-AL-BUILD-040",
        policy_version="1",
        issued_at=now - 100,
        expires_at=now + 10_000,
        revoked=False,
        allowed_operations=frozenset({"BUILD_SUCCESSOR"}),
        denied_operations=frozenset(),
        human_approval_operations=frozenset(),
        offline_allowed_operations=frozenset({"BUILD_SUCCESSOR"}),
        allowed_capabilities=frozenset({"LOCAL_ARTIFACT_WRITE", "LOCAL_TEST", "NOTION_EVIDENCE_UPDATE"}),
        required_metadata=frozenset({"artifact", "scope"}),
        max_risk_allow=1,
        max_impact_allow=1,
        max_risk_human_approval=3,
        max_impact_human_approval=3,
        require_offline_for_critical=True,
    )
    req37 = a37.SafetyRequest(
        request_id="BUILD-040",
        actor="NOEPIN",
        operation="BUILD_SUCCESSOR",
        resource="NOEPIN-AL-040",
        risk_level=1,
        impact_scope=1,
        requested_capabilities=frozenset({"LOCAL_ARTIFACT_WRITE", "LOCAL_TEST", "NOTION_EVIDENCE_UPDATE"}),
        metadata={"artifact": "NOEPIN-AL-040", "scope": "NOEPIN AL only"},
        network_required=False,
        offline_mode=True,
        manual_override_requested=False,
        expected_policy_version="1",
    )
    auth37 = a37.AuthorityContext(
        active_actor=True,
        actor_revoked=False,
        permission_grants=frozenset({"BUILD_SUCCESSOR@NOEPIN-AL-040"}),
        authority_epoch="NOEPIN-AL-BUILD-040-E1",
    )
    d37 = a37.evaluate(req37, profile37, auth37, now=now)

    policy38 = a38.MemoryPolicy(
        policy_id="NOEPIN-AL-BUILD-EVIDENCE",
        version=1,
        authority_epoch=1,
        allowed_purposes=frozenset({"verification_evidence"}),
        default_retention_seconds=86_400,
        max_retention_seconds=604_800,
        classifications_allowed=frozenset({"INTERNAL"}),
        delete_requires_human=False,
        store_requires_human=False,
        revoked=False,
    )
    req38 = a38.MemoryRequest(
        operation="STORE",
        purpose="verification_evidence",
        now=now,
        requested_retention_seconds=86_400,
        classification="INTERNAL",
        expected_policy_id=policy38.policy_id,
        expected_policy_version=policy38.version,
        expected_authority_epoch=policy38.authority_epoch,
    )
    d38 = a38.evaluate(policy38, req38, None)

    rules39 = (
        a39.Rule("R1", "NOEPIN_BUILD_POLICY", "1", "NO_EXTERNAL_EXEC", "static_no_external_execution", a39.Operator.TRUE, severity=a39.Severity.CRITICAL),
        a39.Rule("R2", "NOEPIN_BUILD_POLICY", "1", "NO_NETWORK", "static_no_network", a39.Operator.TRUE, severity=a39.Severity.HIGH),
        a39.Rule("R3", "NOEPIN_BUILD_POLICY", "1", "AUTHORITY_BOUNDARY", "authority_boundaries_declared", a39.Operator.TRUE, severity=a39.Severity.HIGH),
        a39.Rule("R4", "NOEPIN_BUILD_POLICY", "1", "DCSR_NO_AUTHORITY", "dcsr_no_authority", a39.Operator.TRUE, severity=a39.Severity.HIGH),
        a39.Rule("R5", "NOEPIN_BUILD_POLICY", "1", "BASELINE_IMMUTABLE", "baseline_immutable", a39.Operator.TRUE, severity=a39.Severity.CRITICAL),
        a39.Rule("R6", "NOEPIN_BUILD_POLICY", "1", "LICENSE_UNSPECIFIED", "license_not_specified", a39.Operator.TRUE, severity=a39.Severity.MEDIUM),
    )
    profile39 = a39.RuleProfile(
        profile_id="NOEPIN-AL-BUILD-040",
        profile_version="1",
        authority_epoch=1,
        issued_at=now - 100,
        expires_at=now + 10_000,
        revoked=False,
        rules=rules39,
    )
    req39 = a39.EvaluationRequest(
        request_id="BUILD-040",
        subject_id="NOEPIN-AL-040-SUCCESSOR-V2",
        operation="BUILD_SUCCESSOR",
        attributes={
            "static_no_external_execution": True,
            "static_no_network": True,
            "authority_boundaries_declared": True,
            "dcsr_no_authority": True,
            "baseline_immutable": True,
            "license_not_specified": True,
        },
    )
    d39 = a39.evaluate(req39, profile39, (), now=now)

    pass37 = d37.decision.value == "ALLOW" and not d37.action_executed and not d37.permission_granted
    pass38 = d38.decision.value == "ALLOW" and not d38.memory_written and not d38.memory_deleted and not d38.truth_established
    pass39 = d39.decision.value == "ALLOW" and not d39.authoritative_compliance_proven and not d39.action_executed

    out = {
        "schema": "NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1",
        "technology_under_build": 40,
        "creator": "NOEPIN / のえぴん",
        "ai_support": "AI-assisted implementation / analysis / documentation support using ChatGPT",
        "al_artifacts_used": {
            "037": {"source_sha256": file_sha(args.al037), "decision": d37.decision.value, "reasons": list(d37.reasons), "action_executed": d37.action_executed, "permission_granted": d37.permission_granted},
            "038": {"source_sha256": file_sha(args.al038), "decision": d38.decision.value, "reason_codes": list(d38.reason_codes), "memory_written": d38.memory_written, "memory_deleted": d38.memory_deleted, "truth_established": d38.truth_established},
            "039": {"source_sha256": file_sha(args.al039), "decision": d39.decision.value, "gap_rule_ids": list(d39.gap_rule_ids), "authoritative_compliance_proven": d39.authoritative_compliance_proven, "action_executed": d39.action_executed},
        },
        "gate_checks": {"037_pass": pass37, "038_pass": pass38, "039_pass": pass39},
        "production_gate_pass": bool(pass37 and pass38 and pass39),
        "authority_note": "AL decisions are pre-execution/control evidence; they do not grant execution success, compliance truth, or memory persistence.",
    }
    args.out.write_text(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, sort_keys=True))
    return 0 if out["production_gate_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
