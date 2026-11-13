import json,time,statistics
from dataclasses import replace
import noepin_al_153_safe_contextual_bandit_selector as m
b='BENCH'; e='EPOCH-B'
ctx=m.BanditContext('CTX-B',(1.0,.4,.2),False,b,e)
arms=tuple(m.CandidateArm(f'ARM-{i}',(.4+(i%5)*.1,.2,.1),.5+(i%10)*.02,(i%13)!=0,.3+(i%7)*.1,True,b,e) for i in range(32))
hist=tuple(m.RewardRecord(f'R{i}',f'ARM-{i%32}',(i%100)/100.0,(i%13)!=0,b,e) for i in range(3000))
s=m.SafetyConstraints('SAFE-B',.2,.7,.2,.05,.08,True,'ARM-1',b,e); sh=m.ShadowCanaryState('SH-B','stable','canary','shadow',False,b,e); q=m.BanditRequest('REQ-B',ctx,arms,hist,s,sh,b,e)
full=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate(q) for __ in range(5)]; full.append((time.perf_counter()-z)*1000/5)
st=m.prepare_state(q,b,e); prep=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_arms_fingerprint=st.arms_fingerprint,current_history_fingerprint=st.history_fingerprint,current_safety_fingerprint=st.safety_fingerprint,current_shadow_fingerprint=st.shadow_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint) for __ in range(20)]; prep.append((time.perf_counter()-z)*1000/20)
q2=replace(q,shadow=replace(sh,shadow_version='shadow-2')); st2=m.prepare_state(q2,b,e); d=m.make_delta(st,st2); p=m.plan_missing_only(st,st2); fb=len(m._canon(q2)); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 32 arms + 3000 reward records; safety filter + deterministic bounded exploration scoring; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(p.missing_or_changed_record_ids),'missing_metadata_bytes':p.metadata_bytes_required,'full_resend':p.full_resend_required},sort_keys=True))
