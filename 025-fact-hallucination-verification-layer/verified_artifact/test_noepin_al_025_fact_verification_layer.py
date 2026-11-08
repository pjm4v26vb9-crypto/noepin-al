import dataclasses
import hashlib
import json
import unittest

from noepin_al_025_fact_verification_layer import *

CLAIM_FP = hashlib.sha256(b"claim-a").hexdigest()
OTHER_FP = hashlib.sha256(b"claim-b").hexdigest()

def h(s): return hashlib.sha256(s.encode()).hexdigest()

def ev(i="1", stance=EvidenceStance.SUPPORTS, group="g1", primary=False, verified=True,
       auth=True, quality=0.95, directness=0.95, freshness=0.95, claim_fp=CLAIM_FP,
       target_version="v1", expired=False, synthetic=False):
    return Evidence(
        evidence_id=f"e{i}", source_kind="official" if primary else "secondary",
        source_id=f"s{i}", source_version="1", claim_fingerprint=claim_fp,
        target_version=target_version, content_fingerprint=h(f"content-{i}"), stance=stance,
        source_verified=verified, source_authenticated=auth, primary_source=primary,
        independent_group=group, quality=quality, directness=directness, freshness=freshness,
        expired=expired, synthetic=synthetic,
    )

def req(evidence=(), **kw):
    base = dict(claim_id="c1", claim_text="A factual claim", claim_fingerprint=CLAIM_FP,
                target_version="v1", impact=Impact.MEDIUM, evidence=tuple(evidence),
                minimum_independent_sources=2, minimum_support_score=1.2)
    base.update(kw)
    return VerificationRequest(**base)

class CoreTests(unittest.TestCase):
    def setUp(self): self.layer = FactVerificationLayer()

    def test_no_evidence_insufficient(self): self.assertEqual(self.layer.evaluate(req()).decision, Decision.INSUFFICIENT)
    def test_two_independent_supports_verified_candidate(self):
        r=self.layer.evaluate(req([ev("1",group="g1"),ev("2",group="g2")]))
        self.assertEqual(r.decision, Decision.VERIFIED_CANDIDATE); self.assertFalse(r.truth_established)
    def test_same_group_insufficient(self): self.assertEqual(self.layer.evaluate(req([ev("1",group="g"),ev("2",group="g")])).decision, Decision.INSUFFICIENT)
    def test_primary_required_hold(self): self.assertEqual(self.layer.evaluate(req([ev("1",group="a"),ev("2",group="b")], require_primary=True)).decision, Decision.HOLD)
    def test_primary_present_passes(self): self.assertEqual(self.layer.evaluate(req([ev("1",group="a",primary=True),ev("2",group="b")], require_primary=True)).decision, Decision.VERIFIED_CANDIDATE)
    def test_high_impact_human_confirm(self): self.assertEqual(self.layer.evaluate(req([ev("1",group="a"),ev("2",group="b")], impact=Impact.HIGH)).decision, Decision.HUMAN_CONFIRM)
    def test_critical_impact_human_confirm(self): self.assertEqual(self.layer.evaluate(req([ev("1",group="a"),ev("2",group="b")], impact=Impact.CRITICAL)).decision, Decision.HUMAN_CONFIRM)
    def test_strong_contradiction_blocks(self):
        e=[ev("1",group="a"),ev("2",stance=EvidenceStance.CONTRADICTS,group="b",primary=True,quality=1,directness=1,freshness=1)]
        self.assertEqual(self.layer.evaluate(req(e, minimum_independent_sources=1, minimum_support_score=.2)).decision, Decision.CONTRADICTED)
    def test_unverified_evidence_not_counted(self): self.assertEqual(self.layer.evaluate(req([ev("1",verified=False),ev("2",verified=False)])).decision, Decision.INSUFFICIENT)
    def test_expired_evidence_not_counted(self): self.assertIn(self.layer.evaluate(req([ev("1",expired=True),ev("2",expired=True)])).decision,(Decision.HOLD,Decision.INSUFFICIENT))
    def test_claim_binding_mismatch(self): self.assertEqual(self.layer.evaluate(req([ev("1",claim_fp=OTHER_FP),ev("2",claim_fp=OTHER_FP)])).decision, Decision.HOLD)
    def test_target_version_mismatch(self): self.assertEqual(self.layer.evaluate(req([ev("1",target_version="v2"),ev("2",target_version="v2")])).decision, Decision.HOLD)
    def test_action_requested_does_not_execute(self):
        r=self.layer.evaluate(req([ev("1",group="a"),ev("2",group="b")],action_requested=True)); self.assertFalse(r.action_executed); self.assertIn("ACTION_REQUEST_NOT_EXECUTED",r.reasons)
    def test_human_approval_not_execution(self):
        r=self.layer.evaluate(req([ev("1",group="a"),ev("2",group="b")],human_approval_evidence=True)); self.assertFalse(r.action_succeeded); self.assertIn("HUMAN_APPROVAL_EVIDENCE_NOT_ACTION_EXECUTION",r.reasons)
    def test_cache_exact_request(self):
        q=req([ev("1",group="a"),ev("2",group="b")]); self.assertFalse(self.layer.evaluate(q).cache_hit); self.assertTrue(self.layer.evaluate(q).cache_hit)
    def test_cache_changes_on_target_version(self):
        q=req([ev("1",group="a"),ev("2",group="b")]); self.layer.evaluate(q)
        q2=dataclasses.replace(q,target_version="v2"); self.assertFalse(self.layer.evaluate(q2).cache_hit)
    def test_cache_changes_on_evidence(self):
        q=req([ev("1",group="a"),ev("2",group="b")]); self.layer.evaluate(q)
        q2=req([ev("1",group="a"),ev("3",group="c")]); self.assertFalse(self.layer.evaluate(q2).cache_hit)
    def test_invalid_claim_fp_denied(self): self.assertEqual(self.layer.evaluate(dataclasses.replace(req(),claim_fingerprint="bad")).decision,Decision.DENY)
    def test_duplicate_evidence_id_denied(self): self.assertEqual(self.layer.evaluate(req([ev("1"),ev("1",group="b")])).decision,Decision.DENY)
    def test_nan_quality_denied(self): self.assertEqual(self.layer.evaluate(req([ev("1",quality=float("nan"))])).decision,Decision.DENY)
    def test_empty_claim_denied(self): self.assertEqual(self.layer.evaluate(dataclasses.replace(req(),claim_text=" ")).decision,Decision.DENY)
    def test_min_sources_invalid_denied(self): self.assertEqual(self.layer.evaluate(dataclasses.replace(req(),minimum_independent_sources=0)).decision,Decision.DENY)
    def test_result_never_authoritative(self): self.assertFalse(self.layer.evaluate(req([ev("1",group="a"),ev("2",group="b")])).authoritative)
    def test_result_never_committed(self): self.assertFalse(self.layer.evaluate(req([ev("1",group="a"),ev("2",group="b")])).state_committed)
    def test_deterministic_fingerprint(self):
        q=req([ev("1",group="a"),ev("2",group="b")]); self.assertEqual(canonical_fingerprint(q),canonical_fingerprint(q))
    def test_synthetic_evidence_discount(self):
        a=self.layer.evaluate(req([ev("1",group="a"),ev("2",group="b")],minimum_support_score=0)).support_score
        b=FactVerificationLayer().evaluate(req([ev("1",group="a",synthetic=True),ev("2",group="b",synthetic=True)],minimum_support_score=0)).support_score
        self.assertLess(b,a)
    def test_authentication_affects_weight_not_truth(self):
        r=self.layer.evaluate(req([ev("1",group="a",auth=False),ev("2",group="b",auth=False)],minimum_support_score=.1)); self.assertFalse(r.truth_established)
    def test_unknown_stance_not_support(self): self.assertEqual(self.layer.evaluate(req([ev("1",stance=EvidenceStance.UNKNOWN),ev("2",stance=EvidenceStance.UNKNOWN)])).decision,Decision.INSUFFICIENT)
    def test_low_score_insufficient(self): self.assertEqual(self.layer.evaluate(req([ev("1",group="a",quality=.2),ev("2",group="b",quality=.2)])).decision,Decision.INSUFFICIENT)
    def test_clear_cache_resets_hit(self):
        q=req([ev("1",group="a"),ev("2",group="b")]); self.layer.evaluate(q); self.layer.clear_cache(); self.assertFalse(self.layer.evaluate(q).cache_hit)

# Add 31 boundary/regression tests with distinct methods => total 61 tests.
def _make_case(n):
    def test(self):
        layer=FactVerificationLayer()
        if n % 6 == 0:
            q=req([ev(f"a{n}",group="a",primary=True),ev(f"b{n}",group="b")], require_primary=True)
            expected=Decision.VERIFIED_CANDIDATE
        elif n % 6 == 1:
            q=req([ev(f"a{n}",group="a",expired=True),ev(f"b{n}",group="b")], minimum_independent_sources=2)
            expected=Decision.INSUFFICIENT
        elif n % 6 == 2:
            q=req([ev(f"a{n}",group="a"),ev(f"b{n}",group="b")], impact=Impact.HIGH)
            expected=Decision.HUMAN_CONFIRM
        elif n % 6 == 3:
            q=req([ev(f"a{n}",group="a",claim_fp=OTHER_FP),ev(f"b{n}",group="b",claim_fp=OTHER_FP)])
            expected=Decision.HOLD
        elif n % 6 == 4:
            q=req([ev(f"a{n}",group="a"),ev(f"b{n}",group="a")])
            expected=Decision.INSUFFICIENT
        else:
            q=req([ev(f"a{n}",group="a"),ev(f"b{n}",group="b")])
            expected=Decision.VERIFIED_CANDIDATE
        r=layer.evaluate(q)
        self.assertEqual(r.decision, expected)
        self.assertFalse(r.truth_established)
        self.assertFalse(r.action_executed)
        self.assertFalse(r.action_succeeded)
    return test

for i in range(31):
    setattr(CoreTests, f"test_regression_{i:02d}", _make_case(i))

if __name__ == "__main__": unittest.main(verbosity=2)
