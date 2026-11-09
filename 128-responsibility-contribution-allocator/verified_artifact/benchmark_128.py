import json,time,statistics
from dataclasses import replace
import noepin_al_128_responsibility_contribution_allocator as m
b='BENCH'; e='EPOCH-B'; nodes=[]; edges=[]
for i in range(1200):
    role=('ACTION','APPROVAL','PROPOSAL','REVIEW')[i%4]
    nodes.append(m.DecisionNode(f'N{i:04d}',f'AGENT-{i%40:02d}',role,.25+(i%70)/100,b,e))
nodes.append(m.DecisionNode('OUTCOME',None,'OUTCOME',None,b,e))
# Every actor node has a direct causal trace to outcome; deterministic and large enough for throughput comparison.
for i in range(1200): edges.append(m.CausalEdge(f'N{i:04d}','OUTCOME',.20+(i%70)/100,b,e))
q=m.AttributionRequest('BENCH-128',tuple(nodes),tuple(edges),m.OutcomeSpec('OUTCOME',True,'LOW',b,e),m.default_policy(),b,e)
full=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(5): m.evaluate(q)
    full.append((time.perf_counter()-t)*1000/5)
st=m.prepare_state(q,binding=b,state_epoch=e); prep=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(20): m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_graph_fingerprint=st.graph_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)
    prep.append((time.perf_counter()-t)*1000/20)
ns=list(nodes); ns[-2]=replace(ns[-2],counterfactual_effect=.96); q2=replace(q,nodes=tuple(ns)); st2=m.prepare_state(q2,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
full_bytes=len(m._canon(q2)); delta_bytes=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 1200 causal decision/action nodes + 1200 outcome edges across 40 agents; causal path + counterfactual contribution allocation; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':full_bytes,'delta_bytes':delta_bytes,'delta_percent':delta_bytes/full_bytes*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required},sort_keys=True))
