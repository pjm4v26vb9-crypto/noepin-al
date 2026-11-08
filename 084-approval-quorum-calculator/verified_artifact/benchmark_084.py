from dataclasses import replace
import json,statistics,time
from noepin_al_084_approval_quorum_calculator import *
p=default_policy(); q=default_proposal(); b,ep=p.binding,p.state_epoch; N=5000
roles=[]; approvals=[]
for n in range(N):
    role=('OPERATOR',) if n%2==0 else ('REVIEWER',)
    roles.append(RoleMatrixEntry(f'u{n:05d}',role,f'g{n:05d}',True,b,ep))
    approvals.append(ApprovalEvidence(f'ap{n:05d}',q.proposal_id,f'u{n:05d}',True,True,False,b,ep))
roles=tuple(roles); approvals=tuple(approvals)
st=prepare_state(p,q,roles,approvals,binding=b,state_epoch=ep); valid=validate_prepared_integrity(st)
full=[]; prep=[]; semantic=True
for _ in range(5):
    t=time.perf_counter(); z1=None
    for __ in range(10): z1=evaluate(q,roles,approvals,p)
    full.append((time.perf_counter()-t)*1000)
    t=time.perf_counter(); z2=None
    for __ in range(10): z2=evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=valid)
    prep.append((time.perf_counter()-t)*1000); semantic &= (z1==z2)
a2=list(approvals)
for n in range(10): a2[n]=replace(a2[n],observed=False)
st2=prepare_state(p,q,roles,tuple(a2),binding=b,state_epoch=ep); delta=make_delta(st,st2)
kr=dict(st2.role_fingerprints); ka=dict(st2.approval_fingerprints)
for n in range(5): kr.pop(f'u{n:05d}')
for n in range(5): ka.pop(f'ap{n:05d}')
plan=missing_only_sync_plan(st2,kr,ka)
out={'schema':'NOEPIN_AL_BENCHMARK_V1','technology':84,'condition':'Python stdlib; 5000 Role Matrix records + 5000 Approval Evidence records; 10 evaluations x 5 batches; prepared verified-result reuse','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':semantic,'full_bytes':full_registry_bytes(st2),'delta_bytes':delta_bytes(delta),'delta_percent':delta_bytes(delta)/full_registry_bytes(st2)*100,'missing_role_records':len(plan.missing_or_changed_actor_ids),'missing_approval_records':len(plan.missing_or_changed_approval_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend_required':plan.full_resend_required}
print(json.dumps(out,ensure_ascii=False,sort_keys=True))
