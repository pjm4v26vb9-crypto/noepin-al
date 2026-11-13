import json,time,statistics
from dataclasses import replace
import noepin_al_141_purpose_completion_forgetting_engine as m
b='BENCH'; e='EPOCH-B'; xs=[]
classes=(m.RetentionClass.DELETE_AFTER_PURPOSE,m.RetentionClass.ARCHIVE_AFTER_PURPOSE,m.RetentionClass.RETAIN_REQUIRED,m.RetentionClass.ANONYMIZE_AFTER_PURPOSE)
for i in range(2500):
    kind=m.MemoryKind.CREDENTIAL if i%97==0 else (m.MemoryKind.PERSONAL if i%11==0 else m.MemoryKind.GENERAL)
    rc=classes[i%len(classes)]
    xs.append(m.MemoryRecord(f'M-{i:04d}',('PURPOSE-A',),kind,rc,(f'TRACE-{i:04d}',),i%173==0,i%127==0,i%113==0,'',b,e))
q=m.ForgetRequest('BENCH-141',('PURPOSE-A',),tuple(xs),m.default_policy(),b,e)
full=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(5): m.evaluate(q)
    full.append((time.perf_counter()-t)*1000/5)
st=m.prepare_state(q,b,e); prep=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(20): m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_memories_fingerprint=st.memories_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)
    prep.append((time.perf_counter()-t)*1000/20)
ys=list(xs); ys[-1]=replace(ys[-1],retention_reason='changed'); q2=replace(q,memories=tuple(ys)); st2=m.prepare_state(q2,b,e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
fb=len(m._canon(q2)); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 2500 Memory records; completed-purpose dependency reverse lookup with retention/legal-hold/audit/provenance planning; candidate-only destructive actions; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required},sort_keys=True))
