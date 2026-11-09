import json,time,statistics
from dataclasses import replace
import noepin_al_102_safe_astar_action_planner as m
p=m.default_policy(); b=p.binding; e=p.state_epoch
# 5000-edge safe linear/branching graph with one hard-constraint shortcut per 100 steps.
a=[]
N=2500
for i in range(N):
    a.append(m.ActionEdge(f'S{i:04d}',f'N{i}',f'N{i+1}',.01,.0005,True,'PASS','V1',f'F-S{i}',True,b,e))
    a.append(m.ActionEdge(f'B{i:04d}',f'N{i}',f'N{i+1}',.011,.0004,True,'PASS','V1',f'F-B{i}',True,b,e))
for i in range(0,N,100): a.append(m.ActionEdge(f'X{i:04d}',f'N{i}',f'N{min(N,i+100)}',.001,5.0,False,'HARD_CONSTRAINT','V1',f'F-X{i}',True,b,e))
a=tuple(a); q=m.PlanningRequest('BENCH','N0',f'N{N}',m.RiskClass.LOW,1000,10,True,b,e); p=replace(p,max_expansions=20000,low_risk_cap=10)
st=m.prepare_state(q,a,p,binding=b,state_epoch=e); integrity=m.validate_prepared_integrity(st)
full=[]; prep=[]
for _ in range(5):
    t=time.perf_counter(); z=None
    for _j in range(10): z=m.evaluate(q,a,p)
    full.append((time.perf_counter()-t)*1000/10)
    t=time.perf_counter(); z2=None
    for _j in range(10): z2=m.evaluate_prepared(st,integrity_validated=integrity,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_frontier_fingerprint=st.frontier_fingerprint,current_heuristic_fingerprint=st.heuristic_fingerprint)
    prep.append((time.perf_counter()-t)*1000/10)
ids={f'S{i:04d}' for i in range(10)}
a2=tuple(replace(x,risk_cost=x.risk_cost+.0001) if x.action_id in ids else x for x in a)
st2=m.prepare_state(q,a2,p,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
full_bytes=len(m._canon((q,a2,p))); delta_bytes=len(m._canon(d))
out={'condition':'Python stdlib; ~5000 safe A* action edges + hard-constraint shortcuts; 10 evaluations x 5 batches; prepared verified-result reuse','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':z==z2,'full_bytes':full_bytes,'delta_bytes':delta_bytes,'delta_percent':delta_bytes/full_bytes*100,'missing_records':len(sp.missing_or_changed_action_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required}
print(json.dumps(out,sort_keys=True))
