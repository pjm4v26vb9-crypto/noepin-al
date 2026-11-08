from dataclasses import replace
import json,statistics,time
from noepin_al_092_bayesian_uncertainty_fusion import *
p=default_policy(); r=FusionRequest('BENCH','H-SAFE',RiskLevel.LOW,1_800_000_000,True,p.binding,p.state_epoch)
h=(Hypothesis('H-SAFE',.5,True,p.binding,p.state_epoch),Hypothesis('H-UNSAFE',.5,True,p.binding,p.state_epoch))
s=tuple(SourceReliability(f'S{n:03d}',.85+(n%10)*.01,True,'V1',f'SFP{n:03d}',p.binding,p.state_epoch) for n in range(100))
e=[]
for n in range(5000):
    e.append(EvidenceRecord(f'E{n:05d}',f'S{n%100:03d}',(('H-SAFE',.70+(n%5)*.02),('H-UNSAFE',.30-(n%5)*.02)),f'G{n:05d}',True,True,f'EFP{n:05d}','V1',p.binding,p.state_epoch))
e=tuple(e)
st=prepare_state(r,h,e,s,p,binding=p.binding,state_epoch=p.state_epoch); valid=validate_prepared_integrity(st)
full=[]; prep=[]; semantic=True
for _ in range(5):
    t=time.perf_counter(); z1=None
    for __ in range(10): z1=evaluate(r,h,e,s,p)
    full.append((time.perf_counter()-t)*1000)
    t=time.perf_counter(); z2=None
    for __ in range(10): z2=evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_calibration_fingerprint=st.calibration_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=valid)
    prep.append((time.perf_counter()-t)*1000); semantic &= (z1==z2)
e2=list(e)
for n in range(10): e2[n]=replace(e2[n],likelihoods=(('H-SAFE',.55),('H-UNSAFE',.45)))
st2=prepare_state(r,h,tuple(e2),s,p,binding=p.binding,state_epoch=p.state_epoch); delta=make_delta(st,st2)
known=dict(st2.record_fingerprints)
for n in range(10): known.pop(f'EVID:E{n:05d}')
plan=missing_only_sync_plan(st2,known)
out={'schema':'NOEPIN_AL_BENCHMARK_V1','technology':92,'condition':'Python stdlib; 5000 Evidence records + 100 Source profiles + 2 Hypotheses; 10 evaluations x 5 batches; prepared verified-result reuse','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':semantic,'full_bytes':full_registry_bytes(st2),'delta_bytes':delta_bytes(delta),'delta_percent':delta_bytes(delta)/full_registry_bytes(st2)*100,'missing_records':len(plan.missing_or_changed_record_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend_required':plan.full_resend_required}
print(json.dumps(out,ensure_ascii=False,sort_keys=True))
