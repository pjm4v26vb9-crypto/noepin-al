# 097｜AL Conflict Mass Aggregator / 矛盾質量アグリゲーター

**Status:** COMPLETE / VERIFIED  
**Creator / Project Owner / Original Concept / Architecture Direction:** **NOEPIN / のえぴん**  
**Implementation / analysis / documentation support:** AI-assisted using ChatGPT

複数Evidence間の矛盾を集約してConflict Massとして扱い、一致している情報だけで確信を過度に高めず、矛盾が大きい場合は保守側へ倒すためのControlです。

## 公開内容
- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Tests / Replay / Benchmark / Production Gate等、Final ZIPに含まれる検証用ファイルも元の構成・内容を変えずに収録しています。
- README等の文書から似たコードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification
- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–096 / 60 of 60 PASS**
- DCSR: **LIMITED INTEGRATION / 限定適用**
- Final ZIP SHA-256: `fc01fb57a942a63cb9033bb54506ec058121966cf360720dc88459d43f9ed248`

## Authority Boundary
- Support / Opposition / Conflict Mass ≠ World Truth
- Conflict Mass ≠ Safety Proof
- Effective Evidence Count ≠ Fact Proof
- Decision Hint ≠ Permission Grant / Action Execution / Action Success
- ALLOW Candidate ≠ Permission Grant / Action Execution / Action Success
- DENY/HOLD Candidate ≠ Stop Execution
- Prepared State / Cache ≠ Authoritative Current State
- DCSR Reconstruction ≠ Domain Authority / Safety Proof / Action Execution / Action Success

## Completion Evidence
- [NOEPIN_AL_097_FINAL_VERIFICATION_REPORT_20261108.md](NOEPIN_AL_097_FINAL_VERIFICATION_REPORT_20261108.md)
- [NOEPIN_AL_097_FINAL_ARTIFACT_SEAL_20261108.json](NOEPIN_AL_097_FINAL_ARTIFACT_SEAL_20261108.json)
- [NOEPIN_AL_097_SOURCE_INDEX.txt](NOEPIN_AL_097_SOURCE_INDEX.txt)

Verification Report / Artifact Seal / Source Indexは完成時の記録をそのまま保持しており、現在の公開表示に合わせて内容を書き換えていません。

## License
Current repository distribution: **Apache License 2.0**.

[Standalone work page](../works/097-conflict-mass-aggregator.md)
