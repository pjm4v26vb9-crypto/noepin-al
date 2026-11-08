from __future__ import annotations
import dataclasses, json, statistics, time
import noepin_al_045_undo_planner as m
NOW=1_800_000_000

def catalog(n,prefix='B'):
    ops=[('communicate','draft',100,8,'DISCARD_DRAFT'),('remove_file','trash',90,15,'RESTORE'),('release','preview',100,5,'DISCARD'),('update_file','versioned_write',95,12,'ROLLBACK'),('deploy_change','dry_run',100,4,'DISCARD')]
    out=[]
    for i in range(n):
        obj,op,rev,risk,undo=ops[i%len(ops)]
        out.append(m.ActionCandidate(f'{prefix}-{i:05d}',obj,op,max(0,rev-(i%7)),min(100,risk+(i%11)),undo,'local',False,False,f'E-{prefix}-{i}'))
    # add requested irreversible candidates so full/prepared semantics are representative
    out.extend([
      m.ActionCandidate(f'{prefix}-SEND','communicate','send',5,65,'NONE','external_candidate',True,False,f'E-{prefix}-SEND'),
      m.ActionCandidate(f'{prefix}-DELETE','remove_file','delete',0,60,'NONE','local',False,True,f'E-{prefix}-DELETE'),
    ])
    return tuple(out)

def timed(fn,batches=5):
    vals=[]
    for _ in range(batches):
        t=time.perf_counter(); fn(); vals.append((time.perf_counter()-t)*1000)
    return vals

def main():
    p=m.default_policy(NOW); c=catalog(1998); prepared=m.prepare_catalog(p,c,now=NOW)
    req=m.PlanRequest('BENCH','communicate','send','E-BENCH',p.policy_id,p.version,p.authority_epoch)
    def full():
        d=None
        for _ in range(40): d=m.evaluate(req,p,c,now=NOW)
        return d
    def prep():
        d=None
        for _ in range(40): d=m.evaluate_prepared(req,p,prepared,now=NOW)
        return d
    full_result=full(); prep_result=prep(); full_ms=timed(full); prep_ms=timed(prep)

    base=list(catalog(4998,'D')); target=list(base)
    for i in range(5,55): target[i]=dataclasses.replace(target[i],risk_score=(target[i].risk_score+9)%100,evidence_binding=f'E-CH-{i}')
    target=target[5:]
    for i in range(5): target.append(m.ActionCandidate(f'D-NEW-{i}','communicate','draft',99,3,'DISCARD','local',False,False,f'E-NEW-{i}'))
    delta=m.build_catalog_delta(base,target); rebuilt=m.apply_catalog_delta(base,delta)
    full_bytes=len(m.canonical_json(m._normalize_candidates(target)).encode('utf-8'))
    delta_bytes=len(m.canonical_json(delta).encode('utf-8'))
    ptarget=m.prepare_catalog(p,target,now=NOW)
    known=dict(ptarget.item_fingerprints)
    for k in sorted(known)[:10]: del known[k]
    transfer=m.plan_catalog_sync(ptarget,known)
    out={
      'condition':'2,000 action candidates; 40 evaluations per batch; 5 batches; Python standard library',
      'full_materialization_median_ms':statistics.median(full_ms),
      'prepared_catalog_median_ms':statistics.median(prep_ms),
      'semantic_match':full_result==prep_result,
      'delta':{'base_items':len(base),'target_items':len(target),'changed':len(delta.changed),'removed':len(delta.removed_ids),'added':len(delta.added),'full_bytes':full_bytes,'delta_bytes':delta_bytes,'ratio_percent':delta_bytes/full_bytes*100,'reconstruction_fingerprint_match':m.catalog_fingerprint(rebuilt)==m.catalog_fingerprint(target)},
      'transfer_plan':{'target_items':len(target),'remote_known':len(known),'missing_or_changed':len(transfer.missing_or_changed_ids),'metadata_bytes_required':transfer.metadata_bytes_required,'full_resend_required':transfer.full_resend_required,'action_execution_authorized':transfer.action_execution_authorized}
    }
    print(json.dumps(out,sort_keys=True))
    return 0 if out['semantic_match'] and out['delta']['reconstruction_fingerprint_match'] else 2
if __name__=='__main__': raise SystemExit(main())
