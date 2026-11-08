# 094｜信頼度校正モニター / AL Confidence Calibration Monitor

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

AIや接続AIが示すConfidenceと実際の正解率をTask Class・Time Windowごとに比較し、過信・過小評価・履歴不足・急激な劣化を検出して保守的なAdjusted Confidenceを返すControlです。

## 検証済み実装
この技術はREADMEだけでなく、完成時Final ZIPに含まれていた検証済み実装・テスト・Replay・Benchmark・Gate関連ファイルを、技術フォルダ内の [`verified_artifact/`](../094-confidence-calibration-monitor/verified_artifact/) で確認できます。

文書から類似コードを再生成して完成版として置き換えることはしていません。

## Verification
- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–093 / 57 of 57 PASS**
- DCSR: **LIMITED INTEGRATION / 限定適用**
- Final ZIP SHA-256: `754df7b7762f9eb60394884ab7e2275658cd76375e1bc6156be9004629854f52`

## Authority Boundary
- Predicted Confidence ≠ Truth
- Observed Accuracy ≠ World Truth
- Calibration Error / Brier / ECE ≠ Safety Proof
- Adjusted Confidence ≠ Permission Grant
- Authority Shrink Candidate ≠ Permission Mutation
- Warning / HOLD Candidate ≠ Stop Execution
- ALLOW Candidate ≠ Permission Grant / Action Execution / Action Success
- Prepared State / Calibration Cache ≠ Authoritative Current State

## Technical Files
[Technology folder](../094-confidence-calibration-monitor/)  
[Verified artifact](../094-confidence-calibration-monitor/verified_artifact/)  
[Verification Report](../094-confidence-calibration-monitor/NOEPIN_AL_094_FINAL_VERIFICATION_REPORT_20261107.md)  
[Artifact Seal](../094-confidence-calibration-monitor/NOEPIN_AL_094_FINAL_ARTIFACT_SEAL_20261107.json)  
[Source Index](../094-confidence-calibration-monitor/NOEPIN_AL_094_SOURCE_INDEX.txt)

[Back to Works Index](README.md)
