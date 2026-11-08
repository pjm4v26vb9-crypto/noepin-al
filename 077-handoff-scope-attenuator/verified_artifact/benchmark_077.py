from dataclasses import replace
import json,statistics,time
from noepin_al_077_handoff_scope_attenuator import *
p=default_policy(); b=p.binding; e=p.state_epoch
caps=tuple(CapabilitySpec(f'CAP-{i:04d}',('READ',),('PUBLIC',),('WORKSPACE',),True,b,e) for i in range(1500))
scopes=[]
for i in range(1500):
    scopes.append(ScopeSpec(f'P-{i:04d}',('TASK',),('PUBLIC',),('READ',),('WORKSPACE',),(f'CAP-{i:04d}',),0,True,True,b,e))
    scopes.append(ScopeSpec(f'C-{i:04d}',('TASK',),('PUBLIC',),('READ',),('WORKSPACE',),(f'CAP-{i:04d}',),1,True,False,b,e))
scopes=tuple(scopes); q=HandoffRequest('BENCH-77','P-0000','C-0000',('TASK',),('CAP-0000',),b,e)
st=prepare_state(p,scopes,caps,binding=b); valid=validate_prepared_integrity(st); full=[]; prep=[]; sem=True
for _ in range(5):
    t=time.perf_counter(); z1=None
    for __ in range(10): z1=evaluate(q,p,scopes,caps)
    full.append((time.perf_counter()-t)*1000)
    t=time.perf_counter(); z2=None
    for __ in range(10): z2=evaluate_prepared(q,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=valid)
    prep.append((time.perf_counter()-t)*1000)
    sem &= (z1.decision==z2.decision and z1.reasons==z2.reasons and z1.violation_items==z2.violation_items and z1.attenuated_scope==z2.attenuated_scope)
scopes2=list(scopes)
for i in range(10):
    idx=2*i+1; scopes2[idx]=replace(scopes2[idx],data_classes=('INTERNAL','PUBLIC'))
st2=prepare_state(p,tuple(scopes2),caps,binding=b); d=make_delta(st,st2); ks=dict(st2.scope_fingerprints); kc=dict(st2.capability_fingerprints)
for i in range(10): ks.pop(f'C-{i:04d}')
plan=missing_only_sync_plan(st2,ks,kc)
out={'schema':'NOEPIN_AL_BENCHMARK_V1','technology':77,'condition':'Python stdlib; 3000 Scope records + 1500 Capability records; 10 evaluations x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':sem,'full_bytes':full_registry_bytes(st2),'delta_bytes':delta_bytes(d),'delta_percent':delta_bytes(d)/full_registry_bytes(st2)*100,'missing_scopes':len(plan.missing_or_changed_scopes),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend_required':plan.full_resend_required}
print(json.dumps(out,ensure_ascii=False,sort_keys=True))
