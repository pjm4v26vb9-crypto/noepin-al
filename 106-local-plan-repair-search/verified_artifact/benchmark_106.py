import json,time,statistics
from dataclasses import replace
import noepin_al_106_local_plan_repair_search as m
p=m.default_policy(); b=p.binding; e=p.state_epoch
q=m.default_request(); plan=m.default_plan(); diff=m.default_diff()
c=[]
for i in range(5000):
    safe=(i%19)!=0
    c.append(m.RepairCandidate(f'C{i:05d}','BUILD',('source_ready',),('artifact_built',),.15+(i%17)/1000,1.0+(i%11)/100,safe,safe,'V1',f'F{i}',True,b,e))
c=tuple(c)
st=m.prepare_state(q,plan,diff,c,p,binding=b,state_epoch=e); integrity=m.validate_prepared_integrity(st)
full=[]; prep=[]
for _ in range(5):
    t=time.perf_counter(); z=None
    for _j in range(10): z=m.evaluate(q,plan,diff,c,p)
    full.append((time.perf_counter()-t)*1000/10)
    t=time.perf_counter(); z2=None
    for _j in range(10): z2=m.evaluate_prepared(st,integrity_validated=integrity,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_frontier_fingerprint=st.frontier_fingerprint,current_boundary_fingerprint=st.boundary_fingerprint)
    prep.append((time.perf_counter()-t)*1000/10)
ids={x.candidate_id for x in c[:10]}; c2=tuple(replace(x,risk=x.risk+.001) if x.candidate_id in ids else x for x in c)
st2=m.prepare_state(q,plan,diff,c2,p,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
full_bytes=len(m._canon((q,plan,diff,c2,p))); delta_bytes=len(m._canon(d))
out={'condition':'Python stdlib; 5000 local repair candidates over a dependency-sliced plan; 10 evaluations x 5 batches; prepared verified-result reuse','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':z==z2,'full_bytes':full_bytes,'delta_bytes':delta_bytes,'delta_percent':delta_bytes/full_bytes*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required}
print(json.dumps(out,sort_keys=True))
