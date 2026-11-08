from dataclasses import replace
from hashlib import sha256
import json
from noepin_al_086_compensation_action_planner import *
base=(default_request(),default_intent(),default_permit(),default_actions(),default_effects(),default_compensations(),default_policy())
digests=[]
for run in range(3):
    rows=[]
    for n in range(1000):
        r,i,p,a,e,c,pol=base; mode=n%10
        if mode==0: pass
        elif mode==1: p=replace(p,allow_candidate=False)
        elif mode==2: e=(e[0],replace(e[1],observed=False))
        elif mode==3: c=(c[0],replace(c[1],status=CompensationStatus.FAILED))
        elif mode==4: c=(c[0],replace(c[1],risk=Risk.HIGH))
        elif mode==5: c=(c[0],replace(c[1],coverage=.8))
        elif mode==6: c=(c[0],replace(c[1],coverage=.2))
        elif mode==7: a=(replace(a[0],risk=Risk.UNKNOWN),a[1])
        elif mode==8: e=(e[0],replace(e[1],severity=Risk.CRITICAL)); c=(c[0],replace(c[1],status=CompensationStatus.FAILED))
        else: pol=replace(pol,revoked=True)
        z=evaluate(r,i,p,a,e,c,pol)
        rows.append((n,z.decision.value,z.reasons,[(x.compensation_id,x.effect_id,x.action_id,x.reverse_action_order,x.coverage,x.compensation_risk.value) for x in z.compensation_plan],z.coverage,z.residual_risk,z.uncovered_effect_ids,z.critical_uncovered_effect_ids,z.approval_state.value,z.plan_attached_candidate,z.next_gate_candidate,z.permission_granted,z.forward_action_executed,z.compensation_executed,z.plan_committed,z.atomic_publish_executed,z.external_write_performed,z.receipt_promoted_to_truth,z.world_truth_proven,z.safety_proven,z.action_success))
    digests.append(sha256(json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest())
out={'schema':'NOEPIN_AL_REPLAY_V1','technology':86,'iterations_per_run':1000,'runs':3,'total':3000,'divergence':len(set(digests))-1,'digest':digests[0]}
print(json.dumps(out,sort_keys=True))
