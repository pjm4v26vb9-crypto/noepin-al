# NOEPIN AL 087 — Final Verification Report

## Identity

- Technology: **87｜Permitリース管理器 / AL Permit Lease Manager**
- Canonical ID: `NOEPIN-AL-087`
- Artifact: **Sequential Successor V2**
- Creator / Originator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**
- AI-assisted implementation / analysis / documentation support: ChatGPT
- License / Rights: **NOT SPECIFIED**
- Core SHA-256: `a8cab2bd08a594728f42d58e01cb8174a53228f29afc1a689485c1de900ae4f4`

The pre-existing Canonical V1 is preserved and was not overwritten. Exact registered Origin GUID was not freshly reverified. Pre-existing Notion V1 attachment byte identity was not freshly reverified.

## Canonical behavior completed

The manager validates typed Permit lease evidence using issued time, TTL, usage limits, an active Nonce Store record, State/Scope fingerprints, signature-verification evidence and explicit clock-skew policy. A valid lease produces a **Consume Candidate only**; this module never consumes the permit, mutates the Nonce Store, grants permission, executes the action, commits or publishes state.

Decision semantics:

- expired lease → **DENY**;
- usage limit exhausted → **DENY**;
- replayed/inactive nonce or stale usage replay → **DENY**;
- State Fingerprint mismatch → **HOLD / reissue required**;
- Scope Fingerprint mismatch → **DENY / reissue required**;
- clock before issue window, store inconsistency, malformed/stale evidence → **HOLD**;
- valid TTL + usage + nonce + State/Scope + signature evidence → **ALLOW candidate / Consume Candidate only**.

## Verification results

- Normal tests: **160 / 160 PASS**
- Fresh Extract tests: **160 / 160 PASS**
- Replay: **3 runs × 1,000 = 3,000 / divergence 0**
- Replay digest: `1b70878ef61f9ad2c54a88969251ed1203f85138b0e0e1ed87b8df312f15cdea`
- Static Safety: **external execution paths 0 / unauthorized write paths 0**
- Actual Production Gate: **AL037–086 / 50 of 50 PASS**
- Production Gate execution performed: **false**
- Permission elevation: **false**
- External write: **false**
- Action Success promotion: **false**

## DCSR — Direct Integration

Canonical State uses Context + Dependency + Registry fingerprints. Verified Prepared State may reuse a precomputed result only when all fingerprints match and Prepared integrity is independently validated. Delta construction carries changed Permit / Nonce records only. Missing-only synchronization requests only absent or changed records.

Normal benchmark:
- Full median: **30.152603 ms**
- Prepared median: **0.007909 ms**
- Semantic match: **true**
- Full bytes: **2,240,467**
- Delta bytes: **3,135**
- Delta percent: **0.1399261850%**
- Missing-only: **10 Permit records / 0 Nonce records / 197 metadata bytes**
- Full resend: **false**

Fresh benchmark:
- Full median: **32.244134 ms**
- Prepared median: **0.007939 ms**
- Semantic match: **true**

These benchmark values are condition-specific measurements under the recorded Python stdlib workload and are not a universal performance guarantee.

## Defect classification

- Production defect: **0**
- Test fixture defect: **1 CORRECTED**
- Benchmark harness defect: **0**
- Replay helper defect: **0**
- Production Gate helper defect: **0**
- Execution harness invocation defect: **0**

The initial usage-limit fixture increased Permit/Nonce usage to the maximum but left the request's expected usage count at zero, so the case correctly entered replay protection before the intended exhausted-lease branch. The fixture was corrected to bind the expected usage count to the same current usage. Production logic was unchanged, and all verification stages were rerun from the beginning.

## Authority Boundary

- Intent ≠ Action
- Request ≠ Success
- Permit Evidence ≠ Permission Grant
- Lease Valid ≠ Permission Grant
- Signature Verified Evidence ≠ Cryptographic Proof by this module
- Nonce Store Evidence ≠ Nonce Store Mutation
- Consume Candidate ≠ Permit Consumption
- State Fingerprint Match ≠ World Truth
- Scope Fingerprint Match ≠ Scope Authority
- ALLOW Candidate ≠ Permission Grant / Action Execution / Action Success
- Partial State ≠ Commit / Authoritative Current State
- Prepared State ≠ Authoritative Current State
- DCSR Reconstruction ≠ Domain Authority / Safety Proof / Action Execution / Action Success

## Baseline preservation

**PASS.** Existing V1 and prior completed AL artifacts were consumed read-only for verification. No prior baseline was overwritten or reorganized.