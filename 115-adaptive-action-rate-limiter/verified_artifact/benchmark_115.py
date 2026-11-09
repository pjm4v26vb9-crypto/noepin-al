import json,time,statistics
from dataclasses import replace
import noepin_al_115_adaptive_action_rate_limiter as m
b='BENCH-BIND'; e='BENCH-EPOCH'
ws=[]
for i in range(1200):
    risk=0.20+((i%13)-6)*0.002
    err=0.05+((i%7)-3)*0.001
    load=0.45+((i%11)-5)*0.002
    trust=0.88-((i%9)-4)*0.001
    ws.append(m.RateWindow(i,50.0,risk,err,load,trust,False,'V1',f'FP-{i:04d}',b,e))
p=m.RatePolicy(100.0,0.25,0.10,0.85,3,0.70,0.40,0.25,0.35,0.25,0.20,0.20,3,0.10,1.0,60.0)
q=m.RateLimitRequest('BENCH-115',tuple(ws),False,p,b,e)
st=m.prepare_state(q,binding=b,state_epoch=e); integrity=m.validate_prepared_integrity(st)
full=[]; prep=[]; z=z2=None
for _ in range(5):
    t0=time.perf_counter()
    for _j in range(5): z=m.evaluate(q)
    full.append((time.perf_counter()-t0)*1000/5)
    t0=time.perf_counter()
    for _j in range(20): z2=m.evaluate_prepared(st,integrity_validated=integrity,current_context_fingerprint=st.context_fingerprint,current_metrics_fingerprint=st.metrics_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_limiter_fingerprint=st.limiter_fingerprint)
    prep.append((time.perf_counter()-t0)*1000/20)
changed=[]
for w in ws[:10]: changed.append(replace(w,risk=w.risk+0.01,metric_fingerprint=w.metric_fingerprint+'X'))
q2=replace(q,windows=tuple(changed)+tuple(ws[10:])); st2=m.prepare_state(q2,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
full_bytes=len(m._canon(q2)); delta_bytes=len(m._canon(d))
out={'condition':'Python stdlib; 1200 rate windows; risk/error/load/trust adaptive limiting; deterministic backoff/recovery; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':z==z2,'full_bytes':full_bytes,'delta_bytes':delta_bytes,'delta_percent':delta_bytes/full_bytes*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required}
print(json.dumps(out,sort_keys=True))
