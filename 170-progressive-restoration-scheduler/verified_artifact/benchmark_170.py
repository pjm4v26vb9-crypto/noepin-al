import json,time,statistics
from dataclasses import replace
import noepin_al_170_progressive_restoration_scheduler as m
q=m.default_request(); b=q.binding; e=q.state_epoch
full=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate(q) for __ in range(500)]; full.append((time.perf_counter()-z)*1000/500)
st=m.prepare_state(q,b,e); prep=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate_prepared(st,integrity_validated=True,current_base_fingerprint=st.base_fingerprint,current_detail_fingerprint=st.detail_fingerprint,current_config_fingerprint=st.config_fingerprint,current_result_fingerprint=st.result_fingerprint) for __ in range(500)]; prep.append((time.perf_counter()-z)*1000/500)
cs=list(q.detail_chunks); cs[4]=replace(cs[4],importance=0.91); q2=replace(q,detail_chunks=tuple(cs)); st2=m.prepare_state(q2,b,e); d=m.make_delta(st,st2); plan=m.plan_missing_only(st,st2)
fb=len(m._canon(tuple(q for _ in range(1000)))); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 500 progressive restoration schedule evaluations per round; 1 Base + 10 Detail chunks; Critical/required reservation + P0-P4 priority + byte/latency budgets; full request batch vs one changed Detail record; 5 full x 500 and 5 prepared x 500','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(plan.missing_or_changed_record_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend':plan.full_resend_required},sort_keys=True))
