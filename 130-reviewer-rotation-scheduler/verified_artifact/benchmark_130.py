import json,time,statistics
from dataclasses import replace
import noepin_al_130_reviewer_rotation_scheduler as m
b='BENCH'; e='EPOCH-B'; agents=[]
for i in range(1200):
    agents.append(m.ReviewerAgent(f'R{i:04d}',f'F{i%40:02d}',f'P{i%17:02d}',.60+(i%40)/100,True,True,b,e))
history=tuple(m.ReviewEvent('SUBJ',f'R{i%1200:04d}',f'OLD-{i}',i,'FPAIR','PPAIR') for i in range(600))
q=m.RotationRequest('BENCH-130',m.ReviewTask('TASK','SUBJ','F00','P00',m.TaskRisk.CRITICAL,b,e),tuple(agents),history,m.default_rules(),b,e)
full=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(5): m.evaluate(q)
    full.append((time.perf_counter()-t)*1000/5)
st=m.prepare_state(q,binding=b,state_epoch=e); prep=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(20): m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_agent_fingerprint=st.agent_fingerprint,current_history_fingerprint=st.history_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)
    prep.append((time.perf_counter()-t)*1000/20)
aa=list(agents); aa[-1]=replace(aa[-1],available=False); q2=replace(q,agents=tuple(aa)); st2=m.prepare_state(q2,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
full_bytes=len(m._canon(q2)); delta_bytes=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 1200 reviewer agents + 600 review-history records; self-review/conflict/correlation/rotation/fairness filters and deterministic reviewer scheduling; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':full_bytes,'delta_bytes':delta_bytes,'delta_percent':delta_bytes/full_bytes*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required},sort_keys=True))
