import json,time,statistics
from dataclasses import replace
import noepin_al_112_model_predictive_safety_controller as m
b='BENCH-BIND'; e='BENCH-EPOCH'
state=tuple((f'x{i}',50.0) for i in range(6))
goals=tuple(m.GoalTarget(f'x{i}',55.0,1.0,'V1',f'G{i}',b,e) for i in range(6))
constraints=tuple(m.HardConstraint(f'C{i}',f'x{i}',0.0,100.0,'V1',f'C{i}',b,e) for i in range(6))
actions=[]
for i in range(1200):
    d=tuple((f'x{j}',((i+j)%5-2)*0.1) for j in range(6))
    actions.append(m.ActionEffectModel(f'A{i:04d}',d,float(i%7)*0.05,float((i%5)+1)*0.01,'V1',f'FP{i:04d}',b,e))
q=m.MPCRequest('BENCH-112',state,tuple(actions),goals,constraints,5,1.0,5.0,1.0,b,e)
st=m.prepare_state(q,binding=b,state_epoch=e); integrity=m.validate_prepared_integrity(st)
full=[]; prep=[]; z=z2=None
for _ in range(5):
    t0=time.perf_counter()
    for _j in range(5): z=m.evaluate(q)
    full.append((time.perf_counter()-t0)*1000/5)
    t0=time.perf_counter()
    for _j in range(20): z2=m.evaluate_prepared(st,integrity_validated=integrity,current_context_fingerprint=st.context_fingerprint,current_dynamics_fingerprint=st.dynamics_fingerprint,current_constraint_fingerprint=st.constraint_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_frontier_fingerprint=st.frontier_fingerprint)
    prep.append((time.perf_counter()-t0)*1000/20)
changed=[]
for a in actions[:10]: changed.append(replace(a,risk_cost=a.risk_cost+0.01,effect_fingerprint=a.effect_fingerprint+'X'))
q2=replace(q,actions=tuple(changed)+tuple(actions[10:])); st2=m.prepare_state(q2,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
full_bytes=len(m._canon(q2)); delta_bytes=len(m._canon(d))
out={'condition':'Python stdlib; 1200 action-effect candidates; 6 state dimensions; 6 hard constraints; horizon 5; deterministic receding-horizon evaluation; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':z==z2,'full_bytes':full_bytes,'delta_bytes':delta_bytes,'delta_percent':delta_bytes/full_bytes*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required}
print(json.dumps(out,sort_keys=True))
