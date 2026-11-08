from dataclasses import replace
from hashlib import sha256
import json
from noepin_al_081_postcondition_auditor import *

base=(default_request(),default_intent(),default_permit(),default_receipt(),default_policy(),default_conditions(),default_observed_state(),default_diff())
digests=[]
for run in range(3):
    rows=[]
    for n in range(1000):
        q,i,p,r,pol,c,s,d=base; m=n%8
        if m==0: pass
        elif m==1: s=(s[0],replace(s[1],value='bad'),s[2])
        elif m==2: s=(s[0],replace(s[1],observed=False),s[2])
        elif m==3: d=d+(DiffEffect('D-X','outside',None,'x',True,False,Severity.CRITICAL,pol.binding,pol.state_epoch),)
        elif m==4: d=d+(DiffEffect('D-X','outside',None,'x',True,False,Severity.HIGH,pol.binding,pol.state_epoch),)
        elif m==5: q=replace(q,diff_complete=False)
        elif m==6: p=replace(p,valid=False)
        else: r=replace(r,claimed_success=False)
        z=evaluate(q,i,p,r,pol,c,s,d)
        rows.append((n,z.decision.value,z.success_state.value,z.reasons,z.unmet_conditions,z.unexpected_effects,z.coverage,z.next_gate_candidate,z.rollback_candidate,z.atomic_publish_candidate))
    blob=json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode(); digests.append(sha256(blob).hexdigest())
out={'schema':'NOEPIN_AL_REPLAY_V1','technology':81,'iterations_per_run':1000,'runs':3,'total':3000,'divergence':len(set(digests))-1,'digest':digests[0]}
print(json.dumps(out,sort_keys=True))
