import json
from hashlib import sha256
import noepin_al_124_separation_of_duties_allocator as m
q=m.default_request(); first=None; div=0
for i in range(3000):
    r=m.evaluate(q); b=m._canon(r)
    if first is None: first=b
    elif b!=first: div+=1
print(json.dumps({'iterations':3000,'divergence':div,'digest':sha256(first).hexdigest()},sort_keys=True))
