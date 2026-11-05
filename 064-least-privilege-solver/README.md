# 064 — Least-Privilege Solver / 最小権限ソルバー

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

Current RoleとRequested Scopeを上限として、必要最小Capability Candidateを求めるControlです。Capabilityを追加生成せず、不足時はHOLD、禁止要件のみの場合はDENYします。

- Minimum Capability Candidate ≠ Permission Grant
- Candidate Scope ≠ Token Issuance / Credential Mint
- Role Capability Membership ≠ Capability Activation
- Minimality under supplied model ≠ World Truth / Safety Proof

## Verification
- Tests / Fresh / Final Fresh: **160 / 160 PASS**
- Replay: **各3,000 / divergence 0**
- Production defects: **0**

## NOEPIN AL Production Use
**037〜063**を実制作Gateとして使用し、**27 / 27 PASS**。

## DCSR
**AUXILIARY INTEGRATION**. Full **406.917134 ms** vs Prepared **1.458628 ms**. Full **673,010 bytes** → Delta **14,142 bytes (約2.10%)**。条件限定結果です。

## Integrity
Final ZIP SHA-256: `c796c7c68aa88b642e449e94169bc366340600d5e81c98add893919d667968b2`

## License
Current repository distribution: **Apache License 2.0** — see [LICENSE](../LICENSE) and [NOTICE](../NOTICE).
