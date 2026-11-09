import json,time,statistics
from dataclasses import replace
import noepin_al_104_risk_aware_mcts as m
p=m.default_policy(); b=p.binding; e=p.state_epoch
# 5000 typed root branches with deterministic long-horizon simulator summaries.
a=[]
for i in range(500):
    safe=(i%13)!=0
    reward=5.0+(i%97)/100.0
    risk=.05+(i%31)/1000.0
    a.append(m.MCTSAction(f'A{i:05d}',(reward,reward+.1,reward-.1,reward+.05),(risk,risk+.01,max(0,risk-.01),risk),.95,safe,'PASS' if safe else 'HARD_CONSTRAINT','V1',f'F{i}',True,b,e))
a=tuple(a)
q=m.MCTSRequest('BENCH','S0',m.RiskClass.LOW,400,100,2.0,True,b,e)
st=m.prepare_state(q,a,p,binding=b,state_epoch=e); integrity=m.validate_prepared_integrity(st)
full=[]; prep=[]
for _ in range(3):
    t=time.perf_counter(); z=None
    for _j in range(5): z=m.evaluate(q,a,p)
    full.append((time.perf_counter()-t)*1000/5)
    t=time.perf_counter(); z2=None
    for _j in range(5): z2=m.evaluate_prepared(st,integrity_validated=integrity,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_frontier_fingerprint=st.frontier_fingerprint,current_simulator_fingerprint=st.simulator_fingerprint)
    prep.append((time.perf_counter()-t)*1000/5)
ids={x.action_id for x in a[:10]}; a2=tuple(replace(x,risk_samples=tuple(v+.001 for v in x.risk_samples)) if x.action_id in ids else x for x in a)
st2=m.prepare_state(q,a2,p,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
full_bytes=len(m._canon((q,a2,p))); delta_bytes=len(m._canon(d))
out={'condition':'Python stdlib; 500 MCTS action branches with deterministic rollout summaries; 400 simulations; 5 evaluations x 3 batches; prepared verified-result reuse','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':z==z2,'full_bytes':full_bytes,'delta_bytes':delta_bytes,'delta_percent':delta_bytes/full_bytes*100,'missing_records':len(sp.missing_or_changed_action_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required}
print(json.dumps(out,sort_keys=True))
