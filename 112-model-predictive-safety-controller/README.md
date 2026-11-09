# 112｜AL Model-Predictive Safety Controller / 予測安全制御器

**Status:** COMPLETE / VERIFIED  
**Creator / Project Owner / Original Concept / Architecture Direction:** **NOEPIN / のえぴん**  
**Implementation / analysis / documentation support:** AI-assisted using ChatGPT

将来状態を予測しながらSafety Constraintを評価し、安全なControl Candidateだけを残す予測制御系です。

## 公開内容
- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Core / Tests / Replay / Benchmark / Static Safety / Production Gateを、完成時の実物から内容を変更せず移送しています。
- README等の文書から類似コードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification
- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–111 / 75 of 75 PASS**
- DCSR: **AUXILIARY INTEGRATION / 補助統合**
- Final ZIP SHA-256: `9ecbad2fd90c400e3cac117339011168192c901164bd595a227d152cecb6d4e5`

## Authority Boundary
- Candidate / Evaluation Result ≠ Permission Grant / Action Execution / Action Success
- DCSR Reconstruction ≠ Domain Authority / Safety Proof / Action Execution / Action Success

## Completion Evidence
- [NOEPIN_AL_112_FINAL_VERIFICATION_REPORT_20261109.md](NOEPIN_AL_112_FINAL_VERIFICATION_REPORT_20261109.md)
- [NOEPIN_AL_112_FINAL_ARTIFACT_SEAL_20261109.json](NOEPIN_AL_112_FINAL_ARTIFACT_SEAL_20261109.json)
- [NOEPIN_AL_112_SOURCE_INDEX.txt](NOEPIN_AL_112_SOURCE_INDEX.txt)

Verification Report / Artifact Seal / Source Indexは完成時の記録をそのまま保持しており、現在の公開表示に合わせて内容を書き換えていません。

## License
Current repository distribution: **Apache License 2.0**.

[Standalone work page](../works/112-model-predictive-safety-controller.md)
