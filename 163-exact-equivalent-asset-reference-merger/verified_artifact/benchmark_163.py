import json,time,statistics
from dataclasses import replace
import noepin_al_163_exact_equivalent_asset_reference_merger as m
q=m.default_request(); b=q.binding; e=q.state_epoch
full=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate(q) for __ in range(3000)]; full.append((time.perf_counter()-z)*1000/3000)
st=m.prepare_state(q,b,e); prep=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate_prepared(st,integrity_validated=True,current_assets_fingerprint=st.assets_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint) for __ in range(3000)]; prep.append((time.perf_counter()-z)*1000/3000)
a=list(q.assets); a[2]=replace(a[2],state_hash='3'*64); q2=replace(q,assets=tuple(a)); st2=m.prepare_state(q2,b,e); d=m.make_delta(st,st2); plan=m.plan_missing_only(st,st2); fb=len(m._canon(tuple(q2 for _ in range(3000)))); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 3000 exact-equivalent asset-reference evaluations; full asset state batch vs one changed asset state-hash delta; 5 full x 3000 and 5 prepared x 3000','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(plan.missing_or_changed_record_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend':plan.full_resend_required},sort_keys=True))
