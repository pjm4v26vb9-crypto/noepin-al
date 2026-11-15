import json,time,statistics
from dataclasses import replace
import noepin_al_184_quantum_transport_interference_simulator as m
q=m.default_request(); full=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate(q) for __ in range(1000)]; full.append((time.perf_counter()-z)*1000/1000)
st=m.prepare_state(q); prep=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate_prepared(st,integrity_validated=True,current_request_fingerprint=st.request_fingerprint,current_result_fingerprint=st.result_fingerprint,current_integrity_fingerprint=st.integrity_fingerprint,current_request=q) for __ in range(1000)]; prep.append((time.perf_counter()-z)*1000/1000)
old=replace(q,bell_fidelity=.85); d=m.make_delta(old,q); plan=m.plan_missing_only(old,q)
full_state=tuple(replace(q,seed=i) for i in range(1000)); fb=len(m._canon(full_state)); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib CPU mathematical simulator; 1000 complete model evaluations per round (remote-CZ toy state-vector + DD + route constraints) vs integrity-verified prepared result reuse with current request fingerprint check; 5 x 1000 each; condition-specific only','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q).simulation_fingerprint==m.evaluate_prepared(st,integrity_validated=True,current_request_fingerprint=st.request_fingerprint,current_result_fingerprint=st.result_fingerprint,current_integrity_fingerprint=st.integrity_fingerprint,current_request=q).simulation_fingerprint,'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(plan.missing_or_changed_record_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'missing_record_ids':plan.missing_or_changed_record_ids,'full_resend':plan.full_resend_required},sort_keys=True))
