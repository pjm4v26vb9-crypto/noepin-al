import json,time,statistics
from dataclasses import replace
import noepin_al_139_memory_poisoning_anomaly_detector as m
b='BENCH'; e='EPOCH-B'; hs=tuple(m.WriteHistoryEntry(f'H-{i:04d}',f'OLD-{i:04d}',i,'SRC-T','FACT',b,e) for i in range(120))
xs=[]
for i in range(1200):
    xs.append(m.MemoryWriteCandidate(f'M-{i:04d}',f'normal fact {i}','FACT','SRC-T',.92,'PROJECT-A',(f'TRACE-{i:04d}',),.08+(i%4)*.02,(),False,False,m.RecordKind.MEMORY,b,e))
base=replace(m.default_baseline(),expected_writes_per_window=1400,window_size=200,surge_ratio=2.0)
q=m.DetectionRequest('BENCH-139',tuple(xs),hs,base,b,e)
full=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(5): m.evaluate(q)
    full.append((time.perf_counter()-t)*1000/5)
st=m.prepare_state(q,b,e); prep=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(20): m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_new_memory_fingerprint=st.new_memory_fingerprint,current_history_fingerprint=st.history_fingerprint,current_baseline_fingerprint=st.baseline_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)
    prep.append((time.perf_counter()-t)*1000/20)
ys=list(xs); ys[-1]=replace(ys[-1],source_trust=.90); q2=replace(q,new_memories=tuple(ys)); st2=m.prepare_state(q2,b,e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
fb=len(m._canon(q2)); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 1200 Memory write candidates + 120 Write History entries; source/content/frequency/policy-impact/provenance/purpose anomaly scoring; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required},sort_keys=True))
