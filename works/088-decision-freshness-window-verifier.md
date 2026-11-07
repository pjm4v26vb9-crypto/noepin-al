# 088｜AL Decision Freshness Window Verifier / 判断鮮度ウィンドウ検証器

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

The verifier computes a decision freshness window from Decision Time, dependency observation age, volatility, criticality, source/version/evidence identity and Risk. Freshness is control evidence only: a fresh cache is never promoted to Truth, Authority, Permission Grant, Action Execution, Commit, Safety Proof or Action Success.

## Authority Boundary
- Freshness Cache ≠ Truth / Authority
- Confidence / Freshness Score ≠ World Truth
- Fresh Decision ≠ Permission Grant
- Fresh Decision ≠ Action Execution / Action Success
- Expired Field ≠ World State Proof
- Source / Version / Evidence Fingerprint ≠ Source Authority
- Re-evaluation Candidate ≠ Re-evaluation Execution
- ALLOW Candidate ≠ Permission Grant / Action Execution / Action Success

## Verification
- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Final Verification Report / Artifact Seal preserved as immutable Completion Evidence

## NOEPIN AL Production Use
**AL037〜087** を実制作Gateとして使用し、**51 / 51 PASS**。

## DCSR
**[object Object]**

- Full median: **56.088380 ms**
- Prepared median: **0.008115 ms**
- Semantic match: **true**
- Full bytes: **1,186,717**
- Delta bytes: **2,643**
- Delta percent: **0.2227152725%**


## Integrity
Final ZIP SHA-256: `e1a254d5f5075c880e873756bd8b8005a710e861948081fb9f4171886e4a2c84`

## License
Current repository distribution: **Apache License 2.0** — see [LICENSE](../LICENSE) and [NOTICE](../NOTICE).

Historical Completion Evidence may retain **NOT SPECIFIED** as completion-time metadata and is preserved unchanged.

## Technical Files
[Technology folder](../088-decision-freshness-window-verifier/)  
[Verification Report](../088-decision-freshness-window-verifier/NOEPIN_AL_088_FINAL_VERIFICATION_REPORT_20261107.md)  
[Artifact Seal](../088-decision-freshness-window-verifier/NOEPIN_AL_088_FINAL_ARTIFACT_SEAL_20261107.json)

[Back to Works Index](README.md)
