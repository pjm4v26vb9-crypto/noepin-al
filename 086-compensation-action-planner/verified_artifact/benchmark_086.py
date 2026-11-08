from dataclasses import replace
import json,statistics,time
from noepin_al_086_compensation_action_planner import *
r,i,p,_,_,_,pol=default_request(),default_intent(),default_permit(),default_actions(),default_effects(),default_compensations(),default_policy()
N=5000
b,eph=pol.binding,pol.state_epoch
a=tuple(ForwardAction(f'A{n:05d}',n,Risk.MEDIUM,True,b,eph) for n in range(N))
e=tuple(EffectRecord(f'E{n:05d}',f'A{n:05d}',Risk.MEDIUM,1.0,True,b,eph) for n in range(N))
c=tuple(CompensationCandidate(f'C{n:05d}',f'E{n:05d}',1.0,Risk.LOW,CompensationStatus.READY,True,b,eph) for n in range(N))
st=prepare_state(r,i,p,a,e,c,pol,binding=b,state_epoch=eph); valid=validate_prepared_integrity(st)
full=[]; prep=[]; semantic=True
for _ in range(5):
    t=time.perf_counter(); z1=None
    for __ in range(10): z1=evaluate(r,i,p,a,e,c,pol)
    full.append((time.perf_counter()-t)*1000)
    t=time.perf_counter(); z2=None
    for __ in range(10): z2=evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=valid)
    prep.append((time.perf_counter()-t)*1000); semantic &= (z1==z2)
c2=list(c)
for n in range(10): c2[n]=replace(c2[n],coverage=.9)
st2=prepare_state(r,i,p,a,e,tuple(c2),pol,binding=b,state_epoch=eph); delta=make_delta(st,st2)
ka=dict(st2.action_fingerprints); ke=dict(st2.effect_fingerprints); kc=dict(st2.compensation_fingerprints)
for n in range(10): kc.pop(f'C{n:05d}')
plan=missing_only_sync_plan(st2,ka,ke,kc)
out={'schema':'NOEPIN_AL_BENCHMARK_V1','technology':86,'condition':'Python stdlib; 5000 Forward Actions + 5000 Effect records + 5000 Compensation records; 10 evaluations x 5 batches; prepared verified-result reuse','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':semantic,'full_bytes':full_registry_bytes(st2),'delta_bytes':delta_bytes(delta),'delta_percent':delta_bytes(delta)/full_registry_bytes(st2)*100,'missing_action_records':len(plan.missing_or_changed_action_ids),'missing_effect_records':len(plan.missing_or_changed_effect_ids),'missing_compensation_records':len(plan.missing_or_changed_compensation_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend_required':plan.full_resend_required}
print(json.dumps(out,ensure_ascii=False,sort_keys=True))
