# 121｜遅延・安全トレードオフ制御器 / AL Latency-Safety Tradeoff Controller

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

Latencyを短縮する場合でも必須Safety Checkを省略せず、遅延と安全性のTradeoff Candidateを評価するControlです。

## 検証済み実装
この技術はREADMEだけでなく、完成時Final ZIPに含まれていた検証済み実装・テスト・Replay・Benchmark・Static Safety・Gate関連ファイルを、技術フォルダ内の [`verified_artifact/`](../121-latency-safety-tradeoff-controller/verified_artifact/) で確認できます。

文書から類似コードを再生成して完成版として置き換えることはしていません。

## Verification
- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–120 / 84 of 84 PASS**
- DCSR: **AUXILIARY INTEGRATION / 補助統合**
- Final ZIP SHA-256: `f08f587e7a91ca53da70dea3e9237f83e1fe820926e75243920334f5b6340f87`

## Technical Files
[Technology folder](../121-latency-safety-tradeoff-controller/)  
[Verified artifact](../121-latency-safety-tradeoff-controller/verified_artifact/)  
[Verification Report](../121-latency-safety-tradeoff-controller/NOEPIN_AL_121_FINAL_VERIFICATION_REPORT_20261109.md)  
[Artifact Seal](../121-latency-safety-tradeoff-controller/NOEPIN_AL_121_FINAL_ARTIFACT_SEAL_20261109.json)  
[Source Index](../121-latency-safety-tradeoff-controller/NOEPIN_AL_121_SOURCE_INDEX.txt)

[Back to Works Index](README.md)
