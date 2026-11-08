import json
import math
import unittest
from noepin_al_024_typed_action_converter import *


def base(**overrides):
    d = {
        "version": "1",
        "action_type": "TOOL_REQUEST",
        "operation": "calendar.read",
        "target": "calendar://primary",
        "purpose": "read schedule",
        "args": {"date": "2026-11-02"},
        "risk": {},
    }
    d.update(overrides)
    return d


class TestTypedActionConverter(unittest.TestCase):
    def setUp(self):
        self.c = TypedActionConverter()

    def cv(self, obj):
        return self.c.convert(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))

    def test_001_valid_tool_candidate(self): self.assertEqual(self.cv(base()).decision, "TYPED_CANDIDATE")
    def test_002_not_authorized(self): self.assertFalse(self.cv(base()).authorized)
    def test_003_not_executed(self): self.assertFalse(self.cv(base()).executed)
    def test_004_not_succeeded(self): self.assertFalse(self.cv(base()).succeeded)
    def test_005_not_committed(self): self.assertFalse(self.cv(base()).committed)
    def test_006_empty_denied(self): self.assertEqual(self.c.convert(" ").decision, "DENY")
    def test_007_non_json_denied(self): self.assertEqual(self.c.convert("please do it").reason, "INVALID_JSON_OR_NON_JSON_WRAPPER")
    def test_008_json_wrapper_denied(self): self.assertEqual(self.c.convert("prefix {\"a\":1}").reason, "INVALID_JSON_OR_NON_JSON_WRAPPER")
    def test_009_array_denied(self): self.assertEqual(self.c.convert("[]").reason, "TOP_LEVEL_OBJECT_REQUIRED")
    def test_010_duplicate_key_denied(self): self.assertEqual(self.c.convert('{"version":"1","version":"1"}').reason, "DUPLICATE_KEY")
    def test_011_unknown_top_denied(self): self.assertEqual(self.cv(base(extra=1)).reason, "UNKNOWN_TOP_LEVEL_FIELD")
    def test_012_missing_version(self): self.assertEqual(self.cv({k:v for k,v in base().items() if k!="version"}).reason, "MISSING_REQUIRED_FIELD")
    def test_013_missing_action_type(self): self.assertEqual(self.cv({k:v for k,v in base().items() if k!="action_type"}).reason, "MISSING_REQUIRED_FIELD")
    def test_014_missing_operation(self): self.assertEqual(self.cv({k:v for k,v in base().items() if k!="operation"}).reason, "MISSING_REQUIRED_FIELD")
    def test_015_missing_target(self): self.assertEqual(self.cv({k:v for k,v in base().items() if k!="target"}).reason, "MISSING_REQUIRED_FIELD")
    def test_016_missing_args(self): self.assertEqual(self.cv({k:v for k,v in base().items() if k!="args"}).reason, "MISSING_REQUIRED_FIELD")
    def test_017_missing_purpose(self): self.assertEqual(self.cv({k:v for k,v in base().items() if k!="purpose"}).reason, "MISSING_REQUIRED_FIELD")
    def test_018_bad_version(self): self.assertEqual(self.cv(base(version="2")).reason, "UNSUPPORTED_SCHEMA_VERSION")
    def test_019_action_type_not_string(self): self.assertEqual(self.cv(base(action_type=1)).reason, "ACTION_TYPE_MUST_BE_STRING")
    def test_020_shell_denied(self): self.assertEqual(self.cv(base(action_type="SHELL")).reason, "FORBIDDEN_ACTION_TYPE")
    def test_021_exec_denied(self): self.assertEqual(self.cv(base(action_type="EXEC")).reason, "FORBIDDEN_ACTION_TYPE")
    def test_022_eval_denied(self): self.assertEqual(self.cv(base(action_type="EVAL")).reason, "FORBIDDEN_ACTION_TYPE")
    def test_023_unknown_type_denied(self): self.assertEqual(self.cv(base(action_type="MAGIC")).reason, "UNKNOWN_ACTION_TYPE")
    def test_024_data_query_valid(self): self.assertEqual(self.cv(base(action_type="DATA_QUERY")).decision, "TYPED_CANDIDATE")
    def test_025_file_read_valid(self): self.assertEqual(self.cv(base(action_type="FILE_READ")).decision, "TYPED_CANDIDATE")
    def test_026_network_request_valid(self): self.assertEqual(self.cv(base(action_type="NETWORK_REQUEST")).decision, "TYPED_CANDIDATE")
    def test_027_ui_request_valid(self): self.assertEqual(self.cv(base(action_type="UI_REQUEST")).decision, "TYPED_CANDIDATE")
    def test_028_bad_operation_space(self): self.assertEqual(self.cv(base(operation="do bad")).reason, "INVALID_OPERATION")
    def test_029_bad_operation_control(self): self.assertEqual(self.cv(base(operation="do\u0001bad")).reason, "CONTROL_CHARACTER")
    def test_030_empty_target(self): self.assertEqual(self.cv(base(target=" ")).reason, "INVALID_TARGET")
    def test_031_target_control(self): self.assertEqual(self.cv(base(target="x\u0001y")).reason, "CONTROL_CHARACTER")
    def test_032_empty_purpose(self): self.assertEqual(self.cv(base(purpose=" ")).reason, "INVALID_PURPOSE")
    def test_033_purpose_control(self): self.assertEqual(self.cv(base(purpose="x\u0001y")).reason, "CONTROL_CHARACTER")
    def test_034_args_not_object(self): self.assertEqual(self.cv(base(args=[])).reason, "ARGS_MUST_BE_OBJECT")
    def test_035_risk_not_object(self): self.assertEqual(self.cv(base(risk=[])).reason, "RISK_MUST_BE_OBJECT")
    def test_036_unknown_risk_field(self): self.assertEqual(self.cv(base(risk={"magic":True})).reason, "UNKNOWN_RISK_FIELD")
    def test_037_risk_non_bool(self): self.assertEqual(self.cv(base(risk={"destructive":1})).reason, "RISK_VALUES_MUST_BE_BOOL")
    def test_038_risk_normalized(self): self.assertEqual(set(self.cv(base()).typed_action.risk), {"destructive","external_side_effect","high_privilege","irreversible"})
    def test_039_candidate_fp_stable(self): self.assertEqual(self.cv(base()).typed_action.candidate_fingerprint, TypedActionConverter(enable_cache=False).convert(json.dumps(base(), ensure_ascii=False, separators=(",", ":"))).typed_action.candidate_fingerprint)
    def test_040_cache_hit_marked(self):
        raw=json.dumps(base(), separators=(",", ":")); self.c.convert(raw); self.assertTrue(self.c.convert(raw).from_cache)
    def test_041_cache_does_not_authorize(self):
        raw=json.dumps(base(), separators=(",", ":")); self.c.convert(raw); self.assertFalse(self.c.convert(raw).authorized)
    def test_042_cache_does_not_execute(self):
        raw=json.dumps(base(), separators=(",", ":")); self.c.convert(raw); self.assertFalse(self.c.convert(raw).executed)
    def test_043_changed_target_changes_fp(self): self.assertNotEqual(self.cv(base()).typed_action.candidate_fingerprint, self.cv(base(target="calendar://other")).typed_action.candidate_fingerprint)
    def test_044_changed_purpose_changes_fp(self): self.assertNotEqual(self.cv(base()).typed_action.candidate_fingerprint, self.cv(base(purpose="other")).typed_action.candidate_fingerprint)
    def test_045_changed_args_changes_fp(self): self.assertNotEqual(self.cv(base()).typed_action.candidate_fingerprint, self.cv(base(args={"date":"2026-11-03"})).typed_action.candidate_fingerprint)
    def test_046_changed_risk_changes_fp(self): self.assertNotEqual(self.cv(base()).typed_action.candidate_fingerprint, self.cv(base(risk={"destructive":True})).typed_action.candidate_fingerprint)
    def test_047_large_input_denied(self): self.assertEqual(TypedActionConverter(ConversionPolicy(max_input_bytes=20)).convert(json.dumps(base())).reason, "INPUT_TOO_LARGE")
    def test_048_long_string_denied(self): self.assertEqual(TypedActionConverter(ConversionPolicy(max_string_length=10)).convert(json.dumps(base())).reason, "STRING_TOO_LONG")
    def test_049_too_many_args_denied(self): self.assertEqual(TypedActionConverter(ConversionPolicy(max_args_keys=1)).convert(json.dumps(base(args={"a":1,"b":2}))).reason, "TOO_MANY_ARGS")
    def test_050_depth_denied(self): self.assertEqual(TypedActionConverter(ConversionPolicy(max_depth=2)).convert(json.dumps(base(args={"a":{"b":{"c":1}}}))).reason, "MAX_DEPTH_EXCEEDED")
    def test_051_nan_denied(self): self.assertEqual(self.c.convert('{"version":"1","action_type":"TOOL_REQUEST","operation":"x","target":"x","purpose":"x","args":{"v":NaN}}').reason, "INVALID_JSON_OR_NON_JSON_WRAPPER")
    def test_052_infinity_denied(self): self.assertEqual(self.c.convert('{"version":"1","action_type":"TOOL_REQUEST","operation":"x","target":"x","purpose":"x","args":{"v":Infinity}}').reason, "INVALID_JSON_OR_NON_JSON_WRAPPER")
    def test_053_negative_numbers_allowed(self): self.assertEqual(self.cv(base(args={"n":-1})).decision, "TYPED_CANDIDATE")
    def test_054_bool_allowed(self): self.assertEqual(self.cv(base(args={"ok":True})).decision, "TYPED_CANDIDATE")
    def test_055_null_allowed(self): self.assertEqual(self.cv(base(args={"x":None})).decision, "TYPED_CANDIDATE")
    def test_056_list_allowed(self): self.assertEqual(self.cv(base(args={"xs":[1,2,3]})).decision, "TYPED_CANDIDATE")
    def test_057_unicode_allowed(self): self.assertEqual(self.cv(base(purpose="予定を読む", args={"名前":"のえぴん"})).decision, "TYPED_CANDIDATE")
    def test_058_target_trimmed(self): self.assertEqual(self.cv(base(target="  x  ")).typed_action.target, "x")
    def test_059_purpose_trimmed(self): self.assertEqual(self.cv(base(purpose="  read  ")).typed_action.purpose, "read")
    def test_060_converter_has_no_execute_method(self): self.assertFalse(hasattr(self.c, "execute"))
    def test_061_converter_has_no_commit_method(self): self.assertFalse(hasattr(self.c, "commit"))
    def test_062_result_reason_requires_downstream(self): self.assertIn("DOWNSTREAM_AUTHORIZATION_REQUIRED", self.cv(base()).reason)
    def test_063_schema_valid_only_on_candidate(self): self.assertTrue(self.cv(base()).schema_valid)
    def test_064_deny_schema_invalid(self): self.assertFalse(self.c.convert("bad").schema_valid)
    def test_065_cache_key_policy_sensitive(self):
        raw=json.dumps(base(), separators=(",", ":"))
        a=TypedActionConverter(ConversionPolicy(policy_version="A")); b=TypedActionConverter(ConversionPolicy(policy_version="B"))
        self.assertNotEqual(a._cache_key(raw), b._cache_key(raw))
    def test_066_result_fingerprint_deterministic(self):
        raw=json.dumps(base(), separators=(",", ":"))
        a=TypedActionConverter(enable_cache=False).convert(raw); b=TypedActionConverter(enable_cache=False).convert(raw)
        self.assertEqual(conversion_fingerprint(a), conversion_fingerprint(b))


if __name__ == "__main__":
    unittest.main(verbosity=2)
