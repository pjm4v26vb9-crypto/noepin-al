# NOEPIN AL 096 — Final Verification Report — 2026-11-08

## Identity

- Technology: **96｜情報鮮度減衰器 / AL Source Freshness Decay**
- Canonical ID: `NOEPIN-AL-096`
- Artifact: **Sequential Successor V2**
- Creator / Originator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**
- Implementation / analysis / documentation support: **AI-assisted using ChatGPT**
- License / Rights: **NOT SPECIFIED**
- DCSR: **LIMITED INTEGRATION / 限定適用**
- Core SHA-256: `4770146a624387749b696859dfdf550510753e2287aa07bf4b08c560500cf04d`

## Canonical behavior implemented

Source freshness is evaluated from policy-defined source half-life, volatility class, elapsed time, and action risk. Updated/verified evidence resets freshness. Unknown timestamps are conservatively scored; unknown timestamps on HIGH/UNKNOWN volatility sources fail-safe to HOLD. Risk-specific freshness thresholds produce Freshness Score, Expired Flag, Refresh Priority and re-evaluation/refresh candidates.

Authority boundary: Freshness Score / cache ≠ Truth or Authority; Expired Flag ≠ World State proof; Refresh Candidate ≠ Refresh Execution; ALLOW Candidate ≠ Permission Grant / Action Execution / Action Success; Prepared State ≠ Authoritative Current State; DCSR Reconstruction ≠ Domain Authority / Safety Proof / Action Execution / Action Success.

## Validation

- Normal tests: **160 / 160 PASS**
- Fresh Extract tests: **160 / 160 PASS**
- Replay Normal/Fresh: **3 × 1000 = 3000**, divergence **0**
- Replay digest: `ebf8e30656f69138ed733426ecb7d17fb301f9a0cc32e19796576b5c31716903`
- Static Safety Normal/Fresh: external execution paths **0**, unauthorized write paths **0**
- Actual AL Production Gate: **AL037–095 / 59 of 59 PASS**
- Production defect: **0**
- Test fixture defect: **0**
- Benchmark harness defect: **0**
- Replay helper defect: **0**
- Production Gate helper defect: **0**
- Execution harness invocation defect: **0**

## DCSR benchmark — condition-specific

Condition: `Python stdlib; 5000 Source freshness records; 10 evaluations x 5 batches; prepared verified-result reuse`

- Normal full median: **1.207883400 ms**
- Normal prepared median: **0.000172200 ms**
- Fresh full median: **1.199897000 ms**
- Fresh prepared median: **0.000167300 ms**
- Full bytes: **1,356,219**
- Delta bytes: **3,125**
- Delta percent: **0.2304200133%**
- Missing-only records: **10**
- Missing-only metadata bytes: **489**
- Full resend required: **false**
- Semantic match: **true**

Prepared-result reuse is valid only after Prepared integrity is independently validated and while Context + Dependency + Calibration + Registry fingerprints match. Measurements are condition-specific and are not a universal performance guarantee.

## Baseline / provenance limitations

- Pre-existing Canonical V1 remains immutable and was not overwritten.
- Pre-existing Notion V1 attachment byte identity was not freshly reverified.
- exact registered Origin GUID was not freshly reverified.
- Final ZIP SHA-256 is intentionally stored externally after ZIP freeze; it is not embedded into the ZIP itself.

## Status

**COMPLETE / VERIFIED — pending only second Fresh Extract verification of the frozen Final ZIP, external Artifact Seal / Source Index, and Canonical/Master readback.**
