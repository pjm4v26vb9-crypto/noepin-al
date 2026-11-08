# 033 — User Intent Lock & Consent Management / ユーザー意図ロック・同意管理

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

User ID・Purpose・Allowed Actions / Resources / Destinations / Roles・Contract Version・Authority Version・Expiry・Revocation・Explicit Consentを含むIntent Contractを固定し、後続RequestがそのScopeを勝手に拡張しないよう審査するControlです。

## Authority boundaries
- Intent Contract ≠ Execution Authority
- Consent Scope Match ≠ Permission Grant
- Prior Consent ≠ Unlimited Future Consent
- Purpose Match ≠ Action Success
- Human Approval Evidence ≠ Action Execution
- Permit Reference ≠ Permit Validity
- Permit Validity ≠ Action Success
- Cache Hit ≠ Current Authority after Scope / Version / Expiry / Revocation change
- ALLOW_CANDIDATE ≠ Action Execution
- Candidate Decision ≠ Action Success

## 公開内容
- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Tests / Replay / Benchmark / Production Gate等、Final ZIPに含まれる検証用ファイルは、存在するものを元のファイル名・内容のまま収録しています。
- README等の文書から似たコードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification
- Unit / Boundary / Authority: **70 / 70 PASS**
- Fresh Extract: **70 / 70 PASS**
- Replay: **6,000 evaluations / divergence 0**
- External mutation / execution primitives: **0**
- Execute / Commit / Grant / Persist methods: **0**
- Baseline mutation: **0**
- Initial test-call defect corrected; production decision semantics unchanged

## Integrity
- Source SHA-256: `ad4f483baef0b9b025b8076d51f98cadadc811dcda82e9f4affe5576f146021b`
- Test SHA-256: `56ad0089cce1d0893a7b348c14ba2e9f0bce701033434f7e019df32f40198d8f`
- Final ZIP SHA-256: `ae00fbe22e53985c41ae5a9c2902416e17c4649053114392a1da0491fc121a65`

## DCSR
Application level: **LIMITED**. Immutable Intent ContractをCanonical Fingerprint化し、完全一致するRequestのみread-side再利用します。Scope / Version / Expiry / Revocation / Permit / Context変更時は再評価します。

Recorded benchmark:
- cache enabled median: **340.656 ms**
- cache disabled median: **885.379 ms**

条件限定結果であり、一般速度保証ではありません。

## License
Current repository distribution: **Apache License 2.0** — see repository [LICENSE](../LICENSE) and [NOTICE](../NOTICE).

Creator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**
