from __future__ import annotations
from dataclasses import replace
from hashlib import sha256
import json
import noepin_al_058_ephemeral_credential as m
NOW=1_800_000_000

def run_once():
    p=m.default_policy(NOW); outs=[]
    for i in range(1000):
        if i%4==0:
            r=replace(m.default_request(NOW),request_id=f'I-{i}',task_id=f'T-{i}',run_id=f'R-{i}',subject_id=f'S-{i}',evidence_binding=f'B-{i}',requested_ttl_seconds=1+(i%900))
            rs=()
        else:
            rec=replace(m.default_active_record(NOW),credential_id=f'C-{i}',task_id=f'T-{i}',run_id=f'R-{i}',subject_id=f'S-{i}',evidence_binding=f'B-{i}',use_count=0 if i%7 else 1,revoked=(i%17==0),expires_at=NOW+(100 if i%13 else 0))
            r=replace(m.default_request(NOW),request_id=f'U-{i}',operation=m.CredentialOperation.USE,credential_id=rec.credential_id,task_id=rec.task_id,run_id=rec.run_id,subject_id=rec.subject_id,evidence_binding=rec.evidence_binding,requested_ttl_seconds=0,task_completed=(i%19==0))
            rs=(rec,)
        outs.append(m.canonical_json(m.evaluate(r,p,rs,now=NOW)))
    return sha256('\n'.join(outs).encode()).hexdigest()
def main():
    ds=[run_once() for _ in range(3)]; out={'runs':3,'evaluations_per_run':1000,'total_evaluations':3000,'digests':ds,'divergence':len(set(ds))-1,'digest':ds[0]}; print(json.dumps(out,sort_keys=True)); return out
if __name__=='__main__': main()
