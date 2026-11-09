# 110｜AL Resource-Bounded Planner / 資源制約プランナー

**Status:** COMPLETE / VERIFIED  
**Creator / Project Owner / Original Concept / Architecture Direction:** **NOEPIN / のえぴん**  
**Implementation / analysis / documentation support:** AI-assisted using ChatGPT

Token・API Call・CPU・Memory・Cost・Tool Call等の複数資源Budgetを守りながら実行可能なPlan Candidateを探索するPlannerです。

## 公開内容
- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Core / Tests / Replay / Benchmark / Static Safety / Production Gateを、完成時の実物から内容を変更せず移送しています。
- README等の文書から類似コードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification
- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–109 / 73 of 73 PASS**
- DCSR: **AUXILIARY INTEGRATION / 補助統合**
- Final ZIP SHA-256: `0f8c2aef5a83d3dcc369335b174232c0fbf43814c180c42889a55318fd895f0a`

## Authority Boundary
- Feasible Plan Candidate ≠ Permission Grant / Budget Grant / Credential Grant / Action Execution / Action Success
- Resource Forecast / Shortfall ≠ World Truth
- Budget Feasible ≠ Safety Proof
- HUMAN_APPROVAL Candidate ≠ Approval Execution
- DCSR Reconstruction ≠ Domain Authority / Semantic Judgment / Safety Proof / Action Execution / Action Success

## Completion Evidence
- [NOEPIN_AL_110_FINAL_VERIFICATION_REPORT_20261109.md](NOEPIN_AL_110_FINAL_VERIFICATION_REPORT_20261109.md)
- [NOEPIN_AL_110_FINAL_ARTIFACT_SEAL_20261109.json](NOEPIN_AL_110_FINAL_ARTIFACT_SEAL_20261109.json)
- [NOEPIN_AL_110_SOURCE_INDEX.txt](NOEPIN_AL_110_SOURCE_INDEX.txt)

Verification Report / Artifact Seal / Source Indexは完成時の記録をそのまま保持しており、現在の公開表示に合わせて内容を書き換えていません。

## License
Current repository distribution: **Apache License 2.0**.

[Standalone work page](../works/110-resource-bounded-planner.md)
