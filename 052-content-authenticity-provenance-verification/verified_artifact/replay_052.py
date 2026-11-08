from __future__ import annotations
import argparse,json
from dataclasses import replace
from pathlib import Path
import noepin_al_052_content_authenticity as m
NOW=1_800_000_000

def one(i):
    p=m.default_policy(NOW); r=m.default_request(NOW); steps,sigs=m.default_evidence(NOW); k=i%10
    if k==0: return m.evaluate(r,p,steps,sigs,now=NOW)
    if k==1: return m.evaluate(r,p,(steps[0],replace(steps[1],input_sha256=m.fingerprint(('broken',i)))),sigs,now=NOW)
    if k==2: return m.evaluate(r,p,steps,(replace(sigs[0],signature_verified=False),),now=NOW)
    if k==3: return m.evaluate(r,p,tuple(replace(x,origin_trust=.65) for x in steps),sigs,now=NOW)
    if k==4: return m.evaluate(r,p,tuple(replace(x,origin_trust=.3) for x in steps),sigs,now=NOW)
    if k==5: return m.evaluate(replace(r,expected_policy_version='bad'),p,steps,sigs,now=NOW)
    if k==6: return m.evaluate(r,p,steps,(),now=NOW)
    if k==7: return m.evaluate(replace(r,purpose='UNAPPROVED'),p,steps,sigs,now=NOW)
    if k==8:
        prepared=m.prepare_registry(p,steps,sigs,now=NOW); return m.evaluate_prepared(r,p,prepared,now=NOW)
    return m.evaluate(replace(r,expected_origin_id='OTHER'),p,steps,sigs,now=NOW)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); digs=[]
    for _ in range(3): digs.append(m.verdicts_digest(one(i) for i in range(1000)))
    out={'schema':'NOEPIN_AL_REPLAY_V1','technology':52,'runs':3,'evaluations_per_run':1000,'total_evaluations':3000,'digests':digs,'divergence':len(set(digs))-1,'digest':digs[0]}
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,sort_keys=True)); return 0 if out['divergence']==0 else 2
if __name__=='__main__': raise SystemExit(main())
