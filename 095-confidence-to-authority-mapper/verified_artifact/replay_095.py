import dataclasses,hashlib,json
import noepin_al_095_confidence_to_authority_mapper as m

def cv(x):
    if hasattr(x,'value'): return x.value
    if hasattr(x,'__dataclass_fields__'): return {k:cv(getattr(x,k)) for k in x.__dataclass_fields__}
    if isinstance(x,tuple): return [cv(v) for v in x]
    return x
def run_once():
    out=[]
    for i in range(1000):
        q=dataclasses.replace(m.default_request(),adjusted_confidence=((i*17)%101)/100,action_risk=list(m.RiskLevel)[i%4],request_id=f'R{i:04d}')
        out.append(cv(m.evaluate(q,m.default_capabilities(),m.default_policy())))
    b=json.dumps(out,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode(); return hashlib.sha256(b).hexdigest()
if __name__=='__main__':
    ds=[run_once() for _ in range(3)]; print(json.dumps({'runs':3,'cases_per_run':1000,'total_cases':3000,'digests':ds,'divergence':len(set(ds))-1,'replay_digest':ds[0]},sort_keys=True))
