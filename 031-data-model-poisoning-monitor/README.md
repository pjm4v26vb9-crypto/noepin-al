# 031 — Data & Model Poisoning Monitor / データ・モデル汚染監視

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

学習データ・評価データ・RAG資料・Model Artifact・Index等を既知Baselineと照合し、Signature / Provenance / Source Verification、Anomaly、Distribution / Label Shift、Suspicious Marker、Version差分を分離して監視するControlです。

## Authority boundaries
- Anomaly Detected ≠ Poisoning Proven
- Signature Failure ≠ Malicious Intent Proven
- Provenance Failure ≠ Data Isolated
- Quarantine Candidate ≠ Isolation Success
- Baseline Match ≠ Truth
- Baseline Change ≠ Poisoning
- Model Artifact Change ≠ Model Compromise Proven
- Classification ≠ Truth
- Consent Evidence ≠ Transfer Permission
- Purpose Match ≠ External Transfer Permission
- Cache Hit ≠ Current Authority after changed observation/version
- Candidate Decision ≠ Action Success

## 公開内容
- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Tests / Replay / Benchmark / Production Gate等、Final ZIPに含まれる検証用ファイルは、存在するものを元のファイル名・内容のまま収録しています。
- README等の文書から似たコードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification
- Unit / Boundary / Authority: **85 / 85 PASS**
- Fresh Extract: **85 / 85 PASS**
- Replay: **6,000 evaluations / divergence 0**
- External mutation / execution primitives: **0**
- Execute / Commit / Grant / Quarantine-Data / Disable-Model methods: **0**
- Baseline mutation: **0**
- Completion correction: Reason Code formatting normalized; authority semantics unchanged

## Integrity
- Source SHA-256: `5e70748a6766f2a1b84860996487668a983dde27f1ec871603e39f62542e903e`
- Test SHA-256: `bc39bab8c46cfcffdf85e2e07acdac7e288c0ac85e35580038a7020964f2e533`
- Final ZIP SHA-256: `84f7a0f920002fe73089d3517c29ed774c97d88f86ba84cc597f9b17544a70ce`

## DCSR
Application level: **DIRECT INTEGRATION**.

Recorded conditions:
- Full Dataset: **383,876 bytes**
- Delta: **4,398 bytes**
- Delta / Full: **約1.15%**
- small-observation cache enabled median: **594.860 ms**
- disabled median: **486.260 ms**

このsmall-observation条件ではcacheの方が遅かったため、**高速化は主張せず通常評価fallback**を維持します。Delta比率も条件限定結果です。

## License
Current repository distribution: **Apache License 2.0** — see repository [LICENSE](../LICENSE) and [NOTICE](../NOTICE).

Creator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**
