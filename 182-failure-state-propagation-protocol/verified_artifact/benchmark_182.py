import json,time,statistics
import noepin_al_182_failure_state_propagation_protocol as m
q=m.default_request(); full=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate(q) for __ in range(1000)]; full.append((time.perf_counter()-z)*1000/1000)
st=m.prepare_state(q,q.binding,q.state_epoch); prep=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate_prepared(st,integrity_validated=True,current_request_fingerprint=st.request_fingerprint,current_result_fingerprint=st.result_fingerprint,current_binding=q.binding,current_state_epoch=q.state_epoch,current_current_state=q.current_state,current_incoming_state=q.incoming_state,current_proposed_state=q.proposed_state,current_recovery_authorization=q.recovery_authorization) for __ in range(1000)]; prep.append((time.perf_counter()-z)*1000/1000)
d=m.make_delta(q.current_state,q.incoming_state); plan=m.plan_missing_only(q.current_state,q.incoming_state)
fb=len(m._canon(tuple(q for _ in range(1000)))); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 1000 Failure-State Propagation evaluations per round; Current/Incoming/Proposed State + Recovery Authorization binding; full request batch vs one changed Failure State segment; 5 full x 1000 and 5 prepared x 1000; prepared path re-evaluates current Authority-side state and Recovery Authorization','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==m.evaluate_prepared(st,integrity_validated=True,current_request_fingerprint=st.request_fingerprint,current_result_fingerprint=st.result_fingerprint,current_binding=q.binding,current_state_epoch=q.state_epoch,current_current_state=q.current_state,current_incoming_state=q.incoming_state,current_proposed_state=q.proposed_state,current_recovery_authorization=q.recovery_authorization),'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(plan.missing_or_changed_record_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'missing_record_ids':plan.missing_or_changed_record_ids,'full_resend':plan.full_resend_required},sort_keys=True))
