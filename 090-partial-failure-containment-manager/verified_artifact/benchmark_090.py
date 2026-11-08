from dataclasses import replace
import json,statistics,time
from noepin_al_090_partial_failure_containment_manager import *
r=ContainmentRequest('BENCH','GRAPH',True,True,True,'CONT-BIND','STATE-EPOCH-1'); p=default_policy(); N=5000
steps=[]; states=[]; comps=[]
for n in range(N):
    sid=f'S{n:05d}'; deps=(f'S{n-1:05d}',) if n%50 and n>0 else (); res=(f'R{n//50:04d}',)
    steps.append(ExecutionStep(sid,deps,res,RiskLevel.LOW,True,p.binding,p.state_epoch)); states.append(StepStateRecord(sid,StepState.SUCCESS,'',True,p.binding,p.state_epoch)); comps.append(CompensationRecord(sid,f'C{n:05d}',1.0,RiskLevel.LOW,True,True,p.binding,p.state_epoch))
# one contained failure plus many records
states[0]=replace(states[0],state=StepState.FAILED,failure_code='ERR'); states[100]=replace(states[100],state=StepState.PENDING); states[150]=replace(states[150],state=StepState.PENDING)
steps=tuple(steps); states=tuple(states); comps=tuple(comps)
st=prepare_state(r,steps,states,comps,p,binding=p.binding,state_epoch=p.state_epoch); valid=validate_prepared_integrity(st)
full=[]; prep=[]; semantic=True
for _ in range(5):
    t=time.perf_counter(); z1=None
    for __ in range(10): z1=evaluate(r,steps,states,comps,p)
    full.append((time.perf_counter()-t)*1000)
    t=time.perf_counter(); z2=None
    for __ in range(10): z2=evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=valid)
    prep.append((time.perf_counter()-t)*1000); semantic &= (z1==z2)
states2=list(states)
for n in range(10): states2[n]=replace(states2[n],failure_code=f'ERR{n}',state=StepState.FAILED)
st2=prepare_state(r,steps,tuple(states2),comps,p,binding=p.binding,state_epoch=p.state_epoch); delta=make_delta(st,st2)
known=dict(st2.record_fingerprints)
for n in range(10): known.pop(f'STATE:S{n:05d}')
plan=missing_only_sync_plan(st2,known)
out={'schema':'NOEPIN_AL_BENCHMARK_V1','technology':90,'condition':'Python stdlib; 5000 Execution Graph steps + 5000 Step States + 5000 Compensation records; 10 evaluations x 5 batches; prepared verified-result reuse','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':semantic,'full_bytes':full_registry_bytes(st2),'delta_bytes':delta_bytes(delta),'delta_percent':delta_bytes(delta)/full_registry_bytes(st2)*100,'missing_records':len(plan.missing_or_changed_record_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend_required':plan.full_resend_required}
print(json.dumps(out,ensure_ascii=False,sort_keys=True))
