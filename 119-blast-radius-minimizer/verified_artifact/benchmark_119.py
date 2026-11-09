import json,time,statistics
from dataclasses import replace
import noepin_al_119_blast_radius_minimizer as m
b='BENCH-BIND'; e='BENCH-EPOCH'; resources=[]; edges=[]; candidates=[]
for i in range(1800):
    resources.append(m.ResourceNode(f'R{i:04d}',1+(i%7)*.25,i%17==0,i%41==0,b,e))
for i in range(1790):
    if i%3==0: edges.append(m.DependencyEdge(f'R{i:04d}',f'R{i+1:04d}'))
    if i%11==0: edges.append(m.DependencyEdge(f'R{i:04d}',f'R{i+3:04d}'))
for i in range(1200):
    candidates.append(m.CandidateAction(f'A{i:04d}',(f'R{i%1600:04d}',),1.0,i%29==0,b,e))
p=m.BlastPolicy(.9,1.75,2.0,1.10,30.0,5000); q=m.BlastRequest('BENCH-119',tuple(candidates),tuple(resources),tuple(edges),'GOAL',p,b,e)
st=m.prepare_state(q,binding=b,state_epoch=e); integrity=m.validate_prepared_integrity(st)
full=[]; prep=[]; z=z2=None
for _ in range(5):
    t=time.perf_counter()
    for _j in range(5): z=m.evaluate(q)
    full.append((time.perf_counter()-t)*1000/5)
    t=time.perf_counter()
    for _j in range(20): z2=m.evaluate_prepared(st,integrity_validated=integrity,current_context_fingerprint=st.context_fingerprint,current_candidate_fingerprint=st.candidate_fingerprint,current_resource_fingerprint=st.resource_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_selection_fingerprint=st.selection_fingerprint)
    prep.append((time.perf_counter()-t)*1000/20)
changed=[replace(x,goal_coverage=.95 if x.goal_coverage==1 else 1) for x in candidates[:10]]
q2=replace(q,candidates=tuple(changed)+tuple(candidates[10:])); st2=m.prepare_state(q2,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
full_bytes=len(m._canon(q2)); delta_bytes=len(m._canon(d))
out={'condition':'Python stdlib; 1200 candidate actions; 1800 resources; dependency reachability + weighted critical/shared/authority set-size minimization; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':z==z2,'full_bytes':full_bytes,'delta_bytes':delta_bytes,'delta_percent':delta_bytes/full_bytes*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required}
print(json.dumps(out,sort_keys=True))
