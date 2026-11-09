import json,time,statistics
from dataclasses import replace
import noepin_al_129_conflict_resolution_equilibrium_selector as m
b='BENCH'; e='EPOCH-B'; agents=[f'AGENT-{i:02d}' for i in range(24)]; props=[]
for i in range(240):
    utils=tuple(m.AgentUtility(a,.44+((i*7+j*11)%50)/100) for j,a in enumerate(agents))
    props.append(m.Proposal(f'P{i:04d}',agents[i%24],utils,.05+(i%20)/100,.70+(i%25)/100,True,True,b,e))
q=m.EquilibriumRequest('BENCH-129',tuple(props),m.SharedGoal('G',True,.40,.40,b,e),m.default_policy(),b,e)
full=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(5): m.evaluate(q)
    full.append((time.perf_counter()-t)*1000/5)
st=m.prepare_state(q,binding=b,state_epoch=e); prep=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(20): m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_proposal_fingerprint=st.proposal_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)
    prep.append((time.perf_counter()-t)*1000/20)
ps=list(props); ps[-1]=replace(ps[-1],risk=.06); q2=replace(q,proposals=tuple(ps)); st2=m.prepare_state(q2,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
full_bytes=len(m._canon(q2)); delta_bytes=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 240 proposals x 24 agent utilities; hard safety filters + Pareto/Nash-like equilibrium selection; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':full_bytes,'delta_bytes':delta_bytes,'delta_percent':delta_bytes/full_bytes*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required},sort_keys=True))
