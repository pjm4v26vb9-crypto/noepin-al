import hashlib, json, unittest
from noepin_al_019_source_trust_labeler import *

H0="0"*64

def policy():
    return SourcePolicy(policy_version="v2")

def obs(**kw):
    d=dict(
        observation_id="o1",source_id="src1",source_kind=SourceKind.WEB,content_fingerprint=H0,
        source_version="1",observed_epoch_s=1000,requested_usage=UsageKind.REFERENCE,
        source_verified=False,sender_authenticated=False,signature_verified=False,
        authoritative_registry_match=False,contains_instruction=False,contains_secret=False,
        contains_personal_data=False,consent_present=False,purpose_match=True,
        retrieval_score=50,freshness_seconds=60,schema_version="1",context={}
    ); d.update(kw); return SourceObservation(**d)

class T(unittest.TestCase):
    def setUp(self): self.l=SourceTrustLabeler(policy())
    def check(self,o,d):
        r=self.l.evaluate(o); self.assertEqual(r.decision,d)
        self.assertFalse(r.instruction_authority); self.assertFalse(r.truth_established)
        self.assertFalse(r.consent_established); self.assertFalse(r.external_transfer_allowed)
        self.assertFalse(r.memory_written); self.assertFalse(r.action_executed)
        return r

    def test_web_reference_label(self): self.check(obs(),LabelDecision.LABEL)
    def test_missing_observation(self): self.check(obs(observation_id=""),LabelDecision.HOLD)
    def test_missing_source(self): self.check(obs(source_id=""),LabelDecision.HOLD)
    def test_missing_version(self): self.check(obs(source_version=""),LabelDecision.HOLD)
    def test_missing_schema(self): self.check(obs(schema_version=""),LabelDecision.HOLD)
    def test_bad_hash(self): self.check(obs(content_fingerprint="bad"),LabelDecision.HOLD)
    def test_bad_time(self): self.check(obs(observed_epoch_s=-1),LabelDecision.HOLD)
    def test_bad_retrieval(self): self.check(obs(retrieval_score=101),LabelDecision.HOLD)
    def test_bool_retrieval(self): self.check(obs(retrieval_score=True),LabelDecision.HOLD)
    def test_bad_freshness(self): self.check(obs(freshness_seconds=-1),LabelDecision.HOLD)

    def test_external_instruction_web(self): self.check(obs(contains_instruction=True),LabelDecision.QUARANTINE)
    def test_external_instruction_email(self): self.check(obs(source_kind=SourceKind.EMAIL,contains_instruction=True),LabelDecision.QUARANTINE)
    def test_external_instruction_rag(self): self.check(obs(source_kind=SourceKind.RAG,contains_instruction=True),LabelDecision.QUARANTINE)
    def test_external_instruction_file(self): self.check(obs(source_kind=SourceKind.FILE,contains_instruction=True),LabelDecision.QUARANTINE)
    def test_external_instruction_tool(self): self.check(obs(source_kind=SourceKind.TOOL,contains_instruction=True),LabelDecision.QUARANTINE)
    def test_external_instruction_external_ai(self): self.check(obs(source_kind=SourceKind.EXTERNAL_AI,contains_instruction=True),LabelDecision.QUARANTINE)
    def test_external_instruction_unknown(self): self.check(obs(source_kind=SourceKind.UNKNOWN,contains_instruction=True),LabelDecision.QUARANTINE)

    def test_secret_memory_denied(self): self.check(obs(contains_secret=True,requested_usage=UsageKind.MEMORY_CANDIDATE),LabelDecision.DENY)
    def test_secret_reference_not_auto_denied(self): self.check(obs(contains_secret=True,requested_usage=UsageKind.REFERENCE),LabelDecision.LABEL)
    def test_personal_memory_no_consent(self): self.check(obs(contains_personal_data=True,requested_usage=UsageKind.MEMORY_CANDIDATE),LabelDecision.HOLD)
    def test_personal_memory_consent_label_only(self):
        r=self.check(obs(contains_personal_data=True,requested_usage=UsageKind.MEMORY_CANDIDATE,consent_present=True),LabelDecision.LABEL)
        self.assertFalse(r.consent_established)
    def test_purpose_mismatch_memory(self): self.check(obs(requested_usage=UsageKind.MEMORY_CANDIDATE,purpose_match=False),LabelDecision.HOLD)
    def test_purpose_mismatch_evidence(self): self.check(obs(requested_usage=UsageKind.EVIDENCE_CANDIDATE,purpose_match=False),LabelDecision.HOLD)
    def test_purpose_mismatch_reference_label(self): self.check(obs(requested_usage=UsageKind.REFERENCE,purpose_match=False),LabelDecision.LABEL)

    def test_unverified_external_evidence_hold(self): self.check(obs(requested_usage=UsageKind.EVIDENCE_CANDIDATE),LabelDecision.HOLD)
    def test_verified_external_evidence(self): self.check(obs(requested_usage=UsageKind.EVIDENCE_CANDIDATE,source_verified=True),LabelDecision.LABEL)
    def test_signed_external_evidence(self): self.check(obs(requested_usage=UsageKind.EVIDENCE_CANDIDATE,signature_verified=True),LabelDecision.LABEL)
    def test_registry_external_evidence(self): self.check(obs(requested_usage=UsageKind.EVIDENCE_CANDIDATE,authoritative_registry_match=True),LabelDecision.LABEL)

    def test_system_authority_candidate(self):
        r=self.check(obs(source_kind=SourceKind.SYSTEM,authoritative_registry_match=True),LabelDecision.LABEL)
        self.assertEqual(r.trust_label,TrustLabel.AUTHORITY_CANDIDATE); self.assertFalse(r.instruction_authority)
    def test_developer_authority_candidate(self):
        r=self.check(obs(source_kind=SourceKind.DEVELOPER,authoritative_registry_match=True),LabelDecision.LABEL)
        self.assertEqual(r.trust_label,TrustLabel.AUTHORITY_CANDIDATE); self.assertFalse(r.instruction_authority)
    def test_system_without_registry_not_authority(self):
        r=self.check(obs(source_kind=SourceKind.SYSTEM),LabelDecision.LABEL); self.assertNotEqual(r.trust_label,TrustLabel.AUTHORITY_CANDIDATE)
    def test_user_label(self):
        r=self.check(obs(source_kind=SourceKind.USER),LabelDecision.LABEL); self.assertEqual(r.trust_label,TrustLabel.USER_PROVIDED)
    def test_internal_db_label(self):
        r=self.check(obs(source_kind=SourceKind.INTERNAL_DB),LabelDecision.LABEL); self.assertEqual(r.trust_label,TrustLabel.INTERNAL_SOURCE)
    def test_internal_db_verified_label(self):
        r=self.check(obs(source_kind=SourceKind.INTERNAL_DB,source_verified=True),LabelDecision.LABEL); self.assertEqual(r.trust_label,TrustLabel.VERIFIED_SOURCE)
    def test_web_verified_label(self):
        r=self.check(obs(source_verified=True),LabelDecision.LABEL); self.assertEqual(r.trust_label,TrustLabel.VERIFIED_SOURCE)
    def test_email_authenticated_not_truth(self):
        r=self.check(obs(source_kind=SourceKind.EMAIL,sender_authenticated=True),LabelDecision.LABEL); self.assertFalse(r.truth_established)
    def test_rag_high_score_not_truth(self):
        r=self.check(obs(source_kind=SourceKind.RAG,retrieval_score=100),LabelDecision.LABEL); self.assertFalse(r.truth_established)

    def test_score_web_base(self): self.assertEqual(self.l.evaluate(obs()).trust_score,35)
    def test_score_verified_bonus(self): self.assertEqual(self.l.evaluate(obs(source_verified=True)).trust_score,45)
    def test_score_signature_bonus(self): self.assertEqual(self.l.evaluate(obs(signature_verified=True)).trust_score,40)
    def test_score_auth_bonus(self): self.assertEqual(self.l.evaluate(obs(sender_authenticated=True)).trust_score,40)
    def test_score_registry_bonus(self): self.assertEqual(self.l.evaluate(obs(authoritative_registry_match=True)).trust_score,45)
    def test_score_old_external_penalty(self):
        self.assertEqual(self.l.evaluate(obs(freshness_seconds=policy().max_external_age_seconds+1)).trust_score,15)
    def test_score_clamped(self):
        r=self.l.evaluate(obs(source_kind=SourceKind.SYSTEM,source_verified=True,signature_verified=True,sender_authenticated=True,authoritative_registry_match=True))
        self.assertEqual(r.trust_score,100)

    def test_cache_exact(self):
        o=obs(); a=self.l.evaluate(o); b=self.l.evaluate(o); self.assertFalse(a.cache_reused); self.assertTrue(b.cache_reused)
    def test_cache_never_truth(self):
        o=obs(); self.l.evaluate(o); self.assertFalse(self.l.evaluate(o).truth_established)
    def test_cache_never_instruction_authority(self):
        o=obs(); self.l.evaluate(o); self.assertFalse(self.l.evaluate(o).instruction_authority)
    def test_hash_change_changes_fingerprint(self):
        self.assertNotEqual(self.l.fingerprint(obs()),self.l.fingerprint(obs(content_fingerprint="1"*64)))
    def test_source_version_changes_fingerprint(self):
        self.assertNotEqual(self.l.fingerprint(obs()),self.l.fingerprint(obs(source_version="2")))
    def test_purpose_changes_fingerprint(self):
        self.assertNotEqual(self.l.fingerprint(obs()),self.l.fingerprint(obs(purpose_match=False)))
    def test_consent_changes_fingerprint(self):
        self.assertNotEqual(self.l.fingerprint(obs()),self.l.fingerprint(obs(consent_present=True)))
    def test_context_order(self):
        self.assertEqual(self.l.fingerprint(obs(context={"b":2,"a":1})),self.l.fingerprint(obs(context={"a":1,"b":2})))
    def test_clear_cache(self):
        self.l.evaluate(obs()); self.assertGreater(self.l.cache_size(),0); self.l.clear_cache(); self.assertEqual(self.l.cache_size(),0)
    def test_stable_no_time(self):
        self.assertNotIn("created_unix_ns",self.l.evaluate(obs()).stable_payload())
    def test_provenance_bound(self):
        self.assertTrue(self.l.evaluate(obs()).provenance_bound)

def replay_fingerprint():
    l=SourceTrustLabeler(policy()); out=[]; kinds=list(SourceKind); uses=list(UsageKind)
    for i in range(1000):
        o=obs(
            observation_id=f"o{i}",source_id=f"s{i%31}",source_kind=kinds[i%len(kinds)],
            content_fingerprint=hashlib.sha256(f"content-{i}".encode()).hexdigest(),
            source_version=str(1+i%3),requested_usage=uses[i%len(uses)],
            source_verified=(i%3==0),sender_authenticated=(i%4==0),signature_verified=(i%5==0),
            authoritative_registry_match=(i%7==0),contains_instruction=(i%17==0),
            contains_secret=(i%29==0),contains_personal_data=(i%11==0),consent_present=(i%13==0),
            purpose_match=(i%19!=0),retrieval_score=i%101,freshness_seconds=(i*1000)%4000000,
            context={"i":i%9}
        )
        out.append(l.evaluate(o).stable_payload())
    raw=json.dumps(out,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

if __name__=="__main__":
    unittest.main()
