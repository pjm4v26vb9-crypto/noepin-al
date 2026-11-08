# 009 — MCP & Tool Permission Controller / MCP・ツール権限コントローラー

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

MCPサーバーや外部ツールについて、**接続・認証できること**と**特定のTool / Operation / Scopeを使ってよいこと**を分離するControlです。

重要な境界:
- Tool discoverability ≠ Tool authority
- OAuth/OIDC authentication ≠ Operation authorization
- Tool allowlist ≠ Operation allow
- Permit presence ≠ Valid permit
- Expired / Revoked Permit ≠ Authority
- Cached Allow ≠ Current Authority
- Permission Decision ≠ Tool Call / Action Success

検証:
- Unit / Boundary / Authority: **54 / 54 PASS**
- Fresh Extract: **54 / 54 PASS**
- Replay: **6,000 decisions / divergence 0**
- Baseline mutation: **0**
- MCP / Tool invocation paths in Controller: **0**
- External Action / commit paths: **0**

Final ZIP SHA-256: `ca4384c1be677710df3bd513a179eca6c4975eac39487a78ea2e08b93b299ef3`

Creator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**  
Implementation / analysis / documentation support: AI-assisted using ChatGPT  
License: **Apache License 2.0** — see repository [LICENSE](../LICENSE) and [NOTICE](../NOTICE).

## 公開内容
- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Tests / Replay / Benchmark / Production Gate等、Final ZIPに含まれる検証用ファイルは、存在するものを元のファイル名・内容のまま収録しています。
- README等の文書から似たコードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

