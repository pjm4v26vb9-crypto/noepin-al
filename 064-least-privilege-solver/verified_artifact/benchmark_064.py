from __future__ import annotations
import argparse,json,statistics,time
from dataclasses import replace
from pathlib import Path
import noepin_al_064_least_privilege_solver as m
NOW=1_800_000_000

def dataset(extra=1500):
    p=m.default_policy(NOW); caps=list(m.default_capabilities(NOW)); edges=list(m.default_edges()); roles=m.default_roles(NOW); actions=m.default_actions(); reqs=m.default_requirements(); r=m.default_request(NOW)
    for i in range(extra):
        cid=f'CAP-AUX-{i:04d}'
        caps.append(m.CapabilitySpec(cid,'LP-BIND',True,False,NOW-1000,NOW+10000,3.0,'LP-POLICY','1','LP-EPOCH'))
        edges.append(m.CapabilityEdge(f'EDGE-AUX-{i:04d}',cid,'CAP_READ','LP-BIND',True,False,'LP-POLICY','1','LP-EPOCH'))
    return r,p,tuple(caps),tuple(edges),roles,actions,reqs

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    r,p,caps,edges,roles,actions,reqs=dataset()
    batches=5; iters=10; full=[]; prepared_times=[]
    for _ in range(batches):
        t=time.perf_counter()
        vals=[m.evaluate(r,p,caps,edges,roles,actions,reqs,now=NOW) for __ in range(iters)]
        full.append((time.perf_counter()-t)*1000)
    ps=m.prepare_state(p,caps,edges,roles,actions,reqs,binding=r.binding,now=NOW); integrity=m.validate_prepared_integrity(ps)
    for _ in range(batches):
        t=time.perf_counter()
        vals2=[m.evaluate_prepared(r,ps,None,current_policy_fingerprint=ps.policy_fingerprint,current_registry_fingerprint=ps.registry_fingerprint,prepared_integrity_validated=integrity,now=NOW) for __ in range(iters)]
        prepared_times.append((time.perf_counter()-t)*1000)
    semantic=m.canonical_json(vals[-1])==m.canonical_json(vals2[-1])
    # Delta fixture: 50 changed, 5 removed, 5 added for capabilities and edges.
    target_caps=[]; target_edges=[]
    remove_caps={f'CAP-AUX-{i:04d}' for i in range(1490,1495)}; remove_edges={f'EDGE-AUX-{i:04d}' for i in range(1490,1495)}
    for x in caps:
        if x.capability_id in remove_caps: continue
        if x.capability_id.startswith('CAP-AUX-') and int(x.capability_id[-4:])<50: x=replace(x,risk_weight=4.0)
        target_caps.append(x)
    for x in edges:
        if x.edge_id in remove_edges: continue
        if x.edge_id.startswith('EDGE-AUX-') and int(x.edge_id[-4:])<50: x=replace(x,verified=True)  # record retained; paired cap changes drive delta
        target_edges.append(x)
    for i in range(5):
        cid=f'CAP-NEW-{i:04d}'; target_caps.append(m.CapabilitySpec(cid,'LP-BIND',True,False,NOW-1000,NOW+10000,3.0,'LP-POLICY','1','LP-EPOCH'))
        target_edges.append(m.CapabilityEdge(f'EDGE-NEW-{i:04d}',cid,'CAP_READ','LP-BIND',True,False,'LP-POLICY','1','LP-EPOCH'))
    target=m.prepare_state(p,tuple(target_caps),tuple(target_edges),roles,actions,reqs,binding=r.binding,now=NOW)
    delta=m.build_delta(ps,target); recon=m.apply_delta(ps,delta,now=NOW)
    full_bytes=m.full_registry_bytes(target); dbytes=m.delta_bytes(delta)
    remote={
      'capabilities':dict(target.capability_fingerprints),'edges':dict(target.edge_fingerprints),'roles':dict(target.role_fingerprints),'actions':dict(target.action_fingerprints),'requirements':dict(target.requirement_fingerprints)
    }
    for k in list(sorted(remote['capabilities']))[-10:]: remote['capabilities'].pop(k)
    for k in list(sorted(remote['edges']))[-10:]: remote['edges'].pop(k)
    sync=m.missing_only_sync_plan(target,remote)
    out={
      'runtime':'Python standard library','condition_specific':True,'dataset':{'total_capabilities':len(caps),'total_edges':len(edges),'roles':len(roles),'actions':len(actions),'requirements':len(reqs)},
      'batches':batches,'iterations_per_batch':iters,'full_batch_ms':full,'prepared_batch_ms':prepared_times,
      'full_materialization_median_ms':statistics.median(full),'prepared_solver_median_ms':statistics.median(prepared_times),'semantic_match':semantic,
      'delta':{'full_bytes':full_bytes,'delta_bytes':dbytes,'delta_ratio_percent':dbytes/full_bytes*100,'changed_capabilities':len(delta.changed_capabilities),'removed_capabilities':len(delta.removed_capability_ids),'added_capabilities':len(delta.added_capabilities),'changed_edges':len(delta.changed_edges),'removed_edges':len(delta.removed_edge_ids),'added_edges':len(delta.added_edges),'reconstruction_fingerprint_match':recon.registry_fingerprint==target.registry_fingerprint},
      'missing_only_sync':{'missing_capabilities':len(sync.missing_or_changed_capability_ids),'missing_edges':len(sync.missing_or_changed_edge_ids),'missing_roles':len(sync.missing_or_changed_role_ids),'missing_actions':len(sync.missing_or_changed_action_ids),'missing_requirements':len(sync.missing_or_changed_requirement_ids),'metadata_bytes_required':sync.metadata_bytes_required,'full_bytes':sync.full_bytes,'full_resend_required':sync.full_resend_required},
      'authority':{'permission_granted':sync.permission_granted,'token_issued':sync.token_issued,'credential_minted':sync.credential_minted,'role_changed':sync.role_changed,'capability_activated':sync.capability_activated,'action_execution_authorized':sync.action_execution_authorized,'action_success_authorized':sync.action_success_authorized}
    }
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,sort_keys=True));
    return 0 if integrity and semantic and out['delta']['reconstruction_fingerprint_match'] and not sync.full_resend_required and not any(out['authority'].values()) else 2
if __name__=='__main__': raise SystemExit(main())
