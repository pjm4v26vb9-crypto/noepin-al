# 045｜Undo-First Action Planner / Undo優先アクションプランナー

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

Reversibility / Riskを比較し、Trash-over-delete、Draft-over-send、Preview-over-publish、Versioned-write-over-overwrite、Dry-run-over-deployなど、より戻しやすい候補を優先するControlです。実行・Commitはしません。

- Plan Candidate ≠ Action Execution
- Undoable ≠ Safe
- Reversibility Score ≠ Safety Proof
- Draft Candidate ≠ Message Sent
- Trash Candidate ≠ Delete Completed

## 検証済み実装
この技術はREADMEだけでなく、完成時Final ZIPに含まれていた検証済み実装・テスト等を、技術フォルダ内の [`verified_artifact/`](../045-undo-first-action-planner/verified_artifact/) で確認できます。

Final ZIPにReplay / Benchmark / Production Gate等が含まれる場合は、それらも元のファイル名・内容のまま公開しています。

文書から類似コードを再生成して完成版として置き換えることはしていません。

## Verification
- Tests: **160 / 160 PASS**
- Fresh Extract: **160 / 160 PASS**
- Replay: **6,000 / divergence 0**
- External execution / mutation paths: **0**

## NOEPIN AL Production Use
**037〜044**を実制作Gateとして使用し、全Gate **PASS**。

## DCSR
**DIRECT INTEGRATION**. Full **1621.927351 ms** vs Prepared **10.308062 ms**. Full **1,197,176 bytes** → Delta **13,373 bytes (約1.12%)**。条件限定結果です。

## Integrity
Final ZIP SHA-256: `6894ce1431d1c3d077bdca1f638bc3aacb9a9fe34ef20371650954e4f4aa030d`  
Source SHA-256: `6b07c47a6f5c13433979a8a108507861495c9d561b870c7c61a2e5593b24b0f8`

## License
Current repository distribution: **Apache License 2.0** — see [LICENSE](../LICENSE) and [NOTICE](../NOTICE).


## Technical Files

[Technology folder](../045-undo-first-action-planner/)  
[Verified artifact](../045-undo-first-action-planner/verified_artifact/)  
[Verification Report](../045-undo-first-action-planner/NOEPIN_AL_045_FINAL_VERIFICATION_REPORT_20261103.md)  
[Artifact Seal](../045-undo-first-action-planner/NOEPIN_AL_045_FINAL_ARTIFACT_SEAL_20261103.json)

[Back to Works Index](README.md)
