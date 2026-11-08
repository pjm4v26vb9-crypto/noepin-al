from dataclasses import replace
import json,statistics,time
from noepin_al_072_approval_binding_digest import *
NOW=1_800_000_000
p=default_policy(NOW); r=default_request(NOW); a=list(default_authorities()); k=list(default_keys(NOW)); rr=[]
ap=[reference_approval(r,issued_at=NOW)]
for i in range(1500):
    ap.append(ApprovalRecord(f'DAPR-{i:04d}','HUMAN-ADMIN','KEY-HUMAN',f'rf-{i}',f'dig-{i}',f'mac-{i}',f'nonce-{i}',NOW,NOW+300,'APPROVAL-BIND','APPROVAL-EPOCH',True))
    a.append(ApproverAuthority(f'DUMMY-{i:04d}',f'DKEY-{i:04d}',(f'CAP-{i:04d}',),'APPROVAL-BIND','APPROVAL-EPOCH',True,False))
    k.append(VerifierKeyRecord(f'DKEY-{i:04d}','33'*32,'APPROVAL-BIND','APPROVAL-EPOCH',True,False,NOW+3600))
ap=tuple(ap); a=tuple(a); k=tuple(k); rr=tuple(rr)
st=prepare_state(p,ap,a,k,rr,binding='APPROVAL-BIND'); valid=validate_prepared_integrity(st)
full=[]; prep=[]; sem=True
for _ in range(5):
    t=time.perf_counter(); z1=None
    for __ in range(10): z1=evaluate(r,'APR-72',p,ap,a,k,rr,current_policy_fingerprint=r.policy_fingerprint,now=NOW)
    full.append((time.perf_counter()-t)*1000)
    t=time.perf_counter(); z2=None
    for __ in range(10): z2=evaluate_prepared(r,'APR-72',st,current_approval_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_bound_policy_fingerprint=r.policy_fingerprint,prepared_integrity_validated=valid,now=NOW)
    prep.append((time.perf_counter()-t)*1000)
    sem &= (z1.decision==z2.decision and z1.reasons==z2.reasons and z1.approval_digest==z2.approval_digest)
ap2=ap+tuple(ApprovalRecord(f'NEW-{i:02d}','HUMAN-ADMIN','KEY-HUMAN',f'nrf-{i}',f'ndig-{i}',f'nmac-{i}',f'nnonce-{i}',NOW,NOW+300,'APPROVAL-BIND','APPROVAL-EPOCH',True) for i in range(10))
st2=prepare_state(p,ap2,a,k,rr,binding='APPROVAL-BIND'); d=make_delta(st,st2)
remote={'approvals':dict(st2.approval_fingerprints),'authorities':dict(st2.authority_fingerprints),'keys':dict(st2.key_fingerprints),'replay':dict(st2.replay_fingerprints)}
for i in range(10): remote['approvals'].pop(f'NEW-{i:02d}')
plan=missing_only_sync_plan(st2,remote)
out={'schema':'NOEPIN_AL_BENCHMARK_V1','technology':72,'condition':'Python stdlib; 1501 approvals + 1502 authorities + 1502 verifier keys; 10 evaluations x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':sem,'full_bytes':full_registry_bytes(st2),'delta_bytes':delta_bytes(d),'delta_percent':delta_bytes(d)/full_registry_bytes(st2)*100,'missing_approvals':len(plan.missing_or_changed_approval_ids),'missing_authorities':len(plan.missing_or_changed_authority_ids),'missing_keys':len(plan.missing_or_changed_key_ids),'missing_replay':len(plan.missing_or_changed_replay_digests),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend_required':plan.full_resend_required}
print(json.dumps(out,ensure_ascii=False,sort_keys=True))
