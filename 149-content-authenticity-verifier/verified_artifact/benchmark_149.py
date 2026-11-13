import json,time,statistics
from dataclasses import replace
import noepin_al_149_content_authenticity_verifier as m
b='BENCH'; e='EPOCH-B'; text='x'*600000; digest=m._content_sha(text)
c=m.ContentArtifact('BENCH-C',text,m.ContentClass.POLICY,True,b,e)
s=m.SignatureEvidence('BENCH-S',True,True,'NOEPIN',digest,False,'OFFLINE_VERIFIED',b,e)
p=m.ProvenanceMetadata('NOEPIN',tuple(f'P{i:04d}' for i in range(3000)),True,'registry://canonical',('registry://canonical',),b,e)
x=m.PublisherExpectation('NOEPIN',digest,b,e); q=m.AuthenticityRequest('BENCH-149',c,s,p,x,b,e)
full=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(5): m.evaluate(q)
    full.append((time.perf_counter()-t)*1000/5)
st=m.prepare_state(q,b,e); prep=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(20): m.evaluate_prepared(st,integrity_validated=True,current_content_fingerprint=st.content_fingerprint,current_signature_fingerprint=st.signature_fingerprint,current_provenance_fingerprint=st.provenance_fingerprint,current_expectation_fingerprint=st.expectation_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)
    prep.append((time.perf_counter()-t)*1000/20)
p2=replace(p,acquisition_path='registry://mirror',registered_acquisition_paths=('registry://canonical','registry://mirror')); q2=replace(q,provenance=p2); st2=m.prepare_state(q2,b,e); delta=m.make_delta(st,st2); plan=m.plan_missing_only(st,st2)
fb=len(m._canon(q2)); db=len(m._canon(delta))
print(json.dumps({'condition':'Python stdlib; 600kB content + 3000 provenance chain entries; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(plan.missing_or_changed_record_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend':plan.full_resend_required},sort_keys=True))
