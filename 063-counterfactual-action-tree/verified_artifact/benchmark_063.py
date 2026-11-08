from __future__ import annotations
import argparse,json,statistics,time
from dataclasses import replace
from pathlib import Path
import noepin_al_063_counterfactual_action_tree as m
NOW=1_800_000_000

def dataset(n_actions=1000):
    p=m.default_policy(NOW); mo=m.default_effect_model(NOW); req=m.default_request(NOW)
    actions=list(m.default_actions()); branches=list(m.default_branches())
    for i in range(n_actions):
        aid=f'X-ACT-{i:04d}'
        actions.append(m.ActionCandidate(aid,f'aux {i}','CTX-063',.7,True,False,False,False,True,False,'EFFECT-063','1'))
        branches.append(m.CounterfactualBranch(f'X-B-{i:04d}-DO',aid,'ROOT',1,m.BranchKind.DO,'CTX-063',True,True,False,'EFFECT-063','1',.95,.7,.2,False,False,False,False,m.fingerprint((i,'do')),''))
        branches.append(m.CounterfactualBranch(f'X-B-{i:04d}-NO',aid,'ROOT',1,m.BranchKind.DO_NOT,'CTX-063',True,True,False,'EFFECT-063','1',.95,.1,.05,False,False,False,False,m.fingerprint((i,'no')),''))
    p=replace(p,max_branches=len(branches)+1000)
    return req,p,mo,tuple(actions),tuple(branches)

def median_ms(fn,batches=5,iters=10):
    vals=[]
    for _ in range(batches):
        t=time.perf_counter()
        for _ in range(iters): fn()
        vals.append((time.perf_counter()-t)*1000)
    return statistics.median(vals),vals

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--actions',type=int,default=1000); ap.add_argument('--iters',type=int,default=10); ap.add_argument('--batches',type=int,default=5); a=ap.parse_args()
    req,p,mo,actions,branches=dataset(a.actions)
    prepared=m.prepare_tree(p,mo,actions,branches,graph_binding=req.graph_binding,now=NOW)
    if not m.validate_prepared_state(prepared,p,mo,actions,branches,graph_binding=req.graph_binding): raise SystemExit('prepared integrity fail')
    full_result=m.evaluate(req,p,mo,actions,branches,now=NOW); prepared_result=m.evaluate_prepared(req,p,mo,prepared,now=NOW)
    semantic=m.canonical_json(full_result)==m.canonical_json(prepared_result)
    def full():
        q=m.prepare_tree(p,mo,actions,branches,graph_binding=req.graph_binding,now=NOW); return m.evaluate_prepared(req,p,mo,q,now=NOW)
    def reused(): return m.evaluate_prepared(req,p,mo,prepared,now=NOW)
    full_med,full_batches=median_ms(full,a.batches,a.iters); prep_med,prep_batches=median_ms(reused,a.batches,a.iters)
    # Target state: 50 changed actions, 50 changed branches, 5 removed action-pairs, 5 added action-pairs.
    target_actions=list(actions); target_branches=list(branches)
    for i in range(50):
        idx=2+i; target_actions[idx]=replace(target_actions[idx],label=f'changed {i}')
        bid=f'X-B-{i:04d}-DO'; target_branches=[replace(x,risk=.21) if x.branch_id==bid else x for x in target_branches]
    remove_ids={f'X-ACT-{i:04d}' for i in range(50,55)}
    target_actions=[x for x in target_actions if x.action_id not in remove_ids]
    target_branches=[x for x in target_branches if x.action_id not in remove_ids]
    for i in range(5):
        aid=f'NEW-ACT-{i:02d}'
        target_actions.append(m.ActionCandidate(aid,f'new {i}','CTX-063',.7,True,False,False,False,True,False,'EFFECT-063','1'))
        target_branches.append(m.CounterfactualBranch(f'NEW-B-{i:02d}-DO',aid,'ROOT',1,m.BranchKind.DO,'CTX-063',True,True,False,'EFFECT-063','1',.95,.7,.2,False,False,False,False,m.fingerprint((i,'newdo')),''))
        target_branches.append(m.CounterfactualBranch(f'NEW-B-{i:02d}-NO',aid,'ROOT',1,m.BranchKind.DO_NOT,'CTX-063',True,True,False,'EFFECT-063','1',.95,.1,.05,False,False,False,False,m.fingerprint((i,'newno')),''))
    target=m.prepare_tree(p,mo,tuple(target_actions),tuple(target_branches),graph_binding=req.graph_binding,now=NOW+1)
    delta=m.make_delta(prepared,target); rebuilt=m.apply_delta(prepared,delta,generated_at=NOW+1)
    reconstruction=(rebuilt.registry_fingerprint==target.registry_fingerprint and dict(rebuilt.action_fingerprints)==dict(target.action_fingerprints) and dict(rebuilt.branch_fingerprints)==dict(target.branch_fingerprints))
    full_bytes=len(m.canonical_json({'actions':target.actions_by_id,'branches':target.branches_by_id}).encode())
    delta_bytes=len(m.canonical_json(delta).encode())
    known_a=dict(target.action_fingerprints); known_b=dict(target.branch_fingerprints)
    for k in list(sorted(known_a))[:10]: known_a.pop(k)
    for k in list(sorted(known_b))[:10]: known_b.pop(k)
    sync=m.sync_plan(target,known_a,known_b)
    out={
      'runtime':'Python standard library','dataset':{'aux_actions':a.actions,'total_actions':len(actions),'total_branches':len(branches)},'iterations_per_batch':a.iters,'batches':a.batches,
      'full_materialization_median_ms':full_med,'prepared_tree_median_ms':prep_med,'full_batch_ms':full_batches,'prepared_batch_ms':prep_batches,'semantic_match':semantic,
      'delta':{'full_bytes':full_bytes,'delta_bytes':delta_bytes,'delta_ratio_percent':(delta_bytes/full_bytes*100 if full_bytes else 0),'changed_actions':len(delta.changed_actions),'removed_actions':len(delta.removed_action_ids),'added_actions':len(delta.added_actions),'changed_branches':len(delta.changed_branches),'removed_branches':len(delta.removed_branch_ids),'added_branches':len(delta.added_branches),'reconstruction_fingerprint_match':reconstruction},
      'missing_only_sync':{'missing_actions':len(sync.missing_or_changed_action_ids),'missing_branches':len(sync.missing_or_changed_branch_ids),'metadata_bytes_required':sync.metadata_bytes_required,'full_bytes':sync.full_bytes,'full_resend_required':sync.full_resend_required},
      'authority':{'permission_granted':sync.permission_granted,'action_execution_authorized':sync.action_execution_authorized,'world_truth_authorized':sync.world_truth_authorized,'action_success_authorized':sync.action_success_authorized},
      'condition_specific':True
    }
    a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True)); return 0 if semantic and reconstruction and not sync.full_resend_required else 2
if __name__=='__main__': raise SystemExit(main())
