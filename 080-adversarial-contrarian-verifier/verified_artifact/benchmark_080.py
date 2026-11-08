from dataclasses import replace
import json,statistics,time
from noepin_al_080_adversarial_contrarian_verifier import *
r=default_risk_model(); b,e=r.binding,r.state_epoch
constraints=tuple(ConstraintRule(f'C-{i:04d}',(f'FX-{i:04d}',),(),Severity.MEDIUM,True,b,e) for i in range(1500))
env=tuple(EnvironmentFact(f'K-{i:04d}','OK',True,b,e) for i in range(1500))
actions=tuple(PlanAction(f'A-{i:04d}','CHECK',f'T-{i:04d}',('SAFE',),(),b,e) for i in range(60)); p=PrimaryPlan('BENCH',actions,plan_fingerprint(actions),b,e); q=VerificationRequest('BENCH','BENCH',tuple(x.constraint_id for x in constraints[:60]),b,e)
st=prepare_state(r,constraints,env,binding=b); valid=validate_prepared_integrity(st); full=[]; prep=[]; sem=True
for _ in range(5):
    t=time.perf_counter(); z1=None
    for __ in range(10): z1=evaluate(q,p,r,constraints,env)
    full.append((time.perf_counter()-t)*1000)
    t=time.perf_counter(); z2=None
    for __ in range(10): z2=evaluate_prepared(q,p,st,current_risk_fingerprint=st.risk_model_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=valid)
    prep.append((time.perf_counter()-t)*1000)
    sem &= (z1.decision==z2.decision and z1.reasons==z2.reasons and z1.coverage==z2.coverage and z1.counterexamples==z2.counterexamples)
c2=list(constraints)
for i in range(10): c2[i]=replace(c2[i],observed=False)
st2=prepare_state(r,tuple(c2),env,binding=b); d=make_delta(st,st2); kc=dict(st2.constraint_fingerprints); ke=dict(st2.environment_fingerprints)
for i in range(10): kc.pop(f'C-{i:04d}')
plan=missing_only_sync_plan(st2,kc,ke)
out={'schema':'NOEPIN_AL_BENCHMARK_V1','technology':80,'condition':'Python stdlib; 1500 Constraint + 1500 Environment records; request checks 60 constraints x 60 actions; 10 evaluations x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':sem,'full_bytes':full_registry_bytes(st2),'delta_bytes':delta_bytes(d),'delta_percent':delta_bytes(d)/full_registry_bytes(st2)*100,'missing_constraints':len(plan.missing_or_changed_constraints),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend_required':plan.full_resend_required}
print(json.dumps(out,ensure_ascii=False,sort_keys=True))
