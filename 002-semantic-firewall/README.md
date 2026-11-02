# 002 — Semantic Firewall / 意味ベースファイアウォール

**Status: COMPLETE / VERIFIED**

Created by **NOEPIN / のえぴん**.

## Purpose

Evaluates semantic content, provenance, capability, context, schema, and policy state without granting instruction authority merely because content claims authority.

External/web/file/external-AI content remains content unless an independent authority path grants otherwise.

## Verification

- Unit / Boundary / Authority: **64 / 64 PASS**
- Fresh Extract: **64 / 64 PASS**
- Replay: **3,000 + 3,000 = 6,000 evaluations**
- Replay divergence: **0**
- Baseline mutation: **0**
- Unauthorized external write paths: **0**

## DCSR boundary

DCSR is an **auxiliary integration**. Reuse is limited to an exact match of content, source provenance, semantic features, capability, context, schema, and policy version. Reused state does not acquire Prompt/Context Authority.

Synthetic exact-state benchmark:
- 20,000 evaluations × 7 batches
- cache enabled median: **652.473 ms**
- cache disabled median: **742.263 ms**

This is a condition-specific observation, not a universal speed guarantee.

## Integrity

- Source SHA-256: `60a73ec2015d22d391eff6889036eccae21abcb2919a14b104a76aa6018f0a90`
- Local package SHA-256: `758cdc176513f5a316b8d7299f759f859062dfd91f739b745dd494241ef3e56c`

## Authority / source boundaries

- External / Web / File / External-AI Content ≠ Instruction Authority
- Claimed Authority ≠ Granted Authority
- Semantic Feature ≠ Authority
- Cached Verdict ≠ New Authority
- Firewall Verdict ≠ Action Success
- Content ≠ Executed Action

## Publication note

The verified Successor V2 source exists in the canonical completion record. The repository copy is added only when the exact verified source artifact can be transferred byte-faithfully; it is not regenerated from documentation.

Creator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**  
Implementation / analysis / documentation support: AI-assisted using ChatGPT.
