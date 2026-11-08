import json
import random
import unittest
from NOEPIN_AL_001_AI_SUPERVISOR_SUCCESSOR_V2 import (
    AISupervisor, Decision, GatewayDecision, RolePolicy, SupervisionRequest, default_policies
)


class TestAISupervisor(unittest.TestCase):
    def setUp(self):
        self.s = AISupervisor(
            default_policies(),
            policy_version="2.0.0",
            registered_agents={
                "obs-1": "observer",
                "dev-1": "developer",
                "op-1": "operator",
            },
        )

    def req(self, **kw):
        base = dict(
            agent_id="dev-1", role="developer", action="read",
            resource="project_read", risk=5, context={"task": "x"},
            schema_version="1",
        )
        base.update(kw)
        return SupervisionRequest(**base)

    def test_001_allow_low_risk(self):
        self.assertEqual(self.s.supervise(self.req()).decision, Decision.ALLOW)

    def test_002_unknown_agent_hold(self):
        self.assertEqual(self.s.supervise(self.req(agent_id="x")).decision, Decision.HOLD)

    def test_003_role_mismatch_deny(self):
        self.assertEqual(self.s.supervise(self.req(role="observer")).decision, Decision.DENY)

    def test_004_unknown_role_hold(self):
        s = AISupervisor(default_policies(), registered_agents={})
        self.assertEqual(s.supervise(self.req(role="unknown")).decision, Decision.HOLD)

    def test_005_action_not_allowed(self):
        self.assertEqual(self.s.supervise(self.req(action="publish_public")).decision, Decision.DENY)

    def test_006_explicit_deny(self):
        self.assertEqual(self.s.supervise(self.req(action="delete_production")).decision, Decision.DENY)

    def test_007_resource_not_allowed(self):
        self.assertEqual(self.s.supervise(self.req(resource="production")).decision, Decision.DENY)

    def test_008_risk_over_max(self):
        self.assertEqual(self.s.supervise(self.req(risk=61)).decision, Decision.DENY)

    def test_009_risk_human_confirm(self):
        self.assertEqual(self.s.supervise(self.req(risk=40)).decision, Decision.HUMAN_CONFIRM)

    def test_010_irreversible_human_confirm(self):
        self.assertEqual(self.s.supervise(self.req(irreversible=True)).decision, Decision.HUMAN_CONFIRM)

    def test_011_external_side_effect_human_confirm(self):
        self.assertEqual(self.s.supervise(self.req(external_side_effect=True)).decision, Decision.HUMAN_CONFIRM)

    def test_012_action_requires_human_confirm(self):
        self.assertEqual(self.s.supervise(self.req(action="propose_patch")).decision, Decision.HUMAN_CONFIRM)

    def test_013_gateway_deny_overrides(self):
        self.assertEqual(self.s.supervise(self.req(), gateway_decision=GatewayDecision.DENY).decision, Decision.DENY)

    def test_014_gateway_hold_overrides(self):
        self.assertEqual(self.s.supervise(self.req(), gateway_decision=GatewayDecision.HOLD).decision, Decision.HOLD)

    def test_015_gateway_human_confirm_overrides(self):
        self.assertEqual(
            self.s.supervise(self.req(), gateway_decision=GatewayDecision.HUMAN_CONFIRM).decision,
            Decision.HUMAN_CONFIRM,
        )

    def test_016_missing_agent_hold(self):
        self.assertEqual(self.s.supervise(self.req(agent_id="")).decision, Decision.HOLD)

    def test_017_missing_role_hold(self):
        self.assertEqual(self.s.supervise(self.req(role="")).decision, Decision.HOLD)

    def test_018_missing_action_hold(self):
        self.assertEqual(self.s.supervise(self.req(action="")).decision, Decision.HOLD)

    def test_019_missing_resource_hold(self):
        self.assertEqual(self.s.supervise(self.req(resource="")).decision, Decision.HOLD)

    def test_020_invalid_negative_risk_hold(self):
        self.assertEqual(self.s.supervise(self.req(risk=-1)).decision, Decision.HOLD)

    def test_021_invalid_high_risk_hold(self):
        self.assertEqual(self.s.supervise(self.req(risk=101)).decision, Decision.HOLD)

    def test_022_bool_risk_invalid(self):
        self.assertEqual(self.s.supervise(self.req(risk=True)).decision, Decision.HOLD)

    def test_023_missing_schema_hold(self):
        self.assertEqual(self.s.supervise(self.req(schema_version="")).decision, Decision.HOLD)

    def test_024_fingerprint_deterministic_mapping_order(self):
        a = self.req(context={"a":1,"b":2})
        b = self.req(context={"b":2,"a":1})
        self.assertEqual(self.s.fingerprint_request(a), self.s.fingerprint_request(b))

    def test_025_fingerprint_changes_on_action(self):
        self.assertNotEqual(self.s.fingerprint_request(self.req(action="read")),
                            self.s.fingerprint_request(self.req(action="inspect")))

    def test_026_cache_exact_state_reuse(self):
        a = self.s.supervise(self.req())
        b = self.s.supervise(self.req())
        self.assertFalse(a.cache_reused)
        self.assertTrue(b.cache_reused)
        self.assertEqual(a.decision, b.decision)

    def test_027_cache_not_reused_when_gateway_changes(self):
        self.s.supervise(self.req(), gateway_decision=GatewayDecision.ALLOW)
        b = self.s.supervise(self.req(), gateway_decision=GatewayDecision.HOLD)
        self.assertFalse(b.cache_reused)
        self.assertEqual(b.decision, Decision.HOLD)

    def test_028_policy_rotation_clears_cache(self):
        self.s.supervise(self.req())
        self.assertGreater(self.s.cache_size(), 0)
        self.s.rotate_policy_version("2.0.1")
        self.assertEqual(self.s.cache_size(), 0)

    def test_029_empty_policy_version_rejected(self):
        with self.assertRaises(ValueError):
            AISupervisor(default_policies(), policy_version="")

    def test_030_empty_policy_rotation_rejected(self):
        with self.assertRaises(ValueError):
            self.s.rotate_policy_version("")

    def test_031_result_not_authoritative(self):
        r = self.s.supervise(self.req())
        self.assertFalse(r.authoritative)

    def test_032_action_never_executed(self):
        r = self.s.supervise(self.req())
        self.assertFalse(r.action_executed)

    def test_033_cached_result_not_authoritative(self):
        self.s.supervise(self.req())
        r = self.s.supervise(self.req())
        self.assertTrue(r.cache_reused)
        self.assertFalse(r.authoritative)
        self.assertFalse(r.action_executed)

    def test_034_audit_chain_valid(self):
        for i in range(10):
            self.s.supervise(self.req(context={"i":i}))
        self.assertTrue(self.s.verify_audit_chain())

    def test_035_audit_sequence(self):
        for i in range(4):
            self.s.supervise(self.req(context={"i":i}))
        self.assertEqual([x.sequence for x in self.s.audit_events()], [1,2,3,4])

    def test_036_audit_previous_hash_links(self):
        self.s.supervise(self.req(context={"i":1}))
        self.s.supervise(self.req(context={"i":2}))
        a,b = self.s.audit_events()
        self.assertEqual(b.previous_hash, a.event_hash)

    def test_037_observer_read_allow(self):
        r = self.req(agent_id="obs-1", role="observer", action="read", resource="public", risk=1)
        self.assertEqual(self.s.supervise(r).decision, Decision.ALLOW)

    def test_038_observer_write_deny(self):
        r = self.req(agent_id="obs-1", role="observer", action="write", resource="public", risk=1)
        self.assertEqual(self.s.supervise(r).decision, Decision.DENY)

    def test_039_operator_deploy_human(self):
        r = self.req(agent_id="op-1", role="operator", action="deploy_candidate",
                     resource="candidate_runtime", risk=10)
        self.assertEqual(self.s.supervise(r).decision, Decision.HUMAN_CONFIRM)

    def test_040_operator_bypass_policy_deny(self):
        r = self.req(agent_id="op-1", role="operator", action="bypass_policy",
                     resource="candidate_runtime", risk=1)
        self.assertEqual(self.s.supervise(r).decision, Decision.DENY)

    def test_041_risk_boundary_below_confirm(self):
        self.assertEqual(self.s.supervise(self.req(risk=39)).decision, Decision.ALLOW)

    def test_042_risk_boundary_confirm(self):
        self.assertEqual(self.s.supervise(self.req(risk=40)).decision, Decision.HUMAN_CONFIRM)

    def test_043_risk_boundary_max(self):
        self.assertEqual(self.s.supervise(self.req(risk=60)).decision, Decision.HUMAN_CONFIRM)

    def test_044_risk_boundary_over_max(self):
        self.assertEqual(self.s.supervise(self.req(risk=61)).decision, Decision.DENY)

    def test_045_cache_separates_context(self):
        self.s.supervise(self.req(context={"x":1}))
        b = self.s.supervise(self.req(context={"x":2}))
        self.assertFalse(b.cache_reused)

    def test_046_cache_separates_authority_refs(self):
        self.s.supervise(self.req(authority_refs={"policy":"a"}))
        b = self.s.supervise(self.req(authority_refs={"policy":"b"}))
        self.assertFalse(b.cache_reused)

    def test_047_cache_separates_schema(self):
        self.s.supervise(self.req(schema_version="1"))
        b = self.s.supervise(self.req(schema_version="2"))
        self.assertFalse(b.cache_reused)

    def test_048_cache_disabled(self):
        s = AISupervisor(default_policies(), registered_agents={"dev-1":"developer"}, enable_exact_state_cache=False)
        a = s.supervise(self.req())
        b = s.supervise(self.req())
        self.assertFalse(a.cache_reused)
        self.assertFalse(b.cache_reused)
        self.assertEqual(s.cache_size(), 0)

    def test_049_wildcard_resource(self):
        p = RolePolicy(role="x", allowed_actions=frozenset({"read"}), allowed_resources=frozenset({"*"}))
        s = AISupervisor({"x":p}, registered_agents={"x1":"x"})
        r = self.req(agent_id="x1", role="x", resource="anything", action="read", risk=0)
        self.assertEqual(s.supervise(r).decision, Decision.ALLOW)

    def test_050_exact_resource(self):
        p = RolePolicy(role="x", allowed_actions=frozenset({"read"}), allowed_resources=frozenset({"r1"}))
        s = AISupervisor({"x":p}, registered_agents={"x1":"x"})
        r = self.req(agent_id="x1", role="x", resource="r1", action="read", risk=0)
        self.assertEqual(s.supervise(r).decision, Decision.ALLOW)

    def test_051_other_resource_deny(self):
        p = RolePolicy(role="x", allowed_actions=frozenset({"read"}), allowed_resources=frozenset({"r1"}))
        s = AISupervisor({"x":p}, registered_agents={"x1":"x"})
        r = self.req(agent_id="x1", role="x", resource="r2", action="read", risk=0)
        self.assertEqual(s.supervise(r).decision, Decision.DENY)

    def test_052_stable_payload_excludes_time(self):
        a = self.s.supervise(self.req(context={"stable":1}))
        self.s.clear_cache()
        b = self.s.supervise(self.req(context={"stable":1}))
        self.assertEqual(a.stable_payload(), b.stable_payload())

    def test_053_reason_code_allow(self):
        self.assertIn("POLICY_ALLOW", self.s.supervise(self.req()).reason_codes)

    def test_054_reason_code_unknown_agent(self):
        self.assertIn("UNKNOWN_AGENT", self.s.supervise(self.req(agent_id="z")).reason_codes)

    def test_055_reason_code_gateway(self):
        self.assertIn("SECURITY_GATEWAY_DENY",
                      self.s.supervise(self.req(), gateway_decision=GatewayDecision.DENY).reason_codes)

    def test_056_requested_effect_changes_fingerprint(self):
        a = self.req(requested_effect="read-only")
        b = self.req(requested_effect="mutate")
        self.assertNotEqual(self.s.fingerprint_request(a), self.s.fingerprint_request(b))

    def test_057_irreversible_changes_fingerprint(self):
        self.assertNotEqual(self.s.fingerprint_request(self.req(irreversible=False)),
                            self.s.fingerprint_request(self.req(irreversible=True)))

    def test_058_external_side_effect_changes_fingerprint(self):
        self.assertNotEqual(self.s.fingerprint_request(self.req(external_side_effect=False)),
                            self.s.fingerprint_request(self.req(external_side_effect=True)))

    def test_059_audit_on_cache_hit(self):
        self.s.supervise(self.req())
        self.s.supervise(self.req())
        self.assertEqual(len(self.s.audit_events()), 2)

    def test_060_audit_chain_after_cache_hits(self):
        for _ in range(8):
            self.s.supervise(self.req())
        self.assertTrue(self.s.verify_audit_chain())

    def test_061_no_registered_agents_mode_still_policy_checks(self):
        s = AISupervisor(default_policies(), registered_agents={})
        self.assertEqual(s.supervise(self.req(agent_id="anything")).decision, Decision.ALLOW)

    def test_062_policy_denial_precedes_human_confirm_action(self):
        p = RolePolicy(role="x", allowed_actions=frozenset({"a"}), denied_actions=frozenset({"a"}),
                       human_confirm_actions=frozenset({"a"}), allowed_resources=frozenset({"*"}))
        s = AISupervisor({"x":p}, registered_agents={"x1":"x"})
        r = self.req(agent_id="x1", role="x", action="a", resource="r", risk=0)
        self.assertEqual(s.supervise(r).decision, Decision.DENY)

    def test_063_gateway_deny_precedes_unknown_agent(self):
        r = self.req(agent_id="unknown")
        self.assertEqual(s := self.s.supervise(r, gateway_decision=GatewayDecision.DENY).decision, Decision.DENY)

    def test_064_audit_event_hash_len(self):
        self.s.supervise(self.req())
        self.assertEqual(len(self.s.audit_events()[0].event_hash), 64)

    def test_065_request_fp_len(self):
        self.assertEqual(len(self.s.fingerprint_request(self.req())), 64)

    def test_066_deterministic_decisions_corpus(self):
        corpus = []
        for i in range(100):
            corpus.append(self.req(
                action=["read","inspect","run_test","propose_patch"][i % 4],
                resource=["project_read","sandbox","test_runtime"][i % 3],
                risk=i % 61,
                context={"i": i, "mod": i % 7},
                irreversible=(i % 29 == 0),
                external_side_effect=(i % 31 == 0),
            ))
        def run():
            s = AISupervisor(default_policies(), policy_version="2.0.0", registered_agents={"dev-1":"developer"})
            return [(s.supervise(r).decision.value, s.supervise(r).reason_codes) for r in corpus]
        self.assertEqual(run(), run())


if __name__ == "__main__":
    unittest.main(verbosity=2)
