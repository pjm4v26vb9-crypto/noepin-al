import json,time,statistics
import noepin_al_179_decision_execution_handshake_protocol as m
q=m.default_request(); b=q.binding; e=q.state_epoch
full=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate_transition(q) for __ in range(1000)]; full.append((time.perf_counter()-z)*1000/1000)
st=m.prepare_state(q,b,e); prep=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate_prepared(st,integrity_validated=True,current_session_fingerprint=st.session_fingerprint,current_query_fingerprint=st.query_fingerprint,current_result_fingerprint=st.result_fingerprint) for __ in range(1000)]; prep.append((time.perf_counter()-z)*1000/1000)
new=m.default_bound_session(); old=m.build_session(new.request_id)
for x in new.bound_artifacts:
 if x.kind!=m.ArtifactKind.RECEIPT: old=m.bind_artifact(old,x.kind,x.fingerprint,final_verified=x.final_verified)
d=m.make_delta(old,new); plan=m.plan_missing_only(old,new)
fb=len(m._canon(tuple(q for _ in range(1000)))); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 1000 Decision-to-Execution Handshake transition validations per round; Request ID + ordered states + Artifact SHA-256 bindings + Final Verified flags + transition history; full request batch vs one missing Receipt binding; 5 full x 1000 and 5 prepared x 1000','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate_transition(q)==m.evaluate_prepared(st,integrity_validated=True,current_session_fingerprint=st.session_fingerprint,current_query_fingerprint=st.query_fingerprint,current_result_fingerprint=st.result_fingerprint),'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(plan.missing_or_changed_record_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'missing_record_ids':plan.missing_or_changed_record_ids,'full_resend':plan.full_resend_required},sort_keys=True))
