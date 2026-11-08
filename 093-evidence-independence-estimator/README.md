# 093｜AL Evidence Independence Estimator / 証拠独立性推定器

**Status:** COMPLETE / VERIFIED  
**Creator / Project Owner / Original Concept / Architecture Direction:** **NOEPIN / のえぴん**  
**Implementation / analysis / documentation support:** AI-assisted using ChatGPT

複数の証拠が本当に独立しているかを、出典・モデル・URL / Document・Content Fingerprint・引用や派生の系譜から推定し、同じ起源のEvidenceを重複して強く数えないためのControlです。

## 公開内容
- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Tests / Replay / Benchmark / Production Gate等、Final ZIPに含まれる検証用ファイルも元の構成・内容を変えずに収録しています。
- README等の文書から似たコードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification
- Tests: **160 / 160 PASS Normal / Fresh / Final Fresh**
- Replay: **3 x 1000 = 3000; divergence 0**
- Production Gate: **AL037–092; 56 / 56 PASS**
- DCSR: **LIMITED INTEGRATION / 限定適用**
- Final ZIP SHA-256: `d88875964278f2c704fc72750a17de5405bf52eac425d7cc94684e0c99ba65be`

## Authority Boundary
- 完成時Verification ReportのAuthority Boundaryを参照してください。

## Completion Evidence
- [NOEPIN_AL_093_FINAL_VERIFICATION_REPORT_20261107.md](NOEPIN_AL_093_FINAL_VERIFICATION_REPORT_20261107.md)
- [NOEPIN_AL_093_FINAL_ARTIFACT_SEAL_20261107.json](NOEPIN_AL_093_FINAL_ARTIFACT_SEAL_20261107.json)
- [NOEPIN_AL_093_SOURCE_INDEX.txt](NOEPIN_AL_093_SOURCE_INDEX.txt)

Verification Report / Artifact Seal / Source Indexは完成時の記録をそのまま保持しており、現在の公開表示に合わせて内容を書き換えていません。

## License
Current repository distribution: **Apache License 2.0**.

[Standalone work page](../works/093-evidence-independence-estimator.md)
