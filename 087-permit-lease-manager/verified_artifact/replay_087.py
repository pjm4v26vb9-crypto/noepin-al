from dataclasses import replace
from hashlib import sha256
import json
from noepin_al_087_permit_lease_manager import *
base=(default_request(),default_permits(),default_nonce_records(),default_policy())
digests=[]
for run in range(3):
    rows=[]
    for k in range(1000):
        r,p,n,pol=base; mode=k%10
        if mode==0: pass
        elif mode==1: r=replace(r,now=1064)
        elif mode==2: r=replace(r,current_state_fingerprint='X')
        elif mode==3: n=(replace(n[0],active=False),)
        elif mode==4: n=(replace(n[0],seen_attempt_nonces=(r.attempt_nonce,)),)
        elif mode==5: p=(replace(p[0],signature_verified=False),)
        elif mode==6: r=replace(r,current_scope_fingerprint='X')
        elif mode==7: pol=replace(pol,revoked=True)
        elif mode==8: p=(replace(p[0],usage_count=3),); n=(replace(n[0],usage_count=3),)
        else: r=replace(r,expected_usage_count=1)
        z=evaluate(r,p,n,pol)
        rows.append((k,z.decision.value,z.lease_state.value,z.reasons,z.remaining_ttl,z.consume_state.value,z.next_usage_count,z.consume_candidate,z.next_gate_candidate,z.reissue_required,z.replay_detected,z.permission_granted,z.usage_consumed,z.nonce_store_mutated,z.action_executed,z.plan_committed,z.atomic_publish_executed,z.external_write_performed,z.receipt_promoted_to_truth,z.world_truth_proven,z.safety_proven,z.action_success))
    digests.append(sha256(json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest())
out={'schema':'NOEPIN_AL_REPLAY_V1','technology':87,'iterations_per_run':1000,'runs':3,'total':3000,'divergence':len(set(digests))-1,'digest':digests[0]}
print(json.dumps(out,sort_keys=True))
