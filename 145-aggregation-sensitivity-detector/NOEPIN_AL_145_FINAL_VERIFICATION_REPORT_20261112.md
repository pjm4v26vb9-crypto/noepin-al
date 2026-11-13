# NOEPIN AL 145 — Final Verification Report — 2026-11-12

## Identity

- Technology: 145｜情報集約感度検知器
- English Name: AL Aggregation Sensitivity Detector
- Canonical ID: NOEPIN-AL-145
- Artifact: Sequential Successor V2
- Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
- AI support: AI-assisted implementation / analysis / documentation support using ChatGPT
- License / Rights: NOT SPECIFIED
- DCSR: AUXILIARY INTEGRATION / 補助統合

## Canonical semantics implemented

- Data Fragmentをentity / attribute / join key / sensitivity / provenanceとして正規化する。
- 同一join keyで安全に結合できるFragment集合に対して、明示されたInference Ruleだけを適用する。
- 個別Fragmentより高いSensitivityを持つInferred Fact Candidateが生成された場合、Aggregate Sensitivityを昇格する。
- 外部Audienceで推論影響が不明な場合は、個別ラベルだけを根拠にALLOWせずHOLD / Policy Review candidateへ接続する。
- Audience policy boundを超えるAggregate SensitivityはHOLDまたはDENY candidateへ接続する。
- Inferred Fact CandidateはWorld Truthではなく、Leak RiskはLeak Proofではなく、ALLOWはPermission Grant / Disclosure Executionを実行しない。
- DCSRはfragments / rules / audience / outcome fingerprintと差分再利用のみを行い、認証・暗号・Policy・DLPの代替にはしない。

## Authority / Safety Boundary

Inferred Fact Candidate ≠ World Truth. Aggregate Sensitivity ≠ Policy Decision. Leak Risk ≠ Leak Proof. Audience Policy Evidence ≠ Permission Grant. ALLOW Candidate ≠ Disclosure Execution. HOLD / DENY Candidate ≠ Stop Execution. DCSR is not Authentication, Encryption, Policy, or DLP. DCSR reconstruction does not establish new Fact, Domain Authority, Semantic Judgment, Permission Grant, Safety Proof, Approval Execution, Action Execution, or Action Success.

## Verification

- Tests Normal: 160 / 160 PASS
- Tests Fresh Extract: 160 / 160 PASS
- Replay Normal: 3,000 / divergence 0
- Replay Fresh Extract: 3,000 / divergence 0
- Replay digest: `843c25c464ac71c13855afb5b865860ca3509689bb1ef98c1ca5dec7a4c7d97a`
- Static Safety Normal: external execution paths 0 / unauthorized write paths 0
- Static Safety Fresh Extract: external execution paths 0 / unauthorized write paths 0
- AL Production Gate Normal: AL037–144 / 108 / 108 PASS
- AL Production Gate Fresh Extract: AL037–144 / 108 / 108 PASS
- Provisional Fresh Manifest: 1,220 / 1,220 matched

## Benchmark — condition-specific only

Condition: Python stdlib; 3000 fragments; knowledge-graph join + inference rules + sensitivity lattice; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches

- Normal Full median: 4.4542304000 ms
- Normal Prepared median: 0.0063982000 ms
- Fresh Full median: 4.0687352001 ms
- Fresh Prepared median: 0.0063278000 ms
- Semantic match: true
- DCSR Full bytes: 620,402
- DCSR Delta bytes: 261
- DCSR Delta ratio: 0.0420694969%
- Missing-only records: 1
- Missing metadata bytes: 109
- Full resend required: false

Prepared reuse includes integrity and fingerprint checks. These values are condition-specific measurements, not universal performance guarantees.

## Defect classification

- Production defect: 0
- Test fixture defect: 0
- Benchmark harness defect: 0
- Replay helper defect: 0
- Production Gate helper defect: 0
- Execution harness invocation defect: 0
- Production logic correction required: false

## Identity / provenance limitations

- Core SHA-256: `04f4e820f7c2b0b921ea9746d57ad0162c8ef4a9b6bc35d9a70f2470e6c9a0fb`
- Existing V1 remained immutable and was not overwritten.
- exact registered Origin GUID was not freshly reverified.
- Pre-existing Notion V1 attachment byte identity was not freshly reverified.

## Final Fresh requirement

Final ZIP is frozen only after this report is frozen. A second Fresh Extract must verify Final Manifest, Core identity, Report identity, compile, 160 tests, Replay 3000, Benchmark, Static Safety, and AL037–144 Production Gate. Final ZIP SHA-256 is intentionally stored outside the ZIP in the Final Artifact Seal, Source Index, Canonical Notion evidence, and Completion Master to avoid self-reference.
