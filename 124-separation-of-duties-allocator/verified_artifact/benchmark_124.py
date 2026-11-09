import json,time,statistics
from dataclasses import replace
import noepin_al_124_separation_of_duties_allocator as m
b='BENCH'; e='EPOCH-B'
roles=[]; agents=[]
conf=(m.ConflictRule('PLANNER','APPROVER'),m.ConflictRule('EXECUTOR','APPROVER'),m.ConflictRule('EXECUTOR','REVIEWER'),m.ConflictRule('PLANNER','REVIEWER'))
# 300 independent tasks x 4 roles = 1200 role requirements; 1200 purpose-specific agents.
for i in range(300):
    tid=f'TASK-{i:04d}'
    for role,cap,trust in [('PLANNER','PLAN',.6),('EXECUTOR','EXECUTE',.65),('APPROVER','APPROVE',.7),('REVIEWER','REVIEW',.65)]:
        roles.append(m.RoleRequirement(tid,role,cap,True,trust))
        agents.append(m.Agent(f'{role}-{i:04d}',(cap,),.90+(i%5)*.01,f'DOMAIN-{role}-{i:04d}',True,role=='APPROVER',b,e))
q=m.AllocationRequest('BENCH-124',tuple(roles),tuple(agents),conf,m.default_policy(),b,e)
full=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(5): m.evaluate(q)
    full.append((time.perf_counter()-t)*1000/5)
st=m.prepare_state(q,binding=b,state_epoch=e); prep=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(20): m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_role_fingerprint=st.role_fingerprint,current_agent_fingerprint=st.agent_fingerprint,current_conflict_fingerprint=st.conflict_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)
    prep.append((time.perf_counter()-t)*1000/20)
xs=list(agents); xs[10]=replace(xs[10],trust=xs[10].trust-.01); q2=replace(q,agents=tuple(xs)); st2=m.prepare_state(q2,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
full_bytes=len(m._canon(q2)); delta_bytes=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 300 tasks / 1200 role requirements / 1200 purpose-specific agents; conflict-matrix separation-of-duties allocation with independent reviewer; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':full_bytes,'delta_bytes':delta_bytes,'delta_percent':delta_bytes/full_bytes*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required},sort_keys=True))
