# 009｜MCP・ツール権限コントローラー / MCP & Tool Permission Controller

**NOEPIN AL Technology Work 009**  
**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

## 作品概要

MCPサーバーや外部ツールについて、**接続・認証できること**と**特定のTool / Operation / Scopeを利用してよいこと**を分離するControlです。

Toolが見えることやOAuth/OIDC認証済みであることを、そのままOperation Authorizationへ昇格させません。

## 主な用途

MCP接続、外部ツール利用、危険機能の限定公開、AIごとの最小権限運用など。

## 設計上の重要な境界

- Tool discoverability ≠ Tool authority
- OAuth/OIDC authentication ≠ Operation authorization
- Tool allowlist ≠ Operation allow
- Permit presence ≠ Valid permit
- Expired / Revoked Permit ≠ Authority
- Cached Allow ≠ Current Authority
- Permission Decision ≠ Tool Call / Action Success

## 検証

- Unit / Boundary / Authority: **54 / 54 PASS**
- Fresh Extract: **54 / 54 PASS**
- Replay: **6,000 decisions**
- Replay divergence: **0**
- Baseline mutation: **0**
- MCP / Tool invocation paths in Controller: **0**
- External Action / commit paths: **0**

## Integrity

Final ZIP SHA-256  
`ca4384c1be677710df3bd513a179eca6c4975eac39487a78ea2e08b93b299ef3`

Source SHA-256  
`e9b9997bf6c7275a7d4bd6582a0001a643ab13e5de0ad4abb0baac57d2d89b9f`

## 技術資料

[技術フォルダを開く](../009-mcp-tool-permission-controller/)  
[Verification Report](../009-mcp-tool-permission-controller/NOEPIN_AL_009_FINAL_VERIFICATION_REPORT_20261102.md)  
[Artifact Seal](../009-mcp-tool-permission-controller/NOEPIN_AL_009_FINAL_ARTIFACT_SEAL_20261102.json)

---

Creator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**  
Implementation / analysis / documentation support: AI-assisted using ChatGPT  
License: **Apache License 2.0** — see repository [LICENSE](../LICENSE) and [NOTICE](../NOTICE).

[作品一覧へ戻る](README.md)
