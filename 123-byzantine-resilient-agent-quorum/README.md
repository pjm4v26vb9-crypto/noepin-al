# 123｜AL Byzantine-Resilient Agent Quorum / ビザンチン耐性Agentクォーラム

**Status:** COMPLETE / VERIFIED  
**Creator / Project Owner / Original Concept / Architecture Direction:** **NOEPIN / のえぴん**  
**Implementation / analysis / documentation support:** AI-assisted using ChatGPT

独立Trust Domainと2f+1基準を用い、重複Domain・無効署名・Equivocationを除外してByzantine耐性Quorum Candidateを評価するControlです。

## 公開内容
- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Core / Tests / Replay / Benchmark / Static Safety / Production Gateを、完成時の実物から内容を変更せず移送しています。
- README等の文書から類似コードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification
- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–122 / 86 of 86 PASS**
- DCSR: **DIRECT INTEGRATION / 直接統合**
- Final ZIP SHA-256: `c4a290eccef6f40a3f315a4363dd225b4e505a65846e82594380e21acfe9e684`

## Authority Boundary
- Candidate / Evaluation Result ≠ Permission Grant / Action Execution / Action Success
- DCSR Reconstruction ≠ Domain Authority / Safety Proof / Action Execution / Action Success

## Completion Evidence
- [NOEPIN_AL_123_FINAL_VERIFICATION_REPORT_20261109.md](NOEPIN_AL_123_FINAL_VERIFICATION_REPORT_20261109.md)
- [NOEPIN_AL_123_FINAL_ARTIFACT_SEAL_20261109.json](NOEPIN_AL_123_FINAL_ARTIFACT_SEAL_20261109.json)
- [NOEPIN_AL_123_SOURCE_INDEX.txt](NOEPIN_AL_123_SOURCE_INDEX.txt)

Verification Report / Artifact Seal / Source Indexは完成時の記録をそのまま保持しており、現在の公開表示に合わせて内容を書き換えていません。

## License
Current repository distribution: **Apache License 2.0**.

[Standalone work page](../works/123-byzantine-resilient-agent-quorum.md)
