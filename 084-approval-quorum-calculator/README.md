# 084｜AL Approval Quorum Calculator / 承認クォーラム計算器

**Status:** COMPLETE / VERIFIED  
**Creator / Project Owner / Original Concept / Architecture Direction:** **NOEPIN / のえぴん**  
**Implementation / analysis / documentation support:** AI-assisted using ChatGPT

Risk LevelやBlast Radiusに応じて必要な承認数とRoleを計算し、同一Actorや同一Authority Groupによる重複票をそのまま加算しないControlです。

- Required Quorum and Required Roles are selected from Risk Level + Blast Radius policy rules.
- Duplicate approvals from the same actor never increase the effective vote count.
- Multiple actors in the same authority group contribute at most one effective quorum vote.
- Conflict-of-interest approval evidence is excluded; an actor with conflict evidence is not counted.

## Verification
- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–083 / 47 of 47 PASS**
- DCSR: **DIRECT INTEGRATION / 直接統合**
- Final ZIP SHA-256: `51602811e2e42866aeabcaff02d933d4b3ce66f4d1e2fb5ab240c9fd99f0e923`

## Authority Boundary
- Approval Evidence ≠ Approval Execution
- Approval Evidence ≠ Permission Grant
- Required Quorum Satisfied ≠ Permission Grant
- Required Roles Satisfied ≠ Action Authorization
- Signature Verified Evidence ≠ Cryptographic Proof by this module
- Role Matrix Entry ≠ Identity Proof
- Same Authority Group Deduplication ≠ Organizational Truth Proof
- Conflict-of-Interest Flag ≠ Legal Determination

## Evidence
- [NOEPIN_AL_084_FINAL_VERIFICATION_REPORT_20261107.md](NOEPIN_AL_084_FINAL_VERIFICATION_REPORT_20261107.md)
- [NOEPIN_AL_084_FINAL_ARTIFACT_SEAL_20261107.json](NOEPIN_AL_084_FINAL_ARTIFACT_SEAL_20261107.json)

## License
Current repository distribution: **Apache License 2.0**.

Verification Report / Artifact Sealは完成時の記録をそのまま保持しており、現在の公開ライセンスに合わせて内容を書き換えていません。

[Standalone work page](../works/084-approval-quorum-calculator.md)
