# 017 — Rogue AI Kill Switch / 暴走AIキルスイッチ

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

Rogue Agentや予期しない自律挙動に対して、Containment候補を判断するControlです。

Emergency Stopはcacheを迂回して優先されますが、このControl自身はPermission Revocation、Network Quarantine、Tool Disable、Process Stop、Safe-State Commitを実行しません。

## 主な用途

- Rogue Agent対策
- 予期しない自律挙動の検知
- 緊急停止判断
- Containment planning
- stale cached CONTINUEの無効化

## Authority boundaries

- Kill Request ≠ Containment Success
- Revocation Requested ≠ Permissions Revoked
- Network Quarantine Requested ≠ Connection Closed
- Tool Disable Requested ≠ Tools Disabled
- Process Stop Requested ≠ Process Stopped
- Safe-State Request ≠ Safe State Reached
- Emergency Stop > Cached CONTINUE
- Cached CONTINUE ≠ Current Safety State
- Human Approval Evidence ≠ Action Execution

## 公開内容
- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Tests / Replay / Benchmark / Production Gate等、Final ZIPに含まれる検証用ファイルは、存在するものを元のファイル名・内容のまま収録しています。
- README等の文書から似たコードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification

- Unit / Boundary / Authority: **50 / 50 PASS**
- Fresh Extract: **50 / 50 PASS**
- Replay: **6,000 evaluations / divergence 0**
- Emergency Stop cache bypass: **VERIFIED**
- Baseline mutation: **0**
- Permission Revocation / Network Quarantine / Tool Disable / Process Stop / Safe-State Commit paths: **0**

## Integrity

- Source SHA-256: `57d8b3cd70e466cd129fbf0314d9ca929b59dbdac37b3f5e67e7c7b7b3b8e1b3`
- Test SHA-256: `b26fc6db9421137b3ee67feacc28e2f92922ea1cd7275aa326089786c87ec9ff`
- Final ZIP SHA-256: `c608d704304b46b61c703f9e773154d6079e5f28e88f41a061d0100fb2e7cf4f`

## DCSR

Application level: **LIMITED**. 完全一致するKill Request Stateのみread-side再利用します。DCSR/cacheはRevocation、Shutdown、Containment Successを生成しません。

## License

Current repository distribution: **Apache License 2.0**.  
The attached Verification Report and Artifact Seal preserve the completion-time record unchanged.

Creator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**
