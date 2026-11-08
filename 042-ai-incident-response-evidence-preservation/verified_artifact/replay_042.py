from __future__ import annotations
from dataclasses import replace
import argparse, json
import noepin_al_042_incident_evidence as m

NOW=1_800_000_000


def case(i:int):
    p=m.default_policy(NOW)
    sev=list(m.IncidentSeverity)[i%4]
    if i%10==5:
        s=m.build_default_state(NOW,classification="RESTRICTED"); r=m.default_request(NOW,severity=sev)
    elif i%10==6:
        full=m.build_default_state(NOW); kept=tuple(x for x in full.segments if x.evidence_type!=m.EvidenceType.NETWORK_STATE)
        # rebuild a valid chain after removal
        items=[]; prev=""
        for seq,old in enumerate(kept):
            seg=m.EvidenceSegment(old.segment_id,old.incident_id,old.evidence_type,old.captured_at,old.source_id,old.source_version,old.classification,old.content_sha256,old.byte_length,seq,prev,old.evidence_binding,True)
            items.append(seg); prev=m.segment_fingerprint(seg)
        s=replace(full,segments=tuple(items)); r=m.default_request(NOW,severity=sev)
    elif i%10==7:
        s=m.build_default_state(NOW); r=replace(m.default_request(NOW,severity=sev),expected_policy_version="BAD")
    elif i%10==8:
        s=m.build_default_state(NOW,classification="PUBLIC"); r=m.default_request(NOW,severity=sev)
    elif i%10==9:
        s=m.build_default_state(NOW); xs=list(s.segments); xs[-1]=replace(xs[-1],integrity_verified=False); s=replace(s,segments=tuple(xs)); r=m.default_request(NOW,severity=sev)
    else:
        s=m.build_default_state(NOW); r=m.default_request(NOW,severity=sev)
    return m.assess(r,p,s,now=NOW)


def run(n:int):
    vals=tuple(case(i) for i in range(n))
    return m.assessment_digest(vals)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--evals',type=int,default=1000); ap.add_argument('--runs',type=int,default=3); ap.add_argument('--out')
    a=ap.parse_args(); digests=[run(a.evals) for _ in range(a.runs)]
    out={"runs":a.runs,"evaluations_per_run":a.evals,"total_evaluations":a.runs*a.evals,"digests":digests,"divergence":len(set(digests))-1,"digest":digests[0]}
    if a.out: open(a.out,'w',encoding='utf-8').write(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True))
    return 0 if out['divergence']==0 else 2
if __name__=='__main__': raise SystemExit(main())
