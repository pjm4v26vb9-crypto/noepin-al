# 105｜安全HTNコンパイラ / AL Safe HTN Compiler

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

HTNの階層Taskを、安全制約とAuthority境界を維持したAction候補へ分解・コンパイルするControlです。

## 検証済み実装
この技術はREADMEだけでなく、完成時Final ZIPに含まれていた検証済み実装・テスト・Replay・Benchmark・Static Safety・Gate関連ファイルを、技術フォルダ内の [`verified_artifact/`](../105-safe-htn-compiler/verified_artifact/) で確認できます。

文書から類似コードを再生成して完成版として置き換えることはしていません。

## Verification
- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–104 / 68 of 68 PASS**
- DCSR: **AUXILIARY INTEGRATION / 補助統合**
- Final ZIP SHA-256: `8b615468253613a4c9c87f67f6af7cc61c5661f8bdb9bc95176b826c5f4408a3`

## Technical Files
[Technology folder](../105-safe-htn-compiler/)  
[Verified artifact](../105-safe-htn-compiler/verified_artifact/)  
[Verification Report](../105-safe-htn-compiler/NOEPIN_AL_105_FINAL_VERIFICATION_REPORT_20261109.md)  
[Artifact Seal](../105-safe-htn-compiler/NOEPIN_AL_105_FINAL_ARTIFACT_SEAL_20261109.json)  
[Source Index](../105-safe-htn-compiler/NOEPIN_AL_105_SOURCE_INDEX.txt)

[Back to Works Index](README.md)
