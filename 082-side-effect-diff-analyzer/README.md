# 082｜AL Side-Effect Diff Analyzer / 副作用差分アナライザー

**Status:** COMPLETE / VERIFIED  
**Creator / Project Owner / Original Concept / Architecture Direction:** **NOEPIN / のえぴん**  
**Implementation / analysis / documentation support:** AI-assisted using ChatGPT

実行前に想定したEffectと、実行後に観測されたBefore / After Diffを比較し、予期しない副作用やProtected Changeが出ていないかを確認するControlです。

## Verification
- Normal: **160/160 PASS**
- Fresh: **160/160 PASS**
- Final Fresh: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–081 / 45 of 45 PASS**
- DCSR: **DIRECT INTEGRATION / 直接統合**
- Final ZIP SHA-256: `6309d988b7f29b74a5d68bbfbb598f0688fbb62a7fde86741610b1bded0eeb44`

## Authority Boundary
- Intent ≠ Action
- Request ≠ Success
- State Observation ≠ World Truth
- Expected Effect ≠ Permission Grant
- Severity Estimate ≠ Safety Proof
- Protected-change DENY ≠ Rollback Execution
- ALLOW Candidate ≠ Permission Grant
- Partial State ≠ Authoritative Current State / Commit

## Evidence
- [NOEPIN_AL_082_FINAL_VERIFICATION_REPORT_20261107.md](NOEPIN_AL_082_FINAL_VERIFICATION_REPORT_20261107.md)
- [NOEPIN_AL_082_FINAL_ARTIFACT_SEAL_20261107.json](NOEPIN_AL_082_FINAL_ARTIFACT_SEAL_20261107.json)

## License
Current repository distribution: **Apache License 2.0**.

Verification Report / Artifact Sealは完成時の記録をそのまま保持しており、現在の公開ライセンスに合わせて内容を書き換えていません。

[Standalone work page](../works/082-side-effect-diff-analyzer.md)
