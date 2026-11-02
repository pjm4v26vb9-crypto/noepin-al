# 006｜AI同士の仲裁役 / AI-to-AI Arbitrator

**NOEPIN AL Technology Work 006**  
**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

## 作品概要

複数AIが異なる提案を出したとき、単純な多数決ではなく、Evidence・Risk・Policy・Authorityを分離して比較する仲裁Controlです。

この技術では、候補選択をTruth確定やAction Successへ自動昇格させません。

## 主な用途

Multi-agent development、複数モデルによるレビュー、設計判断、AI間の役割分担、複数候補からの安全な候補選定に利用できます。

## 設計上の重要な境界

- **Majority ≠ Truth**
- **Evidence Score ≠ Truth**
- Agent Claim ≠ Authority
- **Selected Proposal ≠ Action Success**
- Human Override Evidence ≠ Action Execution
- Fingerprint Match ≠ Authority Match
- Cached Arbitration ≠ New Authority

## 検証

- Unit / Boundary / Authority: **49 / 49 PASS**
- Fresh Extract: **49 / 49 PASS**
- Replay: **6,000 arbitrations**
- Replay divergence: **0**
- Baseline mutation: **0**
- External Action / commit paths: **0**

## Integrity

Final ZIP SHA-256  
`22078f19b3fed04099adbd5686af23420b7a8265ff66bdd31c260eb53757f33a`

Source SHA-256  
`9d0bd198bed1866f8f13d35a3eb276998dbd2380e2526510b63cb5d12269a7c2`

## 技術資料

[技術フォルダを開く](../006-ai-to-ai-arbitrator/)  
[Verification Report](../006-ai-to-ai-arbitrator/NOEPIN_AL_006_FINAL_VERIFICATION_REPORT_20261102.md)  
[Artifact Seal](../006-ai-to-ai-arbitrator/NOEPIN_AL_006_FINAL_ARTIFACT_SEAL_20261102.json)

---

Creator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**  
Implementation / analysis / documentation support: AI-assisted using ChatGPT  
License: **Apache License 2.0** — see repository [LICENSE](../LICENSE) and [NOTICE](../NOTICE).

[作品一覧へ戻る](README.md)
