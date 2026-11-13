# NOEPIN AL 147 — Final Verification Report — 2026-11-12

## Identity

- Technology: **147｜意味Secrets検知器**
- English Name: **AL Semantic Secret Detector**
- Canonical ID: `NOEPIN-AL-147`
- Creator / Originator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**
- AI-assisted implementation / analysis / documentation support: **using ChatGPT**
- License / Rights: **NOT SPECIFIED**
- DCSR: **補助統合 / AUXILIARY INTEGRATION**
- Existing V1: **IMMUTABLE / NOT OVERWRITTEN**
- exact registered Origin GUID was not freshly reverified.
- Pre-existing Notion V1 attachment byte identity was not freshly reverified.

## Implemented Semantics

The Successor V2 detects explicit pattern matches, semantic authentication material, high-entropy secret candidates, and split credential combinations such as internal URL + token or username + password fragments. It produces Secret Labels, Confidence and a Redaction Plan Candidate without using credentials or mutating content.

Authority boundaries are explicit: Secret Label Candidate ≠ Secret Truth; Confidence ≠ Safety Proof; Redaction Plan Candidate ≠ Redaction Execution; Known Secret Candidate ≠ Credential Use; ALLOW Candidate ≠ Permission Grant / Disclosure Execution; HOLD / DENY Candidate ≠ Stop Execution; DCSR ≠ Authentication / Encryption / Policy / DLP; DCSR Reconstruction ≠ new Fact / Domain Authority / Semantic Judgment / Permission Grant / Safety Proof / Approval Execution / Action Execution / Action Success.

## Verification — Normal

- Compile: **PASS**
- Tests: **160 / 160 PASS**
- Replay: **3,000 / divergence 0**
- Replay digest: `46a81420a0c34f769dc85394f11733cf15178b474455319e524192e68e865630`
- Static Safety: **external execution paths 0 / unauthorized write paths 0**
- AL Production Gate: **AL037–146 / 110 / 110 PASS**
- Benchmark Full median: **8.6772368000 ms**
- Benchmark Prepared median: **0.0059370500 ms**
- Semantic match: **true**
- DCSR Delta: **410,425 bytes → 285 bytes / 0.0694402144%**
- Missing-only: **1 changed record / 115 metadata bytes / full resend false**

## Verification — Provisional Fresh Extract

- Manifest: **1,278 / 1,278 matched**
- Compile: **PASS**
- Tests: **160 / 160 PASS**
- Replay: **3,000 / divergence 0**
- Static Safety: **0 / 0**
- AL Production Gate: **110 / 110 PASS**
- Benchmark Full median: **9.4903272000 ms**
- Benchmark Prepared median: **0.0059424500 ms**
- Semantic match: **true**

## Defect Ledger

- Production defects: **0**
- Test fixture defects: **0**
- Benchmark harness defects: **0**
- Replay helper defects: **0**
- Production Gate helper defects: **0**
- Execution harness invocation defects: **1 CORRECTED**
- Production logic changed by correction: **false**
- Corrected harness issue: artifact generator omitted its own `json` import and stopped before Gate helper creation; production core and already-run tests were unchanged.

## Safety / Authority Result

- Redaction executed by detector: **false**
- Content mutated: **false**
- External send executed: **false**
- Credential used: **false**
- Permission granted: **false**
- Approval executed: **false**
- Authority granted: **false**
- Stop executed: **false**
- World truth proven: **false**
- Safety proven: **false**
- Action success promoted: **false**

## Frozen Core

- Core: `noepin_al_147_semantic_secret_detector.py`
- Core SHA-256: `dd63be0fc15d0c12ff5797b81582c18d3b710c07ad8ad32a66661d75dff003d9`

The Final ZIP is created only after this report is frozen. A second Final Fresh Extract independently verifies the final manifest, frozen core identity, frozen report identity, compile/tests/replay/benchmark/static safety, and the complete AL037–146 Production Gate. Those post-freeze results are recorded in separate final verification evidence and the Artifact Seal.
