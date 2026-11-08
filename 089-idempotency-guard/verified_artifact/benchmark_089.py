from dataclasses import replace
import json,statistics,time
from noepin_al_089_idempotency_guard import *
r,_,p=default_request(),default_histories(),default_policy()
N=5000
b,e=p.binding,p.state_epoch
hist=tuple(ExecutionHistoryRecord(f'H{n:05d}',f'K{n:05d}',f'I{n:05d}',f'A{n:05d}',ExecutionStatus.FAILED,'',True,b,e) for n in range(N))
st=prepare_state(r,hist,p,binding=b,state_epoch=e); valid=validate_prepared_integrity(st)
full=[]; prep=[]; semantic=True
for _ in range(5):
    t=time.perf_counter(); z1=None
    for __ in range(10): z1=evaluate(r,hist,p)
    full.append((time.perf_counter()-t)*1000)
    t=time.perf_counter(); z2=None
    for __ in range(10): z2=evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=valid)
    prep.append((time.perf_counter()-t)*1000); semantic &= (z1==z2)
h2=list(hist)
for n in range(10): h2[n]=replace(h2[n],status=ExecutionStatus.SUCCESS,result_fingerprint=f'R{n}')
st2=prepare_state(r,tuple(h2),p,binding=b,state_epoch=e); delta=make_delta(st,st2)
known=dict(st2.history_fingerprints)
for n in range(10): known.pop(f'H{n:05d}')
plan=missing_only_sync_plan(st2,known)
out={'schema':'NOEPIN_AL_BENCHMARK_V1','technology':89,'condition':'Python stdlib; 5000 Execution History records; 10 evaluations x 5 batches; prepared verified-result reuse','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':semantic,'full_bytes':full_registry_bytes(st2),'delta_bytes':delta_bytes(delta),'delta_percent':delta_bytes(delta)/full_registry_bytes(st2)*100,'missing_history_records':len(plan.missing_or_changed_record_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend_required':plan.full_resend_required}
print(json.dumps(out,ensure_ascii=False,sort_keys=True))
