import json,time,statistics
from dataclasses import replace
import noepin_al_101_claim_provenance_score_aggregator as m
p=m.default_policy(); q=m.default_request(); b=p.binding; e=p.state_epoch
nodes=[]
for i in range(5000):
    nodes.append(m.ProvenanceNode(f'S{i}',m.NodeKind.SOURCE,(),.85+(i%10)*.01,1.0,f'G{i}',f'V{i}',f'F{i}',True,b,e))
nodes.append(m.ProvenanceNode('C-A',m.NodeKind.CLAIM,tuple(f'S{i}' for i in range(5000)),1,1,'','CV','CF',True,b,e))
nodes=tuple(nodes)
st=m.prepare_state(q,nodes,p,binding=b,state_epoch=e); integrity=m.validate_prepared_integrity(st)
full=[]; prep=[]
for _ in range(5):
    t=time.perf_counter(); z=None
    for _j in range(10): z=m.evaluate(q,nodes,p)
    full.append((time.perf_counter()-t)*1000/10)
    t=time.perf_counter(); z2=None
    for _j in range(10): z2=m.evaluate_prepared(st,integrity_validated=integrity,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint)
    prep.append((time.perf_counter()-t)*1000/10)
# DCSR delta: 10 source changes
nodes2=tuple(replace(n,source_trust=max(0,n.source_trust-.1)) if n.node_id in {f'S{i}' for i in range(10)} else n for n in nodes)
st2=m.prepare_state(q,nodes2,p,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
full_bytes=len(m._canon((q,nodes2,p))); delta_bytes=len(m._canon(d))
out={'condition':'Python stdlib; 5000 Source roots + Claim node; provenance DAG aggregation; 10 evaluations x 5 batches; prepared verified-result reuse','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':z==z2,'full_bytes':full_bytes,'delta_bytes':delta_bytes,'delta_percent':delta_bytes/full_bytes*100,'missing_records':len(sp.missing_or_changed_node_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required}
print(json.dumps(out,sort_keys=True))
