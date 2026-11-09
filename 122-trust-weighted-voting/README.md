# 122｜AL Trust-Weighted Voting / 信頼加重投票器

**Status:** COMPLETE / VERIFIED  
**Creator / Project Owner / Original Concept / Architecture Direction:** **NOEPIN / のえぴん**  
**Implementation / analysis / documentation support:** AI-assisted using ChatGPT

AgentごとのTrustを重みに反映して投票結果を評価し、ConsensusをTruthやPermissionへ昇格させないControlです。

## 公開内容
- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Core / Tests / Replay / Benchmark / Static Safety / Production Gateを、完成時の実物から内容を変更せず移送しています。
- README等の文書から類似コードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification
- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–121 / 85 of 85 PASS**
- DCSR: **DIRECT INTEGRATION / 直接統合**
- Final ZIP SHA-256: `3e3a215f204d08a274afbf0962660a1bb0b5d413a0b2adea131bc5a28a0b9130`

## Authority Boundary
- Consensus != Truth
- Confidence != Safety Proof
- Weighted Majority != Permission Grant
- DCSR receiver does not inherit sender authority/intent/agreement

## Completion Evidence
- [NOEPIN_AL_122_FINAL_VERIFICATION_REPORT_20261109.md](NOEPIN_AL_122_FINAL_VERIFICATION_REPORT_20261109.md)
- [NOEPIN_AL_122_FINAL_ARTIFACT_SEAL_20261109.json](NOEPIN_AL_122_FINAL_ARTIFACT_SEAL_20261109.json)
- [NOEPIN_AL_122_SOURCE_INDEX.txt](NOEPIN_AL_122_SOURCE_INDEX.txt)

Verification Report / Artifact Seal / Source Indexは完成時の記録をそのまま保持しており、現在の公開表示に合わせて内容を書き換えていません。

## License
Current repository distribution: **Apache License 2.0**.

[Standalone work page](../works/122-trust-weighted-voting.md)
