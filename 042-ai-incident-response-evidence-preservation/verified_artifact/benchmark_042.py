from __future__ import annotations
import argparse, json, statistics, time
import noepin_al_042_incident_evidence as m

NOW=1_800_000_000


def make_large_state(n:int):
    incident="INC-042-BENCH"; binding="BENCH-BIND"; out=[]; prev=""
    types=list(m.EvidenceType)
    for i in range(n):
        seg=m.build_segment(segment_id=f"S{i:05d}",incident_id=incident,evidence_type=types[i%len(types)],captured_at=NOW-(i%30),source_id=f"SRC-{i%17}",source_version="1",classification="INTERNAL",payload=f"payload-{i}".encode(),sequence=i,previous_segment_fingerprint=prev,evidence_binding=binding,integrity_verified=True)
        out.append(seg); prev=m.segment_fingerprint(seg)
    return m.IncidentState(incident,"1",1,binding,tuple(out))


def request_for(state):
    p=m.default_policy(NOW)
    r=m.IncidentRequest(state.incident_id,"NOEPIN",NOW,m.IncidentSeverity.HIGH,"benchmark",p.policy_id,p.version,p.authority_epoch,state.evidence_binding,True)
    return p,r


def timed(fn, iterations):
    t0=time.perf_counter()
    for _ in range(iterations): fn()
    return (time.perf_counter()-t0)*1000


def make_delta_pair(n=5000):
    base=make_large_state(n)
    cut=n-55
    out=list(base.segments[:cut]); prev=m.segment_fingerprint(out[-1]) if out else ""
    # 50 changed retained segments
    for i in range(cut,n-5):
        old=base.segments[i]
        seg=m.build_segment(segment_id=old.segment_id,incident_id=base.incident_id,evidence_type=old.evidence_type,captured_at=old.captured_at,source_id=old.source_id,source_version=old.source_version,classification=old.classification,payload=f"changed-{i}".encode(),sequence=len(out),previous_segment_fingerprint=prev,evidence_binding=base.evidence_binding,integrity_verified=True)
        out.append(seg); prev=m.segment_fingerprint(seg)
    # 5 base tail segments removed, 5 new segments added
    for j in range(5):
        i=n+j
        seg=m.build_segment(segment_id=f"ADD{j}",incident_id=base.incident_id,evidence_type=m.EvidenceType.OTHER,captured_at=NOW,source_id=f"ADD-SRC-{j}",source_version="1",classification="INTERNAL",payload=f"added-{j}".encode(),sequence=len(out),previous_segment_fingerprint=prev,evidence_binding=base.evidence_binding,integrity_verified=True)
        out.append(seg); prev=m.segment_fingerprint(seg)
    target=m.IncidentState(base.incident_id,"2",1,base.evidence_binding,tuple(out))
    return base,target


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--pairs',type=int,default=1000); ap.add_argument('--evals',type=int,default=30); ap.add_argument('--batches',type=int,default=5); ap.add_argument('--out'); a=ap.parse_args()
    state=make_large_state(a.pairs); policy,request=request_for(state); prepared=m.prepare_state(state)
    full=[]; prep=[]
    for _ in range(a.batches):
        full.append(timed(lambda:m.assess(request,policy,state,now=NOW),a.evals))
        prep.append(timed(lambda:m.assess_prepared(request,policy,prepared,now=NOW),a.evals))
    f=m.assess(request,policy,state,now=NOW); q=m.assess_prepared(request,policy,prepared,now=NOW)
    base,target=make_delta_pair(5000); delta=m.make_evidence_delta(base,target); rebuilt=m.apply_evidence_delta(base,delta)
    full_bytes=len(m.canonical_json(target).encode()); delta_bytes=len(m.canonical_json(delta).encode())
    target_prepared=m.prepare_state(target); known=frozenset(list(target_prepared.segment_fingerprints.values())[:-10]); transfer=m.plan_evidence_transfer(target_prepared,known)
    result={
      "condition":{"pairs":a.pairs,"evaluations_per_batch":a.evals,"batches":a.batches,"runtime":"Python standard library"},
      "full_materialization_ms":full,"prepared_ms":prep,
      "full_materialization_median_ms":statistics.median(full),"prepared_median_ms":statistics.median(prep),
      "semantic_match":f.bundle_fingerprint==q.bundle_fingerprint and f.decision==q.decision,
      "delta":{"base_segments":5000,"changed":len(delta.changed_segments),"removed":len(delta.removed_segment_ids),"added":len(delta.added_segments),"full_bytes":full_bytes,"delta_bytes":delta_bytes,"ratio_percent":delta_bytes/full_bytes*100,"reconstruction_fingerprint_match":m.fingerprint(rebuilt)==m.fingerprint(m.normalize_state(target))},
      "transfer_plan":{"target_segments":len(target.segments),"remote_known":len(known),"missing":len(transfer.missing_segment_ids),"full_resend_required":transfer.full_resend_required}
    }
    if a.out: open(a.out,'w',encoding='utf-8').write(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
    return 0 if result['semantic_match'] and result['delta']['reconstruction_fingerprint_match'] else 2
if __name__=='__main__': raise SystemExit(main())
