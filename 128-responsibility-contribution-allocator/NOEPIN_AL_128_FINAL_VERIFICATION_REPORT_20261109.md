# NOEPIN AL 128 — Final Verification Report — 2026-11-09

## Identity

- Technology: 128｜責任寄与度アロケーター
- Canonical ID: `NOEPIN-AL-128`
- English Name: `AL Responsibility Contribution Allocator`
- Creator / Originator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**
- AI-assisted implementation / analysis / documentation support: ChatGPT
- License / Rights: **NOT SPECIFIED**
- Existing V1: **IMMUTABLE / NOT OVERWRITTEN**
- DCSR: **直接統合 / DIRECT INTEGRATION**

## Verification

- Normal compile: PASS
- Normal tests: **160 / 160 PASS**
- Normal replay: **3000 / divergence 0**
- Normal replay digest: `b0d38bf8adf1d81e051a5a5c857c2bc3e68e8ae63a5c8341ff9bd415ef723db8`
- Normal static safety: **external execution paths 0 / unauthorized write paths 0**
- Normal Production Gate: **AL037–127 / 91 / 91 PASS**
- Fresh manifest: **753 / 753 matched**
- Fresh compile: PASS
- Fresh tests: **160 / 160 PASS**
- Fresh replay: **3000 / divergence 0**
- Fresh Production Gate: **AL037–127 / 91 / 91 PASS**
- Fresh static safety: **0 / 0**

## Benchmark

- Condition: Python stdlib; 1200 causal decision/action nodes + 1200 outcome edges across 40 agents; causal path + counterfactual contribution allocation; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches
- Normal: Full **10.2041872001 ms** / Prepared **0.0085462500 ms** / semantic match `true`
- Fresh: Full **5.6278446001 ms** / Prepared **0.0073925000 ms** / semantic match `true`
- DCSR transfer: Full **286,856 bytes** → Delta **399 bytes** / **0.1390941797%**
- Missing-only: **1 changed record / 168 metadata bytes / full resend false**
- Measurements are condition-specific and are not a universal performance guarantee.

## Defect Ledger

- Production defect: **0**
- Test fixture defect: **0**
- Benchmark harness defect: **0**
- Replay helper defect: **0**
- Production Gate helper defect: **0**
- Execution harness invocation defect: **0**

## Semantics / Fail-safe

- Decision/Action DAG and known causal edges are used to trace candidate causal paths to the observed Outcome.
- Counterfactual-removal evidence and path strength are combined as audit evidence; Role weighting distinguishes Action / Approval / Proposal / Review contribution without converting role labels into blame.
- Single critical paths can produce high contribution; redundant parallel contributors distribute contribution rather than forcing a single responsible Agent.
- If causal coverage is insufficient, unknown causal links remain unresolved and the result is HOLD / human-review candidate rather than single-agent responsibility assertion.
- Contribution Scores are audit candidates only and are not automatically connected to punishment, Trust reduction, or Authority restriction.

## Authority Boundary

- Contribution Score ≠ legal/moral responsibility proof / World Truth.
- Critical Contributor Candidate ≠ sole responsible party.
- Attribution Result ≠ Trust Update Execution / Penalty Execution / Authority Restriction Execution.
- Approval contribution ≠ Approval Execution.
- HOLD Candidate ≠ Stop Execution.
- DCSR-reconstructed State does not inherit sender Authority / Intent / Agreement / Permission / Action Success.
- DCSR Reconstruction ≠ Domain Authority / Semantic Judgment / Permission Grant / Safety Proof / Action Execution / Action Success.

## Provenance limitations

- exact registered Origin GUID was not freshly reverified.
- Pre-existing Notion V1 attachment byte identity was not freshly reverified.
