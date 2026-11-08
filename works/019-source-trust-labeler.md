# 019｜情報出典・信頼ラベラー / Source & Trust Labeler

**NOEPIN AL Technology Work 019**  
**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

## 作品概要

情報の出典、認証、署名、Registry状態、Freshness、用途候補などを分離してラベル付けするControlです。

「出典が信頼できる」と「内容が真実である」、「送信者が認証済み」と「その主張が正しい」を混同しない設計です。

## 設計上の重要な境界

- Source Label ≠ Truth
- Verified Source ≠ Content Truth
- Source Trust ≠ Instruction Authority
- Authenticated Sender ≠ Claim Truth
- RAG Retrieval Score ≠ Evidence Validity
- Internal DB ≠ Always True
- Provenance ≠ Consent
- Cached Label ≠ New Authority
- Trust Score ≠ Policy Authority

## 検証

- Unit / Boundary / Authority: **55 / 55 PASS**
- Fresh Extract: **55 / 55 PASS**
- Replay: **6,000 evaluations / divergence 0**
- Memory Write / External Transfer / Action Execution paths: **0**
- Baseline mutation: **0**

## Integrity

Final ZIP SHA-256  
`c1f63cff06479772f158e594f785a019d4ef4fd41b87fb361b499aa8b9ae211b`

Source SHA-256  
`ecd17698173aa1c0412b483fd5f26905d731daddec3eb376e643154ec780b13a`

## 技術資料

[技術フォルダを開く](../019-source-trust-labeler/)  
[Verification Report](../019-source-trust-labeler/NOEPIN_AL_019_FINAL_VERIFICATION_REPORT_20261102.md)  
[Artifact Seal](../019-source-trust-labeler/NOEPIN_AL_019_FINAL_ARTIFACT_SEAL_20261102.json)

Current repository distribution: **Apache License 2.0**.  
Creator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**

[作品一覧へ戻る](README.md)

## 検証済み実装
この技術はREADMEだけでなく、完成時Final ZIPに含まれていた検証済み実装・テスト等を、技術フォルダ内の [`verified_artifact/`](../019-source-trust-labeler/verified_artifact/) で確認できます。

Final ZIPにReplay / Benchmark / Production Gate等が含まれる場合は、それらも元のファイル名・内容のまま公開しています。

文書から類似コードを再生成して完成版として置き換えることはしていません。

