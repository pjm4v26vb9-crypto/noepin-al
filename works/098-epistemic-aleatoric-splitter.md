# 098｜認識的不確実性分離器 / AL Epistemic-Aleatoric Splitter

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

不確実性を「情報不足などで減らせる認識的不確実性」と「現象そのもののばらつきによる不確実性」に分け、追加確認で解消できる部分と残る部分を区別するControlです。

## 検証済み実装
この技術はREADMEだけでなく、完成時Final ZIPに含まれていた検証済み実装・テスト・Replay・Benchmark・Gate関連ファイルを、技術フォルダ内の [`verified_artifact/`](../098-epistemic-aleatoric-splitter/verified_artifact/) で確認できます。

文書から類似コードを再生成して完成版として置き換えることはしていません。

## Verification
- Tests: **160 / 160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–097 / 61 of 61 PASS**
- DCSR: **LIMITED INTEGRATION / 限定適用**
- Final ZIP SHA-256: `01b4ec52ccf194cacbbbec808f29b5acb7ae5251c9fed474e74fd2cc3ab98230`

## Authority Boundary
- Epistemic Score ≠ proof that more information will resolve uncertainty
- Aleatoric Score ≠ proof of intrinsic randomness
- Variance decomposition ≠ World Truth / Safety Proof
- Research Candidate ≠ Research Execution
- Human Approval Candidate ≠ Approval Execution
- ALLOW Candidate ≠ Permission Grant / Action Execution / Action Success
- Prepared State / Cache ≠ Authoritative Current State
- DCSR Reconstruction ≠ Domain Authority / Safety Proof / Action Execution / Action Success

## Technical Files
[Technology folder](../098-epistemic-aleatoric-splitter/)  
[Verified artifact](../098-epistemic-aleatoric-splitter/verified_artifact/)  
[Verification Report](../098-epistemic-aleatoric-splitter/NOEPIN_AL_098_FINAL_VERIFICATION_REPORT_20261108.md)  
[Artifact Seal](../098-epistemic-aleatoric-splitter/NOEPIN_AL_098_FINAL_ARTIFACT_SEAL_20261108.json)  
[Source Index](../098-epistemic-aleatoric-splitter/NOEPIN_AL_098_SOURCE_INDEX.txt)

[Back to Works Index](README.md)
