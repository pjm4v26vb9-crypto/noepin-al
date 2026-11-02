# 030 — AI Registry & Lifecycle Management / AI登録・ライフサイクル管理

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

利用中のAI / AgentをAgent ID・Owner・Role・Agent Version・Registry Version・Authority Version・Expiry・Revocation・Lifecycle Stateで明示管理し、REGISTER / ACTIVATE / UPDATE / RENEW / SUSPEND / DECOMMISSIONの実行前Transition Candidateを返すControlです。

## Authority boundaries
- Registered Record ≠ Runtime Permission
- Registry Entry ≠ Active Authority
- Owner Match ≠ Permission Grant
- Role Label ≠ Current Permit
- Expiry Detection ≠ Agent Actually Stopped
- Revocation Flag ≠ Stop Success
- Suspend Candidate ≠ Agent Suspended
- Decommission Candidate ≠ Agent Decommissioned
- Human Approval Evidence ≠ Lifecycle Commit
- Cache Hit ≠ Current Authority after Registry / Authority / Expiry / Revocation change
- Lifecycle Candidate ≠ Action Success

## Verification
- Unit / Boundary / Authority: **78 / 78 PASS**
- Fresh Extract: **78 / 78 PASS**
- Replay: **6,000 evaluations / divergence 0**
- Shell / Process / Network / external filesystem mutation primitives: **0**
- Execute / Commit / Grant / Stop-Agent / Persist methods: **0**
- Baseline mutation: **0**

## Integrity
- Source SHA-256: `b92d5bade108cecb3241cc59c6b58f52d082f2fe344d809fbea0f43bc5cf0a4a`
- Test SHA-256: `0349fb6f9ccf9e3e0638473e07bf4a95e606bf33301ba4488d79b88ee7ecf77a`
- Final ZIP SHA-256: `6df2f3d4b9395bed05bcd12bf445483aef5d507f3a5a6397a50a5265e255ec3b`

## DCSR
Application level: **DIRECT INTEGRATION**. Immutable Registry Stateのstructural validation・Canonical Fingerprint・Agent Lookup Indexをmaterializeし、完全一致するRegistry Fingerprint + Lifecycle Requestのみread-side再利用します。

Recorded conditions:
- Exact CHECK cache enabled median: **391.873 ms**
- cache disabled median: **578.661 ms**
- Full Registry: **330,971 bytes**
- Delta: **7,347 bytes**
- Delta / Full: **約2.22%**

条件限定結果であり、一般速度・圧縮率保証ではありません。

## License
Current repository distribution: **Apache License 2.0** — see repository [LICENSE](../LICENSE) and [NOTICE](../NOTICE).

Creator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**
