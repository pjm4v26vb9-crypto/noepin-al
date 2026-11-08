from __future__ import annotations
import json,statistics,sys,time
from dataclasses import replace
from pathlib import Path
import noepin_al_060_stop_completion_checker as m
NOW=1_800_000_000

def build(n):
    ps=[]; cs=[]; ds=[]
    for i in range(n):
        task=f'TASK-{i:05d}'; bind=f'B-{i:05d}'
        ps.append(m.TaskProgressState(f'P-{i:05d}',task,f'S-{i:05d}',10,300,0,False,False,False,NOW-20,NOW+3600,True,True,bind,False))
        cs.append(m.SuccessCriterion(f'C-{i:05d}',task,True,True,True,True,NOW-20,NOW+3600,bind,False))
        ds.append(m.DependencyState(f'D-{i:05d}',task,True,True,False,True,True,NOW-20,NOW+3600,bind,False))
    return tuple(ps),tuple(cs),tuple(ds)

def main():
    out=Path(sys.argv[1] if len(sys.argv)>1 else 'BENCHMARK_RESULT.json'); p=m.default_policy(NOW)
    ps,cs,ds=build(1500); reg=m.prepare_registry(p,ps,cs,ds,now=NOW)
    reqs=[m.TaskCheckRequest(f'R-{i}',f'TASK-{i:05d}',f'S-{i:05d}',p.policy_id,p.version,p.authority_epoch,f'B-{i:05d}') for i in range(15)]
    full=[]; prep=[]; sem=True
    for _ in range(5):
        t=time.perf_counter(); aa=[m.evaluate(r,p,ps,cs,ds,now=NOW) for r in reqs]; full.append((time.perf_counter()-t)*1000)
        t=time.perf_counter(); bb=[m.evaluate_prepared(r,p,reg,now=NOW) for r in reqs]; prep.append((time.perf_counter()-t)*1000)
        sem=sem and all(m.canonical_json(a)==m.canonical_json(b) for a,b in zip(aa,bb))
    bp,bc,bd=build(2000); tp=list(bp); tc=list(bc); td=list(bd)
    # non-overlapping changed [100:150], removed [0:5], added 5
    for i in range(100,150):
        tp[i]=replace(tp[i],current_step=11); tc[i]=replace(tc[i],satisfied=False); td[i]=replace(td[i],completed=False)
    tp=tp[5:]; tc=tc[5:]; td=td[5:]
    for i in range(5):
        j=2000+i; task=f'TASK-{j:05d}'; bind=f'B-{j:05d}'
        tp.append(m.TaskProgressState(f'P-{j:05d}',task,f'S-{j:05d}',10,300,0,False,False,False,NOW-20,NOW+3600,True,True,bind,False))
        tc.append(m.SuccessCriterion(f'C-{j:05d}',task,True,True,True,True,NOW-20,NOW+3600,bind,False))
        td.append(m.DependencyState(f'D-{j:05d}',task,True,True,False,True,True,NOW-20,NOW+3600,bind,False))
    tp,tc,td=tuple(tp),tuple(tc),tuple(td); delta=m.make_registry_delta(bp,bc,bd,tp,tc,td); rp,rc,rd=m.apply_registry_delta(bp,bc,bd,delta)
    full_bytes=len(m.canonical_json({'progress':tp,'criteria':tc,'dependencies':td}).encode()); delta_bytes=len(m.canonical_json(delta).encode())
    treg=m.prepare_registry(p,tp,tc,td,now=NOW)
    rpf=dict(treg.progress_fingerprints); rcf=dict(treg.criterion_fingerprints); rdf=dict(treg.dependency_fingerprints)
    for k in sorted(rpf)[:10]: rpf.pop(k)
    for k in sorted(rcf)[:10]: rcf.pop(k)
    for k in sorted(rdf)[:10]: rdf.pop(k)
    sync=m.plan_registry_sync(tp,tc,td,rpf,rcf,rdf)
    obj={'schema':'NOEPIN_AL_BENCHMARK_RESULT_V1','technology':60,'condition':{'progress_records':1500,'criteria_records':1500,'dependency_records':1500,'evaluations_per_batch':15,'batches':5,'runtime':'Python standard library'},'full_materialization_median_ms':statistics.median(full),'prepared_registry_median_ms':statistics.median(prep),'semantic_match':sem,
    'delta':{'base_progress':2000,'base_criteria':2000,'base_dependencies':2000,'target_progress':len(tp),'target_criteria':len(tc),'target_dependencies':len(td),'changed_progress':len(delta.changed_progress),'changed_criteria':len(delta.changed_criteria),'changed_dependencies':len(delta.changed_dependencies),'removed_progress':len(delta.removed_progress_ids),'removed_criteria':len(delta.removed_criterion_ids),'removed_dependencies':len(delta.removed_dependency_ids),'added_progress':len(delta.added_progress),'added_criteria':len(delta.added_criteria),'added_dependencies':len(delta.added_dependencies),'full_bytes':full_bytes,'delta_bytes':delta_bytes,'ratio_percent':(delta_bytes/full_bytes*100 if full_bytes else 0),'reconstruction_fingerprint_match':m.registry_fingerprint(rp,rc,rd)==m.registry_fingerprint(tp,tc,td)},
    'sync':{'target_records':len(tp)+len(tc)+len(td),'remote_known':len(tp)+len(tc)+len(td)-30,'missing_or_changed_progress':len(sync.missing_or_changed_progress_ids),'missing_or_changed_criteria':len(sync.missing_or_changed_criterion_ids),'missing_or_changed_dependencies':len(sync.missing_or_changed_dependency_ids),'metadata_bytes_required':sync.metadata_bytes_required,'full_resend_required':sync.full_resend_required,'permission_granted':sync.permission_granted,'task_success_authorized':sync.task_success_authorized,'stop_execution_authorized':sync.stop_execution_authorized,'scope_expansion_authorized':sync.scope_expansion_authorized,'cleanup_execution_authorized':sync.cleanup_execution_authorized}}
    out.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n'); print(json.dumps(obj,sort_keys=True))
if __name__=='__main__': main()
