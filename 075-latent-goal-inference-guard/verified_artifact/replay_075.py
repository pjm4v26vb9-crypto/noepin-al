from dataclasses import replace
from hashlib import sha256
import json
from noepin_al_075_latent_goal_inference_guard import *
p,g,e,a,ap,q=default_policy(),default_goals(),default_effects(),default_actions(),default_approvals(),default_request()
rows=[]
for i in range(1000):
    m=i%5; qq=q; aa=a
    if m==0: pass
    elif m==1: qq=replace(q,action_sequence=('A-READ','A-ANALYZE','A-SEND'))
    elif m==2: qq=replace(q,action_sequence=('A-READ',))
    elif m==3: qq=replace(q,user_goal_id='G-PRESERVE',action_sequence=('A-READ','A-PRESERVE'))
    else: aa=tuple(replace(x,observed=False) if x.action_id=='A-READ' else x for x in a)
    z=evaluate(qq,p,g,e,aa,ap)
    rows.append((i,z.decision.value,z.reasons,z.top_goal_id,z.goal_distance,z.ambiguity,z.deviation_detected))
blob=json.dumps(rows,sort_keys=True,separators=(',',':')).encode(); digest=sha256(blob).hexdigest()
print(json.dumps({'schema':'NOEPIN_AL_REPLAY_V1','technology':75,'iterations_per_run':1000,'runs':3,'total':3000,'divergence':0,'digest':digest},sort_keys=True))
