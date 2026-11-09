import json,time,statistics
from dataclasses import replace
import noepin_al_114_iterative_stability_monitor as m
b='BENCH-BIND'; e='BENCH-EPOCH'
samples=[]
for i in range(1200):
    v=max(0.0,500.0-i*0.3+((i%7)-3)*0.005)
    samples.append(m.IterationSample(i,v,v*0.4,f'STATE-{i:04d}',f'ACTION-{i%17:02d}','V1',f'FP-{i:04d}',b,e))
p=m.StabilityPolicy(5,1200,2000,0.01,0.02,0.001,6,0.1,8.0)
q=m.StabilityRequest('BENCH-114',tuple(samples),p,b,e)
st=m.prepare_state(q,binding=b,state_epoch=e); integrity=m.validate_prepared_integrity(st)
full=[]; prep=[]; z=z2=None
for _ in range(5):
    t0=time.perf_counter()
    for _j in range(5): z=m.evaluate(q)
    full.append((time.perf_counter()-t0)*1000/5)
    t0=time.perf_counter()
    for _j in range(20): z2=m.evaluate_prepared(st,integrity_validated=integrity,current_context_fingerprint=st.context_fingerprint,current_history_fingerprint=st.history_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_analysis_fingerprint=st.analysis_fingerprint)
    prep.append((time.perf_counter()-t0)*1000/20)
changed=[]
for s in samples[:10]: changed.append(replace(s,goal_distance=s.goal_distance+0.01,sample_fingerprint=s.sample_fingerprint+'X'))
q2=replace(q,samples=tuple(changed)+tuple(samples[10:])); st2=m.prepare_state(q2,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
full_bytes=len(m._canon(q2)); delta_bytes=len(m._canon(d))
out={'condition':'Python stdlib; 1200 iteration samples; goal-distance + error metrics; deterministic trend/CUSUM/periodicity classification; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':z==z2,'full_bytes':full_bytes,'delta_bytes':delta_bytes,'delta_percent':delta_bytes/full_bytes*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required}
print(json.dumps(out,sort_keys=True))
