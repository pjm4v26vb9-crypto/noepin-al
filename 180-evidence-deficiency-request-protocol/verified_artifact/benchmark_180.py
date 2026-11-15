import json,time,statistics
import noepin_al_180_evidence_deficiency_request_protocol as m
q=m.default_response_request(); full=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate_response(q) for __ in range(1000)]; full.append((time.perf_counter()-z)*1000/1000)
st=m.prepare_state(q,q.binding,q.state_epoch); prep=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate_prepared(st,integrity_validated=True,current_deficiency_fingerprint=st.deficiency_fingerprint,current_query_fingerprint=st.query_fingerprint,current_result_fingerprint=st.result_fingerprint) for __ in range(1000)]; prep.append((time.perf_counter()-z)*1000/1000)
old=m.default_open_request(); new=m.default_closed_request(); d=m.make_delta(old,new); plan=m.plan_missing_only(old,new)
fb=len(m._canon(tuple(q for _ in range(1000)))); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 1000 Evidence Deficiency Response validations per round; Parent Decision ID + 3 explicit missing Claims + 3 allowed Source Types + accepted Evidence IDs + explicit close; full request batch vs one missing final Claim response and close-state delta; 5 full x 1000 and 5 prepared x 1000','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate_response(q)==m.evaluate_prepared(st,integrity_validated=True,current_deficiency_fingerprint=st.deficiency_fingerprint,current_query_fingerprint=st.query_fingerprint,current_result_fingerprint=st.result_fingerprint),'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(plan.missing_or_changed_record_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'missing_record_ids':plan.missing_or_changed_record_ids,'full_resend':plan.full_resend_required},sort_keys=True))
