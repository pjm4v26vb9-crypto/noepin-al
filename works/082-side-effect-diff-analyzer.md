# 082｜AL Side-Effect Diff Analyzer / 副作用差分アナライザー

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

実行前に想定したEffectと、実行後に観測されたBefore / After Diffを比較し、予期しない副作用やProtected Changeが出ていないかを確認するControlです。

## Authority Boundary
- Intent ≠ Action
- Request ≠ Success
- State Observation ≠ World Truth
- Expected Effect ≠ Permission Grant
- Severity Estimate ≠ Safety Proof
- Protected-change DENY ≠ Rollback Execution

## 検証済み実装
この技術はREADMEだけでなく、完成時Final ZIPに含まれていた検証済み実装・テスト等を、技術フォルダ内の [`verified_artifact/`](../082-side-effect-diff-analyzer/verified_artifact/) で確認できます。

Final ZIPにReplay / Benchmark / Production Gate等が含まれる場合は、それらも元のファイル名・内容のまま公開しています。

文書から類似コードを再生成して完成版として置き換えることはしていません。

## Verification
- Tests / Fresh / Final Fresh: **160/160 PASS / 160/160 PASS / 160/160 PASS**
- Replay: **3000 / divergence 0**
- Verification Report / Artifact Sealを正式な検証記録として参照しています。

## NOEPIN AL Production Use
**AL037〜081** を実制作Gateとして使用し、**45 / 45 PASS**。

## DCSR
**DIRECT INTEGRATION / 直接統合**

## Benchmark — condition-specific
- Full median: 53.622945 ms
- Prepared median: 38.921147 ms
- Full median: 59.409800 ms
- Prepared median: 40.669774 ms

The recorded values are condition-specific and are not a universal performance guarantee.

## Integrity
Final ZIP SHA-256: `6309d988b7f29b74a5d68bbfbb598f0688fbb62a7fde86741610b1bded0eeb44`

## License
Current repository distribution: **Apache License 2.0** — see [LICENSE](../LICENSE) and [NOTICE](../NOTICE).

Verification Report / Artifact Sealは完成時の記録をそのまま保持しており、現在の公開ライセンスに合わせて内容を書き換えていません。

## Technical Files

[Technology folder](../082-side-effect-diff-analyzer/)  
[Verified artifact](../082-side-effect-diff-analyzer/verified_artifact/)  
[Verification Report](../082-side-effect-diff-analyzer/NOEPIN_AL_082_FINAL_VERIFICATION_REPORT_20261107.md)  
[Artifact Seal](../082-side-effect-diff-analyzer/NOEPIN_AL_082_FINAL_ARTIFACT_SEAL_20261107.json)

[Back to Works Index](README.md)
