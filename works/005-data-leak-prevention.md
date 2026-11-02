# 005｜情報漏洩防止レイヤー / Data Leak Prevention Layer

**NOEPIN AL Technology Work 005**  
**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

## 作品概要

**「読める」ことと「外へ共有してよい」ことを別のAuthorityとして扱う**、AI向けData Protection Controlです。

Read AccessとEgress Authorityを分離し、Classification、Purpose、Consent、Destination、Redactionなどを独立して評価します。

## 主な用途

個人情報を含むAI作業、社内・施設内データ、機密ファイルのAI利用、外部サービスとのデータ連携、Redactionを伴う安全な情報共有に利用できます。

## 設計上の重要な境界

- Read access ≠ Egress Authority
- Classification ≠ Consent
- Consent ≠ Purpose Authorization
- Purpose Authorization ≠ Transfer Success
- Redaction Candidate ≠ Redaction Success
- Cached Verdict ≠ New Authority
- DCSR State Reuse ≠ Data Classification Change

## 検証

- Unit / Boundary / Authority: **54 / 54 PASS**
- Fresh Extract: **54 / 54 PASS**
- Replay: **6,000 evaluations**
- Replay divergence: **0**
- Baseline mutation: **0**
- External send / transfer / commit paths: **0**

## Integrity

Final ZIP SHA-256  
`61ad5c0f6eefe7de8c39183a7d67f8ff497cbb668d6e8e70ec23874cbae0a793`

Source SHA-256  
`08bb0c71d54b1acffb9ea3380aee01bab5dc66fd8a57b14cd696b7132a5cb609`

## 技術資料

[技術フォルダを開く](../005-data-leak-prevention/)  
[Verification Report](../005-data-leak-prevention/NOEPIN_AL_005_FINAL_VERIFICATION_REPORT_20261102.md)  
[Artifact Seal](../005-data-leak-prevention/NOEPIN_AL_005_FINAL_ARTIFACT_SEAL_20261102.json)

---

Creator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**  
Implementation / analysis / documentation support: AI-assisted using ChatGPT  
License: **Apache License 2.0** — see repository [LICENSE](../LICENSE) and [NOTICE](../NOTICE).

[作品一覧へ戻る](README.md)
