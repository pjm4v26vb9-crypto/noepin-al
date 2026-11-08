from __future__ import annotations
import argparse,json
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import noepin_al_065_minimal_change_optimizer as m
NOW=1_800_000_000

def outcome(i:int):
    r=m.default_request(NOW); p=m.default_policy(NOW); c=m.default_changes(); g=m.default_goals(); ap=None
    k=i%12
    if k==1: r=replace(r,current_state_facts=('GOAL-A','GOAL-B'))
    elif k==2: r=replace(r,candidate_change_ids=('CHG-PROTECTED','CHG-B'))
    elif k==3: r=replace(r,candidate_change_ids=('CHG-NOISE',))
    elif k==4: r=replace(r,candidate_change_ids=('CHG-TIE-REV','CHG-TIE-IRREV'))
    elif k==5: r=replace(r,candidate_change_ids=('CHG-TIE-REV','CHG-TIE-UNKNOWN'))
    elif k==6: r=replace(r,candidate_change_ids=('CHG-APPROVAL',))
    elif k==7: r=replace(r,candidate_change_ids=('CHG-APPROVAL',)); ap=m.default_approval(NOW)
    elif k==8: p=replace(p,exact_search_limit=2)
    elif k==9: r=replace(r,expected_policy_version='BAD')
    elif k==10: c=tuple(replace(x,revoked=True) if x.change_id=='CHG-MIN' else x for x in c)
    elif k==11: r=replace(r,expires_at=NOW-1)
    d=m.evaluate(r,p,c,g,ap,now=NOW)
    return m.canonical_json(d)

def run_once(n=1000):
    vals=[outcome(i) for i in range(n)]
    return sha256(('\n'.join(vals)).encode()).hexdigest(),vals

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); args=ap.parse_args()
    digests=[]; runs=[]
    for _ in range(3):
        d,v=run_once(); digests.append(d); runs.append(v)
    divergence=sum(1 for i in range(1000) if not (runs[0][i]==runs[1][i]==runs[2][i]))
    out={'runs':3,'evaluations_per_run':1000,'total_evaluations':3000,'digests':digests,'digest_same':len(set(digests))==1,'digest':digests[0],'divergence':divergence}
    args.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,sort_keys=True)); return 0 if out['digest_same'] and divergence==0 else 2
if __name__=='__main__': raise SystemExit(main())
