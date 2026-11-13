import json,time,statistics
from dataclasses import replace
import noepin_al_158_policy_regression_detector as m
b='BENCH'; e='EPOCH-B'; old='policy-old'; new='policy-new'
corpus=tuple(m.RegressionCase(f'C-{i:05d}','SAFE' if i%3 else 'CRITICAL',m.Decision.DENY if i%3==0 else (m.Decision.HOLD if i%3==1 else m.Decision.ALLOW),m.Decision.DENY if i%3==0 else (m.Decision.HOLD if i%3==1 else m.Decision.ALLOW),m.Decision.DENY if i%3==0 else (m.Decision.HOLD if i%3==1 else m.Decision.ALLOW),'R','R',i%3==0,b,e) for i in range(3000))
v=m.VersionPair(old,new,b,e); p=m.RegressionPolicy(True,True,b,e); sh=m.ShadowCanaryState('SC',old,new,new,False,old,b,e); q=m.RegressionRequest('REQ',v,corpus,True,p,sh,b,e)
full=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate(q) for __ in range(5)]; full.append((time.perf_counter()-z)*1000/5)
st=m.prepare_state(q,b,e); prep=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate_prepared(st,integrity_validated=True,current_corpus_fingerprint=st.corpus_fingerprint,current_versions_fingerprint=st.versions_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_shadow_fingerprint=st.shadow_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint) for __ in range(20)]; prep.append((time.perf_counter()-z)*1000/20)
q2=replace(q,versions=replace(v,new_version='policy-new-2')); st2=m.prepare_state(q2,b,e); d=m.make_delta(st,st2); plan=m.plan_missing_only(st,st2); fb=len(m._canon(q2)); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 3000 fixed regression corpus cases with old/new/expected decisions; golden differential evaluation; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(plan.missing_or_changed_record_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend':plan.full_resend_required},sort_keys=True))
