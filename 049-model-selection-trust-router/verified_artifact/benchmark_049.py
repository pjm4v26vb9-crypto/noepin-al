from __future__ import annotations
import dataclasses, json, statistics, time
import noepin_al_049_model_trust_router as m
NOW=1_800_000_000

def mk(i):
    loc=(m.ModelLocation.LOCAL,m.ModelLocation.EDGE,m.ModelLocation.CLOUD)[i%3]
    sens=frozenset(m.Sensitivity) if loc==m.ModelLocation.LOCAL else frozenset({m.Sensitivity.PUBLIC,m.Sensitivity.INTERNAL,m.Sensitivity.CONFIDENTIAL})
    return m.ModelProfile(f"M{i:05d}","NOEPIN_LOCAL" if loc==m.ModelLocation.LOCAL else ("TRUSTED_EDGE" if loc==m.ModelLocation.EDGE else "TRUSTED_CLOUD"),loc,frozenset({"TEXT","ANALYSIS","CODE"}),sens,0.91+(i%5)*0.01,0.95,NOW-100,NOW+10000,"MODEL-ROUTE-EVIDENCE-49",True)

def main():
    p=m.default_policy(NOW); profiles=tuple(mk(i) for i in range(400)); r=m.default_request(NOW); prepared=m.prepare_registry(p,profiles,now=NOW)
    full=[]; prep=[]; semantic=True
    for _ in range(5):
        t=time.perf_counter()
        a=[m.evaluate(r,p,profiles,now=NOW) for _ in range(10)]
        full.append((time.perf_counter()-t)*1000)
        t=time.perf_counter()
        b=[m.evaluate_prepared(r,p,profiles,prepared,now=NOW) for _ in range(10)]
        prep.append((time.perf_counter()-t)*1000)
        semantic=semantic and a==b
    base=tuple(mk(i) for i in range(2000)); target=list(base)
    for i in range(50): target[i]=dataclasses.replace(target[i],trust_score=max(.5,target[i].trust_score-.01))
    target=target[:-5]
    target.extend(dataclasses.replace(mk(7000+i),model_id=f"A{i:05d}") for i in range(5))
    target=tuple(target)
    d=m.build_registry_delta(base,target); rebuilt=m.apply_registry_delta(base,d)
    full_bytes=len(m.canonical_json(target).encode()); delta_bytes=len(m.canonical_json(d).encode())
    prep_target=m.prepare_registry(p,target,now=NOW)
    known=dict(prep_target.profile_fingerprints)
    for k in list(sorted(known))[-10:]: known.pop(k)
    sync=m.plan_registry_sync(prep_target,known)
    result={"schema":"NOEPIN_AL_BENCHMARK_RESULT_V1","technology":49,"condition":{"profiles":400,"evaluations_per_batch":10,"batches":5,"runtime":"Python standard library"},"full_materialization_median_ms":statistics.median(full),"prepared_registry_median_ms":statistics.median(prep),"semantic_match":semantic,"delta":{"base_items":len(base),"target_items":len(target),"changed":len(d.changed_profiles),"removed":len(d.removed_model_ids),"added":len(d.added_profiles),"full_bytes":full_bytes,"delta_bytes":delta_bytes,"ratio_percent":delta_bytes/full_bytes*100,"reconstruction_fingerprint_match":m.registry_fingerprint(rebuilt)==m.registry_fingerprint(target)},"sync":{"target_items":len(target),"remote_known":len(known),"missing_or_changed":len(sync.missing_or_changed_model_ids),"metadata_bytes_required":sync.metadata_bytes_required,"full_resend_required":sync.full_resend_required,"permission_granted":sync.permission_granted,"model_invocation_authorized":sync.model_invocation_authorized,"data_transfer_authorized":sync.data_transfer_authorized}}
    print(json.dumps(result,ensure_ascii=False,sort_keys=True)); return result
if __name__=='__main__': main()
