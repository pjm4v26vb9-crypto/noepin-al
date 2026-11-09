import json,time,statistics
from dataclasses import replace
import noepin_al_123_byzantine_resilient_agent_quorum as m
b='BENCH'; e='EPOCH-B'
# 1200 agents across 400 independent trust domains; every domain agrees internally.
ds=tuple(m.AgentDecision(f'A{i:04d}',f'DOMAIN-{i%400:04d}',f'CHOICE-{(i%400)%3}',.55+(i%40)/100,.60+(i%35)/100,f'SIG-{i:04d}',True,b,e) for i in range(1200))
q=m.QuorumRequest('BENCH-123',ds,m.QuorumPolicy(50,.4,.4,True),b,e)
full=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(5): m.evaluate(q)
    full.append((time.perf_counter()-t)*1000/5)
st=m.prepare_state(q,binding=b,state_epoch=e); prep=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(20): m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_decision_fingerprint=st.decision_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)
    prep.append((time.perf_counter()-t)*1000/20)
xs=list(ds); xs[10]=replace(xs[10],evidence_quality=max(.4,xs[10].evidence_quality-.05)); q2=replace(q,decisions=tuple(xs)); st2=m.prepare_state(q2,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
full_bytes=len(m._canon(q2)); delta_bytes=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 1200 agent decisions across 400 trust domains; Byzantine-style 2f+1 independent-domain quorum with signature evidence and domain deduplication; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':full_bytes,'delta_bytes':delta_bytes,'delta_percent':delta_bytes/full_bytes*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required},sort_keys=True))
