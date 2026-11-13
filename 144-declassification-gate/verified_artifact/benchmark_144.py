import json,time,statistics
from dataclasses import replace
import noepin_al_144_declassification_gate as m
b='BENCH'; e='EPOCH-B'
p=m.SanitizationProof('P',True,'SAN',0.10,m.Classification.INTERNAL,tuple(f'SRC-{i:04d}' for i in range(3000)),b,e)
a=m.ApproverEvidence('A',True,(m.Classification.CONFIDENTIAL,m.Classification.RESTRICTED,m.Classification.SECRET),(m.Classification.PUBLIC,m.Classification.INTERNAL,m.Classification.CONFIDENTIAL),'AB',b,e)
q=m.DeclassificationRequest('BENCH-144','DATA-BENCH',m.Classification.CONFIDENTIAL,m.Classification.INTERNAL,0.08,p,a,b,e,tuple(f'SRC-{i:04d}' for i in range(3000)))
full=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(5): m.evaluate(q)
    full.append((time.perf_counter()-t)*1000/5)
st=m.prepare_state(q,b,e); prep=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(20): m.evaluate_prepared(st,integrity_validated=True,current_request_fingerprint=st.request_fingerprint,current_proof_fingerprint=st.proof_fingerprint,current_approver_fingerprint=st.approver_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)
    prep.append((time.perf_counter()-t)*1000/20)
q2=replace(q,provenance_ids=q.provenance_ids+('SRC-CHANGED',)); st2=m.prepare_state(q2,b,e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
fb=len(m._canon(q2)); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 3000 provenance records; classification lattice + sanitizer verifier + approval binding; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required},sort_keys=True))
