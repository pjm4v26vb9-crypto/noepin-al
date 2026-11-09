import json
from hashlib import sha256
from dataclasses import replace
import noepin_al_122_trust_weighted_voting as m
q=m.default_request(); first=None; div=0
for i in range(3000):
    r=m.evaluate(q); b=m._canon(r)
    if first is None: first=b
    elif b!=first: div+=1
print(json.dumps({'iterations':3000,'divergence':div,'digest':sha256(first).hexdigest()},sort_keys=True))
