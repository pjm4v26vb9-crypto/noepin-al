import hashlib,json
from dataclasses import replace
import noepin_al_184_quantum_transport_interference_simulator as m
cases=[
 m.default_request(),
 m.make_request(permission_evidence_present=False),
 m.make_request(min_route_fidelity=.81),
 m.make_request(min_dd_quality=.999999,max_pulses=0),
 m.make_request(qpu_available=True,estimated_classical_cost=8,estimated_qpu_cost=2),
 m.make_request(bell_fidelity=.25,min_gate_fidelity=.95),
]
base=[m._canon(m.evaluate(q)) for q in cases]; div=0; h=hashlib.sha256()
for run in range(3):
 for i in range(1000):
  q=cases[i%len(cases)]; got=m._canon(m.evaluate(q)); exp=base[i%len(cases)]
  if got!=exp: div+=1
  h.update(got)
print(json.dumps({'runs':3,'per_run':1000,'total':3000,'divergence':div,'digest':h.hexdigest()},sort_keys=True))
