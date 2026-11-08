from __future__ import annotations
import json
from dataclasses import replace
import noepin_al_056_explanation_layer as m
NOW=1_800_000_000

def one(i):
    p=m.default_policy(NOW); d=m.default_record(NOW); rs=m.default_reasons(); es=m.default_evidence(NOW); ts=m.default_traces(NOW)
    k=i%6
    if k==1: es=(replace(es[0],sensitivity='SECRET'),)
    elif k==2: d=replace(d,expected_policy_version='bad')
    elif k==3: es=(replace(es[0],verified=False),)
    elif k==4: ts=(replace(ts[0],verified=False),)
    elif k==5: rs=(replace(rs[0],required_policy_rules=frozenset({'MISSING_RULE'})),)
    return m.assessment_digest(m.evaluate(d,p,rs,es,ts,now=NOW))

def run():
    digests=[]; divergence=0
    baseline=None
    for _ in range(3):
        cur=[one(i) for i in range(1000)]
        d=m.fingerprint(cur); digests.append(d)
        if baseline is None: baseline=cur
        elif cur!=baseline: divergence+=sum(a!=b for a,b in zip(cur,baseline))
    out={'runs':3,'evaluations_per_run':1000,'total_evaluations':3000,'divergence':divergence,'digest':m.fingerprint(digests),'run_digests':digests}
    print(json.dumps(out,sort_keys=True)); return out
if __name__=='__main__': run()
