from dataclasses import replace
import json,statistics,time
from noepin_al_088_decision_freshness_window_verifier import *
r,_,p=default_request(),default_dependencies(),default_policy()
N=5000
b,e=p.binding,p.state_epoch
deps=tuple(DependencyFreshness(f'F{n:05d}',1009.0,(n%10)/20.0,Criticality.LOW if n%4 else Criticality.MEDIUM,f'SRC{n%7}',f'V{n%5}',f'EVID{n:05d}',True,b,e) for n in range(N))
r=replace(r,decision_time=1009.0,now=1010.0,risk=RiskLevel.MEDIUM)
st=prepare_state(r,deps,p,binding=b,state_epoch=e); valid=validate_prepared_integrity(st)
full=[]; prep=[]; semantic=True
for _ in range(5):
    t=time.perf_counter(); z1=None
    for __ in range(10): z1=evaluate(r,deps,p)
    full.append((time.perf_counter()-t)*1000)
    t=time.perf_counter(); z2=None
    for __ in range(10): z2=evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_calibration_fingerprint=st.calibration_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=valid)
    prep.append((time.perf_counter()-t)*1000); semantic &= (z1==z2)
d2=list(deps)
for n in range(10): d2[n]=replace(d2[n],source_version='VX',evidence_fingerprint=f'NEW{n}')
st2=prepare_state(r,tuple(d2),p,binding=b,state_epoch=e); delta=make_delta(st,st2)
known=dict(st2.dependency_fingerprints)
for n in range(10): known.pop(f'F{n:05d}')
plan=missing_only_sync_plan(st2,known)
out={'schema':'NOEPIN_AL_BENCHMARK_V1','technology':88,'condition':'Python stdlib; 5000 Dependency freshness records; 10 evaluations x 5 batches; prepared verified-result reuse','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':semantic,'full_bytes':full_registry_bytes(st2),'delta_bytes':delta_bytes(delta),'delta_percent':delta_bytes(delta)/full_registry_bytes(st2)*100,'missing_dependency_records':len(plan.missing_or_changed_field_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend_required':plan.full_resend_required}
print(json.dumps(out,ensure_ascii=False,sort_keys=True))
