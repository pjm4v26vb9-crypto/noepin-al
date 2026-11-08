from dataclasses import replace
from hashlib import sha256
import json
from noepin_al_080_adversarial_contrarian_verifier import *
q,p,r,c,e=default_request(),default_plan(),default_risk_model(),default_constraints(),default_environment(); digests=[]
for run in range(3):
    rows=[]
    for i in range(1000):
        qq,pp,rr,cc,ee=q,p,r,c,e; m=i%7
        if m==0: pass
        elif m==1:
            a=replace(p.actions[0],effect_tags=('EXTERNAL_WRITE',)); pp=replace(p,actions=(a,p.actions[1]),plan_fingerprint=plan_fingerprint((a,p.actions[1])))
        elif m==2:
            a=replace(p.actions[0],effect_tags=('EXTERNAL_SEND',)); pp=replace(p,actions=(a,p.actions[1]),plan_fingerprint=plan_fingerprint((a,p.actions[1])))
        elif m==3: cc=(replace(c[0],observed=False),c[1],c[2])
        elif m==4: qq=replace(q,constraint_ids=('NOPE',))
        elif m==5: ee=(replace(e[0],observed=False),e[1])
        else:
            a=replace(p.actions[0],effect_tags=('UNBOUNDED_SCAN',)); pp=replace(p,actions=(a,p.actions[1]),plan_fingerprint=plan_fingerprint((a,p.actions[1])))
        z=evaluate(qq,pp,rr,cc,ee); rows.append((i,z.decision.value,z.reasons,z.coverage,z.risk_addition,[(x.counterexample_id,x.severity.value,x.condition) for x in z.counterexamples],z.failure_conditions))
    blob=json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode(); digests.append(sha256(blob).hexdigest())
out={'schema':'NOEPIN_AL_REPLAY_V1','technology':80,'iterations_per_run':1000,'runs':3,'total':3000,'divergence':len(set(digests))-1,'digest':digests[0]}
print(json.dumps(out,sort_keys=True))
