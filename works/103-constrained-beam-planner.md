# 103｜制約付きビームプランナー / AL Constrained Beam Planner

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

制約違反候補を除外し、Beam幅の中で候補を絞りながら安全な計画候補を探索するPlannerです。

## 検証済み実装
この技術はREADMEだけでなく、完成時Final ZIPに含まれていた検証済み実装・テスト・Replay・Benchmark・Static Safety・Gate関連ファイルを、技術フォルダ内の [`verified_artifact/`](../103-constrained-beam-planner/verified_artifact/) で確認できます。

文書から類似コードを再生成して完成版として置き換えることはしていません。

## Verification
- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–102 / 66 of 66 PASS**
- DCSR: **AUXILIARY INTEGRATION / 補助統合**
- Final ZIP SHA-256: `cfa412a992d36cab0a6c44690f8d0f52560cd398b7dd45e32f0d77de7d603250`

## Technical Files
[Technology folder](../103-constrained-beam-planner/)  
[Verified artifact](../103-constrained-beam-planner/verified_artifact/)  
[Verification Report](../103-constrained-beam-planner/NOEPIN_AL_103_FINAL_VERIFICATION_REPORT_20261109.md)  
[Artifact Seal](../103-constrained-beam-planner/NOEPIN_AL_103_FINAL_ARTIFACT_SEAL_20261109.json)  
[Source Index](../103-constrained-beam-planner/NOEPIN_AL_103_SOURCE_INDEX.txt)

[Back to Works Index](README.md)
