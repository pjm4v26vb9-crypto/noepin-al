from dataclasses import replace
from hashlib import sha256
import json
from noepin_al_069_dependency_order_verifier import *
NOW=1_800_000_000

def case(i):
    p=default_policy(NOW); a=default_actions(); o=default_observations(); f=default_forbidden_orders(); r=default_request(NOW); m=i%5
    if m==1: r=replace(r,action_sequence=("A-APPLY","A-VERIFY","A-CLEANUP"))
    elif m==2: r=replace(r,action_sequence=("A-APPLY","A-SNAPSHOT","A-VERIFY","A-CLEANUP"))
    elif m==3: r=replace(r,action_sequence=("A-SNAPSHOT","A-APPLY","A-CLEANUP","A-VERIFY"))
    elif m==4: o=tuple(replace(x,known=False) if x.predicate.name=="workspace_ready" else x for x in o)
    return r,p,a,o,f

def row(z):
    return (z.decision.value,z.reasons,z.legal_order,z.violating_actions,z.unmet_dependencies,z.unknown_dependencies,z.cycle_nodes,z.forbidden_violations,z.reorder_required,z.next_gate_candidate)

def run():
    rows=[]
    for i in range(1000):
        r,p,a,o,f=case(i); rows.append(row(evaluate(r,p,a,o,f,now=NOW)))
    digest=sha256(json.dumps(rows,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest(); div=0
    for _ in range(2):
        rows2=[]
        for i in range(1000):
            r,p,a,o,f=case(i); rows2.append(row(evaluate(r,p,a,o,f,now=NOW)))
        d2=sha256(json.dumps(rows2,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest(); div += 0 if d2==digest else 1
    return {'schema':'NOEPIN_AL_REPLAY_RESULT_V1','technology':69,'runs':3,'cases_per_run':1000,'total':3000,'divergence':div,'digest':digest}
if __name__=='__main__': print(json.dumps(run(),ensure_ascii=False,sort_keys=True))
