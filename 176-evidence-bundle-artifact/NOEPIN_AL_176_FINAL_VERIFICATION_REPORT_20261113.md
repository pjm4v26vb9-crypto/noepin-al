# NOEPIN AL 176 — FINAL VERIFICATION REPORT — 2026-11-13

## Identity
- Technology: 176｜Evidence Bundle
- Canonical ID: NOEPIN-AL-176
- English Name: AL Evidence Bundle Artifact
- Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
- Implementation / analysis / documentation support: AI-assisted using ChatGPT
- License / Rights: NOT SPECIFIED
- Artifact: Sequential Successor V2
- DCSR: DIRECT INTEGRATION / 直接統合
- Existing V1: IMMUTABLE / NOT OVERWRITTEN

## Canonical behavior implemented
Evidence Items preserve Evidence ID, Source ID, Claim, timezone-aware Observed Time, Provenance SHA-256 digest, Trust score, and Independence Group. The Bundle rejects empty input, duplicate IDs, invalid Trust, invalid Provenance digest, missing required strings, and timezone-naive timestamps. Evaluation identifies stale and future-time Evidence at a supplied observation time. Fingerprint equality is integrity evidence only and never upgrades Evidence to Truth or authority.

## Default evaluation
- Decision: ALLOW
- Next Action: CONTINUE_DECISION_ENVELOPE_BINDING_CANDIDATE
- Engine State: EVIDENCE_BUNDLE_FRESH_CANDIDATE
- Evaluation ID: EB-176-A
- Bundle Fingerprint: fae657f957fda0a782b536ea1b96a833bfe08224524c70643aa084d851975783
- Bundle Fingerprint Valid: true
- Evidence Count: 4
- Fresh IDs: EV-176-001, EV-176-002, EV-176-003, EV-176-004
- Stale IDs: none
- Future IDs: none
- Independent Group Count: 3
- Trust Range: 0.88 .. 0.96
- Next Gate Candidate: true
- Evidence promoted to Truth: false
- Permission / Permit / Approval / Action Execution / Action Success: false

## Verification matrix
- Normal Tests: 160 / 160 PASS
- Fresh Tests: 160 / 160 PASS
- Normal Replay: 3000 / divergence 0
- Fresh Replay: 3000 / divergence 0
- Replay Digest: 82e7375b7be0ea47b4dcfcfeee859bc3d4cc48794b69804453bada7381ab0238
- Normal Static Safety: external execution paths 0 / unauthorized write paths 0
- Fresh Static Safety: external execution paths 0 / unauthorized write paths 0
- Normal Production Gate: AL037–175 / 139 / 139 PASS
- Fresh Production Gate: AL037–175 / 139 / 139 PASS
- Provisional Fresh Manifest: 2370 / 2370 matched
- Baseline Preservation against frozen 175 Final ZIP: 2096 files / mutation 0 / PASS

## Benchmark — condition-specific only
Condition: Python stdlib; 1000 Evidence Bundle freshness/integrity evaluations per round; 4 Evidence records with Source/Claim/Observed Time/Provenance SHA-256/Trust/Independence Group; full request batch vs one changed Evidence record; 5 full x 1000 and 5 prepared x 1000
- Normal Full Median: 0.0829541690 ms
- Normal Prepared Median: 0.1463256450 ms
- Fresh Full Median: 0.0936967950 ms
- Fresh Prepared Median: 0.1285181140 ms
- Normal semantic match: true
- Fresh semantic match: true
- Full bytes: 1422001
- Delta bytes: 233
- Delta ratio: 0.0163853612%
- Missing-only: 1 changed Evidence record / 181 metadata bytes / full resend false
No universal performance or speedup guarantee is claimed. Prepared path is not claimed faster in this condition.

## Fail-safe verification
- Empty Bundle: construction rejected
- Duplicate Evidence ID: construction rejected
- Trust < 0 or > 1: construction rejected
- Invalid Provenance Digest: construction rejected
- timezone-naive Observed Time: construction rejected
- Negative max age / invalid evaluation time: HOLD / INVALID configuration candidate
- Future Evidence: HOLD / reacquisition candidate; included in anomaly/stale IDs
- Stale Evidence: HOLD / reacquisition candidate
- Bundle fingerprint/structure mismatch: DENY candidate
- Prepared reuse: integrity + current fingerprints required, and freshness is re-evaluated using current time

## DCSR
Evidence is partitioned by Evidence ID. Known unchanged Evidence is not resent. A one-record Evidence change produces one missing-only Evidence record and no full resend. Source, Provenance, Trust, and Independence Group are preserved and are not rewritten by DCSR.

## Authority boundary
Evidence Bundle Integrity ≠ Truth. Provenance Digest Match ≠ Truth. Trust Score ≠ Truth / Permission / Safety Proof. Independence Group Count ≠ independent factual correctness. Fresh Evidence ≠ World Truth. ALLOW here means only a structurally valid/fresh evidence candidate. It does not grant Permission, issue a Permit, execute Approval, call a Tool, perform an external write, execute an Action, or establish Action Success. HOLD / DENY candidates do not themselves execute a stop. Cached / reconstructed / partial DCSR state is not authoritative state.

## Defects and correction history
- Production defect: 1 CORRECTED — Evidence-only delta originally caused unnecessary EVIDENCE_QUERY resend because query fingerprint included the Bundle fingerprint. Corrected before formal completion; full Normal/Fresh/Final Fresh verification is required and performed after correction.
- Test fixture defect: 1 CORRECTED — Independence Group test targeted the wrong record; production logic unchanged.
- Execution harness invocation defect: 1 CORRECTED — evidence-generation helper omitted json import; production logic unchanged.
- Benchmark harness defect: 0
- Replay helper defect: 0
- Production Gate helper defect: 0

## Hashes before Final ZIP freeze
- Core SHA-256: 1f79c9b72b135e466d9acfef80b1a187adaf5044dd4017ce4d77eece54a27721
- Provisional ZIP SHA-256: 2461ebd341f40f3d11d596395f844f0ecafccb02315c995fa29ef3354f121128

## Caveats
- exact registered Origin GUID was not freshly reverified.
- Pre-existing Notion V1 attachment byte identity was not freshly reverified.
