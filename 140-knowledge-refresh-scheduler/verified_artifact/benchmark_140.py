import json,time,statistics
from dataclasses import replace
import noepin_al_140_knowledge_refresh_scheduler as m
b='BENCH'; e='EPOCH-B'; xs=[]
for i in range(2000):
    xs.append(m.KnowledgeItem(f'K-{i:04d}','SRC-T','PROJECT-A',(f'TRACE-{i:04d}',),.55+(i%5)*.08,.05+(i%7)*.10,.10+(i%6)*.12,.05+(i%4)*.15,50+(i%900),1200+(i%5)*300,i%41==0,m.RefreshStatus.NOT_ATTEMPTED,b,e))
q=m.SchedulerRequest('BENCH-140',tuple(xs),m.default_policy(),b,e)
full=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(5): m.evaluate(q)
    full.append((time.perf_counter()-t)*1000/5)
st=m.prepare_state(q,b,e); prep=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(20): m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_items_fingerprint=st.items_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)
    prep.append((time.perf_counter()-t)*1000/20)
ys=list(xs); ys[-1]=replace(ys[-1],age_seconds=ys[-1].age_seconds+1); q2=replace(q,items=tuple(ys)); st2=m.prepare_state(q2,b,e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
fb=len(m._canon(q2)); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 2000 Knowledge Items; TTL/decay priority queue using importance/volatility/usage/refresh-cost plus critical stale fail-safe; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required},sort_keys=True))
