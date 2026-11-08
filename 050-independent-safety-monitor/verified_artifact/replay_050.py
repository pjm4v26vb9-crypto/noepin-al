from __future__ import annotations
import json
from dataclasses import replace
from pathlib import Path
import noepin_al_050_independent_safety_monitor as m
NOW=1_800_000_000

def corpus():
    p=m.default_policy(NOW); c=m.default_context(); base=m.default_observations(NOW)
    out=[]
    sevs=list(m.SignalSeverity)
    for i in range(100):
        risk=(i%10)/10
        sev=sevs[i%len(sevs)]
        x=m.SafetyObservation(f'R-{i}','WORKER-A','TASK-A',NOW-(i%100),'RISK',f'SIG-{i}',sev,risk,'FILE_READ','READ_LOCAL','PLAN-A',c.evidence_binding,True,True,False)
        req=m.default_request(NOW)
        if i%17==0: req=replace(req,requested_tool='EXTERNAL_SEND',requested_operation='SEND_SECRET')
        out.append((req,base+(x,)))
    return p,c,out

def run_once():
    p,c,items=corpus(); results=[]
    for _ in range(10):
        for req,obs in items: results.append(m.evaluate(req,p,c,obs,now=NOW))
    return m.verdicts_digest(results),len(results)

def main(out_path=None):
    runs=[]
    for _ in range(3):
        d,n=run_once(); runs.append({'digest':d,'evaluations':n})
    result={'schema':'NOEPIN_AL_REPLAY_V1','technology':50,'runs':runs,'total_evaluations':sum(x['evaluations'] for x in runs),'divergence':len({x['digest'] for x in runs})-1,'digest':runs[0]['digest']}
    text=json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+'\n'
    if out_path: Path(out_path).write_text(text,encoding='utf-8')
    print(text,end='')
    return 0 if result['divergence']==0 else 2
if __name__=='__main__': raise SystemExit(main())
