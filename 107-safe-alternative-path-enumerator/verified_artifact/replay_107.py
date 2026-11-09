import json,hashlib
import noepin_al_107_safe_alternative_path_enumerator as m
def canon(z):
    def cv(x):
        from enum import Enum
        if isinstance(x,Enum): return x.value if not isinstance(x,m.RiskClass) else x.name
        if hasattr(x,'__dataclass_fields__'): return {k:cv(getattr(x,k)) for k in x.__dataclass_fields__}
        if isinstance(x,tuple): return [cv(v) for v in x]
        return x
    return json.dumps(cv(z),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
base=canon(m.default_evaluation()); h=hashlib.sha256(base).hexdigest(); div=0
for _batch in range(3):
    for _i in range(1000):
        if canon(m.default_evaluation())!=base: div+=1
print(json.dumps({'batches':3,'per_batch':1000,'total':3000,'divergence':div,'replay_digest':h},sort_keys=True))
raise SystemExit(0 if div==0 else 2)
