# 138｜意味重複Memory圧縮器 / AL Semantic Memory Deduplicator

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

意味的に重複するMemoryを候補化しつつ、Time・Scope・Critical差分・Provenanceを失わない条件でのみ統合し、重要な差分は別保持するControlです。

## 検証済み実装

この技術はREADMEだけでなく、完成時Final ZIPに含まれていた検証済み実装・テスト・Replay・Benchmark・Static Safety・Gate関連ファイルを、技術フォルダ内の [`verified_artifact/`](../138-semantic-memory-deduplicator/verified_artifact/) で確認できます。

文書から類似コードを再生成して完成版として置き換えることはしていません。

## Verification

- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–137 / 101 of 101 PASS**
- DCSR: **LIMITED INTEGRATION / 限定適用**
- Final ZIP SHA-256: `002c84c10fa5ce5d7bbfe52902b4e726ef54213f86fef81fc9a646601fe4e559`

## Technical Files

[Technology folder](../138-semantic-memory-deduplicator/)  
[Verified artifact](../138-semantic-memory-deduplicator/verified_artifact/)  
[Verification Report](../138-semantic-memory-deduplicator/NOEPIN_AL_138_FINAL_VERIFICATION_REPORT_20261111.md)  
[Artifact Seal](../138-semantic-memory-deduplicator/NOEPIN_AL_138_FINAL_ARTIFACT_SEAL_20261111.json)  
[Source Index](../138-semantic-memory-deduplicator/NOEPIN_AL_138_SOURCE_INDEX.txt)

[Back to Works Index](README.md)
