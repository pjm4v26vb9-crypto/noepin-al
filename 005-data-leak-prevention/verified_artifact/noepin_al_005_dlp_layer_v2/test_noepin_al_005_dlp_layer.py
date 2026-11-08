import hashlib, json, unittest
from noepin_al_005_dlp_layer import *

H0="0"*64
H1="1"*64

def policy():
    return DLPPolicy(
        allowed_destinations=("internal-ai","approved-api","archive"),
        internal_destinations=("internal-ai","archive"),
        confidential_destinations=("internal-ai",),
        restricted_destinations=("archive",),
        allowed_purposes=("analysis","backup","support"),
        require_consent_for_personal_data=True,
        require_redaction_for_confidential_external=True,
        deny_restricted_external=True,
        max_payload_bytes_without_confirmation=1000,
        policy_version="v2",
    )

def req(**kw):
    d=dict(
        source_id="src", actor_id="ai", destination="approved-api", purpose="analysis",
        classification=Classification.PUBLIC, payload_fingerprint=H0, payload_bytes=100,
        contains_personal_data=False, contains_secret=False, contains_credentials=False,
        contains_restricted_identifier=False, consent_present=False, consent_ref=None,
        redaction_available=False, redaction_fingerprint=None, human_approved=False,
        approval_ref=None, external_destination=True, schema_version="1", context={}
    )
    d.update(kw)
    return EgressRequest(**d)

class T(unittest.TestCase):
    def setUp(self): self.dlp=DataLeakPreventionLayer(policy())
    def check(self,r,d,reason=None):
        o=self.dlp.evaluate(r)
        self.assertEqual(o.decision,d)
        self.assertFalse(o.authoritative); self.assertFalse(o.data_sent); self.assertFalse(o.transfer_succeeded)
        if reason: self.assertIn(reason,o.reason_codes)
        return o

    def test_public_allowed(self): self.check(req(),EgressDecision.ALLOW_PREPARE)
    def test_missing_source(self): self.check(req(source_id=""),EgressDecision.HOLD)
    def test_missing_actor(self): self.check(req(actor_id=""),EgressDecision.HOLD)
    def test_missing_destination(self): self.check(req(destination=""),EgressDecision.HOLD)
    def test_missing_purpose(self): self.check(req(purpose=""),EgressDecision.HOLD)
    def test_missing_schema(self): self.check(req(schema_version=""),EgressDecision.HOLD)
    def test_negative_size(self): self.check(req(payload_bytes=-1),EgressDecision.HOLD)
    def test_bool_size(self): self.check(req(payload_bytes=True),EgressDecision.HOLD)
    def test_bad_payload_hash(self): self.check(req(payload_fingerprint="bad"),EgressDecision.HOLD)
    def test_bad_redaction_hash(self): self.check(req(redaction_fingerprint="bad"),EgressDecision.HOLD)
    def test_bad_purpose(self): self.check(req(purpose="marketing"),EgressDecision.DENY)
    def test_destination_not_allowlisted(self): self.check(req(destination="random-api"),EgressDecision.DENY)

    def test_internal_destination_restricted(self):
        self.check(req(classification=Classification.INTERNAL,destination="approved-api"),EgressDecision.DENY)
    def test_internal_internal_destination(self):
        self.check(req(classification=Classification.INTERNAL,destination="internal-ai",external_destination=False),EgressDecision.ALLOW_PREPARE)
    def test_confidential_only_internal(self):
        self.check(req(classification=Classification.CONFIDENTIAL,destination="archive",external_destination=False),EgressDecision.DENY)
    def test_confidential_internal_ok(self):
        self.check(req(classification=Classification.CONFIDENTIAL,destination="internal-ai",external_destination=False),EgressDecision.ALLOW_PREPARE)
    def test_restricted_only_archive(self):
        self.check(req(classification=Classification.RESTRICTED,destination="internal-ai",external_destination=False),EgressDecision.DENY)
    def test_restricted_archive_internal(self):
        self.check(req(classification=Classification.RESTRICTED,destination="archive",external_destination=False),EgressDecision.ALLOW_PREPARE)

    def test_secret_denied(self): self.check(req(contains_secret=True),EgressDecision.DENY)
    def test_credentials_denied(self): self.check(req(contains_credentials=True),EgressDecision.DENY)
    def test_restricted_identifier_external_denied(self): self.check(req(contains_restricted_identifier=True),EgressDecision.DENY)
    def test_restricted_external_denied(self):
        self.check(req(classification=Classification.RESTRICTED,destination="archive",external_destination=True),EgressDecision.DENY)

    def test_personal_requires_consent(self):
        self.check(req(contains_personal_data=True),EgressDecision.HOLD)
    def test_consent_bool_without_ref_insufficient(self):
        self.check(req(contains_personal_data=True,consent_present=True),EgressDecision.HOLD)
    def test_consent_ref_without_bool_insufficient(self):
        self.check(req(contains_personal_data=True,consent_ref="C"),EgressDecision.HOLD)
    def test_personal_with_consent(self):
        self.check(req(contains_personal_data=True,consent_present=True,consent_ref="C"),EgressDecision.ALLOW_PREPARE)

    def test_large_public_confirm(self):
        self.check(req(payload_bytes=1001),EgressDecision.HUMAN_CONFIRM)
    def test_large_public_approved(self):
        self.check(req(payload_bytes=1001,human_approved=True,approval_ref="A"),EgressDecision.ALLOW_PREPARE)
    def test_large_boundary_1000_allowed(self):
        self.check(req(payload_bytes=1000),EgressDecision.ALLOW_PREPARE)
    def test_large_approval_bool_without_ref(self):
        self.check(req(payload_bytes=1001,human_approved=True),EgressDecision.HUMAN_CONFIRM)

    def test_internal_external_destination_denied_by_class_policy(self):
        self.check(req(classification=Classification.INTERNAL,destination="approved-api",external_destination=True),EgressDecision.DENY)

    def test_confidential_external_destination_denied_by_class_policy(self):
        self.check(req(classification=Classification.CONFIDENTIAL,destination="approved-api",external_destination=True),EgressDecision.DENY)

    def test_confidential_external_to_internal_ai_redaction_required(self):
        self.check(req(classification=Classification.CONFIDENTIAL,destination="internal-ai",external_destination=True),EgressDecision.HOLD)
    def test_confidential_redaction_same_payload_hold(self):
        self.check(req(classification=Classification.CONFIDENTIAL,destination="internal-ai",external_destination=True,redaction_available=True,redaction_fingerprint=H0),EgressDecision.HOLD)
    def test_confidential_redaction_confirm(self):
        self.check(req(classification=Classification.CONFIDENTIAL,destination="internal-ai",external_destination=True,redaction_available=True,redaction_fingerprint=H1),EgressDecision.HUMAN_CONFIRM)
    def test_confidential_redaction_approved(self):
        self.check(req(classification=Classification.CONFIDENTIAL,destination="internal-ai",external_destination=True,redaction_available=True,redaction_fingerprint=H1,human_approved=True,approval_ref="A"),EgressDecision.REDACT_AND_PREPARE)

    def test_nonpublic_external_internal_ai_confirm(self):
        self.check(req(classification=Classification.INTERNAL,destination="internal-ai",external_destination=True),EgressDecision.HUMAN_CONFIRM)
    def test_nonpublic_external_internal_ai_approved(self):
        self.check(req(classification=Classification.INTERNAL,destination="internal-ai",external_destination=True,human_approved=True,approval_ref="A"),EgressDecision.ALLOW_PREPARE)

    def test_cache_exact(self):
        r=req(); a=self.dlp.evaluate(r); b=self.dlp.evaluate(r); self.assertFalse(a.cache_reused); self.assertTrue(b.cache_reused)
    def test_cache_never_authority(self):
        r=req(); self.dlp.evaluate(r); self.assertFalse(self.dlp.evaluate(r).authoritative)
    def test_cache_never_sent(self):
        r=req(); self.dlp.evaluate(r); self.assertFalse(self.dlp.evaluate(r).data_sent)
    def test_cache_diff_destination(self):
        self.assertNotEqual(self.dlp.fingerprint(req(destination="approved-api")),self.dlp.fingerprint(req(destination="archive")))
    def test_cache_diff_classification(self):
        self.assertNotEqual(self.dlp.fingerprint(req()),self.dlp.fingerprint(req(classification=Classification.INTERNAL)))
    def test_cache_diff_consent(self):
        self.assertNotEqual(self.dlp.fingerprint(req()),self.dlp.fingerprint(req(consent_present=True,consent_ref="C")))
    def test_cache_diff_redaction(self):
        self.assertNotEqual(self.dlp.fingerprint(req()),self.dlp.fingerprint(req(redaction_available=True,redaction_fingerprint=H1)))
    def test_context_order_deterministic(self):
        self.assertEqual(self.dlp.fingerprint(req(context={"b":2,"a":1})),self.dlp.fingerprint(req(context={"a":1,"b":2})))
    def test_clear_cache(self):
        self.dlp.evaluate(req()); self.assertGreater(self.dlp.cache_size(),0); self.dlp.clear_cache(); self.assertEqual(self.dlp.cache_size(),0)
    def test_stable_payload_no_time(self): self.assertNotIn("created_unix_ns",self.dlp.evaluate(req()).stable_payload())

    def test_classification_preserved(self):
        o=self.dlp.evaluate(req(classification=Classification.INTERNAL,destination="internal-ai",external_destination=False))
        self.assertEqual(o.classification,Classification.INTERNAL)
    def test_purpose_preserved(self):
        o=self.dlp.evaluate(req(purpose="backup",destination="archive")); self.assertEqual(o.purpose,"backup")
    def test_destination_preserved(self):
        o=self.dlp.evaluate(req(destination="archive")); self.assertEqual(o.destination,"archive")

    def test_read_permission_not_modeled_as_egress_permission(self):
        # no field exists that promotes read access to egress authority
        o=self.dlp.evaluate(req()); self.assertEqual(o.decision,EgressDecision.ALLOW_PREPARE); self.assertFalse(o.data_sent)

    def test_redaction_candidate_not_transfer_success(self):
        o=self.dlp.evaluate(req(classification=Classification.CONFIDENTIAL,destination="internal-ai",external_destination=True,redaction_available=True,redaction_fingerprint=H1,human_approved=True,approval_ref="A"))
        self.assertFalse(o.transfer_succeeded)

    def test_many_public_allowed(self):
        for i in range(10):
            self.check(req(payload_fingerprint=f"{i:x}".rjust(64,"0"),payload_bytes=i),EgressDecision.ALLOW_PREPARE)

def replay_fingerprint():
    d=DataLeakPreventionLayer(policy())
    out=[]
    classes=list(Classification)
    dests=["approved-api","internal-ai","archive"]
    for i in range(1000):
        c=classes[i%4]; dest=dests[i%3]
        kwargs=dict(
            source_id="s",actor_id="a",destination=dest,purpose=("analysis","backup","support")[i%3],
            classification=c,payload_fingerprint=f"{i:x}".rjust(64,"0"),payload_bytes=i%1200,
            external_destination=(i%2==0)
        )
        if i%5==0:
            kwargs["contains_personal_data"]=True; kwargs["consent_present"]=True; kwargs["consent_ref"]="C"
        if c==Classification.CONFIDENTIAL and kwargs["external_destination"]:
            kwargs["redaction_available"]=True; kwargs["redaction_fingerprint"]=f"{i+10000:x}".rjust(64,"0")
        if i%4==0:
            kwargs["human_approved"]=True; kwargs["approval_ref"]="A"
        r=d.evaluate(EgressRequest(**kwargs))
        out.append(r.stable_payload())
    raw=json.dumps(out,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

if __name__=="__main__":
    unittest.main()
