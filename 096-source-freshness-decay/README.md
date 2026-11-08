# 096｜AL Source Freshness Decay / 情報鮮度減衰器

**Status:** COMPLETE / VERIFIED  
**Creator / Project Owner / Original Concept / Architecture Direction:** **NOEPIN / のえぴん**  
**Implementation / analysis / documentation support:** AI-assisted using ChatGPT

情報源の鮮度を時間経過や更新条件に応じて減衰評価し、古いEvidenceを現在の判断へ過大に残さないためのControlです。

## 公開内容
- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Tests / Replay / Benchmark / Production Gate等、Final ZIPに含まれる検証用ファイルも元の構成・内容を変えずに収録しています。
- README等の文書から似たコードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification
- Tests: **160 / 160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–095 / 59 of 59 PASS**
- DCSR: **LIMITED INTEGRATION / 限定適用**
- Final ZIP SHA-256: `8e1b5f56c271cfee93c04484672c178e4b24fda1aa2a0b1fc5c2e4f117c77c1f`

## Authority Boundary
- 完成時Verification ReportのAuthority Boundaryを参照してください。

## Completion Evidence
- [NOEPIN_AL_096_FINAL_VERIFICATION_REPORT_20261108.md](NOEPIN_AL_096_FINAL_VERIFICATION_REPORT_20261108.md)
- [NOEPIN_AL_096_FINAL_ARTIFACT_SEAL_20261108.json](NOEPIN_AL_096_FINAL_ARTIFACT_SEAL_20261108.json)
- [NOEPIN_AL_096_SOURCE_INDEX.txt](NOEPIN_AL_096_SOURCE_INDEX.txt)

Verification Report / Artifact Seal / Source Indexは完成時の記録をそのまま保持しており、現在の公開表示に合わせて内容を書き換えていません。

## License
Current repository distribution: **Apache License 2.0**.

[Standalone work page](../works/096-source-freshness-decay.md)
