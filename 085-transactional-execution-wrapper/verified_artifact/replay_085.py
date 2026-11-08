from dataclasses import replace
from hashlib import sha256
import json
from noepin_al_085_transactional_execution_wrapper import *
base=(default_request(),default_intent(),default_permit(),default_plan(),default_before(),default_after(),default_steps(),default_verify(),default_rollback(),default_policy())
digests=[]
for run in range(3):
    rows=[]
    for n in range(1000):
        r,i,p,pl,b,a,s,v,rb,pol=base; mode=n%10
        if mode==0: pass
        elif mode==1: s=(s[0],replace(s[1],status=StepStatus.FAILED))
        elif mode==2: v=replace(v,status=VerifyStatus.MISMATCH)
        elif mode==3: v=replace(v,status=VerifyStatus.TIMEOUT)
        elif mode==4: s=(replace(s[0],status=StepStatus.EXCEPTION),s[1])
        elif mode==5: p=replace(p,observed=False)
        elif mode==6: p=replace(p,allow_candidate=False)
        elif mode==7: a=replace(a,observed=False)
        elif mode==8: v=replace(v,final_state_fingerprint='BAD')
        else: pol=replace(pol,revoked=True)
        z=evaluate(r,i,p,pl,b,a,s,v,rb,pol)
        rows.append((n,z.decision.value,z.transaction_state.value,z.reasons,z.applied_action_ids,z.failed_action_id,z.commit_candidate,z.rollback_candidate,z.rollback_verified,z.incident_candidate,z.commit_result,z.rollback_result,z.next_gate_candidate,z.permission_granted,z.action_executed,z.commit_executed,z.rollback_executed,z.external_write_performed,z.receipt_promoted_to_truth,z.world_truth_proven,z.safety_proven,z.action_success))
    digests.append(sha256(json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest())
out={'schema':'NOEPIN_AL_REPLAY_V1','technology':85,'iterations_per_run':1000,'runs':3,'total':3000,'divergence':len(set(digests))-1,'digest':digests[0]}
print(json.dumps(out,sort_keys=True))
