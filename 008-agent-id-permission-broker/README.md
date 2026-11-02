# 008 — Agent ID & Permission Broker / エージェントID・権限ブローカー

**Status:** COMPLETE / VERIFIED  
**Creator:** **NOEPIN / のえぴん**

AI / AgentごとにIdentity、Role、Permit、Resource / Action Scope、期限、失効状態を分離し、最小権限で操作候補を判定するBrokerです。

重要な境界:
- Agent ID ≠ Authority
- Role claim ≠ Granted Role
- Permit presence ≠ Valid Permit
- Expired / Revoked Permit ≠ Authority
- Cached allow ≠ Current Authority
- Permission Decision ≠ Action Success

検証:
- Unit / Boundary / Authority: **51 / 51 PASS**
- Fresh Extract: **51 / 51 PASS**
- Replay: **6,000 decisions / divergence 0**
- Baseline mutation: **0**
- External action / commit paths: **0**

Final ZIP SHA-256: `5dc5265ed74587b00357089c3c5afc5692b7a7088cd30540298ef0e20f2a8d95`

Creator / Project Owner / Original Concept / Architecture Direction: **NOEPIN / のえぴん**  
Implementation / analysis / documentation support: AI-assisted using ChatGPT  
License / Rights: **NOT SPECIFIED**
