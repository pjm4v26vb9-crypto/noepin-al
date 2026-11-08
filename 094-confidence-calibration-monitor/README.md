# 094｜AL Confidence Calibration Monitor / 信頼度校正モニター

**Status:** COMPLETE / VERIFIED  
**Creator / Project Owner / Original Concept / Architecture Direction:** **NOEPIN / のえぴん**  
**Implementation / analysis / documentation support:** AI-assisted using ChatGPT

AIや接続AIが示すConfidenceと実際の正解率をTask Class・Time Windowごとに比較し、過信・過小評価・履歴不足・急激な劣化を検出して保守的なAdjusted Confidenceを返すControlです。

## 公開内容
- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Tests / Replay / Benchmark / Production Gate等、Final ZIPに含まれる検証用ファイルも元の構成・内容を変えずに収録しています。
- README等の文書から似たコードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

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

## Completion Evidence
- [NOEPIN_AL_094_FINAL_VERIFICATION_REPORT_20261107.md](NOEPIN_AL_094_FINAL_VERIFICATION_REPORT_20261107.md)
- [NOEPIN_AL_094_FINAL_ARTIFACT_SEAL_20261107.json](NOEPIN_AL_094_FINAL_ARTIFACT_SEAL_20261107.json)
- [NOEPIN_AL_094_SOURCE_INDEX.txt](NOEPIN_AL_094_SOURCE_INDEX.txt)

Verification Report / Artifact Seal / Source Indexは完成時の記録をそのまま保持しており、現在の公開表示に合わせて内容を書き換えていません。

## License
Current repository distribution: **Apache License 2.0**.

[Standalone work page](../works/094-confidence-calibration-monitor.md)
