import json,time,statistics
from dataclasses import replace
import noepin_al_145_aggregation_sensitivity_detector as m
b='BENCH'; e='EPOCH-B'
fs=[]
for i in range(3000):
    attr=('a',str(i)) if i%2==0 else ('b',str(i))
    fs.append(m.DataFragment(f'F-{i:04d}','ENTITY-B',(attr,),(('person_id','P-B'),),m.Sensitivity.PUBLIC,(f'SRC-{i:04d}',),b,e))
r=m.InferenceRule('R-B',('a','b'),'aggregate_secret',m.Sensitivity.CONFIDENTIAL,'person_id',True,b,e)
a=m.AudienceContext('AUD-B',False,m.Sensitivity.CONFIDENTIAL,True,b,e)
q=m.AggregationRequest('BENCH-145',tuple(fs),(r,),a,True,b,e)
full=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(5): m.evaluate(q)
    full.append((time.perf_counter()-t)*1000/5)
st=m.prepare_state(q,b,e); prep=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(20): m.evaluate_prepared(st,integrity_validated=True,current_fragments_fingerprint=st.fragments_fingerprint,current_rules_fingerprint=st.rules_fingerprint,current_audience_fingerprint=st.audience_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)
    prep.append((time.perf_counter()-t)*1000/20)
fs2=list(fs); fs2[-1]=replace(fs2[-1],attributes=(('b','CHANGED'),)); q2=replace(q,fragments=tuple(fs2)); st2=m.prepare_state(q2,b,e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
fb=len(m._canon(q2)); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 3000 fragments; knowledge-graph join + inference rules + sensitivity lattice; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required},sort_keys=True))
