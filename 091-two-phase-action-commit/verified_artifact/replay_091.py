from dataclasses import replace
from hashlib import sha256
import json
from noepin_al_091_two_phase_action_commit import *
base=(default_request(),default_actions(),default_participants(),default_prepares(),default_approvals(),default_outcomes(),default_policy())
digests=[]
for run in range(3):
    rows=[]
    for k in range(1000):
        r,a,p,pr,ap,o,pol=base; mode=k%10
        if mode==0: pass
        elif mode==1: pr=(replace(pr[0],status=PrepareStatus.REJECTED),pr[1])
        elif mode==2: pr=(replace(pr[0],status=PrepareStatus.TIMEOUT),pr[1])
        elif mode==3: pr=(replace(pr[0],status=PrepareStatus.UNKNOWN),pr[1])
        elif mode==4: ap=()
        elif mode==5: pol=replace(pol,revoked=True)
        elif mode==6: pr=(replace(pr[0],resource_ready_evidence=False),pr[1])
        elif mode==7: r=replace(r,observed=False)
        elif mode==8: o=(CommitOutcomeEvidence('P-A',r.tx_id,CommitObservationStatus.FAILED,True,pol.binding,pol.state_epoch),)
        else: pol=replace(pol,allow_commit_candidate=False)
        z=evaluate(r,a,p,pr,ap,o,pol)
        rows.append((k,z.decision.value,z.transaction_state.value,z.reasons,z.prepared_participant_ids,z.rejected_participant_ids,z.timeout_participant_ids,z.unknown_participant_ids,z.commit_candidate,z.abort_candidate,z.human_approval_candidate,z.incident_candidate,z.compensation_candidate,z.coordinator_recovery_validated,z.next_gate_candidate,z.permission_granted,z.approval_executed,z.prepare_request_executed,z.resource_lock_mutated,z.commit_executed,z.abort_executed,z.action_executed,z.compensation_executed,z.plan_committed,z.atomic_publish_executed,z.external_write_performed,z.world_truth_proven,z.safety_proven,z.action_success))
    digests.append(sha256(json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest())
out={'schema':'NOEPIN_AL_REPLAY_V1','technology':91,'iterations_per_run':1000,'runs':3,'total':3000,'divergence':len(set(digests))-1,'digest':digests[0]}
print(json.dumps(out,sort_keys=True))
