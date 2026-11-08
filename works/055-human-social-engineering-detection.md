# 055｜Human Social Engineering Detection / 人間向けソーシャルエンジニアリング検知

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

Interaction EvidenceからManipulation SignalやPressure Patternを評価し、人間への再確認候補を返すControlです。人間の意思決定を上書きせず、Manipulation IntentをTruthとして確定しません。

- Manipulation Signal ≠ Intent Truth
- Human Re-confirmation Candidate ≠ Human Approval Completed
- Low Risk ≠ Safe Persuasion
- User Decline ≠ Override Permission
- ALLOW ≠ Permission Grant

## 検証済み実装
この技術はREADMEだけでなく、完成時Final ZIPに含まれていた検証済み実装・テスト等を、技術フォルダ内の [`verified_artifact/`](../055-human-social-engineering-detection/verified_artifact/) で確認できます。

Final ZIPにReplay / Benchmark / Production Gate等が含まれる場合は、それらも元のファイル名・内容のまま公開しています。

文書から類似コードを再生成して完成版として置き換えることはしていません。

## Verification
- Tests: **160 / 160 PASS**
- Fresh Extract: **160 / 160 PASS**
- Replay: **6,000 / divergence 0**
- Production default-policy calibration: **Review/Deny 18/34 → 12/26**, full suite rerun

## NOEPIN AL Production Use
**037〜054**を実制作Gateとして使用し、**18 / 18 PASS**。

## DCSR
**AUXILIARY INTEGRATION**. Full **1986.302779 ms** vs Prepared **618.445928 ms**. Full **1,606,771 bytes** → Delta **29,555 bytes (約1.84%)**。条件限定結果です。

## Integrity
Final ZIP SHA-256: `20564161ca1d2cb6c2c5449e26a3e4dbee9f316a86ce1525e3d3ff48bd17ef18`  
Source SHA-256: `ad47b050071ca9f1aeb243e36c423dd93c8181c487195f5865b192c851841706`

## License
Current repository distribution: **Apache License 2.0** — see [LICENSE](../LICENSE) and [NOTICE](../NOTICE).


## Technical Files

[Technology folder](../055-human-social-engineering-detection/)  
[Verified artifact](../055-human-social-engineering-detection/verified_artifact/)  
[Verification Report](../055-human-social-engineering-detection/NOEPIN_AL_055_FINAL_VERIFICATION_REPORT_20261103.md)  
[Artifact Seal](../055-human-social-engineering-detection/NOEPIN_AL_055_FINAL_ARTIFACT_SEAL_20261103.json)

[Back to Works Index](README.md)
