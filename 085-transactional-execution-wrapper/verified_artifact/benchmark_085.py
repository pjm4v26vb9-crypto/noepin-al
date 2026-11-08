from dataclasses import replace
import json,statistics,time
from noepin_al_085_transactional_execution_wrapper import *
r,i,p,pl,b,a,s,v,rb,pol=default_request(),default_intent(),default_permit(),default_plan(),default_before(),default_after(),default_steps(),default_verify(),default_rollback(),default_policy()
N=5000
pl=replace(pl,actions=tuple(ActionSpec(f'A{n:05d}',n) for n in range(N)))
steps=tuple(StepEvidence(f'S{n:05d}','TX-1',f'A{n:05d}',True,StepStatus.APPLIED,f'F{n:05d}',f'F{n+1:05d}',pol.binding,pol.state_epoch) for n in range(N))
a=replace(a,state_fingerprint=f'F{N:05d}'); v=replace(v,final_state_fingerprint=f'F{N:05d}',expected_final_state_fingerprint=f'F{N:05d}')
st=prepare_state(r,i,p,pl,b,a,steps,v,rb,pol,binding=pol.binding,state_epoch=pol.state_epoch); valid=validate_prepared_integrity(st)
full=[]; prep=[]; semantic=True
for _ in range(5):
    t=time.perf_counter(); z1=None
    for __ in range(10): z1=evaluate(r,i,p,pl,b,a,steps,v,rb,pol)
    full.append((time.perf_counter()-t)*1000)
    t=time.perf_counter(); z2=None
    for __ in range(10): z2=evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=valid)
    prep.append((time.perf_counter()-t)*1000); semantic &= (z1==z2)
steps2=list(steps)
for n in range(10): steps2[n]=replace(steps2[n],after_fingerprint=f'CHANGED{n}')
st2=prepare_state(r,i,p,pl,b,a,tuple(steps2),v,rb,pol,binding=pol.binding,state_epoch=pol.state_epoch); delta=make_delta(st,st2)
known=dict(st2.step_fingerprints)
for n in range(10): known.pop(f'S{n:05d}')
plan=missing_only_sync_plan(st2,known)
out={'schema':'NOEPIN_AL_BENCHMARK_V1','technology':85,'condition':'Python stdlib; 5000 Action Specs + 5000 Step Evidence records; 10 evaluations x 5 batches; prepared verified-result reuse','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':semantic,'full_bytes':full_registry_bytes(st2),'delta_bytes':delta_bytes(delta),'delta_percent':delta_bytes(delta)/full_registry_bytes(st2)*100,'missing_step_records':len(plan.missing_or_changed_step_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend_required':plan.full_resend_required}
print(json.dumps(out,ensure_ascii=False,sort_keys=True))
