import json
import os
import re
import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path

import noepin_al_037_critical_system_safety_mode as m

NOW = 1_700_000_000


def req(**kw):
    base = dict(
        request_id="r-1", actor="operator-1", operation="read_status", resource="plant:A",
        risk_level=0, impact_scope=0, requested_capabilities=frozenset({"read"}),
        metadata={"ticket":"T-1","purpose":"monitor"}, network_required=False,
        offline_mode=False, manual_override_requested=False, expected_policy_version="2026.11"
    )
    base.update(kw)
    return m.SafetyRequest(**base)


def approval_for(r, **kw):
    base=dict(
        approval_id="ap-1", actor=r.actor, operation=r.operation, resource=r.resource,
        verified_by_external_authority=True, issued_at=NOW-10, expires_at=NOW+100,
        revoked=False,
    )
    base.update(kw)
    return m.ApprovalEvidence(**base)


def override_for(r, **kw):
    base=dict(
        override_id="ov-1", actor=r.actor, allowed_operations=frozenset({r.operation}),
        allowed_resources=frozenset({r.resource}), verified_by_external_authority=True,
        issued_at=NOW-10, expires_at=NOW+100, revoked=False,
    )
    base.update(kw)
    return m.OverrideEvidence(**base)


class CoreDecisionTests(unittest.TestCase):
    def setUp(self):
        self.p = m.default_profile(NOW)
        self.a = m.default_authority()

    def assertDecision(self, expected, r=None, p=None, a=None, now=NOW):
        out=m.evaluate(r or req(), p or self.p, a or self.a, now=now)
        self.assertEqual(expected, out.decision)
        self.assertFalse(out.action_executed)
        self.assertFalse(out.permission_granted)
        self.assertFalse(out.action_success)
        self.assertFalse(out.provisional)
        return out

    def test_001_safe_read_allow(self): self.assertDecision(m.Decision.ALLOW)
    def test_002_unknown_operation_deny(self): self.assertDecision(m.Decision.DENY, req(operation="unknown"))
    def test_003_explicit_deny(self): self.assertDecision(m.Decision.DENY, req(operation="disable_safety"))
    def test_004_missing_permission_deny(self): self.assertDecision(m.Decision.DENY, a=replace(self.a, permission_grants=frozenset()))
    def test_005_missing_metadata_hold(self): self.assertDecision(m.Decision.HOLD, req(metadata={"ticket":"T-1"}))
    def test_006_empty_ticket_hold(self): self.assertDecision(m.Decision.HOLD, req(metadata={"ticket":" ","purpose":"x"}))
    def test_007_capability_not_allowed(self): self.assertDecision(m.Decision.DENY, req(requested_capabilities=frozenset({"shell"})))
    def test_008_actor_inactive(self): self.assertDecision(m.Decision.DENY, a=replace(self.a, active_actor=False))
    def test_009_actor_revoked(self): self.assertDecision(m.Decision.DENY, a=replace(self.a, actor_revoked=True))
    def test_010_authority_epoch_missing(self): self.assertDecision(m.Decision.DENY, a=replace(self.a, authority_epoch=""))
    def test_011_policy_revoked(self): self.assertDecision(m.Decision.DENY, p=replace(self.p, revoked=True))
    def test_012_policy_expired(self): self.assertDecision(m.Decision.DENY, now=self.p.expires_at)
    def test_013_policy_not_yet_valid(self): self.assertDecision(m.Decision.DENY, now=self.p.issued_at-1)
    def test_014_version_mismatch(self): self.assertDecision(m.Decision.DENY, req(expected_policy_version="old"))
    def test_015_version_unspecified_allowed_to_evaluate(self): self.assertDecision(m.Decision.ALLOW, req(expected_policy_version=None))
    def test_016_offline_read_allow(self): self.assertDecision(m.Decision.ALLOW, req(offline_mode=True))
    def test_017_network_in_offline_deny(self): self.assertDecision(m.Decision.DENY, req(offline_mode=True, network_required=True))
    def test_018_not_offline_allowlist_deny(self):
        p=replace(self.p, offline_allowed_operations=frozenset())
        self.assertDecision(m.Decision.DENY, req(offline_mode=True), p=p)
    def test_019_critical_requires_offline_hold(self): self.assertDecision(m.Decision.HOLD, req(operation="simulate_change",risk_level=3,requested_capabilities=frozenset({"simulate"})))
    def test_020_critical_offline_human(self): self.assertDecision(m.Decision.HUMAN_APPROVAL, req(operation="simulate_change",risk_level=3,requested_capabilities=frozenset({"simulate"}),offline_mode=True))
    def test_021_high_risk_ceiling_deny(self): self.assertDecision(m.Decision.DENY, req(operation="simulate_change",risk_level=5,requested_capabilities=frozenset({"simulate"}),offline_mode=True))
    def test_022_high_impact_ceiling_deny(self): self.assertDecision(m.Decision.DENY, req(operation="simulate_change",impact_scope=5,requested_capabilities=frozenset({"simulate"}),offline_mode=True))
    def test_023_human_operation_requires_approval(self): self.assertDecision(m.Decision.HUMAN_APPROVAL, req(operation="apply_config",requested_capabilities=frozenset({"prepare_config"}),offline_mode=True))
    def test_024_valid_approval_allows_control_decision(self):
        r=req(operation="apply_config",requested_capabilities=frozenset({"prepare_config"}),offline_mode=True)
        a=replace(self.a, approval=approval_for(r))
        self.assertDecision(m.Decision.ALLOW,r,a=a)
    def test_025_unverified_approval_not_enough(self):
        r=req(operation="apply_config",requested_capabilities=frozenset({"prepare_config"}),offline_mode=True)
        a=replace(self.a, approval=approval_for(r,verified_by_external_authority=False))
        self.assertDecision(m.Decision.HUMAN_APPROVAL,r,a=a)
    def test_026_revoked_approval_not_enough(self):
        r=req(operation="apply_config",requested_capabilities=frozenset({"prepare_config"}),offline_mode=True)
        a=replace(self.a, approval=approval_for(r,revoked=True))
        self.assertDecision(m.Decision.HUMAN_APPROVAL,r,a=a)
    def test_027_expired_approval_not_enough(self):
        r=req(operation="apply_config",requested_capabilities=frozenset({"prepare_config"}),offline_mode=True)
        a=replace(self.a, approval=approval_for(r,expires_at=NOW))
        self.assertDecision(m.Decision.HUMAN_APPROVAL,r,a=a)
    def test_028_wrong_scope_approval_not_enough(self):
        r=req(operation="apply_config",requested_capabilities=frozenset({"prepare_config"}),offline_mode=True)
        a=replace(self.a, approval=approval_for(r,resource="plant:B"))
        self.assertDecision(m.Decision.HUMAN_APPROVAL,r,a=a)
    def test_029_manual_override_request_alone_not_override(self): self.assertDecision(m.Decision.HUMAN_APPROVAL, req(manual_override_requested=True))
    def test_030_valid_scoped_override_allows_control_decision(self):
        r=req(manual_override_requested=True)
        a=replace(self.a, override=override_for(r))
        self.assertDecision(m.Decision.ALLOW,r,a=a)
    def test_031_override_cannot_bypass_explicit_deny(self):
        r=req(operation="disable_safety",manual_override_requested=True)
        a=replace(self.a, permission_grants=self.a.permission_grants|frozenset({"disable_safety@plant:A"}),override=override_for(r))
        self.assertDecision(m.Decision.DENY,r,a=a)
    def test_032_override_cannot_create_permission(self):
        r=req(manual_override_requested=True)
        a=replace(self.a, permission_grants=frozenset(),override=override_for(r))
        self.assertDecision(m.Decision.DENY,r,a=a)
    def test_033_invalid_risk_deny(self): self.assertDecision(m.Decision.DENY, req(risk_level=6))
    def test_034_invalid_impact_deny(self): self.assertDecision(m.Decision.DENY, req(impact_scope=-1))
    def test_035_empty_request_id_deny(self): self.assertDecision(m.Decision.DENY, req(request_id=""))
    def test_036_empty_actor_deny(self): self.assertDecision(m.Decision.DENY, req(actor=""))
    def test_037_empty_operation_deny(self): self.assertDecision(m.Decision.DENY, req(operation=""))
    def test_038_empty_resource_deny(self): self.assertDecision(m.Decision.DENY, req(resource=""))
    def test_039_result_fingerprint_stable(self):
        a=self.assertDecision(m.Decision.ALLOW); b=self.assertDecision(m.Decision.ALLOW)
        self.assertEqual(a.result_fingerprint,b.result_fingerprint)
    def test_040_cache_flag_not_in_result_semantic_fingerprint(self):
        a=m.evaluate(req(),self.p,self.a,now=NOW,cache_hit=False)
        b=m.evaluate(req(),self.p,self.a,now=NOW,cache_hit=True)
        self.assertEqual(a.result_fingerprint,b.result_fingerprint)


class PolicyAndDCSRTests(unittest.TestCase):
    def setUp(self):
        self.p=m.default_profile(NOW); self.a=m.default_authority()

    def raw(self,p=None):
        d=asdict(p or self.p)
        for k in ["allowed_operations","denied_operations","human_approval_operations","offline_allowed_operations","allowed_capabilities","required_metadata"]:
            d[k]=sorted(d[k])
        return d

    def test_041_mapping_roundtrip(self): self.assertEqual(self.p,m.safe_profile_from_mapping(self.raw()))
    def test_042_mapping_missing_required(self):
        x=self.raw(); x.pop("profile_id")
        with self.assertRaises(m.SafetyModeError): m.safe_profile_from_mapping(x)
    def test_043_invalid_profile_time(self):
        with self.assertRaises(m.SafetyModeError): m.safe_profile_from_mapping({**self.raw(),"expires_at":self.p.issued_at})
    def test_044_allow_deny_overlap_invalid(self):
        with self.assertRaises(m.SafetyModeError): m.safe_profile_from_mapping({**self.raw(),"denied_operations":["read_status"]})
    def test_045_prepared_second_call_hits(self):
        e=m.PreparedSafetyEvaluator(self.p); a=e.evaluate(req(),self.a,now=NOW); b=e.evaluate(req(),self.a,now=NOW)
        self.assertFalse(a.dcsr_cache_hit); self.assertTrue(b.dcsr_cache_hit)
    def test_046_authority_change_invalidates_by_key(self):
        e=m.PreparedSafetyEvaluator(self.p); e.evaluate(req(),self.a,now=NOW)
        b=e.evaluate(req(),replace(self.a,authority_epoch="epoch-2"),now=NOW)
        self.assertFalse(b.dcsr_cache_hit)
    def test_047_request_change_invalidates_by_key(self):
        e=m.PreparedSafetyEvaluator(self.p); e.evaluate(req(),self.a,now=NOW)
        b=e.evaluate(req(request_id="r-2"),self.a,now=NOW)
        self.assertFalse(b.dcsr_cache_hit)
    def test_048_profile_new_evaluator_no_reuse(self):
        e=m.PreparedSafetyEvaluator(replace(self.p,policy_version="2026.12")); b=e.evaluate(req(expected_policy_version="2026.12"),self.a,now=NOW)
        self.assertFalse(b.dcsr_cache_hit)
    def test_049_expiry_transition_recomputed(self):
        p=replace(self.p,expires_at=NOW+1); e=m.PreparedSafetyEvaluator(p)
        e.evaluate(req(),self.a,now=NOW); b=e.evaluate(req(),self.a,now=NOW+1)
        self.assertFalse(b.dcsr_cache_hit); self.assertEqual(m.Decision.DENY,b.decision)
    def test_050_future_approval_transition_recomputed(self):
        r=req(operation="apply_config",requested_capabilities=frozenset({"prepare_config"}),offline_mode=True)
        ap=approval_for(r,issued_at=NOW+5,expires_at=NOW+20)
        a=replace(self.a,approval=ap); e=m.PreparedSafetyEvaluator(self.p)
        x=e.evaluate(r,a,now=NOW); y=e.evaluate(r,a,now=NOW+5)
        self.assertEqual(m.Decision.HUMAN_APPROVAL,x.decision); self.assertEqual(m.Decision.ALLOW,y.decision); self.assertFalse(y.dcsr_cache_hit)
    def test_051_invalidate_all(self):
        e=m.PreparedSafetyEvaluator(self.p); e.evaluate(req(),self.a,now=NOW); self.assertEqual(1,e.cache_entries); e.invalidate_all(); self.assertEqual(0,e.cache_entries)
    def test_052_delta_reconstructs_target(self):
        t=replace(self.p,policy_version="2026.12",allowed_operations=self.p.allowed_operations|{"health_check"},denied_operations=self.p.denied_operations|{"raw_write"})
        d=m.compute_policy_delta(self.p,t); self.assertEqual(t,m.apply_policy_delta(self.p,d))
    def test_053_delta_wrong_base_fails(self):
        t=replace(self.p,policy_version="2026.12"); d=m.compute_policy_delta(self.p,t)
        with self.assertRaises(m.FingerprintMismatch): m.apply_policy_delta(replace(self.p,profile_id="other"),d)
    def test_054_delta_tamper_target_fails(self):
        t=replace(self.p,policy_version="2026.12"); d=m.compute_policy_delta(self.p,t); d=replace(d,target_fingerprint="0"*64)
        with self.assertRaises(m.FingerprintMismatch): m.apply_policy_delta(self.p,d)
    def test_055_unprepared_matches_direct(self):
        a=m.evaluate(req(),self.p,self.a,now=NOW); b=m.evaluate_unprepared(self.raw(),req(),self.a,now=NOW)
        self.assertEqual(a.result_fingerprint,b.result_fingerprint)
    def test_056_audit_record_no_mutation(self):
        out=m.evaluate(req(),self.p,self.a,now=NOW); rec=m.audit_record(out); self.assertFalse(rec["action_executed"]); self.assertFalse(rec["permission_granted"])
    def test_057_fingerprint_order_independent_mapping(self): self.assertEqual(m.fingerprint({"a":1,"b":2}),m.fingerprint({"b":2,"a":1}))
    def test_058_fingerprint_set_order_independent(self): self.assertEqual(m.fingerprint({"x":frozenset({"a","b"})}),m.fingerprint({"x":frozenset({"b","a"})}))
    def test_059_dcsr_cache_never_changes_semantics(self):
        e=m.PreparedSafetyEvaluator(self.p); x=e.evaluate(req(),self.a,now=NOW); y=e.evaluate(req(),self.a,now=NOW)
        self.assertEqual(x.result_fingerprint,y.result_fingerprint)
    def test_060_cache_permission_removal_cannot_reuse(self):
        e=m.PreparedSafetyEvaluator(self.p); e.evaluate(req(),self.a,now=NOW)
        y=e.evaluate(req(),replace(self.a,permission_grants=frozenset()),now=NOW)
        self.assertEqual(m.Decision.DENY,y.decision); self.assertFalse(y.dcsr_cache_hit)


class StaticSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src=Path(m.__file__).read_text(encoding="utf-8")

    def test_061_no_subprocess(self): self.assertNotIn("subprocess",self.src)
    def test_062_no_os_system(self): self.assertNotIn("os.system",self.src)
    def test_063_no_socket(self): self.assertNotIn("socket",self.src)
    def test_064_no_requests(self): self.assertNotRegex(self.src,r"(^|\n)\s*(import requests|from requests import)|requests\.")
    def test_065_no_urllib(self): self.assertNotIn("urllib",self.src)
    def test_066_no_shell_execution(self): self.assertNotRegex(self.src,r"\bPopen\b|\bexec\(")
    def test_067_no_file_write_api(self): self.assertNotRegex(self.src,r"write_text|write_bytes|open\([^\n]*['\"]w")
    def test_068_no_unlink(self): self.assertNotIn("unlink(",self.src)
    def test_069_no_shutil(self): self.assertNotIn("shutil",self.src)
    def test_070_no_network_send(self): self.assertNotRegex(self.src,r"\.send\(|sendmail|smtp")
    def test_071_no_deploy_publish(self): self.assertNotRegex(self.src,r"\bdeploy\(|\bpublish\(")
    def test_072_no_grant_primitive(self): self.assertNotRegex(self.src,r"def\s+grant\b|def\s+commit\b|def\s+execute\b")
    def test_073_license_unspecified(self): self.assertEqual("NOT SPECIFIED",m.LICENSE_STATUS)
    def test_074_creator_correct(self): self.assertEqual("NOEPIN / のえぴん",m.CREATOR)
    def test_075_technology_number(self): self.assertEqual(37,m.TECHNOLOGY_NUMBER)


class SerializationBoundaryTests(unittest.TestCase):
    def setUp(self): self.p=m.default_profile(NOW); self.a=m.default_authority()
    def test_076_canonical_json_deterministic(self): self.assertEqual(m.canonical_json(self.p),m.canonical_json(self.p))
    def test_077_result_json_serializable(self): json.dumps(m.audit_record(m.evaluate(req(),self.p,self.a,now=NOW)),ensure_ascii=False)
    def test_078_no_secret_field_in_authority_context(self): self.assertNotIn("secret",m.canonical_json(self.a).lower())
    def test_079_approval_evidence_not_action(self):
        r=req(operation="apply_config",requested_capabilities=frozenset({"prepare_config"}),offline_mode=True); a=replace(self.a,approval=approval_for(r)); out=m.evaluate(r,self.p,a,now=NOW)
        self.assertEqual(m.Decision.ALLOW,out.decision); self.assertFalse(out.action_executed)
    def test_080_policy_allow_not_permission_grant(self):
        out=m.evaluate(req(),self.p,replace(self.a,permission_grants=frozenset()),now=NOW); self.assertEqual(m.Decision.DENY,out.decision)


# 24 risk/impact boundary cases, each a separate unittest. These exercise the
# transition among ALLOW, HOLD, HUMAN_APPROVAL, and DENY under the critical
# offline requirement without weakening production semantics.
def _make_boundary_case(risk, impact):
    def test(self):
        p=m.default_profile(NOW); a=m.default_authority()
        r=req(operation="simulate_change",requested_capabilities=frozenset({"simulate"}),risk_level=risk,impact_scope=impact,offline_mode=(risk>=3 or impact>=3))
        out=m.evaluate(r,p,a,now=NOW)
        if risk>4 or impact>4:
            expected=m.Decision.DENY
        elif risk>1 or impact>1:
            expected=m.Decision.HUMAN_APPROVAL
        else:
            expected=m.Decision.ALLOW
        self.assertEqual(expected,out.decision)
        self.assertFalse(out.action_executed)
    return test

_idx=81
for _risk,_impact in [(r,i) for r in range(6) for i in range(6)][:24]:
    setattr(SerializationBoundaryTests,f"test_{_idx:03d}_risk_{_risk}_impact_{_impact}",_make_boundary_case(_risk,_impact))
    _idx += 1


if __name__ == "__main__":
    unittest.main(verbosity=2)
