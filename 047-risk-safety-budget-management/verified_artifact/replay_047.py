from __future__ import annotations
import argparse, dataclasses, json
import noepin_al_047_risk_budget as m

NOW=1_800_000_000

def one(i:int):
    p=m.default_policy(NOW)
    base=m.default_request(NOW)
    task=f"TASK-{i%17}"
    r=dataclasses.replace(base,request_id=f"R-{i}",task_id=task,candidate_id=f"C-{i}",
        operation=("LOCAL_TEST","DRAFT","TRASH","PREVIEW","VERSIONED_WRITE","DRY_RUN")[i%6],
        scope=("artifact","workspace","external_candidate","critical_system_candidate")[i%4],
        candidate_risk_units=(i*17)%301,candidate_impact_units=(i*23)%401,evidence_binding=f"B-{i%7}")
    es=[]
    for j in range(i%7):
        es.append(m.RiskLedgerEntry(f"E-{i}-{j}",task,("LOCAL_TEST","DRAFT","PREVIEW")[j%3],r.scope,
            (i+j*31)%230,(i+j*29)%210,NOW-100+j,NOW+1000,False,p.policy_id,p.version,p.authority_epoch,r.evidence_binding))
    if i%19==0 and es: es[-1]=dataclasses.replace(es[-1],revoked=True)
    if i%23==0 and es: es[-1]=dataclasses.replace(es[-1],expires_at=NOW-1,occurred_at=NOW-100)
    if i%29==0 and es: es[-1]=dataclasses.replace(es[-1],evidence_binding="WRONG")
    return m.evaluate(r,p,tuple(es),now=NOW)

def run(evals:int): return m.assessment_digest(one(i) for i in range(evals))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--runs',type=int,default=3); ap.add_argument('--evals',type=int,default=1000); a=ap.parse_args()
    ds=[run(a.evals) for _ in range(a.runs)]
    out={'runs':a.runs,'evals_per_run':a.evals,'total_evaluations':a.runs*a.evals,'digests':ds,'digest':ds[0],'divergence':len(set(ds))-1}
    print(json.dumps(out,sort_keys=True)); return 0 if len(set(ds))==1 else 2
if __name__=='__main__': raise SystemExit(main())
