import json,time,statistics
import noepin_al_183_schema_version_negotiation_protocol as m
q=m.default_request(); full=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate(q) for __ in range(1000)]; full.append((time.perf_counter()-z)*1000/1000)
st=m.prepare_state(q); prep=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate_prepared(st,integrity_validated=True,current_request_fingerprint=st.request_fingerprint,current_result_fingerprint=st.result_fingerprint,current_local_manifest_fingerprint=st.local_manifest_fingerprint,current_remote_manifest_fingerprint=st.remote_manifest_fingerprint,current_requirement_fingerprint=st.requirement_fingerprint,current_request=q) for __ in range(1000)]; prep.append((time.perf_counter()-z)*1000/1000)
old=m.build_manifest('LOCAL-AL',('1.0','1.1'),'SCHEMA-A','FP-A','EPOCH-0'); new=q.local
d=m.make_delta(old,new); plan=m.plan_missing_only(old,new)
fb=len(m._canon(tuple(q.local for _ in range(1000)))); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 1000 Schema-Version negotiations per round; explicit Local/Remote manifests + Compatibility Requirement; full local-manifest batch vs one supported-version delta; 5 full x 1000 and 5 prepared x 1000; prepared path revalidates integrity and current Authority-side manifests/requirement','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==m.evaluate_prepared(st,integrity_validated=True,current_request_fingerprint=st.request_fingerprint,current_result_fingerprint=st.result_fingerprint,current_local_manifest_fingerprint=st.local_manifest_fingerprint,current_remote_manifest_fingerprint=st.remote_manifest_fingerprint,current_requirement_fingerprint=st.requirement_fingerprint,current_request=q),'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(plan.missing_or_changed_record_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'missing_record_ids':plan.missing_or_changed_record_ids,'full_resend':plan.full_resend_required},sort_keys=True))
