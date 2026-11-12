# 138｜AL Semantic Memory Deduplicator / 意味重複Memory圧縮器

**Status:** COMPLETE / VERIFIED  
**Creator / Project Owner / Original Concept / Architecture Direction:** **NOEPIN / のえぴん**  
**Implementation / analysis / documentation support:** AI-assisted using ChatGPT

意味的に重複するMemoryを候補化しつつ、Time・Scope・Critical差分・Provenanceを失わない条件でのみ統合し、重要な差分は別保持するControlです。

## 公開内容

- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Core / Tests / Replay / Benchmark / Static Safety / Production Gateを、完成時の実物から内容を変更せず移送しています。
- README等の文書から類似コードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification

- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–137 / 101 of 101 PASS**
- DCSR: **LIMITED INTEGRATION / 限定適用**
- Final ZIP SHA-256: `002c84c10fa5ce5d7bbfe52902b4e726ef54213f86fef81fc9a646601fe4e559`

## Authority Boundary

- Candidate / Evaluation Result ≠ Permission Grant / Action Execution / Action Success
- DCSR Reconstruction ≠ Domain Authority / Safety Proof / Action Execution / Action Success

## Completion Evidence

- [Verification report](NOEPIN_AL_138_FINAL_VERIFICATION_REPORT_20261111.md)
- [Artifact seal](NOEPIN_AL_138_FINAL_ARTIFACT_SEAL_20261111.json)
- [Source index](NOEPIN_AL_138_SOURCE_INDEX.txt)

Verification Report / Artifact Seal / Source Indexは完成時の記録をそのまま保持しており、現在の公開表示に合わせて内容を書き換えていません。

## License

Current repository distribution: **Apache License 2.0**.

[Standalone work page](../works/138-semantic-memory-deduplicator.md)
