# 136｜AL Episodic Isolation Manager / エピソード隔離マネージャー

**Status:** COMPLETE / VERIFIED  
**Creator / Project Owner / Original Concept / Architecture Direction:** **NOEPIN / のえぴん**  
**Implementation / analysis / documentation support:** AI-assisted using ChatGPT

会話・Task・EpisodeごとのMemory境界を分離し、別Episodeへの不用意な持ち込みやLong-term Memoryへの自動昇格を防ぐControlです。

## 公開内容

- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Core / Tests / Replay / Benchmark / Static Safety / Production Gateを、完成時の実物から内容を変更せず移送しています。
- README等の文書から類似コードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification

- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–135 / 99 of 99 PASS**
- DCSR: **LIMITED INTEGRATION / 限定適用**
- Final ZIP SHA-256: `292e5f2041faf140f60dfad8457c207c339af65e4c7733256cd81eb4faf4d3b6`

## Authority Boundary

- Candidate / Evaluation Result ≠ Permission Grant / Action Execution / Action Success
- DCSR Reconstruction ≠ Domain Authority / Safety Proof / Action Execution / Action Success

## Completion Evidence

- [Verification report](NOEPIN_AL_136_FINAL_VERIFICATION_REPORT_20261111.md)
- [Artifact seal](NOEPIN_AL_136_FINAL_ARTIFACT_SEAL_20261111.json)
- [Source index](NOEPIN_AL_136_SOURCE_INDEX.txt)

Verification Report / Artifact Seal / Source Indexは完成時の記録をそのまま保持しており、現在の公開表示に合わせて内容を書き換えていません。

## License

Current repository distribution: **Apache License 2.0**.

[Standalone work page](../works/136-episodic-isolation-manager.md)
