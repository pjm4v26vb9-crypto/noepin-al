import json,time,statistics
from dataclasses import replace
import noepin_al_107_safe_alternative_path_enumerator as m
p=m.default_policy(); b=p.binding; e=p.state_epoch
q=replace(m.default_request(),k=5,max_hops=4,max_total_cost=20,max_total_time=20,max_total_risk=4)
edges=[]
# ~5000 edges: START -> 1250 mids -> 3 second-layer choices -> GOAL, plus unsafe decoys.
for i in range(1250):
    mid=f'M{i:04d}'; edges.append(m.GraphEdge(f'S{i:04d}','START',mid,1+(i%7)/100,1,.05+(i%5)/100,.9,True,True,'V1',f'FS{i}',True,b,e))
    for j in range(3):
        n=f'N{i:04d}_{j}'; edges.append(m.GraphEdge(f'M{i:04d}_{j}',mid,n,.5+j/10,.5,.03+j/100,.85+j*.03,True,True,'V1',f'FM{i}_{j}',True,b,e))
        # only j=0 gets goal for most to constrain total path count; others are safe dead-ends
        if j==0: edges.append(m.GraphEdge(f'G{i:04d}',n,'GOAL',.8,.8,.03,.9,True,True,'V1',f'FG{i}',True,b,e))
# cap to roughly 5000 by construction: 1250 + 3750 + 1250 = 6250; use 1000 -> 5000 exactly
edges=tuple(edges[:5000])
st=m.prepare_state(q,edges,(),p,binding=b,state_epoch=e); integrity=m.validate_prepared_integrity(st)
full=[]; prep=[]
for _ in range(5):
    t=time.perf_counter(); z=None
    for _j in range(10): z=m.evaluate(q,edges,(),p)
    full.append((time.perf_counter()-t)*1000/10)
    t=time.perf_counter(); z2=None
    for _j in range(10): z2=m.evaluate_prepared(st,integrity_validated=integrity,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_frontier_fingerprint=st.frontier_fingerprint,current_pareto_fingerprint=st.pareto_fingerprint)
    prep.append((time.perf_counter()-t)*1000/10)
ids={x.edge_id for x in edges[:10]}; e2=tuple(replace(x,risk=x.risk+.001) if x.edge_id in ids else x for x in edges)
st2=m.prepare_state(q,e2,(),p,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
full_bytes=len(m._canon((q,e2,(),p))); delta_bytes=len(m._canon(d))
out={'condition':'Python stdlib; 5000 graph edges with safe alternatives/dead-end branches; 10 evaluations x 5 batches; prepared verified-result reuse','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':z==z2,'full_bytes':full_bytes,'delta_bytes':delta_bytes,'delta_percent':delta_bytes/full_bytes*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required}
print(json.dumps(out,sort_keys=True))
