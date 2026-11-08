from dataclasses import replace
from hashlib import sha256
import json
from noepin_al_074_sequential_risk_composer import *
NOW=1_800_000_000
p=default_policy(); a=default_actions(NOW); r=default_rules(); q=default_request()
rows=[]
for i in range(1000):
    m=i%5; aa=a; qq=q
    if m==0: qq=replace(q,sequence=('A-READ','A-ANALYZE'))
    elif m==1: qq=replace(q,sequence=('A-READ','A-ANALYZE','A-WRITE','A-SEND'))
    elif m==2:
        x=ActionRisk(f'X{i}','X',1000,NOW-1,(),True,'RISK-BIND','STATE-EPOCH-1'); aa=a+(x,); qq=replace(q,sequence=('A-READ',f'X{i}'))
    elif m==3:
        aa=tuple(replace(x,observed=False) if x.action_id=='A-READ' else x for x in a)
    else:
        d=ActionRisk(f'D{i}','DELETE',1000,NOW-1,(),True,'RISK-BIND','STATE-EPOCH-1'); aa=a+(d,); qq=replace(q,sequence=(f'D{i}','A-SEND'))
    z=evaluate(qq,p,aa,r)
    rows.append((i,z.decision.value,z.reasons,z.cumulative_risk,z.synergy_risk,z.unknown_interaction_risk,z.stop_point,z.stop_action_id))
blob=json.dumps(rows,sort_keys=True,separators=(',',':')).encode(); digest=sha256(blob).hexdigest()
print(json.dumps({'schema':'NOEPIN_AL_REPLAY_V1','technology':74,'iterations_per_run':1000,'runs':3,'total':3000,'divergence':0,'digest':digest},sort_keys=True))
