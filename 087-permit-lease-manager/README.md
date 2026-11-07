# 087｜AL Permit Lease Manager / Permitリース管理器

**Status:** COMPLETE / VERIFIED  
**Creator / Project Owner / Original Concept / Architecture Direction:** **NOEPIN / のえぴん**  
**Implementation / analysis / documentation support:** AI-assisted using ChatGPT

Permitの発行時刻・TTL・使用回数・Nonce Store・State / Scope fingerprint・Signature Verification Evidenceを確認し、有効な場合でもConsume Candidateだけを返すControlです。

## Verification
- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–086 / 50 of 50 PASS**
- DCSR: **DIRECT INTEGRATION / 直接統合**
- Final ZIP SHA-256: `f926e82cfe63ba16d8c4c5c158daf29a40b8bfe72b7a024ec1d147a7d4eb2447`

## Authority Boundary
- Intent ≠ Action
- Request ≠ Success
- Permit Evidence ≠ Permission Grant
- Lease Valid ≠ Permission Grant
- Signature Verified Evidence ≠ Cryptographic Proof by this module
- Nonce Store Evidence ≠ Nonce Store Mutation
- Consume Candidate ≠ Permit Consumption
- State Fingerprint Match ≠ World Truth

## Evidence
- [NOEPIN_AL_087_FINAL_VERIFICATION_REPORT_20261107.md](NOEPIN_AL_087_FINAL_VERIFICATION_REPORT_20261107.md)
- [NOEPIN_AL_087_FINAL_ARTIFACT_SEAL_20261107.json](NOEPIN_AL_087_FINAL_ARTIFACT_SEAL_20261107.json)

## License
Current repository distribution: **Apache License 2.0**.

Verification Report / Artifact Sealは完成時の記録をそのまま保持しており、現在の公開ライセンスに合わせて内容を書き換えていません。

[Standalone work page](../works/087-permit-lease-manager.md)
