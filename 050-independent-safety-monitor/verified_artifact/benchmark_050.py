from __future__ import annotations
import json, statistics, time
from dataclasses import replace
from pathlib import Path
import noepin_al_050_independent_safety_monitor as m
NOW=1_800_000_000

def make_items(n):
    c=m.default_context(); out=[]
    sevs=list(m.SignalSeverity)
    for i in range(n):
        out.append(m.SafetyObservation(f'B-{i:05d}','WORKER-A' if i%3 else 'OTHER', 'TASK-A' if i%5 else 'OTHER-TASK', NOW-(i%1000), ['PLAN','TOOL','NETWORK','RISK'][i%4],f'SIG-{i}',sevs[i%5],(i%30)/100,'FILE_READ','READ_LOCAL','PLAN-A',c.evidence_binding,True,True,False))
    return tuple(out)

def main(out_path=None):
    p=m.default_policy(NOW); c=m.default_context(); req=m.default_request(NOW)
    items=make_items(2000)
    prepared=m.prepare_registry(p,c,items,now=NOW)
    full=[]; prep=[]; a=None; b=None
    for _ in range(5):
        t=time.perf_counter()
        for _ in range(40): a=m.evaluate(req,p,c,items,now=NOW)
        full.append((time.perf_counter()-t)*1000)
        t=time.perf_counter()
        for _ in range(40): b=m.evaluate_prepared(req,p,c,prepared,now=NOW)
        prep.append((time.perf_counter()-t)*1000)
    base=make_items(5000)
    target=list(base)
    for i in range(50,100): target[i]=replace(target[i],risk_score=min(.99,target[i].risk_score+.2))
    del target[:5]
    for i in range(5):
        target.append(m.SafetyObservation(f'NEW-{i}','WORKER-A','TASK-A',NOW-1,'RISK',f'NEW-SIG-{i}',m.SignalSeverity.MEDIUM,.3,'FILE_READ','READ_LOCAL','PLAN-A',c.evidence_binding,True,True,False))
    target=tuple(target)
    d=m.make_registry_delta(base,target); rebuilt=m.apply_registry_delta(base,d)
    full_bytes=len(m.canonical_json(target).encode()); delta_bytes=len(m.canonical_json(d).encode())
    known={o.observation_id:m.fingerprint(o) for o in target[:4990]}
    sync=m.plan_registry_sync(target,known)
    result={'schema':'NOEPIN_AL_BENCHMARK_V1','technology':50,'condition':'2000 observations; 40 evaluations per batch; 5 batches; Python standard library','full_materialization_median_ms':statistics.median(full),'prepared_registry_median_ms':statistics.median(prep),'semantic_match':m.canonical_json(a)==m.canonical_json(b),'delta':{'base_items':len(base),'target_items':len(target),'changed':len(d.changed_observations),'removed':len(d.removed_observation_ids),'added':len(d.added_observations),'full_bytes':full_bytes,'delta_bytes':delta_bytes,'ratio_percent':delta_bytes/full_bytes*100,'reconstruction_fingerprint_match':m.registry_fingerprint(rebuilt)==m.registry_fingerprint(target)},'sync':{'target_items':len(target),'remote_known':4990,'missing_or_changed':len(sync.missing_or_changed_observation_ids),'metadata_bytes_required':sync.metadata_bytes_required,'full_resend_required':sync.full_resend_required,'permission_granted':sync.permission_granted,'block_execution_authorized':sync.block_execution_authorized,'tool_execution_authorized':sync.tool_execution_authorized}}
    text=json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+'\n'
    if out_path: Path(out_path).write_text(text,encoding='utf-8')
    print(text,end='')
if __name__=='__main__': main()
