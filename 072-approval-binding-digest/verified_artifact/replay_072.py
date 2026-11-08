from dataclasses import replace
from hashlib import sha256
import json
from noepin_al_072_approval_binding_digest import *
NOW=1_800_000_000

def run_once():
    rows=[]
    for i in range(1000):
        p=default_policy(NOW); r=default_request(NOW); a=default_authorities(); k=default_keys(NOW); rr=()
        ap=(reference_approval(r,issued_at=NOW),); aid='APR-72'
        m=i%6
        if m==1: r=replace(r,action='READ')
        elif m==2: ap=(replace(ap[0],mac_hex='00'*32),)
        elif m==3: rr=(ReplayReceipt(ap[0].approval_digest,r.nonce,'APPROVAL-BIND'),)
        elif m==4: aid=None
        elif m==5:
            z=evaluate(r,aid,p,ap,a,k,rr,current_policy_fingerprint=r.policy_fingerprint,now=NOW+301)
            rows.append((z.decision.value,z.reasons,z.request_fingerprint,z.approval_digest,z.next_gate_candidate,z.atomic_publish_candidate,z.permission_granted,z.action_success)); continue
        z=evaluate(r,aid,p,ap,a,k,rr,current_policy_fingerprint=r.policy_fingerprint,now=NOW)
        rows.append((z.decision.value,z.reasons,z.request_fingerprint,z.approval_digest,z.next_gate_candidate,z.atomic_publish_candidate,z.permission_granted,z.action_success))
    b=json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode(); return sha256(b).hexdigest()

d=[run_once() for _ in range(3)]
out={'schema':'NOEPIN_AL_REPLAY_V1','technology':72,'cases_per_batch':1000,'batches':3,'total':3000,'digests':d,'digest':d[0],'divergence':sum(x!=d[0] for x in d)}
print(json.dumps(out,ensure_ascii=False,sort_keys=True))
