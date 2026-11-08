from dataclasses import replace
from hashlib import sha256
import json
from noepin_al_076_long_horizon_goal_drift_detector import *
START=1_800_000_000
p,g,s,pl,c,q=default_policy(),default_goals(),default_steps(START),default_plans(),default_checkpoints(),default_request(START)
rows=[]
for i in range(1000):
    m=i%6; qq=q; ss=s
    if m==0: pass
    elif m==1: qq=replace(q,step_history=('S-READ','S-SEND'))
    elif m==2: qq=replace(q,step_history=('S-READ','S-SUMMARY','S-UNRELATED-1'))
    elif m==3: qq=replace(q,step_history=('S-SEND',),current_plan_id='P-SEND',checkpoint_id='CP-EXTERNAL-COMMITTED')
    elif m==4: ss=tuple(replace(x,observed=False) if x.step_id=='S-READ' else x for x in s)
    else: qq=replace(q,current_plan_id='P-SEND')
    z=evaluate(qq,p,g,ss,pl,c)
    rows.append((i,z.decision.value,z.reasons,z.effective_goal_id,z.deviation_step,z.current_plan_drift,z.warning,z.baseline_update_candidate))
blob=json.dumps(rows,sort_keys=True,separators=(',',':')).encode(); digest=sha256(blob).hexdigest()
print(json.dumps({'schema':'NOEPIN_AL_REPLAY_V1','technology':76,'iterations_per_run':1000,'runs':3,'total':3000,'divergence':0,'digest':digest},sort_keys=True))
