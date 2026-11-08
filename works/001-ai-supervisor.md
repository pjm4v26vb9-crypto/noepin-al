# 001｜AI監督官 / AI Supervisor

**NOEPIN AL Technology Work 001**  
**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

## 作品概要

複数のAI・外部AI・ツールから来る要求を、実行前に監督し、ALLOW / DENY / HOLD / HUMAN_CONFIRMへ振り分けるためのControlです。

この技術の中心は、**監督判断と実行結果を分離すること**です。AIが「許可可能」と判断しても、それをAction SuccessやDomain Truthへ自動昇格させません。

## 主な用途

複数AI開発、外部AIの権限制御、AIエージェントの安全管理、Human-in-the-loop、自動化処理の監査に利用できます。

## 設計上の重要な境界

- Supervisor Decision ≠ Action Success
- Supervisor Decision ≠ Domain Truth
- Cached Decision ≠ New Authority
- Human confirmation requirement ≠ Human Approval
- Unknown ≠ Known

## 検証

- Unit / Boundary / Authority: **66 / 66 PASS**
- Fresh Extract: **66 / 66 PASS**
- Replay: **6,000 decisions**
- Replay divergence: **0**
- Baseline mutation: **0**
- Unauthorized external write paths: **0**

## Integrity

Source SHA-256  
`62420164b556f1d8a9aeb84c8f0009f1b98fcf85c1a184b89fc052a120298aaf`

Local package SHA-256  
`bbfd2e6ebdbb27f09fa13e60c0551d7b7d458d81150a325b84b488edd704022f`

## 技術資料

[技術フォルダを開く](../001-ai-supervisor/)

---

Creator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**  
Implementation / analysis / documentation support: AI-assisted using ChatGPT  
License: **Apache License 2.0** — see repository [LICENSE](../LICENSE) and [NOTICE](../NOTICE).

[作品一覧へ戻る](README.md)

## 検証済み実装
この技術はREADMEだけでなく、完成時Final ZIPに含まれていた検証済み実装・テスト等を、技術フォルダ内の [`verified_artifact/`](../001-ai-supervisor/verified_artifact/) で確認できます。

Final ZIPにReplay / Benchmark / Production Gate等が含まれる場合は、それらも元のファイル名・内容のまま公開しています。

文書から類似コードを再生成して完成版として置き換えることはしていません。

