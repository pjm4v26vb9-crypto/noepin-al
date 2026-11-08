from __future__ import annotations
import json,time,statistics
from dataclasses import replace
from pathlib import Path
import noepin_al_059_external_trust_score as m
NOW=1_800_000_000

def make(n=1500):
    ps=[]; es=[]
    for i in range(n):
        eid=f'EXT-{i:05d}'; b=f'B-{i:05d}'
        ps.append(m.ExternalEntityProfile(eid,m.EntityType.TOOL,'PROVIDER-059',f'FP-{i:05d}',NOW-1000,NOW-10,True,b,False))
        es.append(m.TrustEvidence(f'EV-{i:05d}',eid,m.EvidenceKind.RELIABILITY,NOW-50,NOW+3000,10,True,True,'MON',b,False))
    return tuple(ps),tuple(es)

def main():
    p=m.default_policy(NOW); ps,es=make(); reqs=[]
    for i in range(15):
        prof=ps[i]; reqs.append(m.TrustRequest(f'R{i}',m.TrustOperation.ASSESS,prof.entity_id,prof.identity_fingerprint,m.PrivilegeLevel.NONE,p.policy_id,p.version,p.authority_epoch,prof.evidence_binding,False))
    reg=m.prepare_registry(p,ps,es,now=NOW); full=[]; prep=[]; sem=True
    for _ in range(5):
        t=time.perf_counter(); a=[m.evaluate(r,p,ps,es,now=NOW) for r in reqs]; full.append((time.perf_counter()-t)*1000)
        t=time.perf_counter(); b=[m.evaluate_prepared(r,p,reg,now=NOW) for r in reqs]; prep.append((time.perf_counter()-t)*1000)
        sem &= [m.canonical_json(x) for x in a]==[m.canonical_json(x) for x in b]
    bp,be=make(2000); tp=list(bp); te=list(be)
    for i in range(5,55): tp[i]=replace(tp[i],last_verified_at=tp[i].last_verified_at+1); te[i]=replace(te[i],impact=11)
    tp=tp[5:]; te=te[5:]
    for i in range(5):
        k=2000+i; eid=f'EXT-{k:05d}'; b=f'B-{k:05d}'; tp.append(m.ExternalEntityProfile(eid,m.EntityType.TOOL,'PROVIDER-059',f'FP-{k:05d}',NOW-1000,NOW-10,True,b,False)); te.append(m.TrustEvidence(f'EV-{k:05d}',eid,m.EvidenceKind.RELIABILITY,NOW-50,NOW+3000,10,True,True,'MON',b,False))
    tp=tuple(tp); te=tuple(te); d=m.make_registry_delta(bp,be,tp,te); rp,re=m.apply_registry_delta(bp,be,d)
    full_bytes=len(m.canonical_json({'profiles':tp,'evidence':te}).encode()); delta_bytes=len(m.canonical_json(d).encode())
    tr=m.prepare_registry(p,tp,te,now=NOW); rpf=dict(list(tr.profile_fingerprints.items())[:-5]); ref=dict(list(tr.evidence_fingerprints.items())[:-5]); sync=m.plan_registry_sync(tp,te,rpf,ref)
    obj={'condition':{'profiles':1500,'evidence':1500,'evaluations_per_batch':15,'batches':5},'full_materialization_median_ms':statistics.median(full),'prepared_registry_median_ms':statistics.median(prep),'semantic_match':sem,'delta':{'base_profiles':2000,'base_evidence':2000,'target_profiles':len(tp),'target_evidence':len(te),'changed_profiles':len(d.changed_profiles),'removed_profiles':len(d.removed_profile_ids),'added_profiles':len(d.added_profiles),'changed_evidence':len(d.changed_evidence),'removed_evidence':len(d.removed_evidence_ids),'added_evidence':len(d.added_evidence),'full_bytes':full_bytes,'delta_bytes':delta_bytes,'ratio_percent':delta_bytes/full_bytes*100,'reconstruction_fingerprint_match':m.registry_fingerprint(rp,re)==m.registry_fingerprint(tp,te)},'sync':{'target_records':len(tp)+len(te),'remote_known':len(rpf)+len(ref),'missing_or_changed_profiles':len(sync.missing_or_changed_profile_ids),'missing_or_changed_evidence':len(sync.missing_or_changed_evidence_ids),'metadata_bytes_required':sync.metadata_bytes_required,'full_resend_required':sync.full_resend_required,'permission_granted':sync.permission_granted,'connection_authorized':sync.connection_authorized,'high_privilege_authorized':sync.high_privilege_authorized,'probation_completion_authorized':sync.probation_completion_authorized}}
    Path('BENCHMARK_RESULT.json').write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n'); print(json.dumps(obj,sort_keys=True))
if __name__=='__main__': main()
