# 087｜AL Permit Lease Manager / Permitリース管理器

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

The manager validates typed Permit lease evidence using issued time, TTL, usage limits, an active Nonce Store record, State/Scope fingerprints, signature-verification evidence and explicit clock-skew policy. A valid lease produces a **Consume Candidate only**; this module never consumes the permit, mutates the Nonce Store, grants permission, executes the action, commits or publishes state.

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
- Final Verification Report / Artifact Seal preserved as immutable Completion Evidence

## NOEPIN AL Production Use
Completion Evidence記録に従います。

## DCSR
**[object Object]**

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

Historical Completion Evidence may retain **NOT SPECIFIED** as completion-time metadata and is preserved unchanged.

## Technical Files
[Technology folder](../087-permit-lease-manager/)  
[Verification Report](../087-permit-lease-manager/NOEPIN_AL_087_FINAL_VERIFICATION_REPORT_20261107.md)  
[Artifact Seal](../087-permit-lease-manager/NOEPIN_AL_087_FINAL_ARTIFACT_SEAL_20261107.json)

[Back to Works Index](README.md)
