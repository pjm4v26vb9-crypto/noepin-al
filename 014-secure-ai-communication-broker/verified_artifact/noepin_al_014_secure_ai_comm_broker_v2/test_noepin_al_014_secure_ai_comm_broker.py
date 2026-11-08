import hashlib, json, unittest
from dataclasses import replace
from noepin_al_014_secure_ai_comm_broker import *

KEY=b"0123456789abcdef0123456789abcdef"
H0="0"*64
H1="1"*64

def policy():
    return BrokerPolicy(
        require_tls=True,require_mtls=True,require_sender_certificate=True,
        max_clock_skew_seconds=300,max_message_lifetime_seconds=3600,
        max_risk_without_confirmation=35,
        high_risk_purposes=("execute","publish","purchase","external_send","privilege_change"),
        policy_version="v2"
    )

def route(**kw):
    d=dict(agent_id="agent-a",key_id="key-a",allowed_destinations=("agent-b","agent-c"),
           allowed_purposes=("coordinate","status","execute"),disabled=False,route_version=1)
    d.update(kw); return AgentRoute(**d)

def unsigned(**kw):
    d=dict(
        message_id="m1",sender_id="agent-a",recipient_id="agent-b",purpose="coordinate",
        payload_sha256=H0,issued_at_epoch_s=1000,expires_at_epoch_s=1600,nonce="n1",
        key_id="key-a",signature_hex="",tls_authenticated=True,mtls_authenticated=True,
        sender_certificate_ref="cert:a",shared_state_fingerprint=None,delta_fingerprint=None,
        claims_authority=False,requests_external_action=False,risk_score=5,
        human_approved=False,approval_ref=None,schema_version="1",metadata={}
    )
    d.update(kw); return SecureEnvelope(**d)

def signed(**kw):
    e=unsigned(**kw)
    sig=SecureAICommunicationBroker.sign_envelope(e,KEY)
    return replace(e,signature_hex=sig)

def request(**kw):
    d=dict(request_id="r1",envelope=signed(),observed_epoch_s=1100,nonce_already_seen=False,
           expected_sender_route_version=1,schema_version="1",context={})
    d.update(kw); return CommunicationRequest(**d)

def broker(**kw):
    routes={"agent-a": route()}
    keys={"key-a":KEY}
    return SecureAICommunicationBroker(policy(),routes,keys,**kw)

class T(unittest.TestCase):
    def setUp(self): self.b=broker()

    def check(self,r,d):
        o=self.b.evaluate(r); self.assertEqual(o.decision,d)
        self.assertFalse(o.authoritative); self.assertFalse(o.message_sent)
        self.assertFalse(o.message_delivered); self.assertFalse(o.recipient_heard)
        self.assertFalse(o.action_executed); self.assertFalse(o.action_succeeded)
        return o

    def test_valid_allow_prepare(self): self.check(request(),BrokerDecision.ALLOW_PREPARE)
    def test_missing_request(self): self.check(request(request_id=""),BrokerDecision.HOLD)
    def test_missing_request_schema(self): self.check(request(schema_version=""),BrokerDecision.HOLD)
    def test_missing_message_id(self): self.check(request(envelope=signed(message_id="")),BrokerDecision.HOLD)
    def test_sender_recipient_collision(self): self.check(request(envelope=signed(recipient_id="agent-a")),BrokerDecision.HOLD)
    def test_bad_payload_hash(self): self.check(request(envelope=signed(payload_sha256="bad")),BrokerDecision.HOLD)
    def test_bad_shared_state_hash(self): self.check(request(envelope=signed(shared_state_fingerprint="bad")),BrokerDecision.HOLD)
    def test_bad_delta_hash(self): self.check(request(envelope=signed(delta_fingerprint="bad")),BrokerDecision.HOLD)
    def test_bad_observed_time(self): self.check(request(observed_epoch_s=-1),BrokerDecision.HOLD)
    def test_bad_envelope_time_bool(self): self.check(request(envelope=signed(issued_at_epoch_s=True)),BrokerDecision.HOLD)
    def test_invalid_lifetime(self): self.check(request(envelope=signed(expires_at_epoch_s=1000)),BrokerDecision.DENY)
    def test_lifetime_too_long(self): self.check(request(envelope=signed(expires_at_epoch_s=5000)),BrokerDecision.DENY)
    def test_expired_equal(self): self.check(request(observed_epoch_s=1600),BrokerDecision.DENY)
    def test_future_skew_hold(self): self.check(request(envelope=signed(issued_at_epoch_s=1500,expires_at_epoch_s=1800),observed_epoch_s=1100),BrokerDecision.HOLD)
    def test_bad_risk(self): self.check(request(envelope=signed(risk_score=101)),BrokerDecision.HOLD)
    def test_bool_risk(self): self.check(request(envelope=signed(risk_score=True)),BrokerDecision.HOLD)
    def test_replay_nonce_seen(self): self.check(request(nonce_already_seen=True),BrokerDecision.DENY)

    def test_unknown_sender(self):
        e=signed(sender_id="agent-z")
        # re-signing with KEY is fine but route is absent
        self.check(request(envelope=e),BrokerDecision.DENY)
    def test_sender_disabled(self):
        b=SecureAICommunicationBroker(policy(),{"agent-a":route(disabled=True)},{"key-a":KEY})
        self.b=b; self.check(request(),BrokerDecision.DENY)
    def test_route_version_mismatch(self): self.check(request(expected_sender_route_version=2),BrokerDecision.HOLD)
    def test_tls_required(self): self.check(request(envelope=signed(tls_authenticated=False)),BrokerDecision.DENY)
    def test_mtls_required(self): self.check(request(envelope=signed(mtls_authenticated=False)),BrokerDecision.DENY)
    def test_cert_ref_required(self): self.check(request(envelope=signed(sender_certificate_ref=None)),BrokerDecision.HOLD)

    def test_key_id_route_mismatch(self):
        e=unsigned(key_id="key-other")
        e=replace(e,signature_hex=SecureAICommunicationBroker.sign_envelope(e,KEY))
        self.check(request(envelope=e),BrokerDecision.DENY)
    def test_key_unavailable(self):
        b=SecureAICommunicationBroker(policy(),{"agent-a":route()},{})
        self.b=b; self.check(request(),BrokerDecision.HOLD)
    def test_signature_format(self):
        e=replace(unsigned(),signature_hex="bad")
        self.check(request(envelope=e),BrokerDecision.DENY)
    def test_signature_failure(self):
        e=replace(signed(),signature_hex=H1)
        self.check(request(envelope=e),BrokerDecision.DENY)
    def test_tampered_recipient_after_sign(self):
        e=signed()
        e=replace(e,recipient_id="agent-c")
        self.check(request(envelope=e),BrokerDecision.DENY)
    def test_tampered_purpose_after_sign(self):
        e=signed()
        e=replace(e,purpose="status")
        self.check(request(envelope=e),BrokerDecision.DENY)
    def test_tampered_payload_after_sign(self):
        e=signed()
        e=replace(e,payload_sha256=H1)
        self.check(request(envelope=e),BrokerDecision.DENY)

    def test_recipient_not_authorized(self):
        self.check(request(envelope=signed(recipient_id="agent-x")),BrokerDecision.DENY)
    def test_purpose_not_authorized(self):
        self.check(request(envelope=signed(purpose="admin")),BrokerDecision.DENY)
    def test_claims_authority_hold(self):
        self.check(request(envelope=signed(claims_authority=True)),BrokerDecision.HOLD)

    def test_high_risk_purpose_confirm(self):
        self.check(request(envelope=signed(purpose="execute")),BrokerDecision.HUMAN_CONFIRM)
    def test_high_risk_purpose_approved(self):
        self.check(request(envelope=signed(purpose="execute",human_approved=True,approval_ref="H")),BrokerDecision.ALLOW_PREPARE)
    def test_external_action_confirm(self):
        self.check(request(envelope=signed(requests_external_action=True)),BrokerDecision.HUMAN_CONFIRM)
    def test_external_action_approved(self):
        self.check(request(envelope=signed(requests_external_action=True,human_approved=True,approval_ref="H")),BrokerDecision.ALLOW_PREPARE)
    def test_risk_35_allow(self): self.check(request(envelope=signed(risk_score=35)),BrokerDecision.ALLOW_PREPARE)
    def test_risk_36_confirm(self): self.check(request(envelope=signed(risk_score=36)),BrokerDecision.HUMAN_CONFIRM)
    def test_approval_bool_without_ref(self): self.check(request(envelope=signed(risk_score=36,human_approved=True)),BrokerDecision.HUMAN_CONFIRM)
    def test_approval_ref_without_bool(self): self.check(request(envelope=signed(risk_score=36,approval_ref="H")),BrokerDecision.HUMAN_CONFIRM)

    def test_shared_state_valid(self):
        o=self.check(request(envelope=signed(shared_state_fingerprint=H0,delta_fingerprint=H1)),BrokerDecision.ALLOW_PREPARE)
        self.assertFalse(o.authoritative)
    def test_dcsr_state_not_instruction_authority(self):
        o=self.check(request(envelope=signed(shared_state_fingerprint=H0,delta_fingerprint=H1)),BrokerDecision.ALLOW_PREPARE)
        self.assertFalse(o.action_succeeded)

    def test_cache_exact(self):
        r=request(); a=self.b.evaluate(r); c=self.b.evaluate(r)
        self.assertFalse(a.cache_reused); self.assertTrue(c.cache_reused)
    def test_cache_never_authority(self):
        r=request(); self.b.evaluate(r); self.assertFalse(self.b.evaluate(r).authoritative)
    def test_cache_never_delivery(self):
        r=request(); self.b.evaluate(r); self.assertFalse(self.b.evaluate(r).message_delivered)
    def test_cache_diff_nonce_seen(self):
        self.assertNotEqual(self.b.request_fingerprint(request()),self.b.request_fingerprint(request(nonce_already_seen=True)))
    def test_cache_diff_route_version(self):
        self.assertNotEqual(self.b.request_fingerprint(request(expected_sender_route_version=1)),self.b.request_fingerprint(request(expected_sender_route_version=2)))
    def test_context_order(self):
        self.assertEqual(self.b.request_fingerprint(request(context={"b":2,"a":1})),self.b.request_fingerprint(request(context={"a":1,"b":2})))
    def test_clear_cache(self):
        self.b.evaluate(request()); self.assertGreater(self.b.cache_size(),0); self.b.clear_cache(); self.assertEqual(self.b.cache_size(),0)
    def test_stable_no_time(self): self.assertNotIn("created_unix_ns",self.b.evaluate(request()).stable_payload())

    def test_authenticated_channel_not_authority(self):
        o=self.check(request(envelope=signed(claims_authority=True)),BrokerDecision.HOLD)
        self.assertTrue(o.sender_authenticated); self.assertFalse(o.authoritative)
    def test_signature_verified_not_delivery(self):
        o=self.check(request(),BrokerDecision.ALLOW_PREPARE); self.assertTrue(o.signature_verified); self.assertFalse(o.message_delivered)
    def test_allow_prepare_not_heard(self):
        o=self.check(request(),BrokerDecision.ALLOW_PREPARE); self.assertFalse(o.recipient_heard)
    def test_allow_prepare_not_action_success(self):
        o=self.check(request(),BrokerDecision.ALLOW_PREPARE); self.assertFalse(o.action_succeeded)

    def test_many_valid(self):
        for i in range(10):
            e=signed(message_id=f"m{i}",nonce=f"n{i}",payload_sha256=f"{i:x}".rjust(64,"0"))
            self.check(request(request_id=f"r{i}",envelope=e),BrokerDecision.ALLOW_PREPARE)

def replay_fingerprint():
    b=broker()
    out=[]
    for i in range(1000):
        purpose="execute" if i%17==0 else ("status" if i%3==0 else "coordinate")
        e=signed(
            message_id=f"m{i}",nonce=f"n{i%97}",purpose=purpose,
            payload_sha256=f"{i:x}".rjust(64,"0"),
            issued_at_epoch_s=1000+(i%100),expires_at_epoch_s=1500+(i%100),
            shared_state_fingerprint=H0 if i%4==0 else None,
            delta_fingerprint=f"{i+10000:x}".rjust(64,"0") if i%4==0 else None,
            risk_score=i%40,
            human_approved=(i%5==0),approval_ref="H" if i%5==0 else None
        )
        r=CommunicationRequest(
            request_id=f"r{i}",envelope=e,observed_epoch_s=1100+(i%50),
            nonce_already_seen=(i%113==0),expected_sender_route_version=1,
            context={"batch":i%7}
        )
        out.append(b.evaluate(r).stable_payload())
    raw=json.dumps(out,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

if __name__=="__main__":
    unittest.main()
