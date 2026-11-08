from dataclasses import replace
import json,statistics,time
from noepin_al_075_latent_goal_inference_guard import *
p=default_policy(); b=p.binding; ep=p.state_epoch
goals=[]; effects=[]; actions=[]
for i in range(1500):
    tag=f'T{i:04d}'; eid=f'E{i:04d}'; aid=f'A{i:04d}'; gid=f'G{i:04d}'
    effects.append(EffectSpec(eid,(tag,),True,1,b,ep)); actions.append(ActionSpec(aid,(eid,),True,b,ep)); goals.append(GoalSpec(gid,(tag,),(),False,b,ep))
q=LatentGoalRequest('BENCH-75','benchmark',tuple(f'A{i:04d}' for i in range(10)),'G0000',b,ep)
st=prepare_state(p,goals,effects,actions,(),binding=b); valid=validate_prepared_integrity(st)
full=[]; prep=[]; sem=True
for _ in range(5):
    t=time.perf_counter(); z1=None
    for __ in range(10): z1=evaluate(q,p,goals,effects,actions,())
    full.append((time.perf_counter()-t)*1000)
    t=time.perf_counter(); z2=None
    for __ in range(10): z2=evaluate_prepared(q,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=valid)
    prep.append((time.perf_counter()-t)*1000)
    sem &= (z1.decision==z2.decision and z1.reasons==z2.reasons and z1.top_goal_id==z2.top_goal_id and z1.goal_distance==z2.goal_distance)
goals2=list(goals)
for i in range(10): goals2[i]=replace(goals2[i],high_impact=True)
st2=prepare_state(p,goals2,effects,actions,(),binding=b); d=make_delta(st,st2)
rg=dict(st2.goal_fingerprints); re=dict(st2.effect_fingerprints); ra=dict(st2.action_fingerprints); rp=dict(st2.approval_fingerprints)
for i in range(10): rg.pop(f'G{i:04d}')
plan=missing_only_sync_plan(st2,rg,re,ra,rp)
out={'schema':'NOEPIN_AL_BENCHMARK_V1','technology':75,'condition':'Python stdlib; 1500 GoalSpec + 1500 EffectSpec + 1500 ActionSpec; 10 evaluations x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':sem,'full_bytes':full_registry_bytes(st2),'delta_bytes':delta_bytes(d),'delta_percent':delta_bytes(d)/full_registry_bytes(st2)*100,'missing_goals':len(plan.missing_or_changed_goals),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend_required':plan.full_resend_required}
print(json.dumps(out,ensure_ascii=False,sort_keys=True))
