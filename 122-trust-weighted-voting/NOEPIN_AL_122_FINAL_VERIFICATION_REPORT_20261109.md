# NOEPIN AL 122 — Final Verification Report — 2026-11-09

## Identity
- Technology: 122｜信頼加重投票器
- English Name: AL Trust-Weighted Voting
- Canonical ID: NOEPIN-AL-122
- Artifact: Sequential Successor V2
- Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
- AI support: AI-assisted implementation / analysis / documentation support using ChatGPT
- License / Rights: NOT SPECIFIED
- DCSR: 直接統合 / DIRECT INTEGRATION

## Baseline preservation
Existing Canonical V1 remains immutable and was not overwritten.

## Semantics
Votes are weighted by Trust, Task Expertise, Evidence Quality and Independence. Evidence-missing votes are decayed. High-weight agents in material opposition force HOLD rather than being overridden by simple majority. Weighted consensus and confidence are candidates/evidence only.

## Authority boundary
Consensus != Truth. Confidence != Safety Proof. Weighted Majority != Permission Grant. DCSR received state does not automatically inherit sender authority, intent, agreement, permission, execution authority, or action success.

## Verification
- Compile Normal / Fresh: PASS
- Tests Normal / Fresh: 160 / 160 PASS each
- Replay Normal / Fresh: 3,000 / divergence 0 each
- Replay digest: 6f3ae8dc136f6e0b0844eb13a2c8abe68e0454a9ef051dd8a9e6e069b604c447
- Static Safety Normal / Fresh: external execution paths 0 / unauthorized write paths 0
- AL Production Gate Normal / Fresh: AL037–121 / 85 / 85 PASS each
- Provisional Fresh manifest: 740 / 740 matched

## DCSR benchmark
- Normal: Full 1.8190502 ms / Prepared 0.00523075 ms / semantic match true
- Fresh: Full 1.6051802 ms / Prepared 0.00525530 ms / semantic match true
- Full bytes: 236,857
- Delta bytes: 428
- Delta percentage: 0.1806997471%
- Missing-only: 1 changed vote record / metadata 168 bytes / full resend false
- Condition: Python stdlib; 1200 agent votes; trust/expertise/evidence/independence weighted voting; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches.

## Defect ledger
- Production defect: 0
- Test fixture defect: 0
- Benchmark harness defect: 0
- Replay helper defect: 0
- Production Gate helper defect: 0
- Execution harness invocation defect: 0

## Core
- noepin_al_122_trust_weighted_voting.py
- SHA-256: f6885e0d21cbb36bc520a902c9816e39089d92b20978c7551739892ca69f59f8

## Provenance limitations
- exact registered Origin GUID was not freshly reverified.
- Pre-existing Notion V1 attachment byte identity was not freshly reverified.

Final ZIP SHA-256 is intentionally recorded outside the ZIP in the Artifact Seal / Source Index / Canonical completion evidence to avoid self-reference.
