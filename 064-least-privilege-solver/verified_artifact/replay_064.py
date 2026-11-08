from __future__ import annotations
import argparse,json
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import noepin_al_064_least_privilege_solver as m
NOW=1_800_000_000

def outcome(i:int):
    r=m.default_request(NOW); p=m.default_policy(NOW); c=m.default_capabilities(NOW); e=m.default_edges(); ro=m.default_roles(NOW); a=m.default_actions(); q=m.default_requirements(); ap=None
    k=i%12
    if k==1: r=replace(r,requested_capabilities=('CAP_READ',))
    elif k==2: p=replace(p,exact_search_limit=2)
    elif k==3: q=(m.RequirementClause('REQ-ADMIN','ACT-SAFE',('CAP_ADMIN',),'LP-BIND',True,False),)
    elif k==4: r=replace(r,goal_id='GOAL-REVIEW',action_id='ACT-REVIEW',requested_capabilities=('CAP_ELEVATED_REVIEW',))
    elif k==5: r=replace(r,goal_id='GOAL-REVIEW',action_id='ACT-REVIEW',requested_capabilities=('CAP_ELEVATED_REVIEW',)); ap=m.default_approval(NOW)
    elif k==6: r=replace(r,expected_policy_version='BAD')
    elif k==7: r=replace(r,role_id='ROLE_ADMIN',requested_capabilities=('CAP_READ','CAP_WRITE_SCOPED','CAP_WRITE_GLOBAL','CAP_NOTIFY'))
    elif k==8: c=tuple(replace(x,revoked=True) if x.capability_id=='CAP_WRITE_SCOPED' else x for x in c)
    elif k==9: r=replace(r,action_id='MISSING')
    elif k==10: e=e+(m.CapabilityEdge('EDGE-CYCLE','CAP_READ','CAP_WRITE_SCOPED','LP-BIND',True,False,'LP-POLICY','1','LP-EPOCH'),)
    elif k==11: r=replace(r,expires_at=NOW-1)
    d=m.evaluate(r,p,c,e,ro,a,q,ap,now=NOW)
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
