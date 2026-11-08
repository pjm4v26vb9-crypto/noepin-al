from dataclasses import replace
import json,statistics,time
from noepin_al_079_correlated_consensus_detector import *
p=default_policy(); b,e=p.binding,p.state_epoch
outs=tuple(AgentOutput(f'OUT-{i:04d}',f'AGENT-{i:04d}','YES' if i%3 else 'NO',f'MODEL-{i:04d}',f'PROMPT-{i:04d}',(f'SRC-{i:04d}',),(f'EVID-{i:04d}',),True,1.0,b,e) for i in range(1500))
q=ConsensusRequest('BENCH','YES',tuple(x.output_id for x in outs[:60]),b,e)
st=prepare_state(p,outs,binding=b); valid=validate_prepared_integrity(st); full=[]; prep=[]; sem=True
for _ in range(5):
    t=time.perf_counter(); z1=None
    for __ in range(10): z1=evaluate(q,p,outs)
    full.append((time.perf_counter()-t)*1000)
    t=time.perf_counter(); z2=None
    for __ in range(10): z2=evaluate_prepared(q,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=valid)
    prep.append((time.perf_counter()-t)*1000)
    sem &= (z1.decision==z2.decision and z1.reasons==z2.reasons and z1.adjusted_consensus==z2.adjusted_consensus and z1.clusters==z2.clusters)
o2=list(outs)
for i in range(10): o2[i]=replace(o2[i],model_id='SHARED-MODEL')
st2=prepare_state(p,tuple(o2),binding=b); d=make_delta(st,st2); known=dict(st2.output_fingerprints)
for i in range(10): known.pop(f'OUT-{i:04d}')
plan=missing_only_sync_plan(st2,known)
out={'schema':'NOEPIN_AL_BENCHMARK_V1','technology':79,'condition':'Python stdlib; 1500 AgentOutput records; request evaluates 60 outputs; 10 evaluations x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':sem,'full_bytes':full_registry_bytes(st2),'delta_bytes':delta_bytes(d),'delta_percent':delta_bytes(d)/full_registry_bytes(st2)*100,'missing_outputs':len(plan.missing_or_changed_outputs),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend_required':plan.full_resend_required}
print(json.dumps(out,ensure_ascii=False,sort_keys=True))
