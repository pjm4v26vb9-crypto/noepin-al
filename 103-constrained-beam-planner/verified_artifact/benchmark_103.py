import json,time,statistics
from dataclasses import replace
import noepin_al_103_constrained_beam_planner as m
p=m.default_policy(); b=p.binding; e=p.state_epoch
# ~5000 generated Beam actions; each depth contains safe choices and hard-constraint decoys.
a=[]; DEPTH=32; WIDTH=12
for d in range(DEPTH):
    sources=['S0'] if d==0 else [f'N{d}_{j}' for j in range(WIDTH)]
    for si,src in enumerate(sources):
        for j in range(WIDTH):
            dst='GOAL' if d==DEPTH-1 else f'N{d+1}_{j}'
            a.append(m.BeamAction(f'S{d:03d}_{si:02d}_{j:02d}',src,dst,1.0+j/10000,.0005+(j%5)*.00001,.8+(j%4)*.05,True,'PASS','V1',f'FS{d}_{si}_{j}',True,b,e))
            if j==0: a.append(m.BeamAction(f'X{d:03d}_{si:02d}',src,dst,50,5,.1,False,'HARD_CONSTRAINT','V1',f'FX{d}_{si}',True,b,e))
a=tuple(a)
q=m.BeamRequest('BENCH','S0','GOAL',m.RiskClass.LOW,8,DEPTH,10,1,True,b,e); p=replace(p,max_generated_candidates=200000,low_risk_cap=10)
st=m.prepare_state(q,a,p,binding=b,state_epoch=e); integrity=m.validate_prepared_integrity(st)
full=[]; prep=[]
for _ in range(5):
    t=time.perf_counter(); z=None
    for _j in range(10): z=m.evaluate(q,a,p)
    full.append((time.perf_counter()-t)*1000/10)
    t=time.perf_counter(); z2=None
    for _j in range(10): z2=m.evaluate_prepared(st,integrity_validated=integrity,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_frontier_fingerprint=st.frontier_fingerprint,current_rank_fingerprint=st.rank_fingerprint)
    prep.append((time.perf_counter()-t)*1000/10)
ids={x.action_id for x in a[:10]}; a2=tuple(replace(x,risk_cost=x.risk_cost+.0001) if x.action_id in ids and x.hard_constraint_passed else x for x in a)
st2=m.prepare_state(q,a2,p,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
full_bytes=len(m._canon((q,a2,p))); delta_bytes=len(m._canon(d))
out={'condition':'Python stdlib; ~4800 constrained Beam actions with hard-constraint decoys; 10 evaluations x 5 batches; prepared verified-result reuse','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':z==z2,'full_bytes':full_bytes,'delta_bytes':delta_bytes,'delta_percent':delta_bytes/full_bytes*100,'missing_records':len(sp.missing_or_changed_action_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required}
print(json.dumps(out,sort_keys=True))
