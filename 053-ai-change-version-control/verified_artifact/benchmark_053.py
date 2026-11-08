from __future__ import annotations
import argparse,json,time,statistics
from dataclasses import replace
from pathlib import Path
import noepin_al_053_change_version_control as m
NOW=1_800_000_000

def build(n):
    p=m.default_policy(NOW); r=m.default_request(NOW); vs=[]; aps=[]; rbs=[]
    for i in range(n):
        cid=f'C{i:05d}'; fp=m.fingerprint(('v1',i)); parent=m.fingerprint(('v0',i)); bind=f'E{i:05d}'
        vs.append(m.VersionRecord(f'V{i:05d}',cid,'RULE','1.0.0',fp,parent,NOW-(i%300),bind,True,False))
        aps.append(m.ApprovalEvidence(f'A{i:05d}',f'CH{i:05d}',f'ACT{i:05d}','CHANGE_REVIEWER',True,True,NOW-10,NOW+10000,bind,False))
        rbs.append(m.RollbackPoint(f'R{i:05d}',cid,'1.0.0',fp,parent,NOW-20,bind,True,False))
    # first record matches request
    vs[0]=m.VersionRecord('V00000',r.component_id,r.component_type,r.current_version,r.current_fingerprint,m.fingerprint(('parent','0.9.0')),NOW-100,r.evidence_binding,True,False)
    aps[0]=m.ApprovalEvidence('A00000',r.change_id,'REVIEWER-1','CHANGE_REVIEWER',True,True,NOW-10,NOW+10000,r.evidence_binding,False)
    rbs[0]=m.RollbackPoint(r.rollback_point_id,r.component_id,r.current_version,r.current_fingerprint,m.fingerprint(('parent','0.9.0')),NOW-20,r.evidence_binding,True,False)
    return p,r,tuple(vs),tuple(aps),tuple(rbs)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    p,r,vs,aps,rbs=build(1500); prepared=m.prepare_registry(p,vs,aps,rbs,now=NOW); full=[]; prep=[]; sem=True
    for _ in range(5):
        t=time.perf_counter(); va=None
        for _j in range(15): va=m.evaluate(r,p,vs,aps,rbs,now=NOW)
        full.append((time.perf_counter()-t)*1000)
        t=time.perf_counter(); vb=None
        for _j in range(15): vb=m.evaluate_prepared(r,p,prepared,now=NOW)
        prep.append((time.perf_counter()-t)*1000); sem=sem and m.canonical_json(va)==m.canonical_json(vb)
    tv=list(vs); ta=list(aps); tr=list(rbs)
    for i in range(5,55):
        tv[i]=replace(tv[i],version='1.0.1'); ta[i]=replace(ta[i],expires_at=NOW+20000+i); tr[i]=replace(tr[i],created_at=NOW-100-i)
    tv=tv[5:]; ta=ta[5:]; tr=tr[5:]
    for i in range(5):
        j=1500+i; cid=f'N{j:05d}'; fp=m.fingerprint(('new',j)); par=m.fingerprint(('old',j)); bind=f'NE{j:05d}'
        tv.append(m.VersionRecord(f'NV{j:05d}',cid,'RULE','1.0.0',fp,par,NOW,bind,True,False))
        ta.append(m.ApprovalEvidence(f'NA{j:05d}',f'NCH{j:05d}',f'NACT{j:05d}','CHANGE_REVIEWER',True,True,NOW,NOW+10000,bind,False))
        tr.append(m.RollbackPoint(f'NR{j:05d}',cid,'1.0.0',fp,par,NOW,bind,True,False))
    tv,ta,tr=tuple(tv),tuple(ta),tuple(tr)
    d=m.make_registry_delta(vs,aps,rbs,tv,ta,tr); rv,ra,rr=m.apply_registry_delta(vs,aps,rbs,d)
    full_bytes=len(m.canonical_json((tv,ta,tr)).encode()); delta_bytes=len(m.canonical_json(d).encode())
    known={}
    for x in tv[:-10]: known['version:'+x.record_id]=m.fingerprint(x)
    for x in ta[:-10]: known['approval:'+x.approval_id]=m.fingerprint(x)
    for x in tr[:-10]: known['rollback:'+x.rollback_id]=m.fingerprint(x)
    sync=m.plan_registry_sync(tv,ta,tr,known)
    out={'schema':'NOEPIN_AL_BENCHMARK_V1','technology':53,'condition':'1500 version records + 1500 approval evidence + 1500 rollback points; 15 evaluations per batch; 5 batches; Python standard library','full_materialization_median_ms':statistics.median(full),'prepared_registry_median_ms':statistics.median(prep),'semantic_match':sem,'delta':{'base_versions':len(vs),'base_approvals':len(aps),'base_rollbacks':len(rbs),'target_versions':len(tv),'target_approvals':len(ta),'target_rollbacks':len(tr),'changed_versions':len(d.changed_versions),'removed_versions':len(d.removed_version_ids),'added_versions':len(d.added_versions),'changed_approvals':len(d.changed_approvals),'removed_approvals':len(d.removed_approval_ids),'added_approvals':len(d.added_approvals),'changed_rollbacks':len(d.changed_rollbacks),'removed_rollbacks':len(d.removed_rollback_ids),'added_rollbacks':len(d.added_rollbacks),'full_bytes':full_bytes,'delta_bytes':delta_bytes,'ratio_percent':delta_bytes/full_bytes*100,'reconstruction_fingerprint_match':m.registry_fingerprint(rv,ra,rr)==m.registry_fingerprint(tv,ta,tr)},'sync':{'target_records':len(tv)+len(ta)+len(tr),'remote_known':len(known),'missing_or_changed_versions':len(sync.missing_or_changed_version_ids),'missing_or_changed_approvals':len(sync.missing_or_changed_approval_ids),'missing_or_changed_rollbacks':len(sync.missing_or_changed_rollback_ids),'metadata_bytes_required':sync.metadata_bytes_required,'full_resend_required':sync.full_resend_required,'permission_granted':sync.permission_granted,'change_commit_authorized':sync.change_commit_authorized,'deployment_authorized':sync.deployment_authorized,'rollback_execution_authorized':sync.rollback_execution_authorized}}
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,sort_keys=True)); return 0 if sem and out['delta']['reconstruction_fingerprint_match'] else 2
if __name__=='__main__': raise SystemExit(main())
