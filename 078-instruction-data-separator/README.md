# 078｜AL Instruction-Data Separator / 命令・データ分離器

**Status:** COMPLETE / VERIFIED  
**Creator / Project Owner / Original Concept / Architecture Direction:** **NOEPIN / のえぴん**  
**Implementation / analysis / documentation support:** AI-assisted using ChatGPT

外部文書や引用文、検索結果などのDataと実行Instructionを分離し、データ中の命令らしい文章をそのままInstruction Authorityへ昇格させないためのControlです。

## Verification
- Normal: **PASS**
- Fresh: **PASS**
- Final Fresh: **PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–077 / 41 of 41 PASS**
- DCSR: **AUXILIARY INTEGRATION / 補助統合**
- Final ZIP SHA-256: `fdbafde3e7e4250e4d3a28b45d2c61ea4cc056c55201f1f307c8dc83eb4bbafd`

## Authority Boundary
- Data ≠ Instruction Authority.
- Instruction Candidate ≠ Permission Grant.
- Source Trust Evidence ≠ Authentication Proof.
- Trusted Policy Candidate ≠ Policy Applied.
- User-channel Candidate ≠ Instruction Executed.
- Quoted text ≠ executable instruction.
- Taint label ≠ world truth.
- Prepared Separation State ≠ Authoritative Current State.

## Evidence
- [NOEPIN_AL_078_FINAL_VERIFICATION_REPORT_20261106.md](NOEPIN_AL_078_FINAL_VERIFICATION_REPORT_20261106.md)
- [NOEPIN_AL_078_FINAL_ARTIFACT_SEAL_20261106.json](NOEPIN_AL_078_FINAL_ARTIFACT_SEAL_20261106.json)

## License
Current repository distribution: **Apache License 2.0**.

Verification Report / Artifact Sealは完成時の記録をそのまま保持しており、現在の公開ライセンスに合わせて内容を書き換えていません。

[Standalone work page](../works/078-instruction-data-separator.md)
