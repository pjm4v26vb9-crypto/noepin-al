# 105｜AL Safe HTN Compiler / 安全HTNコンパイラ

**Status:** COMPLETE / VERIFIED  
**Creator / Project Owner / Original Concept / Architecture Direction:** **NOEPIN / のえぴん**  
**Implementation / analysis / documentation support:** AI-assisted using ChatGPT

HTNの階層Taskを、安全制約とAuthority境界を維持したAction候補へ分解・コンパイルするControlです。

## 公開内容
- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Core / Tests / Replay / Benchmark / Static Safety / Production Gateを、完成時の実物から内容を変更せず移送しています。
- README等の文書から類似コードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification
- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–104 / 68 of 68 PASS**
- DCSR: **AUXILIARY INTEGRATION / 補助統合**
- Final ZIP SHA-256: `8b615468253613a4c9c87f67f6af7cc61c5661f8bdb9bc95176b826c5f4408a3`

## Authority Boundary
- Hierarchical Plan Candidate ≠ Permission Grant / Action Execution / Action Success
- Authority requirement check ≠ Authority Grant
- Hard Constraint Pass ≠ Safety Proof
- Policy-verified Leaf ≠ Domain Authority
- Human Review Candidate ≠ Approval Execution
- HOLD / Replan Candidate ≠ Stop Execution
- Prepared Frontier / Decomposition Cache ≠ Authoritative Current State
- DCSR Reconstruction ≠ Domain Authority / Semantic Judgment / Safety Proof / Action Execution / Action Success

## Completion Evidence
- [NOEPIN_AL_105_FINAL_VERIFICATION_REPORT_20261109.md](NOEPIN_AL_105_FINAL_VERIFICATION_REPORT_20261109.md)
- [NOEPIN_AL_105_FINAL_ARTIFACT_SEAL_20261109.json](NOEPIN_AL_105_FINAL_ARTIFACT_SEAL_20261109.json)
- [NOEPIN_AL_105_SOURCE_INDEX.txt](NOEPIN_AL_105_SOURCE_INDEX.txt)

Verification Report / Artifact Seal / Source Indexは完成時の記録をそのまま保持しており、現在の公開表示に合わせて内容を書き換えていません。

## License
Current repository distribution: **Apache License 2.0**.

[Standalone work page](../works/105-safe-htn-compiler.md)
