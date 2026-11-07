# 077｜AL Handoff Scope Attenuator / 引継ぎスコープ減衰器

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

AIやAgentへ処理を引き継ぐとき、親側のGoal・Data・Action・Target・Capabilityを上限として、子側のScopeが勝手に広がらないようにするControlです。

## Authority Boundary
- Handoff Scope ALLOW Candidate ≠ Permission Grant
- Attenuated Scope ≠ Automatic Delegation / Scope Mutation
- Delegation Manifest Digest ≠ Signed Delegation Token
- Parent Authority Evidence ≠ Sender Authority Inheritance
- Delegation Purpose ≠ Sender Intent Inheritance
- Context / Evidence State ≠ Consent Inheritance

## Verification
- Tests / Fresh / Final Fresh: **PASS / PASS / PASS**
- Replay: **3000 / divergence 0**
- Evidence source: immutable Final Verification Report / Artifact Seal

## NOEPIN AL Production Use
**AL037〜076** を実制作Gateとして使用し、**40 / 40 PASS**。

## DCSR
**DIRECT INTEGRATION / 直接統合**


## Integrity
Final ZIP SHA-256: `a4e63a7a5f4fe3f7ef39e48a2b093d23f7a64ea8af7edb4802dca19fcb1ba97c`

## License
Current repository distribution: **Apache License 2.0** — see [LICENSE](../LICENSE) and [NOTICE](../NOTICE).

Verification Report / Artifact Sealは完成時の記録をそのまま保持しており、現在の公開ライセンスに合わせて内容を書き換えていません。

## Technical Files

[Technology folder](../077-handoff-scope-attenuator/)  
[Verification Report](../077-handoff-scope-attenuator/NOEPIN_AL_077_FINAL_VERIFICATION_REPORT_20261106.md)  
[Artifact Seal](../077-handoff-scope-attenuator/NOEPIN_AL_077_FINAL_ARTIFACT_SEAL_20261106.json)

[Back to Works Index](README.md)
