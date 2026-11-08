from __future__ import annotations
import argparse,json,time,statistics
from dataclasses import replace
from pathlib import Path
import noepin_al_051_safe_rag_gateway as m
NOW=1_800_000_000

def build(n):
    p=m.default_policy(NOW); r=m.default_request(NOW); docs=[]
    for i in range(n):
        docs.append(m.RetrievedDocument(f'D{i:05d}','KB-PRIMARY',f'kb://{i}',NOW-(i%300),m.DataClass.INTERNAL,frozenset({'TEAM-AL'}),.95,.05,m.fingerprint(('content',i)),f'PROV-{i}','RAG-EVIDENCE-051',True,False,False))
    return p,r,tuple(docs)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    p,r,docs=build(2000); prepared=m.prepare_registry(p,docs,now=NOW)
    full=[]; prep=[]
    sem=True
    for _ in range(5):
        t=time.perf_counter()
        va=None
        for _j in range(20): va=m.evaluate(r,p,docs,now=NOW)
        full.append((time.perf_counter()-t)*1000)
        t=time.perf_counter(); vb=None
        for _j in range(20): vb=m.evaluate_prepared(r,p,prepared,now=NOW)
        prep.append((time.perf_counter()-t)*1000)
        sem=sem and m.canonical_json(va)==m.canonical_json(vb)
    base=docs[:]
    target=list(base)
    for i in range(5,55): target[i]=replace(target[i],source_trust=.91)
    target=target[5:]
    for i in range(5):
        j=2000+i
        target.append(m.RetrievedDocument(f'N{j:05d}','KB-PRIMARY',f'kb://new/{j}',NOW,m.DataClass.INTERNAL,frozenset({'TEAM-AL'}),.95,.05,m.fingerprint(('new',j)),f'PROV-N{j}','RAG-EVIDENCE-051',True,False,False))
    target=tuple(target)
    d=m.make_registry_delta(base,target); rebuilt=m.apply_registry_delta(base,d)
    full_bytes=len(m.canonical_json(target).encode()); delta_bytes=len(m.canonical_json(d).encode())
    known={x.document_id:m.fingerprint(x) for x in target[:-10]}; sync=m.plan_registry_sync(target,known)
    out={'schema':'NOEPIN_AL_BENCHMARK_V1','technology':51,'condition':'2000 documents; 20 evaluations per batch; 5 batches; Python standard library','full_materialization_median_ms':statistics.median(full),'prepared_registry_median_ms':statistics.median(prep),'semantic_match':sem,'delta':{'base_items':len(base),'target_items':len(target),'changed':len(d.changed_documents),'removed':len(d.removed_document_ids),'added':len(d.added_documents),'full_bytes':full_bytes,'delta_bytes':delta_bytes,'ratio_percent':delta_bytes/full_bytes*100,'reconstruction_fingerprint_match':m.registry_fingerprint(rebuilt)==m.registry_fingerprint(target)},'sync':{'target_items':len(target),'remote_known':len(known),'missing_or_changed':len(sync.missing_or_changed_document_ids),'metadata_bytes_required':sync.metadata_bytes_required,'full_resend_required':sync.full_resend_required,'permission_granted':sync.permission_granted,'context_commit_authorized':sync.context_commit_authorized,'model_invocation_authorized':sync.model_invocation_authorized,'data_transfer_authorized':sync.data_transfer_authorized}}
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,sort_keys=True)); return 0 if sem and out['delta']['reconstruction_fingerprint_match'] else 2
if __name__=='__main__': raise SystemExit(main())
