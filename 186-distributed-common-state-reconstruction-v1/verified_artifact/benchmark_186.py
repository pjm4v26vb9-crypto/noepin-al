import json,time,statistics
import noepin_al_186_distributed_common_state_reconstruction_v1 as m
q=m.default_request(); full=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate(q) for __ in range(1000)]; full.append((time.perf_counter()-z)*1000/1000)
st=m.prepare_state(q); prep=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate_prepared(st,integrity_validated=True,current_request_fingerprint=st.request_fingerprint,current_result_fingerprint=st.result_fingerprint,current_integrity_fingerprint=st.integrity_fingerprint,current_request=q) for __ in range(1000)]; prep.append((time.perf_counter()-z)*1000/1000)
r=m.evaluate(q); plan=m.plan_missing_only(q)
print(json.dumps({'condition':'Python stdlib DCSR manifest negotiation; 1000 full evaluations per round vs integrity-bound Prepared State reuse; 5 x 1000 each; modeled transport metrics are deterministic estimates, not physical WAN measurements','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q).final_candidate_fingerprint==m.evaluate_prepared(st,integrity_validated=True,current_request_fingerprint=st.request_fingerprint,current_result_fingerprint=st.result_fingerprint,current_integrity_fingerprint=st.integrity_fingerprint,current_request=q).final_candidate_fingerprint,'full_bytes':r.full_payload_bytes,'delta_bytes':r.delta_payload_bytes,'delta_percent':(r.delta_payload_bytes/r.full_payload_bytes*100 if r.full_payload_bytes else 0),'missing_records':len(plan.missing_or_changed_record_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'missing_record_ids':plan.missing_or_changed_record_ids,'full_resend':plan.full_resend_required,'estimated_full_ms':r.estimated_full_ms,'estimated_dcsr_ms':r.estimated_dcsr_ms},sort_keys=True))
