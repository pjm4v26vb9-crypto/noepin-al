# 077｜AL Handoff Scope Attenuator / 引継ぎスコープ減衰器

**Status:** COMPLETE / VERIFIED  
**Creator / Project Owner / Original Concept / Architecture Direction:** **NOEPIN / のえぴん**  
**Implementation / analysis / documentation support:** AI-assisted using ChatGPT

AIやAgentへ処理を引き継ぐとき、親側のGoal・Data・Action・Target・Capabilityを上限として、子側のScopeが勝手に広がらないようにするControlです。

## 公開内容
- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Tests / Replay / Benchmark / Production Gate等、Final ZIPに含まれる検証用ファイルは、存在するものを元のファイル名・内容のまま収録しています。
- README等の文書から似たコードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification
- Normal: **PASS**
- Fresh: **PASS**
- Final Fresh: **PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–076 / 40 of 40 PASS**
- DCSR: **DIRECT INTEGRATION / 直接統合**
- Final ZIP SHA-256: `a4e63a7a5f4fe3f7ef39e48a2b093d23f7a64ea8af7edb4802dca19fcb1ba97c`

## Authority Boundary
- Handoff Scope ALLOW Candidate ≠ Permission Grant
- Attenuated Scope ≠ Automatic Delegation / Scope Mutation
- Delegation Manifest Digest ≠ Signed Delegation Token
- Parent Authority Evidence ≠ Sender Authority Inheritance
- Delegation Purpose ≠ Sender Intent Inheritance
- Context / Evidence State ≠ Consent Inheritance
- Capability Record ≠ Capability Activation
- Delegation Permit Candidate ≠ Sub-Agent Creation / Tool Execution

## Evidence
- [NOEPIN_AL_077_FINAL_VERIFICATION_REPORT_20261106.md](NOEPIN_AL_077_FINAL_VERIFICATION_REPORT_20261106.md)
- [NOEPIN_AL_077_FINAL_ARTIFACT_SEAL_20261106.json](NOEPIN_AL_077_FINAL_ARTIFACT_SEAL_20261106.json)

## License
Current repository distribution: **Apache License 2.0**.

Verification Report / Artifact Sealは完成時の記録をそのまま保持しており、現在の公開ライセンスに合わせて内容を書き換えていません。

[Standalone work page](../works/077-handoff-scope-attenuator.md)
