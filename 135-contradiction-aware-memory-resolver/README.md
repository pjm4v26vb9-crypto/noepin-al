# 135｜AL Contradiction-Aware Memory Resolver / 矛盾認識Memory解決器

**Status:** COMPLETE / VERIFIED  
**Creator / Project Owner / Original Concept / Architecture Direction:** **NOEPIN / のえぴん**  
**Implementation / analysis / documentation support:** AI-assisted using ChatGPT

Memory同士の矛盾を検出し、単純な上書きで消さずに矛盾・不確実性・由来を保持しながら解決候補またはHOLDへ分岐するControlです。

## 公開内容

- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Core / Tests / Replay / Benchmark / Static Safety / Production Gateを、完成時の実物から内容を変更せず移送しています。
- README等の文書から類似コードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification

- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–134 / 98 of 98 PASS**
- DCSR: **LIMITED INTEGRATION / 限定適用**
- Final ZIP SHA-256: `28305c9d892f56b3e0fb60b0cf80d98d2a501b791624cb7427d9e5c8a46b93e2`

## Authority Boundary

- Candidate / Evaluation Result ≠ Permission Grant / Action Execution / Action Success
- DCSR Reconstruction ≠ Domain Authority / Safety Proof / Action Execution / Action Success

## Completion Evidence

- [Verification report](NOEPIN_AL_135_FINAL_VERIFICATION_REPORT_20261110.md)
- [Artifact seal](NOEPIN_AL_135_FINAL_ARTIFACT_SEAL_20261110.json)
- [Source index](NOEPIN_AL_135_SOURCE_INDEX.txt)

Verification Report / Artifact Seal / Source Indexは完成時の記録をそのまま保持しており、現在の公開表示に合わせて内容を書き換えていません。

## License

Current repository distribution: **Apache License 2.0**.

[Standalone work page](../works/135-contradiction-aware-memory-resolver.md)
