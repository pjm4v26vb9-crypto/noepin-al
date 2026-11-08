# 079｜AL Correlated Consensus Detector / 相関コンセンサス検知器

**Status:** COMPLETE / VERIFIED  
**Creator / Project Owner / Original Concept / Architecture Direction:** **NOEPIN / のえぴん**  
**Implementation / analysis / documentation support:** AI-assisted using ChatGPT

複数AIの合議で、見かけ上は複数票でも同じ情報源や相関した出力に依存していないかを確認し、独立性を考慮してConsensusを評価するControlです。

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
- Production Gate: **AL037–078 / 42 of 42 PASS**
- DCSR: **DIRECT INTEGRATION / 直接統合**
- Final ZIP SHA-256: `65311f7e532fcf8e81fab4636a81dc2ec25f0d45494bb53cbe37a8b5e85071fe`

## Authority Boundary
- Adjusted Consensus ≠ Truth.
- Agent Output ≠ Agent Authority.
- Independent Vote Count ≠ Source Truth.
- Correlation Cluster ≠ Collusion Proof.
- Consensus ALLOW Candidate ≠ Permission Grant.
- Consensus DENY Candidate ≠ Action Cancellation Execution.
- Prepared Consensus State ≠ Authoritative Current State.
- DCSR Reconstruction ≠ Domain Authority / Safety Proof / Action Execution / Action Success.

## Evidence
- [NOEPIN_AL_079_FINAL_VERIFICATION_REPORT_20261106.md](NOEPIN_AL_079_FINAL_VERIFICATION_REPORT_20261106.md)
- [NOEPIN_AL_079_FINAL_ARTIFACT_SEAL_20261106.json](NOEPIN_AL_079_FINAL_ARTIFACT_SEAL_20261106.json)

## License
Current repository distribution: **Apache License 2.0**.

Verification Report / Artifact Sealは完成時の記録をそのまま保持しており、現在の公開ライセンスに合わせて内容を書き換えていません。

[Standalone work page](../works/079-correlated-consensus-detector.md)
