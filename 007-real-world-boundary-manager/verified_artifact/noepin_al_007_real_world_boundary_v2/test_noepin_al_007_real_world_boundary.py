import hashlib, json, unittest
from noepin_al_007_real_world_boundary import *

def policy():
    return BoundaryPolicy(
        allowed_adapters=(AdapterKind.PC,AdapterKind.UNITY,AdapterKind.SMART_HOME,AdapterKind.ROBOT,AdapterKind.EXTERNAL_SERVICE),
        high_risk_capabilities=("physical_motion","unlock","power_cycle","delete","purchase","send_external"),
        require_human_for_physical=True,
        require_interlock_for_physical=True,
        max_risk_without_confirmation=35,
        policy_version="v2"
    )

def token(**kw):
    d=dict(token_id="tok",subject_id="ai",resource_id="pc:1",capabilities=("read","click","write"),expires_at_epoch_s=2000,issuer_ref="auth:1",revoked=False)
    d.update(kw)
    return CapabilityToken(**d)

def req(**kw):
    d=dict(request_id="r1",actor_id="ai",adapter_kind=AdapterKind.PC,resource_id="pc:1",capability="click",
           risk_score=10,observed_epoch_s=1000,token=token(),interlock_ready=False,emergency_stop_active=False,
           device_online=True,target_state_known=True,human_approved=False,approval_ref=None,
           external_side_effect=False,physical_effect=False,schema_version="1",context={})
    d.update(kw)
    return BoundaryRequest(**d)

class T(unittest.TestCase):
    def setUp(self): self.b=RealWorldBoundaryManager(policy())
    def check(self,r,d):
        o=self.b.evaluate(r); self.assertEqual(o.decision,d)
        self.assertFalse(o.authoritative); self.assertFalse(o.action_executed); self.assertFalse(o.action_succeeded); self.assertFalse(o.state_committed)
        return o

    def test_pc_low_allow(self): self.check(req(),BoundaryDecision.ALLOW_PREPARE)
    def test_missing_request(self): self.check(req(request_id=""),BoundaryDecision.HOLD)
    def test_missing_actor(self): self.check(req(actor_id=""),BoundaryDecision.HOLD)
    def test_missing_resource(self): self.check(req(resource_id=""),BoundaryDecision.HOLD)
    def test_missing_capability(self): self.check(req(capability=""),BoundaryDecision.HOLD)
    def test_missing_schema(self): self.check(req(schema_version=""),BoundaryDecision.HOLD)
    def test_emergency_deny(self): self.check(req(emergency_stop_active=True),BoundaryDecision.DENY)
    def test_bad_risk_low(self): self.check(req(risk_score=-1),BoundaryDecision.HOLD)
    def test_bad_risk_high(self): self.check(req(risk_score=101),BoundaryDecision.HOLD)
    def test_bool_risk(self): self.check(req(risk_score=True),BoundaryDecision.HOLD)
    def test_offline_hold(self): self.check(req(device_online=False),BoundaryDecision.HOLD)
    def test_unknown_state_hold(self): self.check(req(target_state_known=False),BoundaryDecision.HOLD)

    def test_token_required(self): self.check(req(token=None),BoundaryDecision.DENY)
    def test_token_malformed(self): self.check(req(token=token(token_id="")),BoundaryDecision.DENY)
    def test_token_revoked(self): self.check(req(token=token(revoked=True)),BoundaryDecision.DENY)
    def test_subject_mismatch(self): self.check(req(token=token(subject_id="other")),BoundaryDecision.DENY)
    def test_resource_mismatch(self): self.check(req(token=token(resource_id="pc:2")),BoundaryDecision.DENY)
    def test_capability_missing(self): self.check(req(capability="delete"),BoundaryDecision.DENY)
    def test_bad_observed_time(self): self.check(req(observed_epoch_s=-1),BoundaryDecision.HOLD)
    def test_bad_expiry(self): self.check(req(token=token(expires_at_epoch_s=True)),BoundaryDecision.HOLD)
    def test_token_expired_equal(self): self.check(req(observed_epoch_s=2000),BoundaryDecision.DENY)
    def test_token_expired_after(self): self.check(req(observed_epoch_s=2001),BoundaryDecision.DENY)
    def test_token_valid_before(self): self.check(req(observed_epoch_s=1999),BoundaryDecision.ALLOW_PREPARE)

    def test_robot_interlock_required(self):
        t=token(resource_id="robot:1",capabilities=("physical_motion",))
        self.check(req(adapter_kind=AdapterKind.ROBOT,resource_id="robot:1",capability="physical_motion",token=t,physical_effect=True),BoundaryDecision.HOLD)
    def test_robot_human_required(self):
        t=token(resource_id="robot:1",capabilities=("physical_motion",))
        self.check(req(adapter_kind=AdapterKind.ROBOT,resource_id="robot:1",capability="physical_motion",token=t,physical_effect=True,interlock_ready=True),BoundaryDecision.HUMAN_CONFIRM)
    def test_robot_approved_prepare_only(self):
        t=token(resource_id="robot:1",capabilities=("physical_motion",))
        o=self.check(req(adapter_kind=AdapterKind.ROBOT,resource_id="robot:1",capability="physical_motion",token=t,physical_effect=True,interlock_ready=True,human_approved=True,approval_ref="H"),BoundaryDecision.ALLOW_PREPARE)
        self.assertTrue(o.interlock_validated); self.assertFalse(o.action_executed)

    def test_smart_home_interlock_required_even_without_flag(self):
        t=token(resource_id="home:1",capabilities=("read",))
        self.check(req(adapter_kind=AdapterKind.SMART_HOME,resource_id="home:1",capability="read",token=t),BoundaryDecision.HOLD)
    def test_smart_home_human_required(self):
        t=token(resource_id="home:1",capabilities=("read",))
        self.check(req(adapter_kind=AdapterKind.SMART_HOME,resource_id="home:1",capability="read",token=t,interlock_ready=True),BoundaryDecision.HUMAN_CONFIRM)

    def test_high_risk_capability_confirm(self):
        t=token(capabilities=("delete",))
        self.check(req(capability="delete",token=t),BoundaryDecision.HUMAN_CONFIRM)
    def test_high_risk_approved(self):
        t=token(capabilities=("delete",))
        self.check(req(capability="delete",token=t,human_approved=True,approval_ref="H"),BoundaryDecision.ALLOW_PREPARE)

    def test_risk_boundary_35_allow(self): self.check(req(risk_score=35),BoundaryDecision.ALLOW_PREPARE)
    def test_risk_36_confirm(self): self.check(req(risk_score=36),BoundaryDecision.HUMAN_CONFIRM)
    def test_risk_36_approved(self): self.check(req(risk_score=36,human_approved=True,approval_ref="H"),BoundaryDecision.ALLOW_PREPARE)
    def test_approval_bool_without_ref(self): self.check(req(risk_score=36,human_approved=True),BoundaryDecision.HUMAN_CONFIRM)
    def test_approval_ref_without_bool(self): self.check(req(risk_score=36,approval_ref="H"),BoundaryDecision.HUMAN_CONFIRM)

    def test_external_side_effect_confirm(self): self.check(req(external_side_effect=True),BoundaryDecision.HUMAN_CONFIRM)
    def test_external_side_effect_approved(self): self.check(req(external_side_effect=True,human_approved=True,approval_ref="H"),BoundaryDecision.ALLOW_PREPARE)

    def test_cache_exact(self):
        r=req(); a=self.b.evaluate(r); c=self.b.evaluate(r); self.assertFalse(a.cache_reused); self.assertTrue(c.cache_reused)
    def test_cache_never_authority(self):
        r=req(); self.b.evaluate(r); self.assertFalse(self.b.evaluate(r).authoritative)
    def test_cache_never_success(self):
        r=req(); self.b.evaluate(r); self.assertFalse(self.b.evaluate(r).action_succeeded)
    def test_cache_diff_token(self):
        self.assertNotEqual(self.b.fingerprint(req(token=token(token_id="a"))),self.b.fingerprint(req(token=token(token_id="b"))))
    def test_cache_diff_approval(self):
        self.assertNotEqual(self.b.fingerprint(req()),self.b.fingerprint(req(human_approved=True,approval_ref="H")))
    def test_context_order(self):
        self.assertEqual(self.b.fingerprint(req(context={"b":2,"a":1})),self.b.fingerprint(req(context={"a":1,"b":2})))
    def test_clear_cache(self):
        self.b.evaluate(req()); self.assertGreater(self.b.cache_size(),0); self.b.clear_cache(); self.assertEqual(self.b.cache_size(),0)

    def test_emergency_overrides_cached_allow(self):
        r=req()
        self.assertEqual(self.b.evaluate(r).decision,BoundaryDecision.ALLOW_PREPARE)
        e=req(emergency_stop_active=True)
        o=self.b.evaluate(e)
        self.assertEqual(o.decision,BoundaryDecision.DENY); self.assertFalse(o.cache_reused); self.assertTrue(o.emergency_stop_observed)

    def test_emergency_with_approval_still_deny(self):
        self.check(req(emergency_stop_active=True,human_approved=True,approval_ref="H"),BoundaryDecision.DENY)

    def test_selected_never_commits(self):
        o=self.check(req(),BoundaryDecision.ALLOW_PREPARE); self.assertFalse(o.state_committed)
    def test_token_valid_not_success(self):
        o=self.check(req(),BoundaryDecision.ALLOW_PREPARE); self.assertTrue(o.token_validated); self.assertFalse(o.action_succeeded)
    def test_stable_no_time(self): self.assertNotIn("created_unix_ns",self.b.evaluate(req()).stable_payload())

    def test_many_low_pc_requests(self):
        for i in range(10):
            t=token(token_id=f"t{i}")
            self.check(req(request_id=f"r{i}",token=t,risk_score=i),BoundaryDecision.ALLOW_PREPARE)

def replay_fingerprint():
    b=RealWorldBoundaryManager(policy())
    out=[]
    kinds=[AdapterKind.PC,AdapterKind.UNITY,AdapterKind.EXTERNAL_SERVICE,AdapterKind.ROBOT]
    for i in range(1000):
        kind=kinds[i%len(kinds)]
        resource=f"res:{i%17}"
        physical=(kind==AdapterKind.ROBOT)
        cap="physical_motion" if physical else ("send_external" if kind==AdapterKind.EXTERNAL_SERVICE and i%3==0 else "read")
        t=CapabilityToken(token_id=f"t{i%23}",subject_id="ai",resource_id=resource,capabilities=(cap,),expires_at_epoch_s=5000,issuer_ref="auth")
        kwargs=dict(request_id=f"r{i}",actor_id="ai",adapter_kind=kind,resource_id=resource,capability=cap,risk_score=i%50,
                    observed_epoch_s=1000+(i%100),token=t,interlock_ready=physical,device_online=True,target_state_known=True,
                    physical_effect=physical,external_side_effect=(kind==AdapterKind.EXTERNAL_SERVICE))
        if i%4==0:
            kwargs["human_approved"]=True; kwargs["approval_ref"]="H"
        r=b.evaluate(BoundaryRequest(**kwargs))
        out.append(r.stable_payload())
    raw=json.dumps(out,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

if __name__=="__main__":
    unittest.main()
