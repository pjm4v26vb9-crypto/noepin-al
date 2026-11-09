# NOEPIN AL 126 — Final Verification Report — 2026-11-09

## Identity

- Technology: 126｜戦略的操作検知器
- Canonical ID: `NOEPIN-AL-126`
- English Name: `AL Strategic Manipulation Detector`
- Creator / Originator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**
- AI-assisted implementation / analysis / documentation support: ChatGPT
- License / Rights: **NOT SPECIFIED**
- Existing V1: **IMMUTABLE / NOT OVERWRITTEN**
- DCSR: **直接統合 / DIRECT INTEGRATION**

## Verification

- Normal compile: PASS
- Normal tests: **160 / 160 PASS**
- Normal replay: **3000 / divergence 0**
- Normal replay digest: `729aa0176264fcf4352c91568a52e4339a468d04c3792881aa33b2d880bbef00`
- Normal static safety: **external execution paths 0 / unauthorized write paths 0**
- Normal Production Gate: **AL037–125 / 89 / 89 PASS**
- Fresh manifest: **703 / 703 matched**
- Fresh compile: PASS
- Fresh tests: **160 / 160 PASS**
- Fresh replay: **3000 / divergence 0**
- Fresh Production Gate: **AL037–125 / 89 / 89 PASS**
- Fresh static safety: **0 / 0**

## Benchmark

- Condition: Python stdlib; 1200 claim/outcome audit records across 24 agents; mismatch + omission + incentive alignment + repetition analysis; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches
- Normal: Full **49.9539202000 ms** / Prepared **0.0126316000 ms** / semantic match `true`
- Fresh: Full **25.9970202000 ms** / Prepared **0.0094499000 ms** / semantic match `true`
- DCSR transfer: Full **429,864 bytes** → Delta **587 bytes** / **0.1365548173%**
- Missing-only: **1 changed record / 169 metadata bytes / full resend false**
- Measurements are condition-specific and are not a universal performance guarantee.

## Defect Ledger

- Production defect: **0**
- Test fixture defect: **0**
- Benchmark harness defect: **0**
- Replay helper defect: **0**
- Production Gate helper defect: **0**
- Execution harness invocation defect: **0**

## Semantics / Fail-safe

- Claim/outcome mismatch is an audit signal, not proof of manipulation or malicious intent.
- Simple non-strategic error is routed to Calibration Candidate rather than manipulation proof.
- Material mismatch aligned with a strong self-interest direction can produce a high-risk restriction candidate.
- Material Evidence omission and repeated mismatch patterns strengthen the risk signal.
- Unverifiable claims do not receive a Truth judgment; vote-weight restriction is a candidate only.
- High-risk outputs propose vote/authority restriction only; they do not execute trust or authority changes.

## Authority Boundary

- Manipulation Risk ≠ malicious-intent proof / World Truth.
- Mismatch Trace ≠ Intent Proof.
- Trust Adjustment Candidate ≠ Trust Update Execution.
- Authority Restriction Candidate ≠ Authority Revocation / Permission Grant.
- Vote Weight Restriction Candidate ≠ Vote-weight execution.
- DCSR-reconstructed State does not inherit sender Authority / Intent / Agreement / Permission / Action Success.
- DCSR Reconstruction ≠ Domain Authority / Semantic Judgment / Permission Grant / Safety Proof / Action Execution / Action Success.

## Provenance limitations

- exact registered Origin GUID was not freshly reverified.
- Pre-existing Notion V1 attachment byte identity was not freshly reverified.
