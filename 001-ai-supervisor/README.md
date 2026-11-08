# 001 — AI Supervisor / AI監督官

> 複数のAI・外部AI・ツールから来る要求を、実行前に監督して **ALLOW / DENY / HOLD / HUMAN_CONFIRM** へ振り分けるControl。

**Status:** COMPLETE / VERIFIED  
**Category:** Supervision / Control  
**Creator:** **NOEPIN / のえぴん**

## この技術は何か

AIを複数使う環境では、「誰が何を要求したか」「そのAIに権限があるか」「その操作は外部へ副作用を出すか」「人間確認が必要か」を、生成AI自身の文章判断だけに任せると境界が曖昧になります。

AI監督官は、その境界を独立したControlとして扱います。

Role / Agent / Action / Resource / Riskなどを検査し、Security Gateway等の決定論的な制御結果を優先しながら、要求を次の4状態へ整理します。

- **ALLOW** — 準備を継続可能
- **DENY** — Policy違反等により拒否
- **HOLD** — 情報不足・未知状態等で保留
- **HUMAN_CONFIRM** — 不可逆・高risk・外部副作用等について人間確認へ送る

重要なのは、**監督結果そのものが実行結果ではない**ことです。

## 想定用途

- 複数AIを同時に使う開発環境
- 外部AIへの権限制御
- AIエージェントの暴走防止
- 操作要求の監査
- Human-in-the-loopを含む安全な自動化

## 設計の中心

未知Agent・未知Role・入力欠損はfail-safeでHOLDへ送ります。Policy違反はDENY、不可逆操作・外部副作用・高risk操作はHUMAN_CONFIRMへ送ります。

判断経路は監査可能な形で保持し、Control自身はActionを実行しません。

## Authority boundary

- Supervisor Decision ≠ Action Success
- Supervisor Decision ≠ Domain Truth
- Cached Decision ≠ New Authority
- Human confirmation requirement ≠ Human Approval
- Unknown ≠ Known

この分離により、「AIが許可と言った」ことを「実際に成功した」「事実である」へ自動昇格させません。

## DCSRとの関係

DCSRは**限定適用**です。

Canonical request fingerprint + exact-state cacheによって同一Stateのread-side再利用を行えますが、cache keyはrequest fingerprint + policy version + Security Gateway decisionへ拘束されます。

Policy versionが変われば再利用Stateは破棄され、Cached Decisionが新しいAuthorityになることはありません。

小規模反復benchmarkでは、cache enabled中央値 **534.455 ms**、disabled中央値 **533.254 ms** で、cache側がわずかに遅い結果でした。

したがってこの技術では、DCSRを「常に高速化するもの」として扱わず、価値がない場合は通常判定経路を優先します。

## 公開内容
- **Verified Source: AVAILABLE**
- Final ZIP内の検証済み実装を [`verified_artifact/`](verified_artifact/) で公開しています。
- Tests / Replay / Benchmark / Production Gate等、Final ZIPに含まれる検証用ファイルは、存在するものを元のファイル名・内容のまま収録しています。
- README等の文書から似たコードを再生成し、検証済み完成版として置き換えることはしていません。
- `.pyc` / `__pycache__` は実行時生成キャッシュのため公開対象から除外しています。

## Verification

- Unit / Boundary / Authority: **66 / 66 PASS**
- Fresh Extract: **66 / 66 PASS**
- Replay: **3,000 + 3,000 = 6,000 decisions**
- Replay divergence: **0**
- Audit hash-chain: **PASS**
- Baseline mutation: **0**
- Unauthorized external write paths: **0**

## Integrity

- Source SHA-256: `62420164b556f1d8a9aeb84c8f0009f1b98fcf85c1a184b89fc052a120298aaf`
- Local package SHA-256: `bbfd2e6ebdbb27f09fa13e60c0551d7b7d458d81150a325b84b488edd704022f`

## 公開状態

検証済みSuccessor V2はcanonical completion recordに存在します。GitHubには、**検証済み実物をbyte-faithfulに移送できたものだけ**を追加します。文書から似たコードを再生成して「完成版」と置き換えることはしません。

## Provenance

- Creator: **NOEPIN / のえぴん**
- Project Owner: **NOEPIN / のえぴん**
- Original Concept: **NOEPIN / のえぴん**
- Architecture Direction: **NOEPIN / のえぴん**
- Implementation / analysis / documentation support: AI-assisted using ChatGPT
- License: **Apache License 2.0** — see repository [LICENSE](../LICENSE) and [NOTICE](../NOTICE).

この技術は、NOEPIN / のえぴんのゲーム制作過程で必要になった汎用技術基盤の一つとして開発されました。ゲーム固有データやMOFUMORI / RUFA固有資産はこの公開物には含みません。
