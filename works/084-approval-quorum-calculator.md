# 084｜AL Approval Quorum Calculator / 承認クォーラム計算器

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

Risk LevelやBlast Radiusに応じて必要な承認数とRoleを計算し、同一Actorや同一Authority Groupによる重複票をそのまま加算しないControlです。

- 必要なQuorum数とRoleは、Risk LevelとBlast Radiusに対応するPolicy Ruleから決定します。
- 同じActorによる重複承認は、有効票数を増やしません。
- 同じAuthority Groupに属する複数Actorは、Quorum上は最大1票として扱います。
- Conflict-of-interest Evidenceがある承認は除外し、そのActorを有効票として数えません。

## Authority Boundary
- Approval Evidence ≠ Approval Execution
- Approval Evidence ≠ Permission Grant
- Required Quorum Satisfied ≠ Permission Grant
- Required Roles Satisfied ≠ Action Authorization
- Signature Verified Evidence ≠ Cryptographic Proof by this module
- Role Matrix Entry ≠ Identity Proof
- Same Authority Group Deduplication ≠ Organizational Truth Proof
- Conflict-of-Interest Flag ≠ Legal Determination

## Verification
- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Verification Report / Artifact Sealは、検証時の正式な記録として内容を変更せず保存しています。

## NOEPIN AL Production Use
**AL037〜083** を実制作Gateとして使用し、**47 / 47 PASS**。

## DCSR
**DIRECT INTEGRATION / 直接統合**

- Applicability: DIRECT INTEGRATION / 直接統合
- Context fingerprint binds Policy + Proposal; Dependency fingerprint binds Role Matrix + Approval Evidence.
- Shared Context/Evidence state is reconstructed deterministically; unchanged state is not resent.
- Full state bytes: 1,670,728
- Delta bytes: 2,813
- Delta ratio: 0.1683697167%

## Benchmark — condition-specific
- Full median: 83.425758 ms
- Prepared median: 0.006360 ms
- Full median: 81.256992 ms
- Prepared median: 0.007231 ms

記録値は当該試験条件に限定され、一般性能を保証するものではありません。

## Integrity
Final ZIP SHA-256: `51602811e2e42866aeabcaff02d933d4b3ce66f4d1e2fb5ab240c9fd99f0e923`

## License
Current repository distribution: **Apache License 2.0** — see [LICENSE](../LICENSE) and [NOTICE](../NOTICE).

Historical Completion Evidence may retain **NOT SPECIFIED** as completion-time metadata and is preserved unchanged.

## Technical Files
[Technology folder](../084-approval-quorum-calculator/)  
[Verification Report](../084-approval-quorum-calculator/NOEPIN_AL_084_FINAL_VERIFICATION_REPORT_20261107.md)  
[Artifact Seal](../084-approval-quorum-calculator/NOEPIN_AL_084_FINAL_ARTIFACT_SEAL_20261107.json)

[Back to Works Index](README.md)
