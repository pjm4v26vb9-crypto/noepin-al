import json,time,statistics
from dataclasses import replace
import noepin_al_108_cost_risk_pareto_planner as m
p=m.default_policy(); b=p.binding; e=p.state_epoch; q=m.default_request()
plans=[]
for i in range(5000):
    # deliberately creates a broad non-dominated/trade-off cloud plus some dominated candidates
    plans.append(m.CandidatePlan(f'P{i:05d}',1+(i%97)/7,1+((i*7)%89)/6,.1+((i*13)%70)/50,.70+((i*17)%30)/100,.50+((i*19)%50)/100,True,True,True,'V1',f'FP{i:05d}',b,e))
plans=tuple(plans)
st=m.prepare_state(q,plans,p,binding=b,state_epoch=e); integrity=m.validate_prepared_integrity(st)
full=[]; prep=[]
for _ in range(5):
    t=time.perf_counter(); z=None
    for _j in range(10): z=m.evaluate(q,plans,p)
    full.append((time.perf_counter()-t)*1000/10)
    t=time.perf_counter(); z2=None
    for _j in range(10): z2=m.evaluate_prepared(st,integrity_validated=integrity,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_frontier_fingerprint=st.frontier_fingerprint,current_selection_fingerprint=st.selection_fingerprint)
    prep.append((time.perf_counter()-t)*1000/10)
ids={x.plan_id for x in plans[:10]}; p2=tuple(replace(x,total_risk=x.total_risk+.001) if x.plan_id in ids else x for x in plans)
st2=m.prepare_state(q,p2,p,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
full_bytes=len(m._canon((q,p2,p))); delta_bytes=len(m._canon(d))
out={'condition':'Python stdlib; 5000 candidate plans across cost/time/risk/success/reversibility trade-offs; 10 evaluations x 5 batches; prepared verified-result reuse','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':z==z2,'full_bytes':full_bytes,'delta_bytes':delta_bytes,'delta_percent':delta_bytes/full_bytes*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required}
print(json.dumps(out,sort_keys=True))
