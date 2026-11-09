# 116｜リスク予算配分器 / AL Risk Budget Allocator

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

Total Risk Budgetを不変上限として、各StepへのRisk Budget Candidateを保守的に配分するControlです。

## 検証済み実装
この技術はREADMEだけでなく、完成時Final ZIPに含まれていた検証済み実装・テスト・Replay・Benchmark・Static Safety・Gate関連ファイルを、技術フォルダ内の [`verified_artifact/`](../116-risk-budget-allocator/verified_artifact/) で確認できます。

文書から類似コードを再生成して完成版として置き換えることはしていません。

## Verification
- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–115 / 79 of 79 PASS**
- DCSR: **AUXILIARY INTEGRATION / 補助統合**
- Final ZIP SHA-256: `e0922c3b1d827b7915fef815443162915f0d88c4a5980ed47c8cc12db0df069a`

## Technical Files
[Technology folder](../116-risk-budget-allocator/)  
[Verified artifact](../116-risk-budget-allocator/verified_artifact/)  
[Verification Report](../116-risk-budget-allocator/NOEPIN_AL_116_FINAL_VERIFICATION_REPORT_20261109.md)  
[Artifact Seal](../116-risk-budget-allocator/NOEPIN_AL_116_FINAL_ARTIFACT_SEAL_20261109.json)  
[Source Index](../116-risk-budget-allocator/NOEPIN_AL_116_SOURCE_INDEX.txt)

[Back to Works Index](README.md)
