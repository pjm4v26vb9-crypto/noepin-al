# 157｜AL Self-Evaluation Bias Detector / 自己評価バイアス検知器

**Status:** COMPLETE / VERIFIED  
**Creator / Project Owner / Original Concept / Architecture Direction:** **NOEPIN / のえぴん**  
**Implementation / analysis / documentation support:** AI-assisted using ChatGPT

自己評価バイアス検知器の完成時Final ZIPに含まれる検証済み実装と、Completion Evidenceを公開しています。

## 公開内容

- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Core / Tests / Replay / Benchmark / Static Safety / Production Gateを、完成時の実物から内容を変更せず移送しています。
- README等の文書から類似コードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification

- Tests: **160 / 160 PASS**
- Replay: **3,000 / divergence 0**
- Production Gate: **AL037–156 / 120 / 120 PASS**
- DCSR: **直接統合 / DIRECT INTEGRATION**
- Final ZIP SHA-256: `73a9efc5f157be2ae14af15589299fb650c7bc5b01d32bd97ad78b02f033a11a`

## Authority Boundary

- Candidate / Evaluation Result ≠ Permission Grant / Action Execution / Action Success
- DCSR Reconstruction ≠ Domain Authority / Safety Proof / Action Execution / Action Success

詳細な技術固有のAuthority BoundaryはCompletion EvidenceのVerification Report / Artifact Sealを参照してください。

## Completion Evidence

- [Verification report](NOEPIN_AL_157_FINAL_VERIFICATION_REPORT_20261112.md)
- [Artifact seal](NOEPIN_AL_157_FINAL_ARTIFACT_SEAL_20261112.json)
- [Source index](NOEPIN_AL_157_SOURCE_INDEX.txt)

Verification Report / Artifact Seal / Source Indexは完成時の記録をそのまま保持しており、現在の公開表示に合わせて内容を書き換えていません。

## License

Current repository distribution: **Apache License 2.0**.

[Standalone work page](../works/157-self-evaluation-bias-detector.md)
