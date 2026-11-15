import hashlib,json
from dataclasses import replace
import noepin_al_185_common_state_kernel_v1 as m
cases=[m.default_request(),replace(m.default_request(),known=False),replace(m.default_request(),ambiguous=True),replace(m.default_request(),context_fingerprint='other'),replace(m.default_request(),schema_version='2')]
base=[m._canon(m.evaluate(q)) for q in cases]; div=0; h=hashlib.sha256()
for run in range(3):
 for i in range(1000):
  got=m._canon(m.evaluate(cases[i%len(cases)])); exp=base[i%len(cases)]
  if got!=exp: div+=1
  h.update(got)
print(json.dumps({'runs':3,'per_run':1000,'total':3000,'divergence':div,'digest':h.hexdigest()},sort_keys=True))
