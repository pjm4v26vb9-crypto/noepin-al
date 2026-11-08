from dataclasses import replace
from hashlib import sha256
import json
from noepin_al_089_idempotency_guard import *
base=(default_request(),default_histories(),default_policy())
def mk(record_id,key='KEY-NEW',intent='INTENT-NEW',action='ACTION-FP-SEND',status=ExecutionStatus.SUCCESS,result='R'):
    return ExecutionHistoryRecord(record_id,key,intent,action,status,result,True,'IDEM-BIND','STATE-EPOCH-1')
digests=[]
for run in range(3):
    rows=[]
    for k in range(1000):
        r,h,p=base; mode=k%10
        if mode==0: pass
        elif mode==1: h=h+(mk(f'S{k}'),)
        elif mode==2: h=h+(mk(f'D{k}',key=f'OTHER{k}'),)
        elif mode==3: r=replace(r,side_effecting=False,history_store_available=False,history_complete=False,idempotency_key='')
        elif mode==4: r=replace(r,history_store_available=False)
        elif mode==5: r=replace(r,history_complete=False)
        elif mode==6: r=replace(r,idempotency_key='')
        elif mode==7: h=h+(mk(f'F{k}',status=ExecutionStatus.FAILED,result=''),)
        elif mode==8: h=h+(mk(f'I{k}',status=ExecutionStatus.IN_FLIGHT,result=''),)
        else: h=h+(mk(f'C{k}',intent='OTHER'),)
        z=evaluate(r,h,p)
        rows.append((k,z.decision.value,z.idempotency_state.value,z.reasons,z.safe_retry_method.value,z.matched_record_ids,z.duplicate_record_ids,z.prior_result_fingerprint,z.generated_key_candidate,z.next_gate_candidate,z.history_registration_candidate,z.result_reuse_candidate,z.retry_candidate,z.request_promoted_to_success,z.history_store_mutated,z.key_registered,z.permission_granted,z.action_executed,z.plan_committed,z.atomic_publish_executed,z.external_write_performed,z.receipt_promoted_to_truth,z.world_truth_proven,z.safety_proven,z.action_success))
    digests.append(sha256(json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest())
out={'schema':'NOEPIN_AL_REPLAY_V1','technology':89,'iterations_per_run':1000,'runs':3,'total':3000,'divergence':len(set(digests))-1,'digest':digests[0]}
print(json.dumps(out,sort_keys=True))
