import json,time,statistics
from dataclasses import replace
import noepin_al_138_semantic_memory_deduplicator as m
b='BENCH'; e='EPOCH-B'; xs=[]
for i in range(1200):
    pair=i//2
    xs.append(m.MemoryClaim(f'M-{i:04d}',f'SEM-{pair:04d}',f'claim expression {i}',f'SCOPE-{pair%5}',f'T-{pair%7}',('CURRENT',),(('entity',f'E-{pair:04d}'),),.98+(i%2)*.005,(f'SRC-{i:04d}',),.80+(i%10)/100,m.RecordKind.MEMORY,True,b,e))
q=m.DedupRequest('BENCH-138',tuple(xs),m.default_policy(),b,e)
full=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(5): m.evaluate(q)
    full.append((time.perf_counter()-t)*1000/5)
st=m.prepare_state(q,b,e); prep=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(20): m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_memory_fingerprint=st.memory_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)
    prep.append((time.perf_counter()-t)*1000/20)
ys=list(xs); ys[-1]=replace(ys[-1],trust=.79); q2=replace(q,memories=tuple(ys)); st2=m.prepare_state(q2,b,e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
fb=len(m._canon(q2)); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 1200 Memory claims in 600 semantic duplicate pairs; semantic-key clustering + structural Time/Scope/critical diff checks + provenance-preserving canonicalization candidates; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required},sort_keys=True))
