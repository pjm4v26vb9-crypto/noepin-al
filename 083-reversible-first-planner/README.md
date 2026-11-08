# 083｜AL Reversible-First Planner / 可逆性優先プランナー

**Status:** COMPLETE / VERIFIED  
**Creator / Project Owner / Original Concept / Architecture Direction:** **NOEPIN / のえぴん**  
**Implementation / analysis / documentation support:** AI-assisted using ChatGPT

同じGoalを達成できる候補の中から、より戻しやすく影響範囲の小さいActionを優先して並べるControlです。可逆性が高いこと自体をSafety Proofにはしません。

## 公開内容
- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Tests / Replay / Benchmark / Production Gate等、Final ZIPに含まれる検証用ファイルは、存在するものを元のファイル名・内容のまま収録しています。
- README等の文書から似たコードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification
- Normal: **160/160 PASS**
- Fresh: **160/160 PASS**
- Final Fresh: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–082 / 46 of 46 PASS**
- DCSR: **AUXILIARY INTEGRATION / 補助統合**
- Final ZIP SHA-256: `93ee3f3c2325ae7d14d2bd84ea75fe012980086d6c59823fd8a83287f10699ad`

## Authority Boundary
- Goal Candidate ≠ User Intent Truth
- Reversibility Score ≠ Safety Proof
- Cost / Risk Estimate ≠ World Truth
- Human Approval Evidence ≠ Approval Execution
- Chosen Action ≠ Action Execution
- Ordered Plan ≠ Plan Commit
- Rollback Option ≠ Rollback Execution
- ALLOW Candidate ≠ Permission Grant

## Evidence
- [NOEPIN_AL_083_FINAL_VERIFICATION_REPORT_20261107.md](NOEPIN_AL_083_FINAL_VERIFICATION_REPORT_20261107.md)
- [NOEPIN_AL_083_FINAL_ARTIFACT_SEAL_20261107.json](NOEPIN_AL_083_FINAL_ARTIFACT_SEAL_20261107.json)

## License
Current repository distribution: **Apache License 2.0**.

Verification Report / Artifact Sealは完成時の記録をそのまま保持しており、現在の公開ライセンスに合わせて内容を書き換えていません。

[Standalone work page](../works/083-reversible-first-planner.md)
