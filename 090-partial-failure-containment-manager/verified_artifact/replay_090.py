from dataclasses import replace
from hashlib import sha256
import json
from noepin_al_090_partial_failure_containment_manager import *
base=(default_request(),default_steps(),default_states(),default_compensations(),default_policy())
digests=[]
for run in range(3):
    rows=[]
    for k in range(1000):
        r,s,st,c,p=base; mode=k%10
        if mode==0: pass
        elif mode==1: r=replace(r,blast_radius_known=False)
        elif mode==2: r=replace(r,resource_map_complete=False)
        elif mode==3: st=tuple(replace(x,state=StepState.UNKNOWN) if x.step_id=='A' else x for x in st)
        elif mode==4: c=(replace(c[0],coverage=.2),)
        elif mode==5: p=replace(p,revoked=True)
        elif mode==6: st=tuple(replace(x,state=StepState.SUCCESS,failure_code='') if x.step_id=='A' else x for x in st)
        elif mode==7: s=(replace(s[0],resources=('GLOBAL-LEDGER',)),replace(s[1],resources=('GLOBAL-LEDGER',)),s[2],s[3])
        elif mode==8: st=tuple(replace(x,state=StepState.FAILED,failure_code='ERR') if x.step_id in ('A','C') else x for x in st)
        else: s=s[:2]; st=st[:2]
        z=evaluate(r,s,st,c,p)
        rows.append((k,z.decision.value,z.containment_state.value,z.reasons,z.failed_step_ids,z.containment_set,z.continue_step_ids,z.stopped_step_ids,z.recovery_plan,z.next_gate_candidate,z.continue_candidate,z.full_stop_candidate,z.recovery_candidate,z.incident_candidate,z.permission_granted,z.action_executed,z.branch_execution_started,z.isolation_executed,z.compensation_executed,z.resource_lock_mutated,z.plan_committed,z.atomic_publish_executed,z.external_write_performed,z.world_truth_proven,z.safety_proven,z.action_success))
    digests.append(sha256(json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest())
out={'schema':'NOEPIN_AL_REPLAY_V1','technology':90,'iterations_per_run':1000,'runs':3,'total':3000,'divergence':len(set(digests))-1,'digest':digests[0]}
print(json.dumps(out,sort_keys=True))
