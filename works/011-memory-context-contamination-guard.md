# 011｜メモリ・文脈汚染ガード / Memory & Context Contamination Guard

**NOEPIN AL Technology Work 011**  
**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

## 作品概要

AI MemoryやRAG Contextへ入る情報を、そのままMemory・Truth・Instruction Authorityとして扱わないためのControlです。

Memory Candidate、Source、TTL、Confidence、Verificationなどを分離し、候補を永続Memoryへ昇格させる権限をGuard自身には持たせません。

## 主な用途

AI Memoryの安全管理、RAG文脈の汚染防止、悪意ある指示の永続化防止、Retrieved ContextのAuthority分離。

## 設計上の重要な境界

- Memory Candidate ≠ Memory
- Memory ≠ Truth
- Conversation Mention ≠ Memory
- Retrieved Context ≠ Instruction Authority
- Source Claim ≠ Verified Authority
- Cached Verdict ≠ New Authority

## 検証

- Unit / Boundary / Authority: **46 / 46 PASS**
- Fresh Extract: **46 / 46 PASS**
- Replay: **6,000 evaluations**
- Replay divergence: **0**
- Memory write paths: **0**
- External action / commit paths: **0**
- Baseline mutation: **0**

## Integrity

Final ZIP SHA-256  
`2d57309c94277ccdd97b0056a51bc5f6ced1fe40952e37f7cf7ce0614790a7d5`

Source SHA-256  
`ebf68b9e42d7931a7bedf50e4e34beb62305759a7bbb44217c7646090882dbe3`

## 技術資料

[技術フォルダを開く](../011-memory-context-contamination-guard/)  
[Verification Report](../011-memory-context-contamination-guard/NOEPIN_AL_011_FINAL_VERIFICATION_REPORT_20261102.md)  
[Artifact Seal](../011-memory-context-contamination-guard/NOEPIN_AL_011_FINAL_ARTIFACT_SEAL_20261102.json)

---

Creator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**  
Implementation / analysis / documentation support: AI-assisted using ChatGPT  
License / Rights: **NOT SPECIFIED**

[作品一覧へ戻る](README.md)
