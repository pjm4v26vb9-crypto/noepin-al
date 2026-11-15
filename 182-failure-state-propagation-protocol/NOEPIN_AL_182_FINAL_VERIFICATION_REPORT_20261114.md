# NOEPIN AL 182 — Final Verification Report — 2026-11-14

## Identity
- Technology: 182｜Failure-State Propagation
- Canonical ID: NOEPIN-AL-182
- English: AL Failure-State Propagation Protocol
- Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
- Implementation / analysis / documentation support: AI-assisted using ChatGPT
- License / Rights: NOT SPECIFIED
- DCSR: Direct Integration / 直接統合

## Canonical behavior
The protocol fixes severity order as OK < HOLD < HUMAN_APPROVAL < DENY < ABORT. Higher incoming severity propagates monotonically; lower incoming severity cannot weaken the current state. Explicit downgrade requires current Recovery Authorization bound to from/to state, binding, and state epoch. Unknown states are rejected. DCSR may transport failure-state records but does not downgrade severity, invent/substitute Recovery Authorization, or promote cached/reconstructed state into current authority.

## Default verified candidate
- Propagation ID: FSP-182-A
- Current state: HOLD
- Incoming state: DENY
- Effective state: DENY
- Severity: 1 → incoming 3 → effective 3
- Decision: ALLOW
- Next action: PROPAGATE_FAILURE_STATE_CANDIDATE
- Engine state: FAILURE_STATE_PROPAGATED_CANDIDATE
- Escalated: True
- Next gate candidate: True
- Propagation Fingerprint: f97ee300c59cacba9db2339fdd62e5ef4cda4cd017e3570f16f985160d41130a
- Authorized recovery example: DENY → HOLD / decision ALLOW / authorization valid=True / downgrade accepted=True / recovery executed=False

## Verification
- Normal tests: 160 / 160 PASS
- Fresh tests: 160 / 160 PASS
- Normal replay: 3000 / divergence 0 / digest be7131a8e14794cee9f6c04e1fef85ac9f7fc0238be6b9e791c2079c023ad69f
- Fresh replay: 3000 / divergence 0 / digest be7131a8e14794cee9f6c04e1fef85ac9f7fc0238be6b9e791c2079c023ad69f
- Normal Production Gate: 145 / 145 PASS
- Fresh Production Gate: 145 / 145 PASS
- Static Safety: external execution paths 0 / unauthorized write paths 0
- Provisional Fresh Manifest: 2588 / 2588 matched
- Baseline preservation against frozen 181 Final Manifest: 2567 / 2567 matched; mutation 0 / PASS=True

## Benchmark
Normal: Full 0.0117576380 ms / Prepared 0.0193414720 ms / semantic match True
Fresh: Full 0.0116837060 ms / Prepared 0.0188007150 ms / semantic match True
Condition: Python stdlib; 1000 Failure-State Propagation evaluations per round; Current/Incoming/Proposed State + Recovery Authorization binding; full request batch vs one changed Failure State segment; 5 full x 1000 and 5 prepared x 1000; prepared path re-evaluates current Authority-side state and Recovery Authorization. Condition-specific only; no universal speedup/performance guarantee.
DCSR Delta: 182001 bytes → 154 bytes / 0.0846149197%
Missing-only: 1 record (FAILURE_STATE) / 55 metadata bytes / full resend False

## Defects
- Production defect: 0
- Test fixture defect: 0
- Benchmark harness defect: 0
- Replay helper defect: 0
- Production Gate helper defect: 0
- Execution harness invocation defect: 0

## Authority boundary
Failure-State propagation validity or an effective DENY/ABORT state ≠ Truth, Permission Grant, Recovery execution, Stop execution, Permit issuance, Tool invocation, Action Execution, Action Success, or universal Safety Proof. Recovery Authorization evidence permits only a downgrade candidate inside this protocol; it is not promoted to Truth or Permission and does not execute recovery. DCSR cannot lower severity, invent/substitute Recovery Authorization, or promote cached/reconstructed failure state.

- exact registered Origin GUID was not freshly reverified.
- Pre-existing Notion V1 attachment byte identity was not freshly reverified.
