from __future__ import annotations
import argparse,json
from dataclasses import replace
from pathlib import Path
import noepin_al_051_safe_rag_gateway as m
NOW=1_800_000_000

def one(i):
    p=m.default_policy(NOW); r=m.default_request(NOW); docs=m.default_documents(NOW)
    k=i%10
    if k==0: return m.evaluate(r,p,docs,now=NOW)
    if k==1:
        d=replace(docs[0],injection_risk=.6); return m.evaluate(r,p,(d,),now=NOW)
    if k==2:
        d=replace(docs[0],injection_risk=.9); return m.evaluate(r,p,(d,),now=NOW)
    if k==3:
        d=replace(docs[0],acl_principals=frozenset({'OTHER'})); return m.evaluate(r,p,(d,),now=NOW)
    if k==4:
        d=replace(docs[0],source_trust=.2); return m.evaluate(r,p,(d,),now=NOW)
    if k==5:
        d=replace(docs[0],captured_at=NOW-p.max_document_age_seconds-1); return m.evaluate(r,p,(d,),now=NOW)
    if k==6:
        rr=replace(r,expected_policy_version='bad'); return m.evaluate(rr,p,docs,now=NOW)
    if k==7:
        d=replace(docs[0],instruction_like_content=True); return m.evaluate(r,p,(d,),now=NOW)
    if k==8:
        prepared=m.prepare_registry(p,docs,now=NOW); return m.evaluate_prepared(r,p,prepared,now=NOW)
    rr=replace(r,purpose='UNAPPROVED'); return m.evaluate(rr,p,docs,now=NOW)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    digests=[]
    for run in range(3):
        vals=[one(i) for i in range(1000)]
        digests.append(m.verdicts_digest(vals))
    out={'schema':'NOEPIN_AL_REPLAY_V1','technology':51,'runs':3,'evaluations_per_run':1000,'total_evaluations':3000,'digests':digests,'divergence':len(set(digests))-1,'digest':digests[0]}
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,sort_keys=True)); return 0 if out['divergence']==0 else 2
if __name__=='__main__': raise SystemExit(main())
