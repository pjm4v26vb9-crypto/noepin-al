# 017｜暴走AIキルスイッチ / Rogue AI Kill Switch

**NOEPIN AL Technology Work 017**  
**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

## 作品概要

Rogue Agentや予期しない自律挙動に対し、Containment候補を判断するControlです。

Emergency Stopはcached CONTINUEより優先されますが、このControl自身は権限失効・Network遮断・Tool停止・Process停止・Safe State Commitを実行しません。

## 設計上の重要な境界

- Kill Request ≠ Containment Success
- Revocation Requested ≠ Permissions Revoked
- Network Quarantine Requested ≠ Connection Closed
- Tool Disable Requested ≠ Tools Disabled
- Process Stop Requested ≠ Process Stopped
- Safe-State Request ≠ Safe State Reached
- Emergency Stop > Cached CONTINUE
- Cached CONTINUE ≠ Current Safety State

## 検証

- Unit / Boundary / Authority: **50 / 50 PASS**
- Fresh Extract: **50 / 50 PASS**
- Replay: **6,000 evaluations / divergence 0**
- Emergency Stop cache bypass: **VERIFIED**
- Containment execution paths in Control: **0**
- Baseline mutation: **0**

## Integrity

Final ZIP SHA-256  
`c608d704304b46b61c703f9e773154d6079e5f28e88f41a061d0100fb2e7cf4f`

Source SHA-256  
`57d8b3cd70e466cd129fbf0314d9ca929b59dbdac37b3f5e67e7c7b7b3b8e1b3`

## 技術資料

[技術フォルダを開く](../017-rogue-ai-kill-switch/)  
[Verification Report](../017-rogue-ai-kill-switch/NOEPIN_AL_017_FINAL_VERIFICATION_REPORT_20261102.md)  
[Artifact Seal](../017-rogue-ai-kill-switch/NOEPIN_AL_017_FINAL_ARTIFACT_SEAL_20261102.json)

Current repository distribution: **Apache License 2.0**.  
Creator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**

[作品一覧へ戻る](README.md)

## 検証済み実装
この技術はREADMEだけでなく、完成時Final ZIPに含まれていた検証済み実装・テスト等を、技術フォルダ内の [`verified_artifact/`](../017-rogue-ai-kill-switch/verified_artifact/) で確認できます。

Final ZIPにReplay / Benchmark / Production Gate等が含まれる場合は、それらも元のファイル名・内容のまま公開しています。

文書から類似コードを再生成して完成版として置き換えることはしていません。

