# 028｜複数AI合議・クォーラム判定 / Multiple-AI Quorum Decision

**NOEPIN AL Technology Work 028**  
**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

## 作品概要
複数AIのVoteを単純多数決ではなく、Voter Identity・Model Family・Independence Group・Context・Evidence・Ballot Version・Confidenceまで分離してQuorum Candidateを判断するControlです。

## 設計上の重要な境界
- Majority ≠ Truth
- Quorum Candidate ≠ Truth
- Quorum Candidate ≠ Permission Grant
- Quorum Candidate ≠ Action Execution
- Verified Voter Identity ≠ Correct Vote
- Model Diversity ≠ Evidence Independence
- Quorum Candidate ≠ Action Success

## 検証
- Unit / Boundary / Authority: **72 / 72 PASS**
- Fresh Extract: **72 / 72 PASS**
- Replay: **6,000 evaluations / divergence 0**
- Execute / Commit / Grant methods: **0**
- Initial test-fixture defect corrected; production decision logic unchanged

## Integrity
Final ZIP SHA-256  
`47c3828c071608ad11a9b69fef1b2e29fd8b1aa40b8cfdf8e28be4e8438c7a5f`

Source SHA-256  
`1f984afe40e1fbd6918b852007e8e5b35ef2f923646cab69623443aaf964eb41`

## 技術資料
[技術フォルダを開く](../028-multiple-ai-quorum-decision/)  
[Verification Report](../028-multiple-ai-quorum-decision/NOEPIN_AL_028_FINAL_VERIFICATION_REPORT_20261102.md)  
[Artifact Seal](../028-multiple-ai-quorum-decision/NOEPIN_AL_028_FINAL_ARTIFACT_SEAL_20261102.json)

Current repository distribution: **Apache License 2.0**.  
Creator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**

[作品一覧へ戻る](README.md)
