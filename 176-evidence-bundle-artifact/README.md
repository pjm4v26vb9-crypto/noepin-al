# 176｜AL Evidence Bundle Artifact / Evidence Bundle

**Status:** COMPLETE / VERIFIED  
**Creator / Project Owner / Original Concept / Architecture Direction:** **NOEPIN / のえぴん**  
**Implementation / analysis / documentation support:** AI-assisted using ChatGPT

Evidence Bundleの完成時Final ZIPに含まれる検証済み実装と、Completion Evidenceを公開しています。

## 公開内容

- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Core / Tests / Replay / Benchmark / Static Safety / Production Gateを、完成時の実物から内容を変更せず移送しています。
- README等の文書から類似コードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification

- Tests: **160 / 160 PASS**
- Replay: **3,000 / divergence 0**
- Production Gate: **AL037–175 / 139 / 139 PASS**
- DCSR: **直接統合 / DIRECT INTEGRATION**
- Final ZIP SHA-256: `38e7ffb021a944be6f1c7db143ffbdc8ad080338b4665476169c677e5d75bd0e`

## Authority Boundary

- Evidence Bundle Integrity ≠ Truth
- Provenance Digest Match ≠ Truth
- Trust Score ≠ Truth / Permission / Safety Proof
- Independence Group Count ≠ independent factual correctness
- Fresh Evidence ≠ World Truth
- ALLOW candidate ≠ Permission Grant / Permit Issuance / Approval Execution / Tool Invocation / Action Execution / Action Success
- DCSR does not create Truth or authority from Evidence

詳細な技術固有のAuthority BoundaryはCompletion EvidenceのVerification Report / Artifact Sealを参照してください。

## Completion Evidence

- [Verification report](NOEPIN_AL_176_FINAL_VERIFICATION_REPORT_20261113.md)
- [Artifact seal](NOEPIN_AL_176_FINAL_ARTIFACT_SEAL_20261113.json)
- [Source index](NOEPIN_AL_176_SOURCE_INDEX.txt)

Verification Report / Artifact Seal / Source Indexは完成時の記録をそのまま保持しており、現在の公開表示に合わせて内容を書き換えていません。

## License

Current repository distribution: **Apache License 2.0**.

[Standalone work page](../works/176-evidence-bundle-artifact.md)
