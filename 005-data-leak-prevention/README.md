# 005 — Data Leak Prevention Layer / 情報漏洩防止レイヤー

> **「読める」ことと「外へ共有してよい」ことを別の権限として扱う**、AI向けData Protection Control。

**Status:** COMPLETE / VERIFIED  
**Category:** Data Protection  
**Creator:** **NOEPIN / のえぴん**

## この技術は何か

AIがある情報へアクセスできても、その情報を別のAI・API・システムへ共有してよいとは限りません。

情報漏洩防止レイヤーは、Read AccessとEgress Authorityを分離し、情報の分類、利用目的、Consent、Destination、Secret / Credential、Redaction条件などを独立して評価します。

## 想定用途

- 個人情報を含むAI作業
- 社内・施設内データ
- 機密ファイルのAI利用
- 外部サービスとのデータ連携
- Redactionを伴う安全な情報共有

## 設計の中心

このControlでは、少なくとも次の状態を分離して扱います。

- Data Classification
- Purpose constraint
- Consent
- Destination policy
- Secret / Credential state
- Restricted Identifier boundary
- Redaction requirement
- Egress Authority

つまり、アクセスできることを、そのまま共有権限へ昇格させません。

## Authority / Data boundary

- Read access ≠ Egress Authority
- Classification ≠ Consent
- Consent ≠ Purpose Authorization
- Purpose Authorization ≠ Transfer Success
- Redaction Candidate ≠ Redaction Success
- Cached Verdict ≠ New Authority
- DCSR State Reuse ≠ Data Classification Change

## DCSRとの関係

DCSRは**補助統合**です。

完全一致するRequest State + Policy VersionのみFingerprint/cache再利用を許可します。

DCSRはClassification、Consent、Purpose、Destination Policy、Egress Authorityを書き換えません。

Synthetic exact-state benchmark:

- 20,000 evaluations × 7 batches
- cache enabled median: **633.122 ms**
- cache disabled median: **1241.202 ms**

これは単一環境・完全一致Stateでの条件付き観測であり、一般的な高速化保証ではありません。

## Verification

- Unit / Boundary / Authority: **54 / 54 PASS**
- Fresh Extract: **54 / 54 PASS**
- Replay: **3,000 + 3,000 = 6,000 evaluations**
- Replay divergence: **0**
- Baseline mutation: **0**
- External send / transfer / commit paths: **0**

## Integrity

- Final artifact: `NOEPIN_AL_005_DLP_LAYER_SUCCESSOR_V2_20261102.zip`
- Source SHA-256: `08bb0c71d54b1acffb9ea3380aee01bab5dc66fd8a57b14cd696b7132a5cb609`
- Test SHA-256: `a806d8533ecf52fe2bb518455e486235c446672eab171e274fca4e643c61b271`
- Final ZIP SHA-256: `61ad5c0f6eefe7de8c39183a7d67f8ff497cbb668d6e8e70ec23874cbae0a793`

## このフォルダにあるもの

- README — 技術説明
- Final Verification Report — 検証内容
- Artifact Seal — 完成Artifactの識別情報

## Provenance

- Creator: **NOEPIN / のえぴん**
- Project Owner: **NOEPIN / のえぴん**
- Original Concept: **NOEPIN / のえぴん**
- Architecture Direction: **NOEPIN / のえぴん**
- Implementation / analysis / documentation support: AI-assisted using ChatGPT
- License: **Apache License 2.0** — see repository [LICENSE](../LICENSE) and [NOTICE](../NOTICE).

この技術は、NOEPIN / のえぴんのゲーム制作やAI利用環境で安全な情報境界が必要になったことから生まれた汎用技術です。
