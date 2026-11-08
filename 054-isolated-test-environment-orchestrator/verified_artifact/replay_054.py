from __future__ import annotations
import argparse,json
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import noepin_al_054_isolated_test_orchestrator as m
NOW=1_800_000_000

def once(n:int):
    p=m.default_policy(NOW); r=m.default_request(NOW); s,e=m.default_registry(NOW); out=[]
    for i in range(n):
        k=i%8
        rr=r; ss=s; ee=e
        if k==1: ee=(replace(e[0],network_escaped=True),)
        elif k==2: rr=replace(r,risk=m.TestRisk.HIGH)
        elif k==3: ee=()
        elif k==4: ss=(replace(s[0],privileged=True),)
        elif k==5: ee=(replace(e[0],real_secret_accessed=True),)
        elif k==6: rr=replace(r,subject_type='TOOL')
        elif k==7: rr=replace(r,requested_network_mode='LOOPBACK_ONLY'); ss=(replace(s[0],network_mode='LOOPBACK_ONLY'),)
        out.append(m.canonical_json(m.evaluate(rr,p,ss,ee,now=NOW)))
    return sha256(('\n'.join(out)).encode()).hexdigest()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--runs',type=int,default=3); ap.add_argument('--evaluations',type=int,default=1000); ap.add_argument('--out',type=Path); a=ap.parse_args()
    ds=[once(a.evaluations) for _ in range(a.runs)]; result={'runs':a.runs,'evaluations_per_run':a.evaluations,'total_evaluations':a.runs*a.evaluations,'digests':ds,'digest':ds[0],'divergence':len(set(ds))-1}
    text=json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+'\n'; print(text,end='');
    if a.out: a.out.write_text(text,encoding='utf-8')
    return 0 if result['divergence']==0 else 2
if __name__=='__main__': raise SystemExit(main())
