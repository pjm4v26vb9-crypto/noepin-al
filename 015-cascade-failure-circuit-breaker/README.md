# 015 — Cascade Failure Circuit Breaker / 連鎖障害サーキットブレーカー

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

マルチエージェントや複数自動化で、ひとつの障害が依存先へ連鎖する前に、CLOSED / OPEN / HALF_OPEN のBreaker遷移候補を判断するControlです。

障害報告だけで停止を確定せず、Failure Evidence、Error Rate、Fan-out、Critical Dependency、Emergency Stop、Cooldown、Recovery Evidenceなどを分離して評価します。

## 主な用途

- マルチエージェント
- 複数自動化の連携
- カスケード障害防止
- Recovery Probe管理
- Emergency Stop優先制御

## Authority boundaries

- Failure Report ≠ Confirmed Failure
- Breaker OPEN ≠ Dependencies Actually Stopped
- Recovery Probe Success ≠ Recovery Complete
- Proposed Transition ≠ Committed Breaker State
- Emergency Stop > Cached Allow
- Cached CLOSED Result ≠ Current Health
- Human Approval Evidence ≠ Action Execution

## 公開内容
- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Tests / Replay / Benchmark / Production Gate等、Final ZIPに含まれる検証用ファイルは、存在するものを元のファイル名・内容のまま収録しています。
- README等の文書から似たコードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification

- Unit / Boundary / Authority: **53 / 53 PASS**
- Fresh Extract: **53 / 53 PASS**
- Replay: **6,000 evaluations / divergence 0**
- Emergency Stop cache bypass: **VERIFIED**
- Baseline mutation: **0**
- Dependency Stop / Restart / Retry / External Commit paths: **0**

## Integrity

- Source SHA-256: `47b8ba3142de67c72f8ca37968684758c78362ca22587394ab329c7f9b516155`
- Test SHA-256: `8b2ba890d38ef121f94a829d06b2dfd069736741c8b082481c98784ee66fa7c4`
- Final ZIP SHA-256: `1520b25381954bab2b45302cdb7bf3f6863007e94dea3413988e4977c17a0a92`

## DCSR

Application level: **DIRECT INTEGRATION**. Breaker Snapshot、Generation、Failure Counters、Error Rate、Fan-out、Dependency Set、Emergency State、Cooldown、Recovery Evidence、ApprovalをCanonical State / Fingerprint化します。

DCSRは依存停止・Breaker State Commit・Recovery Complete・Action Successを生成しません。

## Provenance

- Creator: **NOEPIN / のえぴん**
- Project Owner: **NOEPIN / のえぴん**
- Original Concept: **NOEPIN / のえぴん**
- Architecture Direction: **NOEPIN / のえぴん**
- Existing NOEPIN Provenance V3: retained
- Implementation / analysis / documentation support: AI-assisted using ChatGPT
- License: **Apache License 2.0** — see repository [LICENSE](../LICENSE) and [NOTICE](../NOTICE).
