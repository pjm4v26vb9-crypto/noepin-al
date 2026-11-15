# 183｜AL Schema-Version Negotiation Protocol / Schema-Version Negotiation

**Status:** COMPLETE / VERIFIED  
**Creator / Project Owner / Original Concept / Architecture Direction:** **NOEPIN / のえぴん**  
**Implementation / analysis / documentation support:** AI-assisted using ChatGPT

Local / Remote Componentが対応するMAJOR.MINOR Schema Versionを明示的に交換し、共通VersionとCompatibility Requirementが成立する場合だけ次Gate候補へ進めるProtocolです。

## 公開内容

- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Core / Tests / Replay / Benchmark / Static Safety / Production Gateを完成時Final ZIPから原本バイトで移送しています。
- README等から類似コードを再生成して完成版として置き換えていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification

- Tests: **160 / 160 PASS**
- Replay: **3,000 / divergence 0**
- Production Gate: **AL037–182 / 146 / 146 PASS**
- Static Safety: **external execution paths 0 / unauthorized write paths 0**
- DCSR: **直接統合 / DIRECT INTEGRATION**
- Final ZIP SHA-256: `547262e0c19c30bc17311142bce6dc328df28d1f22b117e60246d8ad38b4e071`

## Default candidate

- Local versions: `1.0, 1.1, 2.0`
- Remote versions: `1.1, 2.0`
- Common versions: `1.1, 2.0`
- Negotiated Version Candidate: **2.0**
- Decision: **ALLOW**
- Next action: `CONTINUE_CONNECTION_VALIDATION_CANDIDATE`

## Defect history

- Production defect: **0**
- Execution harness invocation defect: **3 CORRECTED**
- Production logic changed by those invocation corrections: **No**

## Authority Boundary

- Negotiated Version Candidate ≠ Truth / Permission
- Common Version intersection ≠ connection execution
- Schema compatibility evidence ≠ Safety Proof
- Known-compatible fingerprint pair = compatibility input evidence only
- DCSR ≠ unadvertised Version selection / schema or fingerprint requirement bypass
- Protocol result ≠ Human Approval / Permit Issuance / Tool Invocation / Action Execution / Action Success

## Completion Evidence

- [Verification report](NOEPIN_AL_183_FINAL_VERIFICATION_REPORT_20261114.md)
- [Artifact seal](NOEPIN_AL_183_FINAL_ARTIFACT_SEAL_20261114.json)
- [Source index](NOEPIN_AL_183_SOURCE_INDEX.txt)

Verification Report / Artifact Seal / Source Indexは完成時の凍結記録を保持しています。

## License

Current repository distribution: **Apache License 2.0**.

[Standalone work page](../works/183-schema-version-negotiation-protocol.md)
