from dataclasses import replace
import json,statistics,time
from noepin_al_081_postcondition_auditor import *

pol=default_policy(); b,e=pol.binding,pol.state_epoch
N=5000
conditions=tuple(ExpectedPostcondition(f'C-{n:05d}',f'path/{n:05d}',PredicateOperator.EQ,'OK',True,Severity.MEDIUM,b,e) for n in range(N))
state=tuple(StateFact(f'path/{n:05d}','OK',True,True,'READ-BENCH',b,e) for n in range(N))
allowed=tuple(f'path/{n:05d}' for n in range(50))
diff=tuple(DiffEffect(f'D-{n:05d}',f'path/{n:05d}','OLD','OK',True,True,Severity.LOW,b,e) for n in range(50))
q=AuditRequest('BENCH','INTENT-B','PERMIT-B',tuple(f'C-{n:05d}' for n in range(50)),allowed,True,b,e)
i=IntentEvidence('INTENT-B',allowed,True,b,e)
p=PermitEvidence('PERMIT-B',allowed,True,True,True,b,e)
r=ExecutionReceipt('BENCH',True,True,b,e)
st=prepare_state(pol,q,i,p,r,conditions,state,diff,binding=b); valid=validate_prepared_integrity(st)
full=[]; prep=[]; semantic=True
for _ in range(5):
    t=time.perf_counter(); z1=None
    for __ in range(10): z1=evaluate(q,i,p,r,pol,conditions,state,diff)
    full.append((time.perf_counter()-t)*1000)
    t=time.perf_counter(); z2=None
    for __ in range(10): z2=evaluate_prepared(st,current_policy_fingerprint=st.policy_fingerprint,current_request_fingerprint=st.request_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=valid)
    prep.append((time.perf_counter()-t)*1000)
    semantic &= (z1==z2)
state2=list(state)
for n in range(10): state2[n]=replace(state2[n],value='CHANGED')
st2=prepare_state(pol,q,i,p,r,conditions,tuple(state2),diff,binding=b)
delta=make_delta(st,st2)
kc=dict(st2.condition_fingerprints); ks=dict(st2.state_fingerprints); ke=dict(st2.effect_fingerprints)
for n in range(10): ks.pop(f'path/{n:05d}')
plan=missing_only_sync_plan(st2,kc,ks,ke)
out={'schema':'NOEPIN_AL_BENCHMARK_V1','technology':81,'condition':'Python stdlib; 5000 ExpectedPostconditions + 5000 Observed State facts + 50 Diff effects; request audits 50 required conditions; 10 evaluations x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':semantic,'full_bytes':full_registry_bytes(st2),'delta_bytes':delta_bytes(delta),'delta_percent':delta_bytes(delta)/full_registry_bytes(st2)*100,'missing_state_records':len(plan.missing_or_changed_state_paths),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend_required':plan.full_resend_required}
print(json.dumps(out,ensure_ascii=False,sort_keys=True))
