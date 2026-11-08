from __future__ import annotations
import json
from hashlib import sha256
import noepin_al_048_tool_chain as m
NOW=1_800_000_000

def dataset():
    p=m.default_policy(NOW); out=[]
    for i in range(100):
        b=f"R-{i%9}"; nodes=[]; edges=[]; size=2+i%5
        for j in range(size):
            if j==0: n=m.ToolNode(f"N{j}","LOCAL_READ","READ",frozenset({"READ_INTERNAL"}),frozenset(),frozenset({"INTERNAL"}),False,False,b)
            else: n=m.ToolNode(f"N{j}","LOCAL_TRANSFORM","TRANSFORM",frozenset({"TRANSFORM"}),frozenset({"INTERNAL"}),frozenset({"INTERNAL"}),False,False,b)
            nodes.append(n)
            if j: edges.append(m.ToolEdge(f"E{j-1}",f"N{j-1}",f"N{j}",frozenset({"INTERNAL"}),b))
        if i%10==0:
            nodes[0]=m.ToolNode("N0","LOCAL_READ","READ",frozenset({"READ_SECRET"}),frozenset(),frozenset({"SECRET"}),False,False,b)
            nodes[-1]=m.ToolNode(f"N{size-1}","EXTERNAL_API","CALL",frozenset({"EXTERNAL_SEND"}),frozenset({"SECRET"}),frozenset(),True,False,b)
            if edges: edges[-1]=m.ToolEdge(edges[-1].edge_id,edges[-1].source_id,edges[-1].target_id,frozenset({"SECRET"}),b)
        elif i%7==0:
            nodes[-1]=m.ToolNode(f"N{size-1}","LOCAL_STORE","STORE",frozenset({"WRITE_PRODUCTION"}),frozenset({"INTERNAL"}),frozenset(),False,True,b)
        g=m.PlanGraph(f"P-{i}","REPLAY",b,tuple(nodes),tuple(edges)); r=m.InspectionRequest(f"Q-{i}",g.plan_id,g.purpose,b,p.policy_id,p.version,p.authority_epoch)
        out.append((r,p,g))
    return tuple(out)

def run():
    ds=dataset(); dig=[]
    for _ in range(3):
        vals=[]
        for k in range(10):
            for r,p,g in ds:
                vals.append(m.evaluate(r,p,g,now=NOW))
        dig.append(m.assessment_digest(vals))
    return {"runs":3,"evaluations_per_run":1000,"total_evaluations":3000,"digests":dig,"divergence":len(set(dig))-1,"digest":dig[0]}
if __name__=='__main__': print(json.dumps(run(),ensure_ascii=False,sort_keys=True))
