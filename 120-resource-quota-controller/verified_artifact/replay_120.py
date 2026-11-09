import json,hashlib
import noepin_al_120_resource_quota_controller as m
base=m._canon(m.default_evaluation()); h=hashlib.sha256(base).hexdigest(); div=0
for _b in range(3):
    for _i in range(1000):
        if m._canon(m.default_evaluation())!=base: div+=1
print(json.dumps({'batches':3,'per_batch':1000,'total':3000,'divergence':div,'replay_digest':h},sort_keys=True)); raise SystemExit(0 if div==0 else 2)
