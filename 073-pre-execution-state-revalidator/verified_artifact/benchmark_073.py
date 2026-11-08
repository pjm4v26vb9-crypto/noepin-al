from dataclasses import replace
import json,statistics,time
from noepin_al_073_pre_execution_state_revalidator import *
NOW=1_800_000_000
pol=default_policy(); d=default_decision_snapshot(NOW)
extra=tuple(SnapshotValue(f'dep-{i:04d}',f'fp-{i:04d}','v1',True,'IRRELEVANT','PREEXEC-BIND','STATE-EPOCH-1') for i in range(3000))
d=replace(d,values=d.values+extra)
keys=default_dependency_keys()+tuple(f'dep-{i:04d}' for i in range(3000))
p=matching_preexecution_snapshot(d,NOW)
st=prepare_state(pol,d,keys,binding=d.binding); valid=validate_prepared_integrity(st)
full=[]; prep=[]; sem=True
for _ in range(5):
    t=time.perf_counter(); z1=None
    for __ in range(10): z1=evaluate(d,p,keys,pol,now=NOW)
    full.append((time.perf_counter()-t)*1000)
    t=time.perf_counter(); z2=None
    for __ in range(10): z2=evaluate_prepared(p,st,current_policy_fingerprint=st.policy_fingerprint,current_decision_fingerprint=st.decision_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=valid,now=NOW)
    prep.append((time.perf_counter()-t)*1000)
    sem &= (z1.decision==z2.decision and z1.reasons==z2.reasons and z1.irrelevant_diff_keys==z2.irrelevant_diff_keys)
vals=list(d.values)
for i in range(10):
    idx=5+i
    vals[idx]=replace(vals[idx],value_fingerprint=f'changed-{i}')
d2=replace(d,snapshot_id='DEC-SNAP-73B',values=tuple(vals))
st2=prepare_state(pol,d2,keys,binding=d.binding); delta=make_delta(st,st2)
remote=dict(st2.value_fingerprints)
for i in range(10): remote.pop(f'dep-{i:04d}')
plan=missing_only_sync_plan(st2,remote)
out={'schema':'NOEPIN_AL_BENCHMARK_V1','technology':73,'condition':'Python stdlib; 3005 decision-snapshot values / dependency keys; 10 evaluations x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':sem,'full_bytes':full_registry_bytes(st2),'delta_bytes':delta_bytes(delta),'delta_percent':delta_bytes(delta)/full_registry_bytes(st2)*100,'missing_keys':len(plan.missing_or_changed_keys),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend_required':plan.full_resend_required}
print(json.dumps(out,ensure_ascii=False,sort_keys=True))
