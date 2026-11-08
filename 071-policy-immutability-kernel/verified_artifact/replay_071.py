from dataclasses import replace
from hashlib import sha256
import json
from noepin_al_071_policy_immutability_kernel import *
NOW=1_800_000_000

def run_once():
    rows=[]
    for i in range(1000):
        m=i%5; p=default_kernel_policy(NOW); c=default_snapshot(); a=default_authorities(); v=default_versions()
        if m==0:
            r=default_request(NOW); s=(signature_for(r,c,now=NOW),)
        elif m==1:
            r=replace(default_request(NOW),actor_id="AGENT-1"); s=(signature_for(r,c,now=NOW),)
        elif m==2:
            r=replace(default_request(NOW),expected_version=6); s=(signature_for(r,c,now=NOW),)
        elif m==3:
            r=default_request(NOW); s=(replace(signature_for(r,c,now=NOW),verified=False),)
        else:
            r=ChangeRequest(f"RB{i}","SECURITY-ADMIN",7,"hash-v3","ROLLBACK",3,"SIG-71",NOW,"POL-BIND","POL-EPOCH"); s=(signature_for(r,c,candidate_hash="hash-v3",signer_id="SECURITY-ADMIN",now=NOW),)
        z=evaluate(r,p,c,a,s,v,now=NOW)
        rows.append((z.decision.value,z.reasons,z.current_version,z.proposed_version,z.candidate_policy_hash,z.next_gate_candidate,z.policy_update_committed,z.action_success))
    b=json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode(); return sha256(b).hexdigest()

d=[run_once() for _ in range(3)]
out={"schema":"NOEPIN_AL_REPLAY_V1","technology":71,"cases_per_batch":1000,"batches":3,"total":3000,"digests":d,"digest":d[0],"divergence":sum(x!=d[0] for x in d)}
print(json.dumps(out,ensure_ascii=False,sort_keys=True))
