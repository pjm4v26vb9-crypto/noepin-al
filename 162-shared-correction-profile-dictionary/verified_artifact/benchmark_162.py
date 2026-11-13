import json,time,statistics
from dataclasses import replace
import noepin_al_162_shared_correction_profile_dictionary as m
q=m.default_request(); b=q.binding; e=q.state_epoch
full=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate(q) for __ in range(3000)]; full.append((time.perf_counter()-z)*1000/3000)
st=m.prepare_state(q,b,e); prep=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate_prepared(st,integrity_validated=True,current_targets_fingerprint=st.targets_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint) for __ in range(3000)]; prep.append((time.perf_counter()-z)*1000/3000)
t=list(q.targets); t[2]=replace(t[2],usage_tag='ASSET_CORRECTION_V2'); q2=replace(q,targets=tuple(t)); st2=m.prepare_state(q2,b,e); d=m.make_delta(st,st2); plan=m.plan_missing_only(st,st2); fb=len(m._canon(tuple(q2 for _ in range(3000)))); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 3000 shared-profile dictionary evaluations; full target/profile state batch vs one changed target usage-tag delta; 5 full x 3000 and 5 prepared x 3000','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(plan.missing_or_changed_record_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend':plan.full_resend_required},sort_keys=True))
