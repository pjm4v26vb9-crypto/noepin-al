import json,time,statistics
from dataclasses import replace
import noepin_al_146_cross_context_leakage_detector as m
b='BENCH'; e='EPOCH-B'
s=m.ContextRef('CTX-A','PROJECT','NS-A','OWNER-A',b,e); d=m.ContextRef('CTX-A','PROJECT','NS-A','OWNER-A',b,e)
bridges=tuple(m.BridgeEvidence(f'BR-{i:04d}','CTX-A',f'CTX-{i:04d}',(m.DataLabel.SENSITIVE,),True,True,b,e) for i in range(3000))
p=m.AccessPolicy('P-B',True,True,True,tuple(('CTX-A',f'CTX-{i:04d}') for i in range(3000)),bridges,b,e)
q=m.CrossingRequest('BENCH-146',s,d,(m.DataLabel.INTERNAL,),p,tuple(f'SRC-{i:04d}' for i in range(3000)),b,e)
full=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(5): m.evaluate(q)
    full.append((time.perf_counter()-t)*1000/5)
st=m.prepare_state(q,b,e); prep=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(20): m.evaluate_prepared(st,integrity_validated=True,current_source_fingerprint=st.source_fingerprint,current_destination_fingerprint=st.destination_fingerprint,current_labels_fingerprint=st.labels_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_provenance_fingerprint=st.provenance_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)
    prep.append((time.perf_counter()-t)*1000/20)
q2=replace(q,destination_context=replace(d,context_id='CTX-B',namespace='NS-B')); st2=m.prepare_state(q2,b,e); delta=m.make_delta(st,st2); plan=m.plan_missing_only(st,st2)
fb=len(m._canon(q2)); db=len(m._canon(delta))
print(json.dumps({'condition':'Python stdlib; 3000 bridge/pair policy records + 3000 provenance ids; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(plan.missing_or_changed_record_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend':plan.full_resend_required},sort_keys=True))
