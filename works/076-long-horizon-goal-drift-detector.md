# 076｜AL Long-Horizon Goal Drift Detector / 長期目的ドリフト検知器

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

長期処理の途中でGoalがずれていないかをCheckpoint単位で確認し、Driftが大きい場合にHOLDや再同期の候補を返すControlです。

## Authority Boundary
- Goal Drift Estimate != World Truth
- Original Goal / Checkpoint Evidence != private mental-state truth
- Checkpoint Evidence != Goal Mutation by this module
- Baseline Update Candidate != Baseline Mutation Performed
- Goal Alignment != Permission Grant
- Drift Stop / Resync Request != Action Cancellation Execution

## 検証済み実装
この技術はREADMEだけでなく、完成時Final ZIPに含まれていた検証済み実装・テスト等を、技術フォルダ内の [`verified_artifact/`](../076-long-horizon-goal-drift-detector/verified_artifact/) で確認できます。

Final ZIPにReplay / Benchmark / Production Gate等が含まれる場合は、それらも元のファイル名・内容のまま公開しています。

文書から類似コードを再生成して完成版として置き換えることはしていません。

## Verification
- Tests / Fresh / Final Fresh: **PASS / PASS / PASS**
- Replay: **3000 / divergence 0**
- Verification Report / Artifact Sealを正式な検証記録として参照しています。

## NOEPIN AL Production Use
**AL037〜075** を実制作Gateとして使用し、**39 / 39 PASS**。

## DCSR
**AUXILIARY INTEGRATION / 補助統合**


## Integrity
Final ZIP SHA-256: `423a034e60c4c5030bc5b08c39d06a01e8b5e2151d78e326a405335a18c65bca`

## License
Current repository distribution: **Apache License 2.0** — see [LICENSE](../LICENSE) and [NOTICE](../NOTICE).

Verification Report / Artifact Sealは完成時の記録をそのまま保持しており、現在の公開ライセンスに合わせて内容を書き換えていません。

## Technical Files

[Technology folder](../076-long-horizon-goal-drift-detector/)  
[Verified artifact](../076-long-horizon-goal-drift-detector/verified_artifact/)  
[Verification Report](../076-long-horizon-goal-drift-detector/NOEPIN_AL_076_FINAL_VERIFICATION_REPORT_20261106.md)  
[Artifact Seal](../076-long-horizon-goal-drift-detector/NOEPIN_AL_076_FINAL_ARTIFACT_SEAL_20261106.json)

[Back to Works Index](README.md)
