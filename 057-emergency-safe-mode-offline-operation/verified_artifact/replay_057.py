from __future__ import annotations
from dataclasses import replace
from hashlib import sha256
import json
import noepin_al_057_emergency_safe_mode as m
NOW=1_800_000_000

def run_once():
    p=m.default_policy(NOW); outs=[]
    for i in range(1000):
        req=replace(m.default_request(NOW),request_id=f'REQ-{i:04d}',incident_id=f'INC-{i:04d}',nonce=f'N-{i:04d}',evidence_binding=f'B-{i:04d}')
        sev=('HIGH','CRITICAL','MEDIUM','LOW')[i%4]
        cats=(frozenset({'NETWORK_ANOMALY'}),frozenset({'INTEGRITY_RISK'}),frozenset({'AUTOMATION_ANOMALY'}),frozenset({'DEPENDENCY_OUTAGE'}))[i%4]
        sig=(m.IncidentSignal(f'S-{i:04d}',req.incident_id,sev,cats,NOW-(i%100),True,True,req.evidence_binding,False),)
        rec=() if i%11 else (m.ReplayReceipt(f'R-{i:04d}',req.request_id,req.nonce,m.SafeMode.LOCAL_ONLY,NOW-1,True,req.evidence_binding,False),)
        a=m.evaluate(req,p,sig,rec,now=NOW)
        outs.append(m.canonical_json(a))
    return sha256('\n'.join(outs).encode()).hexdigest()

def main():
    ds=[run_once() for _ in range(3)]
    out={'runs':3,'evaluations_per_run':1000,'total_evaluations':3000,'digests':ds,'divergence':len(set(ds))-1,'digest':ds[0]}
    print(json.dumps(out,sort_keys=True)); return out
if __name__=='__main__': main()
