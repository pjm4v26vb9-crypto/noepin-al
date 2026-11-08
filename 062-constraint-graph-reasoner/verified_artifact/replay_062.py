from __future__ import annotations
import json,sys
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import noepin_al_062_constraint_graph_reasoner as m
NOW=1_800_000_000

def mutate(g,nid,**kw): return replace(g,nodes=tuple(replace(n,**kw) if n.node_id==nid else n for n in g.nodes))
def item(i):
    p=m.default_policy(NOW); g=m.default_graph(NOW,p); r=m.default_request(NOW,p); k=i%10
    if k==1: g=mutate(g,'SCOPE',state=m.NodeState.UNSATISFIED)
    elif k==2: g=mutate(g,'PRE',state=m.NodeState.UNKNOWN)
    elif k==3: g=replace(g,complete=False)
    elif k==4: r=replace(r,expected_policy_version='OLD')
    elif k==5: g=replace(g,edges=g.edges+(m.ConstraintEdge('F','ACTION','TARGET',m.EdgeKind.FORBIDS,True,True,False,g.binding),))
    elif k==6: g=replace(g,edges=g.edges+(m.ConstraintEdge('CY','PRE','ACTION',m.EdgeKind.REQUIRES,False,True,False,g.binding),))
    elif k==7: r=replace(r,high_risk=True)
    elif k==8: g=replace(g,edges=tuple(e for e in g.edges if e.edge_id not in ('E4','E5')))
    elif k==9: g=mutate(g,'SAFE',state=m.NodeState.UNSATISFIED)
    return m.canonical_json(m.evaluate(r,p,g,now=NOW))
def run(n=1000):
    data='\n'.join(item(i) for i in range(n)); return sha256(data.encode()).hexdigest()
def main():
    out=Path(sys.argv[1] if len(sys.argv)>1 else 'REPLAY_RESULT.json'); ds=[run() for _ in range(3)]; obj={'schema':'NOEPIN_AL_REPLAY_RESULT_V1','technology':62,'runs':3,'evaluations_per_run':1000,'total_evaluations':3000,'digests':ds,'digest':ds[0],'divergence':len(set(ds))-1}; out.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n'); print(json.dumps(obj,sort_keys=True))
if __name__=='__main__': main()
