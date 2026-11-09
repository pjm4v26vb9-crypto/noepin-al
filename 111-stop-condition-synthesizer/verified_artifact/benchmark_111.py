import json,time,statistics
from dataclasses import replace
import noepin_al_111_stop_condition_synthesizer as m
b='BENCH-BIND'; e='BENCH-EPOCH'
succ=[]; fail=[]
for i in range(600): succ.append(m.PredicateSpec(f'S{i:04d}',f's{i:04d}',m.Operator.GE,float(i),True,'bench success','V1',f'FPS{i:04d}',b,e))
for i in range(600): fail.append(m.PredicateSpec(f'F{i:04d}',f'f{i:04d}',m.Operator.GT,float(i+1000),True,'bench failure','V1',f'FPF{i:04d}',b,e))
budgets=tuple(m.BudgetLimit(f'r{i:03d}',10000.0+i,'units','V1',f'FPB{i:03d}',b,e) for i in range(100))
q=m.StopSynthesisRequest('BENCH-111','bounded stop synthesis benchmark',tuple(succ),tuple(fail),budgets,5000,True,b,e)
st=m.prepare_state(q,binding=b,state_epoch=e); integrity=m.validate_prepared_integrity(st)
full=[]; prep=[]; z=z2=None
for _ in range(5):
    t0=time.perf_counter()
    for _j in range(5): z=m.synthesize(q)
    full.append((time.perf_counter()-t0)*1000/5)
    t0=time.perf_counter()
    for _j in range(20): z2=m.evaluate_prepared(st,integrity_validated=integrity,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_budget_fingerprint=st.budget_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_monitor_fingerprint=st.monitor_fingerprint)
    prep.append((time.perf_counter()-t0)*1000/20)
changed=[]
for p in succ[:10]: changed.append(replace(p,expected=float(p.expected)+1,predicate_fingerprint=p.predicate_fingerprint+'X'))
q2=replace(q,success_criteria=tuple(changed)+tuple(succ[10:])); st2=m.prepare_state(q2,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
full_bytes=len(m._canon(q2)); delta_bytes=len(m._canon(d))
out={'condition':'Python stdlib; 1200 observable criteria + 100 resource budgets; deterministic predicate synthesis; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':z==z2,'full_bytes':full_bytes,'delta_bytes':delta_bytes,'delta_percent':delta_bytes/full_bytes*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required}
print(json.dumps(out,sort_keys=True))
