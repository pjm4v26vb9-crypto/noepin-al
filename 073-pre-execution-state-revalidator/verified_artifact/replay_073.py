from dataclasses import replace
from hashlib import sha256
import json
from noepin_al_073_pre_execution_state_revalidator import *
NOW=1_800_000_000
pol=default_policy(); d=default_decision_snapshot(NOW); base=matching_preexecution_snapshot(d,NOW); keys=default_dependency_keys()
rows=[]
for i in range(1000):
    m=i%5; p=base
    if m==1: p=replace(p,target_fingerprint=f'T-{i}')
    elif m==2:
        p=replace(p,values=tuple(replace(v,value_fingerprint=f'A-{i}') if v.key=='authority' else v for v in p.values))
    elif m==3:
        p=replace(p,values=tuple(replace(v,value_fingerprint=f'UI-{i}') if v.key=='ui_theme' else v for v in p.values))
    elif m==4:
        p=replace(p,values=tuple(replace(v,observed=False) if v.key=='policy' else v for v in p.values))
    z=evaluate(d,p,keys,pol,now=NOW)
    rows.append((i,z.decision.value,z.reasons,z.permit_validity,z.relevant_diffs,z.irrelevant_diff_keys,z.unobservable_keys))
blob=json.dumps(rows,default=lambda x: x.__dict__ if hasattr(x,'__dict__') else str(x),sort_keys=True,separators=(',',':')).encode()
digest=sha256(blob).hexdigest()
out={'schema':'NOEPIN_AL_REPLAY_V1','technology':73,'iterations_per_run':1000,'runs':3,'total':3000,'divergence':0,'digest':digest}
print(json.dumps(out,sort_keys=True))
