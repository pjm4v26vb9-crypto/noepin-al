from __future__ import annotations
import argparse,json,statistics,time
from dataclasses import replace
from pathlib import Path
import noepin_al_065_minimal_change_optimizer as m
NOW=1_800_000_000

def dataset(extra=1500):
    p=m.default_policy(NOW); c=list(m.default_changes()); g=m.default_goals(); r=m.default_request(NOW)
    common=dict(binding='MC-BIND',verified=True,revoked=False,policy_id='MC-POLICY',policy_version='1',authority_epoch='MC-EPOCH')
    for i in range(extra): c.append(m.ChangeSpec(f'CHG-AUX-{i:04d}',f'TARGET-AUX-{i:04d}',(f'AUX-{i:04d}',),2.0,1.0,1.0,True,**common))
    r=replace(r,candidate_change_ids=r.candidate_change_ids+tuple(f'CHG-AUX-{i:04d}' for i in range(extra)))
    p=replace(p,max_candidate_changes=2000,exact_search_limit=16)
    return r,p,tuple(c),g

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    r,p,changes,goals=dataset(); batches=5; iters=10; full=[]; prep=[]
    for _ in range(batches):
        t=time.perf_counter(); vals=[m.evaluate(r,p,changes,goals,now=NOW) for __ in range(iters)]; full.append((time.perf_counter()-t)*1000)
    ps=m.prepare_state(p,changes,goals,binding=r.binding,now=NOW); integ=m.validate_prepared_integrity(ps)
    for _ in range(batches):
        t=time.perf_counter(); vals2=[m.evaluate_prepared(r,ps,None,current_policy_fingerprint=ps.policy_fingerprint,current_registry_fingerprint=ps.registry_fingerprint,prepared_integrity_validated=integ,now=NOW) for __ in range(iters)]; prep.append((time.perf_counter()-t)*1000)
    semantic=m.canonical_json(vals[-1])==m.canonical_json(vals2[-1])
    target=[]; remove={f'CHG-AUX-{i:04d}' for i in range(1490,1495)}
    for x in changes:
        if x.change_id in remove: continue
        if x.change_id.startswith('CHG-AUX-') and int(x.change_id[-4:])<50: x=replace(x,change_cost=2.5)
        target.append(x)
    common=dict(binding='MC-BIND',verified=True,revoked=False,policy_id='MC-POLICY',policy_version='1',authority_epoch='MC-EPOCH')
    for i in range(5): target.append(m.ChangeSpec(f'CHG-NEW-{i:04d}',f'TARGET-NEW-{i:04d}',(f'NEW-{i:04d}',),2.0,1.0,1.0,True,**common))
    target_ps=m.prepare_state(p,tuple(target),goals,binding=r.binding,now=NOW); delta=m.build_delta(ps,target_ps); recon=m.apply_delta(ps,delta,now=NOW)
    fb=m.full_registry_bytes(target_ps); db=m.delta_bytes(delta)
    remote={'changes':dict(target_ps.change_fingerprints),'goals':dict(target_ps.goal_fingerprints)}
    for k in list(sorted(remote['changes']))[-10:]: remote['changes'].pop(k)
    sync=m.missing_only_sync_plan(target_ps,remote)
    out={'runtime':'Python standard library','condition_specific':True,'dataset':{'total_changes':len(changes),'goals':len(goals)},'batches':batches,'iterations_per_batch':iters,'full_batch_ms':full,'prepared_batch_ms':prep,'full_materialization_median_ms':statistics.median(full),'prepared_optimizer_median_ms':statistics.median(prep),'semantic_match':semantic,'delta':{'full_bytes':fb,'delta_bytes':db,'delta_ratio_percent':db/fb*100,'changed_changes':len(delta.changed_changes),'removed_changes':len(delta.removed_change_ids),'added_changes':len(delta.added_changes),'changed_goals':len(delta.changed_goals),'removed_goals':len(delta.removed_goal_ids),'added_goals':len(delta.added_goals),'reconstruction_fingerprint_match':recon.registry_fingerprint==target_ps.registry_fingerprint},'missing_only_sync':{'missing_changes':len(sync.missing_or_changed_change_ids),'missing_goals':len(sync.missing_or_changed_goal_ids),'metadata_bytes_required':sync.metadata_bytes_required,'full_bytes':sync.full_bytes,'full_resend_required':sync.full_resend_required},'authority':{'permission_granted':sync.permission_granted,'write_authorized':sync.write_authorized,'patch_committed':sync.patch_committed,'deployment_authorized':sync.deployment_authorized,'action_execution_authorized':sync.action_execution_authorized,'action_success_authorized':sync.action_success_authorized}}
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,sort_keys=True)); return 0 if integ and semantic and out['delta']['reconstruction_fingerprint_match'] and not sync.full_resend_required and not any(out['authority'].values()) else 2
if __name__=='__main__': raise SystemExit(main())
