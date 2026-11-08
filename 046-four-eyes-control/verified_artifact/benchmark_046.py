from __future__ import annotations
import dataclasses, json, statistics, time
import noepin_al_046_four_eyes as m
NOW=1_800_000_000

def make_evidence(n:int, *, offset:int=0):
    p=m.default_policy(NOW); out=[]
    roles=("OWNER","REVIEWER","SECURITY","AI_CONTROL")
    for i in range(n):
        j=i+offset; kind=m.ActorKind.HUMAN if j%3 else m.ActorKind.AI
        out.append(m.ApprovalEvidence(f"E-{j:06d}",f"ACTOR-{j:06d}",kind,roles[j%4],f"ACTION-{j%500:04d}",("workspace","external_candidate","critical_system")[j%3],True,NOW-100,NOW+10000,False,p.policy_id,p.version,p.authority_epoch,f"B-{j%500:04d}"))
    return tuple(out)

def payload(es): return [m._canonical(x) for x in es]

def bench():
    p=m.default_policy(NOW); es=make_evidence(2000); raw=payload(es); prepared=m.prepare_registry(p,es,now=NOW)
    r0=m.default_request(NOW)
    reqs=[dataclasses.replace(r0,request_id=f"BR-{i}",action_id=f"ACTION-{i%500:04d}",scope=("workspace","external_candidate","critical_system")[i%3],operation=("PUBLISH","DELETE","TRANSFER","CRITICAL_CONFIG_CHANGE")[i%4],evidence_binding=f"B-{i%500:04d}") for i in range(40)]
    full=[]; prep=[]; semantic=True
    for _ in range(5):
        t=time.perf_counter(); a=[]
        for r in reqs:
            pr=m.registry_from_dict(p,raw,now=NOW); a.append(m.evaluate_prepared(r,p,pr,now=NOW))
        full.append((time.perf_counter()-t)*1000)
        t=time.perf_counter(); b=[m.evaluate_prepared(r,p,prepared,now=NOW) for r in reqs]; prep.append((time.perf_counter()-t)*1000)
        semantic &= m.assessment_digest(a)==m.assessment_digest(b)

    base=list(make_evidence(5000)); target=list(base)
    # non-overlapping: change 50 in middle, remove first 5, add 5 new
    for i in range(100,150): target[i]=dataclasses.replace(target[i],role="REVIEWER" if target[i].role!="REVIEWER" else "SECURITY")
    target=target[5:]
    target.extend(make_evidence(5,offset=10000))
    d=m.build_registry_delta(base,target); rebuilt=m.apply_registry_delta(base,d)
    full_bytes=len(m.canonical_json(tuple(sorted(target,key=lambda x:x.evidence_id))).encode())
    delta_bytes=len(m.canonical_json(d).encode())
    pr_target=m.prepare_registry(p,target,now=NOW)
    known=dict(pr_target.item_fingerprints)
    for k in sorted(known)[-10:]: known.pop(k)
    plan=m.plan_registry_sync(pr_target,known)
    out={
      'condition':'2000 approval evidence; 40 evaluations per batch; 5 batches; Python standard library',
      'full_materialization_median_ms':statistics.median(full),
      'prepared_registry_median_ms':statistics.median(prep),
      'semantic_match':semantic,
      'delta':{'base_items':len(base),'target_items':len(target),'changed':len(d.changed),'removed':len(d.removed_ids),'added':len(d.added),'full_bytes':full_bytes,'delta_bytes':delta_bytes,'ratio_percent':delta_bytes/full_bytes*100,'reconstruction_fingerprint_match':m.registry_fingerprint(rebuilt)==m.registry_fingerprint(target)},
      'sync_plan':{'target_items':len(target),'remote_known':len(known),'missing_or_changed':len(plan.missing_or_changed_ids),'metadata_bytes_required':plan.metadata_bytes_required,'full_resend_required':plan.full_resend_required,'permission_granted':plan.permission_granted,'action_execution_authorized':plan.action_execution_authorized}
    }
    print(json.dumps(out,sort_keys=True)); return out
if __name__=='__main__': bench()
