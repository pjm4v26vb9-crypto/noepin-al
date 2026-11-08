from __future__ import annotations
import json,statistics,sys,time
from dataclasses import replace
from pathlib import Path
import noepin_al_061_logical_execution_interlock as m
NOW=1_800_000_000

def build(n):
    aa=[]; rr=[]
    for i in range(n):
        rid=f'REQ-{i:05d}'; bind=f'B-{i:05d}'
        aa.append(m.ApprovalEvidence(f'A-{i:05d}',rid,'OWNER',True,True,True,NOW-5,NOW+3600,bind,False))
        rr.append(m.PermitReceipt(f'OLD-{i:05d}',rid,f'RF-{i:05d}',False,True,NOW-5,bind,False))
    return tuple(aa),tuple(rr)

def main():
    out=Path(sys.argv[1] if len(sys.argv)>1 else 'BENCHMARK_RESULT.json'); p=m.default_policy(NOW)
    aa,rr=build(1500); reg=m.prepare_registry(p,aa,rr,now=NOW)
    reqs=[]
    for i in range(15):
        reqs.append(m.ExecutionRequest(request_id=f'REQ-{i:05d}',task_id=f'TASK-{i:05d}',action='ANALYZE',target='workspace:/safe/report',user_goal_fingerprint=f'G-{i:05d}',scope_fingerprint='SCOPE-061',parameters_fingerprint=f'P-{i:05d}',expected_policy_id=p.policy_id,expected_policy_version=p.version,expected_authority_epoch=p.authority_epoch,evidence_binding=f'B-{i:05d}',source_trust='TRUSTED',auth_verified=True,external_side_effect=False,irreversible=False,sensitive_data=False,privilege_elevation=False,explicit_authorization=False,safer_alternative_available=False,counterfactual_available=True,semantic_confidence=.95,created_at=NOW-5,expires_at=NOW+300))
    full=[]; prep=[]; sem=True
    for _ in range(5):
        t=time.perf_counter(); x=[m.evaluate(r,p,aa,rr,now=NOW) for r in reqs]; full.append((time.perf_counter()-t)*1000)
        t=time.perf_counter(); y=[m.evaluate_prepared(r,p,reg,now=NOW) for r in reqs]; prep.append((time.perf_counter()-t)*1000)
        sem=sem and all(m.canonical_json(a)==m.canonical_json(b) for a,b in zip(x,y))
    ba,br=build(2000); ta=list(ba); tr=list(br)
    # Changed [100:150], removed [0:5], added [2000:2005] are non-overlapping.
    for i in range(100,150):
        ta[i]=replace(ta[i],approved=False); tr[i]=replace(tr[i],verified=False)
    ta=ta[5:]; tr=tr[5:]
    for i in range(5):
        j=2000+i; rid=f'REQ-{j:05d}'; bind=f'B-{j:05d}'
        ta.append(m.ApprovalEvidence(f'A-{j:05d}',rid,'OWNER',True,True,True,NOW-5,NOW+3600,bind,False))
        tr.append(m.PermitReceipt(f'OLD-{j:05d}',rid,f'RF-{j:05d}',False,True,NOW-5,bind,False))
    ta,tr=tuple(ta),tuple(tr); delta=m.make_registry_delta(ba,br,ta,tr); ra,rr2=m.apply_registry_delta(ba,br,delta)
    full_bytes=len(m.canonical_json({'approvals':ta,'receipts':tr}).encode()); delta_bytes=len(m.canonical_json(delta).encode())
    treg=m.prepare_registry(p,ta,tr,now=NOW); raf=dict(treg.approval_fingerprints); rrf=dict(treg.receipt_fingerprints)
    for k in sorted(raf)[:10]: raf.pop(k)
    for k in sorted(rrf)[:10]: rrf.pop(k)
    sync=m.plan_registry_sync(ta,tr,raf,rrf)
    obj={'schema':'NOEPIN_AL_BENCHMARK_RESULT_V1','technology':61,'condition':{'approval_records':1500,'receipt_records':1500,'evaluations_per_batch':15,'batches':5,'runtime':'Python standard library'},'full_materialization_median_ms':statistics.median(full),'prepared_registry_median_ms':statistics.median(prep),'semantic_match':sem,
      'delta':{'base_approvals':2000,'base_receipts':2000,'target_approvals':len(ta),'target_receipts':len(tr),'changed_approvals':len(delta.changed_approvals),'changed_receipts':len(delta.changed_receipts),'removed_approvals':len(delta.removed_approval_ids),'removed_receipts':len(delta.removed_receipt_ids),'added_approvals':len(delta.added_approvals),'added_receipts':len(delta.added_receipts),'full_bytes':full_bytes,'delta_bytes':delta_bytes,'ratio_percent':(delta_bytes/full_bytes*100 if full_bytes else 0),'reconstruction_fingerprint_match':m.registry_fingerprint(ra,rr2)==m.registry_fingerprint(ta,tr)},
      'sync':{'target_records':len(ta)+len(tr),'remote_known':len(ta)+len(tr)-20,'missing_or_changed_approvals':len(sync.missing_or_changed_approval_ids),'missing_or_changed_receipts':len(sync.missing_or_changed_receipt_ids),'metadata_bytes_required':sync.metadata_bytes_required,'full_resend_required':sync.full_resend_required,'permission_granted':sync.permission_granted,'permit_issued':sync.permit_issued,'permit_consumed':sync.permit_consumed,'action_execution_authorized':sync.action_execution_authorized,'commit_authorized':sync.commit_authorized,'action_success_authorized':sync.action_success_authorized}}
    out.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n'); print(json.dumps(obj,sort_keys=True))
if __name__=='__main__': main()
