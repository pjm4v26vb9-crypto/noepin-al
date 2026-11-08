import hashlib, json, unittest
from noepin_al_015_cascade_circuit_breaker import *

def policy():
    return BreakerPolicy(
        consecutive_failure_threshold=3,
        failure_count_threshold=5,
        error_rate_threshold_percent=50,
        fanout_trip_threshold=4,
        recovery_success_threshold=2,
        critical_failure_requires_human=True,
        policy_version="v2",
    )

def snap(state=CircuitState.CLOSED, **kw):
    d=dict(node_id="agent:a",state=state,generation=1,opened_at_epoch_s=None,last_transition_ref=None)
    if state==CircuitState.OPEN:
        d["opened_at_epoch_s"]=900
    d.update(kw)
    return BreakerSnapshot(**d)

def sig(**kw):
    d=dict(
        request_id="r1",snapshot=snap(),observed_epoch_s=1000,
        consecutive_failures=0,failure_count_window=0,sample_count_window=10,error_rate_percent=0,
        fanout_estimate=1,dependency_ids=("b",),critical_dependency_failure=False,
        validated_failure_evidence=False,upstream_breaker_open=False,emergency_stop_active=False,
        cooldown_elapsed=False,recovery_successes=0,recovery_probe_authorized=False,
        expected_generation=1,human_approved=False,approval_ref=None,schema_version="1",context={}
    )
    d.update(kw)
    return CascadeSignal(**d)

class T(unittest.TestCase):
    def setUp(self): self.b=CascadeCircuitBreaker(policy())
    def check(self,s,d):
        r=self.b.evaluate(s); self.assertEqual(r.decision,d)
        self.assertFalse(r.authoritative); self.assertFalse(r.dependencies_stopped)
        self.assertFalse(r.recovery_completed); self.assertFalse(r.action_executed); self.assertFalse(r.state_committed)
        return r

    def test_healthy_allow(self): self.check(sig(),BreakerDecision.ALLOW_PREPARE)
    def test_missing_request(self): self.check(sig(request_id=""),BreakerDecision.HOLD)
    def test_missing_schema(self): self.check(sig(schema_version=""),BreakerDecision.HOLD)
    def test_missing_node(self): self.check(sig(snapshot=snap(node_id="")),BreakerDecision.HOLD)
    def test_bad_time(self): self.check(sig(observed_epoch_s=-1),BreakerDecision.HOLD)
    def test_bad_generation(self): self.check(sig(snapshot=snap(generation=-1)),BreakerDecision.HOLD)
    def test_generation_mismatch(self): self.check(sig(expected_generation=2),BreakerDecision.HOLD)
    def test_bad_consecutive(self): self.check(sig(consecutive_failures=-1),BreakerDecision.HOLD)
    def test_bad_failure_count(self): self.check(sig(failure_count_window=-1),BreakerDecision.HOLD)
    def test_bad_sample_count(self): self.check(sig(sample_count_window=-1),BreakerDecision.HOLD)
    def test_bad_fanout(self): self.check(sig(fanout_estimate=-1),BreakerDecision.HOLD)
    def test_bad_recovery_successes(self): self.check(sig(recovery_successes=-1),BreakerDecision.HOLD)
    def test_bad_error_rate_low(self): self.check(sig(error_rate_percent=-1),BreakerDecision.HOLD)
    def test_bad_error_rate_high(self): self.check(sig(error_rate_percent=101),BreakerDecision.HOLD)
    def test_failure_gt_sample(self): self.check(sig(failure_count_window=6,sample_count_window=5),BreakerDecision.HOLD)
    def test_duplicate_dependency(self): self.check(sig(dependency_ids=("a","a")),BreakerDecision.HOLD)
    def test_empty_dependency(self): self.check(sig(dependency_ids=("a","")),BreakerDecision.HOLD)
    def test_open_requires_opened_at(self): self.check(sig(snapshot=snap(CircuitState.OPEN,opened_at_epoch_s=None)),BreakerDecision.HOLD)
    def test_opened_at_future(self): self.check(sig(snapshot=snap(CircuitState.OPEN,opened_at_epoch_s=1001)),BreakerDecision.HOLD)

    def test_unvalidated_failure_hold(self):
        self.check(sig(consecutive_failures=3,validated_failure_evidence=False),BreakerDecision.HOLD)
    def test_consecutive_trip(self):
        r=self.check(sig(consecutive_failures=3,validated_failure_evidence=True),BreakerDecision.TRIP_PREPARE)
        self.assertEqual(r.proposed_state,CircuitState.OPEN)
    def test_failure_count_trip(self):
        self.check(sig(failure_count_window=5,sample_count_window=10,validated_failure_evidence=True),BreakerDecision.TRIP_PREPARE)
    def test_error_rate_trip(self):
        self.check(sig(error_rate_percent=50,validated_failure_evidence=True),BreakerDecision.TRIP_PREPARE)
    def test_error_rate_49_no_trip(self):
        self.check(sig(error_rate_percent=49,validated_failure_evidence=True),BreakerDecision.ALLOW_PREPARE)
    def test_fanout_trip(self):
        self.check(sig(fanout_estimate=4,validated_failure_evidence=True),BreakerDecision.TRIP_PREPARE)
    def test_fanout_3_no_trip(self):
        self.check(sig(fanout_estimate=3,validated_failure_evidence=True),BreakerDecision.ALLOW_PREPARE)
    def test_critical_trip(self):
        r=self.check(sig(critical_dependency_failure=True,validated_failure_evidence=True),BreakerDecision.TRIP_PREPARE)
        self.assertIn("HUMAN_REVIEW_REQUIRED_FOR_CRITICAL_FAILURE",r.reason_codes)
    def test_critical_with_approval_still_prepare_only(self):
        r=self.check(sig(critical_dependency_failure=True,validated_failure_evidence=True,human_approved=True,approval_ref="H"),BreakerDecision.TRIP_PREPARE)
        self.assertFalse(r.dependencies_stopped)
    def test_upstream_open_trip_even_without_failure_evidence(self):
        self.check(sig(upstream_breaker_open=True),BreakerDecision.TRIP_PREPARE)
    def test_emergency_trip(self):
        self.check(sig(emergency_stop_active=True),BreakerDecision.TRIP_PREPARE)
    def test_emergency_with_approval_still_trip(self):
        self.check(sig(emergency_stop_active=True,human_approved=True,approval_ref="H"),BreakerDecision.TRIP_PREPARE)

    def test_open_cooldown_not_elapsed(self):
        self.check(sig(snapshot=snap(CircuitState.OPEN),cooldown_elapsed=False),BreakerDecision.TRIP_PREPARE)
    def test_open_requires_probe_auth(self):
        self.check(sig(snapshot=snap(CircuitState.OPEN),cooldown_elapsed=True),BreakerDecision.HOLD)
    def test_open_authorized_probe(self):
        r=self.check(sig(snapshot=snap(CircuitState.OPEN),cooldown_elapsed=True,recovery_probe_authorized=True),BreakerDecision.RECOVERY_PROBE)
        self.assertEqual(r.proposed_state,CircuitState.HALF_OPEN)
    def test_probe_not_recovery_complete(self):
        r=self.check(sig(snapshot=snap(CircuitState.OPEN),cooldown_elapsed=True,recovery_probe_authorized=True),BreakerDecision.RECOVERY_PROBE)
        self.assertFalse(r.recovery_completed)

    def test_half_open_failure_retrip(self):
        self.check(sig(snapshot=snap(CircuitState.HALF_OPEN),consecutive_failures=3,validated_failure_evidence=True),BreakerDecision.TRIP_PREPARE)
    def test_half_open_unvalidated_failure_hold(self):
        self.check(sig(snapshot=snap(CircuitState.HALF_OPEN),consecutive_failures=1),BreakerDecision.HOLD)
    def test_half_open_not_enough_success(self):
        self.check(sig(snapshot=snap(CircuitState.HALF_OPEN),recovery_successes=1),BreakerDecision.HOLD)
    def test_half_open_close_prepare_without_approval(self):
        r=self.check(sig(snapshot=snap(CircuitState.HALF_OPEN),recovery_successes=2),BreakerDecision.CLOSE_PREPARE)
        self.assertFalse(r.recovery_completed)
    def test_half_open_close_prepare_with_approval(self):
        r=self.check(sig(snapshot=snap(CircuitState.HALF_OPEN),recovery_successes=2,human_approved=True,approval_ref="H"),BreakerDecision.CLOSE_PREPARE)
        self.assertFalse(r.state_committed)

    def test_blast_radius_uses_fanout(self):
        self.assertEqual(self.b.evaluate(sig(fanout_estimate=5)).blast_radius_estimate,5)
    def test_blast_radius_uses_dependency_count(self):
        self.assertEqual(self.b.evaluate(sig(fanout_estimate=1,dependency_ids=("a","b","c"))).blast_radius_estimate,3)

    def test_cache_exact(self):
        s=sig(); a=self.b.evaluate(s); c=self.b.evaluate(s); self.assertFalse(a.cache_reused); self.assertTrue(c.cache_reused)
    def test_cache_never_authority(self):
        s=sig(); self.b.evaluate(s); self.assertFalse(self.b.evaluate(s).authoritative)
    def test_cache_never_stops_dependencies(self):
        s=sig(); self.b.evaluate(s); self.assertFalse(self.b.evaluate(s).dependencies_stopped)
    def test_emergency_bypasses_cache(self):
        self.b.evaluate(sig())
        r=self.b.evaluate(sig(emergency_stop_active=True))
        self.assertFalse(r.cache_reused); self.assertEqual(r.decision,BreakerDecision.TRIP_PREPARE)
    def test_failure_state_changes_fingerprint(self):
        self.assertNotEqual(self.b.fingerprint(sig()),self.b.fingerprint(sig(consecutive_failures=1)))
    def test_generation_changes_fingerprint(self):
        self.assertNotEqual(self.b.fingerprint(sig()),self.b.fingerprint(sig(snapshot=snap(generation=2),expected_generation=2)))
    def test_context_order(self):
        self.assertEqual(self.b.fingerprint(sig(context={"b":2,"a":1})),self.b.fingerprint(sig(context={"a":1,"b":2})))
    def test_clear_cache(self):
        self.b.evaluate(sig()); self.assertGreater(self.b.cache_size(),0); self.b.clear_cache(); self.assertEqual(self.b.cache_size(),0)
    def test_stable_no_time(self): self.assertNotIn("created_unix_ns",self.b.evaluate(sig()).stable_payload())

    def test_trip_not_actual_stop(self):
        r=self.check(sig(consecutive_failures=3,validated_failure_evidence=True),BreakerDecision.TRIP_PREPARE)
        self.assertFalse(r.dependencies_stopped)
    def test_close_prepare_not_recovery_complete(self):
        r=self.check(sig(snapshot=snap(CircuitState.HALF_OPEN),recovery_successes=2,human_approved=True,approval_ref="H"),BreakerDecision.CLOSE_PREPARE)
        self.assertFalse(r.recovery_completed)

def replay_fingerprint():
    b=CascadeCircuitBreaker(policy()); out=[]
    states=[CircuitState.CLOSED,CircuitState.OPEN,CircuitState.HALF_OPEN]
    for i in range(1000):
        st=states[i%3]
        sp=snap(st,generation=1+(i%4),opened_at_epoch_s=(900 if st==CircuitState.OPEN else None))
        s=CascadeSignal(
            request_id=f"r{i}",snapshot=sp,observed_epoch_s=1000+(i%50),
            consecutive_failures=i%5,failure_count_window=i%8,sample_count_window=10,
            error_rate_percent=(i*7)%101,fanout_estimate=i%6,dependency_ids=(f"d{i%7}",),
            critical_dependency_failure=(i%17==0),validated_failure_evidence=(i%2==0),
            upstream_breaker_open=(i%19==0),emergency_stop_active=False,
            cooldown_elapsed=(i%2==0),recovery_successes=i%4,recovery_probe_authorized=(i%5==0),
            expected_generation=sp.generation,human_approved=(i%7==0),approval_ref="H" if i%7==0 else None)
        out.append(b.evaluate(s).stable_payload())
    raw=json.dumps(out,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

if __name__=="__main__": unittest.main()
