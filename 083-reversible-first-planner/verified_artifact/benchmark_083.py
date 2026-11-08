from dataclasses import replace
import json,statistics,time
from noepin_al_083_reversible_first_planner import *
p=default_policy(); g=default_goal(); b,ep=p.binding,p.state_epoch; N=5000
actions=tuple(CandidateAction(f'A{n:05d}',g.goal_id,1.0,0.70+(n%30)/100.0,float(n%100),Risk.LOW if n%5 else Risk.MEDIUM,f'R{n:05d}',False,True,None,b,ep) for n in range(N))
approvals=()
st=prepare_state(p,g,actions,approvals,binding=b,state_epoch=ep); valid=validate_prepared_integrity(st)
full=[]; prep=[]; semantic=True
for _ in range(5):
    t=time.perf_counter(); z1=None
    for __ in range(10): z1=evaluate(g,actions,approvals,p)
    full.append((time.perf_counter()-t)*1000)
    t=time.perf_counter(); z2=None
    for __ in range(10): z2=evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=valid)
    prep.append((time.perf_counter()-t)*1000); semantic &= (z1==z2)
a2=list(actions)
for n in range(10): a2[n]=replace(a2[n],cost=a2[n].cost+1)
st2=prepare_state(p,g,tuple(a2),approvals,binding=b,state_epoch=ep); delta=make_delta(st,st2)
known=dict(st2.action_fingerprints)
for n in range(10): known.pop(f'A{n:05d}')
plan=missing_only_sync_plan(st2,known,{})
out={'schema':'NOEPIN_AL_BENCHMARK_V1','technology':83,'condition':'Python stdlib; 5000 Candidate Actions; 10 evaluations x 5 batches; prepared verified-result reuse','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':semantic,'full_bytes':full_registry_bytes(st2),'delta_bytes':delta_bytes(delta),'delta_percent':delta_bytes(delta)/full_registry_bytes(st2)*100,'missing_action_records':len(plan.missing_or_changed_action_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend_required':plan.full_resend_required}
print(json.dumps(out,ensure_ascii=False,sort_keys=True))
