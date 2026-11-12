import json,time,statistics
from dataclasses import replace
import noepin_al_134_provenance_preserving_memory_merger as m
b='BENCH'; e='EPOCH-B'; prov=[]; claims=[]
for i in range(600):
    p=f'P-{i:04d}'; d=f'D-{i:04d}'; prov.append(m.ProvenanceLink(p,None,None,m.SourceKind.PRIMARY,b,e)); prov.append(m.ProvenanceLink(d,p,'SUMMARIZE',m.SourceKind.DERIVED,b,e))
    claims.append(m.MemoryClaim(f'M-{i:04d}-A',f'C-{i:04d}-A',f'key-{i%180:03d}',f'value-{i%7}',p,.80+(i%10)/100,i%149==0,m.RecordKind.MEMORY,'P',i,b,e))
    claims.append(m.MemoryClaim(f'M-{i:04d}-B',f'C-{i:04d}-B',f'key-{i%180:03d}',f'value-{i%7}',d,.75+(i%10)/100,i%149==0,m.RecordKind.MEMORY,'P',i+1,b,e))
q=m.MergeRequest('BENCH-134',tuple(claims),tuple(prov),m.default_policy(),b,e)
full=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(5): m.evaluate(q)
    full.append((time.perf_counter()-t)*1000/5)
st=m.prepare_state(q,b,e); prep=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(20): m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_claim_fingerprint=st.claim_fingerprint,current_provenance_fingerprint=st.provenance_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)
    prep.append((time.perf_counter()-t)*1000/20)
xs=list(claims); xs[-1]=replace(xs[-1],confidence=.71); q2=replace(q,claims=tuple(xs)); st2=m.prepare_state(q2,b,e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
fb=len(m._canon(q2)); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 1200 memory claims + 1200 provenance nodes; explicit semantic clustering + source/transform chain preservation + conflict retention; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required},sort_keys=True))
