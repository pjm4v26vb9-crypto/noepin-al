# 133｜Memory重要度減衰スケジューラ / AL Memory Importance Decay Scheduler

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

Memoryの重要度・使用頻度・鮮度・Trust・経過時間・Purpose・Retention Policyから保持優先度を評価し、保護対象を維持したままArchive / Delete / Refresh候補を分離するControlです。

## 検証済み実装

この技術はREADMEだけでなく、完成時Final ZIPに含まれていた検証済み実装・テスト・Replay・Benchmark・Static Safety・Gate関連ファイルを、技術フォルダ内の [`verified_artifact/`](../133-memory-importance-decay-scheduler/verified_artifact/) で確認できます。

文書から類似コードを再生成して完成版として置き換えることはしていません。

## Verification

- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–132 / 96 of 96 PASS**
- DCSR: **LIMITED INTEGRATION / 限定適用**
- Final ZIP SHA-256: `2670a6c96da760cb708992dce1be1a52b7c154329ce1414b00a6849a64e77561`

## Technical Files

[Technology folder](../133-memory-importance-decay-scheduler/)  
[Verified artifact](../133-memory-importance-decay-scheduler/verified_artifact/)  
[Verification Report](../133-memory-importance-decay-scheduler/NOEPIN_AL_133_FINAL_VERIFICATION_REPORT_20261110.md)  
[Artifact Seal](../133-memory-importance-decay-scheduler/NOEPIN_AL_133_FINAL_ARTIFACT_SEAL_20261110.json)  
[Source Index](../133-memory-importance-decay-scheduler/NOEPIN_AL_133_SOURCE_INDEX.txt)

[Back to Works Index](README.md)
