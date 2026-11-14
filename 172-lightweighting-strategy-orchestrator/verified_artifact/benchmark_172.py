import json,time,statistics
from dataclasses import replace
import noepin_al_172_lightweighting_strategy_orchestrator as m
q=m.default_request(); b=q.binding; e=q.state_epoch
full=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate(q) for __ in range(1000)]; full.append((time.perf_counter()-z)*1000/1000)
st=m.prepare_state(q,b,e); prep=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate_prepared(st,integrity_validated=True,current_records_fingerprint=st.records_fingerprint,current_config_fingerprint=st.config_fingerprint,current_result_fingerprint=st.result_fingerprint) for __ in range(1000)]; prep.append((time.perf_counter()-z)*1000/1000)
rs=list(q.records); rs[5]=replace(rs[5],importance=.61); q2=replace(q,records=tuple(rs)); st2=m.prepare_state(q2,b,e); d=m.make_delta(st,st2); plan=m.plan_missing_only(st,st2)
fb=len(m._canon(tuple(q for _ in range(1000)))); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 1000 lightweighting strategy orchestration evaluations per round; 10 records; Exact Reuse / Shared Profile / Delta / Quantization+Residual / Lossless / Original candidates; Critical-high-sensitivity protection + size-budget recheck; full request batch vs one changed record; 5 full x 1000 and 5 prepared x 1000','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(plan.missing_or_changed_record_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend':plan.full_resend_required},sort_keys=True))
