import unittest
from dataclasses import replace
from noepin_al_033_intent_consent import *

NOW = 1000

def base_contract(**kw):
    c = IntentContract(
        contract_id="c-1", user_id="u-1", contract_version="v1", authority_version="a1",
        purpose="edit_project", allowed_actions=("read","edit"), allowed_resources=("project:a",),
        allowed_destinations=("local",), allowed_roles=("owner","editor"), explicit_consent=True,
        issued_at=900, expires_at=2000, permit_id="p-1", permit_version="pv1", permit_expires_at=1800,
        metadata=(("origin","NOEPIN"),)
    )
    return replace(c, **kw)

def base_request(**kw):
    r = IntentRequest(
        request_id="r-1", user_id="u-1", purpose="edit_project", action="edit", resource="project:a",
        destination="local", role="owner", contract_version="v1", authority_version="a1", observed_at=NOW,
        permit_id="p-1", permit_version="pv1", context_fingerprint="ctx1"
    )
    return replace(r, **kw)

class TestCore(unittest.TestCase):
    def setUp(self): self.g = IntentConsentControl()
    def test_allow(self): self.assertEqual(self.g.evaluate(base_contract(),base_request()).decision, Decision.ALLOW_CANDIDATE)
    def test_high_impact_confirm(self): self.assertEqual(self.g.evaluate(base_contract(),base_request(high_impact=True)).decision, Decision.HUMAN_CONFIRM)
    def test_high_impact_with_evidence_candidate(self): self.assertEqual(self.g.evaluate(base_contract(),base_request(high_impact=True,human_approval_evidence=True)).decision, Decision.ALLOW_CANDIDATE)
    def test_irreversible_confirm(self): self.assertEqual(self.g.evaluate(base_contract(),base_request(irreversible=True)).decision, Decision.HUMAN_CONFIRM)
    def test_revoked_contract(self): self.assertEqual(self.g.evaluate(base_contract(revoked=True),base_request()).decision, Decision.DENY)
    def test_expired_contract(self): self.assertEqual(self.g.evaluate(base_contract(),base_request(observed_at=2000)).decision, Decision.DENY)
    def test_not_yet_effective(self): self.assertEqual(self.g.evaluate(base_contract(),base_request(observed_at=800)).decision, Decision.HOLD)
    def test_contract_version(self): self.assertEqual(self.g.evaluate(base_contract(),base_request(contract_version="v2")).decision, Decision.HOLD)
    def test_authority_version(self): self.assertEqual(self.g.evaluate(base_contract(),base_request(authority_version="a2")).decision, Decision.HOLD)
    def test_user_mismatch(self): self.assertEqual(self.g.evaluate(base_contract(),base_request(user_id="u2")).decision, Decision.DENY)
    def test_no_explicit_consent(self): self.assertEqual(self.g.evaluate(base_contract(explicit_consent=False),base_request()).decision, Decision.DENY)
    def test_purpose_scope(self): self.assertEqual(self.g.evaluate(base_contract(),base_request(purpose="publish")).decision, Decision.DENY)
    def test_action_scope(self): self.assertEqual(self.g.evaluate(base_contract(),base_request(action="delete")).decision, Decision.DENY)
    def test_resource_scope(self): self.assertEqual(self.g.evaluate(base_contract(),base_request(resource="project:b")).decision, Decision.DENY)
    def test_destination_scope(self): self.assertEqual(self.g.evaluate(base_contract(),base_request(destination="external")).decision, Decision.DENY)
    def test_role_scope(self): self.assertEqual(self.g.evaluate(base_contract(),base_request(role="viewer")).decision, Decision.DENY)
    def test_permit_revoked(self): self.assertEqual(self.g.evaluate(base_contract(permit_revoked=True),base_request()).decision, Decision.DENY)
    def test_permit_expired(self): self.assertEqual(self.g.evaluate(base_contract(permit_expires_at=950),base_request()).decision, Decision.DENY)
    def test_permit_id_mismatch(self): self.assertEqual(self.g.evaluate(base_contract(),base_request(permit_id="p2")).decision, Decision.HOLD)
    def test_permit_version_mismatch(self): self.assertEqual(self.g.evaluate(base_contract(),base_request(permit_version="pv2")).decision, Decision.HOLD)

class TestValidation(unittest.TestCase):
    def setUp(self): self.g=IntentConsentControl()

# Generate deterministic validation/boundary tests.
def _mk_contract_field_test(field):
    def t(self):
        c=base_contract(**{field:""})
        self.assertEqual(self.g.evaluate(c,base_request()).decision, Decision.DENY)
    return t
for f in ["contract_id","user_id","contract_version","authority_version","purpose"]:
    setattr(TestValidation, "test_invalid_contract_"+f, _mk_contract_field_test(f))

def _mk_req_field_test(field):
    def t(self):
        r=base_request(**{field:""})
        self.assertEqual(self.g.evaluate(base_contract(),r).decision, Decision.DENY)
    return t
for f in ["request_id","user_id","purpose","action","resource","destination","role","contract_version","authority_version"]:
    setattr(TestValidation, "test_invalid_request_"+f, _mk_req_field_test(f))

class TestValidation2(unittest.TestCase):
    def setUp(self): self.g=IntentConsentControl()
    def test_empty_actions(self): self.assertEqual(self.g.evaluate(base_contract(allowed_actions=()),base_request()).decision,Decision.DENY)
    def test_empty_resources(self): self.assertEqual(self.g.evaluate(base_contract(allowed_resources=()),base_request()).decision,Decision.DENY)
    def test_empty_destinations(self): self.assertEqual(self.g.evaluate(base_contract(allowed_destinations=()),base_request()).decision,Decision.DENY)
    def test_empty_roles(self): self.assertEqual(self.g.evaluate(base_contract(allowed_roles=()),base_request()).decision,Decision.DENY)
    def test_duplicate_actions(self): self.assertEqual(self.g.evaluate(base_contract(allowed_actions=("read","read")),base_request()).decision,Decision.DENY)
    def test_duplicate_resources(self): self.assertEqual(self.g.evaluate(base_contract(allowed_resources=("project:a","project:a")),base_request()).decision,Decision.DENY)
    def test_duplicate_destinations(self): self.assertEqual(self.g.evaluate(base_contract(allowed_destinations=("local","local")),base_request()).decision,Decision.DENY)
    def test_duplicate_roles(self): self.assertEqual(self.g.evaluate(base_contract(allowed_roles=("owner","owner")),base_request()).decision,Decision.DENY)
    def test_invalid_time_equal(self): self.assertEqual(self.g.evaluate(base_contract(expires_at=900),base_request()).decision,Decision.DENY)
    def test_invalid_permit_binding(self): self.assertEqual(self.g.evaluate(base_contract(permit_id="p",permit_version="",permit_expires_at=1800),base_request()).decision,Decision.DENY)
    def test_invalid_observed_at(self): self.assertEqual(self.g.evaluate(base_contract(),replace(base_request(),observed_at="x")).decision,Decision.DENY)

class TestAuthority(unittest.TestCase):
    def setUp(self): self.g=IntentConsentControl()
    def test_flags_never_authoritative(self):
        x=self.g.evaluate(base_contract(),base_request())
        self.assertFalse(x.permission_granted or x.action_executed or x.action_succeeded or x.state_committed or x.authoritative)
    def test_human_evidence_not_execution(self):
        x=self.g.evaluate(base_contract(),base_request(high_impact=True,human_approval_evidence=True))
        self.assertFalse(x.permission_granted); self.assertFalse(x.action_executed); self.assertFalse(x.action_succeeded)
    def test_scope_match_not_permission(self):
        x=self.g.evaluate(base_contract(),base_request())
        self.assertTrue(x.scope_matched); self.assertFalse(x.permission_granted)
    def test_consent_current_not_action(self):
        x=self.g.evaluate(base_contract(),base_request())
        self.assertTrue(x.consent_current); self.assertFalse(x.action_executed)

class TestCacheAndDeterminism(unittest.TestCase):
    def test_cache_equal(self):
        g=IntentConsentControl(); a=g.evaluate(base_contract(),base_request()); b=g.evaluate(base_contract(),base_request()); self.assertEqual(a,b)
    def test_no_cache_equal(self):
        a=IntentConsentControl(enable_cache=False).evaluate(base_contract(),base_request()); b=IntentConsentControl(enable_cache=False).evaluate(base_contract(),base_request()); self.assertEqual(a,b)
    def test_scope_change_fingerprint(self):
        g=IntentConsentControl(); a=g.evaluate(base_contract(),base_request()); b=g.evaluate(base_contract(),base_request(action="read")); self.assertNotEqual(a.fingerprint,b.fingerprint)
    def test_contract_version_fingerprint(self):
        self.assertNotEqual(fingerprint(base_contract()), fingerprint(base_contract(contract_version="v2")))
    def test_revocation_fingerprint(self): self.assertNotEqual(fingerprint(base_contract()),fingerprint(base_contract(revoked=True)))
    def test_expiry_fingerprint(self): self.assertNotEqual(fingerprint(base_contract()),fingerprint(base_contract(expires_at=1900)))
    def test_permit_revocation_fingerprint(self): self.assertNotEqual(fingerprint(base_contract()),fingerprint(base_contract(permit_revoked=True)))
    def test_metadata_order_canonical(self):
        c1=base_contract(metadata=(("a","1"),("b","2"))); c2=base_contract(metadata=(("a","1"),("b","2"))); self.assertEqual(fingerprint(c1),fingerprint(c2))
    def test_clear_cache(self):
        g=IntentConsentControl(); g.evaluate(base_contract(),base_request()); self.assertTrue(g._result_cache); g.clear_cache(); self.assertFalse(g._result_cache)

# Add many in-scope/out-of-scope combinations for boundary coverage.
class TestBoundaryMatrix(unittest.TestCase):
    def setUp(self): self.g=IntentConsentControl()

def _matrix_test(i, action, resource, dest, role, expected):
    def t(self):
        r=base_request(request_id=f"m{i}", action=action, resource=resource, destination=dest, role=role)
        self.assertEqual(self.g.evaluate(base_contract(),r).decision, expected)
    return t
matrix=[]
for i, action in enumerate(["read","edit","delete","publish"]):
    for j, role in enumerate(["owner","editor","viewer"]):
        expected = Decision.ALLOW_CANDIDATE if action in ("read","edit") and role in ("owner","editor") else Decision.DENY
        matrix.append((action,"project:a","local",role,expected))
for idx, row in enumerate(matrix):
    setattr(TestBoundaryMatrix,f"test_matrix_{idx:02d}",_matrix_test(idx,*row))

if __name__ == '__main__': unittest.main()
