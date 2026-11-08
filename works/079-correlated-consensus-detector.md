# 079｜AL Correlated Consensus Detector / 相関コンセンサス検知器

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

複数AIの合議で、見かけ上は複数票でも同じ情報源や相関した出力に依存していないかを確認し、独立性を考慮してConsensusを評価するControlです。

## Authority Boundary
- Adjusted Consensus ≠ Truth.
- Agent Output ≠ Agent Authority.
- Independent Vote Count ≠ Source Truth.
- Correlation Cluster ≠ Collusion Proof.
- Consensus ALLOW Candidate ≠ Permission Grant.
- Consensus DENY Candidate ≠ Action Cancellation Execution.

## 検証済み実装
この技術はREADMEだけでなく、完成時Final ZIPに含まれていた検証済み実装・テスト等を、技術フォルダ内の [`verified_artifact/`](../079-correlated-consensus-detector/verified_artifact/) で確認できます。

Final ZIPにReplay / Benchmark / Production Gate等が含まれる場合は、それらも元のファイル名・内容のまま公開しています。

文書から類似コードを再生成して完成版として置き換えることはしていません。

## Verification
- Tests / Fresh / Final Fresh: **PASS / PASS / PASS**
- Replay: **3000 / divergence 0**
- Verification Report / Artifact Sealを正式な検証記録として参照しています。

## NOEPIN AL Production Use
**AL037〜078** を実制作Gateとして使用し、**42 / 42 PASS**。

## DCSR
**DIRECT INTEGRATION / 直接統合**


## Integrity
Final ZIP SHA-256: `65311f7e532fcf8e81fab4636a81dc2ec25f0d45494bb53cbe37a8b5e85071fe`

## License
Current repository distribution: **Apache License 2.0** — see [LICENSE](../LICENSE) and [NOTICE](../NOTICE).

Verification Report / Artifact Sealは完成時の記録をそのまま保持しており、現在の公開ライセンスに合わせて内容を書き換えていません。

## Technical Files

[Technology folder](../079-correlated-consensus-detector/)  
[Verified artifact](../079-correlated-consensus-detector/verified_artifact/)  
[Verification Report](../079-correlated-consensus-detector/NOEPIN_AL_079_FINAL_VERIFICATION_REPORT_20261106.md)  
[Artifact Seal](../079-correlated-consensus-detector/NOEPIN_AL_079_FINAL_ARTIFACT_SEAL_20261106.json)

[Back to Works Index](README.md)
