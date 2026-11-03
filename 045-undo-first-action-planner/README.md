# 045 — Undo-First Action Planner / Undo優先アクションプランナー

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

Reversibility / Riskを比較し、Trash-over-delete、Draft-over-send、Preview-over-publish、Versioned-write-over-overwrite、Dry-run-over-deployなど、より戻しやすい候補を優先するControlです。実行・Commitはしません。

- Plan Candidate ≠ Action Execution
- Undoable ≠ Safe
- Reversibility Score ≠ Safety Proof
- Draft Candidate ≠ Message Sent
- Trash Candidate ≠ Delete Completed

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
