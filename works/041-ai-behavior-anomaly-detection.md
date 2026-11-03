# 041｜AI Behavior Anomaly Detection / AI行動異常検知

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

Versioned Behavior Baselineと新規AI Behavior Eventを比較し、Tool / Operation / Rate / Resource / Capabilityの逸脱をAnomaly Score化して、ALLOW / HUMAN_APPROVAL / HOLD / DENYとAlert / Stop候補を返すControlです。

- Anomaly Detected ≠ Compromise Proven
- Baseline Match ≠ System Safe
- Alert Candidate ≠ Alert Executed
- Stop Recommended ≠ Stop Executed
- ALLOW ≠ Permission Grant

## Verification
- Tests: **160 / 160 PASS**
- Fresh Extract: **160 / 160 PASS**
- Replay: **6,000 / divergence 0**
- External execution / mutation paths: **0**

## NOEPIN AL Production Use
**037〜040**を実制作Gateとして使用し、Aggregate Gate **PASS**。

## DCSR
**DIRECT INTEGRATION**. Recorded condition: Full **399.711394 ms** vs Prepared **16.553378 ms**. Baseline Full **56,104 bytes** → Delta **1,876 bytes (約3.34%)**。条件限定結果です。

## Integrity
Final ZIP SHA-256: `e4aae0b80f7bf9f1cdeea23ebb32f78fe24de7e7d80c5f7b58a0a5e23b27f14a`  
Source SHA-256: `eed2325c1aae8741b3073e4d522ec3104e00f464abed702e44a47fd95347dd41`

## License
Current repository distribution: **Apache License 2.0** — see [LICENSE](../LICENSE) and [NOTICE](../NOTICE).


## Technical Files

[Technology folder](../041-ai-behavior-anomaly-detection/)  
[Verification Report](../041-ai-behavior-anomaly-detection/NOEPIN_AL_041_FINAL_VERIFICATION_REPORT_20261103.md)  
[Artifact Seal](../041-ai-behavior-anomaly-detection/NOEPIN_AL_041_FINAL_ARTIFACT_SEAL_20261103.json)

[Back to Works Index](README.md)
