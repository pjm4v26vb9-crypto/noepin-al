# 013 — Unexpected Code Execution Guard / 予期しないコード実行ガード

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

自然言語や生成コードを、そのまま実行可能な命令として扱わず、Typed Actionへ変換された候補だけを安全境界で審査するControlです。

この技術の中心は、**生成された内容・Action候補・Capability主張・検証結果・実行成功を明確に分離すること**です。

## 主な用途

- シェル実行AIの安全境界
- コード生成ツール
- 自動化エージェント
- Sandbox前提の実行準備
- Capability Authorityの分離

## Authority boundaries

- Generated Text ≠ Executable Command
- Code Candidate ≠ Approved Typed Action
- Typed Action Validation ≠ Execution Success
- Capability Declaration ≠ Capability Authorization
- Human Approval Evidence ≠ Execution
- Sandbox Selection ≠ Sandbox Containment Proof
- Cached Allow ≠ New Authority
- Partial / Provisional State ≠ Committed State

## 公開内容
- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Tests / Replay / Benchmark / Production Gate等、Final ZIPに含まれる検証用ファイルは、存在するものを元のファイル名・内容のまま収録しています。
- README等の文書から似たコードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification

- Unit / Boundary / Authority: **50 / 50 PASS**
- Fresh Extract: **50 / 50 PASS**
- Replay: **6,000 evaluations / divergence 0**
- Baseline mutation: **0**
- Shell / Code / Process / Network / Filesystem execution paths in Guard: **0**
- External Action / commit paths: **0**

## Integrity

- Source SHA-256: `d38ba50c1a4028eb702272a296ba53cac879b53df2f1edd59540a37a208b4bce`
- Test SHA-256: `e07ee0dc7b37f27a00f1abfd4998f7f43efc33bfc02970cb07d8ecd780df834b`
- Final ZIP SHA-256: `e2950a40211ff6659cf5015f258e05eb962900731acb1931d367d63d22990bd3`

## DCSR

Application level: **AUXILIARY**. Exact-state reuse is limited to identical Execution Request + Policy Version state. Reused State does not gain execution authority, Capability Authority, or Action Success.

## 公開状態

Final ZIPとSource hashはSeal済みです。GitHubには、検証済みSource本体を同一性維持で取得できた場合のみ追加します。再生成した代替コードは掲載しません。

## Provenance

- Creator: **NOEPIN / のえぴん**
- Project Owner: **NOEPIN / のえぴん**
- Original Concept: **NOEPIN / のえぴん**
- Architecture Direction: **NOEPIN / のえぴん**
- Existing NOEPIN Provenance V3: retained
- Implementation / analysis / documentation support: AI-assisted using ChatGPT
- License: **Apache License 2.0** — see repository [LICENSE](../LICENSE) and [NOTICE](../NOTICE).
