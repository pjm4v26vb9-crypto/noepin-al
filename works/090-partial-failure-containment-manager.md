# 090｜AL Partial-Failure Containment Manager / 部分失敗封じ込め器

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

複数Stepの一部だけが失敗した場合に、影響範囲を分けてContainment / Continue / Full Stop / Recoveryの候補を評価するControlです。候補を出しても、このModule自身が停止や補償を実行することはありません。

## Authority Boundary
- PASS / ALLOW Candidate ≠ Permission Grant / Action Execution / Action Success

## Verification
- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Verification Report / Artifact Sealは、検証時の正式な記録として内容を変更せず保存しています。

## NOEPIN AL Production Use
**AL037〜089** を実制作Gateとして使用し、**53 / 53 PASS**。

## DCSR
**DIRECT INTEGRATION / 直接統合**

- Level: **DIRECT INTEGRATION / 直接統合**
- Canonical state: Request / Execution Graph / Step States / Compensation Evidence / Policy
- Prepared reuse requires matching Context + Dependency + Policy + Registry fingerprints and independently validated Prepared integrity.
- Delta processes changed records only; missing-only synchronization does not require full resend in the measured condition.

## Benchmark — condition-specific
- Normal Full median: **85.357875 ms**
- Normal Prepared median: **0.008313 ms**
- Fresh Full median: **85.628087 ms**
- Fresh Prepared median: **0.008212 ms**
- Semantic match: **true**
- Full bytes: **2,214,662**
- Delta bytes: **1,690**
- Delta percent: **0.0763096129%**
- Missing-only records: **10 / 242 bytes metadata**
- Full resend required: **false**

記録値は当該試験条件に限定され、一般性能を保証するものではありません。

## Integrity
Final ZIP SHA-256: `5ff5292f5b8e04db06d742a29097a7607ba23520f4f63d60b77ebd6824c2f4d8`

## License
Current repository distribution: **Apache License 2.0** — see [LICENSE](../LICENSE) and [NOTICE](../NOTICE).

Verification Report / Artifact Sealは完成時の記録をそのまま保持しており、現在の公開ライセンスに合わせて内容を書き換えていません。

## Technical Files
[Technology folder](../090-partial-failure-containment-manager/)  
[Verification Report](../090-partial-failure-containment-manager/NOEPIN_AL_090_FINAL_VERIFICATION_REPORT_20261107.md)  
[Artifact Seal](../090-partial-failure-containment-manager/NOEPIN_AL_090_FINAL_ARTIFACT_SEAL_20261107.json)

[Back to Works Index](README.md)
