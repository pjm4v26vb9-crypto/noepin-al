import hashlib,json
import noepin_al_183_schema_version_negotiation_protocol as m
cases=[
 m.default_request(),
 m.make_request(('1.0',),('2.0',)),
 m.make_request(('1.0','2.0'),('1.0','2.0'),local_schema_id='S1',remote_schema_id='S2'),
 m.make_request(('1.0','2.0'),('1.0','2.0'),local_schema_fingerprint='A',remote_schema_fingerprint='B'),
 m.make_request(('1.0','2.0'),('1.0','2.0'),local_schema_fingerprint='A',remote_schema_fingerprint='B',known_compatible_fingerprint_pairs=(('A','B'),)),
 m.make_request(('0.0','1.0'),('0.0','2.0')),
]
base=[m._canon(m.evaluate(q)) for q in cases]; div=0; h=hashlib.sha256()
for run in range(3):
 for i in range(1000):
  q=cases[i%len(cases)]; got=m._canon(m.evaluate(q)); exp=base[i%len(cases)]
  if got!=exp: div+=1
  h.update(got)
print(json.dumps({'runs':3,'per_run':1000,'total':3000,'divergence':div,'digest':h.hexdigest()},sort_keys=True))
