from dataclasses import replace
import json,statistics,time
from noepin_al_091_two_phase_action_commit import *
pol=default_policy(); req=CommitRequest('BENCH','TX-B','COORD-B','APP-B',False,'',True,pol.binding,pol.state_epoch); N=5000
actions=[]; participants=[]; prepares=[]
for n in range(N):
    pid=f'P{n:05d}'; aid=f'A{n:05d}'
    participants.append(Participant(pid,f'R{n:05d}',True,True,pol.binding,pol.state_epoch)); actions.append(ActionSpec(aid,(pid,),f'EFF{n:05d}',True,True,pol.binding,pol.state_epoch)); prepares.append(PrepareRecord(pid,req.tx_id,PrepareStatus.PREPARED,True,True,True,True,pol.binding,pol.state_epoch))
approvals=(ApprovalEvidence('APP-B',req.tx_id,True,req.approval_binding_digest,True,pol.binding,pol.state_epoch),); outcomes=()
actions=tuple(actions); participants=tuple(participants); prepares=tuple(prepares)
st=prepare_state(req,actions,participants,prepares,approvals,outcomes,pol,binding=pol.binding,state_epoch=pol.state_epoch); valid=validate_prepared_integrity(st)
full=[]; prep=[]; semantic=True
for _ in range(5):
    t=time.perf_counter(); z1=None
    for __ in range(10): z1=evaluate(req,actions,participants,prepares,approvals,outcomes,pol)
    full.append((time.perf_counter()-t)*1000)
    t=time.perf_counter(); z2=None
    for __ in range(10): z2=evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=valid)
    prep.append((time.perf_counter()-t)*1000); semantic &= (z1==z2)
prepares2=list(prepares)
for n in range(10): prepares2[n]=replace(prepares2[n],resource_ready_evidence=False)
st2=prepare_state(req,actions,participants,tuple(prepares2),approvals,outcomes,pol,binding=pol.binding,state_epoch=pol.state_epoch); delta=make_delta(st,st2)
known=dict(st2.record_fingerprints)
for n in range(10): known.pop(f'PREPARE:P{n:05d}')
plan=missing_only_sync_plan(st2,known)
out={'schema':'NOEPIN_AL_BENCHMARK_V1','technology':91,'condition':'Python stdlib; 5000 Actions + 5000 Participants + 5000 Prepare records; 10 evaluations x 5 batches; prepared verified-result reuse','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':semantic,'full_bytes':full_registry_bytes(st2),'delta_bytes':delta_bytes(delta),'delta_percent':delta_bytes(delta)/full_registry_bytes(st2)*100,'missing_records':len(plan.missing_or_changed_record_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend_required':plan.full_resend_required}
print(json.dumps(out,ensure_ascii=False,sort_keys=True))
