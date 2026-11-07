# 089｜AL Idempotency Guard / 冪等性ガード

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

同じRequestが繰り返されたときに二重実行を避けるため、Idempotency Keyや過去のResult Evidenceを確認し、再利用候補やSafe Retry候補を返すControlです。

## Authority Boundary
- Intent ≠ Action
- Request ≠ Success
- History Record ≠ World Truth / Action Success
- Same-Key Success ≠ Permission Grant
- Result Reuse Candidate ≠ Action Success
- Generated Idempotency Key Candidate ≠ Key Registration
- History Registration Candidate ≠ History Store Mutation
- Safe Retry Candidate ≠ Retry Execution

## Verification
- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Verification Report / Artifact Sealは、検証時の正式な記録として内容を変更せず保存しています。

## NOEPIN AL Production Use
**AL037〜088** を実制作Gateとして使用し、**52 / 52 PASS**。

## DCSR
**DIRECT INTEGRATION / 直接統合**

## Benchmark — condition-specific
- Normal Full median: **11.230893 ms**
- Normal Prepared median: **0.007301 ms**
- Fresh Full median: **10.984040 ms**
- Fresh Prepared median: **0.005589 ms**
- Semantic match: **true**
- Full bytes: **1,100,553**
- Delta bytes: **2,546**
- Delta percent: **0.2313382454%**
- Missing-only history records: **10**
- Missing metadata bytes: **182**

記録値は当該試験条件に限定され、一般性能を保証するものではありません。

## Integrity
Final ZIP SHA-256: `dd462b59c0c56e8bd79062d0d493c9c13b6924750eb63ea1664a3427e94bae8b`

## License
Current repository distribution: **Apache License 2.0** — see [LICENSE](../LICENSE) and [NOTICE](../NOTICE).

Verification Report / Artifact Sealは完成時の記録をそのまま保持しており、現在の公開ライセンスに合わせて内容を書き換えていません。

## Technical Files
[Technology folder](../089-idempotency-guard/)  
[Verification Report](../089-idempotency-guard/NOEPIN_AL_089_FINAL_VERIFICATION_REPORT_20261107.md)  
[Artifact Seal](../089-idempotency-guard/NOEPIN_AL_089_FINAL_ARTIFACT_SEAL_20261107.json)

[Back to Works Index](README.md)
