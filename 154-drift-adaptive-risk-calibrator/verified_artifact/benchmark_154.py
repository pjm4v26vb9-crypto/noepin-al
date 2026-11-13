import json,time,statistics
from dataclasses import replace
import noepin_al_154_drift_adaptive_risk_calibrator as m
b='BENCH'; e='EPOCH-B'
rows=[]
for i in range(3000):
 risky=(i%5)<2; base=(.2,.5,.8); jitter=((i%7)-3)*.002
 rows.append(m.FeatureOutcome(f'R{i}',tuple(x+jitter for x in base),(.78 if risky else .18),risky,True,1,b,e))
base=m.BaselineDistribution('BASE-B',(.2,.5,.8),(.1,.1,.1),.18,.4,'stable',b,e)
pol=m.DriftPolicy('POL-B',50,.25,.60,.30,.25,.15,.10,True,b,e)
sh=m.ShadowCanaryState('SH-B',False,False,False,'stable','canary','shadow',b,e)
q=m.DriftCalibrationRequest('REQ-B',tuple(rows),base,pol,sh,True,b,e)
full=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate(q) for __ in range(5)]; full.append((time.perf_counter()-z)*1000/5)
st=m.prepare_state(q,b,e); prep=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate_prepared(st,integrity_validated=True,current_stream_fingerprint=st.stream_fingerprint,current_baseline_fingerprint=st.baseline_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_shadow_fingerprint=st.shadow_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint) for __ in range(20)]; prep.append((time.perf_counter()-z)*1000/20)
q2=replace(q,shadow=replace(sh,shadow_version='shadow-2')); st2=m.prepare_state(q2,b,e); d=m.make_delta(st,st2); p=m.plan_missing_only(st,st2); fb=len(m._canon(q2)); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 3000 feature/outcome/risk records; feature drift + label shift + calibration monitor; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(p.missing_or_changed_record_ids),'missing_metadata_bytes':p.metadata_bytes_required,'full_resend':p.full_resend_required},sort_keys=True))
