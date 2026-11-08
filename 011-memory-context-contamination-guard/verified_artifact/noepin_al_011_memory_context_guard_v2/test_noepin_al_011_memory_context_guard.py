import hashlib, json, unittest
from noepin_al_011_memory_context_guard import *
H0="0"*64

def policy(): return MemoryPolicy(policy_version="v2")
def cand(**kw):
    d=dict(candidate_id="c1",content_fingerprint=H0,source_kind=SourceKind.USER,source_ref="user:1",memory_tier=MemoryTier.SESSION,
           confidence=80,ttl_seconds=3600,observed_epoch_s=1000,contains_instruction=False,claims_authority=False,contains_secret=False,
           contains_personal_data=False,contradiction_detected=False,source_verified=True,user_confirmed=False,confirmation_ref=None,
           schema_version="1",metadata={})
    d.update(kw); return MemoryCandidate(**d)

class T(unittest.TestCase):
    def setUp(self): self.g=MemoryContextContaminationGuard(policy())
    def check(self,c,d):
        o=self.g.evaluate(c); self.assertEqual(o.decision,d); self.assertFalse(o.write_authorized); self.assertFalse(o.authoritative); self.assertFalse(o.truth_established); self.assertFalse(o.memory_written); return o
    def test_session_allow(self): self.check(cand(),MemoryDecision.ALLOW_CANDIDATE)
    def test_missing_id(self): self.check(cand(candidate_id=""),MemoryDecision.HOLD)
    def test_missing_source(self): self.check(cand(source_ref=""),MemoryDecision.HOLD)
    def test_missing_schema(self): self.check(cand(schema_version=""),MemoryDecision.HOLD)
    def test_bad_hash(self): self.check(cand(content_fingerprint="bad"),MemoryDecision.HOLD)
    def test_bad_conf_low(self): self.check(cand(confidence=-1),MemoryDecision.HOLD)
    def test_bad_conf_high(self): self.check(cand(confidence=101),MemoryDecision.HOLD)
    def test_bool_conf(self): self.check(cand(confidence=True),MemoryDecision.HOLD)
    def test_bad_ttl(self): self.check(cand(ttl_seconds=-1),MemoryDecision.HOLD)
    def test_bool_ttl(self): self.check(cand(ttl_seconds=True),MemoryDecision.HOLD)
    def test_bad_time(self): self.check(cand(observed_epoch_s=-1),MemoryDecision.HOLD)
    def test_ttl_clamped(self): self.assertEqual(self.g.evaluate(cand(ttl_seconds=99999999)).normalized_ttl_seconds,31536000)
    def test_secret_session_deny(self): self.check(cand(contains_secret=True),MemoryDecision.DENY)
    def test_secret_long_deny(self): self.check(cand(memory_tier=MemoryTier.LONG_TERM,contains_secret=True,source_verified=True),MemoryDecision.DENY)
    def test_secret_ephemeral_allow(self): self.check(cand(memory_tier=MemoryTier.EPHEMERAL,contains_secret=True),MemoryDecision.ALLOW_CANDIDATE)
    def test_web_instruction_quarantine(self): self.check(cand(source_kind=SourceKind.WEB,contains_instruction=True),MemoryDecision.QUARANTINE)
    def test_file_instruction_quarantine(self): self.check(cand(source_kind=SourceKind.FILE,contains_instruction=True),MemoryDecision.QUARANTINE)
    def test_rag_instruction_quarantine(self): self.check(cand(source_kind=SourceKind.RAG,contains_instruction=True,memory_tier=MemoryTier.RAG_CONTEXT),MemoryDecision.QUARANTINE)
    def test_external_ai_instruction_quarantine(self): self.check(cand(source_kind=SourceKind.EXTERNAL_AI,contains_instruction=True),MemoryDecision.QUARANTINE)
    def test_untrusted_authority_quarantine(self): self.check(cand(source_kind=SourceKind.WEB,claims_authority=True),MemoryDecision.QUARANTINE)
    def test_user_instruction_not_auto_quarantine(self): self.check(cand(source_kind=SourceKind.USER,contains_instruction=True),MemoryDecision.ALLOW_CANDIDATE)
    def test_contradiction_quarantine(self): self.check(cand(contradiction_detected=True),MemoryDecision.QUARANTINE)
    def test_session_low_conf_hold(self): self.check(cand(confidence=39),MemoryDecision.HOLD)
    def test_session_boundary_40(self): self.check(cand(confidence=40),MemoryDecision.ALLOW_CANDIDATE)
    def test_long_low_conf_hold(self): self.check(cand(memory_tier=MemoryTier.LONG_TERM,confidence=69,source_verified=True),MemoryDecision.HOLD)
    def test_long_boundary_70(self): self.check(cand(memory_tier=MemoryTier.LONG_TERM,confidence=70,source_verified=True),MemoryDecision.ALLOW_CANDIDATE)
    def test_long_unverified_hold(self): self.check(cand(memory_tier=MemoryTier.LONG_TERM,source_verified=False),MemoryDecision.HOLD)
    def test_long_user_confirmed_can_pass_source_gate(self): self.check(cand(memory_tier=MemoryTier.LONG_TERM,source_verified=False,user_confirmed=True,confirmation_ref="U"),MemoryDecision.ALLOW_CANDIDATE)
    def test_long_confirmation_bool_only_not_enough(self): self.check(cand(memory_tier=MemoryTier.LONG_TERM,source_verified=False,user_confirmed=True),MemoryDecision.HOLD)
    def test_personal_long_needs_confirm(self): self.check(cand(memory_tier=MemoryTier.LONG_TERM,source_verified=True,contains_personal_data=True),MemoryDecision.HOLD)
    def test_personal_long_confirmed(self): self.check(cand(memory_tier=MemoryTier.LONG_TERM,source_verified=True,contains_personal_data=True,user_confirmed=True,confirmation_ref="U"),MemoryDecision.ALLOW_CANDIDATE)
    def test_rag_clean_context_candidate(self): self.check(cand(source_kind=SourceKind.RAG,memory_tier=MemoryTier.RAG_CONTEXT,confidence=50),MemoryDecision.ALLOW_CANDIDATE)
    def test_ephemeral_low_conf_candidate(self): self.check(cand(memory_tier=MemoryTier.EPHEMERAL,confidence=1),MemoryDecision.ALLOW_CANDIDATE)
    def test_cache_exact(self):
        c=cand(); a=self.g.evaluate(c); b=self.g.evaluate(c); self.assertFalse(a.cache_reused); self.assertTrue(b.cache_reused)
    def test_cache_never_truth(self):
        c=cand(); self.g.evaluate(c); self.assertFalse(self.g.evaluate(c).truth_established)
    def test_cache_never_write(self):
        c=cand(); self.g.evaluate(c); self.assertFalse(self.g.evaluate(c).memory_written)
    def test_cache_diff_source(self): self.assertNotEqual(self.g.fingerprint(cand()),self.g.fingerprint(cand(source_kind=SourceKind.WEB)))
    def test_cache_diff_confidence(self): self.assertNotEqual(self.g.fingerprint(cand(confidence=80)),self.g.fingerprint(cand(confidence=81)))
    def test_cache_diff_confirmation(self): self.assertNotEqual(self.g.fingerprint(cand()),self.g.fingerprint(cand(user_confirmed=True,confirmation_ref="U")))
    def test_context_order(self): self.assertEqual(self.g.fingerprint(cand(metadata={"b":2,"a":1})),self.g.fingerprint(cand(metadata={"a":1,"b":2})))
    def test_clear_cache(self): self.g.evaluate(cand()); self.assertGreater(self.g.cache_size(),0); self.g.clear_cache(); self.assertEqual(self.g.cache_size(),0)
    def test_stable_no_time(self): self.assertNotIn("created_unix_ns",self.g.evaluate(cand()).stable_payload())
    def test_candidate_not_memory(self): self.assertFalse(self.check(cand(),MemoryDecision.ALLOW_CANDIDATE).memory_written)
    def test_candidate_not_truth(self): self.assertFalse(self.check(cand(),MemoryDecision.ALLOW_CANDIDATE).truth_established)
    def test_claim_not_authority(self): self.assertFalse(self.check(cand(source_kind=SourceKind.WEB,claims_authority=True),MemoryDecision.QUARANTINE).authoritative)
    def test_many_valid_session(self):
        for i in range(10): self.check(cand(candidate_id=f"c{i}",content_fingerprint=f"{i:x}".rjust(64,"0")),MemoryDecision.ALLOW_CANDIDATE)

def replay_fingerprint():
    g=MemoryContextContaminationGuard(policy()); out=[]; sources=list(SourceKind); tiers=list(MemoryTier)
    for i in range(1000):
        s=sources[i%len(sources)]; t=tiers[i%len(tiers)]
        c=MemoryCandidate(candidate_id=f"c{i}",content_fingerprint=f"{i:x}".rjust(64,"0"),source_kind=s,source_ref=f"src:{i%17}",memory_tier=t,
          confidence=i%101,ttl_seconds=(i*97)%50000000,observed_epoch_s=1000+i,contains_instruction=(i%13==0),claims_authority=(i%29==0),
          contains_secret=(i%37==0),contains_personal_data=(i%19==0),contradiction_detected=(i%23==0),source_verified=(i%3==0),
          user_confirmed=(i%5==0),confirmation_ref="U" if i%5==0 else None)
        out.append(g.evaluate(c).stable_payload())
    raw=json.dumps(out,sort_keys=True,separators=(",",":")).encode(); return hashlib.sha256(raw).hexdigest()

if __name__=="__main__": unittest.main()
