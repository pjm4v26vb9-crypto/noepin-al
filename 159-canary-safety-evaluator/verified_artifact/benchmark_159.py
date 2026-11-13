import json,time,statistics
from dataclasses import replace
import noepin_al_159_canary_safety_evaluator as m
b='BENCH'; e='EPOCH-B'; stable='stable'; canary='canary'
versions=m.VersionState(stable,canary,stable,b,e); traffic=m.TrafficSlice('SLICE',0.05,True,True,5000,1000,b,e)
safety=tuple(m.SafetyMetric(f'S-{i:05d}',0.001+(i%7)*0.00001,0.001+(i%7)*0.00001,False,0.0001,b,e) for i in range(3000))
utility=tuple(m.UtilityMetric(f'U-{i:05d}',0.8,0.82,0.01,b,e) for i in range(3000))
policy=m.CanaryPolicy(0.10,True,True,True,b,e); q=m.CanaryRequest('REQ',versions,traffic,safety,utility,(),policy,b,e)
full=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate(q) for __ in range(5)]; full.append((time.perf_counter()-z)*1000/5)
st=m.prepare_state(q,b,e); prep=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate_prepared(st,integrity_validated=True,current_versions_fingerprint=st.versions_fingerprint,current_traffic_fingerprint=st.traffic_fingerprint,current_safety_fingerprint=st.safety_fingerprint,current_utility_fingerprint=st.utility_fingerprint,current_incidents_fingerprint=st.incidents_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint) for __ in range(20)]; prep.append((time.perf_counter()-z)*1000/20)
q2=replace(q,traffic=replace(traffic,observed_samples=5001)); st2=m.prepare_state(q2,b,e); d=m.make_delta(st,st2); plan=m.plan_missing_only(st,st2); fb=len(m._canon(q2)); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 3000 safety metrics + 3000 utility metrics; stable/canary bounded traffic evidence; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(plan.missing_or_changed_record_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend':plan.full_resend_required},sort_keys=True))
