import json,hashlib
import noepin_al_188_safety_suite_distribution as m
rows=[]
for i in range(1000):
 r=m.evaluate(m.default_request(),m.default_artifacts()); rows.append(m.fingerprint(r))
d0=hashlib.sha256(('\n'.join(rows)).encode()).hexdigest(); div=0
for _ in range(2):
 cur=[m.fingerprint(m.evaluate(m.default_request(),m.default_artifacts())) for i in range(1000)]
 div += sum(a!=b for a,b in zip(rows,cur))
print(json.dumps({'runs':3000,'divergence':div,'digest':d0},sort_keys=True))
raise SystemExit(0 if div==0 else 2)
