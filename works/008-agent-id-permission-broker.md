# 008｜エージェントID・権限ブローカー / Agent ID & Permission Broker

**NOEPIN AL Technology Work 008**  
**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

## 作品概要

AI / AgentごとにIdentity、Role、Permit、Resource / Action Scope、期限、失効状態を分離し、最小権限で操作候補を判定するBrokerです。

Agentの存在やRoleの自己申告だけでAuthorityを認めず、Authoritative Stateを独立して確認します。

## 主な用途

外部AIと内部AIの権限分離、最小権限運用、役割別アクセス制御、Multi-Agent環境のAuthority管理など。

## 設計上の重要な境界

- Agent ID ≠ Authority
- Role claim ≠ Granted Role
- Permit presence ≠ Valid Permit
- Expired / Revoked Permit ≠ Authority
- Cached allow ≠ Current Authority
- Permission Decision ≠ Action Success

## 検証

- Unit / Boundary / Authority: **51 / 51 PASS**
- Fresh Extract: **51 / 51 PASS**
- Replay: **6,000 decisions**
- Replay divergence: **0**
- Baseline mutation: **0**
- External action / commit paths: **0**

## Integrity

Final ZIP SHA-256  
`5dc5265ed74587b00357089c3c5afc5692b7a7088cd30540298ef0e20f2a8d95`

Source SHA-256  
`f6019e53a15a5a76ff19240932ae54cc0a8d6d4bac9c97e474ccb5f41a90f266`

## 技術資料

[技術フォルダを開く](../008-agent-id-permission-broker/)  
[Verification Report](../008-agent-id-permission-broker/NOEPIN_AL_008_FINAL_VERIFICATION_REPORT_20261102.md)  
[Artifact Seal](../008-agent-id-permission-broker/NOEPIN_AL_008_FINAL_ARTIFACT_SEAL_20261102.json)

---

Creator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**  
Implementation / analysis / documentation support: AI-assisted using ChatGPT  
License: **Apache License 2.0** — see repository [LICENSE](../LICENSE) and [NOTICE](../NOTICE).

[作品一覧へ戻る](README.md)

## 検証済み実装
この技術はREADMEだけでなく、完成時Final ZIPに含まれていた検証済み実装・テスト等を、技術フォルダ内の [`verified_artifact/`](../008-agent-id-permission-broker/verified_artifact/) で確認できます。

Final ZIPにReplay / Benchmark / Production Gate等が含まれる場合は、それらも元のファイル名・内容のまま公開しています。

文書から類似コードを再生成して完成版として置き換えることはしていません。

