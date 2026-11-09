import json,time,statistics
from dataclasses import replace
import noepin_al_120_resource_quota_controller as m
b='BENCH-BIND'; e='BENCH-EPOCH'; qs=[]; us=[]; fs=[]
for i in range(1200):
    hard=1000.0+(i%13)*100; qs.append(m.ResourceQuota(f'R{i:04d}',hard,.80+(i%4)*.03,i%5==0,b,e)); us.append(m.ResourceUsage(f'R{i:04d}',hard*(.2+(i%10)*.03),b,e)); fs.append(m.ResourceForecast(f'R{i:04d}',hard*.02,60.0,b,e))
p=m.QuotaPolicy(.50,.98,.97,.75); q=m.QuotaRequest('BENCH-120',tuple(qs),tuple(us),tuple(fs),.5,p,b,e)
st=m.prepare_state(q,binding=b,state_epoch=e); integrity=m.validate_prepared_integrity(st)
full=[]; prep=[]; z=z2=None
for _ in range(5):
    t=time.perf_counter()
    for _j in range(5): z=m.evaluate(q)
    full.append((time.perf_counter()-t)*1000/5)
    t=time.perf_counter()
    for _j in range(20): z2=m.evaluate_prepared(st,integrity_validated=integrity,current_context_fingerprint=st.context_fingerprint,current_quota_fingerprint=st.quota_fingerprint,current_usage_fingerprint=st.usage_fingerprint,current_forecast_fingerprint=st.forecast_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_decision_fingerprint=st.decision_fingerprint)
    prep.append((time.perf_counter()-t)*1000/20)
us2=[replace(x,current_usage=x.current_usage+1.0) if i<10 else x for i,x in enumerate(us)]; q2=replace(q,current_usage=tuple(us2)); st2=m.prepare_state(q2,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
full_bytes=len(m._canon(q2)); delta_bytes=len(m._canon(d))
out={'condition':'Python stdlib; 1200 quota resources; current usage + short-horizon forecast; hard/soft/unknown conservative control; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':z==z2,'full_bytes':full_bytes,'delta_bytes':delta_bytes,'delta_percent':delta_bytes/full_bytes*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required}
print(json.dumps(out,sort_keys=True))
