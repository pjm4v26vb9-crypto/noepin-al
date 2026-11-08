from __future__ import annotations
import json
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import noepin_al_059_external_trust_score as m
NOW=1_800_000_000

def run_once():
    p=m.default_policy(NOW); ps=(m.default_profile(NOW),); es=m.default_evidence(NOW); out=[]
    for i in range(1000):
        op=(m.TrustOperation.CONNECT,m.TrustOperation.ASSESS,m.TrustOperation.REQUEST_PRIVILEGE)[i%3]
        priv=(m.PrivilegeLevel.NONE,m.PrivilegeLevel.READ_ONLY,m.PrivilegeLevel.HIGH)[i%3]
        req=replace(m.default_request(NOW),request_id=f'R-{i:04d}',operation=op,requested_privilege=priv,high_impact_context=(i%17==0))
        if i%11==0: ev=(replace(es[0],impact=-20),)+es[1:]
        elif i%13==0: ev=es[:2]
        else: ev=es
        a=m.evaluate(req,p,ps,ev,now=NOW)
        out.append(m.canonical_json(a))
    return sha256(('\n'.join(out)).encode()).hexdigest()

def main():
    ds=[run_once() for _ in range(3)]; obj={'runs':3,'evaluations_per_run':1000,'total_evaluations':3000,'digests':ds,'digest':ds[0],'divergence':len(set(ds))-1}
    Path('REPLAY_RESULT.json').write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n'); print(json.dumps(obj,sort_keys=True))
if __name__=='__main__': main()
