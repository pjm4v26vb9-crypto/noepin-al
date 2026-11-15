import hashlib,json
from dataclasses import replace
import noepin_al_186_distributed_common_state_reconstruction_v1 as m
q=m.default_request(); cases=[q,replace(q,allow_remote_lazy=False),replace(q,integrity_validated=False),replace(q,network=m.NetworkCondition(min_shared_ratio_for_dcsr=.8)),replace(q,network=m.NetworkCondition(bandwidth_bytes_per_sec=2_000_000,latency_ms=5))]
base=[m._canon(m.evaluate(x)) for x in cases]; div=0; h=hashlib.sha256()
for run in range(3):
 for i in range(1000):
  got=m._canon(m.evaluate(cases[i%len(cases)])); exp=base[i%len(cases)]
  if got!=exp: div+=1
  h.update(got)
print(json.dumps({'runs':3,'per_run':1000,'total':3000,'divergence':div,'digest':h.hexdigest()},sort_keys=True))
