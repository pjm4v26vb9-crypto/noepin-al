import json,time,statistics
from dataclasses import replace
import noepin_al_156_feedback_reliability_filter as m
b='BENCH';e='EPOCH-B'
f=m.Feedback('FB','SRC',.8,False,False,'benchmark',b,e)
s=m.SourceProfile('SRC','TRUSTED_USER',True,True,.76,.05,True,b,e)
ev=m.OutcomeEvidence('EV',True,True,.9,tuple(f'OBS-{i:05d}-'+'X'*160 for i in range(3000)),b,e)
cx=m.FeedbackContext(30,3600,.05,.4,.85,b,e); sh=m.ShadowCanaryState('SC','stable','canary','shadow',False,'stable',b,e); q=m.FeedbackRequest('REQ',f,s,ev,cx,sh,'policy',b,e)
full=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate(q) for __ in range(5)]; full.append((time.perf_counter()-z)*1000/5)
st=m.prepare_state(q,b,e); prep=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate_prepared(st,integrity_validated=True,current_feedback_fingerprint=st.feedback_fingerprint,current_source_fingerprint=st.source_fingerprint,current_evidence_fingerprint=st.evidence_fingerprint,current_context_fingerprint=st.context_fingerprint,current_shadow_fingerprint=st.shadow_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint) for __ in range(20)]; prep.append((time.perf_counter()-z)*1000/20)
q2=replace(q,shadow=replace(sh,shadow_version='shadow-2')); st2=m.prepare_state(q2,b,e); d=m.make_delta(st,st2); p=m.plan_missing_only(st,st2); fb=len(m._canon(q2)); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; feedback evidence with 3000 corroboration IDs; reliability/conflict/delay/policy-weakening filter; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(p.missing_or_changed_record_ids),'missing_metadata_bytes':p.metadata_bytes_required,'full_resend':p.full_resend_required},sort_keys=True))
