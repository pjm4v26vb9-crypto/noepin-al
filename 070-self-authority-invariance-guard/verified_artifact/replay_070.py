from dataclasses import replace
from hashlib import sha256
import json
from noepin_al_070_self_authority_invariance_guard import *
NOW=1_800_000_000
def case(i):
    p=default_policy(NOW); a=default_authorities(); m=i%5
    if m==0: r=default_request(NOW); aps=()
    elif m==1: r=replace(default_request(NOW),requested_capabilities=("READ","WRITE_SCOPED","ADMIN")); aps=()
    elif m==2:
        r=replace(default_request(NOW),requested_capabilities=("READ","WRITE_SCOPED","ADMIN"),approval_id="APR-1"); aps=(approval_for(r,now=NOW),)
    elif m==3:
        r=replace(default_request(NOW),requested_capabilities=("READ","WRITE_SCOPED","ADMIN"),approval_id="APR-1"); aps=(approval_for(r,approver_id="AGENT-1",now=NOW),)
    else: r=replace(default_request(NOW),created_at=NOW-9999); aps=()
    return r,p,a,aps
def row(z): return (z.decision.value,z.reasons,z.added_capabilities,z.removed_capabilities,z.approver_id,z.independent_approval_valid,z.next_gate_candidate)
def run():
    rows=[]
    for i in range(1000):
        r,p,a,aps=case(i); rows.append(row(evaluate(r,p,a,aps,now=NOW)))
    digest=sha256(json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest(); div=0
    for _ in range(2):
        rows2=[]
        for i in range(1000):
            r,p,a,aps=case(i); rows2.append(row(evaluate(r,p,a,aps,now=NOW)))
        d2=sha256(json.dumps(rows2,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()
        div += 0 if d2==digest else 1
    return {"schema":"NOEPIN_AL_REPLAY_RESULT_V1","technology":70,"runs":3,"cases_per_run":1000,"total":3000,"divergence":div,"digest":digest}
if __name__=="__main__": print(json.dumps(run(),sort_keys=True))
