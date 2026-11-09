import json,time,statistics
from dataclasses import replace
import noepin_al_131_distributed_deadlock_breaker as m
b='BENCH'; e='EPOCH-B'
# 1200 agents arranged into 400 independent 3-agent cycles.
edges=[]; locks=[]; ps=[]
for i in range(400):
    a=f'A{i:04d}'; c=f'B{i:04d}'; d=f'C{i:04d}'
    ra=f'RA{i:04d}'; rb=f'RB{i:04d}'; rc=f'RC{i:04d}'
    edges += [m.WaitEdge(a,c,rb,'RESOURCE',b,e),m.WaitEdge(c,d,rc,'APPROVAL',b,e),m.WaitEdge(d,a,ra,'OUTPUT',b,e)]
    locks += [m.ResourceLock(ra,a,False,True,.25,b,e),m.ResourceLock(rb,c,False,True,.30,b,e),m.ResourceLock(rc,d,False,True,.20,b,e)]
    ps += [m.AgentPriority(a,60,.25,.25,b,e),m.AgentPriority(c,50,.20,.30,b,e),m.AgentPriority(d,20,.15,.20,b,e)]
q=m.DeadlockRequest('BENCH-131',tuple(edges),tuple(locks),tuple(ps),1,m.default_policy(),b,e)
full=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(5): m.evaluate(q)
    full.append((time.perf_counter()-t)*1000/5)
st=m.prepare_state(q,binding=b,state_epoch=e); prep=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(20): m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_wait_fingerprint=st.wait_fingerprint,current_lock_fingerprint=st.lock_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)
    prep.append((time.perf_counter()-t)*1000/20)
ll=list(locks); ll[-1]=replace(ll[-1],safe_release=False); q2=replace(q,locks=tuple(ll)); st2=m.prepare_state(q2,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
full_bytes=len(m._canon(q2)); delta_bytes=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 1200 agents / 1200 locks / 1200 wait edges in 400 three-agent cycles; wait-for SCC cycle detection + safe victim/release candidate selection; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':full_bytes,'delta_bytes':delta_bytes,'delta_percent':delta_bytes/full_bytes*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required},sort_keys=True))
