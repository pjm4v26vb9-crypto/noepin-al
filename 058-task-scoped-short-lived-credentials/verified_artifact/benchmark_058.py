from __future__ import annotations
from dataclasses import replace
import json,statistics,time
import noepin_al_058_ephemeral_credential as m
NOW=1_800_000_000

def make_data(n):
    out=[]
    for i in range(n):
        out.append(m.CredentialRecord(f'C-{i:05d}',f'T-{i}',f'R-{i}',f'S-{i}','TASK_AGENT',frozenset({'READ_RESOURCE'}),'API-A','ISSUER-058',NOW-10,NOW+300,1,0,True,f'B-{i}',False))
    return tuple(out)
def med(fn):
    vals=[]
    for _ in range(5): t=time.perf_counter(); fn(); vals.append((time.perf_counter()-t)*1000)
    return statistics.median(vals)
def main():
    p=m.default_policy(NOW); rs=make_data(2000); rec=rs[0]; req=replace(m.default_request(NOW),operation=m.CredentialOperation.USE,credential_id=rec.credential_id,task_id=rec.task_id,run_id=rec.run_id,subject_id=rec.subject_id,evidence_binding=rec.evidence_binding,requested_ttl_seconds=0)
    def full():
        for _ in range(20): m.evaluate(req,p,rs,now=NOW)
    reg=m.prepare_registry(p,rs,now=NOW)
    def prepared():
        for _ in range(20): m.evaluate_prepared(req,p,reg,now=NOW)
    f=med(full); pr=med(prepared); a=m.evaluate(req,p,rs,now=NOW); b=m.evaluate_prepared(req,p,reg,now=NOW)
    base=make_data(3000); targ=list(base)
    for i in range(50,100): targ[i]=replace(targ[i],expires_at=NOW+200+i)
    del targ[:5]
    for i in range(5): targ.append(m.CredentialRecord(f'NEW-{i}',f'NT-{i}',f'NR-{i}',f'NS-{i}','TASK_AGENT',frozenset({'READ_RESOURCE'}),'API-A','ISSUER-058',NOW,NOW+300,1,0,True,f'NB-{i}',False))
    targ=tuple(targ); dl=m.make_registry_delta(base,targ); recon=m.apply_registry_delta(base,dl)
    fullb=len(m.canonical_json({'records':targ}).encode()); deltab=len(m.canonical_json(dl).encode())
    treg=m.prepare_registry(p,targ,now=NOW); remote=dict(treg.record_fingerprints)
    for k in sorted(remote)[-10:]: remote.pop(k)
    sync=m.plan_registry_sync(targ,remote)
    out={'condition':'2000 credential records; 20 evaluations per batch; 5 batches; Python standard library','full_materialization_median_ms':f,'prepared_registry_median_ms':pr,'semantic_match':m.canonical_json(a)==m.canonical_json(b),'delta':{'base_items':len(base),'target_items':len(targ),'changed':len(dl.changed_records),'removed':len(dl.removed_credential_ids),'added':len(dl.added_records),'full_bytes':fullb,'delta_bytes':deltab,'ratio_percent':deltab/fullb*100,'reconstruction_fingerprint_match':m.registry_fingerprint(recon)==m.registry_fingerprint(targ)},'sync':{'target_items':len(targ),'remote_known':len(targ)-len(sync.missing_or_changed_credential_ids),'missing_or_changed':len(sync.missing_or_changed_credential_ids),'metadata_bytes_required':sync.metadata_bytes_required,'full_resend_required':sync.full_resend_required,'permission_granted':sync.permission_granted,'credential_issue_authorized':sync.credential_issue_authorized,'credential_use_authorized':sync.credential_use_authorized,'revocation_execution_authorized':sync.revocation_execution_authorized}}
    print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return out
if __name__=='__main__': main()
