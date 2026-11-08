import hashlib, json, unittest
from noepin_al_004_pre_execution_simulator import *

def policy():
    return SimulationPolicy(
        max_impact_without_confirmation=40,
        max_impact_allowed=85,
        require_snapshot_for_destructive=True,
        require_rollback_for_destructive=True,
        require_human_for_external_send=True,
        require_human_for_execute=True,
        policy_version="v2"
    )

def plan(**kw):
    d=dict(action=ActionKind.READ,target="project/file",actor_id="ai-1",estimated_impact=5,reversible=True)
    d.update(kw)
    return ActionPlan(**d)

class T(unittest.TestCase):
    def setUp(self): self.s=PreExecutionSimulator(policy())
    def check(self,p,d):
        r=self.s.simulate(p); self.assertEqual(r.decision,d); self.assertTrue(r.simulation_only)
        self.assertFalse(r.authoritative); self.assertFalse(r.action_executed); self.assertFalse(r.action_succeeded); self.assertFalse(r.state_committed); return r

    def test_read_low(self): self.check(plan(),SimulationDecision.SAFE_TO_PREPARE)
    def test_missing_actor(self): self.check(plan(actor_id=""),SimulationDecision.HOLD)
    def test_missing_target(self): self.check(plan(target=""),SimulationDecision.HOLD)
    def test_missing_schema(self): self.check(plan(schema_version=""),SimulationDecision.HOLD)
    def test_bad_impact_low(self): self.check(plan(estimated_impact=-1),SimulationDecision.HOLD)
    def test_bad_impact_high(self): self.check(plan(estimated_impact=101),SimulationDecision.HOLD)
    def test_bool_impact_invalid(self): self.check(plan(estimated_impact=True),SimulationDecision.HOLD)
    def test_dependency_hold(self): self.check(plan(dependencies_ready=False),SimulationDecision.HOLD)
    def test_over_max_reject(self): self.check(plan(estimated_impact=86),SimulationDecision.REJECT)
    def test_high_non_destructive_confirm(self): self.check(plan(estimated_impact=50),SimulationDecision.HUMAN_CONFIRM)
    def test_high_approved(self): self.check(plan(estimated_impact=50,approval_present=True,approval_ref="A"),SimulationDecision.SAFE_TO_PREPARE)
    def test_approval_bool_without_ref_not_enough(self): self.check(plan(estimated_impact=50,approval_present=True),SimulationDecision.HUMAN_CONFIRM)
    def test_approval_ref_without_bool_not_enough(self): self.check(plan(estimated_impact=50,approval_ref="A"),SimulationDecision.HUMAN_CONFIRM)

    def test_delete_snapshot_first(self): self.check(plan(action=ActionKind.DELETE,deletes_data=True),SimulationDecision.HOLD)
    def test_delete_rollback_after_snapshot(self): self.check(plan(action=ActionKind.DELETE,deletes_data=True,snapshot_ref="S"),SimulationDecision.HOLD)
    def test_delete_confirm(self): self.check(plan(action=ActionKind.DELETE,deletes_data=True,snapshot_ref="S",rollback_ref="R"),SimulationDecision.HUMAN_CONFIRM)
    def test_delete_approved(self): self.check(plan(action=ActionKind.DELETE,deletes_data=True,snapshot_ref="S",rollback_ref="R",approval_present=True,approval_ref="A"),SimulationDecision.SAFE_TO_PREPARE)

    def test_move_needs_snapshot(self): self.check(plan(action=ActionKind.MOVE),SimulationDecision.HOLD)
    def test_move_needs_rollback(self): self.check(plan(action=ActionKind.MOVE,snapshot_ref="S"),SimulationDecision.HOLD)
    def test_move_low_with_refs(self): self.check(plan(action=ActionKind.MOVE,snapshot_ref="S",rollback_ref="R"),SimulationDecision.SAFE_TO_PREPARE)

    def test_config_needs_snapshot(self): self.check(plan(action=ActionKind.CONFIG_CHANGE),SimulationDecision.HOLD)
    def test_config_with_refs_low(self): self.check(plan(action=ActionKind.CONFIG_CHANGE,snapshot_ref="S",rollback_ref="R"),SimulationDecision.SAFE_TO_PREPARE)

    def test_world_write_destructive(self): self.check(plan(action=ActionKind.WRITE,writes_world_state=True),SimulationDecision.HOLD)
    def test_world_write_with_refs(self): self.check(plan(action=ActionKind.WRITE,writes_world_state=True,snapshot_ref="S",rollback_ref="R"),SimulationDecision.SAFE_TO_PREPARE)

    def test_external_send_confirm(self): self.check(plan(action=ActionKind.EXTERNAL_SEND,external_side_effect=True),SimulationDecision.HUMAN_CONFIRM)
    def test_external_send_approved(self): self.check(plan(action=ActionKind.EXTERNAL_SEND,external_side_effect=True,approval_present=True,approval_ref="A"),SimulationDecision.SAFE_TO_PREPARE)
    def test_external_side_effect_other_action_confirm(self): self.check(plan(action=ActionKind.WRITE,external_side_effect=True),SimulationDecision.HUMAN_CONFIRM)

    def test_execute_snapshot(self): self.check(plan(action=ActionKind.EXECUTE),SimulationDecision.HOLD)
    def test_execute_rollback(self): self.check(plan(action=ActionKind.EXECUTE,snapshot_ref="S"),SimulationDecision.HOLD)
    def test_execute_confirm(self): self.check(plan(action=ActionKind.EXECUTE,snapshot_ref="S",rollback_ref="R"),SimulationDecision.HUMAN_CONFIRM)
    def test_execute_approved(self): self.check(plan(action=ActionKind.EXECUTE,snapshot_ref="S",rollback_ref="R",approval_present=True,approval_ref="A"),SimulationDecision.SAFE_TO_PREPARE)

    def test_irreversible_confirm(self): self.check(plan(reversible=False),SimulationDecision.HUMAN_CONFIRM)
    def test_irreversible_approved(self): self.check(plan(reversible=False,approval_present=True,approval_ref="A"),SimulationDecision.SAFE_TO_PREPARE)
    def test_production_confirm(self): self.check(plan(affects_production=True),SimulationDecision.HUMAN_CONFIRM)
    def test_production_approved(self): self.check(plan(affects_production=True,approval_present=True,approval_ref="A"),SimulationDecision.SAFE_TO_PREPARE)

    def test_reversibility_full(self): self.assertEqual(self.s.simulate(plan()).reversibility_score,100)
    def test_reversibility_irreversible(self): self.assertLess(self.s.simulate(plan(reversible=False)).reversibility_score,100)
    def test_reversibility_delete(self): self.assertLess(self.s.simulate(plan(action=ActionKind.DELETE,deletes_data=True)).reversibility_score,100)
    def test_refs_raise_reversibility(self):
        a=self.s.simulate(plan(action=ActionKind.DELETE,deletes_data=True)).reversibility_score
        b=self.s.simulate(plan(action=ActionKind.DELETE,deletes_data=True,snapshot_ref="S",rollback_ref="R")).reversibility_score
        self.assertGreater(b,a)
    def test_score_clamped(self): 
        r=self.s.simulate(plan(reversible=False,deletes_data=True,affects_production=True,external_side_effect=True))
        self.assertGreaterEqual(r.reversibility_score,0); self.assertLessEqual(r.reversibility_score,100)

    def test_cache_exact(self):
        p=plan(); a=self.s.simulate(p); b=self.s.simulate(p); self.assertFalse(a.cache_reused); self.assertTrue(b.cache_reused)
    def test_cache_never_authoritative(self):
        p=plan(); self.s.simulate(p); self.assertFalse(self.s.simulate(p).authoritative)
    def test_cache_never_success(self):
        p=plan(); self.s.simulate(p); self.assertFalse(self.s.simulate(p).action_succeeded)
    def test_cache_diff_impact(self):
        self.assertNotEqual(self.s.fingerprint(plan(estimated_impact=1)),self.s.fingerprint(plan(estimated_impact=2)))
    def test_cache_diff_approval(self):
        self.assertNotEqual(self.s.fingerprint(plan()),self.s.fingerprint(plan(approval_present=True,approval_ref="A")))
    def test_cache_context_order(self):
        self.assertEqual(self.s.fingerprint(plan(context={"b":2,"a":1})),self.s.fingerprint(plan(context={"a":1,"b":2})))
    def test_clear_cache(self):
        self.s.simulate(plan()); self.assertGreater(self.s.cache_size(),0); self.s.clear_cache(); self.assertEqual(self.s.cache_size(),0)
    def test_stable_payload_no_time(self): self.assertNotIn("created_unix_ns",self.s.simulate(plan()).stable_payload())

    def test_boundary_impact_40_allow(self): self.check(plan(estimated_impact=40),SimulationDecision.SAFE_TO_PREPARE)
    def test_boundary_impact_41_confirm(self): self.check(plan(estimated_impact=41),SimulationDecision.HUMAN_CONFIRM)
    def test_boundary_impact_85_confirm(self): self.check(plan(estimated_impact=85),SimulationDecision.HUMAN_CONFIRM)
    def test_boundary_impact_86_reject(self): self.check(plan(estimated_impact=86),SimulationDecision.REJECT)

    def test_safe_never_committed(self):
        r=self.check(plan(),SimulationDecision.SAFE_TO_PREPARE); self.assertFalse(r.state_committed)
    def test_approved_never_executed(self):
        r=self.check(plan(estimated_impact=60,approval_present=True,approval_ref="A"),SimulationDecision.SAFE_TO_PREPARE); self.assertFalse(r.action_executed)
    def test_snapshot_ref_not_authority(self):
        r=self.s.simulate(plan(action=ActionKind.MOVE,snapshot_ref="S",rollback_ref="R")); self.assertFalse(r.authoritative)
    def test_rollback_ref_not_success(self):
        r=self.s.simulate(plan(action=ActionKind.MOVE,snapshot_ref="S",rollback_ref="R")); self.assertFalse(r.action_succeeded)

    def test_many_low_reads(self):
        for i in range(10): self.check(plan(target=f"p/{i}",estimated_impact=i),SimulationDecision.SAFE_TO_PREPARE)

def replay_fingerprint():
    s=PreExecutionSimulator(policy())
    out=[]
    kinds=list(ActionKind)
    for i in range(1000):
        k=kinds[i%len(kinds)]
        kwargs=dict(action=k,target=f"target/{i%17}",actor_id="ai",estimated_impact=i%86,reversible=(i%4!=0))
        if k in {ActionKind.DELETE,ActionKind.MOVE,ActionKind.CONFIG_CHANGE,ActionKind.EXECUTE}:
            kwargs["snapshot_ref"]="S"; kwargs["rollback_ref"]="R"
        if k==ActionKind.EXTERNAL_SEND:
            kwargs["external_side_effect"]=True
        if i%3==0:
            kwargs["approval_present"]=True; kwargs["approval_ref"]="A"
        r=s.simulate(ActionPlan(**kwargs))
        out.append(r.stable_payload())
    raw=json.dumps(out,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

if __name__=="__main__":
    unittest.main()
