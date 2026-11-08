# 006 — AI-to-AI Arbitrator / AI同士の仲裁役

> 複数AIが違う答えを出したとき、**多数決ではなくEvidence・Risk・Policy・Authorityを分離して比較する**仲裁Control。

**Status:** COMPLETE / VERIFIED  
**Category:** Multi-Agent Coordination  
**Creator:** **NOEPIN / のえぴん**

## この技術は何か

複数のAI・モデル・Agentを同時に使うと、それぞれが異なる提案を返すことがあります。

単純な多数決や高スコア採用では、「多数が言ったから真実」「評価点が高いから正しい」「候補に選ばれたから実行済み」といった誤ったAuthority昇格が起きます。

AI同士の仲裁役は、各Proposalを独立したEvidence / Risk / Policy / Authority情報として比較し、採用候補またはHuman Reviewへ整理します。

## 想定用途

- Multi-agent development
- 複数モデルによるレビュー
- 設計判断
- AI間の役割分担
- 複数候補からの安全な候補選定

## Proposal model

Proposalごとに、少なくとも以下を分離して保持します。

- Evidence Score
- Evidence References
- Risk Score
- Policy Compatibility
- Validated Authority
- Utility / ranking input

無効・Policy不適合・弱Evidenceの候補を除外し、上位候補のRiskやUtility差を評価して、SELECT_CANDIDATE / HUMAN_REVIEW / HOLD / REJECT_ALLなどへ決定論的に振り分けます。

Human Overrideがあっても変更できるのは候補選択です。Truth確定やAction実行にはなりません。

## この技術の重要な境界

- **Majority ≠ Truth**
- **Evidence Score ≠ Truth**
- Agent Claim ≠ Authority
- **Selected Proposal ≠ Action Success**
- Human Override Evidence ≠ Action Execution
- Fingerprint Match ≠ Authority Match
- Cached Arbitration ≠ New Authority

SELECT_CANDIDATEになっても、候補は候補のままです。

`authoritative=false`  
`truth_established=false`  
`action_executed=false`  
`action_succeeded=false`

という境界を維持します。

## DCSRとの関係

DCSRは**補助統合**です。

完全一致するArbitration Request + Policy Versionのread-side Stateだけを再利用します。

DCSR/cacheはTruth、外部Authority、下流ControlのALLOW/DENY、Action Successを決定しません。

Synthetic exact-state benchmark:

- 20,000 arbitrations × 7 batches
- cache enabled median: **914.035 ms**
- cache disabled median: **1770.753 ms**

これは単一環境・完全一致Stateでの条件付き観測であり、一般速度保証ではありません。

## 公開内容
- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Tests / Replay / Benchmark / Production Gate等、Final ZIPに含まれる検証用ファイルは、存在するものを元のファイル名・内容のまま収録しています。
- README等の文書から似たコードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification

- Unit / Boundary / Authority: **49 / 49 PASS**
- Fresh Extract: **49 / 49 PASS**
- Replay: **3,000 + 3,000 = 6,000 arbitrations**
- Replay divergence: **0**
- Replay fingerprint: `4c739f6ed8a1076032bf19ed51693a6aadc1bc984b5db5b37b1c90c6f16bc1e0`
- Baseline mutation: **0**
- External Action / commit paths: **0**

## Integrity

- Final artifact: `NOEPIN_AL_006_AI_ARBITRATOR_SUCCESSOR_V2_20261102.zip`
- Source SHA-256: `9d0bd198bed1866f8f13d35a3eb276998dbd2380e2526510b63cb5d12269a7c2`
- Test SHA-256: `27f3e80da9859942002bf57c16cd98689613264823f2c5d70131c38ee51c12be`
- Final ZIP SHA-256: `22078f19b3fed04099adbd5686af23420b7a8265ff66bdd31c260eb53757f33a`

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

この技術は、NOEPIN / のえぴんのゲーム制作における複数AI協働を扱う必要から生まれた技術で、公開版では汎用Multi-Agent Controlとして独立させています。
