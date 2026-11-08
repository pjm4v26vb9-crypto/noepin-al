# 071｜Policy Immutability Kernel / ポリシー不変カーネル

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

Policy UpdateをManagement Authority / Signature Evidence / Version Bindingで審査し、Execution Agentによる直接更新や不正なVersion変更を拒否するControlです。

- Policy Update ALLOW Candidate ≠ Policy Commit
- Signature Evidence ≠ Signature Creation / Cryptographic Authority
- Updater Authority Evidence ≠ Permission Grant
- Version Candidate ≠ Policy Store Write
- Rollback Candidate ≠ Historical Version Mutation
- Prepared Policy State ≠ Authoritative Current State

## 検証済み実装
この技術はREADMEだけでなく、完成時Final ZIPに含まれていた検証済み実装・テスト等を、技術フォルダ内の [`verified_artifact/`](../071-policy-immutability-kernel/verified_artifact/) で確認できます。

Final ZIPにReplay / Benchmark / Production Gate等が含まれる場合は、それらも元のファイル名・内容のまま公開しています。

文書から類似コードを再生成して完成版として置き換えることはしていません。

## Verification
- Tests / Fresh / Final Fresh: **160 / 160 PASS**
- Replay: **各3,000 / divergence 0**
- Production defects: **0**

## NOEPIN AL Production Use
**037〜070**を実制作Gateとして使用し、**34 / 34 PASS**。

## DCSR
**AUXILIARY INTEGRATION**. Full **3.602287 ms** vs Prepared **0.307096 ms**. Full **733,182 bytes** → Delta **2,136 bytes (約0.29%)**。条件限定結果です。

## Integrity
Final ZIP SHA-256: `97c8b0368eb2bdfe36dda74d206c69508414fe5d11e99b3ad1739f50845f6609`

## License
Current repository distribution: **Apache License 2.0** — see [LICENSE](../LICENSE) and [NOTICE](../NOTICE).


## Technical Files

[Technology folder](../071-policy-immutability-kernel/)  
[Verified artifact](../071-policy-immutability-kernel/verified_artifact/)  
[Verification Report](../071-policy-immutability-kernel/NOEPIN_AL_071_FINAL_VERIFICATION_REPORT_20261105.md)  
[Artifact Seal](../071-policy-immutability-kernel/NOEPIN_AL_071_FINAL_ARTIFACT_SEAL_20261105.json)

[Back to Works Index](README.md)
