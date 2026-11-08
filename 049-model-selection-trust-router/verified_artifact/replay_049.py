from __future__ import annotations
import dataclasses, json
from noepin_al_049_model_trust_router import *
NOW=1_800_000_000

def cases():
    out=[]; p=default_policy(NOW); ps=default_profiles(NOW)
    sens=list(Sensitivity)
    for i in range(100):
        s=sens[i%4]; risk=(i%10)/10.0
        r=dataclasses.replace(default_request(NOW),request_id=f"REPLAY-{i:03d}",task_id=f"TASK-{i%7}",sensitivity=s,risk_score=risk,external_processing_allowed=(i%5!=0),human_approval_evidence_verified=(i%3==0))
        q=list(ps)
        if i%11==0: q[1]=dataclasses.replace(q[1],evidence_verified=False)
        if i%13==0: q[2]=dataclasses.replace(q[2],provider_id="UNTRUSTED")
        out.append((r,p,tuple(q)))
    return tuple(out)

def run_once(): return assessment_digest(evaluate(r,p,ps,now=NOW) for r,p,ps in cases())
def main():
    ds=[]
    for _ in range(3):
        vals=[]
        for _ in range(10): vals.extend(evaluate(r,p,ps,now=NOW) for r,p,ps in cases())
        ds.append(assessment_digest(vals))
    result={"schema":"NOEPIN_AL_REPLAY_RESULT_V1","technology":49,"runs":3,"evaluations_per_run":1000,"total_evaluations":3000,"digests":ds,"divergence":len(set(ds))-1,"digest":ds[0]}
    print(json.dumps(result,ensure_ascii=False,sort_keys=True)); return result
if __name__=='__main__': main()
