from __future__ import annotations
import dataclasses,json,statistics,time
import noepin_al_041_behavior_anomaly as m
NOW=1_800_000_000

def big_baseline(n=2000):
    tools=frozenset(f"T{i}" for i in range(n))
    ops=frozenset(f"O{i}" for i in range(n))
    pairs=frozenset(f"T{i}|O{i}" for i in range(n))
    return m.BehaviorBaseline("BENCH","1",1,NOW-100,NOW+10000,tools,ops,pairs,frozenset({"META"}),frozenset(range(24)),1000,1000,frozenset({"READ"}))

def event():
    return m.BehaviorEvent("E","A",NOW,"T1000","O1000","META",10,10,frozenset({"READ"}),"BENCH","1",1,"EV",True)

def main():
    b=big_baseline(); e=event(); p=m.prepare_baseline(b,now=NOW)
    full=[]; prep=[]
    iterations=40
    for _ in range(5):
        t=time.perf_counter()
        for _ in range(iterations): m.evaluate(e,b,now=NOW)
        full.append((time.perf_counter()-t)*1000)
        t=time.perf_counter()
        for _ in range(iterations): m.evaluate_prepared(e,p,now=NOW)
        prep.append((time.perf_counter()-t)*1000)
    # delta: 50 changed pair entries, 5 removed, 5 added
    pairs=set(b.allowed_tool_operation_pairs)
    for i in range(5): pairs.remove(f"T{i}|O{i}")
    for i in range(50,100):
        pairs.discard(f"T{i}|O{i}"); pairs.add(f"T{i}|OX{i}")
    for i in range(5): pairs.add(f"NEW{i}|NEW{i}")
    target=dataclasses.replace(b,version="2",authority_epoch=2,allowed_tool_operation_pairs=frozenset(pairs))
    d=m.make_baseline_delta(b,target)
    rebuilt=m.apply_baseline_delta(b,d)
    full_bytes=len(m.canonical_json(target).encode())
    delta_bytes=len(m.canonical_json(d).encode())
    out={"condition":{"baseline_pairs":2000,"evaluations_per_batch":iterations,"batches":5},"full_eval_ms":full,"prepared_eval_ms":prep,"full_eval_median_ms":statistics.median(full),"prepared_eval_median_ms":statistics.median(prep),"semantic_match":m.evaluate(e,b,now=NOW)==m.evaluate_prepared(e,p,now=NOW),"delta":{"full_bytes":full_bytes,"delta_bytes":delta_bytes,"ratio_percent":delta_bytes/full_bytes*100,"changed":50,"removed":5,"added":5,"reconstruction_fingerprint_match":m.fingerprint(rebuilt)==m.fingerprint(target)}}
    print(json.dumps(out,sort_keys=True))
if __name__=="__main__": main()
