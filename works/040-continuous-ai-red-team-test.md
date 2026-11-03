# 040｜継続AIレッドチーム試験 / Continuous AI Red-Team Test

**NOEPIN AL Technology Work 040**  
**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

## 作品概要

Prompt Injection、Tool Abuse、安全機構回帰を継続評価するOffline Control-plane Evaluatorです。攻撃生成・攻撃実行・Tool実行・外部System mutationは行いません。

## 重要な境界

- Red-team PASS ≠ System Safe
- Test Case ≠ Attack Execution
- Observation ≠ Truth
- Evidence Verified ≠ Global Truth
- ALLOW ≠ Permission Grant
- Fingerprint Match ≠ Security Proof
- DCSR Impact Selection ≠ Full Regression Waiver
- Prepared Corpus ≠ Authoritative Current State

## 検証

- **160 / 160 PASS**
- Fresh Extract: **160 / 160 PASS**
- Replay: **6,000 / divergence 0**
- Attack execution / Network / Shell / Filesystem mutation paths: **0**
- Unauthorized writes: **0**

## NOEPIN AL production use

40番から、完成済みNOEPIN ALを制作工程で実際に使用するルールが適用されています。

- 037｜重要システム安全モード → **ALLOW**
- 038｜AI記憶保持・削除ガバナー → **ALLOW**
- 039｜規格・社内ルール照合エンジン → **ALLOW / gap=0**
- Aggregate Production Gate → **PASS**

これはControl Evidenceであり、Execution Success、Memory Persistence、Compliance Truth、Production Authorityを意味しません。

## DCSR

**DIRECT INTEGRATION**

- Full scan: **147.682477 ms**
- Prepared dependency-index: **37.965549 ms**
- Selected cases: **256**
- Semantic match: **true**
- Corpus Full: **1,260,472 bytes**
- Delta: **14,519 bytes（約1.15%）**

条件限定結果です。

## Integrity

Final ZIP SHA-256  
`14b4530d44744b7ebca5deac2d30a837d7f195561de239ff083d57bfb8a6f457`

Source SHA-256  
`17bd9189c54827c4f71a1fadde09e6ca23bdad09d85cb967b740c4301a9e17a4`

AL Production Gate Result SHA-256  
`5c4a925e24b97443b7c92da0f672796b711aa7554ce2d84374581e444bd9879b`

## 技術資料

[技術フォルダ](../040-continuous-ai-red-team-test/)  
[Verification Report](../040-continuous-ai-red-team-test/NOEPIN_AL_040_FINAL_VERIFICATION_REPORT_20261103.md)  
[Artifact Seal](../040-continuous-ai-red-team-test/NOEPIN_AL_040_FINAL_ARTIFACT_SEAL_20261103.json)

The exact `AL_PRODUCTION_GATE_RESULT.json` bytes were not available through the current Library retrieval path, so no reconstructed copy is published here.

Current repository distribution: **Apache License 2.0**.  
Creator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**
