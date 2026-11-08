# 058 — Task-Scoped Short-Lived Credentials / タスク単位短命資格情報

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

Task / Run / Role / Permit / Expiry / Revocationにbindingされた短命Credential候補を評価するControlです。CredentialのMint / Persist / Use / Revocation実行は行いません。

- Credential Candidate ≠ Credential Issued
- Expiry Check ≠ Permission Grant
- Revocation Candidate ≠ Revocation Executed
- Run Binding ≠ Task Success
- Cached Credential State ≠ Authoritative Current State
- ALLOW ≠ Credential Use / Permission Grant

## 公開内容
- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Tests / Replay / Benchmark / Production Gate等、Final ZIPに含まれる検証用ファイルは、存在するものを元のファイル名・内容のまま収録しています。
- README等の文書から似たコードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification
- Tests: **160 / 160 PASS**
- Fresh Extract: **160 / 160 PASS**
- Replay: **6,000 / divergence 0**

## NOEPIN AL Production Use
**037〜057**を実制作Gateとして使用し、**21 / 21 PASS**。

## DCSR
**LIMITED APPLICATION**. Full **2675.476466 ms** vs Prepared **783.145481 ms**. Full **931,583 bytes** → Delta **17,000 bytes (約1.82%)**。Expiry / Revocation / Permit / Role / Credential Authorityは評価時に再確認します。

## Integrity
Final ZIP SHA-256: `d64f27bc6edd72a85f70cc4ac9c1c6d5bd762e0ad9ea2e91795ade25867841cc`  
Source SHA-256: `b2d2802b739a1cd4b6fb9fc5674f7e1f234ac87fbb06f0ec6d09600c6607d1ad`

## License
Current repository distribution: **Apache License 2.0** — see [LICENSE](../LICENSE) and [NOTICE](../NOTICE).
