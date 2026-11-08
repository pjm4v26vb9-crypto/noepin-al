import json
import statistics
import time
from dataclasses import asdict, replace
from noepin_al_037_critical_system_safety_mode import (
    SafetyRequest, SafeProfile, PreparedSafetyEvaluator, default_authority,
    evaluate_unprepared, compute_policy_delta, apply_policy_delta, canonical_json, fingerprint,
)

NOW=1_700_000_000


def large_profile(n=500):
    allowed=frozenset({f"read_{i:04d}" for i in range(n)})
    return SafeProfile(
        profile_id="critical-benchmark",policy_version="bench-v1",issued_at=NOW-100,expires_at=NOW+10000,
        revoked=False,allowed_operations=allowed,denied_operations=frozenset({"disable_safety"}),
        human_approval_operations=frozenset(),offline_allowed_operations=allowed,
        allowed_capabilities=frozenset({"read"}),required_metadata=frozenset({"ticket","purpose"}),
        max_risk_allow=1,max_impact_allow=1,max_risk_human_approval=4,max_impact_human_approval=4,
        require_offline_for_critical=False,
    )


def raw_profile(p):
    d=asdict(p)
    for k in ["allowed_operations","denied_operations","human_approval_operations","offline_allowed_operations","allowed_capabilities","required_metadata"]:
        d[k]=sorted(d[k])
    return d


def requests_1000():
    unique=[]
    for i in range(100):
        unique.append(SafetyRequest(
            request_id=f"bench-{i:03d}",actor="operator-1",operation=f"read_{i%500:04d}",resource="plant:A",
            risk_level=i%2,impact_scope=(i//2)%2,requested_capabilities=frozenset({"read"}),
            metadata={"ticket":f"B-{i}","purpose":"benchmark"},expected_policy_version="bench-v1",
        ))
    return unique*10


def authority_for(reqs):
    a=default_authority()
    grants={f"{r.operation}@plant:A" for r in reqs}
    return replace(a,permission_grants=frozenset(grants),authority_epoch="bench-epoch")


def timed(fn,batches=5):
    vals=[]
    for _ in range(batches):
        t0=time.perf_counter_ns(); fn(); t1=time.perf_counter_ns()
        vals.append((t1-t0)/1_000_000)
    return vals


def main():
    p=large_profile(); raw=raw_profile(p); rs=requests_1000(); auth=authority_for(rs)

    def baseline():
        sig=[]
        for r in rs:
            d=evaluate_unprepared(raw,r,auth,now=NOW)
            sig.append(d.result_fingerprint)
        return fingerprint(sig)

    def prepared():
        e=PreparedSafetyEvaluator(p); sig=[]
        for r in rs:
            d=e.evaluate(r,auth,now=NOW)
            sig.append(d.result_fingerprint)
        return fingerprint(sig)

    base_sig=baseline(); prep_sig=prepared()
    if base_sig!=prep_sig:
        raise SystemExit("SEMANTIC_DIVERGENCE")

    base_times=timed(baseline)
    prep_times=timed(prepared)

    # DCSR delta payload check on 5,000 operations: 50 changed via remove/add.
    base5=large_profile(5000)
    remove={f"read_{i:04d}" for i in range(5)}
    add={f"new_read_{i:04d}" for i in range(5)}
    target=replace(base5,policy_version="bench-v2",allowed_operations=(base5.allowed_operations-remove)|add)
    delta=compute_policy_delta(base5,target)
    rebuilt=apply_policy_delta(base5,delta)
    if fingerprint(rebuilt)!=fingerprint(target):
        raise SystemExit("DELTA_RECONSTRUCTION_DIVERGENCE")
    full_bytes=len(canonical_json(target).encode("utf-8"))
    delta_bytes=len(canonical_json(delta).encode("utf-8"))

    result={
        "runtime":"Python standard library",
        "profile_allowed_operations":500,
        "evaluations_per_batch":1000,
        "batches":5,
        "baseline_full_parse_ms":base_times,
        "prepared_dcsr_ms":prep_times,
        "baseline_median_ms":statistics.median(base_times),
        "prepared_median_ms":statistics.median(prep_times),
        "semantic_digest_match":True,
        "delta_state_items":5000,
        "delta_removed":5,
        "delta_added":5,
        "full_bytes":full_bytes,
        "delta_bytes":delta_bytes,
        "delta_ratio_percent":delta_bytes/full_bytes*100.0,
    }
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))

if __name__=="__main__":
    main()
