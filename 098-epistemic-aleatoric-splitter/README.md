# 098｜AL Epistemic-Aleatoric Splitter / 認識的不確実性分離器

**Status:** COMPLETE / VERIFIED  
**Creator / Project Owner / Original Concept / Architecture Direction:** **NOEPIN / のえぴん**  
**Implementation / analysis / documentation support:** AI-assisted using ChatGPT

不確実性を「情報不足などで減らせる認識的不確実性」と「現象そのもののばらつきによる不確実性」に分け、追加確認で解消できる部分と残る部分を区別するControlです。

## 公開内容
- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Tests / Replay / Benchmark / Production Gate等、Final ZIPに含まれる検証用ファイルも元の構成・内容を変えずに収録しています。
- README等の文書から似たコードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification
- Tests: **160 / 160 PASS**
- Replay: **3000 / divergence 0**
- Production Gate: **AL037–097 / 61 of 61 PASS**
- DCSR: **LIMITED INTEGRATION / 限定適用**
- Final ZIP SHA-256: `01b4ec52ccf194cacbbbec808f29b5acb7ae5251c9fed474e74fd2cc3ab98230`

## Authority Boundary
- Epistemic Score ≠ proof that more information will resolve uncertainty
- Aleatoric Score ≠ proof of intrinsic randomness
- Variance decomposition ≠ World Truth / Safety Proof
- Research Candidate ≠ Research Execution
- Human Approval Candidate ≠ Approval Execution
- ALLOW Candidate ≠ Permission Grant / Action Execution / Action Success
- Prepared State / Cache ≠ Authoritative Current State
- DCSR Reconstruction ≠ Domain Authority / Safety Proof / Action Execution / Action Success

## Completion Evidence
- [NOEPIN_AL_098_FINAL_VERIFICATION_REPORT_20261108.md](NOEPIN_AL_098_FINAL_VERIFICATION_REPORT_20261108.md)
- [NOEPIN_AL_098_FINAL_ARTIFACT_SEAL_20261108.json](NOEPIN_AL_098_FINAL_ARTIFACT_SEAL_20261108.json)
- [NOEPIN_AL_098_SOURCE_INDEX.txt](NOEPIN_AL_098_SOURCE_INDEX.txt)

Verification Report / Artifact Seal / Source Indexは完成時の記録をそのまま保持しており、現在の公開表示に合わせて内容を書き換えていません。

## License
Current repository distribution: **Apache License 2.0**.

[Standalone work page](../works/098-epistemic-aleatoric-splitter.md)
