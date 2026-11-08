import json, random
from dataclasses import replace
import noepin_al_038_memory_governor as m

p=m.MemoryPolicy("p1",2,7,frozenset({"assist","care"}),3600,86400,delete_requires_human=True)
r=m.MemoryRecordMeta("mem1",100,1000,frozenset({"assist"}),"INTERNAL","p1",2,7)

def run(seed=38,n=1000):
    random.seed(seed)
    vals=[]
    for i in range(n):
        op=random.choice(["USE","RETAIN","DELETE","STORE"])
        purpose=random.choice(["assist","care","ads"])
        now=random.choice([500,999,1000,1200])
        q=m.MemoryRequest(op,purpose,now,requested_retention_seconds=random.choice([0,100,1200,90000]),classification="INTERNAL",human_approval_evidence=bool(i%3==0),subject_deletion_request=bool(i%17==0))
        vals.append(m.evaluate(p,q,None if op=="STORE" else r))
    return m.decision_digest(vals)

vals=[run(38,1000) for _ in range(3)]
print(json.dumps({"runs":3,"evaluations":3000,"digests":vals,"divergence":len(set(vals))-1,"status":"PASS" if len(set(vals))==1 else "FAIL"},sort_keys=True))
