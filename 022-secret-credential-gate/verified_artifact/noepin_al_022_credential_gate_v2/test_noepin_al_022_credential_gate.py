import unittest, hashlib, json
from noepin_al_022_credential_gate import *

def req(**kw):
    d=dict(
        request_id="r1", agent_id="agent", role="worker", purpose="weather_lookup",
        credential_ref="vault://service/weather", credential_kind=CredentialKind.API_KEY,
        credential_version=1, credential_expiry_epoch_s=2000, credential_revoked=False,
        vault_attested=True, broker_attested=True, operation=CredentialOperation.PROXY_CALL,
        target_ref="api://weather", permit_id="p1", permit_version=1, permit_expiry_epoch_s=2000,
        permit_revoked=False, role_authorized=True, purpose_authorized=True,
        operation_authorized=True, target_authorized=True, raw_secret_material_present=False,
        high_privilege=False, external_side_effect=False, human_approved=False, approval_ref=None,
        observed_epoch_s=1000, authority_version=1, schema_version="1", context={}
    )
    d.update(kw)
    return CredentialRequest(**d)

class GateTests(unittest.TestCase):
    def setUp(self): self.g=SecretCredentialGate(policy_version="v2")
    def check(self,r,d):
        o=self.g.evaluate(r); self.assertEqual(o.decision,d)
        self.assertFalse(o.secret_exposed); self.assertFalse(o.credential_material_returned)
        self.assertFalse(o.short_lived_token_issued); self.assertFalse(o.signature_created)
        self.assertFalse(o.action_executed); self.assertFalse(o.action_succeeded)
        self.assertFalse(o.state_committed); self.assertFalse(o.authoritative)
        return o

    def test_allow(self): self.assertTrue(self.check(req(),CredentialDecision.ALLOW_PREPARE).proxy_plan_created)
    def test_missing_request(self): self.check(req(request_id=""),CredentialDecision.HOLD)
    def test_missing_agent(self): self.check(req(agent_id=""),CredentialDecision.HOLD)
    def test_missing_role(self): self.check(req(role=""),CredentialDecision.HOLD)
    def test_missing_purpose(self): self.check(req(purpose=""),CredentialDecision.HOLD)
    def test_missing_credential_ref(self): self.check(req(credential_ref=""),CredentialDecision.HOLD)
    def test_missing_target_ref(self): self.check(req(target_ref=""),CredentialDecision.HOLD)
    def test_missing_permit(self): self.check(req(permit_id=""),CredentialDecision.HOLD)
    def test_missing_schema(self): self.check(req(schema_version=""),CredentialDecision.HOLD)

    def test_raw_secret_denied(self): self.check(req(raw_secret_material_present=True),CredentialDecision.DENY)
    def test_credential_revoked(self): self.check(req(credential_revoked=True),CredentialDecision.DENY)
    def test_permit_revoked(self): self.check(req(permit_revoked=True),CredentialDecision.DENY)
    def test_credential_expired(self): self.check(req(credential_expiry_epoch_s=1000),CredentialDecision.DENY)
    def test_permit_expired(self): self.check(req(permit_expiry_epoch_s=1000),CredentialDecision.DENY)
    def test_credential_expiry_none(self): self.check(req(credential_expiry_epoch_s=None),CredentialDecision.ALLOW_PREPARE)
    def test_permit_expiry_none(self): self.check(req(permit_expiry_epoch_s=None),CredentialDecision.ALLOW_PREPARE)
    def test_bad_credential_expiry(self): self.check(req(credential_expiry_epoch_s=True),CredentialDecision.HOLD)
    def test_bad_permit_expiry(self): self.check(req(permit_expiry_epoch_s=True),CredentialDecision.HOLD)

    def test_vault_attestation(self): self.check(req(vault_attested=False),CredentialDecision.HOLD)
    def test_broker_attestation(self): self.check(req(broker_attested=False),CredentialDecision.HOLD)
    def test_role_authorized(self): self.check(req(role_authorized=False),CredentialDecision.DENY)
    def test_purpose_authorized(self): self.check(req(purpose_authorized=False),CredentialDecision.DENY)
    def test_operation_authorized(self): self.check(req(operation_authorized=False),CredentialDecision.DENY)
    def test_target_authorized(self): self.check(req(target_authorized=False),CredentialDecision.DENY)

    def test_high_privilege_confirm(self): self.check(req(high_privilege=True),CredentialDecision.HUMAN_CONFIRM)
    def test_high_privilege_approved(self): self.check(req(high_privilege=True,human_approved=True,approval_ref="A"),CredentialDecision.ALLOW_PREPARE)
    def test_side_effect_confirm(self): self.check(req(external_side_effect=True),CredentialDecision.HUMAN_CONFIRM)
    def test_side_effect_approved(self): self.check(req(external_side_effect=True,human_approved=True,approval_ref="A"),CredentialDecision.ALLOW_PREPARE)
    def test_approval_bool_without_ref(self): self.check(req(high_privilege=True,human_approved=True),CredentialDecision.HUMAN_CONFIRM)
    def test_approval_ref_without_bool(self): self.check(req(high_privilege=True,approval_ref="A"),CredentialDecision.HUMAN_CONFIRM)

    def test_bad_credential_version_zero(self): self.check(req(credential_version=0),CredentialDecision.HOLD)
    def test_bad_permit_version_zero(self): self.check(req(permit_version=0),CredentialDecision.HOLD)
    def test_bad_authority_version_zero(self): self.check(req(authority_version=0),CredentialDecision.HOLD)
    def test_bad_observed_bool(self): self.check(req(observed_epoch_s=True),CredentialDecision.HOLD)
    def test_bad_credential_version_bool(self): self.check(req(credential_version=True),CredentialDecision.HOLD)
    def test_bad_permit_version_bool(self): self.check(req(permit_version=True),CredentialDecision.HOLD)

    def test_cache_reused(self):
        a=self.g.evaluate(req()); b=self.g.evaluate(req())
        self.assertFalse(a.cache_reused); self.assertTrue(b.cache_reused)
    def test_cache_no_secret(self):
        self.g.evaluate(req()); self.assertFalse(self.g.evaluate(req()).secret_exposed)
    def test_cache_no_action(self):
        self.g.evaluate(req()); self.assertFalse(self.g.evaluate(req()).action_executed)
    def test_cache_no_token(self):
        r=req(operation=CredentialOperation.REQUEST_SHORT_LIVED_TOKEN); self.g.evaluate(r)
        self.assertFalse(self.g.evaluate(r).short_lived_token_issued)
    def test_cache_no_signature(self):
        r=req(operation=CredentialOperation.SIGN); self.g.evaluate(r)
        self.assertFalse(self.g.evaluate(r).signature_created)
    def test_fingerprint_purpose(self):
        self.assertNotEqual(self.g.fingerprint(req()),self.g.fingerprint(req(purpose="other")))
    def test_fingerprint_permit_version(self):
        self.assertNotEqual(self.g.fingerprint(req()),self.g.fingerprint(req(permit_version=2)))
    def test_fingerprint_revocation(self):
        self.assertNotEqual(self.g.fingerprint(req()),self.g.fingerprint(req(permit_revoked=True)))
    def test_fingerprint_context_order(self):
        self.assertEqual(self.g.fingerprint(req(context={"b":2,"a":1})),self.g.fingerprint(req(context={"a":1,"b":2})))
    def test_clear_cache(self):
        self.g.evaluate(req()); self.g.clear_cache(); self.assertEqual(self.g.cache_size(),0)
    def test_stable_excludes_time(self):
        self.assertNotIn("created_unix_ns",self.g.evaluate(req()).stable_payload())

    def test_api_key_kind(self): self.check(req(credential_kind=CredentialKind.API_KEY),CredentialDecision.ALLOW_PREPARE)
    def test_oauth_kind(self): self.check(req(credential_kind=CredentialKind.OAUTH_TOKEN),CredentialDecision.ALLOW_PREPARE)
    def test_private_key_kind(self): self.check(req(credential_kind=CredentialKind.PRIVATE_KEY),CredentialDecision.ALLOW_PREPARE)
    def test_certificate_kind(self): self.check(req(credential_kind=CredentialKind.CERTIFICATE),CredentialDecision.ALLOW_PREPARE)
    def test_session_kind(self): self.check(req(credential_kind=CredentialKind.SESSION_TOKEN),CredentialDecision.ALLOW_PREPARE)
    def test_service_kind(self): self.check(req(credential_kind=CredentialKind.SERVICE_CREDENTIAL),CredentialDecision.ALLOW_PREPARE)

    def test_proxy_operation(self): self.check(req(operation=CredentialOperation.PROXY_CALL),CredentialDecision.ALLOW_PREPARE)
    def test_sign_operation(self):
        o=self.check(req(operation=CredentialOperation.SIGN),CredentialDecision.ALLOW_PREPARE); self.assertFalse(o.signature_created)
    def test_short_token_operation(self):
        o=self.check(req(operation=CredentialOperation.REQUEST_SHORT_LIVED_TOKEN),CredentialDecision.ALLOW_PREPARE); self.assertFalse(o.short_lived_token_issued)
    def test_metadata_operation(self): self.check(req(operation=CredentialOperation.READ_METADATA),CredentialDecision.ALLOW_PREPARE)

def replay_fingerprint():
    g=SecretCredentialGate(policy_version="v2")
    out=[]
    kinds=list(CredentialKind); ops=list(CredentialOperation)
    for i in range(1000):
        r=req(
            request_id=f"r{i}",
            credential_kind=kinds[i%len(kinds)],
            operation=ops[i%len(ops)],
            credential_version=1+(i%3),
            permit_version=1+(i%4),
            high_privilege=(i%11==0),
            external_side_effect=(i%13==0),
            human_approved=(i%17==0),
            approval_ref="A" if i%17==0 else None,
            context={"i":i%5,"z":i%7}
        )
        out.append(g.evaluate(r).stable_payload())
    raw=json.dumps(out,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

if __name__=="__main__":
    unittest.main()
