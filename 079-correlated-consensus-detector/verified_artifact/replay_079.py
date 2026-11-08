from dataclasses import replace
from hashlib import sha256
import json
from noepin_al_079_correlated_consensus_detector import *
p,o,q=default_policy(),default_outputs(),default_request(); digests=[]
for run in range(3):
    rows=[]
    for i in range(1000):
        m=i%7; pp=p; oo=o; qq=q
        if m==0: pass
        elif m==1: oo=(replace(o[0],lineage_observed=False),o[1],o[2])
        elif m==2: oo=(replace(o[0],conclusion='NO'),replace(o[1],conclusion='NO'),o[2])
        elif m==3: pp=replace(p,threshold=.75)
        elif m==4:
            a=o[0]; oo=(a,replace(o[1],model_id=a.model_id,prompt_family=a.prompt_family,source_ids=a.source_ids,evidence_ids=a.evidence_ids),o[2])
        elif m==5: qq=replace(q,output_ids=('OUT-A',))
        else: qq=replace(q,output_ids=('OUT-A','NOPE'))
        z=evaluate(qq,pp,oo); rows.append((i,z.decision.value,z.reasons,z.independence_score,z.adjusted_consensus,[(c.member_ids,c.effective_weight,c.avg_similarity) for c in z.clusters],z.lineage_unknown_ids))
    blob=json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode(); digests.append(sha256(blob).hexdigest())
out={'schema':'NOEPIN_AL_REPLAY_V1','technology':79,'iterations_per_run':1000,'runs':3,'total':3000,'divergence':len(set(digests))-1,'digest':digests[0]}
print(json.dumps(out,sort_keys=True))
