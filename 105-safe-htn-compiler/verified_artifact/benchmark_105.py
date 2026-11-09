import json,time,statistics
from dataclasses import replace
import noepin_al_105_safe_htn_compiler as m
p=m.default_policy(); b=p.binding; e=p.state_epoch
# One root task with 5000 candidate HTN methods; most are safe variants over three shared leaf tasks.
leaves=m.default_leaves()[:3]
methods=[]
for i in range(5000):
    safe=(i%17)!=0
    methods.append(m.HTNMethod(f'M{i:05d}','PROJECT_FIX',('INSPECT','PATCH','VERIFY'),('repo_loaded',),2,.1+(i%13)/1000,safe,i%101,'V1',f'F{i}',True,b,e))
methods=tuple(methods)
q=m.default_request(); s=m.default_state()
st=m.prepare_state(q,s,methods,leaves,p,binding=b,state_epoch=e); integrity=m.validate_prepared_integrity(st)
full=[]; prep=[]
for _ in range(5):
    t=time.perf_counter(); z=None
    for _j in range(10): z=m.evaluate(q,s,methods,leaves,p)
    full.append((time.perf_counter()-t)*1000/10)
    t=time.perf_counter(); z2=None
    for _j in range(10): z2=m.evaluate_prepared(st,integrity_validated=integrity,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_frontier_fingerprint=st.frontier_fingerprint,current_decomposition_fingerprint=st.decomposition_fingerprint)
    prep.append((time.perf_counter()-t)*1000/10)
ids={x.method_id for x in methods[:10]}; methods2=tuple(replace(x,method_risk=x.method_risk+.001) if x.method_id in ids else x for x in methods)
st2=m.prepare_state(q,s,methods2,leaves,p,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
full_bytes=len(m._canon((q,s,methods2,leaves,p))); delta_bytes=len(m._canon(d))
out={'condition':'Python stdlib; 5000 candidate HTN methods over three shared leaf tasks; 10 evaluations x 5 batches; prepared verified-result reuse','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':z==z2,'full_bytes':full_bytes,'delta_bytes':delta_bytes,'delta_percent':delta_bytes/full_bytes*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required}
print(json.dumps(out,sort_keys=True))
