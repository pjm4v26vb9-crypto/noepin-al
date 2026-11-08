from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import noepin_al_040_continuous_red_team as m

NOW = 1_800_000_000
TARGET = "target-1"


def mkcase(cid="C1", *, category=m.Category.REGRESSION, severity=m.Severity.HIGH,
           expected=m.ExpectedBehavior.NO_ACTION, deps=frozenset({"policy"}),
           signals=frozenset(), always=False, enabled=True):
    return m.RedTeamCase(cid, category, severity, f"abstract safe case {cid}", expected,
                         deps, signals, always, enabled)


def mksuite(cases=None, *, version="1", epoch=1, issued=NOW-10, expires=NOW+1000, revoked=False):
    if cases is None:
        cases=(mkcase(),)
    return m.RedTeamSuite("S", version, epoch, issued, expires, tuple(cases), revoked)


def mkobs(case, *, behavior=None, signals=None, verified=True, action=False, tool=False,
          permission=False, side=False, target=TARGET, observed_at=NOW-1, evidence_id="E1"):
    return m.Observation(
        case.case_id, target, behavior or case.expected_behavior,
        frozenset(case.required_signals if signals is None else signals), observed_at,
        evidence_id, verified, action, tool, permission, side,
    )


class CoreTests(unittest.TestCase):
    def test_001_constants(self):
        self.assertEqual(m.CREATOR, "NOEPIN / のえぴん")
        self.assertEqual(m.LICENSE_RIGHTS, "NOT SPECIFIED")
        self.assertEqual(m.TECHNOLOGY_NUMBER, 40)

    def test_002_case_requires_id(self):
        with self.assertRaises(ValueError):
            mkcase("").validate()

    def test_003_case_requires_description(self):
        c=mkcase()
        bad=m.RedTeamCase(c.case_id,c.category,c.severity,"",c.expected_behavior,c.dependencies)
        with self.assertRaises(ValueError): bad.validate()

    def test_004_case_requires_dependency_or_always(self):
        with self.assertRaises(ValueError): mkcase(deps=frozenset()).validate()

    def test_005_always_case_can_have_no_dependency(self):
        mkcase(deps=frozenset(), always=True).validate()

    def test_006_invalid_dependency(self):
        with self.assertRaises(ValueError): mkcase(deps=frozenset({""})).validate()

    def test_007_invalid_signal(self):
        with self.assertRaises(ValueError): mkcase(signals=frozenset({""})).validate()

    def test_008_suite_id_required(self):
        s=mksuite(); bad=m.RedTeamSuite("",s.suite_version,s.authority_epoch,s.issued_at,s.expires_at,s.cases)
        with self.assertRaises(ValueError): bad.validate(NOW)

    def test_009_suite_epoch_positive(self):
        with self.assertRaises(ValueError): mksuite(epoch=0).validate(NOW)

    def test_010_suite_time_range(self):
        with self.assertRaises(ValueError): mksuite(issued=NOW,expires=NOW).validate(NOW)

    def test_011_suite_not_yet_valid(self):
        with self.assertRaises(ValueError): mksuite(issued=NOW+1,expires=NOW+10).validate(NOW)

    def test_012_suite_expired(self):
        with self.assertRaises(ValueError): mksuite(issued=NOW-10,expires=NOW).validate(NOW)

    def test_013_suite_revoked(self):
        with self.assertRaises(ValueError): mksuite(revoked=True).validate(NOW)

    def test_014_duplicate_case_id(self):
        with self.assertRaises(ValueError): mksuite((mkcase("X"),mkcase("X"))).validate(NOW)

    def test_015_suite_order_independent_fingerprint(self):
        a,b=mkcase("A"),mkcase("B")
        self.assertEqual(m.fingerprint(mksuite((a,b))),m.fingerprint(mksuite((b,a))))

    def test_016_prepare_corpus_index(self):
        a=mkcase("A",deps=frozenset({"x","y"})); b=mkcase("B",deps=frozenset({"y"}))
        p=m.prepare_corpus(mksuite((b,a)),now=NOW)
        self.assertEqual(p.dependency_index["y"],("A","B"))

    def test_017_prepare_ignores_disabled_index(self):
        a=mkcase("A",enabled=False); p=m.prepare_corpus(mksuite((a,)),now=NOW)
        self.assertEqual(p.case_index,{})

    def test_018_select_changed(self):
        a=mkcase("A",deps=frozenset({"x"})); b=mkcase("B",deps=frozenset({"y"}))
        p=m.prepare_corpus(mksuite((a,b)),now=NOW)
        self.assertEqual([c.case_id for c in m.select_impacted_cases(p,{"x"})],["A"])

    def test_019_select_always(self):
        a=mkcase("A",deps=frozenset(),always=True); b=mkcase("B",deps=frozenset({"y"}))
        p=m.prepare_corpus(mksuite((a,b)),now=NOW)
        self.assertEqual([c.case_id for c in m.select_impacted_cases(p,{"none"})],["A"])

    def test_020_force_full(self):
        a=mkcase("A"); b=mkcase("B")
        p=m.prepare_corpus(mksuite((b,a)),now=NOW)
        self.assertEqual([c.case_id for c in m.select_impacted_cases(p,(),force_full=True)],["A","B"])

    def test_021_missing_observation_hold(self):
        f=m.evaluate_case(mkcase(),None)
        self.assertEqual(f.status,m.CaseStatus.HOLD)

    def test_022_invalid_observation_hold(self):
        c=mkcase(); o=mkobs(c,evidence_id="")
        self.assertEqual(m.evaluate_case(c,o).status,m.CaseStatus.HOLD)

    def test_023_case_binding_mismatch(self):
        c=mkcase("A"); o=mkobs(mkcase("B"))
        self.assertIn("CASE_BINDING_MISMATCH",m.evaluate_case(c,o).reasons)

    def test_024_target_version_mismatch(self):
        c=mkcase(); o=mkobs(c,target="other")
        f=m.evaluate_case(c,o,expected_target_version=TARGET)
        self.assertEqual(f.reasons,("TARGET_VERSION_MISMATCH",))

    def test_025_future_observation_hold(self):
        c=mkcase(); o=mkobs(c,observed_at=NOW+1)
        self.assertIn("OBSERVATION_FROM_FUTURE",m.evaluate_case(c,o,now=NOW).reasons)

    def test_026_unverified_evidence_hold(self):
        c=mkcase(); self.assertIn("EVIDENCE_UNVERIFIED",m.evaluate_case(c,mkobs(c,verified=False)).reasons)

    def test_027_expected_match_pass(self):
        c=mkcase(); self.assertEqual(m.evaluate_case(c,mkobs(c)).status,m.CaseStatus.PASS)

    def test_028_behavior_mismatch_fail(self):
        c=mkcase(); f=m.evaluate_case(c,mkobs(c,behavior=m.ExpectedBehavior.SAFE_RESPONSE))
        self.assertEqual(f.status,m.CaseStatus.FAIL)

    def test_029_side_effect_fail(self):
        c=mkcase(); self.assertIn("EXTERNAL_SIDE_EFFECT_OBSERVED",m.evaluate_case(c,mkobs(c,side=True)).reasons)

    def test_030_unexpected_permission_fail(self):
        c=mkcase(expected=m.ExpectedBehavior.BLOCK); self.assertIn("UNEXPECTED_PERMISSION_GRANT",m.evaluate_case(c,mkobs(c,permission=True)).reasons)

    def test_031_unexpected_action_fail(self):
        c=mkcase(expected=m.ExpectedBehavior.REFUSE); self.assertIn("UNEXPECTED_ACTION_EXECUTION",m.evaluate_case(c,mkobs(c,action=True)).reasons)

    def test_032_unexpected_tool_fail(self):
        c=mkcase(expected=m.ExpectedBehavior.NO_ACTION); self.assertIn("UNEXPECTED_TOOL_CALL",m.evaluate_case(c,mkobs(c,tool=True)).reasons)

    def test_033_required_signal_missing(self):
        c=mkcase(signals=frozenset({"s"})); f=m.evaluate_case(c,mkobs(c,signals=frozenset()))
        self.assertIn("MISSING_SIGNAL:s",f.reasons)

    def test_034_require_approval_human_review(self):
        c=mkcase(expected=m.ExpectedBehavior.REQUIRE_APPROVAL)
        self.assertEqual(m.evaluate_case(c,mkobs(c)).status,m.CaseStatus.HUMAN_REVIEW)

    def test_035_disabled_case_hold_direct(self):
        c=mkcase(enabled=False)
        self.assertEqual(m.evaluate_case(c,mkobs(c)).status,m.CaseStatus.HOLD)

    def test_036_suite_all_pass_allow(self):
        c=mkcase(); r=m.evaluate_suite(mksuite((c,)),(mkobs(c),),target_version=TARGET,now=NOW)
        self.assertEqual(r.decision,m.GateDecision.ALLOW)
        self.assertFalse(r.security_proven)
        self.assertFalse(r.action_executed)
        self.assertFalse(r.permission_granted)

    def test_037_high_fail_deny(self):
        c=mkcase(severity=m.Severity.HIGH,expected=m.ExpectedBehavior.BLOCK)
        r=m.evaluate_suite(mksuite((c,)),(mkobs(c,behavior=m.ExpectedBehavior.SAFE_RESPONSE),),target_version=TARGET,now=NOW)
        self.assertEqual(r.decision,m.GateDecision.DENY)

    def test_038_critical_fail_deny(self):
        c=mkcase(severity=m.Severity.CRITICAL,expected=m.ExpectedBehavior.BLOCK)
        r=m.evaluate_suite(mksuite((c,)),(mkobs(c,behavior=m.ExpectedBehavior.SAFE_RESPONSE),),target_version=TARGET,now=NOW)
        self.assertEqual(r.decision,m.GateDecision.DENY)

    def test_039_medium_fail_hold(self):
        c=mkcase(severity=m.Severity.MEDIUM,expected=m.ExpectedBehavior.BLOCK)
        r=m.evaluate_suite(mksuite((c,)),(mkobs(c,behavior=m.ExpectedBehavior.SAFE_RESPONSE),),target_version=TARGET,now=NOW)
        self.assertEqual(r.decision,m.GateDecision.HOLD)

    def test_040_missing_obs_hold(self):
        c=mkcase(); r=m.evaluate_suite(mksuite((c,)),(),target_version=TARGET,now=NOW)
        self.assertEqual(r.decision,m.GateDecision.HOLD)

    def test_041_human_review_suite(self):
        c=mkcase(expected=m.ExpectedBehavior.REQUIRE_APPROVAL)
        r=m.evaluate_suite(mksuite((c,)),(mkobs(c),),target_version=TARGET,now=NOW)
        self.assertEqual(r.decision,m.GateDecision.HUMAN_APPROVAL)

    def test_042_empty_enabled_suite_hold(self):
        c=mkcase(enabled=False)
        r=m.evaluate_suite(mksuite((c,)),(),target_version=TARGET,now=NOW)
        self.assertEqual(r.decision,m.GateDecision.HOLD)

    def test_043_target_version_required(self):
        with self.assertRaises(ValueError): m.evaluate_suite(mksuite(),(),target_version="",now=NOW)

    def test_044_duplicate_observation_rejected(self):
        c=mkcase(); o=mkobs(c)
        with self.assertRaises(ValueError): m.evaluate_suite(mksuite((c,)),(o,o),target_version=TARGET,now=NOW)

    def test_045_foreign_subset_rejected(self):
        c=mkcase("A"); foreign=mkcase("B")
        with self.assertRaises(ValueError): m.evaluate_suite(mksuite((c,)),(),target_version=TARGET,now=NOW,case_subset=(foreign,))

    def test_046_modified_same_id_subset_rejected(self):
        c=mkcase("A"); modified=mkcase("A",expected=m.ExpectedBehavior.BLOCK)
        with self.assertRaises(ValueError): m.evaluate_suite(mksuite((c,)),(),target_version=TARGET,now=NOW,case_subset=(modified,))

    def test_047_subset_evaluation(self):
        a=mkcase("A"); b=mkcase("B")
        r=m.evaluate_suite(mksuite((a,b)),(mkobs(a),),target_version=TARGET,now=NOW,case_subset=(a,))
        self.assertEqual(len(r.findings),1)
        self.assertEqual(r.decision,m.GateDecision.ALLOW)

    def test_048_report_fingerprint_deterministic(self):
        c=mkcase(); s=mksuite((c,)); o=mkobs(c)
        a=m.evaluate_suite(s,(o,),target_version=TARGET,now=NOW)
        b=m.evaluate_suite(s,(o,),target_version=TARGET,now=NOW)
        self.assertEqual(a.result_fingerprint,b.result_fingerprint)

    def test_049_delta_no_change(self):
        s=mksuite(); d=m.make_corpus_delta(s,s)
        self.assertEqual(d.added_cases,())
        self.assertEqual(d.removed_case_ids,())
        self.assertEqual(d.changed_cases,())
        self.assertEqual(m.apply_corpus_delta(s,d),s)

    def test_050_delta_add(self):
        a=mkcase("A"); b=mkcase("B"); base=mksuite((a,),version="1"); target=mksuite((a,b),version="2")
        d=m.make_corpus_delta(base,target); self.assertEqual([x.case_id for x in d.added_cases],["B"])
        self.assertEqual(m.fingerprint(m.apply_corpus_delta(base,d)),m.fingerprint(target))

    def test_051_delta_remove(self):
        a=mkcase("A"); b=mkcase("B"); base=mksuite((a,b),version="1"); target=mksuite((b,),version="2")
        d=m.make_corpus_delta(base,target); self.assertEqual(d.removed_case_ids,("A",))
        self.assertEqual(m.fingerprint(m.apply_corpus_delta(base,d)),m.fingerprint(target))

    def test_052_delta_change(self):
        a=mkcase("A"); a2=mkcase("A",expected=m.ExpectedBehavior.BLOCK)
        base=mksuite((a,),version="1"); target=mksuite((a2,),version="2")
        d=m.make_corpus_delta(base,target); self.assertEqual([x.case_id for x in d.changed_cases],["A"])
        self.assertEqual(m.fingerprint(m.apply_corpus_delta(base,d)),m.fingerprint(target))

    def test_053_delta_wrong_base_rejected(self):
        base=mksuite((mkcase("A"),),version="1"); target=mksuite((mkcase("B"),),version="2"); d=m.make_corpus_delta(base,target)
        with self.assertRaises(ValueError): m.apply_corpus_delta(mksuite((mkcase("X"),),version="1"),d)

    def test_054_delta_tampered_target_rejected(self):
        base=mksuite((mkcase("A"),),version="1"); target=mksuite((mkcase("B"),),version="2"); d=m.make_corpus_delta(base,target)
        bad=m.CorpusDelta(d.base_fingerprint,"0"*64,d.target_suite_id,d.target_suite_version,d.target_authority_epoch,d.target_issued_at,d.target_expires_at,d.target_revoked,d.added_cases,d.removed_case_ids,d.changed_cases)
        with self.assertRaises(ValueError): m.apply_corpus_delta(base,bad)

    def test_055_default_suite_valid(self):
        s=m.default_suite(NOW); s.validate(NOW); self.assertGreaterEqual(len(s.cases),5)

    def test_056_default_suite_categories(self):
        cats={c.category for c in m.default_suite(NOW).cases}
        self.assertEqual(cats,{m.Category.PROMPT_INJECTION,m.Category.TOOL_ABUSE,m.Category.REGRESSION})

    def test_057_default_has_no_attack_execution(self):
        s=m.default_suite(NOW)
        obs=tuple(mkobs(c,signals=c.required_signals,target="v") for c in s.cases)
        r=m.evaluate_suite(s,obs,target_version="v",now=NOW)
        self.assertFalse(r.attack_executed)

    def test_058_default_mixed_human(self):
        s=m.default_suite(NOW); obs=tuple(mkobs(c,signals=c.required_signals,target="v") for c in s.cases)
        r=m.evaluate_suite(s,obs,target_version="v",now=NOW)
        self.assertEqual(r.decision,m.GateDecision.HUMAN_APPROVAL)

    def test_059_report_digest_deterministic(self):
        c=mkcase(); r=m.evaluate_suite(mksuite((c,)),(mkobs(c),),target_version=TARGET,now=NOW)
        self.assertEqual(m.report_digest((r,r)),m.report_digest((r,r)))

    def test_060_al_production_gate_exists_and_passes(self):
        data=json.loads((ROOT/"AL_PRODUCTION_GATE_RESULT.json").read_text())
        self.assertTrue(data["production_gate_pass"])
        self.assertTrue(all(data["gate_checks"].values()))

    def test_061_al_037_no_action(self):
        data=json.loads((ROOT/"AL_PRODUCTION_GATE_RESULT.json").read_text())
        self.assertFalse(data["al_artifacts_used"]["037"]["action_executed"])
        self.assertFalse(data["al_artifacts_used"]["037"]["permission_granted"])

    def test_062_al_038_no_memory_write(self):
        data=json.loads((ROOT/"AL_PRODUCTION_GATE_RESULT.json").read_text())
        self.assertFalse(data["al_artifacts_used"]["038"]["memory_written"])
        self.assertFalse(data["al_artifacts_used"]["038"]["truth_established"])

    def test_063_al_039_no_compliance_truth(self):
        data=json.loads((ROOT/"AL_PRODUCTION_GATE_RESULT.json").read_text())
        self.assertFalse(data["al_artifacts_used"]["039"]["authoritative_compliance_proven"])

    def test_064_static_no_subprocess(self):
        src=(ROOT/"noepin_al_040_continuous_red_team.py").read_text()
        self.assertNotRegex(src,r"\bimport\s+subprocess\b|\bsubprocess\.")

    def test_065_static_no_socket(self):
        src=(ROOT/"noepin_al_040_continuous_red_team.py").read_text()
        self.assertNotRegex(src,r"\bimport\s+socket\b|\bsocket\.")

    def test_066_static_no_requests(self):
        src=(ROOT/"noepin_al_040_continuous_red_team.py").read_text()
        self.assertNotRegex(src,r"\bimport\s+requests\b|\brequests\.")

    def test_067_static_no_urllib(self):
        src=(ROOT/"noepin_al_040_continuous_red_team.py").read_text()
        self.assertNotRegex(src,r"\bimport\s+urllib\b|\burllib\.")

    def test_068_static_no_os_system(self):
        src=(ROOT/"noepin_al_040_continuous_red_team.py").read_text()
        self.assertNotIn("os.system",src)

    def test_069_static_no_exec_eval(self):
        src=(ROOT/"noepin_al_040_continuous_red_team.py").read_text()
        self.assertNotRegex(src,r"\bexec\s*\(|\beval\s*\(")

    def test_070_static_no_file_write(self):
        src=(ROOT/"noepin_al_040_continuous_red_team.py").read_text()
        self.assertNotRegex(src,r"\.write_text\s*\(|\.write_bytes\s*\(|\bopen\s*\(")

    def test_071_static_no_delete_unlink(self):
        src=(ROOT/"noepin_al_040_continuous_red_team.py").read_text()
        self.assertNotRegex(src,r"\.unlink\s*\(|\brmtree\s*\(")

    def test_072_license_unspecified(self):
        self.assertEqual(m.LICENSE_RIGHTS,"NOT SPECIFIED")

    def test_073_creator_correct(self):
        self.assertEqual(m.PROJECT_OWNER,"NOEPIN / のえぴん")

    def test_074_ai_not_creator(self):
        self.assertNotEqual(m.AI_SUPPORT,m.CREATOR)

    def test_075_no_security_proof(self):
        c=mkcase(); r=m.evaluate_suite(mksuite((c,)),(mkobs(c),),target_version=TARGET,now=NOW)
        self.assertFalse(r.security_proven); self.assertFalse(r.production_safe_proven)

    def test_076_version_mismatch_suite_hold(self):
        c=mkcase(); o=mkobs(c,target="old")
        r=m.evaluate_suite(mksuite((c,)),(o,),target_version="new",now=NOW)
        self.assertEqual(r.decision,m.GateDecision.HOLD)

    def test_077_future_observation_suite_hold(self):
        c=mkcase(); o=mkobs(c,observed_at=NOW+1)
        r=m.evaluate_suite(mksuite((c,)),(o,),target_version=TARGET,now=NOW)
        self.assertEqual(r.decision,m.GateDecision.HOLD)

    def test_078_prepared_fingerprint_changes_with_suite(self):
        a=m.prepare_corpus(mksuite((mkcase("A"),),version="1"),now=NOW)
        b=m.prepare_corpus(mksuite((mkcase("A"),),version="2"),now=NOW)
        self.assertNotEqual(a.suite_fingerprint,b.suite_fingerprint)

    def test_079_dependency_index_deterministic(self):
        a=mkcase("A",deps=frozenset({"z","a"})); b=mkcase("B",deps=frozenset({"a"}))
        p=m.prepare_corpus(mksuite((b,a)),now=NOW)
        self.assertEqual(list(p.dependency_index),["a","z"])

    def test_080_select_unknown_only_always(self):
        a=mkcase("A",deps=frozenset(),always=True); b=mkcase("B",deps=frozenset({"x"}))
        p=m.prepare_corpus(mksuite((a,b)),now=NOW)
        self.assertEqual([c.case_id for c in m.select_impacted_cases(p,{"unknown"})],["A"])


def _add_generated_tests():
    # 40 deterministic PASS cases.
    for i in range(40):
        def test(self, i=i):
            expected=(m.ExpectedBehavior.BLOCK,m.ExpectedBehavior.REFUSE,m.ExpectedBehavior.SAFE_RESPONSE,m.ExpectedBehavior.NO_ACTION)[i%4]
            c=mkcase(f"GP{i:03d}",expected=expected,signals=frozenset({f"sig{i%5}"}))
            f=m.evaluate_case(c,mkobs(c))
            self.assertEqual(f.status,m.CaseStatus.PASS)
        setattr(CoreTests,f"test_gen_pass_{i:03d}",test)

    # 20 deterministic mismatches.
    for i in range(20):
        def test(self, i=i):
            c=mkcase(f"GF{i:03d}",severity=m.Severity.HIGH,expected=m.ExpectedBehavior.BLOCK)
            f=m.evaluate_case(c,mkobs(c,behavior=m.ExpectedBehavior.SAFE_RESPONSE))
            self.assertEqual(f.status,m.CaseStatus.FAIL)
            self.assertIn("EXPECTED_BEHAVIOR_MISMATCH",f.reasons)
        setattr(CoreTests,f"test_gen_fail_{i:03d}",test)

    # 20 impact-selection cases.
    for i in range(20):
        def test(self, i=i):
            cases=tuple(mkcase(f"I{j:03d}",deps=frozenset({f"component-{j%10}"}),always=(j==0)) for j in range(30))
            p=m.prepare_corpus(mksuite(cases),now=NOW)
            selected=m.select_impacted_cases(p,{f"component-{i%10}"})
            ids={c.case_id for c in selected}
            self.assertIn("I000",ids)
            for j in range(30):
                if j%10==i%10:
                    self.assertIn(f"I{j:03d}",ids)
        setattr(CoreTests,f"test_gen_impact_{i:03d}",test)

_add_generated_tests()

if __name__ == "__main__":
    unittest.main(verbosity=2)
