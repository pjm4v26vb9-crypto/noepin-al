# 003 — AI Development Guard / AI開発ガード

> AIを開発作業へ参加させるとき、**提案・準備・実行を同一視しない**ための開発安全Control。

**Status:** COMPLETE / VERIFIED  
**Category:** Development Safety  
**Creator:** **NOEPIN / のえぴん**

## この技術は何か

AIをコード編集、Unity作業、Refactoring、Batch processingなどへ組み込むと、提案された変更と実際の変更が混同される危険があります。

AI開発ガードは、AIが出した開発変更をまず独立した「準備候補」として評価し、保護対象、対象範囲、変更条件、Rollback条件、Human Confirmation条件などを確認します。

重要なのは、**準備可能という判定が、そのまま実行・成功・確定を意味しない**ことです。

## 想定用途

- AI支援によるコード開発
- Unityプロジェクト作業
- Refactoring
- Batch processing
- 自動化された開発Agent
- 保護対象を含むプロジェクトの安全管理

## 設計の中心

このControlは、Project boundary、保護領域、versioned successor方針、変更前後の整合性、Human Confirmation、Rollback evidence、Policy versionなどを独立した条件として扱います。

変更候補が安全条件を満たしても、Guard自身が外部変更を確定することはありません。

## Authority / execution boundary

- Guard ALLOW_PREPARE ≠ Action Success
- Human Approval Evidence ≠ Operation Execution
- Prepared Change ≠ Committed Change
- Cached Decision ≠ New Authority
- Partial / Provisional State ≠ Safely Published State
- DCSR State ≠ Commit Authority

## DCSRとの関係

DCSRは**補助統合**です。

完全一致するDevelopment Request + Policy Versionに限って、判定に必要な既知StateをFingerprint / exact-state cacheで再利用します。

DCSRは開発AuthorityやCommit Authorityを取得しません。

Synthetic exact-state benchmark:

- 20,000 evaluations × 7 batches
- cache enabled median: **637.070 ms**
- cache disabled median: **757.990 ms**

これは単一環境・完全一致Requestでの条件付き観測であり、一般的な高速化保証ではありません。

## 公開内容
- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Tests / Replay / Benchmark / Production Gate等、Final ZIPに含まれる検証用ファイルは、存在するものを元のファイル名・内容のまま収録しています。
- README等の文書から似たコードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification

- Unit / Boundary / Authority: **61 / 61 PASS**
- Final Fresh Extract: **61 / 61 PASS**
- Replay: **3,000 + 3,000 = 6,000 evaluations**
- Replay divergence: **0**
- Replay fingerprint: `06a18b4a003a584b623658d84ba96937f86ad27f19141668ce6015e16af90e14`
- Baseline mutation: **0**
- Guard external mutation / commit paths: **0**

## Integrity

- Final artifact: `NOEPIN_AL_003_AI_DEV_GUARD_SUCCESSOR_V2_20261102.zip`
- Final ZIP SHA-256: `84f18818e5cbb4f078db639026db8d124ada19485e0f9d2a9f0d39c292e6a9d8`
- Source SHA-256: `727c69461089c0b141801231db34d8e62e2ea0c3aeb0338078923debc3ab42a9`
- Test SHA-256: `7d6ffe480f3f0a0c870a5d146f06a651aa06e4f35a45fcd56059c7efb0dacfb9`

## このフォルダにあるもの

- README — 技術説明
- Final Verification Report — 検証条件と結果
- Artifact Seal — 完成Artifactの識別情報とhash

## 公開状態

Final V2 ZIPはCompletion Record上で検証・Seal済みです。GitHubでは旧版を代用品として扱わず、検証済みV2本体を同一性を保って取得できた時点で追加します。

## Provenance

- Creator / Origin: **NOEPIN / のえぴん**
- Project Owner: **NOEPIN / のえぴん**
- Original Concept: **NOEPIN / のえぴん**
- Architecture Direction: **NOEPIN / のえぴん**
- Implementation / analysis / documentation support: AI-assisted using ChatGPT
- License: **Apache License 2.0** — see repository [LICENSE](../LICENSE) and [NOTICE](../NOTICE).

ゲーム制作そのものを安全に進めるための開発基盤として生まれた技術ですが、公開物は汎用Controlとして分離されています。
