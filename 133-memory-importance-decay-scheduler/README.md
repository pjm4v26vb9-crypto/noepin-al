# 133｜AL Memory Importance Decay Scheduler / Memory重要度減衰スケジューラ

**Status:** COMPLETE / VERIFIED  
**Creator / Project Owner / Original Concept / Architecture Direction:** **NOEPIN / のえぴん**  
**Implementation / analysis / documentation support:** AI-assisted using ChatGPT

Memoryの重要度・使用頻度・鮮度・Trust・経過時間・Purpose・Retention Policyから保持優先度を評価し、保護対象を維持したままArchive / Delete / Refresh候補を分離するControlです。

## 公開内容

- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Core / Tests / Replay / Benchmark / Static Safety / Production Gateを、完成時の実物から内容を変更せず移送しています。
- README等の文書から類似コードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification

- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–132 / 96 of 96 PASS**
- DCSR: **LIMITED INTEGRATION / 限定適用**
- Final ZIP SHA-256: `2670a6c96da760cb708992dce1be1a52b7c154329ce1414b00a6849a64e77561`

## Authority Boundary

- Candidate / Evaluation Result ≠ Permission Grant / Action Execution / Action Success
- DCSR Reconstruction ≠ Domain Authority / Safety Proof / Action Execution / Action Success

## Completion Evidence

- [Verification report](NOEPIN_AL_133_FINAL_VERIFICATION_REPORT_20261110.md)
- [Artifact seal](NOEPIN_AL_133_FINAL_ARTIFACT_SEAL_20261110.json)
- [Source index](NOEPIN_AL_133_SOURCE_INDEX.txt)

Verification Report / Artifact Seal / Source Indexは完成時の記録をそのまま保持しており、現在の公開表示に合わせて内容を書き換えていません。

## License

Current repository distribution: **Apache License 2.0**.

[Standalone work page](../works/133-memory-importance-decay-scheduler.md)
