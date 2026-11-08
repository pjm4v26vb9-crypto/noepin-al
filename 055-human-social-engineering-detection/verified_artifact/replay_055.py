from __future__ import annotations
import argparse,json
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import noepin_al_055_social_engineering as m
NOW=1_800_000_000

def once(n):
    p=m.default_policy(NOW); c=m.default_context(NOW); e=m.default_evidence(NOW); out=[]
    for i in range(n):
        k=i%8; cc=c; ee=e
        if k==1: ee=(replace(e[0],urgency=m.SignalLevel.HIGH),)
        elif k==2: ee=(replace(e[0],bypass_request=m.SignalLevel.HIGH),)
        elif k==3: cc=replace(c,action_type='GRANT_PERMISSION',risk_label='HIGH')
        elif k==4: ee=(replace(e[0],verified=False),)
        elif k==5: ee=(replace(e[0],continued_after_decline=True),); cc=replace(c,current_user_decision='DECLINED')
        elif k==6: ee=(replace(e[0],reciprocity_pressure=m.SignalLevel.LOW),)
        elif k==7: ee=(replace(e[0],credential_request=m.SignalLevel.HIGH),)
        out.append(m.canonical_json(m.evaluate(cc,p,ee,now=NOW)))
    return sha256(('\n'.join(out)).encode()).hexdigest()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--runs',type=int,default=3); ap.add_argument('--evaluations',type=int,default=1000); ap.add_argument('--out',type=Path); a=ap.parse_args()
    ds=[once(a.evaluations) for _ in range(a.runs)]; r={'runs':a.runs,'evaluations_per_run':a.evaluations,'total_evaluations':a.runs*a.evaluations,'digests':ds,'digest':ds[0],'divergence':len(set(ds))-1}
    txt=json.dumps(r,ensure_ascii=False,indent=2,sort_keys=True)+'\n'; print(txt,end='');
    if a.out: a.out.write_text(txt,encoding='utf-8')
    return 0 if r['divergence']==0 else 2
if __name__=='__main__': raise SystemExit(main())
