import json,time,statistics
from dataclasses import replace
import noepin_al_110_resource_bounded_planner as m
p=m.default_policy(); b=p.binding; e=p.state_epoch
limits=(m.ResourceLimit('tokens',200000,10000,'tokens',1.0),m.ResourceLimit('api_calls',10000,500,'calls',1.0),m.ResourceLimit('cpu_seconds',10000,500,'s',1.0),m.ResourceLimit('memory_mb',500000,10000,'MB',.3),m.ResourceLimit('money_usd',1000,50,'USD',1.3),m.ResourceLimit('tool_calls',10000,500,'calls',1.0))
a=[]
N=1200
for i in range(N):
    a.append(m.ActionRecord(f'A{i:04d}',f'S{i:04d}',f'S{i+1:04d}',m._rc(tokens=10+(i%5),api_calls=1,cpu_seconds=.01,memory_mb=1,money_usd=.001,tool_calls=1),.1, i==600, True,True,'V1',f'FP{i:04d}',b,e))
a=tuple(a); q=m.PlanRequest('BENCH','S0000',f'S{N:04d}',m.RiskClass.LOW,True,b,e)
st=m.prepare_state(q,a,limits,p,binding=b,state_epoch=e); integrity=m.validate_prepared_integrity(st)
full=[]; prep=[]
for _ in range(5):
    t0=time.perf_counter(); z=None
    for _j in range(5): z=m.evaluate(q,a,limits,p)
    full.append((time.perf_counter()-t0)*1000/5)
    t0=time.perf_counter(); z2=None
    for _j in range(20): z2=m.evaluate_prepared(st,integrity_validated=integrity,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_budget_fingerprint=st.budget_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_frontier_fingerprint=st.frontier_fingerprint)
    prep.append((time.perf_counter()-t0)*1000/20)
a2=tuple(replace(x,resource_cost=m._rc(tokens=12,api_calls=1,cpu_seconds=.01,memory_mb=1,money_usd=.001,tool_calls=1),action_fingerprint=x.action_fingerprint+'X') if x.action_id in {f'A{i:04d}' for i in range(10)} else x for x in a)
st2=m.prepare_state(q,a2,limits,p,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
full_bytes=len(m._canon((q,a2,limits,p))); delta_bytes=len(m._canon(d))
out={'condition':'Python stdlib; 1200-action linear resource-constrained path; six resources; one mandatory safety action; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':z==z2,'full_bytes':full_bytes,'delta_bytes':delta_bytes,'delta_percent':delta_bytes/full_bytes*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required}
print(json.dumps(out,sort_keys=True))
