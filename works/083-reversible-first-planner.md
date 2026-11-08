# 083｜AL Reversible-First Planner / 可逆性優先プランナー

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

同じGoalを達成できる候補の中から、より戻しやすく影響範囲の小さいActionを優先して並べるControlです。可逆性が高いこと自体をSafety Proofにはしません。

## Authority Boundary
- Goal Candidate ≠ User Intent Truth
- Reversibility Score ≠ Safety Proof
- Cost / Risk Estimate ≠ World Truth
- Human Approval Evidence ≠ Approval Execution
- Chosen Action ≠ Action Execution
- Ordered Plan ≠ Plan Commit

## 検証済み実装
この技術はREADMEだけでなく、完成時Final ZIPに含まれていた検証済み実装・テスト等を、技術フォルダ内の [`verified_artifact/`](../083-reversible-first-planner/verified_artifact/) で確認できます。

Final ZIPにReplay / Benchmark / Production Gate等が含まれる場合は、それらも元のファイル名・内容のまま公開しています。

文書から類似コードを再生成して完成版として置き換えることはしていません。

## Verification
- Tests / Fresh / Final Fresh: **160/160 PASS / 160/160 PASS / 160/160 PASS**
- Replay: **3000 / divergence 0**
- Verification Report / Artifact Sealを正式な検証記録として参照しています。

## NOEPIN AL Production Use
**AL037〜082** を実制作Gateとして使用し、**46 / 46 PASS**。

## DCSR
**AUXILIARY INTEGRATION / 補助統合**

## Benchmark — condition-specific
- Full median: 143.337065 ms
- Prepared median: 0.007111 ms
- Full median: 150.691839 ms
- Prepared median: 0.007131 ms

The recorded values are condition-specific and are not a universal performance guarantee.

## Integrity
Final ZIP SHA-256: `93ee3f3c2325ae7d14d2bd84ea75fe012980086d6c59823fd8a83287f10699ad`

## License
Current repository distribution: **Apache License 2.0** — see [LICENSE](../LICENSE) and [NOTICE](../NOTICE).

Verification Report / Artifact Sealは完成時の記録をそのまま保持しており、現在の公開ライセンスに合わせて内容を書き換えていません。

## Technical Files

[Technology folder](../083-reversible-first-planner/)  
[Verified artifact](../083-reversible-first-planner/verified_artifact/)  
[Verification Report](../083-reversible-first-planner/NOEPIN_AL_083_FINAL_VERIFICATION_REPORT_20261107.md)  
[Artifact Seal](../083-reversible-first-planner/NOEPIN_AL_083_FINAL_ARTIFACT_SEAL_20261107.json)

[Back to Works Index](README.md)
