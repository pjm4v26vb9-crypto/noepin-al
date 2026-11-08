from __future__ import annotations
import dataclasses, json, statistics, time
import noepin_al_047_risk_budget as m
NOW=1_800_000_000

def make_entries(n:int, *, offset:int=0):
    p=m.default_policy(NOW); out=[]
    ops=("LOCAL_TEST","DRAFT","TRASH","PREVIEW","VERSIONED_WRITE","DRY_RUN")
    scopes=("artifact","workspace","external_candidate","critical_system_candidate")
    for i in range(n):
        j=i+offset
        out.append(m.RiskLedgerEntry(f"E-{j:06d}",f"TASK-{j%500:04d}",ops[j%6],scopes[j%4],
            (j*7)%180,(j*11)%170,NOW-10000+(j%9000),NOW+100000,False,p.policy_id,p.version,p.authority_epoch,f"B-{j%500:04d}"))
    return tuple(out)

def payload(es): return [m._canonical(x) for x in es]

def bench():
    p=m.default_policy(NOW); es=make_entries(2000); raw=payload(es); prepared=m.prepare_registry(p,es,now=NOW)
    base=m.default_request(NOW)
    reqs=[dataclasses.replace(base,request_id=f"BR-{i}",task_id=f"TASK-{i%500:04d}",candidate_id=f"C-{i}",
        operation=("LOCAL_TEST","DRAFT","TRASH","PREVIEW")[i%4],scope=("artifact","workspace","external_candidate","critical_system_candidate")[i%4],
        candidate_risk_units=(i*13)%250,candidate_impact_units=(i*17)%260,evidence_binding=f"B-{i%500:04d}") for i in range(40)]
    full=[]; prep=[]; semantic=True
    for _ in range(5):
        t=time.perf_counter(); a=[]
        for r in reqs:
            pr=m.registry_from_dict(p,raw,now=NOW); a.append(m.evaluate_prepared(r,p,pr,now=NOW))
        full.append((time.perf_counter()-t)*1000)
        t=time.perf_counter(); b=[m.evaluate_prepared(r,p,prepared,now=NOW) for r in reqs]; prep.append((time.perf_counter()-t)*1000)
        semantic &= m.assessment_digest(a)==m.assessment_digest(b)

    base_entries=list(make_entries(5000)); target=list(base_entries)
    for i in range(100,150): target[i]=dataclasses.replace(target[i],risk_units=(target[i].risk_units+37)%181)
    target=target[5:]
    target.extend(make_entries(5,offset=10000))
    d=m.build_registry_delta(base_entries,target); rebuilt=m.apply_registry_delta(base_entries,d)
    full_bytes=len(m.canonical_json(tuple(sorted(target,key=lambda x:x.entry_id))).encode())
    delta_bytes=len(m.canonical_json(d).encode())
    pr_target=m.prepare_registry(p,target,now=NOW)
    known=dict(pr_target.item_fingerprints)
    for k in sorted(known)[-10:]: known.pop(k)
    plan=m.plan_registry_sync(pr_target,known)
    out={
      'condition':'2000 risk ledger entries; 40 evaluations per batch; 5 batches; Python standard library',
      'full_materialization_median_ms':statistics.median(full),
      'prepared_registry_median_ms':statistics.median(prep),
      'semantic_match':semantic,
      'delta':{'base_items':len(base_entries),'target_items':len(target),'changed':len(d.changed),'removed':len(d.removed_ids),'added':len(d.added),'full_bytes':full_bytes,'delta_bytes':delta_bytes,'ratio_percent':delta_bytes/full_bytes*100,'reconstruction_fingerprint_match':m.registry_fingerprint(rebuilt)==m.registry_fingerprint(target)},
      'sync_plan':{'target_items':len(target),'remote_known':len(known),'missing_or_changed':len(plan.missing_or_changed_ids),'metadata_bytes_required':plan.metadata_bytes_required,'full_resend_required':plan.full_resend_required,'permission_granted':plan.permission_granted,'action_execution_authorized':plan.action_execution_authorized,'stop_execution_authorized':plan.stop_execution_authorized}
    }
    print(json.dumps(out,sort_keys=True)); return out
if __name__=='__main__': bench()
