from dataclasses import replace
import json,statistics,time
from noepin_al_094_confidence_calibration_monitor import *
p=default_policy(); r=CalibrationRequest('BENCH','FACT_VERIFY',.8,RiskLevel.LOW,100000,True,p.binding,p.state_epoch)
o=[]
for n in range(5000):
    pred=.8; outcome=(n%5)!=4
    o.append(CalibrationObservation(f'O{n:05d}','FACT_VERIFY',pred,outcome,n,'SRC-V1','MODEL-V1',f'EFP{n:05d}',True,p.binding,p.state_epoch))
o=tuple(o); st=prepare_state(r,o,p,binding=p.binding,state_epoch=p.state_epoch); valid=validate_prepared_integrity(st)
full=[]; prep=[]; semantic=True
for _ in range(5):
    t=time.perf_counter(); z1=None
    for __ in range(10): z1=evaluate(r,o,p)
    full.append((time.perf_counter()-t)*1000)
    t=time.perf_counter(); z2=None
    for __ in range(10): z2=evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_calibration_fingerprint=st.calibration_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=valid)
    prep.append((time.perf_counter()-t)*1000); semantic &= (z1==z2)
o2=list(o)
for n in range(10): o2[n]=replace(o2[n],source_version='SRC-V2',evidence_fingerprint=f'NEW{n}')
st2=prepare_state(r,tuple(o2),p,binding=p.binding,state_epoch=p.state_epoch); delta=make_delta(st,st2)
known=dict(st2.record_fingerprints)
for n in range(10): known.pop(f'OBS:O{n:05d}')
plan=missing_only_sync_plan(st2,known)
print(json.dumps({'schema':'NOEPIN_AL_BENCHMARK_V1','technology':94,'condition':'Python stdlib; 5000 Calibration observations; 10 evaluations x 5 batches; prepared verified-result reuse','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':semantic,'full_bytes':full_registry_bytes(st2),'delta_bytes':delta_bytes(delta),'delta_percent':delta_bytes(delta)/full_registry_bytes(st2)*100,'missing_records':len(plan.missing_or_changed_record_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend_required':plan.full_resend_required},ensure_ascii=False,sort_keys=True))
