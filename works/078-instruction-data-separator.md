# 078｜AL Instruction-Data Separator / 命令・データ分離器

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

外部文書や引用文、検索結果などのDataと実行Instructionを分離し、データ中の命令らしい文章をそのままInstruction Authorityへ昇格させないためのControlです。

## Authority Boundary
- Data ≠ Instruction Authority.
- Instruction Candidate ≠ Permission Grant.
- Source Trust Evidence ≠ Authentication Proof.
- Trusted Policy Candidate ≠ Policy Applied.
- User-channel Candidate ≠ Instruction Executed.
- Quoted text ≠ executable instruction.

## 検証済み実装
この技術はREADMEだけでなく、完成時Final ZIPに含まれていた検証済み実装・テスト等を、技術フォルダ内の [`verified_artifact/`](../078-instruction-data-separator/verified_artifact/) で確認できます。

Final ZIPにReplay / Benchmark / Production Gate等が含まれる場合は、それらも元のファイル名・内容のまま公開しています。

文書から類似コードを再生成して完成版として置き換えることはしていません。

## Verification
- Tests / Fresh / Final Fresh: **PASS / PASS / PASS**
- Replay: **3000 / divergence 0**
- Verification Report / Artifact Sealを正式な検証記録として参照しています。

## NOEPIN AL Production Use
**AL037〜077** を実制作Gateとして使用し、**41 / 41 PASS**。

## DCSR
**AUXILIARY INTEGRATION / 補助統合**


## Integrity
Final ZIP SHA-256: `fdbafde3e7e4250e4d3a28b45d2c61ea4cc056c55201f1f307c8dc83eb4bbafd`

## License
Current repository distribution: **Apache License 2.0** — see [LICENSE](../LICENSE) and [NOTICE](../NOTICE).

Verification Report / Artifact Sealは完成時の記録をそのまま保持しており、現在の公開ライセンスに合わせて内容を書き換えていません。

## Technical Files

[Technology folder](../078-instruction-data-separator/)  
[Verified artifact](../078-instruction-data-separator/verified_artifact/)  
[Verification Report](../078-instruction-data-separator/NOEPIN_AL_078_FINAL_VERIFICATION_REPORT_20261106.md)  
[Artifact Seal](../078-instruction-data-separator/NOEPIN_AL_078_FINAL_ARTIFACT_SEAL_20261106.json)

[Back to Works Index](README.md)
