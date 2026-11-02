# 029 — Uncertainty & Hold Decision Engine / 不確実性・保留判断エンジン

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

AIが不確かな状況で無理に断定・実行へ進まないよう、Confidence・Evidence Coverage・Contradiction・Freshness・Unknown / Ambiguity・Missing Information・Impact・Irreversibilityを分離評価し、ASK_USER / RESEARCH_REQUIRED / HUMAN_CONFIRM / HOLDへ切り替えるControlです。

## Authority boundaries
- Unknown ≠ Known
- Confidence ≠ Truth
- Evidence Coverage ≠ Truth Authority
- Research Required ≠ Research Completed
- Ask User ≠ User Clarified
- Human Confirm ≠ Human Approval Granted
- PROCEED_CANDIDATE ≠ Permission Grant
- PROCEED_CANDIDATE ≠ Action Execution
- Cache Hit ≠ Current Authority after changed evidence/context/version
- Candidate Decision ≠ Action Success

## Verification
- Unit / Boundary / Authority: **74 / 74 PASS**
- Fresh Extract: **74 / 74 PASS**
- Replay: **6,000 evaluations / divergence 0**
- Shell / Process / Network / external filesystem mutation primitives: **0**
- Execute / Commit / Grant methods: **0**
- Research execution / Human approval grant paths: **0**
- Baseline mutation: **0**

## Integrity
- Source SHA-256: `c41a7d457ae31f9d1591b6665d6e0e9f84d8832a388bcb3d8a5b517d8211b966`
- Test SHA-256: `2a1e5d422a6a2707e84c9f3f1d084963bbc69560502521db012b91efd5448a41`
- Final ZIP SHA-256: `18af8d9329b6259fce14b9d841f0eb15b401acaf840e2da9e4d46d06d75b6976`

## DCSR
Application level: **AUXILIARY**. 完全一致するUncertainty Request + Policy / Authority Stateのみread-side再利用します。

Recorded benchmark:
- cache enabled median: **486.396 ms**
- cache disabled median: **524.882 ms**

差は小さく条件依存なので、一般的な高速化保証はしません。

## License
Current repository distribution: **Apache License 2.0** — see repository [LICENSE](../LICENSE) and [NOTICE](../NOTICE).

Creator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**
