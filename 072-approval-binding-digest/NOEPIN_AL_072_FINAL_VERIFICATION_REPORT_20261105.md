# NOEPIN AL 072 — Final Verification Report

Technology: **72｜承認束縛ダイジェスト / AL Approval-Binding Digest**  
Canonical ID: `NOEPIN-AL-072`  
Artifact: **Sequential Successor V2**  
Originator / Creator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**  
Implementation / analysis / documentation support: **AI-assisted using ChatGPT**

## Final status

**COMPLETE / VERIFIED — TECHNOLOGY ARTIFACT**, subject only to external Final ZIP SHA-256 sealing and Canonical/Master readback after artifact freeze.

The pre-existing Canonical V1 / complete-download artifact is preserved and was not overwritten. Its byte identity was not freshly reverified in this run. The Provenance declaration is preserved; the exact registered Origin GUID was not freshly re-extracted, so no GUID is invented here.

License / Rights: **NOT SPECIFIED**.

## Implemented semantics

- Approval is canonically bound to Request ID, Actor, Action, Target, Parameters, Policy fingerprint, Nonce, approval scope, intent fingerprint, binding and approval epoch.
- Missing Approval Record → **HUMAN_APPROVAL**.
- Action / Target / Parameters / Policy / Nonce / Scope / Intent / binding / epoch substitution → **DENY** or fail-closed reapproval path.
- Execution-time current Policy fingerprint is externally supplied and must equal the approved Request Policy fingerprint; mismatch → **DENY / reapproval required**; unconfirmed current Policy fingerprint → **HOLD**.
- Approval HMAC-SHA256 evidence must match the exact bound digest and an externally supplied verified, non-revoked, sufficiently sized verifier key.
- Approver Authority and key binding/epoch/capability must be valid and trusted.
- Approval issued before Request creation or with an invalid lifetime → **DENY**.
- Expired Approval → **HOLD / reapproval required**.
- Confirmed single-use Replay by digest or Nonce → **DENY**.
- Unconfirmed Replay state/receipt → **HOLD**.
- Complete verified match → **ALLOW candidate only** and `atomic_publish_candidate=true`; no publish/execute/write is performed.

## Authority boundary

This artifact never performs or proves:

- Human Approval Execution / Approval Issue
- Permission Grant
- Nonce Consumption / Replay Ledger Write
- Tool / Action Execution
- External Send
- Atomic Publish
- World Truth / Safety Proof / Action Success

`ALLOW` = **approval-binding verified next-gate candidate only**.

Human Approval Evidence ≠ Approval Execution. Digest Match ≠ Permission Grant. Request Match ≠ Action Execution. Atomic Publish Candidate ≠ Atomic Publish Performed. Prepared State ≠ Authoritative Current State. DCSR Reconstruction ≠ Domain Authority / Action Success.

## Verification results

### Normal verification

- Compile: **PASS**
- Unit / Boundary / Abnormal / Authority / DCSR: **160 / 160 PASS**
- Replay: **3 × 1,000 = 3,000 / divergence 0**
- Replay digest: `4e4d2ce6bc6f1b571227d3b467e44233c9ebbd238d976a3f5bec8f7d1f951f97`
- Static Safety: external execution paths **0**; unauthorized write paths **0**
- Actual completed NOEPIN AL Production Gate: **AL037–071 actual evaluator execution / 35 of 35 PASS**
- Production Gate execution / permission elevation / write / action-success promotion: **false**

### Provisional ZIP Fresh Extract

- Manifest: **30 entries / PASS**
- Compile: **PASS**
- Tests: **160 / 160 PASS**
- Replay: **3,000 / divergence 0**
- Replay digest matches Normal: **true**
- AL037–071 Production Gate: **35 / 35 PASS**
- Gate semantic identity: **true**
- Gate byte identity: **true**
- Fresh Static Safety: external execution paths **0**; unauthorized write paths **0**
- Fresh Benchmark semantic match: **true**

## DCSR direct integration

Prepared state contains canonical Approval Record, Approver Authority, Verifier Key and Replay Receipt registries with per-record fingerprints and deterministic indexes. One-time integrity validation recomputes fingerprints from actual records. Prepared reuse is accepted only when current Approval-Policy registry identity matches; execution-time bound Policy fingerprint is separately revalidated against the approved Request. Base/target Delta reconstruction and missing-only synchronization are available without granting execution or approval authority.

### Condition-specific benchmark

Python standard library; **1,501 Approval records + 1,502 Authority records + 1,502 verifier-key records; 10 evaluations × 5 batches**.

- Normal Full median: **4.654672 ms**
- Normal Prepared median: **0.905981 ms**
- Semantic match: **true**
- Full state bytes: **1,051,656**
- Delta bytes: **3,617**
- Delta ratio: **0.3439337578%**
- Missing-only sync: **10 Approval records**, metadata **144 bytes**, full resend **false**
- Fresh Full median: **5.469377 ms**
- Fresh Prepared median: **0.928443 ms**

These measurements are condition-specific only and are not a universal speed guarantee.

## Defect classification

- Technology 072 Production defects: **1 CORRECTED**
  - Pre-seal audit found that the Approval bound a Policy fingerprint but the evaluator did not initially require an external execution-time current Policy fingerprint identity check. This could allow an otherwise matching Approval from a prior Policy state to be evaluated without proving that the current Policy identity was unchanged. Corrected to require external current Policy fingerprint confirmation; mismatch is DENY/reapproval, missing identity is HOLD. Full verification rerun.
  - The same correction pass also strengthened minimum verifier-key material length, approval-issued-after-request chronology, strict expiry boundary, and unconfirmed Replay Receipt fail-closed handling.
- Test fixture defects: **1 CORRECTED**
  - The original expiry fixture mutated the bound `expires_at` field, which correctly produced tamper DENY rather than expiry HOLD. Corrected to advance evaluation time without changing Approval bytes; production semantics unchanged.
- Benchmark harness defects: **0**
- Replay helper defects: **0**
- Production Gate helper defects: **0**
- Execution harness invocation defects: **0**

## Artifact freeze rule

The Final ZIP SHA-256 is intentionally external to this frozen report to avoid self-reference. Final ZIP identity is recorded in the external Artifact Seal / Source Index / Canonical Notion / Master Audit after Final ZIP creation and second Fresh Extract verification.