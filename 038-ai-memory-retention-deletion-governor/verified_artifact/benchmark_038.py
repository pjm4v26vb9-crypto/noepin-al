import json, statistics, time
from dataclasses import replace
import noepin_al_038_memory_governor as m

p=m.MemoryPolicy("p1",2,7,frozenset({"assist","care"}),3600,86400,delete_requires_human=True)
r=m.MemoryRecordMeta("mem1",100,1000,frozenset({"assist"}),"INTERNAL","p1",2,7)
q=m.MemoryRequest("USE","assist",500,classification="INTERNAL")
prep=m.prepare(p,q,r)
pf=m.fingerprint(p); qf=m.fingerprint(q); rf=m.fingerprint(r)

full=[]; recompute=[]; prematerialized=[]
for _ in range(7):
    t=time.perf_counter()
    for i in range(20000): m.evaluate(p,q,r)
    full.append((time.perf_counter()-t)*1000)
    t=time.perf_counter()
    for i in range(20000): m.reuse_prepared(prep,p,q,r) or m.evaluate(p,q,r)
    recompute.append((time.perf_counter()-t)*1000)
    t=time.perf_counter()
    for i in range(20000): m.reuse_prepared_by_fingerprints(prep,request_fingerprint=qf,policy_fingerprint=pf,record_fingerprint=rf,authority_epoch=7) or m.evaluate(p,q,r)
    prematerialized.append((time.perf_counter()-t)*1000)

base={f"m{i}":m.MemoryRecordMeta(f"m{i}",0,100000,frozenset({"assist"}),"INTERNAL","p1",2,7) for i in range(5000)}
target=dict(base)
for i in range(50): target[f"m{i}"]=replace(target[f"m{i}"],expires_at=90000+i)
for i in range(5): del target[f"m{100+i}"]
for i in range(5): target[f"new{i}"]=m.MemoryRecordMeta(f"new{i}",0,120000,frozenset({"assist"}),"INTERNAL","p1",2,7)
delta=m.build_metadata_delta(base,target)
full_bytes=len(m._canon(target).encode())
delta_bytes=len(m._canon(delta).encode())
recon=m.apply_metadata_delta(base,delta)
print(json.dumps({
 "runtime":"Python standard library",
 "evaluation_condition":{"iterations":20000,"batches":7},
 "normal_eval_median_ms":statistics.median(full),
 "prepared_with_fingerprint_recompute_median_ms":statistics.median(recompute),
 "prepared_with_prematerialized_fingerprints_median_ms":statistics.median(prematerialized),
 "fallback_rule":"If canonical fingerprints are not already materialized or prepared path overhead is not beneficial, use normal evaluation.",
 "semantic_match":m.decision_digest([m.evaluate(p,q,r)])==m.decision_digest([m.reuse_prepared_by_fingerprints(prep,request_fingerprint=qf,policy_fingerprint=pf,record_fingerprint=rf,authority_epoch=7)]),
 "delta_condition":{"base_items":5000,"changed":50,"removed":5,"added":5,"full_bytes":full_bytes,"delta_bytes":delta_bytes,"ratio_percent":delta_bytes/full_bytes*100,"fingerprint_match":m.registry_fingerprint(recon)==m.registry_fingerprint(target)}
},sort_keys=True))
