from __future__ import annotations
import argparse,json,time,statistics
from dataclasses import replace
from pathlib import Path
import noepin_al_052_content_authenticity as m
NOW=1_800_000_000

def build(n):
    p=m.default_policy(NOW); req=m.default_request(NOW); steps=[]; sigs=[]
    for i in range(n):
        cid=f'C{i:05d}'; h0=m.fingerprint(('origin',i)); h1=m.fingerprint(('current',i))
        steps.append(m.ProvenanceStep(f'S{i:05d}',cid,0,'NOEPIN-ORIGIN','NOEPIN','NOEPIN-PROV-ISSUER',NOW-(i%300),m.GENESIS_SHA256,h1,'CREATE',.95,'PROV-EVIDENCE-052',True,False))
        sigs.append(m.SignatureEvidence(f'G{i:05d}',cid,h1,'NOEPIN-ORIGIN','NOEPIN',f'K{i:05d}','ED25519','VERIFIER-TRUSTED',NOW-(i%300),'PROV-EVIDENCE-052',m.signature_payload_fingerprint(cid,h1,'NOEPIN-ORIGIN','NOEPIN',f'K{i:05d}','ED25519'),True,.95,False))
    # Replace first item with the actual requested content so semantic evaluation has one matching record.
    hreq=req.content_sha256
    steps[0]=m.ProvenanceStep('S00000',req.content_id,0,'NOEPIN-ORIGIN','NOEPIN','NOEPIN-PROV-ISSUER',NOW-1,m.GENESIS_SHA256,hreq,'CREATE',.95,req.evidence_binding,True,False)
    sigs[0]=m.SignatureEvidence('G00000',req.content_id,hreq,'NOEPIN-ORIGIN','NOEPIN','K00000','ED25519','VERIFIER-TRUSTED',NOW-1,req.evidence_binding,m.signature_payload_fingerprint(req.content_id,hreq,'NOEPIN-ORIGIN','NOEPIN','K00000','ED25519'),True,.95,False)
    return p,req,tuple(steps),tuple(sigs)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    p,r,steps,sigs=build(2000); prepared=m.prepare_registry(p,steps,sigs,now=NOW); full=[]; prep=[]; sem=True
    for _ in range(5):
        t=time.perf_counter(); va=None
        for _j in range(20): va=m.evaluate(r,p,steps,sigs,now=NOW)
        full.append((time.perf_counter()-t)*1000)
        t=time.perf_counter(); vb=None
        for _j in range(20): vb=m.evaluate_prepared(r,p,prepared,now=NOW)
        prep.append((time.perf_counter()-t)*1000); sem=sem and m.canonical_json(va)==m.canonical_json(vb)
    bs=list(steps); bg=list(sigs); ts=list(bs); tg=list(bg)
    for i in range(5,55): ts[i]=replace(ts[i],origin_trust=.91); tg[i]=replace(tg[i],signer_trust=.91)
    ts=ts[5:]; tg=tg[5:]
    for i in range(5):
        j=2000+i; cid=f'N{j:05d}'; h=m.fingerprint(('new-current',j))
        ts.append(m.ProvenanceStep(f'NS{j:05d}',cid,0,'NOEPIN-ORIGIN','NOEPIN','NOEPIN-PROV-ISSUER',NOW,m.GENESIS_SHA256,h,'CREATE',.95,'PROV-EVIDENCE-052',True,False))
        tg.append(m.SignatureEvidence(f'NG{j:05d}',cid,h,'NOEPIN-ORIGIN','NOEPIN',f'NK{j:05d}','ED25519','VERIFIER-TRUSTED',NOW,'PROV-EVIDENCE-052',m.signature_payload_fingerprint(cid,h,'NOEPIN-ORIGIN','NOEPIN',f'NK{j:05d}','ED25519'),True,.95,False))
    ts=tuple(ts); tg=tuple(tg)
    d=m.make_registry_delta(steps,sigs,ts,tg); rs,rg=m.apply_registry_delta(steps,sigs,d)
    full_bytes=len(m.canonical_json((ts,tg)).encode()); delta_bytes=len(m.canonical_json(d).encode())
    known={}
    for x in ts[:-10]: known['step:'+x.step_id]=m.fingerprint(x)
    for x in tg[:-10]: known['sig:'+x.signature_id]=m.fingerprint(x)
    sync=m.plan_registry_sync(ts,tg,known)
    out={'schema':'NOEPIN_AL_BENCHMARK_V1','technology':52,'condition':'2000 provenance steps + 2000 signature evidence; 20 evaluations per batch; 5 batches; Python standard library','full_materialization_median_ms':statistics.median(full),'prepared_registry_median_ms':statistics.median(prep),'semantic_match':sem,'delta':{'base_steps':len(steps),'base_signatures':len(sigs),'target_steps':len(ts),'target_signatures':len(tg),'changed_steps':len(d.changed_steps),'removed_steps':len(d.removed_step_ids),'added_steps':len(d.added_steps),'changed_signatures':len(d.changed_signatures),'removed_signatures':len(d.removed_signature_ids),'added_signatures':len(d.added_signatures),'full_bytes':full_bytes,'delta_bytes':delta_bytes,'ratio_percent':delta_bytes/full_bytes*100,'reconstruction_fingerprint_match':m.registry_fingerprint(rs,rg)==m.registry_fingerprint(ts,tg)},'sync':{'target_records':len(ts)+len(tg),'remote_known':len(known),'missing_or_changed_steps':len(sync.missing_or_changed_step_ids),'missing_or_changed_signatures':len(sync.missing_or_changed_signature_ids),'metadata_bytes_required':sync.metadata_bytes_required,'full_resend_required':sync.full_resend_required,'permission_granted':sync.permission_granted,'content_use_authorized':sync.content_use_authorized,'content_execution_authorized':sync.content_execution_authorized,'data_transfer_authorized':sync.data_transfer_authorized}}
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,sort_keys=True)); return 0 if sem and out['delta']['reconstruction_fingerprint_match'] else 2
if __name__=='__main__': raise SystemExit(main())
