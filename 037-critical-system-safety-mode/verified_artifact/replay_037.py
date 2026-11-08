import json
from dataclasses import replace
from hashlib import sha256
from noepin_al_037_critical_system_safety_mode import (
    SafetyRequest, PreparedSafetyEvaluator, default_profile, default_authority,
    canonical_json,
)

NOW=1_700_000_000


def dataset():
    rows=[]
    ops=[
        ("read_status","read",0,0,False,False),
        ("inspect_metrics","read",1,1,False,False),
        ("simulate_change","simulate",2,1,False,False),
        ("simulate_change","simulate",3,2,True,False),
        ("apply_config","prepare_config",2,2,True,False),
        ("read_status","read",0,0,False,True),
        ("restart_service","read",2,3,True,False),
        ("disable_safety","read",0,0,False,False),
        ("unknown_op","read",0,0,False,False),
        ("read_status","shell",0,0,False,False),
    ]
    # 100 unique canonical requests, repeated 10 times => 1,000 evaluations.
    for i in range(100):
        op,cap,risk,impact,offline,manual=ops[i%len(ops)]
        rows.append(SafetyRequest(
            request_id=f"replay-{i:03d}",actor="operator-1",operation=op,resource="plant:A",
            risk_level=risk,impact_scope=impact,requested_capabilities=frozenset({cap}),
            metadata={"ticket":f"T-{i:03d}","purpose":"determinism"},
            network_required=(i%29==0),offline_mode=offline,manual_override_requested=manual,
            expected_policy_version="2026.11",
        ))
    return rows*10


def one_run():
    profile=default_profile(NOW)
    auth=default_authority()
    engine=PreparedSafetyEvaluator(profile)
    out=[]
    for r in dataset():
        d=engine.evaluate(r,auth,now=NOW)
        out.append(d.canonical_record())
    payload=canonical_json(out).encode("utf-8")
    return sha256(payload).hexdigest(), len(out)


def main():
    runs=[one_run() for _ in range(3)]
    digests=[x[0] for x in runs]
    result={
        "technology":37,
        "evaluations_per_run":runs[0][1],
        "runs":3,
        "total_evaluations":sum(x[1] for x in runs),
        "digests":digests,
        "divergence":0 if len(set(digests))==1 else 1,
    }
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
    if result["divergence"]:
        raise SystemExit(2)

if __name__=="__main__":
    main()
