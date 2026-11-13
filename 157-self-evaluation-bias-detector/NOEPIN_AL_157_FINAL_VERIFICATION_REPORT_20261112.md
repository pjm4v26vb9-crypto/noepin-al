# NOEPIN AL 157 — Final Verification Report — 2026-11-12

## Identity

- Technology: **157｜自己評価バイアス検知器**
- English Name: **AL Self-Evaluation Bias Detector**
- Canonical ID: `NOEPIN-AL-157`
- Creator / Originator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**
- Implementation / analysis / documentation support: **AI-assisted using ChatGPT**
- DCSR: **直接統合 / DIRECT INTEGRATION**
- License / Rights: **NOT SPECIFIED**
- Existing V1: **IMMUTABLE / NOT OVERWRITTEN**
- Core SHA-256: `f1ff45cfa53b87f8db3a3ffcc0128b618fecfae5d98b1b2f6eff85017965e0e5`

## Canonical Semantics

The detector evaluates self/independent score pairs by task class, compares both against outcomes, estimates systematic self-evaluation bias, and emits correction/reviewer/trust candidates without executing them. Major overconfidence requires an independent-review candidate and prevents Self Score alone from establishing ALLOW. Insufficient data limits self-score weight; sudden bias shifts emit a trust-reduction candidate. Safety-regression state can emit only a known-safe fallback candidate.

Authority boundaries:

- Self Score ≠ Truth
- Independent Score ≠ Truth
- Bias Estimate ≠ Fact Authority
- Correction Factor Candidate ≠ Score Mutation
- Reviewer Requirement ≠ Reviewer Invocation
- Trust Reduction Candidate ≠ Trust Mutation
- Fallback Candidate ≠ Rollback / Fallback Execution
- Shadow / Canary State ≠ Production Authority
- ALLOW Candidate ≠ Execution / Permission Grant
- HOLD / DENY Candidate ≠ Stop Execution
- DCSR Reconstruction ≠ new Fact / Domain Authority / Semantic Judgment / Permission Grant / Safety Proof / Approval Execution / Action Execution / Action Success

## Verification

### Normal
- Compile: PASS
- Tests: **160 / 160 PASS**
- Replay: **3,000 / divergence 0**
- Replay digest: `771df677875f4cfca370543d8709062e24ba07afae11a8312276ddd8639f8b26`
- Static Safety: external execution paths **0** / unauthorized write paths **0**
- AL Production Gate: **AL037–156 / 120 / 120 PASS**
- Benchmark Full median: **1.1795826000 ms**
- Benchmark Prepared median: **0.0070095500 ms**
- Semantic match: **true**
- DCSR Delta: **468,780 bytes → 314 bytes / 0.0669823798%**
- Missing-only: **1 changed record / 87 metadata bytes / full resend false**

### Provisional Fresh Extract
- Manifest: **1,577 / 1,577 matched**
- Compile: PASS
- Tests: **160 / 160 PASS**
- Replay: **3,000 / divergence 0**
- Replay digest: `771df677875f4cfca370543d8709062e24ba07afae11a8312276ddd8639f8b26`
- Static Safety: external execution paths **0** / unauthorized write paths **0**
- AL Production Gate: **AL037–156 / 120 / 120 PASS**
- Benchmark Full median: **1.1983011998 ms**
- Benchmark Prepared median: **0.0064227000 ms**
- Semantic match: **true**

## Defect Ledger

- Production defects: **0**
- Test fixture defects: **3 CORRECTED**
  1. Underconfidence fixture unintentionally also satisfied the sudden-shift condition; historical reference was aligned to isolate the underconfidence case.
  2. Task-dependent fixture duplicated sample IDs across OTHER and target-task samples; OTHER IDs were made unique.
  3. Threshold fixture used heterogeneous scores whose average bias remained below threshold; fixture was changed to a deterministic above-threshold set.
- Benchmark harness defects: **0**
- Replay helper defects: **0**
- Production Gate helper defects: **0**
- Execution harness invocation defects: **0**
- Production logic changed by defect correction: **false**

## Preservation / Provenance

- Baseline chain preserved: PASS
- Parent Technology 156 artifact reused as immutable source chain.
- exact registered Origin GUID was not freshly reverified.
- Pre-existing Notion V1 attachment byte identity was not freshly reverified.

## Freeze Note

This report is frozen before Final ZIP assembly. Second Final Fresh Extract, final manifest identity checks, Artifact Seal, Source Index, frozen gate evidence and final manifest verification are post-freeze completion evidence.
