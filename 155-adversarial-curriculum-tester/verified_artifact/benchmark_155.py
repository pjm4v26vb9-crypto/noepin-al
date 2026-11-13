import json,time,statistics
from dataclasses import replace
import noepin_al_155_adversarial_curriculum_tester as m
b='BENCH';e='EPOCH-B'; cats=('PROMPT_INJECTION','GOAL_HIJACK','TAINTED_TOOL','MEMORY_POISON')
obs=[]
for i in range(3000):
 c=cats[i%4]; d=(i%5)+1; kind=('KNOWN','PARAPHRASE','MULTI_STEP')[i%3]; obs.append(m.AttackObservation(f'C{i}',c,d,kind,True,False,d==1,d==1,(c,kind),b,e))
cov=m.CoverageRequirement(cats,('KNOWN','PARAPHRASE','MULTI_STEP'),100,2,.95,b,e); pol=m.CurriculumPolicy('P',5,True,True,True,True,True,b,e); sh=m.ShadowCanaryState('S','stable','canary','shadow',False,b,e); q=m.CurriculumRequest('R','rules',tuple(obs),cov,pol,sh,(),b,e)
full=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate(q) for __ in range(5)]; full.append((time.perf_counter()-z)*1000/5)
st=m.prepare_state(q,b,e); prep=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate_prepared(st,integrity_validated=True,current_observations_fingerprint=st.observations_fingerprint,current_coverage_fingerprint=st.coverage_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_shadow_fingerprint=st.shadow_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint) for __ in range(20)]; prep.append((time.perf_counter()-z)*1000/20)
q2=replace(q,shadow=replace(sh,shadow_version='shadow-2')); st2=m.prepare_state(q2,b,e); d=m.make_delta(st,st2); p=m.plan_missing_only(st,st2); fb=len(m._canon(q2)); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 3000 adversarial observations; threat coverage + regression + critical failure curriculum analysis; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(p.missing_or_changed_record_ids),'missing_metadata_bytes':p.metadata_bytes_required,'full_resend':p.full_resend_required},sort_keys=True))
