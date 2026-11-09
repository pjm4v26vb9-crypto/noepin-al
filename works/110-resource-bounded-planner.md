# 110｜資源制約プランナー / AL Resource-Bounded Planner

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

Token・API Call・CPU・Memory・Cost・Tool Call等の複数資源Budgetを守りながら実行可能なPlan Candidateを探索するPlannerです。

## 検証済み実装
この技術はREADMEだけでなく、完成時Final ZIPに含まれていた検証済み実装・テスト・Replay・Benchmark・Static Safety・Gate関連ファイルを、技術フォルダ内の [`verified_artifact/`](../110-resource-bounded-planner/verified_artifact/) で確認できます。

文書から類似コードを再生成して完成版として置き換えることはしていません。

## Verification
- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–109 / 73 of 73 PASS**
- DCSR: **AUXILIARY INTEGRATION / 補助統合**
- Final ZIP SHA-256: `0f8c2aef5a83d3dcc369335b174232c0fbf43814c180c42889a55318fd895f0a`

## Technical Files
[Technology folder](../110-resource-bounded-planner/)  
[Verified artifact](../110-resource-bounded-planner/verified_artifact/)  
[Verification Report](../110-resource-bounded-planner/NOEPIN_AL_110_FINAL_VERIFICATION_REPORT_20261109.md)  
[Artifact Seal](../110-resource-bounded-planner/NOEPIN_AL_110_FINAL_ARTIFACT_SEAL_20261109.json)  
[Source Index](../110-resource-bounded-planner/NOEPIN_AL_110_SOURCE_INDEX.txt)

[Back to Works Index](README.md)
