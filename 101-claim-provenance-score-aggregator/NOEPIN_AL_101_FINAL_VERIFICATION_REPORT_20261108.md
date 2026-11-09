# NOEPIN AL 101 — Final Verification Report — 2026-11-08

## Identity

- Technology: **101｜主張由来スコア統合器 / AL Claim Provenance Score Aggregator**
- Canonical ID: `NOEPIN-AL-101`
- Artifact: **Sequential Successor V2**
- Creator / Originator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**
- Implementation / analysis / documentation support: **AI-assisted using ChatGPT**
- License / Rights: **NOT SPECIFIED**
- Core SHA-256: `0ff3ec3d4ff96f0930117df0ae131b0918d4d40f10bc14eeba8fa1318dba4539`

## Canonical behavior implemented

The evaluator walks a Claim provenance DAG backward to Source roots, applies Source Trust and Transform Retention loss, records the Weakest Link, limits scores for broken lineage and untrusted roots, discounts excessive transform chains, and permits a bonus only for multiple independent roots. Important High/Critical claims with broken provenance are HOLD rather than being promoted by averaging. Memory and Mention nodes remain evidence references only: **Memory ≠ Truth** and **Mention ≠ Memory**.

## Authority boundary

- Provenance Score / Trace ≠ World Truth / Safety Proof
- Weakest Link ≠ Domain Authority
- Memory ≠ Truth
- Mention ≠ Memory
- Provenance Reconstruction ≠ new Memory / known fact
- ALLOW Candidate ≠ Permission Grant / Action Execution / Action Success
- Prepared State / Cache ≠ Authoritative Current State
- DCSR Reconstruction ≠ Domain Authority / Safety Proof / Action Execution / Action Success

## Validation

- Normal tests: **160 / 160 PASS**
- Fresh tests: **160 / 160 PASS**
- Normal replay: **3 × 1000 = 3000 / divergence 0**
- Fresh replay: **3 × 1000 = 3000 / divergence 0**
- Replay digest: `4eeae80c11bcc7712a1e19376fd5203291e900a668c5a88036df9269121cdd42`
- Normal Static Safety: **external execution paths 0 / unauthorized write paths 0**
- Fresh Static Safety: **external execution paths 0 / unauthorized write paths 0**
- Fresh Manifest: **153 / 153 files matched**
- Actual completed AL Production Gate: **AL037–100 / 64 of 64 PASS**
- Frozen Fresh Gate Evidence SHA-256: `6d12a3d3ac04a645c3b871162971cc86b6c5014cf968edff5157a47931cff0d9`

## DCSR

DCSR level: **LIMITED INTEGRATION / 限定適用**. Provenance/index/derived representation state is fingerprinted for reuse and missing-only synchronization. Prepared result reuse requires independently validated Prepared integrity and matching precomputed Context + Dependency + Policy + Registry fingerprints; the reuse path does not rehash the full registry. DCSR does not create new memory, facts, Truth, or Authority.

Benchmark condition: Python stdlib; 5000 Source roots + Claim node; provenance DAG aggregation; 10 evaluations x 5 batches; prepared verified-result reuse

- Normal Full median: **8.0435204000 ms**
- Normal Prepared median: **0.0007121000 ms**
- Fresh Full median: **7.2905654000 ms**
- Fresh Prepared median: **0.0007421000 ms**
- Fresh semantic match: **true**
- Full bytes: **1,295,827**
- Delta bytes: **2,683**
- Delta percent: **0.2070492435%**
- Missing-only records: **10**
- Missing metadata bytes: **51**
- Full resend: **false**

Measurements are condition-specific, not a universal performance guarantee.

## Defect classification

- Production defect: **1 CORRECTED**
  - Initial Prepared reuse rehashed the full 5,000-node registry on every reuse, making prepared reuse slower than full evaluation. Corrected so independently validated Prepared integrity plus already-known current fingerprints are used for constant-time candidate reuse. All Normal validation was rerun from the corrected Production state.
- Test fixture defect: **0**
- Benchmark harness defect: **0**
- Replay helper defect: **0**
- Production Gate helper defect: **0**
- Execution harness invocation defect: **1 CORRECTED**
  - The first Fresh Manifest invocation inherited the prior generation's `evidence/FRESH_MANIFEST_VERIFICATION.json` and redirected new output to the same path before validation, truncating that listed file and yielding 159/160. Inherited Fresh evidence was removed from the package target and the Provisional ZIP/Fresh verification was rerun from extraction; Production semantics were unchanged.

## Provenance limitations

- exact registered Origin GUID was not freshly reverified.
- Pre-existing Notion V1 attachment byte identity was not freshly reverified.

## Final ZIP self-reference rule

The Final ZIP SHA-256 is intentionally not embedded inside the ZIP. It is stored externally in the Final Artifact Seal, Source Index, Canonical Notion completion evidence, and Completion Master.
