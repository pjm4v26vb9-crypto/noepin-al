# 102｜AL Safe A* Action Planner / 安全制約付きA*プランナー

**Status:** COMPLETE / VERIFIED  
**Creator / Project Owner / Original Concept / Architecture Direction:** **NOEPIN / のえぴん**  
**Implementation / analysis / documentation support:** AI-assisted using ChatGPT

Hard Constraint・Risk・Cost Budgetを守りながらA*探索を行い、安全な経路がない場合は危険な経路へ置き換えずHOLDするPlannerです。

## 公開内容
- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Core / Tests / Replay / Benchmark / Static Safety / Production Gateを、完成時の実物から内容を変更せず移送しています。
- README等の文書から類似コードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification
- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–101 / 65 of 65 PASS**
- DCSR: **AUXILIARY INTEGRATION / 補助統合**
- Final ZIP SHA-256: `7cd1eb6cba3953d95931057ffa95d93190ef44a88a624fc872d71860b317f470`

## Authority Boundary
- Safe Plan ≠ Permission Grant / Action Execution / Action Success
- Constraint Pass ≠ Safety Proof
- A* Optimal Candidate ≠ Domain Authority
- Risk Trace ≠ World Truth
- HOLD / Replan Candidate ≠ Stop Execution
- Prepared Frontier / Heuristic Cache ≠ Authoritative Current State
- DCSR Reconstruction ≠ Domain Authority / Semantic Judgment / Safety Proof / Action Execution / Action Success

## Completion Evidence
- [NOEPIN_AL_102_FINAL_VERIFICATION_REPORT_20261108.md](NOEPIN_AL_102_FINAL_VERIFICATION_REPORT_20261108.md)
- [NOEPIN_AL_102_FINAL_ARTIFACT_SEAL_20261108.json](NOEPIN_AL_102_FINAL_ARTIFACT_SEAL_20261108.json)
- [NOEPIN_AL_102_SOURCE_INDEX.txt](NOEPIN_AL_102_SOURCE_INDEX.txt)

Verification Report / Artifact Seal / Source Indexは完成時の記録をそのまま保持しており、現在の公開表示に合わせて内容を書き換えていません。

## License
Current repository distribution: **Apache License 2.0**.

[Standalone work page](../works/102-safe-astar-action-planner.md)
