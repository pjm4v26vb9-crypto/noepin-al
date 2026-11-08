from dataclasses import replace
import json,statistics,time
from noepin_al_076_long_horizon_goal_drift_detector import *
p=default_policy(); b=p.binding; ep=p.state_epoch; start=1_800_000_000
goals=(GoalSpec('G-BENCH',('READ',),('DELETE','EXTERNAL_SEND'),b,ep),)
steps=tuple(StepRecord(f'S{i:04d}',start+i,('READ',),True,b,ep) for i in range(1500))
plans=(PlanRecord('P-BENCH',('READ',),True,b,ep),)
q=DriftRequest('BENCH-76','G-BENCH',tuple(f'S{i:04d}' for i in range(10)),'P-BENCH',None,b,ep,start+2000)
st=prepare_state(p,goals,steps,plans,(),binding=b); valid=validate_prepared_integrity(st)
full=[]; prep=[]; sem=True
for _ in range(5):
    t=time.perf_counter(); z1=None
    for __ in range(10): z1=evaluate(q,p,goals,steps,plans,())
    full.append((time.perf_counter()-t)*1000)
    t=time.perf_counter(); z2=None
    for __ in range(10): z2=evaluate_prepared(q,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=valid)
    prep.append((time.perf_counter()-t)*1000)
    sem &= (z1.decision==z2.decision and z1.reasons==z2.reasons and z1.drift_curve==z2.drift_curve)
steps2=list(steps)
for i in range(10): steps2[i]=replace(steps2[i],effect_tags=('READ','FORMAT'))
st2=prepare_state(p,goals,steps2,plans,(),binding=b); d=make_delta(st,st2)
rg=dict(st2.goal_fingerprints); rs=dict(st2.step_fingerprints); rp=dict(st2.plan_fingerprints); rc=dict(st2.checkpoint_fingerprints)
for i in range(10): rs.pop(f'S{i:04d}')
plan=missing_only_sync_plan(st2,rg,rs,rp,rc)
out={'schema':'NOEPIN_AL_BENCHMARK_V1','technology':76,'condition':'Python stdlib; 1 Goal + 1500 StepRecords + 1 Plan; 10 evaluations x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':sem,'full_bytes':full_registry_bytes(st2),'delta_bytes':delta_bytes(d),'delta_percent':delta_bytes(d)/full_registry_bytes(st2)*100,'missing_steps':len(plan.missing_or_changed_steps),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend_required':plan.full_resend_required}
print(json.dumps(out,ensure_ascii=False,sort_keys=True))
