# 032 — Vector DB & Embedding Integrity Guard / ベクトルDB・埋め込み整合性ガード

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

RAG / Vector DBのDocument・Embedding・Indexを、Source Binding・Document ACL・Embedding Model/Version/Dimension・Vector/Index Fingerprint・Provenance/Signature・Requester・Classification/Purpose/Consentまで分離して検証するControlです。

## Authority boundaries
- Vector Similarity ≠ Source Truth
- Fingerprint Match ≠ Document Permission
- Source Binding Verified ≠ Claim Truth
- Index Provenance Verified ≠ Retrieval Truth
- ACL Match ≠ Retrieval Success
- Embedding Model Match ≠ Semantic Correctness
- Quarantine Candidate ≠ Isolation Success
- Rebuild Candidate ≠ Index Rebuild Success
- Classification ≠ Truth
- Consent Evidence ≠ External Transfer Permission
- Cache Hit ≠ Current Authority after changed version/context/ACL
- Candidate Decision ≠ Action Success

## Verification
- Unit / Boundary / Authority: **86 / 86 PASS**
- Fresh Extract: **86 / 86 PASS**
- Replay: **6,000 evaluations / divergence 0**
- External mutation / execution primitives: **0**
- Execute / Commit / Grant / Quarantine-Data / Rebuild-Index methods: **0**
- Baseline mutation: **0**
- Completion defect closed: order-dependent Index Baseline fingerprint

## Integrity
- Source SHA-256: `a8d798f9196077401a64ef0186b45d61befd2a6b319f5decf9f270ecd88aba30`
- Test SHA-256: `e12392cc9cc1fe7c4a4cf4a044eb0d6d3ae42813b7882db96a51cf777ac8dabd`
- Final ZIP SHA-256: `51ca99fb65b9755e045ae908a6932cefd70379920397c3fbf1fe36e334a95762`

## DCSR
Application level: **DIRECT INTEGRATION**.

Recorded conditions:
- Full Index: **1,240,051 bytes**
- Delta: **13,962 bytes**
- Delta / Full: **約1.13%**
- small-observation cache enabled median: **1054.958 ms**
- disabled median: **1056.091 ms**

small-observation条件は**ほぼ同等**のため高速化は主張しません。Delta比率も条件限定結果です。

## License
Current repository distribution: **Apache License 2.0** — see repository [LICENSE](../LICENSE) and [NOTICE](../NOTICE).

Creator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**
