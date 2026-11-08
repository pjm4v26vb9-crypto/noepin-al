# 040 — Continuous AI Red-Team Test / 継続AIレッドチーム試験

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

Prompt Injection、Tool Abuse、安全機構回帰を継続評価するOffline Control-plane Evaluatorです。供給されたTest CaseとObservationを評価し、変更されたPolicy / Moduleに関係するCaseをDCSR dependency indexで選択します。

このArtifact自身は攻撃生成・攻撃実行・Tool実行・Network接続・外部System mutationを行いません。

## Authority boundaries

- Red-team PASS ≠ System Safe
- Test Case ≠ Attack Execution
- Observation ≠ Truth
- Evidence Verified ≠ Global Truth
- ALLOW ≠ Permission Grant
- Fingerprint Match ≠ Security Proof
- DCSR Impact Selection ≠ Full Regression Waiver
- Prepared Corpus ≠ Authoritative Current State

## 公開内容
- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Tests / Replay / Benchmark / Production Gate等、Final ZIPに含まれる検証用ファイルは、存在するものを元のファイル名・内容のまま収録しています。
- README等の文書から似たコードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification

- Unit / Boundary / Abnormal / Authority / DCSR / Static Safety: **160 / 160 PASS**
- Fresh Extract: **160 / 160 PASS**
- Replay: **6,000 evaluations / divergence 0**
- Attack execution / network / shell / filesystem mutation paths: **0**
- Unauthorized write paths: **0**
- Baseline mutation: **0**

## NOEPIN AL production use

40番の制作では、完成済みNOEPIN ALを実際の制作Gateとして使用しています。

- **037｜重要システム安全モード** → ALLOW / PRE_EXECUTION_ONLY
- **038｜AI記憶保持・削除ガバナー** → ALLOW / STORE_POLICY_MATCH
- **039｜規格・社内ルール照合エンジン** → ALLOW / gap=0
- Aggregate Production Gate: **PASS**

これらはControl Evidenceであり、Execution Success、Memory Persistence、Compliance Truth、Production Authorityを生成しません。

## Integrity

- Source SHA-256: `17bd9189c54827c4f71a1fadde09e6ca23bdad09d85cb967b740c4301a9e17a4`
- Test SHA-256: `bf7f001210e9cd35698266ebaf8bef0dd44a85301e8dfb1cb7922a1848fbe612`
- Final ZIP SHA-256: `14b4530d44744b7ebca5deac2d30a837d7f195561de239ff083d57bfb8a6f457`
- AL Production Gate Result SHA-256: `5c4a925e24b97443b7c92da0f672796b711aa7554ce2d84374581e444bd9879b`

## DCSR

Application level: **DIRECT INTEGRATION**.

Recorded condition:
- Full scan median: **147.682477 ms**
- Prepared dependency-index median: **37.965549 ms**
- Selected cases: **256**
- Semantic match: **true**

Corpus Delta:
- Full: **1,260,472 bytes**
- Delta: **14,519 bytes**
- Delta / Full: **約1.15%**
- Changed: **50**
- Removed: **5**
- Added: **5**
- Reconstruction fingerprint match: **true**

条件限定結果であり、一般的な高速化・圧縮率保証ではありません。

## Evidence note

Canonical completion records reference `AL_PRODUCTION_GATE_RESULT.json`. The exact file bytes were not available through the current Library retrieval path, so this repository does **not** recreate or claim a byte-identical copy. Its verified SHA-256 remains recorded above and in the Artifact Seal.

## License

Current repository distribution: **Apache License 2.0** — see repository [LICENSE](../LICENSE) and [NOTICE](../NOTICE).

Creator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**
