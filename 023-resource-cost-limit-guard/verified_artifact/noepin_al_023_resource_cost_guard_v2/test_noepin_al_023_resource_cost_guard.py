import unittest, hashlib, json
from noepin_al_023_resource_cost_guard import *

def req(**kw):
    d=dict(
        request_id="r1", workload_id="w1", agent_id="agent", operation="research",
        budget_version=1, authority_version=1, observed_epoch_ms=1000,
        max_cost_usd=10.0, used_cost_usd=2.0, projected_incremental_cost_usd=1.0,
        max_tokens=10000, used_tokens=2000, projected_incremental_tokens=1000,
        max_elapsed_ms=60000, elapsed_ms=10000, projected_incremental_ms=5000,
        max_api_calls=100, api_calls_used=10, projected_incremental_calls=5,
        max_iterations=50, iterations_used=5, projected_incremental_iterations=2,
        max_cpu_seconds=120.0, cpu_seconds_used=10.0, projected_incremental_cpu_seconds=5.0,
        max_gpu_seconds=120.0, gpu_seconds_used=5.0, projected_incremental_gpu_seconds=2.0,
        deadline_epoch_ms=100000, rate_limit_per_window=20, calls_in_window=5,
        window_end_epoch_ms=2000, hard_stop_requested=False, provider_rate_limited=False,
        high_cost_operation=False, human_approved=False, approval_ref=None,
        schema_version="1", context={}
    )
    d.update(kw)
    return ResourceRequest(**d)

class GuardTests(unittest.TestCase):
    def setUp(self): self.g=ResourceCostGuard(policy_version="v2")
    def check(self,r,d):
        o=self.g.evaluate(r); self.assertEqual(o.decision,d)
        self.assertFalse(o.process_stopped); self.assertFalse(o.api_calls_stopped)
        self.assertFalse(o.billing_stopped); self.assertFalse(o.resources_released)
        self.assertFalse(o.action_executed); self.assertFalse(o.action_succeeded)
        self.assertFalse(o.state_committed); self.assertFalse(o.authoritative)
        return o

    def test_allow(self): self.check(req(),ResourceDecision.ALLOW_PREPARE)
    def test_missing_request(self): self.check(req(request_id=""),ResourceDecision.HOLD)
    def test_missing_workload(self): self.check(req(workload_id=""),ResourceDecision.HOLD)
    def test_missing_agent(self): self.check(req(agent_id=""),ResourceDecision.HOLD)
    def test_missing_operation(self): self.check(req(operation=""),ResourceDecision.HOLD)
    def test_missing_schema(self): self.check(req(schema_version=""),ResourceDecision.HOLD)
    def test_budget_version_zero(self): self.check(req(budget_version=0),ResourceDecision.HOLD)
    def test_authority_version_zero(self): self.check(req(authority_version=0),ResourceDecision.HOLD)
    def test_observed_bool(self): self.check(req(observed_epoch_ms=True),ResourceDecision.HOLD)

    def test_cost_exceeded(self): self.assertTrue(self.check(req(projected_incremental_cost_usd=9.0),ResourceDecision.STOP_PREPARE).stop_plan_created)
    def test_token_exceeded(self): self.check(req(projected_incremental_tokens=9000),ResourceDecision.STOP_PREPARE)
    def test_time_exceeded(self): self.check(req(projected_incremental_ms=60000),ResourceDecision.STOP_PREPARE)
    def test_calls_exceeded(self): self.check(req(projected_incremental_calls=100),ResourceDecision.STOP_PREPARE)
    def test_iterations_exceeded(self): self.check(req(projected_incremental_iterations=50),ResourceDecision.STOP_PREPARE)
    def test_cpu_exceeded(self): self.check(req(projected_incremental_cpu_seconds=200),ResourceDecision.STOP_PREPARE)
    def test_gpu_exceeded(self): self.check(req(projected_incremental_gpu_seconds=200),ResourceDecision.STOP_PREPARE)
    def test_multiple_exceeded(self):
        o=self.check(req(projected_incremental_cost_usd=20,projected_incremental_tokens=20000),ResourceDecision.STOP_PREPARE)
        self.assertGreaterEqual(len(o.reason_codes),2)

    def test_hard_stop(self): self.check(req(hard_stop_requested=True),ResourceDecision.STOP_PREPARE)
    def test_deadline_reached(self): self.check(req(deadline_epoch_ms=1000),ResourceDecision.STOP_PREPARE)
    def test_deadline_none(self): self.check(req(deadline_epoch_ms=None),ResourceDecision.ALLOW_PREPARE)
    def test_provider_rate_limit(self): self.assertTrue(self.check(req(provider_rate_limited=True),ResourceDecision.THROTTLE).throttle_plan_created)
    def test_local_rate_limit(self): self.check(req(calls_in_window=19,projected_incremental_calls=2),ResourceDecision.THROTTLE)
    def test_rate_limit_zero_unlimited(self): self.check(req(rate_limit_per_window=0,calls_in_window=999),ResourceDecision.ALLOW_PREPARE)

    def test_near_cost(self): self.assertTrue(self.check(req(used_cost_usd=8.0,projected_incremental_cost_usd=0.6),ResourceDecision.ALLOW_PREPARE).near_limit)
    def test_near_token(self): self.assertTrue(self.check(req(used_tokens=8500,projected_incremental_tokens=0),ResourceDecision.ALLOW_PREPARE).near_limit)
    def test_near_time(self): self.assertTrue(self.check(req(elapsed_ms=51000,projected_incremental_ms=0),ResourceDecision.ALLOW_PREPARE).near_limit)
    def test_near_calls(self): self.assertTrue(self.check(req(api_calls_used=85,projected_incremental_calls=0),ResourceDecision.ALLOW_PREPARE).near_limit)
    def test_near_iterations(self): self.assertTrue(self.check(req(iterations_used=43,projected_incremental_iterations=0),ResourceDecision.ALLOW_PREPARE).near_limit)
    def test_near_cpu(self): self.assertTrue(self.check(req(cpu_seconds_used=102,projected_incremental_cpu_seconds=0),ResourceDecision.ALLOW_PREPARE).near_limit)
    def test_near_gpu(self): self.assertTrue(self.check(req(gpu_seconds_used=102,projected_incremental_gpu_seconds=0),ResourceDecision.ALLOW_PREPARE).near_limit)

    def test_high_cost_confirm(self): self.check(req(high_cost_operation=True),ResourceDecision.HUMAN_CONFIRM)
    def test_high_cost_bool_without_ref(self): self.check(req(high_cost_operation=True,human_approved=True),ResourceDecision.HUMAN_CONFIRM)
    def test_high_cost_ref_without_bool(self): self.check(req(high_cost_operation=True,approval_ref="A"),ResourceDecision.HUMAN_CONFIRM)
    def test_high_cost_approved(self): self.check(req(high_cost_operation=True,human_approved=True,approval_ref="A"),ResourceDecision.ALLOW_PREPARE)
    def test_approval_does_not_bypass_limit(self):
        self.check(req(high_cost_operation=True,human_approved=True,approval_ref="A",projected_incremental_cost_usd=20),ResourceDecision.STOP_PREPARE)

    def test_negative_cost_invalid(self): self.check(req(used_cost_usd=-1),ResourceDecision.HOLD)
    def test_negative_tokens_invalid(self): self.check(req(used_tokens=-1),ResourceDecision.HOLD)
    def test_negative_elapsed_invalid(self): self.check(req(elapsed_ms=-1),ResourceDecision.HOLD)
    def test_negative_calls_invalid(self): self.check(req(api_calls_used=-1),ResourceDecision.HOLD)
    def test_negative_iterations_invalid(self): self.check(req(iterations_used=-1),ResourceDecision.HOLD)
    def test_negative_cpu_invalid(self): self.check(req(cpu_seconds_used=-1),ResourceDecision.HOLD)
    def test_negative_gpu_invalid(self): self.check(req(gpu_seconds_used=-1),ResourceDecision.HOLD)
    def test_bad_deadline_bool(self): self.check(req(deadline_epoch_ms=True),ResourceDecision.HOLD)
    def test_bad_window_bool(self): self.check(req(window_end_epoch_ms=True),ResourceDecision.HOLD)
    def test_bad_max_tokens_bool(self): self.check(req(max_tokens=True),ResourceDecision.HOLD)
    def test_bad_max_cost_bool(self): self.check(req(max_cost_usd=True),ResourceDecision.HOLD)

    def test_cache_reused(self):
        a=self.g.evaluate(req()); b=self.g.evaluate(req()); self.assertFalse(a.cache_reused); self.assertTrue(b.cache_reused)
    def test_cache_no_stop_execution(self):
        r=req(hard_stop_requested=True); self.g.evaluate(r); self.assertFalse(self.g.evaluate(r).process_stopped)
    def test_cache_no_billing_stop(self):
        r=req(projected_incremental_cost_usd=20); self.g.evaluate(r); self.assertFalse(self.g.evaluate(r).billing_stopped)
    def test_fingerprint_usage_change(self): self.assertNotEqual(self.g.fingerprint(req()),self.g.fingerprint(req(used_tokens=2001)))
    def test_fingerprint_budget_version(self): self.assertNotEqual(self.g.fingerprint(req()),self.g.fingerprint(req(budget_version=2)))
    def test_fingerprint_deadline(self): self.assertNotEqual(self.g.fingerprint(req()),self.g.fingerprint(req(deadline_epoch_ms=99999)))
    def test_fingerprint_context_order(self): self.assertEqual(self.g.fingerprint(req(context={"b":2,"a":1})),self.g.fingerprint(req(context={"a":1,"b":2})))
    def test_clear_cache(self): self.g.evaluate(req()); self.g.clear_cache(); self.assertEqual(self.g.cache_size(),0)
    def test_stable_excludes_time(self): self.assertNotIn("created_unix_ns",self.g.evaluate(req()).stable_payload())

    def test_projected_values(self):
        o=self.check(req(),ResourceDecision.ALLOW_PREPARE)
        self.assertEqual(o.projected_tokens,3000); self.assertEqual(o.projected_api_calls,15)
        self.assertAlmostEqual(o.projected_cost_usd,3.0)
    def test_zero_budget_nonzero_usage_stops(self): self.check(req(max_cost_usd=0,used_cost_usd=0,projected_incremental_cost_usd=0.1),ResourceDecision.STOP_PREPARE)
    def test_zero_budget_zero_usage_allowed(self): self.check(req(max_cost_usd=0,used_cost_usd=0,projected_incremental_cost_usd=0),ResourceDecision.ALLOW_PREPARE)
    def test_custom_near_ratio(self):
        g=ResourceCostGuard(policy_version="v2",near_limit_ratio=0.5)
        self.assertTrue(g.evaluate(req(used_cost_usd=5,projected_incremental_cost_usd=0)).near_limit)
    def test_disable_high_cost_confirm(self):
        g=ResourceCostGuard(policy_version="v2",high_cost_requires_human=False)
        self.assertEqual(g.evaluate(req(high_cost_operation=True)).decision,ResourceDecision.ALLOW_PREPARE)
    def test_bad_near_ratio_low(self):
        with self.assertRaises(ValueError): ResourceCostGuard(near_limit_ratio=0)
    def test_bad_near_ratio_high(self):
        with self.assertRaises(ValueError): ResourceCostGuard(near_limit_ratio=1)
    def test_policy_version_required(self):
        with self.assertRaises(ValueError): ResourceCostGuard(policy_version="")


def replay_fingerprint():
    g=ResourceCostGuard(policy_version="v2")
    out=[]
    for i in range(1000):
        r=req(
            request_id=f"r{i}", workload_id=f"w{i%13}",
            used_cost_usd=float(i%70)/10.0,
            projected_incremental_cost_usd=float(i%5)/10.0,
            used_tokens=(i*37)%8000,
            projected_incremental_tokens=(i*13)%1200,
            api_calls_used=i%70,
            projected_incremental_calls=i%9,
            iterations_used=i%35,
            projected_incremental_iterations=i%4,
            cpu_seconds_used=float(i%80), projected_incremental_cpu_seconds=float(i%6),
            gpu_seconds_used=float(i%50), projected_incremental_gpu_seconds=float(i%4),
            provider_rate_limited=(i%97==0),
            high_cost_operation=(i%29==0),
            human_approved=(i%31==0), approval_ref="A" if i%31==0 else None,
            hard_stop_requested=(i%211==0),
            context={"i":i%5,"z":i%7}
        )
        out.append(g.evaluate(r).stable_payload())
    raw=json.dumps(out,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

if __name__=="__main__":
    unittest.main()
