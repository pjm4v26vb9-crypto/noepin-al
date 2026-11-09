import json,time,statistics
from dataclasses import replace
import noepin_al_109_deadline_aware_safe_scheduler as m
p=m.default_policy(); b=p.binding; e=p.state_epoch
# 5000 tasks in a deterministic DAG: 50 chains x 100 tasks, all mandatory work preserved.
tasks=[]
for c in range(50):
    prev=None
    for j in range(100):
        i=c*100+j; tid=f'T{i:05d}'; deps=() if prev is None else (prev,)
        tasks.append(m.TaskRecord(tid,.01+(i%5)*.001,deps,.1+(i%7)*.02,j%20==0,j%20==0,j%100==0,True,True,True,'V1',f'FP{i:05d}',b,e)); prev=tid
tasks=tuple(tasks); total=sum(x.duration_estimate for x in tasks); q=m.ScheduleRequest('BENCH',0,total*1.4,m.RiskClass.LOW,(),True,b,e)
st=m.prepare_state(q,tasks,p,binding=b,state_epoch=e); integrity=m.validate_prepared_integrity(st)
full=[]; prep=[]
for _ in range(5):
    t0=time.perf_counter(); z=None
    for _j in range(10): z=m.evaluate(q,tasks,p)
    full.append((time.perf_counter()-t0)*1000/10)
    t0=time.perf_counter(); z2=None
    for _j in range(10): z2=m.evaluate_prepared(st,integrity_validated=integrity,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_frontier_fingerprint=st.frontier_fingerprint,current_schedule_fingerprint=st.schedule_fingerprint)
    prep.append((time.perf_counter()-t0)*1000/10)
ids={x.task_id for x in tasks[:10]}; t2=tuple(replace(x,duration_estimate=x.duration_estimate+.0001) if x.task_id in ids else x for x in tasks)
st2=m.prepare_state(q,t2,p,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
full_bytes=len(m._canon((q,t2,p))); delta_bytes=len(m._canon(d))
out={'condition':'Python stdlib; 5000 tasks in 50 dependency chains with mandatory safety verification tasks; 10 evaluations x 5 batches; prepared verified-result reuse','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':z==z2,'full_bytes':full_bytes,'delta_bytes':delta_bytes,'delta_percent':delta_bytes/full_bytes*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required}
print(json.dumps(out,sort_keys=True))
