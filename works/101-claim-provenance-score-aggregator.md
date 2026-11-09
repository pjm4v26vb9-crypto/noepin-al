# 101｜主張由来スコア統合器 / AL Claim Provenance Score Aggregator

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

Claimの由来をSourceまで辿り、Source Trust・変換劣化・独立Root・Weakest Linkを考慮してProvenance Scoreを算出するControlです。

## 検証済み実装
この技術はREADMEだけでなく、完成時Final ZIPに含まれていた検証済み実装・テスト・Replay・Benchmark・Static Safety・Gate関連ファイルを、技術フォルダ内の [`verified_artifact/`](../101-claim-provenance-score-aggregator/verified_artifact/) で確認できます。

文書から類似コードを再生成して完成版として置き換えることはしていません。

## Verification
- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–100 / 64 of 64 PASS**
- DCSR: **LIMITED INTEGRATION / 限定適用**
- Final ZIP SHA-256: `2c691174bd73f0785e53039f45adf7678d25fcf1d44a1e1961e1032802bedfa2`

## Technical Files
[Technology folder](../101-claim-provenance-score-aggregator/)  
[Verified artifact](../101-claim-provenance-score-aggregator/verified_artifact/)  
[Verification Report](../101-claim-provenance-score-aggregator/NOEPIN_AL_101_FINAL_VERIFICATION_REPORT_20261108.md)  
[Artifact Seal](../101-claim-provenance-score-aggregator/NOEPIN_AL_101_FINAL_ARTIFACT_SEAL_20261108.json)  
[Source Index](../101-claim-provenance-score-aggregator/NOEPIN_AL_101_SOURCE_INDEX.txt)

[Back to Works Index](README.md)
