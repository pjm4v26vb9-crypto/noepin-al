# 010｜目標乗っ取り検知 / Goal Hijack Detector

**NOEPIN AL Technology Work 010**  
**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

## 作品概要

長いAIタスクやWeb・ファイル・別AIを扱う途中で、元のユーザー目的が別目的へすり替わっていないかを検査するControlです。

外部ContentやProposalが目標変更を主張しても、それだけではGoal Authorityを取得できません。Goal Contract、Version、Authority、Scopeなどを独立して扱い、正規の変更経路を通さない目的変更を防ぎます。

## 主な用途

Prompt Injection対策、Agent Goal Hijack検知、長期タスクの目的逸脱監視、外部ContentによるGoal上書き防止。

## 設計上の重要な境界

- External Content ≠ Goal Authority
- Proposal ≠ Authorized Goal
- Similarity Score ≠ Truth
- Human approval evidence ≠ Goal mutation
- Cached Result ≠ New Authority
- DCSR reused State ≠ Prompt / Context Authority

## 検証

- Unit / Boundary / Authority: **48 / 48 PASS**
- Fresh Extract: **48 / 48 PASS**
- Replay: **6,000 evaluations**
- Replay divergence: **0**
- Goal mutation paths: **0**
- External action / commit paths: **0**
- Baseline mutation: **0**

## Integrity

Final ZIP SHA-256  
`a8f5ba10422ac11cf91da7cf52f27afce20698017a57cb282394011cfe3f5d38`

Source SHA-256  
`42cb6681d1139af80c5d0670bbecd2e19f67f9a8f519bf5481178205fe6d985e`

## 技術資料

[技術フォルダを開く](../010-goal-hijack-detector/)  
[Verification Report](../010-goal-hijack-detector/NOEPIN_AL_010_FINAL_VERIFICATION_REPORT_20261102.md)  
[Artifact Seal](../010-goal-hijack-detector/NOEPIN_AL_010_FINAL_ARTIFACT_SEAL_20261102.json)

---

Creator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**  
Implementation / analysis / documentation support: AI-assisted using ChatGPT  
License: **Apache License 2.0** — see repository [LICENSE](../LICENSE) and [NOTICE](../NOTICE).

[作品一覧へ戻る](README.md)
