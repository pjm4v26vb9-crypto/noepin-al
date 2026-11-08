import json
from hashlib import sha256
import noepin_al_100_trust_hysteresis_updater as m

def cv(x):
    if hasattr(x,'value'): return x.value
    if hasattr(x,'__dataclass_fields__'): return {k:cv(getattr(x,k)) for k in x.__dataclass_fields__}
    if isinstance(x,tuple): return [cv(v) for v in x]
    return x
r0=m.default_evaluation(); blob=json.dumps(cv(r0),sort_keys=True,separators=(',',':')).encode(); dig=sha256(blob).hexdigest(); div=0
for _ in range(3):
    for _ in range(1000):
        if m.default_evaluation()!=r0: div+=1
print(json.dumps({'runs':3000,'divergence':div,'digest':dig},sort_keys=True))
