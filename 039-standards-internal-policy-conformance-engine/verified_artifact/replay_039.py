from hashlib import sha256
import json
from noepin_al_039_rules_engine import *

NOW=1_800_000_000

def build(i):
    rules=tuple(Rule(rule_id=f"R{j}",source="NIST" if j%2==0 else "INTERNAL",source_version="v1",control_id=f"C{j}",field=f"c{j}",operator=Operator.TRUE,severity=Severity.HIGH if j%7==0 else Severity.MEDIUM) for j in range(12))
    p=RuleProfile("P","1",7,NOW-10,NOW+1000,False,rules)
    attrs={f"c{j}": ((i+j)%11!=0) for j in range(12)}
    q=EvaluationRequest(f"Q{i}","S","AUDIT",attrs,())
    return q,p,[]

def run_once():
    h=sha256()
    for i in range(1000):
        q,p,e=build(i)
        r=evaluate(q,p,e,now=NOW)
        h.update(canonical_json(r).encode())
    return h.hexdigest()

if __name__=="__main__":
    digests=[run_once() for _ in range(3)]
    print(json.dumps({"evaluations":3000,"digests":digests,"divergence":len(set(digests))-1},indent=2))
