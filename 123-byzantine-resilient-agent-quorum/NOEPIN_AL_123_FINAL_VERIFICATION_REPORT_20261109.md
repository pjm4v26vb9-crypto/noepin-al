# NOEPIN AL 123 — FINAL VERIFICATION REPORT — 2026-11-09

## Technology
- 123｜ビザンチン耐性Agentクォーラム
- English: AL Byzantine-Resilient Agent Quorum
- Canonical ID: NOEPIN-AL-123
- Sequential artifact: Successor V2
- Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
- AI-assisted implementation / analysis / documentation support: ChatGPT
- License / Rights: NOT SPECIFIED

## Baseline preservation
- Existing V1 / Canonical attachment: IMMUTABLE / NOT OVERWRITTEN
- exact registered Origin GUID was not freshly reverified.
- Pre-existing Notion V1 attachment byte identity was not freshly reverified.

## Core semantics
- Agent decisions are classified by independent Trust Domain.
- Fault Bound f determines the independent decision quorum threshold as 2f+1.
- Invalid-signature evidence is excluded and recorded as a Fault Suspect.
- Multiple Agents from the same Trust Domain cannot inflate the independent quorum count.
- Same-domain equivocation excludes that domain from quorum and creates a Fault Suspect.
- Required independent quorum not met => HOLD.
- Quorum decision is a candidate only; Quorum != Truth and Quorum satisfaction != Permission Grant / Action Execution / Action Success.
- Received DCSR State never automatically inherits sender Authority / Intent / Agreement / Permission / Action Success.

## Verification
- Normal tests: 160 / 160 PASS
- Fresh tests: 160 / 160 PASS
- Replay: 3,000 iterations / divergence 0
- Replay digest: 48eb80a0dce1bde2148568d286d3a43019a873d1e43d5cff4d979228f48a3289
- Static Safety Normal/Fresh: external execution paths 0 / unauthorized write paths 0
- Production Gate Normal/Fresh: AL037–122 / 86 / 86 PASS
- Fresh Manifest: 620 / 620 matched

## DCSR direct integration
- Full serialized request: 249,944 bytes
- Delta: 446 bytes
- Delta ratio: 0.1784399706%
- Missing-only records: 1
- Missing-only metadata: 172 bytes
- Full resend required: false
- Prepared reuse requires independent integrity validation and exact matching Context + Decision + Policy + Outcome fingerprints.

## Benchmark
- Normal Full median: 1.1277616000 ms
- Normal Prepared median: 0.0052648000 ms
- Fresh Full median: 1.0066616000 ms
- Fresh Prepared median: 0.0052507500 ms
- Semantic match: true
- Condition: Python stdlib; 1200 agent decisions across 400 trust domains; Byzantine-style 2f+1 independent-domain quorum with signature evidence and domain deduplication; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches
- Measurements are condition-specific and are not a universal performance guarantee.

## Defect ledger
- Production defect: 0
- Test fixture defect: 0
- Benchmark harness defect: 0
- Replay helper defect: 0
- Production Gate helper defect: 0
- Execution harness invocation defect: 1 CORRECTED
- Correction: initial Production Gate invocation searched only the work root for AL037; the existing completed legacy cores reside under gate_inputs/cores. Path resolution was corrected and the full 86-evaluator Gate was rerun from the beginning.

## Identity anchor
- Core SHA-256: `f509ea016f19d1d8c3b1a1d330383dda85be28bf06d6e61a69996f7e68b6f867`

## Result
COMPLETE / VERIFIED candidate pending Final ZIP second Fresh verification, identity freeze, Artifact Seal, Source Index, Canonical readback, and Completion Master readback.
