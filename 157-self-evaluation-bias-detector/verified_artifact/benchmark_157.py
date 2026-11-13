import json,time,statistics
from dataclasses import replace
import noepin_al_157_self_evaluation_bias_detector as m
b='BENCH';e='EPOCH-B';t='CODE_REVIEW'
samples=tuple(m.ScoreSample(f'S-{i:05d}',t,.82 if i%2==0 else .72,.80 if i%2==0 else .70,.79 if i%2==0 else .71,b,e) for i in range(3000))
p=m.BiasPolicy(5,.12,.15,.06,.5,.25,.2,b,e); h=m.BiasHistory(t,.02,.02,.01,b,e); sh=m.ShadowCanaryState('SC','stable','canary','shadow',False,'stable',b,e); q=m.BiasRequest('REQ',t,samples,p,h,sh,'policy',b,e)
full=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate(q) for __ in range(5)]; full.append((time.perf_counter()-z)*1000/5)
st=m.prepare_state(q,b,e); prep=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate_prepared(st,integrity_validated=True,current_samples_fingerprint=st.samples_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_history_fingerprint=st.history_fingerprint,current_shadow_fingerprint=st.shadow_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint) for __ in range(20)]; prep.append((time.perf_counter()-z)*1000/20)
q2=replace(q,shadow=replace(sh,shadow_version='shadow-2')); st2=m.prepare_state(q2,b,e); d=m.make_delta(st,st2); plan=m.plan_missing_only(st,st2); fb=len(m._canon(q2)); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 3000 task-scoped Self/Independent/Outcome score samples; paired calibration/bias analysis; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(plan.missing_or_changed_record_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend':plan.full_resend_required},sort_keys=True))
