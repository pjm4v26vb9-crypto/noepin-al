import json,time,statistics
from dataclasses import replace
import noepin_al_174_intent_contract_artifact as m
q=m.default_request(); b=q.binding; e=q.state_epoch
full=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate(q) for __ in range(1000)]; full.append((time.perf_counter()-z)*1000/1000)
st=m.prepare_state(q,b,e); prep=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate_prepared(st,integrity_validated=True,current_contract_fingerprint=st.contract_fingerprint,current_query_fingerprint=st.query_fingerprint,current_result_fingerprint=st.result_fingerprint,current_time=q.at_time) for __ in range(1000)]; prep.append((time.perf_counter()-z)*1000/1000)
q2=replace(q,target='asset:profile-A'); st2=m.prepare_state(q2,b,e); d=m.make_delta(st,st2); plan=m.plan_missing_only(st,st2)
fb=len(m._canon(tuple(q for _ in range(1000)))); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 1000 Intent Contract Action/Target/Time checks per round; normalized allowed/denied actions + scope targets + consent ID + timezone-aware expiry + SHA-256 Contract fingerprint; full request batch vs one changed authorization query; 5 full x 1000 and 5 prepared x 1000','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==m.evaluate_prepared(st,integrity_validated=True,current_contract_fingerprint=st.contract_fingerprint,current_query_fingerprint=st.query_fingerprint,current_result_fingerprint=st.result_fingerprint,current_time=q.at_time),'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(plan.missing_or_changed_record_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend':plan.full_resend_required},sort_keys=True))
