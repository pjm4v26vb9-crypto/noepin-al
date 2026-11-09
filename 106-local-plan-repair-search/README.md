# 106｜AL Local Plan Repair Search / 局所プラン修復器

**Status:** COMPLETE / VERIFIED  
**Creator / Project Owner / Original Concept / Architecture Direction:** **NOEPIN / のえぴん**  
**Implementation / analysis / documentation support:** AI-assisted using ChatGPT

既存Planの問題部分を局所範囲に限定して修復候補を探索し、不要な全体変更を避けるControlです。

## 公開内容
- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Core / Tests / Replay / Benchmark / Static Safety / Production Gateを、完成時の実物から内容を変更せず移送しています。
- README等の文書から類似コードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification
- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–105 / 69 of 69 PASS**
- DCSR: **AUXILIARY INTEGRATION / 補助統合**
- Final ZIP SHA-256: `16eba73d06439dc9e285c6666a1f387125326c6b72501af01b74180cf6ced94d`

## Authority Boundary
- Repaired Subplan Candidate ≠ Permission Grant / Action Execution / Action Success
- Local Compatibility ≠ Global Constraint Proof
- Residual Risk ≠ Safety Proof
- Full Replan Candidate ≠ Replan Execution
- Human Review Candidate ≠ Approval Execution
- Prepared Frontier / Boundary Cache ≠ Authoritative Current State
- DCSR Reconstruction ≠ Domain Authority / Semantic Judgment / Safety Proof / Action Execution / Action Success

## Completion Evidence
- [NOEPIN_AL_106_FINAL_VERIFICATION_REPORT_20261109.md](NOEPIN_AL_106_FINAL_VERIFICATION_REPORT_20261109.md)
- [NOEPIN_AL_106_FINAL_ARTIFACT_SEAL_20261109.json](NOEPIN_AL_106_FINAL_ARTIFACT_SEAL_20261109.json)
- [NOEPIN_AL_106_SOURCE_INDEX.txt](NOEPIN_AL_106_SOURCE_INDEX.txt)

Verification Report / Artifact Seal / Source Indexは完成時の記録をそのまま保持しており、現在の公開表示に合わせて内容を書き換えていません。

## License
Current repository distribution: **Apache License 2.0**.

[Standalone work page](../works/106-local-plan-repair-search.md)
