import json,time,statistics
from dataclasses import replace
import noepin_al_118_rollback_checkpoint_optimizer as m
b='BENCH-BIND'; e='BENCH-EPOCH'; plan=[]
for i in range(1200):
    risk=.42 if i%97==0 else (.08 if i%7 else .15)
    plan.append(m.PlanStep(f'S{i:04d}',1+(i%5),risk,1.5+(i%4)*.1,True,i%97!=0,500000+i*10,400000,30000+(i%9)*1000,1+(i%3)*.1,b,e))
p=m.CheckpointPolicy(.35,.25,.5,1,1,0.000002,20); q=m.RollbackRequest('BENCH-118',tuple(plan),p,b,e)
st=m.prepare_state(q,binding=b,state_epoch=e); integrity=m.validate_prepared_integrity(st)
full=[]; prep=[]; z=z2=None
for _ in range(5):
    t=time.perf_counter();
    for _j in range(5): z=m.evaluate(q)
    full.append((time.perf_counter()-t)*1000/5)
    t=time.perf_counter()
    for _j in range(20): z2=m.evaluate_prepared(st,integrity_validated=integrity,current_context_fingerprint=st.context_fingerprint,current_plan_fingerprint=st.plan_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_optimization_fingerprint=st.optimization_fingerprint)
    prep.append((time.perf_counter()-t)*1000/20)
changed=[replace(x,failure_probability=min(1,(x.failure_probability or .5)+.05),delta_bytes=x.delta_bytes+1000) for x in plan[:10]]
q2=replace(q,plan=tuple(changed)+tuple(plan[10:])); st2=m.prepare_state(q2,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
full_bytes=len(m._canon(q2)); delta_bytes=len(m._canon(d))
out={'condition':'Python stdlib; 1200 plan steps; DP expected-cost checkpoint optimization; full snapshot vs DCSR Shared Base/Delta reconstruction; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':z==z2,'full_bytes':full_bytes,'delta_bytes':delta_bytes,'delta_percent':delta_bytes/full_bytes*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required}
print(json.dumps(out,sort_keys=True))
