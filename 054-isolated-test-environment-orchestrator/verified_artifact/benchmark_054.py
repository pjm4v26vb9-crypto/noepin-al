from __future__ import annotations
import argparse,json,time,statistics
from dataclasses import replace
from pathlib import Path
import noepin_al_054_isolated_test_orchestrator as m
NOW=1_800_000_000

def make_data(n):
    ps=[]; es=[]
    for i in range(n):
        bind=f'B-{i}'
        ps.append(m.SandboxProfile(f'P-{i}',True,True,False,'DENY','TEMP_ONLY',False,False,False,NOW-100,bind,False))
        es.append(m.SandboxRunEvidence(f'E-{i}',f'R-{i}',f'O-{i}',True,True,NOW-20,NOW-10,False,False,False,False,False,False,False,1000+i,True,bind,False))
    return tuple(ps),tuple(es)
def request(i):
    return m.TestRequest(f'R-{i}',f'S-{i}','MCP',m.fingerprint(('artifact',i)),m.TestRisk.MEDIUM,f'P-{i}','DENY','TEMP_ONLY',60,'SANDBOX-054','1',1,f'B-{i}')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path); a=ap.parse_args(); p=m.default_policy(NOW)
    ps,es=make_data(1500); batches=[]; pre=[]
    for _ in range(5):
        t=time.perf_counter();
        for i in range(15): m.evaluate(request(i),p,ps,es,now=NOW)
        batches.append((time.perf_counter()-t)*1000)
    reg=m.prepare_registry(p,ps,es,now=NOW)
    for _ in range(5):
        t=time.perf_counter();
        for i in range(15): m.evaluate_prepared(request(i),p,reg,now=NOW)
        pre.append((time.perf_counter()-t)*1000)
    semantic=m.canonical_json(m.evaluate(request(3),p,ps,es,now=NOW))==m.canonical_json(m.evaluate_prepared(request(3),p,reg,now=NOW))
    bp,be=make_data(2000); tp=list(bp); te=list(be)
    for i in range(50,100): tp[i]=replace(tp[i],created_at=NOW-200)
    for i in range(50,100): te[i]=replace(te[i],output_bytes=9000+i)
    del tp[:5]; del te[:5]
    for i in range(5):
        j=2000+i; bind=f'B-{j}'; tp.append(m.SandboxProfile(f'P-{j}',True,True,False,'DENY','TEMP_ONLY',False,False,False,NOW-100,bind,False)); te.append(m.SandboxRunEvidence(f'E-{j}',f'R-{j}',f'O-{j}',True,True,NOW-20,NOW-10,False,False,False,False,False,False,False,1000+j,True,bind,False))
    tp=tuple(tp); te=tuple(te); d=m.make_registry_delta(bp,be,tp,te); rp,re=m.apply_registry_delta(bp,be,d)
    full=len(m.canonical_json({'profiles':tp,'evidence':te}).encode()); delta=len(m.canonical_json(d).encode())
    known={}
    for x in tp[:-10]: known['profile:'+x.profile_id]=m.fingerprint(x)
    for x in te[:-10]: known['evidence:'+x.evidence_id]=m.fingerprint(x)
    sync=m.plan_registry_sync(tp,te,known)
    result={'condition':'1500 profiles + 1500 run evidence; 15 evaluations per batch; 5 batches; Python standard library','full_materialization_median_ms':statistics.median(batches),'prepared_registry_median_ms':statistics.median(pre),'semantic_match':semantic,'delta':{'base_profiles':len(bp),'base_evidence':len(be),'target_profiles':len(tp),'target_evidence':len(te),'changed_profiles':len(d.changed_profiles),'removed_profiles':len(d.removed_profile_ids),'added_profiles':len(d.added_profiles),'changed_evidence':len(d.changed_evidence),'removed_evidence':len(d.removed_evidence_ids),'added_evidence':len(d.added_evidence),'full_bytes':full,'delta_bytes':delta,'ratio_percent':delta/full*100,'reconstruction_fingerprint_match':m.registry_fingerprint(rp,re)==m.registry_fingerprint(tp,te)},'sync':{'target_records':len(tp)+len(te),'remote_known':len(tp)+len(te)-20,'missing_or_changed_profiles':len(sync.missing_or_changed_profile_ids),'missing_or_changed_evidence':len(sync.missing_or_changed_evidence_ids),'metadata_bytes_required':sync.metadata_bytes_required,'full_resend_required':sync.full_resend_required,'permission_granted':sync.permission_granted,'sandbox_execution_authorized':sync.sandbox_execution_authorized,'production_execution_authorized':sync.production_execution_authorized,'real_secret_access_authorized':sync.real_secret_access_authorized,'network_egress_authorized':sync.network_egress_authorized}}
    text=json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+'\n'; print(text,end='');
    if a.out: a.out.write_text(text,encoding='utf-8')
if __name__=='__main__': main()
