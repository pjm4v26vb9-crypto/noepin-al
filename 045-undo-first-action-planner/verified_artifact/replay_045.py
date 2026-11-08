from __future__ import annotations
import argparse, json
import noepin_al_045_undo_planner as m

NOW=1_800_000_000

def one_run(n=1000):
    p=m.default_policy(NOW); c=m.default_candidates(); prepared=m.prepare_catalog(p,c,now=NOW)
    objectives=[('remove_file','delete'),('communicate','send'),('release','publish'),('update_file','overwrite'),('deploy_change','deploy')]
    vals=[]
    for i in range(n):
        obj,op=objectives[i%len(objectives)]
        r=m.PlanRequest(f'REPLAY-{i}',obj,op,f'E-{i}',p.policy_id,p.version,p.authority_epoch,False,False)
        vals.append(m.evaluate_prepared(r,p,prepared,now=NOW))
    return m.assessment_digest(vals)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--runs',type=int,default=3); ap.add_argument('--n',type=int,default=1000)
    a=ap.parse_args(); dig=[one_run(a.n) for _ in range(a.runs)]
    out={'runs':a.runs,'evaluations_per_run':a.n,'evaluations':a.runs*a.n,'digests':dig,'divergence':len(set(dig))-1,'digest':dig[0]}
    print(json.dumps(out,sort_keys=True))
    return 0 if out['divergence']==0 else 2
if __name__=='__main__': raise SystemExit(main())
