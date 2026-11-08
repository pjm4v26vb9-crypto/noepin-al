from __future__ import annotations
import dataclasses,json,time,statistics
import noepin_al_048_tool_chain as m
NOW=1_800_000_000

def make_graph(n=400):
    b='BENCH-48'; nodes=[]; edges=[]
    for i in range(n):
        if i==0: nodes.append(m.ToolNode(f'N{i}','LOCAL_READ','READ',frozenset({'READ_INTERNAL'}),frozenset(),frozenset({'INTERNAL'}),False,False,b))
        elif i==n-1: nodes.append(m.ToolNode(f'N{i}','LOCAL_STORE','STORE',frozenset({'STORE_LOCAL'}),frozenset({'INTERNAL'}),frozenset(),False,True,b))
        else: nodes.append(m.ToolNode(f'N{i}','LOCAL_TRANSFORM','TRANSFORM',frozenset({'TRANSFORM'}),frozenset({'INTERNAL'}),frozenset({'INTERNAL'}),False,False,b))
        if i: edges.append(m.ToolEdge(f'E{i-1}',f'N{i-1}',f'N{i}',frozenset({'INTERNAL'}),b))
    return m.PlanGraph('BENCH-P','BENCH',b,tuple(nodes),tuple(edges))

def main():
    p=m.default_policy(NOW); g=make_graph(); r=m.InspectionRequest('BENCH-R',g.plan_id,g.purpose,g.evidence_binding,p.policy_id,p.version,p.authority_epoch); pr=m.prepare_graph(p,g,now=NOW)
    full=[]; prep=[]
    for _ in range(5):
        t=time.perf_counter()
        for _ in range(10): m.evaluate(r,p,g,now=NOW)
        full.append((time.perf_counter()-t)*1000)
        t=time.perf_counter()
        for _ in range(10): m.evaluate_prepared(r,p,g,pr,now=NOW)
        prep.append((time.perf_counter()-t)*1000)
    base=make_graph(2000)
    nodes=list(base.nodes); edges=list(base.edges)
    for i in range(50): nodes[i]=dataclasses.replace(nodes[i],produces_labels=frozenset({'INTERNAL','TAG'+str(i)}))
    removed={f'N{i}' for i in range(100,105)}; nodes=[x for x in nodes if x.node_id not in removed]; edges=[e for e in edges if e.source_id not in removed and e.target_id not in removed]
    for i in range(5): nodes.append(m.ToolNode(f'NX{i}','LOCAL_STORE','STORE',frozenset({'STORE_LOCAL'}),frozenset({'INTERNAL'}),frozenset(),False,True,'BENCH-48'))
    target=m.PlanGraph(base.plan_id,base.purpose,base.evidence_binding,tuple(nodes),tuple(edges)); d=m.build_graph_delta(base,target); rebuilt=m.apply_graph_delta(base,d)
    prt=m.prepare_graph(p,target,now=NOW); kn=dict(prt.node_fingerprints); ke=dict(prt.edge_fingerprints)
    for k in sorted(kn)[-5:]: kn.pop(k)
    for k in sorted(ke)[-5:]: ke.pop(k)
    sync=m.plan_graph_sync(prt,kn,ke)
    full_bytes=len(m.canonical_json(target).encode()); delta_bytes=len(m.canonical_json(d).encode())
    out={"condition":"400 nodes; 10 evaluations per batch; 5 batches; Python standard library","full_materialization_median_ms":statistics.median(full),"prepared_graph_median_ms":statistics.median(prep),"semantic_match":m.evaluate(r,p,g,now=NOW)==m.evaluate_prepared(r,p,g,pr,now=NOW),"delta":{"base_nodes":2000,"changed_nodes":len(d.changed_nodes),"removed_nodes":len(d.removed_node_ids),"added_nodes":len(d.added_nodes),"changed_edges":len(d.changed_edges),"removed_edges":len(d.removed_edge_ids),"added_edges":len(d.added_edges),"full_bytes":full_bytes,"delta_bytes":delta_bytes,"ratio_percent":100*delta_bytes/full_bytes,"reconstruction_fingerprint_match":m.graph_fingerprint(rebuilt)==m.graph_fingerprint(target)},"sync":{"missing_nodes":len(sync.missing_or_changed_node_ids),"missing_edges":len(sync.missing_or_changed_edge_ids),"metadata_bytes_required":sync.metadata_bytes_required,"full_resend_required":sync.full_resend_required,"permission_granted":sync.permission_granted,"tool_execution_authorized":sync.tool_execution_authorized,"data_transfer_authorized":sync.data_transfer_authorized}}
    print(json.dumps(out,ensure_ascii=False,sort_keys=True))
if __name__=='__main__': main()
