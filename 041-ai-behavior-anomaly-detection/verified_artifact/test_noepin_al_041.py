from __future__ import annotations
import dataclasses
from pathlib import Path
import re
import unittest

import noepin_al_041_behavior_anomaly as m

NOW = 1_800_000_000


def baseline(**kw):
    b = m.default_baseline(NOW)
    return dataclasses.replace(b, **kw)


def event(i=1, **kw):
    e = m.BehaviorEvent(
        event_id=f"E{i}", actor_id="NOEPIN-AL-AGENT", observed_at=NOW,
        tool_name="LOCAL_ANALYZER", operation="ANALYZE", resource_class="INTERNAL_METADATA",
        events_per_minute=30.0, tool_calls_per_minute=10.0,
        capabilities=frozenset({"READ_METADATA", "LOCAL_EVAL"}),
        expected_baseline_id="NOEPIN-AL-041-DEFAULT", expected_baseline_version="1",
        expected_authority_epoch=1, evidence_id=f"EV{i}", evidence_verified=True,
    )
    return dataclasses.replace(e, **kw)


class CoreTests(unittest.TestCase):
    def test_001_provenance(self):
        self.assertEqual(m.CREATOR, "NOEPIN / のえぴん")
        self.assertEqual(m.PROJECT_OWNER, m.CREATOR)
        self.assertEqual(m.LICENSE_RIGHTS, "NOT SPECIFIED")
        self.assertEqual(m.TECHNOLOGY_NUMBER, 41)

    def test_002_origin_guid_policy(self):
        self.assertIn("PRESERVE_EXISTING", m.ORIGIN_GUID_POLICY)

    def test_003_normal(self):
        f=m.evaluate(event(), baseline(), now=NOW)
        self.assertEqual(f.decision, m.ControlDecision.ALLOW)
        self.assertEqual(f.level, m.DetectionLevel.NORMAL)
        self.assertEqual(f.anomaly_score, 0.0)
        self.assertFalse(f.compromise_proven)
        self.assertFalse(f.system_safe_proven)

    def test_004_unknown_tool(self):
        f=m.evaluate(event(tool_name="REMOTE_ADMIN"), baseline(), now=NOW)
        self.assertGreaterEqual(f.anomaly_score, .45)
        self.assertIn("TOOL_OUTSIDE_BASELINE", f.reasons)

    def test_005_unknown_operation(self):
        f=m.evaluate(event(operation="DEPLOY"), baseline(), now=NOW)
        self.assertGreaterEqual(f.anomaly_score, .35)

    def test_006_unknown_pair(self):
        f=m.evaluate(event(tool_name="LOCAL_TEST", operation="ANALYZE"), baseline(), now=NOW)
        self.assertIn("TOOL_OPERATION_PAIR_OUTSIDE_BASELINE", f.reasons)

    def test_007_resource(self):
        f=m.evaluate(event(resource_class="PROD_SECRET"), baseline(), now=NOW)
        self.assertIn("RESOURCE_CLASS_OUTSIDE_BASELINE", f.reasons)

    def test_008_time(self):
        b=baseline(allowed_hours_utc=frozenset({0}))
        hour=(NOW//3600)%24
        if hour == 0:
            b=baseline(allowed_hours_utc=frozenset({1}))
        f=m.evaluate(event(), b, now=NOW)
        self.assertIn("TIME_WINDOW_OUTSIDE_BASELINE", f.reasons)

    def test_009_event_rate(self):
        f=m.evaluate(event(events_per_minute=500), baseline(), now=NOW)
        self.assertIn("EVENT_RATE_ABOVE_BASELINE", f.reasons)

    def test_010_tool_rate(self):
        f=m.evaluate(event(tool_calls_per_minute=500), baseline(), now=NOW)
        self.assertIn("TOOL_RATE_ABOVE_BASELINE", f.reasons)

    def test_011_capability(self):
        f=m.evaluate(event(capabilities=frozenset({"READ_METADATA","LOCAL_EVAL","ROOT"})), baseline(), now=NOW)
        self.assertTrue(any(x.startswith("CAPABILITY_OUTSIDE_BASELINE") for x in f.reasons))

    def test_012_medium_route(self):
        f=m.evaluate(event(operation="DEPLOY"), baseline(), now=NOW)
        self.assertEqual(f.decision, m.ControlDecision.HUMAN_APPROVAL)
        self.assertEqual(f.recommended_control, m.RecommendedControl.ALERT_AND_REVIEW)

    def test_013_high_route(self):
        f=m.evaluate(event(tool_name="REMOTE", operation="DEPLOY"), baseline(), now=NOW)
        self.assertIn(f.decision, {m.ControlDecision.HOLD,m.ControlDecision.DENY})

    def test_014_critical_route(self):
        f=m.evaluate(event(tool_name="REMOTE", operation="DEPLOY", resource_class="PROD", capabilities=frozenset({"ROOT","NET","DEPLOY"}), events_per_minute=999, tool_calls_per_minute=999), baseline(), now=NOW)
        self.assertEqual(f.decision, m.ControlDecision.DENY)
        self.assertEqual(f.level, m.DetectionLevel.CRITICAL)
        self.assertTrue(f.stop_recommended)
        self.assertFalse(f.stop_executed)

    def test_015_baseline_id_mismatch(self):
        f=m.evaluate(event(expected_baseline_id="OTHER"), baseline(), now=NOW)
        self.assertEqual(f.level, m.DetectionLevel.INDETERMINATE)
        self.assertEqual(f.decision, m.ControlDecision.HOLD)

    def test_016_version_mismatch(self):
        f=m.evaluate(event(expected_baseline_version="2"), baseline(), now=NOW)
        self.assertIn("BASELINE_VERSION_MISMATCH", f.reasons)

    def test_017_epoch_mismatch(self):
        f=m.evaluate(event(expected_authority_epoch=2), baseline(), now=NOW)
        self.assertIn("AUTHORITY_EPOCH_MISMATCH", f.reasons)

    def test_018_unverified(self):
        f=m.evaluate(event(evidence_verified=False), baseline(), now=NOW)
        self.assertEqual(f.decision, m.ControlDecision.HOLD)
        self.assertIn("EVIDENCE_UNVERIFIED", f.reasons)

    def test_019_future(self):
        f=m.evaluate(event(observed_at=NOW+1), baseline(), now=NOW)
        self.assertIn("EVENT_FROM_FUTURE", f.reasons)

    def test_020_expired(self):
        b=baseline(expires_at=NOW)
        f=m.evaluate(event(), b, now=NOW)
        self.assertEqual(f.level, m.DetectionLevel.INDETERMINATE)
        self.assertTrue(f.reasons[0].startswith("BASELINE_INVALID"))

    def test_021_revoked(self):
        f=m.evaluate(event(), baseline(revoked=True), now=NOW)
        self.assertEqual(f.decision, m.ControlDecision.HOLD)

    def test_022_not_yet_valid(self):
        f=m.evaluate(event(), baseline(issued_at=NOW+1, expires_at=NOW+100), now=NOW)
        self.assertEqual(f.decision, m.ControlDecision.HOLD)

    def test_023_bad_thresholds(self):
        f=m.evaluate(event(), baseline(alert_threshold=.8,hold_threshold=.7), now=NOW)
        self.assertEqual(f.decision, m.ControlDecision.HOLD)

    def test_024_negative_event_rate(self):
        f=m.evaluate(event(events_per_minute=-1), baseline(), now=NOW)
        self.assertEqual(f.level, m.DetectionLevel.INDETERMINATE)

    def test_025_negative_tool_rate(self):
        f=m.evaluate(event(tool_calls_per_minute=-1), baseline(), now=NOW)
        self.assertEqual(f.level, m.DetectionLevel.INDETERMINATE)

    def test_026_prepared_semantics(self):
        b=baseline(); e=event()
        p=m.prepare_baseline(b, now=NOW)
        self.assertEqual(m.evaluate(e,b,now=NOW), m.evaluate_prepared(e,p,now=NOW))

    def test_027_fingerprint_set_order(self):
        b1=baseline(allowed_tools=frozenset(["A","B"]))
        b2=baseline(allowed_tools=frozenset(["B","A"]))
        self.assertEqual(m.fingerprint(b1),m.fingerprint(b2))

    def test_028_delta_roundtrip(self):
        b=baseline(); t=dataclasses.replace(b,version="2",authority_epoch=2,allowed_tools=b.allowed_tools|{"X"},allowed_operations=b.allowed_operations|{"Y"},allowed_tool_operation_pairs=b.allowed_tool_operation_pairs|{"X|Y"})
        d=m.make_baseline_delta(b,t)
        self.assertEqual(m.apply_baseline_delta(b,d),t)

    def test_029_delta_wrong_base(self):
        b=baseline(); t=dataclasses.replace(b,version="2")
        d=m.make_baseline_delta(b,t)
        with self.assertRaises(ValueError): m.apply_baseline_delta(dataclasses.replace(b,version="X"),d)

    def test_030_delta_tamper_target(self):
        b=baseline(); t=dataclasses.replace(b,version="2")
        d=dataclasses.replace(m.make_baseline_delta(b,t),target_fingerprint="0"*64)
        with self.assertRaises(ValueError): m.apply_baseline_delta(b,d)

    def test_031_no_authority_promotion(self):
        f=m.evaluate(event(tool_name="REMOTE", operation="DEPLOY"), baseline(), now=NOW)
        self.assertFalse(f.permission_granted); self.assertFalse(f.action_success); self.assertFalse(f.truth_established)
        self.assertFalse(f.alert_executed); self.assertFalse(f.stop_executed)

    def test_032_static_safety(self):
        src=Path(m.__file__).read_text(encoding="utf-8")
        banned=[r"\bsubprocess\b",r"\bos\.system\b",r"\bsocket\b",r"\brequests\b",r"\burllib\b",r"\bPopen\b",r"open\([^\n]*['\"]w",r"\.unlink\(",r"\bshutil\b"]
        for pat in banned:
            self.assertIsNone(re.search(pat,src),pat)

    def test_033_no_execute_methods(self):
        src=Path(m.__file__).read_text(encoding="utf-8")
        self.assertNotRegex(src,r"def\s+(execute|commit|grant|deploy|publish|send|persist|delete|stop)\s*\(")

    def test_034_canonical_json(self):
        self.assertEqual(m.canonical_json({"b":2,"a":1}),'{"a":1,"b":2}')

    def test_035_finding_digest(self):
        fs=[m.evaluate(event(i),baseline(),now=NOW) for i in range(3)]
        self.assertEqual(m.findings_digest(fs),m.findings_digest(fs))

    def test_036_rate_penalty_boundary(self):
        f=m.evaluate(event(events_per_minute=120.0),baseline(),now=NOW)
        self.assertNotIn("EVENT_RATE_ABOVE_BASELINE",f.reasons)

    def test_037_rate_penalty_just_over(self):
        f=m.evaluate(event(events_per_minute=120.01),baseline(),now=NOW)
        self.assertIn("EVENT_RATE_ABOVE_BASELINE",f.reasons)

    def test_038_empty_hours_means_any(self):
        f=m.evaluate(event(),baseline(allowed_hours_utc=frozenset()),now=NOW)
        self.assertNotIn("TIME_WINDOW_OUTSIDE_BASELINE",f.reasons)

    def test_039_invalid_hour(self):
        f=m.evaluate(event(),baseline(allowed_hours_utc=frozenset({24})),now=NOW)
        self.assertEqual(f.level,m.DetectionLevel.INDETERMINATE)

    def test_040_invalid_rate_policy(self):
        f=m.evaluate(event(),baseline(max_events_per_minute=0),now=NOW)
        self.assertEqual(f.decision,m.ControlDecision.HOLD)


# 120 deterministic matrix checks: normal, medium, and critical variants.
def _make_matrix_test(i):
    def test(self):
        mode=i%3
        if mode==0:
            e=event(1000+i,events_per_minute=float(10+(i%50)),tool_calls_per_minute=float(i%20))
            f=m.evaluate(e,baseline(),now=NOW)
            self.assertEqual(f.decision,m.ControlDecision.ALLOW)
            self.assertFalse(f.stop_executed)
        elif mode==1:
            e=event(1000+i,operation=f"UNSEEN_{i}")
            f=m.evaluate(e,baseline(),now=NOW)
            self.assertEqual(f.decision,m.ControlDecision.HUMAN_APPROVAL)
            self.assertFalse(f.compromise_proven)
        else:
            e=event(1000+i,tool_name=f"REMOTE_{i}",operation=f"EXEC_{i}",resource_class="PROD",capabilities=frozenset({"ROOT","NET"}))
            f=m.evaluate(e,baseline(),now=NOW)
            self.assertIn(f.decision,{m.ControlDecision.HOLD,m.ControlDecision.DENY})
            self.assertFalse(f.stop_executed)
    return test

for _i in range(120):
    setattr(CoreTests,f"test_matrix_{_i:03d}",_make_matrix_test(_i))

if __name__ == "__main__":
    unittest.main(verbosity=1)
