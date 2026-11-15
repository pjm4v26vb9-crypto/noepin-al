import json,hashlib
import noepin_al_181_human_approval_challenge_response_protocol as m
q=m.default_verification_request(); vals=[m._canon(m.evaluate_response(q)) for _ in range(3000)]; div=sum(1 for x in vals[1:] if x!=vals[0]); print(json.dumps({'replay_count':3000,'divergence':div,'digest':hashlib.sha256(vals[0]).hexdigest()},sort_keys=True))
