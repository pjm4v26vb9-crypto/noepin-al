# 104｜AL Risk-Aware Monte Carlo Tree Search / リスク認識MCTS

**Status:** COMPLETE / VERIFIED  
**Creator / Project Owner / Original Concept / Architecture Direction:** **NOEPIN / のえぴん**  
**Implementation / analysis / documentation support:** AI-assisted using ChatGPT

Risk上限とPolicy制約を保ったままMonte Carlo Tree Searchで候補を評価し、安全な計画候補を探索するPlannerです。

## 公開内容
- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Core / Tests / Replay / Benchmark / Static Safety / Production Gateを、完成時の実物から内容を変更せず移送しています。
- README等の文書から類似コードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification
- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–103 / 67 of 67 PASS**
- DCSR: **AUXILIARY INTEGRATION / 補助統合**
- Final ZIP SHA-256: `24188343b94781ba7acdf2700389f85852bac658bfca5e344bceba875dc7945a`

## Authority Boundary
- Chosen Action Candidate ≠ Permission Grant / Action Execution / Action Success
- Most Visits ≠ Safety Proof
- Simulator Confidence ≠ World Truth
- Risk Estimate / CVaR ≠ Safety Proof
- Hard Constraint Pass ≠ Domain Authority
- HUMAN_APPROVAL Candidate ≠ Approval Execution
- HOLD / Replan Candidate ≠ Stop Execution
- Prepared Frontier / Simulator Cache ≠ Authoritative Current State

## Completion Evidence
- [NOEPIN_AL_104_FINAL_VERIFICATION_REPORT_20261109.md](NOEPIN_AL_104_FINAL_VERIFICATION_REPORT_20261109.md)
- [NOEPIN_AL_104_FINAL_ARTIFACT_SEAL_20261109.json](NOEPIN_AL_104_FINAL_ARTIFACT_SEAL_20261109.json)
- [NOEPIN_AL_104_SOURCE_INDEX.txt](NOEPIN_AL_104_SOURCE_INDEX.txt)

Verification Report / Artifact Seal / Source Indexは完成時の記録をそのまま保持しており、現在の公開表示に合わせて内容を書き換えていません。

## License
Current repository distribution: **Apache License 2.0**.

[Standalone work page](../works/104-risk-aware-mcts.md)
