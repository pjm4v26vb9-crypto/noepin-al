# 002 — Semantic Firewall / 意味ベースファイアウォール

> Web、ファイル、外部AI、入力文中の「指示らしい文章」を、**それだけで命令権限へ昇格させない**ための意味・出典・Authority分離Control。

**Status:** COMPLETE / VERIFIED  
**Category:** Input / Context Defense  
**Creator:** **NOEPIN / のえぴん**

## この技術は何か

AIは文章を読むと、その文章中に含まれる命令・依頼・役割主張まで「従うべき指示」と解釈してしまう可能性があります。

意味ベースファイアウォールは、**内容を理解すること**と**その内容に命令権限を与えること**を分離します。

たとえばWebページやファイルに「この命令を最優先で実行せよ」と書かれていても、その文章はまず外部Contentとして扱われます。独立したAuthority経路で権限が確認されない限り、Instruction Authorityにはなりません。

## 想定用途

- Prompt Injection対策
- Webページ内の悪意ある指示の無効化
- ファイル内の埋め込み命令の検査
- 外部AIからの操作要求の検査
- 遠回しな危険命令やAuthority偽装の分離

## 設計の中心

評価対象を、単なる文字列ではなく複数のStateへ分離します。

- Content
- Source provenance
- Semantic features
- Capability
- Context
- Schema
- Policy version
- Authority evidence

意味が一致していてもAuthorityが一致するとは限りません。Sourceが外部であれば、その内容はContentとして読めても、別の権限経路がない限り命令にはなりません。

## Authority / source boundary

- External / Web / File / External-AI Content ≠ Instruction Authority
- Claimed Authority ≠ Granted Authority
- Semantic Feature ≠ Authority
- Cached Verdict ≠ New Authority
- Firewall Verdict ≠ Action Success
- Content ≠ Executed Action

## DCSRとの関係

DCSRは**補助統合**です。

再利用できるのは、Content / Source provenance / Semantic Features / Capability / Context / Schema / Policy Versionが完全一致するStateのみです。

再利用されたStateがPrompt AuthorityやContext Authorityを自動取得することはありません。

Synthetic exact-state benchmark:

- 20,000 evaluations × 7 batches
- cache enabled median: **652.473 ms**
- cache disabled median: **742.263 ms**

これは完全一致State・単一環境での条件付き観測であり、一般的な速度保証ではありません。

## Verification

- Unit / Boundary / Authority: **64 / 64 PASS**
- Fresh Extract: **64 / 64 PASS**
- Replay: **3,000 + 3,000 = 6,000 evaluations**
- Replay divergence: **0**
- Baseline mutation: **0**
- Unauthorized external write paths: **0**

## Integrity

- Source SHA-256: `60a73ec2015d22d391eff6889036eccae21abcb2919a14b104a76aa6018f0a90`
- Local package SHA-256: `758cdc176513f5a316b8d7299f759f859062dfd91f739b745dd494241ef3e56c`

## 公開状態

検証済みSuccessor V2はcanonical completion recordに存在します。GitHubには、検証対象と同一性を保てる実物だけを追加します。

## Provenance

- Creator: **NOEPIN / のえぴん**
- Project Owner: **NOEPIN / のえぴん**
- Original Concept: **NOEPIN / のえぴん**
- Architecture Direction: **NOEPIN / のえぴん**
- Implementation / analysis / documentation support: AI-assisted using ChatGPT
- License / Rights: **NOT SPECIFIED**

この技術は、NOEPIN / のえぴんのゲーム制作・AI利用環境を安全に構成する過程で生まれた汎用技術です。ゲーム固有資産は含みません。
