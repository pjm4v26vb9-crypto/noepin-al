from dataclasses import replace
import json,statistics,time
from noepin_al_093_evidence_independence_estimator import *
p=default_policy(); r=IndependenceRequest('BENCH',RiskLevel.LOW,True,p.binding,p.state_epoch)
e=[]
for n in range(500):
    e.append(EvidenceRecord(f'E{n:04d}',f'SRC{n:04d}',f'M{n:04d}',f'U{n:04d}',f'D{n:04d}',(),True,True,'V1',f'EFP{n:04d}',f'CFP{n:04d}',p.binding,p.state_epoch))
e=tuple(e); g=()
st=prepare_state(r,e,g,p,binding=p.binding,state_epoch=p.state_epoch); valid=validate_prepared_integrity(st)
full=[]; prep=[]; semantic=True
for _ in range(5):
    t=time.perf_counter(); z1=None
    for __ in range(10): z1=evaluate(r,e,g,p)
    full.append((time.perf_counter()-t)*1000)
    t=time.perf_counter(); z2=None
    for __ in range(10): z2=evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_calibration_fingerprint=st.calibration_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=valid)
    prep.append((time.perf_counter()-t)*1000); semantic &= (z1==z2)
e2=list(e)
for n in range(10): e2[n]=replace(e2[n],source_id='SHARED-SOURCE')
st2=prepare_state(r,tuple(e2),g,p,binding=p.binding,state_epoch=p.state_epoch); delta=make_delta(st,st2)
known=dict(st2.record_fingerprints)
for n in range(10): known.pop(f'EVID:E{n:04d}')
plan=missing_only_sync_plan(st2,known)
out={'schema':'NOEPIN_AL_BENCHMARK_V1','technology':93,'condition':'Python stdlib; 500 Evidence records; pairwise provenance independence matrix; 10 evaluations x 5 batches; prepared verified-result reuse','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':semantic,'full_bytes':full_registry_bytes(st2),'delta_bytes':delta_bytes(delta),'delta_percent':delta_bytes(delta)/full_registry_bytes(st2)*100,'missing_records':len(plan.missing_or_changed_record_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend_required':plan.full_resend_required}
print(json.dumps(out,ensure_ascii=False,sort_keys=True))
