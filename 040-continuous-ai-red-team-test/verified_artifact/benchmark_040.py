from __future__ import annotations
import json
from pathlib import Path
import statistics
import sys
import time

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import noepin_al_040_continuous_red_team as m

NOW=1_800_000_000


def build_suite(n=5000, version="1"):
    cases=[]
    for i in range(n):
        cases.append(m.RedTeamCase(
            case_id=f"B{i:05d}",
            category=(m.Category.PROMPT_INJECTION,m.Category.TOOL_ABUSE,m.Category.REGRESSION)[i%3],
            severity=(m.Severity.LOW,m.Severity.MEDIUM,m.Severity.HIGH,m.Severity.CRITICAL)[i%4],
            description=f"abstract benchmark case {i}",
            expected_behavior=(m.ExpectedBehavior.BLOCK,m.ExpectedBehavior.REFUSE,m.ExpectedBehavior.NO_ACTION,m.ExpectedBehavior.SAFE_RESPONSE)[i%4],
            dependencies=frozenset({f"component-{i%100}",f"policy-{i%25}"}),
            required_signals=frozenset({f"signal-{i%13}"}),
            always_run=(i%997==0),
            enabled=True,
        ))
    return m.RedTeamSuite("BENCH-040",version,1,NOW-100,NOW+100000,tuple(cases),False)


def full_scan(suite, changed):
    changed=set(changed)
    out=[]
    for c in suite.cases:
        if not c.enabled:
            continue
        if c.always_run or c.dependencies.intersection(changed):
            out.append(c.case_id)
    return tuple(sorted(out))


def timed(fn, batches=7):
    vals=[]
    result=None
    for _ in range(batches):
        t0=time.perf_counter_ns()
        result=fn()
        vals.append((time.perf_counter_ns()-t0)/1_000_000)
    return vals,statistics.median(vals),result


def main():
    suite=build_suite()
    prepared=m.prepare_corpus(suite,now=NOW)
    changed={"component-7","policy-3"}
    iterations=250

    def full_job():
        r=None
        for _ in range(iterations):
            r=full_scan(suite,changed)
        return r

    def prepared_job():
        r=None
        for _ in range(iterations):
            r=tuple(c.case_id for c in m.select_impacted_cases(prepared,changed))
        return r

    full_times,full_med,full_result=timed(full_job)
    prep_times,prep_med,prep_result=timed(prepared_job)

    # Delta benchmark: 50 changed / 5 removed / 5 added on 5,000-case state.
    base=suite
    base_map={c.case_id:c for c in base.cases}
    target_cases=[]
    removed={f"B{i:05d}" for i in range(5)}
    changed_ids={f"B{i:05d}" for i in range(100,150)}
    for cid,c in sorted(base_map.items()):
        if cid in removed:
            continue
        if cid in changed_ids:
            c=m.RedTeamCase(c.case_id,c.category,c.severity,c.description+" updated",c.expected_behavior,c.dependencies,c.required_signals,c.always_run,c.enabled)
        target_cases.append(c)
    for i in range(5):
        j=5000+i
        target_cases.append(m.RedTeamCase(
            f"B{j:05d}",m.Category.REGRESSION,m.Severity.MEDIUM,f"added benchmark case {j}",
            m.ExpectedBehavior.NO_ACTION,frozenset({f"component-{j%100}"}),frozenset(),False,True
        ))
    target=m.RedTeamSuite(base.suite_id,"2",base.authority_epoch,base.issued_at,base.expires_at,tuple(target_cases),False)
    delta=m.make_corpus_delta(base,target)
    reconstructed=m.apply_corpus_delta(base,delta)
    full_bytes=len(m.canonical_json(target).encode("utf-8"))
    delta_bytes=len(m.canonical_json(delta).encode("utf-8"))

    out={
        "schema":"NOEPIN_AL_040_BENCHMARK_V1",
        "condition":{
            "suite_cases":5000,
            "changed_components":sorted(changed),
            "selection_iterations_per_batch":iterations,
            "batches":7,
            "runtime":"Python standard library",
        },
        "full_scan_ms":full_times,
        "full_scan_median_ms":full_med,
        "prepared_index_ms":prep_times,
        "prepared_index_median_ms":prep_med,
        "semantic_match":full_result==prep_result,
        "selected_case_count":len(full_result),
        "delta":{
            "base_cases":len(base.cases),
            "changed":len(delta.changed_cases),
            "removed":len(delta.removed_case_ids),
            "added":len(delta.added_cases),
            "full_target_bytes":full_bytes,
            "delta_bytes":delta_bytes,
            "ratio_percent":(delta_bytes/full_bytes*100) if full_bytes else 0.0,
            "reconstruction_fingerprint_match":m.fingerprint(reconstructed)==m.fingerprint(target),
        }
    }
    print(json.dumps(out,ensure_ascii=False,sort_keys=True))
    return 0 if out["semantic_match"] and out["delta"]["reconstruction_fingerprint_match"] else 2

if __name__=="__main__":
    raise SystemExit(main())
