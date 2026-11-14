import json,time,statistics
from dataclasses import replace
import noepin_al_176_evidence_bundle_artifact as m
q=m.default_request(); b=q.binding; e=q.state_epoch
full=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate(q) for __ in range(1000)]; full.append((time.perf_counter()-z)*1000/1000)
st=m.prepare_state(q,b,e); prep=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate_prepared(st,integrity_validated=True,current_bundle_fingerprint=st.bundle_fingerprint,current_query_fingerprint=st.query_fingerprint,current_result_fingerprint=st.result_fingerprint,current_time=q.at_time) for __ in range(1000)]; prep.append((time.perf_counter()-z)*1000/1000)
x=replace(q.bundle.items[0],claim='Changed evidence claim'); b2=m.build_bundle((x,)+q.bundle.items[1:]); q2=replace(q,bundle=b2); st2=m.prepare_state(q2,b,e); d=m.make_delta(st,st2); plan=m.plan_missing_only(st,st2)
fb=len(m._canon(tuple(q for _ in range(1000)))); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 1000 Evidence Bundle freshness/integrity evaluations per round; 4 Evidence records with Source/Claim/Observed Time/Provenance SHA-256/Trust/Independence Group; full request batch vs one changed Evidence record; 5 full x 1000 and 5 prepared x 1000','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==m.evaluate_prepared(st,integrity_validated=True,current_bundle_fingerprint=st.bundle_fingerprint,current_query_fingerprint=st.query_fingerprint,current_result_fingerprint=st.result_fingerprint,current_time=q.at_time),'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(plan.missing_or_changed_record_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend':plan.full_resend_required},sort_keys=True))
