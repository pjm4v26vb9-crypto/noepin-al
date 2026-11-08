# 074｜AL Sequential Risk Composer / 連続リスク合成器

**Status:** COMPLETE / VERIFIED  
**Creator / Project Owner / Original Concept / Architecture Direction:** **NOEPIN / のえぴん**  
**Implementation / analysis / documentation support:** AI-assisted using ChatGPT

複数ステップのリスクを、単純な足し算ではなく順序や相互作用も含めて評価し、Risk BudgetやStop Pointの候補を出すControlです。

## 公開内容
- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Tests / Replay / Benchmark / Production Gate等、Final ZIPに含まれる検証用ファイルは、存在するものを元のファイル名・内容のまま収録しています。
- README等の文書から似たコードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification
- Normal: **PASS**
- Fresh: **PASS**
- Final Fresh: **PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–073 / 37 of 37 PASS**
- DCSR: **AUXILIARY INTEGRATION / 補助統合**
- Final ZIP SHA-256: `d24c8ea9330773d0ea9c133dcf277ac407adea370d065b9b801f897b2d1dd7de`

## Authority Boundary
- Permission Grant
- Human Approval Execution
- Risk Budget Spend / Reservation
- Tool / Action Execution
- Transaction Commit / External Write
- World Truth / Safety Proof / Action Success

## Evidence
- [NOEPIN_AL_074_FINAL_VERIFICATION_REPORT_20261106.md](NOEPIN_AL_074_FINAL_VERIFICATION_REPORT_20261106.md)
- [NOEPIN_AL_074_FINAL_ARTIFACT_SEAL_20261106.json](NOEPIN_AL_074_FINAL_ARTIFACT_SEAL_20261106.json)

## License
Current repository distribution: **Apache License 2.0**.

Verification Report / Artifact Sealは完成時の記録をそのまま保持しており、現在の公開ライセンスに合わせて内容を書き換えていません。

[Standalone work page](../works/074-sequential-risk-composer.md)
