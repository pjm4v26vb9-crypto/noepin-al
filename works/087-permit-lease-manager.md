# 087｜AL Permit Lease Manager / Permitリース管理器

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

Permitの発行時刻・TTL・使用回数・Nonce Store・State / Scope fingerprint・Signature Verification Evidenceを確認し、有効な場合でもConsume Candidateだけを返すControlです。

## Authority Boundary
- Intent ≠ Action
- Request ≠ Success
- Permit Evidence ≠ Permission Grant
- Lease Valid ≠ Permission Grant
- Signature Verified Evidence ≠ Cryptographic Proof by this module
- Nonce Store Evidence ≠ Nonce Store Mutation
- Consume Candidate ≠ Permit Consumption
- State Fingerprint Match ≠ World Truth

## Verification
- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Verification Report / Artifact Sealは、検証時の正式な記録として内容を変更せず保存しています。

## NOEPIN AL Production Use
**AL037〜086** を実制作Gateとして使用し、**50 / 50 PASS**。

## DCSR
**DIRECT INTEGRATION / 直接統合**

- Full median: **30.152603 ms**
- Prepared median: **0.007909 ms**
- Semantic match: **true**
- Full bytes: **2,240,467**
- Delta bytes: **3,135**
- Delta percent: **0.1399261850%**


## Integrity
Final ZIP SHA-256: `f926e82cfe63ba16d8c4c5c158daf29a40b8bfe72b7a024ec1d147a7d4eb2447`

## License
Current repository distribution: **Apache License 2.0** — see [LICENSE](../LICENSE) and [NOTICE](../NOTICE).

Verification Report / Artifact Sealは完成時の記録をそのまま保持しており、現在の公開ライセンスに合わせて内容を書き換えていません。

## Technical Files
[Technology folder](../087-permit-lease-manager/)  
[Verification Report](../087-permit-lease-manager/NOEPIN_AL_087_FINAL_VERIFICATION_REPORT_20261107.md)  
[Artifact Seal](../087-permit-lease-manager/NOEPIN_AL_087_FINAL_ARTIFACT_SEAL_20261107.json)

[Back to Works Index](README.md)
