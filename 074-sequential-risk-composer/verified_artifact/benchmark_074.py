from dataclasses import replace
import json,statistics,time
from noepin_al_074_sequential_risk_composer import *
NOW=1_800_000_000
p=default_policy()
a=[]; rules=[]; seq=[]
for i in range(1500):
    aid=f'A{i:04d}'; tag=f'T{i%8}'
    deps=() if i==0 else (f'A{i-1:04d}',)
    a.append(ActionRisk(aid,tag,2+(i%3),NOW-(1499-i),deps,True,'RISK-BIND','STATE-EPOCH-1')); seq.append(aid)
for x in range(8):
    for y in range(8): rules.append(InteractionRule(f'R{x}-{y}',f'T{x}',f'T{y}','ANY',1,False,'RISK-BIND','STATE-EPOCH-1'))
q=RiskRequest('BENCH-74',tuple(seq),5000,NOW,'RISK-BIND','STATE-EPOCH-1')
st=prepare_state(p,a,rules,binding=p.binding); valid=validate_prepared_integrity(st)
full=[]; prep=[]; sem=True
for _ in range(5):
    t=time.perf_counter(); z1=None
    for __ in range(10): z1=evaluate(q,p,a,rules)
    full.append((time.perf_counter()-t)*1000)
    t=time.perf_counter(); z2=None
    for __ in range(10): z2=evaluate_prepared(q,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=valid)
    prep.append((time.perf_counter()-t)*1000)
    sem &= (z1.decision==z2.decision and z1.reasons==z2.reasons and z1.cumulative_risk==z2.cumulative_risk and z1.stop_point==z2.stop_point)
a2=list(a)
for i in range(10): a2[i]=replace(a2[i],base_risk=a2[i].base_risk+1)
st2=prepare_state(p,a2,rules,binding=p.binding); d=make_delta(st,st2)
ra=dict(st2.action_fingerprints); rr=dict(st2.rule_fingerprints)
for i in range(10): ra.pop(f'A{i:04d}')
plan=missing_only_sync_plan(st2,ra,rr)
out={'schema':'NOEPIN_AL_BENCHMARK_V1','technology':74,'condition':'Python stdlib; 1500 ActionRisk + 64 interaction rules; 10 evaluations x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':sem,'full_bytes':full_registry_bytes(st2),'delta_bytes':delta_bytes(d),'delta_percent':delta_bytes(d)/full_registry_bytes(st2)*100,'missing_actions':len(plan.missing_or_changed_actions),'missing_rules':len(plan.missing_or_changed_rules),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend_required':plan.full_resend_required}
print(json.dumps(out,ensure_ascii=False,sort_keys=True))
