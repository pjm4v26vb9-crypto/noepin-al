# 028 — Multiple-AI Quorum Decision / 複数AI合議・クォーラム判定

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

複数AIのVoteを単純多数決ではなく、Voter Identity / Model Family / Independence Group / Context / Evidence / Ballot Version / Confidenceまで分離して評価し、Quorum Candidateを返すControlです。

## Authority boundaries

- Majority ≠ Truth
- Quorum Candidate ≠ Truth
- Quorum Candidate ≠ Permission Grant
- Quorum Candidate ≠ Action Execution
- Verified Voter Identity ≠ Correct Vote
- Model Diversity ≠ Evidence Independence
- Context Diversity ≠ Truth
- Human Approval Evidence ≠ Action Execution
- Cache Hit ≠ Current Authority
- Quorum Candidate ≠ Action Success

## 公開内容
- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Tests / Replay / Benchmark / Production Gate等、Final ZIPに含まれる検証用ファイルは、存在するものを元のファイル名・内容のまま収録しています。
- README等の文書から似たコードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification

- Unit / Boundary / Authority: **72 / 72 PASS**
- Fresh Extract: **72 / 72 PASS**
- Replay: **6,000 evaluations / divergence 0**
- Shell / Process / Network / External filesystem mutation primitives: **0**
- Execute / Commit / Grant methods: **0**
- Initial test-fixture defect corrected; production decision logic unchanged
- Baseline mutation: **0**

## Integrity

- Source SHA-256: `1f984afe40e1fbd6918b852007e8e5b35ef2f923646cab69623443aaf964eb41`
- Test SHA-256: `8ed02c2e714817c0d10a1323e96c931e65a4a52991df8cf57b3e52918c8ac9d9`
- Final ZIP SHA-256: `47c3828c071608ad11a9b69fef1b2e29fd8b1aa40b8cfdf8e28be4e8438c7a5f`

## DCSR

Application level: **LIMITED**. 完全一致するQuorum Request + Policy / Authority Stateのみread-side再利用します。Voter / Policy / Authority / Ballotの変更時は再評価します。

Recorded benchmark:
- cache enabled median: **1618.030 ms**
- cache disabled median: **2065.468 ms**

条件限定結果であり、一般速度保証ではありません。

## License

Current repository distribution: **Apache License 2.0** — see repository [LICENSE](../LICENSE) and [NOTICE](../NOTICE).

Creator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**
