# 136｜エピソード隔離マネージャー / AL Episodic Isolation Manager

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

会話・Task・EpisodeごとのMemory境界を分離し、別Episodeへの不用意な持ち込みやLong-term Memoryへの自動昇格を防ぐControlです。

## 検証済み実装

この技術はREADMEだけでなく、完成時Final ZIPに含まれていた検証済み実装・テスト・Replay・Benchmark・Static Safety・Gate関連ファイルを、技術フォルダ内の [`verified_artifact/`](../136-episodic-isolation-manager/verified_artifact/) で確認できます。

文書から類似コードを再生成して完成版として置き換えることはしていません。

## Verification

- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–135 / 99 of 99 PASS**
- DCSR: **LIMITED INTEGRATION / 限定適用**
- Final ZIP SHA-256: `292e5f2041faf140f60dfad8457c207c339af65e4c7733256cd81eb4faf4d3b6`

## Technical Files

[Technology folder](../136-episodic-isolation-manager/)  
[Verified artifact](../136-episodic-isolation-manager/verified_artifact/)  
[Verification Report](../136-episodic-isolation-manager/NOEPIN_AL_136_FINAL_VERIFICATION_REPORT_20261111.md)  
[Artifact Seal](../136-episodic-isolation-manager/NOEPIN_AL_136_FINAL_ARTIFACT_SEAL_20261111.json)  
[Source Index](../136-episodic-isolation-manager/NOEPIN_AL_136_SOURCE_INDEX.txt)

[Back to Works Index](README.md)
