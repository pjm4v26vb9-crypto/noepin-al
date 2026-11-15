import json,time,statistics
import noepin_al_181_human_approval_challenge_response_protocol as m
q=m.default_verification_request(); c=q.challenge; full=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate_response(q) for __ in range(1000)]; full.append((time.perf_counter()-z)*1000/1000)
st=m.prepare_state(q,q.binding,q.state_epoch); prep=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate_prepared(st,integrity_validated=True,current_challenge_state_fingerprint=st.challenge_state_fingerprint,current_response_fingerprint=st.response_fingerprint,current_query_fingerprint=st.query_fingerprint,current_result_fingerprint=st.result_fingerprint,current_action_digest=c.action_digest,current_risk_digest=c.risk_digest,current_nonce=c.nonce,current_time=q.current_time) for __ in range(1000)]; prep.append((time.perf_counter()-z)*1000/1000)
d=m.make_delta(None,q.response); plan=m.plan_missing_only(None,q.response)
fb=len(m._canon(tuple(q for _ in range(1000)))); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 1000 Human Approval Challenge-Response verifications per round; Request/Action/Risk/Scope/Nonce/Expiry + bound APPROVE response; full request batch vs one missing approval response record; 5 full x 1000 and 5 prepared x 1000; prepared path still rechecks current action/risk/nonce/time','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate_response(q)==m.evaluate_prepared(st,integrity_validated=True,current_challenge_state_fingerprint=st.challenge_state_fingerprint,current_response_fingerprint=st.response_fingerprint,current_query_fingerprint=st.query_fingerprint,current_result_fingerprint=st.result_fingerprint,current_action_digest=c.action_digest,current_risk_digest=c.risk_digest,current_nonce=c.nonce,current_time=q.current_time),'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(plan.missing_or_changed_record_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'missing_record_ids':plan.missing_or_changed_record_ids,'full_resend':plan.full_resend_required},sort_keys=True))
