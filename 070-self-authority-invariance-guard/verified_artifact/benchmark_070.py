from dataclasses import replace
import json,statistics,time
from noepin_al_070_self_authority_invariance_guard import *
NOW=1_800_000_000
def fixture(n=1500):
    p=default_policy(NOW); auth=list(default_authorities()); aps=[]
    c=dict(binding="SAG-BIND",verified=True,revoked=False,policy_id="SAG-POLICY",policy_version="1",authority_epoch="SAG-EPOCH")
    for i in range(n): auth.append(AuthorityRecord(f"X{i:04d}",("READ",),**c))
    r=default_request(NOW)
    for i in range(n):
        rr=replace(r,request_id=f"RX{i}",target_id=f"X{i:04d}",actor_id=f"X{i:04d}",requested_capabilities=("READ","WRITE_SCOPED"),approval_id=f"AP{i}")
        aps.append(ApprovalEvidence(f"AP{i}","HUMAN-ADMIN",rr.target_id,rr.actor_id,rr.requested_capabilities,True,True,False,NOW+300,"SAG-BIND","SAG-POLICY","1","SAG-EPOCH"))
    return p,tuple(auth),tuple(aps),r
def run():
    p,a,aps,r=fixture(); st=prepare_state(p,a,aps,binding=r.binding,now=NOW); valid=validate_prepared_integrity(st); full=[]; prep=[]; sem=True
    for _ in range(5):
        t=time.perf_counter()
        for __ in range(10): z=evaluate(r,p,a,aps,now=NOW)
        full.append((time.perf_counter()-t)*1000)
        t=time.perf_counter()
        for __ in range(10): z2=evaluate_prepared(r,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=valid,now=NOW)
        prep.append((time.perf_counter()-t)*1000)
        sem = sem and ((z.decision.value,z.reasons,z.added_capabilities,z.removed_capabilities)==(z2.decision.value,z2.reasons,z2.added_capabilities,z2.removed_capabilities))
    aa=list(a); pp=list(aps)
    for i in range(50): aa[4+i]=replace(aa[4+i],capabilities=("READ","AUDIT"))
    del aa[4:9]; del pp[:5]
    c=dict(binding="SAG-BIND",verified=True,revoked=False,policy_id="SAG-POLICY",policy_version="1",authority_epoch="SAG-EPOCH")
    for i in range(5): aa.append(AuthorityRecord(f"NEW{i}",("READ",),**c))
    st2=prepare_state(p,tuple(aa),tuple(pp),binding=r.binding,now=NOW); d=make_delta(st,st2); rebuilt=apply_delta(st,d,now=NOW)
    remote={"authorities":dict(st2.authority_fingerprints),"approvals":dict(st2.approval_fingerprints)}
    for k in list(remote["authorities"])[:10]: remote["authorities"].pop(k)
    sync=missing_only_sync_plan(st2,remote)
    fb=full_registry_bytes(st2); db=delta_bytes(d)
    return {"schema":"NOEPIN_AL_DCSR_BENCHMARK_V1","technology":70,"condition":{"runtime":"Python standard library","authority_records":len(a),"approval_records":len(aps),"evaluations_per_batch":10,"batches":5},"full_median_ms":statistics.median(full),"prepared_median_ms":statistics.median(prep),"semantic_match":sem,"full_bytes":fb,"delta_bytes":db,"delta_ratio_percent":db/fb*100,"delta_fixture":{"changed_authorities":50,"removed_authorities":5,"added_authorities":5,"removed_approvals":5},"reconstruction_fingerprint_match":rebuilt.registry_fingerprint==st2.registry_fingerprint,"missing_only":{"authorities":len(sync.missing_or_changed_authority_ids),"approvals":len(sync.missing_or_changed_approval_ids),"metadata_bytes_required":sync.metadata_bytes_required,"full_resend_required":sync.full_resend_required},"authority":{"permission_grant":False,"role_change":False,"scope_change":False,"capability_activation":False,"credential_issue":False,"approval_execution":False,"action_execution":False,"truth":False,"safety":False,"action_success":False}}
if __name__=="__main__": print(json.dumps(run(),sort_keys=True))
