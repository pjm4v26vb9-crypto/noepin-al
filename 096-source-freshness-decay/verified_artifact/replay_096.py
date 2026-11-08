import dataclasses, hashlib, json
import noepin_al_096_source_freshness_decay as m

def one(run):
    rows=[]; p=m.default_policy()
    for i in range(1000):
        st=list(m.SourceType)[i%5]; vol=list(m.Volatility)[i%4]; risk=list(m.RiskLevel)[i%4]
        ts=None if i%23==0 else 1000.0-(i%11)
        s=dataclasses.replace(m.default_sources()[0],source_type=st,volatility=vol,source_timestamp=ts,updated_verified=(i%97==0),source_version=f'V{i%13}',source_fingerprint=f'SF{i%17}',claim_fingerprint=f'CF{i%19}')
        q=dataclasses.replace(m.default_query(),now=1000.0+(i%240),risk=risk)
        r=m.evaluate(q,(s,),p)
        rows.append((r.decision.value,round(r.freshness_score,15),r.expired,r.refresh_priority.name,r.reasons,r.next_gate_candidate,r.reevaluation_candidate))
    b=json.dumps(rows,ensure_ascii=False,separators=(',',':')).encode(); return hashlib.sha256(b).hexdigest()
ds=[one(i) for i in range(3)]
out={'runs':3,'cases_per_run':1000,'total_cases':3000,'digests':ds,'digest':ds[0],'divergence':0 if len(set(ds))==1 else 1}
print(json.dumps(out,sort_keys=True))
