from __future__ import annotations
from dataclasses import replace
import json, statistics, time
import noepin_al_043_safe_handoff as al

NOW=1_800_000_000

def build_items(n, intent='benchmark'):
    items=[al.make_context('CTX-TASK','task',intent,payload=b'task'),al.make_context('CTX-AUTH','authority',intent,payload=b'authority')]
    for i in range(n-2):
        items.append(al.make_context(f'CTX-{i:05d}',f'k-{i:05d}',intent,payload=(f'value-{i:05d}').encode()))
    return tuple(items)

def main():
    n=2000; loops=40; batches=5
    items=build_items(n)
    p=replace(al.default_policy(NOW),max_context_bytes=10_000_000)
    a=al.default_authority(); r=replace(al.default_request(NOW),intent='benchmark',context_items=items)
    prepared=al.prepare_context(items)
    full=[]; prep=[]; semantic=True
    for _ in range(batches):
        t=time.perf_counter()
        last1=None
        for i in range(loops):
            last1=al.evaluate(r,p,a,now=NOW)
        full.append((time.perf_counter()-t)*1000)
        t=time.perf_counter()
        last2=None
        for i in range(loops):
            last2=al.evaluate_prepared(r,p,a,prepared,now=NOW)
        prep.append((time.perf_counter()-t)*1000)
        semantic=semantic and (last1.decision==last2.decision and last1.token_candidate_fingerprint==last2.token_candidate_fingerprint and last1.trace_hash==last2.trace_hash)

    base=build_items(5000,'delta')
    target=list(base)
    # Remove 5 extra items (never required task/authority).
    del target[100:105]
    # Change 50 surviving extras.
    for j in range(200,250):
        idx=next(i for i,x in enumerate(target) if x.context_id==f'CTX-{j:05d}')
        old=target[idx]
        target[idx]=replace(old,version='2',content_fingerprint=al.content_fingerprint(f'changed-{j}'.encode()),byte_length=len(f'changed-{j}'))
    # Add 5.
    for j in range(5): target.append(al.make_context(f'CTX-ADD-{j}',f'add-{j}','delta',payload=f'add-{j}'.encode()))
    delta=al.compute_context_delta(base,target)
    rebuilt=al.apply_context_delta(base,delta)
    full_bytes=len(al.canonical_json(al.normalize_context(target)).encode())
    delta_bytes=len(al.canonical_json(delta).encode())
    prep_target=al.prepare_context(target)
    known=dict(prep_target.item_fingerprints)
    for cid in list(sorted(known))[-10:]: del known[cid]
    plan=al.plan_context_transfer(prep_target,known)
    result={
      'condition':{'context_items':n,'evaluations_per_batch':loops,'batches':batches,'runtime':'Python stdlib'},
      'full_materialization_ms':full,'prepared_manifest_ms':prep,
      'full_materialization_median_ms':statistics.median(full),'prepared_manifest_median_ms':statistics.median(prep),
      'semantic_match':semantic,
      'delta':{'base_items':len(base),'target_items':len(target),'changed':len(delta.changed_items),'removed':len(delta.removed_item_ids),'added':len(delta.added_items),'full_bytes':full_bytes,'delta_bytes':delta_bytes,'ratio_percent':delta_bytes/full_bytes*100,'reconstruction_fingerprint_match':al.fingerprint(rebuilt)==al.fingerprint(al.normalize_context(target))},
      'transfer_plan':{'target_items':len(target),'remote_known':len(known),'missing':len(plan.missing_context_ids),'bytes_required':plan.bytes_required,'full_resend_required':plan.full_resend_required}
    }
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
    return 0 if semantic and result['delta']['reconstruction_fingerprint_match'] and len(plan.missing_context_ids)==10 else 2
if __name__=='__main__': raise SystemExit(main())
