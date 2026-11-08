from dataclasses import replace
import json, statistics, time
from noepin_al_067_assumption_verification_graph import *
NOW=1_800_000_000

def fixture(n=1500):
    p=default_policy(NOW); c=dict(binding="AVG-BIND",verified=True,revoked=False,policy_id="AVG-POLICY",policy_version="1",authority_epoch="AVG-EPOCH")
    a=[]; v=[]; x=[]
    for i in range(n):
        aid=f"B{i:04d}"; impact=Impact.LOW if i else Impact.HIGH
        a.append(AssumptionSpec(aid,impact,**c))
        v.append(EvidenceRecord(f"BE{i:04d}",aid,EvidenceState.VERIFIED,.99,f"P{i:04d}",NOW-1,NOW+1000,**c))
        x.append(ActionSpec(f"BA{i:04d}",(aid,),**c))
    r=VerificationRequest("BREQ","BPLAN",("BA0000",),"AVG-BIND","AVG-POLICY","1","AVG-EPOCH",NOW-1,NOW+1000)
    return p,tuple(a),(),tuple(v),(),tuple(x),r

def run():
    p,a,e,v,o,x,r=fixture(); s=prepare_state(p,a,e,v,o,x,binding=r.binding,now=NOW); valid=validate_prepared_integrity(s)
    full=[]; prep=[]; ref=None
    for _ in range(5):
        t=time.perf_counter()
        for __ in range(10): z=evaluate(r,p,a,e,v,o,x,now=NOW)
        full.append((time.perf_counter()-t)*1000)
        t=time.perf_counter()
        for __ in range(10): z2=evaluate_prepared(r,s,current_policy_fingerprint=s.policy_fingerprint,current_registry_fingerprint=s.registry_fingerprint,prepared_integrity_validated=valid,now=NOW)
        prep.append((time.perf_counter()-t)*1000)
        ref=(z.decision.value,z.reasons,z.verified_assumption_ids)==(z2.decision.value,z2.reasons,z2.verified_assumption_ids) if ref is None else ref
    # target delta: 50 changed evidence, 5 removed + 5 added evidence
    vv=list(v)
    for i in range(50): vv[i]=replace(vv[i],confidence=.90)
    vv=vv[5:]
    for i in range(5): vv.append(EvidenceRecord(f"NEW{i}",f"B{100+i:04d}",EvidenceState.VERIFIED,.98,f"NP{i}",NOW-1,NOW+1000,"AVG-BIND",True,False,"AVG-POLICY","1","AVG-EPOCH"))
    s2=prepare_state(p,a,e,tuple(vv),o,x,binding=r.binding,now=NOW); d=make_delta(s,s2); rebuilt=apply_delta(s,d,now=NOW)
    remote={"assumptions":dict(s2.assumption_fingerprints),"edges":dict(s2.edge_fingerprints),"evidence":dict(s2.evidence_fingerprints),"observations":dict(s2.observation_fingerprints),"actions":dict(s2.action_fingerprints)}
    for k in list(remote["evidence"])[:10]: remote["evidence"].pop(k)
    sync=missing_only_sync_plan(s2,remote)
    return {"schema":"NOEPIN_AL_DCSR_BENCHMARK_V1","technology":67,"condition":{"runtime":"Python standard library","assumptions":len(a),"evidence":len(v),"actions":len(x),"evaluations_per_batch":10,"batches":5},"full_median_ms":statistics.median(full),"prepared_median_ms":statistics.median(prep),"semantic_match":bool(ref),"full_bytes":full_registry_bytes(s2),"delta_bytes":delta_bytes(d),"delta_ratio_percent":delta_bytes(d)/full_registry_bytes(s2)*100,"delta_fixture":{"changed_evidence":50,"removed_evidence":5,"added_evidence":5},"reconstruction_fingerprint_match":rebuilt.registry_fingerprint==s2.registry_fingerprint,"missing_only":{"evidence":len(sync.missing_or_changed_evidence_ids),"metadata_bytes_required":sync.metadata_bytes_required,"full_resend_required":sync.full_resend_required},"authority":{"permission_grant":False,"environment_change":False,"evidence_write":False,"action_execution":False,"truth":False,"safety":False,"action_success":False}}
if __name__=='__main__': print(json.dumps(run(),ensure_ascii=False,sort_keys=True))
