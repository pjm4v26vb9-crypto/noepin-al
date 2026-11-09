import json,time,statistics
from dataclasses import replace
import noepin_al_132_temporal_memory_consistency_graph as m
b='BENCH'; e='EPOCH-B'; ms=[]
# 1200 temporal memory records: 400 entities, three sequential versions each; newest explicitly supersedes previous.
for i in range(400):
    ent=f'ENTITY-{i:04d}'
    a=f'M-{i:04d}-A'; bb=f'M-{i:04d}-B'; c=f'M-{i:04d}-C'
    ms += [
      m.MemoryRecord(a,ent,'STATE','V1','SRC-A',10,20,'MAIN',(),m.RecordKind.MEMORY,.85,b,e),
      m.MemoryRecord(bb,ent,'STATE','V2','SRC-B',20,None,'MAIN',(a,),m.RecordKind.MEMORY,.88,b,e),
      m.MemoryRecord(c,ent,'NOTE','N','SRC-C',30,None,'MAIN',(),m.RecordKind.MEMORY,.80,b,e),
    ]
q=m.TemporalMemoryRequest('BENCH-132',tuple(ms),'ENTITY-0399','STATE',None,False,m.default_policy(),b,e)
full=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(5): m.evaluate(q)
    full.append((time.perf_counter()-t)*1000/5)
st=m.prepare_state(q,binding=b,state_epoch=e); prep=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(20): m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_memory_fingerprint=st.memory_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)
    prep.append((time.perf_counter()-t)*1000/20)
xs=list(ms); xs[-2]=replace(xs[-2],trust=.87); q2=replace(q,memories=tuple(xs)); st2=m.prepare_state(q2,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
full_bytes=len(m._canon(q2)); delta_bytes=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 1200 temporal memory records across 400 entities; temporal interval + supersede + provenance/current-candidate evaluation; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':full_bytes,'delta_bytes':delta_bytes,'delta_percent':delta_bytes/full_bytes*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required},sort_keys=True))
