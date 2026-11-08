# NOEPIN AL 093 — Final Verification Report

## Identity

- Technology: **93｜証拠独立性推定器 / AL Evidence Independence Estimator**
- Canonical ID: `NOEPIN-AL-093`
- Artifact: **Sequential Successor V2**
- Creator / Originator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**
- Implementation / analysis / documentation support: **AI-assisted using ChatGPT**
- License / Rights: **NOT SPECIFIED**
- DCSR: **LIMITED INTEGRATION / 限定適用**

## Canonical semantics implemented

Evidence independence is estimated from provenance signals including source identity, model identity, URL/document identity, content fingerprint, and citation/derivation lineage. Same-origin or lineage-connected evidence is discounted; unknown lineage is conservatively not treated as fully independent. The module produces a pairwise Independence Matrix, provenance clusters, and an Effective Evidence Count.

Authority boundary: independence estimates, clusters, Effective Evidence Count, and prepared/cache state are uncertainty-control evidence only. They are not World Truth, Source Authority, Permission Grant, Safety Proof, Action Execution, or Action Success.

## Validation

- Tests Normal: **160 / 160 PASS**
- Tests Fresh: **160 / 160 PASS**
- Replay Normal / Fresh: **3 × 1000 = 3000 / divergence 0**
- Replay digest: `6970cf73870f060c34efe41417002206d9fc811644837e9affe1cbe52d10e952`
- Fresh Manifest: **90 / 90 matched**
- Static Safety Normal / Fresh: **external execution paths 0 / unauthorized write paths 0**
- Actual AL Production Gate: **AL037–092 / 56 of 56 PASS**
- Core SHA-256: `ee0cddbb2a16a930585e2b47e6cc0d2b4d6af915867e53e1cc25dbd9e9aa7b87`

## Benchmark — condition-specific

Condition: Python stdlib; 500 Evidence records; pairwise provenance independence matrix; 10 evaluations x 5 batches; prepared verified-result reuse

- Normal Full median: **1344.646054 ms**
- Normal Prepared median: **0.008442 ms**
- Fresh Full median: **1342.000229 ms**
- Fresh Prepared median: **0.009113 ms**
- Semantic match: **true**
- Full bytes: **152,673**
- Delta bytes: **3,457**
- Delta percent: **2.2643165458%**
- Missing-only records: **10**
- Missing metadata bytes: **131**
- Full resend required: **false**

Prepared-result reuse is valid only after independently validating Prepared integrity and while current Context + Dependency + Calibration + Registry fingerprints match. Pairwise-matrix cost is O(n²) in the number of Evidence records, so the benchmark is condition-specific and not a universal latency guarantee.

## Defect classification

- Production defect: **0**
- Test fixture defect: **0**
- Benchmark harness defect: **0**
- Replay helper defect: **0**
- Production Gate helper defect: **0**
- Execution harness invocation defect: **0**

## Provenance limitations

- exact registered Origin GUID was not freshly reverified.
- Pre-existing Notion V1 attachment byte identity was not freshly reverified.

## Final-freeze note

This report is frozen inside the Final ZIP after Normal + Fresh validation. Second Fresh Extract validation of that Final ZIP is intentionally recorded externally in the Final Artifact Seal / Source Index so the ZIP does not self-reference its own final SHA-256.
