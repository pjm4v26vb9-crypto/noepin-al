import json,time,statistics
from dataclasses import replace
import noepin_al_152_guardrailed_online_threshold_tuner as m
b='BENCH'; e='EPOCH-B'
outs=tuple(m.Outcome(f'O{i}',(i%100)/100.0,(i%3)==0,(i%97)==0,1.0,b,e) for i in range(3000))
t=m.ThresholdState('TH-B',.5,.3,.7,.02,'stable-b',b,e); c=m.CostMatrix('C-B',4,12,1,b,e); g=m.GuardrailBounds('G-B',100,.3,.01,True,b,e); s=m.ShadowState('S-B',True,.02,'stable-b','canary-b','shadow-b',b,e); q=m.ThresholdTuningRequest('REQ-B',outs,t,c,g,s,b,e)
full=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate(q) for __ in range(5)]; full.append((time.perf_counter()-z)*1000/5)
st=m.prepare_state(q,b,e); prep=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate_prepared(st,integrity_validated=True,current_outcome_fingerprint=st.outcome_fingerprint,current_threshold_fingerprint=st.threshold_fingerprint,current_cost_fingerprint=st.cost_fingerprint,current_guardrail_fingerprint=st.guardrail_fingerprint,current_shadow_fingerprint=st.shadow_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_outcome_result_fingerprint=st.outcome_result_fingerprint) for __ in range(20)]; prep.append((time.perf_counter()-z)*1000/20)
q2=replace(q,shadow=replace(s,distribution_shift=.03)); st2=m.prepare_state(q2,b,e); d=m.make_delta(st,st2); p=m.plan_missing_only(st,st2); fb=len(m._canon(q2)); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 3000 outcomes; bounded threshold search; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(p.missing_or_changed_record_ids),'missing_metadata_bytes':p.metadata_bytes_required,'full_resend':p.full_resend_required},sort_keys=True))
