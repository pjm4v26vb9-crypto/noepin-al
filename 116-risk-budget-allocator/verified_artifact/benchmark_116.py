import json,time,statistics
from dataclasses import replace
import noepin_al_116_risk_budget_allocator as m
b='BENCH-BIND'; e='BENCH-EPOCH'; ss=[]
for i in range(1200):
    risk=0.05+((i%17)/100.0); pri=0.5+(i%11)/10.0
    ss.append(m.Subtask(f'S{i:04d}',pri,risk, i%19==0, 0.00001*(i%3),0.0,False,'V1',f'FP-{i:04d}',b,e))
p=m.RiskBudgetPolicy(0.05,0.02,0.35,0.05,0.0001,0.10,0.10,True)
q=m.AllocationRequest('BENCH-116',100.0,tuple(ss),p,b,e); st=m.prepare_state(q,binding=b,state_epoch=e); integrity=m.validate_prepared_integrity(st)
full=[]; prep=[]; z=z2=None
for _ in range(5):
    t0=time.perf_counter()
    for _j in range(5): z=m.evaluate(q)
    full.append((time.perf_counter()-t0)*1000/5)
    t0=time.perf_counter()
    for _j in range(20): z2=m.evaluate_prepared(st,integrity_validated=integrity,current_context_fingerprint=st.context_fingerprint,current_subtask_fingerprint=st.subtask_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_allocation_fingerprint=st.allocation_fingerprint)
    prep.append((time.perf_counter()-t0)*1000/20)
changed=[replace(s,risk_estimate=min(1.0,(s.risk_estimate or 0)+0.01),evidence_fingerprint=s.evidence_fingerprint+'X') for s in ss[:10]]
q2=replace(q,subtasks=tuple(changed)+tuple(ss[10:])); st2=m.prepare_state(q2,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
full_bytes=len(m._canon(q2)); delta_bytes=len(m._canon(d))
out={'condition':'Python stdlib; 1200 subtasks; constrained total/critical/unknown risk budget allocation; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':z==z2,'full_bytes':full_bytes,'delta_bytes':delta_bytes,'delta_percent':delta_bytes/full_bytes*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required}
print(json.dumps(out,sort_keys=True))
