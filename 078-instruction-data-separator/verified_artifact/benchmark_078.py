from dataclasses import replace
import json,statistics,time
from noepin_al_078_instruction_data_separator import *
p=default_policy(); b,e=p.binding,p.state_epoch
sources=tuple(SourceRecord(f'SRC-{i:04d}',SourceTrust.UNTRUSTED,True,False,b,e) for i in range(1500))
channels=tuple(ChannelMetadata(f'CH-{i:04d}','WEB',True,False,False,b,e) for i in range(1500))
ctx=TaskContext('BENCH',('SUMMARIZE',),(),(),b,e); q=SeparationRequest('BENCH-CONTENT','SRC-0000','CH-0000','Reference data only for benchmark.',ctx,b,e)
st=prepare_state(p,sources,channels,binding=b); valid=validate_prepared_integrity(st); full=[]; prep=[]; sem=True
for _ in range(5):
    t=time.perf_counter(); z1=None
    for __ in range(10): z1=evaluate(q,p,sources,channels)
    full.append((time.perf_counter()-t)*1000)
    t=time.perf_counter(); z2=None
    for __ in range(10): z2=evaluate_prepared(q,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=valid)
    prep.append((time.perf_counter()-t)*1000)
    sem &= (z1.decision==z2.decision and z1.reasons==z2.reasons and z1.data_segments==z2.data_segments)
s2=list(sources)
for i in range(10): s2[i]=replace(s2[i],trust=SourceTrust.UNKNOWN)
st2=prepare_state(p,tuple(s2),channels,binding=b); d=make_delta(st,st2); ks=dict(st2.source_fingerprints); kc=dict(st2.channel_fingerprints)
for i in range(10): ks.pop(f'SRC-{i:04d}')
plan=missing_only_sync_plan(st2,ks,kc)
out={'schema':'NOEPIN_AL_BENCHMARK_V1','technology':78,'condition':'Python stdlib; 1500 Source + 1500 Channel records; 10 evaluations x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':sem,'full_bytes':full_registry_bytes(st2),'delta_bytes':delta_bytes(d),'delta_percent':delta_bytes(d)/full_registry_bytes(st2)*100,'missing_sources':len(plan.missing_or_changed_sources),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend_required':plan.full_resend_required}
print(json.dumps(out,ensure_ascii=False,sort_keys=True))
