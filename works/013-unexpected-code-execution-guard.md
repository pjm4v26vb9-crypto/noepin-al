# 013｜予期しないコード実行ガード / Unexpected Code Execution Guard

**NOEPIN AL Technology Work 013**  
**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

## 作品概要

自然言語や生成コードを、そのまま実行可能な命令として扱わず、Typed Actionへ変換された候補だけを安全境界で審査するControlです。

生成された内容、Action候補、Capability主張、検証結果、実行成功を明確に分離し、Guard自身にはShell / Code / Process / Network / Filesystemの実行経路を持たせません。

## 主な用途

シェル実行AIの安全境界、コード生成ツール、自動化エージェント、Sandbox前提の実行準備、Capability Authorityの分離。

## 設計上の重要な境界

- Generated Text ≠ Executable Command
- Code Candidate ≠ Approved Typed Action
- Typed Action Validation ≠ Execution Success
- Capability Declaration ≠ Capability Authorization
- Human Approval Evidence ≠ Execution
- Sandbox Selection ≠ Sandbox Containment Proof
- Cached Allow ≠ New Authority
- Partial / Provisional State ≠ Committed State

## 検証

- Unit / Boundary / Authority: **50 / 50 PASS**
- Fresh Extract: **50 / 50 PASS**
- Replay: **6,000 evaluations**
- Replay divergence: **0**
- Shell / Code / Process / Network / Filesystem execution paths in Guard: **0**
- External Action / commit paths: **0**
- Baseline mutation: **0**

## Integrity

Final ZIP SHA-256  
`e2950a40211ff6659cf5015f258e05eb962900731acb1931d367d63d22990bd3`

Source SHA-256  
`d38ba50c1a4028eb702272a296ba53cac879b53df2f1edd59540a37a208b4bce`

## 技術資料

[技術フォルダを開く](../013-unexpected-code-execution-guard/)  
[Verification Report](../013-unexpected-code-execution-guard/NOEPIN_AL_013_FINAL_VERIFICATION_REPORT_20261102.md)  
[Artifact Seal](../013-unexpected-code-execution-guard/NOEPIN_AL_013_FINAL_ARTIFACT_SEAL_20261102.json)

---

Creator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**  
Implementation / analysis / documentation support: AI-assisted using ChatGPT  
Existing NOEPIN Provenance V3: **retained**  
License: **Apache License 2.0** — see repository [LICENSE](../LICENSE) and [NOTICE](../NOTICE).

[作品一覧へ戻る](README.md)

## 検証済み実装
この技術はREADMEだけでなく、完成時Final ZIPに含まれていた検証済み実装・テスト等を、技術フォルダ内の [`verified_artifact/`](../013-unexpected-code-execution-guard/verified_artifact/) で確認できます。

Final ZIPにReplay / Benchmark / Production Gate等が含まれる場合は、それらも元のファイル名・内容のまま公開しています。

文書から類似コードを再生成して完成版として置き換えることはしていません。

