# 103｜AL Constrained Beam Planner / 制約付きビームプランナー

**Status:** COMPLETE / VERIFIED  
**Creator / Project Owner / Original Concept / Architecture Direction:** **NOEPIN / のえぴん**  
**Implementation / analysis / documentation support:** AI-assisted using ChatGPT

制約違反候補を除外し、Beam幅の中で候補を絞りながら安全な計画候補を探索するPlannerです。

## 公開内容
- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Core / Tests / Replay / Benchmark / Static Safety / Production Gateを、完成時の実物から内容を変更せず移送しています。
- README等の文書から類似コードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification
- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–102 / 66 of 66 PASS**
- DCSR: **AUXILIARY INTEGRATION / 補助統合**
- Final ZIP SHA-256: `cfa412a992d36cab0a6c44690f8d0f52560cd398b7dd45e32f0d77de7d603250`

## Authority Boundary
- Top Plan ≠ Permission Grant / Action Execution / Action Success
- Hard Constraint Pass ≠ Safety Proof
- Beam Rank ≠ Domain Authority
- Utility / Risk Score ≠ World Truth
- Human Review Candidate ≠ Approval Execution
- HOLD / Replan Candidate ≠ Stop Execution
- Prepared Frontier / Rank Cache ≠ Authoritative Current State
- DCSR Reconstruction ≠ Domain Authority / Semantic Judgment / Safety Proof / Action Execution / Action Success

## Completion Evidence
- [NOEPIN_AL_103_FINAL_VERIFICATION_REPORT_20261109.md](NOEPIN_AL_103_FINAL_VERIFICATION_REPORT_20261109.md)
- [NOEPIN_AL_103_FINAL_ARTIFACT_SEAL_20261109.json](NOEPIN_AL_103_FINAL_ARTIFACT_SEAL_20261109.json)
- [NOEPIN_AL_103_SOURCE_INDEX.txt](NOEPIN_AL_103_SOURCE_INDEX.txt)

Verification Report / Artifact Seal / Source Indexは完成時の記録をそのまま保持しており、現在の公開表示に合わせて内容を書き換えていません。

## License
Current repository distribution: **Apache License 2.0**.

[Standalone work page](../works/103-constrained-beam-planner.md)
