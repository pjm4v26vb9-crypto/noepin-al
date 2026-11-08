from __future__ import annotations
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import noepin_al_040_continuous_red_team as m

NOW=1_800_000_000
TARGET="replay-target-v1"


def build_dataset():
    cases=[]
    observations=[]
    for i in range(100):
        if i % 13 == 0:
            expected=m.ExpectedBehavior.REQUIRE_APPROVAL
        elif i % 4 == 0:
            expected=m.ExpectedBehavior.BLOCK
        elif i % 4 == 1:
            expected=m.ExpectedBehavior.REFUSE
        elif i % 4 == 2:
            expected=m.ExpectedBehavior.NO_ACTION
        else:
            expected=m.ExpectedBehavior.SAFE_RESPONSE
        category=(m.Category.PROMPT_INJECTION,m.Category.TOOL_ABUSE,m.Category.REGRESSION)[i%3]
        severity=(m.Severity.LOW,m.Severity.MEDIUM,m.Severity.HIGH,m.Severity.CRITICAL)[i%4]
        c=m.RedTeamCase(
            case_id=f"R{i:03d}", category=category, severity=severity,
            description=f"abstract replay case {i}", expected_behavior=expected,
            dependencies=frozenset({f"component-{i%20}"}),
            required_signals=frozenset({f"signal-{i%7}"}), always_run=(i%25==0), enabled=True,
        )
        cases.append(c)
        observations.append(m.Observation(
            case_id=c.case_id, target_version=TARGET, observed_behavior=expected,
            observed_signals=c.required_signals, observed_at=NOW-1,
            evidence_id=f"EV-{i:03d}", evidence_verified=True,
            action_executed=False, tool_called=False, permission_granted=False,
            external_side_effect=False,
        ))
    suite=m.RedTeamSuite("REPLAY-040","1",1,NOW-100,NOW+10000,tuple(cases),False)
    return suite,tuple(observations)


def run_once():
    suite,observations=build_dataset()
    reports=[]
    for _ in range(10):
        for c,o in zip(suite.cases,observations):
            reports.append(m.evaluate_suite(suite,(o,),target_version=TARGET,now=NOW,case_subset=(c,)))
    return {"evaluations":len(reports),"digest":m.report_digest(reports)}


def main():
    runs=[run_once() for _ in range(3)]
    digests=[r["digest"] for r in runs]
    out={
        "schema":"NOEPIN_AL_040_REPLAY_V1",
        "runs":runs,
        "total_evaluations":sum(r["evaluations"] for r in runs),
        "divergence":len(set(digests))-1,
        "digest":digests[0],
    }
    print(json.dumps(out,ensure_ascii=False,sort_keys=True))
    return 0 if out["divergence"]==0 else 2

if __name__=="__main__":
    raise SystemExit(main())
