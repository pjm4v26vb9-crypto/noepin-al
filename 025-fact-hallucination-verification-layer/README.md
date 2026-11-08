# 025 — Fact & Hallucination Verification Layer / 事実確認・幻覚検証レイヤー

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

AIのClaimをEvidence・Source Verification・Freshness・Target Version・Support / Contradictionなどに分けて検証するLayerです。

この技術は「Verified Sourceだから真実」とは扱わず、Truth / World Fact / Memory Truth / Action Successへの自動昇格を防ぎます。

## Authority boundaries

- Verified Source ≠ Claim Truth
- Source Verification PASS ≠ Claim Verification PASS
- Multiple Supporting Sources ≠ Absolute Truth
- Confidence / Support Score ≠ Truth Authority
- Primary Source ≠ Automatically Correct
- Evidence Fingerprint Match ≠ Evidence Freshness
- Verified Candidate ≠ World Fact
- Verified Candidate ≠ Memory Truth
- Human Approval Evidence ≠ Action Execution
- Cache Hit ≠ Verification PASS for a changed request
- Candidate Verification ≠ Action Success

## 公開内容
- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Tests / Replay / Benchmark / Production Gate等、Final ZIPに含まれる検証用ファイルは、存在するものを元のファイル名・内容のまま収録しています。
- README等の文書から似たコードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification

- Unit / Boundary / Authority: **61 / 61 PASS**
- Fresh Extract: **61 / 61 PASS**
- Replay: **6,000 evaluations / divergence 0**
- External Network / Process / Tool / Filesystem mutation primitives: **0**
- Execute / Commit methods: **0**
- Completion defects found and closed: **2**
- Baseline mutation: **0**

## Integrity

- Source SHA-256: `7d0cad64c886db36b359ceba90f03c677c20c60c59d9cdd83c636c3804132f7e`
- Test SHA-256: `090ba0bd5bef355156e0c8708efb5fcdd0916963a456220009efb8fce56c6825`
- Final ZIP SHA-256: `530048e1fc273dff768a5cf4e8db7ccb61c1384b72219474a226d36fdf47f123`

## DCSR

Application level: **AUXILIARY**. 完全一致するVerification Request + Policy Stateのみread-side再利用します。Claim / Target Version / Evidence Bindingが変われば再評価し、DCSR/cacheからTruth、World Fact、Memory Truth、Action Successを生成しません。

Synthetic exact-state benchmarkではcache enabled中央値 **1017.108 ms**、disabled中央値 **1019.588 ms**で**ほぼ同等**でした。小規模Requestで有意な高速化は主張しません。

## License

Current repository distribution: **Apache License 2.0** — see repository [LICENSE](../LICENSE) and [NOTICE](../NOTICE).

Creator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**
