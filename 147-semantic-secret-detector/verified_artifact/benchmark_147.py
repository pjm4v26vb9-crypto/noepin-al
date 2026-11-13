import json,time,statistics
from dataclasses import replace
import noepin_al_147_semantic_secret_detector as m
b='BENCH'; e='EPOCH-B'
fs=tuple(m.ContentFragment(f'F{i:04d}',('ordinary data '+str(i)) if i<2999 else 'api key = KEY_ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'LOG',(f'S{i:04d}',),b,e) for i in range(3000))
ps=(m.KnownSecretPattern('P-B',r'\bKEY_[A-Z]{20,}\b',m.SecretClass.API_KEY,True,b,e),)
u=m.UsageSemantics(True,True,False,True,('external','logs'),b,e)
q=m.SecretRequest('BENCH-147',fs,'external log publication review',ps,u,True,b,e)
full=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(5): m.evaluate(q)
    full.append((time.perf_counter()-t)*1000/5)
st=m.prepare_state(q,b,e); prep=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(20): m.evaluate_prepared(st,integrity_validated=True,current_fragments_fingerprint=st.fragments_fingerprint,current_context_fingerprint=st.context_fingerprint,current_patterns_fingerprint=st.patterns_fingerprint,current_usage_fingerprint=st.usage_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)
    prep.append((time.perf_counter()-t)*1000/20)
q2=replace(q,context=q.context+' changed'); st2=m.prepare_state(q2,b,e); delta=m.make_delta(st,st2); plan=m.plan_missing_only(st,st2)
fb=len(m._canon(q2)); db=len(m._canon(delta))
print(json.dumps({'condition':'Python stdlib; 3000 content fragments; known-pattern + semantic scan; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(plan.missing_or_changed_record_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend':plan.full_resend_required},sort_keys=True))
