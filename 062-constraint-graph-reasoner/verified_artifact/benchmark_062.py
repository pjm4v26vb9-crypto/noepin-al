from __future__ import annotations
import json,statistics,sys,time
from dataclasses import replace
from pathlib import Path
import noepin_al_062_constraint_graph_reasoner as m
NOW=1_800_000_000

def big_graph(count=3000):
    p=m.default_policy(NOW); g=m.default_graph(NOW,p); ns=list(g.nodes); es=list(g.edges)
    for i in range(count):
        ns.append(m.ConstraintNode(f'ISO-{i:05d}',m.NodeKind.CONSTRAINT,m.NodeState.SATISFIED,False,True,False,g.binding,p.policy_id,p.version,p.authority_epoch,NOW-60,NOW+3600,0,False,f'constraint-{i}'))
        es.append(m.ConstraintEdge(f'X-{i:05d}','ACTION','TARGET',m.EdgeKind.ALLOWS,False,True,False,g.binding))
    return p,replace(g,nodes=tuple(ns),edges=tuple(es))

def main():
    out=Path(sys.argv[1] if len(sys.argv)>1 else 'BENCHMARK_RESULT.json'); p,g=big_graph(1500); r=m.default_request(NOW,p); prep=m.prepare_graph(p,g,now=NOW); assert m.validate_prepared_state(prep); gf=m.graph_fingerprint(g); full=[]; pr=[]; sem=True
    reqs=[replace(r,request_id=f'REQ-{i:03d}') for i in range(12)]
    for _ in range(5):
        t=time.perf_counter(); a=[m.evaluate(x,p,g,now=NOW) for x in reqs]; full.append((time.perf_counter()-t)*1000)
        t=time.perf_counter(); b=[m.evaluate_prepared(x,p,prep,current_graph_fingerprint=gf,now=NOW) for x in reqs]; pr.append((time.perf_counter()-t)*1000)
        sem=sem and all(m.canonical_json(x)==m.canonical_json(y) for x,y in zip(a,b))
    p2,bg=big_graph(2000); nodes=list(bg.nodes); edges=list(bg.edges)
    # Change 50 isolated nodes and 50 ALLOWS edges; remove/add 5 of each without overlap.
    for i in range(100,150):
        for j,n in enumerate(nodes):
            if n.node_id==f'ISO-{i:05d}': nodes[j]=replace(n,label=f'changed-{i}'); break
        for j,e in enumerate(edges):
            if e.edge_id==f'X-{i:05d}': edges[j]=replace(e,hard=True); break
    nodes=[n for n in nodes if n.node_id not in {f'ISO-{i:05d}' for i in range(5)}]
    edges=[e for e in edges if e.edge_id not in {f'X-{i:05d}' for i in range(5)}]
    for i in range(2000,2005):
        nodes.append(m.ConstraintNode(f'ISO-{i:05d}',m.NodeKind.CONSTRAINT,m.NodeState.SATISFIED,False,True,False,bg.binding,p2.policy_id,p2.version,p2.authority_epoch,NOW-60,NOW+3600,0,False,f'added-{i}'))
        edges.append(m.ConstraintEdge(f'X-{i:05d}','ACTION','TARGET',m.EdgeKind.ALLOWS,False,True,False,bg.binding))
    tg=replace(bg,nodes=tuple(nodes),edges=tuple(edges)); d=m.make_graph_delta(bg,tg); rg=m.apply_graph_delta(bg,d)
    full_bytes=len(m.canonical_json(tg).encode()); delta_bytes=len(m.canonical_json(d).encode()); treg=m.prepare_graph(p2,tg,now=NOW); rn=dict(treg.node_fingerprints); re=dict(treg.edge_fingerprints)
    for k in sorted(rn)[:10]: rn.pop(k)
    for k in sorted(re)[:10]: re.pop(k)
    sync=m.plan_graph_sync(tg,rn,re)
    obj={'schema':'NOEPIN_AL_BENCHMARK_RESULT_V1','technology':62,'condition':{'extra_nodes':1500,'extra_edges':1500,'evaluations_per_batch':12,'batches':5,'runtime':'Python standard library'},'full_materialization_median_ms':statistics.median(full),'prepared_graph_median_ms':statistics.median(pr),'semantic_match':sem,'delta':{'base_nodes':len(bg.nodes),'base_edges':len(bg.edges),'target_nodes':len(tg.nodes),'target_edges':len(tg.edges),'changed_nodes':len(d.changed_nodes),'changed_edges':len(d.changed_edges),'removed_nodes':len(d.removed_node_ids),'removed_edges':len(d.removed_edge_ids),'added_nodes':len(d.added_nodes),'added_edges':len(d.added_edges),'full_bytes':full_bytes,'delta_bytes':delta_bytes,'ratio_percent':(delta_bytes/full_bytes*100 if full_bytes else 0),'reconstruction_fingerprint_match':m.graph_fingerprint(rg)==m.graph_fingerprint(tg)},'sync':{'target_records':len(tg.nodes)+len(tg.edges),'remote_known':len(tg.nodes)+len(tg.edges)-20,'missing_or_changed_nodes':len(sync.missing_or_changed_node_ids),'missing_or_changed_edges':len(sync.missing_or_changed_edge_ids),'metadata_bytes_required':sync.metadata_bytes_required,'full_resend_required':sync.full_resend_required,'permission_granted':sync.permission_granted,'action_execution_authorized':sync.action_execution_authorized,'graph_truth_authorized':sync.graph_truth_authorized,'action_success_authorized':sync.action_success_authorized}}
    out.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n'); print(json.dumps(obj,sort_keys=True))
if __name__=='__main__': main()
