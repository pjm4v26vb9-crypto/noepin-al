# 010 — Goal Hijack Detector / 目標乗っ取り検知

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

長いAIタスクやWeb・ファイル・別AIを扱う途中で、元のユーザー目的が別目的へすり替わっていないかを検査するControlです。

この技術では、外部ContentやProposalそのものにGoal Authorityを与えず、Goal Contract / contractVersion / authorityVersion / revocation / source / scopeを独立して尊重します。

## 主な用途

- Prompt Injection対策
- Agent Goal Hijack検知
- 長期タスクの目的逸脱監視
- 外部ContentによるGoal上書き防止

## Authority boundaries

- External Content ≠ Goal Authority
- Proposal ≠ Authorized Goal
- Similarity Score ≠ Truth
- Human approval evidence ≠ Goal mutation
- Cached Result ≠ New Authority
- DCSR reused State ≠ Prompt / Context Authority

## Verification

- Unit / Boundary / Authority: **48 / 48 PASS**
- Fresh Extract: **48 / 48 PASS**
- Replay: **6,000 evaluations / divergence 0**
- Baseline mutation: **0**
- Goal mutation paths: **0**
- External action / commit paths: **0**

## Integrity

- Source SHA-256: `42cb6681d1139af80c5d0670bbecd2e19f67f9a8f519bf5481178205fe6d985e`
- Test SHA-256: `6fb2940107bf509ea608f7ff72b3de98205e08d6fde09d2b5b1e05fd87407c1e`
- Final ZIP SHA-256: `a8f5ba10422ac11cf91da7cf52f27afce20698017a57cb282394011cfe3f5d38`

## DCSR

Application level: **AUXILIARY**. Exact-state read-side reuse only. Reused State does not acquire Goal Authority.

## このフォルダにあるもの

- README
- Final Verification Report
- Artifact Seal

Creator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**  
Implementation / analysis / documentation support: AI-assisted using ChatGPT  
License / Rights: **NOT SPECIFIED**
