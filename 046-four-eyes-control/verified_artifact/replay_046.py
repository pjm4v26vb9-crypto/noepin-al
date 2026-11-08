from __future__ import annotations
import argparse, dataclasses, json
import noepin_al_046_four_eyes as m

NOW=1_800_000_000

def one(i:int):
    p=m.default_policy(NOW)
    base=m.default_request(NOW)
    r=dataclasses.replace(base,request_id=f"R-{i}",action_id=f"A-{i%11}",evidence_binding=f"B-{i%11}",operation=("PUBLISH","DELETE","TRANSFER","CRITICAL_CONFIG_CHANGE")[i%4],scope=("external_candidate","workspace","critical_system")[i%3],risk_score=(i*7)%101)
    e1=m.ApprovalEvidence(f"E1-{i}",f"H-{i}",m.ActorKind.HUMAN,"OWNER",r.action_id,r.scope,True,NOW-10,NOW+1000,False,p.policy_id,p.version,p.authority_epoch,r.evidence_binding)
    e2=m.ApprovalEvidence(f"E2-{i}",f"A-{i}",m.ActorKind.AI,"AI_CONTROL",r.action_id,r.scope,True,NOW-9,NOW+1000,False,p.policy_id,p.version,p.authority_epoch,r.evidence_binding)
    if i%19==0: e2=dataclasses.replace(e2,revoked=True)
    if i%23==0: e2=dataclasses.replace(e2,approved=False)
    if i%29==0: e2=dataclasses.replace(e2,evidence_binding="WRONG")
    return m.evaluate(r,p,(e1,e2),now=NOW)

def run(evals:int): return m.assessment_digest(one(i) for i in range(evals))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--runs',type=int,default=3); ap.add_argument('--evals',type=int,default=1000); a=ap.parse_args()
    ds=[run(a.evals) for _ in range(a.runs)]
    out={'runs':a.runs,'evals_per_run':a.evals,'total_evaluations':a.runs*a.evals,'digests':ds,'digest':ds[0],'divergence':len(set(ds))-1}
    print(json.dumps(out,sort_keys=True)); return 0 if len(set(ds))==1 else 2
if __name__=='__main__': raise SystemExit(main())
