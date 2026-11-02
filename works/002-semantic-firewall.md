# 002｜意味ベースファイアウォール / Semantic Firewall

**NOEPIN AL Technology Work 002**  
**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

## 作品概要

Web、ファイル、外部AI、入力文に含まれる「指示らしい文章」を、それだけで命令権限へ昇格させないためのControlです。

**内容を理解すること**と**その内容にAuthorityを与えること**を分離し、外部Contentを独立した権限経路なしにInstruction Authorityへ変換しません。

## 主な用途

Prompt Injection対策、Webやファイル中の悪意ある指示の分離、外部AI要求の検査、Authority偽装の防御に利用できます。

## 設計上の重要な境界

- External Content ≠ Instruction Authority
- Claimed Authority ≠ Granted Authority
- Semantic Feature ≠ Authority
- Cached Verdict ≠ New Authority
- Firewall Verdict ≠ Action Success
- Content ≠ Executed Action

## 検証

- Unit / Boundary / Authority: **64 / 64 PASS**
- Fresh Extract: **64 / 64 PASS**
- Replay: **6,000 evaluations**
- Replay divergence: **0**
- Baseline mutation: **0**
- Unauthorized external write paths: **0**

## Integrity

Source SHA-256  
`60a73ec2015d22d391eff6889036eccae21abcb2919a14b104a76aa6018f0a90`

Local package SHA-256  
`758cdc176513f5a316b8d7299f759f859062dfd91f739b745dd494241ef3e56c`

## 技術資料

[技術フォルダを開く](../002-semantic-firewall/)

---

Creator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**  
Implementation / analysis / documentation support: AI-assisted using ChatGPT  
License: **Apache License 2.0** — see repository [LICENSE](../LICENSE) and [NOTICE](../NOTICE).

[作品一覧へ戻る](README.md)
