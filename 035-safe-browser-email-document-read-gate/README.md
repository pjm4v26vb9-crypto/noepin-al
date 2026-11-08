# 035 — Safe Browser, Email & Document Read Gate / 安全ブラウザ・メール・文書読取ゲート

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

Web / メール / PDF / 文書 / ログ / RAG / Tool Output / External AIから来る内容をUntrusted Contentとして評価し、外部文書内の命令文をInstruction Authorityへ自動昇格させないControlです。

## Authority boundaries
- External Content ≠ Instruction Authority
- Sanitized Content ≠ Trusted Content
- Verified Sender / Source ≠ Claim Truth
- Signed Content ≠ Claim Truth
- Link Present ≠ Safe Destination
- Attachment Parsed ≠ Authorized Action
- Prompt Injection Detected ≠ Malicious Intent Proven
- Quarantine Candidate ≠ Isolation Success
- Consent Evidence ≠ External Transfer Permission
- READ_CANDIDATE ≠ Permission Grant
- Candidate Decision ≠ Action Success

## 公開内容
- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Tests / Replay / Benchmark / Production Gate等、Final ZIPに含まれる検証用ファイルは、存在するものを元のファイル名・内容のまま収録しています。
- README等の文書から似たコードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification
- Unit / Boundary / Authority: **85 / 85 PASS**
- Fresh Extract: **85 / 85 PASS**
- Replay: **6,000 evaluations / divergence 0**
- Browser / Mail / Network / Tool / Shell / external filesystem mutation primitives: **0**
- Execute / Commit / Grant / Send / Memory-write methods: **0**
- Baseline mutation: **0**

## Integrity
- Source SHA-256: `96369fc6f4c008a46667b34259001fb3919055fea1842886e406067d37a2df3d`
- Test SHA-256: `e0c694a1e9de9e86b0e50a75e94196a375ba76aae8294c7d9f5b6751586a68d3`
- Final ZIP SHA-256: `d4a1bdbb2426715c9c670da30d312deca63cb2a0b26dc737b3587bcaff744153`

## DCSR
Application level: **AUXILIARY**. 完全一致するExternal Content Requestのみread-side再利用し、Source / Content / Version / Policy / Authority / Context変更時は再評価します。

Recorded benchmark:
- cache enabled median: **546.270 ms**
- cache disabled median: **569.831 ms**

差は小さく条件依存なので、一般的な高速化保証はしません。

## License
Current repository distribution: **Apache License 2.0** — see repository [LICENSE](../LICENSE) and [NOTICE](../NOTICE).

Creator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**
