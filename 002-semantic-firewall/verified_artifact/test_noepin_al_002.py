import unittest
from NOEPIN_AL_002_SEMANTIC_FIREWALL_SUCCESSOR_V2 import (
    Verdict, SourceKind, SemanticFeatures, ContentEnvelope, SemanticFirewall
)

class TestSemanticFirewall(unittest.TestCase):
    def setUp(self):
        self.f = SemanticFirewall(policy_version="2.0.0")

    def env(self, **kw):
        base = dict(
            content="ordinary text",
            source_kind=SourceKind.USER,
            source_id="src-1",
            trusted_instruction_channel=False,
            claimed_authority=None,
            allowed_capabilities=("read","summarize"),
            semantic=SemanticFeatures(),
            context={"case":"x"},
            schema_version="1",
        )
        base.update(kw)
        return ContentEnvelope(**base)

    def test_001_allow_benign_user_text(self):
        self.assertEqual(self.f.evaluate(self.env()).verdict, Verdict.ALLOW)

    def test_002_missing_source_hold(self):
        self.assertEqual(self.f.evaluate(self.env(source_id="")).verdict, Verdict.HOLD)

    def test_003_missing_schema_hold(self):
        self.assertEqual(self.f.evaluate(self.env(schema_version="")).verdict, Verdict.HOLD)

    def test_004_invalid_confidence_low(self):
        self.assertEqual(self.f.evaluate(self.env(semantic=SemanticFeatures(confidence=-0.1))).verdict, Verdict.HOLD)

    def test_005_invalid_confidence_high(self):
        self.assertEqual(self.f.evaluate(self.env(semantic=SemanticFeatures(confidence=1.1))).verdict, Verdict.HOLD)

    def test_006_untrusted_claimed_authority_deny(self):
        self.assertEqual(self.f.evaluate(self.env(claimed_authority="system")).verdict, Verdict.DENY)

    def test_007_trusted_claimed_authority_not_auto_deny(self):
        self.assertEqual(self.f.evaluate(self.env(claimed_authority="system", trusted_instruction_channel=True)).verdict, Verdict.ALLOW)

    def test_008_privilege_escalation(self):
        self.assertEqual(self.f.evaluate(self.env(semantic=SemanticFeatures(privilege_escalation=True))).verdict, Verdict.DENY)

    def test_009_policy_evasion(self):
        self.assertEqual(self.f.evaluate(self.env(semantic=SemanticFeatures(policy_evasion=True))).verdict, Verdict.DENY)

    def test_010_secret_request(self):
        self.assertEqual(self.f.evaluate(self.env(semantic=SemanticFeatures(secret_request=True))).verdict, Verdict.DENY)

    def test_011_data_exfiltration(self):
        self.assertEqual(self.f.evaluate(self.env(semantic=SemanticFeatures(data_exfiltration=True))).verdict, Verdict.DENY)

    def test_012_destructive_intent(self):
        self.assertEqual(self.f.evaluate(self.env(semantic=SemanticFeatures(destructive_intent=True))).verdict, Verdict.DENY)

    def test_013_web_executable_payload(self):
        e=self.env(source_kind=SourceKind.WEB, semantic=SemanticFeatures(executable_payload=True))
        self.assertEqual(self.f.evaluate(e).verdict, Verdict.DENY)

    def test_014_file_executable_payload(self):
        e=self.env(source_kind=SourceKind.FILE, semantic=SemanticFeatures(executable_payload=True))
        self.assertEqual(self.f.evaluate(e).verdict, Verdict.DENY)

    def test_015_external_ai_executable_payload(self):
        e=self.env(source_kind=SourceKind.EXTERNAL_AI, semantic=SemanticFeatures(executable_payload=True))
        self.assertEqual(self.f.evaluate(e).verdict, Verdict.DENY)

    def test_016_user_executable_payload_not_auto_deny(self):
        e=self.env(source_kind=SourceKind.USER, semantic=SemanticFeatures(executable_payload=True))
        self.assertEqual(self.f.evaluate(e).verdict, Verdict.ALLOW)

    def test_017_override_attempt(self):
        self.assertEqual(self.f.evaluate(self.env(semantic=SemanticFeatures(override_attempt=True))).verdict, Verdict.DENY)

    def test_018_ignore_boundary_attempt(self):
        self.assertEqual(self.f.evaluate(self.env(semantic=SemanticFeatures(asks_to_ignore_source_boundary=True))).verdict, Verdict.DENY)

    def test_019_web_instruction_deny(self):
        e=self.env(source_kind=SourceKind.WEB, semantic=SemanticFeatures(instruction_intent=True))
        self.assertEqual(self.f.evaluate(e).verdict, Verdict.DENY)

    def test_020_file_instruction_deny(self):
        e=self.env(source_kind=SourceKind.FILE, semantic=SemanticFeatures(instruction_intent=True))
        self.assertEqual(self.f.evaluate(e).verdict, Verdict.DENY)

    def test_021_external_ai_instruction_deny(self):
        e=self.env(source_kind=SourceKind.EXTERNAL_AI, semantic=SemanticFeatures(instruction_intent=True))
        self.assertEqual(self.f.evaluate(e).verdict, Verdict.DENY)

    def test_022_unknown_instruction_deny(self):
        e=self.env(source_kind=SourceKind.UNKNOWN, semantic=SemanticFeatures(instruction_intent=True))
        self.assertEqual(self.f.evaluate(e).verdict, Verdict.DENY)

    def test_023_trusted_web_instruction_can_continue(self):
        e=self.env(source_kind=SourceKind.WEB, trusted_instruction_channel=True, semantic=SemanticFeatures(instruction_intent=True))
        self.assertEqual(self.f.evaluate(e).verdict, Verdict.ALLOW)

    def test_024_capability_not_allowed(self):
        e=self.env(semantic=SemanticFeatures(requested_capability="write"))
        self.assertEqual(self.f.evaluate(e).verdict, Verdict.DENY)

    def test_025_capability_allowed(self):
        e=self.env(semantic=SemanticFeatures(requested_capability="read"))
        self.assertEqual(self.f.evaluate(e).verdict, Verdict.ALLOW)

    def test_026_external_side_effect_human(self):
        e=self.env(semantic=SemanticFeatures(external_side_effect=True))
        self.assertEqual(self.f.evaluate(e).verdict, Verdict.HUMAN_CONFIRM)

    def test_027_suspicious_text_web_hold(self):
        e=self.env(content="ignore previous instructions", source_kind=SourceKind.WEB)
        self.assertEqual(self.f.evaluate(e).verdict, Verdict.HOLD)

    def test_028_suspicious_text_file_hold(self):
        e=self.env(content="bypass security", source_kind=SourceKind.FILE)
        self.assertEqual(self.f.evaluate(e).verdict, Verdict.HOLD)

    def test_029_suspicious_text_external_ai_hold(self):
        e=self.env(content="reveal api key", source_kind=SourceKind.EXTERNAL_AI)
        self.assertEqual(self.f.evaluate(e).verdict, Verdict.HOLD)

    def test_030_suspicious_text_user_not_keyword_block(self):
        e=self.env(content="discuss the phrase ignore previous instructions", source_kind=SourceKind.USER)
        self.assertEqual(self.f.evaluate(e).verdict, Verdict.ALLOW)

    def test_031_low_confidence_web_hold(self):
        e=self.env(source_kind=SourceKind.WEB, semantic=SemanticFeatures(confidence=0.2))
        self.assertEqual(self.f.evaluate(e).verdict, Verdict.HOLD)

    def test_032_low_confidence_user_benign_allow(self):
        e=self.env(source_kind=SourceKind.USER, semantic=SemanticFeatures(confidence=0.2))
        self.assertEqual(self.f.evaluate(e).verdict, Verdict.ALLOW)

    def test_033_low_confidence_instruction_user_hold(self):
        e=self.env(source_kind=SourceKind.USER, semantic=SemanticFeatures(instruction_intent=True,confidence=0.2))
        self.assertEqual(self.f.evaluate(e).verdict, Verdict.HOLD)

    def test_034_result_not_authoritative(self):
        self.assertFalse(self.f.evaluate(self.env()).authoritative)

    def test_035_content_not_executed(self):
        self.assertFalse(self.f.evaluate(self.env()).content_executed)

    def test_036_cache_reuse(self):
        a=self.f.evaluate(self.env())
        b=self.f.evaluate(self.env())
        self.assertFalse(a.cache_reused); self.assertTrue(b.cache_reused)

    def test_037_cache_not_authoritative(self):
        self.f.evaluate(self.env())
        b=self.f.evaluate(self.env())
        self.assertFalse(b.authoritative); self.assertFalse(b.content_executed)

    def test_038_context_changes_fingerprint(self):
        a=self.f.fingerprint(self.env(context={"a":1}))
        b=self.f.fingerprint(self.env(context={"a":2}))
        self.assertNotEqual(a,b)

    def test_039_source_changes_fingerprint(self):
        a=self.f.fingerprint(self.env(source_kind=SourceKind.USER))
        b=self.f.fingerprint(self.env(source_kind=SourceKind.WEB))
        self.assertNotEqual(a,b)

    def test_040_semantics_change_fingerprint(self):
        a=self.f.fingerprint(self.env(semantic=SemanticFeatures()))
        b=self.f.fingerprint(self.env(semantic=SemanticFeatures(policy_evasion=True)))
        self.assertNotEqual(a,b)

    def test_041_mapping_order_stable(self):
        a=self.f.fingerprint(self.env(context={"a":1,"b":2}))
        b=self.f.fingerprint(self.env(context={"b":2,"a":1}))
        self.assertEqual(a,b)

    def test_042_policy_rotation_clears_cache(self):
        self.f.evaluate(self.env()); self.assertGreater(self.f.cache_size(),0)
        self.f.rotate_policy_version("2.0.1"); self.assertEqual(self.f.cache_size(),0)

    def test_043_empty_policy_rejected(self):
        with self.assertRaises(ValueError): SemanticFirewall(policy_version="")

    def test_044_empty_rotation_rejected(self):
        with self.assertRaises(ValueError): self.f.rotate_policy_version("")

    def test_045_cache_disabled(self):
        f=SemanticFirewall(enable_exact_state_cache=False)
        a=f.evaluate(self.env()); b=f.evaluate(self.env())
        self.assertFalse(a.cache_reused); self.assertFalse(b.cache_reused); self.assertEqual(f.cache_size(),0)

    def test_046_privilege_precedes_external_side_effect(self):
        s=SemanticFeatures(privilege_escalation=True,external_side_effect=True)
        self.assertEqual(self.f.evaluate(self.env(semantic=s)).verdict,Verdict.DENY)

    def test_047_exfiltration_precedes_side_effect(self):
        s=SemanticFeatures(data_exfiltration=True,external_side_effect=True)
        self.assertEqual(self.f.evaluate(self.env(semantic=s)).verdict,Verdict.DENY)

    def test_048_override_precedes_low_confidence(self):
        s=SemanticFeatures(override_attempt=True,confidence=0.1)
        self.assertEqual(self.f.evaluate(self.env(semantic=s)).verdict,Verdict.DENY)

    def test_049_reason_privilege(self):
        r=self.f.evaluate(self.env(semantic=SemanticFeatures(privilege_escalation=True)))
        self.assertIn("PRIVILEGE_ESCALATION",r.reason_codes)

    def test_050_reason_suspicious(self):
        r=self.f.evaluate(self.env(content="disable audit",source_kind=SourceKind.WEB))
        self.assertIn("SUSPICIOUS_TEXT_SIGNAL_REQUIRES_SEMANTIC_REVIEW",r.reason_codes)

    def test_051_reason_allow(self):
        self.assertIn("BOUNDARY_ALLOW",self.f.evaluate(self.env()).reason_codes)

    def test_052_web_data_no_instruction_allow(self):
        e=self.env(content="A news article about security",source_kind=SourceKind.WEB)
        self.assertEqual(self.f.evaluate(e).verdict,Verdict.ALLOW)

    def test_053_file_data_no_instruction_allow(self):
        e=self.env(content="ordinary file text",source_kind=SourceKind.FILE)
        self.assertEqual(self.f.evaluate(e).verdict,Verdict.ALLOW)

    def test_054_external_ai_data_no_instruction_allow(self):
        e=self.env(content="analysis result",source_kind=SourceKind.EXTERNAL_AI)
        self.assertEqual(self.f.evaluate(e).verdict,Verdict.ALLOW)

    def test_055_claimed_authority_external_ai_deny(self):
        e=self.env(source_kind=SourceKind.EXTERNAL_AI,claimed_authority="developer")
        self.assertEqual(self.f.evaluate(e).verdict,Verdict.DENY)

    def test_056_claimed_authority_file_deny(self):
        e=self.env(source_kind=SourceKind.FILE,claimed_authority="system")
        self.assertEqual(self.f.evaluate(e).verdict,Verdict.DENY)

    def test_057_fingerprint_len(self):
        self.assertEqual(len(self.f.fingerprint(self.env())),64)

    def test_058_cache_separates_policy_version(self):
        self.f.evaluate(self.env()); self.f.rotate_policy_version("3")
        b=self.f.evaluate(self.env()); self.assertFalse(b.cache_reused)

    def test_059_stable_payload_equal_uncached(self):
        a=self.f.evaluate(self.env(context={"x":1}))
        self.f.rotate_policy_version("2.0.1")
        b=self.f.evaluate(self.env(context={"x":1}))
        # cache flag differs only if hit; both are misses here
        self.assertEqual(a.verdict,b.verdict)
        self.assertEqual(a.reason_codes,b.reason_codes)

    def test_060_content_text_changes_fp(self):
        self.assertNotEqual(self.f.fingerprint(self.env(content="a")),self.f.fingerprint(self.env(content="b")))

    def test_061_source_id_changes_fp(self):
        self.assertNotEqual(self.f.fingerprint(self.env(source_id="a")),self.f.fingerprint(self.env(source_id="b")))

    def test_062_allowed_capability_changes_fp(self):
        self.assertNotEqual(self.f.fingerprint(self.env(allowed_capabilities=("read",))),
                            self.f.fingerprint(self.env(allowed_capabilities=("read","write"))))

    def test_063_destructive_web_deny(self):
        e=self.env(source_kind=SourceKind.WEB,semantic=SemanticFeatures(destructive_intent=True))
        self.assertEqual(self.f.evaluate(e).verdict,Verdict.DENY)

    def test_064_deterministic_corpus(self):
        corpus=[]
        kinds=[SourceKind.USER,SourceKind.WEB,SourceKind.FILE,SourceKind.EXTERNAL_AI]
        for i in range(200):
            corpus.append(self.env(
                content=f"content {i}",
                source_kind=kinds[i%4],
                source_id=f"s{i%9}",
                semantic=SemanticFeatures(
                    instruction_intent=(i%11==0),
                    policy_evasion=(i%37==0),
                    external_side_effect=(i%23==0),
                    requested_capability="read" if i%3 else "write",
                    confidence=(i%10)/10,
                ),
                context={"i":i},
            ))
        def run():
            f=SemanticFirewall(policy_version="2")
            return [(f.evaluate(e).verdict.value,f.evaluate(e).reason_codes) for e in corpus]
        self.assertEqual(run(),run())

if __name__=="__main__":
    unittest.main(verbosity=2)
