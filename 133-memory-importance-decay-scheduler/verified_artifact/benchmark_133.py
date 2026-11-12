import json,time,statistics
from dataclasses import replace
import noepin_al_133_memory_importance_decay_scheduler as m
b='BENCH'; e='EPOCH-B'; ms=[]
for i in range(1200):
    ms.append(m.MemoryMetadata(f'M-{i:04d}',f'SRC-{i%11}',f'PURPOSE-{i%17}',100+(i%200),200+(i%500),i%25,(i%10)/10,(i%9)/9,.75+(i%20)/100, bool(i%4), i%211==0, i%197==0, i%181==0, m.RecordKind.MEMORY,b,e))
p=replace(m.default_policy(),now=1000); q=m.DecayRequest('BENCH-133',tuple(ms),p,b,e)
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
xs=list(ms); xs[-1]=replace(xs[-1],usage_count=xs[-1].usage_count+1); q2=replace(q,memories=tuple(xs)); st2=m.prepare_state(q2,b,e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
fb=len(m._canon(q2)); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 1200 memory metadata records; weighted time decay + usage/freshness/purpose + protected retention policy classification; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required},sort_keys=True))
