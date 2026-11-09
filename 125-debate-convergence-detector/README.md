# 125｜AL Debate Convergence Detector / 討論収束検知器

**Status:** COMPLETE / VERIFIED  
**Creator / Project Owner / Original Concept / Architecture Direction:** **NOEPIN / のえぴん**  
**Implementation / analysis / documentation support:** AI-assisted using ChatGPT

DebateのNovelty・Position Stability・Oscillation・Unresolved Issueを評価し、重要な未解決論点が残る場合に収束したことにしないControlです。

## 公開内容

- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Core / Tests / Replay / Benchmark / Static Safety / Production Gateを、完成時の実物から内容を変更せず移送しています。
- README等の文書から類似コードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification

- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–124 / 88 of 88 PASS**
- DCSR: **DIRECT INTEGRATION / 直接統合**
- Final ZIP SHA-256: `4f354cb77fb30f31a73fe01e9344495a715726a4d18abdd0b519bf4ce65684d8`

## Authority Boundary

- Candidate / Evaluation Result ≠ Permission Grant / Action Execution / Action Success
- DCSR Reconstruction ≠ Domain Authority / Safety Proof / Action Execution / Action Success

## Completion Evidence

- [Verification report](NOEPIN_AL_125_FINAL_VERIFICATION_REPORT_20261109.md)
- [Artifact seal](NOEPIN_AL_125_FINAL_ARTIFACT_SEAL_20261109.json)
- [Source index](NOEPIN_AL_125_SOURCE_INDEX.txt)

Verification Report / Artifact Seal / Source Indexは完成時の記録をそのまま保持しており、現在の公開表示に合わせて内容を書き換えていません。

## License

Current repository distribution: **Apache License 2.0**.

[Standalone work page](../works/125-debate-convergence-detector.md)
