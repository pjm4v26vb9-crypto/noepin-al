
import unittest, hashlib, json
from noepin_al_020_confidential_egress_guard import *
H="a"*64
RH="b"*64

def req(**kw):
    d=dict(request_id="r",content_fingerprint=H,classification=Classification.INTERNAL,
           destination_kind=DestinationKind.INTERNAL,destination_ref="internal://x",purpose="work",
           consent_ref=None,contains_secret=False,contains_personal_data=False,contains_api_key=False,
           contains_auth_token=False,contains_private_key=False,contains_health_data=False,
           contains_financial_data=False,redaction_possible=False,redaction_applied=False,
           redacted_content_fingerprint=None,destination_allowlisted=True,purpose_allowed=True,
           external_transfer_required=False,human_approved=False,approval_ref=None,policy_version="v2",context={})
    d.update(kw); return EgressRequest(**d)

class T(unittest.TestCase):
    def setUp(self): self.g=ConfidentialEgressGuard()
    def chk(self,r,d):
        o=self.g.evaluate(r); self.assertEqual(o.decision,d); self.assertFalse(o.send_authorized)
        self.assertFalse(o.transfer_performed); self.assertFalse(o.transfer_succeeded); self.assertFalse(o.memory_written); self.assertFalse(o.authoritative); return o
    def test_internal_allow(self): self.chk(req(),EgressDecision.ALLOW_PREPARE)
    def test_missing_request(self): self.chk(req(request_id=""),EgressDecision.HOLD)
    def test_missing_dest(self): self.chk(req(destination_ref=""),EgressDecision.HOLD)
    def test_missing_purpose(self): self.chk(req(purpose=""),EgressDecision.HOLD)
    def test_missing_policy(self): self.chk(req(policy_version=""),EgressDecision.HOLD)
    def test_bad_hash(self): self.chk(req(content_fingerprint="x"),EgressDecision.HOLD)
    def test_redact_hash_required(self): self.chk(req(redaction_applied=True),EgressDecision.HOLD)
    def test_unallowlisted(self): self.chk(req(destination_allowlisted=False),EgressDecision.DENY)
    def test_bad_purpose(self): self.chk(req(purpose_allowed=False),EgressDecision.DENY)
    def test_api_key_external(self): self.chk(req(destination_kind=DestinationKind.EXTERNAL_AI,contains_api_key=True),EgressDecision.DENY)
    def test_token_external(self): self.chk(req(destination_kind=DestinationKind.EMAIL,contains_auth_token=True),EgressDecision.DENY)
    def test_private_key_external(self): self.chk(req(destination_kind=DestinationKind.WEBHOOK,contains_private_key=True),EgressDecision.DENY)
    def test_restricted_external(self): self.chk(req(classification=Classification.RESTRICTED,destination_kind=DestinationKind.EXTERNAL_SERVICE),EgressDecision.DENY)
    def test_personal_consent(self): self.chk(req(destination_kind=DestinationKind.EXTERNAL_SERVICE,contains_personal_data=True),EgressDecision.HOLD)
    def test_health_consent(self): self.chk(req(destination_kind=DestinationKind.EXTERNAL_SERVICE,contains_health_data=True),EgressDecision.HOLD)
    def test_financial_consent(self): self.chk(req(destination_kind=DestinationKind.EXTERNAL_SERVICE,contains_financial_data=True),EgressDecision.HOLD)
    def test_sensitive_no_redaction(self): self.chk(req(destination_kind=DestinationKind.EXTERNAL_SERVICE,contains_secret=True,consent_ref="C"),EgressDecision.HUMAN_CONFIRM)
    def test_redaction_required(self): self.chk(req(destination_kind=DestinationKind.EXTERNAL_SERVICE,contains_secret=True,consent_ref="C",redaction_possible=True),EgressDecision.REDACT_AND_PREPARE)
    def test_redacted_needs_human(self): self.chk(req(destination_kind=DestinationKind.EXTERNAL_SERVICE,contains_secret=True,consent_ref="C",redaction_possible=True,redaction_applied=True,redacted_content_fingerprint=RH),EgressDecision.HUMAN_CONFIRM)
    def test_redacted_human_allow(self): self.chk(req(destination_kind=DestinationKind.EXTERNAL_SERVICE,contains_secret=True,consent_ref="C",redaction_possible=True,redaction_applied=True,redacted_content_fingerprint=RH,human_approved=True,approval_ref="H"),EgressDecision.ALLOW_PREPARE)
    def test_external_plain_human(self): self.chk(req(destination_kind=DestinationKind.EXTERNAL_SERVICE),EgressDecision.HUMAN_CONFIRM)
    def test_external_plain_approved(self): self.chk(req(destination_kind=DestinationKind.EXTERNAL_SERVICE,human_approved=True,approval_ref="H"),EgressDecision.ALLOW_PREPARE)
    def test_external_required_flag(self): self.chk(req(external_transfer_required=True),EgressDecision.HUMAN_CONFIRM)
    def test_internal_secret(self): self.chk(req(contains_secret=True),EgressDecision.ALLOW_PREPARE)
    def test_internal_personal(self): self.chk(req(contains_personal_data=True),EgressDecision.ALLOW_PREPARE)
    def test_email_plain(self): self.chk(req(destination_kind=DestinationKind.EMAIL),EgressDecision.HUMAN_CONFIRM)
    def test_unknown_dest(self): self.chk(req(destination_kind=DestinationKind.UNKNOWN),EgressDecision.HUMAN_CONFIRM)
    def test_consent_not_authority(self):
        o=self.chk(req(destination_kind=DestinationKind.EXTERNAL_SERVICE,contains_personal_data=True,consent_ref="C",redaction_possible=False),EgressDecision.HUMAN_CONFIRM); self.assertFalse(o.send_authorized)
    def test_approval_not_transfer(self):
        o=self.chk(req(destination_kind=DestinationKind.EXTERNAL_SERVICE,human_approved=True,approval_ref="H"),EgressDecision.ALLOW_PREPARE); self.assertFalse(o.transfer_performed)
    def test_cache_exact(self):
        r=req(); a=self.g.evaluate(r); b=self.g.evaluate(r); self.assertFalse(a.cache_reused); self.assertTrue(b.cache_reused)
    def test_cache_not_authority(self):
        r=req(); self.g.evaluate(r); self.assertFalse(self.g.evaluate(r).authoritative)
    def test_cache_not_transfer(self):
        r=req(); self.g.evaluate(r); self.assertFalse(self.g.evaluate(r).transfer_succeeded)
    def test_fingerprint_dest(self):
        self.assertNotEqual(self.g.fingerprint(req()),self.g.fingerprint(req(destination_ref="internal://y")))
    def test_fingerprint_purpose(self):
        self.assertNotEqual(self.g.fingerprint(req()),self.g.fingerprint(req(purpose="other")))
    def test_fingerprint_consent(self):
        self.assertNotEqual(self.g.fingerprint(req()),self.g.fingerprint(req(consent_ref="C")))
    def test_fingerprint_secret(self):
        self.assertNotEqual(self.g.fingerprint(req()),self.g.fingerprint(req(contains_secret=True)))
    def test_fingerprint_redaction(self):
        self.assertNotEqual(self.g.fingerprint(req()),self.g.fingerprint(req(redaction_possible=True)))
    def test_fingerprint_approval(self):
        self.assertNotEqual(self.g.fingerprint(req()),self.g.fingerprint(req(human_approved=True,approval_ref="H")))
    def test_context_order(self):
        self.assertEqual(self.g.fingerprint(req(context={"b":2,"a":1})),self.g.fingerprint(req(context={"a":1,"b":2})))
    def test_clear_cache(self):
        self.g.evaluate(req()); self.assertGreater(self.g.cache_size(),0); self.g.clear_cache(); self.assertEqual(self.g.cache_size(),0)
    def test_secret_detected_not_sent(self):
        o=self.chk(req(destination_kind=DestinationKind.EXTERNAL_AI,contains_secret=True,consent_ref="C"),EgressDecision.HUMAN_CONFIRM); self.assertFalse(o.transfer_performed)
    def test_redaction_candidate_not_safe_transfer(self):
        o=self.chk(req(destination_kind=DestinationKind.EXTERNAL_AI,contains_secret=True,consent_ref="C",redaction_possible=True),EgressDecision.REDACT_AND_PREPARE); self.assertFalse(o.transfer_succeeded)
    def test_allowlisted_not_purpose(self):
        self.chk(req(destination_kind=DestinationKind.EXTERNAL_AI,destination_allowlisted=True,purpose_allowed=False),EgressDecision.DENY)
    def test_public_external_still_human(self):
        self.chk(req(classification=Classification.PUBLIC,destination_kind=DestinationKind.EXTERNAL_SERVICE),EgressDecision.HUMAN_CONFIRM)
    def test_confidential_external(self):
        self.chk(req(classification=Classification.CONFIDENTIAL,destination_kind=DestinationKind.EXTERNAL_SERVICE),EgressDecision.HUMAN_CONFIRM)
    def test_personal_redacted_human(self):
        self.chk(req(destination_kind=DestinationKind.EXTERNAL_SERVICE,contains_personal_data=True,consent_ref="C",redaction_possible=True,redaction_applied=True,redacted_content_fingerprint=RH),EgressDecision.HUMAN_CONFIRM)
    def test_personal_redacted_approved(self):
        self.chk(req(destination_kind=DestinationKind.EXTERNAL_SERVICE,contains_personal_data=True,consent_ref="C",redaction_possible=True,redaction_applied=True,redacted_content_fingerprint=RH,human_approved=True,approval_ref="H"),EgressDecision.ALLOW_PREPARE)
    def test_policy_change_fingerprint(self):
        self.assertNotEqual(self.g.fingerprint(req(policy_version="v2")),self.g.fingerprint(req(policy_version="v3")))

def replay_fingerprint():
    g=ConfidentialEgressGuard()
    out=[]
    dests=list(DestinationKind); classes=list(Classification)
    for i in range(1000):
        r=req(request_id=f"r{i}",destination_kind=dests[i%len(dests)],classification=classes[i%len(classes)],
              contains_personal_data=(i%7==0),contains_secret=(i%11==0),contains_api_key=(i%97==0),
              consent_ref="C" if i%5==0 else None,redaction_possible=(i%3==0),
              human_approved=(i%13==0),approval_ref="H" if i%13==0 else None,
              destination_ref=f"d{i%17}",purpose="work" if i%19 else "other",
              purpose_allowed=(i%19!=0),destination_allowlisted=(i%23!=0))
        out.append(g.evaluate(r).stable_payload())
    raw=json.dumps(out,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

if __name__=="__main__": unittest.main()
