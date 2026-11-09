# 102｜安全制約付きA*プランナー / AL Safe A* Action Planner

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

Hard Constraint・Risk・Cost Budgetを守りながらA*探索を行い、安全な経路がない場合は危険な経路へ置き換えずHOLDするPlannerです。

## 検証済み実装
この技術はREADMEだけでなく、完成時Final ZIPに含まれていた検証済み実装・テスト・Replay・Benchmark・Static Safety・Gate関連ファイルを、技術フォルダ内の [`verified_artifact/`](../102-safe-astar-action-planner/verified_artifact/) で確認できます。

文書から類似コードを再生成して完成版として置き換えることはしていません。

## Verification
- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–101 / 65 of 65 PASS**
- DCSR: **AUXILIARY INTEGRATION / 補助統合**
- Final ZIP SHA-256: `7cd1eb6cba3953d95931057ffa95d93190ef44a88a624fc872d71860b317f470`

## Technical Files
[Technology folder](../102-safe-astar-action-planner/)  
[Verified artifact](../102-safe-astar-action-planner/verified_artifact/)  
[Verification Report](../102-safe-astar-action-planner/NOEPIN_AL_102_FINAL_VERIFICATION_REPORT_20261108.md)  
[Artifact Seal](../102-safe-astar-action-planner/NOEPIN_AL_102_FINAL_ARTIFACT_SEAL_20261108.json)  
[Source Index](../102-safe-astar-action-planner/NOEPIN_AL_102_SOURCE_INDEX.txt)

[Back to Works Index](README.md)
