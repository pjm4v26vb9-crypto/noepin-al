from dataclasses import replace
import json,statistics,time
from noepin_al_087_permit_lease_manager import *
r,_,_,pol=default_request(),default_permits(),default_nonce_records(),default_policy()
N=5000
b,e=pol.binding,pol.state_epoch
p=tuple(PermitLease(f'P{n:05d}',1000.0,60.0,3,0,f'N{n:05d}',f'STATE{n:05d}','SCOPE',True,True,b,e) for n in range(N))
ns=tuple(NonceLeaseRecord(f'N{n:05d}',f'P{n:05d}',True,0,(),True,b,e) for n in range(N))
r=replace(r,permit_id='P00000',current_state_fingerprint='STATE00000',current_scope_fingerprint='SCOPE')
st=prepare_state(r,p,ns,pol,binding=b,state_epoch=e); valid=validate_prepared_integrity(st)
full=[]; prep=[]; semantic=True
for _ in range(5):
    t=time.perf_counter(); z1=None
    for __ in range(10): z1=evaluate(r,p,ns,pol)
    full.append((time.perf_counter()-t)*1000)
    t=time.perf_counter(); z2=None
    for __ in range(10): z2=evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=valid)
    prep.append((time.perf_counter()-t)*1000); semantic &= (z1==z2)
p2=list(p)
for n in range(10): p2[n]=replace(p2[n],ttl_seconds=61.0)
st2=prepare_state(r,tuple(p2),ns,pol,binding=b,state_epoch=e); delta=make_delta(st,st2)
kp=dict(st2.permit_fingerprints); kn=dict(st2.nonce_fingerprints)
for n in range(10): kp.pop(f'P{n:05d}')
plan=missing_only_sync_plan(st2,kp,kn)
out={'schema':'NOEPIN_AL_BENCHMARK_V1','technology':87,'condition':'Python stdlib; 5000 Permit leases + 5000 Nonce records; 10 evaluations x 5 batches; prepared verified-result reuse','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':semantic,'full_bytes':full_registry_bytes(st2),'delta_bytes':delta_bytes(delta),'delta_percent':delta_bytes(delta)/full_registry_bytes(st2)*100,'missing_permit_records':len(plan.missing_or_changed_permit_ids),'missing_nonce_records':len(plan.missing_or_changed_nonce_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend_required':plan.full_resend_required}
print(json.dumps(out,ensure_ascii=False,sort_keys=True))
