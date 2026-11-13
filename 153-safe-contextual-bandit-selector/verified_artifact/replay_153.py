import json,hashlib
import noepin_al_153_safe_contextual_bandit_selector as m
q=m.default_request(); vals=[]
for _ in range(3000): vals.append(m._canon(m.evaluate(q)))
div=sum(1 for x in vals[1:] if x!=vals[0]); print(json.dumps({'replay_count':3000,'divergence':div,'digest':hashlib.sha256(vals[0]).hexdigest()},sort_keys=True))
