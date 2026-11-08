from __future__ import annotations
import argparse,json
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import noepin_al_063_counterfactual_action_tree as m
NOW=1_800_000_000

def one(i:int):
    r=m.default_request(NOW); p=m.default_policy(NOW); mo=m.default_effect_model(NOW); a=m.default_actions(); b=m.default_branches(); approval=None
    mode=i%5
    if mode==1:
        mo=replace(mo,confidence=.50)
    elif mode==2:
        b=tuple(replace(x,severe_loss=True,risk=.8) if x.branch_id=='B-SAFE-DO' else x for x in b)
    elif mode==3:
        alt=replace(b[2],branch_id='B-SAFER',kind=m.BranchKind.SAFER_ALTERNATIVE,safer_alternative_for='ACT-SAFE',goal_utility=.90,risk=.05,predicted_state_fingerprint='ALT')
        b=b+(alt,)
    elif mode==4:
        a=tuple(replace(x,approval_required=True) if x.action_id=='ACT-SAFE' else x for x in a)
        approval=m.default_approval(NOW)
    return m.evaluate(r,p,mo,a,b,approval,now=NOW)

def run_once(n:int):
    rows=[]
    for i in range(n): rows.append(m.canonical_json(one(i)))
    blob='\n'.join(rows).encode(); return sha256(blob).hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--runs',type=int,default=3); ap.add_argument('--evaluations',type=int,default=1000); a=ap.parse_args()
    digests=[run_once(a.evaluations) for _ in range(a.runs)]
    out={'runs':a.runs,'evaluations_per_run':a.evaluations,'total_evaluations':a.runs*a.evaluations,'digests':digests,'digest_same':len(set(digests))==1,'divergence':0 if len(set(digests))==1 else len(set(digests))-1,'digest':digests[0]}
    a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True)); return 0 if out['divergence']==0 else 2
if __name__=='__main__': raise SystemExit(main())
