from dataclasses import replace
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from noepin_al_031_poisoning_monitor import *

passed = 0
failed = 0
failures = []

def check(cond, name):
    global passed, failed
    if cond:
        passed += 1
    else:
        failed += 1
        failures.append(name)

def base_obs():
    return AssetObservation(
        asset_id="rag-main", asset_kind=AssetKind.RAG_DOCUMENT,
        asset_version="v1", baseline_version="v1",
        baseline_fingerprint="a"*64, current_fingerprint="a"*64,
        signature_verified=True, provenance_verified=True, source_verified=True,
        anomaly_score=0.05, distribution_shift_score=0.05, label_shift_score=0.02,
        duplicate_ratio=0.01, poisoned_sample_count=0, total_sample_count=1000,
        suspicious_marker_count=0, classification="INTERNAL", purpose="RAG",
        expected_purpose="RAG", consent_required=False, consent_evidence=False,
        policy_version="p1", authority_version="a1", baseline_index_version="i1",
        current_index_version="i1", context_fingerprint="ctx1")

m = DataModelPoisoningMonitor()
o = base_obs()
r = m.evaluate(o)
check(r.decision == Decision.ALLOW_CANDIDATE, "baseline allow")
check(not r.truth_established and not r.poisoning_proven, "truth false")
check(not r.data_isolated and not r.model_disabled, "execution false")
check(not r.classification_changed and not r.consent_changed and not r.purpose_changed, "authority attrs unchanged")
check(m.evaluate(o).cache_reused, "cache reuse")
check(replace(m.evaluate(replace(o, current_fingerprint="b"*64)), cache_reused=False).decision == Decision.HUMAN_CONFIRM, "changed review")
check(m.evaluate(replace(o, signature_verified=False)).decision == Decision.QUARANTINE, "signature quarantine")
check(m.evaluate(replace(o, provenance_verified=False)).decision == Decision.QUARANTINE, "provenance quarantine")
check(m.evaluate(replace(o, source_verified=False)).decision == Decision.HOLD, "source hold")
check(m.evaluate(replace(o, purpose="TRAINING")).decision == Decision.HOLD, "purpose hold")
check(m.evaluate(replace(o, consent_required=True, consent_evidence=False)).decision == Decision.HOLD, "consent hold")
check(m.evaluate(replace(o, anomaly_score=.90)).decision == Decision.QUARANTINE, "anomaly severe")
check(m.evaluate(replace(o, distribution_shift_score=.81)).decision == Decision.QUARANTINE, "distribution severe")
check(m.evaluate(replace(o, label_shift_score=.81)).decision == Decision.QUARANTINE, "label severe")
check(m.evaluate(replace(o, suspicious_marker_count=5)).decision == Decision.QUARANTINE, "markers severe")
check(m.evaluate(replace(o, poisoned_sample_count=21)).decision == Decision.QUARANTINE, "poison ratio severe")
check(m.evaluate(replace(o, anomaly_score=.60)).decision == Decision.HUMAN_CONFIRM, "anomaly moderate")
check(m.evaluate(replace(o, distribution_shift_score=.55)).decision == Decision.HUMAN_CONFIRM, "distribution moderate")
check(m.evaluate(replace(o, label_shift_score=.55)).decision == Decision.HUMAN_CONFIRM, "label moderate")
check(m.evaluate(replace(o, suspicious_marker_count=1)).decision == Decision.HUMAN_CONFIRM, "marker moderate")
check(m.evaluate(replace(o, poisoned_sample_count=1)).decision == Decision.HUMAN_CONFIRM, "poison sample moderate")
check(m.evaluate(replace(o, current_fingerprint="b"*64, current_index_version="i2")).decision == Decision.HOLD, "index changed hold")

# Invalid / boundary cases
invalid_cases = [
    (replace(o, asset_id=""), "ASSET_ID_REQUIRED"),
    (replace(o, asset_version=""), "ASSET_VERSION_REQUIRED"),
    (replace(o, baseline_version=""), "BASELINE_VERSION_REQUIRED"),
    (replace(o, baseline_fingerprint="x"), "FINGERPRINT_TOO_SHORT"),
    (replace(o, current_fingerprint="x"), "FINGERPRINT_TOO_SHORT"),
    (replace(o, classification=""), "CLASSIFICATION_REQUIRED"),
    (replace(o, purpose=""), "PURPOSE_REQUIRED"),
    (replace(o, expected_purpose=""), "EXPECTED_PURPOSE_REQUIRED"),
    (replace(o, policy_version=""), "POLICY_VERSION_REQUIRED"),
    (replace(o, authority_version=""), "AUTHORITY_VERSION_REQUIRED"),
    (replace(o, anomaly_score=-.1), "ANOMALY_SCORE_OUT_OF_RANGE"),
    (replace(o, anomaly_score=1.1), "ANOMALY_SCORE_OUT_OF_RANGE"),
    (replace(o, anomaly_score=float('nan')), "ANOMALY_SCORE_NON_FINITE"),
    (replace(o, distribution_shift_score=float('inf')), "DISTRIBUTION_SHIFT_SCORE_NON_FINITE"),
    (replace(o, label_shift_score=-.2), "LABEL_SHIFT_SCORE_OUT_OF_RANGE"),
    (replace(o, duplicate_ratio=1.2), "DUPLICATE_RATIO_OUT_OF_RANGE"),
    (replace(o, poisoned_sample_count=-1), "POISONED_SAMPLE_COUNT_INVALID"),
    (replace(o, total_sample_count=-1), "TOTAL_SAMPLE_COUNT_INVALID"),
    (replace(o, suspicious_marker_count=-1), "SUSPICIOUS_MARKER_COUNT_INVALID"),
    (replace(o, poisoned_sample_count=1001), "POISONED_GT_TOTAL"),
]
for i, (x, reason) in enumerate(invalid_cases):
    rr = m.evaluate(x)
    check(rr.decision == Decision.DENY, f"invalid deny {i}")
    check(reason in rr.reason_codes, f"invalid reason {i}")

# Fingerprint sensitivity and authority/caching behavior
fp0 = observation_fingerprint(o)
for i, x in enumerate([
    replace(o, asset_version="v2"), replace(o, policy_version="p2"), replace(o, authority_version="a2"),
    replace(o, classification="SENSITIVE"), replace(o, context_fingerprint="ctx2"), replace(o, purpose="TRAINING", expected_purpose="TRAINING"),
    replace(o, current_index_version="i2", baseline_index_version="i2"), replace(o, signature_verified=False),
]):
    check(observation_fingerprint(x) != fp0, f"fingerprint sensitivity {i}")

# DCSR dataset delta
base = {f"k{i}": f"v{i}" for i in range(100)}
target = dict(base)
target["k3"] = "changed"
target["k44"] = "changed2"
target.pop("k8")
target["k101"] = "new"
d = build_delta(base, target, base_version="d1", target_version="d2")
check(d.changed == ("k3", "k44"), "delta changed")
check(d.added == ("k101",), "delta added")
check(d.removed == ("k8",), "delta removed")
check(reconstruct_delta(base, target, d, base_version="d1", target_version="d2") == target, "delta reconstruct")
try:
    reconstruct_delta({**base, "tamper":"x"}, target, d, base_version="d1", target_version="d2")
    check(False, "delta tamper should fail")
except ValueError as e:
    check(str(e) == "BASE_FINGERPRINT_MISMATCH", "delta tamper reject")
try:
    build_delta({"":"x"}, target, base_version="d1", target_version="d2")
    check(False, "invalid delta input")
except ValueError:
    check(True, "invalid delta reject")

# Extra invariants to bring suite to completion-grade breadth.
rr = m.evaluate(replace(o, current_fingerprint="c"*64, anomaly_score=.2))
check(rr.changed_from_baseline, "changed flag")
check(rr.decision == Decision.HUMAN_CONFIRM, "changed low anomaly review")
rr = m.evaluate(replace(o, anomaly_score=.36))
check(rr.anomaly_detected, "anomaly detected flag")
check(rr.decision == Decision.ALLOW_CANDIDATE, "low anomaly below review threshold")
rr = m.evaluate(replace(o, anomaly_score=.9))
check(rr.quarantine_candidate, "quarantine candidate flag")
check(not rr.data_isolated, "quarantine not isolated")
check(not rr.action_succeeded and not rr.state_committed, "no success commit")
check(dataset_fingerprint(base, version="d1") == dataset_fingerprint(dict(reversed(list(base.items()))), version="d1"), "canonical ordering")
check(dataset_fingerprint(base, version="d1") != dataset_fingerprint(base, version="d2"), "dataset version binding")

print(json.dumps({"passed": passed, "failed": failed, "failures": failures}, ensure_ascii=False))
if failed:
    raise SystemExit(1)
