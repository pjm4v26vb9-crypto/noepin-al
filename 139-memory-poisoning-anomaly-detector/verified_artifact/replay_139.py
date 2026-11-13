import json,hashlib
import noepin_al_139_memory_poisoning_anomaly_detector as m
r=m.default_evaluation(); d=hashlib.sha256(m._canon(r)).hexdigest(); div=0
for _ in range(3000):
    if hashlib.sha256(m._canon(m.default_evaluation())).hexdigest()!=d: div+=1
print(json.dumps({'replays':3000,'divergence':div,'digest':d},sort_keys=True))
