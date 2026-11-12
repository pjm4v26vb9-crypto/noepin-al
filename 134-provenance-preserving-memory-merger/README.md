# 134｜AL Provenance-Preserving Memory Merger / 由来保持Memoryマージャー

**Status:** COMPLETE / VERIFIED  
**Creator / Project Owner / Original Concept / Architecture Direction:** **NOEPIN / のえぴん**  
**Implementation / analysis / documentation support:** AI-assisted using ChatGPT

複数のMemory候補を統合するときにSource・Provenance・Confidence・Scope等の由来情報を失わず、Composite Memory Candidateとして保持するControlです。

## 公開内容

- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Core / Tests / Replay / Benchmark / Static Safety / Production Gateを、完成時の実物から内容を変更せず移送しています。
- README等の文書から類似コードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification

- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–133 / 97 of 97 PASS**
- DCSR: **LIMITED INTEGRATION / 限定適用**
- Final ZIP SHA-256: `eaf9d170010860e17f1e56a164c120abef339bf4b46764b8df12b5f14acc60b6`

## Authority Boundary

- Candidate / Evaluation Result ≠ Permission Grant / Action Execution / Action Success
- DCSR Reconstruction ≠ Domain Authority / Safety Proof / Action Execution / Action Success

## Completion Evidence

- [Verification report](NOEPIN_AL_134_FINAL_VERIFICATION_REPORT_20261110.md)
- [Artifact seal](NOEPIN_AL_134_FINAL_ARTIFACT_SEAL_20261110.json)
- [Source index](NOEPIN_AL_134_SOURCE_INDEX.txt)

Verification Report / Artifact Seal / Source Indexは完成時の記録をそのまま保持しており、現在の公開表示に合わせて内容を書き換えていません。

## License

Current repository distribution: **Apache License 2.0**.

[Standalone work page](../works/134-provenance-preserving-memory-merger.md)
