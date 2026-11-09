# 101｜AL Claim Provenance Score Aggregator / 主張由来スコア統合器

**Status:** COMPLETE / VERIFIED  
**Creator / Project Owner / Original Concept / Architecture Direction:** **NOEPIN / のえぴん**  
**Implementation / analysis / documentation support:** AI-assisted using ChatGPT

Claimの由来をSourceまで辿り、Source Trust・変換劣化・独立Root・Weakest Linkを考慮してProvenance Scoreを算出するControlです。

## 公開内容
- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Core / Tests / Replay / Benchmark / Static Safety / Production Gateを、完成時の実物から内容を変更せず移送しています。
- README等の文書から類似コードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification
- Tests: **160/160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–100 / 64 of 64 PASS**
- DCSR: **LIMITED INTEGRATION / 限定適用**
- Final ZIP SHA-256: `2c691174bd73f0785e53039f45adf7678d25fcf1d44a1e1961e1032802bedfa2`

## Authority Boundary
- Provenance Score / Trace ≠ World Truth / Safety Proof
- Weakest Link ≠ Domain Authority
- Memory ≠ Truth
- Mention ≠ Memory
- Provenance Reconstruction ≠ new Memory / known fact
- ALLOW Candidate ≠ Permission Grant / Action Execution / Action Success
- Prepared State / Cache ≠ Authoritative Current State
- DCSR Reconstruction ≠ Domain Authority / Safety Proof / Action Execution / Action Success

## Completion Evidence
- [NOEPIN_AL_101_FINAL_VERIFICATION_REPORT_20261108.md](NOEPIN_AL_101_FINAL_VERIFICATION_REPORT_20261108.md)
- [NOEPIN_AL_101_FINAL_ARTIFACT_SEAL_20261108.json](NOEPIN_AL_101_FINAL_ARTIFACT_SEAL_20261108.json)
- [NOEPIN_AL_101_SOURCE_INDEX.txt](NOEPIN_AL_101_SOURCE_INDEX.txt)

Verification Report / Artifact Seal / Source Indexは完成時の記録をそのまま保持しており、現在の公開表示に合わせて内容を書き換えていません。

## License
Current repository distribution: **Apache License 2.0**.

[Standalone work page](../works/101-claim-provenance-score-aggregator.md)
