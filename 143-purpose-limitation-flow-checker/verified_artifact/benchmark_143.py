import json,time,statistics
from dataclasses import replace
import noepin_al_143_purpose_limitation_flow_checker as m
b='BENCH'; e='EPOCH-B'; ds=[]
for i in range(3000):
    purposes=('care',) if i%5 else ('care:medication','audit')
    sens=m.Sensitivity.SENSITIVE if i%7==0 else m.Sensitivity.NON_SENSITIVE
    ds.append(m.DataItem(f'D-{i:04d}',purposes,sens,(f'SRC-{i:04d}',),b,e))
q=m.PurposeRequest('BENCH-143',tuple(ds),'care:medication','aggregate-care-summary',m.ConsentPolicy((),(),False,True),b,e)
full=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(3): m.evaluate(q)
    full.append((time.perf_counter()-t)*1000/3)
st=m.prepare_state(q,b,e); prep=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(20): m.evaluate_prepared(st,integrity_validated=True,current_data_fingerprint=st.data_fingerprint,current_purpose_fingerprint=st.purpose_fingerprint,current_consent_policy_fingerprint=st.consent_policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)
    prep.append((time.perf_counter()-t)*1000/20)
ys=list(ds); ys[-1]=replace(ys[-1],provenance_ids=(ys[-1].provenance_ids[0],'SRC-CHANGED')); q2=replace(q,data_items=tuple(ys)); st2=m.prepare_state(q2,b,e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
fb=len(m._canon(q2)); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 3000 Data items; purpose tags + sensitivity + consent/policy evidence; 3 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required},sort_keys=True))
