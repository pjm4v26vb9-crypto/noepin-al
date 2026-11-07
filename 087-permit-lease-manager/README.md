# 087｜AL Permit Lease Manager / Permitリース管理器

**Status:** COMPLETE / VERIFIED  
**Creator / Project Owner / Original Concept / Architecture Direction:** **NOEPIN / のえぴん**  
**Implementation / analysis / documentation support:** AI-assisted using ChatGPT

The manager validates typed Permit lease evidence using issued time, TTL, usage limits, an active Nonce Store record, State/Scope fingerprints, signature-verification evidence and explicit clock-skew policy. A valid lease produces a **Consume Candidate only**; this module never consumes the permit, mutates the Nonce Store, grants permission, executes the action, commits or publishes state.

## Verification
- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **recorded in evidence**
- DCSR: **[object Object]**
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

Historical Evidence files are preserved without rewriting their completion-time License / Rights metadata.

[Standalone work page](../works/087-permit-lease-manager.md)
