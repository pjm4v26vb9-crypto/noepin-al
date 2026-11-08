from dataclasses import replace
import json,statistics,time
from noepin_al_071_policy_immutability_kernel import *
NOW=1_800_000_000
p=default_kernel_policy(NOW); c=default_snapshot(); r=default_request(NOW)
a=list(default_authorities()); v=list(default_versions())
for i in range(1500):
    a.append(AuthorityRecord(f"DUMMY-{i:04d}",(f"CAP-{i:04d}",),"POL-BIND","POL-EPOCH",True,False))
    v.append(VersionRecord(1000+i,f"dummy-hash-{i:04d}","POL-BIND",True,False))
s=[signature_for(r,c,now=NOW)]
for i in range(1500):
    s.append(SignatureEvidence(f"DSIG-{i:04d}","HUMAN-ADMIN",f"fp-{i}",f"h-{i}",7,"POL-BIND","POL-EPOCH",True,False,NOW+300))
a=tuple(a); s=tuple(s); v=tuple(v)
st=prepare_state(p,c,a,s,v,binding="POL-BIND",now=NOW); valid=validate_prepared_integrity(st)
full=[]; prep=[]; sem=True
for _ in range(5):
    t=time.perf_counter(); z1=None
    for __ in range(10): z1=evaluate(r,p,c,a,s,v,now=NOW)
    full.append((time.perf_counter()-t)*1000)
    t=time.perf_counter(); z2=None
    for __ in range(10): z2=evaluate_prepared(r,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=valid,now=NOW)
    prep.append((time.perf_counter()-t)*1000)
    sem &= (z1.decision==z2.decision and z1.reasons==z2.reasons and z1.candidate_policy_hash==z2.candidate_policy_hash)
a2=a+tuple(AuthorityRecord(f"NEW-{i:02d}",(f"NEWCAP-{i:02d}",),"POL-BIND","POL-EPOCH",True,False) for i in range(10))
st2=prepare_state(p,c,a2,s,v,binding="POL-BIND",now=NOW); d=make_delta(st,st2)
remote={"authorities":dict(st2.authority_fingerprints),"signatures":dict(st2.signature_fingerprints),"versions":dict(st2.version_fingerprints)}
for i in range(10): remote["authorities"].pop(f"NEW-{i:02d}")
plan=missing_only_sync_plan(st2,remote)
out={"schema":"NOEPIN_AL_BENCHMARK_V1","technology":71,"condition":"Python stdlib; 1504 authorities + 1501 signatures + 1507 version records; 10 evaluations x 5 batches","full_median_ms":statistics.median(full),"prepared_median_ms":statistics.median(prep),"semantic_match":sem,"full_bytes":full_registry_bytes(st2),"delta_bytes":delta_bytes(d),"delta_percent":delta_bytes(d)/full_registry_bytes(st2)*100,"missing_authorities":len(plan.missing_or_changed_authority_ids),"missing_signatures":len(plan.missing_or_changed_signature_ids),"missing_versions":len(plan.missing_or_changed_versions),"missing_metadata_bytes":plan.metadata_bytes_required,"full_resend_required":plan.full_resend_required}
print(json.dumps(out,ensure_ascii=False,sort_keys=True))
