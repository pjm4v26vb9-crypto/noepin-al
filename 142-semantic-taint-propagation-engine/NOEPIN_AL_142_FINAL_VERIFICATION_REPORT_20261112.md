# NOEPIN AL 142 — Final Verification Report — 2026-11-12

## Identity

- Technology: 142｜意味Taint伝播エンジン
- English Name: AL Semantic Taint Propagation Engine
- Canonical ID: NOEPIN-AL-142
- Artifact: Sequential Successor V2
- Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
- AI support: AI-assisted implementation / analysis / documentation support using ChatGPT
- License / Rights: NOT SPECIFIED
- DCSR: AUXILIARY INTEGRATION / 補助統合

## Canonical semantics implemented

- Untrusted / Sensitive / External Instruction / Secret 等をtyped semantic taintとして保持し、Summary / Paraphrase / Merge / Filter / Sanitizer / Unknown Transformを通じて伝播する。
- Mergeでは入力labelのjoinを行い、要約・言い換えだけでtaintを消さない。
- Sanitizerは明示されたsanitizer evidenceが存在する場合のみ、evidenceで指定されたlabelだけを縮小候補として除去する。
- Unknown Transformではfail-safeとしてtaintを保持し、Review / HOLD candidateへ接続する。
- Untrusted + External InstructionがExecution/Tool Sinkへ到達した場合はDENY candidate、Secret/Sensitive/PersonalがExternal Sinkへ到達した場合はDENY/HOLD candidateを生成する。
- CoreはSink実行、Tool実行、External send、Memory/Label write、Policy変更を行わない。
- DCSRはprovenance / taint / flow Stateのfingerprintと差分再利用のみを行い、認証・暗号・Policy・DLPの代替にはしない。

## Authority / Safety Boundary

Taint ≠ Truth. Source ≠ Source Authority. Sanitizer Evidence ≠ universal Safety Proof. Propagated Label ≠ Policy Decision. Tainted Sink Candidate ≠ Sink Execution. DENY / HOLD Candidate ≠ Stop Execution. DCSR is not Authentication, Encryption, Policy, or DLP. DCSR reconstruction does not establish new Fact, Domain Authority, Semantic Judgment, Permission Grant, Safety Proof, Approval Execution, Action Execution, or Action Success.

## Verification

- Tests Normal: 160 / 160 PASS
- Tests Fresh Extract: 160 / 160 PASS
- Replay Normal: 3,000 / divergence 0
- Replay Fresh Extract: 3,000 / divergence 0
- Replay digest: `bec60a9801c33aa9473f489f4cd605cb9a22b08a945adbaebac88b8525018532`
- Static Safety Normal: external execution paths 0 / unauthorized write paths 0
- Static Safety Fresh Extract: external execution paths 0 / unauthorized write paths 0
- AL Production Gate Normal: AL037–141 / 105 / 105 PASS
- AL Production Gate Fresh Extract: AL037–141 / 105 / 105 PASS
- Provisional Fresh Manifest: 1,138 / 1,138 matched

## Benchmark — condition-specific only

Condition: Python stdlib; 2500 Data items; 500 merge transformations; semantic taint propagation with provenance/flow/sink candidates; 3 full evaluations x 5 batches and 20 prepared reuses x 5 batches

- Normal Full median: 10.6054723 ms
- Normal Prepared median: 15.6857475 ms
- Fresh Full median: 6.3812027 ms
- Fresh Prepared median: 13.9775017 ms
- Semantic match: true
- DCSR Full bytes: 375,667
- DCSR Delta bytes: 468
- DCSR Delta ratio: 0.1245784165%
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
- Execution harness invocation defect: 1 CORRECTED

The Fresh Extract initially attempted direct shell execution after ZIP extraction; executable permission was not preserved by the packaging method. Verification was corrected to invoke the script explicitly through `sh`, the Defect Ledger was updated, and Normal/Fresh verification was rerun. Production logic correction required: false.

## Identity / provenance limitations

- Core SHA-256: `4d959fe930ade0186af1a6868bcf31aab14c5b54d55b59e6f63640f965431cbd`
- Existing V1 remained immutable and was not overwritten.
- exact registered Origin GUID was not freshly reverified.
- Pre-existing Notion V1 attachment byte identity was not freshly reverified.

## Final Fresh requirement

Final ZIP is frozen only after this report is frozen. A second Fresh Extract must verify Final Manifest, Core identity, Report identity, compile, 160 tests, Replay 3000, Benchmark, Static Safety, and AL037–141 Production Gate. Final ZIP SHA-256 is intentionally stored outside the ZIP in the Final Artifact Seal, Source Index, Canonical Notion evidence, and Completion Master to avoid self-reference.
