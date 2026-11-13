# NOEPIN AL 143 — Final Verification Report — 2026-11-12

## Identity

- Technology: 143｜目的制限フロー検査器
- English Name: AL Purpose-Limitation Flow Checker
- Canonical ID: NOEPIN-AL-143
- Artifact: Sequential Successor V2
- Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
- AI support: AI-assisted implementation / analysis / documentation support using ChatGPT
- License / Rights: NOT SPECIFIED
- DCSR: AUXILIARY INTEGRATION / 補助統合

## Canonical semantics implemented

- Data取得時のallowed-purpose tagとCurrent Purposeを正規化し、exact match / hierarchical inclusionを評価する。
- 明示Consent evidenceまたはPolicy exception evidenceがCurrent Purposeを覆う場合だけ、利用許可候補へ接続する。
- Purpose mismatchで再同意可能な場合はHUMAN_APPROVAL candidate、再同意経路がない場合はDENY candidateを生成する。
- Sensitive DataでConsentが不明な場合はfail-safeとしてHOLD / Review candidateへ接続し、利用へ進めない。
- 複数Data Itemsは個別に評価し、一部だけ目的外の場合でもblocked itemを明示する。
- CoreはData Use、Consent Request、Permission Grant、Approval Execution、Policy変更、External Sendを実行しない。
- DCSRはprovenance / purpose / policy Stateのfingerprintと差分再利用のみを行い、認証・暗号・Policy・DLPの代替にはしない。

## Authority / Safety Boundary

Purpose Match ≠ Permission Grant. Consent Evidence ≠ Approval Execution. Policy Exception Evidence ≠ Domain Authority. Allowed Use Candidate ≠ Data Use Execution. HUMAN_APPROVAL Candidate ≠ Approval Execution. HOLD / DENY Candidate ≠ Stop Execution. DCSR is not Authentication, Encryption, Policy, or DLP. DCSR reconstruction does not establish Consent, new Fact, Domain Authority, Semantic Judgment, Permission Grant, Safety Proof, Approval Execution, Action Execution, or Action Success.

## Verification

- Tests Normal: 160 / 160 PASS
- Tests Fresh Extract: 160 / 160 PASS
- Replay Normal: 3,000 / divergence 0
- Replay Fresh Extract: 3,000 / divergence 0
- Replay digest: `df55249e80f38f200241a5caa1c14c1beb69f9e12b2cf5b7a9434a6184c28e4a`
- Static Safety Normal: external execution paths 0 / unauthorized write paths 0
- Static Safety Fresh Extract: external execution paths 0 / unauthorized write paths 0
- AL Production Gate Normal: AL037–142 / 106 / 106 PASS
- AL Production Gate Fresh Extract: AL037–142 / 106 / 106 PASS
- Provisional Fresh Manifest: 1,163 / 1,163 matched

## Benchmark — condition-specific only

Condition: Python stdlib; 3000 Data items; purpose tags + sensitivity + consent/policy evidence; 3 full evaluations x 5 batches and 20 prepared reuses x 5 batches

- Normal Full median: 13.8704527 ms
- Normal Prepared median: 39.7885835 ms
- Fresh Full median: 24.1124860 ms
- Fresh Prepared median: 27.9710002 ms
- Semantic match: true
- DCSR Full bytes: 462,988
- DCSR Delta bytes: 459
- DCSR Delta ratio: 0.0991386386%
- Missing-only records: 1
- Missing metadata bytes: 151
- Full resend required: false

Prepared reuse includes integrity and fingerprint checks; on this workload it may be slower than full evaluation. These values are condition-specific measurements, not universal performance guarantees.

## Defect classification

- Production defect: 0
- Test fixture defect: 0
- Benchmark harness defect: 0
- Replay helper defect: 0
- Production Gate helper defect: 0
- Execution harness invocation defect: 0
- Production logic correction required: false

## Identity / provenance limitations

- Core SHA-256: `0c0ab89bc36bde12f52ba7a5c72e53101ffef305cb3ef33a15a42a230c102dc8`
- Existing V1 remained immutable and was not overwritten.
- exact registered Origin GUID was not freshly reverified.
- Pre-existing Notion V1 attachment byte identity was not freshly reverified.

## Final Fresh requirement

Final ZIP is frozen only after this report is frozen. A second Fresh Extract must verify Final Manifest, Core identity, Report identity, compile, 160 tests, Replay 3000, Benchmark, Static Safety, and AL037–142 Production Gate. Final ZIP SHA-256 is intentionally stored outside the ZIP in the Final Artifact Seal, Source Index, Canonical Notion evidence, and Completion Master to avoid self-reference.
