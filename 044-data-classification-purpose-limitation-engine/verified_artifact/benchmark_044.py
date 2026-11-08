from __future__ import annotations
import dataclasses, json, statistics, time
import noepin_al_044_data_purpose as m

NOW=1_800_000_000

def make_registry(n):
    classes=('PUBLIC','INTERNAL','CONFIDENTIAL','RESTRICTED','PERSONAL')
    purposes={
      'PUBLIC':{'publish','analysis','verification'},'INTERNAL':{'analysis','verification','build'},
      'CONFIDENTIAL':{'analysis','verification','build'},'RESTRICTED':{'verification','security_review'},
      'PERSONAL':{'support','subject_service','verification'}
    }
    return tuple(m.make_state(f'D{i:05d}',classes[i%5],purposes[classes[i%5]],payload_seed=f'payload-{i%17}') for i in range(n))

def main():
    p=m.default_policy(NOW)
    states=make_registry(2000)
    req=m.DataUseRequest('BENCH','verification','secure','local_ai',('D00001','D00002','D00003'),'BIND-044',p.policy_id,p.version,p.authority_epoch)
    pre=m.prepare_registry(p,states,now=NOW)
    full=[]; prepared=[]
    for _ in range(5):
        t=time.perf_counter()
        vals=[m.evaluate(dataclasses.replace(req,request_id=f'F{i}'),p,states,now=NOW) for i in range(40)]
        full.append((time.perf_counter()-t)*1000)
        t=time.perf_counter()
        vals2=[m.evaluate_prepared(dataclasses.replace(req,request_id=f'F{i}'),p,pre,now=NOW) for i in range(40)]
        prepared.append((time.perf_counter()-t)*1000)
        assert [x.decision for x in vals]==[x.decision for x in vals2]
    base=make_registry(5000)
    target=list(base)
    for i in range(50):
        idx=100+i
        target[idx]=dataclasses.replace(target[idx],bound_purposes=frozenset(set(target[idx].bound_purposes)|{'verification'}),label_source='BENCH_CHANGED')
    del target[1000:1005]
    for i in range(5): target.append(m.make_state(f'NEW{i:03d}','INTERNAL',{'verification','build'},payload_seed='new'))
    target=tuple(target)
    d=m.compute_registry_delta(base,target)
    rebuilt=m.apply_registry_delta(base,d)
    full_bytes=len(m.canonical_json(target).encode('utf-8'))
    delta_bytes=len(m.canonical_json(d).encode('utf-8'))
    target_pre=m.prepare_registry(p,target,now=NOW)
    remote=dict(target_pre.item_fingerprints)
    for k in sorted(remote)[-10:]: del remote[k]
    plan=m.plan_metadata_sync(target_pre,remote)
    result={
      'condition':'2,000 metadata states; 40 evaluations per batch; 5 batches; Python standard library',
      'full_materialization_median_ms':statistics.median(full),
      'prepared_registry_median_ms':statistics.median(prepared),
      'semantic_match':True,
      'delta':{
        'base_items':5000,'target_items':len(target),'changed':len(d.changed),'removed':len(d.removed_ids),'added':len(d.added),
        'full_bytes':full_bytes,'delta_bytes':delta_bytes,'ratio_percent':delta_bytes/full_bytes*100,
        'reconstruction_fingerprint_match':m.registry_fingerprint(rebuilt)==m.registry_fingerprint(target)
      },
      'sync_plan':{
        'target_items':len(target),'remote_known':len(remote),'missing_or_changed':len(plan.missing_or_changed_ids),
        'metadata_bytes_required':plan.metadata_bytes_required,'full_metadata_bytes':plan.full_metadata_bytes,
        'full_resend_required':plan.full_resend_required,'payload_transfer_authorized':plan.payload_transfer_authorized
      }
    }
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))

if __name__=='__main__': main()
